
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
 
"""
    THIS CLASS has it's own database connections.
    Why?  Because it isn't only used by the UI.
"""

import traceback
import uuid
import json
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET
from catocommon import catocommon
from catoui import uiCommon
from datetime import datetime

# Note: this is not a container for Task objects - it's just a rowset from the database
# with an AsJSON method.
# why? Because we don't need a full object for list pages and dropdowns.
class Tasks(object):
    rows = {}
    def __init__(self, sFilter=""):
        try:
            sWhereString = ""
            if sFilter:
                aSearchTerms = sFilter.split()
                for term in aSearchTerms:
                    if term:
                        sWhereString += " and (t.task_name like '%%" + term + "%%' " \
                            "or t.task_code like '%%" + term + "%%' " \
                            "or t.task_desc like '%%" + term + "%%' " \
                            "or t.task_status like '%%" + term + "%%') "
    
            sSQL = """select t.task_id, t.original_task_id, t.task_name, t.task_code, t.task_desc, t.version, t.task_status,
                (select count(*) from task where original_task_id = t.original_task_id) as versions,
                group_concat(ot.tag_name order by ot.tag_name separator ',') as tags
                from task t
                left outer join object_tags ot on t.original_task_id = ot.object_id
                where t.default_version = 1 %s group by t.original_task_id order by t.task_code""" % sWhereString
            
            db = catocommon.new_conn()
            self.rows = db.select_all_dict(sSQL)
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.rows)
        except Exception as ex:
            raise ex

