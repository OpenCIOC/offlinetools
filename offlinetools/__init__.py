import os

from pyramid.config import Configurator
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from pyramid_beaker import session_factory_from_settings

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import NO_PERMISSION_REQUIRED, Authenticated, Deny, Allow, Everyone

from win32com.shell import shell, shellcon

from apscheduler.scheduler import Scheduler

from offlinetools import const
from offlinetools.models import initialize_sql, get_config
from offlinetools.request import passvars_pregen
from offlinetools.scheduler import scheduled_pull, key_to_schedule


import requests
import logging

log = logging.getLogger('offlinetools')


def groupfinder(userid, request):
    user = request.user
    if user is not None:
        log.debug('user: %s, %d', user.UserName, user.ViewType)
        return ['group:' + str(user.ViewType)]

    return None


class RootFactory(object):
    __acl__ = [(Allow, Authenticated, 'view'), (Deny, Everyone, 'view')]

    def __init__(self, request):
        try:
            if not request.config.machine_name:
                self.__acl__ = [(Allow, Everyone, 'view')]
        except OperationalError:
            log.critical('request.url: %s', request.path_qs)
            pass


def found_view(request):
    return request.context

sched = None


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    global sched

    requests.defaults.defaults['base_headers']['User-Agent'] = 'CIOC Offline Tools/%s' % const.OFFLINE_TOOLS_VERSION

    cacerts = settings.get('offlinetools.cacerts')
    if cacerts:
        from offlinetools.httpsfix import install_validating_https
        install_validating_https(os.path.abspath(cacerts))

    common_appdata_path = shell.SHGetFolderPath(0, shellcon.CSIDL_COMMON_APPDATA, 0, 0)
    app_data_dir = os.path.join(common_appdata_path, 'CIOC', 'OfflineTools')
    try:
        os.makedirs(app_data_dir)
    except os.error, e:
        log.debug('os.error: %s', e)

    engine = create_engine('sqlite:///%s\\OfflineTools.db' % app_data_dir, isolation_level='READ UNCOMMITTED')
    initialize_sql(engine)

    cfg = get_config()

    sched = Scheduler()
    sched.start()
    sched.add_cron_job(scheduled_pull, **key_to_schedule(cfg.public_key))

    session_lock_dir = os.path.join(app_data_dir, 'session')
    try:
        os.makedirs(session_lock_dir)
    except os.error, e:
        pass

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
    config.add_view('offlinetools.views.search.Search', route_name='search', attr='search',
                    permission='view', renderer='search.mak')

    config.add_route('results', '/results', pregenerator=passvars_pregen)
    config.add_view('offlinetools.views.search.Search', route_name='results', attr='results',
                    permission='view', renderer='results.mak')

    config.add_route('record', '/record/{num}', factory='offlinetools.views.record.RecordRootFactory', pregenerator=passvars_pregen)
    config.add_view('offlinetools.views.record.Record', route_name='record',
                    permission='view', renderer='record.mak')

    config.add_route('comgen', '/comgen', pregenerator=passvars_pregen)
    config.add_view('offlinetools.views.comgen.ComGen', renderer='json', route_name='comgen', permission='view')

    config.add_route('keywordgen', '/keywordgen', pregenerator=passvars_pregen)
    config.add_view('offlinetools.views.comgen.KeywordGen', renderer='json', route_name='keywordgen')

    config.add_route('login', '/login', pregenerator=passvars_pregen)
    config.add_view('offlinetools.views.login.Login', renderer='login.mak', route_name='login',
                    request_method='POST', attr='post', permission=NO_PERMISSION_REQUIRED)
    config.add_view('offlinetools.views.login.Login', renderer='login.mak', route_name='login',
                    attr='get', permission=NO_PERMISSION_REQUIRED)
    config.add_view('offlinetools.views.login.Login', renderer='login.mak',
                    context='pyramid.httpexceptions.HTTPForbidden',
                    attr='get', permission=NO_PERMISSION_REQUIRED)

    config.add_route('logout', '/logout', pregenerator=passvars_pregen)
    config.add_view('offlinetools.views.login.logout', route_name='logout', permission=NO_PERMISSION_REQUIRED)

    config.add_route('register', '/register', pregenerator=passvars_pregen)
    config.add_view('offlinetools.views.register.Register', route_name='register', request_method='POST',
                    attr='post', renderer='register.mak', permission=NO_PERMISSION_REQUIRED)
    config.add_view('offlinetools.views.register.Register', route_name='register',
                    attr='get', renderer='register.mak', permission=NO_PERMISSION_REQUIRED)

    config.add_route('updateconfig', '/config', pregenerator=passvars_pregen)
    config.add_view('offlinetools.views.register.UpdateUrl', route_name='updateconfig', request_method='POST',
                    attr='post', renderer='updateurl.mak', permission=NO_PERMISSION_REQUIRED)
    config.add_view('offlinetools.views.register.UpdateUrl', route_name='updateconfig',
                    attr='get', renderer='updateurl.mak', permission=NO_PERMISSION_REQUIRED)

    config.add_route('pull', '/pull', pregenerator=passvars_pregen)
    config.add_view('offlinetools.views.pull.Pull', route_name='pull', renderer='pull.mak')

    config.add_route('pull_status', '/pullstatus', pregenerator=passvars_pregen, factory='pyramid.traversal.DefaultRootFactory')
    config.add_view('offlinetools.views.pull.PullStatus', route_name='pull_status', renderer='json', permission=NO_PERMISSION_REQUIRED)

    config.add_route('status', '/status', factory='offlinetools.views.status.StatusRootFactory', pregenerator=passvars_pregen)
    config.add_view('offlinetools.views.status.Status', route_name='status',
                    renderer='status.mak', permission='view')

    config.add_subscriber('offlinetools.subscribers.add_renderer_globals',
                      'pyramid.events.BeforeRender')

    config.scan()
    return config.make_wsgi_app()
