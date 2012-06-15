
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
import re
import urllib2
import traceback
import json
import time
import xml.etree.ElementTree as ET
import uiGlobals
import uiCommon
from catocommon import catocommon
import task
import stepTemplates as ST

# task-centric web methods

# the db connection that is used in this module.
db = None

class taskMethods:
    #the GET and POST methods here are hooked by web.py.
    #whatever method is requested, that function is called.
    def GET(self, method):
        try:
            self.db = catocommon.new_conn()
            methodToCall = getattr(self, method)
            result = methodToCall()
            return result
        except Exception as ex:
            raise ex
        finally:
            if self.db.conn.socket:
                self.db.close()

    def POST(self, method):
        try:
            self.db = catocommon.new_conn()
            methodToCall = getattr(self, method)
            result = methodToCall()
            return result
        except Exception as ex:
            raise ex
        finally:
            if self.db.conn.socket:
                self.db.close()

    def wmGetTasksTable(self):
        try:
            sHTML = ""
            sFilter = uiCommon.getAjaxArg("sSearch")
            tasks = task.Tasks(sFilter)
            if tasks.rows:
                for row in tasks.rows:
                    sHTML += "<tr task_id=\"" + row["task_id"] + "\">"
                    sHTML += "<td class=\"chkboxcolumn\">"
                    sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                    " id=\"chk_" + row["original_task_id"] + "\"" \
                    " object_id=\"" + row["task_id"] + "\"" \
                    " tag=\"chk\" />"
                    sHTML += "</td>"
                    
                    sHTML += "<td class=\"selectable\">" + row["task_code"] +  "</td>"
                    sHTML += "<td class=\"selectable\">" + row["task_name"] +  "</td>"
                    sHTML += "<td class=\"selectable\">" + str(row["version"]) +  "</td>"
                    sHTML += "<td class=\"selectable\">" + row["task_desc"] +  "</td>"
                    sHTML += "<td class=\"selectable\">" + row["task_status"] +  "</td>"
                    sHTML += "<td class=\"selectable\">" + str(row["versions"]) +  "</td>"
                    
                    sHTML += "</tr>"
    
            return sHTML    
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetTaskInstances(self):
        try:
            sFilter = uiCommon.getAjaxArg("sSearch")
            sStatus = uiCommon.getAjaxArg("sStatus")
            sRecords = uiCommon.getAjaxArg("sRecords", "200")
            sFrom = uiCommon.getAjaxArg("sFrom", "")
            sTo = uiCommon.getAjaxArg("sTo", "")

            sHTML = ""
            sWhereString = " where (1=1) "

            if sFilter:
                aSearchTerms = sFilter.split(",")
                for term in aSearchTerms:
                    if term:
                        sWhereString += " and (ti.task_instance like '%%" + term + "%%' " \
                            "or ti.task_id like '%%" + term + "%%' " \
                            "or ti.asset_id like '%%" + term + "%%' " \
                            "or ti.pid like '%%" + term + "%%' " \
                            "or ti.task_status like '%%" + term + "%%' " \
                            "or ar.hostname like '%%" + term + "%%' " \
                            "or a.asset_name like '%%" + term + "%%' " \
                            "or t.task_name like '%%" + term + "%%' " \
                            "or t.version like '%%" + term + "%%' " \
                            "or u.username like '%%" + term + "%%' " \
                            "or u.full_name like '%%" + term + "%%' " \
                            "or d.ecosystem_name like '%%" + term + "%%') "
    
            sDateSearchString = ""

            if sFrom:
                sDateSearchString += " and (submitted_dt >= str_to_date('" + sFrom + "', '%%m/%%d/%%Y')" \
                " or started_dt >= str_to_date('" + sFrom + "', '%%m/%%d/%%Y')" \
                " or completed_dt >= str_to_date('" + sFrom + "', '%%m/%%d/%%Y')) "
            if sTo:
                sDateSearchString += " and (submitted_dt <= str_to_date('" + sTo + "', '%%m/%%d/%%Y')" \
                " or started_dt <= str_to_date('" + sTo + "', '%%m/%%d/%%Y')" \
                " or completed_dt <= str_to_date('" + sTo + "', '%%m/%%d/%%Y')) "



            # there may be a list of statuses passed in, if so, build out the where clause for them too
            if sStatus:
                l = []
                # status might be a comma delimited list.  but to prevent sql injection, parse it.
                for s in sStatus.split(","):
                    l.append("'%s'" % s)
                # I love python!
                if l:
                    sWhereString += " and ti.task_status in (%s)" % ",".join(map(str, l)) 
                
            # NOT CURRENTLY CHECKING PERMISSIONS
            sTagString = ""
            """
            if !uiCommon.UserIsInRole("Developer") and !uiCommon.UserIsInRole("Administrator"):
                sTagString+= " join object_tags tt on t.original_task_id = tt.object_id" \
                    " join object_tags ut on ut.tag_name = tt.tag_name" \
                    " and ut.object_type = 1 and tt.object_type = 3" \
                    " and ut.object_id = '" + uiCommon.GetSessionUserID() + "'"
            """
            
            sSQL = "select ti.task_instance, t.task_id, t.task_code, a.asset_name," \
                    " ti.pid as process_id, ti.task_status, t.task_name," \
                    " ifnull(u.full_name, '') as started_by," \
                    " t.version, u.full_name, ar.hostname as ce_name, ar.platform as ce_type," \
                    " d.ecosystem_name, d.ecosystem_id," \
                    " convert(ti.submitted_dt, CHAR(20)) as submitted_dt," \
                    " convert(ti.started_dt, CHAR(20)) as started_dt," \
                    " convert(ti.completed_dt, CHAR(20)) as completed_dt" \
                    " from tv_task_instance ti" \
                    " left join task t on t.task_id = ti.task_id" + \
                    sTagString + \
                    " left outer join application_registry ar on ti.ce_node = ar.id" \
                    " left outer join ecosystem d on ti.ecosystem_id = d.ecosystem_id" \
                    " left join users u on u.user_id = ti.submitted_by" \
                    " left join asset a on a.asset_id = ti.asset_id" + \
                    sWhereString + sDateSearchString + \
                    " order by ti.task_instance desc" \
                    " limit " + sRecords

            rows = self.db.select_all_dict(sSQL)
    
            if rows:
                for row in rows:
                    task_label = "%s (%s)" % (row["task_name"], str(row["version"]))
                    sHTML += "<tr style=\"font-size: .8em;\" task_instance=\"%s\">" % row["task_instance"]
                    
                    sHTML += "<td class=\"selectable\">%s</td>" % row["task_instance"]
                    sHTML += "<td class=\"selectable\">%s</td>" % row["task_code"]
                    sHTML += "<td class=\"selectable\">%s</td>" % task_label
                    sHTML += "<td class=\"selectable\">%s</td>" % row["asset_name"]
                    sHTML += "<td class=\"selectable\">%s</td>" % row["task_status"]
                    sHTML += "<td class=\"selectable\">%s</td>" % row["started_by"]
                    sHTML += "<td class=\"selectable\">%s</td>" % row["ce_name"]
                    sHTML += "<td class=\"selectable\">%s</td>" % str(row["process_id"])
                    sHTML += "<td class=\"selectable\">%s</td>" % row["ecosystem_name"]
                    sHTML += "<td class=\"selectable\">%s<br />%s<br />%s</td>" % (row["submitted_dt"], row["started_dt"], row["completed_dt"])
                    sHTML += "<td class=\"selectable\"><span onclick=\"location.href='taskEdit?task_id=%s'\" class=\"ui-icon ui-icon-pencil pointer\"></span></td>" % row["task_id"]
                    
                    sHTML += "</tr>"
    
            return sHTML    
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetTask(self):
        try:
            sID = uiCommon.getAjaxArg("sTaskID")
            
            t = task.Task()
            sErr = t.FromID(sID)
            if sErr:
                uiCommon.log(sErr, 2)
            if t:
                if t.ID:
                    return t.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get Task details for Task ID [" + sID + "].\"}"
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetTaskCodeFromID(self):
        sOriginalTaskID = uiCommon.getAjaxArg("sOriginalTaskID")

        if not uiCommon.IsGUID(sOriginalTaskID.replace("'", "")):
            uiCommon.log("Invalid or missing Task ID.")

        try:
            sSQL = "select task_code from task where original_task_id = '" + sOriginalTaskID + "' and default_version = 1"
            sTaskCode = self.db.select_col_noexcep(sSQL)
            if not sTaskCode:
                if self.db.error:
                    uiCommon.log("Unable to get task code." + self.db.error)
                else:
                    return ""
            else:
                return "{\"code\" : \"%s\"}" % (sTaskCode)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)


    def wmGetTaskVersionsDropdown(self):
        try:
            sOriginalTaskID = uiCommon.getAjaxArg("sOriginalTaskID")
            sbString = []
            sSQL = "select task_id, version, default_version" \
                " from task " \
                " where original_task_id = '" + sOriginalTaskID + "'" \
                " order by default_version desc, version"
            dt = self.db.select_all_dict(sSQL)
            if not dt:
                uiCommon.log("Error selecting versions: " + self.db.error)
            else:
                for dr in dt:
                    sLabel = str(dr["version"]) + (" (default)" if dr["default_version"] == 1 else "")
                    sbString.append("<option value=\"" + dr["task_id"] + "\">" + sLabel + "</option>")

                return "".join(sbString)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
    
    def wmGetTaskVersions(self):
        try:
            sTaskID = uiCommon.getAjaxArg("sTaskID")
            sHTML = ""

            sSQL = "select task_id, version, default_version," \
                " case default_version when 1 then ' (default)' else '' end as is_default," \
                " case task_status when 'Approved' then 'locked' else 'unlocked' end as status_icon," \
                " created_dt" \
                " from task" \
                " where original_task_id = " \
                " (select original_task_id from task where task_id = '" + sTaskID + "')" \
                " order by version"

            dt = self.db.select_all_dict(sSQL)
            if self.db.error:
                sHTML = "Error selecting versions: " + self.db.error
                uiCommon.log_nouser(self.db.error, 0)
            else:
                if dt:
                    for dr in dt:
                        sHTML += "<li class=\"ui-widget-content ui-corner-all version code\" id=\"v_" + dr["task_id"] + "\""
                        sHTML += "task_id=\"" + dr["task_id"] + "\">"
                        sHTML += "<span class=\"ui-icon ui-icon-" + dr["status_icon"] + " forceinline\"></span>"
                        sHTML += str(dr["version"]) + "&nbsp;&nbsp;" + str(dr["created_dt"]) + dr["is_default"]
                        sHTML += "</li>"

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetCommands(self):
        try:
            sCatHTML = ""
            sFunHTML = ""

            # so, we will use the FunctionCategories class in the session that was loaded at login, and build the list items for the commands tab.
            cats = uiCommon.GetTaskFunctionCategories()
            if not cats:
                return "{\"error\" : \"Error: Task Function Categories class is not in the datacache.\"}"
            else:
                for cat in cats:
                    sCatHTML += "<li class=\"ui-widget-content ui-corner-all command_item category\""
                    sCatHTML += " id=\"cat_" + cat.Name + "\""
                    sCatHTML += " name=\"" + cat.Name + "\">"
                    sCatHTML += "<div>"
                    sCatHTML += "<img class=\"category_icon\" src=\"" + cat.Icon + "\" alt=\"\" />"
                    sCatHTML += "<span>" + cat.Label + "</span>"
                    sCatHTML += "</div>"
                    sCatHTML += "<div id=\"help_text_" + cat.Name + "\" class=\"hidden\">"
                    sCatHTML += cat.Description
                    sCatHTML += "</div>"
                    sCatHTML += "</li>"
                    
                    sFunHTML += "<div class=\"functions hidden\" id=\"cat_" + cat.Name + "_functions\">"
                    # now, let's work out the functions.
                    # we can just draw them all... they are hidden and will display on the client as clicked
                    for fn in cat.Functions:
                        sFunHTML += "<div class=\"ui-widget-content ui-corner-all command_item function\""
                        sFunHTML += " id=\"fn_" + fn.Name + "\""
                        sFunHTML += " name=\"" + fn.Name + "\">"
                        sFunHTML += "<img class=\"function_icon\" src=\"" + fn.Icon + "\" alt=\"\" />"
                        sFunHTML += "<span>" + fn.Label + "</span>"
                        sFunHTML += "<div id=\"help_text_" + fn.Name + "\" class=\"hidden\">"
                        sFunHTML += fn.Description
                        sFunHTML += "</div>"
                        sFunHTML += "</div>"

                    sFunHTML += "</div>"

            return "{\"categories\" : \"%s\", \"functions\" : \"%s\"}" % (uiCommon.packJSON(sCatHTML), uiCommon.packJSON(sFunHTML))
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmCreateTask(self):
        try:
            sTaskName = uiCommon.unpackJSON(uiCommon.getAjaxArg("sTaskName"))
            sTaskCode = uiCommon.unpackJSON(uiCommon.getAjaxArg("sTaskCode"))
            sTaskDesc = uiCommon.unpackJSON(uiCommon.getAjaxArg("sTaskDesc"))
    
            t = task.Task()
            t.FromArgs(sTaskName, sTaskCode, sTaskDesc)

            if not t.Name:
                return "{\"error\" : \"Unable to create Task.\"}"
            
            bSuccess, sErr = t.DBSave()
            if not bSuccess:
                if sErr:
                    return "{\"info\" : \"" + sErr + "\"}"
                else:
                    return "{\"error\" : \"Unable to save Task.\"}"
            
                # add security log
                uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.Task, t.ID, t.Name, "");

            return "{\"id\" : \"%s\"}" % (t.ID)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmCopyTask(self):
        try:
            sCopyTaskID = uiCommon.getAjaxArg("sCopyTaskID")
            sTaskName = uiCommon.getAjaxArg("sTaskName")
            sTaskCode =uiCommon.getAjaxArg("sTaskCode")

            t = task.Task()
            sErr = t.FromID(sCopyTaskID)
            if not t:
                return "{\"error\" : \"Unable to build Task object from ID [" + sCopyTaskID + "]. %s\"}" % sErr
            
            sNewTaskID = t.Copy(0, sTaskName, sTaskCode)
            if not sNewTaskID:
                return "Unable to create Task."
            
            uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.Task, t.ID, t.Name, "Copied from " + sCopyTaskID);
            return "{\"id\" : \"%s\"}" % (sNewTaskID)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmDeleteTasks(self):
        try:
            sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
            if len(sDeleteArray) < 36:
                return "{\"info\" : \"Unable to delete - no selection.\"}"
    
            sDeleteArray = uiCommon.QuoteUp(sDeleteArray)

            if not sDeleteArray:
                return "{\"info\" : \"Unable to delete - no selection.\"}"
                
            # first we need a list of tasks that will not be deleted
            sSQL = """select task_name from task t
                    where t.original_task_id in (%s)
                    and (t.task_id in (select ti.task_id from tv_task_instance ti where ti.task_id = t.task_id)
                    or t.original_task_id in (select original_task_id from ecotemplate_action))""" % sDeleteArray 
            sTaskNames = self.db.select_csv(sSQL, True)

            # list of tasks that will be deleted
            # we have an array of 'original_task_id' - we need an array of task_id
            sSQL = "select t.task_id from task t " \
                " where t.original_task_id in (" + sDeleteArray + ")" \
                " and t.task_id not in (select ti.task_id from tv_task_instance ti where ti.task_id = t.task_id)"
            sTaskIDs = self.db.select_csv(sSQL, True)
            if len(sTaskIDs) > 1:
                sSQL = "delete from task_step_user_settings" \
                    " where step_id in" \
                    " (select step_id from task_step where task_id in (" + sTaskIDs + "))"
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log(self.db)
    
                sSQL = "delete from task_step where task_id in (" + sTaskIDs + ")"
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log_nouser(self.db.error, 0)
    
                sSQL = "delete from task_codeblock where task_id in (" + sTaskIDs + ")"
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log(self.db)
    
                sSQL = "delete from task where task_id in (" + sTaskIDs + ")"
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log(self.db)
    
                self.db.tran_commit()
    
                uiCommon.WriteObjectDeleteLog(uiGlobals.CatoObjectTypes.Task, "Multiple", "Original Task IDs", sDeleteArray)
            
            if len(sTaskNames) > 0:
                return "{\"info\" : \"Task(s) (" + sTaskNames + ") have history rows or are referenced by Ecotemplate Actions and could not be deleted.\"}"
            
            return "{\"result\" : \"success\"}"
            
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmUpdateTaskDetail(self):
        try:
            sTaskID = uiCommon.getAjaxArg("sTaskID")
            sColumn = uiCommon.getAjaxArg("sColumn")
            sValue = uiCommon.getAjaxArg("sValue")
            sUserID = uiCommon.GetSessionUserID()

            if uiCommon.IsGUID(sTaskID) and uiCommon.IsGUID(sUserID):
                # we encoded this in javascript before the ajax call.
                # the safest way to unencode it is to use the same javascript lib.
                # (sometimes the javascript and .net libs don't translate exactly, google it.)
                sValue = uiCommon.unpackJSON(sValue)
                sValue = catocommon.tick_slash(sValue)

                sSQL = "select original_task_id from task where task_id = '" + sTaskID + "'"
                sOriginalTaskID = self.db.select_col_noexcep(sSQL)

                if not sOriginalTaskID:
                    uiCommon.log("ERROR: Unable to get original_task_id for [" + sTaskID + "]." + self.db.error)
                    return "{\"error\" : \"Unable to get original_task_id for [" + sTaskID + "].\"}"


                # what's the "set clause"?
                sSetClause = sColumn + "='" + sValue + "'"

                #  bugzilla 1074, check for existing task_code and task_name
                if sColumn == "task_code" or sColumn == "task_name":
                    sSQL = "select task_id from task where " + \
                        sColumn + "='" + sValue + "'" \
                        " and original_task_id <> '" + sOriginalTaskID + "'"

                    sValueExists = self.db.select_col_noexcep(sSQL)
                    if self.db.error:
                        uiCommon.log("ERROR: Unable to check for existing names [" + sTaskID + "]." + self.db.error)

                    if sValueExists:
                        return "{\"info\" : \"" + sValue + " exists, please choose another value.\"}"
                
                    # changing the name or code updates ALL VERSIONS
                    sSQL = "update task set " + sSetClause + " where original_task_id = '" + sOriginalTaskID + "'"
                else:
                    # some columns on this table allow nulls... in their case an empty sValue is a null
                    if sColumn == "concurrent_instances" or sColumn == "queue_depth":
                        if len(sValue.replace(" ", "")) == 0:
                            sSetClause = sColumn + " = null"
                    
                    # some columns are checkboxes, so make sure it is a db appropriate value (1 or 0)
                    if sColumn == "concurrent_by_asset":
                        if catocommon.is_true(sValue):
                            sSetClause = sColumn + " = 1"
                        else:
                            sSetClause = sColumn + " = 0"
                    
                    sSQL = "update task set " + sSetClause + " where task_id = '" + sTaskID + "'"
                

                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to update task [" + sTaskID + "]." + self.db.error)

                uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, sTaskID, sColumn, sValue)

            else:
                uiCommon.log("Unable to update task. Missing or invalid task [" + sTaskID + "] id.")

            return "{\"result\" : \"success\"}"
            
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)           

    def wmCreateNewTaskVersion(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sMinorMajor = uiCommon.getAjaxArg("sMinorMajor")
        try:
            oTask = task.Task()
            sErr = oTask.FromID(sTaskID, True)
            if oTask is None:
                uiCommon.log("Unable to continue.  Unable to build Task object" + sErr)
            
            sNewTaskID = oTask.Copy((1 if sMinorMajor == "Major" else 2), "", "")
            if not sNewTaskID:
                return "Unable to create new Version." + self.db.error

            return sNewTaskID
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return "Unable to create new version.  See server log for details."

    def wmGetCodeblocks(self):
        try:
            sTaskID = uiCommon.getAjaxArg("sTaskID")
            if len(sTaskID) < 36:
                return "Unable to get Codeblocks - invalid Task ID."
            sErr = ""
            #instantiate the new Task object
            oTask = task.Task()
            sErr = oTask.FromID(sTaskID, False)
            if sErr:
                uiCommon.log(sErr, 2)
            if not oTask:
                return "wmGetCodeblocks: Unable to get Task for ID [" + sTaskID + "]. " + sErr
            sCBHTML = ""
            for cb in oTask.Codeblocks.itervalues():
                #if it's a guid it's a bogus codeblock (for export only)
                if uiCommon.IsGUID(cb.Name):
                    continue
                sCBHTML += "<li class=\"ui-widget-content codeblock\" id=\"cb_" + cb.Name + "\">"
                sCBHTML += "<div>"
                sCBHTML += "<div class=\"codeblock_title\" name=\"" + cb.Name + "\">"
                sCBHTML += "<span>" + cb.Name + "</span>"
                sCBHTML += "</div>"
                sCBHTML += "<div class=\"codeblock_icons pointer\">"
                sCBHTML += "<span id=\"codeblock_rename_btn_" + cb.Name + "\" class=\"ui-icon ui-icon-pencil forceinline codeblock_rename\" codeblock_name=\"" + cb.Name + "\">"
                sCBHTML += "</span>"
                sCBHTML += "<span class=\"ui-icon ui-icon-copy forceinline codeblock_copy_btn\" codeblock_name=\"" + cb.Name + "\">"
                sCBHTML += "</span>"
                sCBHTML += "<span id=\"codeblock_delete_btn_" + cb.Name + "\""
                sCBHTML += " class=\"ui-icon ui-icon-close forceinline codeblock_delete_btn codeblock_icon_delete\" remove_id=\"" + cb.Name + "\">"
                sCBHTML += "</span>"
                sCBHTML += "</div>"
                sCBHTML += "</div>"
                sCBHTML += "</li>"
            return sCBHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmAddCodeblock(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sNewCodeblockName = uiCommon.getAjaxArg("sNewCodeblockName")

        try:
            if sNewCodeblockName:
                sSQL = "insert into task_codeblock (task_id, codeblock_name)" \
                       " values (" + "'" + sTaskID + "'," \
                       "'" + sNewCodeblockName + "'" \
                       ")"

                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to add Codeblock [" + sNewCodeblockName + "]. " + self.db.error)

                uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, sTaskID, sNewCodeblockName, "Added Codeblock.")
            else:
                uiCommon.log("Unable to add Codeblock. Invalid or missing Codeblock Name.")
        except Exception:
            uiCommon.log("Unable to add Codeblock. " + traceback.format_exc())
        finally:
            return ""
        
    def wmDeleteCodeblock(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sCodeblockID = uiCommon.getAjaxArg("sCodeblockID")
        try:
            sSQL = "delete u from task_step_user_settings u" \
                " join task_step ts on u.step_id = ts.step_id" \
                " where ts.task_id = '" + sTaskID + "'" \
                " and ts.codeblock_name = '" + sCodeblockID + "'"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log("Unable to delete Steps user settings for Steps in Codeblock." + self.db.error)

            sSQL = "delete from task_step" \
                " where task_id = '" + sTaskID + "'" \
                " and codeblock_name = '" + sCodeblockID + "'"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log("Unable to delete Steps from Codeblock." + self.db.error)

            sSQL = "delete from task_codeblock" \
                " where task_id = '" + sTaskID + "'" \
                " and codeblock_name = '" + sCodeblockID + "'"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log("Unable to delete Codeblock." + self.db.error)

            self.db.tran_commit()

            uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, sTaskID, sCodeblockID, "Deleted Codeblock.")

        except Exception:
            uiCommon.log("Exception: " + traceback.format_exc())
        finally:
            return ""

    def wmRenameCodeblock(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sOldCodeblockName = uiCommon.getAjaxArg("sOldCodeblockName")
        sNewCodeblockName = uiCommon.getAjaxArg("sNewCodeblockName")
        try:
            if uiCommon.IsGUID(sTaskID):
                #  first make sure we are not try:ing to rename it something that already exists.
                sSQL = "select count(*) from task_codeblock where task_id = '" + sTaskID + "'" \
                    " and codeblock_name = '" + sNewCodeblockName + "'"
                iCount = self.db.select_col_noexcep(sSQL)
                if self.db.error:
                    uiCommon.log("Unable to check codeblock names for task." + self.db.error)
                if iCount != 0:
                    return ("Codeblock Name already in use, choose another.")

                #  do it

                # update the codeblock table
                sSQL = "update task_codeblock set codeblock_name = '" + sNewCodeblockName + \
                    "' where codeblock_name = '" + sOldCodeblockName + \
                    "' and task_id = '" + sTaskID + "'"
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log_nouser(self.db.error, 0)

                # and any steps in that codeblock
                sSQL = "update task_step set codeblock_name = '" + sNewCodeblockName + \
                    "' where codeblock_name = '" + sOldCodeblockName + \
                    "' and task_id = '" + sTaskID + "'"
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log_nouser(self.db.error, 0)

                # the fun part... rename it where it exists in any steps
                # but this must be in a loop of only the steps where that codeblock reference exists.
                sSQL = "select step_id from task_step" \
                    " where task_id = '" + sTaskID + "'" \
                    " and ExtractValue(function_xml, '//codeblock[1]') = '" + sOldCodeblockName + "'"
                dtSteps = self.db.select_all_dict(sSQL)
                if self.db.error:
                    uiCommon.log("Unable to get steps referencing the Codeblock." + self.db.error)

                if dtSteps:
                    for dr in dtSteps:
                        uiCommon.SetNodeValueinXMLColumn("task_step", "function_xml", "step_id = '" + dr["step_id"] + "'", "codeblock[.='" + sOldCodeblockName + "']", sNewCodeblockName)

                # all done
                self.db.tran_commit()
                
                uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, sTaskID, sOldCodeblockName, "Renamed Codeblock [%s -> %s]" % (sOldCodeblockName, sNewCodeblockName))

            else:
                uiCommon.log("Unable to get codeblocks for task. Missing or invalid task_id.")
                return "Unable to get codeblocks for task. Missing or invalid task_id."
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
        finally:
            return ""

    def wmCopyCodeblockStepsToClipboard(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sCodeblockName = uiCommon.getAjaxArg("sCodeblockName")

        try:
            if sCodeblockName != "":
                sSQL = "select step_id" \
                    " from task_step" \
                    " where task_id = '" + sTaskID + "'" \
                    " and codeblock_name = '" + sCodeblockName + "'" \
                    " order by step_order desc"

                dt = self.db.select_all_dict(sSQL)
                if self.db.error:
                    uiCommon.log_nouser(self.db.error, 0)

                if dt:
                    for dr in dt:
                        self.CopyStepToClipboard(dr["step_id"])

                return ""
            else:
                uiCommon.log("Unable to copy Codeblock. Missing or invalid codeblock_name.")

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
        
    def wmGetSteps(self):
        try:
            sTaskID = uiCommon.getAjaxArg("sTaskID")
            sCodeblockName = uiCommon.getAjaxArg("sCodeblockName")
            if len(sTaskID) < 36:
                return "Unable to get Steps - invalid Task ID."
            if not sCodeblockName:
                return "Unable to get Steps - No Codeblock specified."

            sAddHelpMsg =  "No Commands have been defined in this Codeblock. Drag a Command here to add it."
            sErr = ""
            #instantiate the new Task object
            oTask = task.Task()
            sErr = oTask.FromID(sTaskID, True)
            if sErr:
                uiCommon.log(sErr, 2)
            if not oTask:
                return "wmGetSteps: Unable to get Task for ID [" + sTaskID + "]. " + sErr

            sHTML = ""

            cb = oTask.Codeblocks[sCodeblockName]
            if cb.Steps:
                # we always need the no_step item to be there, we just hide it if we have other items
                # it will get unhidden if someone deletes the last step.
                sHTML = "<li id=\"no_step\" class=\"ui-widget-content ui-corner-all ui-state-active ui-droppable no_step hidden\">" + sAddHelpMsg + "</li>"
        
                for order in sorted(cb.Steps.iterkeys()):
                    sHTML += ST.DrawFullStep(cb.Steps[order])
            else:
                sHTML = "<li id=\"no_step\" class=\"ui-widget-content ui-corner-all ui-state-active ui-droppable no_step\">" + sAddHelpMsg + "</li>"
                    
            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
        
    def wmGetStep(self):
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            sStepHTML = ""
            if not uiCommon.IsGUID(sStepID):
                uiCommon.log("Unable to get step. Invalid or missing Step ID. [" + sStepID + "].")

            sUserID = uiCommon.GetSessionUserID()

            oStep = ST.GetSingleStep(sStepID, sUserID)
            if oStep is not None:
                sStepHTML += ST.DrawFullStep(oStep)
            else:
                sStepHTML += "<span class=\"red_text\">ERROR: No data found.<br />This command should be deleted and recreated.<br /><br />ID [" + sStepID + "].</span>"

            # return the html
            return sStepHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmAddStep(self):
        try:
            sTaskID = uiCommon.getAjaxArg("sTaskID")
            sCodeblockName = uiCommon.getAjaxArg("sCodeblockName")
            sItem = uiCommon.getAjaxArg("sItem")
            sUserID = uiCommon.GetSessionUserID()

            sStepHTML = ""
            sSQL = ""
            sNewStepID = ""
            
            # in some cases, we'll have some special values to go ahead and set in the function_xml
            # when it's added
            # it's content will be xpath, value
            dValues = {}

            if not uiCommon.IsGUID(sTaskID):
                uiCommon.log("Unable to add step. Invalid or missing Task ID. [" + sTaskID + "]")


            # now, the sItem variable may have a function name (if it's a new command)
            # or it may have a guid (if it's from the clipboard)

            # so, if it's a guid after stripping off the prefix, it's from the clipboard

            # the function has a fn_ or clip_ prefix on it from the HTML.  Strip it off.
            # FIX... test the string to see if it BEGINS with fn_ or clip_
            # IF SO... cut off the beginning... NOT a replace operation.
            if sItem[:3] == "fn_": sItem = sItem[3:]
            if sItem[:5] == "clip_": sItem = sItem[5:]

            # could also beging with cb_, which means a codeblock was dragged and dropped.
            # this special case will result in a codeblock command.
            if sItem[:3] == "cb_":
                # so, the sItem becomes "codeblock"
                sCBName = sItem[3:]
                dValues["codeblock"] = sCBName
                sItem = "codeblock"

            # NOTE: !! yes we are adding the step with an order of -1
            # the update event on the client does not know the index at which it was dropped.
            # so, we have to insert it first to get the HTML... but the very next step
            # will serialize and update the entire sortable... 
            # immediately replacing this -1 with the correct position

            sNewStepID = catocommon.new_guid()

            if uiCommon.IsGUID(sItem):
                # copy from the clipboard
                sSQL = "insert into task_step (step_id, task_id, codeblock_name, step_order, step_desc," \
                    " commented, locked," \
                    " function_name, function_xml)" \
                    " select '" + sNewStepID + "', '" + sTaskID + "'," \
                    " case when codeblock_name is null then '" + sCodeblockName + "' else codeblock_name end," \
                    "-1,step_desc," \
                    "0,0," \
                    "function_name,function_xml" \
                    " from task_step_clipboard" \
                    " where user_id = '" + sUserID + "'" \
                    " and step_id = '" + sItem + "'"

                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to add step." + self.db.error)

                uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, sTaskID, sItem,
                    "Added Command from Clipboard to Codeblock:" + sCodeblockName)

            else:
                # THE NEW CLASS CENTRIC WAY
                # 1) Get a Function object for the sItem (function_name)
                # 2) use those values to construct an insert statement
                
                func = uiCommon.GetTaskFunction(sItem)
                if not func:
                    uiCommon.log("Unable to add step.  Can't find a Function definition for [" + sItem + "]")
                
                # NOTE: !! yes we are doing some command specific logic here.
                # Certain commands have different 'default' values for delimiters, etc.
                # sOPM: 0=none, 1=delimited, 2=parsed
                sOPM = "0"

                # gotta do a few things to the templatexml
                xe = ET.fromstring(func.TemplateXML)
                if xe is not None:
                    # get the OPM
                    sOPM = xe.get("parse_method", "0")
                    # it's possible that variables=true and parse_method=0..
                    # (don't know why you'd do that on purpose, but whatever.)
                    # but if there's NO parse method attribute, and yet there is a 'variables=true' attribute
                    # well, we can't let the absence of a parse_method negate it,
                    # so the default is "2".
                    sPopVars = xe.get("variables", "false")

                    if catocommon.is_true(sPopVars) and sOPM == "0":
                        sOPM = "2"
                    
                    
                    # there may be some provided values ... so alter the func.TemplateXML accordingly
                    for sXPath, sValue in dValues.iteritems():
                        xNode = xe.find(sXPath)
                        if xNode is not None:
                            xNode.text = sValue
                
                    sSQL = "insert into task_step (step_id, task_id, codeblock_name, step_order," \
                        " commented, locked," \
                        " function_name, function_xml)" \
                        " values (" \
                        "'" + sNewStepID + "'," \
                        "'" + sTaskID + "'," + \
                        ("'" + sCodeblockName + "'" if sCodeblockName else "null") + "," \
                        "-1," \
                        "0,0," \
                        "'" + func.Name + "'," \
                        "'" + catocommon.tick_slash(ET.tostring(xe)) + "'" \
                        ")"
                    if not self.db.exec_db_noexcep(sSQL):
                        uiCommon.log("Unable to add step." + self.db.error)
    
                    uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, sTaskID, sItem,
                        "Added Command Type:" + sItem + " to Codeblock:" + sCodeblockName)
                else:
                    uiCommon.log("Unable to add step.  No template xml.")
            if sNewStepID:
                # now... get the newly inserted step and draw it's HTML
                oNewStep = task.Step.FromIDWithSettings(sNewStepID, sUserID)
                if oNewStep:
                    sStepHTML += ST.DrawFullStep(oNewStep)
                else:
                    sStepHTML += "<span class=\"red_text\">Error: Unable to draw Step.</span>"

                # return the html
                return "{\"step_id\":\"" + sNewStepID + "\",\"step_html\":\"" + uiCommon.packJSON(sStepHTML) + "\"}"
            else:
                uiCommon.log("Unable to add step.  No new step_id.")
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmAddEmbeddedCommandToStep(self):
        try:
            sTaskID = uiCommon.getAjaxArg("sTaskID")
            sStepID = uiCommon.getAjaxArg("sStepID")
            sDropXPath = uiCommon.getAjaxArg("sDropXPath")
            sItem = uiCommon.getAjaxArg("sItem")
            sUserID = uiCommon.GetSessionUserID()

            sStepHTML = ""
            
            if not uiCommon.IsGUID(sTaskID):
                uiCommon.log("Unable to add step. Invalid or missing Task ID. [" + sTaskID + "]")
                return "Unable to add step. Invalid or missing Task ID. [" + sTaskID + "]"

            # in some cases, we'll have some special values to go ahead and set in the function_xml
            # when it's added
            # it's content will be xpath, value
            dValues = {}
            
            xe = None
            func = None

            # now, the sItem variable may have a function name (if it's a new command)
            # or it may have a guid (if it's from the clipboard)

            # so, if it's a guid after stripping off the prefix, it's from the clipboard

            # the function has a fn_ or clip_ prefix on it from the HTML.  Strip it off.
            # FIX... test the string to see if it BEGINS with fn_ or clip_
            # IF SO... cut off the beginning... NOT a replace operation.
            if sItem[:3] == "fn_": sItem = sItem[3:]
            if sItem[:5] == "clip_": sItem = sItem[5:]

            # could also beging with cb_, which means a codeblock was dragged and dropped.
            # this special case will result in a codeblock command.
            if sItem[:3] == "cb_":
                # so, the sItem becomes "codeblock"
                sCBName = sItem[3:]
                dValues["codeblock"] = sCBName
                sItem = "codeblock"

            if uiCommon.IsGUID(sItem):
                # a clipboard sItem is a guid id on the task_step_clipboard table
                
                # 1) get the function_xml from the clipboard table (sItem = step_id)
                # 2) Get a Function object for the function name
                # 3) update the parent step with the function objects xml
                
                # get the command from the clipboard, and then update the XML of the parent step
                sSQL = "select function_xml from task_step_clipboard where user_id = '" + sUserID + "' and step_id = '" + sItem + "'"

                sXML = self.db.select_col_noexcep(sSQL)
                if self.db.error:
                    uiCommon.log("Unable to add step." + self.db.error)

                if sXML:
                    # we'll need this below to return the html
                    xe = ET.fromstring(sXML)
                    if xe is None:
                        uiCommon.log("Unable to add clipboard command. Function_xml could not be parsed.")
                        return "An error has occured.  Your command could not be added."

                    sFunctionName = xe.get("name", "")
                    func = uiCommon.GetTaskFunction(sFunctionName)
                    if not func:
                        uiCommon.log("Unable to add clipboard command to step.  Can't find a Function definition for clip [" + sItem + "]")

                    ST.AddToCommandXML(sStepID, sDropXPath, ET.tostring(xe))

                    uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, sTaskID, sItem,
                        "Added Command from Clipboard to Step: " + sStepID)
                    
                else:
                    uiCommon.log("Unable to add clipboard item to step.  Can't find function_xml for clipboard command [" + sItem + "]")
                    

            else:
                # 1) Get a Function object for the sItem (function_name)
                # 2) update the parent step with the function objects xml
                
                func = uiCommon.GetTaskFunction(sItem)
                if not func:
                    uiCommon.log("Unable to add step.  Can't find a Function definition for [" + sItem + "]")
                
                # gotta do a few things to the templatexml
                xe = ET.fromstring(func.TemplateXML)
                if xe is not None:
                    # there may be some provided values ... so alter the func.TemplateXML accordingly
                    for sXPath, sValue in dValues.iteritems():
                        xNode = xe.find(sXPath)
                        if xNode is not None:
                            xNode.text = sValue
                
                    # Add it!
                    ST.AddToCommandXML(sStepID, sDropXPath, ET.tostring(xe))
    
                    uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, sTaskID, sItem,
                        "Added Command Type: " + sItem + " to Step: " + sStepID)

                else:
                    uiCommon.log("Unable to add step.  No template xml.")


            # draw the embedded step and return the html
            # !!!!! This isn't a new step! ... It's an extension of the parent step.
            # but, since it's a different 'function', we'll treat it like a different step for now
            oEmbeddedStep = task.Step() # a new step object
            oEmbeddedStep.ID = sStepID 
            oEmbeddedStep.Function = func # a function object
            oEmbeddedStep.FunctionName = func.Name
            oEmbeddedStep.FunctionXDoc = xe
            # THIS IS CRITICAL - this embedded step ... all fields in it will need an xpath prefix 
            oEmbeddedStep.XPathPrefix = sDropXPath + "/function"
            
            sStepHTML += ST.DrawEmbeddedStep(oEmbeddedStep)
            # return the html
            return sStepHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmReorderSteps(self):
        try:
            sSteps = uiCommon.getAjaxArg("sSteps")
            i = 1
            aSteps = sSteps.split(",")
            for step_id in aSteps:
                sSQL = "update task_step set step_order = " + str(i) + " where step_id = '" + step_id + "'"

                # there will be no sSQL if there were no steps, so just skip it.
                if sSQL:
                    if not self.db.exec_db_noexcep(sSQL):
                        uiCommon.log("Unable to update steps." + self.db.error)
                    
                i += 1

            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmDeleteStep(self):
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            # you have to know which one we are removing
            sDeletedStepOrder = "0"
            sTaskID = ""
            sCodeblock = ""
            sFunction = ""
            sFunctionXML = ""

            sSQL = "select task_id, codeblock_name, step_order, function_name, function_xml" \
                " from task_step where step_id = '" + sStepID + "'"

            dr = self.db.select_row_dict(sSQL)
            if dr:
                sDeletedStepOrder = str(dr["step_order"])
                sTaskID = dr["task_id"]
                sCodeblock = dr["codeblock_name"]
                sFunction = dr["function_name"]
                sFunctionXML = dr["function_xml"]

                # for logging, we'll stick the whole command XML into the log
                # so we have a complete record of the step that was just deleted.
                uiCommon.WriteObjectDeleteLog(uiGlobals.CatoObjectTypes.Task, "Multiple", "Original Task IDs",
                    "Codeblock:" + sCodeblock +
                    " Step Order:" + sDeletedStepOrder +
                    " Command Type:" + sFunction +
                    " Details:" + sFunctionXML)

            # "embedded" steps have a codeblock name referencing their "parent" step.
            # if we're deleting a parent, whack all the children
            sSQL = "delete from task_step where codeblock_name = '" + sStepID + "'"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log("Unable to delete step." + self.db.error)

            # step might have user_settings
            sSQL = "delete from task_step_user_settings where step_id = '" + sStepID + "'"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log("Unable to delete step user settings." + self.db.error)

            # now whack the parent
            sSQL = "delete from task_step where step_id = '" + sStepID + "'"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log("Unable to delete step." + self.db.error)

            sSQL = "update task_step set step_order = step_order - 1" \
                " where task_id = '" + sTaskID + "'" \
                " and codeblock_name = '" + sCodeblock + "'" \
                " and step_order > " + sDeletedStepOrder
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log("Unable to reorder steps after deletion." + self.db.error)

            self.db.tran_commit()
            
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
        
    def wmUpdateStep(self):
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            sFunction = uiCommon.getAjaxArg("sFunction")
            sXPath = uiCommon.getAjaxArg("sXPath")
            sValue = uiCommon.getAjaxArg("sValue")
    
            # we encoded this in javascript before the ajax call.
            # the safest way to unencode it is to use the same javascript lib.
            # (sometimes the javascript and .net libs don't translate exactly, google it.)
            sValue = uiCommon.unpackJSON(sValue)
    
            uiCommon.log("Updating step [%s (%s)] setting [%s] to [%s]." % (sFunction, sStepID, sXPath, sValue) , 4)
            
            # TODO - not gonna do this any more, do a web method for commenting instead
            # if the function type is "_common" that means this is a literal column on the step table.
