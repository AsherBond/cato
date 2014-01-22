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
	$("#new_version_btn").button({
		icons : {
			primary : "ui-icon-extlink"
		}
	});
	$("#new_version_btn").click(function() {
		ShowVersionAdd();
	});

	$("#addVersion_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 400,
		buttons : {
			"New Version" : function() {
				CreateNewVersion();
			},
			"Cancel" : function() {
				$(this).dialog("close");
			}
		}
	});
});

function ShowVersionAdd() {
	$("#hidMode").val("add");
	$("#addVersion_dialog").dialog("open");
}

function CreateNewVersion() {
	$.blockUI({
		message : "Creating new version..."
	});

	var response = ajaxPost("taskMethods/wmCreateNewTaskVersion", {
		sTaskID : g_task_id,
		sMinorMajor : $("input[name='rbMinorMajor']:checked").val()
	}, "text");
	if (response) {
		// this is a little convoluted...
		// if we're already on the taskEdit page, things are fine, and we'll just
		// reload specific elements.

		//BUT -- if we're on the taskView page, a lot of stuff is different...
		// therefore our best bet is to just redirect to taskEdit.

		var pagename = window.location.pathname;
		pagename = pagename.substring(pagename.lastIndexOf('/') + 1);
		// things are page specific
		if (pagename == "taskView") {
			location.href = "taskEdit?task_id=" + response;
		} else {
			// already on taskEdit, just reload some content.
			//NOTE: this changes the g_task_id, and pushes a new URL into the address bar
			g_task_id = response
			history.replaceState({}, "", "taskEdit?task_id=" + g_task_id);
			//refresh the versions toolbox, which will add the new one...
			doGetVersions();

			//BUT WE must do this to set the "focus" of the page on the new version

			//get the details
			doGetDetails();
			//get the codeblocks
			doGetCodeblocks();
			//get the steps
			doGetSteps();
		}
	}

	$.unblockUI();
	$("#addVersion_dialog").dialog("close");

	return false;
}

function CloseVersionDialog() {
	$("#addVersion_dialog").dialog("close");

	return false;
}

function doGetVersions() {
	var response = ajaxPost("taskMethods/wmGetTaskVersions", {
		sTaskID : g_task_id
	}, "html");
	if (response) {
		$("#versions").html(response);
		//VERSION TOOLBOX
		$("#versions .version").disableSelection();

		//the onclick event of the 'version' elements
		//unbind it just to be safe
		$("#versions .version").unbind('click');
		$("#versions .version").click(function() {
			// so, if we're switching pages it does a full redirect.  But, if the target
			// status is the same, we'll just update some content.
			var pagename = window.location.pathname;
			pagename = pagename.substring(pagename.lastIndexOf('/') + 1);
			if ($(this).attr("status") == "Approved" && pagename !== "taskView") {
				location.href = "taskView?task_id=" + $(this).attr("task_id");
				return;
			}
			if ($(this).attr("status") == "Development" && pagename !== "taskEdit") {
				location.href = "taskEdit?tab=versions&task_id=" + $(this).attr("task_id");
				return;
			}

			// If there was a mismatch we'll never get here.  So, if we're here... it must be
			// the same page, so we can just update some content.
			//NOTE: this changes the g_task_id, and pushes a new URL into the address bar
			g_task_id = $(this).attr("task_id")
			history.replaceState({}, "", pagename + "?task_id=" + g_task_id);
			$("#versions .version").removeClass("version_selected")
			$(this).addClass("version_selected");

			// things are page specific
			if (pagename == "taskView") {
				doGetViewDetails();
				doGetViewSteps();
			}

			if (pagename == "taskEdit") {
				doGetDetails();
				doGetCodeblocks();
				doGetSteps();
			}

		});

		//whatever the current version is... change it's class in the list
		$("#v_" + g_task_id).addClass("version_selected");
	}
}
