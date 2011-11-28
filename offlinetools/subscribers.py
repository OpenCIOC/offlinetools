# =================================================================
# Copyright (C) 2011 Community Information Online Consortium (CIOC)
# http://www.cioc.ca
# Developed By Katherine Lambacher / KCL Custom Software
# If you did not receive a copy of the license agreement with this
# software, please contact CIOC via their website above.
#==================================================================

import re, logging
log = logging.getLogger('offlinetools.subscribers')

from markupsafe import Markup, escape

not_html_re = re.compile(r'(<br>)|(<p>)|(<a\s+href)|(<b>)|(<strong>)|(<i>)|(<em>)|(<li>)|(<img\s+)|(<table\s+)|(&nbsp;)|(&amp;)|(h[1-6]>)|(<span[\s>])|(<div[\s>])')
no_break_html_re = re.compile(r'(<br>)|(<p>)')

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
    event['renderer'] = getattr(getattr(request,'model_state',None),'renderer', None)
    event['textToHTML'] = textToHTML

    site_title = request.config.site_title

    if site_title:
        event['site_title'] = _(' for ') + site_title

    else:
        event['site_title'] = ''

