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
from hashlib import pbkdf2_hmac
from base64 import standard_b64encode

from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember, forget

from formencode import Schema
from sqlalchemy import func

from offlinetools import models
from offlinetools.views.base import ViewBase
from offlinetools.views import validators
from offlinetools.syslanguage import _culture_list, default_culture

DEFAULT_REPEAT = 100000


class LoginSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True

    LoginName = validators.UnicodeString(max=50, not_empty=True)
    LoginPwd = validators.String(not_empty=True)

    came_from = validators.UnicodeString()


class Login(ViewBase):
    def post(self):
        request = self.request
        _ = request.translate

        model_state = request.model_state
        model_state.schema = LoginSchema()

        if not model_state.validate():
            return self._get_edit_info()

        LoginName = model_state.value('LoginName')
        user = request.dbsession.query(models.Users).filter_by(UserName=LoginName).first()
        if not user:
            model_state.add_error_for('*', _('Invalid User Name or Password'))
            return self._get_edit_info()

        hash = Crypt(user.PasswordHashSalt, model_state.value('LoginPwd'), user.PasswordHashRepeat)
        if hash != user.PasswordHash:
            model_state.add_error_for('*', _('Invalid User Name or Password'))
            return self._get_edit_info()

        headers = remember(request, user.UserName)
        start_ln = [x.Culture for x in _culture_list if x.LangID == user.LangID and x.Active]
        if not start_ln:
            start_ln = [default_culture()]

        return HTTPFound(location=model_state.value('came_from', request.route_url('search', ln=start_ln[0])),
                         headers=headers)

    def get(self):
        request = self.request
        login_url = request.route_url('login')
        referrer = request.url
        if referrer == login_url:
            referrer = request.route_url('search')  # never use the login form itself as came_from
        came_from = request.params.get('came_from', referrer)

        request.model_state.data['came_from'] = came_from

        return self._get_edit_info()

    def _get_edit_info(self):
        request = self.request
        session = request.dbsession
        user_count = session.query(func.count(models.Users.UserName), func.count(models.Record.NUM)).one()

        has_data = any(user_count)
        failed_updates = False
        has_updated = True
        if not has_data:
            config = request.config
            failed_updates = not not config.update_failure_count

            has_updated = not not config.last_update

        return {'has_data': has_data, 'failed_updates': failed_updates, 'has_updated': has_updated}


def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.route_url('login'),
                     headers=headers)


def Crypt(salt, password, repeat=DEFAULT_REPEAT):
    return standard_b64encode(pbkdf2_hmac('sha1', password.encode('utf-8'), salt.encode('utf-8'), repeat, 33)).decode('utf-8').strip()
