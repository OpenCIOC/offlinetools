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
