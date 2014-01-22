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

//This is all the functions to support the deploymentEdit page.
var g_id;

$(document).ready(function() {
	//used a lot
	g_id = getQuerystringVariable("deployment_id");

	//fix certain ui elements to not have selectable text
	$("#toolbox .toolbox_tab").disableSelection();

	//specific field validation and masking
	$("#txtDeploymentName").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	$("#txtDescription").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	//enabling the 'change' event for the Details tab
	$("#div_details :input[te_group='detail_fields']").change(function() {
		doDetailFieldUpdate(this);
	});

	// TEMPORARILY INCLUDING these fields ... this should go away when these properties get a json editor
	$("#div_details_detail :input[te_group='detail_fields']").change(function() {
		doDetailFieldUpdate(this);
	});

	// add a new group button
	$("#new_group_btn").click(function() {
		var newgroup = $("#new_group_name").val();
		if (newgroup) {
			ajaxPostAsync("depMethods/wmAddDeploymentGroup", {
				"id" : g_id,
				"group_name" : newgroup
			}, function(response) {
				$("#update_success_msg").text("Update Successful").fadeOut(2000);
				addGroupToList(newgroup);
			});
		}
	});

	//the show log link
	$("#show_log_link").button({
		icons : {
			primary : "ui-icon-document"
		}
	});
	$("#show_log_link").click(function() {
		ShowLogViewDialog(70, g_id, true);
	});

	GetDetails();
});

function GetDetails() {
	args = {};
	args.id = g_id;

	var deployment = ajaxPost("depMethods/wmGetDeployment", args);
	if (deployment) {
		$("#txtDeploymentName").val(deployment.Name);
		$("#txtRunState").val(deployment.RunState);
		$("#lblDeploymentHeader").html(deployment.Name);
		$("#txtDescription").val(deployment.Description);
		$("#txtServiceCount").val(deployment.ServiceCount);
		$("#txtInstanceCount").val(deployment.InstanceCount);

		// TODO: these should be on a different tab, and validated as JSON
		$("#txtOptions").val(JSON.stringify(deployment.Options, null, 4));
		$("#txtPrompts").val(JSON.stringify(deployment.Prompts, null, 4));

		// groups
		$("#deployment_groups").empty();
		$.each(deployment.Groups, function(index, groupname) {
			addGroupToList(groupname);
		});
	}
}

function addGroupToList(groupname) {
	var $li = $('<li class="ui-widget-content ui-corner-all">').append($('<div class="floatleft">').append(groupname));
	var $trashcan = $('<span class="ui-icon ui-icon-trash pointer">').data("groupname", groupname);
	$trashcan.click(function() {
		deleteGroup($li, $(this).data("groupname"));
	});
	$li.append($('<div class="floatright">').append($trashcan));
	$li.append($('<div class="clearfloat">'));
	$("#deployment_groups").append($li);
}

function deleteGroup($li, groupname) {
	ajaxPostAsync("depMethods/wmDeleteDeploymentGroup", {
		"id" : g_id,
		"group_name" : groupname
	}, function(response) {
		$("#update_success_msg").text("Update Successful").fadeOut(2000);
		$li.remove();
	});
}

function tabWasClicked(tab) {
	//we'll be hiding and showing right side content when tabs are selected.
	//several tabs on the page use the same detail, so make it the default.
	var detail_div = "#div_status_detail";

	//the generic toolbox.js file handles the click event that will call this function if it exists
	//several tabs here all use the same detail panel
	if (tab === "datastore") {
		detail_div = "#div_datastore_detail";
	} else if (tab === "status") {
		detail_div = "#div_status_detail";
	} else if (tab === "sequences") {
		detail_div = "#div_sequences_detail";
	} else if (tab === "details") {
		detail_div = "#div_details_detail";
		GetDetails();
	} else if (tab === "tags") {
		if ( typeof (GetObjectsTags) !== 'undefined') {
			GetObjectsTags(g_id);
		}
	}

	//hide 'em all
	$("#content_te .detail_panel").addClass("hidden");
	//show the one you clicked
	$(detail_div).removeClass("hidden");
}

function doDetailFieldUpdate(ctl) {
	var column = $(ctl).attr("column");
	var value = $(ctl).val();

	//for checkboxes and radio buttons, we gotta do a little bit more, as the pure 'val()' isn't exactly right.
	//and textareas will not have a type property!
	if ($(ctl).attr("type")) {
		var typ = $(ctl).attr("type").toLowerCase();
		if (typ === "checkbox") {
			value = (ctl.checked === true ? 1 : 0);
		}
		if (typ === "radio") {
			value = (ctl.checked === true ? 1 : 0);
		}
	}

	//escape it
	value = packJSON(value);

	if (column.length > 0) {
		$("#update_success_msg").text("Updating...").show();

		args = {};
		args.id = g_id;
		args.column = column;
		args.value = value;

		var response = ajaxPost("depMethods/wmUpdateDeploymentDetail", args);
		if (response) {
			$("#update_success_msg").text("Update Successful").fadeOut(2000);

			// Change the name in the header
			if (column === "Name") {
				$("#lblDeploymentHeader").html(unpackJSON(value));
			};
		}
	}
}

