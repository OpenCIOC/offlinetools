from datetime import time
import re

from formencode import Schema
from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import case, collate

from offlinetools import models
from offlinetools.views.base import ViewBase
from offlinetools.views import validators
from offlinetools.scheduler import key_to_schedule


import logging
log = logging.getLogger('offlinetools.views.search')


class SearchSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True

    if_key_missing = None

    Terms = validators.UnicodeString(max=255)
    QuickList = validators.UnicodeString(max=50)
    Community = validators.UnicodeString(max=255)
    LocatedIn = validators.StringBool()


def process_search_text_value(val):
    val = val.replace('\\', '\\\\')
    val = val.replace('%', '\\%')
    val = val.replace('_', '\\_')

    return val

_terms_re = re.compile(r'''( |\".*?\"|'.*?')''')


class Search(ViewBase):
    def search(self):
        return self._get_form_values()

    def results(self):
        request = self.request

        model_state = request.model_state
        model_state.schema = SearchSchema()
        model_state.method = None

        if not model_state.validate():
            request.override_renderer = 'search.mak'
            log.debug('errors: %s', model_state.form.errors)
            return self._get_form_values()

        LangID = request.language.LangID
        ViewType = request.user.ViewType
        session = request.dbsession

        filters = [models.Record.LangID == LangID]

        if model_state.value('Terms'):
            strip_chars = ' \t\r\n\'"'
            terms = (process_search_text_value(p.strip(strip_chars)) for p in _terms_re.split(model_state.value('Terms')) if p.strip(strip_chars))
            conditions = (models.Record.fields.any(models.Record_Data.Value.like('%{0}%'.format(p), escape='\\')) for p in terms)
            filters.extend(conditions)

        community = model_state.value('Community')
        if community:
            row = session.query(models.Community_Name.CM_ID, models.Community.ParentCommunity).join(models.Community, models.Community.CM_ID == models.Community_Name.CM_ID).filter(models.Community_Name.Name.like(community)).order_by(case(value=models.Community_Name.LangID, whens={LangID: 0}, else_=1), models.Community_Name.LangID).first()
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
                    Parent = session.query(models.Community.ParentCommunity).filter(models.Community.CM_ID == Parent).first()  # there should be only one
                    if Parent:
                        Parent = Parent[0]
                else:
                    CM_IDS.add(Parent)

                log.debug('Communities: %s', session.query(models.Community.CM_ID, models.Community.ParentCommunity, models.Community_Name.Name).join(models.Community_Name).filter(models.Community_Name.LangID == 0).filter(models.Community.CM_ID.in_(CM_IDS)).all())

                if model_state.value('LocatedIn'):
                    filters.append(or_(models.Record.LOCATED_IN_CM == None, models.Record.LOCATED_IN_CM.in_(CM_IDS)))  # noqa
                else:
                    filters.append(models.Record.communities.any(models.Community.CM_ID.in_(CM_IDS)))

        quick_list = model_state.value('QuickList')
        if quick_list:
            filters.append(models.Record.publications.any(models.Publication.ListID == quick_list))

        stmt = (session.query(models.Record.NUM, models.Record.LOCATED_IN_Cache, models.Record.OrgName_Cache).
                join(models.Record_Views, and_(models.Record_Views.c.NUM == models.Record.NUM, models.Record_Views.c.ViewType == ViewType)))

        results = stmt.filter(and_(*filters)).order_by(collate(models.Record.OrgName_Cache, 'NOCASE'), models.Record.NUM).all()

        log.debug('Return')

        return {'results': results}

    def _get_form_values(self):
        request = self.request
        session = request.dbsession
        user = request.user

        ViewType = user.ViewType
        LangID = request.language.LangID

        publications = session.query(models.Publication.ListID, models.Publication_Name.Name).\
            join(models.Publication.names).\
            filter(and_(
                models.Publication_Name.LangID == LangID,
                models.Publication.views.any(ViewType=ViewType))).\
            order_by(models.Publication_Name.Name).all()

        cfg = request.config

        schedule = key_to_schedule(cfg.public_key)

        _ = request.translate
        schedule = _(' @ ').join([_(schedule['day_of_week']),
                                  request.format_time(time(*[schedule[x] for x in ['hour', 'minute', 'second']]))])

        return {'quicklist': map(tuple, publications), 'config': cfg, 'schedule': schedule}
