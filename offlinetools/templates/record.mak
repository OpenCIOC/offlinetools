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
<%block name="title">${', '.join(x for x in (core_data.get('ORG_LEVEL_%d' % i) for i in range(1,6)) if x is not None) or _('(unknown)') |n}</%block>

<table class="record-header">
<tr><td><strong>${_('Record #:')}</strong> ${num}</td>
<td><strong>${_('Last Full Update:')}</strong> ${core_data.get('UPDATE_DATE') or _('(unknown)')}</td>
<td><strong>${_('Non-Public:')}</strong> ${core_data.get('NON_PUBLIC') or _('(unknown)')}</td>
</tr>
</table>
<table class="form-table">
%for group in field_groups:
<% group_fields = fields.get(group.DisplayFieldGroupID) %>
%if group_fields:
<tr>
    <td colspan="2" class="ui-widget-header">${group.Name|n}</td>
</tr>
%for field in group_fields:
<tr>
    <td class="ui-widget-header field">${field.Name|n}</td>
    <td class="ui-widget-content">${textToHTML(record_data[field.FieldID].Value)}</td>
</tr>

%endfor
%endif

%endfor
</table>

