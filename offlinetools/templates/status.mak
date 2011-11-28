<%inherit file="master.mak"/>
<%block name="title">${_('Status')}</%block>
%if not request.database_has_data:
<%block name="sitenav"/>
%endif

<%! from markupsafe import Markup, escape %>

<table class="form-table">
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


