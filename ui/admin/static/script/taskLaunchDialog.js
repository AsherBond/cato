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

//Shared functionality for the task launch dialog

$(document).ready(function() {
	//any page that includes this script will get the following dialog inner code
	//but the page requires a placeholder div... called "task_launch_dialog"
	var d = '<div id="task_launch_dialog_task_name" class="floatleft"></div><div class="floatright">Server Time: <span class="current_time"></span></div><hr /> \
		Cloud Account: <span id="task_launch_dialog_account_name"></span> \
		&nbsp;&nbsp;Logging Level:&nbsp;&nbsp; \
		<select id="task_launch_dialog_debug_level"> \
		   <option value="0">None</option> \
		   <option value="1">Minimal</option> \
		   <option value="2" selected="selected">Normal</option> \
		   <option value="3">Enhanced</option> \
		   <option value="4">Verbose</option> \
		</select> \
		<hr /> \
		<div id="task_launch_dialog_parameters" class="floatleft task_launch_column ui-widget-content ui-tabs ui-corner-all"> \
		   <div id="task_launch_params_content"> \
		       <div class="task_launch_params_title ui-widget-header ui-corner-all"> \
		       Parameters \
		       </div> \
		       <input type="radio" id="rbDefault" name="radio" /><label for="rbDefault">&nbsp;Task Defaults</label> \
		       &nbsp;&nbsp;<input type="radio" id="rbPrevious" name="radio" /><label for="rbPrevious">&nbsp;Previous Values</label> \
		       <div id="task_launch_dialog_params"></div> \
		   </div> \
		</div> \
		<div id="task_launch_dialog_schedule" class="floatright task_launch_column"> \
		   <ul> \
		       <li><a href="#RunNowTab"><span>Run Now</span></a></li> \
		       <li><a href="#RunLaterTab"><span>Run Later</span></a></li> \
		       <li><a href="#RunRepeatedlyTab"><span>Run Repeatedly</span></a></li> \
		       <li><a href="#PlanTab"><span>Plan</span></a></li> \
		   </ul> \
		   <div id="RunNowTab"> \
		       <div>Will be started immediately and run only once, using the Parameters selected on the left.</div> \
		       <hr /> \
		       <label for="new_runlog_window" class="hidden new_runlog_window">New Window?</label><input type="checkbox" id="new_runlog_window" class="hidden new_runlog_window"/> \
		       <span id="run_now_btn" class="floatright">Run Now</span> \
		   </div> \
		   <div id="RunLaterTab"> \
		       <div>Will be started in the future, and run only once, using the Parameters selected on the left.</div> \
		       <hr /> \
		       Run On: <input type="text" id="run_on_date" class="datetimepicker" /> \
		       <hr /> \
		       <span id="run_later_btn" class="floatright">Plan</span> \
		   </div> \
		   <div id="RunRepeatedlyTab"> \
		       <div id="run_repeatedly_content"> \
		           <div>Will be scheduled to run on a repeating basis, using the criteria selected below, and the Parameters selected on the left.</div> \
		           <hr />' + drawRecurringPanel() + '           <hr /> \
		       </div> \
		      <span id="run_repeatedly_btn" class="floatright">Schedule</span> \
		   </div> \
		   <div id="PlanTab"> \
		       <div>Actions will occur according to the Plans listed below.</div> \
		       <p>Use one of the "Run" tabs to create a new plan.</p> \
		       <p>Click a Plan to edit the Parameters or recurrence details.</p> \
		       <hr /> \
		       Upcoming Plans \
		       <div id="task_launch_dialog_plans"></div> \
		       <hr /> \
		       Recurring Plans \
		       <div id="task_launch_dialog_schedules"></div> \
		   </div> \
		</div> \
		<input type="hidden" id="task_launch_dialog_task_id" /> \
		<input type="hidden" id="task_launch_dialog_account_id" /> \
		<input type="hidden" id="task_launch_dialog_asset_id" /> \
		<input type="hidden" id="task_launch_dialog_task_instance" /> \
		<input type="hidden" id="plan_edit_plan_id" />';

	$("#task_launch_dialog").prepend(d);

	var plan_edit_content = ' \
		Editing <span id="plan_edit_mode"></span>: <span id="plan_edit_name"></span> \
		<hr /> \
		<div id="plan_edit_parameters" class="floatleft task_launch_column ui-widget-content ui-tabs ui-corner-all"> \
		</div> \
		<div id="plan_edit_schedule" class="floatright task_launch_column"> \
		</div>';
	$("#plan_edit_dialog").html(plan_edit_content);

	//dialog was drawn dynamically, have to do some bindings
	$("#task_launch_dialog_schedule").tabs();
	$(".datetimepicker").datetimepicker();
	$("#run_now_btn").button({
		icons : {
			primary : "ui-icon-play"
		}
	});
	$("#run_now_btn").live("click", function() {
		if (checkRequiredParams() == true && checkParamConstraints() == true)
			RunNow();
	});
	$("#run_later_btn").button({
		icons : {
			primary : "ui-icon-seek-next"
		}
	});
	$("#run_later_btn").live("click", function() {
		if (checkRequiredParams() == true && checkParamConstraints() == true)
			RunLater();
	});
	$("#run_repeatedly_btn").button({
		icons : {
			primary : "ui-icon-calculator"
		}
	});
	$("#run_repeatedly_btn").live("click", function() {
		if (checkRequiredParams() == true && checkParamConstraints() == true)
			RunRepeatedly();
	});

	//init the dialogs
	$("#task_launch_dialog").dialog({
		autoOpen : false,
		modal : true,
		height : 650,
		width : 900,
		open : function(event, ui) {
			$(".ui-dialog-titlebar-close", ui).hide();
		},
		buttons : {
			"Close" : function() {
				CloseTaskLaunchDialog();
			}
		}
	});
	$("#plan_edit_dialog").dialog({
		autoOpen : false,
		modal : true,
		height : 650,
		width : 900,
		open : function(event, ui) {
			$(".ui-dialog-titlebar-close", ui).hide();
		},
		buttons : {
			"Save" : function() {
				var mode = $("#plan_edit_mode").html();

				if (mode == "Plan")
					x = SavePlan();
				//only saves params (may eventually prompt to update the timetable?)

				if (mode == "Schedule")
					x = SaveRecurringPlan();
				//does timetable and params

				if (x)
					ClosePlanEditDialog();
			},
			"Cancel" : function() {
				ClosePlanEditDialog();
			}
		}
	});

	//changing the radio button on the dialog
	$("#rbDefault").live("click", function() {
		var task_id = $("#task_launch_dialog_task_id").val();
		$("#task_launch_dialog_params").fadeOut(500, function() {
			getParamXML(task_id, "task");
		});
		$("#task_launch_dialog_params").fadeIn(500);
	});
	$("#rbPrevious").live("click", function() {
		//see if there is an instance first, if not use the task_id
		var id = $("#task_launch_dialog_task_instance").val();
		if (id == "")
			id = $("#task_launch_dialog_task_id").val();
		$("#task_launch_dialog_params").fadeOut(500, function() {
			getParamXML(id, "instance");
		});
		$("#task_launch_dialog_params").fadeIn(500);
	});

	//click on an action plan
	$("#task_launch_dialog_plans .action_plan_name").live("click", function() {
		ShowPlanEditDialog(this);
	});
	//remove an action plan
	$(".action_plan_remove_btn").live("click", function() {
		deleteActionPlan(this);
	});

	//click on a schedule
	$("#task_launch_dialog_schedules .schedule_name").live("click", function() {
		ShowPlanEditDialog(this);
	});
	//remove a schedule
	$(".schedule_remove_btn").live("click", function() {
		deleteSchedule(this);
	});

	//-------------------------------------------------
	//THIS FOLLOWING SECTION IS ALL FOR HANDLING THE RECURRING PLAN PICKERS
	//-------------------------------------------------

	//what happens when you click on any picker?
	$(".plan_datepoint").live("click", function() {
		$(this).toggleClass("plan_datepoint_active");
	});

	// Months
	$("#liMonthsAll").click(function() {
		// if this is being set active
		$("#olMonths li").removeClass("plan_datepoint_active");
		if ($(this).hasClass("plan_datepoint_active")) {
			$("#olMonths li").addClass("plan_datepoint_active");
		}
	});
	$("#olMonths li").click(function() {
		$("#liMonthsAll").removeClass("plan_datepoint_active");
	});

	// days
	// any click on a date turns off All and turns on Dates
	$("#olDates li").click(function() {
		if (!$("#liDates").hasClass("plan_datepoint_active")) {
			$("#liDates").addClass("plan_datepoint_active");
		}
		$("#liDaysWeek").removeClass("plan_datepoint_active");
		$("#liDaysAll").removeClass("plan_datepoint_active");
	});
	$("#liDaysAll").click(function() {
		$("#liDaysWeek").removeClass("plan_datepoint_active");
		$("#liDates").removeClass("plan_datepoint_active");
		$("#olWeek").hide()
		$("#olWeek li").removeClass("plan_datepoint_active");
		$("#olDates li").removeClass("plan_datepoint_active");

		$("#olDates").show();
	});

	$("#liDaysWeek").click(function() {
		$("#liDaysAll").removeClass("plan_datepoint_active");
		$("#liDates").removeClass("plan_datepoint_active");
		$("#olWeek li").removeClass("plan_datepoint_active");
		$("#olWeek").show();
		$("#olDates li").removeClass("plan_datepoint_active");
		$("#olDates").hide();
	});
	$("#liDates").click(function() {
		$("#liDaysAll").removeClass("plan_datepoint_active");
		$("#liDaysWeek").removeClass("plan_datepoint_active");
		$("#olWeek").hide();
		$("#olWeek li").removeClass("plan_datepoint_active");
		$("#olDates").show();
		$("#olDates li").removeClass("plan_datepoint_active");
	});

	// hours
	$("#liHoursAll").click(function() {
		$("#olHours li").removeClass("plan_datepoint_active");
		if ($(this).hasClass("plan_datepoint_active")) {
			$("#olHours li").addClass("plan_datepoint_active");
		}
	});
	$("#olHours li").click(function() {
		$("#liHoursAll").removeClass("plan_datepoint_active");
	});

	// minutes
	$("#liMinutesAll").click(function() {
		$("#olMinutes li").removeClass("plan_datepoint_active");
		if ($(this).hasClass("plan_datepoint_active")) {
			$("#olMinutes li").addClass("plan_datepoint_active");
		}
	});
	$("#olMinutes li").click(function() {
		$("#liMinutesAll").removeClass("plan_datepoint_active");
	});

	//-------------------------------------------------
	//END RECURRING PLAN PICKERS
	//-------------------------------------------------

});

