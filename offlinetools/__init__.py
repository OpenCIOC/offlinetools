import os

from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid_beaker import session_factory_from_settings

from offlinetools.models import initialize_sql
from offlinetools.request import passvars_pregen

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import NO_PERMISSION_REQUIRED, Authenticated, Deny, Allow, Everyone

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

    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)

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

    config.add_route('home', '/', pregenerator=passvars_pregen)

    config.add_route('record', '/record/{num}', factory='offlinetools.views.record.RecordRootFactory', pregenerator=passvars_pregen)

    config.add_route('login', '/login', pregenerator=passvars_pregen)
    config.add_route('logout', '/logout', pregenerator=passvars_pregen)

    config.add_route('register', '/register', pregenerator=passvars_pregen)
    config.add_route('pull', '/pull', pregenerator=passvars_pregen)

    config.add_subscriber('offlinetools.subscribers.add_renderer_globals',
                      'pyramid.events.BeforeRender')

    config.scan()
    return config.make_wsgi_app()

