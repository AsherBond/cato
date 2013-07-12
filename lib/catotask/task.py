
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
from catolog import catolog
logger = catolog.get_logger(__name__)

import traceback
import json

from catocommon import catocommon
from datetime import datetime
from catoerrors import InfoException

# Note: this is not a container for Task objects - it's just a rowset from the database
# with an AsJSON method.
# why? Because we don't need a full object for list pages and dropdowns.
class Tasks(object):
    rows = {}
    def __init__(self, sFilter="", show_all_versions=False):
        db = catocommon.new_conn()
        sWhereString = ""
        if sFilter:
            aSearchTerms = sFilter.split()
            for term in aSearchTerms:
                if term:
                    sWhereString += " and (t.task_name like '%%" + term + "%%' " \
                        "or t.task_code like '%%" + term + "%%' " \
                        "or t.task_desc like '%%" + term + "%%' " \
                        "or t.task_status like '%%" + term + "%%') "

        if show_all_versions:
            sSQL = """select 
                t.task_id as ID, 
                t.original_task_id as OriginalTaskID, 
                t.task_name as Name, 
                t.task_code as Code, 
                t.task_desc as Description, 
                t.version as Version, 
                t.task_status as Status,
                (select count(*) from task where original_task_id = t.original_task_id) as Versions,
                group_concat(ot.tag_name order by ot.tag_name separator ',') as Tags
                from task t
                left outer join object_tags ot on t.original_task_id = ot.object_id
                where 1=1 %s group by t.task_id, t.version order by t.task_code, t.version""" % sWhereString
        else:
            sSQL = """select 
                t.task_id as ID, 
                t.original_task_id as OriginalTaskID, 
                t.task_name as Name, 
                t.task_code as Code, 
                t.task_desc as Description, 
                t.version as Version, 
                t.task_status as Status,
                (select count(*) from task where original_task_id = t.original_task_id) as Versions,
                group_concat(ot.tag_name order by ot.tag_name separator ',') as Tags
                from task t
                left outer join object_tags ot on t.original_task_id = ot.object_id
                where t.default_version = 1 %s group by t.original_task_id order by t.task_code""" % sWhereString
        
        self.rows = db.select_all_dict(sSQL)
        db.close()

    def AsJSON(self):
        return catocommon.ObjectOutput.IterableAsJSON(self.rows)

    def AsXML(self):
        return catocommon.ObjectOutput.IterableAsXML(self.rows, "Tasks", "Task")

    def AsText(self, delimiter=None, headers=None):
        return catocommon.ObjectOutput.IterableAsText(self.rows, ['Code', 'Name', 'Version', 'Status'], delimiter, headers)

    @staticmethod
    def Delete(ids, force=False):
        """
        Delete a list of tasks.
        
        Done here instead of in the Task class - no point to instantiate a task just to delete it.
        """
        db = catocommon.new_conn()
        
        delete_ids = ",".join(ids) 

        tasks_with_history = ""
        task_ids = ""
        if not force:
            # first we need a list of tasks that will not be deleted
            sql = """select task_name from task t
                    where t.original_task_id in (%s)
                    and (
                    t.task_id in (select ti.task_id from task_instance ti where ti.task_id = t.task_id)
                    )""" % delete_ids 
            tasks_with_history = db.select_csv(sql, True)
    
            # build a list of tasks that CAN be deleted because they have no history
            # ... 'delete_ids' is an array of 'original_task_id' - we need an array of 'task_id'
            sql = """select t.task_id from task t
                where t.original_task_id in (%s)
                and t.task_id not in 
                (select ti.task_id from task_instance ti where ti.task_id = t.task_id)""" % delete_ids
            task_ids = db.select_csv(sql, True)
        else:
            # force is True, just build a list of all task_ids for the provided original_task_ids
            sql = """select t.task_id from task t
                where t.original_task_id in (%s)""" % delete_ids
            task_ids = db.select_csv(sql, True)
            
            
        # do we have a list of task_ids to delete? 
        if task_ids:
            sql = "delete from action_schedule where task_id in (%s)" % (task_ids)
            db.tran_exec(sql)

            sql = "delete from action_plan_history where task_id in (%s)" % (task_ids)
            db.tran_exec(sql)

            sql = "delete from action_plan where task_id in (%s)" % (task_ids)
            db.tran_exec(sql)

            sql = """delete from task_step_user_settings
                where step_id in
                (select step_id from task_step where task_id in (%s))""" % (task_ids)
            db.tran_exec(sql)

            sql = "delete from task_step where task_id in (%s)" % (task_ids)
            db.tran_exec(sql)

            sql = "delete from task_codeblock where task_id in (%s)" % (task_ids)
            db.tran_exec(sql)

            sql = "delete from task where task_id in (%s)" % (task_ids)
            db.tran_exec(sql)

            db.tran_commit()
        
        db.close()

        if tasks_with_history:
            raise InfoException("Tasks [%s] have history rows and could not be deleted.  Provide the option to force deletion." % tasks_with_history)
        
        return True

    @staticmethod
    def Export(task_ids, include_refs, outformat="xml"):
        """
        This function creates an xml export document of all tasks specified in otids.  
        
        If the "include_refs" flag is set, each task is scanned for additional
        references, and they are included in the export.
        
        This returns a list of xml documents - one per task.
        """
        
        tasks = []
        
        for tid in task_ids:
            # get the task
            t = Task()
            t.FromID(tid)
            if t:
                tasks.append(t)

                # regarding references, here's the deal
                # in a while loop, we check the references for each task in the array
                # UNTIL THE 'task_ids' LIST STOPS GROWING.
                if catocommon.is_true(include_refs):
                    reftasks = t.GetReferencedTasks()
                    for reftask in reftasks:
                        if reftask.ID not in task_ids:
                            task_ids.append(reftask.ID)


        # this is VERY IMPORTANT - exported tasks must have identifiers removed from them.
        # otherwise, downstream attempts to import might have issues.
        docs = []
        for t in tasks:
            if outformat == "json":
                del t.ID
                for c in t.Codeblocks.itervalues():
                    for s in c.Steps.itervalues():
                        del s.ID
                docs.append(t.AsJSON(include_code=True))
            else:
                docs.append(t.AsXML(include_code=True))

        return docs

        
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
        self.OnConflict = "cancel"  # the default behavior for all conflicts is to cancel the operation
        self.UseConnectorSystem = False
        self.IsDefaultVersion = False
        self.ConcurrentInstances = ""
        self.QueueDepth = ""
        self.ParameterXDoc = None
        self.NumberOfApprovedVersions = 0
        self.MaxVersion = "1.000"
        self.NextMinorVersion = "1.001"
        self.NextMajorVersion = "2.000"
        # a task has a dictionary of codeblocks
        self.Codeblocks = {}
        # in a very few cases getting a Task for a specific user may include some user settings
        # if so this will contain a user id.
        self.IncludeSettingsForUser = None

    @staticmethod
    def DBCreateNew(sName, sCode, sDesc):
        # This function is for creating a simple, new Task (invoked by the UI or API).
        # DBSave is used for import and conflict resolution - it's far more complex than we need 
        # for when a user manually requests to create a Task.
        if not sName:
            raise InfoException("Error building Task object: Name is required.")

        db = catocommon.new_conn()
        ID = catocommon.new_guid()

        sql = """insert task
            (task_id, original_task_id, version, default_version, task_name, task_code, task_desc, created_dt)
            values
            (%s, %s, 1.000, 1, %s, %s, %s, now())"""
        if not db.exec_db_noexcep(sql, (ID, ID, sName, sCode, sDesc)):
            if db.error == "key_violation":
                raise Exception("A Task with that name already exists.  Please select another name.")
            else: 
                raise Exception(db.error)

        sql = "insert task_codeblock (task_id, codeblock_name) values (%s, 'MAIN')"
        db.exec_db_noexcep(sql, (ID))

        db.close()
        
        t = Task()
        t.FromID(ID)
        return t
                
    def FromID(self, sTaskID, bIncludeUserSettings=False, include_code=True):
        db = catocommon.new_conn()
        sSQL = """select task_id, original_task_id, task_name, task_code, task_status, version, default_version,
                task_desc, use_connector_system, concurrent_instances, queue_depth, parameter_xml
                from task
                where task_id = %s"""

        dr = db.select_row_dict(sSQL, (sTaskID))
        db.close()
        if not dr:
            raise InfoException("Unable to find Task for ID [%s]" % sTaskID)

        self.PopulateTask(dr, include_code)

    def FromNameVersion(self, name, version=None, include_code=True):
        db = catocommon.new_conn()
        version_clause = ""

        if version:
            version_clause = " and version = %s" % version
        else:
            version_clause = " and default_version = 1"
            
        sSQL = """select task_id, original_task_id, task_name, task_code, task_status, version, default_version,
                task_desc, use_connector_system, concurrent_instances, queue_depth, parameter_xml
                from task
                where (task_name = '%s') %s""" % (name, version_clause)
        dr = db.select_row_dict(sSQL)
        db.close()

        if not dr:
            raise InfoException("Unable to find Task for [%s / %s]" % (name, version))
        
        self.PopulateTask(dr, include_code)

    def FromOriginalIDVersion(self, otid, version=None, include_code=True):
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
        db.close()

        if not dr:
            raise InfoException("Unable to find Task for Original ID/Version [%s/%s]" % (otid, version))
        
        self.PopulateTask(dr, include_code)

    def FromXML(self, sTaskXML, onconflict=None):
        if not sTaskXML: return None
        
        xmlerr = "XML Error: Attribute not found."
        
        logger.debug("Building a Task object from XML")
        xTask = catocommon.ET.fromstring(sTaskXML)
        
        # if the taskjson has an onconflict directive use it....
        # BUT ONLY IF None WAS PROVIDED
        self.OnConflict = xTask.get("on_conflict", "cancel")
        if onconflict:
            self.OnConflict = onconflict
        logger.debug("On a conflict, we will [%s]" % (self.OnConflict))

        # attributes of the <task> node
        
        # NOTE: id is ALWAYS NEW from xml.  If it matches an existing task by name, that'll be figured out
        # in CheckDBExists below.
        self.ID = catocommon.new_guid()
        
        # original task id is specific to the system where this was originally created.
        # for xml imports, this is a NEW task by default.
        # if the user changes 'on_conflict' to either replace or version up
        # the proper original task id will be resolved by that branch of DBSave
        self.OriginalTaskID = self.ID
        
        self.Name = xTask.get("name", xmlerr)
        logger.debug("    %s" % (self.Name))
        self.Code = xTask.get("code", xmlerr)
        
        # these, if not provided, have initial defaults
        self.Version = xTask.get("version", "1.000")
        self.Status = xTask.get("status", "Development")
        self.IsDefaultVersion = True
        self.ConcurrentInstances = xTask.get("concurrent_instances", "")
        self.QueueDepth = xTask.get("queue_depth", "")
        
        # text nodes in the <task> node
        _desc = xTask.find("description").text
        self.Description = _desc if _desc is not None else ""
        
        # do we have a conflict?
        self.CheckDBExists()
        
        # CODEBLOCKS
        xCodeblocks = xTask.findall("codeblocks/codeblock")
        logger.debug("Number of Codeblocks: " + str(len(xCodeblocks)))
        for xCB in xCodeblocks:
            cbname = xCB.get("name", "")
            if not cbname:
                logger.error("Codeblock 'name' attribute is required.", 1)
        
            newcb = Codeblock(self.ID, cbname)
            newcb.FromXML(catocommon.ET.tostring(xCB))
            self.Codeblocks[newcb.Name] = newcb
            
        # PARAMETERS
        self.ParameterXDoc = xTask.find("parameters")

    def FromJSON(self, taskjson, onconflict=None):
        logger.debug("Building a Task object from JSON.")
        
        t = json.loads(taskjson)
        
        # if the taskjson has an onconflict directive use it....
        # BUT ONLY IF None WAS PROVIDED
        self.OnConflict = t.get("OnConflict", "cancel") 
        if onconflict:
            self.OnConflict = onconflict
        logger.debug("On a conflict, we will [%s]" % (self.OnConflict))

        # NOTE: id is ALWAYS NEW from xml.  If it matches an existing task by name, that'll be figured out
        # in CheckDBExists below.
        self.ID = catocommon.new_guid()
        
        # original task id is specific to the system where this was originally created.
        # for xml imports, this is a NEW task by default.
        # if the user changes 'on_conflict' to either replace or version up
        # the proper original task id will be resolved by that branch of DBSave
        self.OriginalTaskID = self.ID
        
        self.Name = t.get("Name")
        logger.debug("    %s" % (self.Name))
        self.Code = t.get("Code")
        
        # these, if not provided, have initial defaults
        self.Version = t.get("Version", "1.000")
        self.Status = t.get("Status", "Development")
        self.IsDefaultVersion = True
        self.ConcurrentInstances = t.get("ConcurrentInstances", "")
        self.QueueDepth = t.get("QueueDepth", "")
        
        self.Description = t.get("Description", "")
        
        # do we have a conflict?
        self.CheckDBExists()
        
        # CODEBLOCKS
        codeblocks = t.get("Codeblocks", [])
        logger.debug("Number of Codeblocks: %s" % (len(codeblocks)))
        for cb in codeblocks:
            cbname = cb.get("Name")
            if not cbname:
                raise Exception("Codeblock 'Name' attribute is required.")
        
            newcb = Codeblock(self.ID, cbname)
            newcb.FromDict(cb)
            self.Codeblocks[newcb.Name] = newcb
            
        # PARAMETERS
        if t.get("Parameters"):
            self.ParameterXDoc = catocommon.ET.fromstring(t.get("Parameters"))
            

    def AsText(self, delimiter=None, headers=None):
        return catocommon.ObjectOutput.AsText(self, ["Code", "Name", "Version", "Description", "Status", "IsDefaultVersion"], delimiter, headers)

    def AsXML(self, include_code=False):
        root = catocommon.ET.fromstring('<task />')
        
        root.set("original_task_id", self.OriginalTaskID)
        root.set("name", str(self.Name))
        root.set("code", str(self.Code))
        root.set("version", str(self.Version))
        root.set("status", str(self.Status))
        root.set("concurrent_instances", str(self.ConcurrentInstances))
        root.set("queue_depth", str(self.QueueDepth))

        catocommon.ET.SubElement(root, "description").text = self.Description
        
        # PARAMETERS
        if self.ParameterXDoc is not None:
            root.append(self.ParameterXDoc)
        
        # CODEBLOCKS
        xCodeblocks = catocommon.ET.SubElement(root, "codeblocks")  # add the codeblocks section
        
        if include_code:
            for name, cb in self.Codeblocks.items():
                xCB = catocommon.ET.SubElement(xCodeblocks, "codeblock")  # add the codeblock
                xCB.set("name", name)
                
                # STEPS
                xSteps = catocommon.ET.SubElement(xCB, "steps")  # add the steps section
                
                for s in cb.Steps:
                    stp = cb.Steps[s]
                    xStep = catocommon.ET.SubElement(xSteps, "step")  # add the step
                    xStep.set("codeblock", str(stp.Codeblock))
                    xStep.set("output_parse_type", str(stp.OutputParseType))
                    xStep.set("output_column_delimiter", str(stp.OutputColumnDelimiter))
                    xStep.set("output_row_delimiter", str(stp.OutputRowDelimiter))
                    xStep.set("commented", str(stp.Commented).lower())
    
                    catocommon.ET.SubElement(xStep, "description").text = stp.Description
                    
                    xStep.append(stp.FunctionXDoc)
        
        return catocommon.ET.tostring(root)

    def AsJSON(self, include_code=False):
        t = {
            "Name" : self.Name,
            "Code" : self.Code,
            "Version" : self.Version,
            "Status" : self.Status,
            "OriginalTaskID" : self.OriginalTaskID,
            "IsDefaultVersion" : self.IsDefaultVersion,
            "Description" : self.Description,
            "ConcurrentInstances" : self.ConcurrentInstances,
            "QueueDepth" : self.QueueDepth,
            "NumberOfApprovedVersions" : self.NumberOfApprovedVersions,
            "MaxVersion" : self.MaxVersion,
            "NextMinorVersion" : self.NextMinorVersion,
            "NextMajorVersion" : self.NextMajorVersion,
            "UseConnectorSystem" : self.UseConnectorSystem
        }
        if hasattr(self, "ID"):
            t["ID"] = self.ID
        
        if include_code:
            # parameters
            t["Parameters"] = catocommon.ET.tostring(self.ParameterXDoc) if self.ParameterXDoc is not None else ""
            
            # codeblocks
            codeblocks = []
            for name, cb in self.Codeblocks.items():
                steps = []
                for st in cb.Steps.itervalues():
                    steps.append(json.loads(st.AsJSON()))
                codeblocks.append({ "Name" : name, "Steps" : steps })

            t["Codeblocks"] = codeblocks

        return catocommon.ObjectOutput.AsJSON(t)
    
    def CheckDBExists(self):
        db = catocommon.new_conn()
        sSQL = """select task_id, original_task_id from task
            where (task_name = %s and version = %s)
            or task_id = %s"""
        dr = db.select_row_dict(sSQL, (self.Name, self.Version, self.ID))
        db.close()
        if dr:
            # PAY ATTENTION! 
            # if the task exists... it might have been by name/version, so...
            # we're setting the ids to the same as the database so it's more accurate.
            self.ID = dr["task_id"]
            self.OriginalTaskID = dr["original_task_id"]
            self.DBExists = True
    
    def GetReferencedTasks(self):
        """
        does a scan of the function xml and returns a list of all referenced tasks
        """
        logger.debug("Analyzing [%s] for references..." % self.Name)

        db = catocommon.new_conn()
        tasks = []
        
        # get all the runtask/subtask references on this task
        sSQL = """select function_xml from task_step
            where (function_xml like '%%run_task%%' or function_xml like '%%subtask%%')
            and task_id=%s
            order by step_order"""
        rows = db.select_all_dict(sSQL, (self.ID))
        if rows:
            for dr in rows:
                try:
                    xFunc = catocommon.ET.fromstring(dr["function_xml"])
                except:
                    logger.error("Unable to parse function_xml for task [%s]. %s" % (self.Name, dr["function_xml"]))

                tn = ""
                tv = ""

                # annoying, but we gotta check both the root function, and possibly nested functions
                if xFunc.get("name", "") in ["subtask", "run_task"]:
                    # it's a direct function
                    tn = xFunc.findtext("task_name", "")
                    tv = xFunc.findtext("version", "")
                else:
                    # ok, so this isn't a runtask/subtask... but the query matched!
                    # so... it's gotta be an embedded command
                    # check for subtasks
                    for x in xFunc.findall(".//function[@name='subtask']"):
                        tn = x.findtext("task_name", "")
                        tv = x.findtext("version", "")
                    # again for run_task
                    for x in xFunc.findall(".//function[@name='run_task']"):
                        tn = x.findtext("task_name", "")
                        tv = x.findtext("version", "")

                if tn:
                    # I hate instantiating a Task in this loop, but how else would we?  We need to return the original_task_id
                    reftask = Task()
                    reftask.FromNameVersion(tn, tv, False)
                    if reftask.Name:
                        tasks.append(reftask)
                    else:
                        logger.warning("    Found a reference to [%s], but unable to instantiate it." % tn)

                    logger.debug("    Task [%s/%s] references Task [%s/%s]." % (self.Name, self.Version, reftask.Name, reftask.Version))

        db.close()
        
        return tasks
    
    @staticmethod    
    def SetAsDefault(task_id):
        """A static method, because it's not worth instantiating a whole task just to flip a switch."""
        db = catocommon.new_conn()
        
        sSQL = "select original_task_id from task where task_id = '%s'" % task_id
        otid = db.select_col(sSQL)
        
        sSQL = "update task set default_version = 0 where original_task_id = '%s'" % otid
        db.tran_exec(sSQL)
        
        sSQL = """update task set default_version = 1 where task_id = '%s'""" % task_id
        db.tran_exec(sSQL)

        db.tran_commit()
        db.close()

        return True
        
    def DBSave(self, db=None):
        # if a db connection is passed, use it, else create one
        bLocalTransaction = True
        if db:
            bLocalTransaction = False
        else:
            db = catocommon.new_conn()

        if not self.Name or not self.ID:
            if bLocalTransaction:
                db.tran_rollback()
            return False, "ID and Name are required Task properties."

        # this could be used in many cases below...
        parameter_clause = ""
        if self.ParameterXDoc is not None:
            parameter_clause = catocommon.ET.tostring(self.ParameterXDoc)
        
        
        if self.DBExists:
            # uh oh... this task exists.  unless told to do so, we stop here.
            if self.OnConflict == "cancel":
                sErr = """Another Task with that ID or Name/Version exists.
                    [%s / %s / %s]
                    Conflict directive set to 'cancel'. (Default is 'cancel' if omitted.  Valid options are 'cancel', 'replace', 'minor', 'major'.)
                    New version numbers *cannot* be explicitly specified, and 1.000 is assumed if omitted.  
                    Use 'minor' or 'major' to create a new version.""" % (self.ID, self.Name, self.Version)
                if bLocalTransaction:
                    db.tran_rollback()

                return False, sErr
            else:
                # ok, what are we supposed to do then?
                if self.OnConflict == "replace":
                    # whack it all so we can re-insert
                    # but by name or ID?  which was the conflict?
                    # no worries! the _DBExists function called when we created the object
                    # will have resolved any name/id issues.
                    # if the ID existed it doesn't matter, we'll be plowing it anyway.
                    # by "plow" I mean drop and recreate the codeblocks and steps... the task row will be UPDATED
                    sSQL = """delete from task_step_user_settings
                        where step_id in
                        (select step_id from task_step where task_id = %s)"""
                    db.tran_exec(sSQL, (self.ID))
                    sSQL = "delete from task_step where task_id = %s"
                    db.tran_exec(sSQL, (self.ID))
                    sSQL = "delete from task_codeblock where task_id = %s"
                    db.tran_exec(sSQL, (self.ID))
                    
                    # update the task row
                    sSQL = """update task set
                        task_name = %s,
                        task_code = %s,
                        task_desc = %s,
                        task_status = %s,
                        concurrent_instances = %s,
                        queue_depth = %s,
                        created_dt = now(),
                        parameter_xml = %s
                        where task_id = %s"""
                    db.tran_exec(sSQL, (self.Name, self.Code, self.Description, self.Status,
                                        self.ConcurrentInstances, self.QueueDepth, parameter_clause, self.ID))

                elif self.OnConflict == "minor":   
                    self.IncrementMinorVersion()
                    self.DBExists = False
                    self.ID = catocommon.new_guid()
                    self.IsDefaultVersion = False
                    # insert the new version
                    sSQL = """insert task
                        (task_id, original_task_id, version, default_version,
                        task_name, task_code, task_desc, task_status, parameter_xml, created_dt)
                        values
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s,now())"""
                    db.tran_exec(sSQL, (self.ID, self.OriginalTaskID, self.Version, ("1" if self.IsDefaultVersion else "0"),
                                        self.Name, self.Code, self.Description, self.Status, parameter_clause))
                elif self.OnConflict == "major":
                    self.IncrementMajorVersion()
                    self.DBExists = False
                    self.ID = catocommon.new_guid()
                    self.IsDefaultVersion = False
                    # insert the new version
                    sSQL = """insert task
                        (task_id, original_task_id, version, default_version,
                        task_name, task_code, task_desc, task_status, parameter_xml, created_dt)
                        values
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s,now())"""
                    db.tran_exec(sSQL, (self.ID, self.OriginalTaskID, self.Version, ("1" if self.IsDefaultVersion else "0"),
                                        self.Name, self.Code, self.Description, self.Status, parameter_clause))
                else:
                    # there is no default action... if the on_conflict didn't match we have a problem... bail.
                    return False, "There is an ID or Name/Version conflict on [%s], and the on_conflict directive isn't a valid option. (replace/major/minor/cancel)" % (self.Name)
        else:
            # the default action is to ADD the new task row... nothing
            sSQL = """insert task
                (task_id, original_task_id, version, default_version,
                task_name, task_code, task_desc, task_status, parameter_xml, created_dt)
                values
                (%s, %s, %s, 1, %s, %s, %s, %s, %s, now())"""
            db.tran_exec(sSQL, (self.ID, self.OriginalTaskID, self.Version,
                                self.Name, self.Code, self.Description, self.Status, parameter_clause))

        # by the time we get here, there should for sure be a task row, either new or updated.                
        # now, codeblocks
        # if there's no MAIN codeblock, create it.
        if not self.Codeblocks:
            logger.warning("No Codeblocks were defined on this Task. Creating 'MAIN'...")
            self.Codeblocks["MAIN"] = Codeblock(self.ID, "MAIN")
        if "MAIN" not in self.Codeblocks.iterkeys():
            logger.warning("Required 'MAIN' Codeblock does not exist. Creating...")
            self.Codeblocks["MAIN"] = Codeblock(self.ID, "MAIN")
            
        for c in self.Codeblocks.itervalues():
            sSQL = "insert task_codeblock (task_id, codeblock_name) values (%s, %s)"
            db.tran_exec(sSQL, (self.ID, c.Name))

            # and steps
            if c.Steps:
                order = 1
                for s in c.Steps.itervalues():
                    sSQL = """insert into task_step (step_id, task_id, codeblock_name, step_order,
                        commented, locked,
                        function_name, function_xml)
                        values (%s, %s, %s, %s, %s, 0, %s, %s)"""
                    db.tran_exec(sSQL, (s.ID, self.ID, s.Codeblock, order, ("1" if s.Commented else "0"),
                                        s.FunctionName, catocommon.ET.tostring(s.FunctionXDoc)))
                    order += 1

        if bLocalTransaction:
            db.tran_commit()
            db.close()

        return True, ""

    def Copy(self, iMode, sNewTaskName, sNewTaskCode):
        # iMode 0=new task, 1=new major version, 2=new minor version
        # do it all in a transaction
        db = catocommon.new_conn()

        # NOTE: this routine is not very object-aware.  It works and was copied in here
        # so it can live with other relevant code.
        # may update it later to be more object friendly
        sSQL = ""
        sNewTaskID = catocommon.new_guid()
        iIsDefault = 0

        # figure out the new name and selected version
        sTaskName = self.Name
        sOTID = self.OriginalTaskID

        # figure out the new version
        if iMode == 0:
            # figure out the new name and selected version
            sSQL = "select count(*) from task where task_name = '" + sNewTaskName + "'"
            iExists = db.select_col_noexcep(sSQL)
            sTaskName = (sNewTaskName + " (" + str(datetime.now()) + ")" if iExists > 0 else sNewTaskName)

            iIsDefault = 1
            self.Version = "1.000"
            sOTID = sNewTaskID
        elif iMode == 1:
            self.IncrementMajorVersion()
        elif iMode == 2:
            self.IncrementMinorVersion()
        else:  # a iMode is required
            raise InfoException("A mode required for this copy operation.")

        # if we are versioning, AND there are not yet any 'Approved' versions,
        # we set this new version to be the default
        # (that way it's the one that you get taken to when you pick it from a list)
        if iMode > 0:
            sSQL = "select case when count(*) = 0 then 1 else 0 end" \
                " from task where original_task_id = '" + sOTID + "'" \
                " and task_status = 'Approved'"
            iExists = db.select_col_noexcep(sSQL)
            if db.error:
                db.tran_rollback()
                raise Exception(db.error)

        # string sTaskName = (iExists > 0 ? sNewTaskName + " (" + DateTime.Now + ")" : sNewTaskName);
        # drop the temp tables.
        sSQL = "drop temporary table if exists _copy_task"
        db.tran_exec(sSQL)
        sSQL = "drop temporary table if exists _step_ids"
        db.tran_exec(sSQL)
        sSQL = "drop temporary table if exists _copy_task_codeblock"
        db.tran_exec(sSQL)
        sSQL = "drop temporary table if exists _copy_task_step"
        db.tran_exec(sSQL)

        # start copying
        sSQL = "create temporary table _copy_task select * from task where task_id = '" + self.ID + "'"
        db.tran_exec(sSQL)

        # update the task_id
        sSQL = "update _copy_task set" \
            " task_id = '" + sNewTaskID + "'," \
            " original_task_id = '" + sOTID + "'," \
            " version = '" + str(self.Version) + "'," \
            " task_name = '" + sTaskName + "'," \
            " task_code = '" + (sNewTaskCode if sNewTaskCode else self.Code) + "'," \
            " default_version = " + str(iIsDefault) + "," \
            " task_status = 'Development'," \
            " created_dt = now()"
        db.tran_exec(sSQL)

        # codeblocks
        sSQL = "create temporary table _copy_task_codeblock" \
            " select '" + sNewTaskID + "' as task_id, codeblock_name" \
            " from task_codeblock where task_id = '" + self.ID + "'"
        db.tran_exec(sSQL)

        # USING TEMPORARY TABLES... need a place to hold step ids while we manipulate them
        sSQL = "create temporary table _step_ids" \
            " select distinct step_id, uuid() as newstep_id" \
            " from task_step where task_id = '" + self.ID + "'"
        db.tran_exec(sSQL)

        # steps temp table
        sSQL = "create temporary table _copy_task_step" \
            " select step_id, '" + sNewTaskID + "' as task_id, codeblock_name, step_order, commented," \
            " locked, function_name, function_xml, step_desc" \
            " from task_step where task_id = '" + self.ID + "'"
        db.tran_exec(sSQL)

        # update the step id
        sSQL = "update _copy_task_step a, _step_ids b" \
            " set a.step_id = b.newstep_id" \
            " where a.step_id = b.step_id"
        db.tran_exec(sSQL)

        # update steps with codeblocks that reference a step (embedded steps)
        sSQL = "update _copy_task_step a, _step_ids b" \
            " set a.codeblock_name = b.newstep_id" \
            " where b.step_id = a.codeblock_name"
        db.tran_exec(sSQL)

        # spin the steps and update any embedded step id's in the commands
        sSQL = "select step_id, newstep_id from _step_ids"
        dtStepIDs = db.select_all_dict(sSQL)

        if dtStepIDs:
            for drStepIDs in dtStepIDs:
                sSQL = "update _copy_task_step" \
                    " set function_xml = replace(function_xml," \
                    " '" + drStepIDs["step_id"] + "'," \
                    " '" + drStepIDs["newstep_id"] + "')" \
                    " where function_name in ('if','loop','exists','while')"
                db.tran_exec(sSQL)

        # finally, put the temp steps table in the real steps table
        sSQL = "insert into task select * from _copy_task"
        db.tran_exec(sSQL)
        sSQL = "insert into task_codeblock select * from _copy_task_codeblock"
        db.tran_exec(sSQL)
        sSQL = "insert into task_step" \
            " (step_id, task_id, codeblock_name, step_order, commented," \
            " locked, function_name, function_xml, step_desc)" \
            " select step_id, task_id, codeblock_name, step_order, commented," \
            " locked, function_name, function_xml, step_desc" \
            " from _copy_task_step"
        db.tran_exec(sSQL)

        # finally, if we versioned up and we set this one as the new default_version,
        # we need to unset the other row
        if iMode > 0 and iIsDefault == 1:
            sSQL = "update task set default_version = 0 where original_task_id = '" + sOTID + "' and task_id <> '" + sNewTaskID + "'"
            db.tran_exec(sSQL)

        db.tran_commit()
        db.close()

        return sNewTaskID

    def PopulateTask(self, dr, IncludeCode=True):
        db = catocommon.new_conn()

        # of course it exists...
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
        
        # parameters - always available (for other processes)
        if dr["parameter_xml"]:
            xParameters = catocommon.ET.fromstring(dr["parameter_xml"])
            if xParameters is not None:
                self.ParameterXDoc = xParameters

        # 
        # * ok, this is important.
        # * there are some rules for the process of 'Approving' a task and other things.
        # * so, we'll need to know some count information
        # 
        sSQL = """select count(*) from task
            where original_task_id = '%s'
            and task_status = 'Approved'""" % self.OriginalTaskID
        iCount = db.select_col_noexcep(sSQL)
        self.NumberOfApprovedVersions = iCount

        sSQL = "select count(*) from task where original_task_id = '%s'" % self.OriginalTaskID
        iCount = db.select_col_noexcep(sSQL)
        self.NumberOfOtherVersions = iCount

        sSQL = "select max(version) from task where original_task_id = '%s'" % self.OriginalTaskID
        sMax = db.select_col_noexcep(sSQL)
        self.MaxVersion = sMax
        self.NextMinorVersion = str(float(self.MaxVersion) + .001)
        self.NextMajorVersion = str(int(float(self.MaxVersion) + 1)) + ".000"

        if IncludeCode:
            # now, the fun stuff
            # 1 get all the codeblocks and populate that dictionary
            # 2 then get all the steps... ALL the steps in one sql
            # ..... and while spinning them put them in the appropriate codeblock
            # GET THE CODEBLOCKS
            sSQL = "select codeblock_name from task_codeblock where task_id = '%s' order by codeblock_name" % self.ID
            dtCB = db.select_all_dict(sSQL)
            if dtCB:
                for drCB in dtCB:
                    cb = Codeblock(self.ID, drCB["codeblock_name"], self.IncludeSettingsForUser)
                    self.Codeblocks[cb.Name] = cb
            else:
                # uh oh... there are no codeblocks!
                # since all tasks require a MAIN codeblock... if it's missing,
                # we can just repair it right here.
                sSQL = "insert task_codeblock (task_id, codeblock_name) values ('%s', 'MAIN')" % self.ID
                db.exec_db(sSQL)
                self.Codeblocks["MAIN"] = Codeblock(self.ID, "MAIN")
            
        db.close()


    def IncrementMajorVersion(self):
        self.Version = str(int(float(self.MaxVersion) + 1)) + ".000"
        self.NextMinorVersion = str(float(self.Version) + .001)
        self.NextMajorVersion = str(int(float(self.MaxVersion) + 2)) + ".000"

    def IncrementMinorVersion(self):
        self.Version = str(float(self.MaxVersion) + .001)
        self.NextMinorVersion = str(float(self.Version) + .001)
        self.NextMajorVersion = str(int(float(self.MaxVersion) + 1)) + ".000"