//NOTE: this is different than checkRequiredParameters.
// in those cases we're checking our "required" flag... here we're more specific.
function checkParamConstraints() {
	//look over the parameters and do their constraint checking
	if ($(".task_launch_parameter_value_input").length > 0) {
		var warn = false;
		$(".task_launch_parameter_value_input").each(function() {
			msgs = checkFieldConstraints($(this));

			$(this).parent().find(".constraint_msg").remove();

			if (msgs.length > 0) {
				warn = true;
				$ul = $("<ul class=\"constraint_msg ui-state-highlight\" />");
				$.each(msgs, function(index, msg) {
					$ul.append("<li>" + msg + "</li>");
				});
				$(this).parent().append($ul);
			}

		});

		if (warn) {
			return false;
		} else {
			return true;
		}
	} else
		return true;
	//there are no parameters
}

//check parameters before launching or scheduling
function checkRequiredParams() {
	//at this time it doesn't seem necesary to do anything for encrypted values.
	//if the encrypted value is required, it will hightlight if blank.
	//if it was prepopulated by a default, the "********" in the box will count as a value and it will not warn.

	if ($(".task_launch_parameter_required").length > 0) {
		var warn = false;
		$(".task_launch_parameter_required").each(function() {
			var has_val = false;

			//lists and single values are the same, a single is just a one item list.
			$(this).find(".task_launch_parameter_value_input").each(function(i, fld) {
				if ($(fld).val() && $(fld).val() != '')
					has_val = true;
			});

			//mark or unmark it
			if (has_val == true) {
				$(this).removeClass("ui-state-highlight");
			} else {
				$(this).addClass("ui-state-highlight");
				warn = true;
			}
		});

		if (warn == true) {
			ask = confirm("Some Parameters have empty values.\n\nWhile Parameters are allowed to be blank, " + " the highlighted ones are required.\n\nClick 'OK' to proceed, or 'Cancel' to update the Parameters.")
			if (ask) {
				//if they selected OK, clear the highlights and proceed
				$(".task_launch_parameter_required").removeClass("ui-state-highlight");
				return true;
			}
		} else {
			return true;
		}
	} else
		return true;
	//there are no parameters
}

