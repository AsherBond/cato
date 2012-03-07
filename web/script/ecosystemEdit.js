//Copyright 2011 Cloud Sidekick
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

//This is all the functions to support the ecosystemEdit page.

var g_eco_id;
var g_ecotemplate_id;

$(document).ready(function () {
	"use strict";

    //used a lot
    g_eco_id = $("#ctl00_phDetail_hidEcosystemID").val();
    g_ecotemplate_id = $("#ctl00_phDetail_hidEcoTemplateID").val();

    //specific field validation and masking
    $("#ctl00_phDetail_txtEcosystemName").keypress(function (e) { return restrictEntryToSafeHTML(e, this); });
    $("#ctl00_phDetail_txtDescription").keypress(function (e) { return restrictEntryToSafeHTML(e, this); });

    // when you hit enter inside one of the detail fields... do nothing
    // (this prevents accidentally posting something else)
    $("#div_details :input[te_group='detail_fields']").keypress(function (e) {
        if (e.which == 13) {
            return false;
        }
    });

    //the hook for the 'show log' link
    $("#show_log_link").button({ icons: { primary: "ui-icon-document"} });
    $("#show_log_link").click(function () {
        var url = "securityLogView.aspx?type=41&id=" + g_eco_id;
        openWindow(url, "logView", "location=no,status=no,scrollbars=yes,resizable=yes,width=800,height=700");
    });

    $("#goto_ecotemplate_btn").button({ icons: { primary: "ui-icon-arrowthick-1-ne"}, text: false });
    $("#goto_ecotemplate_btn").click(function () {
        showPleaseWait();
        location.href = 'ecoTemplateEdit.aspx?ecotemplate_id=' + g_ecotemplate_id;
    });

    $("#show_stopstorm_btn").button({ icons: { primary: "ui-icon-stop"} });
    $("#show_stopstorm_btn").click(function () {
        if (typeof(ShowStopStormDialog) != 'undefined') {
            ShowStopStormDialog(g_eco_id);
        }
    });

	//the Discovery button looks like an action category for consistency, but its' just a redirect.
    $("#discovery_btn").live("click", function () {
		location.href="awsDiscovery.aspx?ecosystem_id=" + g_eco_id;
	});
	
    //enabling the 'change' event for the Details tab
    $("#div_details :input[te_group='detail_fields']").change(function () { doDetailFieldUpdate(this); });

    //toggle actions
    $("#toolbox .action_category").live("click", function () {
        var thiscat = $(this).attr("id");

        //unselect all the categories
        $("#div_actions .action_category").removeClass("ui-state-focus action_btn_focus");
        //and select this one you clicked
        $(this).addClass("ui-state-focus action_btn_focus");

        //transfer effect
        $(this).effect("transfer", { to: $("#action_flow") }, 300, function () {
            //flow and display the buttons
            if (thiscat == "ac_all") {
                flowButtons($("#div_actions_detail .action"));
            } else {
                flowButtons($("#div_actions_detail .action[category='" + thiscat + "']"));
            }
        });

    });

    //what happens when you click on an action?
    $("#div_actions_detail .action").live("click", function () {
        $.blockUI({ message: null });


        //unselect all the actions
        $("#div_actions_detail .action").removeClass("ui-state-active");

        var action_id = $(this).attr("id");
        var task_id = $(this).attr("task_id").replace(/t_/, "");
        var task_name = $(this).attr("task_name")
        var task_version = $(this).attr("task_version")

        //since this is an "action", we'll pass the action name AND the task name, rather than bother with 
        //another goofy argument.
        task_name = $(this).attr("action") + " : (" + task_name + " - " + task_version + ")";

        //show the dialog
        //note: we are not passing account_id - the dialog will pick the default
        var args = '{"task_id":"' + task_id + '", \
            "task_name":"' + task_name + '", \
            "ecosystem_id":"' + g_eco_id + '", \
            "action_id":"' + action_id + '"}';

        //I hate that we have to occasionally do this setTimeout to get the visual effects time to work.
        setTimeout(function () {
            ShowTaskLaunchDialog(args);
        }, 250); //end timeout
    });
    
    
    //a little more detail for the storm tabs --- clicking one refreshes the content
    $(".storm_tab").click(function () {
    	var href = $(this).attr("href");
        if (href == "#storm_status_tab" || 
        	href == "#storm_events_tab" || 
    		href == "#storm_output_tab" || 
    		href == "#storm_params_tab") {
            getEcosystemLog();
        }
        
        if (href == "#storm_file_tab") {
        	//the storm file isn't part of the get_status response.
        }
    });


    //let's turn the "buttons" to behave like buttons
    //persist the "active" state on a category only! (actions pop back out)
    //    $("#div_actions_detail .action_category").live("mousedown", function (event) {
    //        $("#toolbox .action").removeClass("ui-state-active");
    //        $(this).addClass("ui-state-active");
    //    });
    //    //        $("#div_actions_detail .action_btn").live("mouseover mouseout", function (event) {
    //        if (event.type == "mouseover") $(this).addClass("ui-state-hover");
    //        else $(this).removeClass("ui-state-hover");
    //    });

    //last thing we do... get the ajax content
    getActionCategories();
    getActions();

	if (typeof(STORM) != "undefined") {
    	getEcosystemLog();
	    $("#storm_detail_tabs").tabs();
	}

});

