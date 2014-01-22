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

//dynamic field validation based on custom xhtml tags
$(document).ready(function() {
	$(document).on("keypress", ":input[validate_as='number']", function(e) {
		return restrictEntryToNumber(e, this);
	});
	$(document).on("keypress", ":input[validate_as='posint']", function(e) {
		return restrictEntryToPositiveInteger(e, this);
	});
	$(document).on("keypress", ":input[validate_as='posnum']", function(e) {
		return restrictEntryToPositiveNumber(e, this);
	});
	$(document).on("keypress", ":input[validate_as='variable']", function(e) {
		return restrictEntryCustom(e, this, /[\[\]a-zA-Z0-9_\-,]/);
	});
	$(document).on("keypress", ":input[validate_as='identifier']", function(e) {
		return restrictEntryToIdentifier(e, this);
	});
	$(document).on("keypress", ":input[validate_as='email']", function(e) {
		return restrictEntryToEmail(e, this);
	});
	$(document).on("keypress", ":input[validate_as='username']", function(e) {
		return restrictEntryToUsername(e, this);
	});
	$(document).on("keypress", ":input[validate_as='hostname']", function(e) {
		return restrictEntryToHostname(e, this);
	});
	$(document).on("keypress", ":input[validate_as='tag']", function(e) {
		return restrictEntryToTag(e, this);
	});

	// PROPRIETARY VALIDATIONS
	//These validations are specific to certain fields and business logic.
	//but we still wanted to handle and process them the same as more typical validations

	//an example of specific validation for handling a special case
	$(document).on("keypress", ":input[validate_as='my_special_case']", function(e) {
		//do logic here...

		//then
		return;
	});
});

function checkFieldConstraints($ctl, append_to_parent) {
	var msgs = [];
	var val = $ctl.val();
	var intRegex = /^\d+$/;

	//test the regex pattern
	if ($ctl.attr("constraint")) {
		var rx = $ctl.attr("constraint");
		var patt = new RegExp("^" + rx + "$", "g");

		if (!patt.test(val)) {
			msgs.push($ctl.attr("constraint_msg"));
		}
	}

	//minlength check
	if ($ctl.attr("minlength")) {
		var ml = $ctl.attr("minlength");
		if (intRegex.test(ml)) {
			if (val.length < parseInt(ml)) {
				msgs.push("Value must be at least " + ml + " characters long.");
			}
		}
	}

	//maxvalue check - only applies to numerics
	if ($ctl.attr("maxvalue")) {
		var max = $ctl.attr("maxvalue");
		if (intRegex.test(max) && intRegex.test(val)) {
			if (parseInt(val) > parseInt(max)) {
				msgs.push("Value cannot be greater than " + max + ".");
			}
		}
	}

	//minvalue check - only applies to numerics
	if ($ctl.attr("minvalue")) {
		var min = $ctl.attr("minvalue");
		if (intRegex.test(max) && intRegex.test(val)) {
			if (parseInt(val) < parseInt(min)) {
				msgs.push("Value cannot be less than " + min + ".");
			}
		}
	}

	return msgs;
}

//some validations are not on a keypress basis, rather should happen on the blur event.
//these funcs are called based on field type from the onStepFieldChange function.

//this is the main function that determines how to test the syntax
function checkSyntax(syntax, strtocheck) {
	var msg = "";

	if (syntax !== "") {
		switch (syntax) {
			case "asset_name_or_var":
				if (strtocheck !== "") {
					// 2011-10-11 - PMD - removing asset name check for new connection command, issue #40
					//msg = validateAssetNameOrVar(strtocheck);
					//if (msg && msg !== "")
					//    return msg;
				}
				break;
			case "variable":
				if (strtocheck !== "") {
					msg = validateVariable(strtocheck);
					if (msg && msg !== "")
						return msg;
				}
				break;
			case "cmd_line":
				if (strtocheck !== "") {
					msg = validateCommandLine(strtocheck);
					if (msg && msg !== "")
						return msg;
				}
				break;
		}
	}

	return "";
}

// function validateAssetNameOrVar(name) {
// //first, is it a variable?
// if (name.indexOf('[') > -1 || name.indexOf(']') > -1) {
// //someone typed a bracket, they must have meant for this to be a variable.
// //so, do the end braces match?
// if (/\[\[.*]\]/.test(name)) {
// return "";
// }
// }
//
// //nope...
//
// //will do some ajax here to test the name in the db since it isn't a [[var]]
// var asset_id = "";
//
// $.ajax({
// async: false,
// type: "POST",
// url: "taskMethods.asmx/wmGetAssetIDFromName",
// data: '{"sName":"' + name + '"}',
// contentType: "application/json; charset=utf-8",
// dataType: "json",
// success: function(retval) {
// //the web method returned the ID if it exists.
// if (retval.d !== null)
// asset_id = retval.d;
// },
// error: function(response) {
// showAlert(response.responseText);
// return "";
// }
// });
//
// if (asset_id.length === 36)  //guids are 36 chars long
// return "";
//
// return "Entry must be a valid Asset Name, or a [[variable]].";
// }
function validateVariable(name) {
	if (name.indexOf('[') > -1 || name.indexOf(']') > -1) {
		//someone typed a bracket, they must have meant for this to be a variable.
		//so, do the end braces match?
		if (/\[\[.*]\]/.test(name)) {
			return "";
		}
	}

	return "Entry must be a [[variable]].";
}

function validateCommandLine(name) {
	var trimmed = $.trim(name);
	if (trimmed.length < name.length) {
		return "Command has whitespace or newlines at the beginning or end.";
	}
}
