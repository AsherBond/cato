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

    //dialogs

    $("#edit_dialog").dialog({
        autoOpen: false,
        modal: true,
        height: 500,
        width: 500,
        bgiframe: true,
        buttons: {
            "Save": function () {
                SaveItem(1);
            },
            Cancel: function () {
                $("#edit_dialog").dialog("close");
            }
        }
    });

    $("#edit_dialog_tabs").tabs();

    //the test connection buttton
    $("#test_connection_btn").button({ icons: { primary: "ui-icon-link"} });
	$("#test_connection_btn").live("click", function () {
        TestConnection();
    });

    $("#jumpto_account_btn").button({ icons: { primary: "ui-icon-pencil"}, text: false });
	$("#jumpto_account_btn").click(function () {
        var acct_id = $("#ddlTestAccount").val();
    	var saved = SaveItem(0);
    	if (saved) {
		    if (acct_id) {
				location.href="/cloudAccountEdit?account_id=" + acct_id;
			} else {
				location.href="/cloudAccountEdit";
			}
		}
    });
    $("#add_account_btn").button({ icons: { primary: "ui-icon-plus"}, text: false });
	$("#add_account_btn").click(function () {
        var prv = $("#ddlProvider option:selected").text();
    	var saved = SaveItem(0);
    	if (saved) {
			location.href="/cloudAccountEdit?add=true&provider=" + prv;
		}
    });

	//the Provider ddl changes a few things
	$('#ddlProvider').change(function () {
		GetProviderAccounts();
	});

    GetProvidersList();

	//if there was an cloud_id querystring, we'll pop the edit dialog.
	var cld_id = getQuerystringVariable("cloud_id");
    if (cld_id) {
        LoadEditDialog(cld_id);
    }
	//if there was an add querystring, we'll pop the add dialog.
	var add = getQuerystringVariable("add");
    if (add == "true") {
		var prv = getQuerystringVariable("provider");
        ShowItemAdd();
	    if (prv) { $("#ddlProvider").val(prv); $("#ddlProvider").change(); }
    }

    GetItems();
    ManagePageLoad();

});

