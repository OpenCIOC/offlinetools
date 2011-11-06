<%inherit file="master.mak"/>
<%block name="title">${_('Register With CIOC Database')}</%block>
<%block name="sitenav"/>

<%! import socket %>


${renderer.error_notice()}
<form action='${request.current_route_path(_form=True)}' method='post'>
${renderer.form_passvars()}
<a href="${request.current_route_path(_ln='en-CA' if request.language.Culture=='fr-CA' else 'fr-CA')}">${_(u"S'enregistrer en français")}</a>
<table class="form-table">
<td colspan="2" class="ui-widget-header">${_('Basic Source Database Connection Information')}</td>
<tr>
    <td class="ui-widget-header">
        ${renderer.label('CiocSite', _('Source CIOC Site'))}
    </td>
    <td class="ui-widget-content">
        ${renderer.errorlist('CiocSite')}
        ${renderer.url('CiocSite')}
        <br><span class="SmallNote FieldNote">${_('The URL you use to log-in to CIOC.')}</span>
    </td>
</tr>
<tr>
    <td class="ui-widget-header">
        ${renderer.label('LoginName', _('CIOC User Name:'))}
    </td>
    <td class="ui-widget-content">
        ${renderer.errorlist('LoginName')}
        ${renderer.text('LoginName', max=50)}
        <br><span class="SmallNote FieldNote">${_('What you use to log in to CIOC.')}</span>
    </td>
</tr>
<tr>
    <td class="ui-widget-header">
        ${renderer.label('LoginPwd', _('CIOC Password:'))}
    </td>
    <td class="ui-widget-content">
        ${renderer.errorlist('LoginPwd')}
        ${renderer.password('LoginPwd')}
        <br><span class="SmallNote FieldNote">${_('What you use to log in to CIOC.')}</span>
    </td>
</tr>
<tr>
<td colspan="2" class="ui-widget-header">${_('Information About This Installation of Offline Tools')}</td>
</tr>
<tr>
    <td class="ui-widget-header">${renderer.label('MachineName', _('Computer Name'))}</td>
    <td class="ui-widget-content">
        ${renderer.errorlist('MachineName')}
        ${renderer.text('MachineName', socket.gethostname())}
        <br><span class="SmallNote FieldNote">${_('This is a unique identifier for this installation of the offline tools so that your administrator will be able to recognise it from the CIOC management tools. Something like "Jane\'s Laptop" or "John\'s Desktop" or the hostname of this computer (%s). This needs to be something unique') % socket.gethostname() }</span>
    </td>
</tr>
<td colspan="2" class="ui-widget-header">${_('Customize Your Installation')}</td>
</tr>
<tr>
    <td class="ui-widget-header">${renderer.label('SiteTitle', _('Site Title'))}</td>
    <td class="ui-widget-content">
        ${renderer.errorlist('SiteTitle')}
        ${renderer.text('SiteTitle')}
        <br><span class="SmallNote FieldNote">${_('This title will be shown at the top of all the pages you view in this tool. It will help you know you are looking at the right site.')}</span>
    </td>
</tr>
</table>
<br>
<input type="submit" value="${_('Register This Tool')}">
