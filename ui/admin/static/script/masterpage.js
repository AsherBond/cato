
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

// THIS IS CRITICAL
// different browsers cache ajax different ways.
// this app doesn't require ajax caching - our content is different every time it's requested.
// this should make all ajax requests use the jquery cache buster.
// (this only applies to GET calls)
// $.ajaxSetup({
	// cache : false
// });
// this file *should* always be the first script file loaded, and this block isn't in document.ready.

$(document).ready(function() {
	//there are datepickers all over the app.  Anything with a class of "datepicker" will get initialized.
	$(".datepicker").datepicker({
		clickInput : true
	});
	$(".datetimepicker").datetimepicker();
	$(".timepicker").timepicker();

	// the logout button
	$("#logout_btn").click(function() {
		location.href = "/logout";
	});
	// the 'about' link in the footer
	$("#about_btn").click(function() {
		showAbout();
	});

	$("#error_dialog").dialog({
		autoOpen : false,
		bgiframe : false,
		modal : true,
		width : 400,
		overlay : {
			backgroundColor : '#000',
			opacity : 0.5
		},
		buttons : {
			Ok : function() {
				$(this).dialog("close");
			}
		},
		close : function(event, ui) {
			//$("#fullcontent").unblock();
			//$("#head").unblock();
			$.unblockUI();
			//sometimes ajax commands would have blocked the task_steps div.  Unblock that just as a safety catch.
			$("#task_steps").unblock();
		}
	});

	$("#info_dialog").dialog({
		autoOpen : false,
		draggable : false,
		resizable : false,
		bgiframe : true,
		modal : false,
		width : 400
	});

	$("#about_dialog").dialog({
		autoOpen : false,
		draggable : false,
		resizable : false,
		bgiframe : true,
		modal : true,
		width : 400,
		overlay : {
			backgroundColor : '#000',
			opacity : 0.5
		}
	});

	$("#my_account_dialog").dialog({
		autoOpen : false,
		width : 600,
		modal : true,
		buttons : {
			"Save" : function() {
				// do not submit if the passwords don't match
				var pw1 = $("#my_account_dialog #my_password").val();
				var pw2 = $("#my_account_dialog #my_password_confirm").val();

				if (pw1 !== pw2) {
					showInfo("Passwords must match.");
					return false;
				}

				var args = {};
				args.my_email = $("#my_account_dialog #my_email").val();
				args.my_question = $("#my_account_dialog #my_question").val();
				args.my_password = packJSON(pw1);
				args.my_answer = packJSON($("#my_account_dialog #my_answer").val());

				var response = catoAjax.saveMyAccount(args);
				if (response) {
					$("#update_success_msg").text("Update Successful").fadeOut(2000);
					$("#my_account_dialog").dialog("close");
				}
			},
			"Cancel" : function() {
				$(this).dialog("close");
			}
		}
	});

	// when you show the user settings dialog, an ajax gets the values
	// if it's not a 'local' account, some of the fields are hidden.
	$("#my_account_link").click(function() {
		showMyAccount();
	});

	//the stack trace section on the error dialog is hidden by default
	//this is the click handler for showing it.
	$("#show_stack_trace").click(function() {
		$("#error_dialog_trace").parent().show();
		$(this).removeClass("ui-icon-triangle-1-e");
		$(this).addClass("ui-icon-triangle-1-s");
	});

});
function showMyAccount() {
	ajaxGet("uiMethods/wmGetMyAccount", function(account) {
		$("#my_password").val("");
		$("#my_password_confirm").val("");
		$("#my_question").val("");
		$("#my_answer").val("");
		if (account) {
			$("#my_fullname").html(account.full_name);
			$("#my_username").html(account.username);
			$("#my_email").val(account.email);
			$("#my_question").val(account.security_question);
		}
		//finally, show the dialog
		$("#my_account_dialog").dialog("open");
	});
}

function showAbout() {
	$("#app_version").text(g_config.version);
	$("#db_info").text(g_config.database);
	$('#about_dialog').dialog('open');
}

//This function shows the error dialog.
function showAlert(msg, info) {
	//reset the trace panel
	$("#stack_trace").hide();
	$("#show_stack_trace").removeClass("ui-icon-triangle-1-s");
	$("#show_stack_trace").addClass("ui-icon-triangle-1-e");
	$("#error_dialog_trace").parent().hide();

	var trace = '';

	// in many cases, the "msg" will be a json object with a stack trace
	//see if it is...
	try {
		var o = JSON.parse(msg);
		if (o.Message) {
			msg = o.Message;
			trace = o.StackTrace;
		}
	} catch(err) {
		//nothing to catch, just will display the original message since we couldn't parse it.
	}

	if (msg === "" || msg === "None") {// "None" is often returned by web methods that don't return on all code paths.
		info = info + msg;
		msg = "An unspecified error has occurred.  Check the server log file for details.";
	}

	hidePleaseWait();
	$("#error_dialog_message").html(msg);
	$("#error_dialog_info").html(info);
	if (trace !== null && trace !== '') {
		$("#error_dialog_trace").html(trace);
		$("#stack_trace").show();
	}

	$("#error_dialog").dialog("open");

	//send this message via email
	info = (info === undefined ? "" : info);
	trace = (trace === undefined ? "" : trace);
	var msgtogo = packJSON(msg + '\n' + info + '\n' + trace);
	var pagedetails = window.location.pathname;

	//$.post("uiMethods.asmx/wmSendErrorReport", { "sMessage": msgtogo, "sPageDetails": pagedetails });

}

//This function shows the info dialog.
function showInfo(msg, info, no_timeout) {
	$("#info_dialog_message").html(msg);

	if ( typeof (info) !== "undefined" && info.length > 0)
		$("#info_dialog_info").html(info);
	else
		$("#info_dialog_info").html("");

	//set it to auto close after 2 seconds
	//if the no_timeout flag was not passed
	if ( typeof (no_timeout) !== "undefined" && no_timeout) {
		$("#info_dialog").dialog("option", "buttons", {
			"OK" : function() {
				$(this).dialog("close");
			}
		});
	} else {
		$("#info_dialog").dialog("option", "buttons", null);
        setTimeout(function() {
            hideInfo();
        }, 2000);
	}

	$("#info_dialog").dialog("open");
}

//This function hides the info dialog.
function hideInfo() {
	$("#info_dialog").dialog("close");
}