function GetProvidersList() {
    $.ajax({
        type: "POST",
        async: false,
        url: "cloudMethods/wmGetProvidersList",
        data: '{"sUserDefinedOnly":"True"}',
        contentType: "application/json; charset=utf-8",
        dataType: "html",
        success: function (response) {
			$("#ddlProvider").html(response);
       },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

function GetProviderAccounts() {
	var provider = $("#ddlProvider").val();

    $.ajax({
        type: "POST",
        async: false,
        url: "cloudMethods/wmGetCloudAccountsJSON",
        data: '{"sProvider":"' + provider + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (accounts) {
            // all we want here is to loop the clouds
            $("#ddlTestAccount").empty();
            if (accounts) {
	            $.each(accounts, function(index, account){
	            	$("#ddlTestAccount").append("<option value=\"" + account.account_id + "\">" + account.account_name + "</option>");
				});
			}
			//we can't allow testing the connection if there are no clouds
			if ($("#ddlTestAccount option").length == 0)
				$("#test_connection_btn").hide();
            else
				$("#test_connection_btn").show();
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

function TestConnection() {
	SaveItem(0);

    var cloud_id = $("#hidCurrentEditID").val();
    var account_id = $("#ddlTestAccount").val();

    if (cloud_id.length == 36 && account_id.length == 36)
    {    
		ClearTestResult();
		$("#conn_test_result").text("Testing...");
	    
	    $.ajax({
	        type: "POST",
	        async: false,
	        url: "cloudMethods/wmTestCloudConnection",
	        data: '{"sAccountID":"' + account_id + '","sCloudID":"' + cloud_id + '"}',
	        contentType: "application/json; charset=utf-8",
	        dataType: "json",
	        success: function (response) {
				try
				{
					if (response != null)
					{
						if (response.result == "success") {
							$("#conn_test_result").css("color","green");
							$("#conn_test_result").text("Connection Successful.");
						}
						if (response.result == "fail") {
							$("#conn_test_result").css("color","red");
							$("#conn_test_result").text("Connection Failed.");
							$("#conn_test_error").text(unpackJSON(response.error));
						}
					}
				}
				catch(err)
				{
					alert(err);
					ClearTestResult();
				}
	        },
	        error: function (response) {
	            showAlert(response.responseText);
	        }
	    });
	} else {
		ClearTestResult();
		$("#conn_test_result").css("color","red");
		$("#conn_test_result").text("Unable to test.  Please try again.");
	}
}

function GetItems() {
    $.ajax({
        type: "POST",
        async: false,
        url: "cloudMethods/wmGetCloudsTable",
        data: '{"sSearch":"' + $("#txtSearch").val() + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "html",
        success: function (response) {
            $("#clouds").html(response);
            //gotta restripe the table
            initJtable(true, true);
		    $("#clouds .selectable").click(function () {
		        LoadEditDialog($(this).parent().attr("cloud_id"));
		    });
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

function LoadEditDialog(editID) {
    //specifically for the test connection feature
	$("#conn_test_result").empty();
	$("#conn_test_error").empty();
   
    clearEditDialog();
    $("#hidMode").val("edit");

    $("#hidCurrentEditID").val(editID);

    $.ajax({
        type: "POST",
        async: false,
        url: "cloudMethods/wmGetCloud",
        data: '{"sID":"' + editID + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (cloud) {
            //update the list in the dialog
            if (cloud.length == 0) {
                showAlert('error no response');
                // do we close the dialog, leave it open to allow adding more? what?
            } else {
                $("#txtCloudName").val(cloud.Name);
                $("#ddlProvider").val(cloud.Provider);
                $("#txtAPIUrl").val(cloud.APIUrl);
                $("#ddlAPIProtocol").val(cloud.APIProtocol);
    
			    GetProviderAccounts();
				ClearTestResult();
				
			    $("#edit_dialog").dialog("option", "title", "Modify Cloud");
			    $("#edit_dialog").dialog("open");
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

function ClearTestResult() {
	$("#conn_test_result").css("color","green");
	$("#conn_test_result").empty();
	$("#conn_test_error").empty();
}

function SaveItem(close_after_save) {
	var bSaved = false;
    var bSave = true;
    var strValidationError = '';

    //some client side validation before we attempt to save
    var sCloudID = $("#hidCurrentEditID").val();

    var sCloudName = $("#txtCloudName").val();
    if (sCloudName == '') {
        bSave = false;
        strValidationError += 'Cloud Name required.<br />';
    };

    var sAPIUrl = $("#txtAPIUrl").val();
    if (sAPIUrl == '') {
        bSave = false;
        strValidationError += 'API URL required.';
    };

    if (bSave != true) {
        showInfo(strValidationError);
        return false;
    }

    var args = '{"sMode":"' + $("#hidMode").val() + '", \
    	"sCloudID":"' + sCloudID + '", \
        "sCloudName":"' + sCloudName + '", \
        "sProvider":"' + $("#ddlProvider").val() + '", \
        "sAPIProtocol":"' + $("#ddlAPIProtocol").val() + '", \
        "sAPIUrl":"' + sAPIUrl + '" \
        }';


	$.ajax({
        type: "POST",
        async: false,
        url: "cloudMethods/wmSaveCloud",
        data: args,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
			try {
				cloud = response;
		        if (cloud) {
	                // clear the search field and fire a search click, should reload the grid
	                $("#txtSearch").val("");
					GetItems();
		            
		            if (close_after_save) {
		            	$("#edit_dialog").dialog("close");
	            	} else {
		            	//we aren't closing? fine, we're now in 'edit' mode.
		            	$("#hidMode").val("edit");
	            		$("#hidCurrentEditID").val(cloud.ID);
	            		$("#edit_dialog").dialog("option", "title", "Modify Cloud");	
	            	}
	            	bSaved = true;
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
    return bSaved;
}

function ShowItemAdd() {
    //specifically for the test connection feature
	$("#conn_test_result").empty();
	$("#conn_test_error").empty();
    $("#hidCurrentEditID").val("");
    
    clearEditDialog();
	GetProviderAccounts();
	//clear out any test results
	ClearTestResult();

    $("#hidMode").val("add");

    $('#edit_dialog_tabs').tabs('select', 0);
    $('#edit_dialog_tabs').tabs( "option", "disabled", [1] );
    $('#edit_dialog').dialog('option', 'title', 'Create a New Cloud');
    $("#edit_dialog").dialog("open");
    $("#txtCloudName").focus();
}

function DeleteItems() {
    $("#update_success_msg").text("Deleting...").show().fadeOut(2000);

    var ArrayString = $("#hidSelectedArray").val();
    $.ajax({
        type: "POST",
        url: "cloudMethods/wmDeleteClouds",
        data: '{"sDeleteArray":"' + ArrayString + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
	        if (response) {
                $("#hidSelectedArray").val("");
                $("#delete_dialog").dialog("close");

                // clear the search field and fire a search click, should reload the grid
                $("#txtSearch").val("");
				GetItems();

                $("#update_success_msg").text("Delete Successful").show().fadeOut(2000);
            } else {
                showAlert(response);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}
