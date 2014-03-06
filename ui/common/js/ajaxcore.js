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

/*
 * This file is used by ALL CSK UI's.  It contains the foundational ajax core for those apps.
 *
 * Each UI will augment the 'catoAjax' object with additional functions specific to that app.
 *
 * Of course it should be clear that each UI has it's own "uiMethods" class on the server to handle
 * these few common functions, which are likely only wrappers to a shared server-side function
 * in the uiCommon module.
 */

function catoAjax() {
    // just the catoAjax object.
    // might get some properties in the future.
}

// Class methods.
catoAjax.getConfig = function() {"use strict";
    var args = {};
    return ajaxPost("uiMethods/wmGetConfig", args);
};

catoAjax.getSettings = function() {"use strict";
    return ajaxPost("uiMethods/wmGetSettings");
};

catoAjax.saveMyAccount = function(values) {"use strict";
    var args = {};
    args.values = values;
    return ajaxPost("uiMethods/wmSaveMyAccount", args);
};

//Update a application setting...
catoAjax.updateSetting = function(category, setting, value) {
    var response = ajaxPost("uiMethods/wmSetApplicationSetting", {
        "sCategory" : category,
        "sSetting" : setting,
        "sValue" : value
    }, "text");
};

/*
 * This generic function is used by anything that needs to do an AJAX POST
 * to get back a JSON object.
 *
 * the datatype defaults to json unless explicitly set
 * if explicitly set, must be html, text or xml
 */
function ajaxPost(apiurl, args, datatype) {"use strict";
    datatype = typeof datatype !== 'undefined' ? datatype : 'json';

    // args: a javascript object
    // url: the url of the web api call
    var result;
    $.ajax({
        async : false,
        type : "POST",
        url : apiurl,
        data : JSON.stringify(args),
        contentType : "application/json; charset=utf-8",
        dataType : datatype,
        beforeSend : function() {
            $(document.body).css("cursor", "wait");
        },
        complete : function() {
            $(document.body).css("cursor", "default");
        },
        success : function(response) {
            result = response;
        },
        error : ajaxErrorCallback
    });
    return result;
}

function ajaxPostAsync(apiurl, args, on_success, on_error, datatype) {"use strict";
    // this method is like the ajaxGet - it's asynchronous.
    // which means, the only way to handle it's results is by providing
    // an on_success function.
    datatype = typeof datatype !== 'undefined' ? datatype : 'json';
    on_error = typeof on_error === 'function' ? on_error : ajaxErrorCallback;

    $.ajax({
        async : false,
        type : "POST",
        url : apiurl,
        data : JSON.stringify(args),
        contentType : "application/json; charset=utf-8",
        dataType : datatype,
        success : function(response) {
            if ( typeof on_success === 'function') {
                on_success(response);
            }
        },
        error : on_error
    });
}

/*
 * This generic function is used by anything that needs to do an AJAX GET
 * to get back a JSON object.
 *
 * the datatype defaults to json unless explicitly set
 * if explicitly set, must be html, text or xml
 */
function ajaxGet(apiurl, on_success, datatype) {"use strict";
    // NOTE: this get type takes an on_success() function.
    // async calls can't return values --- there's no telling when they'll be done.
    // but when it is done, we'll call the on_success function!
    datatype = typeof datatype !== 'undefined' ? datatype : 'json';

    $.ajax({
        type : "GET",
        url : apiurl,
        contentType : "application/json; charset=utf-8",
        dataType : datatype,
        success : function(response) {
            if ( typeof (on_success) !== 'undefined') {
                on_success(response);
            }
        },
        error : ajaxErrorCallback
    });
}

ajaxErrorCallback = function(response) {"use strict";
    var method = response.getResponseHeader("X-CSK-Method");
    if (response.status === 500) {
        //only show info, as the real message will already be in the server log
        showInfo("An exception occurred - please check the server logfiles for details. (500)", method);
    } else if (response.status === 280) {
        // 280 is our custom response code to indicate we want an 'info' message
        showInfo(response.responseText);
    } else if (response.status === 480) {
        // 480 is our custom 'session error' response code ... lock it down
        msg = (response.responseText) ? response.responseText : "Your session has ended or been terminated.";
        lockDown(msg);
    } else {
        msg = (response.responseText === "None") ? "Expected a response and got 'None'." : response.responseText;
        showAlert(msg, method);
    }

    // these *might* be necessary in many places
    if ( typeof hidePleaseWait == 'function') {
        hidePleaseWait();
    }
    $("#update_success_msg").fadeOut(2000);
};

//used in many places where we send strings as json data, replaces the two critical json chars " and \
//THESE CALL a jQuery plugin
function packJSON(instr) {"use strict";
    //if it's empty or undefined, return ""
    if (instr === "" || instr === undefined || instr === null)
        return "";

    if (instr.length < 1)
        return "";

    //NOTE! base64 encoding still has a couple of reserved characters so we explicitly replace them AFTER
    var outstr = $.base64.encode(instr);
    return outstr.replace(/\//g, "%2F").replace(/\+/g, "%2B");
}

function unpackJSON(instr) {"use strict";
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

