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

    $("#edit_dialog").hide();
    $("#delete_dialog").hide();

    //specific field validation and masking
    $("#txtUserLoginID").keypress(function (e) { return restrictEntryToUsername(e, this); });
    $("#txtUserFullName").keypress(function (e) { return restrictEntryToSafeHTML(e, this); });
    $("#txtUserEmail").keypress(function (e) { return restrictEntryToEmail(e, this); });

    //what happens when you click a user row
    $("[tag='selectable']").live("click", function () {
        LoadEditDialog(0, $(this).parent().attr("user_id"));
    });

    // change action for dropdown list, saves a callback
    $("#ddlUserAuthType").live("change", function () {
        SetPasswordControls();
    });

    $("#edit_dialog").dialog({
        autoOpen: false,
        modal: true,
        width: 600,
        bgiframe: true,
        buttons: {
            "Save": function () {
                showPleaseWait();
                SaveUser();
            },
            Cancel: function () {
                CloseDialog();
            }
        }

    });

    //the hook for the 'show log' link
    $("#show_log_link").click(function() {
        var sID = $("#hidCurrentEditID").val();
        var url = "securityLogView.aspx?type=1&id=" + sID;
        openWindow(url, "logView", "location=no,status=no,scrollbars=yes,resizable=yes,width=800,height=700");
    });

    //buttons
    $("#clear_failed_btn").button({ icons: { primary: "ui-icon-refresh" }, text: false });
    $("#clear_failed_btn").live("click", function () {
        ClearFailedLoginAttempts();
    });

    $("#pw_reset_btn").button({ icons: { primary: "ui-icon-mail-closed"} });
    $("#pw_reset_btn").live("click", function () {
        if (confirm("Are you sure?")) {
            ResetPassword();
        }
    });

    $("#chkGeneratePW").click(function () {
        //in 'add' mode the controls may be hidden based on the checkbox
        if (this.checked) {
			$(".password_entry").hide();
		} else {
			$(".password_entry").show();
		}
    });

});
function pageLoad() {
    ManagePageLoad();

    // set a handler for cleanup 
    // when the user selects the x close instead of the button
    $('#edit_dialog').bind('dialogclose', function (event) {
        InitializeUserAdd();
    });

    // setup the userAddTabs
    $("#AddUserTabs").tabs();

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
    } else { //ldap mode you can never edit it
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

    $("#edit_dialog").dialog('open');

    $("#txtUserLoginID").focus();
    $("#ddlUserStatus").val("1");
    $("#ddlUserAuthType").val("local");
    $("#ctl00_phDetail_ddlUserRole").val("User");
}

function CloseDialog() {
    // this is called by the button click
    $("#edit_dialog").dialog('close');
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
    var ArrayString = $("#hidSelectedArray").val();
    $.ajax({
        type: "POST",
        url: "userEdit.aspx/DeleteUsers",
        data: '{"sDeleteArray":"' + ArrayString + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            $("#hidSelectedArray").val("");
            $("#delete_dialog").dialog('close');

            $("#ctl00_phDetail_btnSearch").click();

            hidePleaseWait();
            showInfo(msg.d);
        },
        error: function (response) {
            hidePleaseWait();
            showAlert(response.responseText);
        }
    });
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
        if ($("#txtUserPassword").val() == '') {
            bSave = false;
            strValidationError += 'Password required.<br />';
        };
        if ($("#txtUserPassword").val() != $("#txtUserPasswordConfirm").val()) {
            bSave = false;
            strValidationError += 'Passwords do not match!<br />';
        };
    }

    var sForcePasswordChange = '0';
    if ($("#cbNewUserForcePasswordChange").is(':checked')) {
        sForcePasswordChange = '1';
    }
    if (!$("#ctl00_phDetail_ddlUserRole").val()) {
        bSave = false;
        strValidationError += 'Role required.<br />';
    } else {
        var sUserRole = $("#ctl00_phDetail_ddlUserRole").val();
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
    var sGroups = "";
    $("#objects_tags .tag").each(
        function (intIndex) {
            if (sGroups == "")
                sGroups += $(this).attr("val");
            else
                sGroups += "," + $(this).attr("val");
        });


    // ok we made it here, lets attempt to update the user
    var sEditUserID = $("#hidCurrentEditID").val();

    //alert('building stuff');
    var stuff = new Array();
    stuff[0] = sEditUserID;
    stuff[1] = sLoginID;
    stuff[2] = sFullName;
    stuff[3] = sAuthType;
    stuff[4] = sUserPassword;
    stuff[5] = sForcePasswordChange;
    stuff[6] = sUserRole;
    stuff[7] = sEmail;
    stuff[8] = sStatus;
    stuff[9] = sGroups;

    if (stuff.length > 0) {
        //alert('call pagemethod');
        //Doing the Microsoft ajax call because the jQuery one doesn't work.
        PageMethods.SaveUserEdits(stuff, OnUpdateSuccess, OnUpdateFailure);
    } else {
        showAlert('incorrect list of update attributes:' + stuff.length.toString());
    }
}

