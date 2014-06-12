
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
import json
from catoui import uiCommon
from catocommon import catocommon
from catocloud import cloud

# methods for dealing with clouds and cloud accounts

class cloudMethods:
    db = None

    """ Clouds edit page """
    def wmGetCloudsTable(self):
        sHTML = ""
        pager_html = ""
        sFilter = uiCommon.getAjaxArg("sSearch")
        sPage = uiCommon.getAjaxArg("sPage")
        maxrows = 25

        c = cloud.Clouds(sFilter)
        if c.rows:
            start, end, pager_html = uiCommon.GetPager(len(c.rows), maxrows, sPage)

            for row in c.rows[start:end]:
                sHTML += "<tr cloud_id=\"" + row["ID"] + "\">"
                sHTML += "<td class=\"chkboxcolumn\">"
                sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                " id=\"chk_" + row["ID"] + "\"" \
                " tag=\"chk\" />"
                sHTML += "</td>"

                sHTML += "<td class=\"selectable\">%s</td>" % row["Name"]
                sHTML += "<td class=\"selectable\">%s</td>" % row["Provider"]
                sHTML += "<td class=\"selectable\">%s</td>" % row["APIUrl"]
                sHTML += "<td class=\"selectable\">%s</td>" % row["APIProtocol"]
                sHTML += "<td class=\"selectable\">%s</td>" % (row["DefaultAccount"] if row["DefaultAccount"] else "&nbsp;")

                sHTML += "</tr>"

        return json.dumps({"pager": uiCommon.packJSON(pager_html), "rows": uiCommon.packJSON(sHTML)})

    def wmGetProvidersList(self):
        sUserDefinedOnly = uiCommon.getAjaxArg("sUserDefinedOnly")
        sHTML = ""
        cp = cloud.CloudProviders(include_clouds=False, include_products=False)
        if cp:
            for name, p in cp.iteritems():
                if catocommon.is_true(sUserDefinedOnly):
                    if p.UserDefinedClouds:
                        sHTML += "<option value=\"" + name + "\">" + name + "</option>"
                else:
                    sHTML += "<option value=\"" + name + "\">" + name + "</option>"

        return sHTML

    def wmGetCloud(self):
        sID = uiCommon.getAjaxArg("sID")
        c = cloud.Cloud()
        c.FromID(sID)
        return c.AsJSON()

    def wmGetCloudAccountsJSON(self):
        provider = uiCommon.getAjaxArg("sProvider")
        ca = cloud.CloudAccounts(sFilter="", sProvider=provider)
        return ca.AsJSON()

    def wmSaveCloud(self):
        sMode = uiCommon.getAjaxArg("sMode")
        sCloudID = uiCommon.getAjaxArg("sCloudID")
        sCloudName = uiCommon.getAjaxArg("sCloudName")
        sProvider = uiCommon.getAjaxArg("sProvider")
        sAPIUrl = uiCommon.getAjaxArg("sAPIUrl")
        sAPIProtocol = uiCommon.getAjaxArg("sAPIProtocol")
        sDefaultAccountID = uiCommon.getAjaxArg("sDefaultAccountID")

        c = None

        if sMode == "add":
            c = cloud.Cloud.DBCreateNew(sCloudName, sProvider, sAPIUrl, sAPIProtocol, "", sDefaultAccountID)
            uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Cloud, c.ID, c.Name, "Cloud Created")

        elif sMode == "edit":
            c = cloud.Cloud()
            c.FromID(sCloudID)
            c.Name = sCloudName
            c.APIProtocol = sAPIProtocol
            c.APIUrl = sAPIUrl

            # no need to build a complete object, as the update is just updating the ID
            c.DefaultAccount = cloud.CloudAccount()
            c.DefaultAccount.ID = sDefaultAccountID

            # get a new provider by name
            c.Provider = cloud.Provider.FromName(sProvider)
            c.DBUpdate()

            uiCommon.WriteObjectPropertyChangeLog(catocommon.CatoObjectTypes.Cloud, c.ID, c.Name, sCloudName, c.Name)

        if c:
            return c.AsJSON()
        else:
            return json.dumps({"error": "Unable to save Cloud using mode [" + sMode + "]."})

    def wmDeleteClouds(self):
        sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
        sDeleteArray = uiCommon.QuoteUp(sDeleteArray)
        if not sDeleteArray:
            return json.dumps({"info": "Unable to delete - no selection."})

        # get important data that will be deleted for the log
        sSQL = "select cloud_id, cloud_name, provider from clouds where cloud_id in (%s)" % (sDeleteArray)
        rows = self.db.select_all_dict(sSQL)

        _, msg = cloud.Clouds.Delete(sDeleteArray.split(","))
        
        # if we made it here, save the logs
        for dr in rows:
            uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.Cloud, dr["cloud_id"], dr["cloud_name"], dr["provider"] + " Cloud Deleted.")

        if msg:
            return json.dumps({"info": msg})
        else:
            return json.dumps({"result": "success"})


    """ Cloud Accounts Edit page"""
    def wmGetCloudAccountsTable(self):
        sFilter = uiCommon.getAjaxArg("sSearch")
        sPage = uiCommon.getAjaxArg("sPage")
        maxrows = 25
        sHTML = ""
        pager_html = ""

        ca = cloud.CloudAccounts(sFilter)
        if ca.rows:
            start, end, pager_html = uiCommon.GetPager(len(ca.rows), maxrows, sPage)

            for row in ca.rows[start:end]:
                sHTML += "<tr account_id=\"" + row["ID"] + "\">"

                sHTML += "<td class=\"chkboxcolumn\">"
                sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                " id=\"chk_" + row["ID"] + "\"" \
                " tag=\"chk\" />"
                sHTML += "</td>"

                sHTML += "<td class=\"selectable\">%s</td>" % row["Name"]
                sHTML += "<td class=\"selectable\">%s</td>" % row["AccountNumber"]
                sHTML += "<td class=\"selectable\">%s</td>" % row["Provider"]
                sHTML += "<td class=\"selectable\">%s</td>" % row["LoginID"]
                sHTML += "<td class=\"selectable\">%s</td>" % (row["DefaultCloud"] if row["DefaultCloud"] else "&nbsp;")
                sHTML += "<td class=\"selectable\">%s</td>" % row["IsDefault"]

                sHTML += "</tr>"

        return json.dumps({"pager": uiCommon.packJSON(pager_html), "rows": uiCommon.packJSON(sHTML)})

    def wmGetCloudAccount(self):
        sID = uiCommon.getAjaxArg("sID")
        a = cloud.CloudAccount()
        a.FromID(sID)
        return a.AsJSON()

    def wmGetKeyPairs(self):
        sID = uiCommon.getAjaxArg("sID")
        sHTML = ""

        c = cloud.Cloud()
        c.FromID(sID)
        keypairs = c.GetKeyPairs()
        if keypairs:
            sHTML += "<ul>"
            for kp in keypairs:
                sName = kp["Name"]
                sPK = kp["HasPrivateKey"]
                sPP = kp["HasPassphrase"]

                sHTML += "<li class=\"ui-widget-content ui-corner-all keypair\" id=\"kp_" + kp["ID"] + "\" has_pk=\"" + sPK + "\" has_pp=\"" + sPP + "\">"
                sHTML += "<span class=\"keypair_label pointer\">" + sName + "</span>"
                sHTML += "<span class=\"keypair_icons pointer\"><span class=\"keypair_delete_btn ui-icon ui-icon-close forceinline\" /></span></span>"
                sHTML += "</li>"
            sHTML += "</ul>"
        else:
            sHTML += ""

        return sHTML

    def wmGetProvider(self):
        sProvider = uiCommon.getAjaxArg("sProvider")
        if sProvider:
            p = cloud.Provider.FromName(sProvider)
            return p.AsJSON()
        else:
            return json.dumps({"info": "No Cloud Accounts are defined."})

    def wmSaveAccount(self):
        sMode = uiCommon.getAjaxArg("sMode")
        sAccountID = uiCommon.getAjaxArg("sAccountID")
        sAccountName = uiCommon.getAjaxArg("sAccountName")
        sAccountNumber = uiCommon.getAjaxArg("sAccountNumber")
        sProvider = uiCommon.getAjaxArg("sProvider")
        sDefaultCloudID = uiCommon.getAjaxArg("sDefaultCloudID")
        sLoginID = uiCommon.getAjaxArg("sLoginID")
        sLoginPassword = uiCommon.getAjaxArg("sLoginPassword")
        sLoginPasswordConfirm = uiCommon.getAjaxArg("sLoginPasswordConfirm")
        sIsDefault = uiCommon.getAjaxArg("sIsDefault")
        # sAutoManageSecurity = uiCommon.getAjaxArg("sAutoManageSecurity")

        if sLoginPassword != sLoginPasswordConfirm:
            return json.dumps({"info": "Passwords must match."})

        if sMode == "add":
            ca = cloud.CloudAccount.DBCreateNew(sProvider, sAccountName, sLoginID, sLoginPassword, sAccountNumber, sDefaultCloudID, sIsDefault)
            uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.CloudAccount, ca.ID, ca.Name, "Account Created")

        elif sMode == "edit":
            ca = cloud.CloudAccount()
            ca.FromID(sAccountID)
            ca.ID = sAccountID
            ca.Name = sAccountName
            ca.AccountNumber = sAccountNumber
            ca.LoginID = sLoginID
            ca.LoginPassword = sLoginPassword
            ca.IsDefault = (True if sIsDefault == "1" else False)

            # get the cloud
            c = cloud.Cloud()
            c.FromID(sDefaultCloudID)
            if not c:
                return json.dumps({"error": "Unable to reconcile default Cloud from ID [%s]." % sDefaultCloudID})
            ca.DefaultCloud = c

            # note: we must reassign the whole provider
            # changing the name screws up the CloudProviders object in the session, which is writable! (oops)
            ca.Provider = cloud.Provider.FromName(sProvider)
            ca.DBUpdate()

            uiCommon.WriteObjectPropertyChangeLog(catocommon.CatoObjectTypes.CloudAccount, ca.ID, ca.Name, "", ca.Name)

        if ca:
            return ca.AsJSON()
        else:
            return json.dumps({"error": "Unable to save Cloud Account using mode [%s]." % sMode})

    def wmDeleteAccounts(self):
        sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
        if len(sDeleteArray) < 36:
            return json.dumps({"info": "Unable to delete - no selection."})

        sDeleteArray = uiCommon.QuoteUp(sDeleteArray)

        #  get data that will be deleted for the log
        sSQL = "select account_id, account_name, provider, login_id from cloud_account where account_id in (" + sDeleteArray + ")"
        rows = self.db.select_all_dict(sSQL)

        cloud.CloudAccounts.Delete(sDeleteArray.split(","))

        #  if we made it here, so save the logs
        for dr in rows:
            uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.CloudAccount, dr["account_id"], dr["account_name"], dr["provider"] + " Account for LoginID [" + dr["login_id"] + "] Deleted")

        return json.dumps({"result": "success"})

