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

//copy from managePageCommon.js

//only fires on initial load of the page.
$(document).ready(function() {
	//check/uncheck all checkboxes
	$("#chkAll").live("click", function() {
		if (this.checked) {
			this.checked = true;
			$("[tag='chk']").prop("checked", true);
		} else {
			this.checked = false;
			$("[tag='chk']").prop("checked", false);
		}

		//now build out the array
		var lst = "";
		$("[tag='chk']").each(function(intIndex) {
			if (this.checked) {
				lst += $(this).attr("object_id") + ",";
			}
		});

		//chop off the last comma
		if (lst.length > 0)
			lst = lst.substring(0, lst.length - 1);

		$("#hidSelectedArray").val(lst);
		$("#lblItemsSelected").html($("[tag='chk']:checked").length);

	});

	//this spins thru the check boxes on the page and builds the array.
	//yes it rebuilds the list on every selection, but it's fast.
	$("[tag='chk']").live("click", function() {
		//first, deal with some 'check all' housekeeping
		//if I am being unchecked, uncheck the chkAll box too.
		//we do not have logic here to check the chkAll box if all items are checked.
		//that's not necessary right now.
		if (!this.checked) {
			$("#chkAll").prop("checked", false);
		}

		//now build out the array
		var lst = "";
		$("[tag='chk']").each(function(intIndex) {
			if (this.checked) {
				lst += $(this).attr("object_id") + ",";
			}
		});

		//chop off the last comma
		if (lst.length > 0)
			lst = lst.substring(0, lst.length - 1);

		$("#hidSelectedArray").val(lst);
		$("#lblItemsSelected").html($("[tag='chk']:checked").length);

	});

	$(".group_tab").live("click", function() {
		showPleaseWait("Querying the Cloud...");

		//style tabs
		$(".group_tab").removeClass("group_tab_selected");
		$(this).addClass("group_tab_selected");

		//get content here at some possible point in the future.
		$("#update_success_msg").text("Querying the Cloud...").show();

		var object_label = $(this).html();
		var object_type = $(this).attr("object_type");

		var account_id = $.cookie("selected_cloud_account");
		var cloud_id = $("#ddlClouds").val();

		//well, I have no idea why, but this ajax fires before the showPleaseWait can take effect.
		//delaying it is the only solution I've found... :-(
		setTimeout(function() {
			var response = ajaxPost("cloudMethods/wmGetCloudObjectList", {
				sAccountID : account_id,
				sCloudID : cloud_id,
				sObjectType : object_type
			}, "html");
			if (response) {
				$("#update_success_msg").fadeOut(2000);

				$("#results_label").html(object_label);
				$("#results_list").html(response);

				//set the cloud object type on a hidden field so we can use it later
				$("#hidCloudObjectType").val(object_type);

				initJtable(true, false);
				hidePleaseWait();
			}
		}, 250);
	});

	GetProvider();
});

function GetProvider() {
	// when ADDING, we need to get the clouds for this provider
	selected_provider = $.cookie("selected_cloud_provider");
	if (selected_provider) {
		var provider = ajaxPostAsync("cloudMethods/wmGetProvider", {
			sProvider : selected_provider
		}, function(provider) {
			if (provider.info) {
				showInfo(provider.info);
			} else {
				// loop the clouds
				$("#ddlClouds").empty();
				$.each(provider.Clouds, function(id, cloud) {
					$("#ddlClouds").append("<option value=\"" + id + "\">" + cloud.Name + "</option>");
				});

				$("#ddlClouds").change(function() {
					//changing the Cloud just clears the results and sets all tabs back to unselected.
					$(".group_tab").removeClass("group_tab_selected");
					$("#results_label").empty();
					$("#results_list").empty();
				});

				// draw the object type tabs
				$.each(provider.Products, function(name, prod) {
					$("#cloud_object_types").append("<li class=\"group_header\">" + prod.Label + "</li>");
					$.each(prod.CloudObjectTypes, function(id, cot) {
						$("#cloud_object_types").append("<li class=\"group_tab\" object_type=\"" + id + "\">" + cot.Label + "</li>");
					});
				});
			}
		});
	} else {
		showInfo("There are no Cloud Accounts defined.");

	}
}

function CloudAccountWasChanged() {
	location.reload();
}

