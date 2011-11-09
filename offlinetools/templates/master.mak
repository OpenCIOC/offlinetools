<!doctype html>
<!-- paulirish.com/2008/conditional-stylesheets-vs-css-hacks-answer-neither/ -->
<!--[if lt IE 7]> <html class="no-js ie6 oldie" lang="en"> <![endif]-->
<!--[if IE 7]>    <html class="no-js ie7 oldie" lang="en"> <![endif]-->
<!--[if IE 8]>    <html class="no-js ie8 oldie" lang="en"> <![endif]-->
<!-- Consider adding an manifest.appcache: h5bp.com/d/Offline -->
<!--[if gt IE 8]><!--> <html class="no-js" lang="en"> <!--<![endif]-->
<head>
  <meta charset="utf-8">

  <!-- Use the .htaccess and remove these lines to avoid edge case issues.
       More info: h5bp.com/b/378 -->
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">

  <title><%block name="title"/></title>
  <meta name="description" content="">
  <meta name="author" content="">

  <!-- Mobile viewport optimized: j.mp/bplateviewport -->
  <meta name="viewport" content="width=device-width,initial-scale=1">

  <!-- Place favicon.ico and apple-touch-icon.png in the root directory: mathiasbynens.be/notes/touch-icons -->

  <!-- CSS: implied media=all -->
  <!-- CSS concatenated and minified via ant build script-->
  <!-- XXX only local styles -->
  <link rel="stylesheet" href="/static/css/jquery-ui-1.8.16.custom.css" type="text/css" />
  <link rel="stylesheet" href="/static/css/style.css">
  <style type="text/css">
    /* fix the broken font handling in default jquery-ui styles */
    .ui-widget {
        font-family: inherit;
        font-size: 1em;
    }
  </style>
  <!-- end CSS-->

  <!-- More ideas for your <head> here: h5bp.com/d/head-Tips -->

  <!-- All JavaScript at the bottom, except for Modernizr / Respond.
       Modernizr enables HTML5 elements & feature detects; Respond is a polyfill for min/max-width CSS3 Media Queries
       For optimal performance, use a custom Modernizr build: www.modernizr.com/download/ -->
  <script src="/static/js/libs/modernizr-2.0.6-custom.min.js"></script>
</head>

<%block name="body_open_tag">
<body>
</%block>

<div id="wrap">
<header class="ui-widget-header" style="padding-left: 1em;">
<nav class="site-nav"><%block name="sitenav">
<%block name="newsearch"><a class="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-icon-primary" href="${request.route_url('search')}"><span class="ui-icon ui-icon-search ui-button-icon-primary"></span><span class="ui-button-text">${_('New Search')}</span></a></%block>
<a class="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-icon-primary" href="${request.route_path('logout')}"><span class="ui-icon ui-icon-power ui-button-icon-primary"></span><span class="ui-button-text">${_('Logout')}</span></a>
</%block>
</nav>
<h1 style="margin: 0;">${_('CIOC Offline Tools for [INSERT DB]')}</h1>
</header>
<header id="pagetitle">
<h1 class="clearfix"><%block name="searchnav"/>${self.title()}</h1>
</header>

    <div id="main" role="main">
	<% message = request.session.pop_flash() %>
	%if message:
		<div class="ui-widget error-notice clearfix">
			<div class="ui-state-highlight ui-corner-all error-notice-wrapper"> 
				<p><span class="ui-icon ui-icon-info error-notice-icon"></span> ${message[0]} </p>
			</div>
		</div>
	%endif

    ${next.body()}

    </div>

<footer>

</footer>

</div> <!-- #wrap -->


  <!-- JavaScript at the bottom for fast page loading -->

  <!-- Grab Google CDN's jQuery, with a protocol relative URL; fall back to local if offline -->
  <!-- XXX only local scripts -->
  <script src="/static/js/libs/jquery-1.7.min.js"></script>
  <script src="/static/js/libs/jquery-ui-1.8.16.custom.min.js"></script>

  
  <!-- scripts concatenated and minified via ant build script-->
  <script defer src="/static/js/plugins.js"></script>
  <script defer src="/static/js/libs/json2.min.js"></script>
  <!-- end scripts-->
  
  <%block name="bottomscripts"/>
	
</body>
</html>
