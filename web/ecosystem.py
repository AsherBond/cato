
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
import json
import uiCommon
from catocommon import catocommon

# Note: this is not a container for Ecotemplate objects - it's just a rowset from the database
# with an AsJSON method.
# why? Because we don't need a full object for list pages and dropdowns.
class Ecotemplates(object):
    rows = {}
    def __init__(self, sFilter=""):
        try:
            sWhereString = ""
            if sFilter:
                aSearchTerms = sFilter.split()
                for term in aSearchTerms:
                    if term:
                        sWhereString += " and (et.ecotemplate_name like '%%" + term + "%%' " \
                            "or et.ecotemplate_desc like '%%" + term + "%%') "
    
            sSQL = """select et.ecotemplate_id, et.ecotemplate_name, et.ecotemplate_desc,
                (select count(*) from ecosystem where ecotemplate_id = et.ecotemplate_id) as in_use,
                group_concat(ot.tag_name order by ot.tag_name separator ',') as tags
                from ecotemplate et
                left outer join object_tags ot on et.ecotemplate_id = ot.object_id
                where 1=1 %s group by et.ecotemplate_id order by et.ecotemplate_name""" % sWhereString
            
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
        
class Ecotemplate(object):
    ID = None
    Name = None
    Description = None
    StormFileType = None
    StormFile = None
    IncludeTasks = False #used for export to xml
    DBExists = None
    OnConflict = "cancel" #the default behavior for all conflicts is to cancel the operation
    Actions = {}

    def __init__(self):
        self.ID = catocommon.new_guid()
        self.Name = None
        self.Description = None
        self.StormFileType = None
        self.StormFile = None
        self.IncludeTasks = False #used for export to xml
        self.DBExists = None
        self.OnConflict = "cancel" #the default behavior for all conflicts is to cancel the operation
        self.Actions = {}
        
    #the default constructor (manual creation)
    def FromArgs(self, sName, sDescription):
        if not sName:
            raise Exception("Error building Ecotemplate: Name is required.")

        self.Name = sName
        self.Description = sDescription
        self.DBExists = self.dbExists()

    def FromID(self, sEcotemplateID, bIncludeActions = True):
        try:
            sSQL = "select ecotemplate_id, ecotemplate_name, ecotemplate_desc, storm_file_type, storm_file" \
                " from ecotemplate" \
                " where ecotemplate_id = '" + sEcotemplateID + "'"

            db = catocommon.new_conn()
            dr = db.select_row_dict(sSQL)
            if db.error:
                raise Exception("Ecotemplate Object: Unable to get Ecotemplate from database. " + db.error)

            if dr is not None:
                self.DBExists = True
                self.ID = dr["ecotemplate_id"]
                self.Name = dr["ecotemplate_name"]
                self.Description = ("" if not dr["ecotemplate_desc"] else dr["ecotemplate_desc"])
                self.StormFileType = ("" if not dr["storm_file_type"] else dr["storm_file_type"])
                self.StormFile = ("" if not dr["storm_file"] else dr["storm_file"])
                
                if bIncludeActions:
                    # get a table of actions and loop the rows
                    sSQL = "select action_id, ecotemplate_id, action_name, action_desc, category, original_task_id, task_version, parameter_defaults, action_icon" \
                        " from ecotemplate_action" \
                        " where ecotemplate_id = '" + sEcotemplateID + "'"
    
                    dtActions = db.select_all_dict(sSQL)
                    if dtActions:
                        for drAction in dtActions:
                            ea = EcotemplateAction()
                            ea.FromRow(drAction, self)
                            if ea is not None:
                                self.Actions[ea.ID] = ea
            else: 
                raise Exception("Error building Ecotemplate object: " + db.error)
        except Exception as ex:
            raise ex
        finally:
            db.close()

    def AsJSON(self):
        try:
            sb = []
            sb.append("{")
            sb.append("\"%s\" : \"%s\"," % ("ID", self.ID))
            sb.append("\"%s\" : \"%s\"," % ("Name", self.Name))
            sb.append("\"%s\" : \"%s\"" % ("Description", uiCommon.packJSON(self.Description)))
            sb.append("}")
            return "".join(sb)
        except Exception as ex:
            raise ex


    def dbExists(self):
        try:
            # task_id is the PK, and task_name+version is a unique index.
            # so, we check the conflict property, and act accordingly
            sSQL = "select ecotemplate_id from ecotemplate" \
                " where ecotemplate_name = '" + self.Name + "'" \
                " or ecotemplate_id = '" + self.ID + "'"
            db = catocommon.new_conn()
            dr = db.select_row_dict(sSQL)
            if db.error:
                print(db.error)
                raise Exception("Ecotemplate Object: Unable to check for existing Name or ID. " + db.error)
            
            if dr is not None:
                if dr["ecotemplate_id"]:
                    # PAY ATTENTION! 
                    # if the template exists... it might have been by name, so...
                    # we're setting the ids to the same as the database so it's more accurate.
                    
                    self.ID = dr["ecotemplate_id"]
                    return True
                
            return False
        except Exception as ex:
            raise ex
        finally:
            db.close()

    def DBSave(self):
        try:
            if not self.Name or not self.ID:
                return False, "ID and Name are required Ecotemplate properties."

            db = catocommon.new_conn()

            if self.DBExists:
                # uh oh... this ecotemplate exists.  unless told to do so, we stop here.
                if self.OnConflict == "cancel":
                    return False, "Another Ecotemplate with that ID or Name exists.  [" + self.ID + "/" + self.Name + "]  Conflict directive set to 'cancel'. (Default is 'cancel' if omitted.)"
                else:
                    # ok, what are we supposed to do then?
                    if self.OnConflict == "replace":
                        # whack it all so we can re-insert
                        # but by name or ID?  which was the conflict?
                        
                        # no worries! the _DBExists function called when we created the object
                        # will have resolved any name/id issues.
                        
                        # if the ID existed it doesn't matter, we'll be plowing it anyway.
                        # by "plow" I mean drop and recreate the actions... the ecotemplate row will be UPDATED
                        sSQL = "update ecotemplate" \
                            " set ecotemplate_name = '" + self.Name + "'," \
                            " ecotemplate_desc = " + (" null" if not self.Description else " '" + catocommon.tick_slash(self.Description + "'")) + "," \
                            " storm_file_type = " + (" null" if not self.StormFileType else " '" + self.StormFileType + "'") + "," \
                            " storm_file = " + (" null" if not self.StormFile else " '" + catocommon.tick_slash(self.StormFile + "'")) + \
                            " where ecotemplate_id = '" + self.ID + "'"
                        if not db.tran_exec_noexcep(sSQL):
                            return False, db.error

                        sSQL = "delete from ecotemplate_action" \
                            " where ecotemplate_id = '" + self.ID + "'"
                        if not db.tran_exec_noexcep(sSQL):
                            return False, db.error
                    else:
                        # there is no default action... if the on_conflict didn't match we have a problem... bail.
                        return False, "There is an ID or Name conflict, and the on_conflict directive isn't a valid option. (replace/cancel)"
            else:
                # doesn't exist, we'll add it                
                sSQL = "insert into ecotemplate (ecotemplate_id, ecotemplate_name, ecotemplate_desc, storm_file_type, storm_file)" \
                    " values ('" + self.ID + "'," \
                        " '" + self.Name + "',"  + \
                        (" null" if not self.Description else " '" + catocommon.tick_slash(self.Description) + "'") + "," + \
                        (" null" if not self.StormFileType else " '" + self.StormFileType + "'") + "," + \
                        (" null" if not self.StormFile else " '" + catocommon.tick_slash(self.StormFile) + "'") + \
                        ")"
                if not db.tran_exec_noexcep(sSQL):
                    return False, db.error
                
            
            # create the actions
            # actions aren't referenced by id anywhere, so we'll just give them a new guid
            # to prevent any risk of PK issues.
            for ea in self.Actions.itervalues():
                sSQL = "insert into ecotemplate_action" \
                    " (action_id, ecotemplate_id, action_name, action_desc, category, action_icon, original_task_id, task_version, parameter_defaults)" \
                    " values (" \
                    " uuid()," \
                    " '" + self.ID + "'," \
                    " '" + catocommon.tick_slash(ea.Name) + "'," + \
                    ("null" if not ea.Description else " '" + catocommon.tick_slash(ea.Description) + "'") + "," + \
                    ("null" if not ea.Category else " '" + catocommon.tick_slash(ea.Category) + "'") + "," + \
                    ("null" if not ea.Icon else " '" + ea.Icon + "'") + "," + \
                    ("null" if not ea.OriginalTaskID else " '" + ea.OriginalTaskID + "'") + "," + \
                    ("null" if not ea.TaskVersion else " '" + ea.TaskVersion + "'") + "," + \
                    ("null" if not ea.ParameterDefaultsXML else " '" + catocommon.tick_slash(ea.ParameterDefaultsXML) + "'") + \
                    ")"
                
                if not db.tran_exec_noexcep(sSQL):
                    return False, db.error
                
                # now, does this action contain a <task> section?  If so, we'll branch off and do 
                # the create task logic.
                if ea.Task is not None:
                    result, msg = ea.Task.DBSave()
                    if not result:
                        # the task 'should' have rolled back on any errors, but in case it didn't.
                        db.tran_rollback()
                        return False, msg

                    # finally, don't forget to update the action with the new values if any
                    ea.OriginalTaskID = ea.Task.OriginalTaskID
                        
                    # we don't update the version if the action referenced the default (it was empty)
                    if ea.TaskVersion:
                        ea.TaskVersion = ea.Task.Version
            
            # yay!
            db.tran_commit()
            return True, None

        except Exception as ex:
            raise ex
        finally:
            db.close()

    def DBCopy(self, sNewName):
        try:
            #creating a new objects gets a new id.
            et = Ecotemplate()
            if et is not None:
                # populate it from self
                et.Name = sNewName
                et.Description = self.Description
                et.StormFileType = self.StormFileType
                et.StormFile = self.StormFile
                et.Actions = self.Actions
                
                # we gave it a new name and id, recheck if it exists
                et.DBExists = et.dbExists()
                result, msg = et.DBSave()
                if not result:
                    return False, msg
            
                return True, ""
            
            return False, "Unable to create a new Ecotemplate."
        except Exception as ex:
            raise ex

    def DBUpdate(self):
        try:
            if not self.Name:
                return False, "Name is required."

            sSQL = "update ecotemplate set" \
                " ecotemplate_name = '" + self.Name + "'," \
                " ecotemplate_desc = " + (" null" if not self.Description else " '" + catocommon.tick_slash(self.Description) + "'") + "," \
                " storm_file_type = " + (" null" if not self.StormFileType else " '" + catocommon.tick_slash(self.StormFileType) + "'") + "," \
                " storm_file = " + (" null" if not self.StormFile else " '" + catocommon.tick_slash(self.StormFile) + "'") + \
                " where ecotemplate_id = '" + self.ID + "'"

            db = catocommon.new_conn()
            if not db.exec_db_noexcep(sSQL):
                print(db.error)
                if db.error == "key_violation":
                    return None, "An Ecotemplate with that name already exists.  Please select another name."
                else:
                    return False, db.error
            
            return True, ""
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()


