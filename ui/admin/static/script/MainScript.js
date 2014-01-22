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

//This file contains common functions use throughout the main web application.  Changes made in this
//file will have global impact, so please be careful.

//GLOBALS
"use strict";

//Certain pages eval additional scripts for add-on features.
function getScript(script_name) {
	if (script_name) {
		$.ajax({
			async : false,
			type : "POST",
			url : "uiMethods/wmGetScript",
			data : '{"sScriptName":"' + script_name + '"}',
			contentType : "application/json; charset=utf-8",
			dataType : "script",
			error : function(response) {
				showAlert(response.responseText);
			}
		});
	}
}

//used in many places where we send strings as json data, replaces the two critical json chars " and \
//THESE CALL a jQuery plugin
function packJSON(instr) {
	//if it's empty or undefined, return ""
	if (instr === "" || instr === undefined || instr === null)
		return "";

	if (instr.length < 1)
		return "";

	//NOTE! base64 encoding still has a couple of reserved characters so we explicitly replace them AFTER
	var outstr = $.base64.encode(instr);
	return outstr.replace(/\//g, "%2F").replace(/\+/g, "%2B");
}

function unpackJSON(instr) {
	//if it's nothing, return a cleaner nothing
	if (instr === "" || instr === undefined || instr === null) {
		return "";
	}

	if (instr.length < 1)
		return "";

	//NOTE! base64 decoding still has a couple of reserved characters so we explicitly replace them BEFORE
	var outstr = instr.replace(/%2F/g, "/").replace(/%2B/g, "+");
	return $.base64.decode(outstr);
}

//decode a url encoded string
function urldecode(str) {
	return decodeURIComponent((str + '').replace(/\+/g, '%20'));
}

//encode a string with url encoding
function urlencode(str) {
	return encodeURIComponent((str + '').replace(/\%20/g, '+'));
}

//this is a debugging function.
function printClickEvents(ctl) {
	var e = ctl.data("events").click;
	$.each(e, function(key, handlerObj) {
		console.log(handlerObj.handler);
		// prints "function() { console.log('clicked!') }"
	});
}

function printKeypressEvents(ctl) {
	var e = ctl.data("events").keypress;
	$.each(e, function(key, handlerObj) {
		console.log(handlerObj.handler);
		// prints "function() { console.log('clicked!') }"
	});
}

//this function shows the "please wait" blockui effect.
function showPleaseWait(msg) {
	msg = ((msg === "" || msg === undefined) ? "Please Wait ..." : msg);
	$.blockUI({
		message : msg,
		css : {
			'background-repeat' : 'no-repeat',
			'padding-top' : '6px',
			'border-radius' : '10px'
		},
		overlayCSS : {
			'backgroundColor' : '#C0C0C0',
			'opacity' : '0.6'
		}
	});
}

function hidePleaseWait() {
	$.unblockUI();
	document.body.style.cursor = 'default';
}

//PROTOTYPES
String.prototype.replaceAll = function(s1, s2) {
	return this.split(s1).join(s2);
};
//SET UP ANY INSTANCES OF our "jTable" ... striped and themed
function initJtable(stripe, hover) {
	stripe = ((stripe === "" || stripe === undefined) ? false : true);
	hover = ((hover === "" || hover === undefined) ? false : true);

	//Theme the tables with jQueryUI
	$(".jtable th").each(function() {
		$(this).addClass("col_header");
	});
	$(".jtable td").each(function() {
		$(this).addClass("row");
	});

	if (hover) {
		$(".jtable tr").hover(function() {
			$(this).children("td").addClass("row_over");
		}, function() {
			$(this).children("td").removeClass("row_over");
		});
	}
	//    $(".jtable tr").click(function () {
	//        $(this).children("td").toggleClass("ui-state-highlight");
	//    });
	if (stripe) {
		$('.jtable tr:even td').addClass('row_alt');
	}

	// make it sortable, if the headers are defined to be
	makeSortable($(".jtable"));
}

//THESE FUNCTION SWITCH from web formatting (<br>, &nbsp;, etc) into text formatting (\n, \t, etc)
function formatHTMLToText(s) {
    var replaceWith = '';
    var replaceFrom = '';
	//firefox (moz) uses carriage returns in text areas, IE uses newlines AND carriage returns.
	if ( typeof (screenTop) !== "undefined") {
		replaceFrom = '\r';
	} else {
		replaceFrom = '\n';
	}// why?  Only IE defines screenTop, and only IE needs \r.
	s = s.replaceAll('<br />', replaceWith);
	s = s.replaceAll('<br>', replaceWith);
	s = s.replaceAll('<BR>', replaceWith);
	s = s.replaceAll('&nbsp;&nbsp;&nbsp;&nbsp;', '\t');

	return s;
}

function formatTextToHTML(s) {
	return s.replaceAll('\n', '<br />').replaceAll(' ', '&nbsp;').replaceAll('\t', '&nbsp;&nbsp;&nbsp;&nbsp;');
}

//will scroll a page to the ID specified
function jumpToAnchor(anchor) {
	//here's what I'm doing... if the parent of me is "content_te"
	//which is a special scrolling div in the app... scroll it.
	//otherwise just try to scroll the page.

	var new_position = $('#' + anchor).offset();

	if ($("#content_te").length > 0) {
		$("#content_te").scrollTo($('#' + anchor));
	} else {
		$.scrollTo($('#' + anchor));
	}

	return false;
}

//Update a application setting...
function updateSetting(category, setting, value) {
	var response = ajaxPost("uiMethods/wmSetApplicationSetting", {
		"sCategory" : category,
		"sSetting" : setting,
		"sValue" : value
	}, "text");
}

//------------------------------------------------------------
//Generic functions
function getQuerystringVariable(variable) {
	var querystring = location.search.substring(1);
	var vars = querystring.split("&");
	for (var i = 0; i < vars.length; i++) {
		var pair = vars[i].split("=");
		if (pair[0] === variable) {
			return pair[1];
		}
	}
	return "";
}

function AreYouSure() {
	if (window.confirm('Are you sure you want to delete this item?')) {
		return true;
	}
	return false;
}

//------------------------------------------------------------
//These are data entry validation functions.

function restrictEntryToSafeHTML(e, field) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (c === '<' || c === '>')
		return false;

	return true;
}

