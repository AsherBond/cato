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

$(document).ready(function() {
    initJtable(true, true);

	//Page updates counts every 30 seconds
	window.setInterval(getStatuses, 30000);

	getStatuses();
});

function getStatuses() {
    $.ajax({
        type: "POST",
        async: true,
        url: "taskMethods/wmGetTaskStatusCounts",
        data: '',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
        	//the results is a json with each summary count.  Stick 'em where they belong.
            $("#lblProcessing").html(response.Processing);
            $("#lblSubmitted").html(response.Submitted);
            $("#lblStaged").html(response.Staged);
            $("#lblAborting").html(response.Aborting);
            $("#lblPending").html(response.Pending);
            $("#lblQueued").html(response.Queued);
            $("#lblActive").html(response.TotalActive);
            $("#lblCancelled").html(response.Cancelled);
            $("#lblCompleted").html(response.Completed);
            $("#lblErrored").html(response.Errored);
            $("#lblTotalCompleted").html(response.TotalComplete);
            $("#lblAllStatuses").html(response.AllStatuses);

		    // where to go when you click on a summary row
		    $(".selectAutoTask").click(function() {
		        location.href = 'taskActivityLog?status=' + $(this).attr("status");
		    });
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}