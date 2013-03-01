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

//registry editing appears on the many pages.  Shared code.
$(document).ready(function () {
    //building the dialog inner content here so it's the same on all pages.
    var ed = '<label for="reg_edit_dialog_encrypt">Encrypt?</label> <input type="checkbox" id="reg_edit_dialog_encrypt">' +
        '<hr />' +
        '<textarea id="reg_edit_dialog_value" rows="10" cols="80"></textarea>';
    $("#reg_edit_dialog").html(ed);

    var ad = 'Name:' +
        '<input type="text" id="reg_add_dialog_name" validate_as="hostname" />' +
        '<input type="hidden" id="reg_add_dialog_oldname" />' +
        '<input type="hidden" id="selected_node_id" />' +
        '<input type="hidden" id="selected_node_xpath" />' +
        '<input type="hidden" id="reg_edit_mode" />';
    $("#reg_add_dialog").html(ad);


    //disable selection of all editable nodes on the page
    $(".editable").disableSelection();

    //double clicking on some text opens up the appropriate edit dialog
    $(".editable").live("dblclick", function () {
        $("#selected_node_id").val($(this).attr("id"));
        $("#selected_node_xpath").val($(this).parent().attr("xpath"));
        $("#reg_edit_dialog_encrypt").removeAttr("checked")

        //if the value is our (empty) or (********) encrypt placeholders, show an empty dialog
        var value = ($(this).text() == "(empty)" ? "" : ($(this).text() == "(********)" ? "" : $(this).text()));

        //is this node masked?  if so, check the box
        if ($(this).attr("encrypt") == "true")
            $("#reg_edit_dialog_encrypt").attr("checked", "checked")

        //if this field is a "value" it will have a specific class, otherwise it's a node name
        var updatetype = ($(this).hasClass("registry_node_value") ? "value" : "node");
        $("#reg_edit_mode").val(updatetype);

        //if on it...and pick the dialog
        if (updatetype == "value") {
            $("#reg_edit_dialog_value").val(value);

            $("#reg_edit_dialog").dialog("open");
            $("#reg_edit_dialog_value").focus();
        }
        if (updatetype == "node") {
            $("#reg_add_dialog_name").val($(this).text());
            $("#reg_add_dialog_oldname").val($(this).text());

            $("#reg_add_dialog").dialog("open");
            $("#reg_add_dialog_name").focus();
        }
    });

    $(".registry_node_add_btn").live("click", function () {
        $("#selected_node_xpath").val($(this).attr("xpath"));
        $("#reg_edit_mode").val("add");

        $("#reg_add_dialog").dialog("open");
        $("#reg_add_dialog_name").focus();
    });

    $(".registry_node_remove_btn").live("click", function () {
        if (confirm("Are you sure?")) {
            DeleteRegistryItem($(this).attr("id_to_remove"), $(this).attr("xpath_to_delete"));
        }
    });

    $("#registry_refresh_btn").live("click", function () {
        var type = $("#reg_type").val();
        if (type == "global") var objectid = "global";
        if (type == "asset") var objectid = $("#hidCurrentEditID").val();
        if (type == "task") var objectid = $("#hidOriginalTaskID").val();
        GetRegistry(objectid);
    });

    $("#reg_edit_dialog").dialog({
        title: "Edit Value",
        autoOpen: false,
        modal: true,
        width: 600,
        bgiframe: true,
        buttons: {
            "Save": function () {
                SaveRegistryValue();
            },
            Cancel: function () {
                $("#reg_edit_dialog").dialog("close");
            }
        }
    });

    $("#reg_add_dialog").dialog({
        title: "Item Name",
        autoOpen: false,
        modal: true,
        width: 600,
        bgiframe: true,
        buttons: {
            "Save": function () {
                if ($("#reg_edit_mode").val() == "add")
                    AddRegistryItem();
                if ($("#reg_edit_mode").val() == "node")
                    SaveRegistryNode();
            },
            Cancel: function () {
                $("#reg_add_dialog").dialog("close");
            }
        }
    });

});

function DeleteRegistryItem(id, xpath) {
    var type = $("#reg_type").val();
    if (type == "global") var objectid = "global";
    if (type == "asset") var objectid = $("#hidCurrentEditID").val();
    if (type == "task") var objectid = $("#hidOriginalTaskID").val();

    $("#update_success_msg").text("Deleting...").show();

    $.ajax({
        async: false,
        type: "POST",
        url: "uiMethods/wmDeleteRegistryNode",
        data: '{"sObjectID":"' + objectid + '", "sXPath":"' + xpath + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
			if (response.error) {
				showAlert(response.error);
			}
			if (response.info) {
				showInfo(response.info);
			}
			if (response.result) {
	            $("#update_success_msg").text("Delete Successful").fadeOut(2000);
	
	            //after commit, reget everything (xpath indexes may have changed)
	            GetRegistry(objectid);
	        }
        },
        error: function (response) {
            $("#update_success_msg").fadeOut(2000);
            showAlert(response.responseText);
        }
    });

    ClearRegistrySelection();
}