function CloudAccountWasChanged() {
    location.href = "ecosystemManage.aspx";
}
function tabWasClicked(tab) {
	"use strict";

    //we'll be hiding and showing right side content when tabs are selected.
    //"detail" divisions have a div name like the tab, with a "_detail" suffix

    var detail_div = "#div_" + tab + "_detail";

    //hide 'em all
    $("#content_te .detail_panel").addClass("hidden");

    //do some case specific ajax calls
    if (tab == "objects") {
        getEcosystemObjectList();
    } else if (tab == "details") {
        GetRegistry(g_eco_id);
        //temporarily hidden until we enable parameters on ecosystems
        //doGetParams("ecosystem", g_eco_id);
        GetEcosystemSchedules();
    }

    //show the one you clicked
    $(detail_div).removeClass("hidden");
}

function flowButtons($selector) {
	"use strict";

    //take them out of the table, put them back into their holding div, and remove rows from the table
    $("#action_flow .action").each(function () {  //for each one in the table flow
        $(this).appendTo($("#category_actions")); //move it back to the holding div
    });
    //clear the table of any remaining rows
    $("#action_flow").empty();

    //show and flow the ones you clicked (or all if you clicked "all")
    //flow them into a two column stack...
    var col = 0;
    var row = 0;

    //flow them all
    $selector.each(function () {  //for each one about to be visible...
        var rowid = "ab" + row;
        var cellid = rowid + "_" + col;

        if (col == 0) {//it's the first of a set of 5 - add the row
            var html = "";
            html += "<tr id=\"" + rowid + "\">";
            html += "   <td id=\"" + rowid + "_0\"></td>";
            html += "   <td id=\"" + rowid + "_1\"></td>";
            html += "   <td id=\"" + rowid + "_2\"></td>";
            html += "   <td id=\"" + rowid + "_3\"></td>";
            html += "   <td id=\"" + rowid + "_4\"></td>";
            html += "</tr>";  //close the row

            //add the row to the table...
            $("#action_flow").append(html);
        }

        //move the action to the table
        $(this).appendTo($("#" + cellid));

        if (col == 4) {//it's the last of a set of 5
            col = 0; //reset the counter
            row++; //next row
        }
        else
            col++;

    });
}

//seems to work so far.
function pageLoad() {
	"use strict";

    $(".ecosystem_type").live("click", function () {
        //get the type and set it on the page.
        var drilldowntype = $(this).attr("id");
        var label = $(this).attr("label");

        $("#selected_object_type").val(drilldowntype);

        getEcosystemObject(drilldowntype, label);
    });

    $(".ecosystem_item_remove_btn").live("click", function () {
        var id_to_remove = $(this).attr("id_to_remove");
        var id_to_delete = $(this).attr("id_to_delete");
        var object_type = $("#selected_object_type").val();

        if (confirm("Are you sure?")) {
            $.ajax({
                type: "POST",
                url: "uiMethods.asmx/wmDeleteEcosystemObject",
                data: '{"sEcosystemID":"' + g_eco_id + '","sObjectType":"' + object_type + '","sObjectID":"' + id_to_delete + '"}',
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function (msg) {
                    $("#" + id_to_remove).remove();

                    //if there's nothing left, go back to the top
                    if ($("#random_content").children().length == 0)
                        getEcosystemObjectList();
                },
                error: function (response) {
                    showAlert(response.responseText);
                }
            });
        }

    });

    $(".breadcrumb").live("click", function () {
        //get the type and set it on the page.
        var drilldowntype = $(this).attr("id");
        var label = $(this).text();

        $("#selected_object_type").val(drilldowntype);

        if (drilldowntype == "top")
            getEcosystemObjectList();
        else
            getEcosystemObject(drilldowntype, label);
    });

}

