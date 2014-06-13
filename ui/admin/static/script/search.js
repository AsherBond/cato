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

$(function() {"use strict";
    $("#search_btn").button({
        icons : {
            primary : "ui-icon-search"
        }
    });

    $("#pattern").keypress(function(e) {
        if (e.which === 13) {
            search();
            return false;
        }
    });
    $("#search_btn").click(function() {
        search();
    });

    $("#pattern").focus();
});

function search() {
    $("#results").empty();

    var _pattern = $("#pattern").val();

    // at the moment we are searching tasks
    // we will add other stuff later.
    var _type = "task";

    var _in = "function";
    // optional limiter to field name (or other logical subarea)

    if (pattern) {
        catoAjax.search(_type, _in, _pattern, function(response) {
            if (results.error) {
                showInfo(response.error);
                return;
            }
            // spin the results and draw a strip for each one
            // what happens here will be very dependent on _type
            if (response.results.length) {
                $.each(response.results, function(idx, row) {
                    var $item = $('<li class="resultitem ui-widget-content ui-corner-all">');

                    var url = '/taskEdit?task_id=' + row.task_id + '&codeblock=' + row.codeblock_name;
                    $item.append('<span><b>' + _type + ':</b> <a href="' + url + '">' + row.task_name + '</a></span>');
                    $item.append('<span><b> Codeblock:</b> <a href="' + url + '">' + row.codeblock_name + '</a></span>');
                    $item.append('<span><b> Step:</b> ' + row.step_order + '</span>');
                    $item.append('<div><span><b>Code:</b></span><br><code>' + row.function_xml + '</code></div>');

                    $("#results").append($item);
                });
            } else {
                $("#results").append('<li class="resultitem ui-widget-content ui-corner-all">No results found.</li>');
            }
        });

    } else {
        showInfo("Please enter search criteria.");
    }
}