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

	//the hover event of the codeblock picker activator
	$("#codeblock_selector_btn").hover(function() {
		$("#codeblock_selector").show();
	});
	//and hide it when focus leaves the popup div
	$("#codeblock_selector").mouseleave(function() {
		$(this).hide();
	});

	//make the codeblock add button
	$("#codeblock_add_btn").button({
		icons : {
			primary : "ui-icon-plus"
		}
	});

	//the onclick event of the 'add' link for codeblocks
	$("#codeblock_add_btn").live("click", function() {
		ShowCodeblockEdit('');
	});
	// also if the user hits the enter key in the new codeblock textbox
	//    $("#new_codeblock_name").live("keypress", function(e) {
	//        //alert('keypress');
	//        if (e.which == 13) {
	//            doCodeblockAdd();
	//            return false;
	//        }
	//    });

	//the onclick event of the 'copy' link of each codeblock
	$("#codeblock_selector .codeblock_copy_btn").live("click", function() {
		$("#update_success_msg").text("Copying...").show();

		var cb = $(this).attr("codeblock_name");

		ajaxPostAsync("taskMethods/wmCopyCodeblockStepsToClipboard", {
			sTaskID : g_task_id,
			sCodeblockName : cb
		}, function(response) {
			doGetClips();
			$("#update_success_msg").text("Copy Successful").fadeOut(2000);

			$("#codeblock_selector").hide();
		});
	});

	//the onclick event of the 'delete' link of each codeblock
	$("#codeblock_selector .codeblock_delete_btn").live("click", function() {
		$("#codeblock_to_delete").val($(this).attr("remove_id"));
		$("#codeblock_delete_confirm_dialog").dialog("open");
	});

	//the onclick event of the 'codeblock' elements
	$("#codeblock_selector .codeblock_title").live("click", function() {
		cb = $(this).attr("name");

		$("#hidCodeblockName").val(cb);
		doGetSteps();
		$("#codeblock_selector").hide();
	});
	//the onclick event of the 'codeblock rename icon'
	$("#codeblock_selector .codeblock_rename").live("click", function() {
		cb = $(this).attr("codeblock_name");
		ShowCodeblockEdit(cb);
	});

	//init the codeblock add dialog
	$("#codeblock_edit_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 300
	});

	//init the codeblock delete confirm dialog
	$("#codeblock_delete_confirm_dialog").dialog({
		autoOpen : false,
		draggable : false,
		resizable : false,
		bgiframe : true,
		modal : true,
		overlay : {
			backgroundColor : '#000',
			opacity : 0.5
		},
		buttons : {
			'Delete' : function() {
				$(this).dialog("close");
				doCodeblockDelete();
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});

	//hover effect
	$("#codeblock_selector .codeblock").live("hover", function() {
		$("#te_help_box_detail").html("Click a Codeblock to edit its steps.");
	}, function() {
		$("#te_help_box_detail").html("");
	});

});

function doGetCodeblocks() {
	var response = ajaxPostAsync("taskMethods/wmGetCodeblocks", {
		sTaskID : g_task_id
	}, function(response) {
		$("#codeblocks").html(response);

		// the MAIN codeblock can't be deleted or removed
		$("#codeblock_rename_btn_MAIN").remove();
		$("#codeblock_delete_btn_MAIN").remove();

		//crazy... we can drag out of the codeblock selector!
		if ($("#codeblock_selector .codeblock").hasClass("ui-draggable")) {
			$("#codeblock_selector .codeblock").draggable("destroy");
		}
		$("#codeblock_selector .codeblock").draggable({
			distance : 30,
			connectToSortable : '#steps',
			appendTo : 'body',
			revert : 'invalid',
			scroll : false,
			opacity : 0.95,
			helper : function(event) {
				return $("<div class='ui-widget-content ui-corner-all' style='height: 20px;'>" + $(this).find("span").text() + "</div>");
			},
			start : function(event, ui) {
				$("#dd_dragging").val("true");
			},
			stop : function(event, ui) {
				$("#dd_dragging").val("false");
			}
		});
	}, "html");
}

