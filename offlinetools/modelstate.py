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
from markupsafe import Markup
from webhelpers2.html import tags
from webhelpers2.html.builder import HTML, literal

from pyramid_simpleform import Form
from pyramid_simpleform.renderers import FormRenderer

from offlinetools import const

import logging
import six
log = logging.getLogger('offlinetools.modelstate')


class DefaultModel(object):
    pass

_split_re = re.compile(r'((?:-\d+)?\.)')


def split(value):
    retval = _split_re.split(value, 1)

    return retval + ([''] * (3 - len(retval)))


def traverse_object_for_value(obj, name, is_array=False):
    try:
        return obj[name]
    except (KeyError, TypeError, IndexError):
        if is_array:
            raise

        try:
            return getattr(obj, name)
        except (AttributeError, TypeError):
            head, sep, tail = split(name)
            if head == name:
                raise KeyError

            newobj = traverse_object_for_value(obj, head)

            # array
            if sep[0] == '-':
                newobj = traverse_object_for_value(newobj, int(sep[1:-1], 10), is_array=True)

            return traverse_object_for_value(newobj, tail)


class CiocFormRenderer(FormRenderer):
    def value(self, name, default=None):
        try:
            return traverse_object_for_value(self.form.data, name)
        except (KeyError, AttributeError, IndexError):
            return default

    def radio(self, name, value=None, checked=False, label=None, **attrs):
        """
        Outputs radio input.
        """
        try:
            checked = six.text_type(traverse_object_for_value(self.form.data, name)) == six.text_type(value)
        except (KeyError, AttributeError):
            pass

        return tags.radio(name, value, checked, label, **attrs)

    def checkbox(self, name, value='1', checked=False, label=None, id=None, **attrs):
        return tags.checkbox(name, value, self.value(name) or checked,
            label, id or name, **attrs)

    def ms_checkbox(self, name, value=None, checked=False, label=None, id=None, **attrs):
        """
        Outputs checkbox in radio style (i.e. multi select)
        """
        checked = six.text_type(value) in self.value(name, []) or checked
        id = id or ('_'.join((name, six.text_type(value))))
        return tags.checkbox(name, value, checked, label, id, **attrs)

    def label(self, name, label=None, **attrs):
        """
        Outputs a <label> element.

        `name`  : field name. Automatically added to "for" attribute.

        `label` : if **None**, uses the capitalized field name.
        """
        if 'for_' not in attrs:
            attrs['for_'] = name

        # attrs['for_'] = tags._make_safe_id_component(attrs['for_'])
        label = label or name.capitalize()
        return HTML.tag("label", label, **attrs)

    def text(self, name, value=None, id=None, **attrs):
        kw = {'maxlength': 200, 'class_': 'text'}
        kw.update(attrs)
        return FormRenderer.text(self, name, value, id, **kw)

    def url(self, name, value=None, id=None, **attrs):
        kw = {'type': 'text', 'maxlength': 150, 'class_': 'url'}
        kw.update(attrs)
        value = self.value(name, value)
        if value and value.startswith('http://'):
            value = value[len('http://'):]
        return literal(u'http://') + tags.text(name, value, id, **kw)

    def email(self, name, value=None, id=None, **attrs):
        kw = {'type': 'email', 'maxlength': 60, 'class_': 'email'}
        kw.update(attrs)
        return self.text(name, value, id, **kw)

    def textarea(self, name, value=None, id=None, **attrs):
        value = self.value(name, value) or ''
        if value:
            rows = len(value) // (const.TEXTAREA_COLS - 20) + const.TEXTAREA_ROWS_LONG
        else:
            rows = const.TEXTAREA_ROWS_LONG
        kw = {'cols': const.TEXTAREA_COLS, 'rows': rows}
        kw.update(attrs)
        return FormRenderer.textarea(self, name, value, id, **kw)

    def colour(self, name, value=None, id=None, **attrs):
        kw = {'maxlength': 50, 'size': 20, 'class_': 'colour'}
        kw.update(attrs)
        kw['size'] = min((kw['maxlength'], kw['size']))

        id = id or name

        value = self.value(name, value)
        if value and value[0] == '#':
            value = value[1:]

        return literal('#') + tags.text(name, value, id, **kw)

    def password(self, name, id=None, **attrs):
        kw = {'class_': 'password'}
        kw.update(attrs)
        return tags.password(name, id=id, **kw)

    def errorlist(self, name=None, **attrs):
        """
        Renders errors in a <ul> element if there are multiple, otherwise will
        use a div. Unless specified in attrs, class will be "Alert".

        If no errors present returns an empty string.

        `name` : errors for name. If **None** all errors will be rendered.
        """

        if name is None:
            errors = self.all_errors()
        else:
            errors = self.errors_for(name)

        if not errors:
            return ''

        if 'class_' not in attrs:
            attrs['class_'] = "Alert"

        if len(errors) > 1:
            content = Markup("\n").join(HTML.tag("li", error) for error in errors)

            return HTML.tag("ul", tags.literal(content), **attrs)

        return Markup('''
            <div class="ui-widget clearfix" style="margin: 0.25em;">
                <div class="ui-state-error error-field-wrapper">
                <span class="ui-icon ui-icon-alert error-notice-icon"></span>%s
                </div>
            </div>
            ''') % errors[0]

    def error_notice(self, msg=None):
        if not self.all_errors():
            return ''

        star_err = self.errors_for('*')
        if star_err:
            star_err = star_err[0]
        msg = msg or star_err or 'There were validation errors'
        return self.error_msg(msg)

    def error_msg(self, msg):
        return Markup('''
            <div class="ui-widget error-notice clearfix">
                <div class="ui-state-error ui-corner-all error-notice-wrapper">
                    <p><span class="ui-icon ui-icon-alert error-notice-icon"></span>
                    %s</p>
                </div>
            </div>
            ''') % msg

    def form_passvars(self, ln=None):
        params = self.form.request.form_args(ln)
        if not params:
            return ''

        return Markup('<div class="hidden">%s</div>') % \
            Markup('').join(tags.hidden(*x) for x in params)


