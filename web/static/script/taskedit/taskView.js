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

//some code is shared between taskEdit and taskView pages.  That shared code is in this file.
//because we dont' want to include taskEdit.js all over the place, it's full of stuff specific to that page.

$(document).ready(function () {
    //used a lot
    g_task_id = getQuerystringVariable("task_id");

    //jquery buttons
    $("#asset_search_btn").button({ icons: { primary: "ui-icon-search"} });

    //asset, print and show log links
    //the print link
    $("#print_link").live("click", function () {
        var url = "taskPrint?task_id=" + g_task_id;
        openWindow(url, "taskPrint", "location=no,status=no,scrollbars=yes,resizable=yes,width=800,height=700");
    });

    //the show log link
    $("#show_log_link").button({ icons: { primary: "ui-icon-document"} });
    $("#show_log_link").click(function () {
        ShowLogViewDialog(3, g_task_id, true);
    });

    //the show runlog link
    $("#show_runlog_link").button({ icons: { primary: "ui-icon-document"} });
    $("#show_runlog_link").click(function () {
        var url = "taskRunLog?task_id=" + g_task_id;
        openWindow(url, "TaskRunLog" + g_task_id, "location=no,status=no,scrollbars=yes,resizable=yes,width=800,height=700");
    });
});

function tabWasClicked(tab) {
    //load on this page is taking too long.  So, we'll get the tab content on click instead.
    //NOTE: shared on several pages, so there might be some cases here that don't apply to all pages.
    //not a problem, they just won't be hit.

    if (tab == "parameters") {
        doGetParams("task", g_task_id);
    } else if (tab == "versions") {
        doGetVersions();
    } else if (tab == "schedules") {
    	doGetPlans();
    } else if (tab == "registry") {
        GetRegistry($("#hidOriginalTaskID").val());
    } else if (tab == "tags") {
        GetObjectsTags($("#hidOriginalTaskID").val());
    } else if (tab == "clipboard") {
        doGetClips();
    } else if (tab == "debug") {
        doGetDebug();
    } else if (tab == "details") {
        doGetDetails();
    }
}

function doGetPlans() {
    $.ajax({
        async: true,
        type: "POST",
        url: "uiMethods/wmGetActionPlans",
        data: '{"sTaskID":"' + g_task_id + '","sActionID":"","sEcosystemID":""}',
        contentType: "application/json; charset=utf-8",
        dataType: "html",
        success: function (response) {
        	if (response == "") {
        		$("#div_schedules #toolbox_plans").html("No Active Plans");
    		} else {
            	$("#div_schedules #toolbox_plans").html(response);

			    //click on an action plan in the toolbox pops the dialog AND the inner dialog
			    $("#div_schedules #toolbox_plans .action_plan_name").click(function () {
			        var task_name = $("#ctl00_phDetail_lblTaskNameHeader").html() + " - " + $("#ctl00_phDetail_lblVersionHeader").html();
			        var asset_id = $("#ctl00_phDetail_txtTestAsset").attr("asset_id");
			
			        var args = '{"task_id":"' + g_task_id + '", "task_name":"' + task_name + '", "debug_level":"4"}';
			        ShowTaskLaunchDialog(args);

			        ShowPlanEditDialog(this);
			    });
        	}
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
    $.ajax({
        async: true,
        type: "POST",
        url: "uiMethods/wmGetActionSchedules",
        data: '{"sTaskID":"' + g_task_id + '","sActionID":"","sEcosystemID":""}',
        contentType: "application/json; charset=utf-8",
        dataType: "html",
        success: function (response) {
        	if (response == "") {
        		$("#div_schedules #toolbox_schedules").html("No Active Schedules");
    		} else {
	            $("#div_schedules #toolbox_schedules").html(response);

	            //schedule icon tooltips
	            $("#div_schedules #toolbox_schedules .schedule_tip").tipTip({
	                defaultPosition: "right",
	                keepAlive: false,
	                activation: "hover",
	                maxWidth: "500px",
	                fadeIn: 100
	            });
	            
                //click on a schedule in the toolbox - pops the edit dialog and the inner dialog
				$("#div_schedules #toolbox_schedules .schedule_name").click(function () {
			        var task_name = $("#ctl00_phDetail_lblTaskNameHeader").html() + " - " + $("#ctl00_phDetail_lblVersionHeader").html();
			        var asset_id = $("#ctl00_phDetail_txtTestAsset").attr("asset_id");
			
			        var args = '{"task_id":"' + g_task_id + '", "task_name":"' + task_name + '", "debug_level":"4"}';
			        ShowTaskLaunchDialog(args);

				    ShowPlanEditDialog(this);
				});

			}
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

