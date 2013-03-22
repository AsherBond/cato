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
		if ($(this).attr("assets") != "0") {
			this.disabled = true;
		}
	});

	$("#edit_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 500,
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
		page = "1"
	$.ajax({
		type : "POST",
		async : false,
		url : "uiMethods/wmGetCredentialsTable",
		data : '{"sSearch":"' + $("#txtSearch").val() + '", "sPage":"' + page + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(response) {
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
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function LoadEditDialog(editID) {
	clearEditDialog();
	$("#hidCurrentEditID").val(editID);

	$.ajax({
		type : "POST",
		url : "uiMethods/wmGetCredential",
		data : '{"sCredentialID":"' + editID + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(cred) {
			//update the list in the dialog
			if (cred.length == 0) {
				showAlert('error no response');
			} else {
				$("#txtCredName").val(cred.Name);
				$("#txtCredUsername").val(cred.Username);
				$("#txtCredDomain").val(cred.Domain)
				$("#txtCredDescription").val(cred.Description);

				$("#hidMode").val("edit");
				$("#edit_dialog").dialog("option", "title", "Modify Credential");
				$("#edit_dialog").dialog("open");
			}
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function SaveCredential() {
	var bSave = true;
	var strValidationError = '';

	//some client side validation before we attempt to save
	var sCredentialID = $("#hidCurrentEditID").val();
	var sCredentialName = $("#txtCredName").val();
	var sCredUsername = $("#txtCredUsername").val();
	if (sCredentialName == '') {
		bSave = false;
		strValidationError += 'Credential Name required.<br />';
	};
	if (sCredUsername == '') {
		bSave = false;
		strValidationError += 'User Name required.<br />';
	};

	if ($("#txtCredPassword").val() != $("#txtCredPasswordConfirm").val()) {
		bSave = false;
		strValidationError += 'Passwords do not match.<br />';
	};
	if ($("#txtPrivilegedPassword").val() != $("#txtPrivilegedConfirm").val()) {
		bSave = false;
		strValidationError += 'Priviledged passwords do not match.<br />';
	};

	if (bSave != true) {
		showInfo(strValidationError);
		return false;
	}

	var cred = {}
	cred.ID = sCredentialID;
	cred.Name = sCredentialName;
	cred.Description = $("#txtCredDescription").val()
	cred.Username = sCredUsername;
	cred.Password = $("#txtCredPassword").val()
	cred.SharedOrLocal = "0";
	cred.Domain = $("#txtCredDomain").val()
	cred.PrivilegedPassword = $("#txtPrivilegedPassword").val()

	if ($("#hidMode").val() == "edit") {
		$.ajax({
			async : false,
			type : "POST",
			url : "uiMethods/wmUpdateCredential",
			data : JSON.stringify(cred),
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				if (response.error) {
					showAlert(response.error);
				}
				if (response.info) {
					showInfo(response.info);
				}
				if (response.result == "success") {
					GetItems();
					$("#edit_dialog").dialog("close");
				} else {
					showInfo(response);
				}
			},
			error : function(response) {
				showAlert(response.responseText);
			}
		});
	} else {
		$.ajax({
			async : false,
			type : "POST",
			url : "uiMethods/wmCreateCredential",
			data : JSON.stringify(cred),
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				if (response.error) {
					showAlert(response.error);
				}
				if (response.info) {
					showInfo(response.info);
				}
				if (response.ID) {
					GetItems();
					$("#edit_dialog").dialog("close");
				} else {
					showInfo(response);
				}
			},
			error : function(response) {
				showAlert(response.responseText);
			}
		});
	}
}

function ShowItemAdd() {
	$("#hidMode").val("add");

	clearEditDialog();
	$('#edit_dialog').dialog("option", "title", 'Create a New Credential');

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
