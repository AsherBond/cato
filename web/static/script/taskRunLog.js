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
	g_instance = getQuerystringVariable("task_instance");
	g_task_id = getQuerystringVariable("task_id");
	g_asset_id = getQuerystringVariable("asset_id");
	g_rows = getQuerystringVariable("rows");

	$(".link").disableSelection();

	//refresh button
	$("#refresh_btn").click(function() {
		doGetDetails();
	});

	//view logfile link
	$("#view_logfile_btn").click(function() {
		doGetLogfile();
	});

	$("#logfile_dialog").dialog({
		autoOpen : false,
		height : 600,
		width : 700,
		bgiframe : true,
		buttons : {
			OK : function() {
				$(this).dialog("close");
			}
		}
	});

	//parent instance link
	$("#lblSubmittedByInstance").click(function() {
		showPleaseWait();
		self.location.href = "taskRunLog?task_instance=" + $("#hidSubmittedByInstance").val();
		;
		hidePleaseWait();
	});

	//show the abort button if applicable
	status = $("#lblStatus").text();
	if ("Submitted,Processing,Queued".indexOf(status) > -1)
		$("#abort_btn").removeClass("hidden");

	$("#abort_dialog").dialog({
		autoOpen : false,
		draggable : false,
		resizable : false,
		bgiframe : true,
		modal : true,
		overlay : {
			backgroundColor : '#000',
			opacity : 0.5
		},
		buttons : {
			Cancel : function() {
				$(this).dialog("close");
			},
			OK : function() {
				doDebugStop();
			}
		}
	});

	//resubmit button
	//shows a dialog with options
	$("#resubmit_btn").click(function() {
		$("#resubmit_dialog").dialog("open");
	});

	//Stop button
	//shows a dialog with options
	$("#abort_btn").click(function() {
		$("#abort_dialog").dialog("open");
	});

	//show/hide content based on user preference
	$("#show_detail").click(function() {
		$("#full_details").toggleClass("hidden");
		$("#show_detail").toggleClass("vis_btn_off");

		if ($("#full_details").hasClass("hidden")) {
			$("#ti_content").css("margin-top", "84px");
		} else {
			$("#ti_content").css("margin-top", "174px");
		}
	});
	$("#show_cmd").click(function() {
		$(".log_command").toggleClass("hidden");
		$("#show_cmd").toggleClass("vis_btn_off");
	});
	$("#show_results").click(function() {
		$(".log_results").toggleClass("hidden");
		$("#show_results").toggleClass("vis_btn_off");
	});

	//repost and ask for the whole log
	$(".get_all").click(function() {
		if (confirm("This may take a long time.\n\nAre you sure?"))
			// we use this class programatically later to determine if
			// all rows have been requested.
			$(".get_all").removeClass("vis_btn_off");
		$("#get_all_bottom").hide();
		doGetLog("all");
	});

	//enable/disable the 'clear log' button on the dialog
	$("#rb_new").click(function() {
		$("#clear_log").attr("disabled", "disabled");
	});
	$("#rb_existing").click(function() {
		$("#clear_log").removeAttr("disabled");
	});

	$("#resubmit_dialog").dialog({
		autoOpen : false,
		draggable : false,
		resizable : false,
		bgiframe : true,
		modal : true,
		overlay : {
			backgroundColor : '#000',
			opacity : 0.5
		},
		buttons : {
			Cancel : function() {
				$(this).dialog("close");
			},
			OK : function() {
				$(this).dialog("close");

				var task_id = $("#hidTaskID").val();
				var asset_id = $("#hidAssetID").val();
				var ecosystem_id = $("#hidEcosystemID").val();
				var account_id = $("#hidAccountID").val();
				var instance = $("#hidInstanceID").val();
				var debug_level = $("#hidDebugLevel").val();

				var task_name = $("#lblTaskName").text();
				var ecosystem_name = $("#lblEcosystemName").text();
				var account_name = $("#lblAccountName").text();

				var args = '{"task_id":"' + task_id + '", "task_name":"' + task_name + '", "debug_level":"' + debug_level + '", "instance":"' + instance + '"';

				if (account_id)
					args += ', "account_id":"' + account_id + '", "account_name":"' + account_name + '"';

				if (ecosystem_id)
					args += ', "ecosystem_id":"' + ecosystem_id + '", "ecosystem_name":"' + ecosystem_name + '"';

				args += '}';

				// this time we allow the user to select whether or not they want a new run log window.
				$(".new_runlog_window").show();
				
				//NOTE: we *ARE* passing the account_id - we don't want the dialog to use the default
				//this is a previous instance's log and we wanna use the same account as it did.
				ShowTaskLaunchDialog(args);

			}
		}
	});

	hidePleaseWait();

	//if there's no value in the CELogfile ... hide the button.
	if ($("#hidCELogFile").val() == "")
		$("#show_logfile").hide();

	doGetDetails();

});