function restrictEntryToIdentifier(e, field) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (/[a-zA-Z0-9_\-]/.test(c)) {
		return true;
	}

	return false;
}

function restrictEntryToIdentifierUpper(e, field) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (/[A-Z0-9_\-]/.test(c)) {
		return true;
	} else {
		if (/[a-z]/.test(c)) {
			field.value += c.toUpperCase();
		}
		return false;
	}
}

function restrictEntryToUsername(e, field) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (/[\\a-zA-Z0-9_.@\-]/.test(c)) {
		return true;
	} else {
		return false;
	}
}

function restrictEntryToEmail(e, field) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (/[a-zA-Z0-9_.@,\-]/.test(c)) {
		return true;
	} else {
		return false;
	}
}

function restrictEntryToHostname(e, field) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (/[a-zA-Z0-9_.\-]/.test(c)) {
		return true;
	} else {
		return false;
	}
}

function restrictEntryToNumber(e, field) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (/[0-9.\-]/.test(c)) {
		//if user pressed '.', and a '. exists in the string, cancel
		if (c === '.' && field.value.indexOf('.') !== -1)
			return false;

		//if there is anything in the field and user pressed '-', cancel.
		if (c === '-' && field.value.length > 0)
			return false;

		return true;
	}
	return false;
}

function restrictEntryToInteger(e, field) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (/[0-9\-]/.test(c)) {
		//if there is anything in the field and user pressed '-', cancel.
		if (c === '-' && field.value.length > 0)
			return false;

		return true;
	}
	return false;
}

