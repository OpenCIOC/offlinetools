from pyramid.httpexceptions import HTTPFound
from offlinetools import modelstate

class ViewBase(object):
    __skip_register_check__ = False

    def __init__(self, request):
        self.request = request

        request.model_state = modelstate.ModelState(request)

        if not (self.__skip_register_check__ or request.config.machine_name):
            raise HTTPFound(location=request.route_url('register'))
