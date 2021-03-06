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
	$("#format_xml_btn").button({
		icons : {
			primary : "ui-icon-shuffle"
		}
	});
	$("#format_xml_btn").click(function() {
		bad = $("#xml_to_import").val();
		good = vkbeautify.xml(bad);
		$("#xml_to_import").val(good);
	});

	$("#import_from_url").keypress(function(e) {
		if (e.which === 13) {
			GetURL();
		}
	});

	$("#url_load_btn").click(function() {
		GetURL();
	});

	$("#import_xml_btn").button({
		icons : {
			primary : "ui-icon-check"
		}
	});
	$("#import_xml_btn").click(function() {
		var import_text = packJSON($("#xml_to_import").val());
		var on_conflict = $("#on_conflict").val();
		if (import_text) {
			var response = ajaxPost("uiMethods/wmCreateObjectFromXML", {
				import_text : import_text,
				on_conflict : on_conflict
			});
			if (response) {
				if (response.error) {
					showAlert(response.error);
					return;
				}
				var infomsg = "";
				$.each(response.items, function(index, item) {
					if (item.info) {
						infomsg += item.type + " : " + item.name + " : <span class='ui-state-highlight' style='font-size: 0.8em;'>" + item.info + "</span><br />";
					} else {
						var url = "";
						if (item.type === "task")
							url = "taskEdit?task_id=" + item.id;

						infomsg += "Click <a href='" + url + "'>here</a> to edit " + item.name + "<br />";
					}
				});

				infomsg += "<br /><br />Click <a href='taskManage'>here</a> to manage Tasks.<br />";

				showInfo("Results", infomsg, {
                    sticky : true
                });

				// temporary comment $("#xml_to_import").val("");
			}
		}
	});

	$("#analyze_btn").button({
		icons : {
			primary : "ui-icon-search"
		}
	});
	$("#analyze_btn").click(function() {
		var import_text = packJSON($("#xml_to_import").val());
        var on_conflict = $("#on_conflict").val();
		if (import_text) {
			ajaxPostAsync("uiMethods/wmAnalyzeImportXML", {
				import_text : import_text,
                on_conflict : on_conflict
			}, function(response) {
				if (response.error) {
					showAlert(response.error);
					return;
				}
				var infomsg = "";
				$.each(response.items, function(index, item) {
					if (item.info) {
						infomsg += "<p>" + item.type + " : " + item.name + "<br /><span class='ui-state-highlight' style='font-size: 0.8em; padding-left: 10px;'>" + item.info + "</span><br />";
					}
					var url = "taskEdit?task_id=" + item.id;
					infomsg += "<span style='font-size: 0.8em; padding-left: 10px;'>Click <a href='" + url + "'>here</a> to edit " + item.name + ".</span><br />";
					infomsg += "</p>";
				});

				infomsg += "<br /><br />Click <a href='taskManage'>here</a> to manage Tasks.<br />";

				showInfo("Results", infomsg, {
                    sticky : true
                });

				// temporary comment $("#xml_to_import").val("");
			});
		}
	});
});

function GetURL() {
	var response = ajaxPost("uiMethods/wmHTTPGet", {
		url : $("#import_from_url").val()
	}, "text");
	if (response) {
		$("#xml_to_import").val(response);
	}
}

function fileWasSaved(filename) {
	//get the file text from the server and populate the text field.
	$.get("temp/" + filename, function(data) {
		$("#xml_to_import").val(data);
	}, "text");

	$("#import_from_url").val("");
}