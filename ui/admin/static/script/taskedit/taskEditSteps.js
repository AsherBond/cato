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

var fieldWithFocus = null;

$(document).ready(function() {
	//toggle it when you click on a step
	$("#steps").on("click", ".step_toggle_btn", function() {
		//alert($(this).attr("id").replace(/step_header_/, ""));
		var step_id = $(this).attr("step_id");
		var visible = 0;

		//toggle it
		$("#step_detail_" + step_id).toggleClass("step_collapsed");

		//then check it
		if (!$("#step_detail_" + step_id).hasClass("step_collapsed"))
			visible = 1;

		// swap the child image, this will work as long as the up down image stays the first child if the span
		if (visible === 1) {
			$(this).children(":first-child").removeClass("ui-icon-triangle-1-e");
			$(this).children(":first-child").addClass("ui-icon-triangle-1-s");
		} else {
			$(this).children(":first-child").removeClass("ui-icon-triangle-1-s");
			$(this).children(":first-child").addClass("ui-icon-triangle-1-e");
		}

		//now persist it
		$("#update_success_msg").text("Updating...").show();
		ajaxPostAsync("taskMethods/wmToggleStep", {
			sStepID : step_id,
			sVisible : visible
		}, function(msg) {
			$("#update_success_msg").text("Update Successful").fadeOut(2000);
		}, undefined, "text");
	});

	//toggle all of them
	$("#step_toggle_all_btn").click(function() {
		//if all are closed, open them all, else close them all
		// also change the expand images
		if ($("#steps .step_collapsed").length === $(".step_detail").length) {
			$("#steps .step_detail").removeClass("step_collapsed");

			$(this).removeClass("ui-icon-triangle-1-s");
			$(this).addClass("ui-icon-triangle-1-n");

			$("#steps .expand_image").removeClass("ui-icon-triangle-1-e");
			$("#steps .expand_image").addClass("ui-icon-triangle-1-s");
		} else {
			$("#steps .step_detail").addClass("step_collapsed");
			$("#steps .step_common_detail").addClass("step_common_collapsed");

			$(this).removeClass("ui-icon-triangle-1-n");
			$(this).addClass("ui-icon-triangle-1-s");

			$("#steps .expand_image").removeClass("ui-icon-triangle-1-s");
			$("#steps .expand_image").addClass("ui-icon-triangle-1-e");
		}
	});

	//common details within a step
	//toggle it when you click on one of the buttons
	$("#steps").on("click", ".step_common_button", function() {
		var btn = "";
		var dtl = $(this).attr("id").replace(/btn_/, "");
		var stp = $(this).closest(".step_common").attr("step_id");
		var xpp = $(this).closest(".step_common").attr("xpath_prefix");
		var jsid = $(this).closest(".step_common").attr("jsid");

		//if the one we just clicked on is already showing, hide them all
		if ($("#" + dtl).hasClass("step_common_collapsed")) {
			//hide all
			$("#steps div[id^=step_common_detail_" + jsid + "]").addClass("step_common_collapsed");
			$("#steps span[id^=btn_step_common_detail_" + jsid + "]").removeClass("step_common_button_active");

			//show this one
			$("#" + dtl).removeClass("step_common_collapsed");
			$(this).addClass("step_common_button_active");
			btn = $(this).attr("button");
		} else {
			$("#" + dtl).addClass("step_common_collapsed");
			$(this).removeClass("step_common_button_active");
		}

		//now persist it
		$("#update_success_msg").text("Updating...").show();
		ajaxPostAsync("taskMethods/wmToggleStepCommonSection", {
			sStepID : stp,
			sXPathPrefix : xpp,
			sButton : btn
		}, function(msg) {
			$("#update_success_msg").text("Update Successful").fadeOut(2000);
		}, undefined, "text");
	});

	// Command tab details
	//help button
	$("#command_help_btn").button({
		icons : {
			primary : "ui-icon-help"
		}
	});
	$("#command_help_btn").click(function() {
		showPleaseWait();
		$("#command_help_dialog_detail").load("/cache/_command_help.html", function() {
			$("#command_help_dialog").dialog("open");
			hidePleaseWait();
		});
	});

	//the onclick event of the 'skip' icon of each step
	$("#steps").on("click", ".step_skip_btn", function() {
		//click the hidden field and fire the change event
		var step_id = $(this).attr("step_id");
		var skip = $(this).attr("skip");
		if (skip === "1") {
			skip = 0;
			$(this).attr("skip", "0");

			$(this).removeClass("ui-icon-play").addClass("ui-icon-pause");
			$("#" + step_id).removeClass("step_skip");
			$("#step_header_" + step_id).removeClass("step_header_skip");
			$("#step_detail_" + step_id).removeClass("step_collapsed");
		} else {
			skip = 1;
			$(this).attr("skip", "1");

			$(this).removeClass("ui-icon-pause").addClass("ui-icon-play");
			$("#" + step_id).addClass("step_skip");

			//remove the validation nag
			$("#" + step_id).find(".step_validation_template").remove();

			$("#step_header_" + step_id).addClass("step_header_skip");
			$("#step_detail_" + step_id).addClass("step_collapsed");
		}

		ajaxPostAsync("taskMethods/wmToggleStepSkip", {
			sStepID : step_id,
			sSkip : skip
		}, function(msg) {
			$("#update_success_msg").text("Update Successful").fadeOut(2000);
		}, undefined, "text");
	});

	//the onclick event of the 'delete' link of each step
	$("#steps").on("click", ".step_delete_btn", function() {
		$("#hidStepDelete").val($(this).attr("remove_id"));
		$("#step_delete_confirm_dialog").dialog("open");
	});

	//the onclick event of the 'copy' link of each step
	$("#steps").on("click", ".step_copy_btn", function() {
		$("#update_success_msg").text("Copying...").show();
		var step_id = $(this).attr("step_id");

		ajaxPostAsync("taskMethods/wmCopyStepToClipboard", {
			sStepID : step_id
		}, function(response) {
			doGetClips();
			$("#update_success_msg").text("Copy Successful").fadeOut(2000);
		}, undefined, "text");
	});

	//the onclick event of the 'remove' link of embedded steps
	$("#steps").on("click", ".embedded_step_delete_btn", function() {
		$("#embedded_step_remove_xpath").val($(this).attr("remove_xpath"));
		$("#embedded_step_parent_id").val($(this).attr("parent_id"));
		$("#embedded_step_delete_confirm_dialog").dialog("open");
		//alert('remove step ' + $(this).attr("remove_id") + ' from ' + $(this).attr("parent_id"));
	});

	//the onclick event of 'connection picker' buttons on selected fields
	$("#steps").on("click", ".conn_picker_btn", function(e) {
		//hide any open pickers
		$("div[id$='_picker']").hide();
		var field = $("#" + $(this).attr("link_to"));

		//first, populate the picker
		var response = ajaxPost("taskMethods/wmGetTaskConnections", {
			sTaskID : g_task_id
		}, "html");
		if (response) {
			$("#conn_picker_connections").html(response);
			$("#conn_picker_connections .value_picker_value").hover(function() {
				$(this).toggleClass("value_picker_value_hover");
			}, function() {
				$(this).toggleClass("value_picker_value_hover");
			});
			$("#conn_picker_connections .value_picker_value").click(function() {
				field.val($(this).text());
				field.change();

				$("#conn_picker").slideUp();
			});
		}

		//change the click event of this button to now close the dialog
		//        $(this).die("click");
		//        $(this).click(function() { $("#conn_picker").slideUp(); });

		$("#conn_picker").css({
			top : e.clientY,
			left : e.clientX
		});
		$("#conn_picker").slideDown();
	});

	$(document).on("click", "#conn_picker_close_btn", function(e) {
		//hide any open pickers
		$("div[id$='_picker']").hide();
	});
	$(document).on("click", "#var_picker_close_btn", function(e) {
		//hide any open pickers
		$("div[id$='_picker']").hide();
	});

	//// CODEBLOCK PICKER
	//the onclick event of 'codeblock picker' buttons on selected fields
	$(document).on("click", ".codeblock_picker_btn", function(e) {
		//hide any open pickers
		$("div[id$='_picker']").hide();
		field = $("#" + $(this).attr("link_to"));
		stepid = $(this).attr("step_id");

		//first, populate the picker

		var response = ajaxPost("taskMethods/wmGetTaskCodeblockPicker", {
			sTaskID : g_task_id,
			sStepID : stepid
		}, "html");
		if (response) {
			$("#codeblock_picker_codeblocks").html(response);
			$("#codeblock_picker_codeblocks .value_picker_value").hover(function() {
				$(this).toggleClass("value_picker_value_hover");
			}, function() {
				$(this).toggleClass("value_picker_value_hover");
			});
			$("#codeblock_picker_codeblocks .value_picker_value").click(function() {
				field.val($(this).text());
				field.change();

				$("#codeblock_picker").slideUp();
			});
		}

		$("#codeblock_picker").css({
			top : e.clientY,
			left : e.clientX
		});
		$("#codeblock_picker").slideDown();
	});
	$(document).on("click", "#codeblock_picker_close_btn", function(e) {
		//hide any open pickers
		$("[id$='_picker']").hide();
	});

	//////TASK PICKER
	//the onclick event of the 'task picker' buttons everywhere
	$("#steps").on("click", ".task_picker_btn", function() {
		$("#task_picker_target_field_id").val($(this).attr("target_field_id"));
		//alert($(this).attr("target_field_id") + "\n" + $(this).prev().prev().val());
		$("#task_picker_step_id").val($(this).attr("step_id"));
		$("#task_picker_dialog").dialog("open");
	});

	// when you hit enter inside 'task picker' for a subtask
	$("#task_search_text").keypress(function(e) {
		//alert('keypress');
		if (e.which === 13) {
			$("#task_search_btn").click();
			return false;
		}
	});

	//the onclick event of the 'task picker' search button
	$("#task_search_btn").click(function() {
		var field = $("#" + $("#task_picker_target_field_id").val());

		var search_text = $("#task_search_text").val();

		var response = ajaxPostAsync("taskMethods/wmTaskSearch", {
			sSearch : search_text
		}, function(response) {
			$("#task_picker_results").html(response);
			//bind the onclick event for the new results
			$("#task_picker_results .task_picker_value").disableSelection();

			//gotta kill previously bound clicks or it will stack 'em! = bad.
			$("#task_picker_results li[tag='task_picker_row']").click(function() {
				$("#task_steps").block({
					message : null
				});

				$("#task_picker_dialog").dialog("close");
				$("#task_picker_results").empty();

				field.val($(this).attr("task_name"));
				field.change();
			});

			//task description tooltips on the task picker dialog
			$("#task_picker_results .search_dialog_tooltip").tipTip({
				defaultPosition : "right",
				keepAlive : false,
				activation : "hover",
				maxWidth : "500px",
				fadeIn : 100
			});
		}, undefined, "html");
	});
	//////END TASK PICKER

	//////DIALOGS
	//init the step delete confirm dialog
	$("#step_delete_confirm_dialog").dialog({
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
				doStepDelete();
				$(this).dialog("close");
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});

	//init the embedded step delete confirm dialog
	$("#embedded_step_delete_confirm_dialog").dialog({
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
				var remove_path = $("#embedded_step_remove_xpath").val();
				var step_id = $("#embedded_step_parent_id").val();

				doRemoveNode(step_id, remove_path);
				$(this).dialog("close");
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});

	//init the task picker dialog
	$("#task_picker_dialog").dialog({
		autoOpen : false,
		draggable : false,
		resizable : false,
		bgiframe : true,
		modal : true,
		height : 600,
		width : 600,
		overlay : {
			backgroundColor : '#000',
			opacity : 0.5
		},
		close : function(event, ui) {
			$("#task_search_text").val("");
			$("#task_picker_results").empty();
		}
	});
	//////END DIALOGS

	// NODE ADD
	// This single binding handles all the places where a new content node is added to a step.
	$("#steps").on("click", ".fn_node_add_btn", function() {

		// these fully dynamic commands read the section they are gonna add from the original template xml
		// so, it needs the function name and a template xpath in order to be able to look that up.

		var step_id = $(this).attr("step_id");
		var func_name = $(this).attr("function_name");
		var template_path = $(this).attr("template_path");
		var add_to = $(this).attr("add_to_node");

		$("#task_steps").block({
			message : null
		});
		$("#update_success_msg").text("Updating...").show();

		ajaxPostAsync("taskMethods/wmFnNodeArrayAdd", {
			sStepID : step_id,
			sFunctionName : func_name,
			sTemplateXPath : template_path,
			sAddTo : add_to
		}, function(response) {
			//go get the step
			getStep(step_id, step_id, true);
			$("#task_steps").unblock();
			$("#update_success_msg").text("Update Successful").fadeOut(2000);

		});
	});

	// NODE DELETE
	// this single binding hook up every command node deletion function
	$("#steps").on("click", ".fn_node_remove_btn", function() {
		if (confirm("Are you sure?")) {
			var step_id = $(this).attr("step_id");
			var remove_path = $(this).attr("remove_path");

			doRemoveNode(step_id, remove_path);
		}
	});
});

