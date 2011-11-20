import os

from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid_beaker import session_factory_from_settings

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import NO_PERMISSION_REQUIRED, Authenticated, Deny, Allow, Everyone

from win32com.shell import shell, shellcon

from offlinetools.models import initialize_sql
from offlinetools.request import passvars_pregen



import requests

__version__ = '0.1'

import logging 

log = logging.getLogger('offlinetools')

def groupfinder(userid, request):
    user = request.user
    if user is not None:
        log.debug('user: %s, %d', user.UserName, user.ViewType)
        return [ 'group:' + str(user.ViewType) ]

    return None

class RootFactory(object):
    __acl__ = [(Allow, Authenticated, 'view'), (Deny, Everyone, 'view')]

    def __init__(self, request):
        pass


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    requests.defaults.defaults['base_headers']['User-Agent'] = 'CIOC Offline Tools/%s' % __version__

    cacerts = settings.get('offlinetools.cacerts')
    if cacerts:
        from offlinetools.httpsfix import install_validating_https
        install_validating_https(os.path.abspath(cacerts))

    common_appdata_path =  shell.SHGetFolderPath (0, shellcon.CSIDL_COMMON_APPDATA, 0, 0)
    app_data_dir = os.path.join(common_appdata_path, 'CIOC', 'OfflineTools')
    try:
        os.makedirs(app_data_dir)
    except os.error, e:
        log.debug('os.error: %s', e)

    sa_config = {'sqlalchemy.url': 'sqlite:///%s\\OfflineTools.db' % app_data_dir}
    engine = engine_from_config(sa_config, 'sqlalchemy.')
    initialize_sql(engine)

    session_lock_dir = os.path.join(app_data_dir, 'session')
    try:
        os.makedirs(session_lock_dir)
    except os.error, e:
        log.debug('os.error: %s', e)
    settings['beaker.session.lock_dir'] = session_lock_dir
    session_factory = session_factory_from_settings(settings)

    authn_policy = SessionAuthenticationPolicy(callback=groupfinder, debug=True)
    authz_policy = ACLAuthorizationPolicy()
    config = Configurator(settings=settings, session_factory=session_factory,
                          root_factory=RootFactory,
                          request_factory='offlinetools.request.OfflineToolsRequest',
                         authentication_policy=authn_policy,
                         authorization_policy=authz_policy)
    config.add_translation_dirs('offlinetools:locale')
    config.add_static_view('static', 'offlinetools:static', cache_max_age=3600, permission=NO_PERMISSION_REQUIRED)

    config.add_route('search', '/', pregenerator=passvars_pregen)
    config.add_route('results', '/results', pregenerator=passvars_pregen)

    config.add_route('record', '/record/{num}', factory='offlinetools.views.record.RecordRootFactory', pregenerator=passvars_pregen)
    config.add_route('comgen', '/comgen', pregenerator=passvars_pregen)

    config.add_route('login', '/login', pregenerator=passvars_pregen)
    config.add_route('logout', '/logout', pregenerator=passvars_pregen)

    config.add_route('register', '/register', pregenerator=passvars_pregen)
    config.add_route('pull', '/pull', pregenerator=passvars_pregen)

    config.add_subscriber('offlinetools.subscribers.add_renderer_globals',
                      'pyramid.events.BeforeRender')

    config.scan()
    return config.make_wsgi_app()

