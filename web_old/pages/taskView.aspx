<%@ Page Language="C#" AutoEventWireup="True" MasterPageFile="~/pages/site.master"
    CodeBehind="taskView.aspx.cs" Inherits="Web.pages.taskView" %>

<asp:Content ID="cHead" ContentPlaceHolderID="phHead" runat="server">
    <link type="text/css" href="../style/taskEdit.css" rel="stylesheet" />
    <link type="text/css" href="../style/taskView.css" rel="stylesheet" />
    <link type="text/css" href="../style/registry.css" rel="stylesheet" />
    <script type="text/javascript" src="../script/taskedit/taskView.js"></script>
    <script type="text/javascript" src="../script/taskedit/taskVersions.js"></script>
    <script type="text/javascript" src="../script/toolbox.js"></script>
    <script type="text/javascript" src="../script/taskedit/taskEditParams.js"></script>
    <script type="text/javascript" src="../script/taskedit/taskEditDebug.js"></script>
    <script type="text/javascript" src="../script/objectTag.js"></script>
    <script type="text/javascript" src="../script/registry.js"></script>
    <script type="text/javascript" src="../script/parametersOnDialog.js"></script>
    <script type="text/javascript" src="../script/taskLaunchDialog.js"></script>
    <script type="text/javascript">
        //here because other pages (task edit, print) share the taskView.js file.
        //but versions is the default tab on this page so we wanna load it initially.
        $(document).ready(function () {
            doGetVersions();
        });
    </script>