// This single function can remove any dynamically generated section from any command.
// It simply removes a node from the document.
function doRemoveNode(step_id, remove_path) {
	$("#task_steps").block({
		message : null
	});
	$("#update_success_msg").text("Updating...").show();

	var response = ajaxPostAsync("taskMethods/wmRemoveNodeFromStep", {
		sStepID : step_id,
		sRemovePath : remove_path
	}, function(response) {
		getStep(step_id, step_id, true);
		$("#task_steps").unblock();
		$("#update_success_msg").text("Update Successful").fadeOut(2000);
	}, undefined, "text");

}

//called in rare cases when the value entered in one field should push it's update through another field.
//(when the "wired" field is hidden, and the data entry field is visible but not wired.)
function pushStepFieldChangeVia(pushing_ctl, push_via_id) {
	//what's the value in the control doing the pushing?
	var field_value = $(pushing_ctl).val();

	//shove that value in the push_via field
	$("#" + push_via_id).val(field_value);

	//and force the change event?
	$("#" + push_via_id).change();
}

//fires when each individual field on the page is changed.
function onStepFieldChange(ctl, step_id, xpath) {
	$("#update_success_msg").text("Updating...").show();

	//    var step_id = $(ctl).attr("step_id");
	var field_value = $(ctl).val();
	var func = ctl.getAttribute("function");
	var stepupdatefield = "update_" + func + "_" + step_id;
	var reget = ctl.getAttribute("reget_on_change");

	//for checkboxes and radio buttons, we gotta do a little bit more, as the pure 'val()' isn't exactly right.
	var typ = ctl.type;
	if (typ === "checkbox") {
		field_value = (ctl.checked === true ? 1 : 0);
	}
	if (typ === "radio") {
		field_value = (ctl.checked === true ? 1 : 0);
	}

	//simple whack-and-add
	//Why did we use a textarea?  Because the actual 'value' may be complex
	//(sql, code, etc) with lots of chars needing escape sequences.
	//So, stick the complex value in an element that doesn't need any special handling.

	//10/7/2011 NSC - using append including the value was modifying the value if jQuery thought
	//it might be a DOM object.
	//so, we FIRST create the new textarea in the step_update_array
	$("#" + stepupdatefield).remove();
	$("#step_update_array").append("<textarea id='" + stepupdatefield + "' step_id='" + step_id + "' function='" + func + "' xpath='" + xpath + "'></textarea>");
	//... THEN set the value of the new element.
	$("#" + stepupdatefield).val(field_value);

	doStepDetailUpdate(stepupdatefield, step_id, func, xpath);

	//if reget is true, go to the db and refresh the whole step
	if (reget === "true") {
		$("#task_steps").block({
			message : null
		});
		getStep(step_id, step_id, true);
		$("#task_steps").unblock();
	} else {
		//if we're not regetting, we need to handle visualization of validation
		validateStep(step_id);
	}

	$("#update_success_msg").fadeOut(2000);

}

