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
    $('#edit_dialog').dialog('option', 'title', 'New Ecotemplate');
    $("#edit_dialog").dialog({
        autoOpen: false,
        modal: true,
        width: 650,
        buttons: [
        	{
            	id: "edit_dialog_create_btn",
            	text: "Create",
            	click: function() {
                	Save();
            	}
        	},
            {
            	text: "Cancel",
            	click: function () {
	                $("[id*='lblNewMessage']").html("");
	                $("#hidCurrentEditID").val("");
	
	                $("#hidSelectedArray").val("");
	                $("#lblItemsSelected").html("0");
	
	                // nice, clear all checkboxes selected in a single line!
	                $(':input', (".jtable")).attr('checked', false);
	
	                $(this).dialog("close");
            	}
            }
        ]
    });

    $("#export_dialog").dialog({
        autoOpen: false,
        modal: true,
        width: 500,
        buttons: {
            "Export": function () {
                showPleaseWait();
                ExportEcotemplates();
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
                CopyTemplate();
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
        url: "ecoMethods/wmGetEcotemplatesTable",
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

            $("#ecotemplates").html(html);
            //gotta restripe the table
            initJtable(true, true);

		    //what happens when you click a row?
		    $(".selectable").click(function () {
		        showPleaseWait();
		        location.href = '/ecoTemplateEdit?ecotemplate_id=' + $(this).parent().attr("ecotemplate_id");
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
    
    //but we want the Format box to be checked
    $('#chk_reformat').attr('checked','checked')
	$(".stormfields").hide();
    $("#edit_dialog").dialog("open");
    $("#txtTemplateName").focus();
}

function ShowItemExport() {
    // clear all of the previous values
    var ArrayString = $("#hidSelectedArray").val();
    if (ArrayString.length == 0) {
        showInfo('Select an Ecosystem Template to Export.');
        return false;
    }
    if (ArrayString.indexOf(",") > -1) {
    	//make a comment and clear the selection.
        showInfo('Only one Ecosystem Template can be exported at a time.');
        ClearSelectedRows();
        return false;
    }
	
    $("#export_dialog").dialog("open");
}

function DeleteItems() {
    var ArrayString = $("#hidSelectedArray").val();
    $.ajax({
        type: "POST",
        url: "ecoMethods/wmDeleteEcotemplates",
        data: '{"sDeleteArray":"' + ArrayString + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
        	if (response.info) {
    			showInfo(response.info);
        	} else if (response.error) {
        		showAlert(response.error);
            } else if (response.result == "success") {
                $("#hidSelectedArray").val("");
                $("#delete_dialog").dialog("close");

                // clear the search field and fire a search click, should reload the grid
                $("#txtSearch").val("");
                GetItems();

                hidePleaseWait();
                showInfo('Delete Successful');
            } else {
                showAlert(response);

                $("#delete_dialog").dialog("close");
                
                // reload the list, some may have been deleted.
                // clear the search field and fire a search click, should reload the grid
                $("#txtSearch").val("");
                GetItems();
            }

            $("#hidSelectedArray").val("");
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });

}

function ExportEcotemplates() {
    var ArrayString = $("#hidSelectedArray").val();
    var include_tasks = ($('#export_include_tasks').attr('checked') == "checked" ? 1 : 0);
    $.ajax({
        type: "POST",
        url: "uiMethods.asmx/wmExportEcotemplates",
        data: '{"sEcotemplateArray":"' + ArrayString + '", "sIncludeTasks":"' + include_tasks + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            //the return code might be a filename or an error.
            //if it's valid, it will have a ".xml" in it.
            //otherwise we assume it's an error
            if (response.indexOf(".xml") > -1) {
                //developer utility for renaming the file
                //note: only works with one task at a time.
                //var filename = RenameBackupFile(msg.d, ArrayString);
                //the NORMAL way
                var filename = response;
                
                $("#hidSelectedArray").val("");
                $("#export_dialog").dialog("close");

			    $("#txtSearch").val("");
			   	GetItems();

                hidePleaseWait();

                //ok, we're gonna do an iframe in the dialog to force the
                //file download
                var html = "Click <a href='fileDownload.ashx?filename=" + filename + "'>here</a> to download your file.";
                html += "<iframe id='file_iframe' width='0px' height=0px' src='fileDownload.ashx?filename=" + filename + "'>";
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

function Save() {
    var bSave = true;
    var strValidationError = '';

    //some client side validation before we attempt to save the user
    if ($("#txtTemplateName").val() == "") {
        bSave = false;
        strValidationError += 'Name is required.';
    };

    if (bSave != true) {
        showAlert(strValidationError);
        return false;
    }

	var name = packJSON($("#txtTemplateName").val());
	var desc = packJSON($("#txtTemplateDesc").val());
	var sfs = packJSON($("#ddlStormFileSource").val());
	var sf = packJSON($("#txtStormFile").val());
	
    $.ajax({
        async: false,
        type: "POST",
        url: "ecoMethods/wmCreateEcotemplate",
        data: '{"sName":"' + name + '","sDescription":"' + desc + '","sStormFileSource":"' + sfs + '","sStormFile":"' + sf + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
        	if (response.info) {
    			showInfo(response.info);
        	} else if (response.error) {
        		showAlert(response.error);
            } else if (response.ecotemplate_id) {
            	showPleaseWait();
            	
            	//pass a flag if the "run now" box was checked.
            	var runqs = ($("#chkStormRunNow")[0].checked ? "&run=true" : "");
            	
                location.href = "ecoTemplateEdit?ecotemplate_id=" + response.ecotemplate_id + runqs;
            } else {
            	showInfo(response, "", true);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}


function ShowItemCopy() {
    // clear all of the previous values
    var ArrayString = $("#hidSelectedArray").val();
    if (ArrayString.length == 0) {
        showInfo('Select an Ecosystem Template to Copy.');
        return false;
    }
    if (ArrayString.indexOf(",") > -1) {
    	//make a comment and clear the selection.
        showInfo('Only one Ecosystem Template can be copied at a time.');
        ClearSelectedRows();
        return false;
    }
	$("#txtCopyEcotemplateName").val("");
	$("#copy_dialog").dialog("open");
}
function CopyTemplate() {
	var sSelectedTemplateID = $("#hidSelectedArray").val();
    var sNewTemplateName = $("#txtCopyEcotemplateName").val();

    // make sure we have all of the valid fields
    if (sNewTemplateName == '') {
        showInfo('A new Name is required.');
        return false;
    }

    $.ajax({
        type: "POST",
        url: "ecoMethods/wmCopyEcotemplate",
        data: '{"sEcoTemplateID":"' + sSelectedTemplateID + '","sNewName":"' + sNewTemplateName + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
        	if (response.info) {
    			showInfo(response.info);
        	} else if (response.error) {
        		showAlert(response.error);
            } else if (response.ecotemplate_id) {
                showInfo('Copy Successful.');
			    // clear the search field and reload the grid
			    $("#txtSearch").val("");
			   	GetItems();
            } else {
                showInfo(response);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });

    hidePleaseWait();
    $("#copy_dialog").dialog("close");
}
