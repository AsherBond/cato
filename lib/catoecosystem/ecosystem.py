
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
from catocommon import catocommon
from catocloud import cloud

try:
    from catoimage import image
except (AttributeError, ImportError):
    pass

try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

# Note: this is not a container for Ecotemplate objects - it's just a rowset from the database
# with an AsJSON method.
# why? Because we don't need a full object for list pages and dropdowns.
class Ecotemplates(object):
    rows = {}
    def __init__(self, sFilter=""):
        try:
            db = catocommon.new_conn()
            sWhereString = ""
            if sFilter:
                aSearchTerms = sFilter.split()
                for term in aSearchTerms:
                    if term:
                        sWhereString += " and (et.ecotemplate_name like '%%" + term + "%%' " \
                            "or et.ecotemplate_desc like '%%" + term + "%%') "
    
            sSQL = """select et.ecotemplate_id as ID, 
                et.ecotemplate_name as Name, 
                et.ecotemplate_desc as Description,
                (select count(*) from ecosystem where ecotemplate_id = et.ecotemplate_id) as InUse,
                group_concat(ot.tag_name order by ot.tag_name separator ',') as Tags
                from ecotemplate et
                left outer join object_tags ot on et.ecotemplate_id = ot.object_id
                where 1=1 %s group by et.ecotemplate_id order by et.ecotemplate_name""" % sWhereString
            
            self.rows = db.select_all_dict(sSQL)
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.rows, default=catocommon.jsonSerializeHandler)
        except Exception as ex:
            raise ex
        
    def AsXML(self):
        try:
            dom = ET.fromstring('<Ecotemplates />')
            for row in self.rows:
                xml = catocommon.dict2xml(row, "Ecotemplate")
                node = ET.fromstring(xml.tostring())
                dom.append(node)
            
            return ET.tostring(dom)
        except Exception as ex:
            raise ex

    def AsText(self):
        try:
            keys = ['ID', 'Name']
            outrows = []
            for row in self.rows:
                cols = []
                for key in keys:
                    cols.append(str(row[key]))
                outrows.append("\t".join(cols))
              
            return "%s\n%s" % ("\t".join(keys), "\n".join(outrows))
        except Exception as ex:
            raise ex

class Ecotemplate(object):
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
        self.Runlist = []
        
    #the default constructor (manual creation)
    def FromArgs(self, sName, sDescription, sStormFileType=None, sStormFileText=None):
        if not sName:
            raise Exception("Error building Ecotemplate: Name is required.")

        self.Name = sName
        self.Description = sDescription
        self.StormFileType = sStormFileType
        self.StormFile = sStormFileText
        self.DBExists = self.dbExists()

    def FromName(self, sEcotemplateName):
        """Will get an Ecotemplate given either a name OR an id."""
        try:
            db = catocommon.new_conn()
            sSQL = "select ecotemplate_id from ecotemplate where ecotemplate_name = '{0}' or ecotemplate_id = '{0}'".format(sEcotemplateName)
            
            eid = db.select_col_noexcep(sSQL)
            if db.error:
                raise Exception("Ecotemplate Object: Unable to get Ecotemplate from database. " + db.error)

            if eid:
                self.FromID(eid)
            else: 
                raise Exception("Error getting Ecotemplate ID for Name [%s] - no record found. %s" % (sEcotemplateName, db.error))
        except Exception as ex:
            raise ex
        finally:
            db.close()

    def FromID(self, sEcotemplateID, bIncludeActions=True, bIncludeRunlist=True):
        try:
            sSQL = """select ecotemplate_id, ecotemplate_name, ecotemplate_desc, storm_file_type, storm_file
                from ecotemplate
                where ecotemplate_id = '%s'""" % sEcotemplateID

            db = catocommon.new_conn()
            dr = db.select_row_dict(sSQL)
            if db.error:
                raise Exception("Ecotemplate Object: Unable to get Ecotemplate from database. %s" % db.error)

            if dr is not None:
                self.DBExists = True
                self.ID = dr["ecotemplate_id"]
                self.Name = dr["ecotemplate_name"]
                self.Description = ("" if not dr["ecotemplate_desc"] else dr["ecotemplate_desc"])
                self.StormFileType = ("" if not dr["storm_file_type"] else dr["storm_file_type"])
                self.StormFile = ("" if not dr["storm_file"] else dr["storm_file"])
                
                if bIncludeActions:
                    sSQL = """select action_id, ecotemplate_id, action_name, action_desc, category, original_task_id, task_version, parameter_defaults, action_icon
                        from ecotemplate_action
                        where ecotemplate_id = '%s'""" % sEcotemplateID

                    dtActions = db.select_all_dict(sSQL)
                    if dtActions:
                        for drAction in dtActions:
                            ea = EcotemplateAction()
                            ea.FromRow(drAction, self)
                            if ea is not None:
                                self.Actions[ea.ID] = ea

                if bIncludeRunlist:
                    sSQL = """select item_id, item_type, item_order, item_notes, account_id, cloud_id, image_id, source, data
                        from ecotemplate_runlist
                        where ecotemplate_id = '%s' order by item_order""" % sEcotemplateID
    
                    dtRunlist = db.select_all_dict(sSQL)
                    if dtRunlist:
                        for drItem in dtRunlist:
                            ri = EcotemplateRunlistItem()
                            ri.FromRow(drItem, self)
                            if ri is not None:
                                self.Runlist.append(ri)
                                
