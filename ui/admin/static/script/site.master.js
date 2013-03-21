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
g_config.user_ui_url = window.location.hostname + ':' + g_config.user_ui_port;
g_config.admin_ui_url = window.location.hostname + ':' + g_config.admin_ui_port;


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

//and the jquery ajax it performs
function updateHeartbeat() {
    $.ajax({
        type: "GET",
        url: "uiMethods/wmUpdateHeartbeat",
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            if (msg) {
                showAlert(msg);
            }
        },
        error: function (response) {
        	// if the heartbeat failed, it's likely the server is just gone.
        	// so, close down the gui and show a pretty message, with a link to the login page.

        	// this is a wicked trick for erasing thie browser history to prevent the user
        	// from going back and seeing broken pages.
        	var backlen=history.length;
        	history.go(-backlen);
        	
			msg = '<div class="ui-widget-content ui-corner-all" style="margin-left: auto; margin-right: auto; padding: 20px; width: 500px;">' + 
				'<div class="ui-state-highlight ui-corner-all" style="padding: 10px;">' + 
				'<span class="ui-icon ui-icon-info" style="float: left; margin-right: .3em;"></span><strong>Uh oh...</strong>' + 
				'<br><br>' +
				'<p style="margin-left: 10px;">It appears the server is no longer available.</p><br>' + 
				'<p style="margin-left: 10px;">Please contact an Administrator.</p><br>' + 
				'<p style="margin-left: 10px;"><a href="/static/login.html">Click here</a> to return to the login page.</p>' + 
				'</div>' + 
				'</div>'
        	$("body").html(msg);
        }
    });
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