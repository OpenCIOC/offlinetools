<%inherit file="master.mak"/>
<%block name="title">${_('Initial Data Sync')}</%block>
<%block name="sitenav"/>
${self.printInfoMessage(_('Now loading data from your CIOC site. This might take a while...'))}

<div id="progressbar"></div>

<%block name="bottomscripts">
<script type="text/javascript">
(function() {
 var prog_bar = null, update_progress_result = function(data, textStatus, jqXHR) {
    if (!data.status) {
        prog_bar.progressbar('value', data.percent)
        setTimeout(update_progress, 1500);
    }else if (data.status === 'invalid') {
        //no request pending
    } else if (data.status === 'done') {
        prog_bar.progressbar('value', data.percent);
        window.location.href = "${request.route_url('search')}";
    } else {
        alert(data.status);
    }
 }, update_progress_error = function(jqXHR, textStatus, errorThrown) {
    alert('error');
 }, update_progress = function() {
    jQuery.ajax('${request.route_url("pull_status")}', {dataType: 'json', cache: false, success: update_progress_result, error: update_progress_error})
 };
jQuery(function($){
    prog_bar = $( "#progressbar" ).progressbar({value: 0});
    update_progress();
    
});
})();
</script>
</%block>
