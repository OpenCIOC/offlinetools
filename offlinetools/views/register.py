import urlparse, json

from formencode import Schema
import requests

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
import transaction

from offlinetools import models
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



class Register(ViewBase):

    __skip_register_check__ = True
    
    #@view_config(route_name="register", request_method="POST", renderer='register.mak')
    def post(self):
        request = self.request
        _ = request.translate

        model_state = request.model_state
        cfg = request.config


        if cfg.machine_name:
            #maybe allow updateing info
            request.session.flash(_('Site Already Registered.'))
            return HTTPFound(location=request.route_url('search'))

        model_state.schema = RegisterSchema()

        if not model_state.validate():
            return {}

        mapping_url = request.registry.settings.get('offlinetools.map_to_secure_url', 'https://www.cioc.ca/ot_secure_host_mapping.json')

        headers = {'Accept': 'application/json'}
        r = requests.get(mapping_url, headers=headers)
        try:
            r.raise_for_status()
        except Exception, e:
            log.error('unable to contact %s: %s, %s', mapping_url, r.headers['status'], e)
            model_state.add_error_for('*', _('Unable to connect to CIOC servers: %s') % e)
            return {}

        if r.headers['content-type'].split(';')[0] != 'application/json':
            log.error('invalid content type for %s: %s', mapping_url, r.headers['content-type'])
            model_state.add_error_for('*', _('CIOC site returned unexpected response'))
            return {}

        try:
            data = json.loads(r.content.decode('utf-8'))
        except ValueError, e:
            log.error('JSON parse error for %s: %s', mapping_url, e)
            log.debug(u'r.content: %s', r.content.decode('utf-8'))
            model_state.add_error_for('*', _('CIOC site returned unexpected value'))
            return {}


        # XXX this should be a well known https protected site that only
        # translates hostnames to a preferred sslable hostname
        parsedurl = urlparse.urlparse(model_state.value('CiocSite'))

        hostname = parsedurl.hostname.lower()
        for sec_host, all_hosts in data.iteritems():
            if hostname == sec_host or hostname in all_hosts:
                break;
        else:
            model_state.add_error_for('*', _('Source CIOC Site is unknown'))
            return {}

        
        auth = (model_state.value('LoginName').encode('utf-8'), model_state.value('LoginPwd').encode('utf-8'))
        params = {'MachineName': model_state.value('MachineName').encode('utf-8'),
                  'PublicKey': cfg.public_key.encode('utf-8')}
        url = '%s/offline/register?Ln=%s' % (sec_host, request.language.Culture)
        r = requests.post(url, data=params, headers=headers, auth=auth)

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


    #@view_config(route_name="register", renderer="register.mak")
    def get(self):
        request = self.request
        _ = request.translate
        cfg = models.get_config(request)

        if cfg.machine_name or cfg.update_url:
            #maybe allow updateing info
            request.session.flash(_('Site Already Registered.'))
            return HTTPFound(location=request.route_url('search'))


        return {}

