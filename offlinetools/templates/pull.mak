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
        setTimeout(update_progress, 2500);
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
