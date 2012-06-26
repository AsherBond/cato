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

    //define dialogs
    $('#edit_dialog').dialog('option', 'title', 'New Ecosystem');
    $("#edit_dialog").dialog({
        autoOpen: false,
        modal: true,
        width: 500,
        buttons: {
            "Create": function () {
                showPleaseWait();
                Save();
            },
            Cancel: function () {
                $("#lblNewMessage").html("");
                $("#hidCurrentEditID").val("");

                $("#hidSelectedArray").val("");
                $("#lblItemsSelected").html("0");

                // nice, clear all checkboxes selected in a single line!
                $(':input', (".jtable")).attr('checked', false);

                $(this).dialog("close");
            }
        }
    });

    ManagePageLoad();
	GetItems();
	FillEcotemplatesDropdown();
});

function GetItems() {
	var account_id = $("#header_cloud_accounts").val();
	var search = $("#txtSearch").val();
    $.ajax({
        type: "POST",
        async: true,
        url: "ecoMethods/wmGetEcosystemsTable",
        data: '{"sSearch":"' + search + '", "sAccountID":"' + account_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "text",
        success: function (response) {
            $("#ecosystems").html(response);
            //gotta restripe the table
            initJtable(true, true);

		    //what happens when you click a row?
		    $(".selectable").click(function () {
		        showPleaseWait();
		        location.href = '/ecosystemEdit?ecosystem_id=' + $(this).parent().attr("ecosystem_id");
		    });

        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

function FillEcotemplatesDropdown() {
	var provider = $("#ddlProvider").val();

    $.ajax({
        type: "POST",
        async: false,
        url: "ecoMethods/wmGetEcotemplatesJSON",
        data: '{}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (templates) {
            // all we want here is to loop the clouds
            $("#ddlEcotemplates").empty();
            $.each(templates, function(index, template){
            	$("#ddlEcotemplates").append("<option value=\"" + template.ecotemplate_id + "\">" + template.ecotemplate_name + "</option>");
			});
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}
function CloudAccountWasChanged() {
    GetItems();
}

function ShowItemAdd() {
    $("#hidMode").val("add");

    // clear all of the previous values
    clearEditDialog();

    $("#edit_dialog").dialog("open");
    $("#txtTaskName").focus();
}

function DeleteItems() {
	proceed = false;
    var ArrayString = $("#hidSelectedArray").val();
    $.each(ArrayString.split(","), function(index, value) { 
		status = $("tr[ecosystem_id='" + value + "'] .stormstatus").text();
		if (status != "") {
			warnmsg = "One or more of the selected Ecosystems was created by Storm.\n\nManually deleting the Ecosystem will *not* deallocate any resources, and will leave no 'one-click' way to do so.\n\nAre you sure?";
		} 
	});
	
	if (warnmsg != "")
		proceed = confirm(warnmsg);

	if (proceed == true) {
	    $.ajax({
	        type: "POST",
	        url: "ecoMethods/wmDeleteEcosystems",
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
	} else {
		// if we clear them the user won't know which ones might have warned
		//ClearSelectedRows();
		$("#delete_dialog").dialog("close");
	}
}



function Save() {
    var bSave = true;
    var strValidationError = '';

    //some client side validation before we attempt to save
    if ($("#ddlEcotemplates")[0].length == 0) {
        bSave = false;
        strValidationError += 'Ecosystems must belong to an Ecosystem Template.  Create an Ecosystem Template first.';
    };

    if ($("#new_ecosystem_name").val() == "") {
        bSave = false;
        strValidationError += 'Name is required.';
    };

    if ($("#header_cloud_accounts")[0].length == 0) {
        bSave = false;
        strValidationError += 'Ecosystems require a Cloud Account.  Create a Cloud Account first.';
    };

    if (bSave != true) {
        showAlert(strValidationError);
        return false;
    }

	var account_id = $("#header_cloud_accounts").val();
	var name = packJSON($("#new_ecosystem_name").val());
	var desc = packJSON($("#new_ecosystem_desc").val());
	var etid = $("#ddlEcotemplates").val();

	$.ajax({
        async: false,
        type: "POST",
        url: "ecoMethods/wmCreateEcosystem",
        data: '{"sName":"' + name + '","sDescription":"' + desc + '","sEcotemplateID":"' + etid + '", "sAccountID":"' + account_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
        	if (response.error) {
        		showAlert(response.error);
        	} else if (response.info) {
        		showInfo(response.info);
        	} else if (response.id) {
                location.href = "ecosystemEdit?ecosystem_id=" + response.id;
            } else {
                showAlert(response);
                hidePleaseWait();
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}
