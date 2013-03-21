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
	//any page that includes this script will get the following dialog inner code
	//but the page requires a placeholder div... called "log_view_dialog"
	var d = 'Filter: <input type="text" id="log_view_dialog_search" />' + '<span># of Results <input id="log_view_dialog_records" /></span>' + '<br /><span style="z-index: 1200;">Begin Date<input id="log_view_dialog_from" class="datepicker" /></span>' + '<span style="z-index: 1200;">End Date<input id="log_view_dialog_to" class="datepicker" /></span>' + '<span id="log_search_btn">Search</span>' + '<table class="jtable" cellspacing="1" cellpadding="1" width="100%" style="font-size: 0.8em;">' + '<thead><tr>' + '<th width="125px">Date</th>' + '<th width="100px">User</th>' + '<th>Log</th>' + '</tr></thead>' + '<tbody id="log_view_dialog_results">' + '</tbody>';

	$("#log_view_dialog").prepend(d);

	//init the datepickers
	$(".datepicker").datepicker({
		clickInput : true
	});

	//init the dialogs
	$("#log_view_dialog").dialog({
		autoOpen : false,
		modal : true,
		height : 650,
		width : 900,
		open : function(event, ui) {
			$(".ui-dialog-titlebar-close", ui).hide();
		},
		buttons : {
			"Close" : function() {
				CloseLogViewDialog();
			}
		}
	});

	$("#log_search_btn").button({
		icons : {
			primary : "ui-icon-search"
		}
	});
	$("#log_search_btn").click(function() {
		GetLog();
	});

});

function ShowLogViewDialog(type, id, prefill) {
	g_log_object_id = id;
	g_log_object_type = type;
	$("#log_view_dialog").dialog("open");

	if (prefill) {
		GetLog();
	}
}

function CloseLogViewDialog() {
	$("#log_view_dialog").dialog("close");
	$("#log_view_dialog_results").empty();
	$('#log_view_dialog :input').each(function() {
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

	return false;
}

function GetLog() {
	$("#log_view_dialog_results").empty();

	args = {}
	args.sObjectID = g_log_object_id;
	args.sObjectType = g_log_object_type;
	args.sSearch = $("#log_view_dialog_search").val();
	// will come from the pickers.
	args.sFrom = $("#log_view_dialog_from").val();
	;
	args.sTo = $("#log_view_dialog_to").val();
	args.sRecords = $("#log_view_dialog_records").val();

	var response = catoAjax.getLog(args);
	if (response) {
		//spin the json and build a table
		$.each(response.log, function() {
			$("#log_view_dialog_results").append("<tr><td nowrap>" + this[0] + "</td><td>" + unpackJSON(this[1]) + "</td><td>" + unpackJSON(this[2]) + "</td></tr>");
		});
		initJtable(true, false);
	}
}