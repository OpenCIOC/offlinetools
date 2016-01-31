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
import re

from formencode import validators

MAX_ID = 2147483647

_ = lambda x: x


class UnicodeString(validators.UnicodeString):
	trim = True
	if_empty = None


class String(validators.String):
	trim = True
	if_empty = None


class IntID(validators.Int):
	if_empty = None
	min = 1
	max = MAX_ID


class Email(validators.Email):
	trim = True
	if_empty = None

	# update re from dev version of Formencode
	usernameRE = re.compile(r"^[\w!#$%&'*+\-/=?^`{|}~.]+$")
	domainRE = re.compile(r'''
		^(?:[a-z0-9][a-z0-9\-]{,62}\.)+ # (sub)domain - alpha followed by 62max chars (63 total)
		[a-z]{2,}$						 # TLD
	''', re.I | re.VERBOSE)


class AgencyCode(validators.Regex):
	strip = True
	regex = '^[A-Z][A-Z][A-Z]$'
	messages = {'invalid': _("Invalid Agency Code")}


DateConverter = validators.DateConverter
FieldsMatch = validators.FieldsMatch
MaxLength = validators.MaxLength
Int = validators.Int
Bool = validators.Bool
StringBool = validators.StringBool
Invalid = validators.Invalid
URL = validators.URL