class Codeblock(object):
    def __init__(self, sTaskID, sName, IncludeSettingsForUser=None):
        self.Name = sName
        self.Steps = {}

        db = catocommon.new_conn()

        # NOTE: it may seem like STEP sorting will be an issue, but it shouldn't.
        # sorting ALL the steps by their order here will ensure they get added to their respective 
        # codeblocks in the right order.
        
        # GET THE STEPS
        # we need the userID to get the user settings in some cases
        if IncludeSettingsForUser:
            sSQL = """select s.task_id, s.step_id, s.step_order, s.step_desc, s.function_name, s.function_xml, s.commented, s.locked, codeblock_name,
                us.visible, us.breakpoint, us.skip, us.button
                from task_step s
                left outer join task_step_user_settings us on us.user_id = '%s' and s.step_id = us.step_id
                where s.task_id = '%s'
                and codeblock_name = '%s'
                order by s.step_order""" % (IncludeSettingsForUser, sTaskID, self.Name)
        else:
            sSQL = """select s.task_id, s.step_id, s.step_order, s.step_desc, s.function_name, s.function_xml, s.commented, s.locked, codeblock_name,
                0 as visible, 0 as breakpoint, 0 as skip, '' as button
                from task_step s
                where s.task_id = '%s'
                and codeblock_name = '%s'
                order by s.step_order""" % (sTaskID, self.Name)

        dtSteps = db.select_all_dict(sSQL)
        if dtSteps:
            for drSteps in dtSteps:
                oStep = Step.FromRow(drSteps)
                # the steps dictionary for each codeblock uses the ORDER, not the STEP ID, as the key
                # this way, we can order the dictionary.
                
                # maybe this should just be a list?
                if oStep:
                    # just double check that the codeblocks match
                    if self.Name == oStep.Codeblock:
                        self.Steps[oStep.Order] = oStep
                    else:
                        raise Exception("WARNING: Step thinks it belongs in codeblock [%s] but this task doesn't have that codeblock." % (oStep.Codeblock if oStep.Codeblock else "NONE"))
        
    # a codeblock contains a dictionary collection of steps
    def FromXML(self, sCBXML=""):
        if sCBXML == "": return None
        xCB = catocommon.ET.fromstring(sCBXML)
        
        self.Name = xCB.attrib["name"]
        
        # STEPS
        xSteps = xCB.findall("steps/step")
        logger.debug("Number of Steps in [" + self.Name + "]: " + str(len(xSteps)))
        order = 1
        for xStep in xSteps:
            newstep = Step()
            newstep.FromXML(catocommon.ET.tostring(xStep), self.Name)
            self.Steps[order] = newstep
            order += 1

    # a codeblock contains a dictionary collection of steps
    def FromDict(self, cb):
        self.Name = cb.get("Name")
        
        steps = cb.get("Steps", [])
        logger.debug("Number of Steps in [%s]: %s" % (self.Name, len(steps)))
        order = 1
        for step in steps:
            newstep = Step()
            newstep.FromDict(step, self.Name)
            self.Steps[order] = newstep
            order += 1