function initSortable() {
	//this is more than just initializing the sortable... it's some other stuff that needs to be set up
	//after adding to the sortable.
	//define the variable picker context menu

	//enable right click on all edit fields
	$("#steps :input[te_group='step_fields']").rightClick(function(e) {
		showVarPicker(e);
	});

	//what happens when a step field gets focus?
	//we show the help for that field in the help pane.
	//and set a global variable with it's id
	$("#steps :input[te_group='step_fields']").unbind("focus");
	$("#steps :input[te_group='step_fields']").focus(function() {
		$("#te_help_box_detail").html($(this).attr("help"));
		fieldWithFocus = $(this).attr("id");
	});

	//some steps may have 'required' fields that are not populated
	//set up a visualization
	//validateStep();

	//set up the sortable
	if ($("#steps").hasClass("ui-sortable")) {
		$("#steps").sortable("destroy");
	}
	$("#steps").sortable({
		handle : $(".step_header"),
		distance : 20,
		placeholder : 'ui-widget-content ui-corner-all ui-state-active step_drop_placeholder',
		items : 'li:not(#no_step)',
		update : function(event, ui) {
			//if this is a new step... add
			//(add will reorder internally)
			var new_step = $(ui.item[0]);
			var new_step_id = new_step.attr("name");
			if (new_step_id.indexOf("fn_") === 0 || new_step_id.indexOf("clip_") === 0 || new_step_id.indexOf("cb_") === 0) {
				doStepAdd(new_step);
			} else {
				//else just reorder what's here.
				doStepReorder();
			}
		}
	});

	//this turns on the "combobox" controls on steps.
	$(function() {
		$("#steps select.combo").ufd({
			submitFreeText : true,
			css : {
				input : "ui-widget-content code",
				li : "code",
				listWrapper : "list-wrapper code"
			}
		});

		//NOTE: we are using the ufd plugin, but in this case we need more.
		//This copies all the attributes from the source 'select' onto the new 'input' it created.
		$("#steps select.combo").each(function(i, cbo) {
			var id = $(cbo).attr("id");
			$(cbo.attributes).each(function(i, attrib) {
				var name = attrib.name;
				if (name !== "type" && name !== "id" && name !== "class" && name !== "name") {
					var value = attrib.value;
					$("#ufd-" + id).attr(name, value);
				}
			});
		});
	});
}

