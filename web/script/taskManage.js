﻿$(document).ready(function () {
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

                $(this).dialog('close');
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
                $(this).dialog('close');
            },
            Cancel: function () {
                $(this).dialog('close');
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
                $(this).dialog('close');
            }
        }
    });
    
    //what happens when you click a row?
    $("[tag='selectable']").live("click", function () {
        showPleaseWait();
        location.href = 'taskEdit.aspx?task_id=' + $(this).parent().attr("task_id");
    });
});

function pageLoad() {
    ManagePageLoad();
}

function ShowItemAdd() {
    $("#hidMode").val("add");

    // clear all of the previous values
    clearEditDialog();

    $("#edit_dialog").dialog('open');
    $("#txtTaskName").focus();
}

function ShowItemExport() {
    // clear all of the previous values
    var ArrayString = $("#hidSelectedArray").val();
    if (ArrayString.length == 0) {
        showInfo('No Items selected.');
        return false;
    }

    $("#export_dialog").dialog('open');
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
        url: "taskMethods.asmx/wmGetTaskCodeFromID",
        data: '{"sOriginalTaskID":"' + task_copy_original_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {

            if (msg.d.length == 0) {

                showAlert('No task code returned.');

            } else {

                //showAlert(msg.d);
                task_code = msg.d;
                $("#lblTaskCopy").html('<b>Copying task ' + task_code + '</b><br />&nbsp;<br />');
                $("#copy_dialog").dialog('open');
                $("[tag='chk']").attr("checked", false);
                $("#hidSelectedArray").val('');
                $("#hidCopyTaskID").val(task_copy_original_id);
                $("#lblItemsSelected").html("0");
                $("[jqname='txtCopyTaskName']").val('');
                $("[jqname='txtCopyTaskCode']").val('');
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });

    // load the copy from versions drop down
    $.ajax({
        type: "POST",
        url: "taskMethods.asmx/wmGetTaskVersionsDropdown",
        data: '{"sOriginalTaskID":"' + task_copy_original_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {

            if (msg.d.length == 0) {

                showAlert('No versions found for this task?');

            } else {

                $("#divTaskVersions").html(msg.d);

            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });




}
function CopyTask() {


    var sNewTaskName = $("[jqname='txtCopyTaskName']").val();
    var sNewTaskCode = $("[jqname='txtCopyTaskCode']").val();
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
        url: "taskMethods.asmx/wmCopyTask",
        data: '{"sCopyTaskID":"' + sCopyTaskID + '","sTaskCode":"' + sNewTaskCode + '","sTaskName":"' + sNewTaskName + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            if (msg.d.length == 36) {
                $("#copy_dialog").dialog('close');
                // clear the search field and fire a search click, should reload the grid
                $("#ctl00_phDetail_txtSearch").val("");
                $("#ctl00_phDetail_btnSearch").click();

                hidePleaseWait();
                showInfo('Task Copy Successful.');
            } else {
                showAlert(msg.d);
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
        url: "taskMethods.asmx/wmDeleteTasks",
        data: '{"sDeleteArray":"' + ArrayString + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            if (msg.d.length == 0) {

                $("#hidSelectedArray").val("");

                // clear the search field and fire a search click, should reload the grid
                $("#ctl00_phDetail_txtSearch").val("");
                $("#ctl00_phDetail_btnSearch").click();

                hidePleaseWait();
                showInfo('Delete Successful');

            } else {
                showAlert(msg.d);
                // reload the list, some may have been deleted.
                // clear the search field and fire a search click, should reload the grid
                $("#ctl00_phDetail_txtSearch").val("");
                $("#ctl00_phDetail_btnSearch").click();
            }

            $("#delete_dialog").dialog('close');
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

    var ArrayString = $("#hidSelectedArray").val();
    $.ajax({
        type: "POST",
        url: "taskMethods.asmx/wmExportTasks",
        data: '{"sTaskArray":"' + ArrayString + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            //the return code might be a filename or an error.
            //if it's valid, it will have a ".csk" in it.
            //otherwise we assume it's an error
            if (msg.d.indexOf(".csk") > -1) {
                //developer utility for renaming the file
                //note: only works with one task at a time.
                //var filename = RenameBackupFile(msg.d, ArrayString);
                //the NORMAL way
                var filename = msg.d;
                
                $("#hidSelectedArray").val("");
                $("#export_dialog").dialog('close');

                // clear the search field and fire a search click, should reload the grid
                $("#ctl00_phDetail_txtSearch").val("");
                $("#ctl00_phDetail_btnSearch").click();

                hidePleaseWait();

                //ok, we're gonna do an iframe in the dialog to force the
                //file download
                var html = "Click <a href='../temp/" + filename + "'>here</a> to download your file.";
                html += "<iframe width='0px' height=0px' src='../temp/" + filename + "'>";
                showInfo('Export Successful', html, true);

            } else {
                showAlert(msg.d);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

function SaveNewTask() {
    var bSave = true;
    var strValidationError = '';
    
    //some client side validation before we attempt to save
    var sTaskName = packJSON($("[jqname='txtTaskName']").val());
    var sTaskCode = packJSON($("[jqname='txtTaskCode']").val());
    var sTaskDesc = packJSON($("[jqname='txtTaskDesc']").val());

    if (bSave != true) {
        showAlert(strValidationError);
        return false;
    }

    $.ajax({
        type: "POST",
        url: "taskMethods.asmx/wmCreateTask",
        data: '{"sTaskName":"' + sTaskName + '","sTaskCode":"' + sTaskCode + '","sTaskDesc":"' + sTaskDesc + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
	        if (msg.d.length != 0) {
	            //I don't like this.. evidently an ajax call can only have one return value, a string.
	            //so it might be the success value (my task_id) or it may be an error.
	            //I gotta parse the result to know for sure. Ugh.
	            //so instead of just returning the guid, I'm returning task_id=guid.
	            //that way I can peek in the string for 'task_id' and know I have what I want.
	            if (msg.d.indexOf("task_id") == 0) {
	                location.href = "taskEdit.aspx?" + msg.d;
	            } else {
	                hidePleaseWait();
	                showAlert(msg.d);
	            }
	        } else {
	            hidePleaseWait();
	            showAlert("Error: Task was created, but ID was not returned.");
	        }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });

}

function RenameBackupFile(src_file_name, otid) {
	//real simple... call our rename webmethod for the file we just exported
	
	//but first, build a new name from the task name.
	x = $("tr[task_id='" + otid + "']").children()[2];
	newname = $(x).text().trim().toLowerCase().replace(/ /g, "-");
	
	newname = newname + ".csk";

    $.ajax({
        type: "POST",
        async: false,
        url: "taskMethods.asmx/wmRenameFile",
        data: '{"sExistingName":"' + src_file_name + '","sNewFileName":"' + newname + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            //the return code might be a filename or an error.
            //if it's valid, it will have a ".csk" in it.
            //otherwise we assume it's an error
            if (msg.d.indexOf(".csk") > -1) {
            } else {
                showAlert(msg.d);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });

	return newname;
}