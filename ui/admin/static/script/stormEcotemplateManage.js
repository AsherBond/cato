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
	//use storm?
	$("#use_storm_btn").click(function() {
		if($(this).is(':checked')) {
			$(".stormfields").show();
			//create button hidden until a valid source file/url is set
			$("#edit_dialog_create_btn").hide();
			//clear previous errors
			$("#json_parse_msg").empty().removeClass("ui-state-error").removeClass("ui-state-happy");
			$("#txtStormFile").empty().removeClass("redBorder").removeClass("greenBorder");
		} else {
			$(".stormfields").hide();
			$("#edit_dialog_create_btn").show();
		}

		$("#edit_dialog").dialog('option', 'position', 'center');
	});

	//this onchange event will test the json text entry
	//and display a little warning if it couldn't be parsed.
	$("#txtStormFile").change(function() {
		validateStormFileJSON();
	});

	//tabs in the editor
	$("#txtStormFile").tabby();

	//changing the Source dropdown refires the validation
	$("#ddlStormFileSource").change(function() {
		//if it's File, show that section otherwise hide it.
		if($(this).val() == "File")
			$(".stormfileimport").show();
		else
			$(".stormfileimport").hide();

		if($(this).val() == "URL") {
			$("#url_to_text_btn").show();
		} else {
			$("#url_to_text_btn").hide();
		}

		validateStormFileJSON();
	});

	//wire up the json "validate" button and other niceties.
	$("#validate").button({
		icons : {
			primary : "ui-icon-check"
		}
	});
	$("#validate").click(function() {
		var reformat = ($('#chk_reformat').attr('checked') == "checked" ? true : false);
		jsl.interactions.validate($("#txtStormFile"), $("#json_parse_msg"), reformat, false);
		return false;
	});

	$("#storm_edit_dialog_text").keyup(function() {
		$(this).removeClass('greenBorder').removeClass('redBorder');
	});

	$("#url_to_text_btn").button({
		icons : {
			primary : "ui-icon-shuffle"
		}
	});
	$("#url_to_text_btn").click(function() {
		GetStormFileFromURL();
	});
});

function GetStormFileFromURL() {
	var url = $("#txtStormFile").val();

	if(url.length == 0)
		return;

	$.ajax({
		async : false,
		type : "POST",
		url : "ecoMethods/wmGetStormFileFromURL",
		data : '{"sURL":"' + packJSON(url) + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "text",
		success : function(response) {
			if(response.length > 0) {
				try {
					$("#ddlStormFileSource").val("Text");
					$("#txtStormFile").val(unpackJSON(response));
					$("#url_to_text_btn").hide();
					validateStormFileJSON();
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
	$.get(filename, function(data) {
		$("#txtStormFile").val(data);
		$(".stormfileimport").hide();
		$("#ddlStormFileSource").val("Text");
		validateStormFileJSON();
	}, "text");
}

function validateStormFileJSON() {
	//clear previous errors
	$("#json_parse_msg").empty().removeClass("ui-state-error").removeClass("ui-state-happy");
	$("#txtStormFile").empty().removeClass("redBorder").removeClass("greenBorder");

	//no create button yet...
	$("#edit_dialog_create_btn").hide();

	//each source type has a slightly different behavior
	if($("#ddlStormFileSource").val() == "URL") {
		$(".validation").hide();
		$("#edit_dialog_create_btn").show();
		return;
	} else if($("#ddlStormFileSource").val() == "File") {
		$(".validation").hide();
		return;
	} else {
		//call the validate function
		var reformat = ($('#chk_reformat').attr('checked') == "checked" ? true : false);
		jsl.interactions.validate($("#txtStormFile"), $("#json_parse_msg"), reformat, false);

		//if the validation failed (the box has the error class), disable the create button
		if($("#json_parse_msg").hasClass("ui-state-happy")) {
			$("#edit_dialog_create_btn").show();
		}

		$(".validation").show();
	}
}