function getParamXML(id, type, filter_id) {
	var task_parameter_xml = "";

	if (filter_id === undefined || filter_id === null)
		filter_id = ""

	var task_parameter_xml = ajaxPost("taskMethods/wmGetParameterXML", {
		sType : type,
		sID : id,
		sFilterID : filter_id
	}, "xml");

	var output = DrawParameterEditForm(task_parameter_xml);

	$("#task_launch_dialog_params").html(output);

	//don't forget to bind the tooltips!
	bindParameterToolTips();
}

function ShowTaskLaunchDialog(jsonargs) {
	$('.current_time').load('uiMethods/wmGetDatabaseTime');

	//function takes a json array as arguments
	//'{"task_id":"","task_name":"","account_id":"","account_name":"","task_instance":"","asset_id":""}'

	var args = jQuery.parseJSON(jsonargs);

	//work out the mandatory arguments...
	if (!args.task_id || !args.task_name) {
		alert("Task ID and Name are required to launch a Task.");
		return false;
	}

	$("#task_launch_dialog_task_id").val(args.task_id);
	$("#task_launch_dialog_task_name").html(args.task_name);

	//we will always pass over an account_id, but it could vary depending on *where* the launch request originated.
	//1) from task edit it uses the global setting
	//2) from the "Run Log" it will use the same as the previous instance being viewed in the log
	//NOTE: if no args are passed to this function we will use the global setting
	if (!args.account_id || args.account_id == "") {
		args.account_id = $("#header_cloud_accounts").val();
		$("#task_launch_dialog_account_id").val($("#header_cloud_accounts").val());
		$("#task_launch_dialog_account_name").html($("#header_cloud_accounts :selected").text());
	} else {
		$("#task_launch_dialog_account_id").val(args.account_id);
		$("#task_launch_dialog_account_name").html(args.account_name);
	}

	//optional args, depending on how we were called and controlling how the dialog is presented.
	if (args.asset_id)
		$("#task_launch_dialog_asset_id").val(args.asset_id);
	if (args.task_instance)
		$("#task_launch_dialog_task_instance").val(args.task_instance);

	//if a debug level was passed, set it
	if (args.debug_level && args.debug_level != "")
		$('#task_launch_dialog_debug_level option[value=' + args.debug_level + ']').attr('selected', 'selected');

	//ALL DONE WITH Arguments... now let's build out the dialog...

	//what XML do we actually go get?
	if (args.task_instance && args.task_instance != "") {//if there's an instance let's get it!
		$("#rbPrevious").attr("checked", "checked");
		getParamXML(args.task_instance, "instance");
	} else {//task defaults by default!
		$("#rbDefault").attr("checked", "checked");
		getParamXML(args.task_id, "task");
	}

	//get the plans
	getPlans();

	$.unblockUI();
	$("#task_launch_dialog").dialog("open");
}

