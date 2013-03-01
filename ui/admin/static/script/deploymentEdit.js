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

	GetDetails();
});

function GetDetails() {
	args = {}
	args.id = g_id;

	$.ajax({
		type : "POST",
		async : true,
		url : "depMethods/wmGetDeployment",
		data : JSON.stringify(args),
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(deployment) {
			try {
				$("#hidDeploymentID").val(deployment.ID);
				$("#txtDeploymentName").val(deployment.Name);
				$("#txtCurrentStatus").val(deployment.Status);
				$("#lblDeploymentHeader").html(deployment.Name);
				$("#txtDescription").val(deployment.Description);
			} catch (ex) {
				showAlert(ex.message);
			}
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function tabWasClicked(tab) {
	//we'll be hiding and showing right side content when tabs are selected.
	//several tabs on the page use the same detail, so make it the default.
	var detail_div = "#div_status_detail";

	//the generic toolbox.js file handles the click event that will call this function if it exists
	//several tabs here all use the same detail panel
	if (tab == "datastore") {
		detail_div = "#div_datastore_detail";
	} else if (tab == "status") {
		detail_div = "#div_status_detail";
	} else if (tab == "sequences") {
		detail_div = "#div_sequences_detail";
	} else if (tab == "details") {
		detail_div = "#div_details_detail";
		GetDetails();
	} else if (tab == "tags") {
		if ( typeof (GetObjectsTags) != 'undefined') {
			GetObjectsTags($("#hidDeploymentID").val());
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
		if (typ == "checkbox") {
			value = (ctl.checked == true ? 1 : 0);
		}
		if (typ == "radio") {
			value = (ctl.checked == true ? 1 : 0);
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

		$.ajax({
			async : false,
			type : "POST",
			url : "depMethods/wmUpdateDeploymentDetail",
			data : JSON.stringify(args),
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				if (response.error) {
					showAlert(response.error);
				} else if (response.info) {
					showInfo(response.info);
				} else if (response.result == "success") {
					$("#update_success_msg").text("Update Successful").fadeOut(2000);

					// Change the name in the header
					if (column == "Name") {
						$("#lblDeploymentHeader").html(unpackJSON(value));
					};
				} else {
					showInfo(response);
				}
			},
			error : function(response) {
				$("#update_success_msg").fadeOut(2000);
				showAlert(response.responseText);
			}
		});
	}
}