#                    print self.Runlist[0].__dict__
#                    print self.Runlist[0].Image.__dict__
            else: 
                raise Exception("Error building Ecotemplate object: " + db.error)
        except Exception as ex:
            raise ex
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.__dict__, default=catocommon.jsonSerializeHandler)
        except Exception as ex:
            raise ex

    def AsXML(self):
        try:
            xml = catocommon.dict2xml(self.__dict__, "Ecotemplate")
            return xml.tostring()
        except Exception as ex:
            raise ex

    def AsText(self):
        try:
            keys = ["Name", "Description"]
            vals = []
            for key in keys:
                vals.append(str(getattr(self, key)))
              
            return "%s\n%s" % ("\t".join(keys), "\t".join(vals))
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
                        " '" + self.Name + "'," + \
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
            db = catocommon.new_conn()

            if not self.Name:
                return False, "Name is required."

            sSQL = "update ecotemplate set" \
                " ecotemplate_name = '" + self.Name + "'," \
                " ecotemplate_desc = " + (" null" if not self.Description else " '" + catocommon.tick_slash(self.Description) + "'") + "," \
                " storm_file_type = " + (" null" if not self.StormFileType else " '" + catocommon.tick_slash(self.StormFileType) + "'") + "," \
                " storm_file = " + (" null" if not self.StormFile else " '" + catocommon.tick_slash(self.StormFile) + "'") + \
                " where ecotemplate_id = '" + self.ID + "'"

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

    def GetEcosystems(self, ecotemplate_id, account_id=""):
        ecosystems = {}
        
        try:
            db = catocommon.new_conn()
            account_clause = ""
            if account_id:
                account_clause = " and account_id = '%s'" % account_id
            
            sSQL = """select ecosystem_id, account_id, ecosystem_name, ecosystem_desc
                from ecosystem
                where ecotemplate_id = '%s' %s
                order by ecosystem_name""" % (ecotemplate_id, account_clause)

            dt = db.select_all_dict(sSQL)
            if db.error:
                print(db.error)

            if dt:
                for dr in dt:
                    e = Ecosystem()
                    e.ID = dr["ecosystem_id"]
                    e.FromArgs(dr["ecosystem_name"], dr["ecosystem_desc"], ecotemplate_id, dr["account_id"])
                    if e:
                        ecosystems[dr["ecosystem_id"]] = e

            return ecosystems
        
        except Exception as ex:
            raise ex
        finally:
            db.close()

class EcotemplateAction(object):
    def __init__(self):
        self.ID = None
        self.Name = None
        self.Description = None
        self.Category = None
        self.OriginalTaskID = None
        self.TaskVersion = None
        self.Icon = None
        self.ParameterDefaultsXML = None
        self.Ecotemplate = None #pointer to our parent Template.

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

