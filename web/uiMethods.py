
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
import json
from datetime import datetime
try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET


from catocommon import catocommon
from catouser import catouser
from catocloud import cloud
from catoasset import asset
from catotask import task
from catoregistry import registry
from catosettings import settings

from catoui import uiCommon, uiGlobals

# these are generic ui web methods, and stuff that's not enough to need it's own file.

class uiMethods:
    db = None
    
    def wmAttemptLogin(self):
        return uiCommon.AttemptLogin("Cato Admin UI")   
                
    def wmGetQuestion(self):
        return uiCommon.GetQuestion()
            
    def wmUpdateHeartbeat(self):
        uiCommon.UpdateHeartbeat()
        return ""
    
    def wmSetApplicationSetting(self):
        try:
            category = uiCommon.getAjaxArg("sCategory")
            setting = uiCommon.getAjaxArg("sSetting")
            value = uiCommon.getAjaxArg("sValue")

            result, err = settings.settings.set_application_setting(category, setting, value)
            if not result:
                return err
            
            return ""
            
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)    
            
    def wmLicenseAgree(self):
        try:
            result, err = settings.settings.set_application_setting("general", "license_status", "agreed")
            if not result:
                return err
            result, err = settings.settings.set_application_setting("general", "license_datetime", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            if not result:
                return err
            
            return ""
            
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)    
            
    def wmGetDBInfo(self):
        try:
            if uiGlobals.config.has_key("server"):
                return uiGlobals.config["server"]
            else:
                return "Unknown"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)    
            
    def wmGetVersion(self):
        try:
            if uiGlobals.config.has_key("version"):
                return uiGlobals.config["version"]
            else:
                return "Unknown"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)    
            
    def wmGetGettingStarted(self):
        try:
            sset = settings.settings()
            sHTML = ""
            
            user_name = uiCommon.GetSessionObject("user", "user_name")
            user_role = uiCommon.GetSessionUserRole()
            if user_role == "Administrator":
                items = []
                regstatus = sset.get_application_setting("general/register_cato")
                if regstatus not in ["skipped", "registered"]:
                    items.append("Register Cato to receive updates about the latest versions, plus the latest news and Community support.")
                    sHTML += self.DrawGettingStartedItem("registercato", "Register Cato", items,
                         "<a href=\"#\" onclick=\"registerCato();\">Click here</a> to register Cato.<br /><a href=\"#\" id=\"skip_registration_btn\">Click here</a> to skip registering and hide this message.")


                items = []
                if not sset.Messenger["SMTPServerAddress"]:
                    items.append("Define an SMTP server.")
                    sHTML += self.DrawGettingStartedItem("messengersettings", "Messenger Settings", items, "<a href=\"/settings?module=messenger\">Click here</a> to update Messenger settings.")
    
                
                items = []
                sSQL = "select security_question, security_answer, email from users where username = 'administrator'"
                dr = self.db.select_row_dict(sSQL)
                if dr:
                    if not dr["email"]:
                        items.append("Set Administrator email account to receive system notifications.")

                    if not dr["security_question"] or not dr["security_answer"]:
                        items.append("Select a security challenge question and response.")
                
                if items:
                    if user_name.lower() == "administrator":
                        sHTML += self.DrawGettingStartedItem("adminaccount", "Administrator Account", items, "<a href=\"#\" onclick=\"showMyAccount();\">Click here</a> to update Administrator account settings.")
                    else:
                        sHTML += self.DrawGettingStartedItem("adminaccount", "Administrator Account", items, "You must be logged in as 'Administrator' to change these settings.")                    
                

                items = []
                sSQL = "select login_id, login_password from cloud_account"
                dt = self.db.select_all_dict(sSQL)
                if dt:
                    for dr in dt:
                        if not dr["login_id"] or not dr["login_password"]:
                            items.append("Provide an Account Login ID and Password.")
                else: 
                    items.append("There are no Cloud Accounts defined.")
                
                if items:
                    sHTML += self.DrawGettingStartedItem("cloudaccounts", "Cloud Accounts", items, "<a href=\"/cloudAccountEdit\">Click here</a> to manage Cloud Accounts.")
            
            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)    


    def DrawGettingStartedItem(self, sID, sTitle, aItems, sActionLine):
        try:
            sHTML = ""

            sHTML += "<div id=\"" + sID + "\" class=\"ui-widget\" style=\"margin-top: 10px;\">"
            sHTML += "<div style=\"padding: 10px;\" class=\"ui-state-highlight ui-corner-all\">"
            sHTML += "<span style=\"float: left; margin-right: .3em;\" class=\"ui-icon ui-icon-info\"></span>"
            sHTML += "<strong>" + sTitle + "</strong>"
            
            # each item
            for sItem in aItems:
                sHTML += "<p style=\"margin-left: 10px;\">" + sItem + "</p>"          
            
            sHTML += "<br />"
            sHTML += "<p>" + sActionLine + "</p>"
            sHTML += "</div>"
            sHTML += "</div>"
            
            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)    
            
    def wmGetCloudAccountsForHeader(self):
        try:
            sSelected = uiCommon.GetCookie("selected_cloud_account")

            sHTML = ""
            ca = cloud.CloudAccounts("")
            if ca.rows:
                for row in ca.rows:
                    # if sSelected is empty, set the default in the cookie.
                    sSelectClause = ""
                    if not sSelected:
                        if row["is_default"] == "Yes":
                            uiCommon.SetCookie("selected_cloud_account", row["account_id"])
                    else:
                        sSelectClause = ("selected=\"selected\"" if sSelected == row["account_id"] else "")
                        
                    sHTML += "<option value=\"%s\" provider=\"%s\" %s>%s (%s)</option>" % (row["account_id"], row["provider"], sSelectClause, row["account_name"], row["provider"])

                return sHTML
            
            #should not get here if all is well
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetMenu(self):
        try:
                #NOTE: this needs all the kick and warn stuff
            role = uiCommon.GetSessionUserRole()
            
            if not role:
                uiCommon.ForceLogout("Unable to get Role for user.")
    
            filename = ""
            if role == "Administrator":
                filename = "_amenu.html"
            if role == "Developer":
                filename = "_dmenu.html"
            if role == "User":
                filename = "_umenu.html"

            f = open("%s/static/%s" % (uiGlobals.web_root, filename))
            if f:
                return f.read()
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
    
    def wmGetSystemStatus(self):
        try:
            sProcessHTML = ""
            sSQL = "select app_instance as Instance," \
                " app_name as Component," \
                " heartbeat as Heartbeat," \
                " case master when 1 then 'Yes' else 'No' end as Enabled," \
                " timestampdiff(MINUTE, heartbeat, now()) as mslr," \
                " load_value as LoadValue, platform, hostname" \
                " from application_registry " \
                " order by component, master desc"
            rows = self.db.select_all_dict(sSQL)
            if rows:
                for dr in rows:
                    sProcessHTML += "<tr>" \
                        "<td>" + str((dr["Component"] if dr["Component"] else "")) + "</td>" \
                        "<td>" + str((dr["Instance"] if dr["Instance"] else "")) + "</td>" \
                        "<td>" + str((dr["LoadValue"] if dr["LoadValue"] else "")) + "</td>" \
                        "<td>" + str((dr["Heartbeat"] if dr["Heartbeat"] else "")) + "</td>" \
                        "<td>" + str((dr["Enabled"] if dr["Enabled"] else "")) + "</td>" \
                        "<td>" + str((dr["mslr"] if dr["mslr"] is not None else "")) + "</td>" \
                        "<td><span class='ui-icon ui-icon-document forceinline view_component_log' component='" + str((dr["Component"] if dr["Component"] else "")) + "'></span></td>" \
                        "</tr>"

            sUserHTML = ""
            sSQL = "select u.full_name, us.login_dt, us.heartbeat as last_update, us.address," \
                " case when us.kick = 0 then 'Active' when us.kick = 1 then 'Warning' " \
                " when us.kick = 2 then 'Kicking' when us.kick = 3 then 'Inactive' end as kick " \
                " from user_session us join users u on u.user_id = us.user_id " \
                " where timestampdiff(MINUTE,us.heartbeat, now()) < 10" \
                " order by us.heartbeat desc"
            rows = self.db.select_all_dict(sSQL)
            if rows:
                for dr in rows:
                    sUserHTML += "<tr>" \
                        "<td>" + str((dr["full_name"] if dr["full_name"] else "")) + "</td>" \
                        "<td>" + str((dr["login_dt"] if dr["login_dt"] else "")) + "</td>" \
                        "<td>" + str((dr["last_update"] if dr["last_update"] else "")) + "</td>" \
                        "<td>" + str((dr["address"] if dr["address"] else "")) + "</td>" \
                        "<td>" + str((dr["kick"] if dr["kick"] else "")) + "</td>" \
                        "</tr>"
                    
            sMessageHTML = ""
            sSQL = "select msg_to, msg_subject," \
                " case status when 0 then 'Queued' when 1 then 'Error' when 2 then 'Success' end as status," \
                " error_message," \
                " convert(date_time_entered, CHAR(20)) as entered_dt, convert(date_time_completed, CHAR(20)) as completed_dt" \
                " from message" \
                " order by msg_id desc limit 100"
            rows = self.db.select_all_dict(sSQL)
            if rows:
                for dr in rows:
                    sMessageHTML += "<tr>" \
                        "<td>" + str((dr["msg_to"] if dr["msg_to"] else "")) + "</td>" \
                        "<td>" + str((dr["msg_subject"] if dr["msg_subject"] else "")) + "</td>" \
                        "<td>" + str((dr["status"] if dr["status"] else "")) + "</td>" \
                        "<td>" + uiCommon.SafeHTML(str((dr["error_message"] if dr["error_message"] else ""))) + "</td>" \
                        "<td>" + str((dr["entered_dt"] if dr["entered_dt"] else "")) + "<br />" + str((dr["completed_dt"] if dr["completed_dt"] else "")) + "</td>" \
                        "</tr>"
                    
            
            return "{ \"processes\" : \"%s\", \"users\" : \"%s\", \"messages\" : \"%s\" }" % (sProcessHTML, sUserHTML, uiCommon.packJSON(sMessageHTML))

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetProcessLogfile(self):
        try:
            component = uiCommon.getAjaxArg("component")
            logfile = ""
            if component and uiGlobals.config.has_key("logfiles"):
                logdir = uiGlobals.config["logfiles"]
                logfile = "%s/%s.log" % (logdir, component)
                if os.path.exists(logfile):
                    with open(logfile, 'r') as f:
                        f.seek (0, 2)           # Seek @ EOF
                        fsize = f.tell()        # Get Size
                        f.seek (max (fsize - 102400, 0), 0) # Set pos @ last n chars
                        tail = f.readlines()       # Read to end

                        return uiCommon.packJSON("".join(tail))
            
            return uiCommon.packJSON("Unable to read logfile. [%s]" % logfile)
        except Exception as ex:
            return ex.__str__()
            
    def wmGetLog(self):
        try:
            sObjectID = uiCommon.getAjaxArg("sObjectID")
            sObjectType = uiCommon.getAjaxArg("sObjectType")
            sSearch = uiCommon.getAjaxArg("sSearch")
            sRecords = uiCommon.getAjaxArg("sRecords", "100")
            sFrom = uiCommon.getAjaxArg("sFrom", "")
            sTo = uiCommon.getAjaxArg("sTo", "")
            
            sWhereString = "(1=1)"
            if sObjectID:
                sWhereString += " and usl.object_id = '" + sObjectID + "'"

            if sObjectType:
                if sObjectType > "0": # but a 0 object type means we want everything
                    sWhereString += " and usl.object_type = '" + sObjectType + "'"
           
            if not sObjectID and not sObjectType: # no arguments passed means we want a security log
                sWhereString += " and usl.log_type = 'Security'"

            sDateSearchString = ""
            sTextSearch = ""
            
            if sSearch:
                sTextSearch += " and (usl.log_dt like '%%" + sSearch.replace("'", "''") + "%%' " \
                    "or u.full_name like '%%" + sSearch.replace("'", "''") + "%%' " \
                    "or usl.log_msg like '%%" + sSearch.replace("'", "''") + "%%') "
            
            if sFrom:
                sDateSearchString += " and usl.log_dt >= str_to_date('" + sFrom + "', '%%m/%%d/%%Y')"
            if sTo:
                sDateSearchString += " and usl.log_dt <= str_to_date('" + sTo + "', '%%m/%%d/%%Y')"
                
            sSQL = "select usl.log_msg as log_msg," \
                " convert(usl.log_dt, CHAR(20)) as log_dt, u.full_name" \
                " from user_security_log usl" \
                " join users u on u.user_id = usl.user_id" \
                " where " + sWhereString + sDateSearchString + sTextSearch + \
                " order by usl.log_id desc" \
                " limit " + (sRecords if sRecords else "100")
                
            sLog = ""
            rows = self.db.select_all_dict(sSQL)
            if self.db.error:
                return "{ \"error\" : \"Unable to get log. %s\" }" % (self.db.error)
            if rows:
                i = 1
                sb = []
                for row in rows:
                    sb.append("[")
                    sb.append("\"%s\", " % (row["log_dt"]))
                    sb.append("\"%s\", " % (uiCommon.packJSON(row["full_name"])))
                    sb.append("\"%s\"" % (uiCommon.packJSON(uiCommon.SafeHTML(row["log_msg"]))))
                    sb.append("]")
                
                    #the last one doesn't get a trailing comma
                    if i < len(rows):
                        sb.append(",")
                        
                    i += 1
    
                sLog = "".join(sb)

            return "{ \"log\" : [ %s ] }" % (sLog)

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetDatabaseTime(self):
        sNow = self.db.select_col_noexcep("select now()")
        if self.db.error:
            return self.db.error
        
        if sNow:
            return str(sNow)
        else:
            return "Unable to get system time."
        
    def wmGetActionPlans(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sActionID = uiCommon.getAjaxArg("sActionID")
        sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
        try:
            sHTML = ""

            sSQL = "select plan_id, date_format(ap.run_on_dt, '%%m/%%d/%%Y %%H:%%i') as run_on_dt, ap.source, ap.action_id, ap.ecosystem_id," \
                " ea.action_name, e.ecosystem_name, ap.source, ap.schedule_id" \
                " from action_plan ap" \
                " left outer join ecotemplate_action ea on ap.action_id = ea.action_id" \
                " left outer join ecosystem e on ap.ecosystem_id = e.ecosystem_id" \
                " where ap.task_id = '" + sTaskID + "'" + \
                (" and ap.action_id = '" + sActionID + "'" if sActionID else "") + \
                (" and ap.ecosystem_id = '" + sEcosystemID + "'" if sEcosystemID else "") + \
                " order by ap.run_on_dt"
            dt = self.db.select_all_dict(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)
            else:
                if dt:
                    for dr in dt:
                        sHTML += " <div class=\"ui-widget-content ui-corner-all pointer clearfloat action_plan\"" \
                            " id=\"ap_" + str(dr["plan_id"]) + "\"" \
                            " plan_id=\"" + str(dr["plan_id"]) + "\"" \
                            " eco_id=\"" + dr["ecosystem_id"] + "\"" \
                            " run_on=\"" + str(dr["run_on_dt"]) + "\"" \
                            " source=\"" + dr["source"] + "\"" \
                            " schedule_id=\"" + str(dr["schedule_id"]) + "\"" \
                        ">"
                        sHTML += " <div class=\"floatleft action_plan_name\">"
    
                        # an icon denotes if it's manual or scheduled
                        if dr["source"] == "schedule":
                            sHTML += "<span class=\"floatleft ui-icon ui-icon-calculator\" title=\"Scheduled\"></span>"
                        else:
                            sHTML += "<span class=\"floatleft ui-icon ui-icon-document\" title=\"Run Later\"></span>"
    
                        sHTML += dr["run_on_dt"]
    
                        # show the action and ecosystem if it's in the results but NOT passed in
                        # that means we are looking at this from a TASK
                        if not sActionID:
                            if dr["ecosystem_name"]:
                                sHTML += " " + dr["ecosystem_name"]
    
                            if dr["action_name"]:
                                sHTML += " (" + dr["action_name"] + ")"
                        sHTML += " </div>"
    
                        sHTML += " <div class=\"floatright\">"
                        sHTML += "<span class=\"ui-icon ui-icon-trash action_plan_remove_btn\" title=\"Delete Plan\"></span>"
                        sHTML += " </div>"
    
    
                        sHTML += " </div>"

            return sHTML

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetActionSchedules(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sActionID = uiCommon.getAjaxArg("sActionID")
        sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
        try:
            sHTML = ""

            sSQL = "select s.schedule_id, s.label, s.descr, e.ecosystem_name, a.action_name" \
                " from action_schedule s" \
                " left outer join ecotemplate_action a on s.action_id = a.action_id" \
                " left outer join ecosystem e on s.ecosystem_id = e.ecosystem_id" \
                " where s.task_id = '" + sTaskID + "'" + \
                (" and e.ecosystem_id = '" + sEcosystemID + "'" if sEcosystemID else "")
            dt = self.db.select_all_dict(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)
            else:
                if dt:
                    for dr in dt:
                        sToolTip = ""
                        # show the action and ecosystem if it's in the results but NOT passed in
                        # that means we are looking at this from a TASK
                        if not sActionID:
                            sToolTip += "Ecosystem: " + (dr["ecosystem_name"] if dr["ecosystem_name"] else "None") + "<br />"
        
                            if dr["action_name"]:
                                sToolTip += "Action: " + dr["action_name"] + "<br />"
        
                        sToolTip += (dr["descr"] if dr["descr"] else "")
        
                        # draw it
                        sHTML += " <div class=\"ui-widget-content ui-corner-all pointer clearfloat action_schedule\"" \
                            " id=\"as_" + dr["schedule_id"] + "\"" \
                        ">"
                        sHTML += " <div class=\"floatleft schedule_name\">"
        
                        sHTML += "<span class=\"floatleft ui-icon ui-icon-calculator schedule_tip\" title=\"" + sToolTip + "\"></span>"
        
                        sHTML += (dr["schedule_id"] if not dr["label"] else dr["label"])
        
                        sHTML += " </div>"
        
                        sHTML += " <div class=\"floatright\">"
                        sHTML += "<span class=\"ui-icon ui-icon-trash schedule_remove_btn\" title=\"Delete Schedule\"></span>"
                        sHTML += " </div>"
        
        
                        sHTML += " </div>"

            return sHTML

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetRecurringPlan(self):
        sScheduleID = uiCommon.getAjaxArg("sScheduleID")
        # tracing this backwards, if the action_plan table has a row marked "schedule" but no schedule_id, problem.
        if not sScheduleID:
            uiCommon.log("Unable to retrieve Reccuring Plan - schedule id argument not provided.")
        
        sb = []

        # now we know the details, go get the timetable for that specific schedule
        sSQL = "select schedule_id, months, days, hours, minutes, days_or_weeks, label" \
            " from action_schedule" \
            " where schedule_id = '" + sScheduleID + "'"
        dt = self.db.select_all_dict(sSQL)
        if self.db.error:
            uiCommon.log_nouser(self.db.error, 0)

        if dt:
            for dr in dt:
                sMo = dr["months"]
                sDa = dr["days"]
                sHo = dr["hours"]
                sMi = dr["minutes"]
                sDW = dr["days_or_weeks"]
                sDesc = (dr["schedule_id"] if not dr["label"] else dr["label"])
    
                sb.append("{")
                sb.append("\"sDescription\" : \"%s\"," % sDesc)
                sb.append("\"sMonths\" : \"%s\"," % sMo)
                sb.append("\"sDays\" : \"%s\"," % sDa)
                sb.append("\"sHours\" : \"%s\"," % sHo)
                sb.append("\"sMinutes\" : \"%s\"," % sMi)
                sb.append("\"sDaysOrWeeks\" : \"%s\"" % sDW)
                sb.append("}")
        else:
            uiCommon.log("Unable to find details for Recurring Action Plan. " + self.db.error + " ScheduleID [" + sScheduleID + "]")

        return "".join(sb)
    
    def wmDeleteSchedule(self):
        try:
            sScheduleID = uiCommon.getAjaxArg("sScheduleID")
    
            if not sScheduleID:
                uiCommon.log("Missing Schedule ID.")
                return "Missing Schedule ID."
    
            sSQL = "delete from action_plan where schedule_id = '" + sScheduleID + "'"
            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            sSQL = "delete from action_schedule where schedule_id = '" + sScheduleID + "'"
            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)
    
            #  if we made it here, so save the logs
            uiCommon.WriteObjectDeleteLog(uiGlobals.CatoObjectTypes.EcoTemplate, "", "", "Schedule [" + sScheduleID + "] deleted.")
    
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmDeleteActionPlan(self):
        try:
            iPlanID = uiCommon.getAjaxArg("iPlanID")
    
            if iPlanID < 1:
                uiCommon.log("Missing Action Plan ID.")
                return "Missing Action Plan ID."
    
            sSQL = "delete from action_plan where plan_id = " + iPlanID

            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            #  if we made it here, so save the logs
            uiCommon.WriteObjectDeleteLog(uiGlobals.CatoObjectTypes.EcoTemplate, "", "", "Action Plan [" + iPlanID + "] deleted.")
    
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
    
    def wmRunLater(self):
        try:
            sTaskID = uiCommon.getAjaxArg("sTaskID")
            sActionID = uiCommon.getAjaxArg("sActionID")
            sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
            sRunOn = uiCommon.getAjaxArg("sRunOn")
            sParameterXML = uiCommon.getAjaxArg("sParameterXML")
            iDebugLevel = uiCommon.getAjaxArg("iDebugLevel")
            sAccountID = uiCommon.getAjaxArg("sAccountID")
            
            if not sTaskID or not sRunOn:
                uiCommon.log("Missing Action Plan date or Task ID.")

            # we encoded this in javascript before the ajax call.
            # the safest way to unencode it is to use the same javascript lib.
            # (sometimes the javascript and .net libs don't translate exactly, google it.)
            sParameterXML = uiCommon.unpackJSON(sParameterXML)
            
            # we gotta peek into the XML and encrypt any newly keyed values
            sParameterXML = uiCommon.PrepareAndEncryptParameterXML(sParameterXML)          

            sSQL = "insert into action_plan (task_id, action_id, ecosystem_id, account_id," \
                " run_on_dt, parameter_xml, debug_level, source)" \
                " values (" \
                " '" + sTaskID + "'," + \
                (" '" + sActionID + "'" if sActionID else "''") + "," + \
                (" '" + sEcosystemID + "'" if sEcosystemID else "''") + "," + \
                (" '" + sAccountID + "'" if sAccountID else "''") + "," \
                " str_to_date('" + sRunOn + "', '%%m/%%d/%%Y %%H:%%i')," + \
                (" '" + catocommon.tick_slash(sParameterXML) + "'" if sParameterXML else "null") + "," + \
                (iDebugLevel if iDebugLevel > "-1" else "null") + "," \
                " 'manual'" \
                ")"

            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmRunRepeatedly(self):
        try:
            sTaskID = uiCommon.getAjaxArg("sTaskID")
            sActionID = uiCommon.getAjaxArg("sActionID")
            sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
            sMonths = uiCommon.getAjaxArg("sMonths")
            sDays = uiCommon.getAjaxArg("sDays")
            sHours = uiCommon.getAjaxArg("sHours")
            sMinutes = uiCommon.getAjaxArg("sMinutes")
            sDaysOrWeeks = uiCommon.getAjaxArg("sDaysOrWeeks")
            sParameterXML = uiCommon.getAjaxArg("sParameterXML")
            iDebugLevel = uiCommon.getAjaxArg("iDebugLevel")
            sAccountID = uiCommon.getAjaxArg("sAccountID")
            
            if not sTaskID or not sMonths or not sDays or not sHours or not sMinutes or not sDaysOrWeeks:
                uiCommon.log("Missing or invalid Schedule timing or Task ID.")

            # we encoded this in javascript before the ajax call.
            # the safest way to unencode it is to use the same javascript lib.
            # (sometimes the javascript and .net libs don't translate exactly, google it.)
            sParameterXML = uiCommon.unpackJSON(sParameterXML)
            
            # we gotta peek into the XML and encrypt any newly keyed values
            sParameterXML = uiCommon.PrepareAndEncryptParameterXML(sParameterXML)                

            # figure out a label and a description
            sDesc = ""
            sLabel, sDesc = uiCommon.GenerateScheduleLabel(sMonths, sDays, sHours, sMinutes, sDaysOrWeeks)

            sSQL = "insert into action_schedule (schedule_id, task_id, action_id, ecosystem_id, account_id," \
                " months, days, hours, minutes, days_or_weeks, label, descr, parameter_xml, debug_level)" \
                   " values (" \
                " '" + catocommon.new_guid() + "'," \
                " '" + sTaskID + "'," \
                + (" '" + sActionID + "'" if sActionID else "''") + "," \
                + (" '" + sEcosystemID + "'" if sEcosystemID else "''") + "," \
                + (" '" + sAccountID + "'" if sAccountID else "''") + "," \
                " '" + sMonths + "'," \
                " '" + sDays + "'," \
                " '" + sHours + "'," \
                " '" + sMinutes + "'," \
                " '" + sDaysOrWeeks + "'," \
                + (" '" + sLabel + "'" if sLabel else "null") + "," \
                + (" '" + sDesc + "'" if sDesc else "null") + "," \
                + (" '" + catocommon.tick_slash(sParameterXML) + "'" if sParameterXML else "null") + "," \
                + (iDebugLevel if iDebugLevel > "-1" else "null") + \
                ")"

            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmSavePlan(self):
        try:
            iPlanID = uiCommon.getAjaxArg("iPlanID")
            sParameterXML = uiCommon.getAjaxArg("sParameterXML")
            iDebugLevel = uiCommon.getAjaxArg("iDebugLevel")
            """
             * JUST AS A REMINDER:
             * There is no parameter 'merging' happening here.  This is a Plan ...
             *   it has ALL the parameters it needs to pass to the CE.
             * 
             * """
    
            if not iPlanID:
                uiCommon.log("Missing Action Plan ID.")

            # we encoded this in javascript before the ajax call.
            # the safest way to unencode it is to use the same javascript lib.
            # (sometimes the javascript and .net libs don't translate exactly, google it.)
            sParameterXML = uiCommon.unpackJSON(sParameterXML)
            
            # we gotta peek into the XML and encrypt any newly keyed values
            sParameterXML = uiCommon.PrepareAndEncryptParameterXML(sParameterXML)                

            sSQL = "update action_plan" \
                " set parameter_xml = " + ("'" + catocommon.tick_slash(sParameterXML) + "'" if sParameterXML else "null") + "," \
                " debug_level = " + (iDebugLevel if iDebugLevel > -1 else "null") + \
                " where plan_id = " + iPlanID

            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)


    def wmSaveSchedule(self):
        sScheduleID = uiCommon.getAjaxArg("sScheduleID")
        sMonths = uiCommon.getAjaxArg("sMonths")
        sDays = uiCommon.getAjaxArg("sDays")
        sHours = uiCommon.getAjaxArg("sHours")
        sMinutes = uiCommon.getAjaxArg("sMinutes")
        sDaysOrWeeks = uiCommon.getAjaxArg("sDaysOrWeeks")
        sParameterXML = uiCommon.getAjaxArg("sParameterXML")
        iDebugLevel = uiCommon.getAjaxArg("iDebugLevel")
        """
         * JUST AS A REMINDER:
         * There is no parameter 'merging' happening here.  This is a Scheduled Plan ...
         *   it has ALL the parameters it needs to pass to the CE.
         * 
         * """

        try:
            if not sScheduleID or not sMonths or not sDays or not sHours or not sMinutes or not sDaysOrWeeks:
                uiCommon.log("Missing Schedule ID or invalid timetable.")

            # we encoded this in javascript before the ajax call.
            # the safest way to unencode it is to use the same javascript lib.
            # (sometimes the javascript and .net libs don't translate exactly, google it.)
            sParameterXML = uiCommon.unpackJSON(sParameterXML)
            
            # we gotta peek into the XML and encrypt any newly keyed values
            sParameterXML = uiCommon.PrepareAndEncryptParameterXML(sParameterXML)                

            # whack all plans for this schedule, it's been changed
            sSQL = "delete from action_plan where schedule_id = '" + sScheduleID + "'"
            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)


            # figure out a label
            sLabel, sDesc = uiCommon.GenerateScheduleLabel(sMonths, sDays, sHours, sMinutes, sDaysOrWeeks)

            sSQL = "update action_schedule set" \
                " months = '" + sMonths + "'," \
                " days = '" + sDays + "'," \
                " hours = '" + sHours + "'," \
                " minutes = '" + sMinutes + "'," \
                " days_or_weeks = '" + sDaysOrWeeks + "'," \
                " label = " + ("'" + sLabel + "'" if sLabel else "null") + "," \
                " descr = " + ("'" + sDesc + "'" if sDesc else "null") + "," \
                " parameter_xml = " + ("'" + catocommon.tick_slash(sParameterXML) + "'" if sParameterXML else "null") + "," \
                " debug_level = " + (iDebugLevel if iDebugLevel > -1 else "null") + \
                " where schedule_id = '" + sScheduleID + "'"

            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetSettings(self):
        try:
            s = settings.settings()
            if s:
                return s.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Error getting settings.\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmSaveSettings(self):
        """
            In this method, the values come from the browser in a jQuery serialized array of name/value pairs.
        """
        try:
            sType = uiCommon.getAjaxArg("sType")
            sValues = uiCommon.getAjaxArg("sValues")
        
            # sweet, use getattr to actually get the class we want!
            objname = getattr(settings.settings, sType.lower())
            obj = objname()
            if obj:
                # spin the sValues array and set the appropriate properties.
                # setattr is so awesome
                for pair in sValues:
                    setattr(obj, pair["name"], pair["value"])
                    # print  "setting %s to %s" % (pair["name"], pair["value"])
                # of course all of our settings classes must have a DBSave method
                result, msg = obj.DBSave()
                
                if result:
                    uiCommon.AddSecurityLog(uiGlobals.SecurityLogTypes.Security,
                        uiGlobals.SecurityLogActions.ConfigChange, uiGlobals.CatoObjectTypes.NA, "",
                        "%s settings changed." % sType.capitalize())
                    
                    return "{\"result\":\"success\"}"
                else:
                    return "{\"result\":\"fail\",\"error\":\"%s\"}" % msg
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Error saving settings - no type provided.\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetMyAccount(self):
        try:
            user_id = uiCommon.GetSessionUserID()

            sSQL = """select full_name, username, authentication_type, email, 
                ifnull(security_question, '') as security_question, 
                ifnull(security_answer, '') as security_answer
                from users
                where user_id = '%s'""" % user_id
            dr = self.db.select_row_dict(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)
                raise Exception(self.db.error)
            else:
                # here's the deal - we aren't even returning the 'local' settings if the type is ldap.
                if dr["authentication_type"] == "local":
                    return json.dumps(dr)
                else:
                    d = {"full_name":dr["full_name"], "username": dr["username"], "email":dr["email"], "type":dr["authentication_type"]}
                    return json.dumps(d)

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            
    def wmSaveMyAccount(self):
        """
            In this method, the values come from the browser in a jQuery serialized array of name/value pairs.
        """
        
        # TODO 
        # this should move to the user class
        try:
            user_id = uiCommon.GetSessionUserID()
            sValues = uiCommon.getAjaxArg("sValues")
        
            sql_bits = []
            for pair in sValues:
                # but to prevent sql injection, only build a sql from values we accept
                if pair["name"] == "my_email":
                    sql_bits.append("email = '%s'" % catocommon.tick_slash(pair["value"]))
                if pair["name"] == "my_question":
                    sql_bits.append("security_question = '%s'" % catocommon.tick_slash(pair["value"]))
                if pair["name"] == "my_answer":
                    if pair["value"]:
                        sql_bits.append("security_answer = '%s'" % catocommon.cato_encrypt(pair["value"]))

                # only do the password if it was provided
                if pair["name"] == "my_password":
                    newpw = uiCommon.unpackJSON(pair["value"])
                    if newpw:
                        result, msg = catouser.User.ValidatePassword(user_id, newpw)
                        if result:
                            encpw = catocommon.cato_encrypt(newpw)
                            sql = "insert user_password_history (user_id, change_time, password) values ('%s', now(), '%s')" % (user_id, encpw)
                            if not self.db.exec_db_noexcep(sql):
                                uiCommon.log_nouser(self.db.error, 0)
                                return self.db.error

                            sql_bits.append("user_password = '%s'" % encpw)
                        else:
                            return "{\"info\":\"%s\"}" % msg


            sql = "update users set %s where user_id = '%s'" % (",".join(sql_bits), user_id)

            if not self.db.exec_db_noexcep(sql):
                uiCommon.log_nouser(self.db.error, 0)
                return self.db.error

            uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.User, user_id, user_id, "My Account settings updated.")
                
            return "{\"result\":\"success\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetUsersTable(self):
        try:
            sHTML = ""
            sFilter = uiCommon.getAjaxArg("sSearch")
            sPage = uiCommon.getAjaxArg("sPage")
            maxrows = 25

            u = catouser.Users(sFilter)
            if u.rows:
                start, end, pager_html = uiCommon.GetPager(len(u.rows), maxrows, sPage)

                for row in u.rows[start:end]:
                    sHTML += "<tr user_id=\"" + row["user_id"] + "\">"
                    sHTML += "<td class=\"chkboxcolumn\">"
                    sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                    " id=\"chk_" + row["user_id"] + "\"" \
                    " tag=\"chk\" />"
                    sHTML += "</td>"
                    
                    sHTML += "<td class=\"selectable\">" + row["status"] + "</td>"
                    sHTML += "<td class=\"selectable\">" + row["full_name"] + "</td>"
                    sHTML += "<td class=\"selectable\">" + row["username"] + "</td>"
                    sHTML += "<td class=\"selectable\">" + row["role"] + "</td>"
                    sHTML += "<td class=\"selectable\">" + str(row["last_login_dt"]) + "</td>"
                    
                    sHTML += "</tr>"
    
            return "{\"pager\" : \"%s\", \"rows\" : \"%s\"}" % (uiCommon.packJSON(pager_html), uiCommon.packJSON(sHTML))    
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()           
        
    def wmGetUser(self):
        try:
            sID = uiCommon.getAjaxArg("sUserID")
            u = catouser.User()
            if u:
                u.FromID(sID)
                if u.ID:
                    return u.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get details for User [" + sID + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetAsset(self):
        try:
            sID = uiCommon.getAjaxArg("sAssetID")
            a = asset.Asset()
            if a:
                a.FromID(sID)
                if a.ID:
                    return a.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get details for Asset [" + sID + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmUpdateUser(self):
        """
            Updates a user.  Will only update the values passed to it.
            
            TODO: this should be moved to the user module.
        """
        try:
            # FIRST THINGS FIRST - it's critical we make sure the current user making this call
            # is an Administrator
            
            
            args = uiCommon.getAjaxArgs()
            user_id = args["ID"]
            
            sql_bits = []
            for key, val in args.iteritems():
                # but to prevent sql injection, only build a sql from values we accept
                if key == "LoginID":
                    sql_bits.append("username='%s'" % val)
                if key == "FullName":
                    sql_bits.append("full_name='%s'" % val)
                if key == "Status":
                    sql_bits.append("status='%s'" % val)
                if key == "AuthenticationType":
                    sql_bits.append("authentication_type='%s'" % val)
                if key == "ForceChange":
                    sql_bits.append("force_change='%s'" % val)
                if key == "Email":
                    sql_bits.append("email='%s'" % val)
                if key == "Role":
                    sql_bits.append("user_role='%s'" % val)
                if key == "FailedLoginAttempts":
                    sql_bits.append("failed_login_attempts='%s'" % val)


                # only do the password if it was provided
                if key == "Password":
                    newpw = uiCommon.unpackJSON(val)
                    if newpw:
                        result, msg = catouser.User.ValidatePassword(user_id, newpw)
                        if result:
                            sql_bits.append("user_password = '%s'" % catocommon.cato_encrypt(newpw))
                        else:
                            return "{\"info\":\"%s\"}" % msg

                # Here's something special...
                # If the arg "RandomPassword" was provided and is true...
                # Generate a new password and send out an email.
                
                # AND - don't sent it to the email on the submit data, rather to the email on the
                
                # IF for some reason this AND a password were provided, it means someone is hacking
                # (We don't do both of them at the same time.)
                # so the provided one takes precedence.
                if key == "NewRandomPassword" and not args.has_key("Password"):
                    u = catouser.User()
                    if u:
                        u.FromID(args["ID"])
                        if not u.Email:
                            return "{\"info\":\"Unable to reset password - User does not have an email address defined.\"}"
                        else:
                            sNewPassword = catocommon.generate_password()
                            sql_bits.append("user_password='%s'" % sNewPassword)
                              
                            # an additional log entry
                            uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.User, user_id, user_id, "Password reset.")

                            # TODO: 
                            # would get the URL of the application, construct an email message
                            # and send using our SendEmail function (which puts a row in the message table)
                            
                            #sURL = uiCommon.GetSessionObject("app_url", "user")
                            sURL = ""
                            # now, send out an email
                            s_set = settings.settings.security()
                            body = s_set.NewUserMessage
                            if not body:
                                body = """%s - your password has been reset by an Administrator.\n\n
                                Your temporary password is: %s.\n\n
                                Access the application at <a href='%s' target='_blank'>%s</a>.""" % (u.FullName, sNewPassword, sURL, sURL)

                                # replace our special tokens with the values
                                body = body.replace("##FULLNAME##", u.FullName).replace("##USERNAME##", u.LoginID).replace("##PASSWORD##", sNewPassword).replace("##URL##", sURL)

                                print("Would send email here...")
#                                if !uiCommon.SendEmailMessage(sEmail.strip(), ag.APP_COMPANYNAME + " Account Management", "Account Action in " + ag.APP_NAME, sBody, 0000BYREF_ARG0000sErr:
                        
            
            sql = "update users set %s where user_id = '%s'" % (",".join(sql_bits), user_id)

            if not self.db.exec_db_noexcep(sql):
                uiCommon.log_nouser(self.db.error, 0)
                "{\"error\":\"%s\"}" % self.db.error

            uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.User, user_id, user_id, "User updated.")
               
               
            if args.has_key("Groups"):
                # if the Groups argument was empty, that means delete them all!
                # no matter what the case, we're doing a whack-n-add here.
                sql = "delete from object_tags where object_id = '%s'" % user_id
                if not self.db.exec_db_noexcep(sql):
                    uiCommon.log_nouser(self.db.error, 0)
                # now, lets do any groups that were passed in. 
                if args["Groups"]:
                    for tag in args["Groups"]:
                        sql = "insert object_tags (object_type, object_id, tag_name) values (1, '%s','%s')" % (user_id, tag)
                        if not self.db.exec_db_noexcep(sql):
                            uiCommon.log_nouser(self.db.error, 0)
            
            return "{\"result\":\"success\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmCreateUser(self):
        try:
            args = uiCommon.getAjaxArgs()

            u, msg = catouser.User.DBCreateNew(args["LoginID"], args["FullName"], args["AuthenticationType"], uiCommon.unpackJSON(args["Password"]),
                                            args["GeneratePW"], args["ForceChange"], args["Role"], args["Email"], args["Status"], args["Groups"])
            if msg:
                return "{\"error\" : \"" + msg + "\"}"
            if u == None:
                return "{\"error\" : \"Unable to create User.\"}"

            uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.User, u.ID, u.FullName, "User Created")

            return u.AsJSON()
        
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmDeleteUsers(self):
        WhoAmI = uiCommon.GetSessionUserID()
        try:
            sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
            if len(sDeleteArray) < 36:
                return "{\"info\" : \"Unable to delete - no selection.\"}"

            now = []
            later = []

            aUsers = sDeleteArray.split(",")
            for sUserID in aUsers:
                if len(sUserID) == 36: # a guid + quotes
                    # you cannot delete yourself!!!
                    if sUserID != WhoAmI:
                        # this will flag a user for later deletion by the system
                        # it returns True if it's safe to delete now
                        if catouser.User.HasHistory(sUserID):
                            later.append(sUserID)
                        else:
                            now.append(sUserID)


            #  delete some users...
            if now:
                sSQL = "delete from users where user_id in (%s)" % "'%s'" % "','".join(now)
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log_nouser(self.db.error, 0)

            #  flag the others...
            if later:
                sSQL = "update users set status = 86 where user_id in (%s)" % "'%s'" % "','".join(later)
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log_nouser(self.db.error, 0)

            self.db.tran_commit()

            return "{\"result\" : \"success\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetAssetsTable(self):
        try:
            sHTML = ""
            sFilter = uiCommon.getAjaxArg("sSearch")
            sPage = uiCommon.getAjaxArg("sPage")
            maxrows = 25

            a = asset.Assets(sFilter)
            if a.rows:
                start, end, pager_html = uiCommon.GetPager(len(a.rows), maxrows, sPage)

                for row in a.rows[start:end]:
                    sHTML += "<tr asset_id=\"" + row["asset_id"] + "\">"
                    sHTML += "<td class=\"chkboxcolumn\">"
                    sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                    " id=\"chk_" + row["asset_id"] + "\"" \
                    " tag=\"chk\" />"
                    sHTML += "</td>"
                    
                    sHTML += "<td class=\"selectable\">%s</td>" % row["asset_name"]
                    sHTML += "<td class=\"selectable\">%s</td>" % row["asset_status"]
                    sHTML += "<td class=\"selectable\">%s</td>" % (row["address"] if row["address"] else "")
                    sHTML += "<td class=\"selectable\">%s</td>" % (row["credentials"] if row["credentials"] else "")
                    
                    sHTML += "</tr>"

            return "{\"pager\" : \"%s\", \"rows\" : \"%s\"}" % (uiCommon.packJSON(pager_html), uiCommon.packJSON(sHTML))    
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()           
        
    def wmAssetSearch(self):
        try:
            sFilter = uiCommon.getAjaxArg("sSearch")
            sAllowMultiSelect = uiCommon.getAjaxArg("bAllowMultiSelect")
            bAllowMultiSelect = catocommon.is_true(sAllowMultiSelect)
            
            a = asset.Assets(sFilter)
            if a.rows:
                sHTML = "<hr />"
    
                iRowsToGet = len(a.rows)
    
                if iRowsToGet == 0:
                    sHTML += "No results found"
                else:
                    if iRowsToGet >= 100:
                        sHTML += "<div>Search found " + iRowsToGet + " results.  Displaying the first 100.</div>"
                        iRowsToGet = 99

                    sHTML += "<ul id=\"search_asset_ul\" class=\"search_dialog_ul\">"
    
                    i = 0
                    for row in a.rows:
                        if i > iRowsToGet:
                            break
                        
                        sHTML += "<li class=\"ui-widget-content ui-corner-all search_dialog_value\" tag=\"asset_picker_row\"" \
                            " asset_id=\"" + row["asset_id"] + "\"" \
                            " asset_name=\"" + row["asset_name"] + "\"" \
                            "\">"
                        sHTML += "<div class=\"search_dialog_value_name\">"
                        if bAllowMultiSelect:
                            sHTML += "<input type='checkbox' name='assetcheckboxes' id='assetchk_" + row["asset_id"] + "' value='assetchk_" + row["asset_id"] + "'>"
                        sHTML += "<span>" + row["asset_name"] + "</span>"
                        sHTML += "</div>"

                        sHTML += "<span class=\"search_dialog_value_inline_item\">Address: " + row["address"] + "</span>"
    
                        sHTML += "</li>"
                        
                        i += 1
                        
                sHTML += "</ul>"

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            
    def wmGetCredentialsTable(self):
        try:
            sHTML = ""
            sFilter = uiCommon.getAjaxArg("sSearch")
            sPage = uiCommon.getAjaxArg("sPage")
            maxrows = 25

            c = asset.Credentials(sFilter)
            if c.rows:
                start, end, pager_html = uiCommon.GetPager(len(c.rows), maxrows, sPage)

                for row in c.rows[start:end]:
                    sHTML += "<tr credential_id=\"" + row["credential_id"] + "\">"
                    sHTML += "<td class=\"chkboxcolumn\">"
                    sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                    " id=\"chk_" + row["credential_id"] + "\"" \
                    " tag=\"chk\" />"
                    sHTML += "</td>"
                    
                    sHTML += "<td class=\"selectable\">%s</td>" % row["credential_name"]
                    sHTML += "<td class=\"selectable\">%s</td>" % row["username"]
                    sHTML += "<td class=\"selectable\">%s</td>" % (row["domain"] if row["domain"] else "")
                    sHTML += "<td class=\"selectable\">%s</td>" % (row["shared_cred_desc"] if row["shared_cred_desc"] else "")
                    
                    sHTML += "</tr>"

            return "{\"pager\" : \"%s\", \"rows\" : \"%s\"}" % (uiCommon.packJSON(pager_html), uiCommon.packJSON(sHTML))    
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()           
        
    def wmGetCredentialsJSON(self):
        try:
            sFilter = uiCommon.getAjaxArg("sFilter")

            ac = asset.Credentials(sFilter)
            if ac:
                return ac.AsJSON()
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get Credentials using filter [" + sFilter + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetCredential(self):
        try:
            sID = uiCommon.getAjaxArg("sCredentialID")
            c = asset.Credential()
            if c:
                c.FromID(sID)
                if c.ID:
                    return c.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get details for Asset [" + sID + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmCreateAsset(self):
        try:
            args = uiCommon.getAjaxArgs()

            a, sErr = asset.Asset.DBCreateNew(args["Name"], args["Status"], args["DBName"], args["Port"],
              args["Address"], args["ConnString"], args["Tags"], args["CredentialMode"], args["Credential"])
            if sErr:
                return "{\"error\" : \"" + sErr + "\"}"
            if a == None:
                return "{\"error\" : \"Unable to create Asset.\"}"

            uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.Asset, a.ID, a.Name, "Asset Created")

            return a.AsJSON()
        
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmUpdateAsset(self):
        try:
            args = uiCommon.getAjaxArgs()

            a = asset.Asset()
            a.FromID(args["ID"])
            
            if a:
                # assuming the attribute names will match ... spin the post data and update the object
                # only where asset attributes are pre-defined.
                for k, v in args.items():
                    if hasattr(a, k):
                        setattr(a, k, v)

                result, msg = a.DBUpdate(tags=args["Tags"], credential_update_mode=args["CredentialMode"], credential=args["Credential"])
                if not result:
                    return "{\"error\" : \"" + msg + "\"}"

            return "{\"result\" : \"success\"}"
        
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmDeleteAssets(self):
        try:
            sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
            if len(sDeleteArray) < 36:
                return "{\"info\" : \"Unable to delete - no selection.\"}"

            # for this one, 'now' will be all the assets that don't have history.
            # and 'later' will get updated to 'inactive' status
            now = []
            later = []
            aAssets = sDeleteArray.split(",")
            for sAsset in aAssets:
                if len(sAsset) == 36: # a guid + quotes
                    # this will mark an asset as Disabled if it has history
                    # it returns True if it's safe to delete now
                    if asset.Asset.HasHistory(sAsset):
                        later.append(sAsset)
                    else:
                        now.append(sAsset)

            # delete some now
            if now:
                sSQL = """delete from asset_credential
                    where shared_or_local = 1
                    and credential_id in (select credential_id from asset where asset_id in (%s))
                    """ % "'%s'" % "','".join(now)
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log_nouser(self.db.error, 0)

                sSQL = "delete from asset where asset_id in (%s)" % "'%s'" % "','".join(now)
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log_nouser(self.db.error, 0)

            #  deactivate the others...
            if later:
                sSQL = "update asset set asset_status = 'Inactive' where asset_id in (%s)" % "'%s'" % "','".join(later)
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log_nouser(self.db.error, 0)

            self.db.tran_commit()

            if later:
                return "{\"result\" : \"success\", \"info\" : \"One or more assets could not be deleted due to historical information.  These Assets have been marked as Inactive.\"}"
            else:
                return "{\"result\" : \"success\"}"
                
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            
    def wmCreateCredential(self):
        try:
            args = uiCommon.getAjaxArgs()

            # a little different than the others ... crednetial objects must be instantiated
            # before calling DBCreateNew
            # sName, sDesc, sUsername, sPassword, sShared, sDomain, sPrivPassword
            c = asset.Credential()
            c.FromArgs(args["Name"], args["Description"], args["Username"], args["Password"],
                     args["SharedOrLocal"], args["Domain"], args["PrivilegedPassword"])
            result, err = c.DBCreateNew()
            if err:
                return "{\"error\" : \"" + err + "\"}"
            if not result:
                return "{\"error\" : \"Unable to create Credential.\"}"

            uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.Credential, c.ID, c.Name, "Credential Created")

            return c.AsJSON()
        
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmDeleteCredentials(self):
        try:
            sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
            if len(sDeleteArray) < 36:
                return "{\"info\" : \"Unable to delete - no selection.\"}"

            sDeleteArray = uiCommon.QuoteUp(sDeleteArray)
            
            sSQL = """delete from asset_credential where credential_id in (%s)
                and credential_id not in (select distinct credential_id from asset where credential_id is not null)
                """ % sDeleteArray
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            return "{\"result\" : \"success\"}"
                
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            
    def wmUpdateCredential(self):
        try:
            args = uiCommon.getAjaxArgs()

            c = asset.Credential()
            c.FromID(args["ID"])
            
            if c:
                # assuming the attribute names will match ... spin the post data and update the object
                # only where asset attributes are pre-defined.
                for k, v in args.items():
                    if hasattr(c, k):
                        setattr(c, k, v)

                result, msg = c.DBUpdate()
                if not result:
                    return "{\"error\" : \"" + msg + "\"}"

            return "{\"result\" : \"success\"}"
        
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmCreateObjectFromXML(self):
        """Takes a properly formatted XML backup file, and imports each object."""
        try:
            sXML = uiCommon.getAjaxArg("sXML")
            sXML = uiCommon.unpackJSON(sXML)

            # the trick here is to return enough information back to the client
            # to best interact with the user.
            
            # what types of things were in this backup?  what are their new ids?
            items = []

            # parse it as a validation, and to find out what's in it.
            xd = None
            try:
                xd = ET.fromstring(sXML)
            except ET.ParseError as ex:
                return "{\"error\" : \"Data is not properly formatted XML.\"}"
            
            if xd is not None:
                # so, what's in here?  Tasks?  Ecotemplates?
                
                # TASKS
                for xtask in xd.iterfind("task"):
                    uiCommon.log("Importing Task [%s]" % xtask.get("name", "Unknown"), 3)
                    t = task.Task()
                    t.FromXML(ET.tostring(xtask))

                    # NOTE: possible TODO
                    # passing a db connection to task.DBSave will allow rollback of a whole 
                    # batch of task additions.
                    # if it's determined that's necessary here, just create a db connection here 
                    # and pass it in
                    result, err = t.DBSave()
                    if result:
                        # add security log
                        uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.Task, t.ID, t.Name, "Created by import.")

                        items.append({"type" : "task", "id" : t.ID, "name" : t.Name}) 
                    else:
                        if err:
                            items.append({"type" : "task", "id" : t.ID, "name" : t.Name, "info" : err}) 
                        else:
                            items.append({"type" : "task", "id" : t.ID, "name" : t.Name, "error" : "Unable to create Task. No error available."}) 
                    

            else:
                items.append({"info" : "Unable to create Task from backup XML."})
                
                #TODO: for loop for Ecotemplates and Assets will go here, same logic as above
                # ECOTEMPLATES
                # ASSETS
                
            return "{\"items\" : %s}" % json.dumps(items)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)    
            
    def wmHTTPGet(self):
        """Simply proxies an HTTP GET to another domain, and returns the results."""
        try:
            url = uiCommon.getAjaxArg("url")
            try:
                result, err = uiCommon.HTTPGet(url, 15)
                if err:
                    return "External HTTP request failed.  %s" % err

            except:
                uiCommon.log("Error during HTTP GET." + traceback.format_exc())
                return traceback.format_exc()
            
            return result
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetRegistry(self):
        """Return the registry editor, complete html block, to the requestor."""
        try:
            sObjectID = uiCommon.getAjaxArg("sObjectID")
            # NOTE: there is only one global registry... id=1
            # rather than spread that all over the script,if the objectid is "global"
            # we'll change it to a 1
            if sObjectID == "global":
                sObjectID = "1"
            
            r = registry.Registry(sObjectID)
            if not r:
                return "Unable to get Registry for object id [%s]" % sObjectID

            return r.DrawRegistryEditor()

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmAddRegistryNode(self):
        try:
            sObjectID = uiCommon.getAjaxArg("sObjectID")
            sXPath = uiCommon.getAjaxArg("sXPath")
            sName = uiCommon.getAjaxArg("sName")

            # fail on missing values
            if not sXPath:
                return "{\"error\" : \"Missing XPath to add to.\"}"

            # fail on empty name
            if not sName:
                return False, "{\"info\" : \"Node Name required.\"}"

            r = registry.Registry(sObjectID)
            if not r:
                return "Unable to get Registry for object id [%s]" % sObjectID

            result, msg = r.AddNode(sXPath, sName)
            if not result:
                return "{\"error\" : \"%s\"}" % msg
                
            
            return "{\"result\" : \"success\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
   
    def wmUpdateRegistryValue(self):
        try:
            sObjectID = uiCommon.getAjaxArg("sObjectID")
            sXPath = uiCommon.getAjaxArg("sXPath")
            sValue = uiCommon.getAjaxArg("sValue")
            sEncrypt = uiCommon.getAjaxArg("sEncrypt")
            
            sValue = uiCommon.unpackJSON(sValue)

            # fail on missing values
            if not sXPath:
                return "{\"error\" : \"Missing XPath to update.\"}"

            r = registry.Registry(sObjectID)
            if not r:
                return "Unable to get Registry for object id [%s]" % sObjectID

            result, msg = r.SetNodeText(sXPath, sValue, sEncrypt)
            if not result:
                return "{\"error\" : \"%s\"}" % msg
                
            
            return "{\"result\" : \"success\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
   
    def wmDeleteRegistryNode(self):
        try:
            sObjectID = uiCommon.getAjaxArg("sObjectID")
            sXPath = uiCommon.getAjaxArg("sXPath")

            # fail on missing values
            if not sXPath:
                return "{\"error\" : \"Missing path to remove.\"}"

            r = registry.Registry(sObjectID)
            if not r:
                return "Unable to get Registry for object id [%s]" % sObjectID

            result, msg = r.DeleteNode(sXPath)
            if not result:
                return "{\"error\" : \"%s\"}" % msg
                
            
            return "{\"result\" : \"success\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
   
    """
    Some Enterprise features require additional script files.  A CE install would show 
    404 errors if we include them on the client files, so we'll get and eval them this way.
    """
    def wmGetScript(self):
        try:
            sScriptName = uiCommon.getAjaxArg("sScriptName")
            if sScriptName:
                sScriptName = "static/script/%s" % sScriptName
                if os.path.exists(sScriptName):
                    with open(sScriptName, 'r') as f:
                        if f:
                            return f.read()
            
            return ""
        except Exception as ex:
            return ex.__str__()
            
