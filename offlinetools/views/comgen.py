
from offlinetools.views.base import ViewBase
from offlinetools.views.validators import UnicodeString, Invalid

#@view_config(route_name="comgen", renderer='json')
class ComGen(ViewBase):
    def __call__(self):
        request = self.request

        validator = UnicodeString(not_empty=True)
        try:
            search = validator.to_python(request.params.get('term'))
        except Invalid:
            return []


        session = request.dbsession
        LangID = request.language.LangID

        sql = '''
            SELECT cm.CM_ID, cmn.Name AS Community, cpn.Name AS ParentCommunity
                FROM Community AS cm
                INNER JOIN Community_Name AS cmn
                    ON cm.CM_ID=cmn.CM_ID AND cmn.LangID=(SELECT LangID FROM Community_Name WHERE CM_ID=cmn.CM_ID ORDER BY CASE WHEN LangID=? THEN 0 ELSE 1 END, LangID LIMIT 1)
                LEFT JOIN Community_Name AS cpn
                    ON cm.ParentCommunity=cpn.CM_ID AND cpn.LangID=(SELECT LangID FROM Community_Name WHERE CM_ID=cpn.CM_ID ORDER BY CASE WHEN LangID=? THEN 0 ELSE 1 END, LangID LIMIT 1)


            WHERE cmn.Name LIKE ?
            ORDER BY Community
            '''

        connection = session.connection()
        results = connection.execute(sql, LangID, LangID, '%{0}%'.format(search)).fetchall()

        _ = request.translate

        return [{'chkid': x.CM_ID, 'value': x.Community, 
                 'label': _('%s (in %s)') % (x.Community, x.ParentCommunity) if x.ParentCommunity else x.Community}
                 for x in results]

        


class KeywordGen(ViewBase):
    def __call__(self):
        request = self.request

        validator = UnicodeString(not_empty=True)
        try:
            search = validator.to_python(request.params.get('term'))
        except Invalid:
            return []


        session = request.dbsession
        LangID = request.language.LangID

        sql = '''
            SELECT Value
                FROM KeywordCache

            WHERE LangID=? AND Value LIKE ?
            ORDER BY Value
            '''

        connection = session.connection()
        results = connection.execute(sql, LangID, '%{0}%'.format(search)).fetchall()

        return [{'value': x.Value} for x in results]





