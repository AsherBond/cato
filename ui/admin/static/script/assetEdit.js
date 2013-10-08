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
	$("#txtAssetName").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	$("#txtAddress").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	$("#txtDbName").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	$("#txtCredUsername").keypress(function(e) {
		return restrictEntryToUsername(e, this);
	});
	$("#txtCredName").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	$("#txtCredDescription").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	$("#txtCredDomain").keypress(function(e) {
		return restrictEntryToHostname(e, this);
	});

	//dialogs
	$("#edit_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 700,
		bgiframe : true,
		buttons : {
			"Save" : function() {
				SaveAsset();
			},
			Cancel : function() {
				CloseDialog();
			}
		}
	});

	// remove the header and x, to prevent the user from clicking on them
	$("#edit_dialog").dialog().parents(".ui-dialog").find(".ui-dialog-titlebar").remove();

	//the hook for the 'show log' link
	$("#show_log_link").button({
		icons : {
			primary : "ui-icon-document"
		}
	});
	$("#show_log_link").click(function() {
		var sAssetID = $("#hidCurrentEditID").val();
		ShowLogViewDialog(2, sAssetID, true);
	});

	$("#rbShared").live("change", function() {
		$(".SharedCredFields").show();
	});
	$("#rbLocal").live("change", function() {
		$(".SharedCredFields").hide();
	});

	//what happens when you click a asset row
	$(".selectablecrd").live("click", function() {
		$("#hidCredentialID").val($(this).parent().attr("credential_id"));
		$('#tblCredentialSelector td').removeClass('row_over');
		//unselect them all
		$(this).parent().find('td').addClass("row_over");
		//select this one
	});

	// end live version
	//------------------------------------------------------------------

	// setup the AddTabs
	$("#AddAssetTabs").tabs();
	$("#CredentialSelectorTabs").hide();
	$("#CredentialsSubMenu").hide();
	$("#EditCredential").hide();

	$("#btnCredSelect").click(function() {
		$("input[name=rbShared]:checked").val("0")
		$("#hidCredentialType").val("selected");
		$('#hidCredentialID').val('');
		$('#CredentialSelectorTabs').show();
		$('#AddCredential').hide();
		$('#CredentialDetails').hide();
		$('#SharedLocalDiv').hide();
		$('#EditCredential').hide();
		LoadCredentialSelector();
		$('#btnCredAdd').show();
		return false;
	});

	$("#btnCredAdd").click(function() {
		$("input[name=rbShared]:checked").val("1")
		$("#hidCredentialType").val("new");
		$("#hidCredentialID").val("");
		$("#CredentialSelectorTabs").hide();
		$("#CredentialDetails").html("");
		$("#txtCredName").val("");
		$("#txtCredUsername").val("");
		$("#txtCredDomain").val("");
		$("#txtCredPassword").val("");
		$("#txtCredPasswordConfirm").val("");
		$("#EditCredential").show();
		$("#SharedLocalDiv").show();
		$("#txtCredUsername").focus();
		return false;
	});

	GetItems();
	ManagePageLoad();
});

