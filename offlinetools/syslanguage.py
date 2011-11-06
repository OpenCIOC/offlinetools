# =================================================================
# Copyright (C) 2011 Community Information Online Consortium (CIOC)
# http://www.cioc.ca
# Developed By Katherine Lambacher / KCL Custom Software
# If you did not receive a copy of the license agreement with this
# software, please contact CIOC via their website above.
#==================================================================

from collections import namedtuple
from operator import attrgetter

from pyramid.decorator import reify 

#System Language Constants
LANG_ENGLISH = 0
LANG_FRENCH = 2

#SQL Server Language Alias Constants
SQLALIAS_ENGLISH = u"English"
SQLALIAS_FRENCH = u"French"

CULTURE_ENGLISH_CANADIAN = u"en-CA"
CULTURE_FRENCH_CANADIAN = u"fr-CA"
CULTURE_GERMAN = u"de"
CULTURE_SPANISH = u"es-MX"
CULTURE_CHINESE_SIMPLIFIED = u"zh-CN"

def default_culture():
	return active_cultures()[0]

def is_active_culture(culture):
	try:
		return _culture_map[culture].Active
	except KeyError:
		return False

def active_cultures():
	return [x.Culture for x in sorted(_culture_list, key=attrgetter('LanguageName')) if x.Active]

def active_record_cultures():
	return [x.Culture for x in sorted(_culture_list, key=lambda x: (not x.Active, x.LanguageName)) if x.ActiveRecord]

def culture_map():
	return _culture_map.copy()

_culture_fields = 'Culture LanguageName LangID Active ActiveRecord'
_culture_field_list = _culture_fields.split()
CultureDescriptionBase = namedtuple('CultureDescriptionBase', _culture_fields)
class CultureDescription(CultureDescriptionBase):
	slots = ('FormCulture',)

	@reify
	def FormCulture(self):
		return self.Culture.replace('-', '_')

#global value will be updated by running app
_culture_list = [
	CultureDescription(
			Culture=CULTURE_ENGLISH_CANADIAN,
			LanguageName=u'English', 
			LangID=LANG_ENGLISH, 
			Active=True,
			ActiveRecord=True
	),
	CultureDescription(
			Culture=CULTURE_FRENCH_CANADIAN,
			LanguageName=u'Français', 
			LangID=LANG_FRENCH, 
			Active=True,
			ActiveRecord=True
	)
]
_culture_map = {}
def update_culture_map():
	global _culture_map

	_culture_map = dict((x.Culture, x) for x in _culture_list)

update_culture_map()

def update_cultures(cultures):
	global _culture_list
	_culture_list = [CultureDescription(**x) for x in cultures]
	update_culture_map()

class SystemLanguage(object):
	def __init__(self):
		self.setSystemLanguage(default_culture())

	def setSystemLanguage(self, culture):
		try:
			self.description = _culture_map[culture]
		except KeyError:
			self.description = _culture_map[CULTURE_ENGLISH_CANADIAN]._replace(Active=True)

	def __getattr__(self, key):
		""" convenience access to attributes of self.description

		>>> a = SystemLanguage()
		>>> a.description.LanuageName = a.LanguageName
		True
		>>> 
		"""
		return getattr(self.description, key)
pass