function showVarPicker(e) {
	//hide any open pickers
	$("div[id$='_picker']").hide();

	var response = ajaxPost("taskMethods/wmGetTaskVarPickerPopup", {
		sTaskID : g_task_id
	}, "html");
	if (response) {
		$("#var_picker_variables").html(response);

		$("#var_picker_variables .value_picker_group").click(function() {
			$("#" + $(this).attr("target")).toggleClass("hidden");
		});

		$("#var_picker_variables .value_picker_value").hover(function() {
			$(this).toggleClass("value_picker_value_hover");
		}, function() {
			$(this).toggleClass("value_picker_value_hover");
		});

		$("#var_picker_variables .value_picker_group").hover(function() {
			$(this).toggleClass("value_picker_value_hover");
		}, function() {
			$(this).toggleClass("value_picker_value_hover");
		});

		$("#var_picker_variables .value_picker_value").click(function() {
			var fjqo = $("#" + fieldWithFocus);
			var f = $("#" + fieldWithFocus)[0];
			var varname = "";

			//note: certain fields should get variable REPLACEMENT syntax [[foo]]
			//others should get the actual name of the variable
			//switch on the function_name to determine this
			var func = fjqo.attr("function");
            var xpath = fjqo.attr("xpath");
			switch (func) {
				case "clear_variable":
					varname = $(this).text();
					break;
				case "substring":
					// bugzilla 1234 in substring only the variable_name field gets the value without the [[ ]]
					if (xpath === "variable_name") {
						varname = $(this).text();
					} else {
						varname = "[[" + $(this).text() + "]]";
					}
					break;
				case "loop":
					// bugzilla 1234 in substring only the variable_name field gets the value without the [[ ]]
					if (xpath === "counter") {
						varname = $(this).text();
					} else {
						varname = "[[" + $(this).text() + "]]";
					}
					break;
				case "set_variable":
					// bugzilla 1234 in substring only the variable_name field gets the value without the [[ ]]
					if (xpath.indexOf("/name", 0) !== -1) {
						varname = $(this).text();
					} else {
						varname = "[[" + $(this).text() + "]]";
					}
					break;
				default:
					varname = "[[" + $(this).text() + "]]";
					break;
			}

			//IE support
			if (document.selection) {
				f.focus();
				sel = document.selection.createRange();
				sel.text = varname;
				f.focus();
			}
			//MOZILLA / NETSCAPE support
			else if (f.selectionStart || f.selectionStart === '0') {
				var startPos = f.selectionStart;
				var endPos = f.selectionEnd;
				var scrollTop = f.scrollTop;
				f.value = f.value.substring(0, startPos) + varname + f.value.substring(endPos, f.value.length);
				f.focus();
				f.selectionStart = startPos + varname.length;
				f.selectionEnd = startPos + varname.length;
				f.scrollTop = scrollTop;
			} else {
				f.value = varname;
				f.focus();
			}

			fjqo.change();
			$("#var_picker").slideUp();
		});
	}

	$("#var_picker").css({
		top : e.clientY,
		left : e.clientX
	});
	$("#var_picker").slideDown();
}