class Step(object):
    def __init__(self):
        self.ID = ""
        self.TaskID = None
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
        self.ValueSnip = None
        self.UserSettings = StepUserSettings()
        # this property isn't added by the "Populate" methods - but can be added manually.
        # this is because of xml import/export - where the function details aren't required.
        # but they are in the UI when drawing steps.
        self.Function = None 
        # most steps won't even have this - only manually created ones for "embedded" steps
        self.XPathPrefix = ""
        
        # if an error occured parsing, this step will be invalid
        # this property notes that
        self.IsValid = True
        
    def AsJSON(self):
        del self.TaskID
        del self.Function
        del self.UserSettings
        self.FunctionXML = catocommon.ET.tostring(self.FunctionXDoc)
        del self.FunctionXDoc
        return catocommon.ObjectOutput.AsJSON(self.__dict__)        

    def FromXML(self, sStepXML="", sCodeblockName=""):
        if sStepXML == "": return None
        if sCodeblockName == "": return None
        
        xStep = catocommon.ET.fromstring(sStepXML)
        
        # attributes of the <step> node
        self.ID = catocommon.new_guid()
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
    
    def FromDict(self, step="", sCodeblockName=""):
        if sCodeblockName == "": return None
        
        # when created from a dict, steps always get a new id
        self.ID = catocommon.new_guid()
        self.Order = step.get("Order", 0)
        self.Codeblock = sCodeblockName
        self.Commented = catocommon.is_true(step.get("Commented", ""))
        self.OutputParseType = int(step.get("OutputParseType", 0))
        self.OutputRowDelimiter = int(step.get("OutputRowDelimiter", 0))
        self.OutputColumnDelimiter = int(step.get("OutputColumnDelimiter", 0))

        self.Description = step.get("Description", "")

        # FUNCTION
        func = step.get("FunctionXML")
        if not func:
            raise Exception("ERROR: Step [%s] - function xml is empty or cannot be parsed.")
        
        self.FunctionXDoc = catocommon.ET.fromstring(func)
        # command_type is for backwards compatilibity in importing tasks from 1.0.8
        self.FunctionName = step.get("FunctionName", "")
    
    @staticmethod
    def FromRow(dr):
        s = Step()
        s.PopulateStep(dr)
        return s
        
    @staticmethod
    def FromID(sStepID):
        """
        Gets a single step object, *without* user settings.  Does NOT have an associated parent Task object.
        This is called by functions *on* the task page where we don't need
        the associated task object.
        """
        db = catocommon.new_conn()
        sSQL = """select s.task_id, s.step_id, s.step_order, s.step_desc, s.function_name, s.function_xml, s.commented, s.locked, s.codeblock_name
            from task_step s
            where s.step_id = '%s' limit 1""" % sStepID
        row = db.select_row_dict(sSQL)
        db.close()
        if row:
            oStep = Step.FromRow(row)
            return oStep

        return None
        
    @staticmethod
    def FromIDWithSettings(sStepID, sUserID):
        """
        Gets a single step object, including user settings.  Does NOT have an associated parent Task object.
        This is called by the AddStep methods, and other functions *on* the task page where we don't need
        the associated task object
        """
        db = catocommon.new_conn()
        sSQL = """select s.task_id, s.step_id, s.step_order, s.step_desc, s.function_name, s.function_xml, s.commented, s.locked, s.codeblock_name,
            us.visible, us.breakpoint, us.skip, us.button
            from task_step s
            left outer join task_step_user_settings us on us.user_id = '%s' and s.step_id = us.step_id
            where s.step_id = '%s' limit 1""" % (sUserID, sStepID)
        row = db.select_row_dict(sSQL)
        db.close()
        if row:
            oStep = Step.FromRow(row)
            return oStep

        return None
        
    def PopulateStep(self, dr):
        self.ID = dr["step_id"]
        self.TaskID = dr["task_id"]
        self.Codeblock = ("" if not dr["codeblock_name"] else dr["codeblock_name"])
        self.Order = dr["step_order"]
        self.Description = ("" if not dr["step_desc"] else dr["step_desc"])
        self.Commented = (True if dr["commented"] == 1 else False)
        self.Locked = (True if dr["locked"] == 1 else False)
        func_xml = ("" if not dr["function_xml"] else dr["function_xml"])
        # once parsed, it's cleaner.  update the object with the cleaner xml
        if func_xml:
            try:
                self.FunctionXDoc = catocommon.ET.fromstring(func_xml)
                
                # what's the output parse type?
                try:
                    opt = int(self.FunctionXDoc.get("parse_method", 0))
                except:
                    logger.error("parse_method on step xml isn't a valid integer.")
                    opt = 0
                self.OutputParseType = opt
                
                # if the output parse type is "2", we need row and column delimiters too!
                # if self.OutputParseType == 2:
                # but hey! why bother checking, just read 'em anyway.  Won't hurt anything.
                try:
                    rd = int(self.FunctionXDoc.get("row_delimiter", 0))
                except:
                    logger.error("row_delimiter on step xml isn't a valid integer.")
                    rd = 0
                self.OutputRowDelimiter = rd
                
                try:
                    cd = int(self.FunctionXDoc.get("col_delimiter", 0))
                except:
                    logger.error("row_delimiter on step xml isn't a valid integer.")
                    cd = 0
                self.OutputColumnDelimiter = cd
            except catocommon.ET.ParseError:
                self.IsValid = False
                logger.error(traceback.format_exc())    
                raise Exception("CRITICAL: Unable to parse function xml in step [%s]." % self.ID)
            except Exception:
                self.IsValid = False
                logger.error(traceback.format_exc())  
                raise Exception("CRITICAL: Exception in processing step [%s]." % self.ID)
                
            # if there's no description, and the function_xml says so, we can snip
            # a bit of a value as the description
            if self.FunctionXDoc.get("snip"):
                xpath = self.FunctionXDoc.get("snip")
                val = self.FunctionXDoc.findtext(xpath)
                if val:
                    if len(val) > 75:
                        self.ValueSnip = val[:75]
                    else:
                        self.ValueSnip = val

        # this.Function = Function.GetFunctionByName(dr["function_name"]);
        self.FunctionName = dr["function_name"]

        # user settings, if available
        if dr.has_key("button"):
            self.UserSettings.Button = json.loads(dr["button"]) if dr["button"] else {}
        if dr.has_key("skip"):
            self.UserSettings.Skip = (True if dr["skip"] == 1 else False)
        if dr.has_key("visible"):
            self.UserSettings.Visible = (False if dr["visible"] == 0 else True)