# Ecotemplates have a runlist, which is a simple list of these objects.
class EcotemplateRunlistItem(object):
    def __init__(self):
        self.ID = None
        self.Type = None
        self.Order = None
        self.Notes = None
        self.Account = None
        self.Cloud = None
        self.Image = None
        self.Source = None
        self.Data = None
        self.Ecotemplate = None
        
    def FromRow(self, dr, et):
        try:
            self.Ecotemplate = et
            self.ID = dr["item_id"]
            self.Type = dr["item_type"]
            self.Order = dr["item_order"]
            self.Notes = dr["item_notes"]
            self.Source = dr["source"]
            self.Data = dr["data"]

            if dr["account_id"]:
                ca = cloud.CloudAccount()
                ca.FromID(dr["account_id"])
                if ca:
                    self.Account = ca
                    
            if dr["cloud_id"]:
                c = cloud.Cloud()
                c.FromID(dr["cloud_id"])
                if c:
                    self.Cloud = c

            if dr["image_id"]:
                i = image.Image()
                i.FromID(dr["image_id"])
                if i:
                    self.Image = i
            
            # OK, all the following has some rules:
            # The runlist item may or may not just be a pointer to an image.  If so, 
            # we'll want to pull some properties up from the image and populate them here.
            # HOWEVER, if the main value here isn't empty, don't pull up from the image.
            if self.Image:
                self.Source = i.Source if not self.Source else self.Source
                self.Data = i.Data if not self.Data else self.Data
                if not self.Account:
                    self.Account = i.Account
                if not self.Cloud:
                    self.Cloud = i.Cloud
       
        except Exception as ex:
            raise ex

# Note: this is not a container for Ecotemplate objects - it's just a rowset from the database
# with an AsJSON method.
# why? Because we don't need a full object for list pages and dropdowns.
class Ecosystems(object):
    rows = {}
    def __init__(self, sAccountID="", sFilter=""):
        try:
            db = catocommon.new_conn()
            sAccountClause = ""
            if sAccountID:
                sAccountClause = "and e.account_id = '%s'" % sAccountID
                
            sWhereString = ""
            if sFilter:
                aSearchTerms = sFilter.split()
                for term in aSearchTerms:
                    if term:
                        sWhereString += " and (e.ecosystem_name like '%%" + term + "%%' " \
                            "or e.ecosystem_desc like '%%" + term + "%%' " \
                            "or et.ecotemplate_name like '%%" + term + "%%') "
    
            sSQL = """select 
                e.ecosystem_id as ID, 
                e.ecosystem_name as Name, 
                e.ecosystem_desc as Description, 
                e.account_id as AccountID, 
                et.ecotemplate_id as EcotemplateID,
                et.ecotemplate_name as EcotemplateName,
                e.storm_status as StormStatus, 
                e.created_dt as CreatedDate, 
                e.last_update_dt as LastUpdate, 
                e.request_id as RequestID,
                (select count(*) from ecosystem_object where ecosystem_id = e.ecosystem_id) as NumObjects,
                group_concat(ot.tag_name order by ot.tag_name separator ',') as Tags
                from ecosystem e
                join ecotemplate et on e.ecotemplate_id = et.ecotemplate_id
                left outer join object_tags ot on e.ecosystem_id = ot.object_id
                where 1=1 %s %s group by e.ecosystem_id order by e.ecosystem_name""" % (sAccountClause, sWhereString)
            
            self.rows = db.select_all_dict(sSQL)
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.rows, default=catocommon.jsonSerializeHandler)
        except Exception as ex:
            raise ex
        
    def AsXML(self):
        try:
            dom = ET.fromstring('<Ecosystems />')
            for row in self.rows:
                xml = catocommon.dict2xml(row, "Ecosystem")
                node = ET.fromstring(xml.tostring())
                dom.append(node)
            
            return ET.tostring(dom)
        except Exception as ex:
            raise ex

    def AsText(self):
        try:
            keys = ['ID', 'Name', 'StormStatus']
            outrows = []
            for row in self.rows:
                cols = []
                for key in keys:
                    cols.append(str(row[key]))
                outrows.append("\t".join(cols))
              
            return "%s\n%s" % ("\t".join(keys), "\n".join(outrows))
        except Exception as ex:
            raise ex

