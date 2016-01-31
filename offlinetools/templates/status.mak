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
<%!
from offlinetools import const
%>
<%block name="title">${_('Status')}</%block>
%if not request.database_has_data:
<%block name="sitenav"/>
%endif

<%! from markupsafe import Markup, escape %>

<table class="form-table">
<tr>
	<td class="ui-widget-header">${_('Version')}</td>
	<td class="ui-widget-content">${const.OFFLINE_TOOLS_VERSION}</td>
</tr>
<tr>
	<td class="ui-widget-header">${_('Last Updated')}</td>
	<td class="ui-widget-content">${request.format_datetime(config.last_update)}</td>
</tr>
<tr>
	<td class="ui-widget-header">${_('Update Schedule')}</td>
	<td class="ui-widget-content">${schedule}</td>
</tr>
%if config.update_failure_count:
<tr>
	<td class="ui-widget-header">${_('Update Failure Count')}</td>
	<td class="ui-widget-content">${config.update_failure_count}</td>
</tr>
%endif
</table>
<br><br>
<table class="form-table">
<tr>
	<td colspan="2" class="ui-widget-header">${_('Update Log')}</td>
</tr>
<tr>
	<td colspan="2" class="ui-widget-content">
    ${_('Most Recent First:')}
    <br><br>${escape(config.update_log).replace('\n', Markup('<br>'))}</td>
</tr>
</table>


