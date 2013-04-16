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
	//used a lot - also on different script files so be mindful of the include order
	g_task_id = getQuerystringVariable("task_id");

	//get the details
	doGetDetails();
	//params
	doGetParams("task", g_task_id, false);
	//get the commands
	doGetCommands();

});

function doGetDetails() {
	ajaxPostAsync("taskMethods/wmGetTask", {
		sTaskID : g_task_id
	}, function(task) {
		$("#lblTaskCode").text(task.Code);
		$("#lblStatus").text(task.Status);
		$("#lblDescription").text(task.Description);
		$("#lblConcurrentInstances").text(task.ConcurrentInstances);
		$("#lblQueueDepth").text(task.QueueDepth);

		//the header
		$("#lblTaskNameHeader").text(task.Name);
		$("#lblVersionHeader").text(task.Version + (task.IsDefaultVersion ? " (default)" : ""));
	});
}

function doGetCommands() {
	ajaxPostAsync("taskMethods/wmGetStepsPrint", {
		sTaskID : g_task_id
	}, function(response) {
		$("#codeblock_steps").html(response);
	}, "text");
}
