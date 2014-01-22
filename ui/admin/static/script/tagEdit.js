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
	$("#txtTag").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});

	$("#edit_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 500,
		bgiframe : true,
		title : 'Modify Tag',
		buttons : {
			"Save" : function() {
				SaveTag();
			},
			Cancel : function() {
				$("#edit_dialog").dialog("close");
			}
		}
	});

	ManagePageLoad();
	GetItems();
});

function GetItems(page) {
	if (!page)
		page = "1"

	var response = catoAjax.tags.getTagsTable($("#txtSearch").val(), page);
	if (response) {
		pager = response.pager;
		html = response.rows;

		$("#pager").html(pager);
		$("#pager .pager_button").click(function() {
			GetItems($(this).text());
		});

		$("#tags").html(html);
		//gotta restripe the table
		initJtable(true, true);

		$("#tags .selectable").click(function() {
			var tag = $(this).parent().attr("tag_name");

			// WE TOOK desc_id off the table, it was dumb.
			// just use jquery to find the description row, no id selector needed.
			var desc = $.trim($(this).parent().find(".desc").text());

			$("#hidMode").val("edit");
			$("#edit_dialog").dialog("open");

			$("#hidCurrentEditID").val(tag);

			//show what was clicked
			$("#txtTag").val(tag);
			$("#txtDescription").val(desc);
		});
	}
}

function SaveTag() {
	var bSave = true;
	var strValidationError = '';

	//some client side validation before we attempt to save
	var old_tag = $("#hidCurrentEditID").val();

	var new_tag = $("#txtTag").val();
	if (new_tag === '') {
		bSave = false;
		strValidationError += 'Tag required.<br />';
	};

	if (bSave !== true) {
		showInfo(strValidationError);
		return false;
	}

	var desc = $("#txtDescription").val();
	if ($("#hidMode").val() === 'edit') {
		//edit an existing tag
		var response = catoAjax.tags.updateTag(old_tag, new_tag, desc);
		if (response) {
			$("#hidCurrentEditID").val("");
			$("#txtSearch").val("");
			GetItems();
			$("#edit_dialog").dialog("close");
		}
	} else if ($("#hidMode").val() === 'add') {
		//add a new tag
		var tag = catoAjax.tags.createTag(new_tag, desc);
		if (tag.Name) {
			$("#hidCurrentEditID").val("");
			$("#txtSearch").val("");
			GetItems();
			$("#edit_dialog").dialog("close");
		}
	}
}

function ShowItemAdd() {
	$("#hidMode").val("add");

	// clear fields
	$('#txtTag').val('');
	$('#txtDescription').val('');

	$('#edit_dialog').dialog('option', 'title', 'Create a New Tag');
	$("#edit_dialog").dialog("open");
	$("#txtTag").focus();
}

function DeleteItems() {
	var response = catoAjax.tags.deleteTags($("#hidSelectedArray").val());
	if (response) {
		$("#hidSelectedArray").val("");
		$("#txtSearch").val("");
		GetItems();
		$("#update_success_msg").text("Delete Successful").show().fadeOut(2000);
		$("#delete_dialog").dialog("close");
	}
}