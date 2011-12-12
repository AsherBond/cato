﻿//Copyright 2011 Cloud Sidekick
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
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Web.Services;
using System.Data;
using System.Text;
using Globals;

namespace Web.pages
{
    public partial class cloudAccountEdit : System.Web.UI.Page
    {
        dataAccess dc = new dataAccess();
        acUI.acUI ui = new acUI.acUI();

        protected void Page_Load(object sender, EventArgs e)
        {
            if (!Page.IsPostBack)
            {
				ltAccounts.Text = GetAccounts("");
				
				//one time get of the Provider list.
				ltProviders.Text = GetProviders();
            }
        }
		
		public string GetProviders() {
			string sOptionHTML = "";
			
			CloudProviders cp = ui.GetCloudProviders();
			if (cp != null)
			{
				foreach (Provider p in cp.Values) {
					sOptionHTML += "<option value=\"" + p.Name + "\">" + p.Name + "</option>";
				}
			}
		
			return sOptionHTML;
		}
		public string GetAccounts(string sSearch) {
            string sSQL = "";
            string sErr = "";
			string sWhereString = "";

            if (sSearch.Length > 0)
            {
                //split on spaces
                int i = 0;
                string[] aSearchTerms = sSearch.Split(' ');
                for (i = 0; i <= aSearchTerms.Length - 1; i++)
                {
                    //if the value is a guid, it's an existing task.
                    //otherwise it's a new task.
                    if (aSearchTerms[i].Length > 0)
                    {
                        sWhereString = " and (account_name like '%" + aSearchTerms[i] + "%' " +
                            "or account_number like '%" + aSearchTerms[i] + "%' " +
                            "or provider like '%" + aSearchTerms[i] + "%' " +
                            "or login_id like '%" + aSearchTerms[i] + "%') ";
                    }
                }
            }

            sSQL = "select account_id, account_name, account_number, provider, login_id, auto_manage_security," +
                " case is_default when 1 then 'Yes' else 'No' end as is_default" +
                " from cloud_account" +
                " where 1=1 " + sWhereString +
                " order by is_default desc, account_name";

            DataTable dt = new DataTable();
            if (!dc.sqlGetDataTable(ref dt, sSQL, ref sErr))
            {
                ui.RaiseError(Page, sErr, true, "");
            }
			
            string sHTML = "";

            //the first DataColumn is the "id"
            // string sIDColumnName = sDataColumns[0];

            //buld the table
            sHTML += "<table class=\"jtable\" cellspacing=\"1\" cellpadding=\"1\" width=\"99%\">";
            sHTML += "<tr>";
            sHTML += "<th class=\"chkboxcolumn\">";
            sHTML += "<input type=\"checkbox\" class=\"chkbox\" id=\"chkAll\" />";
            sHTML += "</th>";

            sHTML += "<th sortcolumn=\"account_name\">Account Name</th>";
            sHTML += "<th sortcolumn=\"account_number\">Account Number</th>";
            sHTML += "<th sortcolumn=\"provider\">Type</th>";
            sHTML += "<th sortcolumn=\"login_id\">Login ID</th>";
            sHTML += "<th sortcolumn=\"is_default\">Default?</th>";

            sHTML += "</tr>";

            //loop rows
            foreach (DataRow dr in dt.Rows)
            {
                sHTML += "<tr account_id=\"" + dr["account_id"].ToString() + "\">";
                sHTML += "<td class=\"chkboxcolumn\">";
                sHTML += "<input type=\"checkbox\" class=\"chkbox\"" +
                    " id=\"chk_" + dr[0].ToString() + "\"" +
                    " object_id=\"" + dr[0].ToString() + "\"" +
                    " tag=\"chk\" />";
                sHTML += "</td>";

                sHTML += "<td tag=\"selectable\">" + dr["account_name"].ToString() +  "</td>";
                sHTML += "<td tag=\"selectable\">" + dr["account_number"].ToString() +  "</td>";
                sHTML += "<td tag=\"selectable\">" + dr["provider"].ToString() +  "</td>";
                sHTML += "<td tag=\"selectable\">" + dr["login_id"].ToString() +  "</td>";
                sHTML += "<td tag=\"selectable\">" + dr["is_default"].ToString() +  "</td>";

                sHTML += "</tr>";
            }

            sHTML += "</table>";
			
			return sHTML;
		}

        #region "Web Methods"
        [WebMethod(EnableSession = true)]
        public static string wmGetAccounts(string sSearch)
        {
			cloudAccountEdit ca = new cloudAccountEdit();
            return ca.GetAccounts(sSearch);
        }
	