function restrictEntryToPositiveNumber(e, field) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (/[0-9.]/.test(c)) {
		//if user pressed '.', and a '. exists in the string, cancel
		if (c === '.' && field.value.indexOf('.') !== -1)
			return false;

		return true;
	}
	return false;
}

function restrictEntryToPositiveInteger(e, field) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (/[0-9]/.test(c)) {
		return true;
	}
	return false;
}

function restrictEntryToTag(e, field) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (/[a-zA-Z0-9_.\-@#&]/.test(c)) {
		return true;
	} else {
		return false;
	}
}

function restrictEntryCustom(e, field, regex) {
	var c = whatKey(e);
	if (!c) {
		return true;
	}

	if (regex.test(c)) {
		return true;
	}
	return false;
}

function whatKey(e) {
	//this will return the actual character IF it was a character key
	//if not, it will return ~#, where # is the key code
	//so, pressing an 'n' will return n
	//and pressing backspace will return ~8

	//this way we can write code to test against the differences

	//OF COURSE, stymied again by Microsoft...
	//charCode is not recognized by IE...
	//but it is a way in FF to tell character keys from action keys

	if (e.which === null) {
		return String.fromCharCode(e.keyCode);
		// IE
	} else if (e.which !== 0 && e.charCode !== 0) {
		return String.fromCharCode(e.which);
		// the rest
	} else {
		return null;
		// special key
	}
}

//SIZE OF SCREEN FUNCTIONS
function getScreenCenteredTop(eh) {
	var h = screen.height;
	return (h - eh) / 2;
}

function getScreenCenteredLeft(ew) {
	var w = screen.width;
	return (w - ew) / 2;
}

//------------------------------------------------------------
//These are the window open functions.  They will update a window if one exists with
//the same name.
//openMaxWindow - opens a maximized window.
//openDialogWindow - opens a small dialog window, centered on the screen.
//openWindow - Allows full control of window options.
//TODO...
//Add functions with a _New suffix use a random number
//to ensure that the window name is unique.  This will create a new window every time.

function openMaxWindow(aURL, aWinName) {
	var wOpen;
	var sOptions;

	sOptions = 'status=no,menubar=no,scrollbars=yes,resizable=yes,toolbar=no';
	sOptions = sOptions + ',width=' + screen.width + ',height=' + screen.height + ',top=0,left=0';

	wOpen = window.open(aURL, aWinName, sOptions);
	wOpen.focus();
}

function openDialogWindow(aURL, aWinName, w, h, scroll) {
	var wOpen;
	var sOptions;

	var sc = (scroll === 'yes' || scroll === 'true') ? sc = 'yes' : sc = 'no';
	var t = getScreenCenteredTop(h);
	var l = getScreenCenteredLeft(w);

	sOptions = 'location=no,titlebar=no,status=no,menubar=no,resizable=yes,toolbar=no,scrollbars=' + sc;
	sOptions = sOptions + ',width=' + w + ',height=' + h + ',left=' + l + ',top=' + t;

	wOpen = window.open(aURL, aWinName, sOptions);
	wOpen.focus();
}

function openWindow(URLtoOpen, windowName, windowFeatures) {
	var wOpen = window.open(URLtoOpen, windowName, windowFeatures);
	wOpen.focus();
}

// This function can sort enable sorting html table on the provided columns
// works on any column header with the class "sortable"
function makeSortable(table) {
	$(".sortable").wrapInner('<span title="click to sort"/>').each(function() {

		var th = $(this), thIndex = th.index(), inverse = false;

		th.click(function() {

			table.find('td').filter(function() {

				return $(this).index() === thIndex;

			}).sortElements(function(a, b) {

				return $.text([a]) > $.text([b]) ? inverse ? -1 : 1 : inverse ? 1 : -1;

			}, function() {

				// parentNode is the element we want to move
				return this.parentNode;

			});

			inverse = !inverse;

		});

	});
}
