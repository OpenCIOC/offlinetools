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
    <td colspan="2" class="ui-widget-header">${group.Name}</td>
</tr>
%for field in group_fields:
<tr>
    <td class="ui-widget-header">${field.Name}
    <td>${textToHTML(record_data[field.FieldID].Value)}</td>
</tr>

%endfor
%endif

%endfor
</table>

