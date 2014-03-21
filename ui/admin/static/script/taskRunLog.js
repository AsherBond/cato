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

	$("#resubmit_btn").button({
		icons : {
			primary : "ui-icon-play"
		}
	});
	$("#abort_btn").button({
		icons : {
			primary : "ui-icon-stop"
		}
	});
	$("#refresh_btn").button({
		icons : {
			primary : "ui-icon-refresh"
		},
		text : false
	});

	//refresh button
	$("#refresh_btn").click(function() {
		doGetDetails();
	});

	//view logfile link
	$("#view_logfile_btn").click(function() {
		doGetLogfile();
		$("#show_results").addClass("vis_btn_off");
		$("#view_logfile_btn").removeClass("vis_btn_off");
		$("#audit").hide();
		$("#logfile").show();
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

		hidePleaseWait();
	});

	//show the abort button if applicable
	var status = $("#lblStatus").text();
	if ("Submitted,Processing,Queued".indexOf(status) > -1) {
		$("#abort_btn").removeClass("hidden");
	}

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
		$("#logfile").hide();
		$("#audit").show();
		$("#show_results").removeClass("vis_btn_off");
		$("#view_logfile_btn").addClass("vis_btn_off");
	});

	//repost and ask for the whole log
	$(".get_all").click(function() {
		if (confirm("This may take a long time.\n\nAre you sure?")) {
			// we use this class programatically later to determine if
			// all rows have been requested.
			$(".get_all").removeClass("vis_btn_off");
		}
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
				var svc_inst_id = $("#hidServiceInstanceID").val();
				var account_id = $("#hidAccountID").val();
				var instance = $("#hidInstanceID").val();
				var debug_level = $("#hidDebugLevel").val();

				var task_name = $("#lblTaskName").text();
				var account_name = $("#lblAccountName").text();

				// SOME NOTES!!!!!
				// 1) it should display the parameters from this instance in the launch dialog
				// 2) it must use the same account id (wiether or not we need to pass this is unknown)
				// 3) it must know the deployment and service, as well as the instance
				var args = {};
				args.task_id = task_id;
				args.task_name = task_name;
				args.debug_level = debug_level;
				args.task_instance = instance;

				if (account_id) {
					args.account_id = account_id;
					args.account_name = account_name;
				}
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
	if ($("#hidCELogFile").val() === "") {
		$("#show_logfile").hide();
	}
	doGetDetails();

	// if it's running, enable the timer
    // NOTE : status is defined up above
	if ("Completed,Error,Cancelled".indexOf(status) === -1) {
		window.setInterval(refreshDynamic, 5000);
	}

});

function refreshDynamic() {"use strict";
	var status = $("#lblStatus").text();
	if ("Completed,Error,Cancelled".indexOf(status) === -1) {
		doGetDetails();
		location.hash = "_bottom_anchor";
	}
}

function doGetDetails() {
	var instance = ajaxPost("taskMethods/wmGetTaskRunLogDetails", {
		sTaskInstance : g_instance,
		sTaskID : g_task_id,
		sAssetID : g_asset_id
	});
	if (instance) {
		if (instance.error) {
			showInfo(instance.error);
		}

		$("#hidInstanceID").val(instance.task_instance);
		$("#hidTaskID").val(instance.task_id);
		$("#hidAssetID").val(instance.asset_id);
		$("#hidSubmittedByInstance").val(instance.submitted_by_instance);
		$("#hidServiceInstanceID").val(instance.instance_id);
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
		$("#lblCloud").text(instance.cloud_name);
		$("#lblAccountName").text(instance.account_name);

		if (instance.submitted_by_instance !== "") {
			$("#lblSubmittedByInstance").addClass("link");
		}
		//if we got a "resubmit_message"...
		if (instance.resubmit_message) {
			$("#lblResubmitMessage").text(instance.resubmit_message);
		} else {
			$("#lblResubmitMessage").text("");
		}

		//don't show the cancel button if it's not running
		if (instance.allow_cancel === "false") {
			$("#abort_btn").hide();
		} else {
			$("#abort_btn").show();
		}

		//if the log file is local to this server, show a link
		if (instance.logfile_name) {
			$("#view_logfile_btn").show();
		} else {
			$("#view_logfile_btn").hide();
		}

		//if the other instances array has stuff in it, then
		if (instance.other_instances) {
			if (instance.other_instances.length) {
				var html = "";
				$(instance.other_instances).each(function(idx, row) {
					html += '<tr task_instance="' + row.task_instance + '">';
					html += '<td tag="selectable" class="pointer">' + row.task_instance + '</td>';
					html += '<td tag="selectable" class="pointer">' + row.task_status + '</td>';
					html += '</tr>';
				});
				$("#other_instances").empty().append(html);
				initJtable();
				//jump links
				$("#other_instances tr").click(function() {
					self.location.href = "taskRunLog?task_instance=" + $(this).attr("task_instance");
				});

				$("#pnlOtherInstances").show();
			}
		}

		//we rely on the details to get the log
		// and we get all rows if that's previously been selected.
		if ($(".get_all").hasClass("vis_btn_off")) {
			doGetLog(200);
		} else {
			doGetLog("all");
		}
		
		// ONLY IF the 'Logfile' button is selected, we'll also get the Logfile
		if (!$("#view_logfile_btn").hasClass("vis_btn_off")) {
		    doGetLogfile();
		}
	}
}

function doGetLog(rows) {
	var instance = $("#hidInstanceID").val();

	if (instance === '') {
		return;
	}

	$("#ltLog").empty();
	$("#ltSummary").empty();

	var response = ajaxPost("taskMethods/wmGetTaskRunLog", {
		sTaskInstance : instance,
		sRows : rows
	});
	if (response) {
		if (response.log) {
			$("#ltLog").html(unpackJSON(response.log));
		}
		if (response.summary) {
			$("#ltSummary").replaceWith(unpackJSON(response.summary));
			$("#result_summary").show();
		}
		if (response.totalrows) {
			if (rows === "all") {
				$("#row_count_lbl").text(" - all " + response.totalrows + " rows.");
				$("#get_all_bottom").hide();
			} else if (rows >= response.totalrows) {
				$("#row_count_lbl").empty();
			} else {
				$("#row_count_lbl").text(" - " + rows + "/" + response.totalrows + " rows.");
				$("#get_all_bottom").show();
			}
		}
	}
}

function doGetLogfile() {
	instance = $("#hidInstanceID").val();

	if (instance === '') {
		return;
        }
	var response = ajaxPost("taskMethods/wmGetTaskLogfile", {
		sTaskInstance : instance
	}, "text");
	$("#logfile_text").html(unpackJSON(response));
	$("#logfile_dialog").dialog("open");
}

function doDebugStop() {
	instance = $("#hidInstanceID").val();

	if (instance === '') {
		return;
	}
	var response = ajaxPost("taskMethods/wmStopTask", {
		sInstance : instance
	});
	location.reload();
}