#        # NOTE!! :oTask can possibly be null, in lots of cases where we are just getting a step and don't know the task.
#        # if it's null, it will not populate the parent object.
#        # this happens all over the place in the HTMLTemplates stuff, and we don't need the extra overhead of the same task
#        # object being created hundreds of times.
#        if oTask:
#            self.Task = oTask
#        else:
#            # NOTE HACK TODO - this is bad and wrong
#            # we shouldn't assume the datarow was a join to the task table... but in a few places it was.
#            # so we're populating some stuff here.
#            # the right approach is to create a full Task object from the ID, but we need to analyze
#            # how it's working, so we don't create a bunch more database hits.
#            # I THINK THIS is only happening on GetSingleStep and taskStepVarsEdit, but double check.
#            self.Task = Task()
#            if dr.has_key("task_id"):
#                self.Task.ID = dr["task_id"]
#            if dr.has_key("task_name"):
#                self.Task.Name = dr["task_name"]
#            if dr.has_key("version"):
#                self.Task.Version = dr["version"]
        return self
        
class StepUserSettings(object):
    def __init__(self):
        self.Visible = True
        self.Breakpoint = False
        self.Skip = False
        self.Button = {}


class TaskRunLog(object):
    log_rows = {}
    summary_rows = {}
    numrows = 0
    def __init__(self, sTaskInstance, sRows=""):
        db = catocommon.new_conn()
        sLimitClause = " limit 200"

        if sRows:
            if sRows == "all":
                sLimitClause = ""
            else:
                try:
                    sRows = int(sRows)
                except:
                    sRows = 200
                    
                sLimitClause = " limit " + str(sRows)
                
        # how many log rows are there?
        sSQL = "select count(*) from task_instance_log where task_instance = %s"
        self.numrows = db.select_col_noexcep(sSQL, (sTaskInstance))
        
        # result summary rows
        sSQL = """select log from task_instance_log 
            where task_instance = %s 
            and command_text = 'result_summary'
            order by id"""

        self.summary_rows = db.select_all_dict(sSQL, (sTaskInstance))

        # NOW carry on with the regular rows
        sSQL = """select til.task_instance, til.entered_dt, til.connection_name, til.log,
            til.step_id, s.task_id, s.step_order, s.function_name, s.function_name as function_label, s.codeblock_name,
            til.command_text,
            '' as variable_name,  '' as variable_value,
            case when length(til.log) > 256 then 1 else 0 end as large_text
            from task_instance_log til
            left outer join task_step s on til.step_id = s.step_id
            where til.task_instance = %s
            order by til.id %s""" % (str(sTaskInstance), sLimitClause)
            
        self.log_rows = db.select_all_dict(sSQL)
        db.close()

    def AsJSON(self):
        return catocommon.ObjectOutput.AsJSON(self.__dict__)

    def AsXML(self):
        return catocommon.ObjectOutput.IterableAsXML(self.log_rows, "log_rows", "row")

    def AsText(self, delimiter=None, headers=None):
        # NOTE: the AsText method ONLY RETURNS THE LOG ROWS, not the result summary or row count.
        return catocommon.ObjectOutput.IterableAsText(self.log_rows, ['codeblock_name', 'step_order', 'function_name', 'log'], delimiter, headers)

