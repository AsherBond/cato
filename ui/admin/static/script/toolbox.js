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

//tabs appear on the many pages.  Shared code.

//Tabs are simply hidden divs already drawn on the page.
//their content may be ajax... that's up to the specific page.

//at the least, clicking a tab a) hides all other tabs and b) shows the one that was clicked.

//to support additional custom functionality, IF a page
//has a "tabWasClicked" function, it will also be fired.

//gives the ability to have page-specific tab enhancements.

$(document).ready(function () {
    $("#toolbox .toolbox_panel").height($("#left_panel_te").height() - $("#toolbox_tabs").height() - 20);

    //the tab toggle click event
    $("#toolbox_tabs .toolbox_tab").click(function () {
        //we only do stuff if this tab isn't already selected.
        //if it is, do nothing
        if ($(this).hasClass("ui-tabs-selected ui-state-active"))
            return false;


        //hide 'em all
        $("#toolbox .toolbox_panel").addClass("hidden");
        $("#toolbox .toolbox_tab").removeClass("ui-tabs-selected ui-state-active");

        //show the one you clicked
        d = $(this).attr("linkto");
        $("#" + d).removeClass("hidden");
        $(this).addClass("ui-tabs-selected ui-state-active");

        //does the page have a tabClick handler function?
        if (typeof tabWasClicked == 'function') {
            tabWasClicked($(this).attr("id").replace(/tab_/, ""));
        }
    });

    //was there a directive to show a specific tab?  click it!
    var tab = getQuerystringVariable("tab");
    if (tab != "") {
        if ($("#tab_" + tab).length != 0) {
            $("#tab_" + tab).click();
        }
    }

});
