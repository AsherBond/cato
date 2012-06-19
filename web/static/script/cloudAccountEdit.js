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
        width: 600,
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

    $("#keypair_dialog").dialog({
        autoOpen: false,
        modal: true,
        height: 400,
        width: 400,
        bgiframe: true,
        buttons: {
            "Save": function () {
                SaveKeyPair();
            },
            Cancel: function () {
                $("#keypair_dialog").dialog("close");
            }
        }
    });


	//the Provider ddl changes a few labels based on it's value
	$('#ddlProvider').change(function () {
		setLabels();
		GetProviderClouds();
	});

    $("#jumpto_cloud_btn").button({ icons: { primary: "ui-icon-pencil"}, text: false });
	$("#jumpto_cloud_btn").click(function () {
        var cld_id = $("#ddlTestCloud").val();
        var prv = $("#ddlProvider option:selected").text();

	    if (prv != "Amazon AWS") {
	    	var saved = SaveItem(0);
	    	if (saved) {
			    if (cld_id) {
					location.href="/cloudEdit?cloud_id=" + cld_id;
				} else {
					location.href="/cloudEdit";
				}
			}
		}
    });
    $("#add_cloud_btn").button({ icons: { primary: "ui-icon-plus"}, text: false });
	$("#add_cloud_btn").click(function () {
        var prv = $("#ddlProvider option:selected").text();
	    if (prv != "Amazon AWS") {
	    	var saved = SaveItem(0);
	    	if (saved) {
				location.href="/cloudEdit?add=true&provider=" + prv;
			}
		}
    });

    //keypair add button
    $("#keypair_add_btn").button({ icons: { primary: "ui-icon-plus"} });
    $("#keypair_add_btn").click(function () {
        //wipe the fields
        $("#keypair_id").val("");
        $("#keypair_name").val("");
        $("#keypair_private_key").val("");
        $("#keypair_passphrase").val("");

        $("#keypair_dialog").dialog("open");
    });

    //keypair delete button
    $(".keypair_delete_btn").live("click", function () {
        if (confirm("Are you sure?")) {
            $("#update_success_msg").text("Deleting...").show().fadeOut(2000);

            var kpid = $(this).parents(".keypair").attr("id").replace(/kp_/, "");

            $.ajax({
                type: "POST",
                url: "cloudMethods/wmDeleteKeyPair",
                data: '{"sKeypairID":"' + kpid + '"}',
                contentType: "application/json; charset=utf-8",
                dataType: "text",
                success: function (response) {
                    $("#kp_" + kpid).remove();
                    $("#update_success_msg").text("Delete Successful").fadeOut(2000);
                },
                error: function (response) {
                    showAlert(response.responseText);
                }
            });
        }
    });

    //edit a keypair
    $(".keypair_label").live("click", function () {
        //clear the optional fields
        $("#keypair_private_key").val("");
        $("#keypair_passphrase").val("");

        //fill them
        $("#keypair_id").val($(this).parents(".keypair").attr("id"));
        $("#keypair_name").val($(this).html());

        //show stars for the private key and passphrase if they were populated
        //the server sent back a flag denoting that
        var pk = "";

        if ($(this).parents(".keypair").attr("has_pk") == "true")
            pk += "**********\n";

        $("#keypair_private_key").val(pk);


        if ($(this).parents(".keypair").attr("has_pp") == "true")
            $("#keypair_passphrase").val("!2E4S6789O");


        $("#keypair_dialog").dialog("open");
    });


    //the test connection buttton
    $("#test_connection_btn").button({ icons: { primary: "ui-icon-link"} });
	$("#test_connection_btn").live("click", function () {
        TestConnection();
    });

    GetProvidersList();

	//if there was an account_id querystring, we'll pop the edit dialog.
	var acct_id = getQuerystringVariable("account_id");
    if (acct_id) {
        LoadEditDialog(acct_id);
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
        data: '{"sUserDefinedOnly":"False"}',
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


function GetProviderClouds() {
	// when ADDING, we need to get the clouds for this provider
	var provider = $("#ddlProvider").val();

    $.ajax({
        type: "POST",
        async: false,
        url: "cloudMethods/wmGetProvider",
        data: '{"sProvider":"' + provider + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (provider) {
            // all we want here is to loop the clouds
            $("#ddlTestCloud").empty();
            $.each(provider.Clouds, function(id, cloud){
            	$("#ddlTestCloud").append("<option value=\"" + id + "\">" + cloud.Name + "</option>");
			});
			
			//we can't allow testing the connection if there are no clouds
			if ($("#ddlTestCloud option").length == 0)
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

    var account_id = $("#hidCurrentEditID").val();
    var cloud_id = $("#ddlTestCloud").val();

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
        url: "cloudMethods/wmGetCloudAccountsTable",
        data: '{"sSearch":"' + $("#txtSearch").val() + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "html",
        success: function (response) {
            $("#accounts").html(response);
            
            //gotta restripe the table
            initJtable(true, true);

            $(".account_help_btn").tipTip({
			    defaultPosition: "right",
			    keepAlive: false,
			    activation: "hover",
			    maxWidth: "400px",
			    fadeIn: 100
			});

		    $("#accounts .selectable").click(function () {
		        LoadEditDialog($(this).parent().attr("account_id"));
		    });

        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

function setLabels() {
	if ($("#ddlProvider").val() == "Amazon AWS" || $("#ddlProvider").val() == "Eucalyptus")
	{
		$("#login_label").text("Access Key");
		$(".password_label").text("Secret Key");
	} else {
		$("#login_label").text("Login ID");
		$(".password_label").text("Password");
	}
}

function LoadEditDialog(sEditID) {
    clearEditDialog();
    $("#hidMode").val("edit");

    $("#hidCurrentEditID").val(sEditID);

    $.ajax({
        type: "POST",
        async: false,
        url: "cloudMethods/wmGetCloudAccount",
        data: '{"sID":"' + sEditID + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (account) {
            //update the list in the dialog
        	if (account.info) {
    			showInfo(account.info);
        	} else if (account.error) {
        		showAlert(account.error);
            } else {
                $("#txtAccountName").val(account.Name);
                $("#txtAccountNumber").val(account.AccountNumber)
                $("#ddlProvider").val(account.Provider);
                $("#txtLoginID").val(account.LoginID);
                $("#txtLoginPassword").val(account.LoginPassword);
                $("#txtLoginPasswordConfirm").val(account.LoginPassword);

                if (account.IsDefault == "True") $("#chkDefault").attr('checked', true);
                //if (account.AutoManage == "1") $("#chkAutoManageSecurity").attr('checked', true);
                
                //the account result will have a list of all the clouds on this account.
                $("#ddlTestCloud").empty();
                $.each(account.Clouds, function(id, cloud){
                	$("#ddlTestCloud").append("<option value=\"" + id + "\">" + cloud.Name + "</option>");
   				});	
			
				//we can't allow testing the connection if there are no clouds
				if ($("#ddlTestCloud option").length == 0)
					$("#test_connection_btn").hide();
	            else
					$("#test_connection_btn").show();

				setLabels();	
				
				//clear out any test results
				ClearTestResult();
				
			    $('#edit_dialog_tabs').tabs('select', 0);
			    $('#edit_dialog_tabs').tabs( "option", "disabled", [] );
			    $("#edit_dialog").dialog("option", "title", "Modify Account");
			    $("#edit_dialog").dialog("open");
			}
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });

    //get the keypairs
    GetKeyPairs(sEditID);
}

function ClearTestResult() {
	$("#conn_test_result").css("color","green");
	$("#conn_test_result").empty();
	$("#conn_test_error").empty();
}

function GetKeyPairs(sEditID) {
    $.ajax({
        type: "POST",
        async: false,
        url: "cloudMethods/wmGetKeyPairs",
        data: '{"sID":"' + sEditID + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "html",
        success: function (response) {
            $('#keypairs').html(response);
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

function SaveItem(close_after_save) {
	//used for changing the global dropdown if needed
	var old_label = $('#header_cloud_accounts option:selected').text();
    
    var bSaved = false;
    var bSave = true;
    var strValidationError = '';

    //some client side validation before we attempt to save
    var sAccountID = $("#hidCurrentEditID").val();

    var sAccountName = $("#txtAccountName").val();
    if (sAccountName == '') {
        bSave = false;
        strValidationError += 'Account Name required.<br />';
    };

    if ($("#txtLoginPassword").val() != $("#txtLoginPasswordConfirm").val()) {
        bSave = false;
        strValidationError += 'Passwords do not match.';
    };

    if (bSave != true) {
        showInfo(strValidationError);
        return false;
    }

    var args = '{"sMode":"' + $("#hidMode").val() + '", \
    	"sAccountID":"' + sAccountID + '", \
        "sAccountName":"' + sAccountName + '", \
        "sAccountNumber":"' + $("#txtAccountNumber").val() + '", \
        "sProvider":"' + $("#ddlProvider").val() + '", \
        "sLoginID":"' + $("#txtLoginID").val() + '", \
        "sLoginPassword":"' + $("#txtLoginPassword").val() + '", \
        "sLoginPasswordConfirm":"' + $("#txtLoginPasswordConfirm").val() + '", \
        "sIsDefault":"' + ($("#chkDefault").attr("checked") ? "1" : "0") + '", \
        "sAutoManageSecurity":"' + ($("#chkAutoManageSecurity").attr("checked") ? "1" : "0") + '"}';


	$.ajax({
        type: "POST",
        async: false,
        url: "cloudMethods/wmSaveAccount",
        data: args,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (account) {
        	try {
		        if (account) {
					//if there are errors or info, we're closing the dialog.
					//just makes things cleaner regarding the "mode" (add or edit)
		        	if (account.info) {
		            	$("#edit_dialog").dialog("close");
	        			showInfo(account.info);
		        	} else if (account.error) {
		            	$("#edit_dialog").dialog("close");
		        		showAlert(account.error);
		        	} else {
						// clear the search field and fire a search click, should reload the grid
		                $("#txtSearch").val("");
						GetItems();
		
						var dropdown_label = account.Name + ' (' + account.Provider + ')';
						//if we are adding a new one, add it to the dropdown too
						if ($("#hidMode").val() == "add") {
				            $('#header_cloud_accounts').append($('<option>', { value : account.ID }).text(dropdown_label)); 
				          	//if this was the first one, get it in the session by nudging the change event.
				          	if ($("#header_cloud_accounts option").length == 1)
				          		$("#header_cloud_accounts").change();
		          		} else {
		          			//we've only changed it.  update the name in the drop down if it changed.
		          			if (old_label != dropdown_label)
		          				$('#header_cloud_accounts option[value="' + account.ID + '"]').text(dropdown_label);
		          		}
			            
			            if (close_after_save) {
			            	$("#edit_dialog").dialog("close");
		            	} else {
			            	//we aren't closing? fine, we're now in 'edit' mode.
			            	$("#hidMode").val("edit");
		            		$("#hidCurrentEditID").val(account.ID);
		            		$("#edit_dialog").dialog("option", "title", "Modify Account");	
		            	}
		            	bSaved = true;
	          		}
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
    clearEditDialog();
    $("#hidMode").val("add");

	setLabels();	
	GetProviderClouds();

	//clear out any test results
	ClearTestResult();

    $('#edit_dialog_tabs').tabs('select', 0);
    $('#edit_dialog_tabs').tabs( "option", "disabled", [1] );
    $('#edit_dialog').dialog('option', 'title', 'Create a New Account');
    $("#edit_dialog").dialog("open");
    $("#txtAccountName").focus();
}

function SaveKeyPair() {
    var kpid = $("#keypair_id").val().replace(/kp_/, "");
    var name = $("#keypair_name").val();
	//pack up the PK field, JSON doesn't like it
    var pk = packJSON($("#keypair_private_key").val());
    var pp = $("#keypair_passphrase").val();
    var account_id = $("#hidCurrentEditID").val();

    //some client side validation before we attempt to save
    if (name == '') {
        showInfo("KeyPair Name is required.");
        return false;
    };

    $("#update_success_msg").text("Saving...").show().fadeOut(2000);

    $.ajax({
        type: "POST",
        url: "cloudMethods/wmSaveKeyPair",
        data: '{"sKeypairID" : "' + kpid + '","sAccountID" : "' + account_id + '","sName" : "' + name + '","sPK" : "' + pk + '","sPP" : "' + pp + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "text",
        success: function (response) {
            if (response == "") {
                if (kpid) {
                    //find the label and update it
                    $("#kp_" + kpid + " .keypair_label").html(name);
                } else {
                    //re-get the list
                    GetKeyPairs(account_id);
                }
                $("#update_success_msg").text("Save Successful").show().fadeOut(2000);
                $("#keypair_dialog").dialog("close");
            }
            else {
                showAlert(response);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

function DeleteItems() {
    $("#update_success_msg").text("Deleting...").show().fadeOut(2000);

    var ArrayString = $("#hidSelectedArray").val();
    $.ajax({
        type: "POST",
        url: "cloudMethods/wmDeleteAccounts",
        data: '{"sDeleteArray":"' + ArrayString + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
        	var do_refresh = false;
        	
			//first, which one is selected?
			var current = $("#header_cloud_accounts option:selected").val();

        	//remove the deleted ones from the cloud account dropdown
			myArray = $("#hidSelectedArray").val().split(',');
			$.each(myArray, function(name, value) {
				//whack it
				$('#header_cloud_accounts option[value="' + value + '"]').remove();
				//if we whacked what was selected, flag for change push
				if (value == current)
					do_refresh = true;
			});
            
            if (do_refresh)
            	$('#header_cloud_accounts').change();
            
            //update the list in the dialog
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
