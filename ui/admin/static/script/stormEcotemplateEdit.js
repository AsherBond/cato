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

//This is all the functions to support Storm on the ecoTemplateEdit page.
$(document).ready(function () {
    //Storm buttons
    $("#url_to_text_btn").button({ icons: { primary: "ui-icon-shuffle"} });
    $("#url_to_text_btn").click(function () {
		var storm = GetStorm();
	    if (storm != null) {
			$("#storm_edit_dialog_type").val("Text");
			$("#storm_edit_dialog_text").val(unpackJSON(storm.Text));
			$("#url_to_text_btn").hide();
    	}
    });

    $("#run_storm_btn").button({ icons: { primary: "ui-icon-play"}, disabled: true });
    $("#run_storm_btn").click(function () {
    	if ($(this).hasClass("ui-state-disabled")) { return false; }
    	//check if the function to display the dialog exists
    	//otherwise show a message
        if (typeof(ShowRunStormDialog) != 'undefined') {
            ShowRunStormDialog(g_id);
        } else {
		    $("#run_storm_btn").button("disable");
    	}
    });

	//Storm File edit button and dialog
    $("#edit_storm_btn").button({ icons: { primary: "ui-icon-pencil"} });
    $("#edit_storm_btn").click(function () {
    	//check if the function to display the dialog exists
    	//otherwise show a message
        if (typeof(ShowEditStormDialog) != 'undefined') {
            ShowEditStormDialog();
        } else {
		    $("#edit_storm_btn").hide();
    	}
    });
    $("#storm_edit_dialog").dialog({
        autoOpen: false,
        closeOnEscape: false,
        modal: true,
        width: 800,
        height: 650,
        buttons: [
        	{
        		id: "storm_edit_dialog_ok_btn",
				text: "OK",
				click: function () {
                	SaveStormFile();
            	}
        	},
            {
            	text: "Cancel",
            	click: function () {
                	if (confirm("You have unsaved changes. Are you sure?")) {
                		$(this).dialog("close");
            		}
            	}
        	}
        ]
    });

    //this onchange event will test the json text entry 
    //and display a little warning if it couldn't be parsed.
    $("#storm_edit_dialog_text").change(function () {
		validateStormFileJSON();
    });
    
    //tabs in the editor
    $("#storm_edit_dialog_text").tabby();
    
    //changing the Source dropdown refires the validation
    $("#storm_edit_dialog_type").change(function () {
    	//if it's File, show that section otherwise hide it.
    	if ($(this).val() == "File")
    		$(".stormfileimport").show();
    	else
	    	$(".stormfileimport").hide();
	    	
		validateStormFileJSON();
    });

	//if there was a "run=true" querystring, we'll pop the run dialog.
	//this file MUST be included on the page after ecoTemplateEdit.js, because that's where g_id is defined.
	var run = getQuerystringVariable("run");
    if (run == "true") {
        ShowRunStormDialog(g_id);
    }
    
	//wire up the json "validate" button and other niceties.
	$("#validate").button({ icons: { primary: "ui-icon-check"} });
	$("#validate").click(function () {
		var reformat = ($('#chk_reformat').attr('checked') == "checked" ? true : false);
	    jsl.interactions.validate($("#storm_edit_dialog_text"), $("#json_parse_msg"), reformat, false);
	    return false;
	});
	$("#storm_edit_dialog_text").keyup(function () {
	    $(this).removeClass('greenBorder').removeClass('redBorder');
	});
});

function fileWasSaved(filename) {
	//get the file text from the server and populate the text field.
	$.get(filename, function(data) {
		$("#storm_edit_dialog_text").val(data);
        $(".stormfileimport").hide();
        $("#storm_edit_dialog_type").val("Text");
        validateStormFileJSON();
	}, "text");
}

