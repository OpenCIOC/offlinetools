from itertools import groupby, chain, izip, repeat
from pyramid.view import view_config

from formencode import Schema
from sqlalchemy import and_
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import case

from offlinetools import models
from offlinetools.views.base import ViewBase
from offlinetools.views import validators

import logging
log = logging.getLogger('offlinetools.views.search')

class SearchSchema(Schema):
    Terms = validators.UnicodeString(max=255)
    QuickList = validators.UnicodeString(max=50)
    Community = validators.UnicodeString(max=255)


class Search(ViewBase):
    @view_config(route_name='search', permission='view', renderer='search.mak')
    def search(self):
        return self._get_form_values()



    @view_config(route_name='results', permission='view', renderer='results.mak')
    def results(self):
        request = self.request

        model_state = request.model_state
        model_state.schema = SearchSchema()
        model_state.method = None


        if not model_state.validate():
            request.override_renderer = 'search.mak'
            log.debug('errors: %s', model_state.form.errors)
            return self._get_form_values()

        LangID=request.language.LangID
        ViewType = request.user.ViewType
        session = request.dbsession
        
        field_names = [u'ORG_LEVEL_%d' % i for i in range(1,6)] + [u'LOCATED_IN_CM']
        field_ids = dict(session.query(models.Field.FieldName,models.Field.FieldID).filter(models.Field.FieldName.in_(field_names)).all())
        log.debug('field_ids: %s', field_ids)

        name_tmpl = '(SELECT Value FROM Record_Data WHERE bt.NUM=NUM AND LangID=? AND FieldID=?) AS ORG_LEVEL_{0}'

        sql = [('''
                SELECT bt.NUM,\n(SELECT Value FROM  Record_Data rd WHERE bt.NUM=NUM AND FieldID=? AND 
                        LangID=(SELECT LangID FROM Record_Data WHERE rd.NUM=NUM AND FieldID=rd.FieldID 
               ORDER BY CASE WHEN LangID=? THEN 0 ELSE 1 END, LangID LIMIT 1)) AS LOCATED_IN_CM, \n'''
                + ',\n'.join(name_tmpl.format(i) for i in range(1,6)) + 
               '''

               FROM Record bt
               ''')]

        args = [field_ids['LOCATED_IN_CM'], LangID]
        args.extend(chain.from_iterable(izip(repeat(LangID, 5), (field_ids[x] for x in field_names[:5]))))

#        filters = [models.Record.views.any(models.View.ViewType==ViewType), 
#                   models.Record.LangID==LangID]
        where = ['bt.LangID=?', 'EXISTS(SELECT 1 FROM Record_Views WHERE NUM=bt.NUM AND ViewType=?)']
        args.extend([LangID, ViewType])

        quick_list = model_state.value('QuickList')
        if quick_list:
#            filters.append(models.Record.publications.any(models.Publication.ListID==quick_list))
            where.append('\nEXISTS(SELECT 1 FROM Record_Publication rp WHERE rp.NUM=bt.NUM AND ListID=?)')
            args.append(quick_list)


        if model_state.value('Terms'):
#            filters.append(models.Record.fields.any(models.Record_Data.Value.like('%%%s%%' % model_state.value('Terms'))))
            where.append('EXISTS(SELECT 1 from Record_Data WHERE bt.NUM=NUM AND LangID=? AND Value LIKE ?)')
            args.extend([LangID, '%{0}%'.format(model_state.value('Terms'))])

        community = model_state.value('Community')
        if community:
            row = session.query(models.Community_Name.CM_ID, models.Community.ParentCommunity).join(models.Community, models.Community.CM_ID==models.Community_Name.CM_ID).filter(models.Community_Name.Name.like(community)).order_by(case(value=models.Community_Name.LangID, whens={LangID: 0}, else_=1),models.Community_Name.LangID).first()
            log.debug('Community: %s', row)
            if row and row[0]:

                CM_IDS = set()
                Parent = row[1]
                children = {row[0]}
                for i in range(12):
                    if not children:
                        break

                    CM_IDS.update(children)
                    children = [x[0] for x in session.query(models.Community.CM_ID).filter(models.Community.ParentCommunity.in_(children)).all()]
                else:
                    CM_IDS.update(children)

                for i in range(12):
                    if Parent is None:
                        break
                    
                    CM_IDS.add(Parent)
                    Parent = session.query(models.Community.ParentCommunity).filter(models.Community.CM_ID==Parent).first() #there should be only one
                    if Parent:
                        Parent = Parent[0]
                else:
                    CM_IDS.add(Parent)



                log.debug('Communities: %s', session.query(models.Community.CM_ID, models.Community.ParentCommunity, models.Community_Name.Name).join(models.Community_Name).filter(models.Community_Name.LangID==0).filter(models.Community.CM_ID.in_(CM_IDS)).all())

