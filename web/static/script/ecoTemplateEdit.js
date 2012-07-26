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

//This is all the functions to support the ecoTemplateEdit page.
$(document).ready(function() {
	getScript("storm.js");
	getScript("stormRunDialog.js");

	//used a lot
	g_id = getQuerystringVariable("ecotemplate_id");

	//fix certain ui elements to not have selectable text
	$("#toolbox .toolbox_tab").disableSelection();

	//specific field validation and masking
	$("#txtEcoTemplateName").keypress(function(e) {
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

	//create_ecosystem button
	$("#ecosystem_create_btn").button({
		icons : {
			primary : "ui-icon-plus"
		}
	});
	$("#ecosystem_create_btn").click(function() {
		$("#new_ecosystem_name").val('');
		$("#new_ecosystem_desc").val('');

		$("#ecosystem_add_dialog").dialog("open");
	});
	//create ecosystem dialog
	$("#ecosystem_add_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 500,
		buttons : {
			"Create" : function() {
				NewEcosystem();
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});

	//caction icon picker dialog
	$("#action_icon_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 600,
		buttons : {
			"Save" : function() {
				SaveIcon();
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});

	//the hook for the 'show log' link
	$("#show_log_link").button({
		icons : {
			primary : "ui-icon-document"
		}
	});
	$("#show_log_link").click(function() {
		ShowLogViewDialog(42, g_id, true);
	});
	//turn on the "add" button in the dropzone
	$("#action_add_btn").button({
		icons : {
			primary : "ui-icon-plus"
		}
	});
	$("#action_add_btn").click(function() {
		addAction();
	});
	//and the cancel button
	$("#action_add_cancel_btn").button({
		icons : {
			primary : "ui-icon-plus"
		}
	});
	$("#action_add_cancel_btn").click(function() {
		$("#action_add_form").hide().prev().show();
	});
	//dragging tasks from the task tab can be dropped on the drop zone to add a new Action
	$("#action_add").droppable({
		drop : function(event, ui) {
			var task_label = ui.draggable.find(".search_dialog_value_name").html();

			//clear the field
			$("#new_action_name").val("");

			$("#action_add_otid").val(ui.draggable.attr("original_task_id"));
			$("#action_add_task_name").html(task_label);
			$("#action_name_helper").hide().next().show();
			$("#new_action_name").focus();

			$(this).removeClass("ui-state-highlight")
		},
		over : function(event, ui) {
			$(this).addClass("ui-state-highlight")
		},
		out : function(event, ui) {
			$(this).removeClass("ui-state-highlight")
		}
	});

	//the onclick event of the Task Tab search button
	$("#task_search_btn").click(function() {
		//var field = $("#" + $("#task_picker_target_field_id").val());

		$("#div_tasks").block({
			message : null,
			cursor : 'wait'
		});
		var search_text = $("#task_search_text").val();
		$.ajax({
			async : false,
			type : "POST",
			url : "taskMethods/wmTaskSearch",
			data : '{"sSearch":"' + search_text + '"}',
			contentType : "application/json; charset=utf-8",
			dataType : "html",
			success : function(response) {
				$("#task_picker_results").html(response);

				$("#task_picker_results .task_picker_value").disableSelection();
				$("#div_tasks").unblock();

				//task description tooltips on the task picker dialog
				$("#task_picker_results .search_dialog_tooltip").tipTip({
					defaultPosition : "right",
					keepAlive : false,
					activation : "hover",
					maxWidth : "500px",
					fadeIn : 100
				});

				initDraggable();

			},
			error : function(response) {
				showAlert(response.responseText);
			}
		});
	});
	//what happens when you change a value on an action?
	//(we're binding this to any field that has a "field" attribute.
	$('[column]').live('change', function() {
		doActionFieldUpdate(this);
	});
	// enter key for task search
	$("#task_search_txt").live("keypress", function(e) {
		if(e.which == 13) {
			$("#task_search_btn").click();
			return false;
		}
	});
	// enter key for Action Add
	$("#new_action_name").live("keypress", function(e) {
		if(e.which == 13) {
			$("#action_add_btn").click();
			return false;
		}
	});
	//init the parameter dialog
	$("#action_parameter_dialog").dialog({
		autoOpen : false,
		modal : false,
		width : 500,
		open : function(event, ui) {
			$(".ui-dialog-titlebar-close", ui).hide();
		},
		buttons : {
			OK : function() {
				SaveParameterDefaults();
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});

	GetDetails();

	//last, because it can load before the user sees it.
	$('#action_icons').load('ecoMethods/wmGetActionIcons', function() {
		$(".action_picker_icon").click(function() {
			//remove the selected class from all and add to this one.
			$(".action_picker_icon").removeClass("action_picker_icon_selected");
			$(this).addClass("action_picker_icon_selected");
	
			$("#selected_action_icon").val($(this).attr("icon_name"));
		});
	});
});
function GetDetails() {
	$.ajax({
		type : "POST",
		async : true,
		url : "ecoMethods/wmGetEcotemplate",
		data : '{"sID":"' + g_id + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(template) {
			try {
				$("#hidEcoTemplateID").val(template.ID);
				$("#txtEcoTemplateName").val(template.Name);
			 	$("#lblEcoTemplateHeader").html(template.Name);
			 	$("#txtDescription").val(unpackJSON(template.Description));
			 	
		 		getActions();
	
				//TONS of stuff happens here to initialize the action widgets that were just returned.
				// these are all 'live' bindings, but in a function just so this block isn't so huge.
				initActions();

			} catch (ex) {
				showAlert(ex.message);
			}
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function SaveIcon() {
	var action_id = $("#selected_action_id").val();
	var value = $("#selected_action_icon").val();
	var icon = value;
	//because the value is getting encoded for the wire

	//escape it
	value = packJSON(value);

	$("#update_success_msg").text("Updating...").show();
	$.ajax({
		async : false,
		type : "POST",
		url : "ecoMethods/wmUpdateEcoTemplateAction",
		data : '{"sEcoTemplateID":"' + g_id + '","sActionID":"' + action_id + '","sColumn":"action_icon","sValue":"' + value + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "text",
		success : function(response) {
			if (response != "") {
				$("#update_success_msg").text("Update Failed").fadeOut(2000);
				showInfo(response);
			} else {
				//update the icon on the page
				$("#ac_" + action_id).find(".action_icon").attr("src", "static/images/actions/" + icon);
				$("#update_success_msg").text("Update Successful").fadeOut(2000);
			}
		},
		error : function(response) {
			$("#update_success_msg").fadeOut(2000);
			showAlert(response.responseText);
		}
	});

	$("#action_icon_dialog").dialog("close");
}

function tabWasClicked(tab) {
	//we'll be hiding and showing right side content when tabs are selected.
	//several tabs on the page use the same detail, so make it the default.
	var detail_div = "#div_details_detail";

	//the generic toolbox.js file handles the click event that will call this function if it exists
	//several tabs here all use the same detail panel
	if(tab == "storm") {
		ShowStorm();
		detail_div = "#div_storm_detail";
	} else if(tab == "ecosystems") {
		GetEcosystems();
    } else if (tab == "tags") {
        if (typeof(GetObjectsTags) != 'undefined') {
	        GetObjectsTags($("#hidEcoTemplateID").val());
        }
	} else if(tab == "details") {
		GetDetails();
	}

	//hide 'em all
	$("#content_te .detail_panel").addClass("hidden");
	//show the one you clicked
	$(detail_div).removeClass("hidden");
}

function CloudAccountWasChanged() {
	GetEcosystems();
}

function GetEcosystems() {
	$.ajax({
		async : false,
		type : "POST",
		url : "ecoMethods/wmGetEcotemplateEcosystems",
		data : '{"sEcoTemplateID":"' + g_id + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "html",
		success : function(response) {
			$("#ecosystem_results").html(response);

			//task description tooltips on the task picker dialog
			$("#ecosystem_results .ecosystem_tooltip").tipTip({
				defaultPosition : "right",
				keepAlive : false,
				activation : "hover",
				maxWidth : "500px",
				fadeIn : 100
			});

			$(".ecosystem_name").click(function() {
				showPleaseWait();
				location.href = 'ecosystemEdit?ecosystem_id=' + $(this).parents("li").attr('ecosystem_id');
			});
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function ShowParameterDialog(action_id) {
	$("#action_parameter_dialog_action_id").val(action_id);

	$.ajax({
		async : false,
		type : "POST",
		url : "taskMethods/wmGetParameterXML",
		data : '{"sType":"action","sID":"' + action_id + '","sFilterByEcosystemID":""}',
		contentType : "application/json; charset=utf-8",
		dataType : "text",
		success : function(response) {
			if(response != "")
				parameter_xml = $.parseXML(response);
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});

	//using the same function and layout that we do for the task launch dialog.
	var output = DrawParameterEditForm(parameter_xml);
	$("#action_parameter_dialog_params").html(output);

	bindParameterToolTips();

	$("#action_parameter_dialog").dialog("open");
}

function SaveParameterDefaults() {
	var action_id = $("#action_parameter_dialog_action_id").val();

	$("#update_success_msg").text("Saving Defaults...");

	//build the XML from the dialog
	var parameter_xml = packJSON(buildXMLToSubmit());
	//alert(parameter_xml);

	$.ajax({
		async : false,
		type : "POST",
		url : "taskMethods/wmSaveDefaultParameterXML",
		data : '{"sType":"action","sID":"' + action_id + '","sXML":"' + parameter_xml + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "text",
		success : function(response) {
			$("#update_success_msg").text("Save Successful").fadeOut(2000);
		},
		error : function(response) {
			$("#update_success_msg").fadeOut(2000);
			showAlert(response.responseText);
		}
	});

	$("#action_parameter_dialog").dialog("close");

}

function getActions() {
	$.ajax({
		async : false,
		type : "POST",
		url : "ecoMethods/wmGetEcotemplateActions",
		data : '{"sEcoTemplateID":"' + g_id + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "html",
		success : function(response) {
			$("#category_actions").html(response);
			$("#actions").unblock();
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function addAction() {
	var otid = $("#action_add_otid").val();
	var action_name = $("#new_action_name").val();

	//loop the name fields looking for this value.
	var exists = $("input[column='action_name'][value='" + action_name + "']").length;

	if(exists > 0) {
		alert("An Action with that name already exists.");
		$("#new_action_name").val("");
		$("#new_action_name").focus();
		return;
	}

	if(action_name.length > 0) {
		//this ajax takes forever... block it.
		$("#actions").block({
			message : null,
			cursor : 'wait'
		});

		$("#update_success_msg").text("Updating...").show();
		$.ajax({
			async : true,
			type : "POST",
			url : "ecoMethods/wmAddEcotemplateAction",
			data : '{"sEcoTemplateID":"' + g_id + '","sActionName":"' + action_name + '","sOTID":"' + otid + '"}',
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(msg) {
				$("#update_success_msg").text("Update Successful").fadeOut(2000);

				//reset the input dropzone
				$("#action_add_form").hide().prev().show();

				// get the whole list again
				getActions();
			},
			error : function(response) {
				$("#update_success_msg").fadeOut(2000);
				showAlert(response.responseText);
			}
		});
	} else {
		alert("Please enter an Action Name.");
	}

}

function doActionFieldUpdate(ctl) {
	var action_id = $(ctl).parents("li").attr('id').replace(/ac_/, "");
	var column = $(ctl).attr("column");
	var value = $(ctl).val();

	//escape it
	value = packJSON(value);

	if(column.length > 0) {
		$("#update_success_msg").text("Updating...").show();
		$.ajax({
			async : false,
			type : "POST",
			url : "ecoMethods/wmUpdateEcoTemplateAction",
			data : '{"sEcoTemplateID":"' + g_id + '","sActionID":"' + action_id + '","sColumn":"' + column + '","sValue":"' + value + '"}',
			contentType : "application/json; charset=utf-8",
			dataType : "text",
			success : function(response) {
				if(response != "") {
					$("#update_success_msg").text("Update Failed").fadeOut(2000);
					showInfo(response);
				} else {
					$("#update_success_msg").text("Update Successful").fadeOut(2000);

					// Change the name in the header
					//parents.eq(1) says to get the "second" parent (0 based)
					if(column == "action_name") {
						$(ctl).parents().eq(1).find(".action_name_lbl").html(unpackJSON(value));
					};
					if(column == "category") {
						$(ctl).parents().eq(1).find(".action_category_lbl").html(unpackJSON(value) + " - ");
					};
				}
			},
			error : function(response) {
				$("#update_success_msg").fadeOut(2000);
				showAlert(response.responseText);
			}
		});
	}

}

function doDetailFieldUpdate(ctl) {
	var column = $(ctl).attr("column");
	var value = $(ctl).val();

	//for checkboxes and radio buttons, we gotta do a little bit more, as the pure 'val()' isn't exactly right.
	//and textareas will not have a type property!
	if($(ctl).attr("type")) {
		var typ = $(ctl).attr("type").toLowerCase();
		if(typ == "checkbox") {
			value = (ctl.checked == true ? 1 : 0);
		}
		if(typ == "radio") {
			value = (ctl.checked == true ? 1 : 0);
		}
	}

	//escape it
	value = packJSON(value);

	if(column.length > 0) {
		$("#update_success_msg").text("Updating...").show();
		$.ajax({
			async : false,
			type : "POST",
			url : "ecoMethods/wmUpdateEcotemplateDetail",
			data : '{"sEcoTemplateID":"' + g_id + '","sColumn":"' + column + '","sValue":"' + value + '"}',
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
                    if (column == "Name") { $("#lblEcoTemplateHeader").html(unpackJSON(value)); };
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

function initDraggable() {
	//initialize the 'commands' tab and the clipboard tab to be draggable to the step list
	$("#toolbox .search_dialog_value").draggable("destroy");
	$("#toolbox .search_dialog_value").draggable({
		distance : 30,
		// connectToSortable: '#action_categories',
		appendTo : 'body',
		revert : 'invalid',
		scroll : false,
		opacity : 0.95,
		helper : 'clone'
		//        start: function(event, ui) {
		//            $("#dd_dragging").val("true");
		//        },
		//        stop: function(event, ui) {
		//            $("#dd_dragging").val("false");
		//        }
	});
}

function NewEcosystem() {
	var bSave = true;
	var strValidationError = '';

	//name is required
	if($("#new_ecosystem_name").val() == "") {
		bSave = false;
		strValidationError += 'Please enter an Ecosystem Name.';
		return false;
	};

	//we will test it, but really we're not gonna use it rather we'll get it server side
	//this just traps if there isn't one.
	if($("#header_cloud_accounts").val() == "") {
		bSave = false;
		strValidationError += 'Error: Unable to determine Cloud Account.';
	};

	if(bSave != true) {
		showAlert(strValidationError);
		return false;
	}

	var account_id = $("#header_cloud_accounts").val();
	var name = packJSON($("#new_ecosystem_name").val());
	var desc = packJSON($("#new_ecosystem_desc").val());

	$.ajax({
		async : false,
		type : "POST",
		url : "ecoMethods/wmCreateEcosystem",
		data : '{"sName":"' + name + '","sDescription":"' + desc + '","sEcotemplateID":"' + g_id + '", "sAccountID":"' + account_id + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "json",
        success: function (response) {
        	if (response.error) {
        		showAlert(response.error);
        	} else if (response.info) {
        		showInfo(response.info);
        	} else if (response.id) {
				//just add it to the list here
				GetEcosystems();
				$("#ecosystem_add_dialog").dialog("close");
			} else {
				showAlert(response);
			}
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function initActions() {
	$(".action_remove_btn").live("click", function() {
		var action_id = $(this).parents("li").attr('id').replace(/ac_/, "");

		if(confirm("Removing this Action will remove it from all associated Ecosystems, and cancel any future Action Schedules.\n\nThis cannot be undone.\n\nAre you sure?")) {
			$("#actions").block({
				message : null,
				cursor : 'wait'
			});

			var search_text = $("#task_search_text").val();
			$.ajax({
				async : true,
				type : "POST",
				url : "ecoMethods/wmDeleteEcotemplateAction",
				data : '{"sActionID":"' + action_id + '"}',
				contentType : "application/json; charset=utf-8",
				dataType : "json",
				success : function(retval) {
					//just remove it from the DOM
					$("#ac_" + action_id).remove();

					$("#actions").unblock();
				},
				error : function(response) {
					showAlert(response.responseText);
				}
			});
		}
	});
	$(".action_icon").live("click", function() {
		$("#selected_action_id").val($(this).parents("li").attr('id').replace(/ac_/, ""));

		//look at the src of this icon, and highlight that same one in the dialog
		var src = $(this).attr("src");

		//remove the selected class from all and add to this one.
		$(".action_picker_icon").removeClass("action_picker_icon_selected");
		$(".action_picker_icon[src='" + src + "']").addClass("action_picker_icon_selected");

		$("#action_icon_dialog").dialog("open");
	});
	//the task print link
	$("#category_actions .task_print_btn").live("click", function() {
		var url = "taskPrint?task_id=" + $(this).attr("task_id");
		openWindow(url, "taskPrint", "location=no,status=no,scrollbars=yes,resizable=yes,width=800,height=700");
	});
	//the task edit link
	$("#category_actions .task_open_btn").live("click", function() {
		location.href = "taskEdit?task_id=" + $(this).attr("task_id");
	});
	$(".action_param_edit_btn").live("click", function() {
		var action_id = $(this).parents("li").attr('id').replace(/ac_/, "");
		ShowParameterDialog(action_id);
	});

	//this is crazy... dropping a task onto an existing action will CHANGE THE TASK
	//simply by updating the field to the new ID, and firing a change event.
	$(".action").droppable({
		drop : function(event, ui) {
			var task_label = ui.draggable.find(".search_dialog_value_name").html();
			var otid = ui.draggable.attr("original_task_id");
			var action_id = $(this).attr("id").replace(/ac_/, "");

			//update the hidden task field
			$(this).find('[column="original_task_id"]').val(otid);
			//fire the change event
			$(this).find('[column="original_task_id"]').change();
			//reset version
			$(this).find('[column="task_version"]').val("");
			//fire the change event
			$(this).find('[column="task_version"]').change();

			//reget the whole action, as the versions and parameters will be different
			$.ajax({
				async : false,
				type : "POST",
				url : "ecoMethods/wmGetEcotemplateAction",
				data : '{"sActionID":"' + action_id + '"}',
				contentType : "application/json; charset=utf-8",
				dataType : "html",
				success : function(response) {
					//replace our inner content
					$("#ac_" + action_id).html(response);
				},
				error : function(response) {
					showAlert(response.responseText);
				}
			});
		},
		over : function(event, ui) {
			$(this).find(".step_header").addClass("ui-state-highlight")
		},
		out : function(event, ui) {
			$(this).find(".step_header").removeClass("ui-state-highlight")
		}
	});
}