class TaskInstance(object):
    """
    """
    Error = None
    def __init__(self, sTaskInstance, sTaskID="", sAssetID=""):
        self.Instance = sTaskInstance
        self.summary = None
        db = catocommon.new_conn()
        # we could define a whole model here, but it's not necessary... all we want is the data
        # since this won't be acted on as an object.
        
        # different things happen depending on the page args

        # if an instance was provided... it overrides all other args 
        # otherwise we need to figure out which instance we want
        if not sTaskInstance:
            sSQL = "select max(task_instance) from task_instance where task_id = '%s'" % sTaskID

            if catocommon.is_guid(sAssetID):
                sSQL += " and asset_id = '%s'" % sAssetID

            sTaskInstance = str(db.select_col_noexcep(sSQL))
            
        # still no task instance???
        # the task has never been run... just return
        if not sTaskInstance:
            return
            # raise Exception("No Instance found.  Most likely this Task has never been run.") 
        
        # the task instance must be a number, die if it isn't
        try:
            int(sTaskInstance)
        except:
            raise InfoException("Task Instance must be an integer. [%s]." % (sTaskInstance))
        
        # all good... continue...
        self.task_instance = sTaskInstance

        sSQL = """select ti.task_instance, ti.task_id, '' as asset_id, ti.task_status, ti.submitted_by_instance,
            ti.submitted_dt, ti.started_dt, ti.completed_dt, ti.ce_node, ti.pid, ti.debug_level,
            t.task_name, t.version, '' as asset_name, u.full_name,
            ar.app_instance, ar.platform, ar.hostname,
            t.concurrent_instances, t.queue_depth,
            d.instance_id, d.instance_label, ti.account_id, ca.account_name
            from task_instance ti
            join task t on ti.task_id = t.task_id
            left outer join users u on ti.submitted_by = u.user_id
            left outer join application_registry ar on ti.ce_node = ar.id
            left outer join cloud_account ca on ti.account_id = ca.account_id
            left outer join deployment_service_inst d on ti.ecosystem_id = d.instance_id
            where ti.task_instance = %s""" % sTaskInstance

        dr = db.select_row_dict(sSQL)
        if dr is not None:
            self.task_id = dr["task_id"]
            self.asset_id = (dr["asset_id"] if dr["asset_id"] else "")
            self.debug_level = (dr["debug_level"] if dr["debug_level"] else "")

            self.task_name = dr["task_name"]
            self.task_name_label = "%s - Version %s" % (dr["task_name"], str(dr["version"]))
            self.task_status = dr["task_status"]
            self.asset_name = ("N/A" if not dr["asset_name"] else dr["asset_name"])
            self.submitted_dt = ("" if not dr["submitted_dt"] else str(dr["submitted_dt"]))
            self.started_dt = ("" if not dr["started_dt"] else str(dr["started_dt"]))
            self.completed_dt = ("" if not dr["completed_dt"] else str(dr["completed_dt"]))
            self.ce_node = ("" if not dr["ce_node"] else "%s - (%s)" % (str(dr["app_instance"]), dr["platform"]))
            self.pid = ("" if not dr["pid"] else str(dr["pid"]))

            self.submitted_by_instance = ("" if not dr["submitted_by_instance"] else dr["submitted_by_instance"])

            self.instance_id = (dr["instance_id"] if dr["instance_id"] else "")
            self.instance_label = (dr["instance_label"] if dr["instance_label"] else "")
            self.account_id = (dr["account_id"] if dr["account_id"] else "")
            self.account_name = (dr["account_name"] if dr["account_name"] else "")

            self.submitted_by = (dr["full_name"] if dr["full_name"] else "Scheduler")


            # get the result summary
            sSQL = """select log from task_instance_log
                where task_instance = %s
                and command_text = 'result_summary'""" % (sTaskInstance)
            summary = db.select_col_noexcep(sSQL)
            self.summary = summary if summary else ""

            # if THIS instance is 'active', show additional warning info on the resubmit confirmation.
            # and if it's not, don't show the "cancel" button
            if dr["task_status"].lower() in ["processing", "queued", "submitted", "pending", "aborting", "queued", "staged"]:
                self.resubmit_message = "This Task is currently active."
            else:
                self.allow_cancel = "false"


            # check for OTHER active instances
            sSQL = """select count(*) from task_instance where task_id = '%s'
                and task_instance <> '%s'
                and task_status in ('processing','submitted','pending','aborting','queued','staged')""" % (dr["task_id"], sTaskInstance)
            iActiveCount = db.select_col_noexcep(sSQL)

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
                        self.resubmit_message = "The maximum concurrent instances for this Task are running.  This request will be queued."
                    else:
                        self.allow_resubmit = "false"

                # neato... show the user a list of all the other instances!
                sSQL = """select task_instance, task_status from task_instance
                    where task_id = '%s'
                    and task_instance <> '%s'
                    and task_status in ('processing','submitted','pending','aborting','queued','staged')
                    order by task_status""" % (dr["task_id"], sTaskInstance)

                dt = db.select_all_dict(sSQL)

                # build a list of the other instances
                for dr in dt:
                    d = {}
                    d["task_instance"] = str(dr["task_instance"])
                    d["task_status"] = dr["task_status"]
                    aOtherInstances.append(d)

                self.other_instances = aOtherInstances

        else:
            raise InfoException("Did not find any data for Instance [%s]." % sTaskInstance)
        
    def LoadResultSummary(self):
        # at the moment the result_summary is xml
        # and the schema is known
        # DO NOT break the response if the summary can't be loaded
        # also, both set a property and return the object
        out = []
        if self.summary:
            try:
                xroot = catocommon.ET.fromstring(self.summary)
                if xroot is not None:
                    for xparam in xroot.findall(".//items/item"):
                        tmp = {}
                        tmp["name"] = xparam.findtext("name", "")
                        tmp["detail"] = xparam.findtext("detail", "")
                        out.append(tmp)
            except Exception as ex:
                logger.error("Unable to read result summary xml. %s" % (ex.__str__()))
        self.summary = out
        return out

    def AsJSON(self):
        self.LoadResultSummary()
        return catocommon.ObjectOutput.AsJSON(self.__dict__)

    def AsXML(self):
        self.LoadResultSummary()
        return catocommon.ObjectOutput.AsXML(self.__dict__, "TaskInstance")

    def AsText(self, delimiter=None, headers=None):
        return catocommon.ObjectOutput.AsText(self, ["task_instance", "task_status", "task_name_label", "submitted_dt", "completed_dt"], delimiter, headers)

    def Stop(self):
        db = catocommon.new_conn()
        if self.Instance:
            sSQL = """update task_instance set task_status = 'Aborting'
                where task_instance = '%s'
                and task_status in ('Processing')""" % self.Instance
            db.exec_db(sSQL)

            sSQL = """update task_instance set task_status = 'Cancelled'
                where task_instance = '%s'
                and task_status in ('Submitted','Queued','Staged')""" % self.Instance
            db.exec_db(sSQL)
            
            return ""
        else:
            raise InfoException("Unable to stop task. Missing or invalid task_instance.")

    def Resubmit(self, user_id):
        """
        This simply changes a completed task into the Submitted status.
        
        It *might* need to reset the log?
        """
        db = catocommon.new_conn()
        if self.Instance:
            if self.task_status in ('Completed'):
                return False, "Not allowed to resubmit a Task that Completed successfully."
            
            if self.task_status in ('Processing', 'Submitted', 'Queued', 'Staged'):
                return False, "Not allowed to resubmit a Task that is currently processing."
            
            sSQL = """update task_instance set 
                task_status = 'Submitted',
                submitted_by = %s
                where task_instance = %s"""
            db.exec_db(sSQL, (user_id, self.Instance))

            return True, ""
        else:
            return False, "Unable to restart task. Missing or invalid task_instance."

        db.close()

