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

$(document).ready(function() {
	//there are datepickers all over the app.  Anything with a class of "datepicker" will get initialized.
	$(".datepicker").datepicker({
		clickInput : true
	});
	$(".datetimepicker").datetimepicker();
	$(".timepicker").timepicker();

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
				pw1 = $("#my_account_dialog #my_password").val();
				pw2 = $("#my_account_dialog #my_password_confirm").val();

				if (pw1 != pw2) {
					showInfo("Passwords must match.");
					return false;
				}

				args = JSON.stringify($("#my_account_dialog :input").serializeArray());
				args = args.replace(pw1, packJSON(pw1));
				$.ajax({
					async : false,
					type : "POST",
					url : "uiMethods/wmSaveMyAccount",
					data : '{"sValues":' + args + '}',
					contentType : "application/json; charset=utf-8",
					dataType : "json",
					success : function(response) {
						if (response.error) {
							showAlert(response.error);
						}
						if (response.info) {
							showInfo(response.info);
						}
						if (response.result) {
							if (response.result == "success") {
								$("#update_success_msg").text("Update Successful").fadeOut(2000);
								$("#my_account_dialog").dialog("close");
							}
						}
					},
					error : function(response) {
						$("#update_success_msg").fadeOut(2000);
						showAlert(response.responseText);
					}
				});
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

	//Storm
	if ( typeof (STORM) == 'undefined') {
		$(".storm").hide();
	}

});
function showMyAccount() {
	$.ajax({
		type : "GET",
		url : "uiMethods/wmGetMyAccount",
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(account) {
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
		},
		error : function(response) {
			showAlert(response);
		}
	});

	//finally, show the dialog
	$("#my_account_dialog").dialog("open");
}

function showAbout() {
	$("#app_version").load("uiMethods/wmGetVersion");
	$("#db_info").load("uiMethods/wmGetDBInfo");
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
		var o = eval('(' + msg + ')');
		if (o.Message) {
			msg = o.Message;
			trace = o.StackTrace;
		}
	} catch(err) {
		//nothing to catch, just will display the original message since we couldn't parse it.
	}

	if (msg == "" || msg == "None") {// "None" is often returned by web methods that don't return on all code paths.
		msg = "An unspecified error has occurred.  Check the server log file for details.";
		info = info + msg
	}

	hidePleaseWait();
	$("#error_dialog_message").html(msg);
	$("#error_dialog_info").html(info);
	if (trace != null && trace != '') {
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

	if ( typeof (info) != "undefined" && info.length > 0)
		$("#info_dialog_info").html(info);
	else
		$("#info_dialog_info").html("");

	//set it to auto close after 2 seconds
	//if the no_timeout flag was not passed
	if ( typeof (no_timeout) != "undefined" && no_timeout) {
		$("#info_dialog").dialog("option", "buttons", {
			"OK" : function() {
				$(this).dialog("close");
			}
		});
	} else {
		$("#info_dialog").dialog("removebutton", "OK");
		setTimeout("hideInfo()", 2000);
	}

	$("#info_dialog").dialog("open");
}

//This function hides the info dialog.
function hideInfo() {
	$("#info_dialog").dialog("close");
}
