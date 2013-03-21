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
	GetData();

	//the hook for the 'show log' link
	$("#show_log_link").click(function() {
		ShowLogViewDialog(1, '', true);
	});

	$("#logfile_dialog").dialog({
		autoOpen : false,
		height : 600,
		width : 850,
		bgiframe : true,
		buttons : {
			OK : function() {
				$(this).dialog("close");
			}
		}
	});

	// the component log links
	$(".view_component_log").live("click", function() {
		component = $(this).attr("component");

		if (component == '')
			return;

		var response = catoAjax.getProcessLogfile(component);
		if (response) {
			$("#logfile_text").html(unpackJSON(response));
			$("#logfile_dialog").dialog("open");
		}
	});

	//this page updates every 30 seconds
	setInterval("GetData()", 30000);
});

function GetData() {
	ajaxGet("uiMethods/wmGetSystemStatus", function(response) {
		$("#processes").html(response.processes);
		$("#users").html(response.users);
		$("#messages").html(response.messages);

		initJtable(true, true);
	});
}

