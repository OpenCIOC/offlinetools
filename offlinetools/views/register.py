import urlparse
import json

from formencode import Schema
import requests

from pyramid.httpexceptions import HTTPFound
import transaction

from offlinetools import models, const, certstore
from offlinetools.views.base import ViewBase
from offlinetools.views import validators

import logging
log = logging.getLogger('offlinetools.views.register')


class RegisterSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True

    CiocSite = validators.URL(add_http=True, not_empty=True)
    LoginName = validators.UnicodeString(max=50, not_empty=True)
    LoginPwd = validators.UnicodeString(not_empty=True)

    MachineName = validators.UnicodeString(max=255, not_empty=True)
    SiteTitle = validators.UnicodeString(max=255, not_empty=True)


class UpdateUrlSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True

    CiocSite = validators.URL(add_http=True, not_empty=True)


class UrlTranslationError(Exception):
    def __init__(self, message):
        self.message = message


def translate_login_site_to_secure_url(request, login_url):
        _ = request.translate
        mapping_url = request.registry.settings.get('offlinetools.map_to_secure_url', 'https://offline-tools.cioc.ca/ot_secure_host_mapping.json')

        headers = dict(const.DEFAULT_HEADERS, Accept='application/json')
        r = requests.get(mapping_url, headers=headers, verify=certstore.certfile.name)
        try:
            r.raise_for_status()
        except Exception, e:
            log.error('unable to contact %s: %s, %s', mapping_url, r.headers['status'], e)
            raise UrlTranslationError(_('Unable to connect to CIOC servers: %s') % e)

        if r.headers['content-type'].split(';')[0] != 'application/json':
            log.error('invalid content type for %s: %s', mapping_url, r.headers['content-type'])
            raise UrlTranslationError(_('CIOC site returned unexpected response'))

        try:
            data = json.loads(r.content.decode('utf-8'))
        except ValueError, e:
            log.error('JSON parse error for %s: %s', mapping_url, e)
            log.debug(u'r.content: %s', r.content.decode('utf-8'))
            raise UrlTranslationError(_('CIOC site returned unexpected value'))

        # XXX this should be a well known https protected site that only
        # translates hostnames to a preferred sslable hostname
        parsedurl = urlparse.urlparse(login_url)

        hostname = parsedurl.hostname.lower()
        for sec_host, all_hosts in data.iteritems():
            if hostname == sec_host or hostname in all_hosts:
                break
        else:
            raise UrlTranslationError(_('Source CIOC Site is unknown'))
            return {}

        return sec_host


class Register(ViewBase):

    __skip_register_check__ = True

    def post(self):
        request = self.request
        _ = request.translate

        model_state = request.model_state
        cfg = request.config

        if cfg.machine_name:
            # maybe allow updateing info
            request.session.flash(_('Site Already Registered.'))
            return HTTPFound(location=request.route_url('search'))

        model_state.schema = RegisterSchema()

        if not model_state.validate():
            return {}

        try:
            sec_host = translate_login_site_to_secure_url(request, model_state.value('CiocSite'))
        except UrlTranslationError, e:
            model_state.add_error_for('*', e.message)
            return {}

        headers = dict(const.DEFAULT_HEADERS, Accept='application/json')
        auth = (model_state.value('LoginName').encode('utf-8'), model_state.value('LoginPwd').encode('utf-8'))
        params = {'MachineName': model_state.value('MachineName').encode('utf-8'),
                  'PublicKey': cfg.public_key.encode('utf-8')}
        url = '%s/offline/register?Ln=%s' % (sec_host, request.language.Culture)
        r = requests.post(url, data=params, headers=headers, auth=auth, verify=certstore.certfile.name)

        try:
            r.raise_for_status()
        except Exception, e:
            log.error('unable to contact %s: %s, %s', url, r.headers['status'], e)
            model_state.add_error_for('*', _('Unable to connect to Source CIOC site: %s') % e)
            return {}

        if r.headers['content-type'].split(';')[0] != 'application/json':
            log.error('invalid content type for %s: %s', url, r.headers['content-type'])
            log.debug(u'r.content: %s', r.content.decode('utf-8'))
            model_state.add_error_for('*', _('Source CIOC site returned unexpected response'))
            return {}

        try:
            data = json.loads(r.content)
        except ValueError, e:
            log.error('JSON parse error for %s: %s', url, e)
            model_state.add_error_for('*', _('CIOC site returned unexpected value'))
            return {}

        if data['fail']:
            log.error('Unable to register with source cioc site: %s', data['message'])
            model_state.add_error_for('*', _('Unable to register with Source CIOC site: %s') % data['message'])
            return {}

        # success!
        cfg.update_url = sec_host
        cfg.machine_name = model_state.value('MachineName')
        cfg.site_title = model_state.value('SiteTitle')
        request.dbsession.flush()
        transaction.commit()
        return HTTPFound(location=request.route_url('pull'))

    def get(self):
        request = self.request
        _ = request.translate
        cfg = models.get_config(request)

        if cfg.machine_name or cfg.update_url:
            # maybe allow updateing info
            request.session.flash(_('Site Already Registered.'))
            return HTTPFound(location=request.route_url('search'))

        return {}


class UpdateUrl(ViewBase):

    def post(self):
        request = self.request

        model_state = request.model_state
        cfg = request.config

        model_state.schema = UpdateUrlSchema()

        if not model_state.validate():
            return {}

        try:
            sec_host = translate_login_site_to_secure_url(request, model_state.value('CiocSite'))
        except UrlTranslationError, e:
            model_state.add_error_for('*', e.message)
            return {}

        # success!
        cfg.update_url = sec_host
        request.dbsession.flush()
        transaction.commit()
        return HTTPFound(location=request.route_url('pull'))

    def get(self):
        return {}