#            if sFunction == "_common":
#                sValue = catocommon.tick_slash(sValue) # escape single quotes for the SQL insert
#                sSQL = "update task_step set " + sXPath + " = '" + sValue + "' where step_id = '" + sStepID + "'"
#    
#                if not self.db.exec_db_noexcep(sSQL):
#                    uiCommon.log_nouser(self.db.error, 0)
#    
#            else:

            # XML processing
            # get the xml from the step table and update it
            sSQL = "select function_xml from task_step where step_id = '" + sStepID + "'"

            sXMLTemplate = self.db.select_col_noexcep(sSQL)

            if self.db.error:
                uiCommon.log("Unable to get XML data for step [" + sStepID + "].")

            xDoc = ET.fromstring(sXMLTemplate)
            if xDoc is None:
                uiCommon.log("XML data for step [" + sStepID + "] is invalid.")

            try:
                uiCommon.log("... looking for %s" % sXPath, 4)
                xNode = xDoc.find(sXPath)

                if xNode is None:
                    uiCommon.log("XML data for step [" + sStepID + "] does not contain '" + sXPath + "' node.")

                xNode.text = sValue
            except Exception:
                try:
                    # here's the deal... given an XPath statement, we simply cannot add a new node if it doesn't exist.
                    # why?  because xpath is a query language.  It doesnt' describe exactly what to add due to wildcards and # foo syntax.

                    # but, what we can do is make an assumption in our specific case... 
                    # that we are only wanting to add because we changed an underlying command XML template, and there are existing commands.

                    # so... we will split the xpath into segments, and traverse upward until we find an actual node.
                    # once we have it, we will need to add elements back down.

                    # string[] nodes = sXPath.Split('/')

                    # for node in nodes:
