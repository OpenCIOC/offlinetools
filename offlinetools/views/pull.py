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
from threading import Thread

from offlinetools import models
from offlinetools.views.base import ViewBase

from offlinetools import scheduler


import logging
log = logging.getLogger('offlinetools.views.pull')

initial_pull = None
initial_pull_thread = None


class Pull(ViewBase):

    def __call__(self):
        global initial_pull, initial_pull_thread
        request = self.request
        cfg = models.get_config(request)

        _ = request.translate

        if not cfg.machine_name or not cfg.update_url:
            # XXX handled by other tools
            return _('Not properly configured')

        if initial_pull:
            return _('Pull already in progress.')

        initial_pull = scheduler.PullObject(force=request.params.get('force'))
        initial_pull_thread = Thread(target=initial_pull.run)
        initial_pull_thread.start()

        return {}


class PullStatus(ViewBase):
    __skip_register_check__ = True

    def __call__(self):
        global initial_pull, initial_pull_thread

        if initial_pull:

            if initial_pull.completion_code == 'ok':
                ret = {'percent': 100, 'status': 'done'}
            else:
                ret = {'percent': int(initial_pull.status), 'status': initial_pull.completion_code}

            if initial_pull.completion_code:
                initial_pull = None
                initial_pull_thread = None

            return ret

        return {'status': 'invalid', 'percent': 0}
