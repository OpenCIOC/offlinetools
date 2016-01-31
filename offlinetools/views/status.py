# =========================================================================================
#  Copyright 2016 Community Information Online Consortium (CIOC) and KCL Software Solutions
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# =========================================================================================

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

        schedule = key_to_schedule(cfg.public_key)

        _ = request.translate
        schedule = _(' @ ').join([_(schedule['day_of_week']),
                                  request.format_time(time(*[schedule[x] for x in ['hour', 'minute', 'second']]))])

        return {'config': cfg, 'schedule': schedule}
