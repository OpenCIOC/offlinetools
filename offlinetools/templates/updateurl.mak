<%doc>
  =========================================================================================
   Copyright 2016 Community Information Online Consortium (CIOC) and KCL Software Solutions
 
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
 
       http://www.apache.org/licenses/LICENSE-2.0
 
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
  =========================================================================================
</%doc>

<%inherit file="master.mak"/>
<%block name="title">${_('Update Your CIOC Database Connection')}</%block>
<%block name="sitenav"/>

<%! import socket %>


${renderer.error_notice()}
<form action='${request.current_route_path(_form=True)}' method='post'>
${renderer.form_passvars()}
<p><a href="${request.current_route_path(_ln='en-CA' if request.language.Culture=='fr-CA' else 'fr-CA')}">${_(u"S'enregistrer en français")}</a></p>
<table class="form-table">
<td colspan="2" class="ui-widget-header">${_('Basic Source Database Connection Information')}</td>
<tr>
    <td class="ui-widget-header">
        ${renderer.label('CiocSite', _('Source CIOC Site'))}
    </td>
    <td class="ui-widget-content">
        ${renderer.errorlist('CiocSite')}
        ${renderer.url('CiocSite')}
        <br><span class="SmallNote FieldNote">${_('URL of your CIOC database; e.g. test.cioc.ca')}</span>
    </td>
</tr>
</table>
<br>
<input type="submit" value="${_('Update Configuration')}">