function ShowPlanEditDialog(ctl) {
	var plan_id = $(ctl).parents(".action_plan").attr("plan_id");
	var schedule_id = $(ctl).parents(".action_plan").attr("schedule_id");

	$("#task_launch_dialog_parameters").fadeOut(500, function() {

		//user might have clicked a PLAN or a SCHEDULE.
		//if there is a plan_id, it's a plan.
		if (plan_id) {
			var source = $(ctl).parents(".action_plan").attr("source");
			var plan_name = $(ctl).html();
			//show the PLAN parameters
			presentPlanParams(plan_id, plan_name);

			//and get the schedule definition if needed
			if (source == 'schedule')
				loadRecurringPlan(schedule_id);

		} else {//it's a schedule
			schedule_id = $(ctl).parents(".action_schedule").attr("id").replace(/as_/, "");

			//get the params from the SCHEDULE, not the PLAN
			presentScheduleParams(schedule_id, "Schedule");
			//and the definition
			loadRecurringPlan(schedule_id);
		}

		$("#plan_edit_dialog").dialog("open");
	});
}

function ClosePlanEditDialog() {
	dismissPlanParams();
	dismissRecurringPlan();
	$("#plan_edit_dialog").dialog("close");
}

function CloseTaskLaunchDialog() {
	$("#task_launch_dialog").dialog("close");
	$("#task_launch_dialog_params").empty();

	//empty every input on the dialog
	$('#task_launch_dialog :input').each(function() {
		var type = this.type;
		var tag = this.tagName.toLowerCase();
		// normalize case
		if (type == 'text' || type == 'password' || tag == 'textarea')
			this.value = "";
		else if (type == 'checkbox' || type == 'radio')
			this.checked = false;
		else if (tag == 'select')
			this.selectedIndex = 0;
	});

	//NOTE: the debug drop down actually should have item #2 selected by default.
	$('#task_launch_dialog_debug_level option[value="2"]').attr('selected', 'selected');
	return false;
}

