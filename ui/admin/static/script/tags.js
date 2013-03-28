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

//Shared functionality for the "tag" picker dialog.

// NOTE: this content is NOT in a document.ready section, because it was loaded dynamically.
//dialog init
$(function() {"use strict";
	$("#tag_picker_dialog").dialog({
		modal : true,
		autoOpen : false,
		bgiframe : true,
		width : 300,
		height : 500,
		buttons : {
			Close : function() {
				$(this).dialog("close");
			}
		}
	});

	//what happens when you select a value in the tag picker?
	$("#tag_picker_dialog .tag_picker_tag").live("click", function() {
		//if the item already exists... we can't add it again.
		//but the user will never know, they'll just think they added it even though it was already there.
		var id = $(this).attr("id").replace(/tpt_/, "ot_");
		var tag_name = $(this).attr("id").replace(/tpt_/, "");

		if ($("#" + id).length == 0) {
			var ahtml = '<li id="' + id.replace(/ /g, "") + '" val="' + tag_name + '" class="tag ui-widget-content ui-corner-all">';
			ahtml += '<table class="object_tags_table"><tr>';
			ahtml += '<td style="vertical-align: middle;">' + tag_name + '</td>';
			ahtml += '<td width="1px"><span class="ui-icon ui-icon-close tag_remove_btn" remove_id="' + id + '"></span></td>';
			ahtml += '</tr></table>';
			ahtml += '</li>';

			$("#objects_tags").append(ahtml);

			//commit the tag add (ONLY IF ON A DYNAMIC PAGE!)...
			if ($("#hidPageSaveType").val() == "dynamic") {
				var oid = GetCurrentObjectID();
				var ot = GetCurrentObjectType();

				var response = catoAjax.tags.addObjectTag(oid, ot, tag_name);
				if (response.error) {
					showAlert(response.error);
				}
				if (response.result) {
					if (response.result === "success") {
						$("#update_success_msg").text("Update Successful").fadeOut(2000);
					}
				}
			}
		}
		//and whack it from this list so you can't add twice
		//and clear the description
		$(this).remove();
		$("#tag_picker_description").html("");
	});

	//hover shows the description for the tag
	$("#tag_picker_dialog .tag_picker_tag").live("mouseover", function() {
		$(this).addClass("tag_picker_tag_hover");
		$("#tag_picker_description").html($(this).attr("desc"));
	});
	$("#tag_picker_dialog .tag_picker_tag").live("mouseout", function() {
		$(this).removeClass("tag_picker_tag_hover");
	});

	//NOW! this stuff can hopefully stay here, as the mechanism for adding/removing tags from an object should be the same
	//styles might be different on the task/proc pages?
	//remove a tag
	$(".tag_remove_btn").live("click", function() {
		$("#" + $(this).attr("remove_id").replace(/ /g, "")).remove();

		//commit the tag removal
		if ($("#hidPageSaveType").val() == "dynamic") {
			$("#update_success_msg").text("Updating...").show();

			var oid = GetCurrentObjectID();
			var ot = GetCurrentObjectType();
			var tag_name = $(this).attr("remove_id").replace(/ot_/, "");

			var response = catoAjax.tags.removeObjectTag(oid, ot, tag_name);
			if (response.error) {
				showAlert(response.error);
			}
			if (response.result) {
				if (response.result === "success") {
					$("#update_success_msg").text("Update Successful").fadeOut(2000);
				}
			}
		}
	});

	//add a tag
	$("#tag_add_btn").button({
		icons : {
			primary : "ui-icon-plus"
		}
	});

	$("#tag_add_btn").click(function() {

		//hokey, but our "ids" are in different hidden fields on different pages!
		//that should be normalized eventually
		var oid = GetCurrentObjectID();
		GetTagList(oid);

		//hide the title bar on this page, it's a double stacked dialog
		$("#tag_picker_dialog").dialog().parents(".ui-dialog").find(".ui-dialog-titlebar").remove();
		$("#tag_picker_description").html("");
		$("#tag_picker_dialog").dialog("open");
	});
});

function GetCurrentObjectID() {
	var oid = "";

	// on modernized pages, it'll probably be g_id
	if (typeof g_id !== "undefined") {
		oid = g_id;
	}

	// if not, look in the html for the older hidden fields
	if (oid == "" || ( typeof oid == "undefined")) {
		oid = $("input[id$='hidObjectID']").val();
	}
	if (oid == "" || ( typeof oid == "undefined")) {
		oid = $("input[id$='hidCurrentEditID']").val();
	}
	if (oid == "" || ( typeof oid == "undefined")) {
		oid = $("input[id$='hidOriginalTaskID']").val();
	}

	if ( typeof oid == "undefined")
		oid = "";

	return oid;
}

function GetCurrentObjectType() {
	var ot = $("#hidObjectType").val();
	if ( typeof ot == "undefined")
		ot = -1;
	return ot;
}

function GetTagList(object_id) {
	if ( typeof object_id == "undefined")
		object_id = "";

	var response = catoAjax.tags.getTagList(object_id);
	$("#tag_picker_list").html(response);
}

function GetObjectsTags(object_id) {
	var response = catoAjax.tags.getObjectsTags(object_id);
	$("#objects_tags").html(response);
}