function doStepDelete() {
	//if there are any active drop zones on the page, deactivate them first...
	//otherwise the sortable may get messed up.
	$(".step_nested_drop_target_active").each(function(intIndex) {
		doDropZoneDisable($(this).attr("id"));
	});

	var step_id = $("#hidStepDelete").val();
	//don't need to block, the dialog blocks.
	$("#update_success_msg").text("Updating...").show();
	var response = ajaxPost("taskMethods/wmDeleteStep", {
		sStepID : step_id
	});
	if (response) {
		//pull the step off the page
		$("#" + step_id).remove();

		if ($("#steps .step").length === 0) {
			$("#no_step").removeClass("hidden");
		} else {
			//reorder the remaining steps
			//BUT ONLY IN THE BROWSER... the ajax post we just did took care or renumbering in the db.
			$("#steps .step_order_label").each(function(intIndex) {
				$(this).html(intIndex + 1);
				//+1 because we are a 1 based array on the page
			});
		}

		$("#update_success_msg").text("Update Successful").fadeOut(2000);
	}

	$("#hidStepDelete").val("");
}

function doStepAdd(new_step) {
	//ok this works, but we need to know if it's a new item before we override the html
	var task_id = g_task_id;
	var codeblock_name = $("#hidCodeblockName").val();
	var item = new_step.attr("name");

	//it's a new drop!
	//do the add and get the HTML
	$("#task_steps").block({
		message : null
	});
	$("#update_success_msg").text("Adding...").show();

	var response = ajaxPost("taskMethods/wmAddStep", {
		sTaskID : task_id,
		sCodeblockName : codeblock_name,
		sItem : item
	});
	if (response) {
		if (response.step_id) {
			new_step_id = response.step_id;

			$("#no_step").addClass("hidden");

			new_step.replaceWith(unpackJSON(response.step_html));

			//then reorder the other steps
			doStepReorder();

			//note we're not 'unblocking' the ui here... that will happen in stepReorder

			//NOTE NOTE NOTE: this is temporary
			//until I fix the copy command ... we will delete the clipboard item after pasting
			//this is not permanent, but allows it to be checked in now

			// 4-26-12 NSC: since embedded commands work differently, we no longer need to remove a
			// clipboard step when it's used
			// if (item.indexOf('clip_') !== -1)
			//    doClearClipboard(item.replace(/clip_/, ""))

			//but we will change the sortable if this command has embedded commands.
			//you have to add the embedded command NOW, or click cancel.
			if (item === "fn_if" || item === "fn_loop" || item === "fn_exists" || item === "fn_while") {
				doDropZoneEnable($("#" + new_step_id + " .step_nested_drop_target"));
			} else {
				initSortable();
				validateStep(new_step_id);
			}
		}
	}
}

