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

	//init the asset picker dialog
	$("#asset_picker_dialog").dialog({
		autoOpen : false,
		draggable : false,
		resizable : false,
		bgiframe : true,
		modal : true,
		height : 600,
		width : 600,
		overlay : {
			backgroundColor : '#000',
			opacity : 0.5
		},
		close : function(event, ui) {
			$("#asset_search_text").val("");
			$("#asset_picker_results").empty();
		}
	});

	$("#debug_run_btn").button({
		icons : {
			primary : "ui-icon-play"
		}
	});
	$("#debug_stop_btn").button({
		icons : {
			primary : "ui-icon-stop"
		}
	});
	$("#debug_view_active_log").button({
		icons : {
			primary : "ui-icon-document"
		}
	});

	//    //the visual effect for the 'debug' buttons, set on page load
	//    if ($("[id$='lblCurrentStatus']").text() == "Aborting") {
	//        $("#debug_stop_btn").addClass("debug_btn_dim")
	//        $("#debug_run_btn").addClass("debug_btn_dim")
	//    } else if ($("[id$='lblCurrentStatus']").text() == "Inactive") {
	//        $("#debug_stop_btn").addClass("debug_btn_dim")
	//        $("#debug_run_btn").removeClass("debug_btn_dim")
	//    } else {
	//        $("#debug_run_btn").addClass("debug_btn_dim")
	//        $("#debug_stop_btn").removeClass("debug_btn_dim")
	//    }

	//temporary
	$("#debug_run_btn").removeClass("debug_btn_dim")
	$("#debug_stop_btn").removeClass("debug_btn_dim")

	//the click events for the 'debug' buttons
	$("#debug_run_btn").click(function() {
		//don't start it unless it's 'inactive'
		//if ($("[id$='lblCurrentStatus']").text() == "Inactive") {

		var task_name = $("#lblTaskNameHeader").html() + " - " + $("#lblVersionHeader").html();
		var asset_id = $("#txtTestAsset").attr("asset_id");

		var args = '{"task_id":"' + g_task_id + '", "task_name":"' + task_name + '", "debug_level":"4"}';

		//note: we are not passing the account_id - the dialog will use the default
		ShowTaskLaunchDialog(args);
	});
	$("#debug_stop_btn").click(function() {
		doDebugStop();
	});

	//bind the debug show log button
	$("#debug_view_latest_log").click(function() {
		openDialogWindow('taskRunLog?task_id=' + g_task_id, 'TaskRunLog' + g_task_id, 950, 750, 'true');
	});
	//bind the debug show active log button
	$("#debug_view_active_log").click(function() {
		var aid = $("#debug_instance").html();
		if (aid != "") {
			openDialogWindow('taskRunLog?task_instance=' + aid, 'TaskRunLog' + aid, 950, 750, 'true');
		}
	});

	$("#debug_asset_clear_btn").click(function() {
		$("#txtTestAsset").val("");
		$("#txtTestAsset").attr("asset_id", "");
		doSaveDebugAsset();
	});

	//////ASSET PICKER
	//the onclick event of the 'asset picker' buttons everywhere
	$(".asset_picker_btn").live("click", function() {
		$("#asset_picker_target_field").val($(this).attr("link_to"));
		$("#asset_picker_target_name_field").val($(this).attr("target_field_id"));
		$("#asset_picker_dialog").dialog("open");
		$("#asset_search_text").focus();
	});
	// when you hit enter inside an asset search
	$("#asset_search_text").live("keypress", function(e) {
		//alert('keypress');
		if (e.which == 13) {
			$("#asset_search_btn").click();
			return false;
		}
	});
	//the onclick event of the 'asset picker' search button
	$("#asset_search_btn").click(function() {
		var field = $("#" + $("#asset_picker_target_field").val());

		$("#asset_picker_dialog").block({
			message : null,
			cursor : 'wait'
		});
		var search_text = $("#asset_search_text").val();
		var response = ajaxPost("uiMethods/wmAssetSearch", {
			sSearch : search_text,
			bAllowMultiSelect : false
		}, "html");
		if (response) {
			$("#asset_picker_results").html(response);
			//bind the onclick event for the new results
			$("#asset_picker_results .asset_picker_value").disableSelection();
			$("#asset_picker_dialog").unblock();
			$("#asset_picker_results li[tag='asset_picker_row']").click(function() {

				if ($("#asset_picker_target_field").val() == "txtTestAsset") {
					field.val($(this).attr("asset_name"))
					//this is the picker for the Debug tab
					field.attr("asset_id", $(this).attr("asset_id"));
					doSaveDebugAsset();

				} else {
					// this is a picker somewhere on a step
					field.val($(this).attr("asset_id"))
					// we need an id hidden, and a name displayed
					var namefield = $("#" + $("#asset_picker_target_name_field").val());
					namefield.val($(this).attr("asset_name"))

					//disable the "name" field...
					namefield.attr('disabled', 'disabled');

					//turn off any syntax checking on the "name" field... and reset the style
					namefield.removeAttr('syntax');
					namefield.removeClass('is_required');

					field.change();
				}

				$("#asset_picker_dialog").dialog("close");
				$("#asset_picker_results").empty();
			});

			//if we set up the table, commit the change to the database here.
		}
	});
	//////END ASSET PICKER
});

function doDebugStop() {
	//don't stop it unless it's running
	//current_status = $("[id$='lblCurrentStatus']").text();

	//if (current_status != "Inactive" && current_status != "Aborting") {
	$("#update_success_msg").text("Stopping...").fadeIn(200);

	if ($("#debug_instance").html() == '')
		return;

	var response = ajaxPost("taskMethods/wmStopTask", {
		sInstance : $("#debug_instance").html()
	});
	if (response) {
		doGetDebug();

		//                //after stopping, set the visualness
		//                $("#debug_run_btn").removeClass("debug_btn_dim")
		//                $("#debug_stop_btn").addClass("debug_btn_dim")
		//                $("[id$='lblCurrentStatus']").text("Inactive")

		//$("#task_steps").unblock();
		$("#update_success_msg").text("Stop Successful").fadeOut(2000);
	}
}

function doSaveDebugAsset() {
	var asset_id = $("#txtTestAsset").attr("asset_id");
	$("#update_success_msg").text("Updating...").show();

	var response = ajaxPost("taskMethods/wmSaveTestAsset", {
		sTaskID : g_task_id,
		sAssetID : asset_id
	});
	$("#update_success_msg").text("Update Successful").fadeOut(2000);
}

function doGetDebug() {
	var debug = ajaxPost("taskMethods/wmGetTaskRunLogDetails", {
		sTaskID : g_task_id
	});
	if (debug) {
		$("#debug_submitted").html(debug.submitted_dt);
		$("#debug_completed").html(debug.completed_dt);
		$("#debug_status").html(debug.task_status);
		$("#debug_instance").html(debug.task_instance);
		$("#debug_submitted_by").html(debug.submitted_by);

		$("#debug_last_run").show();
	}
}