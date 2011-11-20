from itertools import groupby
from operator import itemgetter

from pyramid.security import Allow, Deny, Everyone
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound

from sqlalchemy import and_

from offlinetools import models
from offlinetools.views.base import ViewBase

import logging
log = logging.getLogger('offlinetools.views.record')

class RecordRootFactory(object):

    def __init__(self, request):
        self.request = request

        session = request.dbsession
        
        LangID = request.language.LangID
        num = request.matchdict['num']

        views = session.query(models.View).filter(models.View.records.any(and_(models.Record.NUM==num, models.Record.LangID==LangID))).all()

        if not views:
            raise HTTPNotFound()

        self.__acl__ = [(Allow, 'group:' + str(v.ViewType), 'view') for v in views]
        self.__acl__.append((Deny, Everyone, 'view'))

        log.debug('__acl__: %s', self.__acl__)
        if request.user:
            log.debug('user: %s, %d', request.user.UserName, request.user.ViewType)


@view_config(route_name='record', permission='view', renderer='record.mak')
class Record(ViewBase):
    def __call__(self):
        request = self.request

        user = request.user
        session = request.dbsession
        LangID = request.language.LangID
        num = request.matchdict['num']

        field_groups = session.query(models.FieldGroup.DisplayFieldGroupID,models.FieldGroup_Name.Name).\
                join(models.FieldGroup.names).\
                filter(and_(
                    models.FieldGroup_Name.LangID==LangID,
                    models.FieldGroup.ViewType==user.ViewType)).\
                order_by(models.FieldGroup.DisplayOrder, models.FieldGroup_Name.Name).all()


        fields = session.query(models.FieldGroup.DisplayFieldGroupID, models.Field.FieldID, models.Field_Name.Name).\
                join(models.Field.names).\
                filter(models.Field_Name.LangID==LangID).\
                join(models.Field.groups).\
                join(models.Record_Data, and_(models.Field_Name.FieldID==models.Record_Data.FieldID,
                                              models.Field_Name.LangID==models.Record_Data.LangID)).\
                filter(and_(models.Record_Data.NUM==num, models.FieldGroup.ViewType==user.ViewType)).\
                order_by(models.FieldGroup.DisplayFieldGroupID, models.Field.DisplayOrder, models.Field_Name.Name).\
                all()

        fields = {k: list(v) for k,v in groupby(fields, itemgetter(0))}


        record_data = (session.query(models.Record_Data.FieldID,models.Record_Data.Value,models.Field.FieldName).
                join(models.Field, models.Record_Data.FieldID==models.Field.FieldID).
                filter(and_(models.Record_Data.NUM==num, models.Record_Data.LangID==LangID)).all())

        core_fields = set('ORG_LEVEL_%d' % i for i in range(1,6))
        core_fields.update(['NON_PUBLIC', 'UPDATE_DATE'])
        core_data = {x.FieldName: x.Value for x in record_data if x.FieldName in core_fields}
        record_data = {x.FieldID: x for x in record_data}



        return {'num': num, 'field_groups':field_groups, 'fields': fields, 'record_data': record_data, 'core_data': core_data}