class EcotemplateAction(object):
    ID = None
    Name = None
    Description = None
    Category = None
    OriginalTaskID = None
    TaskVersion = None
    Icon = None
    ParameterDefaultsXML = None
    Ecotemplate = None #pointer to our parent Template.

    # for export, we might want to tell the action to include the whole referenced task object
    # pretty rare, since for general use we don't wanna be lugging around a whole task.
    IncludeTask = False
    Task = None

    def FromRow(self, dr, et):
        try:
            self.Ecotemplate = et
            self.ID = dr["action_id"]
            self.Name = dr["action_name"]
            self.Description = dr["action_desc"]
            self.Category = dr["category"]
            self.OriginalTaskID = dr["original_task_id"]
            self.TaskVersion = (str(dr["task_version"]) if dr["task_version"] else "")
            self.Icon = dr["action_icon"]
            self.ParameterDefaultsXML = dr["parameter_defaults"]
        except Exception as ex:
            raise ex
        
# Note: this is not a container for Ecotemplate objects - it's just a rowset from the database
# with an AsJSON method.
# why? Because we don't need a full object for list pages and dropdowns.
class Ecosystems(object):
    rows = {}
    def __init__(self, sAccountID, sFilter=""):
        try:
            sWhereString = ""
            if sFilter:
                aSearchTerms = sFilter.split()
                for term in aSearchTerms:
                    if term:
                        sWhereString += " and (e.ecosystem_name like '%%" + term + "%%' " \
                            "or e.ecosystem_desc like '%%" + term + "%%' " \
                            "or et.ecotemplate_name like '%%" + term + "%%') "
    
            sSQL = """select e.ecosystem_id, e.ecosystem_name, e.ecosystem_desc, e.account_id, et.ecotemplate_name,
                e.storm_status, e.created_dt, e.last_update_dt,
                (select count(*) from ecosystem_object where ecosystem_id = e.ecosystem_id) as num_objects,
                group_concat(ot.tag_name order by ot.tag_name separator ',') as tags
                from ecosystem e
                join ecotemplate et on e.ecotemplate_id = et.ecotemplate_id
                left outer join object_tags ot on e.ecosystem_id = ot.object_id
                where e.account_id = '%s' %s group by e.ecosystem_id order by e.ecosystem_name""" % (sAccountID, sWhereString)
            
            db = catocommon.new_conn()
            self.rows = db.select_all_dict(sSQL)
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.rows, default=uiCommon.jsonSerializeHandler)
        except Exception as ex:
            raise ex
        
