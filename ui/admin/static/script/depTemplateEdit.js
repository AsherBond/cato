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

//This is all the functions to support the depTemplateEdit page.
var g_id;
var editor;

$(document).ready(function() {"use strict";
	//used a lot
	g_id = getQuerystringVariable("template_id");

	//fix certain ui elements to not have selectable text
	$("#toolbox .toolbox_tab").disableSelection();

	//specific field validation and masking
	$("#txtTemplateName").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	$("#txtDescription").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	//enabling the 'change' event for the Details tab
	$("#div_details :input[te_group='detail_fields']").change(function() {
		doDetailFieldUpdate(this);
	});
	//jquery buttons
	$("#task_search_btn").button({
		icons : {
			primary : "ui-icon-search"
		}
	});

	//create_deployment button
	$("#deployment_create_btn").button({
		icons : {
			primary : "ui-icon-plus"
		}
	});
	$("#deployment_create_btn").click(function() {
		$("#new_deployment_name").val('');
		$("#new_deployment_desc").val('');

		$("#deployment_add_dialog").dialog("open");
	});
	//create deployment dialog
	$("#deployment_add_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 500,
		buttons : {
			"Create" : function() {
				newDeployment();
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});

	//this onchange event will test the json text entry
	//and display a little warning if it couldn't be parsed.
	$("#txtTemplate").change(function() {
		validateTemplateJSON();
	});

	// the onchange event of the icon picker will fire the draw() function
	// and draw the icon on the canvas.
	// document.getElementById("uploadimage").addEventListener("change", draw, false)
	$("#uploadimage").change(function() {
		saveicon();
	});

	//tabs in the editor
	$("#txtTemplate").tabby();

	//wire up the json "validate" button and other niceties.
	$("#validate").button({
		icons : {
			primary : "ui-icon-check"
		}
	});
	$("#validate").click(function() {
		var reformat = ($('#chk_reformat').attr('checked') === "checked" ? true : false);
		jsl.interactions.validate($("#txtTemplate"), $("#json_parse_msg"), reformat, false);
		return false;
	});
	$("#txtTemplate").keyup(function() {
		$(this).removeClass('greenBorder').removeClass('redBorder');
	});

	$("#text_save_btn").button({
		icons : {
			primary : "ui-icon-disk"
		}
	});
	$("#text_save_btn").click(function() {
		var isvalid = doAnalyze($("#txtTemplate").val());
		doDetailFieldUpdate($("#txtTemplate"));
	});
	$("#editor_save_btn").button({
		icons : {
			primary : "ui-icon-disk"
		}
	});
	$("#editor_save_btn").click(function() {
		//since this function updates from a control not a data argument,
		//move the editor text to the text box...
		$("#txtTemplate").val(JSON.stringify(editor.get()));
		var isvalid = doAnalyze($("#txtTemplate").val());
		doDetailFieldUpdate($("#txtTemplate"));
	});

	// the Analyze buttons parse the template and verify it's accuracy
	// generating any warnings needed.
	$("#text_analyze_btn").button({
		icons : {
			primary : "ui-icon-check"
		}
	});
	$("#text_analyze_btn").click(function() {
		var isvalid = doAnalyze($("#txtTemplate").val());
		if (isvalid) {
			showInfo("Template is Valid.");
		}
	});
	$("#editor_analyze_btn").button({
		icons : {
			primary : "ui-icon-check"
		}
	});
	$("#editor_analyze_btn").click(function() {
		//since this function updates from a control not a data argument,
		//move the editor text to the text box...
		$("#txtTemplate").val(JSON.stringify(editor.get()));
		var isvalid = doAnalyze($("#txtTemplate").val());
		if (isvalid) {
			showInfo("Template is Valid.");
		}
	});

	//there are two different editors... set up the tabs
	$("#editor_tabs").tabs({
		select : function(event, ui) {
			// when switching the tabs, we'll move the content from
			// the CURRENT editor to the TARGET editor
			if ($.trim(ui.tab.text) === "Text") {
				//move the editor code to the text box
				$("#txtTemplate").val(JSON.stringify(editor.get()));
				validateTemplateJSON();
			}
			if ($.trim(ui.tab.text) === "Editor") {
				//move the text box code to the editor
				var jstxt = $("#txtTemplate").val();
				try {
					var jsobj = JSON.parse(jstxt)
					editor.set(jsobj);
				} catch (ex) {
					showAlert("Unable to display Template in editor: \n" + ex.message);
				}
			}
		}
	});
	$("#editor_tabs").show();

	// set up the json editor (global object)
	editor = new JSONEditor($("#jsoneditor")[0]);

	getDetails();

});

function getDetails() {"use strict";
	var template = catoAjax.deployment.getTemplate(g_id);
	if (template) {
		$("#hidTemplateID").val(template.ID);
		$("#txtTemplateName").val(template.Name);
		$("#txtTemplateVersion").val(template.Version);
		$("#txtDescription").val(template.Description);
		$("#txtTemplate").val(template.Text);
		
		// draw the icon on the canvas
		// FROM OUR SPECIAL appicon url that handles delivering an image from the db.
		drawicon("/appicon/" + template.ID);

		try {
			var jsobj = JSON.parse(template.Text)
			editor.set(jsobj);
		} catch (ex) {
			showAlert("Unable to display Template in editor: \n" + ex.message);
		}

		validateTemplateJSON();
	}

}

function getDeployments() {
	var response = catoAjax.deployment.getTemplateDeployments(g_id);
	if (response) {
		$("#deployment_results").html(response);

		//task description tooltips on the task picker dialog
		$("#deployment_results .deployment_tooltip").tipTip({
			defaultPosition : "right",
			keepAlive : false,
			activation : "hover",
			maxWidth : "500px",
			fadeIn : 100
		});

		// $(".deployment_name").click(function() {
		// showPleaseWait();
		// location.href = 'deploymentEdit?deployment_id=' + $(this).parents("li").attr('deployment_id');
		// });
	}
}

function tabWasClicked(tab) {"use strict";
	//we'll be hiding and showing right side content when tabs are selected.
	//several tabs on the page use the same detail, so make it the default.
	var detail_div = "#div_details_detail";

	//the generic toolbox.js file handles the click event that will call this function if it exists
	//several tabs here all use the same detail panel
	if (tab === "deployments") {
		getDeployments();
	} else if (tab === "details") {
		getDetails();
	} else if (tab == "tags") {
		if ( typeof (GetObjectsTags) != 'undefined') {
			GetObjectsTags(g_id);
		}
	}

	//hide 'em all
	$("#content_te .detail_panel").addClass("hidden");
	//show the one you clicked
	$(detail_div).removeClass("hidden");
}

function doAnalyze(template) {"use strict";
	return catoAjax.deployment.validateTemplate(template);
}

function doDetailFieldUpdate(ctl) {"use strict";
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

	if (column.length > 0) {
		$("#update_success_msg").text("Updating...").show();

		var args = {};
		args.id = g_id;
		args.column = column;
		//escape it
		args.value = packJSON(value);

		var response = catoAjax.deployment.updateTemplateDetail(args);
		if (response) {
			$("#update_success_msg").text("Update Successful").fadeOut(2000);
			showInfo("Update Successful");
		}
	}

}

function newDeployment() {"use strict";
	alert("Not implemented in Cato.\n\nUse the Maestro application to create Deployments.");
	return;
}

function validateTemplateJSON() {"use strict";
	//clear previous errors
	$("#json_parse_msg").empty().removeClass("ui-state-error").removeClass("ui-state-happy");
	$("#txtTemplate").removeClass("redBorder").removeClass("greenBorder");

	//no create button yet...
	$("#text_save_btn").hide();

	//each source type has a slightly different behavior
	//call the validate function
	var reformat = ($('#chk_reformat').attr('checked') === "checked" ? true : false);
	jsl.interactions.validate($("#txtTemplate"), $("#json_parse_msg"), reformat, false);

	//if the validation failed (the box has the error class), disable the create button
	if ($("#json_parse_msg").hasClass("ui-state-happy")) {
		$("#text_save_btn").show();
	}

	$(".validation").show();
}

function drawicon(imgurl) {
    var ctx = document.getElementById('canvas').getContext('2d'),
        img = new Image();

    img.src = imgurl;
    img.onload = function() {
        ctx.drawImage(img, 0, 0);
        url.revokeObjectURL(src);
    }
}

function saveicon(ev) {
    // console.log(ev);
    var ctx = document.getElementById('canvas').getContext('2d'),
        img = new Image(),
        f = document.getElementById("uploadimage").files[0],
        url = window.URL || window.webkitURL,
        src = url.createObjectURL(f);

    img.src = src;
    img.onload = function() {
        ctx.drawImage(img, 0, 0);
        url.revokeObjectURL(src);
        
        // now update the db
        dataurl = document.getElementById("canvas").toDataURL();
        $("#iconb64").val(dataurl.replace("data:image/png;base64,", ""));
        $("#iconb64").change();
    }
}
