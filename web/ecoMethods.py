
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

import os
import traceback
import urllib
from datetime import datetime
import hashlib
import base64
import hmac
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

import json
import uiGlobals
import uiCommon
from catocommon import catocommon
from catoecosystem import ecosystem
from catocloud import cloud

class ecoMethods:
    db = None

    def wmGetEcotemplate(self):
        try:
            sID = uiCommon.getAjaxArg("sID")
            et = ecosystem.Ecotemplate()
            if et:
                et.FromID(sID, bIncludeActions=False)
                if et.ID:
                    return et.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get Ecotemplate details for ID [" + sID + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetEcotemplatesTable(self):
        try:
            sHTML = ""
            sFilter = uiCommon.getAjaxArg("sSearch")
            ets = ecosystem.Ecotemplates(sFilter)
            if ets.rows:
                for row in ets.rows:
                    sHTML += "<tr ecotemplate_id=\"%s\">" % row["ecotemplate_id"]
                    sHTML += "<td class=\"chkboxcolumn\">"
                    sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                    " id=\"chk_%s\"" \
                    " object_id=\"%s\"" \
                    " tag=\"chk\" />" % (row["ecotemplate_id"], row["ecotemplate_id"])
                    sHTML += "</td>"
                    
                    sHTML += "<td class=\"selectable\">%s</td>" % row["ecotemplate_name"]
                    sHTML += "<td class=\"selectable\">%s</td>" % (row["ecotemplate_desc"] if row["ecotemplate_desc"] else "")
                    
                    sHTML += "</tr>"
    
            return sHTML    
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            
    def wmCreateEcotemplate(self):
        try:
            sName = uiCommon.getAjaxArg("sName")
            sDescription = uiCommon.getAjaxArg("sDescription")
            sStormFileSource = uiCommon.getAjaxArg("sStormFileSource")
            sStormFile = uiCommon.getAjaxArg("sStormFile")
    
            et = ecosystem.Ecotemplate()
            et.FromArgs(uiCommon.unpackJSON(sName), uiCommon.unpackJSON(sDescription))
            if et is not None:
                sSrc = uiCommon.unpackJSON(sStormFileSource)
                et.StormFileType = ("URL" if sSrc == "URL" else "Text")
                et.StormFile = uiCommon.unpackJSON(sStormFile)
                
                result, msg = et.DBSave()
                if result:
                    uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.Ecosystem, et.ID, et.Name, "Ecotemplate created.")
                    return "{\"ecotemplate_id\" : \"%s\"}" % et.ID
                else:
                    uiCommon.log(msg, 2)
                    return "{\"info\" : \"%s\"}" % msg
            else:
                return "{\"error\" : \"Unable to create Ecotemplate.\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmUpdateEcotemplateDetail(self):
        try:
            sEcoTemplateID = uiCommon.getAjaxArg("sEcoTemplateID")
            sColumn = uiCommon.getAjaxArg("sColumn")
            sValue = uiCommon.getAjaxArg("sValue")
    
            sUserID = uiCommon.GetSessionUserID()

            if uiCommon.IsGUID(sEcoTemplateID) and uiCommon.IsGUID(sUserID):
                et = ecosystem.Ecotemplate()
                et.FromID(sEcoTemplateID)
                
                if et:
                    # we encoded this in javascript before the ajax call.
                    # the safest way to unencode it is to use the same javascript lib.
                    # (sometimes the javascript and .net libs don't translate exactly, google it.)
                    sValue = uiCommon.unpackJSON(sValue)

                    #  check for existing name
                    if sColumn == "Name":
                        if et.Name == sValue:
                            return sValue + " exists, please choose another name."

                    # cool, update the class attribute by name, using getattr!
                    # python is so cool.. I don't even need to check if the attribute I wanna set exists.
                    # just set it
                    setattr(et, sColumn, sValue)
                    
                    bSuccess, msg = et.DBUpdate()
                    if bSuccess:
                        uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Ecosystem, sEcoTemplateID, sColumn, sValue)
                        return "{\"result\" : \"success\"}"
                    else:
                        uiCommon.log(msg, 2)
                        return "{\"info\" : \"%s\"}" % msg
                else:
                    uiCommon.log("Unable to update Ecotemplate. Missing or invalid id [" + sEcoTemplateID + "].")
                    return "Unable to update Ecotemplate. Missing or invalid id [" + sEcoTemplateID + "]."
                
                return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmUpdateEcotemplateStorm(self):
        try:
            sEcoTemplateID = uiCommon.getAjaxArg("sEcoTemplateID")
            sStormFileSource = uiCommon.getAjaxArg("sStormFileSource")
            sStormFile = uiCommon.getAjaxArg("sStormFile")
    
            sUserID = uiCommon.GetSessionUserID()

            if uiCommon.IsGUID(sEcoTemplateID) and uiCommon.IsGUID(sUserID):
                et = ecosystem.Ecotemplate()
                et.FromID(sEcoTemplateID)
                
                if et:
                    et.StormFileType = uiCommon.unpackJSON(sStormFileSource)
                    et.StormFile = uiCommon.unpackJSON(sStormFile)
                    
                    bSuccess, msg = et.DBUpdate()
                    if bSuccess:
                        uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Ecosystem, sEcoTemplateID, "StormFileType", sStormFileSource)
                        uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Ecosystem, sEcoTemplateID, "StormFile", sStormFile)
                        return "{\"result\" : \"success\"}"
                    else:
                        uiCommon.log(msg, 2)
                        return "{\"info\" : \"%s\"}" % msg
                else:
                    uiCommon.log("Unable to update Ecotemplate. Missing or invalid id [" + sEcoTemplateID + "].")
                    return "Unable to update Ecotemplate. Missing or invalid id [" + sEcoTemplateID + "]."
                
                return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmDeleteEcotemplates(self):
        try:
            sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
            if len(sDeleteArray) < 36:
                return "{\"info\" : \"Unable to delete - no selection.\"}"
    
            sDeleteArray = uiCommon.QuoteUp(sDeleteArray)
            
            # can't delete it if it's referenced.
            sSQL = "select count(*) from ecosystem where ecotemplate_id in (" + sDeleteArray + ")"
            iResults = self.db.select_col_noexcep(sSQL)

            if not iResults:
                sSQL = "delete from ecotemplate_action where ecotemplate_id in (" + sDeleteArray + ")"
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log_nouser(self.db.error, 0)
                
                sSQL = "delete from ecotemplate where ecotemplate_id in (" + sDeleteArray + ")"
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log_nouser(self.db.error, 0)
                
                #if we made it here, save the logs
                uiCommon.WriteObjectDeleteLog(uiGlobals.CatoObjectTypes.EcoTemplate, "", "", "Ecosystem Templates(s) Deleted [" + sDeleteArray + "]")
            else:
                return "{\"info\" : \"Unable to delete - %d Ecosystems are referenced by these templates.\"}" % iResults
                
            return "{\"result\" : \"success\"}"
            
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmCopyEcotemplate(self):
        try:
            sEcoTemplateID = uiCommon.getAjaxArg("sEcoTemplateID")
            sNewName = uiCommon.getAjaxArg("sNewName")
            
            if sEcoTemplateID and sNewName:
    
                # have to instantiate one to copy it
                et = ecosystem.Ecotemplate()
                et.FromID(sEcoTemplateID)
                if et is not None:
                    result, msg = et.DBCopy(sNewName)
                    if not result:
                        return "{\"error\" : \"%s\"}" % msg
                    
                    # returning the ID indicates success...
                    return "{\"ecotemplate_id\" : \"%s\"}" % et.ID
                else:
                    uiCommon.log("Unable to get Template [" + sEcoTemplateID + "] to copy.")
                    return "{\"info\" : \"Unable to get Template [" + sEcoTemplateID + "] to copy.\"}"
            else:
                return "{\"info\" : \"Unable to Copy - New name and source ID are both required.\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetEcotemplateEcosystems(self):
        try:
            sEcoTemplateID = uiCommon.getAjaxArg("sEcoTemplateID")
        
            sHTML = ""

            if sEcoTemplateID:
                sSQL = "select ecosystem_id, ecosystem_name, ecosystem_desc" \
                    " from ecosystem" \
                    " where ecotemplate_id = '" + sEcoTemplateID + "'" \
                    " and account_id = '" + uiCommon.GetCookie("selected_cloud_account") + "'" \
                    " order by ecosystem_name"

                dt = self.db.select_all_dict(sSQL)
                if self.db.error:
                    uiCommon.log_nouser(self.db.error, 0)

                if dt:
                    sHTML += "<ul>"
                    for dr in dt:
                        sEcosystemID = dr["ecosystem_id"]
                        sEcosystemName = dr["ecosystem_name"]
                        sDesc = (dr["ecosystem_desc"] if dr["ecosystem_desc"] else "")
                        sDesc = sDesc.replace("\"", "").replace("'", "")

                        sHTML += "<li class=\"ui-widget-content ui-corner-all\"" \
                            " ecosystem_id=\"" + sEcosystemID + "\"" \
                            "\">"
                        sHTML += "<div class=\"step_header_title ecosystem_name pointer\">"
                        sHTML += "<img src=\"static/images/icons/ecosystems_24.png\" alt=\"\" /> " + sEcosystemName
                        sHTML += "</div>"

                        sHTML += "<div class=\"step_header_icons\">"

                        # if there's a description, show a tooltip
                        if sDesc:
                            sHTML += "<span class=\"ui-icon ui-icon-info ecosystem_tooltip\" title=\"" + sDesc + "\"></span>"

                        sHTML += "</div>"
                        sHTML += "<div class=\"clearfloat\"></div>"
                        sHTML += "</li>"

                    sHTML += "</ul>"
            else:
                uiCommon.log("Unable to get Ecosystems - Missing Ecotemplate ID")

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmAddEcotemplateAction(self):
        try:
            sEcoTemplateID = uiCommon.getAjaxArg("sEcoTemplateID")
            sActionName = uiCommon.getAjaxArg("sActionName")
            sOTID = uiCommon.getAjaxArg("sOTID")
    
            if not sEcoTemplateID or not sActionName or not sOTID:
                uiCommon.log("Missing or invalid Ecotemplate ID, Action Name or Task.")
    
            sSQL = "insert into ecotemplate_action " \
                 " (action_id, action_name, ecotemplate_id, original_task_id)" \
                 " values (" \
                 " '" + catocommon.new_guid() + "'," \
                 " '" + sActionName + "'," \
                 " '" + sEcoTemplateID + "'," \
                 " '" + sOTID + "'" \
                 ")"
    
            if not self.db.exec_db_noexcep(sSQL):
                # don't raise an error if its just a PK collision.  That just means it's already there.
                if "Duplicate entry:" not in self.db.error:
                    uiCommon.log_nouser(self.db.error, 0)
    
            uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.EcoTemplate, sEcoTemplateID, "", "Action Added : [" + sActionName + "]")
    
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    # delete an Action
    def wmDeleteEcotemplateAction(self):
        try:
            sActionID = uiCommon.getAjaxArg("sActionID")
    
            if not sActionID:
                return ""

            sSQL = "delete from action_plan where action_id = '" + sActionID + "'"
            sSQL = sSQL
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            sSQL = "delete from action_schedule where action_id = '" + sActionID + "'"
            sSQL = sSQL
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            sSQL = "delete from ecotemplate_action where action_id = '" + sActionID + "'"
            sSQL = sSQL
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            self.db.tran_commit()

            #  if we made it here, so save the logs
            uiCommon.WriteObjectDeleteLog(uiGlobals.CatoObjectTypes.EcoTemplate, "", "", "Action [" + sActionID + "] removed from Ecotemplate.")
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

        return ""

    def wmGetEcotemplateActions(self):
        sEcoTemplateID = uiCommon.getAjaxArg("sEcoTemplateID")

        sHTML = ""

        try:
            if sEcoTemplateID:
                sSQL = "select ea.action_id, ea.action_name, ea.category, ea.action_desc, ea.action_icon, ea.original_task_id, ea.task_version," \
                    " t.task_id, t.task_code, t.task_name," \
                    " ea.parameter_defaults as action_param_xml, t.parameter_xml as task_param_xml" \
                    " from ecotemplate_action ea" \
                    " left outer join task t on ea.original_task_id = t.original_task_id" \
                    " and t.default_version = 1" \
                    " where ea.ecotemplate_id = '" + sEcoTemplateID + "'" \
                    " order by ea.category, ea.action_name"

                dt = self.db.select_all_dict(sSQL)
                if self.db.error:
                    uiCommon.log_nouser(self.db.error, 0)

                if dt:
                    for dr in dt:
                        sHTML += " <li class=\"ui-widget-content ui-corner-all action pointer\" id=\"ac_" + dr["action_id"] + "\">"
                        sHTML += self.DrawEcotemplateAction(dr)
                        sHTML += " </li>"
            else:
                uiCommon.log("Unable to get Actions - Missing Ecotemplate ID")

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
    
    def DrawEcotemplateAction(self, dr):
        try:
            sHTML = ""

            # sActionID = dr["action_id"]
            sActionName = dr["action_name"]
            sCategory = (dr["category"] if dr["category"] else "")
            sDesc = (dr["action_desc"] if dr["action_desc"] else "")
            sIcon = ("action_default_48.png" if not dr["action_icon"] else dr["action_icon"])
            sOriginalTaskID =(dr["original_task_id"] if dr["original_task_id"] else "")
            sTaskID = (dr["task_id"] if dr["task_id"] else "")
            sTaskCode = (dr["task_code"] if dr["task_code"] else "Error")
            sTaskName = (dr["task_name"] if dr["task_name"] else "Task no longer exists.")
            sVersion = (str(dr["task_version"]) if dr["task_version"] else "")
            sTaskParameterXML = (dr["task_param_xml"] if dr["task_param_xml"] else "")
            # sActionParameterXML = ("" if not dr["action_param_xml"]) else dr["action_param_xml"])

            sHTML += "<div class=\"ui-state-default step_header\">"

            sHTML += "<div class=\"step_header_title\">"
            sHTML += "<span class=\"action_category_lbl\">" + (sCategory + " - " if sCategory else "") + "</span>"
            sHTML += "<span class=\"action_name_lbl\">" + sActionName + "</span>"
            sHTML += "</div>"

            sHTML += "<div class=\"step_header_icons\">"
            sHTML += "<span class=\"ui-icon ui-icon-close action_remove_btn\" remove_id=\"" + sActionName + "\"" \
                " title=\"Delete\"></span>"
            sHTML += "</div>"

            sHTML += "</div>"


            # gotta clear the floats
            sHTML += "<div class=\"ui-widget-content step_detail\">"

            # Action Name
            sHTML += "Action: \n"
            sHTML += "<input type=\"text\" " \
                " column=\"action_name\"" \
                " class=\"code\"" \
                " value=\"" + sActionName + "\" />"

            # Category
            sHTML += "Category: \n"
            sHTML += "<input type=\"text\" " \
                " column=\"category\"" \
                " class=\"code\"" \
                " value=\"" + sCategory + "\" />"

            # Icon
            sHTML += "Icon: \n"
            sHTML += "<img class=\"action_icon\" src=\"static/images/actions/" + sIcon + "\" />\n"

            sHTML += "<br />"

            # Description
            sHTML += "Description:<br />\n"
            sHTML += "<textarea rows=\"2\"" \
                " column=\"action_desc\"" \
                " class=\"code\"" \
                ">" + sDesc + "</textarea>\n"

            sHTML += "<br />"

            # Task
            # hidden field
            sHTML += "<input type=\"hidden\" " \
                " column=\"original_task_id\"" \
                " value=\"" + sOriginalTaskID + "\" />"

            # visible stuff
            sHTML += "Task: \n"
            sHTML += "<input type=\"text\"" \
                " onkeydown=\"return false;\"" \
                " onkeypress=\"return false;\"" \
                " is_required=\"true\"" \
                " class=\"code w75pct task_name\"" \
                " value=\"" + sTaskCode + " : " + sTaskName + "\" />\n"
            if sTaskID != "":
                sHTML += "<span class=\"ui-icon ui-icon-pencil forceinline task_open_btn pointer\" title=\"Edit Task\"" \
                    " task_id=\"" + sTaskID + "\"></span>\n"
                sHTML += "<span class=\"ui-icon ui-icon-print forceinline task_print_btn pointer\" title=\"View Task\"" \
                    " task_id=\"" + sTaskID + "\"" \
                    " src=\"static/images/icons/printer.png\"></span>\n"

            # NOT SURE if this is a requirement.  The looping actually slows things down quite a bit
            # so I don't mind not doing it.

            # versions
            if uiCommon.IsGUID(sOriginalTaskID):
                sHTML += "<br />"
                sHTML += "Version: \n"
                sHTML += "<select " \
                    " column=\"task_version\"" \
                    " reget_on_change=\"true\">\n"
                # default
                sHTML += "<option " + (" selected=\"selected\"" if sVersion == "" else "") + " value=\"\">Default</option>\n"

                sSQL = "select version from task" \
                    " where original_task_id = '" + sOriginalTaskID + "'" \
                    " order by version"
                dtVer = self.db.select_all_dict(sSQL)
                if self.db.error:
                    return "Database Error:" + self.db.error

                if dtVer:
                    for drVer in dtVer:
                        sHTML += "<option " + (" selected=\"selected\"" if sVersion == str(drVer["version"]) else "") + \
                            " value=\"" + str(drVer["version"]) + "\">" + \
                            str(drVer["version"]) + "</option>\n"

                sHTML += "</select>\n"


            # we have the parameter xml for the task here.
            # let's peek.  if there are parameters, show the button
            # if any are "required", but a ! by it.
            if sTaskParameterXML:
                xDoc = ET.fromstring(sTaskParameterXML)
                if xDoc is not None:
                    xParams = xDoc.findall("parameter")
                    if xParams is not None:
                        # there are task params!  draw the edit link

                        # are any of them required?
                        xRequired = xDoc.findall("parameter[@required='true']")

                        # # and most importantly, do the required ones have values?
                        # # this should be in a loop of xRequired, and looking in the other XML document.
                        # xEmpty1 = xDoc.findall("/parameters/parameter[@required='true']/values[not(text())]")
                        # xEmpty2 = xDoc.findall("/parameters/parameter[@required='true']/values[not(node())]")


                        sHTML += "<hr />"
                        sHTML += "<div class=\"action_param_edit_btn pointer\" style=\"vertical-align: bottom;\">"

                        if len(xRequired) > 0: #and (xEmpty1.Count() > 0 or xEmpty2.Count() > 0):
                            sHTML += "<img src=\"static/images/icons/status_unknown_16.png\" />"
                        else:
                            sHTML += "<span class=\"ui-icon ui-icon-pencil forceinline\"></span>"

                        sHTML += "<span> Edit Parameters</span>"
                        sHTML += "<span> (" + str(len(xParams)) + ")</span>"

                        # close the div
                        sHTML += "</div>"

            sHTML += "</div>"

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetEcotemplateAction(self):
        try:
            sActionID = uiCommon.getAjaxArg("sActionID")
    
            sHTML = ""

            if sActionID:
                sSQL = "select ea.action_id, ea.action_name, ea.category, ea.action_desc, ea.action_icon, ea.original_task_id, ea.task_version," \
                    " t.task_id, t.task_code, t.task_name," \
                    " ea.parameter_defaults as action_param_xml, t.parameter_xml as task_param_xml" \
                    " from ecotemplate_action ea" \
                    " join task t on ea.original_task_id = t.original_task_id" \
                    " and t.default_version = 1" \
                    " where ea.action_id = '" + sActionID + "'"

                dr = self.db.select_row_dict(sSQL)
                if self.db.error:
                    uiCommon.log_nouser(self.db.error, 0)

                # GetDataRow returns a message if there are no rows...
                if dr:
                    sHTML = self.DrawEcotemplateAction(dr)
            else:
                uiCommon.log("Unable to get Actions - Missing Ecotemplate ID")

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)


    
    def wmUpdateEcoTemplateAction(self):
        try:
            sEcoTemplateID = uiCommon.getAjaxArg("sEcoTemplateID")
            sActionID = uiCommon.getAjaxArg("sActionID")
            sColumn = uiCommon.getAjaxArg("sColumn")
            sValue = uiCommon.getAjaxArg("sValue")
            
            sUserID = uiCommon.GetSessionUserID()

            if uiCommon.IsGUID(sEcoTemplateID) and uiCommon.IsGUID(sUserID):
                # we encoded this in javascript before the ajax call.
                # the safest way to unencode it is to use the same javascript lib.
                # (sometimes the javascript and .net libs don't translate exactly, google it.)
                sValue = uiCommon.unpackJSON(sValue)
                sValue = catocommon.tick_slash(sValue)
                
                #  check for existing name
                if sColumn == "action_name":
                    sSQL = "select action_id from ecotemplate_action where " \
                            " action_name = '" + sValue + "'" \
                            " and ecotemplate_id = '" + sEcoTemplateID + "'"

                    sValueExists = self.db.select_col_noexcep(sSQL)
                    if self.db.error:
                        uiCommon.log("Unable to check for existing names [" + sEcoTemplateID + "]." + self.db.error)

                    if sValueExists:
                        return sValue + " exists, please choose another value."

                sSetClause = sColumn + "='" + sValue + "'"

                # some columns on this table allow nulls... in their case an empty sValue is a null
                if sColumn == "action_desc" or sColumn == "category" or sColumn == "task_version":
                    if not sValue.replace(" ", ""):
                        sSetClause = sColumn + " = null"
                    else:
                        sSetClause = sColumn + "='" + sValue + "'"

                sSQL = "update ecotemplate_action set " + sSetClause + " where action_id = '" + sActionID + "'"

                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to update Ecotemplate Action [" + sActionID + "]." + self.db.error)

                uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.EcoTemplate, sEcoTemplateID, sActionID, "Action updated: [" + sSetClause + "]")
            else:
                uiCommon.log("Unable to update Ecotemplate Action. Missing or invalid Ecotemplate/Action ID.")

            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
        
    def wmGetActionIcons(self):
        try:
            # the icons are in the icons/actions directory
            # get a list of them all, and draw them on the picker dialog
            sIconHTML = ""
            dirList=os.listdir("static/images/actions")
            for fname in dirList:
                sIconHTML += "<img class='action_picker_icon' icon_name='" + fname + "' src='static/images/actions/" + fname + "' />"
        
            return sIconHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetEcotemplateStorm(self):
        try:
            sEcoTemplateID = uiCommon.getAjaxArg("sEcoTemplateID")

            sFileType = ""
            sURL = ""
            sFileDesc = ""
            sStormFileJSON = ""
            bIsValid = False
            
            bIsValid, sErr, sFileType, sURL, sFileDesc, sStormFileJSON = self.GetEcotemplateStormJSON(sEcoTemplateID)
            
            sb = []
            
            sb.append("{")
            sb.append("\"%s\" : \"%s\"," % ("IsValid", bIsValid))
            sb.append("\"%s\" : \"%s\"," % ("Error", uiCommon.packJSON(sErr)))
            sb.append("\"%s\" : \"%s\"," % ("FileType", sFileType))
            sb.append("\"%s\" : \"%s\"," % ("URL",  uiCommon.packJSON(sURL)))
            sb.append("\"%s\" : \"%s\"," % ("Description", uiCommon.packJSON(sFileDesc)))
            sb.append("\"%s\" : \"%s\"," % ("Text", uiCommon.packJSON(sStormFileJSON)))
            sb.append("\"%s\" : \"%s\"," % ("HTMLDescription", uiCommon.packJSON(uiCommon.FixBreaks(uiCommon.SafeHTML(sFileDesc)))))
            sb.append("\"%s\" : \"%s\"" % ("HTMLText", uiCommon.packJSON(uiCommon.FixBreaks(uiCommon.SafeHTML(sStormFileJSON)))))
            sb.append("}")
            
            return "".join(sb)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def GetEcotemplateStormJSON(self, sEcoTemplateID): 
        bIsValid = False
        sErr = ""
        sFileType = ""
        sURL = ""
        sFileDesc = ""
        sStormFileJSON = ""
        try:
            if sEcoTemplateID:
                sSQL = "select storm_file_type, storm_file" \
                    " from ecotemplate" \
                    " where ecotemplate_id = '" + sEcoTemplateID + "'"

                dr = self.db.select_row_dict(sSQL)
                if self.db.error:
                    uiCommon.log_nouser(self.db.error, 0)
                
                # now, we'll validate the json here as a safety precaution, but we're sending the whole storm file to the client
                # where the parameters and description will be parsed out and displayed.
                # this is really no different than where we send entire parameter_xml document to the client
                
                sFileType = (dr["storm_file_type"] if dr["storm_file_type"] else "")
                sStormFile = (dr["storm_file"] if dr["storm_file"] else "")
                
                if sStormFile:
                    if sFileType == "URL":
                        # if it's a URL we try: to get it and parse it.
                        # if we can't, we just send back a nice message.
                        
                        # for display purposes, we'll be sending back the URL as well as the results
                        sURL = sStormFile
                        
                        
                        # using our no fail routine here, error handling later if needed
                        try:
                            sStormFileJSON = uiCommon.HTTPGetNoFail(sURL)
                        except Exception:
                            sErr = "Error getting Storm from URL [" + sURL + "]. " + traceback.format_exc()
                    else:
                        # if it's not a URL we assume it's actual JSON text.
                        sStormFileJSON = sStormFile
                    
                    if sStormFileJSON:
                        try:
                            # the process is simple...
                            # 1) parse the json into a dict
                            # 2) make sure a few key sections exist
                            dic = json.loads(sStormFileJSON)
        
                            if dic.has_key("Description"):
                                sFileDesc = (dic["Description"] if dic["Description"] else "")
    
                            # VALIDATION
                            # we can test for certain values, and return false unless they exist.
                            if dic.has_key("Mappings") and dic.has_key("Resources"):
                                bIsValid = True
                            else:
                                sErr += "Document must contain a Mappings and a Resources section."
                                
                        except Exception:
                            sErr = traceback.format_exc()
                    else:
                        sErr = "Storm File is empty or URL returned nothing."
                else:
                    sErr = "No Storm File or URL defined."
            else:
                uiCommon.log("Unable to get Storm Details - Missing Ecotemplate ID")

            # returns a big tuple
            return bIsValid, sErr, sFileType, sURL, sFileDesc, sStormFileJSON
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetStormFileFromURL(self):
        try:
            sURL = uiCommon.getAjaxArg("sURL")
            sURL = uiCommon.unpackJSON(sURL)
            sStormFileJSON = uiCommon.HTTPGetNoFail(sURL)
            if sStormFileJSON:
                return uiCommon.packJSON(sStormFileJSON)
            else:
                return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return ""

    def wmGetEcosystem(self):
        try:
            sID = uiCommon.getAjaxArg("sID")
            e = ecosystem.Ecosystem()
            if e:
                e.FromID(sID)
                if e.ID:
                    return e.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get Ecosystem details for ID [" + sID + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetEcosystemsTable(self):
        try:
            sFilter = uiCommon.getAjaxArg("sSearch")
            sAccountID = uiCommon.getAjaxArg("sAccountID")

            sHTML = ""
            ets = ecosystem.Ecosystems(sAccountID, sFilter)
            if ets.rows:
                for row in ets.rows:
                    sHTML += "<tr ecosystem_id=\"%s\">" % row["ecosystem_id"]
                    sHTML += "<td class=\"chkboxcolumn\">"
                    sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                    " id=\"chk_%s\"" \
                    " object_id=\"%s\"" \
                    " tag=\"chk\" />" % (row["ecosystem_id"], row["ecosystem_id"])
                    sHTML += "</td>"
                    
                    sHTML += "<td class=\"selectable\">%s</td>" % row["ecosystem_name"]
                    sHTML += "<td class=\"selectable\">%s</td>" % row["ecotemplate_name"]
                    sHTML += "<td class=\"selectable\">%s</td>" % (row["ecosystem_desc"] if row["ecosystem_desc"] else "")
                    sHTML += "<td class=\"selectable stormstatus\">%s</td>" % (row["storm_status"] if row["storm_status"] else "")
                    sHTML += "<td class=\"selectable\">%s</td>" % (str(row["created_dt"]) if row["created_dt"] else "")
                    sHTML += "<td class=\"selectable\">%s</td>" % (str(row["last_update_dt"]) if row["last_update_dt"] else "")
                    sHTML += "<td class=\"selectable itemcount\">%s</td>" % str(row["num_objects"])
                    
                    sHTML += "</tr>"
    
            return sHTML    
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetEcosystemsJSON(self):
        try:
            sFilter = uiCommon.getAjaxArg("sFilter")
            sAccountID = uiCommon.getAjaxArg("sAccountID")

            ets = ecosystem.Ecosystems(sAccountID, sFilter)
            if ets:
                return ets.AsJSON()
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get Ecosystems using filter [" + sFilter + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetEcotemplatesJSON(self):
        try:
            sFilter = uiCommon.getAjaxArg("sFilter")
            ets = ecosystem.Ecotemplates(sFilter)
            if ets:
                return ets.AsJSON()
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get Ecotemplates using filter [" + sFilter + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmCreateEcosystem(self):
        try:
            sName = uiCommon.getAjaxArg("sName")
            sDescription = uiCommon.getAjaxArg("sDescription")
            sEcotemplateID = uiCommon.getAjaxArg("sEcotemplateID")
            sAccountID = uiCommon.getAjaxArg("sAccountID")
            sStormStatus = uiCommon.getAjaxArg("sStormStatus")
            sParameterXML = uiCommon.getAjaxArg("sParameterXML")
            sCloudID = uiCommon.getAjaxArg("sCloudID")

            if not sAccountID:
                return "{\"info\" : \"Unable to create - No Cloud Account selected.\"}"
            if not sEcotemplateID:
                return "{\"info\" : \"Unable to create - An Ecosystem Template is required.\"}"


            e, sErr = ecosystem.Ecosystem.DBCreateNew(uiCommon.unpackJSON(sName), sEcotemplateID, sAccountID, uiCommon.unpackJSON(sDescription), sStormStatus, uiCommon.unpackJSON(sParameterXML), sCloudID)
            if sErr:
                return "{\"error\" : \"" + sErr + "\"}"
            if e == None:
                return "{\"error\" : \"Unable to create Ecosystem.\"}"

            uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.Ecosystem, e.ID, e.Name, "Ecosystem created.")
            
            return "{\"id\" : \"%s\"}" % e.ID

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmDeleteEcosystems(self):
        try:
            sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
            if not sDeleteArray:
                return ""
    
            sDeleteArray = uiCommon.QuoteUp(sDeleteArray)

            sSQL = "delete from action_plan where ecosystem_id in (" + sDeleteArray + ")"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            sSQL = "delete from action_schedule where ecosystem_id in (" + sDeleteArray + ")"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            sSQL = "delete from object_registry where object_id in (" + sDeleteArray + ")"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            sSQL = "delete from ecosystem_object where ecosystem_id in (" + sDeleteArray + ")"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            sSQL = "delete from ecosystem_log where ecosystem_id in (" + sDeleteArray + ")"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            sSQL = "delete from ecosystem where ecosystem_id in (" + sDeleteArray + ")"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)
            
            self.db.tran_commit()
                
            uiCommon.WriteObjectDeleteLog(uiGlobals.CatoObjectTypes.Ecosystem, "", "", "Ecosystem(s) Deleted [" + sDeleteArray + "]")

            return "{\"result\" : \"success\"}"
            
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetEcosystemActionCategories(self):
        try:
            sEcoTemplateID = uiCommon.getAjaxArg("sEcoTemplateID")
            sHTML = ""
    
            if sEcoTemplateID:
                sIcon = "action_category_48.png"

                # the 'All' category is hardcoded
                sHTML += " <div class=\"ui-state-focus action_btn_focus ui-widget-content ui-corner-all action_btn action_category\" id=\"ac_all\">" \
                    "<img src=\"static/images/actions/" + sIcon + "\" alt=\"\" />" \
                    "<span>All</span></div>"


                sSQL = "select distinct category" \
                    " from ecotemplate_action" \
                    " where ecotemplate_id = '" + sEcoTemplateID + "'" \
                    " and category != ''" \
                    " and category != 'all'" \
                    " order by category"

                dt = self.db.select_all_dict(sSQL)
                if self.db.error:
                    uiCommon.log_nouser(self.db.error, 0)

                if dt:
                    for dr in dt:
                        sHTML += " <div class=\"ui-widget-content ui-corner-all action_btn action_category\"" \
                           " id=\"" + dr["category"] + "\"" \
                           ">"
                        sHTML += "<img src=\"static/images/actions/" + sIcon + "\" alt=\"\" />"
                        sHTML += "<span>" + dr["category"] + "</span>"
                        sHTML += " </div>"
            else:
                uiCommon.log("Unable to get Action Categories - Missing Ecotemplate ID")

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetEcosystemActionButtons(self):
        try:
            sEcoTemplateID = uiCommon.getAjaxArg("sEcoTemplateID")
            sHTML = ""
    
            if sEcoTemplateID:
                # get the action from the table, then look at the task_version.
                # if it's null or empty we get the default,
                # otherwise we use the version specified.
                
                # but, rather than do queries inside the loop, we'll do it with a union of two exclusive queries.
                sSQL = "select * from (" \
                    "select ea.action_id, ea.action_name, ea.category, ea.action_desc, ea.original_task_id, ea.action_icon," \
                    " t.task_id, t.task_name, t.version" \
                    " from ecotemplate_action ea" \
                    " join task t on ea.original_task_id = t.original_task_id" \
                        " and t.default_version = 1" \
                    " where ea.ecotemplate_id = '" + sEcoTemplateID + "'" \
                    " and ea.task_version IS null" \
                    " UNION" \
                    " select ea.action_id, ea.action_name, ea.category, ea.action_desc, ea.original_task_id, ea.action_icon," \
                    " t.task_id, t.task_name, t.version" \
                    " from ecotemplate_action ea" \
                    " join task t on ea.original_task_id = t.original_task_id" \
                        " and ea.task_version = t.version" \
                    " where ea.ecotemplate_id = '" + sEcoTemplateID + "'" \
                    " and ea.task_version IS NOT null" \
                    " ) foo" \
                    " order by action_name"

                dt = self.db.select_all_dict(sSQL)
                if self.db.error:
                    uiCommon.log_nouser(self.db.error, 0)

                if dt:
                    # i = 0
                    # sHTML += "<table id=\"actions_table\">"

                    for dr in dt:
                        sActionID = dr["action_id"]
                        sActionName = dr["action_name"]
                        sTaskID = dr["task_id"]
                        sTaskName = dr["task_name"]
                        sVersion = str(dr["version"])
                        sCategory = str(dr["category"])
                        sIcon = ("action_default_48.png" if not dr["action_icon"] else dr["action_icon"])

                        # sDesc is the tooltip
                        sDesc = "<p>" + (dr["action_desc"].replace("\"", "").replace("'", "") if dr["action_desc"] else "") + \
                            "</p><p>" + sTaskName + "</p>"


                        # sAction = ""

                        sHTML += " <div class=\"action\"" \
                           " id=\"" + sActionID + "\"" \
                           " action=\"" + sActionName + "\"" \
                           " task_id=\"" + sTaskID + "\"" \
                           " task_name=\"" + sTaskName + "\"" \
                           " task_version=\"" + sVersion + "\"" \
                           " category=\"" + sCategory + "\"" \
                           ">"

                        sHTML += "<div class=\"ui-widget-content ui-corner-all action_btn action_inner\">" # outer div with no styling at all

                        sHTML += "<div class=\"step_header_title\">"
                        sHTML += "</div>"

                        sHTML += "<div class=\"step_header_icons\">"
                        sHTML += "<img class=\"action_help_btn\"" \
                            " src=\"static/images/icons/info.png\" alt=\"\" style=\"width: 12px; height: 12px;\"" \
                            " title=\"" + sDesc + "\" />"
                        sHTML += "</div>"

                        # gotta clear the floats
                        sHTML += "<div class=\"clearfloat\">"

                        sHTML += "<img class=\"action_icon\" src=\"static/images/actions/" + sIcon + "\" alt=\"\" />"


                        sHTML += " </div>"
                        sHTML += " </div>" # end inner div

                        sHTML += "<span class=\"action_name\">"
                        sHTML += sActionName
                        sHTML += "</span>"


                        sHTML += " </div>" # end outer div

                    # need a clearfloat div here, as javascript flow logic will be 
                    # dynamically adding and removing floats
                    sHTML += "<div class=\"clearfloat\"></div>"

            else:
                uiCommon.log("Unable to get Actions - Missing Ecotemplate ID")

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetEcosystemStormStatus(self):
        try:
            sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
            
            sb = []
            
            
            # status and parameters
            sSQL = "select storm_status, storm_parameter_xml, last_update_dt from ecosystem where ecosystem_id = '" + sEcosystemID + "'"
            dr = self.db.select_row_dict(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)

            sStormStatus = "Unknown"
            sStormParameterXML = ""
            sLastUpdateDT = "Unknown"
            if dr:
                sStormStatus = ("" if not dr["storm_status"] else dr["storm_status"])
                sStormParameterXML = ("" if not dr["storm_parameter_xml"] else dr["storm_parameter_xml"])
                sLastUpdateDT = ("" if not dr["last_update_dt"] else str(dr["last_update_dt"]))

            # log
            sSQL = "select ecosystem_log_id, ecosystem_id, ecosystem_object_type, ecosystem_object_id, logical_id, status, log, convert(update_dt, CHAR(20))" \
                " from ecosystem_log" \
                    " where ecosystem_id = '" + sEcosystemID + "'" \
                    " order by ecosystem_log_id desc"
            
            dtLog = self.db.select_all(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)
            
            # output
            sSQL = "select output_key, output_desc, output_value" \
                " from ecosystem_output" \
                    " where ecosystem_id = '" + sEcosystemID + "'" \
                    " order by output_key"
            
            dtOut = self.db.select_all(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)
            
            
            # build the json
            
            # NOTE: building it manually so we can encode/escape/etc certain values
            sb.append("{ \"storm_status\" : \"%s\"," % (sStormStatus if sStormStatus else ""))
            sb.append("\"last_update_dt\" : \"%s\"," % (sLastUpdateDT if sLastUpdateDT else ""))
            
            # log
            sb.append(" \"ecosystem_log\" : [")
            
            if dtLog:
                sblog = []
                for drLog in dtLog:
                    sblog.append("[ \"{0}\", \"{1}\", \"{2}\", \"{3}\", \"{4}\", \"{5}\", \"{6}\", \"{7}\" ]".format( 
                        drLog[0], 
                        drLog[1], 
                        drLog[2], 
                        drLog[3], 
                        drLog[4], 
                        uiCommon.packJSON(drLog[5]), 
                        (uiCommon.packJSON(uiCommon.FixBreaks(drLog[6])) if drLog[6] else ""), 
                        drLog[7]))
                    
                sb.append(",".join(sblog))
                
            sb.append("],")
            
            # output
            sb.append(" \"storm_output\" : [")
            
            if dtOut:
                sbout = []
                for drOut in dtOut:
                    sbout.append("[ \"{0}\", \"{1}\", \"{2}\" ]".format( 
                        drOut[0], 
                        uiCommon.packJSON(drOut[1]), 
                        uiCommon.packJSON(drOut[2])))
                    
                sb.append(",".join(sbout))
                
            sb.append("],")
            
            # parameters
            sb.append(" \"storm_parameters\" : [")
            
            if sStormParameterXML:
                xDoc = ET.fromstring(sStormParameterXML)
                if xDoc is not None:
                    sbparams = []
                    xParameters = xDoc.findall("parameter")
                    for xParameter in xParameters:
                        xVals = xParameter.find("values", "")
                        sVals = ET.tostring(xVals)
                        sbparams.append("[ \"{0}\", \"{1}\" ]".format(xParameter.findtext("name", ""), uiCommon.packJSON(sVals)))
                        
                    sb.append(",".join(sbparams))

            sb.append("] }")

            return "".join(sb)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetEcosystemSchedules(self):
        try:
            sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
            sHTML = ""

            sSQL = "select s.schedule_id, s.label, s.descr, t.task_name, a.action_id, a.action_name, t.task_id, t.task_name, t.version" \
                " from action_schedule s" \
                " join task t on s.task_id = t.task_id" \
                " left outer join ecotemplate_action a on s.action_id = a.action_id" \
                " where s.ecosystem_id = '" + sEcosystemID + "'"
            dt = self.db.select_all_dict(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)
                return self.db.error

            if dt:
                for dr in dt:
                    sHTML += " <div class=\"ui-widget-content ui-corner-all pointer clearfloat action_schedule\"" \
                        " id=\"as_" + dr["schedule_id"] + "\"" \
                        " action_id=\"" + dr["action_id"] + "\"" \
                        " action=\"" + dr["action_name"] + "\"" \
                        " task_id=\"" + dr["task_id"] + "\"" \
                        " task_name=\"" + dr["task_name"] + "\"" \
                        " task_version=\"" + str(dr["version"]) + "\"" \
                        ">"
                    sHTML += " <div class=\"floatleft schedule_name\">"

                    sHTML += "<span class=\"floatleft ui-icon ui-icon-calculator schedule_tip\" title=\"" + dr["descr"] + "\"></span>"

                    # show the action name, or the task name if no action exists.
                    if not dr["action_name"]:
                        sHTML += "(" + dr["task_name"] + ")"
                    else:
                        sHTML += dr["action_name"]

                    # and the schedule label
                    sHTML += " - " + (dr["schedule_id"] if not dr["label"] else dr["label"])

                    sHTML += " </div>"

                    sHTML += " <div class=\"floatright\">"
                    # sHTML += "<span class=\"ui-icon ui-icon-trash schedule_remove_btn\" title=\"Delete Schedule\"></span>"
                    sHTML += " </div>"


                    sHTML += " </div>"

            return sHTML

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return ""

    def wmGetEcosystemPlans(self):
        try:
            sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
            sHTML = ""

            sSQL = "select ap.plan_id, date_format(ap.run_on_dt, '%%m/%%d/%%Y %%H:%%i') as run_on_dt, ap.source, ap.action_id, t.task_id," \
                " ea.action_name, t.task_name, t.version, ap.source, ap.schedule_id" \
                " from action_plan ap" \
                " join task t on ap.task_id = t.task_id" \
                " left outer join ecotemplate_action ea on ap.action_id = ea.action_id" \
                " where ap.ecosystem_id = '" + sEcosystemID + "'" \
                " order by ap.run_on_dt, ea.action_name, t.task_name"
            dt = self.db.select_all_dict(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)
                return self.db.error

            if dt:
                for dr in dt:
                    sHTML += " <div class=\"ui-widget-content ui-corner-all pointer clearfloat action_plan\"" \
                        " id=\"ap_" + str(dr["plan_id"]) + "\"" \
                        " plan_id=\"" + str(dr["plan_id"]) + "\"" \
                        " run_on=\"" + str(dr["run_on_dt"]) + "\"" \
                        " source=\"" + dr["source"] + "\"" \
                        " schedule_id=\"" + (dr["schedule_id"] if dr["schedule_id"] else "") + "\"" \
                        " action_id=\"" + dr["action_id"] + "\"" \
                        " action=\"" + dr["action_name"] + "\"" \
                        " task_id=\"" + dr["task_id"] + "\"" \
                        " task_name=\"" + dr["task_name"] + "\"" \
                        " task_version=\"" + str(dr["version"]) + "\"" \
                        ">"
                    sHTML += " <div class=\"floatleft action_plan_name\">"

                    # an icon denotes if it's manual or scheduled
                    if dr["source"] == "schedule":
                        sHTML += "<span class=\"floatleft ui-icon ui-icon-calculator\" title=\"Scheduled\"></span>"
                    else:
                        sHTML += "<span class=\"floatleft ui-icon ui-icon-document\" title=\"Run Later\"></span>"

                    # show the time
                    sHTML += dr["run_on_dt"]

                    # show the action name, or the task name if no action exists.
                    if not dr["action_name"]:
                        sHTML += " - (" + dr["task_name"] + ")"
                    else:
                        sHTML += " - " + dr["action_name"]


                    sHTML += " </div>"

                    sHTML += " <div class=\"floatright\">"
                    # sHTML += "<span class=\"ui-icon ui-icon-trash action_plan_remove_btn\" title=\"Delete Plan\"></span>"
                    sHTML += " </div>"


                    sHTML += " </div>"

            return sHTML

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return ""

    def wmGetEcosystemObjects(self):
        try:
            sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
            sAccountID = uiCommon.getAjaxArg("sAccountID")

            ca = cloud.CloudAccount()
            ca.FromID(sAccountID)
            if ca.ID is None:
                return "Failed to get Cloud Account details for Cloud Account ID [" + sAccountID + "]."

            sHTML = ""

            sSQL = "select eo.ecosystem_object_type, count(*) as num_objects" \
                " from ecosystem_object eo" \
                " where eo.ecosystem_id ='" + sEcosystemID + "'" \
                " group by eo.ecosystem_object_type" \
                " order by eo.ecosystem_object_type"

            dt = self.db.select_all_dict(sSQL)
            if self.db.error:
                return self.db.error

            if dt:
                sHTML += "<table>"
                i = 0
                for dr in dt:
                    cot = ca.Provider.GetObjectTypeByName(dr["ecosystem_object_type"])

                    # every 5 items gets a new row
                    if i % 5 == 0:
                        sHTML += "<tr>"
                    # TODO: we need a way to get the pretty label for an object type here, since we moved 
                    # it out of the database.
                    # perhaps a static class method to look up a type name based on the id?
                    # or a peek into the CloudProviders object in the session might be better.
                    
                    # something here can look up the icon for each type if we wanna do that.
                    sIcon = "%s.png" % cot.ID

                    sHTML += "<td>"
                    sHTML += " <div class=\"ecosystem_type\"" \
                       " id=\"" + cot.ID + "\"" \
                       " label=\"" + cot.Label + "\"" \
                       ">"

                    sHTML += "<div class=\"ui-widget-content ui-corner-all action_btn action_inner\">" # outer div with no styling at all

                    sHTML += "<div class=\"step_header_title\">"
                    sHTML += "</div>"

                    sHTML += "<div class=\"step_header_icons\">"
                    sHTML += "(" + str(dr["num_objects"]) + ")"
                    sHTML += "</div>"

                    # gotta clear the floats
                    sHTML += "<div class=\"clearfloat\">"

                    sHTML += "<img class=\"action_icon\" src=\"static/images/cloud_object_types/" + sIcon + "\" alt=\"\" style=\"width: 32px; height: 32px; margin-left: -8px; padding-top: 10px;\" />"


                    sHTML += " </div>"
                    sHTML += " </div>" # end inner div

                    sHTML += "<span class=\"action_name\">"
                    sHTML += cot.Label
                    sHTML += "</span>"


                    sHTML += " </div>" # end outer div
                    
                    sHTML += "</td>"
                    
                    if i % 5 == 4:
                        sHTML += "</tr>"

                    i += 1

                sHTML += "</table>"
            else:
                sHTML += "<span>This ecosystem does not contain any Cloud Objects.</span>"

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return ""

    def wmGetEcosystemObjectByType(self):
        try:
            sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
            sType = uiCommon.getAjaxArg("sType")
            sHTML = ""

            # So, we'll first get a distinct list of all clouds represented in this set
            # then for each cloud we'll get the objects.
            
            # Why two queries on the same table?  Because we need the Cloud ID BEFORE we get in to the loop below.
            # the AWS call to get the properties for the objects is a single API call that returns all the properties
            # for ALL the objects, then we'll marry them up.
            
            # For our custom tagging (For Eucalyptus which currently does not support tagging)
            #  we'll also check our internal tagging mechanism - the ecosystem_object_tags table.
            #  and similarly we'll get them all at once and just draw the ones we need.

            sSQL = "select distinct eo.cloud_id, e.account_id" \
                " from ecosystem_object eo" \
                " join ecosystem e on eo.ecosystem_id = e.ecosystem_id" \
                " where eo.ecosystem_id ='" + sEcosystemID + "'" \
                " and eo.ecosystem_object_type = '" + sType + "'"

            dtClouds = self.db.select_all_dict(sSQL)
            if self.db.error:
                return self.db.error


            sSQL = "select ecosystem_object_id, key_name, value " \
                " from ecosystem_object_tag" \
                " where ecosystem_id ='" + sEcosystemID + "'" \
                " order by key_name"

            dtTags = self.db.select_all_dict(sSQL)
            if self.db.error:
                return self.db.error

            if dtClouds:
                for drCloud in dtClouds:
                    sCloudID = drCloud["cloud_id"]

                    # get the cloud object rows
                    sSQL = "select eo.ecosystem_object_id, eo.ecosystem_object_type" \
                        " from ecosystem_object eo" \
                        " where eo.ecosystem_id ='" + sEcosystemID + "'" \
                        " and eo.ecosystem_object_type = '" + sType + "'" \
                        " and eo.cloud_id = '" + sCloudID + "'" \
                        " order by eo.ecosystem_object_type"
    
                    dtObjects = self.db.select_all_dict(sSQL)
                    if self.db.error:
                        return self.db.error
    
    
                    if dtObjects:
                        # we only need to hit the API once... this result will contain all the objects
                        # and our DrawProperties will filter the DataTable on the ID.
                        dtAPIResults, sErr = uiCommon.GetCloudObjectsAsList(drCloud["account_id"], sCloudID, sType)
                        if sErr:
                            sHTML += sErr
                        
                        for drObject in dtObjects:
                            # look up the cloud and get the name
                            c = cloud.Cloud()
                            c.FromID(sCloudID)
                            if c.ID is not None:
                                # giving each section a guid so we can delete it on the client side after the ajax call.
                                # not 100% the ecosystem_object_id will always be suitable as a javascript ID.
                                sGroupID = catocommon.new_guid()
        
                                sHTML += "<div class=\"ui-widget-content ui-corner-all ecosystem_item\" id=\"" + sGroupID + "\">"
        
        
                                sObjectID = drObject["ecosystem_object_id"]
        
                                sLabel = "Cloud: " + c.Name + " - " + sObjectID
        
                                sHTML += "<div class=\"ui-widget-header ecosystem_item_header\">"
                                sHTML += "<div class=\"ecosystem_item_header_title\"><span>" + sLabel + "</span></div>"
        
                                sHTML += "<div class=\"ecosystem_item_header_icons\">"
        
                                sHTML += "<span class=\"ui-icon ui-icon-close ecosystem_item_remove_btn pointer\"" \
                                    " id_to_delete=\"" + drObject["ecosystem_object_id"] + "\"" \
                                    " id_to_remove=\"" + sGroupID + "\">"
                                sHTML += "</span>"
        
                                sHTML += "</div>"
        
                                sHTML += "</div>"
        
                                # the details section
                                sHTML += "<div class=\"ecosystem_item_detail\">"
        
                                if dtAPIResults:
                                    sHTML += self.DrawAllEcosystemObjectProperties(dtAPIResults, dtTags, sObjectID)
        
        
                                # end detail section
                                sHTML += "</div>"
                                # end block
                                sHTML += "</div>"
                    else:
                        sHTML += "<span>This ecosystem does not contain any Cloud Objects.</span>"

            
            # at this point, sErr will have any issues that occured doing the AWS API call.  display it.
            if self.db.error:
                sHTML += "<span class='ui-state-highlight'>An issue occured while communicating with the Cloud Provider.  Click the refresh button above to try: again.<!--" + self.db.error + "--></span>"

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return ""

    # two def functions to support the wmGetEcosystemObjectByType
    def DrawAllEcosystemObjectProperties(self, dtProps, dtStormTags, sObjectID):
        try:
            sHTML = ""

            # what is the name of the first column?
            # all over the place with AWS we hardcode and assume the first column is the 'ID'.
            # that's bad - so spin the columns looking for the one with the Extended Property that says it's the id
            if dtProps.has_key(sObjectID):
                drFound = dtProps[sObjectID]
                # for each property
                for prop in drFound:
                    # draw only the short list properties here.
                    if prop.ShortList:
                        sHTML += self.DrawEcosystemObjectProperty(prop)
                    
                    # there *might* be a column named "Tags"... if so, it's special and contains the xml of a tag set.
                    # now draw the tag columns only
                    if prop.Name == "Tags":
                        if prop.Value:
                            xDoc = ET.fromstring(prop.Value)
                            if xDoc is not None:
                                sHTML += "<div class=\"ui-widget-header\">AWS Tags</div>"
                                for xeTag in xDoc.findall("item"):
                                    sHTML += "<div class=\"ecosystem_item_property\">" + xeTag.findtext("key", "") + \
                                        ": <span class=\"ecosystem_item_property_value\">" + xeTag.findtext("value", "") + "</span></div>"
            

                # now lets draw the Storm tags
                #  ! NOT the same kind of set as above, this one is multiple simple key/value pairs for an object_id
                # we have all the tags in dtStormTags - we need only the ones for sObjectID
                if dtStormTags:
                    # we only wanna show this section if the object id matched
                    i = 0
                    for drTag in dtStormTags:
                        if drTag["ecosystem_object_id"] == sObjectID:
                            if i==0:
                                sHTML += "<div class=\"ui-widget-header\">Storm Tags</div>"
                            
                            sHTML += "<div class=\"ecosystem_item_property\">" + drTag["key_name"] + \
                                ": <span class=\"ecosystem_item_property_value\">" + drTag["value"] + "</span></div>"
                            i += 1
            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return ""
    
    def DrawEcosystemObjectProperty(self, prop):
        try:
            sHTML = ""
            sValue = ("" if not prop.Value else prop.Value)
            sIcon = ""
            sLabel = (prop.Label if prop.Label else prop.Name)

            # some fields have a status or other icon.
            # it's noted in the extended properties of the column in the AWS results.
            # we are simply assuming to have an image file for every propery that might have an icon.
            # the images will be named "property_value.png" 
            # NOTE: collapsed for spaces of course... just to be safe
            if prop.HasIcon:
                if sValue != "":
                    sIcon = "<img class=\"custom_icon\" src=\"static/images/custom/" + \
                        prop.Name.replace(" ", "").lower() + "_" + \
                        sValue.replace(" ", "") + ".png\" alt=\"\" />".lower()

            if sValue:
                sHTML += "<div class=\"ecosystem_item_property\">" + sLabel + ": <span class=\"ecosystem_item_property_value\">" + sIcon + sValue + "</span></div>"

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return ""
        
    def wmUpdateEcosystemDetail(self):
        try:
            sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
            sColumn = uiCommon.getAjaxArg("sColumn")
            sValue = uiCommon.getAjaxArg("sValue")
    
            sUserID = uiCommon.GetSessionUserID()

            if uiCommon.IsGUID(sEcosystemID) and uiCommon.IsGUID(sUserID):
                e = ecosystem.Ecosystem()
                e.FromID(sEcosystemID)
                
                if e:
                    # we encoded this in javascript before the ajax call.
                    # the safest way to unencode it is to use the same javascript lib.
                    # (sometimes the javascript and .net libs don't translate exactly, google it.)
                    sValue = uiCommon.unpackJSON(sValue)

                    #  check for existing name
                    if sColumn == "Name":
                        if e.Name == sValue:
                            return sValue + " exists, please choose another name."

                    # cool, update the class attribute by name, using getattr!
                    # python is so cool.. I don't even need to check if the attribute I wanna set exists.
                    # just set it
                    setattr(e, sColumn, sValue)
                    
                    bSuccess, msg = e.DBUpdate()
                    
                    if bSuccess:
                        uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Ecosystem, sEcosystemID, sColumn, sValue)
                    else: 
                        uiCommon.log("Error updating Ecosystem. " + msg)
                        return "Error updating Ecosystem. " + msg
                else:
                    uiCommon.log("Unable to update Ecosystem. Missing or invalid id [" + sEcosystemID + "].")
                    return "Unable to update Ecosystem. Missing or invalid id [" + sEcosystemID + "]."
                
                return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
    
    def wmDeleteEcosystemObject(self):
        try:
            sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
            sObjectType = uiCommon.getAjaxArg("sObjectType")
            sObjectID = uiCommon.getAjaxArg("sObjectID")
    
            if not sObjectID:
                return ""

            sSQL = "delete from ecosystem_object" \
                " where ecosystem_id ='" + sEcosystemID + "'" \
                " and ecosystem_object_id ='" + sObjectID + "'" \
                " and ecosystem_object_type ='" + sObjectType + "'"

            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)
                return self.db.error

            sSQL = "delete from ecosystem_object_tag" \
                " where ecosystem_id ='" + sEcosystemID + "'" \
                " and ecosystem_object_id ='" + sObjectID + "'"

            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)
                return self.db.error
            
            self.db.tran_commit()
    
            #  if we made it here, so save the logs
            uiCommon.WriteObjectDeleteLog(uiGlobals.CatoObjectTypes.Ecosystem, "", "", "Object [" + sObjectID + "] removed from Ecosystem [" + sEcosystemID + "]")
    
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetEcotemplateStormParameterXML(self):
        try:
            sEcoTemplateID = uiCommon.getAjaxArg("sEcoTemplateID")

            if sEcoTemplateID:
                bIsValid, sErr, sFileType, sURL, sFileDesc, sStormFileJSON = self.GetEcotemplateStormJSON(sEcoTemplateID)
                
                sb = []
                
                # now we have the storm file json... parse it, spin it, and turn the parameters section into our parameter_xml format
                if sStormFileJSON:
                    sb.append("<parameters>")

                    jo = json.loads(sStormFileJSON)
                    if jo.has_key("Parameters"):
                        oParams = jo["Parameters"]
                        for param, attribs in oParams.iteritems():
                            sParamName = param
                            sParamDesc = ""
                            sPresentAs = "value"
                            sConstraintPattern = ""
                            sConstraintMsg = "";                                        
                            sMinLength = ""
                            sMaxLength = ""
                            sMinValue = ""
                            sMaxValue = ""
                            sDefaultValue = ""
                            sValueType = ""
                            bEncrypt = "false"
                            jaAllowedValues = {}

                            for a_key, a_val in attribs.iteritems():
                                # http:# docs.amazonwebservices.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html
                                if a_key == "Description":
                                    sParamDesc = str(a_val if a_val else "")
                                elif a_key == "Type":
                                    sValueType = str(a_val if a_val else "")
                                elif a_key == "Default":
                                    sDefaultValue = str(a_val if a_val else "")
                                elif a_key == "AllowedValues":
                                    # if there's an allowedvalues section, it's a dropdown.
                                    sPresentAs = "dropdown"
                                    # we might have to use the JArray here.
                                    jaAllowedValues = (a_val if a_val else {})
                                elif a_key == "MinLength":
                                    sMinLength = str(a_val if a_val else "")
                                elif a_key == "MaxLength":
                                    sMaxLength = str(a_val if a_val else "")
                                elif a_key == "MinValue":
                                    sMinValue = str(a_val if a_val else "")
                                elif a_key == "MaxValue":
                                    sMaxValue = str(a_val if a_val else "")
                                elif a_key == "NoEcho":
                                    bEncrypt = "true"
                                elif a_key == "AllowedPattern":
                                    sConstraintPattern = str(a_val if a_val else "")
                                elif a_key == "ConstraintDescription":
                                    sConstraintMsg = str(a_val if a_val else "")
                                    
                                
                            sb.append("<parameter id=\"p_" + catocommon.new_guid() + \
                                "\" required=\"true\" prompt=\"true\" encrypt=\"" + bEncrypt + \
                                "\" value_type=\"" + sValueType  + \
                                "\" minvalue=\"" + sMinValue + "\" maxvalue=\"" + sMaxValue + \
                                "\" minlength=\"" + sMinLength + "\" maxlength=\"" + sMaxLength + \
                                "\" constraint=\"" + sConstraintPattern + "\" constraint_msg=\"" + sConstraintMsg + "\">")
    
                            sb.append("<name>" + sParamName + "</name>")
                            sb.append("<desc>" + sParamDesc + "</desc>")
                            
                            sb.append("<values present_as=\"" + sPresentAs + "\">")
                            
                            if sPresentAs == "dropdown" and jaAllowedValues is not None:
                                for oOpt in jaAllowedValues:
                                    sb.append("<value id=\"pv_" + catocommon.new_guid() + "\">" + oOpt + "</value>")
                            else:
                                sb.append("<value id=\"pv_" + catocommon.new_guid() + "\">" + sDefaultValue + "</value>")
                            
                            sb.append("</values>")
    
                            sb.append("</parameter>")
                        
                    sb.append("</parameters>")
                        
                    return "".join(sb)
                        # no... this parser isn't as accurate as the client one.
                        # don't raise an exception, just dont' return parameters.
                        # uiCommon.log("The Storm File is invalid. " + traceback.format_exc())
                return ""
            else:
                uiCommon.log("Unable to get Storm Details - Missing Ecotemplate ID")
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
    
    def wmCallStormAPI(self):
        try:
            sMethod = uiCommon.getAjaxArg("sMethod")
            sArgs = uiCommon.getAjaxArg("sArgs")
            # This will construct and send an HTTP request to the Storm API,
            # then return the results unmolested back to the caller.
            
            # sArgs is an json object of args for the named method -- we use the Newtonsoft JSON to parse it.
            # after unencoding it.
            
            sQS = ""
            
            sJSONArgs = uiCommon.unpackJSON(sArgs)
            if sJSONArgs:
                jo = json.loads(sJSONArgs)
                 
                for key, val in jo.iteritems():
                    sQS += "&" + key + "=" + urllib.quote_plus(val)
            
            
            # now, we construct the call to the Storm API in a specific way:
            # 1: the "key" is the user_id
            # 2: a "timestamp" which is now in UTC formatted as "%Y-%m-%dT%H:%M:%S"
            # 3: a "signature" which is a specific part of the request SHA256/base64 encoded
            
            # 1:
            sKey = uiCommon.GetSessionUserID()
            sPW = self.db.select_col_noexcep("select user_password from users where user_id = '%s'" % sKey)
            if self.db.error:
                return self.db.error
            
            sPW = catocommon.cato_decrypt(sPW)
            
            # 2:
            sTS = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            sTS = sTS.replace(":","%3A")
            
            # 3:
            # we use the same functions we do for building the aws signature
            sStringToSign = "{0}?key={1}&timestamp={2}".format(sMethod, sKey, sTS)
            
            sSignature = base64.b64encode(hmac.new(sPW, msg=sStringToSign, digestmod=hashlib.sha256).digest())
            # used to be this ... quote_plus should be enough.
            #sSignature = "&signature=" + uiCommon.PercentEncodeRfc3986(sSignature)
            sSignature = "&signature=" + urllib.quote_plus(sSignature)
            
            sHost = "http://localhost"
            if uiGlobals.config.has_key("stormapiurl"):
                sHost = (uiGlobals.config["stormapiurl"] if uiGlobals.config["stormapiurl"] else "http://localhost")
            else:
                uiCommon.log("Warning: stormApiUrl setting not defined in cato.conf... using http://localhost", 2)

            sPort = "8080"
            if uiGlobals.config.has_key("stormapiport"):
                sPort = (uiGlobals.config["stormapiport"] if uiGlobals.config["stormapiport"] else "8080")
            else:
                uiCommon.log("Warning: stormApiPort setting not defined in cato.conf... using 8080", 2)
            
            sURL = "{0}:{1}/{2}{3}{4}".format(sHost, sPort, sStringToSign, sSignature, sQS)
                    
            sXML = ""
            try:
                sXML, sErr = uiCommon.HTTPGet(sURL, 15)
                if sErr:
                    return "{\"error\" : \"Attempt to contact the Storm service failed.  Verify the Stormfront service is running, and check the logfile for errors.  %s\"}" % sErr

            except:
                uiCommon.log("Error calling Storm service." + traceback.format_exc())
                return "{\"error\" : \"Error calling Storm service.\"}"
            
            return "{\"xml\" : \"%s\"}" % uiCommon.packJSON(sXML)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
    

    def wmAddEcosystemObjects(self):
        try:
            sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
            sCloudID = uiCommon.getAjaxArg("sCloudID")
            sObjectType = uiCommon.getAjaxArg("sObjectType")
            sObjectIDs = uiCommon.getAjaxArg("sObjectIDs")

            if not sEcosystemID or not sObjectType or not sObjectIDs:
                uiCommon.log("Missing or invalid Ecosystem ID, Cloud Object Type or Object ID.")

            aObjectIDs = sObjectIDs.split(",")
            for sObjectID in aObjectIDs:
                sSQL = "insert into ecosystem_object " \
                     " (ecosystem_id, cloud_id, ecosystem_object_id, ecosystem_object_type, added_dt)" \
                     " values (" \
                     " '" + sEcosystemID + "'," \
                     " '" + sCloudID + "'," \
                     " '" + sObjectID + "'," \
                     " '" + sObjectType + "'," \
                     " now() " \
                     ")"

                if not self.db.exec_db_noexcep(sSQL):
                    if self.db.error == "key_violation":
                        """do nothing"""
                    else:
                        uiCommon.log_nouser(self.db.error, 0)

            uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Ecosystem, sEcosystemID, "", "Objects Added : {" + sObjectIDs + "}")

            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
