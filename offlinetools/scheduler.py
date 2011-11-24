from datetime import datetime, timedelta
import posixpath, json, zipfile, tempfile
from itertools import groupby, imap
from operator import itemgetter, attrgetter
import gc

import requests

from sqlalchemy import and_
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import bindparam, select, delete, update, insert
import transaction


from offlinetools import models
from offlinetools.keymgmt import get_signature

import logging
log = logging.getLogger('offlinetools.scheduler')

def key_to_schedule(pubkey):
    _ = lambda x: x
    days = [_('Tue'), _('Wed'), _('Thr'), _('Fri'), _('Sat')]
    hours = [datetime(2010, 1, 1,0), datetime(2010, 1, 1, 6)]
    time_delta = hours[1] - hours[0]
    total_seconds_per_night = time_delta.total_seconds()
    total_slots_per_night = total_seconds_per_night / 30
    total_slots = len(days) * total_slots_per_night

    slot = hash(pubkey) % total_slots

    day, night_slot = divmod(slot, total_slots_per_night)
    
    night_time = timedelta(0, night_slot * 30)
    night_time = (datetime(2010, 1, 1, 0) + night_time).time()

    return {'day_of_week': days[int(day)], 'hour': night_time.hour, 'minute': night_time.minute, 'second': night_time.second}


def scheduled_pull():
    pull = PullObject()
    pull.run()

