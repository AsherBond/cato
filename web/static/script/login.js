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
g_newpw = "";

$(document).ready(function () {
    $('#txtLoginUser').focus();
    
    //if there's a 'msg' querystring, show it on a nice label
    var msg = getQuerystringVariable("msg");
    msg = urldecode(msg);
    if (msg) {
        $("#error_msg").text(msg);
        $("#loginerror").show();
    } else {
        $("#error_msg").text("");
        $("#loginerror").hide();
    }
    
	$("#username").keypress(function(e) {
		if(e.which == 13) {
			Login();
		}
	});

    $("#password_change_dialog").dialog({
        autoOpen: false,
        modal: true,
        bgiframe: false,
        buttons: {
            "OK": function () {
				Change();
            },
            Cancel: function () {
            	reset();
                $("#password_change_dialog").dialog("close");
            }
        }
    });

    $("#forgot_password_dialog").dialog({
        autoOpen: false,
        modal: true,
        bgiframe: false,
        buttons: {
            "OK": function () {
				Forgot();
            },
            Cancel: function () {
            	reset();
                $("#forgot_password_dialog").dialog("close");
            }
        }
    });

     
	$("#attempt_login_btn").button({ icons: { primary: "ui-icon-locked"} });
	$("#attempt_login_btn").click(function() { Login();	});
	$(".loginfield").keypress(function(e) {
		if(e.which == 13) { Login(); }
	});
 	
	$(".changefield").keypress(function(e) {
		if(e.which == 13) { Change(); }
	});

	$("#security_answer").keypress(function(e) {
		if(e.which == 13) { Forgot(); }
	});

 	$("#forgot_password_btn").click(function() {
		if ($("#username").val() == "") {
			alert("Please enter a username.");
			return false;
		}
		
	    $.ajax({
	        type: "POST",
	        url: "../uiMethods/wmGetQuestion",
	        data: '{"username":"' + $("#username").val() + '"}',
	        contentType: "application/json; charset=utf-8",
	        dataType: "json",
	        success: function (response) {
				if (response.error) {
					$("#error_msg").html(response.error).parent().show();
					reset();
				}
				if (response.info) {
					$("#error_msg").html(response.info).parent().show();
					reset();
				}
				if (response.result) {
					$("#security_question").html(unpackJSON(response.result));
			    	$("#forgot_password_dialog").dialog("open");
				}
	        },
	        error: function (response) {
	            $("#error_msg").html(response.responseText).parent().show();
	        }
	    });
 	});

	// get the welcome message
	$("#announcement").load("../announcement");

	// check the license.  If it's been agreed to, business as usual.
	// if not, we must present the license file.
	$.get("../getlicense", function(data) {
		if (data) {
			if (data.result != "pass") {
				if (data.license != "") {
					$("#licensetext").html(unpackJSON(data.license));
					$("#loginerror").hide();
					$("#loginpanel").hide();
					$("#licensepanel").show();
				}
				if (data.message != "") {
					$("#error_msg").html(data.message).parent().show();
				}
			}
		}
	}, "json");

	$("#license_agree_btn").click(function() { Agree();	});

});

function Agree() {
    $.ajax({
        type: "POST",
        url: "../uiMethods/wmLicenseAgree",
        data: '',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
        	// agreement!  Hide the license.  Show the login panel.
			$("#loginerror").hide();
			$("#loginpanel").show();
			$("#licensepanel").hide();
        },
        error: function (response) {
            $("#error_msg").html(response.responseText).parent().show();
        }
    });
}

function Login() {
	if ($("#username").val() == "")
		return false;

    var args = {};
    args.username = $("#username").val();
    if ($("#password").val() != "")
    	args.password = packJSON($("#password").val());
    if ($("#new_password").val() != "")
    	args.change_password = packJSON($("#new_password").val());
    if ($("#security_answer").val() != "")
    	args.answer = packJSON($("#security_answer").val());

    $.ajax({
        type: "POST",
        url: "../uiMethods/wmAttemptLogin",
        data: JSON.stringify(args),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
			if (response.error) {
				$("#error_msg").html(response.error).parent().show();
				reset();
			}
			if (response.info) {
				$("#error_msg").html(response.info).parent().show();
				reset();
			}
			if (response.result) {
			    if (response.result == "change") {
			    	$("#security_answer").val("")
			    	$("#password_change_dialog").dialog("open");
				}
			    if (response.result == "success") {
			    	// TODO check for expiration warnings and let the user know.
			    	location.href="../home";
				}
			}
        },
        error: function (response) {
            $("#error_msg").html(response.responseText).parent().show();
        }
    });
}
function Change() {
	// do not submit if the passwords don't match
	pw1 = $("#new_password").val();
	pw2 = $("#new_password_confirm").val();
	
	if (pw1 != pw2) {
		alert("Passwords must match.");
		$("#new_password").val("");
		$("#new_password_confirm").val("");
		$("#new_password").focus();
		return false;	
	}
	Login();
}
function Forgot() {
	if ($("#security_answer").val() == "") {
		return false;	
	}
	$("#forgot_password_dialog").dialog("close");
	Login();
}
function reset() {
	$(":input").val("");
	$("#username").focus();
	$("#password_change_dialog").dialog("close");
	$("#forgot_password_dialog").dialog("close");
}