function doGetDetails() {
	$.ajax({
		async : false,
		type : "POST",
		url : "taskMethods/wmGetTaskRunLogDetails",
		data : '{"sTaskInstance":"' + g_instance + '", "sTaskID":"' + g_task_id + '", "sAssetID":"' + g_asset_id + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(instance) {
			if (instance.error)
				showAlert(instance.error);

			$("#hidInstanceID").val(instance.task_instance);
			$("#hidTaskID").val(instance.task_id);
			$("#hidAssetID").val(instance.asset_id);
			$("#hidSubmittedByInstance").val(instance.submitted_by_instance);
			$("#hidEcosystemID").val(instance.ecosystem_id);
			$("#hidAccountID").val(instance.account_id);
			$("#hidDebugLevel").val(instance.debug_level);

			$("#lblTaskInstance").text(instance.task_instance);
			$("#lblTaskName").text(instance.task_name_label);
			$("#lblStatus").text(instance.task_status);
			$("#lblAssetName").text(instance.asset_name);
			$("#lblSubmittedDT").text(instance.submitted_dt);
			$("#lblStartedDT").text(instance.started_dt);
			$("#lblCompletedDT").text(instance.completed_dt);
			$("#lblSubmittedBy").text(instance.submitted_by);
			$("#lblCENode").text(instance.ce_node);
			$("#lblPID").text(instance.pid);
			$("#lblSubmittedByInstance").text(instance.submitted_by_instance);
			$("#lblEcosystemName").text(instance.ecosystem_name);
			$("#lblAccountName").text(instance.account_name);

			if (instance.submitted_by_instance != "")
				$("#lblSubmittedByInstance").addClass("link");

			//if we got a "resubmit_message"...
			if (instance.resubmit_message)
				$("#lblResubmitMessage").text(instance.resubmit_message);
			else
				$("#lblResubmitMessage").text("");

			//don't show the cancel button if it's not running
			if (instance.allow_cancel == "false")
				$("#phCancel").hide();
			else
				$("#phCancel").show();

			//if the log file is local to this server, show a link
			if (instance.logfile_name)
				$("#view_logfile_btn").show();
			else
				$("#view_logfile_btn").hide();

			//if the other instances array has stuff in it, then
			if (instance.other_instances) {
				if (instance.other_instances.length) {
					html = ""
					$(instance.other_instances).each(function(idx, row) {
						html += '<tr task_instance="' + row.task_instance + '">' + '<td tag="selectable" class="pointer">' + row.task_instance + '</td>' + '<td tag="selectable" class="pointer">' + row.task_status + '</td>' + '</tr>';
					});
					$("#other_instances").empty().append(html);
					initJtable();
					//jump links
					$("#other_instances tr").click(function() {
						self.location.href = "taskRunLog?task_instance=" + $(this).attr("task_instance");
						;
					});

					$("#pnlOtherInstances").show();
				}
			}

			//we rely on the details to get the log
			// and we get all rows if that's previously been selected.
			if ($(".get_all").hasClass("vis_btn_off"))
				doGetLog(200);
			else
				doGetLog("all");

		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function doGetLog(rows) {
	var instance = $("#hidInstanceID").val();

	if (instance == '')
		return;

	$("#ltLog").empty();
	$("#ltSummary").empty();

	$.ajax({
		async : false,
		type : "POST",
		url : "taskMethods/wmGetTaskRunLog",
		data : '{"sTaskInstance":"' + instance + '", "sRows":"' + rows + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(response) {
			if (response.log)
				$("#ltLog").html(unpackJSON(response.log));

			if (response.summary)
				$("#ltSummary").replaceWith(unpackJSON(response.summary));

			if (response.totalrows)
				if (rows == "all") {
					$("#row_count_lbl").text(" - all " + response.totalrows + " rows.");
					$("#get_all_bottom").hide();
				} else if (rows >= response.totalrows) {
					$("#row_count_lbl").empty();
				} else {
					$("#row_count_lbl").text(" - " + rows + "/" + response.totalrows + " rows.");
					$("#get_all_bottom").show();
				}
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function doGetLogfile() {
	instance = $("#hidInstanceID").val();

	if (instance == '')
		return;

	$.ajax({
		async : true,
		type : "POST",
		url : "taskMethods/wmGetTaskLogfile",
		data : '{"sTaskInstance":"' + instance + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "text",
		success : function(response) {
			$("#logfile_text").html(unpackJSON(response));
			$("#logfile_dialog").dialog("open");
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function doDebugStop() {
	instance = $("#hidInstanceID").val();

	if (instance == '')
		return;

	$.ajax({
		async : false,
		type : "POST",
		url : "taskMethods/wmStopTask",
		data : '{"sInstance":"' + instance + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "text",
		success : function(response) {
			location.reload();
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}
