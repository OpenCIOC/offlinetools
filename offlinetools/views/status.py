from __future__ import absolute_import
from datetime import time

from sqlalchemy import func
from pyramid.security import Authenticated, Deny, Allow, Everyone

from offlinetools import models
from offlinetools.views.base import ViewBase
from offlinetools.scheduler import key_to_schedule

import logging
log = logging.getLogger('offlinetools.views.status')

initial_pull = None
initial_pull_thread = None


class StatusRootFactory(object):
    __acl__ = [(Allow, Authenticated, 'view'), (Deny, Everyone, 'view')]

    def __init__(self, request):
        session = request.dbsession
        user_count = session.query(func.count(models.Users.UserName), func.count(models.Record.NUM)).one()

        has_data = request.database_has_data = any(user_count)
        if not has_data:
            self.__acl__ = [(Allow, Everyone, 'view')]


class Status(ViewBase):

    def __call__(self):
        global initial_pull, initial_pull_thread
        request = self.request
        cfg = request.config

        #session = request.dbsession
        #LangID = request.language.LangID

        #sql = '''
        #SELECT vwn.Name
        #    FROM View AS vw
        #    INNER JOIN View_Name AS vwn
        #        ON vw.ViewType=vwn.ViewType AND vwn.LangID=(SELECT LangID FROM View_Name WHERE ViewType=vwn.ViewType ORDER BY CASE WHEN LangID=? THEN 0 ELSE 1 END, LangID LIMIT 1)
        #ORDER BY vwn.Name
        #    '''

        #connection = session.connection()
        #views = connection.execute(sql, LangID).fetchall()
        schedule = key_to_schedule(cfg.public_key)

        _ = request.translate
        schedule = _(' @ ').join([_(schedule['day_of_week']),
                                  request.format_time(time(*[schedule[x] for x in ['hour', 'minute', 'second']]))])

        return {'config': cfg, 'schedule': schedule}
