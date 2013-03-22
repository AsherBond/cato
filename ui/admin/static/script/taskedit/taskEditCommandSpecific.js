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

/*
There are some script that applies to instances of Steps on a Task.

Here is all the code relevant to Steps and their dynamic nature.
*/

//This link can appears anywhere it is needed.
//it clears a field and enables it for data entry.
$(document).ready(function() {
	$(".fn_field_clear_btn").live("click", function() {
		var field_id_to_clear = $(this).attr("clear_id");

		//clear it
		$("#" + field_id_to_clear).val("");

		//in case it's disabled, enable it
		$("#" + field_id_to_clear).removeAttr('disabled');

		//push an change event to it.
		$("#" + field_id_to_clear).change();
	});

	//the parameter edit dialog button for Run Task command
	$(".fn_runtask_edit_parameters_btn").live("click", function() {
		//trying globals!!!  Maybe we'll do this using AmplifyJS one day.
		rt_task_id = $(this).attr("task_id");
		rt_step_id = $(this).attr("step_id");
		rt_base_xpath = $(this).attr("base_xpath");

		ShowRunTaskParameterEdit();
	});

	//init dialogs
	$("#fn_runtask_parameter_dialog").dialog({
		autoOpen : false,
		modal : true,
		height : 650,
		width : 500,
		open : function(event, ui) {
			$(".ui-dialog-titlebar-close", ui).hide();
		},
		buttons : {
			"Save" : function() {
				SaveRunTaskParameters();
				CloseRunTaskParameterEdit();
			},
			"Cancel" : function() {
				CloseRunTaskParameterEdit();
			}
		}
	});

	//the SUBTASK command
	//this will get the parameters in read only format for each subtask command.
	$("#steps .subtask_view_parameters_btn").live("click", function() {
		var task_id = $(this).attr("id").replace(/stvp_/, "");
		var target = $(this).parent().find(".subtask_view_parameters");

		var args = {};
		args.sType = "task";
		args.sID = $(this).attr("id").replace(/stvp_/, "");
		args.bEditable = false;
		args.bSnipValues = true;

		var response = ajaxPost("taskMethods/wmGetParameters", args);
		if (response) {
			target.html(response);

			//have to rebind the tooltips here
			bindParameterToolTips();
		}
	});
	//end SUBTASK command

	//the CODEBLOCK command
	//the onclick event of the 'codeblock' elements
	$("#steps .codeblock_goto_btn").live("click", function() {
		cb = $(this).attr("codeblock");
		$("#hidCodeblockName").val(cb);
		doGetSteps();
	});
	//end CODEBLOCK command

	//the SUBTASK and RUN TASK commands
	//the view link
	$("#steps .task_print_btn").live("click", function() {
		var url = "taskPrint?task_id=" + $(this).attr("task_id");
		openWindow(url, "taskPrint", "location=no,status=no,scrollbars=yes,resizable=yes,width=800,height=700");
	});
	//the edit link
	$("#steps .task_open_btn").live("click", function() {
		location.href = "taskEdit?task_id=" + $(this).attr("task_id");
	});
	// end SUBTASK and RUN TASK commands

	//the IF command has a special add mechanism all to itself.
	$("#steps .fn_if_add_btn").live("click", function() {
		var step_id = $(this).attr("step_id");
		var idx = $(this).attr("next_index");
		var add_to = $(this).attr("add_to_node");

		doAddIfSection(step_id, add_to, idx);
	});

	$("#steps .fn_if_addelse_btn").live("click", function() {
		var step_id = $(this).attr("step_id");
		var add_to = $(this).attr("add_to_node");

		doAddIfSection(step_id, add_to, -1);
	});
	$("#steps .compare_templates").live("change", function() {
		// add whatever was selected into the textarea
		var textarea_id = $(this).attr("textarea_id");
		var tVal = $("#" + textarea_id).val();
		$("#" + textarea_id).val(tVal + this.value);

		// clear the selection
		this.selectedIndex = 0;
	});
	//end IF command

	//Key/Value pairs can appear on lots of different command types
	//and on each type there is a specific list of relevant lookup values
	//So, switch on the function and popup a picker
	$("#steps .key_picker_btn").live("click", function(e) {
		//hide any open pickers
		$("div[id$='_picker']").hide();
		var field = $("#" + $(this).attr("link_to"));
		var func = $(this).attr("function");

		var item_html = "N/A";

		//first, populate the picker
		//(in a minute build this based on the 'function' attr of the picker icon
		switch (func) {
			case "http":
				break;
			case "run_task":
				break;
		}

		$("#key_picker_keys").html(item_html);

		//set the hover effect
		$("#key_picker_keys .value_picker_value").hover(function() {
			$(this).toggleClass("value_picker_value_hover");
		}, function() {
			$(this).toggleClass("value_picker_value_hover");
		});

		//click event
		$("#key_picker_keys .value_picker_value").click(function() {
			field.val($(this).text());
			field.change();

			$("#key_picker").slideUp();
		});

		$("#key_picker").css({
			top : e.clientY,
			left : e.clientX
		});
		$("#key_picker").slideDown();
	});
	$("#key_picker_close_btn").live("click", function(e) {
		//hide any open pickers
		$("div[id$='_picker']").hide();
	});

});

