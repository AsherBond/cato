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

	//dialogs

	$("#edit_dialog").dialog({
		autoOpen : false,
		modal : true,
		height : 500,
		width : 600,
		bgiframe : true,
		buttons : {
			"Save" : function() {
				SaveItem(1);
			},
			Cancel : function() {
				$("#edit_dialog").dialog("close");
			}
		}
	});

	//the Provider ddl changes a few labels based on it's value
	$("#ddlProvider").change(function() {
		setLabels();
		GetProviderClouds();
		ClearTestResult();
	});

	$("#ddlDefaultCloud").change(function() {
		ClearTestResult();
	});

	$("#jumpto_cloud_btn").button({
		icons : {
			primary : "ui-icon-pencil"
		},
		text : false
	});
	$("#jumpto_cloud_btn").click(function() {
		var cld_id = $("#ddlDefaultCloud").val();
		var prv = $("#ddlProvider option:selected").text();

		//if (prv !== "Amazon AWS") {
		var saved = SaveItem(0);
		if (saved) {
			if (cld_id) {
				location.href = "/cloudEdit?cloud_id=" + cld_id;
			} else {
				location.href = "/cloudEdit";
			}
		}
		//}
	});
	$("#add_cloud_btn").button({
		icons : {
			primary : "ui-icon-plus"
		},
		text : false
	});
	$("#add_cloud_btn").click(function() {
		var prv = $("#ddlProvider option:selected").text();
		//if (prv !== "Amazon AWS") {
		var saved = SaveItem(0);
		if (saved) {
			location.href = "/cloudEdit?add=true&provider=" + prv;
		}
		//}
	});

	//the test connection buttton
	$("#test_connection_btn").button({
		icons : {
			primary : "ui-icon-signal-diag"
		},
		text : false
	});
	$("#test_connection_btn").click(function() {
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
	if (add === "true") {
		var prv = getQuerystringVariable("provider");
		ShowItemAdd();
		if (prv) {
			$("#ddlProvider").val(prv);
			$("#ddlProvider").change();
		}
	}

	GetItems();
	ManagePageLoad();
});

function GetProvidersList() {
	var response = ajaxPost("cloudMethods/wmGetProvidersList", {
		"sUserDefinedOnly" : "False"
	}, "html");
	if (response) {
		$("#ddlProvider").html(response);
		ClearTestResult();
	}
}

function GetProviderClouds() {
	// when ADDING, we need to get the clouds for this provider
	var provider = ajaxPost("cloudMethods/wmGetProvider", {
		sProvider : $("#ddlProvider").val()
	});
	if (provider) {
		ClearTestResult();
		// all we want here is to loop the clouds
		$("#ddlDefaultCloud").empty();
		$.each(provider.Clouds, function(id, cloud) {
			$("#ddlDefaultCloud").append("<option value=\"" + id + "\">" + cloud.Name + "</option>");
		});

		//we can't allow testing the connection if there are no clouds
		if ($("#ddlDefaultCloud option").length === 0)
			$("#test_connection_btn").hide();
		else
			$("#test_connection_btn").show();
	}
}

function TestConnection() {
	SaveItem(0);

	var account_id = $("#hidCurrentEditID").val();
	var cloud_id = $("#ddlDefaultCloud").val();

	if (cloud_id.length === 36 && account_id.length === 36) {
		ClearTestResult();
		$("#conn_test_result").text("Testing...");

		var response = ajaxPost("cloudMethods/wmTestCloudConnection", {
			sAccountID : account_id,
			sCloudID : cloud_id
		});
		if (response) {
			try {
				if (response !== null) {
					if (response.result === "success") {
						$("#conn_test_result").css("color", "green");
						$("#conn_test_result").text("Connection Successful.");
					}
					if (response.result === "fail") {
						$("#conn_test_result").css("color", "red");
						$("#conn_test_result").text("Connection Failed.");
						$("#conn_test_error").text(unpackJSON(response.error));
					}
				}
			} catch(err) {
				alert(err);
				ClearTestResult();
			}
		}
	} else {
		ClearTestResult();
		$("#conn_test_result").css("color", "red");
		$("#conn_test_result").text("Unable to test.  Please try again.");
	}
}

function GetItems(page) {
	if (!page)
		page = "1";
	var response = ajaxPost("cloudMethods/wmGetCloudAccountsTable", {
		sSearch : $("#txtSearch").val(),
		sPage : page
	});
	if (response) {
		pager = unpackJSON(response.pager);
		html = unpackJSON(response.rows);

		$("#pager").html(pager);
		$("#pager .pager_button").click(function() {
			GetItems($(this).text());
		});

		$("#accounts").html(html);

		//gotta restripe the table
		initJtable(true, true);

		$(".account_help_btn").tipTip({
			defaultPosition : "right",
			keepAlive : false,
			activation : "hover",
			maxWidth : "400px",
			fadeIn : 100
		});

		$("#accounts .selectable").click(function() {
			LoadEditDialog($(this).parent().attr("account_id"));
		});

	}
}

