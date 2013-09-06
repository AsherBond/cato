
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

from catolog import catolog
from catoconfig import catoconfig
from catocommon import catocommon
from catouser import catouser
from catocloud import cloud
from catoasset import asset
from catotask import task
from catosettings import settings
from catoerrors import InfoException

from catoui import uiCommon

# these are generic ui web methods, and stuff that's not enough to need it's own file.

class uiMethods:
    db = None
    
    def wmAttemptLogin(self):
        return uiCommon.AttemptLogin("Cato Admin UI")   
                
    def wmGetQuestion(self):
        return uiCommon.GetQuestion()
            
    def wmGetConfig(self):
        return json.dumps(catoconfig.SAFECONFIG)
            
    def wmUpdateHeartbeat(self):
        uiCommon.UpdateHeartbeat()
        return ""
    
    def wmSetApplicationSetting(self):
        category = uiCommon.getAjaxArg("sCategory")
        setting = uiCommon.getAjaxArg("sSetting")
        value = uiCommon.getAjaxArg("sValue")
        settings.settings.set_application_setting(category, setting, value)
            
    def wmLicenseAgree(self):
        settings.settings.set_application_setting("general", "license_status", "agreed")
        settings.settings.set_application_setting("general", "license_datetime", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
        return ""
            
    def wmGetDBInfo(self):
        if catoconfig.CONFIG.has_key("server"):
            return catoconfig.CONFIG["server"]
        else:
            return "Unknown"
            
    def wmGetVersion(self):
        return catoconfig.VERSION
    
    def wmGetGettingStarted(self):
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
            if not sset.Messenger.has_key("SMTPServerAddress") or not sset.Messenger["SMTPServerAddress"]:
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
                        items.append("Provide an Account Login ID and Password for all Cloud Accounts.")
            else: 
                items.append("There are no Cloud Accounts defined.")
            
            if items:
                sHTML += self.DrawGettingStartedItem("cloudaccounts", "Cloud Accounts", items, "<a href=\"/cloudAccountEdit\">Click here</a> to manage Cloud Accounts.")
        
        return sHTML


    def DrawGettingStartedItem(self, sID, sTitle, aItems, sActionLine):
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
            
    def wmGetCloudAccountsForHeader(self):
        sSelected = uiCommon.GetCookie("selected_cloud_account")

        sHTML = ""
        ca = cloud.CloudAccounts("")
        if ca.rows:
            for row in ca.rows:
                # if sSelected is empty, set the default in the cookie.
                sSelectClause = ""
                if not sSelected:
                    if row["IsDefault"] == "Yes":
                        uiCommon.SetCookie("selected_cloud_account", row["ID"])
                else:
                    sSelectClause = ("selected=\"selected\"" if sSelected == row["ID"] else "")
                    
                sHTML += "<option value=\"%s\" provider=\"%s\" %s>%s (%s)</option>" % (row["ID"], row["Provider"], sSelectClause, row["Name"], row["Provider"])

        return sHTML

    def wmGetMenu(self):
        # NOTE: this needs all the kick and warn stuff
        role = uiCommon.GetSessionUserRole()
        
        if not role:
            raise Exception("Unable to get Role for user.")

        filename = ""
        if role == "Administrator":
            filename = "_amenu.html"
        if role == "Developer":
            filename = "_dmenu.html"
        if role == "User":
            filename = "_umenu.html"

        f = open(os.path.join(catoconfig.CONFIG["uicache"], filename))
        if f:
            return f.read()
    
    def wmGetCategories(self):
        f = open(os.path.join(catoconfig.CONFIG["uicache"], "_categories.html"))
        if f:
            return f.read()
    
    def wmGetFunctions(self):
        f = open(os.path.join(catoconfig.CONFIG["uicache"], "_functions.html"))
        if f:
            return f.read()
    
    def wmGetCommandHelp(self):
        f = open(os.path.join(catoconfig.CONFIG["uicache"], "_command_help.html"))
        if f:
            return f.read()
    
    def wmGetSystemStatus(self):
        sProcessHTML = ""
        sSQL = """select app_instance as Instance,
            app_name as Component,
            heartbeat as Heartbeat,
            case master when 1 then 'Yes' else 'No' end as Enabled,
            timestampdiff(MINUTE, heartbeat, now()) as mslr,
            load_value as LoadValue, platform, hostname
            from application_registry
            order by component, master desc"""
        rows = self.db.select_all_dict(sSQL)
        if rows:
            for dr in rows:
                sProcessHTML += """<tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td><span class='ui-icon ui-icon-document forceinline view_component_log' component='%s'></span></td>
                    </tr>""" % (dr.get("Component", ""),
                                dr.get("Instance", ""),
                                dr["LoadValue"] if dr["LoadValue"] is not None else "",
                                dr.get("Heartbeat", ""),
                                dr.get("Enabled", ""),
                                dr.get("mslr", ""),
                                dr.get("Component", ""))

        sUserHTML = ""
        sSQL = """select u.full_name, us.login_dt, us.heartbeat as last_update, us.address,
            case when us.kick = 0 then 'Active' when us.kick = 1 then 'Warning'
            when us.kick = 2 then 'Kicking' when us.kick = 3 then 'Inactive' end as kick
            from user_session us join users u on u.user_id = us.user_id
            where timestampdiff(MINUTE,us.heartbeat, now()) < 10
            order by us.heartbeat desc"""
        rows = self.db.select_all_dict(sSQL)
        if rows:
            for dr in rows:
                sUserHTML += """<tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    </tr>""" % (dr.get("full_name", ""), dr.get("login_dt", ""), dr.get("last_update", ""), dr.get("address", ""), dr.get("kick", ""))
                
        sMessageHTML = ""
        sSQL = """select msg_to, msg_subject,
            case status when 0 then 'Queued' when 1 then 'Error' when 2 then 'Success' end as status,
            error_message,
            convert(date_time_entered, CHAR(20)) as entered_dt, convert(date_time_completed, CHAR(20)) as completed_dt
            from message
            order by msg_id desc limit 100"""
        rows = self.db.select_all_dict(sSQL)
        if rows:
            for dr in rows:
                sMessageHTML += """<tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s<br />%s</td>
                    </tr>""" % (dr.get("msg_to", ""), dr.get("msg_subject", ""), dr.get("status", ""), uiCommon.SafeHTML(dr.get("error_message", "")), dr.get("entered_dt", ""), dr.get("completed_dt", ""))
                
        
        return json.dumps({"processes" : sProcessHTML, "users" : sUserHTML, "messages" : sMessageHTML})

    def wmGetProcessLogfile(self):
        component = uiCommon.getAjaxArg("component")
        logfile = ""
        if component:
            logfile = "%s/%s.log" % (catolog.LOGPATH, component)
            if os.path.exists(logfile):
                with open(logfile, 'r') as f:
                    f.seek (0, 2)  # Seek @ EOF
                    fsize = f.tell()  # Get Size
                    f.seek (max (fsize - 102400, 0), 0)  # Set pos @ last n chars
                    tail = f.readlines()  # Read to end

                    return uiCommon.packJSON("".join(tail))
        
        return uiCommon.packJSON("Unable to read logfile. [%s]" % logfile)
            
    def wmGetLog(self):
        sObjectID = uiCommon.getAjaxArg("sObjectID")
        sObjectType = uiCommon.getAjaxArg("sObjectType")
        sSearch = uiCommon.getAjaxArg("sSearch")
        sRecords = uiCommon.getAjaxArg("sRecords", "100")
        sFrom = uiCommon.getAjaxArg("sFrom", "")
        sTo = uiCommon.getAjaxArg("sTo", "")
        
        logtype = "Security" if not sObjectID and not sObjectType else "Object"
        rows = catocommon.get_security_log(oid=sObjectID, otype=sObjectType, logtype=logtype,
                                           search=sSearch, num_records=sRecords, _from=sFrom, _to=sTo)
        if rows:
            out = []
            for row in rows:
                r = []
                r.append(row["log_dt"])
                r.append(uiCommon.packJSON(row["full_name"]))
                r.append(uiCommon.packJSON(uiCommon.SafeHTML(row["log_msg"])))
                out.append(r)
                
        return json.dumps({"log" : out})

    def wmGetDatabaseTime(self):
        sNow = self.db.select_col("select now()")
        if sNow:
            return str(sNow)
        else:
            return "Unable to get system time."
        
    def wmGetActionPlans(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        try:
            sHTML = ""

            sSQL = """select plan_id, date_format(ap.run_on_dt, '%%m/%%d/%%Y %%H:%%i') as run_on_dt, ap.source, ap.action_id,
                ap.source, ap.schedule_id
                from action_plan ap
                where ap.task_id = %s 
                order by ap.run_on_dt"""
            dt = self.db.select_all_dict(sSQL, (sTaskID))
            if dt:
                for dr in dt:
                    sHTML += '''<div class="ui-widget-content ui-corner-all pointer clearfloat action_plan"
                        id="ap_%s" plan_id="%s" run_on="%s" source="%s"
                        schedule_id="%s">''' % (str(dr["plan_id"]), str(dr["plan_id"]), str(dr["run_on_dt"]), dr["source"], str(dr["schedule_id"]))
                    sHTML += " <div class=\"floatleft action_plan_name\">"

                    # an icon denotes if it's manual or scheduled
                    if dr["source"] == "schedule":
                        sHTML += "<span class=\"floatleft ui-icon ui-icon-calculator\" title=\"Scheduled\"></span>"
                    else:
                        sHTML += "<span class=\"floatleft ui-icon ui-icon-document\" title=\"Run Later\"></span>"

                    sHTML += dr["run_on_dt"]

                    sHTML += " </div>"

                    sHTML += " <div class=\"floatright\">"
                    sHTML += "<span class=\"ui-icon ui-icon-trash action_plan_remove_btn\" title=\"Delete Plan\"></span>"
                    sHTML += " </div>"


                    sHTML += " </div>"

            return sHTML

        except Exception:
            uiCommon.log(traceback.format_exc())

    def wmGetActionSchedules(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sHTML = ""

        sSQL = """select s.schedule_id, s.label, s.descr
            from action_schedule s
            where s.task_id = %s"""
        dt = self.db.select_all_dict(sSQL, (sTaskID))
        if dt:
            for dr in dt:
                sToolTip = ""
                sToolTip += (dr["descr"] if dr["descr"] else "")

                # draw it
                sHTML += " <div class=\"ui-widget-content ui-corner-all pointer clearfloat action_schedule\"" \
                    " id=\"as_" + dr["schedule_id"] + "\">"
                sHTML += " <div class=\"floatleft schedule_name\">"

                sHTML += "<span class=\"floatleft ui-icon ui-icon-calculator schedule_tip\" title=\"" + sToolTip + "\"></span>"

                sHTML += (dr["schedule_id"] if not dr["label"] else dr["label"])

                sHTML += " </div>"

                sHTML += " <div class=\"floatright\">"
                sHTML += "<span class=\"ui-icon ui-icon-trash schedule_remove_btn\" title=\"Delete Schedule\"></span>"
                sHTML += " </div>"


                sHTML += " </div>"

        return sHTML

    def wmGetRecurringPlan(self):
        sScheduleID = uiCommon.getAjaxArg("sScheduleID")
        # tracing this backwards, if the action_plan table has a row marked "schedule" but no schedule_id, problem.
        if not sScheduleID:
            uiCommon.log("Unable to retrieve Reccuring Plan - schedule id argument not provided.")
        
        sched = {}

        # now we know the details, go get the timetable for that specific schedule
        sSQL = """select schedule_id, months, days, hours, minutes, days_or_weeks, label
            from action_schedule
            where schedule_id = %s"""
        dr = self.db.select_row_dict(sSQL, (sScheduleID))
        if dr:
            sDesc = (dr["schedule_id"] if not dr["label"] else dr["label"])

            sched["sDescription"] = sDesc
            sched["sMonths"] = dr["months"]
            sched["sDays"] = dr["days"]
            sched["sHours"] = dr["hours"]
            sched["sMinutes"] = dr["minutes"]
            sched["sDaysOrWeeks"] = str(dr["days_or_weeks"])
        else:
            uiCommon.log("Unable to find details for Recurring Action Plan. " + self.db.error + " ScheduleID [" + sScheduleID + "]")

        return json.dumps(sched)
    
    def wmDeleteSchedule(self):
        sScheduleID = uiCommon.getAjaxArg("sScheduleID")

        if not sScheduleID:
            uiCommon.log("Missing Schedule ID.")
            return "Missing Schedule ID."

        sSQL = "delete from action_plan where schedule_id = %s"
        self.db.exec_db(sSQL, (sScheduleID))

        sSQL = "delete from action_schedule where schedule_id = %s"
        self.db.exec_db(sSQL, (sScheduleID))

        #  if we made it here, so save the logs
        uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.Schedule, "", "", "Schedule [" + sScheduleID + "] deleted.")

        return json.dumps({"result" : "success"})

    def wmDeleteActionPlan(self):
        iPlanID = uiCommon.getAjaxArg("iPlanID")

        if iPlanID < 1:
            uiCommon.log("Missing Action Plan ID.")
            return "Missing Action Plan ID."

        sSQL = "delete from action_plan where plan_id = %s"

        self.db.exec_db(sSQL, (iPlanID))

        #  if we made it here, so save the logs
        uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.Schedule, "", "", "Action Plan [" + iPlanID + "] deleted.")

        return json.dumps({"result" : "success"})
    
    def wmRunLater(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
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

        sSQL = "insert into action_plan (task_id, account_id," \
            " run_on_dt, parameter_xml, debug_level, source)" \
            " values (" \
            " '" + sTaskID + "'," + \
            (" '" + sAccountID + "'" if sAccountID else "''") + "," \
            " str_to_date('" + sRunOn + "', '%%m/%%d/%%Y %%H:%%i')," + \
            (" '" + catocommon.tick_slash(sParameterXML) + "'" if sParameterXML else "null") + "," + \
            (iDebugLevel if iDebugLevel > "-1" else "null") + "," \
            " 'manual'" \
            ")"

        self.db.exec_db(sSQL)

    def wmRunRepeatedly(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        aMonths = uiCommon.getAjaxArg("sMonths")
        aDays = uiCommon.getAjaxArg("sDays")
        aHours = uiCommon.getAjaxArg("sHours")
        aMinutes = uiCommon.getAjaxArg("sMinutes")
        sDaysOrWeeks = uiCommon.getAjaxArg("sDaysOrWeeks")
        sParameterXML = uiCommon.getAjaxArg("sParameterXML")
        iDebugLevel = uiCommon.getAjaxArg("iDebugLevel")
        sAccountID = uiCommon.getAjaxArg("sAccountID")
        
        if not sTaskID or not aMonths or not aDays or not aHours or not aMinutes or not sDaysOrWeeks:
            uiCommon.log("Missing or invalid Schedule timing or Task ID.")

        # we encoded this in javascript before the ajax call.
        # the safest way to unencode it is to use the same javascript lib.
        # (sometimes the javascript and .net libs don't translate exactly, google it.)
        sParameterXML = uiCommon.unpackJSON(sParameterXML)
        
        # we gotta peek into the XML and encrypt any newly keyed values
        sParameterXML = uiCommon.PrepareAndEncryptParameterXML(sParameterXML)                

        # figure out a label and a description
        sLabel, sDesc = catocommon.GenerateScheduleLabel(aMonths, aDays, aHours, aMinutes, sDaysOrWeeks)

        sSQL = "insert into action_schedule (schedule_id, task_id, account_id," \
            " months, days, hours, minutes, days_or_weeks, label, descr, parameter_xml, debug_level)" \
               " values (" \
            " '" + catocommon.new_guid() + "'," \
            " '" + sTaskID + "'," \
            + (" '" + sAccountID + "'" if sAccountID else "''") + "," \
            " '" + ",".join([str(x) for x in aMonths]) + "'," \
            " '" + ",".join([str(x) for x in aDays]) + "'," \
            " '" + ",".join([str(x) for x in aHours]) + "'," \
            " '" + ",".join([str(x) for x in aMinutes]) + "'," \
            " '" + sDaysOrWeeks + "'," \
            + (" '" + sLabel + "'" if sLabel else "null") + "," \
            + (" '" + sDesc + "'" if sDesc else "null") + "," \
            + (" '" + catocommon.tick_slash(sParameterXML) + "'" if sParameterXML else "null") + "," \
            + (iDebugLevel if iDebugLevel > "-1" else "null") + \
            ")"

        self.db.exec_db(sSQL)

    def wmSavePlan(self):
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

        sSQL = """update action_plan
            set parameter_xml = %s,
            debug_level = %s
            where plan_id = %s"""

        self.db.exec_db(sSQL, (sParameterXML, iDebugLevel if iDebugLevel > -1 else None, iPlanID))
        
        return json.dumps({"result" : "success"})

    def wmSaveSchedule(self):
        sScheduleID = uiCommon.getAjaxArg("sScheduleID")
        aMonths = uiCommon.getAjaxArg("sMonths")
        aDays = uiCommon.getAjaxArg("sDays")
        aHours = uiCommon.getAjaxArg("sHours")
        aMinutes = uiCommon.getAjaxArg("sMinutes")
        sDaysOrWeeks = uiCommon.getAjaxArg("sDaysOrWeeks")
        sParameterXML = uiCommon.getAjaxArg("sParameterXML")
        iDebugLevel = uiCommon.getAjaxArg("iDebugLevel")
        """
         * JUST AS A REMINDER:
         * There is no parameter 'merging' happening here.  This is a Scheduled Plan ...
         *   it has ALL the parameters it needs to pass to the CE.
         * 
         * """

        if not sScheduleID or not aMonths or not aDays or not aHours or not aMinutes or not sDaysOrWeeks:
            uiCommon.log("Missing Schedule ID or invalid timetable.")

        # we encoded this in javascript before the ajax call.
        # the safest way to unencode it is to use the same javascript lib.
        # (sometimes the javascript and .net libs don't translate exactly, google it.)
        sParameterXML = uiCommon.unpackJSON(sParameterXML)
        
        # we gotta peek into the XML and encrypt any newly keyed values
        sParameterXML = uiCommon.PrepareAndEncryptParameterXML(sParameterXML)                

        # whack all plans for this schedule, it's been changed
        sSQL = "delete from action_plan where schedule_id = '" + sScheduleID + "'"
        self.db.exec_db(sSQL)


        # figure out a label
        sLabel, sDesc = catocommon.GenerateScheduleLabel(aMonths, aDays, aHours, aMinutes, sDaysOrWeeks)
        
        sSQL = "update action_schedule set" \
            " months = '" + ",".join([str(x) for x in aMonths]) + "'," \
            " days = '" + ",".join([str(x) for x in aDays]) + "'," \
            " hours = '" + ",".join([str(x) for x in aHours]) + "'," \
            " minutes = '" + ",".join([str(x) for x in aMinutes]) + "'," \
            " days_or_weeks = '" + sDaysOrWeeks + "'," \
            " label = " + ("'" + sLabel + "'" if sLabel else "null") + "," \
            " descr = " + ("'" + sDesc + "'" if sDesc else "null") + "," \
            " parameter_xml = " + ("'" + catocommon.tick_slash(sParameterXML) + "'" if sParameterXML else "null") + "," \
            " debug_level = " + (iDebugLevel if iDebugLevel > -1 else "null") + \
            " where schedule_id = '" + sScheduleID + "'"

        self.db.exec_db(sSQL)

    def wmGetSettings(self):
        s = settings.settings()
        return s.AsJSON()

    def wmSaveSettings(self):
        """
            In this method, the values come from the browser in a jQuery serialized array of name/value pairs.
        """
        sModule = uiCommon.getAjaxArg("module")
        sSettings = uiCommon.getAjaxArg("settings")
    
        # sweet, use getattr to actually get the class we want!
        objname = getattr(settings.settings, sModule.lower())
        obj = objname()
        if obj:
            # spin the sValues array and set the appropriate properties.
            # setattr is so awesome
            for pair in sSettings:
                setattr(obj, pair["name"], pair["value"])
                # print  "setting %s to %s" % (pair["name"], pair["value"])
            # of course all of our settings classes must have a DBSave method
            obj.DBSave()
            catocommon.add_security_log(uiCommon.GetSessionUserID(), catocommon.SecurityLogTypes.Security,
                catocommon.SecurityLogActions.ConfigChange, catocommon.CatoObjectTypes.NA, "",
                "%s settings changed." % sModule.capitalize())
        
        return "{}"

    def wmGetMyAccount(self):
        user_id = uiCommon.GetSessionUserID()

        sSQL = """select full_name, username, authentication_type, email, 
            ifnull(security_question, '') as security_question, 
            ifnull(security_answer, '') as security_answer
            from users
            where user_id = '%s'""" % user_id
        dr = self.db.select_row_dict(sSQL)
        # here's the deal - we aren't even returning the 'local' settings if the type is ldap.
        if dr["authentication_type"] == "local":
            return json.dumps(dr)
        else:
            d = {"full_name":dr["full_name"], "username": dr["username"], "email":dr["email"], "type":dr["authentication_type"]}
            return json.dumps(d)

    def wmSaveMyAccount(self):
        """
            In this method, the values come from the browser in a jQuery serialized array of name/value pairs.
        """
        user_id = uiCommon.GetSessionUserID()
        args = uiCommon.getAjaxArg("sValues")

        u = catouser.User()
        u.FromID(user_id)

        if u.ID:
            # if a password was provided...
            # these changes are done BEFORE we manipulate the user properties for update.
            new_pw = uiCommon.unpackJSON(args.get("my_password"))
            if new_pw:
                u.ChangePassword(new_password=new_pw)
                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.User, u.ID, u.FullName, "Password changed.")
                
            # now the other values...
            u.Email = args.get("my_email")
            u.SecurityQuestion = args.get("my_question")
            u.SecurityAnswer = uiCommon.unpackJSON(args.get("my_answer"))

            if u.DBUpdate():
                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.User, u.ID, u.ID, "User updated.")

        return json.dumps({"result" : "success"})

    def wmGetUsersTable(self):
        sHTML = ""
        pager_html = ""
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

        return json.dumps({"pager" : uiCommon.packJSON(pager_html), "rows" : uiCommon.packJSON(sHTML)})    
        
    def wmGetUser(self):
        sID = uiCommon.getAjaxArg("sUserID")
        u = catouser.User()
        u.FromID(sID)
        return u.AsJSON()

    def wmGetAsset(self):
        sID = uiCommon.getAjaxArg("sAssetID")
        a = asset.Asset()
        a.FromID(sID)
        return a.AsJSON()
            
    def wmUpdateUser(self):
        """
            Updates a user.  Will only update the values passed to it.
        """
        user_role = uiCommon.GetSessionUserRole()
        if user_role != "Administrator":
            raise Exception("Only Administrators can edit user accounts.")
         
        args = uiCommon.getAjaxArgs()
        
        u = catouser.User()
        u.FromID(args["ID"])

        if u.ID:
            # these changes are done BEFORE we manipulate the user properties for update.

            new_pw = uiCommon.unpackJSON(args.get("Password"))
            random_pw = args.get("NewRandomPassword")
    
            # if a password was provided, or the random flag was set...exclusively
            if new_pw:
                # if the user requesting the change *IS* the user being changed...
                # set force_change to False
                force = True
                if u.ID == uiCommon.GetSessionUserID():
                    force = False
                    
                u.ChangePassword(new_password=new_pw, force_change=force)
                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.User, u.ID, u.FullName, "Password changed.")
            elif random_pw:
                u.ChangePassword(generate=random_pw)
                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.User, u.ID, u.FullName, "Password reset.")
                
            # now we can change the properties
            u.LoginID = args.get("LoginID")
            u.FullName = args.get("FullName")
            u.Status = args.get("Status")
            u.AuthenticationType = args.get("AuthenticationType")
            u.ForceChange = args.get("ForceChange")
            u.Email = args.get("Email")
            u.Role = args.get("Role")
            u.FailedLoginAttempts = args.get("FailedLoginAttempts")
            u.Expires = args.get("Expires")

            u._Groups = args.get("Groups")

        if u.DBUpdate():
            uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.User, u.ID, u.ID, "User updated.")

        return json.dumps({"result" : "success"})

    def wmCreateUser(self):
        args = uiCommon.getAjaxArgs()

        u = catouser.User.DBCreateNew(username=args["LoginID"],
                                        fullname=args["FullName"],
                                        role=args["Role"],
                                        password=args.get("Password"),
                                        generatepw=args["GeneratePW"],
                                        authtype=args["AuthenticationType"],
                                        forcechange=args.get("ForceChange"),
                                        email=args.get("Email"),
                                        status=args["Status"],
                                        expires=args["Expires"],
                                        groups=args["Groups"])

        uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.User, u.ID, u.FullName, "User Created")
        return u.AsJSON()
        
    def wmDeleteUsers(self):
        WhoAmI = uiCommon.GetSessionUserID()
        sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
        if len(sDeleteArray) < 36:
            return json.dumps({"info" : "Unable to delete - no selection."})

        now = []
        later = []

        aUsers = sDeleteArray.split(",")
        for sUserID in aUsers:
            if len(sUserID) == 36:  # a guid + quotes
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
            sSQL = "delete from api_tokens where user_id in (%s)" % ("'%s'" % ("','".join(now)))
            self.db.tran_exec(sSQL)

            sSQL = "delete from user_password_history where user_id in (%s)" % ("'%s'" % ("','".join(now)))
            self.db.tran_exec(sSQL)

            sSQL = "delete from users where user_id in (%s)" % ("'%s'" % ("','".join(now)))
            self.db.tran_exec(sSQL)

        #  flag the others...
        if later:
            sSQL = "update users set status = 86 where user_id in (%s)" % ("'%s'" % ("','".join(later)))
            self.db.tran_exec(sSQL)

        self.db.tran_commit()

        return json.dumps({"result" : "success"})

    def wmGetAssetsTable(self):
        sHTML = ""
        pager_html = ""
        sFilter = uiCommon.getAjaxArg("sSearch")
        sPage = uiCommon.getAjaxArg("sPage")
        maxrows = 25

        a = asset.Assets(sFilter)
        if a.rows:
            # before we break the results into pages, we first filter it by tag
            # THIS IS DEPENDANT on the results containing a list of tags.
            allowedrows = uiCommon.FilterSetByTag(a.rows)

            start, end, pager_html = uiCommon.GetPager(len(allowedrows), maxrows, sPage)

            for row in allowedrows[start:end]:
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

        return json.dumps({"pager" : uiCommon.packJSON(pager_html), "rows" : uiCommon.packJSON(sHTML)})
        
    def wmAssetSearch(self):
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
            
    def wmGetCredentialsTable(self):
        sHTML = ""
        pager_html = ""
        sFilter = uiCommon.getAjaxArg("sSearch")
        sPage = uiCommon.getAjaxArg("sPage")
        maxrows = 25

        c = asset.Credentials(sFilter)
        if c.rows:
            start, end, pager_html = uiCommon.GetPager(len(c.rows), maxrows, sPage)

            for row in c.rows[start:end]:
                sHTML += """<tr credential_id="{0}">
                    <td class="chkboxcolumn">
                        <input type="checkbox" class="chkbox" id="chk_{0}" tag="chk" />
                    </td>
                    <td class="selectable">{1}</td>
                    <td class="selectable">{2}</td>
                    <td class="selectable">{3}</td>
                </tr>
                """.format(row["ID"], row["Name"], row["Type"], row["Description"])

        return json.dumps({"pager" : uiCommon.packJSON(pager_html), "rows" : uiCommon.packJSON(sHTML)})
        
    def wmGetCredentialsJSON(self):
        sFilter = uiCommon.getAjaxArg("sFilter")

        ac = asset.Credentials(sFilter)
        if ac:
            return ac.AsJSON()
        # should not get here if all is well
        return json.dumps({"result":"fail", "error":"Failed to get Credentials using filter [%s]." % (sFilter)})

    def wmGetCredential(self):
        sID = uiCommon.getAjaxArg("sCredentialID")
        c = asset.Credential()
        c.FromID(sID)
        return c.AsJSON()

    def wmCreateAsset(self):
        args = uiCommon.getAjaxArgs()

        a, sErr = asset.Asset.DBCreateNew(args["Name"], args["Status"], args["DBName"], args["Port"],
          args["Address"], args["ConnString"], args["Tags"], args["CredentialMode"], args["Credential"])
        if sErr:
            return json.dumps({"error" : sErr})
        if a == None:
            return json.dumps({"error" : "Unable to create Asset."})

        uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Asset, a.ID, a.Name, "Asset Created")

        return a.AsJSON()

    def wmUpdateAsset(self):
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
                return json.dumps({"error" : msg})

        return json.dumps({"result" : "success"})
        
    def wmDeleteAssets(self):
        sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
        if len(sDeleteArray) < 36:
            return json.dumps({"info" : "Unable to delete - no selection."})

        # for this one, 'now' will be all the assets that don't have history.
        # and 'later' will get updated to 'inactive' status
        now = []
        later = []
        aAssets = sDeleteArray.split(",")
        for sAsset in aAssets:
            if len(sAsset) == 36:  # a guid + quotes
                # this will mark an asset as Disabled if it has history
                # it returns True if it's safe to delete now
                if asset.Asset.HasHistory(sAsset):
                    later.append(sAsset)
                else:
                    now.append(sAsset)

        # delete some now
        if now:
            sql = """delete from asset_credential
                where shared_or_local = 1
                and credential_id in (select credential_id from asset where asset_id in (%s))
                """ % "'%s'" % "','".join(now)
            self.db.tran_exec(sql)

            sql = "delete from asset where asset_id in (%s)" % "'%s'" % "','".join(now)
            self.db.tran_exec(sql)

        #  deactivate the others...
        if later:
            sql = "update asset set asset_status = 'Inactive' where asset_id in (%s)" % "'%s'" % "','".join(later)
            self.db.tran_exec(sql)

        self.db.tran_commit()

        if later:
            raise InfoException("One or more assets could not be deleted due to historical information.  These Assets have been marked as Inactive.")
        else:
            return json.dumps({"result" : "success"})
                
    def wmCreateCredential(self):
        args = uiCommon.getAjaxArgs()

        # a little different than the others ... credential objects must be instantiated before calling DBCreateNew
        c = asset.Credential()
        c.FromArgs(args["Name"], args["Description"], args["Username"], args["Password"],
                 args["SharedOrLocal"], args["Domain"], args["PrivilegedPassword"], args["PrivateKey"])
        result = c.DBCreateNew()
        if not result:
            json.dumps({"error" : "Unable to create Credential."})

        uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Credential, c.ID, c.Name, "Credential Created")

        return c.AsJSON()
        
    def wmDeleteCredentials(self):
        sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
        if len(sDeleteArray) < 36:
            raise Exception("Unable to delete - no selection.")

        sDeleteArray = uiCommon.QuoteUp(sDeleteArray)
        
        sSQL = """delete from asset_credential where credential_id in (%s)
            and credential_id not in (select distinct credential_id from asset where credential_id is not null)
            """ % sDeleteArray
        self.db.exec_db(sSQL)

        return json.dumps({"result" : "success"})
                
    def wmUpdateCredential(self):
        args = uiCommon.getAjaxArgs()

        c = asset.Credential()
        c.FromID(args["ID"])
        # assuming the attribute names will match ... spin the post data and update the object
        # only where asset attributes are pre-defined.
        for k, v in args.items():
            if hasattr(c, k):
                setattr(c, k, v)

        c.DBUpdate()

        return json.dumps({"result" : "success"})
        
    def wmCreateObjectFromXML(self):
        """Takes a properly formatted XML backup file, and imports each object."""
        inputtext = uiCommon.getAjaxArg("import_text")
        inputtext = uiCommon.unpackJSON(inputtext)
        on_conflict = uiCommon.getAjaxArg("on_conflict")

        # the trick here is to return enough information back to the client
        # to best interact with the user.
        
        # what types of things were in this backup?  what are their new ids?
        items = []

        # parse it as a validation, and to find out what's in it.
        xd = None
        js = None
        try:
            xd = catocommon.ET.fromstring(inputtext)
        except catocommon.ET.ParseError:
            try:
                js = json.loads(inputtext)
            except:
                return json.dumps({"error" : "Data is not properly formatted XML or JSON."})
        
        if xd is not None:
            # so, what's in here?  Tasks?
            
            # TASKS
            for xtask in xd.findall("task"):
                uiCommon.log("Importing Task [%s]" % xtask.get("name", "Unknown"))
                t = task.Task()
                t.FromXML(catocommon.ET.tostring(xtask), on_conflict)

                # NOTE: possible TODO
                # passing a db connection to task.DBSave will allow rollback of a whole 
                # batch of task additions.
                # if it's determined that's necessary here, just create a db connection here 
                # and pass it in
                result, err = t.DBSave()
                if result:
                    # add security log
                    uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Task, t.ID, t.Name, "Created by import.")

                    items.append({"type" : "task", "id" : t.ID, "name" : t.Name}) 
                else:
                    if err:
                        items.append({"type" : "task", "id" : t.ID, "name" : t.Name, "info" : err}) 
                    else:
                        items.append({"type" : "task", "id" : t.ID, "name" : t.Name, "error" : "Unable to create Task. No error available."}) 
        # otherwise it might have been JSON
        elif js is not None:
            # if js isn't a list, bail...
            if not isinstance(js, list):
                js = [js]
                
            for jstask in js:
                uiCommon.log("Importing Task [%s]" % jstask.get("name", "Unknown"))
                t = task.Task()
                t.FromJSON(json.dumps(jstask))

                result, err = t.DBSave()
                if result:
                    # add security log
                    uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Task, t.ID, t.Name, "Created by import.")

                    items.append({"type" : "task", "id" : t.ID, "name" : t.Name}) 
                else:
                    if err:
                        items.append({"type" : "task", "id" : t.ID, "name" : t.Name, "info" : err}) 
                    else:
                        items.append({"type" : "task", "id" : t.ID, "name" : t.Name, "error" : "Unable to create Task. No error available."}) 
        else:
            items.append({"info" : "Unable to create Task from backup JSON/XML."})
            
            # TODO: for loop for Assets will go here, same logic as above
            # ASSETS
            
        return json.dumps({"items" : items})
            
    def wmAnalyzeImportXML(self):
        """Takes a properly formatted XML backup file, and replies with the existence/condition of each Task."""
        inputtext = uiCommon.getAjaxArg("import_text")
        inputtext = uiCommon.unpackJSON(inputtext)

        # the trick here is to return enough information back to the client
        # to best interact with the user.
        
        # what types of things were in this backup?  what are their new ids?
        items = []

        # parse it as a validation, and to find out what's in it.
        xd = None
        js = None
        try:
            xd = catocommon.ET.fromstring(inputtext)
        except catocommon.ET.ParseError as ex:
            uiCommon.log("Data is not valid XML... trying JSON...")
            try:
                js = json.loads(inputtext)
            except Exception as ex:
                uiCommon.log(ex)
                return json.dumps({"error" : "Data is not properly formatted XML or JSON."})
        
        # if the submitted data was XML
        if xd is not None:
            # so, what's in here?  Tasks?
            
            # TASKS
            for xtask in xd.findall("task"):
                t = task.Task()
                t.FromXML(catocommon.ET.tostring(xtask))

                if t.DBExists and t.OnConflict == "cancel":
                    msg = "Task exists - set 'on_conflict' attribute to 'replace', 'minor' or 'major'."
                elif t.OnConflict == "replace":
                    msg = "Will be replaced."
                elif t.OnConflict == "minor" or t.OnConflict == "major":
                    msg = "Will be versioned up."
                else:
                    msg = "Will be created."
                
                items.append({"type" : "task", "id" : t.ID, "name" : t.Name, "info" : msg})  
            
        # otherwise it might have been JSON
        elif js is not None:
            # if js isn't a list, bail...
            if not isinstance(js, list):
                return json.dumps({"error" : "JSON data must be a list of Tasks."})
                
            for jstask in js:
                t = task.Task()
                t.FromJSON(json.dumps(jstask))

                if t.DBExists and t.OnConflict == "cancel":
                    msg = "Task exists - set OnConflict to 'replace', 'minor' or 'major'."
                elif t.OnConflict == "replace":
                    msg = "Will be replaced."
                elif t.OnConflict == "minor" or t.OnConflict == "major":
                    msg = "Will be versioned up."
                else:
                    msg = "Will be created."
                
                items.append({"type" : "task", "id" : t.ID, "name" : t.Name, "info" : msg})  
        else:
            items.append({"info" : "Unable to create Task from backup JSON/XML."})
                
            
        return json.dumps({"items" : items})
        
    def wmHTTPGet(self):
        """Simply proxies an HTTP GET to another domain, and returns the results."""
        url = uiCommon.getAjaxArg("url")
        try:
            result, err = catocommon.http_get(url, 15)
            if err:
                return "External HTTP request failed.  %s" % err

        except:
            uiCommon.log("Error during HTTP GET." + traceback.format_exc())
            return traceback.format_exc()
        
        return result

    """
    Some Enterprise features require additional script files.  A CE install would show 
    404 errors if we include them on the client files, so we'll get and eval them this way.
    """
    def wmGetScript(self):
        sScriptName = uiCommon.getAjaxArg("sScriptName")
        if sScriptName:
            sScriptName = "static/script/%s" % sScriptName
            if os.path.exists(sScriptName):
                with open(sScriptName, 'r') as f:
                    if f:
                        return f.read()
        
        return ""
          
    """
        The Cloud Sidekick reporting tool is a standalone web service.
        Because of cross site scripting rules, we have proxy the http connection here.
    """  
    def wmGetWidget(self):
        return uiCommon.GetWidget()

    def wmGetLayout(self):
        return uiCommon.GetLayout()
        
