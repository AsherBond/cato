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

// This file contains common functions use throughout the main web application.  
// Changes made in this file will have global impact, so please be careful.

// this function pushes a message to the server log
function pushClientLog(msg, debug) {
    try {
        debug = typeof debug !== 'undefined' ? debug : 2;
        // NOTE: this server side procedure will never throw an exception if it encounters problems
        // ... it's completely silent.
        $.ajax({
            type : "POST",
            url : "/uiMethods/wmWriteClientLog",
            data : JSON.stringify({
                "msg" : msg,
                "debug" : debug
            })
        });
    } catch(err) {
        // well, last ditch effort - throw the error to the console
        console.log(msg);
        console.log(err);
    }
}

//This function shows the error dialog.
function showAlert(msg, info) {
    if (msg || info) {
        var options = {
            icon : "/common/img/icons/warning_32.png",
            sticky : true,
            title : 'Alert',
            message : msg
        };

        if ( typeof (info) !== "undefined" && info.length > 0) {
            options.message = options.message + "<br />" + info;
        }

        $.meow(options);

        // OK, let's send this message back to the server and write it to the client logfile.
        pushClientLog(msg, 3);
    }
}

//This function shows the info dialog.
function showInfo(msg, info, options) {
    if (msg || info) {
        // if options were provided, use them
        if ( typeof (options) !== "undefined") {
            if (!options.message) {
                options.message = msg;
            }
            if (!options.icon) {
                options.icon = "/common/img/icons/information_32.png";
            }
        } else {
            options = {
                icon : "/common/img/icons/information_32.png",
                title : 'Information',
                message : msg,
                duration : 2000
            };
        }

        if ( typeof (info) !== "undefined" && info.length > 0) {
            options.message = options.message + "<br /><br />" + info;
        }

        $.meow(options);
    }
}

//This function shows the 'success' dialog.
function showSuccess(msg, info, no_timeout) {
    if (msg || info) {
        var options = {
            icon : "/common/img/icons/checkmark_32.png",
            title : 'Success',
            message : msg
        };

        if ( typeof (info) !== "undefined" && info.length > 0) {
            options.message = options.message + "<br />" + info;
        }

        //set it to auto close after 2 seconds
        //if the no_timeout flag was not passed
        if ( typeof (no_timeout) !== "undefined" && no_timeout) {
            options.closeable = true;
        } else {
            options.duration = 2000;
        }

        $.meow(options);
    }
}
