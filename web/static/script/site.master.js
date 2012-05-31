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

//the timer that keeps the heartbeat updated
window.setInterval(updateHeartbeat, 120000);

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
	// NOTE: This is not async for a reason - other 'page load' ajax calls depend on it.
    $.ajax({
        type: "POST",
        async: false,
        url: "uiMethods/wmGetCloudAccountsForHeader",
        data: '{"sSelected":"' + $("#selected_cloud_account").val() + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "html",
        success: function (response) {
            $("#header_cloud_accounts").empty().append(response)
        	$.cookie("selected_cloud_account", $("#header_cloud_accounts option:selected").val());
	    	$.cookie("selected_cloud_provider", $("#header_cloud_accounts option:selected").attr("provider"));
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
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