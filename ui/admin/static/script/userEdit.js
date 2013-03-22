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

	$("#edit_dialog").hide();
	$("#delete_dialog").hide();

	//specific field validation and masking
	$("#txtUserLoginID").keypress(function(e) {
		return restrictEntryToUsername(e, this);
	});
	$("#txtUserFullName").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	$("#txtUserEmail").keypress(function(e) {
		return restrictEntryToEmail(e, this);
	});

	// change action for dropdown list, saves a callback
	$("#ddlUserAuthType").live("change", function() {
		SetPasswordControls();
	});

	$("#edit_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 600,
		bgiframe : true,
		buttons : {
			"Save" : function() {
				SaveUser();
			},
			Cancel : function() {
				CloseDialog();
			}
		}

	});

	//the hook for the 'show log' link
	$("#show_log_link").button({
		icons : {
			primary : "ui-icon-document"
		}
	});
	$("#show_log_link").click(function() {
		var sID = $("#hidCurrentEditID").val();
		ShowLogViewDialog(1, sID, true);
	});

	//buttons
	$("#clear_failed_btn").button({
		icons : {
			primary : "ui-icon-refresh"
		},
		text : false
	});
	$("#clear_failed_btn").live("click", function() {
		ClearFailedLoginAttempts();
	});

	$("#pw_reset_btn").button({
		icons : {
			primary : "ui-icon-mail-closed"
		}
	});
	$("#pw_reset_btn").live("click", function() {
		if (confirm("Are you sure?")) {
			ResetPassword();
		}
	});

	$("#chkGeneratePW").click(function() {
		//in 'add' mode the controls may be hidden based on the checkbox
		if (this.checked) {
			$(".password_entry").hide();
		} else {
			$(".password_entry").show();
		}
	});

	GetItems();
	ManagePageLoad();

	// set a handler for cleanup
	// when the user selects the x close instead of the button
	$('#edit_dialog').bind('dialogclose', function(event) {
		InitializeUserAdd();
	});

	// setup the userAddTabs
	$("#AddUserTabs").tabs();

});

