from datetime import time

from offlinetools import models
from offlinetools.views.base import ViewBase
from offlinetools.scheduler import key_to_schedule

import logging
log = logging.getLogger('offlinetools.views.status')

initial_pull = None
initial_pull_thread = None

class Status(ViewBase):

    def __call__(self):
        global initial_pull,initial_pull_thread
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