function ShowStorm() {
	//gets the details of Storm and sets it up on the page    
    var storm = GetStorm();
    if (storm != null) {
        //$("#storm_file_error").html(storm.Error);
        $("#storm_file_source").html(storm.FileType);
        $("#storm_file_url").html(unpackJSON(storm.URL));
        $("#storm_file_desc").html(unpackJSON(storm.HTMLDescription));
        $("#storm_file_text").html(unpackJSON(storm.HTMLText));
    
		$("#storm_file_error").empty();
		$("#storm_file_error").hide();
    	$("#run_storm_btn").button("disable");

    	var storm_text = unpackJSON(storm.Text);
    	
    	if (storm_text.length > 0) {
	    	jsl.interactions.json_in(storm_text);
		    var success = jsl.interactions.validate_string();
	        if (success) {
	        	$("#run_storm_btn").button("enable");
			} else {
				$("#storm_file_error").text(jsl.interactions.validation_msg());
				$("#storm_file_error").show();
			}
        }



        //turn on the buttons
        $("#edit_storm_btn").show();
	}
}

function GetStorm() {
    //gets the storm details for an Ecosystem, but several different functions consume the results
    var storm = null;
    
    $.ajax({
        async: false,
        type: "POST",
        url: "ecoMethods/wmGetEcotemplateStorm",
        data: '{"sEcoTemplateID":"' + g_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
			storm = response
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
    
    return storm;
}

function ShowEditStormDialog() {
	//hide the OK button, it'll get enabled if the json is valid.
	$("#storm_edit_dialog_ok_btn").hide();
	
	//get the details of the Storm and populate the edit dialog.
	var storm = GetStorm();
    if (storm != null) {
		$("#storm_edit_dialog_type").val(storm.FileType);
		
		//if it's a URL, we want to edit the URL, not the data.
		if (storm.FileType == "URL") {
			$("#storm_edit_dialog_text").val(unpackJSON(storm.URL));
			
			//show the url_to_text button
			$("#url_to_text_btn").show();
		} else {
			$("#storm_edit_dialog_text").val(unpackJSON(storm.Text));

			//hide the url_to_text button
			$("#url_to_text_btn").hide();
		}
		
	    $("#storm_edit_dialog").dialog("open");
		
		//CANNOT validate the json unless the textarea is visible.
		//this mustn't happen on a closed or otherwise hidden dialog
		//because "setSelectionRange" fails on a hidden element.
		validateStormFileJSON();
	} else {
		showAlert("Unable to edit Storm.  Could not get Storm File.");
	}
}

function SaveStormFile() {
	var sfs = packJSON($("#storm_edit_dialog_type").val());
	var sf = packJSON($("#storm_edit_dialog_text").val());
	
    $.ajax({
        async: false,
        type: "POST",
        url: "ecoMethods/wmUpdateEcotemplateStorm",
        data: '{"sEcoTemplateID":"' + g_id + '", "sStormFileSource":"' + sfs + '", "sStormFile":"' + sf + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
        	if (response.error) {
        		showAlert(response.error);
        	} else if (response.info) {
        		showInfo(response.info);
        	} else if (response.result == "success") {
	            ShowStorm();
	         	$("#storm_edit_dialog").dialog("close");
           	} else {
                showInfo(response);
            }
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });

}

function validateStormFileJSON() {
	//clear previous errors
	$("#json_parse_msg").empty().removeClass("ui-state-error").removeClass("ui-state-happy");			
	$("#storm_edit_dialog_text").empty().removeClass("redBorder").removeClass("greenBorder");

	//no create button yet...
	$("#storm_edit_dialog_ok_btn").hide();

	//each source type has a slightly different behavior
	if ($("#storm_edit_dialog_type").val() == "URL") {
		$(".validation").hide();
		$("#storm_edit_dialog_ok_btn").show();
		return;
	} else if ($("#storm_edit_dialog_type").val() == "File") {
		$(".validation").hide();
		return;
	} else {	
		//call the validate function
		var reformat = ($('#chk_reformat').attr('checked') == "checked" ? true : false);
	    jsl.interactions.validate($("#storm_edit_dialog_text"), $("#json_parse_msg"), reformat, false);
	    
	    //if the validation failed (the box has the error class), disable the create button
	    if ($("#json_parse_msg").hasClass("ui-state-happy")) {
	    	$("#storm_edit_dialog_ok_btn").show();
	    }
	    
		$(".validation").show();
	}
}
