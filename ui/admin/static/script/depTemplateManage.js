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
				showPleaseWait();
				CopyTemplate();
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});

	//this onchange event will test the json text entry
	//and display a little warning if it couldn't be parsed.
	$("#txtTemplateFile").change(function() {
		validateTemplateJSON();
	});

	//tabs in the editor
	$("#txtTemplateFile").tabby();

	//changing the Source dropdown refires the validation
	$("#ddlTemplateSource").change(function() {
		//if it's File, show that section otherwise hide it.
		if ($(this).val() == "File")
			$(".templatefileimport").show();
		else
			$(".templatefileimport").hide();

		if ($(this).val() == "URL") {
			$("#url_to_text_btn").show();
		} else {
			$("#url_to_text_btn").hide();
		}

		validateTemplateJSON();
	});

	//wire up the json "validate" button and other niceties.
	$("#validate").button({
		icons : {
			primary : "ui-icon-check"
		}
	});
	$("#validate").click(function() {
		var reformat = ($('#chk_reformat').prop('checked') ? true : false);
		jsl.interactions.validate($("#txtTemplateFile"), $("#json_parse_msg"), reformat, false);
		return false;
	});

	$("#url_to_text_btn").button({
		icons : {
			primary : "ui-icon-shuffle"
		}
	});
	$("#url_to_text_btn").click(function() {
		GetTemplateFromURL();
	});
	$("#url_to_text_btn").hide();

	ManagePageLoad();
	GetItems();
});

function GetItems(page) {
	if (!page)
		page = "1";
	var response = catoAjax.deployment.getTemplatesTable($("#txtSearch").val(), page);
	if (response) {
		pager = unpackJSON(response.pager);
		html = unpackJSON(response.rows);

		$("#pager").html(pager);
		$("#pager .pager_button").click(function() {
			GetItems($(this).text());
		});

		$("#templates").html(html);
		//gotta restripe the table
		initJtable(true, true);

		//what happens when you click a row?
		$(".selectable").click(function() {
			showPleaseWait();
			location.href = '/depTemplateEdit?template_id=' + $(this).parent().attr("template_id");
		});
	}
}

function ShowItemAdd() {
	$("#hidMode").val("add");

	// clear all of the previous values
	clearEditDialog();

	//but we want the Format box to be checked
	$('#chk_reformat').prop('checked', true);
	$("#edit_dialog").dialog("open");
	$("#txtTemplateName").focus();
}

function DeleteItems() {
	var response = catoAjax.deployment.deleteTemplates($("#hidSelectedArray").val());
	if (response) {
		$("#hidSelectedArray").val("");
		$("#txtSearch").val("");
		GetItems();
		$("#update_success_msg").text("Delete Successful").show().fadeOut(2000);
	}
	$("#delete_dialog").dialog("close");
}

function Save() {
	var bSave = true;
	var strValidationError = '';

	//some client side validation before we attempt to save the user
	if ($("#txtTemplateName").val() == "") {
		bSave = false;
		strValidationError += 'Name is required.';
	};
	if ($("#txtTemplateVersion").val() == "") {
		bSave = false;
		strValidationError += 'Version is required.';
	};

	if (bSave != true) {
		showAlert(strValidationError);
		return false;
	}

	args = {};
	args.name = $("#txtTemplateName").val();
	args.version = $("#txtTemplateVersion").val();
	args.desc = packJSON($("#txtTemplateDesc").val());
	args.template = packJSON($("#txtTemplateFile").val());

	var response = catoAjax.deployment.createTemplate(args);
	if (response) {
		showPleaseWait();

		location.href = "depTemplateEdit?template_id=" + response.template_id;
	}
}

function GetTemplateFromURL() {
	var url = $("#txtTemplateFile").val();

	if (url.length == 0)
		return;

	var response = catoAjax.deployment.getTemplateFromURL(url);
	if (response) {
		if (response.length > 0) {
			try {
				$("#ddlTemplateSource").val("Text");
				$("#txtTemplateFile").val(unpackJSON(response));
				$("#url_to_text_btn").hide();
				validateTemplateJSON();
			} catch(err) {
				showAlert(err.message);
			}
		} else {
			showAlert("Nothing returned from url [" + url + "].");
		}
	}
}

function fileWasSaved(filename) {
	//get the file text from the server and populate the text field.
	$.get("temp/" + filename, function(data) {
		$("#txtTemplateFile").val(data);
		$(".templatefileimport").hide();
		$("#ddlTemplateSource").val("Text");
		validateTemplateJSON();
	}, "text");
}

function validateTemplateJSON() {
	//clear previous errors
	$("#json_parse_msg").empty().removeClass("ui-state-error").removeClass("ui-state-happy");
	$("#txtTemplateFile").empty().removeClass("redBorder").removeClass("greenBorder");

	//no create button yet...
	$("#edit_dialog_create_btn").hide();

	//each source type has a slightly different behavior
	if ($("#ddlTemplateSource").val() == "URL") {
		$(".validation").hide();
		$("#edit_dialog_create_btn").show();
		return;
	} else if ($("#ddlTemplateSource").val() == "File") {
		$(".validation").hide();
		return;
	} else {
		//call the validate function
		var reformat = ($('#chk_reformat').prop('checked') ? true : false);
		jsl.interactions.validate($("#txtTemplateFile"), $("#json_parse_msg"), reformat, false);

		//if the validation failed (the box has the error class), disable the create button
		if ($("#json_parse_msg").hasClass("ui-state-happy")) {
			$("#edit_dialog_create_btn").show();
		}

		$(".validation").show();
	}
}

function ShowItemCopy() {
	// clear all of the previous values
	var ArrayString = $("#hidSelectedArray").val();
	if (ArrayString.length == 0) {
		showInfo('Select a Template to Copy.');
		return false;
	}

	// before loading the task copy dialog, we need to get the task_code for the
	// first task selected, to be able to show something useful in the copy message.
	var myArray = ArrayString.split(',');

	var copy_id = myArray[0];

	//alert(myArray[0]);
	var src_name = $("[template_id=" + copy_id +"] td")[1].innerHTML;
	var src_ver = $("[template_id=" + copy_id +"] td")[2].innerHTML;
	$("#lblTemplateCopy").html('<b>Copying ' + src_name + ' Version ' + src_ver + '</b><br />&nbsp;<br />');
	$("[tag='chk']").prop("checked", false);
	$("#hidSelectedArray").val('');
	$("#hidCopyTemplateID").val(copy_id);
	$("#lblItemsSelected").html("0");
	$("#txtCopyTemplateName").val('');
	$("#txtCopyTemplateVersion").val('');

	$("#copy_dialog").dialog("open");
}

function CopyTemplate() {
	var sNewName = $("#txtCopyTemplateName").val();
	var sNewVersion = $("#txtCopyTemplateVersion").val();
	var sSourceID = $("#hidCopyTemplateID").val();

	// make sure we have all of the valid fields
	if (sNewName == '' || sNewVersion == '') {
		showInfo('Name and Version are required.');
		return false;
	}
	// this shouldnt happen, but just in case.
	if (sSourceID == '') {
		showInfo('Can not copy, no ID found.');
		return false;
	}

	var response = ajaxPost("depMethods/wmCopyTemplate", {
		template : sSourceID,
		name : sNewName,
		version : sNewVersion
	});
	if (response) {
		$("#copy_dialog").dialog("close");
		$("#txtSearch").val("");
		GetItems();
		hidePleaseWait();
		showInfo('Copy Successful.');
	}
}
