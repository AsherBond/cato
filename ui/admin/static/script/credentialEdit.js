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

	//specific field validation and masking
	$("#txtCredUsername").keypress(function(e) {
		return restrictEntryToUsername(e, this);
	});
	$("#txtCredDomain").keypress(function(e) {
		return restrictEntryToUsername(e, this);
	});

	// clear the edit array
	$("#hidSelectedArray").val("");

	// burn through the grid and disable any checkboxes that have assets associated
	$("[tag='chk']").each(function(intIndex) {
		if ($(this).attr("assets") !== "0") {
			this.disabled = true;
		}
	});

	$("#edit_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 800,
		bgiframe : true,
		buttons : {
			"Save" : function() {
				SaveCredential();
			},
			Cancel : function() {
				$("#edit_dialog").dialog("close");
			}
		}
	});

	$("#edit_dialog_tabs").tabs();

	var tip = "For uncommon cases where a system requires multiple authentication prompts, for example certain brands of TCP/IP switches.";
	$("#priv_mode_info").attr("title", tip);
	$("#priv_mode_info").click(function() {
		showInfo(tip, "", true);
	});
	$("#priv_mode_info").tipTip();

	ManagePageLoad();
	GetItems();
});

function GetItems(page) {
	if (!page)
		page = "1";
	var response = ajaxPost("uiMethods/wmGetCredentialsTable", {
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

		$("#credentials").html(html);
		//gotta restripe the table
		initJtable(true, true);
		$("#credentials .selectable").click(function() {
			LoadEditDialog($(this).parent().attr("credential_id"));
		});
	}
}

function LoadEditDialog(editID) {
	clearEditDialog();
	$("#hidCurrentEditID").val(editID);

	var cred = ajaxPost("uiMethods/wmGetCredential", {
		sCredentialID : editID
	});
	if (cred) {
		$("#txtCredName").val(cred.Name);
		$("#txtCredUsername").val(cred.Username);
		$("#txtCredDomain").val(cred.Domain);
		$("#txtCredDescription").val(cred.Description);

		if (cred.Type === "Private Key") {
			$("#txtPrivateKey").val("********");
			$("#edit_dialog_tabs").tabs("option", "active", 1);
		} else {
			$("#txtPrivateKey").val("");
			$("#edit_dialog_tabs").tabs("option", "active", 0);
		}

		$("#hidMode").val("edit");
		$("#edit_dialog").dialog("option", "title", "Modify Credential");
		$("#edit_dialog").dialog("open");
	}
}

function SaveCredential() {
	var bSave = true;
	var strValidationError = "";

	//some client side validation before we attempt to save
	var sCredentialID = $("#hidCurrentEditID").val();
	var sCredentialName = $("#txtCredName").val();
	var sCredUsername = $("#txtCredUsername").val();
	var sPrivateKey = $("#txtPrivateKey").val();
	if (sCredentialName === "") {
		bSave = false;
		strValidationError += "Credential Name required.<br />";
	}
	if (sCredUsername === "" && sPrivateKey === "") {
		bSave = false;
		strValidationError += "User Name or Private Key required.<br />";
	}

	if ($("#txtCredPassword").val() !== $("#txtCredPasswordConfirm").val()) {
		bSave = false;
		strValidationError += "Passwords do not match.<br />";
	}
	if ($("#txtPrivilegedPassword").val() !== $("#txtPrivilegedConfirm").val()) {
		bSave = false;
		strValidationError += "Priviledged passwords do not match.<br />";
	}

	if (bSave !== true) {
		showInfo(strValidationError);
		return false;
	}

	var cred = {};
	cred.ID = sCredentialID;
	cred.Name = sCredentialName;
	cred.Description = $("#txtCredDescription").val();
	cred.Username = sCredUsername;
	cred.Password = $("#txtCredPassword").val();
	cred.SharedOrLocal = "0";
	cred.Domain = $("#txtCredDomain").val();
	cred.PrivilegedPassword = $("#txtPrivilegedPassword").val();
	cred.PrivateKey = sPrivateKey;

	if ($("#hidMode").val() === "edit") {
		var response = ajaxPost("uiMethods/wmUpdateCredential", cred);
		if (response) {
			GetItems();
			$("#edit_dialog").dialog("close");
		}
	} else {
		var success = ajaxPost("uiMethods/wmCreateCredential", cred);
		if (success) {
			GetItems();
			$("#edit_dialog").dialog("close");
		}
	}
}

function ShowItemAdd() {
	$("#hidMode").val("add");

	clearEditDialog();
	$("#edit_dialog").dialog("option", "title", "Create a New Credential");

	$("#edit_dialog").dialog("open");
	$("#txtCredName").focus();
}

function DeleteItems() {
	var args = {};
	args.sDeleteArray = $("#hidSelectedArray").val();
	var response = ajaxPost("uiMethods/wmDeleteCredentials", args);
	if (response) {
		$("#hidSelectedArray").val("");
		$("#delete_dialog").dialog("close");

		// clear the search field and fire a search click, should reload the grid
		$("#txtSearch").val("");
		GetItems();

		$("#update_success_msg").text("Delete Successful").show().fadeOut(2000);
	}
}