class Task(object):
    def __init__(self):
        self.ID = ""
        self.OriginalTaskID = ""
        self.Name = ""
        self.Code = ""
        self.Version = "1.000"
        self.Status = "Development"
        self.Description = ""
        self.DBExists = False
        self.OnConflict = "cancel" #the default behavior for all conflicts is to cancel the operation
        self.UseConnectorSystem = False
        self.IsDefaultVersion = False
        self.ConcurrentInstances = ""
        self.QueueDepth = ""
        self.ParameterXDoc = None
        self.NumberOfApprovedVersions = 0
        self.MaxVersion = "1.000"
        self.NextMinorVersion = "1.001"
        self.NextMajorVersion = "2.000"
        #a task has a dictionary of codeblocks
        self.Codeblocks = {}

    #the default constructor (manual creation)
    def FromArgs(self, sName, sCode, sDesc):
        if not sName:
            raise Exception("Error building Task object: Name is required.")

        self.ID = str(uuid.uuid4())
        self.OriginalTaskID = self.ID
        self.Name = sName
        self.Code = sCode
        self.Description = sDesc
        self.CheckDBExists()

    #constructor - from the database by ID
    def FromID(self, sTaskID, bIncludeUserSettings = False):
        sErr = ""
        try:
            db = catocommon.new_conn()
            sSQL = "select task_id, original_task_id, task_name, task_code, task_status, version, default_version," \
                    " task_desc, use_connector_system, concurrent_instances, queue_depth, parameter_xml" \
                    " from task" \
                    " where task_id = '" + sTaskID + "'"

            dr = db.select_row_dict(sSQL)

            if dr:
                sErr = self.PopulateTask(db, dr, bIncludeUserSettings)

            if self.ID:
                return ""
            else:
                return sErr
            
        except Exception as ex:
            raise ex
        finally:
            db.close()

    def FromOriginalIDVersion(self, otid, version=None):
        sErr = ""
        try:
            db = catocommon.new_conn()
            version_clause = ""
            if version:
                version_clause = " and version = %s" % version
            else:
                version_clause = " and default_version = 1"
                
            sSQL = """select task_id, original_task_id, task_name, task_code, task_status, version, default_version,
                    task_desc, use_connector_system, concurrent_instances, queue_depth, parameter_xml
                    from task
                    where original_task_id = '%s' %s""" % (otid, version_clause)
            dr = db.select_row_dict(sSQL)

            if dr:
                sErr = self.PopulateTask(db, dr, False)

            if self.ID:
                return ""
            else:
                return sErr
            
        except Exception as ex:
            raise ex
        finally:
            db.close()

    def FromXML(self, sTaskXML=""):
        try:
            if sTaskXML == "": return None
            
            xmlerr = "XML Error: Attribute not found."
            
            uiCommon.log("Creating Task object from XML", 3)
            xTask = ET.fromstring(sTaskXML)
            
            #attributes of the <task> node
            
            # NOTE: id is ALWAYS NEW from xml.  If it matches an existing task by name, that'll be figured out
            # in CheckDBExists below.
            self.ID = str(uuid.uuid4())
            
            # original task id is specific to the system where this was originally created.
            # for xml imports, this is a NEW task by default.
            # if the user changes 'on_conflict' to either replace or version up
            # the proper original task id will be resolved by that branch of DBSave
            self.OriginalTaskID = self.ID
            self.Name = xTask.get("name", xmlerr)
            self.Code = xTask.get("code", xmlerr)
            self.OnConflict = xTask.get("on_conflict", "cancel") #cancel is the default action if on_conflict isn't specified
            
            # these, if not provided, have initial defaults
            self.Version = xTask.get("version", "1.000")
            self.Status = xTask.get("status", "Development")
            self.IsDefaultVersion = True
            self.ConcurrentInstances = xTask.get("concurrent_instances", "")
            self.QueueDepth = xTask.get("queue_depth", "")
            
            #text nodes in the <task> node
            _desc = xTask.find("description", xmlerr).text
            self.Description = _desc if _desc is not None else ""
            
            # do we have a conflict?
            self.CheckDBExists()
 
            # CODEBLOCKS
            xCodeblocks = xTask.findall("codeblocks/codeblock")
            uiCommon.log("Number of Codeblocks: " + str(len(xCodeblocks)), 4)
            for xCB in xCodeblocks:
                cbname = xTask.get("name", "")
                if not cbname:
                    uiCommon.log("Error: Codeblock 'name' attribute is required.", 1)

                newcb = Codeblock(cbname)
                newcb.FromXML(ET.tostring(xCB))
                self.Codeblocks[newcb.Name] = newcb
                
            # PARAMETERS
            self.ParameterXDoc = xTask.find("parameters")

        except Exception as ex:
            raise ex


    def AsXML(self):
        # NOTE!!! this was just a hand coded test... it needs to be pulled in from the C# version
        root=ET.fromstring('<task />')
        
        root.set("original_task_id", self.OriginalTaskID)
        root.set("name", str(self.Name))
        root.set("code", str(self.Code))
        root.set("version", str(self.Version))
        root.set("on_conflict", "cancel")
        root.set("status", str(self.Status))
        root.set("concurrent_instances", str(self.ConcurrentInstances))
        root.set("queue_depth", str(self.QueueDepth))

        ET.SubElement(root, "description").text = self.Description
        
        # PARAMETERS
        if self.ParameterXDoc is not None:
            root.append(self.ParameterXDoc)
        
        #CODEBLOCKS
        xCodeblocks = ET.SubElement(root, "codeblocks") #add the codeblocks section
        
        #TODO!!! fix this to be for name, cb in self.Codeblocks!!!!
        for k in self.Codeblocks:
            #the dict can't unpack the object?
            #try it by reference
            cb = self.Codeblocks[k]
            xCB = ET.SubElement(xCodeblocks, "codeblock") #add the codeblock
            xCB.set("name", cb.Name)
            
            #STEPS
            xSteps = ET.SubElement(xCB, "steps") #add the steps section
            
            for s in cb.Steps:
                stp = cb.Steps[s]
                xStep = ET.SubElement(xSteps, "step") #add the step
                xStep.set("codeblock", str(stp.Codeblock))
                xStep.set("output_parse_type", str(stp.OutputParseType))
                xStep.set("output_column_delimiter", str(stp.OutputColumnDelimiter))
                xStep.set("output_row_delimiter", str(stp.OutputRowDelimiter))
                xStep.set("commented", str(stp.Commented).lower())

                ET.SubElement(xStep, "description").text = stp.Description
                
                xStep.append(stp.FunctionXDoc)
        
        return ET.tostring(root)

    def AsJSON(self, include_code=False):
        try:
            sb = []
            sb.append("{")
            sb.append("\"%s\" : \"%s\"," % ("ID", self.ID))
            sb.append("\"%s\" : \"%s\"," % ("Name", self.Name))
            sb.append("\"%s\" : \"%s\"," % ("Code", self.Code))
            sb.append("\"%s\" : \"%s\"," % ("Version", self.Version))
            sb.append("\"%s\" : \"%s\"," % ("Status", self.Status))
            sb.append("\"%s\" : \"%s\"," % ("OriginalTaskID", self.OriginalTaskID))
            sb.append("\"%s\" : \"%s\"," % ("IsDefaultVersion", self.IsDefaultVersion))
            sb.append("\"%s\" : \"%s\"," % ("Description", self.Description))
            sb.append("\"%s\" : \"%s\"," % ("ConcurrentInstances", self.ConcurrentInstances))
            sb.append("\"%s\" : \"%s\"," % ("QueueDepth", self.QueueDepth))
            sb.append("\"%s\" : \"%s\"," % ("NumberOfApprovedVersions", self.NumberOfApprovedVersions))
            sb.append("\"%s\" : \"%s\"," % ("MaxVersion", self.MaxVersion))
            sb.append("\"%s\" : \"%s\"," % ("NextMinorVersion", self.NextMinorVersion))
            sb.append("\"%s\" : \"%s\"," % ("NextMajorVersion", self.NextMajorVersion))
            sb.append("\"%s\" : \"%s\"" % ("UseConnectorSystem", self.UseConnectorSystem))
            
            if include_code:
                #codeblocks
                sb.append("\", Codeblocks\" : {")
                for name, cb in self.Codeblocks.iteritems():
                    sb.append(" \"%s\" : {\"Steps\" : {" % name)
    
                    steps = []
                    for order, st in cb.Steps.iteritems():
                        steps.append(" \"%s\" : %s" % (order, st.AsJSON()))
                    sb.append(",".join(steps))
                    sb.append("}")
                sb.append("}")
                sb.append("}")

            sb.append("}")
            return "".join(sb)
        except Exception as ex:
            raise ex

    def CheckDBExists(self):
        try:
            db = catocommon.new_conn()
            sSQL = """select task_id, original_task_id from task
                where (task_name = '%s' and version = '%s')
                or task_id = '%s'""" % (self.Name, self.Version, self.ID)
            dr = db.select_row_dict(sSQL)
            if dr:
                # PAY ATTENTION! 
                # if the task exists... it might have been by name/version, so...
                # we're setting the ids to the same as the database so it's more accurate.
                self.ID = dr["task_id"]
                self.OriginalTaskID = dr["original_task_id"]
                self.DBExists = True
        except Exception as ex:
            raise ex
        finally:
            db.close()
    
    @staticmethod    
    def SetAsDefault(task_id):
        """A static method, because it's not worth instantiating a whole task just to flip a switch."""
        try:
            db = catocommon.new_conn()
            
            sSQL = """update task set default_version = 0
                where original_task_id = 
                (select original_task_id from task where task_id = '%s')""" % task_id
            if not db.tran_exec_noexcep(sSQL):
                return False, db.error
            
            sSQL = """update task set default_version = 1 where task_id = '%s'""" % task_id
            if not db.tran_exec_noexcep(sSQL):
                return False, db.error

            db.tran_commit()

            return True, ""
        
        except Exception as ex:
            raise ex
        finally:
            db.close()
        
    def DBSave(self, db = None):
        try:
            #if a db connection is passed, use it, else create one
            bLocalTransaction = True
            if db:
                bLocalTransaction = False
            else:
                db = catocommon.new_conn()

            if not self.Name or not self.ID:
                if bLocalTransaction:
                    db.tran_rollback()
                return False, "ID and Name are required Task properties."

            if self.DBExists:
                #uh oh... this task exists.  unless told to do so, we stop here.
                if self.OnConflict == "cancel":
                    sErr = """Another Task with that ID or Name/Version exists.
                        [%s / %s / %s]
                        Conflict directive set to 'cancel'. (Default is 'cancel' if omitted.)""" % (self.ID, self.Name, self.Version)
                    if bLocalTransaction:
                        db.tran_rollback()

                    return False, sErr
                else:
                    #ok, what are we supposed to do then?
                    if self.OnConflict == "replace":
                        #whack it all so we can re-insert
                        #but by name or ID?  which was the conflict?
                        #no worries! the _DBExists function called when we created the object
                        #will have resolved any name/id issues.
                        #if the ID existed it doesn't matter, we'll be plowing it anyway.
                        #by "plow" I mean drop and recreate the codeblocks and steps... the task row will be UPDATED
                        sSQL = "delete from task_step_user_settings" \
                            " where step_id in" \
                            " (select step_id from task_step where task_id = '" + self.ID + "')"
                        if not db.tran_exec_noexcep(sSQL):
                            return False, db.error
                        sSQL = "delete from task_step where task_id = '" + self.ID + "'"
                        if not db.tran_exec_noexcep(sSQL):
                            return False, db.error
                        sSQL = "delete from task_codeblock where task_id = '" + self.ID + "'"
                        if not db.tran_exec_noexcep(sSQL):
                            return False, db.error
                        
                        #update the task row
                        sSQL = "update task set" \
                            " task_name = '" + catocommon.tick_slash(self.Name) + "'," \
                            " task_code = '" + catocommon.tick_slash(self.Code) + "'," \
                            " task_desc = '" + catocommon.tick_slash(self.Description) + "'," \
                            " task_status = '" + self.Status + "'," \
                            " concurrent_instances = '" + str(self.ConcurrentInstances) + "'," \
                            " queue_depth = '" + str(self.QueueDepth) + "'," \
                            " created_dt = now()," \
                            " parameter_xml = " + ("'" + catocommon.tick_slash(ET.tostring(self.ParameterXDoc)) + "'" if self.ParameterXDoc is None else "null") + \
                            " where task_id = '" + self.ID + "'"
                        if not db.tran_exec_noexcep(sSQL):
                            return False, db.error
                    elif self.OnConflict == "minor":   
                        self.IncrementMinorVersion()
                        self.DBExists = False
                        self.ID = catocommon.new_guid()
                        self.IsDefaultVersion = False
                        #insert the new version
                        sSQL = "insert task" \
                            " (task_id, original_task_id, version, default_version," \
                            " task_name, task_code, task_desc, task_status, parameter_xml, created_dt)" \
                            " values " \
                            " ('" + self.ID + "'," \
                            " '" + self.OriginalTaskID + "'," \
                            " " + self.Version + "," + " " \
                            " " + ("1" if self.IsDefaultVersion else "0") + "," \
                            " '" + catocommon.tick_slash(self.Name) + "'," \
                            " '" + catocommon.tick_slash(self.Code) + "'," \
                            " '" + catocommon.tick_slash(self.Description) + "'," \
                            " '" + self.Status + "'," \
                            " '" + catocommon.tick_slash(ET.tostring(self.ParameterXDoc)) + "'," \
                            " now())"
                        if not db.tran_exec_noexcep(sSQL):
                            return False, db.error
                    elif self.OnConflict == "major":
                        self.IncrementMajorVersion()
                        self.DBExists = False
                        self.ID = catocommon.new_guid()
                        self.IsDefaultVersion = False
                        #insert the new version
                        sSQL = "insert task" \
                            " (task_id, original_task_id, version, default_version," \
                            " task_name, task_code, task_desc, task_status, parameter_xml, created_dt)" \
                            " values " \
                            " ('" + self.ID + "'," \
                            " '" + self.OriginalTaskID + "'," \
                            " " + self.Version + "," \
                            " " + ("1" if self.IsDefaultVersion else "0") + "," \
                            " '" + catocommon.tick_slash(self.Name) + "'," \
                            " '" + catocommon.tick_slash(self.Code) + "'," \
                            " '" + catocommon.tick_slash(self.Description) + "'," \
                            " '" + self.Status + "'," \
                            " '" + catocommon.tick_slash(ET.tostring(self.ParameterXDoc)) + "'," \
                            " now())"
                        if not db.tran_exec_noexcep(sSQL):
                            return False, db.error
                    else:
                        #there is no default action... if the on_conflict didn't match we have a problem... bail.
                        return False, "There is an ID or Name/Version conflict, and the on_conflict directive isn't a valid option. (replace/major/minor/cancel)"
            else:
                #the default action is to ADD the new task row... nothing
                parameter_clause = " '',"
                if self.ParameterXDoc is not None:
                    parameter_clause = " '" + catocommon.tick_slash(ET.tostring(self.ParameterXDoc)) + "',"
                    
                sSQL = "insert task" \
                    " (task_id, original_task_id, version, default_version," \
                    " task_name, task_code, task_desc, task_status, parameter_xml, created_dt)" \
                    " values " + " ('" + self.ID + "'," \
                    "'" + self.OriginalTaskID + "'," \
                    " " + self.Version + "," \
                    " 1," \
                    " '" + catocommon.tick_slash(self.Name) + "'," \
                    " '" + catocommon.tick_slash(self.Code) + "'," \
                    " '" + catocommon.tick_slash(self.Description) + "'," \
                    " '" + self.Status + "'," \
                    + parameter_clause +  \
                    " now())"
                if not db.tran_exec_noexcep(sSQL):
                    return False, db.error

            #by the time we get here, there should for sure be a task row, either new or updated.                
            #now, codeblocks
            for c in self.Codeblocks.itervalues():
                sSQL = "insert task_codeblock (task_id, codeblock_name)" \
                    " values ('" + self.ID + "', '" + c.Name + "')"
                if not db.tran_exec_noexcep(sSQL):
                    return False, db.error

                #and steps
                if c.Steps:
                    order = 1
                    for s in c.Steps.itervalues():
                        sSQL = "insert into task_step (step_id, task_id, codeblock_name, step_order," \
                            " commented, locked," \
                            " function_name, function_xml)" \
                            " values ('" + s.ID + "'," \
                            "'" + self.ID + "'," \
                            "'" + s.Codeblock + "'," \
                            + str(order) + "," \
                            " " + ("1" if s.Commented else "0") + "," \
                            "0," \
                            "'" + s.FunctionName + "'," \
                            "'" + catocommon.tick_slash(ET.tostring(s.FunctionXDoc)) + "'" \
                            ")"
                        if not db.tran_exec_noexcep(sSQL):
                            return False, db.error
                        order += 1

            if bLocalTransaction:
                db.tran_commit()
                db.close()

            return True, ""

        except Exception as ex:
            return False, "Error updating the DB. " + ex.__str__()

    def Copy(self, iMode, sNewTaskName, sNewTaskCode):
        #iMode 0=new task, 1=new major version, 2=new minor version
        try:
            #NOTE: this routine is not very object-aware.  It works and was copied in here
            #so it can live with other relevant code.
            #may update it later to be more object friendly
            sSQL = ""
            sNewTaskID = catocommon.new_guid()
            iIsDefault = 0
            sTaskName = ""
            sOTID = ""

            #do it all in a transaction
            db = catocommon.new_conn()

            #figure out the new name and selected version
            sTaskName = self.Name
            sOTID = self.OriginalTaskID

            #figure out the new version
            if iMode == 0:
                #figure out the new name and selected version
                sSQL = "select count(*) from task where task_name = '" + sNewTaskName + "'"
                iExists = db.select_col_noexcep(sSQL)
                if db.error:
                    raise Exception("Unable to check name conflicts for  [" + sNewTaskName + "]." + db.error)
                sTaskName = (sNewTaskName + " (" + str(datetime.now()) + ")" if iExists > 0 else sNewTaskName)

                iIsDefault = 1
                self.Version = "1.000"
                sOTID = sNewTaskID
            elif iMode == 1:
                self.IncrementMajorVersion()
            elif iMode == 2:
                self.IncrementMinorVersion()
            else: #a iMode is required
                raise Exception("A mode required for this copy operation.")

            #if we are versioning, AND there are not yet any 'Approved' versions,
            #we set this new version to be the default
            #(that way it's the one that you get taken to when you pick it from a list)
            if iMode > 0:
                sSQL = "select case when count(*) = 0 then 1 else 0 end" \
                    " from task where original_task_id = '" + sOTID + "'" \
                    " and task_status = 'Approved'"
                iExists = db.select_col_noexcep(sSQL)
                if db.error:
                    db.tran_rollback()
                    raise Exception(db.error)

            #string sTaskName = (iExists > 0 ? sNewTaskName + " (" + DateTime.Now + ")" : sNewTaskName);
            #drop the temp tables.
            sSQL = "drop temporary table if exists _copy_task"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)
            sSQL = "drop temporary table if exists _step_ids"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)
            sSQL = "drop temporary table if exists _copy_task_codeblock"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)
            sSQL = "drop temporary table if exists _copy_task_step"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)

            #start copying
            sSQL = "create temporary table _copy_task select * from task where task_id = '" + self.ID + "'"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)

            #update the task_id
            sSQL = "update _copy_task set" \
                " task_id = '" + sNewTaskID + "'," \
                " original_task_id = '" + sOTID + "'," \
                " version = '" + str(self.Version) + "'," \
                " task_name = '" + sTaskName + "'," \
                " task_code = '" + (sNewTaskCode if sNewTaskCode else self.Code) + "'," \
                " default_version = " + str(iIsDefault) + "," \
                " task_status = 'Development'," \
                " created_dt = now()"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)

            #codeblocks
            sSQL = "create temporary table _copy_task_codeblock" \
                " select '" + sNewTaskID + "' as task_id, codeblock_name" \
                " from task_codeblock where task_id = '" + self.ID + "'"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)

            #USING TEMPORARY TABLES... need a place to hold step ids while we manipulate them
            sSQL = "create temporary table _step_ids" \
                " select distinct step_id, uuid() as newstep_id" \
                " from task_step where task_id = '" + self.ID + "'"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)

            #steps temp table
            sSQL = "create temporary table _copy_task_step" \
                " select step_id, '" + sNewTaskID + "' as task_id, codeblock_name, step_order, commented," \
                " locked, function_name, function_xml, step_desc" \
                " from task_step where task_id = '" + self.ID + "'"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)

            #update the step id
            sSQL = "update _copy_task_step a, _step_ids b" \
                " set a.step_id = b.newstep_id" \
                " where a.step_id = b.step_id"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)

            #update steps with codeblocks that reference a step (embedded steps)
            sSQL = "update _copy_task_step a, _step_ids b" \
                " set a.codeblock_name = b.newstep_id" \
                " where b.step_id = a.codeblock_name"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)

            #spin the steps and update any embedded step id's in the commands
            sSQL = "select step_id, newstep_id from _step_ids"
            dtStepIDs = db.select_all_dict(sSQL)
            if db.error:
                raise Exception("Unable to get step ids." + db.error)

            if dtStepIDs:
                for drStepIDs in dtStepIDs:
                    sSQL = "update _copy_task_step" \
                        " set function_xml = replace(lower(function_xml)," \
                        " '" + drStepIDs["step_id"].lower() + "'," \
                        " '" + drStepIDs["newstep_id"] + "')" \
                        " where function_name in ('if','loop','exists','while')"
                    if not db.tran_exec_noexcep(sSQL):
                        raise Exception(db.error)

            #finally, put the temp steps table in the real steps table
            sSQL = "insert into task select * from _copy_task"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)
            sSQL = "insert into task_codeblock select * from _copy_task_codeblock"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)
            sSQL = "insert into task_step" \
                " (step_id, task_id, codeblock_name, step_order, commented," \
                " locked, function_name, function_xml, step_desc)" \
                " select step_id, task_id, codeblock_name, step_order, commented," \
                " locked, function_name, function_xml, step_desc" \
                " from _copy_task_step"
            if not db.tran_exec_noexcep(sSQL):
                raise Exception(db.error)

            #finally, if we versioned up and we set this one as the new default_version,
            #we need to unset the other row
            if iMode > 0 and iIsDefault == 1:
                sSQL = "update task set default_version = 0 where original_task_id = '" + sOTID + "' and task_id <> '" + sNewTaskID + "'"
                if not db.tran_exec_noexcep(sSQL):
                    raise Exception(db.error)

            db.tran_commit()

            return sNewTaskID
        except Exception as ex:
            print(traceback.format_exc())
            raise ex
        finally:
            db.close()

    def PopulateTask(self, db, dr, IncludeUserSettings):
        # only called from inside this class, so the caller passed in a db conn pointer too
        try:
            #of course it exists...
            self.DBExists = True

            self.ID = dr["task_id"]
            self.Name = dr["task_name"]
            self.Code = dr["task_code"]
            self.Version = dr["version"]
            self.Status = dr["task_status"]
            self.OriginalTaskID = dr["original_task_id"]
            self.IsDefaultVersion = (True if dr["default_version"] == 1 else False)
            self.Description = (dr["task_desc"] if dr["task_desc"] else "")
            self.ConcurrentInstances = (dr["concurrent_instances"] if dr["concurrent_instances"] else "")
            self.QueueDepth = (dr["queue_depth"] if dr["queue_depth"] else "")
            self.UseConnectorSystem = (True if dr["use_connector_system"] == 1 else False)
            
            #parameters
            if dr["parameter_xml"]:
                xParameters = ET.fromstring(dr["parameter_xml"])
                if xParameters is not None:
                    self.ParameterXDoc = xParameters
            # 
            # * ok, this is important.
            # * there are some rules for the process of 'Approving' a task and other things.
            # * so, we'll need to know some count information
            # 
            sSQL = "select count(*) from task" \
                " where original_task_id = '" + self.OriginalTaskID + "'" \
                " and task_status = 'Approved'"
            iCount = db.select_col_noexcep(sSQL)
            if db.error:
                return "Error counting Approved versions:" + db.error
            self.NumberOfApprovedVersions = iCount

            sSQL = "select count(*) from task where original_task_id = '" + self.OriginalTaskID + "'"
            iCount = db.select_col_noexcep(sSQL)
            if db.error:
                return "Error counting Approved versions:" + db.error
            self.NumberOfOtherVersions = iCount

            sSQL = "select max(version) from task where original_task_id = '" + self.OriginalTaskID + "'"
            sMax = db.select_col_noexcep(sSQL)
            if db.error:
                return "Error getting max version:" + db.error
            self.MaxVersion = sMax
            self.NextMinorVersion = str(float(self.MaxVersion) + .001)
            self.NextMajorVersion = str(int(float(self.MaxVersion) + 1)) + ".000"

            #now, the fun stuff
            #1 get all the codeblocks and populate that dictionary
            #2 then get all the steps... ALL the steps in one sql
            #..... and while spinning them put them in the appropriate codeblock
            #GET THE CODEBLOCKS
            sSQL = "select codeblock_name from task_codeblock where task_id = '" + self.ID + "' order by codeblock_name"
            dtCB = db.select_all_dict(sSQL)
            if dtCB:
                for drCB in dtCB:
                    cb = Codeblock(drCB["codeblock_name"])
                    self.Codeblocks[cb.Name] = cb
            else:
                #uh oh... there are no codeblocks!
                #since all tasks require a MAIN codeblock... if it's missing,
                #we can just repair it right here.
                sSQL = "insert task_codeblock (task_id, codeblock_name) values ('" + self.ID + "', 'MAIN')"
                if not db.exec_db_noexcep(sSQL):
                    raise Exception(db.error)
                self.Codeblocks["MAIN"] = Codeblock("MAIN")

            #GET THE STEPS
            #we need the userID to get the user settings in some cases
            if IncludeUserSettings:
                sUserID = uiCommon.GetSessionUserID()
                #NOTE: it may seem like sorting will be an issue, but it shouldn't.
                #sorting ALL the steps by their order here will ensure they get added to their respective 
                # codeblocks in the right order.
                sSQL = "select s.step_id, s.step_order, s.step_desc, s.function_name, s.function_xml, s.commented, s.locked, codeblock_name," \
                    " us.visible, us.breakpoint, us.skip, us.button" \
                    " from task_step s" \
                    " left outer join task_step_user_settings us on us.user_id = '" + sUserID + "' and s.step_id = us.step_id" \
                    " where s.task_id = '" + self.ID + "'" \
                    " order by s.step_order"
            else:
                sSQL = "select s.step_id, s.step_order, s.step_desc, s.function_name, s.function_xml, s.commented, s.locked, codeblock_name," \
                    " 0 as visible, 0 as breakpoint, 0 as skip, '' as button" \
                    " from task_step s" \
                    " where s.task_id = '" + self.ID + "'" \
                    " order by s.step_order"

            dtSteps = db.select_all_dict(sSQL)
            if dtSteps:
                for drSteps in dtSteps:
                    oStep = Step.FromRow(drSteps, self)
                    # the steps dictionary for each codeblock uses the ORDER, not the STEP ID, as the key
                    # this way, we can order the dictionary.
                    
                    # maybe this should just be a list?
                    if oStep:
                        # just double check that the codeblocks match
                        if self.Codeblocks.has_key(oStep.Codeblock):
                            self.Codeblocks[oStep.Codeblock].Steps[oStep.Order] = oStep
                        else:
                            print("WARNING: Step thinks it belongs in codeblock [%s] but this task doesn't have that codeblock." % (oStep.Codeblock if oStep.Codeblock else "NONE"))
        except Exception as ex:
            raise ex

    def IncrementMajorVersion(self):
        self.Version = str(int(float(self.MaxVersion) + 1)) + ".000"
        self.NextMinorVersion = str(float(self.Version) + .001)
        self.NextMajorVersion = str(int(float(self.MaxVersion) + 2)) + ".000"

    def IncrementMinorVersion(self):
        self.Version = str(float(self.MaxVersion) + .001)
        self.NextMinorVersion = str(float(self.Version) + .001)
        self.NextMajorVersion = str(int(float(self.MaxVersion) + 1)) + ".000"