function getEcosystemLog() {
	"use strict";

    $.ajax({
        type: "POST",
        url: "uiMethods.asmx/wmGetEcosystemStormStatus",
        data: '{"sEcosystemID":"' + g_eco_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            var log = jQuery.parseJSON(msg.d);
            
            //if this ecosystem doesn't have a storm_status, it's not a storm ecosystem, so hide the storm tabs
            if (log.storm_status == '') {
            	$(".storm").hide();
        	} else {
            	$(".storm").show();
        	}

            //hide the stop button if it's already stopped
            if (log.storm_status == 'Running') {
            	$("#show_stopstorm_btn").show();
        	} else {
            	$("#show_stopstorm_btn").hide();
        	}
			
            $("#storm_status").text(log.storm_status);
            $("#last_update_dt").text(log.last_update_dt);
            
			var html = "";
			//write the log table
			$.each(log.ecosystem_log, function(rowidx) {
        	    html += "<tr>";
				
				$.each(log.ecosystem_log[rowidx], function(colidx) {
					//skip the first two columns, the ascending id and the ecosystem_id.
					if (colidx < 2)
						return true;
        	    	
        	    	var val = log.ecosystem_log[rowidx][colidx];
        	    	
        	    	//only columns 5 & 6 are json packed
        	    	if (colidx == 5 || colidx == 6)
        	    		val = unpackJSON(val);
        	    		
        	    	html += "<td>" + val + "</td>";
				});
				
        	    html += "</tr>";
	        });

            $("#ecosystem_log tbody").empty();
            $("#ecosystem_log").append(html);
            
            //write the parameters table
            html = "";
			$.each(log.storm_parameters, function(rowidx) {
        	    html += "<tr>";
				
				$.each(log.storm_parameters[rowidx], function(colidx) {
        	    	var val = log.storm_parameters[rowidx][colidx];
        	    	
        	    	//only the second value is json packed
        	    	if (colidx == 1)
        	    		val = unpackJSON(val);
        	    		
        	    	html += "<td>" + val + "</td>";
				});
				
        	    html += "</tr>";
	        });

            $("#storm_parameters tbody").empty();
            $("#storm_parameters").append(html);
            
            //write the output table
            html = "";
			$.each(log.storm_output, function(rowidx) {
        	    html += "<tr>";
				
				$.each(log.storm_output[rowidx], function(colidx) {
        	    	var val = log.storm_output[rowidx][colidx];
        	    	
        	    	//second and third values are json packed
        	    	if (colidx == 1 || colidx == 2)
        	    		val = unpackJSON(val);
        	    		
        	    	html += "<td>" + val + "</td>";
				});
				
        	    html += "</tr>";
	        });

            $("#storm_output tbody").empty();
            $("#storm_output").append(html);
            
            //stripe the tables
            initJtable();
        },
        error: function (response) {
            hidePleaseWait();
            showAlert(response.responseText);
        }
    });
}

function getEcosystemObjectList() {
	"use strict";

    showPleaseWait();

    $.ajax({
        type: "POST",
        url: "uiMethods.asmx/wmGetEcosystemObjects",
        data: '{"sEcosystemID":"' + g_eco_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            $("#random_content").html(msg.d);

            //wicked! remove all breadcrumbs but me!
            $(".breadcrumb").not("#top").remove();

            hidePleaseWait();
        },
        error: function (response) {
            hidePleaseWait();
            showAlert(response.responseText);
        }
    });

}

function getEcosystemObject(drilldowntype, label) {
	"use strict";

    showPleaseWait();

    $.ajax({
        type: "POST",
        url: "uiMethods.asmx/wmGetEcosystemObjectByType",
        data: '{"sEcosystemID":"' + g_eco_id + '", "sType":"' + drilldowntype + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            $("#random_content").html(msg.d);

            //breadcrumb
            $(".breadcrumb").not("#top").last().remove();
            $("#breadcrumbs").append("<span class=\"breadcrumb\" id=\"" + drilldowntype + "\"> - " + label.replace(/ - /, "") + "<span class=\"ui-icon ui-icon-refresh floatright\"></span></span>");

            hidePleaseWait();
        },
        error: function (response) {
            hidePleaseWait();
            showAlert(response.responseText);
        }
    });

}

