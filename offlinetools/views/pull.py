from threading import Thread

from pyramid.view import view_config


from offlinetools import models
from offlinetools.views.base import ViewBase

from offlinetools import scheduler


import logging
log = logging.getLogger('offlinetools.views.pull')

initial_pull = None
initial_pull_thread = None

class Pull(ViewBase):

    #@view_config(route_name="pull", renderer="pull.mak")
    def __call__(self):
        global initial_pull,initial_pull_thread
        request = self.request
        cfg = models.get_config(request)

        if not cfg.machine_name or not cfg.update_url:
            return 'Not properly configured'

        initial_pull = scheduler.PullObject()
        initial_pull_thread = Thread(target=initial_pull.run)
        initial_pull_thread.start()

        return {}

    #@view_config(route_name="pull_status", renderer="json")
    def status_poll(self):
        global initial_pull,initial_pull_thread

        if initial_pull:

            if initial_pull.completion_code == 'ok':
                ret =  {'percent': 100, 'status': 'done'}
            else:
                ret = {'percent': int(initial_pull.status), 'status': initial_pull.completion_code}

            if initial_pull.completion_code:
                initial_pull = None
                initial_pull_thread = None

            return ret

        return {'status': 'invalid', 'percent': 0}



