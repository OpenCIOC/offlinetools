<%inherit file="master.mak" />
<%block name="title">Search</%block>
<%block name="newsearch"/>

${renderer.error_notice()}
<form method="get" action="${request.route_url('results', _form=True)}">
${renderer.form_passvars()}
	<table class="form-table">
		<tr>
			<td class="ui-widget-header">${renderer.label('Terms', _('Keyword Search'))}</td>
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
				${renderer.select('QuickList', options=[('','')] + map(tuple, quicklist))}
				</td>
		</tr>
        %endif
		<tr>
			<td class="ui-widget-header">${renderer.label('Community', 'Community')}</td>
			<td class="ui-widget-content">
				${renderer.errorlist('Community')}
				${renderer.text('Community', maxlength=255)}
				</td>
		</tr>
	</table>
	<br>
	<input type="submit" value="Submit"> <input type="reset" value="Clear">
</form>


<%block name="bottomscripts">

</%block>