function doStepReorder() {
	//get the steps from the step list
	var steparray = $('#steps').sortable('toArray');

	$("#task_steps").block({
		message : null
	});
	$("#update_success_msg").text("Updating...").show();

	var response = ajaxPost("taskMethods/wmReorderSteps", {
		sSteps : steparray
	});
	if (response) {
		//renumber the step widget labels
		$("#steps .step_order_label").each(function(intIndex) {
			$(this).html(intIndex + 1);
			//+1 because we are a 1 based array on the page
		});

		$("#task_steps").unblock();
		$("#update_success_msg").text("Update Successful").fadeOut(2000);
	}
}

function doStepDetailUpdate(field, step_id, func, xpath) {
	if ($("#step_update_array").length > 0) {
		//get the value ready to be shipped via json
		//since some steps can have complex script or other sql, there
		//are special characters that need to be escaped for the JSON data.
		//on the web service we are using the actual javascript unescape to unpack this.
		var val = packJSON($("#" + field).val());

		var response = ajaxPost("taskMethods/wmUpdateStep", {
			sStepID : step_id,
			sFunction : func,
			sXPath : xpath,
			sValue : val
		});
		if (response) {
			$("#task_steps").unblock();
			$("#update_success_msg").text("Update Successful").fadeOut(2000);
		}

		//clear out the div of the stuff we just updated!
		$("#step_update_array").empty();
	}
}

