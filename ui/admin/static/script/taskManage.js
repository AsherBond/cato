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

$(document).ready(function () {
    // clear the edit array
    $("#hidSelectedArray").val("");

    $("#edit_dialog").hide();
    $("#delete_dialog").hide();
    $("#export_dialog").hide();

    //define dialogs
    $('#edit_dialog').dialog('option', 'title', 'Create a New Task');
    $("#edit_dialog").dialog({
        autoOpen: false,
        modal: true,
        width: 500,
        buttons: {
            "Create": function () {
                showPleaseWait();
                SaveNewTask();
            },
            Cancel: function () {
                $("[id*='lblNewTaskMessage']").html("");
                $("#hidCurrentEditID").val("");

                $("#hidSelectedArray").val("");
                $("#lblItemsSelected").html("0");

                // nice, clear all checkboxes selected in a single line!
                $(':input', (".jtable")).attr('checked', false);

                $(this).dialog("close");
            }
        }
    });

    $("#export_dialog").dialog({
        autoOpen: false,
        modal: true,
        buttons: {
            "Export": function () {
                showPleaseWait();
                ExportTasks();
                $(this).dialog("close");
            },
            Cancel: function () {
                $(this).dialog("close");
            }
        }
    });
    $("#copy_dialog").dialog({
        autoOpen: false,
        modal: true,
        width: 500,
        buttons: {
            "Copy": function () {
                showPleaseWait();
                CopyTask();
            },
            Cancel: function () {
                $(this).dialog("close");
            }
        }
    });
    
    ManagePageLoad();
	GetItems();

});