#                         #     # try: to select THIS one, and stick it on the backwards stack
                    #     xNode = xRoot.find("# " + node)
                    #     if xNode is None:
                    #         uiCommon.log("XML data for step [" + sStepID + "] does not contain '" + sXPath + "' node.")

                    # }

                    xFoundNode = None
                    aMissingNodes = []

                    # if there are no slashes we'll just add this one explicitly as a child of root
                    if sXPath.find("/") == -1:
                        xDoc.append(ET.Element(sXPath))
                    else:                             # and if there are break it down
                        sWorkXPath = sXPath
                        while sWorkXPath.find("/") > -1:
                            idx = uiCommon.LastIndexOf(sWorkXPath, "/") + 1
                            aMissingNodes.append(sWorkXPath[idx:])
                            sWorkXPath = sWorkXPath[:idx]

                            xFoundNode = xDoc.find(sWorkXPath)
                            if xFoundNode is not None:
                                # Found one! stop looping
                                break

                        # now that we know where to start (xFoundNode), we can use that as a basis for adding
                        for sNode in aMissingNodes:
                            xFoundNode.append(ET.Element(sNode))

                    # now we should be good to stick the value on the final node.
                    xNode = xDoc.find(sXPath)
                    if xNode is None:
                        uiCommon.log("XML data for step [" + sStepID + "] does not contain '" + sXPath + "' node.")

                    xNode.text = sValue

                    # xRoot.Add(new XElement(sXPath, sValue))
                    # xRoot.SetElementValue(sXPath, sValue)
                except Exception, ex:
                    uiCommon.log("Error Saving Step [" + sStepID + "].  Could not find and cannot create the [" + sXPath + "] property in the XML." + ex.__str__())
                    return ""

            sSQL = "update task_step set " \
                " function_xml = '" + catocommon.tick_slash(ET.tostring(xDoc)) + "'" \
                " where step_id = '" + sStepID + "';"

            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log(self.db)
    
    
            sSQL = "select task_id, codeblock_name, step_order from task_step where step_id = '" + sStepID + "'"
            dr = self.db.select_row_dict(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)
    
            if dr is not None:
                uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, dr["task_id"], sFunction,
                    "Codeblock:" + dr["codeblock_name"] + \
                    " Step Order:" + str(dr["step_order"]) + \
                    " Command Type:" + sFunction + \
                    " Property:" + sXPath + \
                    " New Value: " + sValue)
    
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmToggleStepCommonSection(self):
        # no exceptions, just a log message if there are problems.
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            sButton = uiCommon.getAjaxArg("sButton")
            if uiCommon.IsGUID(sStepID):
                sUserID = uiCommon.GetSessionUserID()
                sButton = ("null" if sButton == "" else "'" + sButton + "'")
    
                #is there a row?
                iRowCount = self.db.select_col_noexcep("select count(*) from task_step_user_settings" \
                    " where user_id = '" + sUserID + "'" \
                    " and step_id = '" + sStepID + "'")
                if iRowCount == 0:
                    sSQL = "insert into task_step_user_settings" \
                        " (user_id, step_id, visible, breakpoint, skip, button)" \
                        " values ('" + sUserID + "','" + sStepID + "', 1, 0, 0, " + sButton + ")"
                else:
                    sSQL = "update task_step_user_settings set button = " + sButton + " where step_id = '" + sStepID + "'"

                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to toggle step button [" + sStepID + "]." + self.db.error)

                return ""
            else:
                uiCommon.log("Unable to toggle step button. Missing or invalid step_id.")
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            
    def wmToggleStep(self):
        # no exceptions, just a log message if there are problems.
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            sVisible = uiCommon.getAjaxArg("sVisible")
            
            if uiCommon.IsGUID(sStepID):
                sUserID = uiCommon.GetSessionUserID()

                sVisible = ("1" if sVisible == "1" else "0")
    
                #is there a row?
                iRowCount = self.db.select_col_noexcep("select count(*) from task_step_user_settings" \
                    " where user_id = '" + sUserID + "'" \
                    " and step_id = '" + sStepID + "'")
                if iRowCount == 0:
                    sSQL = "insert into task_step_user_settings" \
                        " (user_id, step_id, visible, breakpoint, skip)" \
                        " values ('" + sUserID + "','" + sStepID + "', " + sVisible + ", 0, 0)"
                else:
                    sSQL = "update task_step_user_settings set visible = '" + sVisible + "' where step_id = '" + sStepID + "'"

                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to toggle step visibility [" + sStepID + "]." + self.db.error)
                
                return ""
            else:
                uiCommon.log("Unable to toggle step visibility. Missing or invalid step_id.", 2)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmToggleStepSkip(self):
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            sSkip = uiCommon.getAjaxArg("sSkip")

            sSQL = "update task_step set commented = " + str(sSkip) + " where step_id = '" + sStepID + "'"
            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log("Unable to update steps." + self.db.error)

            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmFnIfAddSection(self):
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            sAddTo = uiCommon.getAjaxArg("sAddTo")
            sIndex = uiCommon.getAjaxArg("iIndex")
            if sIndex > "0":
                # an index > 0 means its one of many 'elif' sections
                if sAddTo:
                    # add a slash seperator if there's an add to
                    sAddTo += "/" 
                ST.AddToCommandXML(sStepID, sAddTo + "tests", "<test><eval input_type=\"text\" /><action input_type=\"text\" /></test>")
            elif sIndex == "-1":
                # whereas an index of -1 means its the ONLY 'else' section
                ST.AddToCommandXML(sStepID, sAddTo, "<else input_type=\"text\" />")
            else:
                # and of course a missing or 0 index is an error
                uiCommon.log("Unable to modify step. Invalid index.")

            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmTaskSearch(self):
        try:
            sFilter = uiCommon.getAjaxArg("sSearch")
            tasks = task.Tasks(sFilter)
            if tasks.rows:
                sHTML = "<hr />"
    
                iRowsToGet = len(tasks.rows)
    
                if iRowsToGet == 0:
                    sHTML += "No results found"
                else:
                    if iRowsToGet >= 100:
                        sHTML += "<div>Search found " + iRowsToGet + " results.  Displaying the first 100.</div>"
                        iRowsToGet = 99
                    sHTML += "<ul id=\"search_task_ul\" class=\"search_dialog_ul\">"
    
                    i = 0
                    for row in tasks.rows:
                        if i > iRowsToGet:
                            break
                        
                        sTaskName = row["task_name"].replace("\"", "\\\"")
                        sLabel = row["task_code"] + " : " + sTaskName
                        sDesc = (row["task_desc"] if row["task_desc"] else "")
                        sDesc = sDesc.replace("\"", "").replace("'", "")
    
                        sHTML += "<li class=\"ui-widget-content ui-corner-all search_dialog_value\" tag=\"task_picker_row\"" \
                            " original_task_id=\"" + row["original_task_id"] + "\"" \
                            " task_label=\"" + sLabel + "\"" \
                            "\">"
                        sHTML += "<div class=\"step_header_title search_dialog_value_name\">" + sLabel + "</div>"
    
                        sHTML += "<div class=\"step_header_icons\">"
    
                        # if there's a description, show a tooltip
                        if sDesc:
                            sHTML += "<img src=\"static/images/icons/info.png\" class=\"search_dialog_tooltip trans50\" title=\"" + sDesc + "\" />"
    
                        sHTML += "</div>"
                        sHTML += "<div class=\"clearfloat\"></div>"
                        sHTML += "</li>"
                        
                        i += 1
                        
                sHTML += "</ul>"

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetStepVarsEdit(self):
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            sUserID = uiCommon.GetSessionUserID()
    
            oStep = ST.GetSingleStep(sStepID, sUserID)
            fn = uiCommon.GetTaskFunction(oStep.FunctionName)
            if fn is None:
                uiCommon.log("Error - Unable to get the details for the Command type '" + oStep.FunctionName + "'.")
            
            # we will return some key values, and the html for the dialog
            sHTML = ST.DrawVariableSectionForEdit(oStep)
            
            if not sHTML:
                sHTML = "<span class=\"red_text\">Unable to get command variables.</span>"
    
            return '{"parse_type":"%d","row_delimiter":"%d","col_delimiter":"%d","html":"%s"}' % \
                (oStep.OutputParseType, oStep.OutputRowDelimiter, oStep.OutputColumnDelimiter, uiCommon.packJSON(sHTML))
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmUpdateVars(self):
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            sOPM = uiCommon.getAjaxArg("sOPM")
            sRowDelimiter = uiCommon.getAjaxArg("sRowDelimiter")
            sColDelimiter = uiCommon.getAjaxArg("sColDelimiter")
            oVarArray = uiCommon.getAjaxArg("oVarArray")
            
            # if every single variable is delimited, we can sort them!
            bAllDelimited = True
            
            # update the function_xml attributes.
            ST.SetNodeAttributeinCommandXML(sStepID, "function", "row_delimiter", sRowDelimiter)
            ST.SetNodeAttributeinCommandXML(sStepID, "function", "col_delimiter", sColDelimiter)
    
    
            # 1 - create a new xdocument
            # 2 - spin thru adding the variables
            # 3 - commit the whole doc at once to the db
    
            xVars = ET.Element("step_variables")
    
            # spin thru the variable array from the client
            for oVar in oVarArray:
                # [0 - var type], [1 - var_name], [2 - left property], [3 - right property], [4 - left property type], [5 - right property type]
    
                # I'm just declaring named variable here for readability
                sVarName = str(oVar[0])  # no case conversion
                sVarType = str(oVar[1]).lower()
                sLProp = str(uiCommon.unpackJSON(oVar[2]))
                sRProp = str(uiCommon.unpackJSON(oVar[3]))
                sLType = str(oVar[4])
                sRType = str(oVar[5])
    
                xVar = ET.SubElement(xVars, "variable")
                xVarName = ET.SubElement(xVar, "name")
                xVarName.text = sVarName
                xVarType = ET.SubElement(xVar, "type")
                xVarType.text = sVarType
    
                # now that we've added it, based on the type let's add the custom properties
                if sVarType == "delimited":
                    x = ET.SubElement(xVar, "position")
                    x.text = sLProp
                elif sVarType == "regex":
                    bAllDelimited = False
                    x = ET.SubElement(xVar, "regex")
                    x.text = sLProp
                elif sVarType == "range":
                    bAllDelimited = False
                    # we favor the 'string' mode over the index.  If a person selected 'index' that's fine
                    # but if something went wrong, we default to prefix/suffix.
                    if sLType == "index":
                        x = ET.SubElement(xVar, "range_begin")
                        x.text = sLProp
                    else:
                        x = ET.SubElement(xVar, "prefix")
                        x.text = sLProp
    
                    if sRType == "index":
                        x = ET.SubElement(xVar, "range_end")
                        x.text = sRProp
                    else:
                        x = ET.SubElement(xVar, "suffix")
                        x.text = sRProp
                elif sVarType == "xpath":
                    bAllDelimited = False
                    x = ET.SubElement(xVar, "xpath")
                    x.text = sLProp
    
            # if it's delimited, sort it
            if sOPM == "1" or bAllDelimited == True:
                # They're all delimited, sort by the delimiter index
                data = []
                for elem in xVars:
                    key = elem.findtext("position")
                    data.append((key, elem)) # the double parens are required! we're appending a tuple
                
                data.sort()
                
                # insert the last item from each tuple
                xVars[:] = [item[-1] for item in data]

            
            uiCommon.log("Saving variables ...", 4)
            uiCommon.log(ET.tostring(xVars), 4)
            
            # add and remove using the xml wrapper functions
            ST.RemoveFromCommandXML(sStepID, "step_variables")
            ST.AddToCommandXML(sStepID, "", catocommon.tick_slash(ET.tostring(xVars)))

            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetClips(self):
        try:
            sUserID = uiCommon.GetSessionUserID()
            sHTML = ""
            
            sSQL = "select s.clip_dt, s.step_id, s.step_desc, s.function_name, s.function_xml," \
                " s.output_parse_type, s.output_row_delimiter, s.output_column_delimiter, s.variable_xml" \
                " from task_step_clipboard s" \
                " where s.user_id = '" + sUserID + "'" \
                " and s.codeblock_name is null" \
                " order by s.clip_dt desc"

            dt = self.db.select_all_dict(sSQL)
            if self.db.error:
                uiCommon.log("Unable to get clipboard data for user [" + sUserID + "].<br />" + self.db.error)

            if dt:
                for dr in dt:
                    fn = uiCommon.GetTaskFunction(dr["function_name"])
                    if fn is None:
                        return "Error building Clip - Unable to get the details for the Command type '" + dr["function_name"] + "'."
        
                    sStepID = dr["step_id"]
                    sLabel = fn.Label
                    sIcon = fn.Icon
                    sDesc = uiCommon.GetSnip(dr["step_desc"], 75)
                    sClipDT = str(dr["clip_dt"])
                    
                    sHTML += "<li" \
                        " id=\"clip_" + sStepID + "\"" \
                            " name=\"clip_" + sStepID + "\"" \
                            " class=\"command_item function clip\"" \
                            ">"
                    
                    # a table for the label so the clear icon can right align
                    sHTML += "<table width=\"99%\" border=\"0\"><tr>"
                    sHTML += "<td width=\"1px\"><img alt=\"\" src=\"" + sIcon + "\" /></td>"
                    sHTML += "<td style=\"vertical-align: middle; padding-left: 5px;\">" + sLabel + "</td>"
                    sHTML += "<td width=\"1px\" style=\"vertical-align: middle;\">"
                    
                    # view icon
                    # due to the complexity of telling the core routines to look in the clipboard table, it 
                    # it not possible to easily show the complex command types
                    #  without a redesign of how this works.  NSC 4-19-2011
                    # due to several reasons, most notable being that the XML node for each of those commands 
                    # that contains the step_id is hardcoded and the node names differ.
                    # and GetSingleStep requires a step_id which must be mined from the XML.
                    # so.... don't show a preview icon for them
                    sFunction = fn.Name
                    
                    if not sFunction in "loop,exists,if,while":
                        sHTML += "<span id=\"btn_view_clip\" view_id=\"v_" + sStepID + "\">" \
                            "<img src=\"static/images/icons/search.png\" style=\"width: 16px; height: 16px;\" alt=\"\" />" \
                                "</span>"
                    sHTML += "</td></tr>"
                    
                    sHTML += "<tr><td>&nbsp;</td><td><span class=\"code\">" + sClipDT + "</span></td>"
                    sHTML += "<td>"
                    # delete icon
                    sHTML += "<span id=\"ui-icon ui-icon-close forceinline btn_clear_clip\" remove_id=\"" + sStepID + "\"></span>"
                    sHTML += "</td></tr></table>"
                    
                    
                    sHTML += "<div class=\"hidden\" id=\"help_text_clip_" + sStepID + "\">" + sDesc + "</div>"
                    
                    # TODO: for the moment we aren't building the view viersion of the command
                    # until we convert all the VIEW functions!
                    # we use this function because it draws a smaller version than DrawReadOnlyStep
                    #sStepHTML = ""
                    ## and don't draw those complex ones either
                    #if not sFunction in "loop,exists,if,while":
                    # BUT WHEN WE DO! ... build a clipboard step object here from the row selected above
                    #    sStepHTML = ST.DrawClipboardStep(cs, True)
                    
                    # sHTML += "<div class=\"hidden\" id=\"v_" + sStepID + "\">" + sStepHTML + "</div>"
                    
                    sHTML += "</li>"
            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmCopyStepToClipboard(self):
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            self.CopyStepToClipboard(sStepID)
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def CopyStepToClipboard(self, sStepID):
        try:
            if uiCommon.IsGUID(sStepID):
                sUserID = uiCommon.GetSessionUserID()
    
                # commands get new ids when copied into the clpboard.
                sNewStepID = catocommon.new_guid()
    
                # it's a bit hokey, but if a step already exists in the clipboard, 
                # and we are copying that step again, 
                # ALWAYS remove the old one.
                # we don't want to end up with lots of confusing copies
                sSQL = "delete from task_step_clipboard" \
                    " where user_id = '" + sUserID + "'" \
                    " and src_step_id = '" + sStepID + "'"
                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to clean clipboard." + self.db.error)
    
                sSQL = " insert into task_step_clipboard" \
                    " (user_id, clip_dt, src_step_id, root_step_id, step_id, function_name, function_xml, step_desc," \
                        " output_parse_type, output_row_delimiter, output_column_delimiter, variable_xml)" \
                    " select '" + sUserID + "', now(), step_id, '" + sNewStepID + "', '" + sNewStepID + "'," \
                        " function_name, function_xml, step_desc," \
                        " output_parse_type, output_row_delimiter, output_column_delimiter, variable_xml" \
                    " from task_step" \
                    " where step_id = '" + sStepID + "'"
                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to copy step [" + sStepID + "]." + self.db.error)
    
                return ""
            else:
                uiCommon.log("Unable to copy step. Missing or invalid step_id.")
    
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmRemoveFromClipboard(self):
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            sUserID = uiCommon.GetSessionUserID()

            # if the sStepID is a guid, we are removing just one
            # otherwise, if it's "ALL" we are whacking them all
            if uiCommon.IsGUID(sStepID):
                sSQL = "delete from task_step_clipboard" \
                    " where user_id = '" + sUserID + "'" \
                    " and root_step_id = '" + sStepID + "'"
                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to remove step [" + sStepID + "] from clipboard." + self.db.error)

                return ""
            elif sStepID == "ALL":
                sSQL = "delete from task_step_clipboard where user_id = '" + sUserID + "'"
                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to remove step [" + sStepID + "] from clipboard." + self.db.error)

                return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    
    def wmRunTask(self):
        try:
            sTaskID = uiCommon.getAjaxArg("sTaskID")
            sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
            sAccountID = uiCommon.getAjaxArg("sAccountID")
            sAssetID = uiCommon.getAjaxArg("sAssetID")
            sParameterXML = uiCommon.getAjaxArg("sParameterXML")
            sDebugLevel = uiCommon.getAjaxArg("iDebugLevel")
            
            sUserID = uiCommon.GetSessionUserID()
            return uiCommon.AddTaskInstance(sUserID, sTaskID, sEcosystemID, sAccountID, sAssetID, sParameterXML, sDebugLevel)
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetAccountEcosystems(self):
        sAccountID = uiCommon.getAjaxArg("sAccountID")
        sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")

        sHTML = ""

        try:
            # if the ecosystem passed in isn't really there, make it "" so we can compare below.
            if not sEcosystemID:
                sEcosystemID = ""

            if sAccountID:
                sSQL = "select ecosystem_id, ecosystem_name from ecosystem" \
                     " where account_id = '" + sAccountID + "'" \
                     " order by ecosystem_name"; 

            dt = self.db.select_all_dict(sSQL)
    
            if dt:
                sHTML += "<option value=''></option>"

                for dr in dt:
                    sSelected = ("selected=\"selected\"" if sEcosystemID == dr["ecosystem_id"] else "")
                    sHTML += "<option value=\"" + dr["ecosystem_id"] + "\" " + sSelected + ">" + dr["ecosystem_name"] + "</option>"

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)


    """
        PARAMETER WEB METHODS and supporting static methods.
        
        The following group of parameter web methods all just call static methods in this class.  Why?
        Because there is an interplay between them, where they call one another depending on the context.
    """
    def wmGetParameterXML(self):
        sType = uiCommon.getAjaxArg("sType")
        sID = uiCommon.getAjaxArg("sID")
        sFilterByEcosystemID = uiCommon.getAjaxArg("sFilterByEcosystemID")
        return self.GetParameterXML(sType, sID, sFilterByEcosystemID)

    def GetParameterXML(self, sType, sID, sFilterByEcosystemID):
        if sType == "task":
            return self.GetObjectParameterXML(sType, sID, "")
        else:
            return self.GetMergedParameterXML(sType, sID, sFilterByEcosystemID); # Merging is happening here!

    # """
    #  This method simply gets the XML directly from the db for the type.
    #  It may be different by type!
    
    #  The schema should be the same, but some documents (task) are complete, while
    #  others (action, instance) are JUST VALUES, not the complete document.
    # """
    def wmGetObjectParameterXML(self):
        sType = uiCommon.getAjaxArg("sType")
        sID = uiCommon.getAjaxArg("sID")
        sFilterByEcosystemID = uiCommon.getAjaxArg("sFilterByEcosystemID")
        return self.GetObjectParameterXML(sType, sID, sFilterByEcosystemID)

    def GetObjectParameterXML(self, sType, sID, sFilterByEcosystemID):
        try:
            if sType == "instance":
                # if sID is a guid, it's a task_id ... get the most recent run
                # otherwise assume it's a task_instance and try: that.
                if uiCommon.IsGUID(sID):
                    sSQL = "select parameter_xml from task_instance_parameter where task_instance = " \
                        "(select max(task_instance) from task_instance where task_id = '" + sID + "')"
                elif uiCommon.IsGUID(sFilterByEcosystemID):  # but if there's an ecosystem_id, limit it to tha:
                    sSQL = "select parameter_xml from task_instance_parameter where task_instance = " \
                        "(select max(task_instance) from task_instance where task_id = '" + sID + "')" \
                        " and ecosystem_id = '" + sFilterByEcosystemID + "'"
                else:
                    sSQL = "select parameter_xml from task_instance_parameter where task_instance = '" + sID + "'"
            elif sType == "runtask":
                #  in this case, sID is actually a *step_id* !
                # sucks that MySql doesn't have decent XML functions... we gotta do manipulation grr...
                sSQL = "select substring(function_xml," \
                    " locate('<parameters>', function_xml)," \
                    " locate('</parameters>', function_xml) - locate('<parameters>', function_xml) + 13)" \
                    " as parameter_xml" \
                    " from task_step where step_id = '" + sID + "'"
    
            elif sType == "action":
                sSQL = "select parameter_defaults from ecotemplate_action where action_id = '" + sID + "'"
            elif sType == "plan":
                sSQL = "select parameter_xml from action_plan where plan_id = " + sID
            elif sType == "schedule":
                sSQL = "select parameter_xml from action_schedule where schedule_id = '" + sID + "'"
            elif sType == "task":
                sSQL = "select parameter_xml from task where task_id = '" + sID + "'"
    
            sParameterXML = self.db.select_col_noexcep(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)
    
            if sParameterXML:
                xParams = ET.fromstring(sParameterXML)
                if xParams is None:
                    uiCommon.log("Parameter XML data for [" + sType + ":" + sID + "] is invalid.")
    
                # NOTE: some values on this document may have a "encrypt" attribute.
                # If so, we will:
                #  1) obscure the ENCRYPTED value and make it safe to be an html attribute
                #  2) return some stars so the user will know a value is there.
                for xEncryptedValue in xParams.findall("parameter[@encrypt='true']/values/value"):
                    # if the value is empty, it still gets an oev attribute
                    sVal = ("" if not xEncryptedValue.text else uiCommon.packJSON(xEncryptedValue.text))
                    xEncryptedValue.attrib["oev"] = sVal
                    # but it only gets stars if it has a value
                    if sVal:
                        xEncryptedValue.text = "********"
    
                resp = ET.tostring(xParams)
                if resp:
                    return resp

            # nothing found
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
    
        # it may just be there are no parameters
        return ""

    def wmGetMergedParameterXML(self):
        sType = uiCommon.getAjaxArg("sType")
        sID = uiCommon.getAjaxArg("sID")
        sEcosystemID = uiCommon.getAjaxArg("sEcosystemID")
        return self.GetMergedParameterXML(sType, sID, sEcosystemID)

    # """
    #  * This method does MERGING!
    #  * 
    #  * It gets the XML for the Task, and additionally get the XML for the other record,
    #  * and merges them together, using the values from one to basically select values in 
    #  * the master task XML.
    #  * 
    #  * """
    def GetMergedParameterXML(self, sType, sID, sEcosystemID):
        try:
            if not sID:
                uiCommon.log("ID required to look up default Parameter values.")
        
            # what is the task associated with this action?
            # and get the XML for it
            sDefaultsXML = ""
            sTaskID = ""
        
            if sType == "action":
                sDefaultsXML = self.GetObjectParameterXML(sType, sID, "")
        
                sSQL = "select t.task_id" \
                     " from ecotemplate_action ea" \
                     " join task t on ea.original_task_id = t.original_task_id" \
                     " and t.default_version = 1" \
                     " where ea.action_id = '" + sID + "'"
            elif sType == "runtask":
                # RunTask is actually a command type
                # but it's very very similar to an Action.
                # so... it handles it's params like an action... more or less.
                
                # HACK ALERT!  Since we are dealing with a unique case here where we have and need both the 
                # step_id AND the target task_id, we're piggybacking a value in.
                # the sID is the STEP_ID (which is kindof equivalient to the action)
                # the sEcosystemID is the target TASK_ID
                # yes, it's a hack I know... but better than adding another argument everywhere... sue me.
                
                # NOTE: plus, don't get confused... yes, run task references tasks by original id and version, but we already worked that out.
                # the sEcosystemID passed in to this function is already resolved to an explicit task_id... it's the right one.
        
                # get the parameters off the step itself.
                # which is also goofy, as they are embedded *inside* the function xml of the step.
                # but don't worry that's handled in here
                sDefaultsXML = self.GetObjectParameterXML(sType, sID, "")
                
                # now, we will want to get the parameters for the task *referenced by the command* down below
                # but no sql is necessary to get the ID... we already know it!
                sTaskID = sEcosystemID
                
            elif sType == "instance":
                sDefaultsXML = self.GetObjectParameterXML(sType, sID, sEcosystemID)
        
                # IMPORTANT!!! if the ID is not a guid, it's a specific instance ID, and we'll need to get the task_id
                # but if it is a GUID, but the type is "instance", taht means the most recent INSTANCE for this TASK_ID
                if uiCommon.IsGUID(sID):
                    sTaskID = sID
                else:
                    sSQL = "select task_id" \
                         " from task_instance" \
                         " where task_instance = '" + sID + "'"
            elif sType == "plan":
                sDefaultsXML = self.GetObjectParameterXML(sType, sID, "")
        
                sSQL = "select task_id" \
                    " from action_plan" \
                    " where plan_id = '" + sID + "'"
            elif sType == "schedule":
                sDefaultsXML = self.GetObjectParameterXML(sType, sID, "")
        
                sSQL = "select task_id" \
                    " from action_schedule" \
                    " where schedule_id = '" + sID + "'"
        
        
            # if we didn't get a task id directly, use the SQL to look it up
            if not sTaskID:
                sTaskID = self.db.select_col_noexcep(sSQL)
                if self.db.error:
                    uiCommon.log_nouser(self.db.error, 0)
        
            if not uiCommon.IsGUID(sTaskID):
                uiCommon.log("Unable to find Task ID for record.")
        
        
            # get the parameter XML from the TASK
            sTaskParamXML = self.GetParameterXML("task", sTaskID, "")
            xTPParams = None
            if sTaskParamXML:
                xTPParams = ET.fromstring(sTaskParamXML)
                if xTPParams is None:
                    uiCommon.log("Task Parameter XML data is invalid.")
        
            # we populated this up above too
            if sDefaultsXML:
                xDefParams = ET.fromstring(sDefaultsXML)
                if xDefParams is None:
                    uiCommon.log("Defaults XML data is invalid.")
        
                # spin the nodes in the DEFAULTS xml, then dig in to the task XML and UPDATE the value if found.
                # (if the node no longer exists, delete the node from the defaults xml IF IT WAS AN ACTION)
                # and default "values" take precedence over task values.
                for xDefault in xDefParams.findall("parameter"):
                    # nothing to do if it's empty
                    if xDefault is None:
                        break
            
                    # look it up in the task param xml
                    sDefID = xDefault.get("id", "")
                    sDefName = xDefault.findtext("name", "")
                    xDefValues = xDefault.find("values")
                    
                    # nothing to do if there is no values node...
                    if xDefValues is None:
                        break
                    # or if it contains no values.
                    if not len(xDefValues):
                        break
                    # or if there is no parameter name
                    if not sDefName:
                        break
                
                
                    # so, we have some valid data in the defaults xml... let's merge!
    
                    # NOTE! elementtree doesn't track parents of nodes.  We need to build a parent map...
                    parent_map = dict((c, p) for p in xTPParams.getiterator() for c in p)
                    
                    # we have the name of the parameter... go spin and find the matching node in the TASK param XML
                    xTaskParam = None
                    for node in xTPParams.findall("parameter/name"):
                        if node.text == sDefName:
                            # now we have the "name" node, what's the parent?
                            xTaskParam = parent_map[node]
                            
                            
                    # if it doesn't exist in the task params, remove it from this document, permanently
                    # but only for action types... instance data is historical and can't be munged
    
                    if xTaskParam is None and sType == "action":
                        uiCommon.log("INFO: A parameter exists on the Action that no longer exists on the Task.  Removing it...", 4)
                        # BUT! in order to be able to delete it, we need enough xpath information to identify it.
                        # it has an 'id' attribute ... use that.
                        if sDefID:
                            uiCommon.RemoveNodeFromXMLColumn("ecotemplate_action", "parameter_defaults", "action_id = '" + sID + "'", "parameter[@id='" + sDefID + "']")           
                        continue
            
                    if xTaskParam is not None:
                        # is this an encrypted parameter?
                        sEncrypt = ""
                        if xTaskParam.get("encrypt") is not None:
                            sEncrypt = xTaskParam.get("encrypt", "")
                
                
                        # and the "values" collection will be the 'next' node
                        xTaskParamValues = xTaskParam.find("values")
                
                        sPresentAs = xTaskParamValues.get("present_as", "")
                        if sPresentAs == "dropdown":
                            # dropdowns get a "selected" indicator
                            sValueToSelect = xDefValues.findtext("value", "")
                            if sValueToSelect:
                                print sValueToSelect
                                # find the right one by value and give it the "selected" attribute.
                                for xVal in xTaskParamValues.findall("value"):
                                    if xVal.text == sValueToSelect:
                                        xVal.attrib["selected"] = "true"
                        elif sPresentAs == "list":
                            # first, a list gets ALL the values replaced...
                            xTaskParamValues.clear()
                            xTaskParamValues.append(xDefValues)
                        else:
                            # IMPORTANT NOTE:
                            # remember... both these XML documents came from wmGetObjectParameterXML...
                            # so any encrypted data IS ALREADY OBFUSCATED and base64'd in the oev attribute.
                            
                            # it's a single value, so just replace it with the default.
                            xVal = xTaskParamValues.find("value[1]")
                            if xVal is not None:
                                # if this is an encrypted parameter, we'll be replacing (if a default exists) the oev attribute
                                # AND the value... don't want them to get out of sync!
                                if catocommon.is_true(sEncrypt):
                                    if xDefValues.find("value") is not None:
                                        xVal.attrib["oev"] = xDefValues.find("value").get("oev", "")
                                        xVal.text = xDefValues.findtext("value", "")
                                else:
                                    # not encrypted, just replace the value.
                                    if xDefValues.find("value") is not None:
                                        xVal.text = xDefValues.findtext("value", "")
        
            if xTPParams is not None:    
                resp = ET.tostring(xTPParams)
                if resp:
                    return resp

            # nothing found
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
    
    def wmSaveDefaultParameterXML(self):
        try:
            sType = uiCommon.getAjaxArg("sType")
            sID = uiCommon.getAjaxArg("sID")
            sTaskID = uiCommon.getAjaxArg("sTaskID") # sometimes this may be here
            sXML = uiCommon.getAjaxArg("sXML")
            sUserID = uiCommon.GetSessionUserID()
    
            if uiCommon.IsGUID(sID) and uiCommon.IsGUID(sUserID):
                # we encoded this in javascript before the ajax call.
                # the safest way to unencode it is to use the same javascript lib.
                # (sometimes the javascript and .net libs don't translate exactly, google it.)
                sXML = uiCommon.unpackJSON(sXML)

                # we gotta peek into the XML and encrypt any newly keyed values
                sXML = uiCommon.PrepareAndEncryptParameterXML(sXML);                
    
                # so, like when we read it, we gotta spin and compare, and build an XML that only represents *changes*
                # to the defaults on the task.
                
                if sType == "action":
                    # what is the task associated with this action?
                    sSQL = "select t.task_id" \
                        " from ecotemplate_action ea" \
                        " join task t on ea.original_task_id = t.original_task_id" \
                        " and t.default_version = 1" \
                        " where ea.action_id = '" + sID + "'"
                    sTaskID = self.db.select_col_noexcep(sSQL)
                    if self.db.error:
                        uiCommon.log_nouser(self.db.error, 0)
    
                if not uiCommon.IsGUID(sTaskID):
                    uiCommon.log("Unable to find Task ID for Action, or no Task ID provided.")
    
    
                sOverrideXML = ""
                xTPDoc = None
                xADDoc = None
    
                # get the parameter XML from the TASK
                sTaskParamXML = self.GetParameterXML("task", sTaskID, "")
                if sTaskParamXML:
                    xTPDoc = ET.fromstring(sTaskParamXML)
                    if xTPDoc is None:
                        uiCommon.log("Task Parameter XML data is invalid.")
        
                # we had the ACTION defaults handed to us
                if sXML:
                    xADDoc = ET.fromstring(sXML)
                    if xADDoc is None:
                        uiCommon.log("Action Defaults XML data is invalid.")
    
                # spin the nodes in the ACTION xml, then dig in to the task XML and UPDATE the value if found.
                # (if the node no longer exists, delete the node from the action XML)
                # and action "values" take precedence over task values.
                
                for xDefault in xADDoc.findall("parameter"):
                    # look it up in the task param xml
                    sADName = xDefault.findtext("name", "")
                    xADValues = xDefault.find("values")

                    # NOTE! elementtree doesn't track parents of nodes.  We need to build a parent map...
                    parent_map = dict((c, p) for p in xTPDoc.getiterator() for c in p)
                    
                    # we have the name of the parameter... go spin and find the matching node in the TASK param XML
                    xTaskParam = None
                    for node in xTPDoc.findall("parameter/name"):
                        if node.text == sADName:
                            # now we have the "name" node, what's the parent?
                            xTaskParam = parent_map[node]
    
                    # if it doesn't exist in the task params, remove it from this document
                    if xTaskParam is None:
                        xADDoc.remove(xDefault)
                        continue
    
    
                    # and the "values" collection will be the 'next' node
                    xTaskParamValues = xTaskParam.find("values")
    
                    
                    # so... it might be 
                    # a) just an oev (original encrypted value) so de-base64 it
                    # b) a value flagged for encryption
                    
                    # note we don't care about dirty unencrypted values... they'll compare down below just fine.
                    
                    # is it encrypted?
                    bEncrypted = catocommon.is_true(xTaskParam.get("encrypt", ""))
                            
                    if bEncrypted:
                        for xVal in xADValues.findall("value"):
                            # a) is it an oev?  unpackJSON it (that's just an obfuscation wrapper)
                            if catocommon.is_true(xVal.get("oev", "")):
                                xVal.text = uiCommon.unpackJSON(xVal.text)
                                del xVal.attrib["oev"]
                            
                            # b) is it do_encrypt?  (remove the attribute to keep the db clutter down)
                            if xVal.get("do_encrypt") is not None:
                                xVal.text = catocommon.cato_encrypt(xVal.text)
                                del xVal.attrib["do_encrypt"]
                                
                    
                    # now that the encryption is sorted out,
                    #  if the combined values of the parameter happens to match what's on the task
                    #   we just remove it.
                    
                    # we're doing combined because of lists (the whole list must match for it to be a dupe)
                    
                    # it's easy to look at all the values in a node with the node.text property.
                    # but we'll have to manually concatenate all the oev attributes
                    
                    sTaskVals = ""
                    sDefVals = ""

                    if bEncrypted:
                        #  the task document already has the oev obfuscated
                        for xe in xTaskParamValues.findall("value"):
                            sTaskVals += xe.get("oev", "")
                        # but the XML we just got from the client doesn't... it's in the value.
                        for xe in xADValues.findall("value"):
                            s = (xe.text if xe.text else "")
                            sDefVals += uiCommon.packJSON(s)
                            
                        if sTaskVals == sDefVals:
                            xADDoc.remove(xDefault)
                            continue
                    else:
                        # just spin the values and construct a string of all the text, 
                        # then check if they match
                        for s in xTaskParamValues.findtext("value"):
                            sTaskVals += s
                        for s in xADValues.findtext("value"):
                            sDefVals += s
                        if sTaskVals == sDefVals:
                            xADDoc.remove(xDefault)
                            continue

                # done
                sOverrideXML = ET.tostring(xADDoc)
    
                # FINALLY, we have an XML that represents only the differences we wanna save.
                if sType == "action":
                    sSQL = "update ecotemplate_action set" \
                        " parameter_defaults = '" + sOverrideXML + "'" \
                        " where action_id = '" + sID + "'"
    
                    if not self.db.exec_db_noexcep(sSQL):
                        uiCommon.log("Unable to update Action [" + sID + "]." + self.db.error)
    
                    uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.EcoTemplate, sID, sID, "Default parameters updated: [" + sOverrideXML + "]")
                elif sType == "runtask":
                    # WICKED!!!!
                    # I can use my super awesome xml functions!
                    ST.RemoveFromCommandXML(sID, "parameters")
                    ST.AddToCommandXML(sID, "", sOverrideXML)
            else:
                uiCommon.log("Unable to update Eco Template Action. Missing or invalid Action ID.")
    
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    """
        END OF PARAMETER METHODS
    """
    
    # This one is normal, just returns html for the Parameters toolbox
    # But, it's shared by several pages.
    def wmGetParameters(self):
        sType = uiCommon.getAjaxArg("sType")
        sID = uiCommon.getAjaxArg("sID")
        bEditable = uiCommon.getAjaxArg("bEditable")
        bSnipValues = uiCommon.getAjaxArg("bSnipValues")

        try:
            if not sType:
                uiCommon.log("ERROR: Type was not passed to wmGetParameters.", 0)
                return "ERROR: Type was not passed to wmGetParameters."
            
            sTable = ""

            if sType == "ecosystem":
                sTable = "ecosystem"
            elif sType == "task":
                sTable = "task"

            sSQL = "select parameter_xml from " + sTable + " where " + sType + "_id = '" + sID + "'"

            sParameterXML = self.db.select_col_noexcep(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)

            if sParameterXML:
                xParams = ET.fromstring(sParameterXML)
                if xParams is None:
                    uiCommon.log("Parameter XML data for " + sType + " [" + sID + "] is invalid.")

                sHTML = ""

                for xParameter in xParams.findall("parameter"):
                    sPID = xParameter.get("id", "")
                    sName = xParameter.findtext("name", "")
                    sDesc = xParameter.findtext("desc", "")

                    bEncrypt = catocommon.is_true(xParameter.get("encrypt", ""))

                    sHTML += "<div class=\"parameter\">"
                    sHTML += "  <div class=\"ui-state-default parameter_header\">"

                    sHTML += "<div class=\"step_header_title\"><span class=\"parameter_name"
                    sHTML += (" pointer" if bEditable else "") # make the name a pointer if it's editable
                    sHTML += "\" id=\"" + sPID + "\">"
                    sHTML += sName
                    sHTML += "</span></div>"

                    sHTML += "<div class=\"step_header_icons\">"
                    sHTML += "<span class=\"ui-icon ui-icon-info forceinline parameter_help_btn\" title=\"" + sDesc.replace("\"", "") + "\"></span>"

                    if catocommon.is_true(bEditable):
                        sHTML += "<span class=\"ui-icon ui-icon-close forceinline parameter_remove_btn pointer\" remove_id=\"" + sPID + "\"></span>"

                    sHTML += "</div>"
                    sHTML += "</div>"


                    sHTML += "<div class=\"ui-widget-content ui-corner-bottom clearfloat parameter_detail\">"

                    # desc - a short snip is shown here... 75 chars.

                    # if sDesc):
                    #     if bSnipValues:
                    #         sDesc = uiCommon.GetSnip(sDesc, 75)
                    #     else
                    #         sDesc = uiCommon.FixBreaks(sDesc)
                    # sHTML += "<div class=\"parameter_desc hidden\">" + sDesc + "</div>"


                    # values
                    xValues = xParameter.find("values")
                    if xValues is not None:
                        for xValue in xValues.findall("value"):
                            sValue = ("" if not xValue.text else xValue.text)

                            # only show stars IF it's encrypted, but ONLY if it has a value
                            if bEncrypt and sValue:
                                sValue = "********"
                            else:
                                if bSnipValues:
                                    sValue = uiCommon.GetSnip(sValue, 64)
                                else:
                                    sValue = uiCommon.FixBreaks(sValue, "")

                            sHTML += "<div class=\"ui-widget-content ui-corner-tl ui-corner-bl parameter_value\">" + sValue + "</div>"

                    sHTML += "</div>"
                    sHTML += "</div>"

                return sHTML

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

        # it may just be there are no parameters
        return ""

    def wmGetTaskParam(self):
        try:
            sID = uiCommon.getAjaxArg("sID")
            sType = uiCommon.getAjaxArg("sType")
            sParamID = uiCommon.getAjaxArg("sParamID")
    
            if not uiCommon.IsGUID(sID):
                uiCommon.log("Invalid or missing ID.")
                return "Invalid or missing ID."

            sTable = ""

            if sType == "ecosystem":
                sTable = "ecosystem"
            elif sType == "task":
                sTable = "task"

            # default values if adding - get overridden if there is a record
            sName = ""
            sDesc = ""
            sRequired = "false"
            sPrompt = "true"
            sEncrypt = "false"
            sValuesHTML = ""
            sPresentAs = "value"
            sConstraint = ""
            sConstraintMsg = "";                                        
            sMinLength = ""
            sMaxLength = ""
            sMinValue = ""
            sMaxValue = ""

            if sParamID:
                sXML = ""
                sSQL = "select parameter_xml" \
                        " from " + sTable + \
                        " where " + sType + "_id = '" + sID + "'"

                sXML = self.db.select_col_noexcep(sSQL)
                if self.db.error:
                    uiCommon.log("Unable to get parameter_xml.  " + self.db.error)
                    return "Unable to get parameter_xml.  See log for details."

                if sXML:
                    xd = ET.fromstring(sXML)
                    if xd is None: uiCommon.log("XML parameter data is invalid.")

                    xParameter = xd.find("parameter[@id='" + sParamID + "']")
                    if xParameter is None: return "Error: XML does not contain parameter."

                    sName = xParameter.findtext("name", "")
                    if sName is None: return "Error: XML does not contain parameter name."

                    sDesc = xParameter.findtext("desc", "")

                    sRequired = xParameter.get("required", "")
                    sPrompt = xParameter.get("prompt", "")
                    sEncrypt = xParameter.get("encrypt", "")
                    sMaxLength = xParameter.get("maxlength", "")
                    sMaxValue = xParameter.get("maxvalue", "")
                    sMinLength = xParameter.get("minlength", "")
                    sMinValue = xParameter.get("minvalue", "")
                    sConstraint = xParameter.get("constraint", "")
                    sConstraintMsg = xParameter.get("constraint_msg", "")


                    xValues = xParameter.find("values")
                    if xValues is not None:
                        sPresentAs = xValues.get("present_as", "")

                        i = 0
                        xVals = xValues.findall("value")
                        for xVal in xVals:
                            # since we can delete each item from the page it needs a unique id.
                            sPID = "pv" + catocommon.new_guid()

                            sValue = (xVal.text if xVal.text else "")
                            sObscuredValue = ""
                            
                            if catocommon.is_true(sEncrypt):
                                #  1) obscure the ENCRYPTED value and make it safe to be an html attribute
                                #  2) return some stars so the user will know a value is there.
                                sObscuredValue = "oev=\"" + uiCommon.packJSON(sValue) + "\""
                                sValue = ("" if not sValue else "********")

                            sValuesHTML += "<div id=\"" + sPID + "\">" \
                                "<textarea class=\"param_edit_value\" rows=\"1\" " + sObscuredValue + ">" + sValue + "</textarea>"

                            if i > 0:
                                sHideDel = ("dropdown" if sPresentAs == "list" or sPresentAs == "dropdown" else " hidden")
                                sValuesHTML += " <span class=\"ui-icon ui-icon-close forceinline param_edit_value_remove_btn pointer " + sHideDel + "\" remove_id=\"" + sPID + "\"></span>"

                            sValuesHTML += "</div>"

                            i += 1
                    else:
                        # if, when getting the parameter, there are no values... add one.  We don't want a parameter with no values
                        # AND - no remove button on this only value
                        sValuesHTML += "<div id=\"pv" + catocommon.new_guid() + "\">" \
                            "<textarea class=\"param_edit_value\" rows=\"1\"></textarea></div>"
                else:
                    uiCommon.log("Unable to get parameter details. Not found.")
            else:
                # if, when getting the parameter, there are no values... add one.  We don't want a parameter with no values
                # AND - no remove button on this only value
                sValuesHTML += "<div id=\"pv" + catocommon.new_guid() + "\">" \
                    "<textarea class=\"param_edit_value\" rows=\"1\"></textarea></div>"

            # this draws no matter what, if it's empty it's just an add dialog
            sHTML = ""

            sHTML += "Name: <input type=\"text\" class=\"w95pct\" id=\"param_edit_name\" validate_as=\"variable\" value=\"" + sName + "\" />"

            sHTML += "Options:<div class=\"param_edit_options\">"
            sHTML += "<span class=\"ui-widget-content ui-corner-all param_edit_option\"><input type=\"checkbox\" id=\"param_edit_required\"" + ("checked=\"checked\"" if sRequired == "true" else "") + " /> <label for=\"param_edit_required\">Required?</label></span>"
            sHTML += "<span class=\"ui-widget-content ui-corner-all param_edit_option\"><input type=\"checkbox\" id=\"param_edit_prompt\"" + ("checked=\"checked\"" if sPrompt == "true" else "") + " /> <label for=\"param_edit_prompt\">Prompt?</label></span>"
            sHTML += "<span class=\"ui-widget-content ui-corner-all param_edit_option\"><input type=\"checkbox\" id=\"param_edit_encrypt\"" + ("checked=\"checked\"" if sEncrypt == "true" else "") + " /> <label for=\"param_edit_encrypt\">Encrypt?</label></span>"

            sHTML += "<hr />"

            sHTML += "Min / Max Length: <input type=\"text\" class=\"w25px\" id=\"param_edit_minlength\"" \
                " validate_as=\"posint\" value=\"" + sMinLength + "\" /> / " \
                " <input type=\"text\" class=\"w25px\" id=\"param_edit_maxlength\"" \
                " validate_as=\"posint\" value=\"" + sMaxLength + "\" />" \
                "<br />"
            sHTML += "Min / Max Value: <input type=\"text\" class=\"w25px\" id=\"param_edit_minvalue\"" \
                " validate_as=\"number\" value=\"" + sMinValue + "\" /> / " \
                " <input type=\"text\" class=\"w25px\" id=\"param_edit_maxvalue\"" \
                " validate_as=\"number\" value=\"" + sMaxValue + "\" />" \
                "<br />"
            sHTML += "Constraint: <input type=\"text\" class=\"w95pct\" id=\"param_edit_constraint\"" \
                " value=\"" + sConstraint + "\" /><br />"
            sHTML += "Constraint Help: <input type=\"text\" class=\"w95pct\" id=\"param_edit_constraint_msg\"" \
                " value=\"" + sConstraintMsg + "\" /><br />"

            sHTML += "</div>"

            sHTML += "<br />Description: <br /><textarea id=\"param_edit_desc\" rows=\"2\">" + sDesc + "</textarea>"

            sHTML += "<div id=\"param_edit_values\">Values:<br />"
            sHTML += "Present As: <select id=\"param_edit_present_as\">"
            sHTML += "<option value=\"value\"" + ("selected=\"selected\"" if sPresentAs == "value" else "") + ">Value</option>"
            sHTML += "<option value=\"list\"" + ("selected=\"selected\"" if sPresentAs == "list" else "") + ">List</option>"
            sHTML += "<option value=\"dropdown\"" + ("selected=\"selected\"" if sPresentAs == "dropdown" else "") + ">Dropdown</option>"
            sHTML += "</select>"

            sHTML += "<hr />" + sValuesHTML + "</div>"

            # if it's not available for this presentation type, it will get the "hidden" class but still be drawn
            sHideAdd = ("" if sPresentAs == "list" or sPresentAs == "dropdown" else " hidden")
            sHTML += "<div id=\"param_edit_value_add_btn\" class=\"pointer " + sHideAdd + "\">" \
                "<img title=\"Add Another\" alt=\"\" src=\"static/images/icons/edit_add.png\" style=\"width: 10px;" \
                "   height: 10px;\" />( click to add a value )</div>"

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmDeleteTaskParam(self):
        try:
            sType = uiCommon.getAjaxArg("sType")
            sID = uiCommon.getAjaxArg("sID")
            sParamID = uiCommon.getAjaxArg("sParamID")
    
            sTable = ""
    
            if sType == "ecosystem":
                sTable = "ecosystem"
            elif sType == "task":
                sTable = "task"
    
            if sParamID and uiCommon.IsGUID(sID):
                #  need the name and values for logging
                sXML = ""
    
                # ALL OF THIS is just for logging ...
                sSQL = "select parameter_xml" \
                    " from " + sTable + \
                    " where " + sType + "_id = '" + sID + "'"
    
                sXML = self.db.select_col_noexcep(sSQL)
                if self.db.error:
                    uiCommon.log("Unable to get parameter_xml.  " + self.db.error)
    
                if sXML != "":
                    xd = ET.fromstring(sXML)
                    if xd is None:
                        uiCommon.log("XML parameter data is invalid.")
    
                    sName = xd.findtext("parameter[@id='" + sParamID + "']/name", "")
                    sValues = xd.findtext("parameter[@id='" + sParamID + "']/values", "")
    
                    #  add security log
                    uiCommon.WriteObjectDeleteLog(uiGlobals.CatoObjectTypes.Parameter, "", sID, "")
    
                    if sType == "task":
                        uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, sID, "Deleted Parameter:[" + sName + "]", sValues)
                    if sType == "ecosystem":
                        uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Ecosystem, sID, "Deleted Parameter:[" + sName + "]", sValues)
    
    
                # Here's the real work ... do the whack
                uiCommon.RemoveNodeFromXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", "parameter[@id='" + sParamID + "']")
    
                return ""
            else:
                uiCommon.log("Invalid or missing Task or Parameter ID.")
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmUpdateTaskParam(self):
        try:
            sType = uiCommon.getAjaxArg("sType")
            sID = uiCommon.getAjaxArg("sID")
            sParamID = uiCommon.getAjaxArg("sParamID")
            sName = uiCommon.getAjaxArg("sName")
            sDesc = uiCommon.getAjaxArg("sDesc")
            sRequired = uiCommon.getAjaxArg("sRequired")
            sPrompt = uiCommon.getAjaxArg("sPrompt")
            sEncrypt = uiCommon.getAjaxArg("sEncrypt")
            sPresentAs = uiCommon.getAjaxArg("sPresentAs")
            sValues = uiCommon.getAjaxArg("sValues")
            sMinLength = uiCommon.getAjaxArg("sMinLength")
            sMaxLength = uiCommon.getAjaxArg("sMaxLength")
            sMinValue = uiCommon.getAjaxArg("sMinValue")
            sMaxValue = uiCommon.getAjaxArg("sMaxValue")
            sConstraint = uiCommon.getAjaxArg("sConstraint")
            sConstraintMsg = uiCommon.getAjaxArg("sConstraintMsg")

            if not uiCommon.IsGUID(sID):
                uiCommon.log("ERROR: Save Parameter - Invalid or missing ID.")

            # we encoded this in javascript before the ajax call.
            # the safest way to unencode it is to use the same javascript lib.
            # (sometimes the javascript and .net libs don't translate exactly, google it.)
            sDesc = uiCommon.unpackJSON(sDesc).strip()
            sConstraint = uiCommon.unpackJSON(sConstraint)
            sConstraintMsg = uiCommon.unpackJSON(sConstraintMsg).strip()
            
            # normalize and clean the values
            sRequired = ("true" if catocommon.is_true(sRequired) else "false")
            sPrompt = ("true" if catocommon.is_true(sPrompt) else "false")
            sEncrypt = ("true" if catocommon.is_true(sEncrypt) else "false")
            sName = sName.strip().replace("'", "''")


            sTable = ""
            sCurrentXML = ""
            sParameterXPath = "parameter[@id='" + sParamID + "']" #using this to keep the code below cleaner.

            if sType == "ecosystem":
                sTable = "ecosystem"
            elif sType == "task":
                sTable = "task"

            bParamAdd = False
            # bParamUpdate = false

            # if sParamID is empty, we are adding
            if not sParamID:
                sParamID = "p_" + catocommon.new_guid()
                sParameterXPath = "parameter[@id='" + sParamID + "']" # reset this if we had to get a new id


                # does the task already have parameters?
                sSQL = "select parameter_xml from " + sTable + " where " + sType + "_id = '" + sID + "'"
                sCurrentXML = self.db.select_col_noexcep(sSQL)
                if self.db.error:
                    uiCommon.log_nouser(self.db.error, 0)

                sAddXML = "<parameter id=\"" + sParamID + "\"" \
                    " required=\"" + sRequired + "\" prompt=\"" + sPrompt + "\" encrypt=\"" + sEncrypt + "\"" \
                    " minlength=\"" + sMinLength + "\" maxlength=\"" + sMaxLength + "\"" \
                    " minvalue=\"" + sMinValue + "\" maxvalue=\"" + sMaxValue + "\"" \
                    " constraint=\"" + sConstraint + "\" constraint_msg=\"" + sConstraintMsg + "\"" \
                    ">" \
                    "<name>" + sName + "</name>" \
                    "<desc>" + sDesc + "</desc>" \
                    "</parameter>"

                if not sCurrentXML:
                    # XML doesn't exist at all, add it to the record
                    sAddXML = "<parameters>" + sAddXML + "</parameters>"

                    sSQL = "update " + sTable + " set " \
                        " parameter_xml = '" + sAddXML + "'" \
                        " where " + sType + "_id = '" + sID + "'"

                    if not self.db.exec_db_noexcep(sSQL):
                        uiCommon.log_nouser(self.db.error, 0)

                    bParamAdd = True
                else:
                    # XML exists, add the node to it
                    uiCommon.AddNodeToXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", "", sAddXML)
                    bParamAdd = True
            else:
                # update the node values
                uiCommon.SetNodeValueinXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath + "/name", sName)
                uiCommon.SetNodeValueinXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath + "/desc", sDesc)
                # and the attributes
                uiCommon.SetNodeAttributeinXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath, "required", sRequired)
                uiCommon.SetNodeAttributeinXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath, "prompt", sPrompt)
                uiCommon.SetNodeAttributeinXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath, "encrypt", sEncrypt)
                uiCommon.SetNodeAttributeinXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath, "minlength", sMinLength)
                uiCommon.SetNodeAttributeinXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath, "maxlength", sMaxLength)
                uiCommon.SetNodeAttributeinXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath, "minvalue", sMinValue)
                uiCommon.SetNodeAttributeinXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath, "maxvalue", sMaxValue)
                uiCommon.SetNodeAttributeinXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath, "constraint", sConstraint)
                uiCommon.SetNodeAttributeinXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath, "constraint_msg", sConstraintMsg)

                bParamAdd = False


            #  not clean at all handling both tasks and ecosystems in the same method, but whatever.
            if bParamAdd:
                if sType == "task":
                    uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.Task, sID, "Parameter", "Added Parameter [%s]" % sName )
                if sType == "ecosystem":
                    uiCommon.WriteObjectAddLog(uiGlobals.CatoObjectTypes.Ecosystem, sID, "Parameter", "Added Parameter [%s]" % sName )
            else:
                #  would be a lot of trouble to add the from to, why is it needed you have each value in the log, just scroll back
                #  so just add a changed message to the log
                if sType == "task":
                    uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, sID, "Parameter", "Modified Parameter [%s]" % sName )
                if sType == "ecosystem":
                    uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Ecosystem, sID, "Parameter", "Modified Parameter [%s]" % sName )

            # update the values
            aValues = sValues.split("|")
            sValueXML = ""

            for sVal in aValues:
                sReadyValue = ""
                
                # if encrypt is true we MIGHT want to encrypt this value.
                # but it might simply be a resubmit of an existing value in which case we DON'T
                # if it has oev: as a prefix, it needs no additional work
                if catocommon.is_true(sEncrypt) and sVal:
                    if sVal.find("oev:") > -1:
                        sReadyValue = uiCommon.unpackJSON(sVal.replace("oev:", ""))
                    else:
                        sReadyValue = uiCommon.CatoEncrypt(uiCommon.unpackJSON(sVal))
                else:
                    sReadyValue = uiCommon.unpackJSON(sVal)
                    
                sValueXML += "<value id=\"pv_" + catocommon.new_guid() + "\">" + sReadyValue + "</value>"

            sValueXML = "<values present_as=\"" + sPresentAs + "\">" + sValueXML + "</values>"


            # whack-n-add
            uiCommon.RemoveNodeFromXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath + "/values")
            uiCommon.AddNodeToXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath, sValueXML)

            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetTaskRunLogDetails(self):
        try:
            sTaskInstance = str(uiCommon.getAjaxArg("sTaskInstance"))
            sTaskID = uiCommon.getAjaxArg("sTaskID")
            sAssetID = uiCommon.getAjaxArg("sAssetID")
            
            # we're building a json object to be returned, so we'll start with a dictionary
            output = {}

            # different things happen depending on the page args

            # if an instance was provided... it overrides all other args 
            # otherwise we need to figure out which instance we want
            if sTaskInstance == "":
                if uiCommon.IsGUID(sTaskID):
                    sSQL = "select max(task_instance) from tv_task_instance where task_id = '" + sTaskID + "'"

                    if uiCommon.IsGUID(sAssetID):
                        sSQL += " and asset_id = '" + sAssetID + "'"

                    sTaskInstance = str(self.db.select_col_noexcep(sSQL))
                    if self.db.error:
                        uiCommon.log("Unable to get task_instance from task/asset id.  " + self.db.error)
            
            if sTaskInstance:
                # the task instance must be a number, die if it isn't
                try:
                    int(sTaskInstance)
                except:
                    return "Task Instance must be an integer. [%s]." % (sTaskInstance)
                
                # not doing the permission check yet
                """
                # PERMISSION CHECK
                # now... kick out if the user isn't allowed to see this page

                # it's a little backwards... IsPageAllowed will kick out this page for users...
                # so don't bother to check that if we can determine the user has permission by 
                # a group association to this task
                sOTID = ""
                stiSQL = "select t.original_task_id" \
                   " from tv_task_instance ti join task t on ti.task_id = t.task_id" \
                   " where ti.task_instance = '" + sTaskInstance + "'"

                sOTID = self.db.select_col_noexcep(sSQL)
                if self.db.error:
                    uiCommon.log("Unable to get original_task_id for task instance.  " + self.db.error)

                # now we know the ID, see if we are grouped with it
                # this will kick out if they DONT match tags and they AREN'T in a role with sufficient privileges
                if !uiCommon.UserAndObjectTagsMatch(sOTID, 3)) uiCommon.IsPageAllowed("You do not have permission to view this Task.":
                # END PERMISSION CHECK
                """

                # all good... continue...
                output["task_instance"] = sTaskInstance
                
                sSQL = "select ti.task_instance, ti.task_id, '' as asset_id, ti.task_status, ti.submitted_by_instance, " \
                    " ti.submitted_dt, ti.started_dt, ti.completed_dt, ti.ce_node, ti.pid, ti.debug_level," \
                    " t.task_name, t.version, '' as asset_name, u.full_name," \
                    " ar.app_instance, ar.platform, ar.hostname," \
                    " t.concurrent_instances, t.queue_depth," \
                    " ti.ecosystem_id, d.ecosystem_name, ti.account_id, ca.account_name" \
                    " from tv_task_instance ti" \
                    " join task t on ti.task_id = t.task_id" \
                    " left outer join users u on ti.submitted_by = u.user_id" \
                    " left outer join tv_application_registry ar on ti.ce_node = ar.id" \
                    " left outer join cloud_account ca on ti.account_id = ca.account_id" \
                    " left outer join ecosystem d on ti.ecosystem_id = d.ecosystem_id" \
                    " where task_instance = " + sTaskInstance

                dr = self.db.select_row_dict(sSQL)
                if self.db.error:
                    uiCommon.log("Unable to get instance details for task instance.  " + self.db.error)

                if dr is not None:
                    output["task_id"] = dr["task_id"]
                    output["asset_id"] = (dr["asset_id"] if dr["asset_id"] else "")
                    output["debug_level"] = (dr["debug_level"] if dr["debug_level"] else "")

                    output["task_name_label"] = dr["task_name"] + " - Version " + str(dr["version"])
                    output["task_status"] = dr["task_status"]
                    output["asset_name"] = ("N/A" if not dr["asset_name"] else dr["asset_name"])
                    output["submitted_dt"] = ("" if not dr["submitted_dt"] else str(dr["submitted_dt"]))
                    output["started_dt"] = ("" if not dr["started_dt"] else str(dr["started_dt"]))
                    output["completed_dt"] = ("" if not dr["completed_dt"] else str(dr["completed_dt"]))
                    output["ce_node"] = ("" if not dr["ce_node"] else str(dr["app_instance"]) + " (" + dr["platform"] + ")")
                    output["pid"] = ("" if not dr["pid"] else str(dr["pid"]))

                    output["submitted_by_instance"] = ("" if not dr["submitted_by_instance"] else dr["submitted_by_instance"])

                    output["ecosystem_id"] = (dr["ecosystem_id"] if dr["ecosystem_id"] else "")
                    output["ecosystem_name"] = (dr["ecosystem_name"] if dr["ecosystem_name"] else "")
                    output["account_id"] = (dr["account_id"] if dr["account_id"] else "")
                    output["account_name"] = (dr["account_name"] if dr["account_name"] else "")

                    output["submitted_by"] = (dr["full_name"] if dr["full_name"] else "Scheduler")

                    # we should return some indication of whether or not the user can do
                    # certain functions.
                    """
                    # superusers AND those tagged with this Task can see the stop and resubmit button
                    if uiCommon.UserIsInRole("Developer") or uiCommon.UserIsInRole("Administrator") or uiCommon.UserAndObjectTagsMatch(dr["original_task_id"], 3):
                        phResubmit.Visible = true
                        phCancel.Visible = true
                    else:
                        phResubmit.Visible = false
                        phCancel.Visible = false
                    """



                    # if THIS instance is 'active', show additional warning info on the resubmit confirmation.
                    # and if it's not, don't show the "cancel" button
                    if dr["task_status"].lower() in ["processing","queued","submitted","pending","aborting","queued","staged"]:
                        output["resubmit_message"] = "This Task is currently active.  You have requested to start another instance."
                    else:
                        output["allow_cancel"] = "false"


                    # check for OTHER active instances
                    sSQL = "select count(*) from tv_task_instance where task_id = '" + dr["task_id"] + "'" \
                        " and task_instance <> '" + sTaskInstance + "'" \
                        " and task_status in ('processing','submitted','pending','aborting','queued','staged')"
                    iActiveCount = self.db.select_col_noexcep(sSQL)
                    if self.db.error:
                        uiCommon.log("Unable to get active instance count.  " + self.db.error)


                    # and hide the resubmit button if we're over the limit
                    # if active < concurrent do nothing
                    # if active >= concurrent but there's room in the queue, change the message
                    # if this one would pop the queue, hide the button
                    aOtherInstances = []
                    if iActiveCount > 0:
                        try:
                            iConcurrent = int(dr["concurrent_instances"])
                        except:
                            iConcurrent = 0
    
                        try:
                            iQueueDepth = int(dr["queue_depth"])
                        except:
                            iQueueDepth = 0
    
                        if iConcurrent + iQueueDepth > 0:
                            if iActiveCount >= iConcurrent and (iActiveCount + 1) <= iQueueDepth:
                                output["resubmit_message"] = "The maximum concurrent instances for this Task are running.  This request will be queued."
                            else:
                                output["allow_resubmit"] = "false"

                        # neato... show the user a list of all the other instances!
                        sSQL = "select task_instance, task_status from tv_task_instance" \
                            " where task_id = '" + dr["task_id"] + "'" \
                            " and task_instance <> '" + sTaskInstance + "'" \
                            " and task_status in ('processing','submitted','pending','aborting','queued','staged')" \
                            " order by task_status"

                        dt = self.db.select_all_dict(sSQL)
                        if self.db.error:
                            uiCommon.log_nouser(self.db.error, 0)

                        # build a list of the other instances
                        for dr in dt:
                            aOtherInstances.append((dr["task_instance"], dr["task_status"]))

                        output["other_instances"] = aOtherInstances
                    
                    # one last thing... does the logfile for this run exist on this server?
                    if uiGlobals.config.has_key("logfiles"):
                        logdir = uiGlobals.config["logfiles"]
                        if os.path.exists( r"%s/ce/%s.log" % (logdir, sTaskInstance) ):
                            output["logfile_name"] = "%s/ce/%s.log" % (logdir, sTaskInstance)
                    
                    # all done, serialize our output dictionary
                    return json.dumps(output)

                else:
                    return "{\"error\":\"Did not find any data for Instance [%s].\"}" % (sTaskInstance)
                
            #if we get here, there is just no data... maybe it never ran.
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetTaskRunLog(self):
        sTaskInstance = uiCommon.getAjaxArg("sTaskInstance")
        sRows = uiCommon.getAjaxArg("sRows")

        # OK, here's something neat.
        # the TE *might* write a row in the log table with some xml content for a "results summary".
        # we don't wanna hardcode too much, so we'll just inspect each log row looking for a flag.
        # if we find it, we'll hold on to the data until the end and display it nicely instead of the log.
        sResultSummary = ""
        
        try:
            if not sTaskInstance:
                return "{\"log\" : \"Unable to get log - no Instance passed to wmGetTaskRunLog.\"}"
            
            sLimitClause = " limit 100"

            if sRows:
                if sRows == "all":
                    sLimitClause = ""
                else:
                    sLimitClause = " limit " + sRows

            sSQL = "select til.task_instance, til.entered_dt, til.connection_name, til.log," \
                " til.step_id, s.step_order, s.function_name, s.function_name as function_label, s.codeblock_name, " \
                " til.command_text," \
                " '' as variable_name,  '' as variable_value, " \
                " case when length(til.log) > 256 then 1 else 0 end as large_text" \
                " from task_instance_log til" \
                " left outer join task_step s on til.step_id = s.step_id" \
                " where til.task_instance = " + sTaskInstance + \
                " order by til.id" + sLimitClause

            dt = self.db.select_all_dict(sSQL)
            if self.db.error:
                uiCommon.log_nouser(self.db.error, 0)

            sLog = ""
            sSummary = ""

            if dt:
                sLog += "<ul class=\"log\">\n"
                sThisStepID = ""
                sPrevStepID = ""

                for dr in dt:
                    # first, check if this row contains the 'results summary'
                    # this will be indicated by the text "Results Summary" in the *command* field.
                    if dr["command_text"]:
                        if dr["command_text"] == "result_summary":
                            sResultSummary = dr["log"]
                            continue
                    
                    sThisStepID = dr["step_id"]




                    # start a new list item and header only if we are moving on to a different step.
                    if sPrevStepID != sThisStepID:
                        # this is backwards, we are closing the previous loops list item
                        # only if this loop is a different step_id than the last.
                        # but not on the first loop (sPrevStepID = "")
                        if sPrevStepID != "":
                            sLog += "</li>\n"

                        # new item
                        sLog += "<li class=\"ui-widget-content ui-corner-bottom log_item\">\n"
                        sLog += "    <div class=\"log_header ui-state-default ui-widget-header\">\n"
                        if dr["function_label"]:
                            try:
                                iStepOrder = int(dr["step_order"])
                            except:
                                iStepOrder = 0
                                
                            if iStepOrder:
                                sLog += "[" + dr["codeblock_name"] + " - " + dr["function_label"] + " - Step " + str(iStepOrder) + "]\n"
                            else:
                                sLog += "[Action - " + dr["function_label"]

                        sLog += "At: [" + str(dr["entered_dt"]) + "]\n"

                        if dr["connection_name"]:
                            sLog += "On Connection: [" + dr["connection_name"] + "]\n"


                        sLog += "    </div>\n"

                    # detail section
                    sLog += "<div class=\"log_detail\">\n"

                    # it might have a command
                    if dr["command_text"].strip():
                        sLog += "<div class=\"log_command ui-widget-content ui-corner-all hidden\">\n"

                        # the command text might hold special information we want to display differently
                        if "run_task" in dr["command_text"]:
                            sInstance = dr["command_text"].replace("run_task ", "")
                            sLog += "<span class=\"link\" onclick=\"location.href='taskRunLog?task_instance=" + sInstance + "';\">Jump to Task</span>"
                        else:
                            sLog += uiCommon.FixBreaks(uiCommon.SafeHTML(dr["command_text"]))
                        sLog += "</div>\n"


                    # it might be a log entry:
                    if dr["log"].strip():
                        # commented out to save space
                        # sLog += "Results:\n"
                        sLog += "    <div class=\"log_results ui-widget-content ui-corner-all\">\n"
                        sLog += uiCommon.FixBreaks(uiCommon.SafeHTML(dr["log"]))
                        sLog += "    </div>\n"


