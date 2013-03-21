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
	//was there a directive to show a specific module?  click it!
	var module = getQuerystringVariable("module");
	if (module != "") {
		if ($("#" + module).length != 0) {
			$("#" + module).addClass("group_tab_selected");
			$("#div_" + module + "_detail").removeClass("hidden");
		}
	}

	$(".group_tab").click(function() {
		//style tabs
		$(".group_tab").removeClass("group_tab_selected");
		$(this).addClass("group_tab_selected");

		var module = $(this).attr("id");
		var module_div = "#div_" + module + "_detail";

		//hide 'em all
		$("#content .detail_panel").addClass("hidden");
		//show the one you clicked
		$(module_div).removeClass("hidden");

	});

	$(".save_btn").button({
		icons : {
			primary : "ui-icon-disk"
		}
	});
	$(".save_btn").click(function() {
		SaveSettings($(this).attr("module"));
	});

	GetSettings();
});

function GetSettings() {
	var settings = catoAjax.getSettings();
	if (settings) {
		try {
			//so, we're gonna try to spin through the settings json and put any values in the appropriate fields.
			//this expects the receiving input element to have the same 'id' as the json property
			for (modulename in settings) {
				mod_settings = settings[modulename];
				for (key in mod_settings) {
					var value = mod_settings[key].toString();
					//cast to a string for booleans
					var selector = "#div_" + modulename.toLowerCase() + "_detail #" + key;
					var $ctl = $(selector)

					var type = $ctl.get(0).tagName.toLowerCase();
					var typeattr = $ctl.attr("type");

					if (type == "input") {
						if (typeattr == "checkbox") {
							if (value == "true" || value > 0)
								$ctl.attr("checked", "checked");
							else
								$ctl.removeAttr("checked");
						} else {
							$ctl.val(value);
						}
					} else {
						$ctl.val(value);
					}
					//console.log(selector);
					//console.log("Set " + modulename + ":" + key + " to " + value);
				}
			}
		} catch (ex) {
			alert(ex.message + "\nProbably a mismatched html input field/json attribute name");
		}
	}
}

//THIS SHOULD just be one function
//in fact, I still wanna put all this in one table.
function SaveSettings(type) {
	args = $("#div_" + type + "_detail :input").serializeArray()

	/* Because serializeArray() ignores unset checkboxes and radio buttons: */
	args = args.concat($("#div_" + type + "_detail :input[type=checkbox]:not(:checked)").map(function() {
		// NOT checked is 'off'
		return {
			"name" : this.name,
			"value" : "off"
		}
	}).get());

	var response = catoAjax.saveSettings(type, args);
	if (response) {
		$("#update_success_msg").text("Save Successful").fadeOut(2000);
	}
}