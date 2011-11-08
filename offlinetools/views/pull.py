import posixpath, json, zipfile, tempfile
from itertools import groupby, imap
from operator import itemgetter, attrgetter

from pyramid.view import view_config
import requests

from sqlalchemy import and_
from sqlalchemy.sql.expression import bindparam, select, delete, update, insert
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
        
        # insert

        for fn in [self._insert_views, self._insert_communities, self._insert_publications,
                   self._insert_publication_views, self._insert_field_groups, 
                   self._insert_fields, self._insert_fieldgroup_fields,
                   self._insert_users, self._insert_records, self._insert_record_views,
                   self._insert_records_communities, self._insert_records_publications]:
            fn(data)

        for fn in [self._update_views, self._update_communities, self._update_publications,
                   self._update_field_groups, self._update_fields, self._update_users, 
                  self._update_record_data]:
            fn(data)

        for fn in [self._delete_views, self._delete_communities, self._delete_publications,
                   self._delete_publication_views, self._delete_field_groups, 
                   self._delete_fields, self._delete_fieldgroup_fields,
                   self._delete_users, self._delete_records, self._delete_record_views,
                   self._delete_records_communities, self._delete_records_publications]:
            fn(data)
            
                

                

    def _insert_views(self, data):
        self._insert_named_records(data['views'], models.View, models.View_Name, 'ViewType',
                                   [], ['ViewName'])
    def _update_views(self, data):
        self._update_named_records(data['views'], models.View, models.View_Name, 'ViewType',
                                  [], ['ViewName'])
    def _delete_views(self, data):
        self._delete_named_records(data['views'], models.View, models.View_Name, 'ViewType',
                                  [], ['ViewName'])

    def _insert_field_groups(self, data):
        self._insert_named_records(data['field_groups'], models.FieldGroup, models.FieldGroup_Name, 
                                   'DisplayFieldGroupID', 
                                   ['DisplayOrder', 'ViewType'], 
                                   ['Name'])
    def _update_field_groups(self, data):
        self._update_named_records(data['field_groups'], models.FieldGroup, models.FieldGroup_Name, 
                                   'DisplayFieldGroupID', 
                                   ['DisplayOrder', 'ViewType'], 
                                   ['Name'])
    def _delete_field_groups(self, data):
        self._delete_named_records(data['field_groups'], models.FieldGroup, models.FieldGroup_Name, 
                                   'DisplayFieldGroupID', 
                                   ['DisplayOrder', 'ViewType'], 
                                   ['Name'])


    def _insert_fields(self, data):
        self.new_fields = self._insert_named_records(data['fields'], models.Field, models.Field_Name,
                                   'FieldID',
                                   ['FieldName', 
                                    'DisplayOrder'],
                                   ['Name'])
    def _update_fields(self, data):
        self._update_named_records(data['fields'], models.Field, models.Field_Name,
                                   'FieldID',
                                   ['FieldName', 
                                    'DisplayOrder'],
                                   ['Name'])
    def _delete_fields(self, data):
        self._delete_named_records(data['fields'], models.Field, models.Field_Name,
                                   'FieldID',
                                   ['FieldName', 
                                    'DisplayOrder'],
                                   ['Name'])

    def _insert_users(self,data):
        self._insert_named_records(data['users'], models.Users, None, 'UserName',
                                   ['PasswordHash', 'PasswordHashRepeat', 'PasswordHashSalt',
                                    'ViewType', 'LangID'], [])
    def _update_users(self,data):
        self._update_named_records(data['users'], models.Users, None, 'UserName',
                                   ['PasswordHash', 'PasswordHashRepeat', 'PasswordHashSalt',
                                    'ViewType', 'LangID'], [])
    def _delete_users(self,data):
        self._delete_named_records(data['users'], models.Users, None, 'UserName',
                                   ['PasswordHash', 'PasswordHashRepeat', 'PasswordHashSalt',
                                    'ViewType', 'LangID'], [])

    def _insert_communities(self,data):
        self._insert_named_records(data['communities'], models.Community, models.Community_Name, 'CM_ID',
                                   [], ['Name'])
    def _update_communities(self,data):
        self._update_named_records(data['communities'], models.Community, models.Community_Name, 'CM_ID',
                                   [], ['Name'])
    def _delete_communities(self,data):
        self._delete_named_records(data['communities'], models.Community, models.Community_Name, 'CM_ID',
                                   [], ['Name'])


    def _insert_publications(self,data):
        self._insert_named_records(data['publications'], models.Publication, models.Publication_Name, 'ListID',
                                   [], ['Name'])
    def _update_publications(self,data):
        self._update_named_records(data['publications'], models.Publication, models.Publication_Name, 'ListID',
                                   [], ['Name'])
    def _delete_publications(self,data):
        self._delete_named_records(data['publications'], models.Publication, models.Publication_Name, 'ListID',
                                   [], ['Name'])


    def _insert_multi_relation(self, data, cols, item_model):
        fn = itemgetter(*cols)
        source = set(imap(fn, data))

        session = self.request.dbsession
        session.flush()

        existing = set(map(tuple, session.execute(select([getattr(item_model.c, x) for x in cols]))))

        to_add = [dict(zip(cols, x)) for x in source-existing]
        session.execute(item_model.insert(), to_add)

        return existing-source

    def _delete_multi_relation(self, cols, item_model, to_delete):
        to_delete = [dict(zip(cols,x)) for x in to_delete]

        session = self.request.dbsession
        d = delete(item_model).where(and_(*[getattr(item_model.c, x) == bindparam(x) for x in cols]))

        session.execute(d, to_delete)
    
    def _insert_fieldgroup_fields(self,data):
        self._fieldgroup_fields_to_delete = self._insert_multi_relation(
            data['fieldgroup_fields'], ['DisplayFieldGroupID', 'FieldID'], models.FieldGroup_Fields)

    def _delete_fieldgroup_fields(self,data):
        self._delete_multi_relation(['DisplayFieldGroupID', 'FieldID'], models.FieldGroup_Fields,
                                    self._fieldgroup_fields_to_delete)


    def _insert_record_views(self,data):
        self._record_views_to_delete = self._insert_multi_relation(
            data['records_views'], ['NUM', 'ViewType'], models.Record_Views)

    def _delete_record_views(self,data):
        self._delete_multi_relation(['NUM', 'ViewType'], models.Record_Views,
                                    self._record_views_to_delete)


    def _insert_publication_views(self,data):
        self._publication_views_to_delete = self._insert_multi_relation(
            data['view_publications'], ['ListID', 'ViewType'], models.Publication_View)

    def _delete_publication_views(self,data):
        self._delete_multi_relation(['ListID', 'ViewType'], models.Publication_View,
                                    self._publication_views_to_delete)


    def _insert_records_communities(self,data):
        self._record_communities_to_delete = self._insert_multi_relation(
            data['record_communities'], ['NUM', 'CM_ID'], models.Record_Community)

    def _delete_records_communities(self,data):
        self._delete_multi_relation(['NUM', 'CM_ID'], models.Record_Community,
                                    self._record_communities_to_delete)
        

    def _insert_records_publications(self,data):
        self._record_publications_to_delete = self._insert_multi_relation(
            data['record_publications'], ['NUM', 'ListID'], models.Record_Publication)

    def _delete_records_publications(self,data):
        self._delete_multi_relation(['NUM', 'ListID'], models.Record_Publication,
                                    self._record_publications_to_delete)
        

    def _insert_records(self, data):
        cols = ['NUM', 'LangID']
        session = self.request.dbsession

        source = set(map(itemgetter(*cols), data['records_views']))

        existing = set(map(tuple, session.execute(select([models.Record.NUM, models.Record.LangID]))))

        to_add = [dict(zip(cols, x)) for x in source-existing]
        if to_add:
            self.request.data_records = to_add
            session.execute(insert(models.Record.__table__).values({models.Record.NUM:bindparam('NUM'),models.Record.LangID:bindparam('LangID')}), to_add)

        self._records_to_delete = existing-source

    def _delete_records(self, data):
        if not self._records_to_delete:
            return

        cols = ['NUM', 'LangID']

        session = self.request.dbsession

        to_delete = [dict(zip(cols, x)) for x in self._records_to_delete]
        d = delete(models.Record.__table__).where(and_(models.Record.NUM==bindparam('NUM'),models.Record.LangID==bindparam('LangID')))

        session.execute(d, to_delete)

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
        existing = set(x[0] for x in session.query(pk).all())

        to_insert = [x for x in items if x[primary_key] in source-existing]
        keyfn = itemgetter(primary_key)
        to_insert.sort(key=itemgetter(primary_key))

        for key,group in groupby(to_insert, keyfn):
            names = []
            for i,source_item in enumerate(group):
                if not i:
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
            lang = name_model.LangID
            existing = set(session.query(pk,lang).all())
            names_to_insert = [x for x in items if (x[primary_key], x['LangID']) in source-existing]

            for source_item in names_to_insert:
                kw = {f: source_item[f] for f in name_updates + [primary_key, 'LangID']}

                session.add(name_model(**kw))
            
            session.flush()

        return to_insert

    def _delete_named_records(self, items, item_model, name_model, primary_key, primary_updates, name_updates):
        session = self.request.dbsession

        if name_model:
            source = set([(x[primary_key],x['LangID']) for x in items])
            pk = getattr(name_model, primary_key)
            lang = name_model.LangID
            existing = set(session.query(pk,lang).all())
            to_delete = existing-source

            d = delete(name_model.__table__).where(and_(getattr(name_model, primary_key)==bindparam(primary_key), name_model.LangID==bindparam('LangID')))
            session.execute(d, [{primary_key: x[0], 'LangID': x[1]} for x in to_delete])

        source = set([x[primary_key] for x in items])

        pk = getattr(item_model, primary_key)
        existing = set(x[0] for x in session.query(pk).all())

        to_delete = existing-source

        d = delete(item_model.__table__).where(getattr(item_model, primary_key)==bindparam(primary_key))
        session.execute(d, [{primary_key: x} for x in to_delete])

    def _update_named_records(self, items, item_model, name_model, primary_key, primary_updates, name_updates):
        session = self.request.dbsession
        id_map = {}
        
        keyfn = itemgetter(primary_key)
        items.sort(key=keyfn)

        for key, group in groupby(items, keyfn):
            id_map[key] = list(group)

        source = set(id_map.keys())

        pk = getattr(item_model, primary_key)

        existing = set(x[0] for x in session.query(pk).all())

        to_update = existing & source

        if primary_updates:
            kw = {getattr(item_model,x): bindparam(x) for x in primary_updates}
            u = update(item_model.__table__).where(getattr(item_model, primary_key)==bindparam('pk')).\
                        values(kw)
            upd = (id_map[x][0] for x in to_update)
            cols = [primary_key] + primary_updates
            keyfn = itemgetter(*cols)
            cols = ['pk'] + primary_updates
            session.execute(u, [dict(zip(cols, keyfn(x))) for x in upd])

        if name_model:
            kw = {getattr(name_model,x): bindparam(x) for x in name_updates}
            u = update(name_model.__table__).where(and_(getattr(name_model, primary_key)==bindparam('pk'), name_model.LangID==bindparam('langid'))).\
                    values(kw)
            upd = (y for x in to_update for y in id_map[x])
            cols = [primary_key, 'LangID'] + name_updates
            keyfn = itemgetter(*cols)
            cols = ['pk', 'langid'] + name_updates
            session.execute(u, [dict(zip(cols, keyfn(x))) for x in upd])
            