function GetItems(page) {
	if (!page)
		page = "1"
	var response = ajaxPost("uiMethods/wmGetAssetsTable", {
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

		$("#assets").html(html);
		//gotta restripe the table
		initJtable(true, true);
		$("#assets .selectable").click(function() {
			LoadEditDialog(0, $(this).parent().attr("asset_id"));
		});
	}
}

function ShowItemAdd() {
	$("#hidMode").val("add");
	// clear all of the previous values
	$(':input', ("#tblEdit")).each(function() {
		var type = this.type;
		var tag = this.tagName.toLowerCase();
		// normalize case
		if (type == 'text' || type == 'password' || tag == 'textarea')
			this.value = "";
		else if (type == 'checkbox' || type == 'radio')
			this.checked = false;
		else if (tag == 'select')
			this.selectedIndex = -1;
	});

	$('#edit_dialog').data('title.dialog', 'Add New Asset');

	// hide the log link on a new asset creation
	$('#show_log_link').hide();

	// bugzilla 1243 make Active the default on add
	$("#ddlAssetStatus").val("Active");

	//bugzilla 1203 when ading a new asset set the credentials tab to add new credential by default.
	//if the user adds no information nothing will get saved but new local credential is default.
	$("#btnCredAdd").click();

	$('#CredentialDetails').html('');
	$("#edit_dialog").dialog("open");
	$("#txtAssetName").focus();

}

function CloseDialog() {
	$("#AddAssetTabs").tabs("option", "active", 0);

	CancelCredentialAdd();

	$("#edit_dialog").dialog("close");
	InitializeAdd();

	return false;
}

function InitializeAdd() {
	// called from button click, or the small x in the dialog
	$("#AddAssetTabs").tabs("option", "active", 0);
	$("#hidCurrentEditID").val("");

	$("#CredentialsSubMenu").hide();
	// and credential add
	$("#txtCredUsername").val("");
	$("#txtCredPassword").val("");
	$("#txtCredPasswordConfirm").val("");
	$("#txtCredName").val("");
	$("#txtCredDescription").val("");
	$("#txtCredDomain").val("");
	$("#txtPrivilegedPassword").val("");
	$("#txtPrivilegedConfirm").val("");
	$("#objects_tags").empty();

	ClearSelectedRows();

}

function DeleteItems() {
	var args = {};
	args.sDeleteArray = $("#hidSelectedArray").val();
	var response = ajaxPost("uiMethods/wmDeleteAssets", args);
	if (response) {
		$("#hidSelectedArray").val("");
		$("#delete_dialog").dialog("close");

		GetItems();
	}
}

function SaveAsset() {

	var bSave = true;
	var strValidationError = '';
	//some client side validation before we attempt to save
	var sAssetID = $("#hidCurrentEditID").val();
	var sAssetName = $("#txtAssetName").val();
	if (sAssetName == '') {
		bSave = false;
		strValidationError += 'Asset Name required.';
	};

	var ddlAssetStatus = "";
	if ($("#ddlAssetStatus").val() != null) {
		ddlAssetStatus = $("#ddlAssetStatus").val();
	}
	if (ddlAssetStatus == "") {
		bSave = false;
		strValidationError += 'Select a status for the Asset.';
	}

	var sDbName = $("#txtDbName").val();
	var sPort = $('#txtPort').val();

	// new credentials
	var sCredUsername = $("#txtCredUsername").val();
	var sCredPassword = $("#txtCredPassword").val();
	var sCredPasswordConfirm = $("#txtCredPasswordConfirm").val();
	var sPrivilegedPassword = $("#txtPrivilegedPassword").val();
	var sPrivilegedPasswordConfirm = $("#txtPrivilegedConfirm").val();
	var rbShared = $('input[name=rbShared]:checked').val();
	var sCredentialName = $("#txtCredName").val();
	var sCredentialDescr = $("#txtCredDescription").val();
	var sDomain = $("#txtCredDomain").val();
	var sCredentialType = $("#hidCredentialType").val()
	var sCredentialID = $("#hidCredentialID").val();

	if (sCredentialType == 'selected') {
		if (sCredentialID == '') {
			bSave = false;
			strValidationError += 'Select a credential, or create a new credential.';
		}
	} else {
		// if the type is new, and the user didnt add a username, just ignore it
		//if (sCredentialType == 'existing') {
		if (rbShared == '0') {
			// this is a shared credential, name and description are required
			if (sCredentialDescr == '' || sCredentialName == '') {
				bSave = false;
				strValidationError += 'Name and Description are required on Shared Credentials.<br />';
			}
		}
		if (sCredPassword != sCredPasswordConfirm) {
			bSave = false;
			strValidationError += 'Credential Passwords do not match.<br />';
		}
		// check the privileged password if one is filled in they should match
		if (sPrivilegedPassword != sPrivilegedPasswordConfirm) {
			bSave = false;
			strValidationError += 'Credential Passwords do not match.<br />';
		}
		//}

	}
	if (bSave != true) {
		showInfo(strValidationError);
		return false;
	}

	//put the tags in an array for submission
	var sTags = new Array();
	$("#objects_tags .tag").each(function(idx) {
		sTags[idx] = $(this).attr("val");
	});

	var cred = {}
	cred.ID = sCredentialID;
	cred.Name = sCredentialName;
	cred.Description = sCredentialDescr;
	cred.Username = sCredUsername;
	cred.Password = sCredPassword;
	cred.SharedOrLocal = rbShared;
	cred.Domain = sDomain;
	cred.PrivilegedPassword = sPrivilegedPassword;

	var asset = {};
	asset.ID = sAssetID;
	asset.Name = sAssetName;
	asset.DBName = $("#txtDbName").val();
	asset.Port = sPort;
	asset.Address = $("#txtAddress").val();
	asset.Status = ddlAssetStatus;
	asset.ConnString = $("#txtConnString").val();
	;
	asset.Tags = sTags;
	asset.CredentialMode = $("#hidCredentialType").val();
	asset.Credential = cred;

	if ($("#hidMode").val() == "edit") {
		var response = ajaxPost("uiMethods/wmUpdateAsset", asset);
		if (response) {
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
				GetItems();
			} else {
				CloseDialog();
				GetItems();
			}
		}
	} else {
		var response = ajaxPost("uiMethods/wmCreateAsset", asset);
		if (response) {
			CloseDialog();
			GetItems();
		}
	}
}

function ShowCredentialAdd() {
	$('#Credentials').hide();
	$('#btnCreateCredentials').hide();
	$('#btnCancelCredentials').show();
	$('#EditCredential').show();
}

