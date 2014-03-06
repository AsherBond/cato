//Copyright 2014 Cloud Sidekick
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

// Utility functions for dealing with the url and querystring

function getQuerystringVariable(variable) {"use strict";
    var querystring = location.search.substring(1);
    var vars = querystring.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) {
            return pair[1];
        }
    }
    return "";
}

// returns the name of the current page
function getPageName() {"use strict";
    var pagename = window.location.pathname;
    pagename = pagename.substring(pagename.lastIndexOf('/') + 1);
    return pagename;
}

//decode a url encoded string
function urldecode(str) {
    return decodeURIComponent((str + '').replace(/\+/g, '%20'));
}

//encode a string with url encoding
function urlencode(str) {
    return encodeURIComponent((str + '').replace(/\%20/g, '+'));
}
