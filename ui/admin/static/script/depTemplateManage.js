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
	$('#edit_dialog').dialog('option', 'title', 'New Deployment Template');
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
				$(':input', (".jtable")).attr('checked', false);

				$(this).dialog("close");
			}
		}]
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
		var reformat = ($('#chk_reformat').attr('checked') == "checked" ? true : false);
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
		page = "1"
	$.ajax({
		type : "POST",
		async : true,
		url : "depMethods/wmGetTemplatesTable",
		data : '{"sSearch":"' + $("#txtSearch").val() + '", "sPage":"' + page + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(response) {
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

		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function ShowItemAdd() {
	$("#hidMode").val("add");

	// clear all of the previous values
	clearEditDialog();

	//but we want the Format box to be checked
	$('#chk_reformat').attr('checked', 'checked')
	$("#edit_dialog").dialog("open");
	$("#txtTemplateName").focus();
}

function DeleteItems() {
	var ArrayString = $("#hidSelectedArray").val();
	$.ajax({
		type : "POST",
		url : "depMethods/wmDeleteTemplates",
		data : '{"sDeleteArray":"' + ArrayString + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(response) {
			if (response.info) {
				showInfo(response.info);
			} else if (response.error) {
				showAlert(response.error);
			} else if (response.result == "success") {
				$("#hidSelectedArray").val("");
				$("#delete_dialog").dialog("close");

				// clear the search field and fire a search click, should reload the grid
				$("#txtSearch").val("");
				GetItems();

				hidePleaseWait();
				showInfo('Delete Successful');
			} else {
				showAlert(response);

				$("#delete_dialog").dialog("close");

				// reload the list, some may have been deleted.
				// clear the search field and fire a search click, should reload the grid
				$("#txtSearch").val("");
				GetItems();
			}

			$("#hidSelectedArray").val("");
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});

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
	if ($("#txtTemplateFile").val() == "") {
		bSave = false;
		strValidationError += 'Template definition is required.';
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

	$.ajax({
		async : false,
		type : "POST",
		url : "depMethods/wmCreateTemplate",
		data : JSON.stringify(args),
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(response) {
			if (response.info) {
				showInfo(response.info);
			} else if (response.error) {
				showAlert(response.error);
			} else if (response.template_id) {
				showPleaseWait();

				location.href = "depTemplateEdit?template_id=" + response.template_id;
			} else {
				showInfo(response, "", true);
			}
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function GetTemplateFromURL() {
	var url = $("#txtTemplateFile").val();

	if(url.length == 0)
		return;

	$.ajax({
		async : false,
		type : "POST",
		url : "depMethods/wmGetTemplateFromURL",
		data : '{"sURL":"' + packJSON(url) + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "text",
		success : function(response) {
			if(response.length > 0) {
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
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
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
	if($("#ddlTemplateSource").val() == "URL") {
		$(".validation").hide();
		$("#edit_dialog_create_btn").show();
		return;
	} else if($("#ddlTemplateSource").val() == "File") {
		$(".validation").hide();
		return;
	} else {
		//call the validate function
		var reformat = ($('#chk_reformat').attr('checked') == "checked" ? true : false);
		jsl.interactions.validate($("#txtTemplateFile"), $("#json_parse_msg"), reformat, false);

		//if the validation failed (the box has the error class), disable the create button
		if($("#json_parse_msg").hasClass("ui-state-happy")) {
			$("#edit_dialog_create_btn").show();
		}

		$(".validation").show();
	}
}
