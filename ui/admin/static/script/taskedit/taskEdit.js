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

				$.ajax({
					async : false,
					type : "POST",
					url : "taskMethods/wmApproveTask",
					data : '{"sTaskID":"' + g_task_id + '","sMakeDefault":"' + make_default + '"}',
					contentType : "application/json; charset=utf-8",
					dataType : "text",
					success : function(response) {
						//now redirect (using replace so they can't go "back" to the editable version)
						location.replace("taskView?task_id=" + g_task_id);
					},
					error : function(response) {
						$("#update_success_msg").fadeOut(2000);
						showAlert(response.responseText);
					}
				});
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
	$.ajax({
		type : "POST",
		async : true,
		url : "taskMethods/wmGetTask",
		data : '{"sTaskID":"' + g_task_id + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(task) {
			try {
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

			} catch (ex) {
				showAlert(ex.message);
			}
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function doGetCommands() {
	$("#div_commands #categories").load("uiMethods/wmGetCategories", function() {
		//set the help text on hover over a category
		$("#toolbox .category").hover(function() {
			$("#te_help_box_detail").html($("#help_text_" + $(this).attr("name")).html());
		}, function() {
			$("#te_help_box_detail").html("");
		});

		//toggle categories
		$("#toolbox .category").click(function() {
			//unselect all the categories
			$("#toolbox .category").removeClass("category_selected");

			//and select this one you clicked
			//alert($(this).attr("id"));
			$(this).addClass("category_selected");

			//hide 'em all
			$("#toolbox .functions").addClass("hidden");

			//show the one you clicked
			$("#" + $(this).attr("id") + "_functions").removeClass("hidden");
		});
	});
	$("#div_commands #category_functions").load("uiMethods/wmGetFunctions", function() {
		//init the draggable items (commands and the clipboard)
		//this will also be called when items are added/removed from the clipboard.
		initDraggable();
	});
}

function doGetSteps() {
	//this codeblock thing has always been an issue.  What codeblock are we getting?
	//for now, we're gonna try keeping the codeblock in a hidden field
	var codeblock_name = $("#hidCodeblockName").val();

	$.ajax({
		type : "POST",
		async : true,
		url : "taskMethods/wmGetSteps",
		data : '{"sTaskID":"' + g_task_id + '","sCodeblockName":"' + codeblock_name + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "html",
		success : function(response) {
			try {
				//the result is an html snippet
				//we have to redo the sortable for the new content
				$("#steps").empty();
				$("#steps").sortable("destroy");
				$("#steps").append(response);
				initSortable();
				validateStep();
				$("#codeblock_steps_title").text(codeblock_name);
			} catch (ex) {
				showAlert(ex.message);
			}
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});

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
		$.ajax({
			async : false,
			type : "POST",
			url : "taskMethods/wmUpdateTaskDetail",
			data : '{"sTaskID":"' + g_task_id + '","sColumn":"' + column + '","sValue":"' + value + '"}',
			contentType : "application/json; charset=utf-8",
			dataType : "json",
			success : function(response) {
				try {
					if (response.error) {
						showAlert(response.error);
					}
					if (response.info) {
						showInfo(response.info);
					}
					if (response.result) {
						if (response.result == "success") {
							$("#update_success_msg").text("Update Successful").fadeOut(2000);
							// bugzilla 1037 Change the name in the header
							if (column == "task_name") {
								$("#lblTaskNameHeader").html(unpackJSON(value));
							};
						} else {
							$("#update_success_msg").text("Update Failed").fadeOut(2000);
							showInfo(response);
						}
					}
				} catch (ex) {
					showAlert(ex.message);
				}
			},
			error : function(response) {
				$("#update_success_msg").fadeOut(2000);
				showAlert(response.responseText);
			}
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

	$.ajax({
		async : false,
		type : "POST",
		url : "taskMethods/wmAddEmbeddedCommandToStep",
		data : '{"sTaskID":"' + g_task_id + '","sStepID":"' + drop_step_id + '","sDropXPath":"' + drop_xpath + '","sItem":"' + item + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "html",
		success : function(response) {
			$("#" + droptarget).replaceWith(response);

			//you have to add the embedded command NOW, or click cancel.
			// if (item == "fn_if" || item == "fn_loop" || item == "fn_exists" || item == "fn_while") {
			// doDropZoneEnable($("#" + droptarget + " .step_nested_drop_target"));
			// }
			$("#task_steps").unblock();
			$("#update_success_msg").fadeOut(2000);
		},
		error : function(response) {
			$("#update_success_msg").fadeOut(2000);
			showAlert(response.responseText);
		}
	});
}

function getStep(step_id, target, init) {
	$.ajax({
		async : false,
		type : "POST",
		url : "taskMethods/wmGetStep",
		data : '{"sStepID":"' + step_id + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "html",
		success : function(retval) {
			$("#" + target).replaceWith(retval);

			if (init)
				initSortable();

			validateStep(step_id);

			$("#task_steps").unblock();
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
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
		}, 999)
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
			$ctl.droppable("destroy");

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
	$("#" + id).droppable("destroy");
	initSortable();
}

function doClearClipboard(id) {
	$("#update_success_msg").text("Removing...").show();
	$.ajax({
		async : false,
		type : "POST",
		url : "taskMethods/wmRemoveFromClipboard",
		data : '{"sStepID":"' + id + '"}',
		contentType : "application/json; charset=utf-8",
		dataType : "json",
		success : function(response) {
			// we can just whack it from the dom
			if (id == "ALL")
				$("#clipboard").empty();
			else
				$("#clipboard #clip_" + id).remove();

			$("#update_success_msg").text("Remove Successful").fadeOut(2000);
		},
		error : function(response) {
			$("#update_success_msg").fadeOut(2000);
			showAlert(response.responseText);
		}
	});
}

function doGetClips() {
	$.ajax({
		async : false,
		type : "GET",
		url : "taskMethods/wmGetClips",
		contentType : "application/json; charset=utf-8",
		dataType : "html",
		success : function(response) {
			$("#clipboard").html(response);
			initDraggable();
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
}

function initDraggable() {
	//initialize the 'commands' tab and the clipboard tab to be draggable to the step list
	$("#toolbox .function").draggable("destroy");
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
	})

	//unbind it first so they don't stack (since hover doesn't support "live")
	$("#toolbox .function").unbind("mouseenter mouseleave");
	$("#toolbox .command_item").unbind("mouseenter mouseleave");

	//set the help text on hover over a function
	$("#toolbox .function").hover(function() {
		$("#te_help_box_detail").html($("#help_text_" + $(this).attr("name")).html());
	}, function() {
		$("#te_help_box_detail").html("");
	});

	$("#toolbox .command_item").hover(function() {
		$(this).addClass("command_item_hover");
	}, function() {
		$(this).removeClass("command_item_hover");
	});
}