function AddRegistryItem() {
    var xpath = $("#selected_node_xpath").val();
    var name = $("#reg_add_dialog_name").val();
    var type = $("#reg_type").val();
    if (type == "global") var objectid = "global";
    if (type == "asset") var objectid = $("#hidCurrentEditID").val();
    if (type == "task") var objectid = $("#hidOriginalTaskID").val();

    if (name == "") {
        alert("Name is required.");
        return;
    }


    $("#update_success_msg").text("Adding...").show();

    $.ajax({
        async: false,
        type: "POST",
        url: "uiMethods/wmAddRegistryNode",
        data: '{"sObjectID":"' + objectid + '","sXPath":"' + xpath + '","sName":"' + name + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
			if (response.error) {
				showAlert(response.error);
			}
			if (response.info) {
				showInfo(response.info);
			}
			if (response.result) {
	            //after commit, reget the whole registry
	            $("#update_success_msg").text("Add Successful...").fadeOut(2000);
	            GetRegistry(objectid);
	            $("#reg_add_dialog").dialog("close");
	        }
        },
        error: function (response) {
            $("#update_success_msg").fadeOut(2000);
            showAlert(response.responseText);
        }
    });

    ClearRegistrySelection();
}

function SaveRegistryValue() {
    var id = $("#selected_node_id").val();
    var xpath = $("#selected_node_xpath").val();
    var type = $("#reg_type").val();
    if (type == "global") var objectid = "global";
    if (type == "asset") var objectid = $("#hidCurrentEditID").val();
    if (type == "task") var objectid = $("#hidOriginalTaskID").val();

    var value = $("#reg_edit_dialog_value").val();
    var encrypt = ($("#reg_edit_dialog_encrypt").attr("checked") == "checked" ? 1 : 0);


    $("#update_success_msg").text("Updating...").show();

    $.ajax({
        async: false,
        type: "POST",
        url: "uiMethods/wmUpdateRegistryValue",
        data: '{"sObjectID":"' + objectid + '","sXPath":"' + xpath + '","sValue":"' + packJSON(value) + '","sEncrypt":"' + encrypt + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
			if (response.error) {
				showAlert(response.error);
			}
			if (response.info) {
				showInfo(response.info);
			}
			if (response.result) {
	            $("#update_success_msg").text("Update Successful").fadeOut(2000);
	
	            //after commit, update the node with the new value
	            if (encrypt == 1)
	                value = "(********)";
	
	            $('#' + id).html(value);
	
	            $("#reg_edit_dialog").dialog("close");
			}
        },
        error: function (response) {
            $("#update_success_msg").fadeOut(2000);
            showAlert(response.responseText);
        }
    });

    ClearRegistrySelection();
}

function SaveRegistryNode() {
    var id = $("#selected_node_id").val();
    var xpath = $("#selected_node_xpath").val();
    var type = $("#reg_type").val();
    if (type == "global") var objectid = "global";
    if (type == "asset") var objectid = $("#hidCurrentEditID").val();
    if (type == "task") var objectid = $("#hidOriginalTaskID").val();

    var oldname = $("#reg_add_dialog_oldname").val();
    var name = $("#reg_add_dialog_name").val();

    if (name == "") {
        alert("Name is required.");
        return;
    }


    $("#update_success_msg").text("Updating...").show();

    $.ajax({
        async: false,
        type: "POST",
        url: "uiMethods/wmRenameRegistryNode",
        data: '{"sObjectID":"' + objectid + '","sXPath":"' + xpath + '","sOldName":"' + oldname + '","sNewName":"' + name + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            $("#update_success_msg").text("Update Successful").fadeOut(2000);

            //after commit, update the node with the new name
            $('#' + id).html(name);

            $("#reg_add_dialog").dialog("close");
        },
        error: function (response) {
            $("#update_success_msg").fadeOut(2000);
            showAlert(response.responseText);
        }
    });

    ClearRegistrySelection();
}

function ClearRegistrySelection() {
    $("#selected_node_id").val("");
    $("#selected_node_xpath").val("");

    $("#reg_add_dialog_name").val("");
    $("#reg_add_dialog_oldname").val("");

    $("#reg_edit_dialog_value").val("");

    $("#reg_edit_mode").val("");
}

function GetRegistry(sObjectID) {
    $.ajax({
        async: false,
        type: "POST",
        url: "uiMethods/wmGetRegistry",
        data: '{"sObjectID":"' + sObjectID + '"}',
        contentType: "application/json; charset=utf-8",
        dataType: "html",
        success: function (response) {
            $("#registry_content").html(response);
        },
        error: function (response) {
            showAlert(response.responseText);
        }
    });
}

