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
		if(e.which == 13) { GetURL(); }
	});
	
	$("#url_load_btn").click(function() {
		GetURL();
	});

	$("#import_xml_btn").button({ icons: { primary: "ui-icon-check"} });
    $("#import_xml_btn").click(function() {
		var xml = packJSON($("#xml_to_import").val());
		if (xml) {
		    $.ajax({
		        type: "POST",
		        async: false,
		        url: "uiMethods/wmCreateObjectFromXML",
		        data: '{"sXML":"' + xml + '"}',
		        contentType: "application/json; charset=utf-8",
		        dataType: "json",
		        success: function (response) {
					try
					{
			        	if (response.error) {
		        			showAlert(response.error);
		        		} else {
							//the response is an array of items
							
							var infomsg = "";
				            $.each(response.items, function(index, item){
				            	if (item.info) {
				            		infomsg += item.type + " : " + item.name + " : <span class='ui-state-highlight' style='font-size: 0.8em;'>" + item.info + "</span><br />";
				            	} else {
			            			var url = "";
									if (item.type == "task")
										url = "taskEdit?task_id=" + item.id;
									if (item.type == "ecotemplate")
										url = "ecoTemplateEdit?ecotemplate_id=" + item.id;
			            			
			            			infomsg += "Click <a href='" + url + "'>here</a> to edit " + item.name + "<br />";
			            		}
							});
							
							infomsg += "<br /><br />Click <a href='taskManage'>here</a> to manage Tasks.<br />";
							infomsg += "Click <a href='ecotemplateManage'>here</a> to manage Ecotemplates.<br />";
							
							showInfo("Results", infomsg, true);
	
							// temporary comment $("#xml_to_import").val("");
							
						}		
					}
					catch(err)
					{
						showAlert(err);
					}
		        },
		        error: function (response) {
		            showAlert(response.responseText);
		        }
		    });
	    }
    });
});

function GetURL() {
    $.ajax({
        type: "POST",
        async: false,
        url: "uiMethods/wmHTTPGet",
        data: '{"url":"' + $("#import_from_url").val() + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "text",
        success: function (response) {
			$("#xml_to_import").val(response);
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

function fileWasSaved(filename) {
	//get the file text from the server and populate the text field.
	$.get("temp/" + filename, function(data) {
		$("#xml_to_import").val(data);
	}, "text");
	
	$("#import_from_url").val("")
}