</asp:Content>
<asp:Content ID="cDetail" ContentPlaceHolderID="phDetail" runat="server">
    <div id="left_panel_te">
        <div id="toolbox">
            <div id="toolbox_tabs" class="toolbox_tabs_1_row">
                <span id="tab_versions" linkto="div_versions" class="ui-state-default ui-corner-top toolbox_tab ui-tabs-selected ui-state-active">
                    Versions&nbsp;</span><span id="tab_parameters" linkto="div_parameters" class="ui-state-default ui-corner-top toolbox_tab"
                        style="padding-left: 6px; padding-right: 6px;">Parameters</span><span id="tab_schedules"
                            linkto="div_schedules" class="ui-state-default ui-corner-top toolbox_tab" 
                            style="padding-left: 6px; padding-right: 6px;">Schedules</span><span id="tab_debug"
                                linkto="div_debug" class="ui-state-default ui-corner-top toolbox_tab">Run</span>
                <!--<span
                        id="tab_registry" linkto="div_registry" class="ui-state-default ui-corner-top toolbox_tab"
                        style="padding-left: 7px; padding-right: 7px;" runat="server">Registry</span><span
                            id="tab_tags" linkto="div_tags" class="ui-state-default ui-corner-top toolbox_tab">Tags</span>-->
            </div>
            <div id="div_versions" class="toolbox_panel">
				<center>
					<span id="show_log_link">View Change Log</span>						
					<span id="show_runlog_link">View Last Run Log</span>
				</center>
                <br />
                <br />
                <span class="detail_label">Selected Version:</span>
                <asp:Label ID="lblVersion" runat="server" CssClass="code"></asp:Label><br />
                <span class="detail_label">Status: </span>
                <asp:Label ID="lblStatus2" runat="server" CssClass="code"></asp:Label><br />
                <asp:Button ID="btnSetDefault" runat="server" Text="Set as Default" OnClick="btnSetDefault_Click" />
                <hr />
                <span class="detail_label">All Versions:</span>
                <ul id="versions">
                </ul>
                <input type="button" value="New Version" onclick="ShowVersionAdd();return false;" />
            </div>
            <div id="div_debug" class="toolbox_panel hidden">
                <!--<p>
                    Test Asset:<br />
                    <asp:TextBox ID="txtTestAsset" runat="server" Enabled="false" asset_id="" CssClass="code"
                        Width="80%"></asp:TextBox>
                    <img class="asset_picker_btn pointer" src="../images/icons/search.png" link_to="ctl00_phDetail_txtTestAsset"
                        alt="" />
                    <img id="debug_asset_clear_btn" class="pointer" src="../images/icons/fileclose.png"
                        alt="" />
                </p>-->
                <p>
                    Last Run Time:
                    <asp:Label ID="lblLastRunDT" runat="server"></asp:Label><br />
                    Last Run Status:
                    <asp:Label ID="lblLastRunStatus" runat="server"></asp:Label>
                    <asp:Image ID="debug_view_latest_log" CssClass="debug_btn" ImageUrl="../images/icons/view_text_16.png"
                        runat="server" />
                </p>
                <br />
                <hr />
                <br />
                <p style="text-align: center;">
                    Current Status:
                    <asp:Label ID="lblCurrentStatus" runat="server"></asp:Label>
                    <br />
                    <img id="debug_stop_btn" class="debug_btn" src="../images/icons/player_stop_32.png"
                        alt="" />
                    <img id="debug_run_btn" class="debug_btn" src="../images/icons/player_play_32.png"
                        alt="" />
                    <img id="debug_view_active_log" class="debug_btn" src="../images/icons/view_text_32.png"
                        alt="" />
                </p>
            </div>
            <div id="div_tags" class="toolbox_panel hidden">
                <span id="tag_add_btn" class="tag_add_btn pointer">
                    <img alt="" src="../images/icons/edit_add.png" />
                    click to add </span>
                <ul id="objects_tags">
                </ul>
            </div>
            <div id="div_registry" class="toolbox_panel hidden">
                <div id="registry_content">
                </div>
            </div>
            <div id="div_parameters" class="toolbox_panel hidden">
                <span id="parameter_add_btn">Add New</span>
                <hr />
                <div id="parameters">
                </div>
            </div>
            <div id="div_schedules" class="toolbox_panel hidden">
	        	<div class="ui-state-default">        
					<span class="detail_label">Action Plans</span>
				</div>
				<div id="toolbox_plans" class="ui-widget-content">
                </div>
				<br />
				<div class="ui-state-default">
					<span class="detail_label">Schedules</span>
				</div>
                <div id="toolbox_schedules" class="ui-widget-content">
                </div>
            </div>
        </div>
    </div>
    <div id="content_te" class="display">
        <center>
            <h3>
                <asp:Label ID="lblTaskNameHeader" runat="server"></asp:Label>
                <span id="version_tag">Version:
                    <asp:Label ID="lblVersionHeader" runat="server"></asp:Label></span></h3>
        </center>
        <div class="ui-state-highlight">
            <p>
                <img src="../images/icons/encrypted_32.png" alt="" />
                This Task is "Approved". Changes are not permitted.
            </p>
        </div>
        <br />
        <div class="codebox">
            <span class="detail_label">Code:</span>
            <asp:Label ID="lblTaskCode" runat="server" CssClass="code" Style="font-size: 1.2em;"></asp:Label>
            <br />
            <span class="detail_label">Status: </span>
            <asp:Label ID="lblStatus" runat="server" CssClass="code" Style="font-size: 1.2em;"></asp:Label>
            <br />
            <span class="detail_label">Concurrent Instances:</span>
            <asp:Label ID="lblConcurrentInstances" runat="server" CssClass="task_details code"
                Style="font-size: 1.2em;"></asp:Label>
            <br />
            <span class="detail_label">Number to Queue:</span>
            <asp:Label ID="lblQueueDepth" runat="server" CssClass="task_details code" Style="font-size: 1.2em;"></asp:Label>
            <br />
            <span class="detail_label">Description:</span>
            <br />
            <asp:Label ID="lblDescription" TextMode="MultiLine" Rows="10" runat="server" CssClass="code"
                Style="font-size: 1.2em;"></asp:Label>
            <!-- *** Commented out per Bug 1029 ***
                     <asp:Label ID="lblDirect" runat="server" CssClass="code"></asp:Label>
                        Direct to Asset?<br />
            -->
        </div>
        <hr />
        <div id="div_steps" class="">
            <h3>
                Steps</h3>
            <ul id="codeblock_steps">
                <asp:PlaceHolder ID="phSteps" runat="server"></asp:PlaceHolder>
            </ul>
        </div>
        <hr />
    </div>
    <!--DIALOGS-->
    <div id="task_launch_dialog" title="Run Task">
        <div id="plan_edit_dialog" title="Edit Plan">
        </div>
    </div>
    <div id="param_edit_dialog" title="Parameter">
    </div>
    <div id="param_delete_confirm_dialog" title="Remove Parameter">
    </div>
    <!--
    <div id="asset_picker_dialog" title="Select an Asset" class="hidden ui-state-highlight">
        <span style="padding-left: 15px; padding-top: 5px; font-weight: bold;">Enter search
            criteria:</span> <span style="padding-left: 15px; padding-top: 5px;">
                <input id="asset_search_text" class="search_text" /></span> <span style="padding-left: 15px;
                    padding-top: 5px;">
                    <img src="../images/icons/btnSearch.png" alt="" style="border: none; vertical-align: top;"
                        id="asset_search_btn" class="pointer" /></span>
        <div id="asset_picker_results">
        </div>
        <input type="hidden" id="asset_picker_target_field" value="" />
        <input type="hidden" id="asset_picker_target_name_field" value="" />
    </div>
    -->
    <div id="addVersion_dialog" class="hidden" title="Create Another Version">
        Current Version Number:
        <asp:Label ID="lblCurrentVersion" runat="server" Text="" />
        <center>
            <input id="rbMinor" checked="checked" name="rbMinorMajor" value="Minor" type="radio" />
            <asp:Label ID="lblNewMinor" runat="server" Text="New Minor Version" /><br />
            <input id="rbMajor" name="rbMinorMajor" value="Major" type="radio" />
            <asp:Label ID="lblNewMajor" runat="server" Text="New Major Version" /><br />
            <input type="button" value="Create New Version" onclick="CreateNewVersion();return false;" />
            <input type="button" value="Cancel" onclick="CloseVersionDialog();return false;" />
        </center>
    </div>
    <!-- Registry dialogs. -->
    <div id="reg_edit_dialog" class="hidden">
    </div>
    <div id="reg_add_dialog" class="hidden">
    </div>
    <!-- End Registry dialogs.-->
    <input type="hidden" id="reg_type" value="task" />
    <!--END DIALOGS-->
    <input id="hidPageSaveType" type="hidden" value="dynamic" />
    <input id="hidObjectType" type="hidden" value="3" />
    <asp:HiddenField ID="hidOriginalTaskID" runat="server"></asp:HiddenField>
    <asp:HiddenField ID="hidTaskID" runat="server" />
    <asp:HiddenField ID="hidDefault" runat="server"></asp:HiddenField>
    <asp:HiddenField ID="hidDebugActiveInstance" runat="server"></asp:HiddenField>
    <input type="hidden" id="hidParamType" value="task" />
</asp:Content>
