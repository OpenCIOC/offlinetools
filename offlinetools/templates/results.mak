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
<%block name="title">${_('Search Results')}</%block>

%if not results:
${self.printInfoMessage(_('No results found for criteria'))}
%else:
${self.printInfoMessage(_('Found %d results matching that criteria') % len(results))}
<table class="form-table">
<tr>
    <th class="ui-widget-header">${_('ID')}</th>
    <th class="ui-widget-header">${_('Org Name')}</th>
    <th class="ui-widget-header">${_('Located In')}</th>
</tr>
%for result in results:
<tr>
    <td class="ui-widget-content">${result[0]}</td>
    <td class="ui-widget-content"><a href="${request.route_path('record', num=result[0])}">${result.OrgName_Cache or _('(unknown)')|n}</a></td>
    <td class="ui-widget-content">${result.LOCATED_IN_Cache or ''}</td>
</tr>
%endfor
</table>
%endif

