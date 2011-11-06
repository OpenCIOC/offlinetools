import posixpath, json, zipfile, tempfile
from itertools import groupby, imap
from operator import itemgetter, attrgetter

from pyramid.view import view_config
import requests

from sqlalchemy.orm import subqueryload
from sqlalchemy import and_
from sqlalchemy.sql.expression import bindparam, select
from sqlalchemy.orm.exc import StaleDataError


from offlinetools import models
from offlinetools.views.base import ViewBase
from offlinetools.keymgmt import get_signature

import gc

import logging
log = logging.getLogger('offlinetools.views.pull')

@view_config(route_name="pull", renderer="string")
class Pull(ViewBase):

    def __call__(self):
        request = self.request
        cfg = models.get_config(request)

        if not cfg.machine_name or not cfg.update_url:
            return 'Not properly configured'


        url_base = posixpath.join(cfg.update_url, 'offline')

        # auth request
        auth_data = {'MachineName': cfg.machine_name}
        r = requests.post(posixpath.join(url_base, 'auth'), auth_data)
        r.raise_for_status()

        auth = json.loads(r.content)
        if auth['fail']:
            # Log error
            return 'Request failed: ' + auth['reason']

        
        tosign = ''.join([
                auth['challenge'].decode('base64'), 
                cfg.machine_name.encode('utf-8')])
        signature = get_signature(cfg.private_key, tosign)

        auth_data['ChallengeSig'] = json.dumps(signature)
        r = requests.post(posixpath.join(url_base, 'pull'), auth_data)
        r.raise_for_status()


        log.debug('Response Size: %d', len(r.content))
        with tempfile.TemporaryFile() as fd:
            fd.write(r.content)
            fd.seek(0)

            del r


            with zipfile.ZipFile(fd, 'r') as zip:

                log.debug('Full Size: %d', zip.getinfo('export.json').file_size)
                with zip.open('export.json') as zfd:
                    data = json.load(zfd)



        if data['fail']:
            return 'failed: %s' % data['reason']
        
        self._update(data['data'])

        gc.collect()
        
        return "ok"


    def _update(self, data):
        #session = self.request.dbsession
        
        for fn in [self._update_views, self._update_field_groups, 
                   self._update_fields, self._update_fieldgroup_fields,
                  self._update_users, self._update_records, self._update_record_views,
                  self._update_record_data]:
            fn(data)
            
                
                

    def _update_views(self, data):
        self._update_named_records(data['views'], models.View, models.View_Name, 'ViewType',
                                  [], ['ViewName'])
    def _update_field_groups(self, data):
        self._update_named_records(data['field_groups'], models.FieldGroup, models.FieldGroup_Name, 
                                   'DisplayFieldGroupID', 
                                   ['DisplayOrder', 'ViewType'], 
                                   ['Name'])

    def _update_fields(self, data):
        self.new_fields = self._update_named_records(data['fields'], models.Field, models.Field_Name,
                                   'FieldID',
                                   ['FieldName', 
                                    'DisplayOrder'],
                                   ['Name'])
    def _update_users(self,data):
        self._update_named_records(data['users'], models.Users, None, 'UserName',
                                   ['PasswordHash', 'PasswordHashRepeat', 'PasswordHashSalt',
                                    'ViewType', 'LangID'], [])

    def _update_fieldgroup_fields(self, data):
        cols = ['DisplayFieldGroupID', 'FieldID']
        fn = itemgetter(*cols)
        source = set(imap(fn, data['fieldgroup_fields']))

        session = self.request.dbsession
        session.flush()

        existing = set(map(tuple, session.execute(select([models.FieldGroup_Fields.c.DisplayFieldGroupID, models.FieldGroup_Fields.c.FieldID]))))

        to_delete = [dict(zip(cols, x)) for x in existing-source]

        d = models.FieldGroup_Fields.delete().where(and_(models.FieldGroup_Fields.c.DisplayFieldGroupID==bindparam('DisplayFieldGroupID'),models.FieldGroup_Fields.c.FieldID==bindparam('FieldID')))

        session.execute(d, to_delete)

        to_add = [dict(zip(cols, x)) for x in source-existing]
        session.execute(models.FieldGroup_Fields.insert(), to_add)

    def _update_records(self, data):
        cols = ['NUM', 'LangID']
        session = self.request.dbsession
        records = set(map(itemgetter(*cols), data['records_views']))

        for record in session.query(models.Record).all():
            if (record.NUM, record.LangID) in records:
                records.remove((record.NUM, record.LangID))
            else:
                session.delete(record)

        for num, lang in records:
            session.add(models.Record(NUM=num, LangID=lang))

        self.unseen_records = [dict(zip(cols, x)) for x in records]

    def _update_record_views(self,data):
        cols = ['NUM', 'ViewType']
        source = set(imap(itemgetter(*cols), data['records_views']))

        session = self.request.dbsession
        session.flush()
        
        existing = set(map(tuple, session.execute(models.Record_Views.select())))

        to_delete = existing-source

        d = models.Record_Views.delete().where(and_(models.Record_Views.c.NUM==bindparam('NUM'),models.Record_Views.c.ViewType==bindparam('ViewType')))
        session.execute(d, [dict(zip(cols, x)) for x in to_delete])

        try:
            session.flush()
        except StaleDataError:
            pass

        to_add = [dict(zip(cols,x)) for x in source-existing]
        session.execute(models.Record_Views.insert(), to_add)


    def _update_record_data(self, data):
        session = self.request.dbsession


        fn = itemgetter('NUM', 'LangID', 'FieldID')
        id_map = {fn(x): x for x in data['record_data']}

        keyfn = attrgetter('NUM', 'LangID', 'FieldID')
        for i,item in enumerate(session.query(models.Record_Data).yield_per(100)):
            if i and i % 100 == 0:
                session.flush()

            item_id = keyfn(item)
            if item_id not in id_map:
                session.delete(item)
                continue

            item_to_update = id_map.pop(item_id)
            item.Value = item_to_update['FieldDisplay']
            if item.Value is None:
                session.delete(item)




        for item_to_update in id_map.values():
            if item_to_update['FieldDisplay'] is None:
                continue

            item_to_update['Value'] = item_to_update.pop('FieldDisplay')
            item = models.Record_Data(**item_to_update)
            session.add(item)



    def _insert_named_records(self, items, item_model, name_model, primary_key, primary_updates, name_updates):
        session = self.request.dbsession
        source = set([x[primary_key] for x in items])

        pk = getattr(item_model, primary_key)
        existing = set(session.query(pk).all())

        to_insert = [x for x in items if x[primary_key] in source-existing]
        keyfn = itemgetter(primary_key)
        to_insert.sort(key=itemgetter(primary_key))

        for key,group in groupby(to_insert, keyfn):
            names = []
            for i,source_item in enumerate(group):
                if not i:
                    source_item = group
                    kw = {f: source_item[f] for f in primary_updates}
                    kw[primary_key] = key
                    item = item_model(**kw)

                if name_model:
                    kw = {f: source_item[f] for f in name_updates}
                    kw['LangID'] = source_item['LangID']
                    names.append(name_model(**kw))

            if name_model:
                item.names = names

            session.add(item)

        session.flush()


        if name_model:
            source = set([(x[primary_key], x['LangID']) for x in items])
            pk = getattr(name_model, primary_key)
            lang = getattr(name_model, 'LangID')
            existing = set(session.query(pk,lang).all())
            names_to_insert = [x for x in items if (x[primary_key], x['LangID']) in source-existing]

            for source_item in names_to_insert:
                kw = {f: source_item[f] for f in name_updates + [primary_key, 'LangID']}

                session.add(name_model(**kw))
            
            session.flush()

        return to_insert


    def _update_named_records(self, items, item_model, name_model, primary_key, primary_updates, name_updates):
        session = self.request.dbsession
        id_map = {}

        keyfn = itemgetter(primary_key)
        items.sort(key=keyfn)

        for key, group in groupby(items, keyfn):
            id_map[key] = {x['LangID']: x for x in group}

        query = session.query(item_model)
        if name_model:
            query = query.options(subqueryload(item_model.names))
        for item in query.all():
            item_id = getattr(item, primary_key)
            if item_id not in id_map:
                session.delete(item)
                continue

            items_to_update = id_map.pop(item_id)
            langs = set(items_to_update.keys())

            source_item = items_to_update.values()[0]
            for field in primary_updates:
                setattr(item, field, source_item[field])

            if not name_model:
                #only primary model
                continue 

            for name in item.names:
                if name.LangID not in items_to_update:
                    session.delete(name)
                    continue

                source_item = items_to_update[name.LangID]
                langs.remove(name.LangID)

                for field in name_updates:
                    setattr(name, field, source_item[field])

            for lang in langs:
                source_item = items_to_update[lang]
                kw = {f: source_item[f] for f in name_updates}
                name = name_model(LangID=lang, **kw)
                item.names.append(name)


        for item_id,items_to_update in id_map.iteritems():
            source_item = items_to_update.values()[0]
            kw = {f: source_item[f] for f in primary_updates}
            kw[primary_key] = item_id

            item = item_model(**kw)

            if name_model:
                names = []
                for lang,source_item in items_to_update.items():
                    kw = {f: source_item[f] for f in name_updates}
                    names.append(name_model(LangID=lang, **kw))

                item.names = names

            session.add(item)

        return id_map.keys()

                

                
                







               