function setLabels() {
	if ($("#ddlProvider").val() === "Amazon AWS" || $("#ddlProvider").val() === "Eucalyptus") {
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

	var account = ajaxPostAsync("cloudMethods/wmGetCloudAccount", {
		sID : sEditID
	}, function(account) {
		$("#txtAccountName").val(account.Name);
		$("#txtAccountNumber").val(account.AccountNumber);
		$("#ddlProvider").val(account.Provider);
		$("#txtLoginID").val(account.LoginID);
		$("#txtLoginPassword").val(account.LoginPassword);
		$("#txtLoginPasswordConfirm").val(account.LoginPassword);

		if (account.IsDefault)
			$("#chkDefault").prop("checked", true);
		//if (account.AutoManage === "1") $("#chkAutoManageSecurity").prop("checked", true);

		//the account result will have a list of all the clouds on this account.
		$("#ddlDefaultCloud").empty();
		$.each(account.ProviderClouds, function(index, cloud) {
			// the 'default' one is selected here
			if (cloud.ID === account.DefaultCloud.ID)
				$("#ddlDefaultCloud").append("<option value=\"" + cloud.ID + "\" selected=\"selected\">" + cloud.Name + "</option>");
			else
				$("#ddlDefaultCloud").append("<option value=\"" + cloud.ID + "\">" + cloud.Name + "</option>");
		});

		//we can't allow testing the connection if there are no clouds
		if ($("#ddlDefaultCloud option").length === 0)
			$("#test_connection_btn").hide();
		else
			$("#test_connection_btn").show();

		setLabels();

		//clear out any test results
		ClearTestResult();

		$("#edit_dialog_tabs").tabs("option", "active", 0);
		$("#edit_dialog_tabs").tabs("option", "disabled", []);
		$("#edit_dialog").dialog("option", "title", "Modify Account");
		$("#edit_dialog").dialog("open");
	});
}

function ClearTestResult() {
	$("#conn_test_result").css("color", "green");
	$("#conn_test_result").empty();
	$("#conn_test_error").empty();
}

function SaveItem(close_after_save) {
	//used for changing the global dropdown if needed
	var old_label = $("#header_cloud_accounts option:selected").text();

	var bSaved = false;
	var bSave = true;
	var strValidationError = "";

	//some client side validation before we attempt to save
	var sAccountID = $("#hidCurrentEditID").val();

	var sAccountName = $("#txtAccountName").val();
	if (!sAccountName) {
		bSave = false;
		strValidationError += "Account Name required.<br />";
	}

	var sDefaultCloudID = $("#ddlDefaultCloud").val();
	if (!sDefaultCloudID) {
		bSave = false;
		strValidationError += "Default Cloud required.<br />";
	}

	if ($("#txtLoginPassword").val() !== $("#txtLoginPasswordConfirm").val()) {
		bSave = false;
		strValidationError += "Passwords do not match.";
	}

	if (bSave !== true) {
		var prv = $("#ddlProvider option:selected").text();
		url = "/cloudEdit?add=true&provider=" + prv;

		showInfo(strValidationError, '<a href="' + url + '">Click here</a> to create a new Cloud.', true);
		return false;
	}

	var args = {};
	args.sMode = $("#hidMode").val();
	args.sAccountID = sAccountID;
	args.sAccountName = sAccountName;
	args.sAccountNumber = $("#txtAccountNumber").val();
	args.sProvider = $("#ddlProvider").val();
	args.sDefaultCloudID = sDefaultCloudID;
	args.sLoginID = $("#txtLoginID").val();
	args.sLoginPassword = $("#txtLoginPassword").val();
	args.sLoginPasswordConfirm = $("#txtLoginPasswordConfirm").val();
	args.sIsDefault = ($("#chkDefault").prop("checked") ? "1" : "0");
	args.sAutoManageSecurity = ($("#chkAutoManageSecurity").prop("checked") ? "1" : "0");

	var account = ajaxPost("cloudMethods/wmSaveAccount", args);
	if (account) {
		// clear the search field and fire a search click, should reload the grid
		$("#txtSearch").val("");
		GetItems();

		var dropdown_label = account.Name + " (" + account.Provider + ")";
		//if we are adding a new one, add it to the dropdown too
		if ($("#hidMode").val() === "add") {
			$("#header_cloud_accounts").append($("<option>", {
				value : account.ID
			}).text(dropdown_label));
			//if this was the first one, get it in the session by nudging the change event.
			if ($("#header_cloud_accounts option").length === 1)
				$("#header_cloud_accounts").change();
		} else {
			//we've only changed it.  update the name in the drop down if it changed.
			if (old_label !== dropdown_label)
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
	} else {
		$("#edit_dialog").dialog("close");
	}

	return bSaved;
}

function ShowItemAdd() {
	clearEditDialog();
	$("#hidMode").val("add");

	setLabels();
	GetProviderClouds();

	//clear out any test results
	ClearTestResult();

	$("#edit_dialog_tabs").tabs("option", "active", 0);
	$("#edit_dialog_tabs").tabs("option", "disabled", [1]);
	$("#edit_dialog").dialog("option", "title", "Create a New Account");
	$("#edit_dialog").dialog("open");
	$("#txtAccountName").focus();
}

function DeleteItems() {
	var args = {};
	args.sDeleteArray = $("#hidSelectedArray").val();
	var response = ajaxPost("cloudMethods/wmDeleteAccounts", args);
	if (response) {
		var do_refresh = false;

		//first, which one is selected?
		var current = $("#header_cloud_accounts option:selected").val();

		//remove the deleted ones from the cloud account dropdown
		myArray = $("#hidSelectedArray").val().split(",");
		$.each(myArray, function(name, value) {
			//whack it
			$('#header_cloud_accounts option[value="' + value + '"]').remove();
			//if we whacked what was selected, flag for change push
			if (value === current)
				do_refresh = true;
		});

		if (do_refresh)
			$("#header_cloud_accounts").change();

		//update the list in the dialog
		$("#hidSelectedArray").val("");
		$("#delete_dialog").dialog("close");

		// clear the search field and fire a search click, should reload the grid
		$("#txtSearch").val("");
		GetItems();

		$("#update_success_msg").text("Delete Successful").show().fadeOut(2000);
	}
}
