# ======================================================================================
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
import logging
log = logging.getLogger('offlinetools.subscribers')

from markupsafe import Markup, escape

not_html_re = re.compile(r'(<br>)|(<p>)|(<a\s+href)|(<b>)|(<strong>)|(<i>)|(<em>)|(<li>)|(<img\s+)|(<table\s+)|(&nbsp;)|(&amp;)|(h[1-6]>)|(<span[\s>])|(<div[\s>])', re.I)
no_break_html_re = re.compile(r'(<br>)|(<p>)', re.I)

br_markup = Markup('&nbsp;<br>')
crlf_markup = Markup('\r\n')
lf_markup = Markup('\n')
cr_markup = Markup('\r')


def textToHTML(text):
    if text:
        if not not_html_re.search(text):
            return escape(text).replace(crlf_markup, br_markup).replace(lf_markup, br_markup).replace(cr_markup, br_markup)
        if not no_break_html_re.search(text):
            return Markup(text).replace(crlf_markup, br_markup).replace(lf_markup, br_markup).replace(cr_markup, br_markup)
        return Markup(text)

    return ''


def add_renderer_globals(event):
    request = event['request']
    if not request:
        return

    log.debug('renderer_name: %s', event['renderer_name'])
    if event['renderer_name'] == 'json' or event['renderer_name'].startswith('pyramid'):
        return

    _ = event['_'] = request.translate
    event['localizer'] = request.localizer
    event['renderer'] = getattr(getattr(request, 'model_state', None), 'renderer', None)
    event['textToHTML'] = textToHTML

    site_title = request.config.site_title

    if site_title:
        event['site_title'] = _(' for ') + site_title

    else:
        event['site_title'] = ''
