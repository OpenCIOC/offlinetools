from pyramid.request import Request
from pyramid.decorator import reify
from pyramid.i18n import get_localizer, TranslationStringFactory
from pyramid.security import unauthenticated_userid

from offlinetools.models import DBSession, Users, get_config

from offlinetools.syslanguage import SystemLanguage, default_culture, is_active_culture

class OfflineToolsRequest(Request):
    def form_args(self, ln=None):
        if not ln:
            ln = self.language.Culture

        extra_args = []
        if ln and ln != self.default_culture:
            extra_args.append(('Ln', ln))

        return extra_args



    @reify
    def default_form_args(self):
        return self.form_args()


    @reify
    def _LOCALE_(self):
        return self.language.Culture.replace('-', '_')


    @reify
    def language(self):
        language = SystemLanguage()

        ln = self.params.get('Ln')
        if ln and is_active_culture(ln): 
            language.setSystemLanguage(ln)

        return language


    @reify
    def default_culture(self):
        return default_culture()

    @reify
    def translate(self):
        if not hasattr(self,'localizer'):
            self.localizer = get_localizer(self)

        localizer = self.localizer
        def auto_translate(string):
            return localizer.translate(tsf(string))

        return auto_translate

    @reify
    def user(self):
        # <your database connection, however you get it, the below line
        # is just an example>
        dbsession = self.dbsession
        userid = unauthenticated_userid(self)
        if userid is not None:
            # this should return None if the user doesn't exist
            # in the database
            user = dbsession.query(Users).filter_by(UserName=userid).first()
            return user

        return None

    @reify
    def dbsession(self):
        return DBSession()

    @reify
    def config(self):
        return get_config(self)


tsf = TranslationStringFactory('offlinetools')

def passvars_pregen(request, elements, kw):
    query = kw.get('_query')
    ln = kw.pop('_ln', None)
    form = kw.pop('_form', None)

    if not form and not ln:
        ln = request.language.Culture

    extra_args = []
    if ln and ln != request.default_culture:
        extra_args.append(('Ln', ln))

    if extra_args:
        if not query:
            query = []

        elif isinstance(query, dict):
            query = query.items()

        else:
            query = list(query)

        query.extend(extra_args)
        kw['_query'] = query

    return elements, kw