function doAddIfSection(step_id, add_to, idx) {
	$("#task_steps").block({
		message : null
	});
	$("#update_success_msg").text("Updating...").show();

	var args = {};
	args.sStepID = step_id;
	args.sAddTo = add_to;
	args.iIndex = idx;

	var response = ajaxPost("taskMethods/wmFnIfAddSection", args);
	if (response) {
		//go get the step
		getStep(step_id, step_id, true);
		$("#task_steps").unblock();
		$("#update_success_msg").text("Update Successful").fadeOut(2000);

		//hardcoded index for the last "else" section
		if (idx == -1)
			doDropZoneEnable($("#if_" + step_id + "_else .step_nested_drop_target"));
		else
			doDropZoneEnable($("#if_" + step_id + "_else_" + idx + " .step_nested_drop_target"));
	}
}

//FUNCTIONS for dealing with the very specific parameters for a Run Task command
function ShowRunTaskParameterEdit() {
	var task_parameter_xml = "";

	if (rt_task_id != "") {
		args = {};
		args.sXPath = rt_base_xpath;
		args.sType = "runtask";
		args.sID = rt_step_id;
		args.sFilterID = rt_task_id;

		task_parameter_xml = ajaxPost("taskMethods/wmGetParameterXML", args, "xml");

		var output = DrawParameterEditForm(task_parameter_xml);
		$("#fn_runtask_parameter_dialog_params").html(output);

		//don't forget to bind the tooltips!
		bindParameterToolTips();

		//and for this case we bind the right click event of the value fields
		//so... for the new parameters feature on the Run Task command... bind the right click for the runtime var picker too
		//enable right click on all edit fields
		$("#fn_runtask_parameter_dialog .task_launch_parameter_value_input").rightClick(function(e) {
			showVarPicker(e);
		});
		//this focus hack is required too
		$("#fn_runtask_parameter_dialog .task_launch_parameter_value_input").focus(function() {
			fieldWithFocus = $(this).attr("id");
		});

		$("#fn_runtask_parameter_dialog").dialog("open");
	} else {
		showInfo("Unable to resolve the ID of the Task referenced by this command.");
	}
}

function CloseRunTaskParameterEdit() {
	$("#fn_runtask_parameter_dialog").dialog("close");
}

function SaveRunTaskParameters() {
	$("#update_success_msg").text("Saving Defaults...");

	var args = {};
	args.sType = "runtask";
	args.sID = rt_step_id;
	args.sTaskID = rt_task_id;
	args.sBaseXPath = rt_base_xpath;
	args.sXML = packJSON(buildXMLToSubmit());

	var response = ajaxPost("taskMethods/wmSaveDefaultParameterXML", args);
	if (response) {
		$("#update_success_msg").text("Save Successful").fadeOut(2000);
		CloseRunTaskParameterEdit();
	}

	$("#action_parameter_dialog").dialog("close");

}

//End Run Task Parameters