#  VARIABLE STUFF IS NOT YET ACTIVE
#                         # it could be a variable:value entry:
#                         if !dr["variable_name"].Equals(System.DBNull.Value):
#                         #                             if dr["variable_name"].strip()):
#                             #                                 sLog += "Variable:\n"
#                                 sLog += "<div class=\"log_variable_name ui-widget-content ui-corner-all\">\n"
#                                 sLog += dr["variable_name"]
#                                 sLog += "</div>\n"
#                                 sLog += "Set To:\n"
#                                 sLog += "<div class=\"log_variable_value ui-widget-content ui-corner-all\">\n"
#                                 sLog += dr["variable_value"]
#                                 sLog += "</div>\n"
#                             }
#                         }

                    
                    # end detail
                    sLog += "</div>\n"

                    sPrevStepID = sThisStepID

                # the last one get's closed no matter what
                sLog += "</li>\n"
                sLog += "</ul>\n"

                try:                         
                    # almost done... if there is a Result Summary ... display that.
                    if sResultSummary:
                        xdSummary = ET.fromstring(sResultSummary)
                        if xdSummary is not None:
                            for item in xdSummary.findall("items/item"):
                                name = item.findtext("name", "")
                                detail = item.findtext("detail", "")
                                sSummary += "<div class='result_summary_item_name'>%s</div>" % name
                                sSummary += "<div class='result_summary_item_detail ui-widget-content ui-corner-all'>%s</div>" % detail    
                except Exception:
                    uiCommon.log_nouser(traceback.format_exc(), 0)
            
            return "{\"log\" : \"%s\", \"summary\" : \"%s\"}" % (uiCommon.packJSON(sLog), uiCommon.packJSON(sSummary))

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return ""

    def wmGetTaskLogfile(self):
        try:
            instance = uiCommon.getAjaxArg("sTaskInstance")
            logfile = ""
            if instance and uiGlobals.config.has_key("logfiles"):
                logdir = uiGlobals.config["logfiles"]
                logfile = "%s/ce/%s.log" % (logdir, instance)
                if os.path.exists(logfile):
                    if os.path.getsize(logfile) > 20971520: # 20 meg is a pretty big logfile for the browser.
                        return uiCommon.packJSON("Logfile is too big to view in a web browser.")
                    with open(logfile, 'r') as f:
                        if f:
                            return uiCommon.packJSON(uiCommon.SafeHTML(f.read()))
            
            return uiCommon.packJSON("Unable to read logfile. [%s]" % logfile)
        except Exception, ex:
            return ex.__str__()
            
    def wmExportTasks(self):
        try:
            sTaskArray = uiCommon.getAjaxArg("sTaskArray")
            if len(sTaskArray) < 36:
                return "{\"info\" : \"Unable to delete - no selection.\"}"
    
            otids = sTaskArray.split(",")
            
            xml = ""
            for otid in otids:
                # get the task
                t = task.Task()
                t.FromOriginalIDVersion(otid)
                if t:
                    xml += t.AsXML()
            
            xml = "<tasks>%s</tasks>" % xml

            # what are we gonna call this file?
            seconds = str(int(time.time()))
            filename = "%s_%s.csk" % (t.Name.replace(" ","").replace("/",""), seconds)
            with open("%s/temp/%s" % (uiGlobals.web_root, filename), 'w') as f_out:
                if not f_out:
                    print "ERROR: unable to write task export file."
                f_out.write(xml)
                
            return "{\"export_file\" : \"%s\"}" % filename
        except Exception, ex:
            return ex.__str__()
            
    def wmGetTaskStatusCounts(self):
        try:
            # we're building a json object to be returned, so we'll start with a dictionary
            output = {}
            sSQL = "select Processing, Staged, Pending, Submitted, Aborting, Queued, AllStatuses," \
                    "(Processing + Pending + Submitted + Aborting + Queued + Staged) as TotalActive," \
                    "Cancelled, Completed, Errored, (Cancelled + Completed + Errored) as TotalComplete " \
                    "from (select count(case when task_status = 'Processing' then 1 end) as Processing," \
                    "count(case when task_status = 'Pending' then 1 end) as Pending," \
                    "count(case when task_status = 'Submitted' then 1 end) as Submitted," \
                    "count(case when task_status = 'Aborting' then 1 end) as Aborting," \
                    "count(case when task_status = 'Queued' then 1 end) as Queued," \
                    "count(case when task_status = 'Cancelled' then 1 end) as Cancelled," \
                    "count(case when task_status = 'Completed' then 1 end) as Completed," \
                    "count(case when task_status = 'Staged' then 1 end) as Staged," \
                    "count(case when task_status = 'Error' then 1 end) as Errored, " \
                    "count(*) as AllStatuses " \
                    "from tv_task_instance) foo"

            dr = self.db.select_row_dict(sSQL)
            if self.db.error:
                uiCommon.log("Unable to get instance details for task instance.  " + self.db.error)

            if dr is not None:
                output["Processing"] = dr["Processing"]
                output["Submitted"] = dr["Submitted"]
                output["Staged"] = dr["Staged"]
                output["Aborting"] = dr["Aborting"]
                output["Pending"] = dr["Pending"]
                output["Queued"] = dr["Queued"]
                output["TotalActive"] = dr["TotalActive"]
                output["Cancelled"] = dr["Cancelled"]
                output["Completed"] = dr["Completed"]
                output["Errored"] = dr["Errored"]
                output["TotalComplete"] = dr["TotalComplete"]
                output["AllStatuses"] = dr["AllStatuses"]
                
                # all done, serialize our output dictionary
                return json.dumps(output)

            #if we get here, there is just no data... 
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetTaskVarPickerPopup(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")

        try:
            if uiCommon.IsGUID(sTaskID):
                sHTML = ""

                # VARIABLES
                sSQL = "select distinct var_name from (" \
                    " select ExtractValue(function_xml, '//step_variables/variable/name[1]') as var_name" \
                    " from task_step" \
                    " where task_id = '" + sTaskID + "'" \
                    " UNION" \
                    " select ExtractValue(function_xml, '//function/counter[1]') as var_name" \
                    " from task_step" \
                    " where task_id = '" + sTaskID + "'" \
                    " and function_name = 'loop'" \
                    " UNION" \
                    " select ExtractValue(function_xml, '//variable/name[1]') as var_name" \
                    " from task_step" \
                    " where task_id = '" + sTaskID + "'" \
                    " and function_name in ('set_variable','substring')" \
                    " ) foo" \
                    " where ifnull(var_name,'') <> ''" \
                    " order by var_name"

                #lVars is a list of all the variables we can pick from
                # the value is the var "name"
                lVars = []

                dtStupidVars = self.db.select_all_dict(sSQL)
                if self.db.error:
                    uiCommon.log("Unable to get variables for task." + self.db.error)

                if dtStupidVars is not None:
                    for drStupidVars in dtStupidVars:
                        aVars = drStupidVars["var_name"].split(' ')
                        for sVar in aVars:
                            lVars.append(str(sVar))

                # sort it
                lVars.sort()

                # Finally, we have a table with all the vars!
                if lVars:
                    sHTML += "<div target=\"var_picker_group_vars\" class=\"ui-widget-content ui-corner-all value_picker_group\"><img alt=\"\" src=\"static/images/icons/expand.png\" style=\"width:12px;height:12px;\" /> Variables</div>"
                    sHTML += "<div id=\"var_picker_group_vars\" class=\"hidden\">"

                    for thisvar in lVars:
                        sHTML += "<div class=\"ui-widget-content ui-corner-all value_picker_value\">%s</div>" % thisvar

                    sHTML += "</div>"

                # PARAMETERS
                sSQL = "select parameter_xml from task where task_id = '" + sTaskID + "'"

                sParameterXML = self.db.select_col_noexcep(sSQL)
                if self.db.error:
                    uiCommon.log_nouser(self.db.error, 0)

                if sParameterXML:
                    xParams = ET.fromstring(sParameterXML)
                    if xParams is None:
                        uiCommon.log("Parameter XML data for task [" + sTaskID + "] is invalid.")
                    else:
                        sHTML += "<div target=\"var_picker_group_params\" class=\"ui-widget-content ui-corner-all value_picker_group\"><img alt=\"\" src=\"static/images/icons/expand.png\" style=\"width:12px;height:12px;\" /> Parameters</div>"
                        sHTML += "<div id=\"var_picker_group_params\" class=\"hidden\">"

                        for xParameter in xParams.findall("parameter"):
                            sHTML += "<div class=\"ui-widget-content ui-corner-all value_picker_value\">" + xParameter.findtext("name", "") + "</div>"

                    sHTML += "</div>"

                
                # "Global" Variables
                sHTML += "<div target=\"var_picker_group_globals\" class=\"ui-widget-content ui-corner-all value_picker_group\"><img alt=\"\" src=\"static/images/icons/expand.png\" style=\"width:12px;height:12px;\" /> Globals</div>"
                sHTML += "<div id=\"var_picker_group_globals\" class=\"hidden\">"

                lItems = ["_ASSET","_SUBMITTED_BY","_SUBMITTED_BY_EMAIL","_TASK_INSTANCE","_TASK_NAME","_TASK_VERSION","_DATE"]
                for gvar in lItems:
                    sHTML += "<div class=\"ui-widget-content ui-corner-all value_picker_value\">%s</div>" % gvar

                sHTML += "</div>"

                # all done
                return sHTML
            else:
                uiCommon.log("Unable to get variables for task. Missing or invalid task_id.")

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetTaskCodeblockPicker(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sStepID = uiCommon.getAjaxArg("sStepID")

        try:
            if uiCommon.IsGUID(sTaskID):
                sSQL = "select codeblock_name from task_codeblock where task_id = '" + sTaskID + "'" \
                    " and codeblock_name not in (select codeblock_name from task_step where step_id = '" + sStepID + "')" \
                    " order by codeblock_name"

                dt = self.db.select_all_dict(sSQL)
                if self.db.error:
                    uiCommon.log("Unable to get codeblocks for task." + self.db.error)

                sHTML = ""

                for dr in dt:
                    sHTML += "<div class=\"ui-widget-content ui-corner-all value_picker_value\">" + dr["codeblock_name"] + "</div>"

                return sHTML
            else:
                uiCommon.log("Unable to get codeblocks for task. Missing or invalid task_id.")

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmGetTaskConnections(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")

        try:
            if uiCommon.IsGUID(sTaskID):
                sSQL = "select conn_name from (" \
                    "select distinct ExtractValue(function_xml, '//conn_name[1]') as conn_name" \
                    " from task_step" \
                        " where function_name = 'new_connection'" \
                        " and task_id = '" + sTaskID + "'" \
                        " ) foo" \
                    " where ifnull(conn_name,'') <> ''" \
                    " order by conn_name"

                dt = self.db.select_all_dict(sSQL)
                if self.db.error:
                    uiCommon.log("Unable to get connections for task." + self.db.error)

                sHTML = ""

                if dt:
                    for dr in dt:
                        sHTML += "<div class=\"ui-widget-content ui-corner-all value_picker_value\">" + dr["conn_name"] + "</div>"

                return sHTML
            else:
                uiCommon.log("Unable to get connections for task. Missing or invalid task_id.")

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            
    def wmStopTask(self):
        try:
            sInstance = uiCommon.getAjaxArg("sInstance")

            if sInstance != "":
                sSQL = "update task_instance set task_status = 'Aborting'" \
                    " where task_instance = '" + sInstance + "'" \
                    " and task_status in ('Processing');"

                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to stop task instance [" + sInstance + "]." + self.db.error)

                sSQL = "update task_instance set task_status = 'Cancelled'" \
                    " where task_instance = '" + sInstance + "'" \
                    " and task_status in ('Submitted','Queued','Staged')"

                if not self.db.exec_db_noexcep(sSQL):
                    uiCommon.log("Unable to stop task instance [" + sInstance + "]." + self.db.error)

                return ""
            else:
                uiCommon.log("Unable to stop task. Missing or invalid task_instance.")

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmApproveTask(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sMakeDefault = uiCommon.getAjaxArg("sMakeDefault")

        try:
            sUserID = uiCommon.GetSessionUserID()

            if uiCommon.IsGUID(sTaskID) and uiCommon.IsGUID(sUserID):

                # check to see if this is the first task to be approved.
                # if it is, we will make it default.
                sSQL = "select count(*) from task" \
                    " where original_task_id = " \
                    " (select original_task_id from task where task_id = '" + sTaskID + "')" \
                    " and task_status = 'Approved'"

                iCount = self.db.select_col_noexcep(sSQL)
                if not iCount:
                    sMakeDefault = "1"

                # flag all the other tasks as not default if this one is meant to be
                if sMakeDefault == "1":
                    sSQL = "update task set" \
                        " default_version = 0" \
                        " where original_task_id =" \
                        " (select original_task_id from (select original_task_id from task where task_id = '" + sTaskID + "') as x)"
                    if not self.db.tran_exec_noexcep(sSQL):
                        uiCommon.log("Unable to update task [" + sTaskID + "]." + self.db.error)

                    sSQL = "update task set" \
                    " task_status = 'Approved'," \
                    " default_version = 1" \
                    " where task_id = '" + sTaskID + "'"
                else:
                    sSQL = "update task set" \
                        " task_status = 'Approved'" \
                        " where task_id = '" + sTaskID + "'"

                sSQL = sSQL
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log("Unable to update task [" + sTaskID + "]." + self.db.error)

                self.db.tran_commit()

                uiCommon.WriteObjectPropertyChangeLog(uiGlobals.CatoObjectTypes.Task, sTaskID, "Status", "Development", "Approved")
                if sMakeDefault == "1":
                    uiCommon.WriteObjectChangeLog(uiGlobals.CatoObjectTypes.Task, sTaskID, "Default", "Set as Default Version.")

            else:
                uiCommon.log("Unable to update task. Missing or invalid task id. [" + sTaskID + "]")

        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmFnNodeArrayAdd(self):
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            sFunctionName = uiCommon.getAjaxArg("sFunctionName")
            sTemplateXPath = uiCommon.getAjaxArg("sTemplateXPath")
            sAddTo = uiCommon.getAjaxArg("sAddTo")

            func = uiCommon.GetTaskFunction(sFunctionName)
            if not func:
                uiCommon.log("Unable to get a Function definition for name [%s]" % sFunctionName)
            
            # validate it
            # parse the doc from the table
            xd = func.TemplateXDoc
            print ET.tostring(xd)
            if xd is None:
                uiCommon.log("Unable to get Function Template.")
            
            # get the original "group" node from the xml_template
            # here's the rub ... the "sGroupNode" from the actual command instance might have xpath indexes > 1... 
            # but the template DOESN'T!
            # So, I'm regexing any [#] on the back to a [1]... that value should be in the template.
            
            rx = re.compile("\[[0-9]*\]")
            sTemplateNode = re.sub(rx, "[1]", sTemplateXPath)
            
            # this is a little weird... if the sTemplateNode is empty, or is "function"...
            # that means we want the root node (everything)
            if sTemplateNode == "" or sTemplateNode == "function":
                xGroupNode = xd
            else:
                xGroupNode = xd.find(sTemplateNode)
            
            if xGroupNode is None:
                uiCommon.log("Error: Unable to add.  Source node not found in Template XML. [" + sTemplateNode + "]")
            
            # yeah, this wicked single line aggregates the value of each node
            sNewXML = "".join(ET.tostring(x) for x in list(xGroupNode))
            uiCommon.log(sNewXML, 4)
            
            if sNewXML != "":
                ST.AddToCommandXML(sStepID, sAddTo, sNewXML.strip())
                # uiCommon.AddNodeToXMLColumn("task_step", "function_xml", "step_id = '" + sStepID + "'", sTemplateXPath, sNewXML)

            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmRemoveNodeFromStep(self):
        # NOTE: this function is capable of removing data from any command.
        # it is not failsafe - it simply take a path and removes the node.
        try:
            sStepID = uiCommon.getAjaxArg("sStepID")
            sRemovePath = uiCommon.getAjaxArg("sRemovePath")
            if sRemovePath:
                ST.RemoveFromCommandXML(sStepID, sRemovePath)
                return ""
            else:
                uiCommon.log("Unable to modify step. Invalid remove path.")
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
