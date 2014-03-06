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

// THIS IS CRITICAL
// different browsers cache ajax different ways.
// this app doesn't require ajax caching - our content is different every time it's requested.
// this should make all ajax requests use the jquery cache buster.
// (this only applies to GET calls)
// $.ajaxSetup({
// cache : false
// });
// this file *should* always be the first script file loaded, and this block isn't in document.ready.

$(document).ready(function() {
    //there are datepickers all over the app.  Anything with a class of "datepicker" will get initialized.
    $(".datepicker").datepicker({
        clickInput : true
    });
    $(".datetimepicker").datetimepicker();
    $(".timepicker").timepicker();
});

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