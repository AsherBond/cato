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
	// clear the edit array
	$("#hidSelectedArray").val("");

	$("#edit_dialog").hide();
	$("#delete_dialog").hide();
	$("#export_dialog").hide();

	//define dialogs
	$("#edit_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 500,
		buttons : {
			"Create" : function() {
				showPleaseWait();
				SaveNewTask();
			},
			Cancel : function() {
				$("[id*='lblNewTaskMessage']").html("");
				$("#hidCurrentEditID").val("");

				$("#hidSelectedArray").val("");
				$("#lblItemsSelected").html("0");

				// nice, clear all checkboxes selected in a single line!
				$(':input', (".jtable")).prop('checked', false);

				$(this).dialog("close");
			}
		}
	});

	$("#export_dialog").dialog({
		autoOpen : false,
		modal : true,
		buttons : {
			"Export" : function() {
				showPleaseWait();
				ExportTasks();
				$(this).dialog("close");
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});
	$("#copy_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 500,
		buttons : {
			"Copy" : function() {
				showPleaseWait();
				CopyTask();
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});

	ManagePageLoad();
	GetItems();

});

function GetItems(page) {
	if (!page)
		page = "1";
	var response = ajaxPost("taskMethods/wmGetTasksTable", {
		sSearch : $("#txtSearch").val(),
		sPage : page
	});
	if (response) {
		var pager = unpackJSON(response.pager);
		var html = unpackJSON(response.rows);

		$("#pager").html(pager);
		$("#pager .pager_button").click(function() {
			GetItems($(this).text());
		});

		$("#tasks").html(html);
		//gotta restripe the table
		initJtable(true, true);

		//what happens when you click a row?
		$(".selectable").click(function() {
			showPleaseWait();
			if ($(this).parent().attr("status") == "Approved") {
				location.href = '/taskView?task_id=' + $(this).parent().attr("task_id");
			} else {
				location.href = '/taskEdit?task_id=' + $(this).parent().attr("task_id");
			}
		});

		// a run button on the task list!
		$(".task_run").click(function() {
			event.stopPropagation();
			var task_id = $(this).parent().attr("task_id");
			var task_name = $(this).parent().find("td")[2].innerHTML + " - " + $(this).parent().find("td")[3].innerHTML;

			var args = {};
			args.task_id = task_id;
			args.task_name = task_name;
			args.debug_level = 4;

			//note: we are not passing the account_id - the dialog will use the default
			ShowTaskLaunchDialog(args);
		});

	}
}

function ShowItemAdd() {
	$("#hidMode").val("add");

	// clear all of the previous values
	clearEditDialog();

	$("#edit_dialog").dialog("open");
	$("#txtTaskCode").focus();
}

function ShowItemExport() {
	// clear all of the previous values
	var ArrayString = $("#hidSelectedArray").val();
	if (ArrayString.length == 0) {
		showInfo('No Items selected.');
		return false;
	}

	$("#export_dialog").dialog("open");
}

function ShowItemCopy() {
	// clear all of the previous values
	var ArrayString = $("#hidSelectedArray").val();
	if (ArrayString.length == 0) {
		showInfo('Select a Task to Copy.');
		return false;
	}

	// before loading the task copy dialog, we need to get the task_code for the
	// first task selected, to be able to show something useful in the copy message.
	var myArray = ArrayString.split(',');

	var task_copy_original_id = myArray[0];

	//alert(myArray[0]);
	var task_name = $("[task_id=" + task_copy_original_id +"] td")[2].innerHTML;
	$("#lblTaskCopy").html('<b>Copying Task ' + task_name + '</b><br />&nbsp;<br />');
	$("[tag='chk']").prop("checked", false);
	$("#hidSelectedArray").val('');
	$("#hidCopyTaskID").val(task_copy_original_id);
	$("#lblItemsSelected").html("0");
	$("#txtCopyTaskName").val('');
	$("#txtCopyTaskCode").val('');

	var msg = ajaxPost("taskMethods/wmGetTaskVersionsDropdown", {
		sOriginalTaskID : task_copy_original_id
	}, "html");
	if (msg) {
		// load the copy from versions drop down
		if (msg.length == 0) {
			showAlert('No versions found for this task?');
		} else {
			$("#ddlTaskVersions").html(msg);
		}
	}

	$("#copy_dialog").dialog("open");
}

function CopyTask() {
	var sNewTaskName = $("#txtCopyTaskName").val();
	var sNewTaskCode = $("#txtCopyTaskCode").val();
	var sCopyTaskID = $("#ddlTaskVersions").val();

	// make sure we have all of the valid fields
	if (sNewTaskName == '' || sNewTaskCode == '') {
		showInfo('Task Name and Task Code are required.');
		return false;
	}
	// this shouldnt happen, but just in case.
	if (sCopyTaskID == '') {
		showInfo('Can not copy, no version selected.');
		return false;
	}

	var response = ajaxPost("taskMethods/wmCopyTask", {
		sCopyTaskID : sCopyTaskID,
		sTaskCode : sNewTaskCode,
		sTaskName : sNewTaskName
	});
	if (response) {
		$("#copy_dialog").dialog("close");
		$("#txtSearch").val("");
		GetItems();
		hidePleaseWait();
		showInfo('Task Copy Successful.');
	}
}

function DeleteItems() {
	//NOTE NOTE NOTE!!!!!!!
	//on this page, the hidSelectedArray is ORIGINAL TASK IDS.
	//take that into consideration.
	var args = {};
	args.sDeleteArray = $("#hidSelectedArray").val();
	args.sForce = $("#delete_dialog_force").is(':checked');

	var response = ajaxPost("taskMethods/wmDeleteTasks", args);
	if (response) {
		// clear the selected array, search field and fire a new search
		$("#hidSelectedArray").val("");
		$("#txtSearch").val("");
		GetItems();
		hidePleaseWait();
		$("#update_success_msg").text("Delete Successful").show().fadeOut(2000);
		$("#delete_dialog_force").prop("checked", false);
		$("#delete_dialog").dialog("close");
	}
}

function ExportTasks() {
	//NOTE NOTE NOTE!!!!!!!
	//on this page, the hidSelectedArray is ORIGINAL TASK IDS.
	//take that into consideration.

	var args = {};
	args.sIncludeRefs = $("#export_dialog_include_refs").is(':checked');
	args.sTaskArray = $("#hidSelectedArray").val();

	var response = ajaxPost("taskMethods/wmExportTasks", args);
	if (response) {
		if (response.export_file) {
			//developer utility for renaming the file
			//note: only works with one task at a time.
			//var filename = RenameBackupFile(msg.d, ArrayString);
			//the NORMAL way
			var filename = response.export_file;

			$("#hidSelectedArray").val("");
			$("#export_dialog").dialog("close");

			//ok, we're gonna do an iframe in the dialog to force the
			//file download
			var html = "Click <a href='temp/" + filename + "' target='_blank'>here</a> to download your file.";
			html += "<iframe id='file_iframe' width='0px' height=0px' src='temp/" + filename + "'>";

			hidePleaseWait();
			showInfo('Export Successful', html, true);
		} else {
			showAlert(response);
		}
	}
}

function SaveNewTask() {
	var bSave = true;
	var sValidationErr = "";

	//some client side validation before we attempt to save
	var sTaskName = $("#txtTaskName").val();
	var sTaskCode = $("#txtTaskCode").val();
	var sTaskDesc = $("#txtTaskDesc").val();

	if (sTaskName.length < 3) {
		sValidationErr += "- Task Name is required and must be at least three characters in length.<br />";
		bSave = false;
	}

	if (bSave !== true) {
		showAlert(sValidationErr);
		return false;
	}

	sTaskName = packJSON(sTaskName);
	sTaskCode = packJSON(sTaskCode);
	sTaskDesc = packJSON(sTaskDesc);

	var response = ajaxPost("taskMethods/wmCreateTask", {
		sTaskName : sTaskName,
		sTaskCode : sTaskCode,
		sTaskDesc : sTaskDesc
	});
	if (response) {
		location.href = "/taskEdit?task_id=" + response.id;
	}
}
