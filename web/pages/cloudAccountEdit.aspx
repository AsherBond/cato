<%@ Page Language="C#" AutoEventWireup="true" CodeBehind="cloudAccountEdit.aspx.cs"
    Inherits="Web.pages.cloudAccountEdit" MasterPageFile="~/pages/site.master" %>

<asp:Content ID="cHead" ContentPlaceHolderID="phHead" runat="server">
    <style type="text/css">
        .keypair
        {
            clear: both;
            height: 18px;
            margin: 1px 2px 1px 4px;
            padding: 1px;
        }
        .keypair_label
        {
            float: left;
        }
        .keypair_icons
        {
            float: right;
        }
    </style>
</asp:Content>
<asp:Content ID="cDetail" ContentPlaceHolderID="phDetail" runat="server">
    <script type="text/javascript" src="../script/managePageCommon.js"></script>    
	<script type="text/javascript" src="../script/cloudAccountEdit.js"></script>
    <div style="display: none;">
        <input id="hidMode" type="hidden" name="hidMode" />
        <input id="hidCurrentEditID" type="hidden" name="hidCurrentEditID" />
        <input id="hidSelectedArray" type="hidden" name="hidSelectedArray" />
        <asp:HiddenField ID="hidSortColumn" runat="server" />
        <asp:HiddenField ID="hidPage" runat="server" />
        <!-- Start visible elements -->
    </div>
    <div id="left_panel">
        <div id="left_tooltip_img">
			<img src="../images/icons/cloud_accounts_192.png" alt="" />
        </div>
		<div class="left_tooltip">
            <div id="left_tooltip_box_outer">
                <div id="left_tooltip_box_inner">
					<h2>Cloud Accounts</h2>
                    <p>
                        The Manage Cloud Accounts screen allows administrators
                        to modify, add and delete Cloud Accounts.</p>
                    <p>
                        Select an Account from the list or select an action to edit or delete the Accounts
                        you've selected.</p>
					<p><i>Cloud Accounts can not be deleted if they are associated with any Ecosystems.</i></p>
 					<p><a href="http://projects.cloudsidekick.com/projects/cato/wiki/CloudAccount?utm_source=cato_app&amp;utm_medium=helplink&amp;utm_campaign=app" target="_blank"><img src="../images/icons/info.png" alt="" />Click here</a>
						for a more detailed introduction to Cloud Accounts.</p>
                </div>
            </div>
        </div>
    </div>
    <div id="content">
        <span id="lblItemsSelected">0</span> Items Selected <span id="clear_selected_btn"></span><span 
			id="item_create_btn">Create</span><span id="item_delete_btn">Delete</span>
        <asp:TextBox ID="txtSearch" runat="server" class="search_text" />
        <span id="item_search_btn">Search</span>
		<div id="accounts">
			<asp:Literal id="ltAccounts" runat="server"></asp:Literal>
		</div>
    </div>
    <div id="edit_dialog" class="hidden" title="Create Account">
        <div id="edit_dialog_tabs">
            <ul>
                <li><a href="#AccountTab"><span>Account</span></a></li>
                <li><a href="#KeyPairTab"><span>Key Pairs</span></a></li>
            </ul>
            <div id="AccountTab" style="height: 340px;">
                <table width="100%">
                    <tr>
                        <td>
                            Account Name:
                        </td>
                        <td>
                            <input id="txtAccountName" class="usertextbox" name="txtAccountName" />
                        </td>
                    </tr>
                    <tr>
                        <td>
                            Account Number:
                        </td>
                        <td>
                            <input id="txtAccountNumber" class="usertextbox" name="txtAccountNumber" />
                        </td>
                    </tr>
                    <tr>
                        <td>
                            Provider:
                        </td>
                        <td>
                            <select id="ddlProvider">
								<asp:Literal id="ltProviders" runat="server"></asp:Literal>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <span id="login_label">Access Key</span>:
                        </td>
                        <td>
                            <input id="txtLoginID" class="usertextbox" name="txtLoginID" />
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <span class="password_label">Secret Key</span>:
                        </td>
                        <td>
                            <input id="txtLoginPassword" type="password" class="usertextbox" name="txtLoginPassword" />
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <span class="password_label">Secret Key</span> Confirm:
                        </td>
                        <td>
                            <input id="txtLoginPasswordConfirm" type="password" class="usertextbox" name="txtLoginPasswordConfirm" />
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
						<td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            Make Default:
                        </td>
                        <td>
                            <input id="chkDefault" type="checkbox" class="usertextbox" name="chkDefault" />
                        </td>
                    </tr>
                    <tr>
                        <td>
                        </td>
                        <td>
                            <i>The "default" account is automatically selected on intial login.</i>
                        </td>
                    </tr>
                    <tr style="display: none;"><!--hidden temporarily pending a decision about auto_manage_security-->
                        <td>
                            Auto Security:
                        </td>
                        <td>
                            <input id="chkAutoManageSecurity" type="checkbox" class="usertextbox" name="chkAutoManageSecurity" />
                        </td>
                    </tr>
                    <tr style="display: none;"><!--hidden temporarily pending a decision about auto_manage_security-->
                        <td>
                        </td>
                        <td>
                            Automatically grant port access for EC2? (ssh, winrm, etc.)
                        </td>
                    </tr>
					<tr>
		                <td colspan="2">
							<hr />
						</td>	
		            </tr>
					<tr>
						<td>
							Cloud: <span id="add_cloud_btn" title="Add a Cloud"></span><span id="jumpto_cloud_btn" title="Edit Cloud"></span>
						</td>
		                <td>
                            <select id="ddlTestCloud">
                            </select>
							<span id="test_connection_btn">Test Connection</span>
						</td>
					</tr>
	             	<tr>
		                <td colspan="2">
							<div id="conn_test_result" style="margin-top: 10px;"></div>
							<div id="conn_test_error" style="font-size: 0.8em; font-style: italic; margin-top: 10px;"></div>
						</td>
		            </tr>
				</table>
            </div>
            <div id="KeyPairTab">
                <span style="font-style: italic;">(Changes to Key Pairs are saved automatically, and
                    cannot be undone.)</span>
                <hr />
                <span id="keypair_add_btn">Add</span>
                <hr />
                <div id="keypairs">
                </div>
            </div>
        </div>
    </div>
    <div id="keypair_dialog" class="hidden" title="Key Pair">
        <table width="100%">
            <tr>
                <td>
                    Name:
                </td>
            </tr>
            <tr>
                <td>
                    <input id="keypair_name" name="keypair_name" class="usertextbox" type="text" />
                </td>
            </tr>
            <tr>
                <td>
                    Private Key:
                </td>
            </tr>
            <tr>
                <td>
                    <textarea id="keypair_private_key" name="keypair_private_key" rows="3" cols="40"></textarea>
                </td>
            </tr>
            <tr>
                <td>
                    Passphrase:
                </td>
            </tr>
            <tr>
                <td>
                    <input id="keypair_passphrase" name="keypair_passphrase" class="usertextbox" type="password" />
                </td>
            </tr>
        </table>
        <input type="hidden" id="keypair_id" />
    </div>
    <div id="delete_dialog" class="hidden" title="Delete">
        Are you sure you want to delete these Accounts?
		<br /><br />
		This action cannot be undone.
    </div>
</asp:Content>