function RunNow() {

	showPleaseWait();
	$("#update_success_msg").text("Starting Task...");

	var account_id = $("#task_launch_dialog_account_id").val();
	var task_id = $("#task_launch_dialog_task_id").val();
	var asset_id = $("#task_launch_dialog_asset_id").val();
	var debug_level = $("#task_launch_dialog_debug_level").val();

	//build the XML from the dialog
	var parameter_xml = packJSON(buildXMLToSubmit());
	//alert(parameter_xml);

	var response = ajaxPost("taskMethods/wmRunTask", {
		sTaskID : task_id,
		sAccountID : account_id,
		sParameterXML : parameter_xml,
		iDebugLevel : debug_level
	}, "text");
	if (response.length > 0) {
		// if the 'new window' box is checked...
		if ($("#new_runlog_window").is(':visible')) {
			if ($("#new_runlog_window").is(':checked')) {
				openDialogWindow('taskRunLog?task_instance=' + response, 'TaskRunLog' + response, 950, 750, 'true');
			} else {
				location.href = 'taskRunLog?task_instance=' + response;
			}
		} else {
			openDialogWindow('taskRunLog?task_instance=' + response, 'TaskRunLog' + response, 950, 750, 'true');
		}

		$("#update_success_msg").text("Start Successful").fadeOut(2000);

		//hate sticking it here, but this is only for the task edit/view pages...
		$("#debug_instance").val(response);
		//does the page have this function?
		if ( typeof doGetDebug == 'function') {
			doGetDebug();
		}
	} else {
		alert("The Task may not have started... no Task Instance was returned.")
	}

	$("#update_success_msg").fadeOut(2000);
	hidePleaseWait();

	CloseTaskLaunchDialog();

}

function ReadTimetable() {
	//built the timetable values
	//I know this seems crazy, but we can loop every single selected datepoint, and build different arrays
	//based on the name of the datepoint!

	var months = [];
	var days = [];
	var hrs = [];
	var mins = [];
	var dorw = "";

	$('.plan_datepoint_active').each(function() {
		var id = $(this).attr("id");
		var typ = id.substring(0, id.indexOf('_'));

		switch (id) {
			case 'liMonthsAll':
				months = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
				break;
			case 'liDaysAll':
				days = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30];
				dorw = "0";
				// 0 = explicit days, all selected
				break;
			case 'liDates':
				dorw = "0";
				// 0 = explicit days, only some selected
				break;
			case 'liDaysWeek':
				//this toggle does NOT indicate an 'all' condition, rather a weekdays mode
				dorw = "1";
				// 1 = weekdays
				break;
			case 'liHoursAll':
				hrs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23];
				break;
			case 'liMinutesAll':
				mins = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59];
				break;
			default:
				//if it wasn't one of the selector buttons, it must be an explicit date point
				//NOTE: both days (d) and weekday (w) selectors populate the "days" array.
				var tmp;
				switch (typ) {
					case 'mo':
						tmp = parseInt(id.replace(/mo_/, ""));
						if (!isNaN(tmp)) {
							months.push(tmp);
						}
						break;
					case 'd':
						tmp = parseInt(id.replace(/d_/, ""));
						if (!isNaN(tmp)) {
							days.push(tmp);
						}
						break;
					case 'w':
						tmp = parseInt(id.replace(/w_/, ""));
						if (!isNaN(tmp)) {
							days.push(tmp);
						}
						break;
					case 'h':
						tmp = parseInt(id.replace(/h_/, ""));
						if (!isNaN(tmp)) {
							hrs.push(tmp);
						}
						break;
					case 'm':
						tmp = parseInt(id.replace(/m_/, ""));
						if (!isNaN(tmp)) {
							mins.push(tmp);
						}
						break;
				}

				break;
		}
	});

	if (!months.length || !days.length || !hrs.length || !mins.length || dorw == "") {
		showInfo("Please select a complete schedule - at least one item from each section.");
		return null;
	}

	var ttarr = {};
	ttarr.months = months;
	ttarr.days = days;
	ttarr.hrs = hrs;
	ttarr.mins = mins;
	ttarr.dorw = dorw;

	return ttarr;
}

function RunRepeatedly() {
	var account_id = $("#task_launch_dialog_account_id").val();
	var task_id = $("#task_launch_dialog_task_id").val();
	var debug_level = $("#task_launch_dialog_debug_level").val();

	//timetable comes back as json
	var tt = ReadTimetable();
	if (tt) {
		//build the XML from the dialog
		var parameter_xml = packJSON(buildXMLToSubmit());

		var args = {};
		args.sTaskID = task_id;
		args.sAccountID = account_id;
		args.sMonths = tt.months;
		args.sDays = tt.days;
		args.sHours = tt.hrs;
		args.sMinutes = tt.mins;
		args.sDaysOrWeeks = tt.dorw;
		args.sParameterXML = parameter_xml;
		args.iDebugLevel = debug_level;

		ajaxPost("uiMethods/wmRunRepeatedly", args, "text");
		$("#update_success_msg").text("Schedule Successful").fadeOut(2000);

		//refresh and change to the "Plan" tab so the user knows something happened
		getPlans();
		$('#task_launch_dialog_schedule').tabs('select', 3);
	}
}