#    def wmGetProviderObjectTypes(self):
#        try:
#            sProvider = uiCommon.getAjaxArg("sProvider")
#            sHTML = ""
#            cp = providers.CloudProviders(include_clouds = False)
#            if cp:
#                p = cp[sProvider]
#                for i in p.GetAllObjectTypes.items():
#                    print i
#
#            return sHTML
#        except Exception:
#            uiCommon.log(traceback.format_exc())
#            return traceback.format_exc()

    def wmGetCloudObjectList(self):
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
            sHTML += "<p>%s</p>" % err
            sHTML += "</div>"
            sHTML += "</div>"

        return sHTML

    def DrawTableForType(self, sAccountID, sObjectType, dt):
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

        sHTML += "</tr>"

        # loop rows

        # remember, the properties themselves have the value
        for sObjectID, props in dt.iteritems():
            # crush the spaces... a javascript ID can't have spaces
            sJSID = sObjectID.strip().replace(" ", "")

            sHTML += "<tr>"
            sHTML += "<td class=\"chkboxcolumn\">"

            # not drawing the checkbox if there's no ID defined
            if sObjectID:
                sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                    " id=\"chk_" + sJSID + "\"" \
                    " object_id=\"" + sObjectID + "\"" \
                    " tag=\"chk\" />"

                sHTML += "</td>"

            # loop data columns
            for prop in props:
                uiCommon.log_nouser("%s - %s" % (prop.Name, prop.Value), 3)
                sValue = (prop.Value if prop.Value else "")
                sHTML += "<td>"

                # should we try to show an icon?
                if prop.HasIcon and sValue:
                    sHTML += "<img class=\"custom_icon\" src=\"static/images/custom/" + prop.Name.replace(" ", "").lower() + "_" + sValue.replace(" ", "").lower() + ".png\" alt=\"\" />"

                # if this is the "Tags" column, it might contain some xml... break 'em down
                if prop.Name == "Tags" and sValue:
                    try:
                        xDoc = catocommon.ET.fromstring(sValue)
                        if xDoc is not None:
                            sTags = ""
                            for xeTag in xDoc.findall("item"):
                                sTags += "<b>%s</b> : %s<br />" % (xeTag.findtext("key", ""), xeTag.findtext("value", ""))
                            sHTML += sTags
                    except:  # couldn't parse it.  hmmm....
                        uiCommon.log_nouser(traceback.format_exc())
                        # I guess just stick the value in there, but make it safe
                        sHTML += uiCommon.SafeHTML(sValue)
                else:
                    sHTML += (sValue if sValue else "&nbsp;")  # we're building a table, empty cells should still have &nbsp;

                sHTML += "</td>"

            sHTML += "</tr>"

        sHTML += "</table>"

        return sHTML

    def wmTestCloudConnection(self):
        sAccountID = uiCommon.getAjaxArg("sAccountID")
        sCloudID = uiCommon.getAjaxArg("sCloudID")

        c = cloud.Cloud()
        c.FromID(sCloudID)

        ca = cloud.CloudAccount()
        ca.FromID(sAccountID)

        # NOTE: the Cloud object has a *THIN* copy of the Provider (it doesn't include
        #    products or provider clouds.)
        # But, we actually need a full provider here, so go get it!

        full_provider = cloud.Provider.FromName(c.Provider.Name)
        cot = full_provider.GetObjectTypeByName(c.Provider.TestObject)
        if not cot:
            raise Exception("Unable to find object type [%s] on Provider [%s] in cloud_providers.xml" % (c.Provider.TestObject, c.Provider.Name))

        # different providers libs have different methods for building a url
        url = ""
        if c.Provider.Name.lower() == "amazon aws":
            # Amazon aws, Eucalyptus, and OpenStackAws
            from catocloud import aws
            awsi = aws.awsInterface()
            url, err = awsi.BuildURL(ca, c, cot)
            if err:
                raise Exception(err)
        else:  
            raise Exception("Testing connection to %s not yet supported." % (c.Provider.Name))

        if not url:
            raise Exception("Unable to build API URL.")
        result, err = catocommon.http_get(url, 30)
        if err:
            raise Exception(err)

        return json.dumps({"result": "success", "response": result})

    def wmSaveKeyPair(self):
        sKeypairID = uiCommon.getAjaxArg("sKeypairID")
        sCloudID = uiCommon.getAjaxArg("sCloudID")
        sName = uiCommon.getAjaxArg("sName")
        sPK = uiCommon.getAjaxArg("sPK")
        sPP = uiCommon.getAjaxArg("sPP")

        sPK = uiCommon.unpackJSON(sPK)

        c = cloud.Cloud()
        c.FromID(sCloudID)

        if not sKeypairID:
            # keypair_id not passed in, create a new one...
            c.AddKeyPair(sName, sPK, sPP)
        else:
            c.SaveKeyPair(sKeypairID, sName, sPK, sPP)

        return json.dumps({"result": "success"})

    def wmDeleteKeyPair(self):
        sCloudID = uiCommon.getAjaxArg("sCloudID")
        sKeypairID = uiCommon.getAjaxArg("sKeypairID")
        c = cloud.Cloud()
        c.FromID(sCloudID)
        c.DeleteKeyPair(sKeypairID)
        return json.dumps({"result": "success"})

    def wmCreateStaticClouds(self):
        success = cloud.create_static_clouds()
        if success:
            return json.dumps({"result": "success"})
        else:
            raise Exception("Unable to create Clouds.  Check the UI Log for more information.")