class Ecosystem(object):
    def __init__(self):
        self.ID = catocommon.new_guid()
        self.Name = None
        self.Description = None
        self.StormFile = None
        self.AccountID = None
        self.EcotemplateID = None
        self.EcotemplateName = None #no referenced objects just yet, just the name and ID until we need more.
        self.ParameterXML = None
        self.CloudID = None
        self.StormStatus = None
        self.CreatedDate = None
        self.LastUpdate = None
        self.NumObjects = 0

    def FromArgs(self, sName, sDescription, sEcotemplateID, sAccountID):
        if not sName or not sEcotemplateID or not sAccountID:
            raise Exception("Error building Ecosystem: Name, Ecotemplate and Cloud Account are required.")

        self.Name = sName
        self.Description = sDescription
        self.EcotemplateID = sEcotemplateID
        self.AccountID = sAccountID

    def Objects(self, sFilter=""):
        try:
            db = catocommon.new_conn()
                
            sWhereString = ""
            if sFilter:
                aSearchTerms = sFilter.split()
                for term in aSearchTerms:
                    if term:
                        sWhereString += " and (eo.ecosystem_object_id like '%%" + term + "%%' " \
                            "or eo.ecosystem_object_type like '%%" + term + "%%' " \
                            "or c.cloud_name like '%%" + term + "%%') "
    
            sSQL = """select 
                eo.ecosystem_object_id as EcosystemObjectID, 
                eo.ecosystem_object_type as EcosystemObjectType,
                eo.added_dt as AddedDate, 
                c.cloud_id as CloudID, 
                c.cloud_name as CloudName
                from ecosystem_object eo
                join clouds c on c.cloud_id = eo.cloud_id
                where ecosystem_id='%s' %s order by eo.ecosystem_object_id""" % (self.ID, sWhereString)
            
            rows = db.select_all_dict(sSQL)
            if rows:
                return rows
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()
        
    def ObjectsAsJSON(self, sFilter=""):
        try:
            objects = self.Objects(sFilter)
            if objects:
                return json.dumps(objects, default=catocommon.jsonSerializeHandler)
        except Exception as ex:
            raise ex

    def ObjectsAsXML(self, sFilter=""):
        try:
            objects = self.Objects(sFilter)
            if objects:
                dom = ET.fromstring('<EcosystemLog />')
                for row in objects:
                    xml = catocommon.dict2xml(row, "Item")
                    node = ET.fromstring(xml.tostring())
                    dom.append(node)
                
                return ET.tostring(dom)
        except Exception as ex:
            raise ex

    def ObjectsAsText(self, sFilter=""):
        try:
            log = self.Objects(sFilter)
            if log:
                keys = ['EcosystemObjectType', 'EcosystemObjectID', 'CloudName', 'AddedDate']
                rows = []
                for row in log:
                    cols = []
                    for key in keys:
                        cols.append(str(row[key]))
                    rows.append("\t".join(cols))
                  
                return "%s\n%s" % ("\t".join(keys), "\n".join(rows))
        except Exception as ex:
            raise ex

    def Log(self, sFilter=""):
        try:
            db = catocommon.new_conn()
                
            sWhereString = ""
            if sFilter:
                aSearchTerms = sFilter.split()
                for term in aSearchTerms:
                    if term:
                        sWhereString += " and (ecosystem_object_id like '%%" + term + "%%' " \
                            "or ecosystem_object_type like '%%" + term + "%%' " \
                            "or logical_id like '%%" + term + "%%' " \
                            "or status like '%%" + term + "%%' " \
                            "or log like '%%" + term + "%%') "
    
            sSQL = """select 
                ecosystem_object_id as EcosystemObjectID, 
                ecosystem_object_type as EcosystemObjectType, 
                logical_id as LogicalID, 
                status as Status, 
                log as Log
                from ecosystem_log
                where ecosystem_id='%s' %s order by ecosystem_log_id""" % (self.ID, sWhereString)
            
            rows = db.select_all_dict(sSQL)
            if rows:
                return rows
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def LogAsJSON(self, sFilter=""):
        try:
            log = self.Log(sFilter)
            if log:
                return json.dumps(log, default=catocommon.jsonSerializeHandler)
        except Exception as ex:
            raise ex

    def LogAsXML(self, sFilter=""):
        try:
            log = self.Log(sFilter)
            if log:
                dom = ET.fromstring('<EcosystemLog />')
                for row in log:
                    xml = catocommon.dict2xml(row, "Item")
                    node = ET.fromstring(xml.tostring())
                    dom.append(node)
                
                return ET.tostring(dom)
        except Exception as ex:
            raise ex

    def LogAsText(self, sFilter=""):
        try:
            log = self.Log(sFilter)
            if log:
                keys = ['EcosystemObjectType', 'LogicalID', 'EcosystemObjectID', 'Status', 'Log']
                rows = []
                for row in log:
                    cols = []
                    for key in keys:
                        cols.append(str(row[key]))
                    rows.append("\t".join(cols))
                  
                return "%s\n%s" % ("\t".join(keys), "\n".join(rows))
        except Exception as ex:
            raise ex

                
    @staticmethod
    def DBCreateNew(sName, sEcotemplateID, sAccountID, sDescription="", sStormStatus="", sParameterXML="", sCloudID=""):
        try:
            if not sName or not sEcotemplateID or not sAccountID:
                return None, "Name, Ecotemplate and Cloud Account are required Ecosystem properties."
              
            db = catocommon.new_conn()
            
            # check the template
            sSQL = "select ecotemplate_id from ecotemplate where ecotemplate_id = '{0}' or ecotemplate_name = '{0}'".format(sEcotemplateID)
            etid = db.select_col_noexcep(sSQL)
            if not etid:
                return None, "Unable to create Ecosystem, Ecotemplate for identifier [%s] not found." % sEcotemplateID
            
            # check the account
            sSQL = "select account_id from cloud_account where account_id = '{0}' or account_name = '{0}'".format(sAccountID)
            caid = db.select_col_noexcep(sSQL)
            if not caid:
                return None, "Unable to create Ecosystem, Account for identifier [%s] not found." % sAccountID

            # if provided, check the cloud
            cid = ""
            if sCloudID:
                sSQL = "select cloud_id from clouds where cloud_id = '{0}' or cloud_name = '{0}'".format(sCloudID)
                cid = db.select_col_noexcep(sSQL)
                if not cid:
                    return None, "Unable to create Ecosystem, Cloud for identifier [%s] not found." % sCloudID
            
            
            sID = catocommon.new_guid()

            sSQL = "insert into ecosystem (ecosystem_id, ecosystem_name, ecosystem_desc, account_id, ecotemplate_id," \
                " storm_file, storm_status, storm_parameter_xml, storm_cloud_id, created_dt, last_update_dt)" \
                " select '" + sID + "'," \
                " '" + sName + "'," \
                + (" null" if not sDescription else " '" + catocommon.tick_slash(sDescription) + "'") + "," \
                " '" + caid + "'," \
                " ecotemplate_id," \
                " storm_file," \
                + (" null" if not sStormStatus else " '" + catocommon.tick_slash(sStormStatus) + "'") + "," \
                + (" null" if not sParameterXML else " '" + catocommon.tick_slash(sParameterXML) + "'") + "," \
                + (" null" if not cid else " '" + cid + "'") + "," \
                " now(), now()" \
                " from ecotemplate where ecotemplate_id = '" + etid + "'"
            
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
            db = catocommon.new_conn()
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
            
            if not db.exec_db_noexcep(sSQL):
                return False, db.error
            
            return True, ""
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def FromName(self, sEcosystemName):
        """Will get an Ecosystem given either a name OR an id."""
        try:
            db = catocommon.new_conn()
            sSQL = "select ecosystem_id from ecosystem where ecosystem_name = '{0}' or ecosystem_id = '{0}'".format(sEcosystemName)
            
            eid = db.select_col_noexcep(sSQL)
            if db.error:
                raise Exception("Ecosystem Object: Unable to get Ecosystem from database. " + db.error)

            if eid:
                self.FromID(eid)
            else: 
                raise Exception("Error getting Ecosystem ID for Name [%s] - no record found. %s" % (sEcosystemName, db.error))
        except Exception as ex:
            raise ex
        finally:
            db.close()

    def FromID(self, sEcosystemID):
        try:
            db = catocommon.new_conn()
            sSQL = "select e.ecosystem_id, e.ecosystem_name, e.ecosystem_desc, e.storm_file, e.storm_status," \
                " e.account_id, e.ecotemplate_id, et.ecotemplate_name, e.created_dt, e.last_update_dt," \
                " (select count(*) from ecosystem_object where ecosystem_id = e.ecosystem_id) as num_objects" \
                " from ecosystem e" \
                " join ecotemplate et on e.ecotemplate_id = et.ecotemplate_id" \
                " where e.ecosystem_id = '" + sEcosystemID + "'"
            
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
                raise Exception("Error building Ecosystem object for ID [%s] - no record found. %s" % (self.ID, db.error))
        except Exception as ex:
            raise ex
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.__dict__, default=catocommon.jsonSerializeHandler)
        except Exception as ex:
            raise ex

    def AsXML(self):
        try:
            xml = catocommon.dict2xml(self.__dict__, "Ecosystem")
            return xml.tostring()
        except Exception as ex:
            raise ex

    def AsText(self):
        try:
            keys = ["Name", "EcotemplateName", "StormStatus", "CreatedDate", "NumObjects"]
            vals = []
            for key in keys:
                vals.append(str(getattr(self, key)))
              
            return "%s\n%s" % ("\t".join(keys), "\t".join(vals))
        except Exception as ex:
            raise ex

