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

$(document).ready(function () {
	GetItems();
    ManagePageLoad();
});

function GetItems() {
    status = getQuerystringVariable("status");
	search = $("#txtSearch").val();
	from = $("#txtStartDate").val();;
	to = $("#txtStopDate").val();
	records = $("#txtResultCount").val();

    $.ajax({
        type: "POST",
        async: true,
        url: "taskMethods/wmGetTaskInstances",
        data: '{"sSearch":"' + search + '", "sFrom":"' + from + '", "sTo":"' + to + '", "sRecords":"' + records + '", "sStatus":"' + status + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "html",
        success: function (response) {
            $("#instances").html(response);
            //gotta restripe the table
            initJtable(true, true);

		    // where to go on row click
		    $(".selectable").click(function () {
		    	var id = $(this).parent().attr("task_instance");
		        openDialogWindow('taskRunLog?task_instance=' + id, 'TaskRunLog' + id, 950, 750, 'true');
		    });

		    $(".task_edit_btn").click(function (event) {
			    event.stopPropagation()
		        location.href='taskEdit?task_id=' + $(this).attr("task_id");
		    });

        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}