function RunLater() {
	//future enhancement:
	//if this save would be really close to a recurring entry ... courtesy prompt the user?

	var run_on = $("#run_on_date").val();
	if (!run_on) {
		alert("Please select a Time.");
		return false;
	}

	var account_id = $("#task_launch_dialog_account_id").val();
	var task_id = $("#task_launch_dialog_task_id").val();
	var debug_level = $("#task_launch_dialog_debug_level").val();

	//build the XML from the dialog
	var parameter_xml = packJSON(buildXMLToSubmit());

	var response = ajaxPost("uiMethods/wmRunLater", {
		sTaskID : task_id,
		sAccountID : account_id,
		sRunOn : run_on,
		sParameterXML : parameter_xml,
		iDebugLevel : debug_level
	}, "text");
	if (response) {
		$("#update_success_msg").text("Plan Successful").fadeOut(2000);

		//refresh and change to the "Plan" tab so the user knows something happened
		getPlans();
		$('#task_launch_dialog_schedule').tabs('select', 3);
	}
}

function SaveRecurringPlan() {
	var schedule_id = $("#plan_edit_plan_id").val();
	var debug_level = $("#task_launch_dialog_debug_level").val();

	//timetable comes back as json
	var tt = ReadTimetable();
	if (tt) {

		//build the XML from the dialog
		var parameter_xml = packJSON(buildXMLToSubmit());

		var args = {
			sScheduleID : schedule_id,
			sMonths : tt.months,
			sDays : tt.days,
			sHours : tt.hrs,
			sMinutes : tt.mins,
			sDaysOrWeeks : tt.dorw,
			sParameterXML : parameter_xml,
			iDebugLevel : debug_level
		}

		var response = ajaxPost("uiMethods/wmSaveSchedule", args, "text");
		if (response) {
			$("#update_success_msg").text("Update Successful").fadeOut(2000);

			//change to the "Plan" tab so the user knows something happened
			getPlans();
			//this refreshes the plans tabs because labels have changed.
			$('#task_launch_dialog_schedule').tabs('select', 3);

			//will refresh the parent page, if it has an appropriate function
			if ( typeof doGetPlans == 'function') {
				doGetPlans();
			}
		}

		return true;
	}

	return false;
}

function SavePlan() {
	var plan_id = $("#plan_edit_plan_id").val();
	var debug_level = $("#task_launch_dialog_debug_level").val();

	//build the XML from the dialog
	var parameter_xml = packJSON(buildXMLToSubmit());

	var response = ajaxPost("uiMethods/wmSavePlan", {
		iPlanID : plan_id,
		sParameterXML : parameter_xml,
		iDebugLevel : debug_level
	});
	if (response) {
		$("#update_success_msg").text("Update Successful").fadeOut(2000);

		//change to the "Plan" tab so the user knows something happened
		//unlike SaveRecurringPlan - no need to refresh the plan tab here
		$('#task_launch_dialog_schedule').tabs('select', 3);

		//will refresh the parent page, if it has an appropriate function
		if ( typeof doGetPlans == 'function') {
			doGetPlans();
		}
	}
	return true;
}

function getPlans() {
	var task_id = $("#task_launch_dialog_task_id").val();

	ajaxPostAsync("uiMethods/wmGetActionPlans", {
		sTaskID : task_id
	}, function(response) {
		$("#task_launch_dialog_plans").html(response);
	}, "html");

	ajaxPostAsync("uiMethods/wmGetActionSchedules", {
		sTaskID : task_id
	}, function(response) {
		$("#task_launch_dialog_schedules").html(response);
		//schedule icon tooltips
		$("#task_launch_dialog_schedules .schedule_tip").tipTip({
			defaultPosition : "right",
			keepAlive : false,
			activation : "hover",
			maxWidth : "500px",
			fadeIn : 100
		});

	}, "html");
}

function deleteSchedule(ctl) {
	var schedule_id = $(ctl).parents(".action_schedule").attr("id").replace(/as_/, "");
	var msg = "Are you sure you want to delete this Recurring Action Plan?";

	if (confirm(msg)) {
		var response = ajaxPost("uiMethods/wmDeleteSchedule", {
			sScheduleID : schedule_id
		});
		if (response) {
			$("#update_success_msg").text("Delete Successful").fadeOut(2000);

			$(ctl).parents(".action_schedule").remove();
			//might be some on the Schedules tab too
			$(".action_schedule[id='as_" + schedule_id + "']").remove();
			//remove any action plans too, directly from the page.
			$(".action_plan[schedule_id='" + schedule_id + "']").remove();
		}
	}
}

