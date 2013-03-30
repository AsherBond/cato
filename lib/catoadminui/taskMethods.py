
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
import traceback
import json
import time
import cgi

try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

from catoui import uiCommon
from catolog import catolog
from catocommon import catocommon
from catotask import task, stepTemplates as ST
from catoconfig import catoconfig
from catoerrors import WebmethodInfo

# task-centric web methods

class taskMethods:
    db = None

    def wmGetTasksTable(self):
        sHTML = ""
        pager_html = ""
        sFilter = uiCommon.getAjaxArg("sSearch")
        sPage = uiCommon.getAjaxArg("sPage")
        maxrows = 50
        tasks = task.Tasks(sFilter)
        if tasks.rows:
            # before we break the results into pages, we first filter it by tag
            # THIS IS DEPENDANT on the task results containing a list of tags for each task.
            allowedrows = uiCommon.FilterSetByTag(tasks.rows)
                           
            # now we have a filtered set... proceed...
            start, end, pager_html = uiCommon.GetPager(len(allowedrows), maxrows, sPage)

            for row in allowedrows[start:end]:
                sHTML += '<tr task_id="%s" status="%s">' % (row["ID"], row["Status"])
                sHTML += '<td class="chkboxcolumn">'
                sHTML += '''<input type="checkbox" class="chkbox"
                    id="chk_%s" object_id=%s" tag="chk" />''' % (row["OriginalTaskID"], row["ID"])
                sHTML += "</td>"
                
                sHTML += '<td class="selectable">' + row["Code"] + '</td>'
                sHTML += '<td class="selectable">' + row["Name"] + '</td>'
                sHTML += '<td class="selectable">' + str(row["Version"]) + '</td>'
                sHTML += '<td class="selectable">' + row["Description"] + '</td>'
                sHTML += '<td class="selectable">' + row["Status"] + '</td>'
                sHTML += '<td class="selectable">' + str(row["Versions"]) + '</td>'
                
                sHTML += '</tr>'

        out = {}
        out["pager"] = uiCommon.packJSON(pager_html)
        out["rows"] = uiCommon.packJSON(sHTML)
        
        return catocommon.ObjectOutput.AsJSON(out)

    def wmGetTaskInstances(self):
        _filter = uiCommon.getAjaxArg("sSearch")
        status = uiCommon.getAjaxArg("sStatus")
        _from = uiCommon.getAjaxArg("sFrom", "")
        _to = uiCommon.getAjaxArg("sTo", "")
        num_records = uiCommon.getAjaxArg("sRecords", "200")
        
        sHTML = ""
        tasks = task.TaskInstances(sFilter=_filter,
                                   sStatus=status,
                                   sFrom=_from,
                                   sTo=_to,
                                   sRecords=num_records)
        if tasks.rows:
            for row in tasks.rows:
                task_label = "%s (%s)" % (row["TaskName"], str(row["Version"]))
                sHTML += "<tr style=\"font-size: .8em;\" task_instance=\"%s\">" % row["Instance"]
                
                sHTML += "<td class=\"selectable\">%s</td>" % row["Instance"]
                sHTML += "<td class=\"selectable\">%s</td>" % row["TaskCode"]
                sHTML += "<td class=\"selectable\">%s</td>" % task_label
                sHTML += "<td class=\"selectable\">%s</td>" % (row["AssetName"] if row["AssetName"] else "")
                sHTML += "<td class=\"selectable\">%s</td>" % row["Status"]
                sHTML += "<td class=\"selectable\">%s</td>" % row["StartedBy"]
                sHTML += "<td class=\"selectable\">%s</td>" % (row["CEName"] if row["CEName"] else "")
                sHTML += "<td class=\"selectable\">%s</td>" % str((row["ProcessID"] if row["ProcessID"] else ""))
                sHTML += "<td class=\"selectable\">%s</td>" % (row["ServiceInstanceLabel"] if row["ServiceInstanceLabel"] else "")
                sHTML += "<td class=\"selectable\">%s<br />%s</td>" % (
                    ("(s)&nbsp;%s" % row["SubmittedDate"].replace(" ", "&nbsp;") if row["SubmittedDate"] else ""),
                    ("(c)&nbsp;%s" % row["CompletedDate"].replace(" ", "&nbsp;") if row["CompletedDate"] else "")
                    )
                sHTML += "<td class=\"selectable\"><span task_id=\"%s\" class=\"ui-icon ui-icon-pencil pointer task_edit_btn\"></span></td>" % row["TaskID"]
                
                sHTML += "</tr>"

        return sHTML    

    def wmGetTask(self):
        sID = uiCommon.getAjaxArg("sTaskID")
        
        t = task.Task()
        sErr = t.FromID(sID, False, False)
        if sErr:
            uiCommon.log(sErr)
        if t:
            if t.ID:
                return t.AsJSON()
        
        # should not get here if all is well
        return json.dumps({"result":"fail", "error":"Failed to get Task details for Task ID [%s]." % sID})

    def wmTaskSetDefault(self):
        sID = uiCommon.getAjaxArg("sTaskID")
        task.Task.SetAsDefault(sID)
        return json.dumps({"result" : "success"})

    def wmGetTaskCodeFromID(self):
        sOriginalTaskID = uiCommon.getAjaxArg("sOriginalTaskID")

        if not catocommon.is_guid(sOriginalTaskID):
            raise Exception("Invalid or missing Task ID.")

            sSQL = "select task_code from task where original_task_id = %s and default_version = 1"
            sTaskCode = self.db.select_col(sSQL, sOriginalTaskID)
            return json.dumps({"code" : sTaskCode})
        return "{}"

    @staticmethod
    def IsTaskAllowed(task_id):
        # Tasks are a special case - permissions are done by the original_task_id
        db = catocommon.new_conn()
        sql = "select original_task_id from task where task_id = %s"
        otid = db.select_col_noexcep(sql, (task_id))
        if otid:
            return uiCommon.IsObjectAllowed(otid, catocommon.CatoObjectTypes.Task)
        else:
            uiCommon.log("Unable to find Task for permissions check using ID [%s]" % task_id)
            return False

    @staticmethod
    def GetTaskStatus(sTaskID):
        if not catocommon.is_guid(sTaskID):
            uiCommon.log("Invalid or missing Task ID.")

        db = catocommon.new_conn()
        sSQL = "select task_status from task where task_id = '%s'" % sTaskID
        sStatus = db.select_col(sSQL)
        db.close()
        return sStatus


    def wmGetTaskVersionsDropdown(self):
        sOriginalTaskID = uiCommon.getAjaxArg("sOriginalTaskID")
        sbString = []
        sSQL = """select task_id, version, default_version
            from task
            where original_task_id = %s
            order by default_version desc, version"""
        dt = self.db.select_all_dict(sSQL, (sOriginalTaskID))
        if dt:
            for dr in dt:
                sLabel = str(dr["version"]) + (" (default)" if dr["default_version"] == 1 else "")
                sbString.append("<option value=\"" + dr["task_id"] + "\">" + sLabel + "</option>")

        return "".join(sbString)
    
    def wmGetTaskVersions(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sHTML = ""

        sSQL = """select task_id, version, default_version, task_status,
            case default_version when 1 then ' (default)' else '' end as is_default,
            case task_status when 'Approved' then 'locked' else 'unlocked' end as status_icon,
            created_dt
            from task
            where original_task_id = 
            (select original_task_id from task where task_id = %s)
            order by version"""

        dt = self.db.select_all_dict(sSQL, sTaskID)
        if dt:
            for dr in dt:
                sHTML += "<li class=\"ui-widget-content ui-corner-all version code\" id=\"v_" + dr["task_id"] + "\""
                sHTML += "task_id=\"" + dr["task_id"] + "\""
                sHTML += "status=\"" + dr["task_status"] + "\">"
                sHTML += "<span class=\"ui-icon ui-icon-" + dr["status_icon"] + " forceinline\"></span>"
                sHTML += str(dr["version"]) + "&nbsp;&nbsp;" + str(dr["created_dt"]) + dr["is_default"]
                sHTML += "</li>"

        return sHTML

    def wmCreateTask(self):
        sTaskName = uiCommon.unpackJSON(uiCommon.getAjaxArg("sTaskName"))
        sTaskCode = uiCommon.unpackJSON(uiCommon.getAjaxArg("sTaskCode"))
        sTaskDesc = uiCommon.unpackJSON(uiCommon.getAjaxArg("sTaskDesc"))

        t = task.Task()
        t.FromArgs(sTaskName, sTaskCode, sTaskDesc)

        bSuccess, sErr = t.DBSave()
        if not bSuccess:
            raise Exception(sErr)
        
            # add security log
            uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Task, t.ID, t.Name, "");

        return json.dumps({"id" : t.ID})

    def wmCopyTask(self):
        sCopyTaskID = uiCommon.getAjaxArg("sCopyTaskID")
        sTaskName = uiCommon.getAjaxArg("sTaskName")
        sTaskCode = uiCommon.getAjaxArg("sTaskCode")

        t = task.Task()
        t.FromID(sCopyTaskID)
        
        sNewTaskID = t.Copy(0, sTaskName, sTaskCode)
        
        uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Task, t.ID, t.Name, "Copied from " + sCopyTaskID);
        return json.dumps({"id" : sNewTaskID})

    def wmDeleteTasks(self):
        sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
        sDeleteArray = uiCommon.QuoteUp(sDeleteArray)

        if not sDeleteArray:
            raise Exception("Unable to delete - no selection.")
            
        task.Tasks.Delete(sDeleteArray.split(","), uiCommon.GetSessionUserID())
        
        uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.Task, "Multiple", "Original Task IDs", sDeleteArray)
        return json.dumps({"result" : "success"})
        
    def wmUpdateTaskDetail(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sColumn = uiCommon.getAjaxArg("sColumn")
        sValue = uiCommon.getAjaxArg("sValue")
        sUserID = uiCommon.GetSessionUserID()

        if catocommon.is_guid(sTaskID) and catocommon.is_guid(sUserID):
            # we encoded this in javascript before the ajax call.
            # the safest way to unencode it is to use the same javascript lib.
            # (sometimes the javascript and .net libs don't translate exactly, google it.)
            sValue = uiCommon.unpackJSON(sValue)
            sValue = catocommon.tick_slash(sValue)

            sSQL = "select original_task_id, task_name from task where task_id = %s"
            row = self.db.select_row_dict(sSQL, (sTaskID))
            if not row:
                raise Exception("Unable to get original_task_id for [%s]." % sTaskID)
                
            sOriginalTaskID = row["original_task_id"]
            sTaskName = row["task_name"]
            

            # what's the "set clause"?
            sSetClause = "%s='%s'" % (sColumn, sValue)

            #  bugzilla 1074, check for existing task_code and task_name
            if sColumn == "task_code" or sColumn == "task_name":
                sSQL = "select task_id from task where %s='%s' and original_task_id <> '%s'" % (sColumn, sValue, sOriginalTaskID)

                sValueExists = self.db.select_col(sSQL)

                if sValueExists:
                    raise WebmethodInfo("%s exists, please choose another value." % sValue)
            
                # changing the name or code updates ALL VERSIONS
                sSQL = "update task set %s where original_task_id = '%s'" % (sSetClause, sOriginalTaskID)
                self.db.exec_db(sSQL)
                
                if sColumn == "task_name":
                    # changing the TASK NAME updates any references (run_task, subtask commands) on any other Tasks.
                    # NOTE: this is done with a like clause and string replacement on the name
                    # ... and just to further clarify no conflict with other data, some xml pre/suffix is included
                    sSQL = """update task_step set 
                        function_xml = replace(function_xml, '>{0}</', '>{1}</')
                        where function_xml like '%%>{0}</%%'
                        and function_name in ('run_task', 'subtask')""".format(sTaskName, sValue)
                    self.db.exec_db(sSQL)
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
                
                sSQL = "update task set %s where task_id = '%s'" % (sSetClause, sTaskID)
                self.db.exec_db(sSQL)

            uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, sTaskID, sColumn, sValue)

        else:
            raise Exception("Unable to update task. Missing or invalid task [%s] id." % sTaskID)

        return json.dumps({"result" : "success"})
            
    def wmCreateNewTaskVersion(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sMinorMajor = uiCommon.getAjaxArg("sMinorMajor")

        oTask = task.Task()
        oTask.IncludeSettingsForUser = uiCommon.GetSessionUserID()
        oTask.FromID(sTaskID)
        
        sNewTaskID = oTask.Copy((1 if sMinorMajor == "Major" else 2), "", "")

        return sNewTaskID

    def wmGetCodeblocks(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")

        # instantiate the new Task object
        oTask = task.Task()
        oTask.FromID(sTaskID)

        sCBHTML = ""
        for cb in oTask.Codeblocks.itervalues():
            # if it's a guid it's a bogus codeblock (for export only)
            if catocommon.is_guid(cb.Name):
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

    def wmAddCodeblock(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sNewCodeblockName = uiCommon.getAjaxArg("sNewCodeblockName")

        if sNewCodeblockName:
            sSQL = "insert into task_codeblock (task_id, codeblock_name) values (%s, %s)"
                   
            self.db.exec_db(sSQL, (sTaskID, sNewCodeblockName))
            uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, sTaskID, sNewCodeblockName, "Added Codeblock.")
            
            return json.dumps({"result" : "success"})
        else:
            raise Exception("Unable to add Codeblock. Invalid or missing Codeblock Name.")
        
    def wmDeleteCodeblock(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sCodeblockID = uiCommon.getAjaxArg("sCodeblockID")
        sSQL = "delete u from task_step_user_settings u" \
            " join task_step ts on u.step_id = ts.step_id" \
            " where ts.task_id = '" + sTaskID + "'" \
            " and ts.codeblock_name = '" + sCodeblockID + "'"
        self.db.tran_exec(sSQL)

        sSQL = "delete from task_step" \
            " where task_id = '" + sTaskID + "'" \
            " and codeblock_name = '" + sCodeblockID + "'"
        self.db.tran_exec(sSQL)

        sSQL = "delete from task_codeblock" \
            " where task_id = '" + sTaskID + "'" \
            " and codeblock_name = '" + sCodeblockID + "'"
        self.db.tran_exec(sSQL)

        self.db.tran_commit()
        self.db.close()
        
        uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, sTaskID, sCodeblockID, "Deleted Codeblock.")

        return json.dumps({"result" : "success"})

    def wmRenameCodeblock(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sOldCodeblockName = uiCommon.getAjaxArg("sOldCodeblockName")
        sNewCodeblockName = uiCommon.getAjaxArg("sNewCodeblockName")
        if catocommon.is_guid(sTaskID):
            #  first make sure we are not try:ing to rename it something that already exists.
            sSQL = "select count(*) from task_codeblock where task_id = '" + sTaskID + "'" \
                " and codeblock_name = '" + sNewCodeblockName + "'"
            iCount = self.db.select_col(sSQL)
            if iCount != 0:
                raise Exception("Codeblock Name already in use, choose another.")

            #  do it

            # update the codeblock table
            sSQL = "update task_codeblock set codeblock_name = '" + sNewCodeblockName + \
                "' where codeblock_name = '" + sOldCodeblockName + \
                "' and task_id = '" + sTaskID + "'"
            self.db.tran_exec(sSQL)

            # and any steps in that codeblock
            sSQL = "update task_step set codeblock_name = '" + sNewCodeblockName + \
                "' where codeblock_name = '" + sOldCodeblockName + \
                "' and task_id = '" + sTaskID + "'"
            self.db.tran_exec(sSQL)

            # the fun part... rename it where it exists in any steps
            # but this must be in a loop of only the steps where that codeblock reference exists.
            sSQL = "select step_id from task_step" \
                " where task_id = '" + sTaskID + "'" \
                " and ExtractValue(function_xml, '//codeblock[1]') = '" + sOldCodeblockName + "'"
            dtSteps = self.db.select_all_dict(sSQL)

            if dtSteps:
                for dr in dtSteps:
                    uiCommon.SetNodeValueinXMLColumn("task_step", "function_xml", "step_id = '" + dr["step_id"] + "'", "codeblock[.='" + sOldCodeblockName + "']", sNewCodeblockName)

            # all done
            self.db.tran_commit()
            self.db.close()
            uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, sTaskID, sOldCodeblockName, "Renamed Codeblock [%s -> %s]" % (sOldCodeblockName, sNewCodeblockName))

            return json.dumps({"result" : "success"})
        else:
            raise Exception("Unable to get codeblocks for task. Missing or invalid task_id.")


    def wmCopyCodeblockStepsToClipboard(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sCodeblockName = uiCommon.getAjaxArg("sCodeblockName")

        if sCodeblockName != "":
            sSQL = "select step_id" \
                " from task_step" \
                " where task_id = '" + sTaskID + "'" \
                " and codeblock_name = '" + sCodeblockName + "'" \
                " order by step_order desc"

            dt = self.db.select_all_dict(sSQL)
            if dt:
                for dr in dt:
                    self.CopyStepToClipboard(dr["step_id"])

            return json.dumps({"result" : "success"})
        else:
            raise Exception("Unable to copy Codeblock. Missing or invalid codeblock_name.")

    def wmGetSteps(self):
            sTaskID = uiCommon.getAjaxArg("sTaskID")
            sCodeblockName = uiCommon.getAjaxArg("sCodeblockName")
            if not sCodeblockName:
                raise Exception("Unable to get Steps - No Codeblock specified.")

            sAddHelpMsg = "No Commands have been defined in this Codeblock. Drag a Command here to add it."

            # instantiate the new Task object
            oTask = task.Task()
            oTask.IncludeSettingsForUser = uiCommon.GetSessionUserID()
            oTask.FromID(sTaskID)

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
    
    def wmGetStepsPrint(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sHTML = ""
        
        # instantiate a Task object
        oTask = task.Task()
        oTask.FromID(sTaskID)

        # MAIN codeblock first
        sHTML += "<div class=\"ui-state-default te_header\">MAIN</div>"
        sHTML += "<div class=\"codeblock_box\">"
        sHTML += ST.BuildReadOnlySteps(oTask, "MAIN")
        sHTML += "</div>"

        # for the rest of the codeblocks
        for cb in oTask.Codeblocks.itervalues():
            # don't redraw MAIN
            if cb.Name == "MAIN":
                continue
            
            sHTML += "<div class=\"ui-state-default te_header\" id=\"cbt_" + cb.Name + "\">" + cb.Name + "</div>"
            sHTML += "<div class=\"codeblock_box\">"
            sHTML += ST.BuildReadOnlySteps(oTask, cb.Name)
            sHTML += "</div>"

        return sHTML
    
    def wmGetStep(self):
        sStepID = uiCommon.getAjaxArg("sStepID")
        sStepHTML = ""
        if not catocommon.is_guid(sStepID):
            uiCommon.log("Unable to get step. Invalid or missing Step ID. [" + sStepID + "].")

        sUserID = uiCommon.GetSessionUserID()

        oStep = ST.GetSingleStep(sStepID, sUserID)
        if oStep is not None:
            sStepHTML += ST.DrawFullStep(oStep)
        else:
            sStepHTML += "<span class=\"red_text\">ERROR: No data found.<br />This command should be deleted and recreated.<br /><br />ID [" + sStepID + "].</span>"

        # return the html
        return sStepHTML


    def wmAddStep(self):
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

        if not catocommon.is_guid(sTaskID):
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

        if catocommon.is_guid(sItem):
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

            self.db.exec_db(sSQL)

            uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, sTaskID, sItem,
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
                self.db.exec_db(sSQL)

                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, sTaskID, sItem,
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
            return json.dumps({"step_id":sNewStepID , "step_html": uiCommon.packJSON(sStepHTML)})
        else:
            raise Exception("Unable to add step.  No new step_id.")

    def wmAddEmbeddedCommandToStep(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sStepID = uiCommon.getAjaxArg("sStepID")
        sDropXPath = uiCommon.getAjaxArg("sDropXPath")
        sItem = uiCommon.getAjaxArg("sItem")
        sUserID = uiCommon.GetSessionUserID()

        sStepHTML = ""
        
        if not catocommon.is_guid(sTaskID):
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

        if catocommon.is_guid(sItem):
            # a clipboard sItem is a guid id on the task_step_clipboard table
            
            # 1) get the function_xml from the clipboard table (sItem = step_id)
            # 2) Get a Function object for the function name
            # 3) update the parent step with the function objects xml
            
            # get the command from the clipboard, and then update the XML of the parent step
            sSQL = "select function_xml from task_step_clipboard where user_id = '" + sUserID + "' and step_id = '" + sItem + "'"

            sXML = self.db.select_col(sSQL)
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

                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, sTaskID, sItem,
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

                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, sTaskID, sItem,
                    "Added Command Type: " + sItem + " to Step: " + sStepID)

            else:
                uiCommon.log("Unable to add step.  No template xml.")


        # draw the embedded step and return the html
        # !!!!! This isn't a new step! ... It's an extension of the parent step.
        # but, since it's a different 'function', we'll treat it like a different step for now
        oEmbeddedStep = task.Step()  # a new step object
        oEmbeddedStep.ID = sStepID 
        oEmbeddedStep.Function = func  # a function object
        oEmbeddedStep.FunctionName = func.Name
        oEmbeddedStep.FunctionXDoc = xe
        # THIS IS CRITICAL - this embedded step ... all fields in it will need an xpath prefix 
        oEmbeddedStep.XPathPrefix = sDropXPath + "/function"
        
        sStepHTML += ST.DrawEmbeddedStep(oEmbeddedStep)
        # return the html
        return sStepHTML

    def wmReorderSteps(self):
        sSteps = uiCommon.getAjaxArg("sSteps")
        i = 1
        for step_id in sSteps:
            sSQL = "update task_step set step_order = " + str(i) + " where step_id = '" + step_id + "'"

            # there will be no sSQL if there were no steps, so just skip it.
            if sSQL:
                self.db.exec_db(sSQL)
                
            i += 1

        return json.dumps({"result" : "success"})

    def wmDeleteStep(self):
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
            uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.Task, "Multiple", "Original Task IDs",
                "Codeblock:" + sCodeblock + 
                " Step Order:" + sDeletedStepOrder + 
                " Command Type:" + sFunction + 
                " Details:" + sFunctionXML)

        # "embedded" steps have a codeblock name referencing their "parent" step.
        # if we're deleting a parent, whack all the children
        sSQL = "delete from task_step where codeblock_name = '" + sStepID + "'"
        self.db.tran_exec(sSQL)

        # step might have user_settings
        sSQL = "delete from task_step_user_settings where step_id = '" + sStepID + "'"
        self.db.tran_exec(sSQL)

        # now whack the parent
        sSQL = "delete from task_step where step_id = '" + sStepID + "'"
        self.db.tran_exec(sSQL)

        sSQL = "update task_step set step_order = step_order - 1" \
            " where task_id = '" + sTaskID + "'" \
            " and codeblock_name = '" + sCodeblock + "'" \
            " and step_order > " + sDeletedStepOrder
        self.db.tran_exec(sSQL)

        self.db.tran_commit()
        self.db.close()
        
        return json.dumps({"result" : "success"})
        
    def wmUpdateStep(self):
        sStepID = uiCommon.getAjaxArg("sStepID")
        sFunction = uiCommon.getAjaxArg("sFunction")
        sXPath = uiCommon.getAjaxArg("sXPath")
        sValue = uiCommon.getAjaxArg("sValue")

        # we encoded this in javascript before the ajax call.
        # the safest way to unencode it is to use the same javascript lib.
        # (sometimes the javascript and .net libs don't translate exactly, google it.)
        sValue = uiCommon.unpackJSON(sValue)

        uiCommon.log("Updating step [%s (%s)] setting [%s] to [%s]." % (sFunction, sStepID, sXPath, sValue))
        
        # Some xpaths are hardcoded because they're on the step table and not in the xml.
        # this currently only applies to the step_desc column ("notes" field).
        if sXPath == "step_desc":
            sValue = catocommon.tick_slash(sValue)  # escape single quotes for the SQL insert
            sSQL = "update task_step set " + sXPath + " = '" + sValue + "' where step_id = '" + sStepID + "'"

            self.db.exec_db(sSQL)

        else:

            # XML processing
            # get the xml from the step table and update it
            sSQL = "select function_xml from task_step where step_id = '" + sStepID + "'"

            sXMLTemplate = self.db.select_col(sSQL)

            xDoc = ET.fromstring(sXMLTemplate)
            if xDoc is None:
                raise Exception("XML data for step [" + sStepID + "] is invalid.")

            try:
                uiCommon.log("... looking for [%s]" % sXPath)
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
                    else:  # and if there are break it down
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
                except Exception as ex:
                    uiCommon.log("Error Saving Step [" + sStepID + "].  Could not find and cannot create the [" + sXPath + "] property in the XML." + ex.__str__())
                    return ""

            sSQL = "update task_step set " \
                " function_xml = '" + catocommon.tick_slash(ET.tostring(xDoc)) + "'" \
                " where step_id = '" + sStepID + "';"

            self.db.exec_db(sSQL)


        sSQL = "select task_id, codeblock_name, step_order from task_step where step_id = '" + sStepID + "'"
        dr = self.db.select_row_dict(sSQL)
        if self.db.error:
            uiCommon.log_nouser(self.db.error, 0)

        if dr is not None:
            uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, dr["task_id"], sFunction,
                "Codeblock:" + dr["codeblock_name"] + \
                " Step Order:" + str(dr["step_order"]) + \
                " Command Type:" + sFunction + \
                " Property:" + sXPath + \
                " New Value: " + sValue)

        return json.dumps({"result" : "success"})

    def wmToggleStepCommonSection(self):
        # no exceptions, just a log message if there are problems.
        sStepID = uiCommon.getAjaxArg("sStepID")
        
        # todo: issue #71 - this should be saved to the db
        # sXPathPrefix = uiCommon.getAjaxArg("sXPathPrefix")
        
        sButton = uiCommon.getAjaxArg("sButton")
        if catocommon.is_guid(sStepID):
            sUserID = uiCommon.GetSessionUserID()
            sButton = ("null" if sButton == "" else "'" + sButton + "'")

            # is there a row?
            iRowCount = self.db.select_col_noexcep("select count(*) from task_step_user_settings" \
                " where user_id = '" + sUserID + "'" \
                " and step_id = '" + sStepID + "'")
            if iRowCount == 0:
                sSQL = "insert into task_step_user_settings" \
                    " (user_id, step_id, visible, breakpoint, skip, button)" \
                    " values ('" + sUserID + "','" + sStepID + "', 1, 0, 0, " + sButton + ")"
            else:
                sSQL = "update task_step_user_settings set button = " + sButton + " where step_id = '" + sStepID + "'"

            self.db.exec_db(sSQL)

            return ""
        else:
            uiCommon.log("Unable to toggle step button. Missing or invalid step_id.")
            
    def wmToggleStep(self):
        # no exceptions, just a log message if there are problems.
        sStepID = uiCommon.getAjaxArg("sStepID")
        sVisible = uiCommon.getAjaxArg("sVisible")
        
        if catocommon.is_guid(sStepID):
            sUserID = uiCommon.GetSessionUserID()

            sVisible = ("1" if sVisible == "1" else "0")

            # is there a row?
            iRowCount = self.db.select_col_noexcep("select count(*) from task_step_user_settings" \
                " where user_id = '" + sUserID + "'" \
                " and step_id = '" + sStepID + "'")
            if iRowCount == 0:
                sSQL = "insert into task_step_user_settings" \
                    " (user_id, step_id, visible, breakpoint, skip)" \
                    " values ('" + sUserID + "','" + sStepID + "', " + sVisible + ", 0, 0)"
            else:
                sSQL = "update task_step_user_settings set visible = '" + sVisible + "' where step_id = '" + sStepID + "'"

            self.db.exec_db(sSQL)
            
            return ""
        else:
            uiCommon.log("Unable to toggle step visibility. Missing or invalid step_id.")

    def wmToggleStepSkip(self):
        sStepID = uiCommon.getAjaxArg("sStepID")
        sSkip = uiCommon.getAjaxArg("sSkip")

        sSQL = "update task_step set commented = %s where step_id = %s"
        self.db.exec_db(sSQL, (sSkip, sStepID))

        return ""

    def wmFnIfAddSection(self):
        sStepID = uiCommon.getAjaxArg("sStepID")
        sAddTo = uiCommon.getAjaxArg("sAddTo")
        sIndex = uiCommon.getAjaxArg("iIndex")
        if sIndex > 0:
            # an index > 0 means its one of many 'elif' sections
            if sAddTo:
                # add a slash seperator if there's an add to
                sAddTo += "/" 
            ST.AddToCommandXML(sStepID, sAddTo + "tests", "<test><eval input_type=\"text\" /><action input_type=\"text\" /></test>")
        elif sIndex == -1:
            # whereas an index of -1 means its the ONLY 'else' section
            ST.AddToCommandXML(sStepID, sAddTo, "<else input_type=\"text\" />")
        else:
            # and of course a missing or 0 index is an error
            raise Exception("Unable to modify step. Invalid index.")

        return json.dumps({"result" : "success"})

    def wmTaskSearch(self):
        sFilter = uiCommon.getAjaxArg("sSearch")
        tasks = task.Tasks(sFilter)
        if tasks.rows:
            sHTML = "<hr />"

            iRowsToGet = len(tasks.rows)

            if iRowsToGet == 0:
                sHTML += "No results found"
            else:
                if iRowsToGet >= 100:
                    sHTML += "<div>Search found %s results.  Displaying the first 100.</div>" % iRowsToGet
                    iRowsToGet = 99
                sHTML += "<ul id=\"search_task_ul\" class=\"search_dialog_ul\">"

                i = 0
                for row in tasks.rows:
                    if i > iRowsToGet:
                        break
                    
                    sTaskName = row["Name"].replace("\"", "\\\"")
                    sLabel = row["Code"] + " : " + sTaskName
                    sDesc = (row["Description"] if row["Description"] else "")
                    sDesc = sDesc.replace("\"", "").replace("'", "")

                    sHTML += "<li class=\"ui-widget-content ui-corner-all search_dialog_value\" tag=\"task_picker_row\"" \
                        " task_name=\"" + sTaskName + "\"" \
                        " original_task_id=\"" + row["OriginalTaskID"] + "\"" \
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

    def wmGetStepVarsEdit(self):
        sStepID = uiCommon.getAjaxArg("sStepID")
        sXPathPrefix = uiCommon.getAjaxArg("sXPathPrefix")
        sUserID = uiCommon.GetSessionUserID()

        oStep = ST.GetSingleStep(sStepID, sUserID)
        fn = uiCommon.GetTaskFunction(oStep.FunctionName)
        if fn is None:
            uiCommon.log("Error - Unable to get the details for the Command type '" + oStep.FunctionName + "'.")
        
        # we will return some key values, and the html for the dialog
        html, pt, rd, cd = ST.DrawVariableSectionForEdit(oStep, sXPathPrefix)
        
        if not html:
            html = "<span class=\"red_text\">Unable to get command variables.</span>"

        return json.dumps({"parse_type":pt, "row_delimiter":rd, "col_delimiter":cd, "html":uiCommon.packJSON(html)})

    def wmUpdateVars(self):
        sStepID = uiCommon.getAjaxArg("sStepID")
        sXPathPrefix = uiCommon.getAjaxArg("sXPathPrefix")
        sOPM = uiCommon.getAjaxArg("sOPM")
        sRowDelimiter = uiCommon.getAjaxArg("sRowDelimiter")
        sColDelimiter = uiCommon.getAjaxArg("sColDelimiter")
        oVarArray = uiCommon.getAjaxArg("oVarArray")
        
        # if every single variable is delimited, we can sort them!
        bAllDelimited = True
        
        # update the function_xml attributes.
        # row and col delimiters must be integers...
        try:
            int(sRowDelimiter)
        except:
            sRowDelimiter = 0
        try:
            int(sColDelimiter)
        except:
            sColDelimiter = 0
            
        xpath = sXPathPrefix if sXPathPrefix else "function"
        ST.SetNodeAttributeinCommandXML(sStepID, xpath, "row_delimiter", sRowDelimiter)
        ST.SetNodeAttributeinCommandXML(sStepID, xpath, "col_delimiter", sColDelimiter)


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
                data.append((key, elem))  # the double parens are required! we're appending a tuple
            
            data.sort()
            
            # insert the last item from each tuple
            xVars[:] = [item[-1] for item in data]

        
        uiCommon.log("Saving variables ...")
        uiCommon.log(ET.tostring(xVars))
        
        # add and remove using the xml wrapper functions
        removenode = "%s/step_variables" % sXPathPrefix if sXPathPrefix else "step_variables"
        ST.RemoveFromCommandXML(sStepID, removenode)

        ST.AddToCommandXML(sStepID, xpath, catocommon.tick_slash(ET.tostring(xVars)))

        return ""

    def wmGetClips(self):
        sUserID = uiCommon.GetSessionUserID()
        sHTML = ""
        
        sSQL = "select s.clip_dt, s.step_id, s.step_desc, s.function_name, s.function_xml" \
            " from task_step_clipboard s" \
            " where s.user_id = '" + sUserID + "'" \
            " and s.codeblock_name is null" \
            " order by s.clip_dt desc"

        dt = self.db.select_all_dict(sSQL)
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
                        " class=\"command_item function clip ui-widget-content ui-corner-all\"" \
                        ">"
                
                # a table for the label so the clear icon can right align
                sHTML += "<table width=\"99%\" border=\"0\"><tr>"
                sHTML += "<td width=\"1px\"><img alt=\"\" src=\"" + sIcon + "\" /></td>"
                sHTML += "<td style=\"vertical-align: middle; padding-left: 5px;\">" + sLabel + "</td>"
                sHTML += "<td style=\"vertical-align: middle;\">"
                
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
                    sHTML += "<span view_id=\"v_" + sStepID + "\" class=\"btn_view_clip ui-icon ui-icon-search forceinline pointer\"></span>"
                # delete icon
                sHTML += "<span class=\"btn_clear_clip ui-icon ui-icon-close forceinline\" remove_id=\"" + sStepID + "\"></span>"
                sHTML += "</td></tr>"
                
                sHTML += "<tr><td>&nbsp;</td><td><span class=\"code\">" + sClipDT + "</span></td>"
                sHTML += "<td>&nbsp;</td></tr></table>"
                
                
                sHTML += "<div class=\"hidden\" id=\"help_text_clip_" + sStepID + "\">" + sDesc + "</div>"
                
                # TODO: for the moment we aren't building the view viersion of the command
                # until we convert all the VIEW functions!
                # we use this function because it draws a smaller version than DrawReadOnlyStep
                # sStepHTML = ""
                # # and don't draw those complex ones either
                # if not sFunction in "loop,exists,if,while":
                # BUT WHEN WE DO! ... build a clipboard step object here from the row selected above
                #    sStepHTML = ST.DrawClipboardStep(cs, True)
                
                # sHTML += "<div class=\"hidden\" id=\"v_" + sStepID + "\">" + sStepHTML + "</div>"
                
                sHTML += "</li>"
        return sHTML

    def wmCopyStepToClipboard(self):
        sStepID = uiCommon.getAjaxArg("sStepID")
        self.CopyStepToClipboard(sStepID)
        return ""

    def CopyStepToClipboard(self, sStepID):
        if catocommon.is_guid(sStepID):
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
            self.db.exec_db(sSQL)

            sSQL = " insert into task_step_clipboard" \
                " (user_id, clip_dt, src_step_id, root_step_id, step_id, function_name, function_xml, step_desc)" \
                " select '" + sUserID + "', now(), step_id, '" + sNewStepID + "', '" + sNewStepID + "'," \
                    " function_name, function_xml, step_desc" \
                " from task_step" \
                " where step_id = '" + sStepID + "'"
            self.db.exec_db(sSQL)

            return ""
        else:
            uiCommon.log("Unable to copy step. Missing or invalid step_id.")

    def wmRemoveFromClipboard(self):
        sStepID = uiCommon.getAjaxArg("sStepID")
        sUserID = uiCommon.GetSessionUserID()

        # if the sStepID is a guid, we are removing just one
        # otherwise, if it's "ALL" we are whacking them all
        if catocommon.is_guid(sStepID):
            sSQL = "delete from task_step_clipboard" \
                " where user_id = '" + sUserID + "'" \
                " and root_step_id = '" + sStepID + "'"
            self.db.exec_db(sSQL)

            return ""
        elif sStepID == "ALL":
            sSQL = "delete from task_step_clipboard where user_id = '" + sUserID + "'"
            self.db.exec_db(sSQL)

            return ""

    def wmRunTask(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sScopeID = uiCommon.getAjaxArg("sScopeID")
        sAccountID = uiCommon.getAjaxArg("sAccountID")
        sAssetID = uiCommon.getAjaxArg("sAssetID")
        sParameterXML = uiCommon.getAjaxArg("sParameterXML")
        sDebugLevel = uiCommon.getAjaxArg("iDebugLevel")
        
        sUserID = uiCommon.GetSessionUserID()
        return uiCommon.AddTaskInstance(sUserID, sTaskID, sScopeID, sAccountID, sAssetID, sParameterXML, sDebugLevel)

    """
        PARAMETER WEB METHODS and supporting static methods.
        
        The following group of parameter web methods all just call static methods in this class.  Why?
        Because there is an interplay between them, where they call one another depending on the context.
    """
    def wmGetParameterXML(self):
        sType = uiCommon.getAjaxArg("sType")
        sID = uiCommon.getAjaxArg("sID")
        sFilterID = uiCommon.getAjaxArg("sFilterID")
        sXPath = uiCommon.getAjaxArg("sXPath")
        return self.GetParameterXML(sType, sID, sFilterID, sXPath)

    def GetParameterXML(self, sType, sID, sFilterID, sXPath=""):
        if sType == "task":
            return self.GetObjectParameterXML(sType, sID, "")
        else:
            return self.GetMergedParameterXML(sType, sID, sFilterID, sXPath);  # Merging is happening here!

    # """
    #  This method simply gets the XML directly from the db for the type.
    #  It may be different by type!
    
    #  The schema should be the same, but some documents (task) are complete, while
    #  others (action, instance) are JUST VALUES, not the complete document.
    # """
    def wmGetObjectParameterXML(self):
        sType = uiCommon.getAjaxArg("sType")
        sID = uiCommon.getAjaxArg("sID")
        sFilterID = uiCommon.getAjaxArg("sFilterID")
        return self.GetObjectParameterXML(sType, sID, sFilterID)

    def GetObjectParameterXML(self, sType, sID, sFilterID, sXPath=""):
        if sType == "runtask":
            # run task needs xpath to find the xml in step function xml

            #  in this case, sID is actually a *step_id* !
            # sucks that MySql doesn't have decent XML functions... we gotta do manipulation grr...
            sSQL = """select function_xml from task_step where step_id = '%s'""" % sID
            func_xml = self.db.select_col(sSQL)
                
            xroot = ET.fromstring(func_xml)
            prefix = "%s/" if sXPath else ""
            xparams = xroot.find("%sparameters" % prefix)
            sParameterXML = ET.tostring(xparams)

        else:
            # other types can select it directly from their repspective tables
            if sType == "instance":
                # if sID is a guid, it's a task_id ... get the most recent run
                # otherwise assume it's a task_instance and try: that.
                if catocommon.is_guid(sID):
                    sSQL = """select parameter_xml from task_instance_parameter where task_instance = 
                        (select max(ti.task_instance) 
                        from task_instance ti
                        join task_instance_parameter tip on ti.task_instance = tip.task_instance
                         where ti.task_id = '%s')""" % sID
                elif catocommon.is_guid(sFilterID):  # but if there's a filter_id, limit it to tha:
                    sSQL = """select parameter_xml from task_instance_parameter where task_instance = 
                        (select max(ti.task_instance) 
                        from task_instance ti
                        join task_instance_parameter tip on ti.task_instance = tip.task_instance
                         where ti.task_id = '%s'
                         and ti.ecosystem_id = '%s'""" % (sID, sFilterID)
                else:
                    sSQL = "select parameter_xml from task_instance_parameter where task_instance = '" + sID + "'"
            elif sType == "plan":
                sSQL = "select parameter_xml from action_plan where plan_id = " + sID
            elif sType == "schedule":
                sSQL = "select parameter_xml from action_schedule where schedule_id = '" + sID + "'"
            elif sType == "task":
                sSQL = "select parameter_xml from task where task_id = '" + sID + "'"
    
            sParameterXML = self.db.select_col(sSQL)

        if sParameterXML:
            xParams = ET.fromstring(sParameterXML)
            if xParams is None:
                raise Exception("Parameter XML data for [" + sType + ":" + sID + "] is invalid.")

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

        # it may just be there are no parameters
        return ""

    def wmGetMergedParameterXML(self):
        sType = uiCommon.getAjaxArg("sType")
        sID = uiCommon.getAjaxArg("sID")
        sFilterID = uiCommon.getAjaxArg("sFilterID")
        return self.GetMergedParameterXML(sType, sID, sFilterID)

    def GetMergedParameterXML(self, sType, sID, sFilterID, sXPath=""):
        """
         This method does MERGING!
         
         It gets the XML for the Task, and additionally get the XML for the other record,
         and merges them together, using the values from one to basically select values in 
         the master task XML.
         
         For example, the run_task command may have parameter VALUES saved on it.
         These will override any values defined on the task.
         
         However, if the value is NOT defined on run_task, the task default still applies.
         
         More commonly, this method merges any parameters submitted 
             on a PREVIOUS RUN of the task, again using defined task defaults 
             if any are omitted.
          
         """
        if not sID:
            uiCommon.log("ID required to look up default Parameter values.")
    
        sDefaultsXML = ""
        sTaskID = ""
        sSQL = ""
        
        if sType == "runtask":
            # RunTask is actually a command type
            # but it's very very similar to an Action.
            # so... it handles it's params like an action... more or less.
            
            # HACK ALERT!  Since we are dealing with a unique case here where we have and need both the 
            # step_id AND the target task_id, we're piggybacking a value in.
            # the sID is the STEP_ID (which is kindof equivalient to the action)
            # the sFilterID is the target TASK_ID
            # yes, it's a hack I know... but better than adding another argument everywhere... sue me.
            
            # NOTE: plus, don't get confused... yes, run task references tasks by original id and version, but we already worked that out.
            # the sFilterID passed in to this function is already resolved to an explicit task_id... it's the right one.
    
            # get the parameters off the step itself.
            # which is also goofy, as they are embedded *inside* the function xml of the step.
            # but don't worry that's handled in here
            sDefaultsXML = self.GetObjectParameterXML(sType, sID, "", sXPath)
            
            # now, we will want to get the parameters for the task *referenced by the command* down below
            # but no sql is necessary to get the ID... we already know it!
            sTaskID = sFilterID
            
        elif sType == "instance":
            sDefaultsXML = self.GetObjectParameterXML(sType, sID, sFilterID)
    
            # IMPORTANT!!! if the ID is not a guid, it's a specific instance ID, and we'll need to get the task_id
            # but if it is a GUID, but the type is "instance", taht means the most recent INSTANCE for this TASK_ID
            if catocommon.is_guid(sID):
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
            if sSQL:
                sTaskID = self.db.select_col(sSQL)
            else:
                raise Exception("GetMergedParams - no task id and no sql to look one up.", 0)
    
        if not catocommon.is_guid(sTaskID):
            raise Exception("Unable to find Task ID for record.")
    
    
        # get the parameter XML from the TASK
        sTaskParamXML = self.GetParameterXML("task", sTaskID, "")
        xTPParams = None
        if sTaskParamXML:
            xTPParams = ET.fromstring(sTaskParamXML)
            if xTPParams is None:
                raise Exception("Task Parameter XML data is invalid.")
    
        # we populated this up above too
        if sDefaultsXML:
            xDefParams = ET.fromstring(sDefaultsXML)
            if xDefParams is None:
                raise Exception("Defaults XML data is invalid.")
    
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
                            # find the right one by value and give it the "selected" attribute.
                            for xVal in xTaskParamValues.findall("value"):
                                if xVal.text == sValueToSelect:
                                    xVal.attrib["selected"] = "true"
                    elif sPresentAs == "list":
                        # replace the whole list with the defaults if they exist
                        xTaskParam.remove(xTaskParamValues)
                        xTaskParam.append(xDefValues)
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
    
    def wmSaveDefaultParameterXML(self):
        sType = uiCommon.getAjaxArg("sType")
        sID = uiCommon.getAjaxArg("sID")
        sTaskID = uiCommon.getAjaxArg("sTaskID")  # sometimes this may be here
        sBaseXPath = uiCommon.getAjaxArg("sBaseXPath", "")
        sXML = uiCommon.getAjaxArg("sXML")
        sUserID = uiCommon.GetSessionUserID()

        if catocommon.is_guid(sID) and catocommon.is_guid(sUserID):
            # we encoded this in javascript before the ajax call.
            # the safest way to unencode it is to use the same javascript lib.
            # (sometimes the javascript and .net libs don't translate exactly, google it.)
            sXML = uiCommon.unpackJSON(sXML)

            # we gotta peek into the XML and encrypt any newly keyed values
            sXML = uiCommon.PrepareAndEncryptParameterXML(sXML);                

            # so, like when we read it, we gotta spin and compare, and build an XML that only represents *changes*
            # to the defaults on the task.
            
            if not catocommon.is_guid(sTaskID):
                uiCommon.log("No Task ID provided.")


            sOverrideXML = ""
            xTPDoc = None
            xADDoc = None

            # get the parameter XML from the TASK
            sTaskParamXML = self.GetParameterXML("task", sTaskID, "")
            if sTaskParamXML:
                xTPDoc = ET.fromstring(sTaskParamXML)
                if xTPDoc is None:
                    raise Exception("Task Parameter XML data is invalid.")
    
            # we had the ACTION defaults handed to us
            if sXML:
                xADDoc = ET.fromstring(sXML)
                if xADDoc is None:
                    raise Exception("Action Defaults XML data is invalid.")

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
                        
                    # if the values match the defaults identically, don't include them
                    # this allows the defaults to change if needed without storing
                    # an old copy here.
                    if sTaskVals == sDefVals:
                        xADDoc.remove(xDefault)
                        continue

            # done
            sOverrideXML = ET.tostring(xADDoc)

            # FINALLY, we have an XML that represents only the differences we wanna save.
            if sType == "runtask":
                # WICKED!!!!
                # I can use my super awesome xml functions!
                xpath = "%s/parameters" % sBaseXPath if sBaseXPath else "parameters"
                ST.RemoveFromCommandXML(sID, xpath)
                ST.AddToCommandXML(sID, sBaseXPath, sOverrideXML)
        else:
            raise Exception("Unable to update Action. Missing or invalid Action ID.")

        return ""

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

        if not sType:
            raise Exception("ERROR: Type was not passed to wmGetParameters.")
        
        sTable = ""

        if sType == "task":
            sTable = "task"

        sSQL = "select parameter_xml from " + sTable + " where " + sType + "_id = '" + sID + "'"

        sParameterXML = self.db.select_col(sSQL)

        return ST.DrawCommandParameterSection(sParameterXML, bEditable, bSnipValues)

    def wmGetTaskParam(self):
        sID = uiCommon.getAjaxArg("sID")
        sType = uiCommon.getAjaxArg("sType")
        sParamID = uiCommon.getAjaxArg("sParamID")

        if not catocommon.is_guid(sID):
            raise Exception("Invalid or missing ID.")

        sTable = ""

        if sType == "task":
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

            sXML = self.db.select_col(sSQL)
            if sXML:
                xd = ET.fromstring(sXML)
                if xd is None: raise Exception("XML parameter data is invalid.")

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
                raise Exception("Unable to get parameter details. Not found.")
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

    def wmDeleteTaskParam(self):
        sType = uiCommon.getAjaxArg("sType")
        sID = uiCommon.getAjaxArg("sID")
        sParamID = uiCommon.getAjaxArg("sParamID")

        sTable = ""

        if sType == "task":
            sTable = "task"

        if sParamID and catocommon.is_guid(sID):
            #  need the name and values for logging
            sXML = ""

            # ALL OF THIS is just for logging ...
            sSQL = "select parameter_xml" \
                " from " + sTable + \
                " where " + sType + "_id = '" + sID + "'"

            sXML = self.db.select_col(sSQL)
            if sXML != "":
                xd = ET.fromstring(sXML)
                if xd is None:
                    raise Exception("XML parameter data is invalid.")

                sName = xd.findtext("parameter[@id='" + sParamID + "']/name", "")
                sValues = xd.findtext("parameter[@id='" + sParamID + "']/values", "")

                #  add security log
                uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.Parameter, "", sID, "")

                if sType == "task":
                    uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, sID, "Deleted Parameter:[" + sName + "]", sValues)


            # Here's the real work ... do the whack
            uiCommon.RemoveNodeFromXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", "parameter[@id='" + sParamID + "']")

            return json.dumps({"result" : "success"})
        else:
            raise Exception("Invalid or missing Task or Parameter ID.")

    def wmUpdateTaskParam(self):
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

        if not catocommon.is_guid(sID):
            raise Exception("Save Parameter - Invalid or missing ID.")

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
        sParameterXPath = "parameter[@id='" + sParamID + "']"  # using this to keep the code below cleaner.

        if sType == "task":
            sTable = "task"

        bParamAdd = False
        # bParamUpdate = false

        # if sParamID is empty, we are adding
        if not sParamID:
            sParamID = "p_" + catocommon.new_guid()
            sParameterXPath = "parameter[@id='" + sParamID + "']"  # reset this if we had to get a new id


            # does the task already have parameters?
            sSQL = "select parameter_xml from " + sTable + " where " + sType + "_id = '" + sID + "'"
            sCurrentXML = self.db.select_col(sSQL)

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

                self.db.exec_db(sSQL)

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


        #  not clean at all, but whatever.
        if bParamAdd:
            if sType == "task":
                uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Task, sID, "Parameter", "Added Parameter [%s]" % sName)
        else:
            #  would be a lot of trouble to add the from to, why is it needed you have each value in the log, just scroll back
            #  so just add a changed message to the log
            if sType == "task":
                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, sID, "Parameter", "Modified Parameter [%s]" % sName)

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
                
            # the value must be htmlencoded since we're building the xml as a string
            # (this is so ugly... would love to take time to do it right)
            sReadyValue = cgi.escape(sReadyValue)
                
            sValueXML += "<value id=\"pv_" + catocommon.new_guid() + "\">" + sReadyValue + "</value>"

        sValueXML = "<values present_as=\"" + sPresentAs + "\">" + sValueXML + "</values>"


        # whack-n-add
        uiCommon.RemoveNodeFromXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath + "/values")
        uiCommon.AddNodeToXMLColumn(sTable, "parameter_xml", sType + "_id = '" + sID + "'", sParameterXPath, sValueXML)

        return json.dumps({"result" : "success"})

    def wmGetTaskRunLogDetails(self):
        sTaskInstance = str(uiCommon.getAjaxArg("sTaskInstance"))
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sAssetID = uiCommon.getAjaxArg("sAssetID")
        
        # not doing the permission check yet
        """
        # PERMISSION CHECK
        # now... kick out if the user isn't allowed to see this page

        # it's a little backwards... IsPageAllowed will kick out this page for users...
        # so don't bother to check that if we can determine the user has permission by 
        # a group association to this task
        sOTID = ""
        stiSQL = "select t.original_task_id" \
           " from task_instance ti join task t on ti.task_id = t.task_id" \
           " where ti.task_instance = '" + sTaskInstance + "'"

        sOTID = self.db.select_col_noexcep(sSQL)
        if self.db.error:
            uiCommon.log("Unable to get original_task_id for task instance.  " + self.db.error)

        # now we know the ID, see if we are grouped with it
        # this will kick out if they DONT match tags and they AREN'T in a role with sufficient privileges
        if !uiCommon.UserAndObjectTagsMatch(sOTID, 3)) uiCommon.IsPageAllowed("You do not have permission to view this Task.":
        # END PERMISSION CHECK
        """

        # we should return some indication of whether or not the user can do
        # certain functions.
        """
        # superusers AND those tagged with this Task can see the stop and resubmit button
        if uiCommon.UserIsInRole("Developer") or uiCommon.UserIsInRole("Administrator") or uiCommon.UserAndObjectTagsMatch(dr["original_task_id"], 3):
            resubmit_btn.Visible = true
            abort_btn.Visible = true
        else:
            resubmit_btn.Visible = false
            abort_btn.Visible = false
        """

        # so, it's simple.  We get the object (a dictionary) from the task class
        # do any adjustments we need, then return it as json.
        
        ti = task.TaskInstance(sTaskInstance, sTaskID, sAssetID)
        if ti.Error:
            return json.dumps({"error" : ti.Error})
        
        # one last thing... does the logfile for this run exist on this server?
        if os.path.exists(r"%s/ce/%s.log" % (catolog.LOGPATH, sTaskInstance)):
            ti.logfile_name = "%s/ce/%s.log" % (catolog.LOGPATH, sTaskInstance)

        # all done, serialize our output dictionary
        return ti.AsJSON()

    def wmGetTaskRunLog(self):
        sTaskInstance = uiCommon.getAjaxArg("sTaskInstance")
        sRows = uiCommon.getAjaxArg("sRows")

        runlog = task.TaskRunLog(sTaskInstance, sRows)
        sLog = ""
        sSummary = ""
    
        if runlog.summary_rows:
            for dr in runlog.summary_rows:
                # almost done... if there is a Result Summary ... display that.
                if dr["log"]:
                    xdSummary = ET.fromstring(dr["log"])
                    if xdSummary is not None:
                        for item in xdSummary.findall("items/item"):
                            name = item.findtext("name", "")
                            detail = item.findtext("detail", "")
                            sSummary += "<div class='result_summary_item_name'>%s</div>" % name
                            sSummary += "<div class='result_summary_item_detail ui-widget-content ui-corner-all'>%s</div>" % detail    

        # log rows
        if runlog.log_rows:
            sLog += "<ul class=\"log\">\n"
            sThisStepID = ""
            sPrevStepID = ""

            for dr in runlog.log_rows:
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
                    # the command text might hold special information we want to display differently
                    if "run_task" in dr["command_text"]:
                        sInstance = dr["command_text"].replace("run_task ", "")
                        sLog += "<span class=\"link\" onclick=\"location.href='taskRunLog?task_instance=" + sInstance + "';\">Jump to Task</span>"
                    else:
                        sLog += "<div class=\"log_command ui-widget-content ui-corner-all hidden\">\n"
                        sLog += uiCommon.FixBreaks(uiCommon.SafeHTML(dr["command_text"]))
                        sLog += "</div>\n"



                # it might be a log entry:
                # ( we write out the div even if it's empty, so the user 
                # will see an indication of progress
                sLog += "    <div class=\"log_results ui-widget-content ui-corner-all\">\n"
                if dr["log"].strip():
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

        sNumRows = str(runlog.numrows) if runlog.numrows else "0"
        return json.dumps({"log" : uiCommon.packJSON(sLog), "summary" : uiCommon.packJSON(sSummary), "totalrows" : sNumRows})

    def wmGetTaskLogfile(self):
        instance = uiCommon.getAjaxArg("sTaskInstance")
        logfile = ""
        if instance:
            logfile = "%s/ce/%s.log" % (catolog.LOGPATH, instance)
            if os.path.exists(logfile):
                if os.path.getsize(logfile) > 20971520:  # 20 meg is a pretty big logfile for the browser.
                    return uiCommon.packJSON("Logfile is too big to view in a web browser.")
                with open(logfile, 'r') as f:
                    if f:
                        return uiCommon.packJSON(uiCommon.SafeHTML(f.read()))
        
        return uiCommon.packJSON("Unable to read logfile. [%s]" % logfile)
            
    def wmExportTasks(self):
        """
        This function creates an xml export file of all tasks specified in sTaskArray.  
        
        If the "include references" flag is set, each task is scanned for additional
        references, and they are included in the export.
        """
        
        sIncludeRefs = uiCommon.getAjaxArg("sIncludeRefs")
        sTaskArray = uiCommon.getAjaxArg("sTaskArray")

        otids = sTaskArray.split(",")
        xml = ""
        
        # there can be many tasks selected...
        # to help a little bit, we'll use the first name we encounter on the export file name
        helpername = ""
        
        for otid in otids:
            # get the task
            t = task.Task()
            t.FromOriginalIDVersion(otid)
            if t:
                if not helpername:
                    helpername = t.Name
                    
                xml += t.AsXML(include_code=True)

                # regarding references, here's the deal
                # in a while loop, we check the references for each task in the array
                # UTIL THE 'otid' LIST STOPS GROWING.
                if catocommon.is_true(sIncludeRefs):
                    reftasks = t.GetReferencedTasks()
                    for reftask in reftasks:
                        if reftask.OriginalTaskID not in otids:
                            otids.append(reftask.OriginalTaskID)

        xml = "<tasks>%s</tasks>" % xml

        # what are we gonna call this file?
        seconds = str(int(time.time()))
        filename = "%s_%s.csk" % (helpername.replace(" ", "").replace("/", ""), seconds)
        with open(os.path.join(catoconfig.CONFIG["tmpdir"], filename), 'w') as f_out:
            if not f_out:
                uiCommon.log("ERROR: unable to write task export file.")
            f_out.write(xml)
            
        return json.dumps({"export_file" : filename})
            
    def wmGetTaskStatusCounts(self):
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
                "from task_instance) foo"

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

        # if we get here, there is just no data... 
        return ""

    def wmGetTaskVarPickerPopup(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")

        if catocommon.is_guid(sTaskID):
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

            # lVars is a list of all the variables we can pick from
            # the value is the var "name"
            lVars = []

            dtStupidVars = self.db.select_all_dict(sSQL)

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

            sParameterXML = self.db.select_col(sSQL)
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

            lItems = ["_ASSET", "_SUBMITTED_BY", "_SUBMITTED_BY_EMAIL",
                      "_TASK_INSTANCE", "_TASK_NAME", "_TASK_VERSION",
                      "_DATE", "_HTTP_RESPONSE", "_UUID", "_UUID2",
                      "_CLOUD_NAME", "_CLOUD_LOGIN_ID", "_CLOUD_LOGIN_PASS",
                      "_HOST_ID", "_HOST", "_INSTANCE_ID",
                      "_SERVICE_ID", "_SERVICE_NAME", "_SERVICE_DOCID",
                      "_DEPLOYMENT_ID", "_DEPLOYMENT_NAME", "_DEPLOYMENT_DOCID"]
            for gvar in lItems:
                sHTML += "<div class=\"ui-widget-content ui-corner-all value_picker_value\">%s</div>" % gvar

            sHTML += "</div>"

            # all done
            return sHTML
        else:
            uiCommon.log("Unable to get variables for task. Missing or invalid task_id.")

    def wmGetTaskCodeblockPicker(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sStepID = uiCommon.getAjaxArg("sStepID")

        if catocommon.is_guid(sTaskID):
            sSQL = "select codeblock_name from task_codeblock where task_id = '" + sTaskID + "'" \
                " and codeblock_name not in (select codeblock_name from task_step where step_id = '" + sStepID + "')" \
                " order by codeblock_name"

            dt = self.db.select_all_dict(sSQL)

            sHTML = ""

            for dr in dt:
                sHTML += "<div class=\"ui-widget-content ui-corner-all value_picker_value\">" + dr["codeblock_name"] + "</div>"

            return sHTML
        else:
            raise Exception("Unable to get codeblocks for task. Missing or invalid task_id.")

    def wmGetTaskConnections(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")

        if catocommon.is_guid(sTaskID):
            sSQL = "select conn_name from (" \
                "select distinct ExtractValue(function_xml, '//conn_name[1]') as conn_name" \
                " from task_step" \
                    " where function_name = 'new_connection'" \
                    " and task_id = '" + sTaskID + "'" \
                    " ) foo" \
                " where ifnull(conn_name,'') <> ''" \
                " order by conn_name"

            dt = self.db.select_all_dict(sSQL)

            sHTML = ""

            if dt:
                for dr in dt:
                    sHTML += "<div class=\"ui-widget-content ui-corner-all value_picker_value\">" + dr["conn_name"] + "</div>"

            return sHTML
        else:
            uiCommon.log("Unable to get connections for task. Missing or invalid task_id.")
            
    def wmStopTask(self):
        sInstance = uiCommon.getAjaxArg("sInstance")
        ti = task.TaskInstance(sInstance)
        ti.Stop()
        return json.dumps({"result" : "success"})

    def wmApproveTask(self):
        sTaskID = uiCommon.getAjaxArg("sTaskID")
        sMakeDefault = uiCommon.getAjaxArg("sMakeDefault")

        sUserID = uiCommon.GetSessionUserID()

        if catocommon.is_guid(sTaskID) and catocommon.is_guid(sUserID):

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
                self.db.tran_exec(sSQL)

                sSQL = "update task set" \
                " task_status = 'Approved'," \
                " default_version = 1" \
                " where task_id = '" + sTaskID + "'"
            else:
                sSQL = "update task set" \
                    " task_status = 'Approved'" \
                    " where task_id = '" + sTaskID + "'"

            sSQL = sSQL
            self.db.tran_exec(sSQL)
            self.db.tran_commit()

            uiCommon.WriteObjectPropertyChangeLog(catocommon.CatoObjectTypes.Task, sTaskID, "Status", "Development", "Approved")
            if sMakeDefault == "1":
                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Task, sTaskID, "Default", "Set as Default Version.")

        else:
            raise Exception("Unable to update task. Missing or invalid task id. [" + sTaskID + "]")

    def wmFnNodeArrayAdd(self):
        sStepID = uiCommon.getAjaxArg("sStepID")
        sFunctionName = uiCommon.getAjaxArg("sFunctionName")
        sTemplateXPath = uiCommon.getAjaxArg("sTemplateXPath")
        sAddTo = uiCommon.getAjaxArg("sAddTo")

        func = uiCommon.GetTaskFunction(sFunctionName)
        if not func:
            raise Exception("Unable to get a Function definition for name [%s]" % sFunctionName)
        
        # validate it
        # parse the doc from the table
        xd = func.TemplateXDoc
        if xd is None:
            raise Exception("Unable to get Function Template.")
        
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
            # well, let's try to add it, we might get lucky if it's a single node :-)
            try:
                xd.append(ET.Element(sTemplateNode))
                xGroupNode = xd.find(sTemplateNode)
            except:
                raise Exception("Error: Source node not found in Template XML, and cannot create it. [" + sTemplateNode + "].")
        
        if xGroupNode is None:
            raise Exception("Error: Unable to add.  Template XML does not contain [" + sTemplateNode + "].")
        
        # yeah, this wicked single line aggregates the value of each node
        sNewXML = "".join(ET.tostring(x) for x in list(xGroupNode))
        uiCommon.log(sNewXML)
        
        if sNewXML != "":
            ST.AddToCommandXML(sStepID, sAddTo, sNewXML.strip())
            # uiCommon.AddNodeToXMLColumn("task_step", "function_xml", "step_id = '" + sStepID + "'", sTemplateXPath, sNewXML)

        return ""

    def wmRemoveNodeFromStep(self):
        # NOTE: this function is capable of removing data from any command.
        # it is not failsafe - it simply take a path and removes the node.
        sStepID = uiCommon.getAjaxArg("sStepID")
        sRemovePath = uiCommon.getAjaxArg("sRemovePath")
        if sRemovePath:
            ST.RemoveFromCommandXML(sStepID, sRemovePath)
            return ""
        else:
            raise Exception("Unable to modify step. Invalid remove path.")
