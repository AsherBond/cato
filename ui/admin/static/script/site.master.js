//Copyright 2012 Cloud Sidekick
// 
//Licensed under the Apache License, Version 2.0 (the "License");
//you may not use this file except in compliance with the License.
//You may obtain a copy of the License at
// 
//    http://www.apache.org/licenses/LICENSE-2.0
// 
//Unless required by applicable law or agreed to in writing, software
//distributed under the License is distributed on an "AS IS" BASIS,
//WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//See the License for the specific language governing permissions and
//limitations under the License.
//

var g_config = {};

//the timer that keeps the heartbeat updated
window.setInterval(updateHeartbeat, 120000);

// THIS IS AWESOME
// get some important python configuration settings that have relevance on the client
g_config = catoAjax.getConfig();
g_config.user_ui_url = g_config.user_ui_protocol + '://' + window.location.hostname + ':' + g_config.user_ui_port;
g_config.admin_ui_url = g_config.admin_ui_protocol + '://' + window.location.hostname + ':' + g_config.admin_ui_port;


$(document).ready(function () {
    //NOTE: this is the main jQuery function that will execute
    //when the DOM is ready.  Things you want defined on 'page load' should 
    //go in here.

    //use this to define constants, set up jQuery objects, etc.

    $("#main-menu").load("uiMethods/wmGetMenu", function() {
	    $("ul.sf-menu").supersubs({
	        minWidth: 18,   // minimum width of sub-menus in em units 
	        maxWidth: 27,   // maximum width of sub-menus in em units 
	        extraWidth: .5     // extra width can ensure lines don't sometimes turn over 
	        // due to slight rounding differences and font-family 
	    }).superfish();  // call supersubs first, then superfish, so that subs are 
	    // not display:none when measuring. Call before initialising 
	    // containing tabs for same reason.
	});

	getCloudAccounts();
	
    //note the selected one for other functions
    $("#header_cloud_accounts").change(function () {
    	$.cookie("selected_cloud_account", $(this).val());
    	$.cookie("selected_cloud_provider", $("#header_cloud_accounts option:selected").attr("provider"));
    	
        if (typeof CloudAccountWasChanged == 'function') {
	    	CloudAccountWasChanged();
        }
    });
});


// Menu
$(function () {
    var tabContainers = $('div.tabs > div');
    tabContainers.hide().filter(':home').hide();
    $('div.tabs ul.tabNavigation a').click(function () {
        tabContainers.slideUp();
        tabContainers.filter(this.hash).slideDown();
        //$('div.tabs ul.tabNavigation a').removeClass('selected');
        //$(this).addClass('selected');
    }).filter(':first').click();
});
// End Menu

function updateHeartbeat() {"use strict";
	ajaxGet("uiMethods/wmUpdateHeartbeat");
}

function lockDown(msg) {
	// if the heartbeat failed or a method returned a session error...
	// or, possibly the server is just gone...
	// close down the gui and show a pretty message, with a link to the login page.

	// NOTE: you cannot do a location.href here to any page, because if the server is down
	// it'll result in an ugly message.  By doing it with script here we don't need the server.

	msg = (msg) ? msg : 'It appears the server is no longer available.';

	//this will clear the page
	$("body").empty();

	// this is a wicked trick for erasing thie browser history to prevent the user
	// from going back and seeing broken pages.
	var backlen = history.length;
	history.go(-backlen);

	var $msg = $('<div class="ui-widget-content ui-corner-all" style="margin-left: auto; margin-right: auto; padding: 20px; width: 500px;" />');
	var $inner = $('<div class="ui-state-highlight ui-corner-all" style="padding: 10px;">');
	$inner.append('<span class="ui-icon ui-icon-info" style="float: left; margin-right: .3em;"></span><strong>Uh oh...</strong>');
	$inner.append('<br><br>');
	$inner.append('<p style="margin-left: 10px;">' + msg + '</p><br>');
	$inner.append('<p style="margin-left: 10px;">Please contact an Administrator if this condition persists.</p><br>');
	$inner.append('<p style="margin-left: 10px;"><a href="/static/login.html">Click here</a> to return to the login page.</p>');
	$msg.append($inner);
	$("body").append($msg);

	// this nice little bit gets the index of a new setTimeout, then clears every outstanding timeout.
	// very useful for when dynamic content like user-defined reports are setting timeouts
	var x = setTimeout(function(){}, 0);
	for (var i = 0; i < x; i++) {
		clearTimeout(i);
	}

	//same magic to clear intervals
	var x = setInterval(function(){}, 0);
	for (var i = 0; i < x; i++) {
		clearInterval(i);
	}
}

function getCloudAccounts() {
	var response = catoAjax.getCloudAccountsForHeader($("#selected_cloud_account").val());
	if (response) {
		$("#header_cloud_accounts").empty().append(response);
		$.cookie("selected_cloud_account", $("#header_cloud_accounts option:selected").val());
		$.cookie("selected_cloud_provider", $("#header_cloud_accounts option:selected").attr("provider"));
	}
}

function registerCato()
{
	//update the setting
	updateSetting("general","register_cato","registered");
	
	//open the form
	openWindow('http://community.cloudsidekick.com/register-cato?utm_source=cato_app&amp;utm_medium=menu&amp;utm_campaign=app', 'ask', 'location=no,status=no,scrollbars=yes,resizable=yes,width=800,height=700');
	
	//this might not be visible, but try to remove it anyway.
	$("#registercato").remove();
}