function ShowCodeblockEdit(codeblock_name) {
	$("#codeblock_edit_dialog_msg").text("");

	//if codeblock_name is empty, we are adding otherwise we are editing
	if (codeblock_name.length > 0) {
		//Enter a name for the Codeblock :
		if (codeblock_name == 'MAIN') {
			// main codeblocks can not be renamed.
			showInfo('The MAIN codeblock can not be renamed.');
			return false;
		};
		$("#new_codeblock_name").val(codeblock_name);
		$("#codeblock_edit_dialog").dialog("option", "buttons", {
			"Save" : function() {
				doCodeblockUpdate(codeblock_name);
			},
			"Cancel" : function() {
				$(this).dialog("close");
			}
		});
	} else {
		//Enter a name for the new Codeblock:
		$("#new_codeblock_name").val('');
		$("#codeblock_edit_dialog").dialog("option", "buttons", {
			"Add" : function() {
				doCodeblockAdd();
			},
			"Cancel" : function() {
				$(this).dialog("close");
			}
		});
	}

	$("#codeblock_edit_dialog").dialog("open");
}

function doCodeblockUpdate(old_name) {
	$("#update_success_msg").text("Updating...").show();
	var sNewCodeblockName = $("#new_codeblock_name").val();

	// before doing the postback, make sure the user entered something in the new name, and that its different than the old name.
	if (sNewCodeblockName == '') {
		return false;
	};

	var response = ajaxPost("taskMethods/wmRenameCodeblock", {
		sTaskID : g_task_id,
		sOldCodeblockName : old_name,
		sNewCodeblockName : sNewCodeblockName
	});
	if (response) {
		$("#codeblock_edit_dialog").dialog("close");

		//if we are looking at the codeblock we are changing... gotta reset the hidden field
		if ($("#hidCodeblockName").val() == old_name) {
			$("#codeblock_steps_title").text(sNewCodeblockName);
			$("#hidCodeblockName").val(sNewCodeblockName);
		}

		//refresh the codeblock list
		doGetCodeblocks();
		//refresh the step list - it's possible a codeblock on the page holds an old value
		doGetSteps();

		$("#update_success_msg").text("Update Successful").fadeOut(2000);
	}

	// since we are reloading the codeblock list, remove the delete button again for the MAIN codeblock
	$("#codeblock_delete_btn_MAIN").remove();
	$("#codeblock_rename_btn_MAIN").remove();

}

function doCodeblockAdd() {
	codeblock_name = $("#new_codeblock_name").val();

	if (codeblock_name != "") {
		$.blockUI({
			message : null
		});
		$("#update_success_msg").text("Updating...").show();

		var response = ajaxPost("taskMethods/wmAddCodeblock", {
			sTaskID : g_task_id,
			sNewCodeblockName : codeblock_name
		});
		if (response) {
			//set the hidden field and label
			$("#hidCodeblockName").val(codeblock_name);
			$("#codeblock_steps_title").text(codeblock_name);

			//refresh the list
			doGetCodeblocks();

			//clear the 'add' box
			$("#new_codeblock_name").val("");

			//it's an extra call, but the best way to set up the new codeblock is to get its steps
			//sure, there will be none, but this sets up the sortable, dropzone and all that.
			doGetSteps();

			$.unblockUI();
			$("#codeblock_edit_dialog").dialog("close");
			$("#update_success_msg").text("Update Successful").fadeOut(2000);
		}

	} else {
		//this would be better if you couldn't click the Add button if it was blank
		$("#codeblock_edit_dialog_msg").text("Codeblock Name is required.");
		$("#new_codeblock_name").focus();
	}

	$("#codeblock_picker").hide();
}

function doCodeblockDelete() {
	var codeblock_name = $("#codeblock_to_delete").val();

	//don't need to block, the dialog blocks.
	$("#update_success_msg").text("Updating...").show();

	var response = ajaxPost("taskMethods/wmDeleteCodeblock", {
		sTaskID : g_task_id,
		sCodeblockID : codeblock_name
	});
	if (response) {
		//remove it from the list of codeblocks
		$("#codeblocks #cb_" + codeblock_name).remove();

		//clear the dialog value
		$("#codeblock_to_delete").val("");

		//when we delete a codeblock we reset the step list to MAIN.
		$("#hidCodeblockName").val("MAIN");
		doGetSteps();

		$("#update_success_msg").text("Update Successful").fadeOut(2000);
	}

	$("#codeblock_picker").hide();
}