//tried this... no marked effect on performance

//function OnFieldUpdateSuccess(result, userContext, methodName) {
//    //renumber the step widget labels
//    $("#steps .step_order_label").each(
//                function(intIndex) {
//                    $(this).html(intIndex + 1); //+1 because we are a 1 based array on the page
//                }
//            );

//    $("#task_steps").unblock();
//    $("#update_success_msg").text("Update Successful").fadeOut(2000);
//}

//// Callback function invoked on failure of the MS AJAX page method.
//function OnFieldUpdateFailure(error, userContext, methodName) {
//    $("#update_success_msg").fadeOut(2000);

//    if (error !== null) {
//        showAlert(error.get_message());
//    }
//}

function validateStep(in_element_id) {
	var container;

	//if we didn't get a specific step_id, run the test on ALL STEPS!
	if (in_element_id)
		container = "#" + in_element_id + ":not(.step_skip)";
	//no space before :not
	else
		container = "#steps li:not(.step_skip)";

	// spin and check each input
	$(container + " :input").each(function(intIndex) {
		var step_id = $(this).attr("step_id");
		var msg = "";
		$(this).next(".fielderror").remove();
		$(this).removeClass("is_required");

		// value constraints
		msgs = checkFieldConstraints($(this));
		if (msgs) {
			msg += msgs.join("\n");
		}

		if ($(this).val() === "") {
			if ($(this).attr("is_required")) {
				if ($(this).attr("is_required") === "true") {
					$(this).addClass("is_required");
					// don't think we need a mesage just for a required field... it's obvious
					//msg += "Value is required.\n";
				}
			}
		}

		//check syntax (just a few fields have this
		if ($(this).val() !== "") {
			if ($(this).attr("syntax")) {
				var syntax = $(this).attr("syntax");
				if (syntax !== "") {
					var field_value = $(this).val();
					var syntax_error = checkSyntax(syntax, field_value);

					if (syntax_error !== "") {
						$(this).addClass("is_required");
						msg += syntax_error;
					}
				}
			}
		}

		if (msg) {
			$(this).after("<span class=\"fielderror ui-icon ui-icon-alert forceinline pointer\" title=\"" + msg + "\">");
			$(this).addClass("is_required");
		}

	});
}