function deleteActionPlan(ctl) {
	var plan_id = $(ctl).parents(".action_plan").attr("plan_id");

	var src = $(ctl).parents(".action_plan").attr("source");
	var msg = "Are you sure you want to remove this Action Plan?";

	if (src == 'scheduler')
		msg += "\n\nA plan added by the Scheduler and removed here cannot be rescheduled.";

	if (confirm(msg)) {
		var response = ajaxPost("uiMethods/wmDeleteActionPlan", {
			iPlanID : plan_id
		});
		if (response) {
			$("#update_success_msg").text("Delete Successful").fadeOut(2000);

			$(ctl).parents(".action_plan").remove();
			//might be some on the Schedules tab too
			$(".action_plan[plan_id='" + plan_id + "']").remove();
		}
	}
}

function presentScheduleParams(schedule_id, schedule_name) {
	$("#plan_edit_plan_id").val(schedule_id);
	$("#plan_edit_mode").html("Schedule");
	$("#plan_edit_name").html(schedule_name);

	//uncheck all radio buttons as an indicator the data didn't come from there
	$("input[name='radio']").removeAttr("checked");

	//get the params for this plan
	getParamXML(schedule_id, "schedule", "");

	$("#task_launch_params_content").appendTo("#plan_edit_parameters");
}

function presentPlanParams(plan_id, plan_name) {
	$("#plan_edit_plan_id").val(plan_id);
	$("#plan_edit_mode").html("Plan");
	$("#plan_edit_name").html(plan_name);

	//uncheck all radio buttons as an indicator the data didn't come from there
	$("input[name='radio']").removeAttr("checked");

	//get the params for this plan
	getParamXML(plan_id, "plan", "");

	$("#task_launch_params_content").appendTo("#plan_edit_parameters");
}

function dismissPlanParams() {
	var task_id = $("#task_launch_dialog_task_id").val();
	var plan_id = $("#plan_edit_plan_id").val();

	//get the default parameters for the task again
	$("#rbDefault").attr("checked", "checked");
	getParamXML(task_id, "task");

	//put it back
	$("#task_launch_params_content").appendTo("#task_launch_dialog_parameters");

	$("#task_launch_dialog_parameters").fadeIn(500);
}

function dismissRecurringPlan() {
	//clear all selected timetable buttons
	$(".plan_datepoint_active").removeClass("plan_datepoint_active");

	//put it back
	$("#run_repeatedly_content").appendTo("#RunRepeatedlyTab");
}

function loadRecurringPlan(schedule_id) {
	var response = ajaxPost("uiMethods/wmGetRecurringPlan", {
		sScheduleID : schedule_id
	});
	if (response) {
		populateTimetable(response);

		//move it to the edit dialog
		$("#run_repeatedly_content").appendTo("#plan_edit_schedule");
	}
}

function populateTimetable(timetable) {
	//the timetable may have previous selections... clear EVERYTHING
	$(".plan_datepoint_active").removeClass("plan_datepoint_active");

	// Months, 0 == Jan, 11 == Dec
	var Months = timetable.sMonths;
	if (Months == "0,1,2,3,4,5,6,7,8,9,10,11") {
		$("#liMonthsAll").addClass("plan_datepoint_active");
	} else {
		var valueArray = Months.split(",")
		for (var i = 0; i < valueArray.length; i++) {
			$("#mo_" + valueArray[i]).addClass("plan_datepoint_active");
		}
	}

	// Days or weekdays
	var dorw = timetable.sDaysOrWeeks;
	var days = timetable.sDays;
	valueArray = days.split(",")

	switch (dorw) {
		case '0':
			//days
			$("#olWeek").hide();
			//hide and clear the "weekdays"
			$("#olWeek li").removeClass("plan_datepoint_active");
			$("#olDates").show();

			if (days == "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30") {
				$("#liDaysAll").addClass("plan_datepoint_active");
			} else {
				for (var i = 0; i < valueArray.length; i++) {
					$("#d_" + valueArray[i]).addClass("plan_datepoint_active");
				}
				$("#liDates").addClass("plan_datepoint_active");
			}
			break;
		case '1':
			//days of week
			//hide and clear the "days"
			$("#olDates").hide();
			$("#olDates li").removeClass("plan_datepoint_active");
			$("#olWeek").show();

			for (var i = 0; i < valueArray.length; i++) {
				$("#w_" + valueArray[i]).addClass("plan_datepoint_active");
			}
			$("#liDaysWeek").addClass("plan_datepoint_active");
			break;
		default:
			$("#olWeek").hide();
			break;
	};

	// Hours
	var Hours = timetable.sHours;
	valueArray = Hours.split(",")
	if (Hours == "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23") {
		$("#liHoursAll").addClass("plan_datepoint_active");
	} else {
		for (var i = 0; i < valueArray.length; i++) {
			$("#h_" + valueArray[i]).addClass("plan_datepoint_active");
		}
	}

	// Minutes
	var Minutes = timetable.sMinutes;
	valueArray = Minutes.split(",")
	if (Minutes == "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59") {
		$("#liMinutesAll").addClass("plan_datepoint_active");
	} else {
		for (var i = 0; i < valueArray.length; i++) {
			$("#m_" + valueArray[i]).addClass("plan_datepoint_active");
		}
	}
}

