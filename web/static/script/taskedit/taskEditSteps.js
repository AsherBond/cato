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
    $("#steps .step_toggle_btn").live("click", function() {
        //alert($(this).attr("id").replace(/step_header_/, ""));
        var step_id = $(this).attr("step_id");
        var visible = 0;

        //toggle it
        $("#step_detail_" + step_id).toggleClass("step_collapsed");

        //then check it
        if (!$("#step_detail_" + step_id).hasClass("step_collapsed"))
            visible = 1;

        // swap the child image, this will work as long as the up down image stays the first child if the span
        if (visible == 1) {
            $(this).children(":first-child").removeClass("ui-icon-triangle-1-e");
            $(this).children(":first-child").addClass("ui-icon-triangle-1-s");
        } else {
            $(this).children(":first-child").removeClass("ui-icon-triangle-1-s");
            $(this).children(":first-child").addClass("ui-icon-triangle-1-e");
        }



        //now persist it
        $("#update_success_msg").text("Updating...").show();
        $.ajax({
            async: true,
            type: "POST",
            url: "taskMethods/wmToggleStep",
            data: '{"sStepID":"' + step_id + '","sVisible":"' + visible + '"}',
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(msg) {
                $("#update_success_msg").text("Update Successful").fadeOut(2000);
            },
            error: function(response) {
                $("#update_success_msg").fadeOut(2000);
                showAlert(response.responseText);
            }
        });
    });

    //toggle all of them
    $("#step_toggle_all_btn").live("click", function() {
        //if all are closed, open them all, else close them all
        // also change the expand images
        if ($("#steps .step_collapsed").length == $(".step_detail").length) {
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
    $("#steps .step_common_button").live("click", function() {
        var btn = "";
        var dtl = $(this).attr("id").replace(/btn_/, "");
        var stp = $(this).attr("step_id");

        //if the one we just clicked on is already showing, hide them all
        if ($("#" + dtl).hasClass("step_common_collapsed")) {
            //hide all
            $("#steps div[id^=step_common_detail_" + stp + "]").addClass("step_common_collapsed");
            $("#step_detail_" + stp + " .step_common_button").removeClass("step_common_button_active");

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
        $.ajax({
            async: true,
            type: "POST",
            url: "taskMethods/wmToggleStepCommonSection",
            data: '{"sStepID":"' + stp + '","sButton":"' + btn + '"}',
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(msg) {
                $("#update_success_msg").text("Update Successful").fadeOut(2000);
            },
            error: function(response) {
                $("#update_success_msg").fadeOut(2000);
                showAlert(response.responseText);
            }
        });
    });

    // Command tab details
    //help button
    $("#command_help_btn").button({ icons: { primary: "ui-icon-help"} });
    $("#command_help_btn").click(function () {
		showPleaseWait();
		$("#command_help_dialog_detail").load("static/_command_help.html", function() {
	        $("#command_help_dialog").dialog("open");
	        hidePleaseWait();
		});
    });

    //the onclick event of the 'skip' icon of each step
    $("#steps .step_skip_btn").live("click", function() {
        //click the hidden field and fire the change event
        var step_id = $(this).attr("step_id");
        var skip = $(this).attr("skip");
        if (skip == "1") {
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

	    $.ajax({
	        async: true,
	        type: "POST",
	        url: "taskMethods/wmToggleStepSkip",
	        data: '{"sStepID":"' + step_id + '", "sSkip":"' + skip + '"}',
	        contentType: "application/json; charset=utf-8",
	        dataType: "json",
	        success: function(response) {
	            $("#update_success_msg").text("Update Successful").fadeOut(2000);
	        },
	        error: function(response) {
	            $("#update_success_msg").fadeOut(2000);
	            showAlert(response.responseText);
	        }
	    });

    });

    //the onclick event of the 'delete' link of each step
    $("#steps .step_delete_btn").live("click", function() {
        $("#hidStepDelete").val($(this).attr("remove_id"));
        $("#step_delete_confirm_dialog").dialog("open");
    });

    //the onclick event of the 'copy' link of each step
    $("#steps .step_copy_btn").live("click", function() {
        $("#update_success_msg").text("Copying...").show();
        var step_id = $(this).attr("step_id");

        $.ajax({
            async: true,
            type: "POST",
            url: "taskMethods/wmCopyStepToClipboard",
            data: '{"sStepID":"' + step_id + '"}',
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(response) {
                doGetClips();
                $("#update_success_msg").text("Copy Successful").fadeOut(2000);
            },
            error: function(response) {
                $("#update_success_msg").fadeOut(2000);
                showAlert(response.responseText);
            }
        });
    });

    //the onclick event of the 'remove' link of embedded steps
    $("#steps .embedded_step_delete_btn").live("click", function() {
        $("#embedded_step_remove_xpath").val($(this).attr("remove_xpath"));
        $("#embedded_step_parent_id").val($(this).attr("parent_id"));
        $("#embedded_step_delete_confirm_dialog").dialog("open");
        //alert('remove step ' + $(this).attr("remove_id") + ' from ' + $(this).attr("parent_id"));
    });

    //the onclick event of 'connection picker' buttons on selected fields
    $("#steps .conn_picker_btn").live("click", function(e) {
        //hide any open pickers
        $("div[id$='_picker']").hide();
        var field = $("#" + $(this).attr("link_to"));

        //first, populate the picker
        $.ajax({
            async: false,
            type: "POST",
            url: "taskMethods/wmGetTaskConnections",
            data: '{"sTaskID":"' + g_task_id + '"}',
            contentType: "application/json; charset=utf-8",
            dataType: "html",
            success: function(response) {
                $("#conn_picker_connections").html(response);
                $("#conn_picker_connections .value_picker_value").hover(
                        function() {
                            $(this).toggleClass("value_picker_value_hover");
                        },
                        function() {
                            $(this).toggleClass("value_picker_value_hover");
                        }
                    );
                $("#conn_picker_connections .value_picker_value").click(function() {
                    field.val($(this).text());
                    field.change();

                    $("#conn_picker").slideUp();
                });
            },
            error: function(response) {
                showAlert(response.responseText);
            }
        });

        //change the click event of this button to now close the dialog
        //        $(this).die("click");
        //        $(this).click(function() { $("#conn_picker").slideUp(); });

        $("#conn_picker").css({ top: e.clientY, left: e.clientX });
        $("#conn_picker").slideDown();
    });


    $("#conn_picker_close_btn").live("click", function(e) {
        //hide any open pickers
        $("div[id$='_picker']").hide();
    });
    $("#var_picker_close_btn").live("click", function(e) {
        //hide any open pickers
        $("div[id$='_picker']").hide();
    });


    //// CODEBLOCK PICKER
    //the onclick event of 'codeblock picker' buttons on selected fields
    $("#steps .codeblock_picker_btn").live("click", function(e) {
        //hide any open pickers
        $("div[id$='_picker']").hide();
        field = $("#" + $(this).attr("link_to"));
        stepid = $(this).attr("step_id");

        //first, populate the picker
        $.ajax({
            async: false,
            type: "POST",
            url: "taskMethods/wmGetTaskCodeblockPicker",
            data: '{"sTaskID":"' + g_task_id + '","sStepID":"' + stepid + '"}',
            contentType: "application/json; charset=utf-8",
            dataType: "html",
            success: function(response) {
                $("#codeblock_picker_codeblocks").html(response);
                $("#codeblock_picker_codeblocks .value_picker_value").hover(
                        function() {
                            $(this).toggleClass("value_picker_value_hover");
                        },
                        function() {
                            $(this).toggleClass("value_picker_value_hover");
                        }
                    );
                $("#codeblock_picker_codeblocks .value_picker_value").click(function() {
                    field.val($(this).text());
                    field.change();

                    $("#codeblock_picker").slideUp();
                });
            },
            error: function(response) {
                showAlert(response.responseText);
            }
        });

        $("#codeblock_picker").css({ top: e.clientY, left: e.clientX });
        $("#codeblock_picker").slideDown();
    });
    $("#codeblock_picker_close_btn").live("click", function(e) {
        //hide any open pickers
        $("[id$='_picker']").hide();
    });

    //////TASK PICKER
    //the onclick event of the 'task picker' buttons everywhere
    $("#steps .task_picker_btn").live("click", function() {
        $("#task_picker_target_field_id").val($(this).attr("target_field_id"));
        //alert($(this).attr("target_field_id") + "\n" + $(this).prev().prev().val());
        $("#task_picker_step_id").val($(this).attr("step_id"));
        $("#task_picker_dialog").dialog("open");
    });

    // when you hit enter inside 'task picker' for a subtask
    $("#task_search_text").live("keypress", function(e) {
        //alert('keypress');
        if (e.which == 13) {
            $("#task_search_btn").click();
            return false;
        }
    });

    //the onclick event of the 'task picker' search button
    $("#task_search_btn").click(function() {
        var field = $("#" + $("#task_picker_target_field_id").val());

        $("#task_picker_dialog").block({ message: null, cursor: 'wait' });
        var search_text = $("#task_search_text").val();
        $.ajax({
            async: false,
            type: "POST",
            url: "taskMethods/wmTaskSearch",
            data: '{"sSearch":"' + search_text + '"}',
            contentType: "application/json; charset=utf-8",
            dataType: "html",
            success: function(response) {
                $("#task_picker_results").html(response);
                //bind the onclick event for the new results
                $("#task_picker_results .task_picker_value").disableSelection();
                $("#task_picker_dialog").unblock();
                
                //gotta kill previously bound clicks or it will stack 'em! = bad.
                $("#task_picker_results li[tag='task_picker_row']").die();
                $("#task_picker_results li[tag='task_picker_row']").live("click", function() {
                    $("#task_steps").block({ message: null });

                    $("#task_picker_dialog").dialog("close");
                    $("#task_picker_results").empty();

                    field.val($(this).attr("original_task_id"));
                    field.change();
                });

                //task description tooltips on the task picker dialog
                $("#task_picker_results .search_dialog_tooltip").tipTip({
                    defaultPosition: "right",
                    keepAlive: false,
                    activation: "hover",
                    maxWidth: "500px",
                    fadeIn: 100
                });
            },
            error: function(response) {
                showAlert(response.responseText);
            }
        });
    });
    //////END TASK PICKER



    //COMMENTED OUT THE BEGINNING OF EDITING A WHOLE STEP AT ONCE.
    //Possible, but cosmic and not crucial right now.

    //////    $("[te_group='step_fields']").live("focus", function() {
    //////        //stick the step_id in a hidden field so we'll know when we move off of it.
    //////        $("editing_step_id").val($(this).attr("step_id"));
    //////    });

    //////DIALOGS
    //init the step delete confirm dialog
    $("#step_delete_confirm_dialog").dialog({
        autoOpen: false,
        draggable: false,
        resizable: false,
        bgiframe: true,
        modal: true,
        overlay: {
            backgroundColor: '#000',
            opacity: 0.5
        },
        buttons: {
            'Delete': function() {
                doStepDelete();
                $(this).dialog("close");
            },
            Cancel: function() {
                $(this).dialog("close");
            }
        }
    });

    //init the embedded step delete confirm dialog
    $("#embedded_step_delete_confirm_dialog").dialog({
        autoOpen: false,
        draggable: false,
        resizable: false,
        bgiframe: true,
        modal: true,
        overlay: {
            backgroundColor: '#000',
            opacity: 0.5
        },
        buttons: {
            'Delete': function() {
			    var remove_path = $("#embedded_step_remove_xpath").val();
			    var step_id = $("#embedded_step_parent_id").val();
			
                doRemoveNode(step_id, remove_path);
                $(this).dialog("close");
            },
            Cancel: function() {
                $(this).dialog("close");
            }
        }
    });

    //init the task picker dialog
    $("#task_picker_dialog").dialog({
        autoOpen: false,
        draggable: false,
        resizable: false,
        bgiframe: true,
        modal: true,
        height: 600,
        width: 600,
        overlay: {
            backgroundColor: '#000',
            opacity: 0.5
        },
        close: function(event, ui) {
            $("#task_search_text").val("");
            $("#task_picker_results").empty();
        }
    });
    //////END DIALOGS

	// NODE ADD
	// This single binding handles all the places where a new content node is added to a step.
    $("#steps .fn_node_add_btn").live("click", function () {
    	
    	// these fully dynamic commands read the section they are gonna add from the original template xml
		// so, it needs the function name and a template xpath in order to be able to look that up.   	
    	
        var step_id = $(this).attr("step_id");
        var func_name = $(this).attr("function_name");
        var template_path = $(this).attr("template_path");
        var add_to = $(this).attr("add_to_node");

        $("#task_steps").block({ message: null });
        $("#update_success_msg").text("Updating...").show();

        $.ajax({
            async: false,
            type: "POST",
            url: "taskMethods/wmFnNodeArrayAdd",
            data: '{"sStepID":"' + step_id + '","sFunctionName":"' + func_name + '","sTemplateXPath":"' + template_path + '","sAddTo":"' + add_to + '"}',
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (retval) {
                //go get the step
                getStep(step_id, step_id, true);
                $("#task_steps").unblock();
                $("#update_success_msg").text("Update Successful").fadeOut(2000);

            },
            error: function (response) {
                showAlert(response.responseText);
            }
        });
    });

	// NODE DELETE
	// this single binding hook up every command node deletion function
    $("#steps .fn_node_remove_btn").live("click", function () {
	    if (confirm("Are you sure?")) {
	        var step_id = $(this).attr("step_id");
	        var remove_path = $(this).attr("remove_path");
	
	        doRemoveNode(step_id, remove_path);
		}
    });
});

function pageLoad() {
    //do this here until (if) the codeblock click gets the full step list via ajax
    initSortable();
    validateStep();

    //fix it so you can't select text in the step headers.
    $("#steps .step_header").disableSelection();

    // hate to have to move this here, but when a codeblock is renamed
    // it reloads the repeater, and we have to hide the main codeblock delete button again
    //the delete and rename links on the MAIN codeblock are always unavailable!
    //but it's a pita to take it out of the repeater in C#, so just remove it here.
    $("#codeblock_rename_btn_MAIN").remove();
    $("#codeblock_delete_btn_MAIN").remove();

}

// This single function can remove any dynamically generated section from any command.
// It simply removes a node from the document.
function doRemoveNode(step_id, remove_path) {
    $("#task_steps").block({ message: null });
    $("#update_success_msg").text("Updating...").show();

    $.ajax({
        async: false,
        type: "POST",
        url: "taskMethods/wmRemoveNodeFromStep",
        data: '{"sStepID":"' + step_id + '","sRemovePath":"' + remove_path + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "text",
        success: function (response) {
            getStep(step_id, step_id, true);
            $("#task_steps").unblock();
            $("#update_success_msg").text("Update Successful").fadeOut(2000);
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
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
    if (typ == "checkbox") {
        field_value = (ctl.checked == true ? 1 : 0);
    }
    if (typ == "radio") {
        field_value = (ctl.checked == true ? 1 : 0);
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
    if (reget == "true") {
        $("#task_steps").block({ message: null });
        getStep(step_id, step_id, true);
        $("#task_steps").unblock();
    }
    else {
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
    $("#steps").sortable("destroy");
    $("#steps").sortable({
        handle: $(".step_header"),
        distance: 20,
        placeholder: 'ui-widget-content ui-corner-all ui-state-active step_drop_placeholder',
        items: 'li:not(#no_step)',
        update: function(event, ui) {
            //if this is a new step... add
            //(add will reorder internally)
            var new_step = $(ui.item[0]);
            var new_step_id = new_step.attr("id");
            if (new_step_id.indexOf("fn_") == 0 || new_step_id.indexOf("clip_") == 0 || new_step_id.indexOf("cb_") == 0) {
                doStepAdd(new_step);
            } else {
                //else just reorder what's here.
                doStepReorder();
            }
        }
    });

	//this turns on the "combobox" controls on steps.
	$(function () {
		$("#steps select:.combo").ufd({submitFreeText: true,
			css: {
				input: "ui-widget-content code",
				li: "code",
				listWrapper: "list-wrapper code"
			}
		});

		
		//NOTE: we are using the ufd plugin, but in this case we need more.
		//This copies all the attributes from the source 'select' onto the new 'input' it created.	
		$("#steps select:.combo").each(function(i, cbo) {
			var id = $(cbo).attr("id");
			$(cbo.attributes).each(function(i, attrib) {
	     		var name = attrib.name;
	     		if (name != "type" && name != "id" && name != "class" && name != "name") {
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

    $.ajax({
        async: false,
        type: "POST",
        url: "taskMethods/wmGetTaskVarPickerPopup",
        data: '{"sTaskID":"' + g_task_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "html",
        success: function(response) {
            $("#var_picker_variables").html(response);

            $("#var_picker_variables .value_picker_group").click(function() {
                $("#" + $(this).attr("target")).toggleClass("hidden");
            });

            $("#var_picker_variables .value_picker_value").hover(
                        function() {
                            $(this).toggleClass("value_picker_value_hover");
                        },
                        function() {
                            $(this).toggleClass("value_picker_value_hover");
                        }
                    );

            $("#var_picker_variables .value_picker_group").hover(
                        function() {
                            $(this).toggleClass("value_picker_value_hover");
                        },
                        function() {
                            $(this).toggleClass("value_picker_value_hover");
                        }
                    );

            $("#var_picker_variables .value_picker_value").click(function() {
                var fjqo = $("#" + fieldWithFocus);
                var f = $("#" + fieldWithFocus)[0];
                var varname = "";

                //note: certain fields should get variable REPLACEMENT syntax [[foo]]
                //others should get the actual name of the variable
                //switch on the function_name to determine this
                var func = fjqo.attr("function");

                switch (func) {
                    case "clear_variable":
                        varname = $(this).text();
                        break;
                    case "substring":
                        // bugzilla 1234 in substring only the variable_name field gets the value without the [[ ]]
                        var xpath = fjqo.attr("xpath");
                        if (xpath == "variable_name") {
                            varname = $(this).text();
                        } else {
                            varname = "[[" + $(this).text() + "]]";
                        }
                        break;
                    case "loop":
                        // bugzilla 1234 in substring only the variable_name field gets the value without the [[ ]]
                        var xpath = fjqo.attr("xpath");
                        if (xpath == "counter") {
                            varname = $(this).text();
                        } else {
                            varname = "[[" + $(this).text() + "]]";
                        }
                        break;
                    case "set_variable":
                        // bugzilla 1234 in substring only the variable_name field gets the value without the [[ ]]
                        var xpath = fjqo.attr("xpath");
                        if (xpath.indexOf("/name", 0) != -1) {
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
                else if (f.selectionStart || f.selectionStart == '0') {
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
        },
        error: function(response) {
            showAlert(response.responseText);
        }
    });

    $("#var_picker").css({ top: e.clientY, left: e.clientX });
    $("#var_picker").slideDown();
}
function doStepDelete() {
    //if there are any active drop zones on the page, deactivate them first...
    //otherwise the sortable may get messed up.
    $(".step_nested_drop_target_active").each(
        function(intIndex) {
            doDropZoneDisable($(this).attr("id"));
        }
    );


    var step_id = $("#hidStepDelete").val();
    //don't need to block, the dialog blocks.
    $("#update_success_msg").text("Updating...").show();
    $.ajax({
        async: false,
        type: "POST",
        url: "taskMethods/wmDeleteStep",
        data: '{"sStepID":"' + step_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function(msg) {
            //pull the step off the page
            $("#" + step_id).remove();

            if ($("#steps .step").length == 0) {
                $("#no_step").removeClass("hidden");
            } else {
                //reorder the remaining steps
                //BUT ONLY IN THE BROWSER... the ajax post we just did took care or renumbering in the db.
                $("#steps .step_order_label").each(
                    function(intIndex) {
                        $(this).html(intIndex + 1); //+1 because we are a 1 based array on the page
                    }
                );
            }

            $("#update_success_msg").text("Update Successful").fadeOut(2000);
        },
        error: function(response) {
            $("#update_success_msg").fadeOut(2000);
            showAlert(response.responseText);
        }
    });

    $("#hidStepDelete").val("");
}

function doStepAdd(new_step) {
    //ok this works, but we need to know if it's a new item before we override the html
    var task_id = g_task_id;
    var codeblock_name = $("#hidCodeblockName").val();
    var item = new_step.attr("id");

    //it's a new drop!
    //do the add and get the HTML
    $("#task_steps").block({ message: null });
    $("#update_success_msg").text("Adding...").show();

    $.ajax({
        async: false,
        type: "POST",
        url: "taskMethods/wmAddStep",
        data: '{"sTaskID":"' + task_id + '","sCodeblockName":"' + codeblock_name + '","sItem":"' + item + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function(response) {
        	if (response.step_id){
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
		        // if (item.indexOf('clip_') != -1)
		        //    doClearClipboard(item.replace(/clip_/, ""))
		
		        //but we will change the sortable if this command has embedded commands.
		        //you have to add the embedded command NOW, or click cancel.
		        if (item == "fn_if" || item == "fn_loop" || item == "fn_exists" || item == "fn_while") {
		            doDropZoneEnable($("#" + new_step_id + " .step_nested_drop_target"));
		        }
		        else {
		            initSortable();
		            validateStep(new_step_id);
		        }
        	}
        },
        error: function(response) {
            $("#update_success_msg").fadeOut(2000);
            showAlert(response.responseText);
        }
    });
}
function doStepReorder() {
    //get the steps from the step list
    var steparray = $('#steps').sortable('toArray');

    $("#task_steps").block({ message: null });
    $("#update_success_msg").text("Updating...").show();

    $.ajax({
        async: false,
        type: "POST",
        url: "taskMethods/wmReorderSteps",
        data: '{"sSteps":"' + steparray + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function(msg) {
            //renumber the step widget labels
            $("#steps .step_order_label").each(
                function(intIndex) {
                    $(this).html(intIndex + 1); //+1 because we are a 1 based array on the page
                }
            );

            $("#task_steps").unblock();
            $("#update_success_msg").text("Update Successful").fadeOut(2000);
        },
        error: function(response) {
            $("#update_success_msg").fadeOut(2000);
            showAlert(response.responseText);
        }
    });
}

function doStepDetailUpdate(field, step_id, func, xpath) {
    if ($("#step_update_array").length > 0) {
        //get the value ready to be shipped via json
        //since some steps can have complex script or other sql, there
        //are special characters that need to be escaped for the JSON data.
        //on the web service we are using the actual javascript unescape to unpack this.
        var val = packJSON($("#" + field).val());
        
        $.ajax({
            async: false,
            type: "POST",
            url: "taskMethods/wmUpdateStep",
            data: '{"sStepID":"' + step_id + '","sFunction":"' + func + '","sXPath":"' + xpath + '","sValue":"' + val + '"}',
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(msg) {
                $("#task_steps").unblock();
                $("#update_success_msg").text("Update Successful").fadeOut(2000);
            },
            error: function(response) {
                $("#update_success_msg").fadeOut(2000);
                showAlert(response.responseText);
            }
        });

        //clear out the div of the stuff we just updated!
        $("#step_update_array").empty()
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
        container = "#" + in_element_id + ":not(.step_skip)"; //no space before :not
    else
        container = "#steps li:not(.step_skip)";

    //check required fields and alert
    var err_cnt = 0;

    $(container + " :input[is_required='true']").each(
        function(intIndex) {
            var step_id = $(this).attr("step_id");
            var msg = "Missing required value.";

            //clear syntax error list
            $("#info_" + step_id + " .info_syntax_errors").html("");

            //how many errors on this step?
            err_cnt = $(container + " :input[step_id='" + step_id + "']").filter(container + " :input[is_required='true']").filter(container + " :input[value='']").length;

            if ($(this).val() == "") {
                if ($("#info_" + step_id).length == 0) {
                    $("#" + step_id).prepend(drawStepValidationBar(step_id, err_cnt, ''));
                } else {
                    $("#info_" + step_id + " .info_error_count").text(err_cnt);
                }

                $("#info_" + step_id + " .info_syntax_errors").append("<div>* " + msg + "</div>");
                $(this).addClass("is_required");
            }
            else {
                $(this).removeClass("is_required");

                //only remove the popup if there are no remaining errors on the step
                if (err_cnt == 0) {
                    $("#info_" + step_id).remove();
                }
            }
        }
    );

    //check syntax errors and alert
    //if ($("#" + combined_id).length == 0) {
    $(container + " :input[syntax]").each(function(intIndex) {
        var step_id = $(this).attr("step_id");
        var syntax = $(this).attr("syntax");
        var field_value = $(this).val();

        var syntax_error;
        if (syntax != "") {
            syntax_error = checkSyntax(syntax, field_value);
        }

        if (syntax_error != "") {
            //increment the error counter
            err_cnt += 1;

            if ($("#info_" + step_id).length == 0) {
                $("#" + step_id).prepend(drawStepValidationBar(step_id, err_cnt, syntax_error));
            } else {
                $("#info_" + step_id + " .info_error_count").text(err_cnt);
            }

            $("#info_" + step_id + " .info_syntax_errors").append("<div>* " + syntax_error + "</div>");
            $(this).addClass("is_required");
        }
        else {
            $(this).removeClass("is_required");
        }
    });
    // }

}

function drawStepValidationBar(step_id, cnt, msg) {
    return "<div id=\"info_" + step_id.toString() + "\" class=\"step_validation_template\">" +
        "<img src=\"static/images/icons/status_unknown_16.png\" alt=\"\" />" +
        "The following Command has <span class=\"info_error_count\">" + cnt.toString() +
        "</span> item(s) needing attention." +
        "<div class=\"info_syntax_errors\"></div>" +
        "</div>";
}