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
from pyramid.httpexceptions import HTTPFound
from offlinetools import modelstate


class ViewBase(object):
    __skip_register_check__ = False

    def __init__(self, request):
        if not (self.__skip_register_check__ or request.config.machine_name):
            raise HTTPFound(location=request.route_url('register'))

        self.request = request

        request.model_state = modelstate.ModelState(request)