class TaskInstances(object):
    rows = {}
    def __init__(self, sTaskID=None, sTaskInstance=None, sFilter="", sStatus="", sFrom="", sTo="", sRecords=""):
        db = catocommon.new_conn()
        
        # # of records must be numeric
        if sRecords:
            try:
                sRecords = str(int(sRecords))
            except TypeError:
                sRecords = "200"
        else:
            sRecords = "200"
            
        sWhereString = " where (1=1) "
        
        # if sTaskID or sTaskInstance are defined, they are hard filters, not like clauses.
        if sTaskInstance:
            sWhereString += " and ti.task_instance = '%s'" % sTaskInstance
        if sTaskID:
            sWhereString += " and ti.task_id = '%s'" % sTaskID

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
                        "or t.task_code like '%%" + term + "%%' " \
                        "or t.task_name like '%%" + term + "%%' " \
                        "or t.version like '%%" + term + "%%' " \
                        "or u.username like '%%" + term + "%%' " \
                        "or u.full_name like '%%" + term + "%%') "

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
        if sStatus and sStatus != "all":
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
        
        sSQL = """select 
            ti.task_instance as Instance, 
            t.task_id as TaskID, 
            t.task_code as TaskCode, 
            a.asset_name as AssetName,
            ti.pid as ProcessID, 
            ti.task_status as Status, 
            t.task_name as TaskName,
            ifnull(u.full_name, '') as StartedBy,
            t.version as Version, 
            ar.hostname as CEName, 
            ar.platform as CEType,
            d.instance_label as ServiceInstanceLabel, 
            d.instance_id as ServiceInstanceID,
            convert(ti.submitted_dt, CHAR(20)) as SubmittedDate,
            convert(ti.started_dt, CHAR(20)) as StartedDate,
            convert(ti.completed_dt, CHAR(20)) as CompletedDate
            from task_instance ti
            left join task t on t.task_id = ti.task_id
            %s
            left outer join application_registry ar on ti.ce_node = ar.id
            left outer join deployment_service_inst d on ti.ecosystem_id = d.instance_id
            left join users u on u.user_id = ti.submitted_by
            left join asset a on a.asset_id = ti.asset_id
            %s %s
            order by ti.task_instance desc
            limit %s""" % (sTagString, sWhereString, sDateSearchString, sRecords)
        
        self.rows = db.select_all_dict(sSQL)
        db.close()

    def AsJSON(self):
        return catocommon.ObjectOutput.IterableAsJSON(self.rows)

    def AsXML(self):
        return catocommon.ObjectOutput.IterableAsXML(self.rows, "TaskInstances", "Instance")

    def AsText(self, delimiter=None, headers=None):
        return catocommon.ObjectOutput.IterableAsText(self.rows, ['Instance', 'TaskName', 'Version', 'Status', 'StartedBy', 'SubmittedDate', 'CompletedDate'], delimiter, headers)

