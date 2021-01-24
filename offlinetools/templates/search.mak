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

<%inherit file="master.mak" />
<%!
from offlinetools import const
%>
<%block name="title">Search</%block>
<%block name="newsearch"/>

${renderer.error_notice()}

<%doc>
<!-- ERRORS

${renderer.form.errors}

-->
</%doc>
<form method="get" action="${request.route_url('results', _form=True)}" id="SearchForm">
${renderer.form_passvars()}
	<table class="form-table">
		<tr>
			<td class="ui-widget-header">${renderer.label('Terms', _('Contains word/phrase'))}</td>
			<td class="ui-widget-content">
				${renderer.errorlist('Terms')}
				${renderer.text('Terms', maxlength=255)}
			</td>
		</tr>
        %if quicklist:
		<tr>
			<td class="ui-widget-header">${renderer.label('QuickList', _('Quick List'))}</td>
			<td class="ui-widget-content">
				${renderer.errorlist('QuickList')}
				${renderer.select('QuickList', options=[('','')] + list(map(tuple, quicklist)))}
				</td>
		</tr>
        %endif
		<tr>
			<td class="ui-widget-header">${renderer.label('Community', 'Community')}</td>
			<td class="ui-widget-content">
                ${renderer.errorlist('LocatedIn')}
                ${renderer.radio('LocatedIn', True, True, label=_('Located In'))}
                ${renderer.radio('LocatedIn', False, False, label=_('Areas Served'), class_='extra-space')}
                <br>
				${renderer.errorlist('Community')}
				${renderer.text('Community', maxlength=255)}
				</td>
		</tr>
	</table>
	<br>
	<input type="submit" value="${_('Search')}"> <input type="reset" value="${_('Clear')}">
</form>

<table class="form-table status-summary">
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
	<td class="ui-widget-content">${config.update_failure_count} <a href="${request.route_path('status')}">${_('Check Full Status')}</a></td>
</tr>
%endif
</table>


<%block name="bottomscripts">

	<form class="hidden" name="stateForm" id="stateForm">
	<textarea id="cache_form_values"></textarea>
	</form>

	<script type="text/javascript" src="static/js/search.min.js"></script>
	<script type="text/javascript">
	(function() {
	jQuery(function($) {

		init_cached_state('#SearchForm');

		init_community_autocomplete($, 'Community', "${request.route_url('comgen')}", 3);
		init_community_autocomplete($, 'Terms', "${request.route_url('keywordgen')}", 3);

		restore_cached_state();
		});
	})();
	</script>
</%block>