class PullObject(object):

    def __init__(self, force=False):
        self.status = 0
        self.completion_code = None
        self.force = force


    def run(self):
        self.dbsession = models.DBSession()
        try:
            self._run()
        except Exception, e:
            log.exception('Caught Failure in pull:')
            self.completion_code = 'Unknown failure: %s' % e

        if self.completion_code != 'ok':
            # failure machinery
            transaction.abort()
            cfg = models.get_config(self.dbsession)

            if not cfg.update_log:
                update_log = []
                log_msg = '%s: Initial Update Failed: %s' % (datetime.now().isoformat(), self.completion_code)
            else:
                update_log = [cfg.update_log]
                log_msg = '%s: Update Failed: %s' % (datetime.now().isoformat(), self.completion_code)

            cfg.update_log = '\n'.join([log_msg] + update_log)

            cfg.update_failure_count = (cfg.update_failure_count or 0) + 1

            self.dbsession.flush()
            transaction.commit()



    def _run(self):
        dbsession = self.dbsession
        cfg = models.get_config(session=dbsession)

        if not cfg.machine_name or not cfg.update_url:
            self.completion_code = 'Not properly configured'
            return 


        url_base = posixpath.join(cfg.update_url, 'offline')

        # auth request
        auth_data = {'MachineName': cfg.machine_name}
        r = requests.post(posixpath.join(url_base, 'auth'), auth_data)
        try:
            r.raise_for_status()
        except Exception, e:
            self.completion_code = 'Request failed: %s' % e 
            return

        auth = json.loads(r.content)
        if auth['fail']:
            # Log error
            self.completion_code = 'Request failed: ' + auth['reason']
            return 

        
        tosign = ''.join([
                auth['challenge'].decode('base64'), 
                cfg.machine_name.encode('utf-8')])
        signature = get_signature(cfg.private_key, tosign)

        auth_data['ChallengeSig'] = json.dumps(signature)
        if cfg.last_update and not self.force:
            auth_data['FromDate'] = cfg.last_update.isoformat()
        r = requests.post(posixpath.join(url_base, 'pull'), auth_data)
        try:
            r.raise_for_status()
        except Exception, e:
            self.completion_code = 'Request failed: %s' % e
            return 


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
            self.completion_code = 'failed: %s' % data['reason']
            return 
        
        self._update(data['data'], (cfg.last_update and not self.force))

        data = None

        log.debug('gc collect')

        gc.collect()

        log.debug('after gc collect')

        if (cfg.last_update and not self.force) and (self._new_fields or self._new_records):
            log.debug('********** Second Update')
            try:
                del auth_data['FromDate']
            except KeyError:
                pass

            auth_data['NewFields'] = list(sorted(set(unicode(x['FieldID']) for x in self._new_fields)))
            auth_data['NewRecords'] = list(sorted(set(x[0] for x in self._new_records)))
            r = requests.post(posixpath.join(url_base, 'pull2'), auth_data)
            try:
                r.raise_for_status()
            except Exception, e:
                self.completion_code = '*************************************** Request failed: %s' % e
                return 


            log.debug('***************************************************** Response Size: %d', len(r.content))
            with tempfile.TemporaryFile() as fd:
                fd.write(r.content)
                fd.seek(0)

                del r


                with zipfile.ZipFile(fd, 'r') as zip:

                    log.debug('Full Size: %d', zip.getinfo('export.json').file_size)
                    with zip.open('export.json') as zfd:
                        data = json.load(zfd)



            if data['fail']:
                self.completion_code = 'failed: %s' % data['reason']
                return 
            
            self._update2(data['data'])

            data = None

            log.debug('gc collect')
            gc.collect()
            log.debug('after gc collect')
        
        self.completion_code = 'ok'
        cfg.last_update = datetime.now()
        update_log = [cfg.update_log] if cfg.update_log else []
        cfg.update_log = '\n'.join(['%s: Pull Success' % datetime.now().isoformat()] + update_log)
        cfg.update_failure_count = 0

        dbsession.flush()

        log.debug('********************************************* before commit')
        transaction.commit()
        log.debug('********************************************* after commit')
        return 


    def _update(self, data, expect_second_update):
        #session = self.dbsession
        
        inserts = [self._insert_views, self._insert_communities, self._insert_publications,
                   self._insert_publication_views, self._insert_field_groups, 
                   self._insert_fields, self._insert_fieldgroup_fields,
                   self._insert_users, self._insert_records, self._insert_record_views,
                   self._insert_records_communities, self._insert_records_publications]

        updates = [self._update_views, self._update_communities, self._update_publications,
                   self._update_field_groups, self._update_fields, self._update_users, 
                  self._update_record_data]
        
        deletes = [self._delete_views, self._delete_communities, self._delete_publications, 
                   self._delete_publication_views, self._delete_field_groups, 
                   self._delete_fields, self._delete_fieldgroup_fields,
                   self._delete_users, self._delete_records, self._delete_record_views,
                   self._delete_records_communities, self._delete_records_publications]

        tasks = inserts + updates + deletes

        total_tasks = len(tasks)

        if expect_second_update:
            total_tasks = total_tasks * 2


        for i,fn in enumerate(tasks):
            self.status = min(((100 * (1+i))/total_tasks, 100))
            fn(data)

        self.status = min(((100 * (2+i))/total_tasks, 100))

        if not expect_second_update or not self._new_fields or not self._new_records:
            log.debug('Before UPdate Caches')
            self._update_caches()
            log.debug('After Update Caches')

        

    def _update2(self, data):
        self._update_record_data(data)
        log.debug('Before UPdate Caches')
        self._update_caches()
        log.debug('After Update Caches')
                

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
        self._new_fields = self._insert_named_records(data['fields'], models.Field, models.Field_Name,
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
                                   ['ParentCommunity'], ['Name'])
    def _update_communities(self,data):
        self._update_named_records(data['communities'], models.Community, models.Community_Name, 'CM_ID',
                                   ['ParentCommunity'], ['Name'])
    def _delete_communities(self,data):
        self._delete_named_records(data['communities'], models.Community, models.Community_Name, 'CM_ID',
                                   ['ParentCommunity'], ['Name'])


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

        session = self.dbsession
        session.flush()

        existing = set(map(tuple, session.execute(select([getattr(item_model.c, x) for x in cols]))))

        to_add = [dict(zip(cols, x)) for x in source-existing]
        session.execute(item_model.insert(), to_add)

        return existing-source

    def _delete_multi_relation(self, cols, item_model, to_delete):
        to_delete = [dict(zip(cols,x)) for x in to_delete]

        session = self.dbsession
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
        session = self.dbsession

        source = set(map(itemgetter(*cols), data['records_views']))

        existing = set(map(tuple, session.execute(select([models.Record.NUM, models.Record.LangID]))))

        to_add = [dict(zip(cols, x)) for x in source-existing]
        if to_add:
            session.execute(insert(models.Record.__table__).values({models.Record.NUM:bindparam('NUM'),models.Record.LangID:bindparam('LangID')}), to_add)

        self._new_records = source-existing

        self._records_to_delete = existing-source

    def _delete_records(self, data):
        if not self._records_to_delete:
            return

        cols = ['NUM', 'LangID']

        session = self.dbsession

        to_delete = [dict(zip(cols, x)) for x in self._records_to_delete]
        d = delete(models.Record.__table__).where(and_(models.Record.NUM==bindparam('NUM'),models.Record.LangID==bindparam('LangID')))

        session.execute(d, to_delete)

    def _update_caches(self):

        session = self.dbsession

        d = delete(models.KeywordCache.__table__)
        session.execute(d)

        fields = [u'ORG_LEVEL_%d' % i for i in range(1,6)]
        q = (session.query(models.Record_Data.LangID, models.Record_Data.Value).
             join(models.Field, models.Record_Data.FieldID==models.Field.FieldID).
             filter(models.Field.FieldName.in_(fields)))

        vals = {(x.LangID, x.Value.strip()) for x in q}

        q = (session.query(models.Record_Data.LangID, models.Record_Data.Value).
             join(models.Field, models.Record_Data.FieldID==models.Field.FieldID).
             filter(models.Field.FieldName==u'TAXONOMY'))

        vals.update((x.LangID, y.strip()) for x in q for y in x.Value.split(';'))


        cols = ['LangID', 'Value']
        if vals:
            session.execute(models.KeywordCache.__table__.insert(), [dict(zip(cols, x)) for x in vals if x[-1]])

        name_args = [aliased(models.Record_Data,session.query(models.Record_Data).
                     join(models.Field, models.Field.FieldID==models.Record_Data.FieldID).
                     filter(models.Field.FieldName==('ORG_LEVEL_%d'% x)).
                     subquery()) for x in range(1,6)]

        located_in = (aliased(models.Record_Data,session.query(models.Record_Data).
                     join(models.Field, models.Field.FieldID==models.Record_Data.FieldID).
                     filter(models.Field.FieldName=='LOCATED_IN_CM').
                     subquery()))

        stmt = session.query(models.Record.NUM, models.Record.LangID, located_in.Value, *[x.Value for x in name_args])
        stmt = stmt.outerjoin(located_in, and_(models.Record.NUM==located_in.NUM, models.Record.LangID==located_in.LangID))
        for substmt in name_args:
            stmt = stmt.outerjoin(substmt, and_(models.Record.NUM==substmt.NUM, models.Record.LangID==substmt.LangID))


        cols = ['b_NUM', 'b_LangID', 'b_LOCATED_IN_Cache', 'b_OrgName_Cache']
        cache_data = stmt.all()
        cache_data = ((x.NUM, x.LangID, x[2], ', '.join(y for y in x[-5:] if y) or None) for x in cache_data)

        u = update(models.Record.__table__).where(and_(models.Record.NUM==bindparam('b_NUM'), models.Record.LangID==bindparam('b_LangID'))).values({'LOCATED_IN_Cache': bindparam('b_LOCATED_IN_Cache'), 'OrgName_Cache': bindparam('b_OrgName_Cache')})

        session.execute(u, [dict(zip(cols, x)) for x in cache_data])


        sql = '''
        UPDATE Record SET LOCATED_IN_CM = 
            (SELECT 
                (SELECT CM_ID 
                    FROM Community_Name 
                    WHERE Community_Name.Name=Record_Data.Value 
                    ORDER BY Community_Name.LangID 
                    LIMIT 1
                ) 
            FROM Record_Data 
            WHERE FieldID=(SELECT FieldID FROM Field WHERE FieldName='LOCATED_IN_CM') 
                AND Record_Data.NUM=Record.NUM 
                AND Record_Data.LangID=Record.LangID 
            ORDER BY Record_Data.LangID
            LIMIT 1
            ) 
            '''

        session.execute(sql)


    def _update_record_data(self, data):
        session = self.dbsession


        fn = itemgetter('NUM', 'LangID', 'FieldID')
        id_map = {fn(x): x for x in data['record_data']}

        keyfn = attrgetter('NUM', 'LangID', 'FieldID')
        for i,item in enumerate(session.query(models.Record_Data).yield_per(100)):
            if i and i % 100 == 0:
                session.flush()

            item_id = keyfn(item)
            if item_id not in id_map:
                #session.delete(item)
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
        session = self.dbsession
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
        session = self.dbsession

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
        session = self.dbsession
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
            