class Ecosystem(object):
    ID = catocommon.new_guid()
    Name = None
    Description = None
    StormFile = None
    AccountID = None
    EcotemplateID = None
    EcotemplateName = None #no referenced objects just yet, just the name and ID until we need more.
    ParameterXML = None
    CloudID = None
    StormStatus = None
    CreatedDate = None
    LastUpdate = None
    NumObjects = 0

    def FromArgs(self, sName, sDescription, sEcotemplateID, sAccountID):
        if not sName or not sEcotemplateID or not sAccountID:
            raise Exception("Error building Ecosystem: Name, Ecotemplate and Cloud Account are required.")

        self.Name = sName
        self.Description = sDescription
        self.EcotemplateID = sEcotemplateID
        self.AccountID = sAccountID

    @staticmethod
    def DBCreateNew(sName, sEcotemplateID, sAccountID, sDescription="", sStormStatus="", sParameterXML="", sCloudID=""):
        try:
            if not sName or not sEcotemplateID or not sAccountID:
                return None, "Name, Ecotemplate and Cloud Account are required Ecosystem properties."
              
            db = catocommon.new_conn()
            
            sID = catocommon.new_guid()

            sSQL = "insert into ecosystem (ecosystem_id, ecosystem_name, ecosystem_desc, account_id, ecotemplate_id," \
                " storm_file, storm_status, storm_parameter_xml, storm_cloud_id, created_dt, last_update_dt)" \
                " select '" + sID + "'," \
                " '" + sName + "'," \
                + (" null" if not sDescription else " '" + catocommon.tick_slash(sDescription) + "'") + "," \
                " '" + sAccountID + "'," \
                " ecotemplate_id," \
                " storm_file," \
                + (" null" if not sStormStatus else " '" + catocommon.tick_slash(sStormStatus) + "'") + "," \
                + (" null" if not sParameterXML else " '" + catocommon.tick_slash(sParameterXML) + "'") + "," \
                + (" null" if not sCloudID else " '" + sCloudID + "'") + "," \
                " now(), now()" \
                " from ecotemplate where ecotemplate_id = '" + sEcotemplateID + "'"
            
            if not db.exec_db_noexcep(sSQL):
                if db.error == "key_violation":
                    return None, "An Ecosystem with that name already exists.  Please select another name."
                else:
                    return None, db.error

            #now it's inserted and in the session... lets get it back from the db as a complete object for confirmation.
            e = Ecosystem()
            e.FromID(sID)
            #yay!
            return e, None
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def DBUpdate(self):
        try:
            if not self.Name or not self.EcotemplateID or not self.AccountID:
                return False, "Name, EcotemplateID and Account ID are required Ecosystem properties."

            sSQL = "update ecosystem set" \
                " ecosystem_name = '" + self.Name + "'," \
                " ecotemplate_id = '" + self.EcotemplateID + "'," \
                " account_id = '" + self.AccountID + "'," \
                " ecosystem_desc = " + (" null" if not self.Description else " '" + catocommon.tick_slash(self.Description) + "'") + "," \
                " last_update_dt = now()," \
                " storm_file = " + (" null" if not self.StormFile else " '" + catocommon.tick_slash(self.StormFile) + "'") + \
                " where ecosystem_id = '" + self.ID + "'"
            
            db = catocommon.new_conn()
            if not db.exec_db_noexcep(sSQL):
                return False, db.error
            
            return True, ""
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def FromID(self, sEcosystemID):
        try:
            sSQL = "select e.ecosystem_id, e.ecosystem_name, e.ecosystem_desc, e.storm_file, e.storm_status," \
                " e.account_id, e.ecotemplate_id, et.ecotemplate_name, e.created_dt, e.last_update_dt," \
                " (select count(*) from ecosystem_object where ecosystem_id = e.ecosystem_id) as num_objects" \
                " from ecosystem e" \
                " join ecotemplate et on e.ecotemplate_id = et.ecotemplate_id" \
                " where e.ecosystem_id = '" + sEcosystemID + "'"
            
            db = catocommon.new_conn()
            dr = db.select_row_dict(sSQL)
            if db.error:
                raise Exception("Ecosystem Object: Unable to get Ecosystem from database. " + db.error)

            if dr:
                self.ID = dr["ecosystem_id"]
                self.Name = dr["ecosystem_name"]
                self.AccountID = dr["account_id"]
                self.EcotemplateID = dr["ecotemplate_id"]
                self.EcotemplateName = dr["ecotemplate_name"]
                self.Description = (dr["ecosystem_desc"] if dr["ecosystem_desc"] else "")
                self.StormFile = (dr["storm_file"] if dr["storm_file"] else "")
                self.StormStatus = (dr["storm_status"] if dr["storm_status"] else "")
                self.CreatedDate = (str(dr["created_dt"]) if dr["created_dt"] else "")
                self.LastUpdate = (str(dr["last_update_dt"]) if dr["storm_status"] else "")
                self.NumObjects = str(dr["num_objects"])
            else: 
                raise Exception("Error building Ecosystem object: " + db.error)
        except Exception as ex:
            raise ex
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.__dict__, default=uiCommon.jsonSerializeHandler)
#            sb = []
#            sb.append("{")
#            sb.append("\"%s\" : \"%s\"," % ("ID", self.ID))
#            sb.append("\"%s\" : \"%s\"," % ("Name", self.Name))
#            sb.append("\"%s\" : \"%s\"," % ("EcotemplateID", self.EcotemplateID))
#            sb.append("\"%s\" : \"%s\"," % ("CreatedDate", self.CreatedDate))
#            sb.append("\"%s\" : \"%s\"" % ("Description", uiCommon.packJSON(self.Description)))
#            sb.append("}")
#            return "".join(sb)
        except Exception as ex:
            raise ex

            