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

//This is all the functions to support the taskEdit page.
$(document).ready(function() {
	//used a lot - also on different script files so be mindful of the include order
	g_task_id = getQuerystringVariable("task_id");

	//fix certain ui elements to not have selectable text
	$("#toolbox .toolbox_tab").disableSelection();
	$("#toolbox .codeblock").disableSelection();
	$("#toolbox .category").disableSelection();
	$("#toolbox .function").disableSelection();
	$(".step_common_button").disableSelection();

	//specific field validation and masking
	$("#txtTaskCode").keypress(function(e) {
		return restrictEntryCustom(e, this, /[a-zA-Z0-9 _\-]/);
	});
	$("#txtTaskName").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	$("#txtTaskDesc").keypress(function(e) {
		return restrictEntryToSafeHTML(e, this);
	});
	$("#txtConcurrentInstances").keypress(function(e) {
		return restrictEntryToPositiveInteger(e, this);
	});
	$("#txtQueueDepth").keypress(function(e) {
		return restrictEntryToPositiveInteger(e, this);
	});

	//enabling the 'change' event for the Details tab
	$("#div_details :input[te_group='detail_fields']").change(function() {
		var column = $(this).attr("column");

		if (column === "task_name") {
			// changing a task name has repercussions... warn about it.
			var agreed = confirm("Changing a Task Name will update all programmatic references to this Task.\n\nAre you sure?");
			if (!agreed) {
				$("#txtTaskName").val($("#txtTaskName").data("original_name"));
				return;
			}
		}

		doDetailFieldUpdate(this);
	});

	//jquery buttons
	$("#task_search_btn").button({
		icons : {
			primary : "ui-icon-search"
		}
	});

	//the 'Approve' button
	$("#approve_dialog").dialog({
		autoOpen : false,
		draggable : false,
		resizable : false,
		bgiframe : true,
		modal : true,
		width : 400,
		overlay : {
			backgroundColor : '#000',
			opacity : 0.5
		},
		buttons : {
			'Approve' : function() {
				$.blockUI({
					message : null
				});

				var $chk = $("#chkMakeDefault");
				var make_default = 0;

				if ($chk.is(':checked'))
					make_default = 1;

				var response = ajaxPost("taskMethods/wmApproveTask", {
					sTaskID : g_task_id,
					sMakeDefault : make_default
				}, "text");
				if (response) {
					//now redirect (using replace so they can't go "back" to the editable version)
					location.replace("taskView?task_id=" + g_task_id);
				}
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});

	$("#approve_btn").button({
		icons : {
			primary : "ui-icon-check"
		}
	});
	$("#approve_btn").click(function() {
		$("#approve_dialog").dialog("open");
	});

	//make the clipboard clear button
	$("#clear_clipboard_btn").button({
		icons : {
			primary : "ui-icon-close"
		}
	});

	//clear the whole clipboard
	$("#clear_clipboard_btn").click(function() {
		doClearClipboard("ALL");
	});

	//clear just one clip
	$(".btn_clear_clip").live("click", function() {
		doClearClipboard($(this).attr("remove_id"));
	});

	//the clip view dialog
	$("#clip_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 800
	});
	//pop up the clip to view it
	$(".btn_view_clip").live("click", function() {
		var clip_id = $(this).attr("view_id");

		var html = $("#" + clip_id).html();

		$("#clip_dialog_clip").html(html);
		$("#clip_dialog").dialog("open");
	});

	//big edit box dialog
	//init the big box dialog
	$("#big_box_dialog").dialog({
		autoOpen : false,
		modal : true,
		width : 800,
		buttons : {
			OK : function() {
				var ctl = $("#big_box_link").val();
				$("#" + ctl).val($("#big_box_text").val());

				//do something to fire the blur event so it will update
				$("#" + ctl).change();

				$(this).dialog("close");
			},
			Cancel : function() {
				$(this).dialog("close");
			}
		}
	});
	$(".big_box_btn").live("click", function() {
		var ctl = $(this).attr("link_to");

		$("#big_box_link").val(ctl);
		$("#big_box_text").val($("#" + ctl).val());

		$("#big_box_dialog").dialog("open");
	});

	// tab handling for the big_box_text textarea
	$("#big_box_text").tabby();

	//activating the dropzone for nested steps
	$("#steps .step_nested_drop_target").live("click", function() {
		doDropZoneEnable($(this));
	});

	// unblock when ajax activity stops
	//$().ajaxStop($.unblockUI);

	//the command help dialog
	$("#command_help_dialog").dialog({
		autoOpen : false,
		width : 800,
		height : 600
	});
	// this dialog has huge content... it's important to empty it when its closed
	// otherwise the page dom is noticeably slower.
	$("#command_help_dialog").bind("dialogclose", function(event) {
		$("#command_help_dialog_detail").empty();
	});

	//get the details
	doGetDetails();
	//get the commands
	doGetCommands();
	//get the codeblocks
	doGetCodeblocks();
	//get the steps
	doGetSteps();
});

function doGetDetails() {
	ajaxPostAsync("taskMethods/wmGetTask", {
		sTaskID : g_task_id
	}, function(task) {
		$("#hidOriginalTaskID").val(task.OriginalTaskID);
		$("#txtTaskCode").val(task.Code);
		$("#txtTaskName").val(task.Name);
		$("#txtTaskName").data("original_name", task.Name);
		$("#txtDescription").val(task.Description);
		$("#txtConcurrentInstances").val(task.ConcurrentInstances);
		$("#txtQueueDepth").val(task.QueueDepth);

		//ATTENTION!
		//Approved tasks CANNOT be edited.  So, if the status is approved... we redirect to the
		//task 'view' page.
		//this is to prevent any sort of attempts on the client to load an approved or otherwise 'locked'
		// version into the edit page.
		var pagename = window.location.pathname;
		pagename = pagename.substring(pagename.lastIndexOf('/') + 1);
		if (pagename != "taskView") {
			if (task.Status == "Approved") {
				location.href = "taskView?task_id=" + g_task_id;
			}
		}

		$("#lblVersion").text(task.Version);
		$("#lblCurrentVersion").text(task.Version);
		$("#lblStatus2").text(task.Status);

		$("#lblNewMinorVersion").text(task.NextMinorVersion);
		$("#lblNewMajorVersion").text(task.NextMajorVersion);

		/*
		 * ok, this is important.
		 * there are some rules for the process of 'Approving' a task.
		 * specifically:
		 * -- if there are no other approved tasks in this family, this one will become the default.
		 * -- if there is another approved task in this family, we show the checkbox
		 * -- allowing the user to decide whether or not to make this one the default
		 */
		if (task.NumberOfApprovedVersions > "0") {
			$("#make_default_chk").show();
			// you can't make a development version default if there is an approved version
			$("#set_default_btn").hide();
		} else {
			$("#make_default_chk").hide();
			if (task.IsDefaultVersion == "True") {
				$("#set_default_btn").hide();
			} else {
				$("#set_default_btn").show();
			}
		}

		//the header
		$("#lblTaskNameHeader").text(task.Name);
		$("#lblVersionHeader").text(task.Version + (task.IsDefaultVersion == "True" ? " (default)" : ""));

	});
}

function doGetCommands() {
	$("#div_commands #categories").load("uiMethods/wmGetCategories", function() {
		//set the help text on hover over a category
		$("#toolbox .category").hover(function() {
			$(this).children(":first").addClass("command_item_hover");
			$("#te_help_box_detail").html($(this).find(".cathelp").html());
		}, function() {
			$(this).children(":first").removeClass("command_item_hover");
			$("#te_help_box_detail").html("");
		});

		//toggle categories
		$("#toolbox .category").click(function(event) {
			// so subcat clicks won't roll up...
			event.stopPropagation();

			// our visible element is wrapped in a container... meaning we are always adding/removing classes
			// from our first child.  Make it easier.
			$visible_me = $(this).children(":first");

			var i_am_selected = $visible_me.hasClass("category_selected");
			var $my_subs = $(this).find(".subcategories");
			var i_have_subs = $my_subs.length > 0;

			// unselect everything
			$("#toolbox .category_selected").removeClass("category_selected");

			// select ourselves and our parent if relevant
			$visible_me.addClass("category_selected");
			if ($(this).hasClass("subcategory")) {
				$(this).parent().parent().children(":first").addClass("category_selected");
			}

			if (i_have_subs) {
				// if I have subs, toggle them
				if ($my_subs.hasClass("hidden")) {
					$my_subs.removeClass("hidden");
				} else {
					$my_subs.addClass("hidden");
					$visible_me.removeClass("category_selected");
				}
			} else if ($(this).hasClass("subcategory")) {
				// if I don't have subs, perhaps I *AM* a sub?
			} else {
				// I neither have subs nor am a sub, so hide all subs.
				$("#toolbox .subcategories").addClass("hidden");
			}

			//hide all functions
			$("#toolbox .functions").addClass("hidden");

			// of course, always show functions, even cats with subcats may have root level functions
			$("#" + $(this).attr("id") + "_functions").removeClass("hidden");

			// and scroll to the top
			$('#div_commands').animate({
				scrollTop : 0
			}, 'slow');
		});
	});
	ajaxGet("uiMethods/wmGetFunctions", function(response) {
		$("#div_commands #category_functions").html(response);
		//init the draggable items (commands and the clipboard)
		//this will also be called when items are added/removed from the clipboard.
		initDraggable();
	}, "html");
}

function doGetSteps() {
	//this codeblock thing has always been an issue.  What codeblock are we getting?
	//for now, we're gonna try keeping the codeblock in a hidden field
	var codeblock_name = $("#hidCodeblockName").val();

	ajaxPostAsync("taskMethods/wmGetSteps", {
		sTaskID : g_task_id,
		sCodeblockName : codeblock_name
	}, function(response) {//the result is an html snippet
		//we have to redo the sortable for the new content
		$("#steps").empty();
		if ($("#steps").hasClass("ui-sortable")) {
			$("#steps").sortable("destroy");
		}
		$("#steps").append(response);
		initSortable();
		validateStep();
		$("#codeblock_steps_title").text(codeblock_name);
	}, "html");
}

function doDetailFieldUpdate(ctl) {
	var column = $(ctl).attr("column");
	var value = $(ctl).val();

	//for checkboxes and radio buttons, we gotta do a little bit more, as the pure 'val()' isn't exactly right.
	//and textareas will not have a type property!
	if ($(ctl).attr("type")) {
		var typ = $(ctl).attr("type").toLowerCase();
		if (typ == "checkbox") {
			value = (ctl.checked == true ? 1 : 0);
		}
		if (typ == "radio") {
			value = (ctl.checked == true ? 1 : 0);
		}
	}

	//escape it
	value = packJSON(value);

	if (column.length > 0) {
		$("#update_success_msg").text("Updating...").show();

		var response = ajaxPostAsync("taskMethods/wmUpdateTaskDetail", {
			sTaskID : g_task_id,
			sColumn : column,
			sValue : value
		}, function(response) {
			$("#update_success_msg").text("Update Successful").fadeOut(2000);
			// bugzilla 1037 Change the name in the header
			if (column == "task_name") {
				$("#lblTaskNameHeader").html(unpackJSON(value));
			};
		});
	}
}

function doEmbeddedStepAdd(func, droptarget) {
	$("#task_steps").block({
		message : null
	});
	$("#update_success_msg").text("Adding...").show();

	var item = func.attr("id");
	var drop_step_id = $("#" + droptarget).attr("step_id");
	var drop_xpath = $("#" + droptarget).attr("xpath");

	var response = ajaxPost("taskMethods/wmAddEmbeddedCommandToStep", {
		sTaskID : g_task_id,
		sStepID : drop_step_id,
		sDropXPath : drop_xpath,
		sItem : item
	}, "html");
	if (response) {
		$("#" + droptarget).replaceWith(response);

		//you have to add the embedded command NOW, or click cancel.
		// if (item == "fn_if" || item == "fn_loop" || item == "fn_exists" || item == "fn_while") {
		// doDropZoneEnable($("#" + droptarget + " .step_nested_drop_target"));
		// }
		$("#task_steps").unblock();
		$("#update_success_msg").fadeOut(2000);
	}
}

function getStep(step_id, target, init) {
	var response = ajaxPost("taskMethods/wmGetStep", {
		sStepID : step_id
	}, "html");
	if (response) {
		$("#" + target).replaceWith(response);

		if (init)
			initSortable();

		validateStep(step_id);

		$("#task_steps").unblock();
	}
}

function doDropZoneEnable($ctl) {
	$ctl.html("Drag a command from the toolbox and drop it here now, or <span class=\"step_nested_drop_target_cancel_btn\" onclick=\"doDropZoneDisable('" + $ctl.attr("id") + "');\">click " + "here to cancel</span> add add it later.");
	//
	//$("#" + $(this).attr("id") + " > span").removeClass("hidden");
	$ctl.addClass("step_nested_drop_target_active");

	//gotta destroy the sortable to receive drops in the action area
	//we'll reenable it after we process the drop
	$("#steps").sortable("destroy");

	$ctl.everyTime(2000, function() {
		$ctl.animate({
			backgroundColor : "#ffbbbb"
		}, 999).animate({
			backgroundColor : "#ffeeee"
		}, 999);
	});

	$ctl.droppable({
		accept : ".function",
		hoverClass : "step_nested_drop_target_hover",
		drop : function(event, ui) {
			//add the new step
			var new_step = $(ui.draggable[0]);
			var func = new_step.attr("id");

			if (func.indexOf("fn_") == 0 || func.indexOf("clip_") == 0) {
				doEmbeddedStepAdd(new_step, $ctl.attr("id"));
			}

			$ctl.removeClass("step_nested_drop_target_active");
			if ($ctl.hasClass("ui-droppable")) {
				$ctl.droppable("destroy");
			}
			//DO NOT init the sortable if the command you just dropped has an embedded command
			//at this time it's IF and LOOP, EXISTS and WHILE
			if (func != "fn_if" && func != "fn_loop" && func != "fn_exists" && func != "fn_while")
				initSortable();
		}
	});
}

function doDropZoneDisable(id) {
	$("#" + id).stopTime();
	$("#" + id).css("background-color", "#ffeeee");
	$("#" + id).html("Click here to add a command.");
	$("#" + id).removeClass("step_nested_drop_target_active");
	if ($("#" + id).hasClass("ui-droppable")) {
		$("#" + id).droppable("destroy");
	}
	initSortable();
}

function doClearClipboard(id) {
	ajaxPostAsync("taskMethods/wmRemoveFromClipboard", {
		sStepID : id
	});
	// we can just whack it from the dom
	if (id == "ALL")
		$("#clipboard").empty();
	else
		$("#clipboard #clip_" + id).remove();
}

function doGetClips() {
	ajaxPostAsync("taskMethods/wmGetClips", {}, function(response) {
		$("#clipboard").html(response);
		initDraggable();
	}, "html");

}

function initDraggable() {
	//initialize the 'commands' tab and the clipboard tab to be draggable to the step list
	if ($("#toolbox .function").hasClass("ui-draggable")) {
		$("#toolbox .function").draggable("destroy");
	}
	$("#toolbox .function").draggable({
		distance : 30,
		connectToSortable : '#steps',
		appendTo : 'body',
		revert : 'invalid',
		scroll : false,
		opacity : 0.95,
		helper : 'clone',
		start : function(event, ui) {
			$("#dd_dragging").val("true");
		},
		stop : function(event, ui) {
			$("#dd_dragging").val("false");
		}
	});

	//unbind it first so they don't stack (since hover doesn't support "live")
	$("#toolbox .function").unbind("mouseenter mouseleave");

	//set the help text on hover over a function
	$("#toolbox .function").hover(function() {
		$(this).addClass("command_item_hover");
		$("#te_help_box_detail").html($(this).find(".funchelp").html());
	}, function() {
		$(this).removeClass("command_item_hover");
		$("#te_help_box_detail").html("");
	});
}