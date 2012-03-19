//Copyright 2011 Cloud Sidekick
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

    $("[tag='selectable']").live("click", function () {
        LoadEditDialog($(this).parent().attr("account_id"));
    });

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
                $("#edit_dialog").dialog('close');
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
				location.href="cloudAccountEdit.aspx?account_id=" + acct_id;
			} else {
				location.href="cloudAccountEdit.aspx";
			}
		}
    });
    $("#add_account_btn").button({ icons: { primary: "ui-icon-plus"}, text: false });
	$("#add_account_btn").click(function () {
        var prv = $("#ddlProvider option:selected").text();
    	var saved = SaveItem(0);
    	if (saved) {
			location.href="cloudAccountEdit.aspx?add=true&provider=" + prv;
		}
    });

	//override the search click button as defined on managepagecommon.js, because this page is now ajax!
	$("#item_search_btn").die();
	//and rebind it
	$("#item_search_btn").live("click", function () {
        GetClouds();
    });

	//the Provider ddl changes a few things
	$('#ddlProvider').change(function () {
		GetProviderAccounts();
	});

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
});

function pageLoad() {
    ManagePageLoad();
}

function GetProviderAccounts() {
	var provider = $("#ddlProvider").val();

    $.ajax({
        type: "POST",
        async: false,
        url: "uiMethods.asmx/wmGetCloudAccounts",
        data: '{"sProvider":"' + provider + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            var accounts = jQuery.parseJSON(response.d);

            // all we want here is to loop the clouds
            $("#ddlTestAccount").empty();
            $.each(accounts, function(index, account){
            	$("#ddlTestAccount").append("<option value=\"" + account.ID + "\">" + account.Name + "</option>");
			});
			
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
	        url: "awsMethods.asmx/wmTestCloudConnection",
	        data: '{"sAccountID":"' + account_id + '","sCloudID":"' + cloud_id + '"}',
	        contentType: "application/json; charset=utf-8",
	        dataType: "json",
	        success: function (response) {
				try
				{
		        	var oResultData = jQuery.parseJSON(response.d);
					if (oResultData != null)
					{
						if (oResultData.result == "success") {
							$("#conn_test_result").css("color","green");
							$("#conn_test_result").text("Connection Successful.");
						}
						if (oResultData.result == "fail") {
							$("#conn_test_result").css("color","red");
							$("#conn_test_result").text("Connection Failed.");
							$("#conn_test_error").text(unpackJSON(oResultData.error));
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

function GetClouds() {
    $.ajax({
        type: "POST",
        async: false,
        url: "cloudEdit.aspx/wmGetClouds",
        data: '{"sSearch":"' + $("#ctl00_phDetail_txtSearch").val() + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            $('#clouds').html(response.d);
            //gotta restripe the table
            initJtable(true, true);
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

    FillEditForm(editID);

	//clear out any test results
	ClearTestResult();
	
    $('#edit_dialog_tabs').tabs('select', 0);
    $('#edit_dialog_tabs').tabs( "option", "disabled", [] );
    $("#edit_dialog").dialog("option", "title", "Modify Cloud");
    $("#edit_dialog").dialog('open');

}

function ClearTestResult() {
	$("#conn_test_result").css("color","green");
	$("#conn_test_result").empty();
	$("#conn_test_error").empty();
}

function FillEditForm(sEditID) {
    $.ajax({
        type: "POST",
        async: false,
        url: "uiMethods.asmx/wmGetCloud",
        data: '{"sID":"' + sEditID + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            //update the list in the dialog
            if (response.d.length == 0) {
                showAlert('error no response');
                // do we close the dialog, leave it open to allow adding more? what?
            } else {
                var cloud = jQuery.parseJSON(response.d);

                // show the assets current values
                $("#txtCloudName").val(cloud.Name);
                $("#ddlProvider").val(cloud.Provider);
                $("#txtAPIUrl").val(cloud.APIUrl);
                $("#ddlAPIProtocol").val(cloud.APIProtocol);
    
			    GetProviderAccounts();
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
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
        url: "uiMethods.asmx/wmSaveCloud",
        data: args,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
	       try {
	            var cloud = jQuery.parseJSON(response.d);
		        if (cloud) {
		        	if (cloud.info) {
		        		showInfo(cloud.info);
		        	} else if (cloud.error) {
		        		showAlert(cloud.error);
		        	} else {
		                // clear the search field and fire a search click, should reload the grid
		                $("[id*='txtSearch']").val("");
						GetClouds();
			            
			            if (close_after_save) {
			            	$("#edit_dialog").dialog('close');
		            	} else {
			            	//we aren't closing? fine, we're now in 'edit' mode.
			            	$("#hidMode").val("edit");
		            		$("#hidCurrentEditID").val(cloud.ID);
		            		$("#edit_dialog").dialog("option", "title", "Modify Cloud");	
		            	}
		            	bSaved = true;
					}
		        } else {
		            showAlert(response.d);
		        }
			} catch (ex) {
				showAlert(response.d);
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
    $("#edit_dialog").dialog('open');
    $("#txtCloudName").focus();
}

function DeleteItems() {
    $("#update_success_msg").text("Deleting...").show().fadeOut(2000);

    var ArrayString = $("#hidSelectedArray").val();
    $.ajax({
        type: "POST",
        url: "uiMethods.asmx/wmDeleteClouds",
        data: '{"sDeleteArray":"' + ArrayString + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            //update the list in the dialog
            if (msg.d.length == 0) {
                $("#hidSelectedArray").val("");
                $("#delete_dialog").dialog('close');

                // clear the search field and fire a search click, should reload the grid
                $("[id*='txtSearch']").val("");
				GetClouds();

                $("#update_success_msg").text("Delete Successful").show().fadeOut(2000);
            } else {
                showAlert(msg.d);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}