function GetItems(page) {
	if (!page)
		page = "1"
    $.ajax({
        type: "POST",
        async: true,
        url: "taskMethods/wmGetTasksTable",
        data: '{"sSearch":"' + $("#txtSearch").val() + '", "sPage":"' + page + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
        	pager = unpackJSON(response.pager);
        	html = unpackJSON(response.rows);
        	
            $("#pager").html(pager);
        	$("#pager .pager_button").click(function () {
        		GetItems($(this).text());
        	});

            $("#tasks").html(html);
            //gotta restripe the table
            initJtable(true, true);

		    //what happens when you click a row?
		    $(".selectable").click(function () {
		        showPleaseWait();
		    	if ($(this).parent().attr("status") == "Approved") {
			        location.href = '/taskView?task_id=' + $(this).parent().attr("task_id");
			    } else {
			        location.href = '/taskEdit?task_id=' + $(this).parent().attr("task_id");
			    }
		    });

        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
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
    var task_code = '';

    $.ajax({
        type: "POST",
        async: false,
        url: "taskMethods/wmGetTaskCodeFromID",
        data: '{"sOriginalTaskID":"' + task_copy_original_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            if (response.code) {
                task_code = response.code;
                $("#lblTaskCopy").html('<b>Copying Task ' + task_code + '</b><br />&nbsp;<br />');
                $("[tag='chk']").attr("checked", false);
                $("#hidSelectedArray").val('');
                $("#hidCopyTaskID").val(task_copy_original_id);
                $("#lblItemsSelected").html("0");
                $("#txtCopyTaskName").val('');
                $("#txtCopyTaskCode").val('');
            // } else {
                // showAlert('No task code returned.');
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });

    // load the copy from versions drop down
    $.ajax({
        type: "POST",
        url: "taskMethods/wmGetTaskVersionsDropdown",
        data: '{"sOriginalTaskID":"' + task_copy_original_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "html",
        success: function (msg) {
            if (msg.length == 0) {
                showAlert('No versions found for this task?');
            } else {
                $("#ddlTaskVersions").html(msg);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });

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

    $.ajax({
        type: "POST",
        url: "taskMethods/wmCopyTask",
        data: '{"sCopyTaskID":"' + sCopyTaskID + '","sTaskCode":"' + sNewTaskCode + '","sTaskName":"' + sNewTaskName + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
        	if (response.error) {
        		showAlert(response.error);
        	} else if (response.info) {
        		showInfo(response.info);
        	} else if (response.id) {
                $("#copy_dialog").dialog("close");
                $("#txtSearch").val("");
                GetItems();
                hidePleaseWait();
                showInfo('Task Copy Successful.');
            } else {
                showAlert(response);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });



}


function DeleteItems() {
    //NOTE NOTE NOTE!!!!!!!
    //on this page, the hidSelectedArray is ORIGINAL TASK IDS.
    //take that into consideration.

    var ArrayString = $("#hidSelectedArray").val();
    $.ajax({
        type: "POST",
        url: "taskMethods/wmDeleteTasks",
        data: '{"sDeleteArray":"' + ArrayString + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (task) {
	       try {
		        if (task) {
		        	if (task.info) {
		        		showInfo(task.info, "", true);
		        	}

	                // clear the selected array, search field and fire a new search
	                $("#hidSelectedArray").val("");
	                $("#txtSearch").val("");
					GetItems();		
	                hidePleaseWait();
                	$("#update_success_msg").text("Delete Successful").show().fadeOut(2000);
		        }
		        
                $("#delete_dialog").dialog("close");
			} catch (ex) {
				showAlert(ex.message);
			}
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });

}
function ExportTasks() {
    //NOTE NOTE NOTE!!!!!!!
    //on this page, the hidSelectedArray is ORIGINAL TASK IDS.
    //take that into consideration.

	var args = {};
	args.sIncludeRefs = $("#export_dialog_include_refs").is(':checked')
	args.sTaskArray = $("#hidSelectedArray").val();

    $.ajax({
        type: "POST",
        url: "taskMethods/wmExportTasks",
        data: JSON.stringify(args),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
	        if (response.error) {
        		showAlert(response.error);
        	} else if (response.info) {
        		showInfo(response.info);
        	} else if (response.export_file) {
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
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
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
	if (sTaskCode.length < 1) {
        sValidationErr += "- Task Code is required.";
        bSave = false;
    }

    if (bSave != true) {
        showAlert(sValidationErr);
        return false;
    }

    sTaskName = packJSON(sTaskName);
    sTaskCode = packJSON(sTaskCode);
    sTaskDesc = packJSON(sTaskDesc);

    $.ajax({
        type: "POST",
        async: false,
        url: "taskMethods/wmCreateTask",
        data: '{"sTaskName":"' + sTaskName + '","sTaskCode":"' + sTaskCode + '","sTaskDesc":"' + sTaskDesc + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
	       try {
		        if (response.error) {
	        		showAlert(response.error);
	        	} else if (response.info) {
	        		showInfo(response.info);
	        	} else if (response.id) {
	                location.href = "/taskEdit?task_id=" + response.id;
		        } else {
		            showAlert(response);
		        }
			} catch (ex) {
				showAlert(ex.message);
			}
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

// function RenameBackupFile(src_file_name, otid) {
	// //real simple... call our rename webmethod for the file we just exported
// 	
	// //but first, build a new name from the task name.
	// x = $("tr[task_id='" + otid + "']").children()[2];
	// newname = $(x).text().trim().toLowerCase().replace(/ /g, "-");
// 	
	// newname = newname + ".csk";
// 
    // $.ajax({
        // type: "POST",
        // async: false,
        // url: "taskMethods.asmx/wmRenameFile",
        // data: '{"sExistingName":"' + src_file_name + '","sNewFileName":"' + newname + '"}',
        // contentType: "application/json; charset=utf-8",
        // dataType: "json",
        // success: function (response) {
            // //the return code might be a filename or an error.
            // //if it's valid, it will have a ".csk" in it.
            // //otherwise we assume it's an error
            // if (response.indexOf(".csk") > -1) {
            // } else {
                // showAlertresponse);
            // }
        // },
        // error: function (response) {
            // showAlert(response.responseText);
        // }
    // });
// 
	// return newname;
// }