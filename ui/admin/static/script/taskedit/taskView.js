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

//some code is shared between taskEdit and taskView pages.  That shared code is in this file.
//because we dont' want to include taskEdit.js all over the place, it's full of stuff specific to that page.

$(document).ready(function() {
	//used a lot
	g_task_id = getQuerystringVariable("task_id");

	//jquery buttons
	$("#asset_search_btn").button({
		icons : {
			primary : "ui-icon-search"
		}
	});

	//asset, print and show log links
	//the print link
	$("#print_link").live("click", function() {
		var url = "taskPrint?task_id=" + g_task_id;
		openWindow(url, "taskPrint", "location=no,status=no,scrollbars=yes,resizable=yes,width=800,height=700");
	});

	//the show log link
	$("#show_log_link").button({
		icons : {
			primary : "ui-icon-document"
		}
	});
	$("#show_log_link").click(function() {
		ShowLogViewDialog(3, g_task_id, true);
	});

	//the show runlog link
	$("#show_runlog_link").button({
		icons : {
			primary : "ui-icon-document"
		}
	});
	$("#show_runlog_link").click(function() {
		var url = "taskRunLog?task_id=" + g_task_id;
		openWindow(url, "TaskRunLog" + g_task_id, "location=no,status=no,scrollbars=yes,resizable=yes,width=800,height=700");
	});

	$("#set_default_btn").button({
		icons : {
			primary : "ui-icon-check"
		}
	});
	$("#set_default_btn").click(function() {
		var response = ajaxPost("taskMethods/wmTaskSetDefault", {
			sTaskID : g_task_id
		});
		if (response) {
			$("#update_success_msg").text("Update Successful").fadeOut(2000);

			doGetVersions();
			// add (default) to the page header label
			$("#lblVersionHeader").text($("#lblVersionHeader").text() + " (default)");
		}
	});

	// the schedule tab has refresh buttons
	$(".refresh_plans_btn").click(function() {
		doGetPlans();
	});

	// this code is shared by many pages, but a few things should happen only on the taskView page.
	var pagename = window.location.pathname;
	pagename = pagename.substring(pagename.lastIndexOf('/') + 1);
	if (pagename == "taskView") {
		doGetViewDetails();
		doGetViewSteps();
	}
});

function doGetViewDetails() {
	var task = ajaxPost("taskMethods/wmGetTask", {
		sTaskID : g_task_id
	});
	if (task) {
		$("#hidOriginalTaskID").val(task.OriginalTaskID);
		$("#lblTaskCode").text(task.Code);
		$("#lblDescription").text(task.Description);
		$("#lblConcurrentInstances").text(task.ConcurrentInstances);
		$("#lblQueueDepth").text(task.QueueDepth);

		$("#lblVersion").text(task.Version);
		$("#lblCurrentVersion").text(task.Version);
		$("#lblStatus").text(task.Status);
		$("#lblStatus2").text(task.Status);

		$("#lblNewMinorVersion").text(task.NextMinorVersion);
		$("#lblNewMajorVersion").text(task.NextMajorVersion);

		/*
		 * ok, this is important.
		 * there are some rules for the process of 'Approving' a task.
		 * specifically:
		 * -- if there are no other approved tasks in this family, this one will become the default.
		 * -- if there is another approved task in this family, we show the checkbox
		 * -- allowing the user to decide whether or not to make this one the default
		 */
		if (task.NumberOfApprovedVersions > "0")
			$("#chkMakeDefault").show();
		else
			$("#chkMakeDefault").hide();

		//the header
		$("#lblTaskNameHeader").text(task.Name);
		$("#lblVersionHeader").text(task.Version + (task.IsDefaultVersion == "True" ? " (default)" : ""));

		if (task.IsDefaultVersion == "True") {
			$("#set_default_btn").hide();
		} else {
			$("#set_default_btn").show();
		}
	}
}

function doGetViewSteps() {
	var response = ajaxPost("taskMethods/wmGetStepsPrint", {
		sTaskID : g_task_id
	}, "text");
	$("#codeblock_steps").html(response);
}

function tabWasClicked(tab) {
	//load on this page is taking too long.  So, we'll get the tab content on click instead.
	//NOTE: shared on several pages, so there might be some cases here that don't apply to all pages.
	//not a problem, they just won't be hit.

	if (tab == "parameters") {
		doGetParams("task", g_task_id);
	} else if (tab == "versions") {
		doGetVersions();
	} else if (tab == "schedules") {
		doGetPlans();
	} else if (tab == "tags") {
		if ( typeof (GetObjectsTags) != 'undefined') {
			GetObjectsTags($("#hidOriginalTaskID").val());
		}
	} else if (tab == "clipboard") {
		doGetClips();
	} else if (tab == "debug") {
		doGetDebug();
	} else if (tab == "details") {
		doGetDetails();
	}
}

function doGetPlans() {
	var response = ajaxPost("uiMethods/wmGetActionPlans", {
		sTaskID : g_task_id
	}, "html");
	if (response == "") {
		$("#div_schedules #toolbox_plans").html("No Active Plans");
	} else {
		$("#div_schedules #toolbox_plans").html(response);

		//click on an action plan in the toolbox pops the dialog AND the inner dialog
		$("#div_schedules #toolbox_plans .action_plan_name").click(function() {
			var task_name = $("#lblTaskNameHeader").html() + " - " + $("#lblVersionHeader").html();
			var args = {};
			args.task_id = g_task_id;
			args.task_name = task_name;
			args.debug_level = 4;

			ShowTaskLaunchDialog(args);
			ShowPlanEditDialog(this);
		});
	}

	var response = ajaxPost("uiMethods/wmGetActionSchedules", {
		sTaskID : g_task_id
	}, "html");
	if (response == "") {
		$("#div_schedules #toolbox_schedules").html("No Active Schedules");
	} else {
		$("#div_schedules #toolbox_schedules").html(response);

		//schedule icon tooltips
		$("#div_schedules #toolbox_schedules .schedule_tip").tipTip({
			defaultPosition : "right",
			keepAlive : false,
			activation : "hover",
			maxWidth : "500px",
			fadeIn : 100
		});

		//click on a schedule in the toolbox - pops the edit dialog and the inner dialog
		$("#div_schedules #toolbox_schedules .schedule_name").click(function() {
			var task_name = $("#lblTaskNameHeader").html() + " - " + $("#lblVersionHeader").html();
			var args = {};
			args.task_id = g_task_id;
			args.task_name = task_name;
			args.debug_level = 4;

			ShowTaskLaunchDialog(args);
			ShowPlanEditDialog(this);
		});

	}
}

