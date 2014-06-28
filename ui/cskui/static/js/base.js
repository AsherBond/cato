// #########################################################################
// #
// # Copyright 2014 Cloud Sidekick
// # __________________
// #
// #  All Rights Reserved.
// #
// # NOTICE:  All information contained herein is, and remains
// # the property of Cloud Sidekick and its suppliers,
// # if any.  The intellectual and technical concepts contained
// # herein are proprietary to Cloud Sidekick
// # and its suppliers and may be covered by U.S. and Foreign Patents,
// # patents in process, and are protected by trade secret or copyright law.
// # Dissemination of this information or reproduction of this material
// # is strictly forbidden unless prior written permission is obtained
// # from Cloud Sidekick.
// #
// #########################################################################

var g_config = {};

//the timer that keeps the heartbeat updated
window.setInterval(updateHeartbeat, 120000);

// THIS IS AWESOME
// get some important python configuration settings that have relevance on the client
g_config = catoAjax.getConfig();

// and this one has the global Maestro settings
g_settings = catoAjax.getSettings();

$(function() {"use strict";
    $(document).foundation();

    // show the version in the footer
    $("#app_version").text(g_config.version);

    $("#my_account_link").click(function() {
        showMyAccount();
    });
    // the about button opens the about dialog
    $("#about_btn").click(function() {
        showAbout();
    });
    $("#logout_btn").click(function() {
        location.href = "/logout";
    });

    // Auto-log uncaught JS errors
    window.onerror = function(msg, url, line) {
        pushClientLog(msg + "\n" + url + "\n" + line, 4);
    };

    // subapps will tweak the title, but we always clear it here
    $("#app_header_subapp").text("");

    // set the clicks for each of the product links
    var applink = $.cookie("csk_cd_ui-applink");
    $("#flow_link").click(function() {
        location.href = '/flow/pis';
    });
    $("#deploy_link").click(function() {
        location.href = g_config.user_ui_url + '?applink=' + applink;
    });
    $("#automate_link").click(function() {
        location.href = '/automate';
    });
    $("#canvas_link").click(function() {
        location.href = g_config.dash_api_url + '?applink=' + applink;
    });

    // click the logo
    $("#app_header_logo").click(function() {
        location.href = "/";
    });
});

function updateHeartbeat() {"use strict";
    ajaxGet("/uiMethods/wmUpdateHeartbeat", undefined, "text");
}

function lockDown(msg) {
    // if the heartbeat failed or a method returned a session error...
    // or, possibly the server is just gone...
    // close down the gui and show a pretty message, with a link to the login page.

    // NOTE: you cannot do a location.href here to any page, because if the server is down
    // it'll result in an ugly message.  By doing it with script here we don't need the server.

    msg = (msg) ? msg : 'It appears the server is no longer available.';

    //this will clear the page
    $("body").empty();

    // this is a wicked trick for erasing thie browser history to prevent the user
    // from going back and seeing broken pages.
    var backlen = history.length;
    history.go(-backlen);

    var $msg = $('<div class="ui-widget-content ui-corner-all" style="margin-left: auto; margin-right: auto; padding: 20px; width: 500px;" />');
    var $inner = $('<div class="ui-state-highlight ui-corner-all" style="padding: 10px;">');
    $inner.append('<span class="glyphicon glyphicon-info-sign" style="float: left; margin-right: .3em;"></span><strong>Uh oh...</strong>');
    $inner.append('<br><br>');
    $inner.append('<p style="margin-left: 10px;">' + msg + '</p><br>');
    $inner.append('<p style="margin-left: 10px;">Please contact an Administrator if this condition persists.</p><br>');
    $inner.append('<p style="margin-left: 10px;"><a href="/login">Click here</a> to return to the login page.</p>');
    $msg.append($inner);
    $("body").append($msg);

    // this nice little bit gets the index of a new setTimeout, then clears every outstanding timeout.
    // very useful for when dynamic content like user-defined reports are setting timeouts
    var x = setTimeout(function() {
    }, 0);
    for (var t = 0; t < x; t++) {
        clearTimeout(t);
    }

    //same magic to clear intervals
    var y = setInterval(function() {
    }, 0);
    for (var i = 0; i < y; i++) {
        clearInterval(i);
    }
}

function showMyAccount() {
    ajaxGet("/uiMethods/wmGetMyAccount", function(account) {
        $("#my_password").val("");
        $("#my_password_confirm").val("");
        $("#my_question").val("");
        $("#my_answer").val("");
        if (account) {
            $("#my_fullname").html(account.full_name);
            $("#my_username").html(account.username);
            $("#my_email").val(account.email);
            $("#my_question").val(account.security_question);
        }
        //finally, show the dialog
        $("#my_account_dialog").foundation('reveal', 'open');
    });
}

function showAbout() {"use strict";
    $("#app_version").text(g_config.version);
    $("#db_info").text(g_config.database);
    $("#license_company").text(g_config.license_company);
    $("#license_instances").text(g_config.used_instances + " of " + g_config.license_instances);
    $("#license_expires").text(g_config.license_expires);
    $('#about_dialog').foundation('reveal', 'open');
}

// this works with the foundation framework and the reveal modal
function showConfirm(message, on_confirm) {
    $("#csk_confirm .message").html(message);
    $("#csk_confirm").foundation('reveal', 'open');

    $("#csk_confirm").off("click", ".cancel");
    $("#csk_confirm").off("click", ".confirm");

    $("#csk_confirm").on("click", ".cancel", function() {
        $("#csk_confirm").foundation('reveal', 'close');
    });
    $("#csk_confirm").on("click", ".confirm", function() {
        if ( typeof on_confirm === "function") {
            on_confirm();
        }
        $("#csk_confirm").foundation('reveal', 'close');
    });
};