        [WebMethod(EnableSession = true)]
        public static string DeleteAccounts(string sDeleteArray)
        {
            dataAccess dc = new dataAccess();
            acUI.acUI ui = new acUI.acUI();
            string sSql = null;
            string sErr = "";

            if (sDeleteArray.Length < 36)
                return "";

            sDeleteArray = ui.QuoteUp(sDeleteArray);

            DataTable dt = new DataTable();
            // get a list of ids that will be deleted for the log
            sSql = "select account_id, account_name, provider, login_id from cloud_account where account_id in (" + sDeleteArray + ")";
            if (!dc.sqlGetDataTable(ref dt, sSql, ref sErr))
                throw new Exception(sErr);

            try
            {

                dataAccess.acTransaction oTrans = new dataAccess.acTransaction(ref sErr);

                sSql = "delete from cloud_account where account_id in (" + sDeleteArray + ")";
                oTrans.Command.CommandText = sSql;
                if (!oTrans.ExecUpdate(ref sErr))
                    throw new Exception(sErr);

				//refresh the cloud account list in the session
                if (!ui.PutCloudAccountsInSession(ref sErr))
					throw new Exception(sErr);

                oTrans.Commit();
            }
            catch (Exception ex)
            {
                throw new Exception(ex.Message);
            }

            // if we made it here, so save the logs
            foreach (DataRow dr in dt.Rows)
            {
                ui.WriteObjectDeleteLog(Globals.acObjectTypes.CloudAccount, dr["account_id"].ToString(), dr["account_name"].ToString(), dr["provider"].ToString() + " Account for LoginID [" + dr["login_id"].ToString() + "] Deleted");
            }

            return sErr;
        }

        [WebMethod(EnableSession = true)]
        public static string wmSaveAccount(string sMode, string sAccountID, string sAccountName, string sAccountNumber, string sProvider, 
			string sLoginID, string sLoginPassword, string sLoginPasswordConfirm, string sIsDefault, string sAutoManageSecurity)
        {
            string sErr = null;

			try
			{
				if (sMode == "add")
	            {
					CloudAccount ca = CloudAccount.DBCreateNew(sAccountName, sAccountNumber, sProvider, 
					                                           sLoginID, sLoginPassword, sIsDefault, ref sErr);
					if (ca == null) {
						return "{}";
					}
					else
					{
						return ca.AsJSON();
					}
				}
	            else if (sMode == "edit")
	            {
					//TODO: test the two passwords and confirm they match!
					
					CloudAccount ca = new CloudAccount(sAccountID);
					if (ca == null) {
						return "{}";
					}
					else
					{
						ca.ID = sAccountID;
						ca.Name = sAccountName;
						ca.AccountNumber = sAccountNumber;
						ca.LoginID = sLoginID;
						ca.LoginPassword = sLoginPassword;
						ca.IsDefault = (sIsDefault == "1" ? true : false);
						
						//note: simply changing the provider NAME will tell the update method to switch providers.
						//no need to redo the whole object
						ca.Provider.Name = sProvider;
						
						if (!ca.DBUpdate(ref sErr))
							throw new Exception(sErr);	
						
						return ca.AsJSON();
					}
				}
			}
			catch (Exception ex)
			{
			    throw new Exception("Error: General Exception: " + ex.Message);
			}
			
            // no errors to here, so return an empty string
            return "{}";
        }

        [WebMethod(EnableSession = true)]
        public static string wmGetCloudAccount(string sID)
        {
			CloudAccount ca = new CloudAccount(sID);
			if (ca == null) {
				return "{'result':'fail','error':'Failed to get Cloud Account details for Cloud Account ID [" + sID + "].'}";
			}
            else
            {
				return ca.AsJSON();
			}
        }

        [WebMethod(EnableSession = true)]
        public static string wmGetProviderClouds(string sProvider)
        {
			acUI.acUI ui = new acUI.acUI();
			
			CloudProviders cp = ui.GetCloudProviders();
			if (cp == null) {
				return "{'result':'fail','error':'Failed to get Provider details for [" + sProvider + "].'}";
			}
            else
			{
				Provider p = cp[sProvider];
				if (p != null)
					return p.AsJSON();
				else
					return "{'result':'fail','error':'Failed to get Provider details for [" + sProvider + "].'}";
			}
		}

        [WebMethod(EnableSession = true)]
        public static string GetKeyPairs(string sID)
        {

            dataAccess dc = new dataAccess();
            string sSql = null;
            string sErr = null;
            string sHTML = "";

            sSql = "select keypair_id, keypair_name, private_key, passphrase" +
                " from cloud_account_keypair" +
                " where account_id = '" + sID + "'";

            DataTable dt = new DataTable();
            if (!dc.sqlGetDataTable(ref dt, sSql, ref sErr))
            {
                throw new Exception(sErr);
            }

            if (dt.Rows.Count > 0)
            {
                sHTML += "<ul>";
                foreach (DataRow dr in dt.Rows)
                {
                    string sName = dr["keypair_name"].ToString();

                    //DO NOT send these back to the client.
                    string sPK = (object.ReferenceEquals(dr["private_key"], DBNull.Value) ? "false" : "true");
                    string sPP = (object.ReferenceEquals(dr["passphrase"], DBNull.Value) ? "false" : "true");
                    //sLoginPassword = "($%#d@x!&";

                    sHTML += "<li class=\"ui-widget-content ui-corner-all keypair\" id=\"kp_" + dr["keypair_id"].ToString() + "\" has_pk=\"" + sPK + "\" has_pp=\"" + sPP + "\">";
                    sHTML += "<span class=\"keypair_label pointer\">" + sName + "</span>";
                    sHTML += "<span class=\"keypair_icons pointer\"><img src=\"../images/icons/fileclose.png\" class=\"keypair_delete_btn\" /></span>";
                    sHTML += "</li>";
                }
                sHTML += "</ul>";
            }
            else
            {
                sHTML += "";
            }


            return sHTML;
        }