// Callback function invoked on successful completion of the MS AJAX page method.
function OnUpdateSuccess(result, userContext, methodName) {
    hidePleaseWait();
    //alert('success');
    if (methodName == "SaveUserEdits") {
        if (result.length == 0) {
            showInfo('User updated.');

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
                    $("#ctl00_phDetail_btnSearch").click();
                } else {
                    // load the next item to edit
                    $("#hidCurrentEditID").val(myArray[0]);
                    FillEditForm(myArray[0]);
                }
            } else {
                CloseDialog();

                //leave any search string the user had entered, so just click the search button
                $("#ctl00_phDetail_btnSearch").click();
            }

        } else {
            showInfo(result);
        }

    } else if (methodName == "SaveNewUser") {
        if (result.length == 0) {
            showInfo('User created.');
            CloseDialog();
            $("#ctl00_phDetail_btnSearch").click();
        } else {
            showInfo(result);
        }
    }
}

// Callback function invoked on failure of the MS AJAX page method.
function OnUpdateFailure(error, userContext, methodName) {
    hidePleaseWait();
    //alert('failure');
    if (error !== null) {
        showAlert(error.get_message());
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

    if (!$("#ctl00_phDetail_ddlUserRole").val()) {
        bSave = false;
        strValidationError += 'Role required.<br />';
    } else {
        var sUserRole = $("#ctl00_phDetail_ddlUserRole").val();
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
    $("#objects_tags .tag").each(
        function (intIndex) {
            if (sGroups == "")
                sGroups += $(this).attr("id").replace(/ot_/, "");
            else
                sGroups += "," + $(this).attr("id").replace(/ot_/, "");
        });

    // using ajax post send the
    var stuff = new Array();
    stuff[0] = sLoginID;
    stuff[1] = sFullName;
    stuff[2] = sAuthType;
    stuff[3] = sUserPassword;
    stuff[4] = sGeneratePW;
    stuff[5] = sForcePasswordChange;
    stuff[6] = sUserRole;
    stuff[7] = sEmail;
    stuff[8] = sStatus;
    stuff[9] = sGroups;

    if (stuff.length > 0) {
        PageMethods.SaveNewUser(stuff, OnUpdateSuccess, OnUpdateFailure);
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
    FillEditForm(editUserID);

    $("#edit_dialog").dialog('open');
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


function FillEditForm(sUserID) {

    // get all the data for the user and populate the fields
    // return from server example
    //    sUserFullName & "::" & sEmail & "::" & sEditUserID & "::" & sLoginID & "::" & sAuthenticationType & "::" & sStatus & "::" & sRole & "::" & sPasswordMasked
    $.ajax({
        type: "POST",
        async: false,
        url: "userEdit.aspx/LoadUserFormData",
        data: '{"sUserID":"' + sUserID + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            //update the list in the dialog
            if (response.d.length == 0) {
                showAlert('error no response');
                // do we close the dialog, leave it open to allow adding more? what?
            } else {

                var oResultData = jQuery.parseJSON(response.d);
                $("#txtUserLoginID").val(oResultData.sEditUserID);
                $("#txtUserFullName").val(oResultData.sUserFullName)
                $("#txtUserEmail").val(oResultData.sEmail);
                $("#txtUserPassword").val(oResultData.sPasswordMasked);
                $("#txtUserPasswordConfirm").val(oResultData.sPasswordMasked)
                $("#ddlUserAuthType").val(oResultData.sAuthenticationType);
                $("#ddlUserStatus").val(oResultData.sUserStatus);
                $("#ctl00_phDetail_ddlUserRole").val(oResultData.sRole);
                $("#lblFailedLoginAttempts").html(oResultData.sFailedLogins);

                SetPasswordControls();
                GetObjectsTags(sUserID);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}
function ClearFailedLoginAttempts() {
    //reset the counter and change the text
    $.ajax({
        type: "POST",
        url: "userEdit.aspx/ClearFailedAttempts",
        data: '{"sUserID":"' + $("#hidCurrentEditID").val() + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            //update the list in the dialog
            if (msg.d.length == 0) {

                $("#lblFailedLoginAttempts").html("0");

            } else {

                showAlert('error resetting failed attempts.');

            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
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
    FillEditForm(user_copy_id);

    $("#hidMode").val("add");
    $('#edit_dialog').dialog("option", "title", 'Create New User like ' + $("#txtUserFullName").val());

    // clear some values...
    $("#txtUserLoginID").val("");
    $("#txtUserFullName").val("");
    $("#txtUserEmail").val("");

    SetPasswordControls();

    $("#edit_dialog").dialog('open');
    $("#txtUserLoginID").focus();
    $("#ddlUserStatus").val("1");
    $("#ddlUserAuthType").val("local");
    $("#ctl00_phDetail_ddlUserRole").val("User");
}

function ResetPassword() {
    //reset the counter and change the text
    $.ajax({
        type: "POST",
        url: "userEdit.aspx/ResetPassword",
        data: '{"sUserID":"' + $("#hidCurrentEditID").val() + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            if (msg.d.length == 0) {
                showInfo('Password successfully reset.');
            } else {
                showAlert(msg.d);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}
