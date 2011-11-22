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
    <td class="ui-widget-content"><a href="${request.route_path('record', num=result[0])}">${', '.join(x for x in result[-5:] if x is not None) or _('(unknown)')|n}</a></td>
    <td class="ui-widget-content">${result[1] or ''}</td>
</tr>
%endfor
</table>
%endif