function doDetailFieldUpdate(ctl) {
	"use strict";

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
            async: false,
            type: "POST",
            url: "uiMethods.asmx/wmUpdateEcosystemDetail",
            data: '{"sEcosystemID":"' + g_eco_id + '","sColumn":"' + column + '","sValue":"' + value + '"}',
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (msg) {

                if (msg.d != '') {
                    $("#update_success_msg").text("Update Failed").fadeOut(2000);
                    showInfo(msg.d);
                }
                else {
                    $("#update_success_msg").text("Update Successful").fadeOut(2000);

                    // bugzilla 1037 Change the name in the header
                    if (column == "Name") { $("#ctl00_phDetail_lblEcosystemNameHeader").html(unpackJSON(value)); };
                }

            },
            error: function (response) {
                $("#update_success_msg").fadeOut(2000);
                showAlert(response.responseText);
            }
        });
    }
}

function getActionCategories() {
	"use strict";

    $.ajax({
        type: "POST",
        url: "uiMethods.asmx/wmGetEcotemplateActionCategories",
        data: '{"sEcoTemplateID":"' + g_ecotemplate_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            $("#action_categories").html(msg.d);
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}
function getActions() {
	"use strict";

    $.ajax({
        type: "POST",
        url: "uiMethods.asmx/wmGetEcotemplateActionButtons",
        data: '{"sEcoTemplateID":"' + g_ecotemplate_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (msg) {
            $("#category_actions").html(msg.d);
            flowButtons($("#div_actions_detail .action"));

            //action tooltips
            $("#div_actions_detail .action_help_btn").tipTip({
                defaultPosition: "right",
                keepAlive: false,
                activation: "hover",
                maxWidth: "500px",
                fadeIn: 100
            });

        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}
function GetEcosystemSchedules() {
	"use strict";

    $.ajax({
        async: true,
        type: "POST",
        url: "uiMethods.asmx/wmGetEcosystemSchedules",
        data: '{"sEcosystemID":"' + g_eco_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (retval) {
            $("#ecosystem_schedules").html(retval.d);
            //schedule icon tooltips
            $("#ecosystem_schedules .schedule_tip").tipTip({
                defaultPosition: "right",
                keepAlive: false,
                activation: "hover",
                maxWidth: "500px",
                fadeIn: 100
            });
		    //click on a schedule in the detail panel pops the dialog AND the inner dialog
		    $("#ecosystem_schedules .schedule_name").click(function () {
		        var action_id = $(this).parent().attr("action_id");
		        var task_id = $(this).parent().attr("task_id");
		        var task_name = $(this).parent().attr("task_name")
		        var task_version = $(this).parent().attr("task_version")
		
		        //since this is an "action", we'll pass the action name AND the task name, rather than bother with 
		        //another goofy argument.
		        task_name = $(this).parent().attr("action") + " : (" + task_name + " - " + task_version + ")";
		
		        //show the dialog
		        //note: we are not passing account_id - the dialog will pick the default
		        var args = '{"task_id":"' + task_id + '", \
		            "task_name":"' + task_name + '", \
		            "ecosystem_id":"' + g_eco_id + '", \
            		"action_id":"' + action_id + '"}';
		        
		        ShowTaskLaunchDialog(args);

		        ShowPlanEditDialog(this);
		    });
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
    $.ajax({
        async: true,
        type: "POST",
        url: "uiMethods.asmx/wmGetEcosystemPlans",
        data: '{"sEcosystemID":"' + g_eco_id + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (retval) {
            $("#ecosystem_plans").html(retval.d);

		    //click on a schedule in the detail panel pops the dialog AND the inner dialog
		    $("#ecosystem_plans .action_plan_name").click(function () {
		        var action_id = $(this).parent().attr("action_id");
		        var task_id = $(this).parent().attr("task_id");
		        var task_name = $(this).parent().attr("task_name")
		        var task_version = $(this).parent().attr("task_version")
		
		        //since this is an "action", we'll pass the action name AND the task name, rather than bother with 
		        //another goofy argument.
		        task_name = $(this).parent().attr("action") + " : (" + task_name + " - " + task_version + ")";
		
		        //show the dialog
		        //note: we are not passing account_id - the dialog will pick the default
		        var args = '{"task_id":"' + task_id + '", \
		            "task_name":"' + task_name + '", \
		            "ecosystem_id":"' + g_eco_id + '", \
            		"action_id":"' + action_id + '"}';
		        
		        ShowTaskLaunchDialog(args);

		        ShowPlanEditDialog(this);
		    });
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}