function CancelCredentialAdd() {
	//alert('cancel credentials');
	$('#Credentials').show();
	$('#btnCreateCredentials').show();
	$('#btnCancelCredentials').hide();
	$('#EditCredential').hide();
}

function LoadEditDialog(editCount, editAssetID) {
	// show the log link on an existing asset
	$('#show_log_link').show();
	$('#show_tasks_link').show();

	// clear credentials
	$('#txtCredUsername').val();
	$('#txtCredDomain').val();
	$('#txtCredPassword').val();
	$('#txtCredPasswordConfirm').val();

	$("#hidMode").val("edit");
	$("#hidEditCount").val(editCount);
	$("#hidCurrentEditID").val(editAssetID);

	var asset = ajaxPost("uiMethods/wmGetAsset", {
		sAssetID : editAssetID
	});
	if (asset) {
		// show the assets current values
		$("#txtAssetName").val(asset.Name);
		$("#ddlAssetStatus").val(asset.Status);
		$("#txtPort").val(asset.Port)
		$("#txtDbName").val(asset.DBName);
		var sAddress = asset.Address.replace("||", "\\\\");
		sAddress = sAddress.replace(/\|/g, "\\");
		$("#txtAddress").val(sAddress);
		$("#txtConnString").val(asset.ConnString);

		$("#hidCredentialID").val(asset.CredentialID);
		var sCredentialID = asset.CredentialID;
		$("#hidCredentialID").val(sCredentialID);
		$('#CredentialSelectorTabs').hide();
		var CredentialUser = asset.UserName;

		$('#btnCredAdd').hide();

		if (sCredentialID == '') {
			// no existing credential, just show the add dialog
			$("#hidCredentialType").val("new");
			$("#CredentialDetails").html("");
			$('#SharedLocalDiv').show();
			$('#EditCredential').show();
			$('.SharedCredFields').hide();

		} else {
			// display the credentials if they exist, if not display only the add button
			if (asset.UserName != '') {
				var CredentialShared = asset.SharedOrLocal;
				if (CredentialShared == 'Local') {
					$("#CredentialDetails").html("");
					$("#hidCredentialType").val("existing");
					$("input[name=rbShared]:checked").val("1");
					$('#txtCredUsername').val(asset.UserName);
					$('#txtCredDomain').val(asset.Domain);
					//$('#txtCredPassword').val(asset.Password);
					//$('#txtCredPasswordConfirm').val(asset.Password);
					//$('#txtPrivilegedPassword').val(asset.PriviledgedPassword);
					//$('#txtPrivilegedConfirm').val(asset.PriviledgedPassword);
					$('.SharedCredFields').hide();
					$('#SharedLocalDiv').hide();
					$('#EditCredential').show();
				} else {
					// display the existing shared credential
					$("#CredentialDetails").html(CredentialShared + ' - ' + asset.UserName + '<br />Domain - ' + asset.Domain + '<br />Name - ' + asset.SharedCredName + '<br />Description - ' + asset.SharedCredDesc);
					$('#CredentialRemove').show();
					$('#CredentialDetails').show();
					$('#imgCredClear').show();
					$('#btnCredAdd').show();
				}
			} else {
				$('#imgCredClear').hide();
				$("#CredentialDetails").html("");
				$('#CredentialRemove').hide();
				$('#CredentialDetails').hide();
			}
		}

		$("#CredentialSelectorLocal").empty();

		// at load default to the first tab
		$("#AddAssetTabs").tabs("option", "active", 0);

		if ( typeof (GetObjectsTags) != 'undefined') {
			GetObjectsTags(asset.ID);
		}

		$("#edit_dialog").data("title.dialog", "Modify Asset");
		$("#edit_dialog").dialog("open");

	}
}

function ShowItemModify() {

	var ArrayString = $("#hidSelectedArray").val();
	if (ArrayString.length == 0) {
		showInfo('Select one or more Assets to modify.');
		return false;
	}
	var curArray = ArrayString.split(',');

	//load up the first or only asset to modify
	var sFirstID = curArray[0];

	// load the asset for editing
	LoadEditDialog(curArray.length, sFirstID);

}

function LoadCredentialSelector() {
	$("#CredentialSelectorShared").html("Loading...");
	// set the return t the default 'local' credentials
	var creds = ajaxPost("uiMethods/wmGetCredentialsJSON");
	if (creds) {
		$("#credentials").html("");
		$.each(creds, function(index, cred) {
			s = "<tr class=\"select_credential\" credential_id=\"" + cred.ID + "\">"
			s += "<td class=\"selectablecrd row\">" + cred.Name + "</td>"
			s += "<td class=\"selectablecrd row\">" + cred.Username + "</td>"
			s += "<td class=\"selectablecrd row\">" + cred.Domain + "</td>"
			s += "<td class=\"selectablecrd row\">" + cred.Description + "</td>"
			s += "</tr>"

			$("#credentials").append(s);
		});
	}
	$('#CredentialSelectorTabs').show();

}