        [WebMethod(EnableSession = true)]
        public static string SaveKeyPair(string sKeypairID, string sAccountID, string sName, string sPK, string sPP)
        {
            acUI.acUI ui = new acUI.acUI();

			if (string.IsNullOrEmpty(sName))
                return "KeyPair Name is Required.";

            //we encoded this in javascript before the ajax call.
            //the safest way to unencode it is to use the same javascript lib.
            //(sometimes the javascript and .net libs don't translate exactly, google it.)
            sPK = ui.unpackJSON(sPK);

            bool bUpdatePK = false;
            if (sPK != "-----BEGIN RSA PRIVATE KEY-----\n**********\n-----END RSA PRIVATE KEY-----")
            {

                //we want to make sure it's not just the placeholder, but DOES have the wrapper.
                //and 61 is the lenght of the wrapper with no content... effectively empty
                if (sPK.StartsWith("-----BEGIN RSA PRIVATE KEY-----\n") && sPK.EndsWith("\n-----END RSA PRIVATE KEY-----"))
                {
                    //now, is there truly something in it?
                    string sContent = sPK.Replace("-----BEGIN RSA PRIVATE KEY-----", "").Replace("-----END RSA PRIVATE KEY-----", "").Replace("\n", "");
                    if (sContent.Length > 0)
                        bUpdatePK = true;
                    else
                        return "Private Key contained within:<br />-----BEGIN RSA PRIVATE KEY-----<br />and<br />-----END RSA PRIVATE KEY-----<br />cannot be blank.";
                }
                else
                {
                    return "Private Key must be contained within:<br />-----BEGIN RSA PRIVATE KEY-----<br />and<br />-----END RSA PRIVATE KEY-----";
                }
            }

            bool bUpdatePP = false;
            if (sPP != "!2E4S6789O")
                bUpdatePP = true;


            //all good, keep going


            dataAccess dc = new dataAccess();
            string sSQL = null;
            string sErr = null;

            try
            {
                if (string.IsNullOrEmpty(sKeypairID))
                {
                    //empty id, it's a new one.
                    string sPKClause = "";
                    if (bUpdatePK)
                        sPKClause = "'" + dc.EnCrypt(sPK) + "'";

                    string sPPClause = "null";
                    if (bUpdatePP)
                        sPPClause = "'" + dc.EnCrypt(sPP) + "'";

                    sSQL = "insert into cloud_account_keypair (keypair_id, account_id, keypair_name, private_key, passphrase)" +
                        " values ('" + ui.NewGUID() + "'," +
                        "'" + sAccountID + "'," +
                        "'" + sName.Replace("'", "''") + "'," +
                        sPKClause + "," +
                        sPPClause +
                        ")";
                }
                else
                {
                    string sPKClause = "";
                    if (bUpdatePK)
                        sPKClause = ", private_key = '" + dc.EnCrypt(sPK) + "'";

                    string sPPClause = "";
                    if (bUpdatePP)
                        sPPClause = ", passphrase = '" + dc.EnCrypt(sPP) + "'";

                    sSQL = "update cloud_account_keypair set" +
                        " keypair_name = '" + sName.Replace("'", "''") + "'" +
                        sPKClause + sPPClause +
                        " where keypair_id = '" + sKeypairID + "'";
                }

                if (!dc.sqlExecuteUpdate(sSQL, ref sErr))
                    throw new Exception(sErr);

            }
            catch (Exception ex)
            {

                throw new Exception(ex.Message);
            }




            //// add security log
            //// since this is not handled as a page postback, theres no "Viewstate" settings
            //// so 2 options either we keep an original setting for each value in hid values, or just get them from the db as part of the 
            //// update above, since we are already passing in 15 or so fields, lets just get the values at the start and reference them here
            //if (sMode == "edit")
            //{
            //    ui.WriteObjectChangeLog(Globals.acObjectTypes.CloudAccount, sAccountID, sAccountName, sOriginalName, sAccountName);
            //}
            //else
            //{
            //    ui.WriteObjectAddLog(Globals.acObjectTypes.CloudAccount, sAccountID, sAccountName, "Account Created");
            //}


            // no errors to here, so return an empty string
            return "";
        }

        [WebMethod(EnableSession = true)]
        public static string DeleteKeyPair(string sKeypairID)
        {
            dataAccess dc = new dataAccess();
            string sSQL = null;
            string sErr = "";

            try
            {
                sSQL = "delete from cloud_account_keypair where keypair_id = '" + sKeypairID + "'";
                if (!dc.sqlExecuteUpdate(sSQL, ref sErr))
                    throw new Exception(sErr);

                if (sErr != "")
                    throw new Exception(sErr);
            }
            catch (Exception ex)
            {
                throw new Exception(ex.Message);
            }

            return "";
        }
        #endregion
    }
}
