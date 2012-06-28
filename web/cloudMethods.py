
# Copyright 2012 Cloud Sidekick
#  
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  
#     http:# www.apache.org/licenses/LICENSE-2.0
#  
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import traceback
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

import uiGlobals
import uiCommon
from catocommon import catocommon
from catocloud import cloud

# methods for dealing with clouds and cloud accounts

class cloudMethods:
    db = None
    
    """ Clouds edit page """
    def wmGetCloudsTable(self):
        try:
            sHTML = ""
            sFilter = uiCommon.getAjaxArg("sSearch")
            sHTML = ""
            
            ca = cloud.Clouds(sFilter)
            if ca.rows:
                for row in ca.rows:
                    sHTML += "<tr cloud_id=\"" + row["cloud_id"] + "\">"
                    sHTML += "<td class=\"chkboxcolumn\">"
                    sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                    " id=\"chk_" + row["cloud_id"] + "\"" \
                    " tag=\"chk\" />"
                    sHTML += "</td>"
                    
                    sHTML += "<td class=\"selectable\">" + row["cloud_name"] +  "</td>"
                    sHTML += "<td class=\"selectable\">" + row["provider"] +  "</td>"
                    sHTML += "<td class=\"selectable\">" + row["api_url"] +  "</td>"
                    sHTML += "<td class=\"selectable\">" + row["api_protocol"] +  "</td>"
                    
                    sHTML += "</tr>"
    
            return sHTML    
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetProvidersList(self):
        try:
            sUserDefinedOnly = uiCommon.getAjaxArg("sUserDefinedOnly")
            sHTML = ""
            cp = cloud.CloudProviders()
            if cp:
                for name, p in cp.iteritems():
                    if catocommon.is_true(sUserDefinedOnly):
                        if p.UserDefinedClouds:
                            sHTML += "<option value=\"" + name + "\">" + name + "</option>"
                    else:
                        sHTML += "<option value=\"" + name + "\">" + name + "</option>"
    
                    
            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()
    
    def wmGetCloud(self):
        try:
            sID = uiCommon.getAjaxArg("sID")
            c = cloud.Cloud()
            if c:
                c.FromID(sID)
                if c.ID:
                    return c.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get Cloud details for Cloud ID [" + sID + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetCloudAccountsJSON(self):
        try:
            provider = uiCommon.getAjaxArg("sProvider")
            ca = cloud.CloudAccounts(sFilter="", sProvider=provider)
            if ca:
                return ca.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get Cloud Accounts using filter [" + provider + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmSaveCloud(self):
        sMode = uiCommon.getAjaxArg("sMode")
        sCloudID = uiCommon.getAjaxArg("sCloudID")
        sCloudName = uiCommon.getAjaxArg("sCloudName")
        sProvider = uiCommon.getAjaxArg("sProvider")
        sAPIUrl = uiCommon.getAjaxArg("sAPIUrl")
        sAPIProtocol = uiCommon.getAjaxArg("sAPIProtocol")

        c = None
        try:
            if sMode == "add":
                c, sErr = cloud.Cloud.DBCreateNew(sCloudName, sProvider, sAPIUrl, sAPIProtocol)
                if sErr:
                    return "{\"error\" : \"" + sErr + "\"}"
                if c == None:
                    return "{\"error\" : \"Unable to create Cloud.\"}"

                uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.Cloud, c.ID, c.Name, "Cloud Created")
            elif sMode == "edit":
                c = cloud.Cloud()
                c.FromID(sCloudID)
                if c == None:
                    return "{\"error\" : \"Unable to get Cloud using ID [" + sCloudID + "].\"}"
                c.Name = sCloudName
                c.APIProtocol = sAPIProtocol
                c.APIUrl = sAPIUrl

                #get a new provider by name
                c.Provider = cloud.Provider.FromName(sProvider)
                result, msg = c.DBUpdate()
                if not result:
                    uiCommon.log(msg, 2)
                    return "{\"info\" : \"%s\"}" % msg
                
                uiCommon.WriteObjectPropertyChangeLog(uiGlobals.CatoObjectTypes.Cloud, c.ID, c.Name, sCloudName, c.Name)

            if c:
                return c.AsJSON()
            else:
                return "{\"error\" : \"Unable to save Cloud using mode [" + sMode + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmDeleteClouds(self):
        try:
            sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
            if len(sDeleteArray) < 36:
                return "{\"info\" : \"Unable to delete - no selection.\"}"
    
            sDeleteArray = uiCommon.QuoteUp(sDeleteArray)
            
            #get important data that will be deleted for the log
            sSQL = "select cloud_id, cloud_name, provider from clouds where cloud_id in (" + sDeleteArray + ")"
            rows = self.db.select_all_dict(sSQL)

            sSQL = "delete from clouds where cloud_id in (" + sDeleteArray + ")"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)
            
            #if we made it here, save the logs
            for dr in rows:
                uiCommon.WriteObjectDeleteLog(uiGlobals.CatoObjectTypes.Cloud, dr["cloud_id"], dr["cloud_name"], dr["provider"] + " Cloud Deleted.")
    
            return "{\"result\" : \"success\"}"
            
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

        
    """ Cloud Accounts Edit page"""
    def wmGetCloudAccountsTable(self):
        try:
            sFilter = uiCommon.getAjaxArg("sSearch")
            sHTML = ""
            
            ca = cloud.CloudAccounts(sFilter)
            if ca.rows:
                for row in ca.rows:
                    sHTML += "<tr account_id=\"" + row["account_id"] + "\">"
                    
                    if not row["has_ecosystems"]:
                        sHTML += "<td class=\"chkboxcolumn\">"
                        sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                        " id=\"chk_" + row["account_id"] + "\"" \
                        " tag=\"chk\" />"
                        sHTML += "</td>"
                    else:
                        sHTML += "<td>"
                        sHTML += "<span class=\"ui-icon ui-icon-info forceinline account_help_btn\"" \
                            " title=\"This account has associated Ecosystems and cannot be deleted.\"></span>"
                        sHTML += "</td>"
                    
                    sHTML += "<td class=\"selectable\">" + row["account_name"] +  "</td>"
                    sHTML += "<td class=\"selectable\">" + row["account_number"] +  "</td>"
                    sHTML += "<td class=\"selectable\">" + row["provider"] +  "</td>"
                    sHTML += "<td class=\"selectable\">" + row["login_id"] +  "</td>"
                    sHTML += "<td class=\"selectable\">" + row["is_default"] +  "</td>"
                    
                    sHTML += "</tr>"

            return sHTML    
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get Cloud Accounts using filter [" + sFilter + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetCloudAccount(self):
        try:
            sID = uiCommon.getAjaxArg("sID")
            a = cloud.CloudAccount()
            if a:
                a.FromID(sID)
                if a.ID:
                    return a.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get details for Cloud Account [" + sID + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetKeyPairs(self):
        try:
            sID = uiCommon.getAjaxArg("sID")
            sHTML = ""
    
            sSQL = "select keypair_id, keypair_name, private_key, passphrase" \
                " from cloud_account_keypair" \
                " where account_id = '" + sID + "'"
    
            dt = self.db.select_all_dict(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)
    
            if dt:
                sHTML += "<ul>"
                for dr in dt:
                    sName = dr["keypair_name"]
    
                    # DO NOT send these back to the client.
                    sPK = ("false" if not dr["private_key"] else "true")
                    sPP = ("false" if not dr["passphrase"] else "true")
                    # sLoginPassword = "($%#d@x!&"
    
                    sHTML += "<li class=\"ui-widget-content ui-corner-all keypair\" id=\"kp_" + dr["keypair_id"] + "\" has_pk=\"" + sPK + "\" has_pp=\"" + sPP + "\">"
                    sHTML += "<span class=\"keypair_label pointer\">" + sName + "</span>"
                    sHTML += "<span class=\"keypair_icons pointer\"><img src=\"static/images/icons/fileclose.png\" class=\"keypair_delete_btn\" /></span>"
                    sHTML += "</li>"
                sHTML += "</ul>"
            else:
                sHTML += ""
    
            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetProvider(self):
        try:
            sProvider = uiCommon.getAjaxArg("sProvider")
            
            cp = cloud.CloudProviders()
            if cp is None:
                return "{\"result\":\"fail\",\"error\":\"Failed to get Providers.\"}"
            else:
                p = cp[sProvider]
                if p is not None:
                    return p.AsJSON()
                else:
                    return "{\"result\":\"fail\",\"error\":\"Failed to get Provider details for [" + sProvider + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmSaveAccount(self):
        try:
            sMode = uiCommon.getAjaxArg("sMode")
            sAccountID = uiCommon.getAjaxArg("sAccountID")
            sAccountName = uiCommon.getAjaxArg("sAccountName")
            sAccountNumber = uiCommon.getAjaxArg("sAccountNumber")
            sProvider = uiCommon.getAjaxArg("sProvider")
            sLoginID = uiCommon.getAjaxArg("sLoginID")
            sLoginPassword = uiCommon.getAjaxArg("sLoginPassword")
            sLoginPasswordConfirm = uiCommon.getAjaxArg("sLoginPasswordConfirm")
            sIsDefault = uiCommon.getAjaxArg("sIsDefault")
            #sAutoManageSecurity = uiCommon.getAjaxArg("sAutoManageSecurity")

            if sLoginPassword != sLoginPasswordConfirm:
                return "{\"info\" : \"Passwords must match.\"}"

            if sMode == "add":
                ca, sErr = cloud.CloudAccount.DBCreateNew(sAccountName, sAccountNumber, sProvider, sLoginID, sLoginPassword, sIsDefault)
                if sErr:
                    return "{\"error\" : \"" + sErr + "\"}"
                    
                if ca is None:
                    return "{\"error\" : \"Unable to create Cloud Account.\"}"
                else:
                    uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.CloudAccount, ca.ID, ca.Name, "Account Created")
        
            elif sMode == "edit":
                ca = cloud.CloudAccount()
                ca.FromID(sAccountID)
                if ca is None:
                    return "{\"error\" : \"Unable to get Cloud Account using ID [" + sAccountID + "].\"}"
                else:
                    ca.ID = sAccountID
                    ca.Name = sAccountName
                    ca.AccountNumber = sAccountNumber
                    ca.LoginID = sLoginID
                    ca.LoginPassword = sLoginPassword
                    ca.IsDefault = (True if sIsDefault == "1" else False)
                    
                    # note: we must reassign the whole provider
                    # changing the name screws up the CloudProviders object in the session, which is writable! (oops)
                    ca.Provider = cloud.Provider.FromName(sProvider)
                    result, msg = ca.DBUpdate()
                    if not result:
                        uiCommon.log(msg, 2)
                        return "{\"info\" : \"%s\"}" % msg

#            # what's the original name?
#            sSQL = "select account_name from cloud_account where account_id = '" + self.ID + "'"
#            sOriginalName = db.select_col_noexcep(sSQL)
#            if db.error:
#                return None, "Error getting original Cloud Account Name:" + db.error
  
                    uiCommon.WriteObjectPropertyChangeLog(uiGlobals.CatoObjectTypes.CloudAccount, ca.ID, ca.Name, "", ca.Name)


            if ca:
                return ca.AsJSON()
            else:
                return "{\"error\" : \"Unable to save Cloud Account using mode [" + sMode + "].\"}"

        except Exception:
            uiCommon.log("Error: General Exception: " + traceback.format_exc())
        
        #  no errors to here, so return an empty object
        return "{}"

    def wmDeleteAccounts(self):
        try:
            sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
            if len(sDeleteArray) < 36:
                return "{\"info\" : \"Unable to delete - no selection.\"}"
    
            sDeleteArray = uiCommon.QuoteUp(sDeleteArray)

            #  get data that will be deleted for the log
            sSQL = "select account_id, account_name, provider, login_id from cloud_account where account_id in (" + sDeleteArray + ")"
            rows = self.db.select_all_dict(sSQL)


            sSQL = "delete from cloud_account_keypair where account_id in (" + sDeleteArray + ")"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            sSQL = "delete from cloud_account where account_id in (" + sDeleteArray + ")"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            self.db.tran_commit()

            #  if we made it here, so save the logs
            for dr in rows:
                uiCommon.WriteObjectDeleteLog(uiGlobals.CatoObjectTypes.CloudAccount, dr["account_id"], dr["account_name"], dr["provider"] + " Account for LoginID [" + dr["login_id"] + "] Deleted")

            return "{\"result\" : \"success\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

#    def wmGetProviderObjectTypes(self):
#        try:
#            sProvider = uiCommon.getAjaxArg("sProvider")
#            sHTML = ""
#            cp = providers.CloudProviders()
#            if cp:
#                p = cp[sProvider]
#                for i in p.GetAllObjectTypes.items():
#                    print i
#                    
#            return sHTML
#        except Exception:
#            uiCommon.log_nouser(traceback.format_exc(), 0)
#            return traceback.format_exc()
    
    def wmGetCloudObjectList(self):
        try:
            sAccountID = uiCommon.getAjaxArg("sAccountID")
            sCloudID = uiCommon.getAjaxArg("sCloudID")
            sObjectType = uiCommon.getAjaxArg("sObjectType")
            sHTML = ""

            dt, err = uiCommon.GetCloudObjectsAsList(sAccountID, sCloudID, sObjectType)
            if not err:
                if dt:
                    sHTML = self.DrawTableForType(sAccountID, sObjectType, dt)
                else:
                    sHTML = "No data returned from the Cloud Provider.<br />[%s]" % (err if err else "")
            else:
                sHTML += "<div class=\"ui-widget\" style=\"margin-top: 10px;\">"
                sHTML += "<div style=\"padding: 10px;\" class=\"ui-state-highlight ui-corner-all\">"
                sHTML += "<span style=\"float: left; margin-right: .3em;\" class=\"ui-icon ui-icon-info\"></span>"
                sHTML += "<p>" + err + "</p>"
                sHTML += "</div>"
                sHTML += "</div>"

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def DrawTableForType(self, sAccountID, sObjectType, dt):
        try:
            # we will need this at the bottom
            sSQL = "select eo.ecosystem_object_id, e.ecosystem_id, e.ecosystem_name" \
                " from ecosystem_object eo" \
                " join ecosystem e on eo.ecosystem_id = e.ecosystem_id" \
                " where e.account_id = '" + sAccountID + "'" \
                " and eo.ecosystem_object_type = '" + sObjectType + "'"

            ecosystems = self.db.select_all_dict(sSQL)
            if self.db.error:
                return self.db.error

            sHTML = ""

            # buld the table
            sHTML += "<table class=\"jtable\" cellspacing=\"1\" cellpadding=\"1\" width=\"99%\">"
            sHTML += "<tr>"
            sHTML += "<th class=\"chkboxcolumn\">"
            sHTML += "<input type=\"checkbox\" class=\"chkbox\" id=\"chkAll\" />"
            sHTML += "</th>"

            # loop column headers (by getting just one item in the dict)
            for prop in dt.itervalues().next():
                sHTML += "<th>"
                sHTML += prop.Label
                sHTML += "</th>"

            # the last column is hardcoded for ecosystems.
            sHTML += "<th>Ecosystems</th>"

            sHTML += "</tr>"

            # loop rows

            # remember, the properties themselves have the value
            for sObjectID, props in dt.iteritems():
                # crush the spaces... a javascript ID can't have spaces
                sJSID = sObjectID.strip().replace(" ","")

                sHTML += "<tr>"
                sHTML += "<td class=\"chkboxcolumn\">"
                
                # not drawing the checkbox if there's no ID defined, we can't add it to an ecosystem without an id
                if sObjectID:
                    sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                        " id=\"chk_" + sJSID + "\"" \
                        " object_id=\"" + sObjectID + "\"" \
                        " tag=\"chk\" />"
                
                    sHTML += "</td>"

                # loop data columns
                for prop in props:
                    print("%s - %s" % (prop.Name, prop.Value))
                    sValue = (prop.Value if prop.Value else "")
                    sHTML += "<td>"

                    # should we try to show an icon?
                    if prop.HasIcon and sValue:
                        sHTML += "<img class=\"custom_icon\" src=\"static/images/custom/" + prop.Name.replace(" ", "").lower() + "_" + sValue.replace(" ", "").lower() + ".png\" alt=\"\" />"
                
                    # if this is the "Tags" column, it might contain some xml... break 'em down
                    if prop.Name == "Tags" and sValue:
                        try:
                            xDoc = ET.fromstring(sValue)
                            if xDoc is not None:
                                sTags = ""
                                for xeTag in xDoc.findall("item"):
                                    sTags += "<b>%s</b> : %s<br />" % (xeTag.findtext("key", ""), xeTag.findtext("value", ""))
                                sHTML += sTags
                        except: # couldn't parse it.  hmmm....
                            print(traceback.format_exc())
                            # I guess just stick the value in there, but make it safe
                            sHTML += uiCommon.SafeHTML(sValue)
                    else:                         
                        sHTML += (sValue if sValue else "&nbsp;") # we're building a table, empty cells should still have &nbsp;

                    sHTML += "</td>"

                # spin the ecosystems query here, building a list of ecosystems associated with this object
                sHTML += "<td>"
                if ecosystems:
                    for ecosystem in ecosystems:
                        if ecosystem["ecosystem_object_id"] == sObjectID:
                            sHTML += "<span class=\"ecosystem_link pointer\" ecosystem_id=\"%s\">%s</span><br />" % (ecosystem["ecosystem_id"], ecosystem["ecosystem_name"])
                sHTML += "</td>"
                
                sHTML += "</tr>"

            sHTML += "</table>"

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmTestCloudConnection(self):
        try:
            sAccountID = uiCommon.getAjaxArg("sAccountID")
            sCloudID = uiCommon.getAjaxArg("sCloudID")
            
            c = cloud.Cloud()
            c.FromID(sCloudID)
            if c.ID is None:
                return "{\"result\":\"fail\",\"error\":\"Failed to get Cloud details for Cloud ID [" + sCloudID + "].\"}"
            
            ca = cloud.CloudAccount()
            ca.FromID(sAccountID)
            if ca.ID is None:
                return "{\"result\":\"fail\",\"error\":\"Failed to get Cloud Account details for Cloud Account ID [" + sAccountID + "].\"}"

            # get the test cloud object type for this provider
            cot = c.Provider.GetObjectTypeByName(c.Provider.TestObject)
            if cot is not None:
                if not cot.ID:
                    return "{\"result\":\"fail\",\"error\":\"Cannot find definition for requested object type [" + c.Provider.TestObject + "].\"}"
            else:
                return "{\"result\":\"fail\",\"error\":\"GetCloudObjectType failed for [" + c.Provider.TestObject + "].\"}"
            
            # different providers libs have different methods for building a url
            url = ""
            if c.Provider.Name.lower() =="openstack":
                """not yet implemented"""
                #ACWebMethods.openstackMethods acOS = new ACWebMethods.openstackMethods()
                #sXML = acOS.GetCloudObjectsAsXML(c.ID, cot, 0000BYREF_ARG0000sErr, null)
            else: #Amazon aws, Eucalyptus, and OpenStackAws
                import aws
                awsi = aws.awsInterface()
                url, err = awsi.BuildURL(ca, c, cot);            
                if err:
                    return "{\"result\":\"fail\",\"error\":\"" + uiCommon.packJSON(err) +"\"}"

            if not url:
                return "{\"result\":\"fail\",\"error\":\"Unable to build API URL.\"}"
            result, err = uiCommon.HTTPGet(url, 30)
            if err:
                return "{\"result\":\"fail\",\"error\":\"" + uiCommon.packJSON(err) + "\"}"
            
            return "{\"result\":\"success\",\"response\":\"" + uiCommon.packJSON(result) + "\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmSaveKeyPair(self):
        try:
            sKeypairID = uiCommon.getAjaxArg("sKeypairID")
            sAccountID = uiCommon.getAjaxArg("sAccountID")
            sName = uiCommon.getAjaxArg("sName")
            sPK = uiCommon.getAjaxArg("sPK")
            sPP = uiCommon.getAjaxArg("sPP")

            if not sName:
                return "KeyPair Name is Required."
    
            sPK = uiCommon.unpackJSON(sPK)
    
            bUpdatePK = False
            if sPK:
                bUpdatePK = True
    
            bUpdatePP = False
            if sPP and sPP != "!2E4S6789O":
                bUpdatePP = True
    
    
            if not sKeypairID:
                # empty id, it's a new one.
                sPKClause = ""
                if bUpdatePK:
                    sPKClause = "'" + catocommon.cato_encrypt(sPK) + "'"

                sPPClause = "null"
                if bUpdatePP:
                    sPPClause = "'" + catocommon.cato_encrypt(sPP) + "'"

                sSQL = "insert into cloud_account_keypair (keypair_id, account_id, keypair_name, private_key, passphrase)" \
                    " values ('" + catocommon.new_guid() + "'," \
                    "'" + sAccountID + "'," \
                    "'" + sName.replace("'", "''") + "'," \
                    + sPKClause + "," \
                    + sPPClause + \
                    ")"
            else:
                sPKClause = ""
                if bUpdatePK:
                    sPKClause = ", private_key = '" + catocommon.cato_encrypt(sPK) + "'"

                sPPClause = ""
                if bUpdatePP:
                    sPPClause = ", passphrase = '" + catocommon.cato_encrypt(sPP) + "'"

                sSQL = "update cloud_account_keypair set" \
                    " keypair_name = '" + sName.replace("'", "''") + "'" \
                    + sPKClause + sPPClause + \
                    " where keypair_id = '" + sKeypairID + "'"

            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log(self.db.error)
                return self.db.error

            return ""
        
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmDeleteKeyPair(self):
        try:
            sKeypairID = uiCommon.getAjaxArg("sKeypairID")
            
            sSQL = "delete from cloud_account_keypair where keypair_id = '" + sKeypairID + "'"
            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log(self.db.error)
                return self.db.error

            return ""

        except Exception:
            uiCommon.log(traceback.format_exc())