#                filters.append(models.Record.communities.any(models.Community.CM_ID.in_(CM_IDS)))
                where.append('EXISTS(SELECT 1 FROM Record_Community WHERE bt.NUM=NUM AND CM_ID IN ({0}))'.format(','.join('?' * len(CM_IDS))))
                args.extend(CM_IDS)




#        name_args = [aliased(models.Record_Data,session.query(models.Record_Data).
#                     join(models.Field, models.Field.FieldID==models.Record_Data.FieldID).
#                     filter(models.Record_Data.LangID==LangID).
#                     filter(models.Field.FieldName==('ORG_LEVEL_%d'% x)).
#                     subquery()) for x in range(1,6)]
#
#        located_in = (aliased(models.Record_Data,session.query(models.Record_Data).
#                     join(models.Field, models.Field.FieldID==models.Record_Data.FieldID).
#                     filter(models.Record_Data.LangID==LangID).
#                     filter(models.Field.FieldName=='LOCATED_IN_CM').
#                     subquery()))
#
#        stmt = session.query(models.Record.NUM)#, located_in.Value, *[x.Value for x in name_args])
        #stmt = stmt.outerjoin(located_in, models.Record.NUM==located_in.NUM)
        #for substmt in name_args:
        #    stmt = stmt.outerjoin(substmt, models.Record.NUM==substmt.NUM)
        
        #results = stmt.filter(and_(*filters)).all()
        sql = ''.join(['SELECT * FROM ('] + sql + ['\nWHERE\n\t' , '\nAND\n\t'.join(where),') AS iq ORDER BY iq.ORG_LEVEL_1 COLLATE NOCASE, iq.ORG_LEVEL_2 COLLATE NOCASE, iq.ORG_LEVEL_3 COLLATE NOCASE, iq.ORG_LEVEL_4 COLLATE NOCASE, iq.ORG_LEVEL_5 COLLATE NOCASE, NUM'])
        connection = session.connection()
        results = map(tuple,connection.execute(sql, *args))

        

        #fields = ['ORG_LEVEL_%d' % x for x in range(1,6)]
#        name_data = (session.query(models.Record_Data.NUM, models.Field.FieldName, models.Record_Data.Value).
#            join(models.Field, models.Field.FieldID==models.Record_Data.FieldID).
#            filter(models.Record_Data.LangID==LangID).
#            filter(models.Record_Data.NUM.in_([x[0] for x in results])).
#            filter(models.Field.FieldName.in_(fields)).
#            order_by(models.Record_Data.NUM)
#           ).all()
#
#        stmt = aliased(session.query(models.Record_Data).subquery())
#        located_in_data = (session.query(models.Record_Data.NUM, models.Field.FieldName, models.Record_Data.Value).
#            join(models.Field, and_(models.Field.FieldID==models.Record_Data.FieldID,
#            models.Record_Data.LangID==stmt.select(and_(stmt.c.NUM==models.Record_Data.NUM, stmt.c.FieldID==models.Record_Data.FieldID)).with_only_columns([stmt.c.LangID]).order_by(case(value=stmt.c.LangID, whens={LangID: 0}, else_=1),stmt.c.LangID).offset(0).limit(1).as_scalar())).
#            filter(models.Record_Data.NUM.in_([x[0] for x in results])).
#            filter(models.Field.FieldName=='LOCATED_IN_CM').
#            order_by(models.Record_Data.NUM)
#           ).all()
#
#
#        
#        data = name_data + located_in_data
#        data.sort(key=lambda x: x[0])
#
#        
#        name_data = {k: {x[1]:x[2] for x in v} for (k,v) in groupby(name_data, lambda x: x[0])}
        log.debug('Return')

                     
        return {'results': results}#, 'name_data': name_data}





    def _get_form_values(self):
        request = self.request
        session = request.dbsession
        user = request.user

        ViewType = user.ViewType
        LangID = request.language.LangID

        publications = session.query(models.Publication.ListID, models.Publication_Name.Name).\
                join(models.Publication.names).\
                filter(and_(
                    models.Publication_Name.LangID==LangID,
                    models.Publication.views.any(ViewType=ViewType))).\
                order_by(models.Publication_Name.Name).all()
        
        return {'quicklist': map(tuple, publications)}


