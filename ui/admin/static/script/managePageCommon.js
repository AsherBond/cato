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

//only fires on initial load of the page.
$(document).ready(function () {
    // nice, clear all checkboxes selected in a single line!
    $(':input', (".jtable")).prop('checked', false);



    //search button
    $(".search_text").keypress(function (e) {
        if (e.which === 13) {
            GetItems();
            return false;
        }
    });

    $("#content").on("click", ".pager_button", function () {
        // since we are changing pages,
        // the selected array and selected label goes away

        //NOTE NOTE NOTE NOTE!!!!
        //the ClearSelectedRows function is PAGE SPECIFIC!.  Refer to the actual page
        //to see exactly what it's doing when it 'clears the array'

        //but don't crash if the page doesn't have it...
        if (window.ClearSelectedRows)
            ClearSelectedRows();
    });


    // sorting the list
    $().on("click", ".col_header", function () {
		//may not be needed when we implement a sortable pagable grid.
    });



    //button bindings
    $("#content").on("click", "#clear_selected_btn", function () {
        ClearSelectedRows();
    });
    $("#content").on("click", "#item_create_btn", function () {
        ShowItemAdd();
    });
    $("#content").on("click", "#item_delete_btn", function () {
        ShowItemDelete();
    });
    $("#content").on("click", "#item_copy_btn", function () {
        ShowItemCopy();
    });
    $("#content").on("click", "#item_export_btn", function () {
        ShowItemExport();
    });
    $("#content").on("click", "#item_modify_btn", function () {
        ShowItemModify();
    });
    $("#content").on("click", "#item_search_btn", function () {
        GetItems();
    });
    

    //dialogs
    //this delete dialog is common for all 'manage' pages.  The dialog HTML is defined on each page.
    //the delete function DeleteItems() must exist on each page.
    $("#delete_dialog").dialog({
        autoOpen: false,
        modal: false,
        bgiframe: false,
        width: 400,
        buttons: {
            "Delete": function () {
                showPleaseWait();
                DeleteItems();
                hidePleaseWait();
            },
            Cancel: function () {
                $("#delete_dialog").dialog("close");
            }
        }
    });

    //check/uncheck all checkboxes
    $("#content").on("click", "#chkAll", function () {
        if (this.checked) {
            this.checked = true;
            $("[tag='chk']").prop("checked", true);
        } else {
            this.checked = false;
            $("[tag='chk']").prop("checked", false);
        }

        //now build out the array
        var lst = "";
        $("[tag='chk']").each(function (intIndex) {
            if (this.checked) {
                lst += $(this).attr("id").replace(/chk_/, "") + ",";
            }
        });

        //chop off the last comma
        if (lst.length > 0)
            lst = lst.substring(0, lst.length - 1);

        $("#hidSelectedArray").val(lst);
        $("#lblItemsSelected").html($("[tag='chk']:checked").length);
    });


	//this spins thru the check boxes on the page and builds the array.
    //yes it rebuilds the list on every selection, but it's fast.
    $("#content").on("click", "[tag='chk']", function () {
        //first, deal with some 'check all' housekeeping
        //if I am being unchecked, uncheck the chkAll box too.
        //we do not have logic here to check the chkAll box if all items are checked.
        //that's not necessary right now.
        if (!this.checked) {
            $("#chkAll").prop("checked", false);
        }

        //now build out the array
        var lst = "";
        $("[tag='chk']").each(function (intIndex) {
            if (this.checked) {
                lst += $(this).attr("id").replace(/chk_/, "") + ",";
            }
        });

        //chop off the last comma
        if (lst.length > 0)
            lst = lst.substring(0, lst.length - 1);

        $("#hidSelectedArray").val(lst);
        $("#lblItemsSelected").html($("[tag='chk']:checked").length);
    });

	// set the focus to the search box
	$("#txtSearch").focus();
});

//look, you can't overload a pure javascript function.
//but we have stuff on each page that's page specific for the pageLoad function.
//so, on each "manage" page, we'll call this from the individual pageLoads.

function ManagePageLoad() {
    //initJtable(true, true);

    //all the buttons are jQuery "button" widgets - enable them
    $("#clear_selected_btn").button({ icons: { primary: "ui-icon-refresh" }, text: false });
    $("#item_create_btn").button({ icons: { primary: "ui-icon-plus"} });
    $("#item_delete_btn").button({ icons: { primary: "ui-icon-trash"} });
    $("#item_copy_btn").button({ icons: { primary: "ui-icon-copy"} });
    $("#item_export_btn").button({ icons: { primary: "ui-icon-extlink"} });
    $("#item_modify_btn").button({ icons: { primary: "ui-icon-pencil"} });
    $("#item_search_btn").button({ icons: { primary: "ui-icon-search"} });
}
function ShowItemDelete() {
    // if there are 0 items select then show a message
    // clear all of the previous values
    var ArrayString = $("#hidSelectedArray").val();
    if (ArrayString.length === 0) {
        showInfo('No Items selected.');
        return false;
    }

    //target page may have extra stuff to do... call it's function just in case
    if (typeof PreDeleteChecklist === 'function') {
        PreDeleteChecklist();
    }

    $("#delete_dialog").dialog("open");
    $("#delete_dialog").show();
}

function ClearSelectedRows() {
    $("#hidSelectedArray").val("");
    $("#lblItemsSelected").html("0");
    $(':input', (".jtable")).prop('checked', false);
}

function clearEditDialog() {
    $('#edit_dialog :input').each(function () {
        var type = this.type;
        var tag = this.tagName.toLowerCase(); // normalize case
        if (type === 'text' || type === 'password' || tag === 'textarea')
            this.value = "";
        else if (type === 'checkbox' || type === 'radio')
            this.checked = false;
        else if (tag === 'select')
            this.selectedIndex = 0;
    });
}


//this is some array management stuff used for the multiple edit chains
//and for IE compatibility evidently.  Thanks Stan but I'm not sure what you did here.
Array.prototype.remove = function (s) {
    var i = IsInArray(this, s);
    if (i !== -1) this.splice(i, 1);
};

// this should handle the odd problem on ie where "indexOf" doesn't exist
function IsInArray(myArray, searchString) {
    if (!myArray.indexOf) {
        Array.prototype.indexOf = function (obj) {
            for (var i = 0; i < searchString.length; i++) {
                if (searchString[i] === obj) {
                    return i;
                }
            }
            return -1;
        };
    } else {
        return myArray.indexOf(searchString);
    }
}