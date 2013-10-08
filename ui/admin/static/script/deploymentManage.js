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

	//define dialogs
	$("#edit_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 650,
		buttons : [{
			id : "edit_dialog_create_btn",
			text : "Create",
			click : function() {
				Save();
			}
		}, {
			text : "Cancel",
			click : function() {
				$("[id*='lblNewMessage']").html("");
				$("#hidCurrentEditID").val("");

				$("#hidSelectedArray").val("");
				$("#lblItemsSelected").html("0");

				// nice, clear all checkboxes selected in a single line!
				$(':input', (".jtable")).prop('checked', false);

				$(this).dialog("close");
			}
		}]
	});

	$("#copy_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 500,
		buttons : {
			"Copy" : function() {
				CopyDeployment();
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});

	ManagePageLoad();
	GetItems();
});

function GetItems(page) {
	if (!page)
		page = "1";
	var response = ajaxPost("depMethods/wmGetDeploymentsTable", {
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

		$("#deployments").html(html);
		//gotta restripe the table
		initJtable(true, true);

		//what happens when you click a row?
		$(".selectable").click(function() {
			showPleaseWait();
			location.href = '/deploymentEdit?deployment_id=' + $(this).parent().attr("deployment_id");
		});

	}
}

function ShowItemAdd() {
	$("#hidMode").val("add");

	// clear all of the previous values
	clearEditDialog();

	$("#edit_dialog").dialog("open");
	$("#txtDeploymentName").focus();
}

function DeleteItems() {
	var args = {};
	args.sDeleteArray = $("#hidSelectedArray").val();
	var response = ajaxPost("depMethods/wmDeleteDeployments", args);
	if (response) {

		$("#hidSelectedArray").val("");
		$("#delete_dialog").dialog("close");

		// clear the search field and fire a search click, should reload the grid
		$("#txtSearch").val("");
		GetItems();

		hidePleaseWait();
		showInfo('Delete Successful');
	}
}

function Save() {
	var bSave = true;
	var strValidationError = '';

	//some client side validation before we attempt to save the user
	if ($("#txtDeploymentName").val() == "") {
		bSave = false;
		strValidationError += 'Name is required.';
	};

	if (bSave != true) {
		showAlert(strValidationError);
		return false;
	}

	var args = {};
	args.name = packJSON($("#txtDeploymentName").val());
	args.desc = packJSON($("#txtDeploymentDesc").val());
	args.owner = "";

	var response = ajaxPost("depMethods/wmCreateDeployment", args);
	if (response) {
		showPleaseWait();

		location.href = "deploymentEdit?deployment_id=" + response.deployment_id;
	}
}

function ShowItemCopy() {
	// clear all of the previous values
	var ArrayString = $("#hidSelectedArray").val();
	if (ArrayString.length == 0) {
		showInfo('Select a Deployment to Copy.');
		return false;
	}
	if (ArrayString.indexOf(",") > -1) {
		//make a comment and clear the selection.
		showInfo('Only one Deployment can be copied at a time.');
		ClearSelectedRows();
		return false;
	}
	$("#txtCopyDeploymentName").val("");
	$("#copy_dialog").dialog("open");
}