class ModelState(object):
    def __init__(self, request):
        self.form = Form(request)
        self.renderer = CiocFormRenderer(self.form)
        self._defaults = None

    @property
    def is_valid(self):
        return not self.form.errors

    @property
    def schema(self):
        return self.form.schema

    @schema.setter
    def schema(self, value):
        if self.form.schema:
            raise RuntimeError("schema property has already been set")
        self.form.schema = value

    @property
    def validators(self):
        return self.form.validators

    @validators.setter
    def validators(self, value):
        if self.form.validators:
            raise RuntimeError("validators property has alread been set")

        self.form.validators = value

    @property
    def method(self):
        return self.form.method

    @method.setter
    def method(self, value):
        self.form.method = value

    @property
    def defaults(self):
        return self._defaults

    @defaults.setter
    def defaults(self, value):
        if self._defaults:
            raise RuntimeError("defaults property has already been set")

        if self.form.is_validated:
            raise RuntimeError("Form has already been validated")
        self._defaults = value
        self.form.data.update(value)

    @property
    def data(self):
        return self.form.data

    def validate(self, *args, **kw):
        return self.form.validate(*args, **kw)

    def bind(self, obj=None, include=None, exclude=None):
        if obj is None:
            obj = DefaultModel()

        return self.form.bind(obj, include, exclude)

    def value(self, name, default=None):
        return self.renderer.value(name, default)

    def is_error(self, name):
        return self.renderer.is_error(name)

    def errors(self):
        return self.form.errors

    def errors_for(self, name):
        return self.renderer.errors_for(name)

    def add_error_for(self, name, msg):
        errlist = self.form.errors_for(name)
        errlist.append(msg)

        self.form.errors[name] = errlist