function GetItems(page) {
	if (!page)
		page = "1"
	var response = ajaxPost("uiMethods/wmGetUsersTable", {
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

		$("#users").html(html);
		//gotta restripe the table
		initJtable(true, true);
		$("#users .selectable").click(function() {
			LoadEditDialog(0, $(this).parent().attr("user_id"));
		});
	}
}

function SetPasswordControls() {
	if ($("#ddlUserAuthType").val() == "local") {
		if ($("#hidMode").val() == 'add') {
			$(".password_checkbox").show();
			$(".password_edit").hide();
		} else {
			$(".password_checkbox").hide();
			$(".password_entry").show();
			$(".password_edit").show();
		}
	} else {//ldap mode you can never edit it
		$(".password_entry ").hide();
		$(".password_checkbox").hide();
		$(".password_edit").hide();
	}
}

function ShowItemAdd() {
	$("#hidMode").val("add");

	// clear all of the previous values
	clearEditDialog();

	$('#edit_dialog').dialog('option', 'title', 'Create a New User');

	SetPasswordControls();

	$("#edit_dialog").dialog("open");

	$("#txtUserLoginID").focus();
	$("#ddlUserStatus").val("1");
	$("#ddlUserAuthType").val("local");
	$("#ddlUserRole").val("User");
}

function CloseDialog() {
	// this is called by the button click
	$("#edit_dialog").dialog("close");
	InitializeUserAdd();
}

function InitializeUserAdd() {
	// called from button click, or the small x in the dialog
	$('#AddUserTabs').tabs('select', 0);
	$("[id*='lblNewUserMessage']").html('');
	$("#hidCurrentEditID").val("");
	$("#objects_tags").empty();

	ClearSelectedRows();
	clearEditDialog();
}

function DeleteItems() {
	var args = {};
	args.sDeleteArray = $("#hidSelectedArray").val();
	var response = ajaxPost("uiMethods/wmDeleteUsers", args);
	if (response) {
		$("#hidSelectedArray").val("");
		$("#delete_dialog").dialog("close");

		GetItems();
	}
}

function SaveUser() {
	// save or create a new user
	if ($("#hidMode").val() == 'edit') {
		//alert('save edit');
		SaveUserEdits();
	} else {
		SaveNewUser();
	}
}

function SaveUserEdits() {
	//alert('saveUserEdits');
	// using ajax post send the
	// loginID                  -   txtUserLoginID
	// full name                -   txtUserFullName
	// Authentication Type      -   ddlUserAuthType
	// Email                    -   txtUserEmail
	// Password                 -   txtUserPassword
	// Force Password Change    -   cbNewUserForcePasswordChange
	// user role                -   ddlUserRole
	// asset assignments        -   tbd?
	var bSave = true;
	var strValidationError = '';
	//some client side validation before we attempt to save the user
	var sLoginID = $("#txtUserLoginID").val();
	if (sLoginID == '') {
		bSave = false;
		strValidationError += 'Login ID required.<br />';
	};
	var sFullName = $("#txtUserFullName").val();
	if (sFullName == '') {
		bSave = false;
		strValidationError += 'Full Name required.<br />';
	};
	if (!$("#ddlUserAuthType").val()) {
		bSave = false;
		strValidationError += 'Authentication Type required.<br />';
	} else {
		var sAuthType = $("#ddlUserAuthType").val();
	}
	var sUserPassword = $("#txtUserPassword").val();
	if (sAuthType == 'local') {
		if ($("#txtUserPassword").val() != $("#txtUserPasswordConfirm").val()) {
			bSave = false;
			strValidationError += 'Passwords do not match!<br />';
		};
	}

	var sForcePasswordChange = '0';
	if ($("#cbNewUserForcePasswordChange").is(':checked')) {
		sForcePasswordChange = '1';
	}
	if (!$("#ddlUserRole").val()) {
		bSave = false;
		strValidationError += 'Role required.<br />';
	} else {
		var sUserRole = $("#ddlUserRole").val();
	}
	var sEmail = $('#txtUserEmail').val();
	if (sEmail == '') {
		bSave = false;
		strValidationError += 'Email Address required.<br />';
	};

	if (!$("#ddlUserStatus").val()) {
		bSave = false;
		strValidationError += 'Status required.<br />';
	} else {
		var sStatus = $("#ddlUserStatus").val();
	}

	if (bSave != true) {
		showAlert(strValidationError);
		return false;
	}

	//put the users groups in a string for submission
	var sGroups = new Array();
	$("#objects_tags .tag").each(function(idx) {
		sGroups[idx] = $(this).attr("val");
	});

	var user = {};
	user.ID = $("#hidCurrentEditID").val();
	user.LoginID = sLoginID;
	user.FullName = sFullName;
	user.AuthenticationType = sAuthType;
	user.Password = packJSON(sUserPassword);
	user.ForceChange = sForcePasswordChange;
	user.Role = sUserRole;
	user.Email = sEmail;
	user.Status = sStatus;
	user.Groups = sGroups;

	var response = ajaxPost("uiMethods/wmUpdateUser", user);
	if (response) {
		if ($("#hidMode").val() == 'edit') {
			// remove this item from the array
			var sEditID = $("#hidCurrentEditID").val();
			var myArray = new Array();
			var sArrHolder = $("#hidSelectedArray").val();
			myArray = sArrHolder.split(',');

			//how many in the array before you clicked Save?
			var wereInArray = myArray.length;

			if (jQuery.inArray(sEditID, myArray) > -1) {
				$("#chk_" + sEditID).attr("checked", false);
				myArray.remove(sEditID);
			}

			$("#lblItemsSelected").html(myArray.length);
			$("#hidSelectedArray").val(myArray.toString());

			if (wereInArray == 1) {
				// this was the last or only user edited so close
				$("#hidCurrentEditID").val("");
				$("#hidEditCount").val("");

				CloseDialog();
				//leave any search string the user had entered, so just click the search button
				GetItems();
			} else {
				// load the next item to edit
				$("#hidCurrentEditID").val(myArray[0]);
				LoadEditDialog(myArray.length, myArray[0]);
			}
		} else {
			CloseDialog();
			//leave any search string the user had entered, so just click the search button
			GetItems();
		}
	}
}

//sLoginID sFullName sAuthType sUserPassword sForcePasswordChange sUserRole sEmail As String
function SaveNewUser() {
	//alert('save new user');
	var bSave = true;
	var strValidationError = '';

	//some fields are fixed on a new user
	var sForcePasswordChange = '1';

	//some client side validation before we attempt to save the user
	var sLoginID = $("#txtUserLoginID").val();
	if (sLoginID == '') {
		bSave = false;
		strValidationError += 'Login ID required.<br />';
	};
	var sFullName = $("#txtUserFullName").val();
	if (sFullName == '') {
		bSave = false;
		strValidationError += 'Full Name required.<br />';
	};
	if (!$("#ddlUserAuthType").val()) {
		bSave = false;
		strValidationError += 'Authentication Type required.<br />';
	} else {
		var sAuthType = $("#ddlUserAuthType").val();
	}

	if (!$("#ddlUserRole").val()) {
		bSave = false;
		strValidationError += 'Role required.<br />';
	} else {
		var sUserRole = $("#ddlUserRole").val();
	}
	var sEmail = $("#txtUserEmail").val();
	if (sEmail == '') {
		bSave = false;
		strValidationError += 'Email Address required.<br />';
	};

	if (!$("#ddlUserStatus").val()) {
		bSave = false;
		strValidationError += 'Status required.<br />';
	} else {
		var sStatus = $("#ddlUserStatus").val();
	}

	//passwords must match, unless the check box is checked
	var sUserPassword = $("#txtUserPassword").val();
	var sGeneratePW = ($("#chkGeneratePW").attr("checked") == "checked" ? 1 : 0);
	if (sGeneratePW == 0) {
		if ($("#txtUserPassword").val() == '') {
			bSave = false;
			strValidationError += 'Password required.<br />';
		};
		if ($("#txtUserPassword").val() != $("#txtUserPasswordConfirm").val()) {
			bSave = false;
			strValidationError += 'Passwords do not match!<br />';
		};
	}

	if (bSave != true) {
		showAlert(strValidationError);
		return false;
	}

	//put the users groups in a string for submission
	var sGroups = "";
	$("#objects_tags .tag").each(function(intIndex) {
		if (sGroups == "")
			sGroups += $(this).attr("id").replace(/ot_/, "");
		else
			sGroups += "," + $(this).attr("id").replace(/ot_/, "");
	});

	var user = {};
	user.LoginID = sLoginID;
	user.FullName = sFullName;
	user.AuthenticationType = sAuthType;
	user.Password = packJSON(sUserPassword);
	user.GeneratePW = sGeneratePW;
	user.ForceChange = sForcePasswordChange;
	user.Role = sUserRole;
	user.Email = sEmail;
	user.Status = sStatus;
	user.Groups = sGroups;

	var response = ajaxPost("uiMethods/wmCreateUser", user);
	if (response) {
		CloseDialog();
		GetItems();
	}
}

function LoadEditDialog(editCount, editUserID) {

	$("#hidMode").val("edit");

	if (editCount > 1)
		$('#edit_dialog').dialog('option', 'title', 'Modify Multiple Users');
	else
		$("#edit_dialog").dialog("option", "title", "Modify User");

	$("#trFailedLoginAttempts").show();

	$("#hidEditCount").val(editCount);
	$("#hidCurrentEditID").val(editUserID);

	var user = ajaxPost("uiMethods/wmGetUser", {
		sUserID : editUserID
	});
	if (user) {
		$("#txtUserLoginID").val(user.LoginID);
		$("#txtUserFullName").val(user.FullName)
		$("#txtUserEmail").val(user.Email);
		//$("#txtUserPassword").val(user.sPasswordMasked);
		//$("#txtUserPasswordConfirm").val(user.sPasswordMasked)
		$("#ddlUserAuthType").val(user.AuthenticationType);
		$("#ddlUserStatus").val(user.Status);
		$("#ddlUserRole").val(user.Role);
		$("#lblFailedLoginAttempts").html(user.FailedLoginAttempts);

		SetPasswordControls();
		if ( typeof (GetObjectsTags) != 'undefined') {
			GetObjectsTags(user.ID);
		}

		$("#edit_dialog").dialog("open");
	}
}

function ShowItemModify() {

	var myArray = new Array();
	var curArray = $("#hidSelectedArray").val();
	myArray = curArray.split(',');
	var userCount = myArray.length;
	if (userCount == 0) {
		showAlert("Select a user, or multiple users to modify.");
		return false;
	}

	SetPasswordControls();

	//load up the first or only user to modify
	var sFirstUserID = myArray[0].toString()

	// load the user for editing
	LoadEditDialog(userCount, sFirstUserID);

}

function ClearFailedLoginAttempts() {
	//reset the counter and change the text
	var user = {};
	user.ID = $("#hidCurrentEditID").val();
	user.FailedLoginAttempts = 0;
	var response = ajaxPost("uiMethods/wmUpdateUser", user);
	if (response) {
		$("#lblFailedLoginAttempts").html("0");
	}
}

function ShowItemCopy() {
	//copy is pretty simple.
	//we show the "Edit" dialog for the selected user, but clear a couple of the fields and
	//set the "mode" to "edit"

	// clear all of the previous values
	var ArrayString = $("#hidSelectedArray").val();
	if (ArrayString.length == 0) {
		showInfo('Select a User to Copy.');
		return false;
	}

	// multiple select is allowed, but we only copy the first one
	var myArray = ArrayString.split(',');
	var user_copy_id = myArray[0];

	//get the data for the selected user
	LoadEditDialog(1, user_copy_id);

	$("#hidMode").val("add");
	$('#edit_dialog').dialog("option", "title", 'Create New User like ' + $("#txtUserFullName").val());

	// clear some values...
	$("#txtUserLoginID").val("");
	$("#txtUserFullName").val("");
	$("#txtUserEmail").val("");

	SetPasswordControls();

	$("#edit_dialog").dialog("open");
	$("#txtUserLoginID").focus();
	$("#ddlUserStatus").val("1");
	$("#ddlUserAuthType").val("local");
	$("#ddlUserRole").val("User");
}

function ResetPassword() {
	var user = {};
	user.ID = $("#hidCurrentEditID").val();
	user.NewRandomPassword = true;
	var response = ajaxPost("uiMethods/wmUpdateUser", user);
	if (response) {
		showInfo('Password successfully reset.');
	}
}
