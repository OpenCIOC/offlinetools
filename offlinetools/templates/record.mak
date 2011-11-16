<%inherit file="master.mak"/>
<%block name="title">${_('Record Details')}</%block>

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
    <td>${record_data[field.FieldID].Value}</td>
</tr>

%endfor
%endif

%endfor
</table>