function drawRecurringItem(howmany, idprefix, add) {
	var output = '';
	var label = '';

	for ( i = 0; i < howmany; i++) {
		if (add)
			label = i + 1;
		else
			label = i;

		if (("" + label).length == 1)
			label = "0" + label;

		var id = idprefix + "_" + i;

		output += '<li id="' + id + '" class="plan_datepoint"><span class="ui-state-default ui-corner-all">' + label + '</span></li>';
	}

	return output;
}

function drawRecurringPanel() {
	//separated this out so the dynamic html block at the top of this file isn't stupid huge

	var output = 'Months \
		<div class="ui-dropslide ui-widget"> \
		   <ol id="olMonthsAll" class="ui-widget ui-helper-clearfix ui-helper-reset"> \
		       <li id="liMonthsAll" class="plan_datepoint"><span class="ui-state-default ui-corner-all">All</span></li> \
		   </ol> \
		   <ol id="olMonths" class="ui-widget ui-helper-clearfix ui-helper-reset"> \
		       <li id="mo_0" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Jan</span></li> \
		       <li id="mo_1" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Feb</span></li> \
		       <li id="mo_2" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Mar</span></li> \
		       <li id="mo_3" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Apr</span></li> \
		       <li id="mo_4" class="plan_datepoint"><span class="ui-state-default ui-corner-all">May</span></li> \
		       <li id="mo_5" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Jun</span></li> \
		       <li id="mo_6" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Jul</span></li> \
		       <li id="mo_7" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Aug</span></li> \
		       <li id="mo_8" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Sep</span></li> \
		       <li id="mo_9" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Oct</span></li> \
		       <li id="mo_10" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Nov</span></li> \
		       <li id="mo_11" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Dec</span></li> \
		   </ol> \
		</div> \
		Days \
		<div class="ui-dropslide ui-widget"> \
		    <ol id="olDaysType" class="ui-widget ui-helper-clearfix ui-helper-reset"> \
		        <li id="liDaysAll" class="plan_datepoint"><span class="ui-state-default ui-corner-all">All</span></li> \
		        <li style="width: 35px;" id="liDaysWeek" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Week</span></li> \
		        <li style="width: 35px;" id="liDates" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Days</span></li> \
		    </ol> \
		    <ol id="olWeek" class="ui-widget ui-helper-clearfix ui-helper-reset hidden"> \
		        <li id="w_0" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Sun</span></li> \
		        <li id="w_1" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Mon</span></li> \
		        <li id="w_2" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Tue</span></li> \
		        <li id="w_3" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Wed</span></li> \
		        <li id="w_4" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Thu</span></li> \
		        <li id="w_5" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Fri</span></li> \
		        <li id="w_6" class="plan_datepoint"><span class="ui-state-default ui-corner-all">Sat</span></li> \
		    </ol> \
		    <ol id="olDates" class="ui-widget ui-helper-clearfix ui-helper-reset">' + drawRecurringItem(31, 'd', true) + '</ol> \
		</div> \
		Hours \
		<div class="ui-dropslide ui-widget"> \
		    <ol id="olHoursAll" class="ui-widget ui-helper-clearfix ui-helper-reset"> \
		        <li id="liHoursAll" class="plan_datepoint"><span class="ui-state-default ui-corner-all">All</span></li> \
		    </ol> \
		    <ol id="olHours" class="ui-widget ui-helper-clearfix ui-helper-reset">' + drawRecurringItem(24, 'h', false) + '</ol> \
		</div> \
		Minutes \
		<div class="ui-dropslide ui-widget"> \
		    <ol id="olMinutesAll" class="ui-widget ui-helper-clearfix ui-helper-reset"> \
		        <li id="liMinutesAll" class="plan_datepoint"><span class="ui-state-default ui-corner-all">All</span></li> \
		    </ol> \
		    <ol id="olMinutes" class="ui-widget ui-helper-clearfix ui-helper-reset">' + drawRecurringItem(60, 'm', false) + '</ol> \
		</div>';

	return output;
}