class Codeblock(object):
    def __init__(self, sName):
        self.Name = sName
        self.Steps = {}
        
    #a codeblock contains a dictionary collection of steps
    def FromXML(self, sCBXML=""):
        if sCBXML == "": return None
        xCB = ET.fromstring(sCBXML)
        
        self.Name = xCB.attrib["name"]
        
        #STEPS
        xSteps = xCB.findall("steps/step")
        uiCommon.log("Number of Steps in [" +self.Name + "]: " + str(len(xSteps)), 4)
        order = 1
        for xStep in xSteps:
            newstep = Step()
            newstep.FromXML(ET.tostring(xStep), self.Name)
            self.Steps[order] = newstep
            order += 1

class Step(object):
    def __init__(self):
        self.ID = ""
        self.Codeblock = ""
        self.Order = 0
        self.Description = ""
        self.Commented = False
        self.Locked = False
        self.OutputParseType = 0
        self.OutputRowDelimiter = 0
        self.OutputColumnDelimiter = 0
        self.FunctionXDoc = None
        self.FunctionName = ""
        self.UserSettings = StepUserSettings()
        # this property isn't added by the "Populate" methods - but can be added manually.
        # this is because of xml import/export - where the function details aren't required.
        # but they are in the UI when drawing steps.
        self.Function = None 
        # Very rarely does a single Step object have an associated parent Task.
        # usually, we're working on steps within the context of already knowing the Task.
        # but if it's needed, it will have been explicitly populated.
        self.Task = None
        # most steps won't even have this - only manually created ones for "embedded" steps
        self.XPathPrefix = ""
        
        # if an error occured parsing, this step will be invalid
        # this property notes that
        self.IsValid = True
        
    def AsJSON(self):
        try:
            sb = []
            sb.append("{")
            sb.append("\"%s\" : \"%s\"," % ("ID", self.ID))
            sb.append("\"%s\" : \"%s\"," % ("Codeblock", self.Codeblock))
            sb.append("\"%s\" : \"%s\"," % ("Order", self.Order))
            sb.append("\"%s\" : \"%s\"," % ("Description", self.Description))
            sb.append("\"%s\" : \"%s\"," % ("Commented", self.Commented))
            sb.append("\"%s\" : \"%s\"," % ("Locked", self.Locked))
            sb.append("\"%s\" : \"%s\"," % ("OutputParseType", self.OutputParseType))
            sb.append("\"%s\" : \"%s\"," % ("OutputRowDelimiter", self.OutputRowDelimiter))
            sb.append("\"%s\" : \"%s\"," % ("OutputColumnDelimiter", self.OutputColumnDelimiter))
            sb.append("\"%s\" : \"%s\"" % ("FunctionName", self.FunctionName))
            sb.append("}")
            return "".join(sb)        
        except Exception as ex:
            raise ex

    def FromXML(self, sStepXML="", sCodeblockName=""):
        if sStepXML == "": return None
        if sCodeblockName == "": return None
        
        xStep = ET.fromstring(sStepXML)
        
        #attributes of the <step> node
        self.ID = xStep.get("id", str(uuid.uuid4()))
        self.Order = xStep.get("order", 0)
        self.Codeblock = sCodeblockName
        self.Commented = catocommon.is_true(xStep.get("commented", ""))
        self.OutputParseType = int(xStep.get("output_parse_method", 0))
        self.OutputRowDelimiter = int(xStep.get("output_row_delimiter", 0))
        self.OutputColumnDelimiter = int(xStep.get("output_column_delimiter", 0))

        _desc = xStep.findtext("description", "")
        self.Description = _desc if _desc is not None else ""

        # FUNCTION
        xFunc = xStep.find("function")
        if xFunc is None:
            raise Exception("ERROR: Step [%s] - function xml is empty or cannot be parsed.")
        
        self.FunctionXDoc = xFunc
        # command_type is for backwards compatilibity in importing tasks from 1.0.8
        self.FunctionName = xFunc.get("name", xFunc.get("command_type", ""))
    
    @staticmethod
    def FromRow(dr, task):
        s = Step()
        s.PopulateStep(dr, task)
        return s
        
    @staticmethod
    def FromID(sStepID):
        """
        Gets a single step object, *without* user settings.  Does NOT have an associated parent Task object.
        This is called by functions *on* the task page where we don't need
        the associated task object.
        """
        try:
            sSQL = """select s.step_id, s.step_order, s.step_desc, s.function_name, s.function_xml, s.commented, s.locked, s.codeblock_name
                from task_step s
                where s.step_id = '%s' limit 1""" %sStepID
            db = catocommon.new_conn()
            row = db.select_row_dict(sSQL)
            if row:
                oStep = Step.FromRow(row, None)
                return oStep

            if db.error:
                uiCommon.log("Error getting Step by ID: " + db.error, 2)
            
            return None
        except Exception as ex:
            raise ex
        finally:
            db.close()
        
    @staticmethod
    def FromIDWithSettings(sStepID, sUserID):
        """
        Gets a single step object, including user settings.  Does NOT have an associated parent Task object.
        This is called by the AddStep methods, and other functions *on* the task page where we don't need
        the associated task object
        """
        try:
            sSQL = """select s.step_id, s.step_order, s.step_desc, s.function_name, s.function_xml, s.commented, s.locked, s.codeblock_name,
                us.visible, us.breakpoint, us.skip, us.button
                from task_step s
                left outer join task_step_user_settings us on us.user_id = '%s' and s.step_id = us.step_id
                where s.step_id = '%s' limit 1""" % (sUserID, sStepID)
            db = catocommon.new_conn()
            row = db.select_row_dict(sSQL)
            if row:
                oStep = Step.FromRow(row, None)
                return oStep

            if db.error:
                uiCommon.log("Error getting Step by ID: " + db.error, 2)
            
            return None
        except Exception as ex:
            raise ex
        finally:
            db.close()
        
    def PopulateStep(self, dr, oTask):
        try:
            self.ID = dr["step_id"]
            self.Codeblock = ("" if not dr["codeblock_name"] else dr["codeblock_name"])
            self.Order = dr["step_order"]
            self.Description = ("" if not dr["step_desc"] else dr["step_desc"])
            self.Commented = (True if dr["commented"] == 1 else False)
            self.Locked = (True if dr["locked"] == 1 else False)
            func_xml = ("" if not dr["function_xml"] else dr["function_xml"])
            #once parsed, it's cleaner.  update the object with the cleaner xml
            if func_xml:
                try:
                    self.FunctionXDoc = ET.fromstring(func_xml)
                    
                    # what's the output parse type?
                    self.OutputParseType = int(self.FunctionXDoc.get("parse_method", 0))
                    
                    # if the output parse type is "2", we need row and column delimiters too!
                    #if self.OutputParseType == 2:
                    # but hey! why bother checking, just read 'em anyway.  Won't hurt anything.
                    self.OutputRowDelimiter = int(self.FunctionXDoc.get("row_delimiter", 0))
                    self.OutputColumnDelimiter = int(self.FunctionXDoc.get("col_delimiter", 0))
                except ET.ParseError:
                    self.IsValid = False
                    print(traceback.format_exc())    
                    print("CRITICAL: Unable to parse function xml in step [%s]." % self.ID)
                except Exception:
                    self.IsValid = False
                    print(traceback.format_exc())  
                    print("CRITICAL: Exception in processing step [%s]." % self.ID)

            #this.Function = Function.GetFunctionByName(dr["function_name"]);
            self.FunctionName = dr["function_name"]

            # user settings, if available
            if dr.has_key("button"):
                self.UserSettings.Button = (dr["button"] if dr["button"] else "")
            if dr.has_key("skip"):
                self.UserSettings.Skip = (dr["skip"] if dr["skip"] else "0")
            if dr.has_key("visible"):
                self.UserSettings.Visible = (dr["visible"] if dr["visible"] else "1")
            
            #NOTE!! :oTask can possibly be null, in lots of cases where we are just getting a step and don't know the task.
            #if it's null, it will not populate the parent object.
            #this happens all over the place in the HTMLTemplates stuff, and we don't need the extra overhead of the same task
            #object being created hundreds of times.
            if oTask:
                self.Task = oTask
            else:
                #NOTE HACK TODO - this is bad and wrong
                #we shouldn't assume the datarow was a join to the task table... but in a few places it was.
                #so we're populating some stuff here.
                #the right approach is to create a full Task object from the ID, but we need to analyze
                #how it's working, so we don't create a bunch more database hits.
                #I THINK THIS is only happening on GetSingleStep and taskStepVarsEdit, but double check.
                self.Task = Task()
                if dr.has_key("task_id"):
                    self.Task.ID = dr["task_id"]
                if dr.has_key("task_name"):
                    self.Task.Name = dr["task_name"]
                if dr.has_key("version"):
                    self.Task.Version = dr["version"]
            return self
        except Exception as ex:
            raise ex
        
class StepUserSettings(object):
    def __init__(self):
        self.Visible = True
        self.Breakpoint= False
        self.Skip = False
        self.Button = ""


