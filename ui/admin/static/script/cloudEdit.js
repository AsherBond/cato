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
		width : 500,
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

	$("#edit_dialog_tabs").tabs();

	$("#keypair_dialog").dialog({
		autoOpen : false,
		modal : true,
		height : 400,
		width : 400,
		bgiframe : true,
		buttons : {
			"Save" : function() {
				SaveKeyPair();
			},
			Cancel : function() {
				$("#keypair_dialog").dialog("close");
			}
		}
	});

	//keypair add button
	$("#keypair_add_btn").button({
		icons : {
			primary : "ui-icon-plus"
		}
	});
	$("#keypair_add_btn").click(function() {
		//wipe the fields
		$("#keypair_id").val("");
		$("#keypair_name").val("");
		$("#keypair_private_key").val("");
		$("#keypair_passphrase").val("");

		$("#keypair_dialog").dialog("open");
	});

	//keypair delete button
	$(".keypair_delete_btn").live("click", function() {
		if (confirm("Are you sure?")) {
			$("#update_success_msg").text("Deleting...").show().fadeOut(2000);

			var kpid = $(this).parents(".keypair").attr("id").replace(/kp_/, "");

			var response = ajaxPost("cloudMethods/wmDeleteKeyPair", {
				sKeypairID : kpid
			}, "text");
			if (response) {
				$("#kp_" + kpid).remove();
				$("#update_success_msg").text("Delete Successful").fadeOut(2000);
			}
		}
	});

	//edit a keypair
	$(".keypair_label").live("click", function() {
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
	$(".test_connection_btn").button({
		icons : {
			primary : "ui-icon-signal-diag"
		},
		text : false
	});
	$(".test_connection_btn").live("click", function() {
		TestConnection();
	});

	$("#jumpto_account_btn").button({
		icons : {
			primary : "ui-icon-pencil"
		},
		text : false
	});
	$("#jumpto_account_btn").click(function() {
		var acct_id = $("#ddlDefaultAccount").val();
		var saved = SaveItem(0);
		if (saved) {
			if (acct_id) {
				location.href = "/cloudAccountEdit?account_id=" + acct_id;
			} else {
				location.href = "/cloudAccountEdit";
			}
		}
	});
	$("#add_account_btn").button({
		icons : {
			primary : "ui-icon-plus"
		},
		text : false
	});
	$("#add_account_btn").click(function() {
		var prv = $("#ddlProvider option:selected").text();
		var saved = SaveItem(0);
		if (saved) {
			location.href = "/cloudAccountEdit?add=true&provider=" + prv;
		}
	});

	//the Provider ddl changes a few things
	$('#ddlProvider').change(function() {
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

function GetProviderAccounts() {
	var provider = $("#ddlProvider").val();

	var accounts = ajaxPost("cloudMethods/wmGetCloudAccountsJSON", {
		sProvider : provider
	});
	if (accounts) {
		// all we want here is to loop the clouds
		$("#ddlDefaultAccount").empty();
		if (accounts) {
			$.each(accounts, function(index, account) {
				$("#ddlDefaultAccount").append("<option value=\"" + account.ID + "\">" + account.Name + "</option>");
			});
		}

		//we can't allow testing the connection if there are no clouds
		if ($("#ddlDefaultAccount option").length == 0)
			$("#test_connection_btn").hide();
		else
			$("#test_connection_btn").show();
	}
}

function TestConnection() {
	SaveItem(0);

	var cloud_id = $("#hidCurrentEditID").val();
	var account_id = $("#ddlDefaultAccount").val();

	if (cloud_id.length == 36 && account_id.length == 36) {
		ClearTestResult();
		$("#conn_test_result").text("Testing...");

		var response = ajaxPost("cloudMethods/wmTestCloudConnection", {
			sAccountID : account_id,
			sCloudID : cloud_id
		});
		if (response) {
			if (response.result == "success") {
				$("#conn_test_result").css("color", "green");
				$("#conn_test_result").text("Connection Successful.");
			}
			if (response.result == "fail") {
				$("#conn_test_result").css("color", "red");
				$("#conn_test_result").text("Connection Failed.");
				$("#conn_test_error").text(unpackJSON(response.error));
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
		page = "1"
	var response = ajaxPost("cloudMethods/wmGetCloudsTable", {
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

		$("#clouds").html(html);
		//gotta restripe the table
		initJtable(true, true);
		$("#clouds .selectable").click(function() {
			LoadEditDialog($(this).parent().attr("cloud_id"));
		});
	}

}

function LoadEditDialog(editID) {
	//specifically for the test connection feature
	$("#conn_test_result").empty();
	$("#conn_test_error").empty();

	clearEditDialog();
	$("#hidMode").val("edit");
	
	$('#edit_dialog_tabs').tabs("enable", 1);

	$("#hidCurrentEditID").val(editID);

	var cloud = ajaxPost("cloudMethods/wmGetCloud", {
		sID : editID
	});
	if (cloud) {
		$("#txtCloudName").val(cloud.Name);
		$("#ddlProvider").val(cloud.Provider.Name);
		$("#txtAPIUrl").val(cloud.APIUrl);
		$("#ddlAPIProtocol").val(cloud.APIProtocol);

		GetProviderAccounts();
		$("#ddlDefaultAccount").val(cloud.DefaultAccount.ID);

		ClearTestResult();

		$("#edit_dialog").dialog("option", "title", "Modify Cloud");
		$("#edit_dialog").dialog("open");
	}

	//get the keypairs
	GetKeyPairs(editID);
}

function ClearTestResult() {
	$("#conn_test_result").css("color", "green");
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

	var acct_id = ($("#ddlDefaultAccount").val() !== null) ? $("#ddlDefaultAccount").val() : '';

	var args = {
		sMode : $("#hidMode").val(),
		sCloudID : sCloudID,
		sCloudName : sCloudName,
		sProvider : $("#ddlProvider").val(),
		sDefaultAccountID : acct_id,
		sAPIProtocol : $("#ddlAPIProtocol").val(),
		sAPIUrl : sAPIUrl
	};

	var cloud = ajaxPost("cloudMethods/wmSaveCloud", args);
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
	}
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
	$('#edit_dialog_tabs').tabs("option", "disabled", [1]);
	$('#edit_dialog').dialog('option', 'title', 'Create a New Cloud');
	$("#edit_dialog").dialog("open");
	$("#txtCloudName").focus();
}

function DeleteItems() {
	var args = {};
	args.sDeleteArray = $("#hidSelectedArray").val();
	var response = ajaxPost("cloudMethods/wmDeleteClouds", args);
	if (response) {
		$("#hidSelectedArray").val("");
		$("#delete_dialog").dialog("close");

		// clear the search field and fire a search click, should reload the grid
		$("#txtSearch").val("");
		GetItems();

		$("#update_success_msg").text("Delete Successful").show().fadeOut(2000);
	}
}

function GetKeyPairs(sEditID) {
	var response = ajaxPost("cloudMethods/wmGetKeyPairs", {
		sID : sEditID
	}, "html");
	$('#keypairs').html(response);
}

function SaveKeyPair() {
	var kpid = $("#keypair_id").val().replace(/kp_/, "");
	var name = $("#keypair_name").val();
	//pack up the PK field, JSON doesn't like it
	var pk = packJSON($("#keypair_private_key").val());
	var pp = $("#keypair_passphrase").val();
	var cloud_id = $("#hidCurrentEditID").val();

	//some client side validation before we attempt to save
	if (name == '') {
		showInfo("KeyPair Name is required.");
		return false;
	};
	if ($("#keypair_private_key").val() == '') {
		showInfo("Private Key is required.");
		return false;
	};

	$("#update_success_msg").text("Saving...").show().fadeOut(2000);

	var response = ajaxPost("cloudMethods/wmSaveKeyPair", {
		sKeypairID : kpid,
		sCloudID : cloud_id,
		sName : name,
		sPK : pk,
		sPP : pp
	});
	if (response) {
		if (kpid) {
			//find the label and update it
			$("#kp_" + kpid + " .keypair_label").html(name);
		} else {
			//re-get the list
			GetKeyPairs(cloud_id);
		}
		$("#update_success_msg").text("Save Successful").show().fadeOut(2000);
		$("#keypair_dialog").dialog("close");
	}
}
