
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
System endpoint methods.
"""
from catolog import catolog
logger = catolog.get_logger(__name__)

import traceback
import json

try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

from catoapi import api
from catoapi.api import response as R
from catocommon import catocommon
from catotask import task

class sysMethods:
    """These are utility methods for the Cato system."""

    # ## NOTE:
    # ## many of the functions here aren't done up in pretty classes.
    # ## ... this is sort of a catch-all module.
    def import_backup(self, args):
        """
        Imports an XML backup file.
        
        NOTE: this function is a near identical copy of catoadminui/uiMethods.wmCreateObjectsFromXML.
        Any changes here should be considered there as well.
        """
        # define the required parameters for this call
        required_params = ["xml"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        # what types of things were in this backup?  what are their new ids?
        items = []

        # parse it as a validation, and to find out what's in it.
        xd = None
        try:
            xd = ET.fromstring(args["xml"])
        except ET.ParseError as ex:
            return R(err_code=R.Codes.Exception, err_detail="File is not properly formatted XML.")
        
        if xd is not None:
            for xtask in xd.iterfind("task"):
                logger.info("Importing Task [%s]" % xtask.get("name", "Unknown"))
                t = task.Task()
                t.FromXML(ET.tostring(xtask))

                result, err = t.DBSave()
                if result:
                    catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.Task, t.ID, t.Name, "Created by import.")

                    items.append({"type" : "task", "id" : t.ID, "Name" : t.Name, "Info" : "Success"}) 
                else:
                    if err:
                        items.append({"type" : "task", "id" : t.ID, "Name" : t.Name, "Info" : err}) 
                    else:
                        items.append({"type" : "task", "id" : t.ID, "Name" : t.Name, "Info" : "Unable to create Task. No error available."}) 
                

        else:
            items.append({"info" : "Unable to create Task from backup XML."})
        
        if args["output_format"] == "json":
            return R(response=catocommon.ObjectOutput.IterableAsJSON(items))
        elif args["output_format"] == "text":
            return R(response=catocommon.ObjectOutput.IterableAsText(items, ["Name", "Info"], args["output_delimiter"]))
        else:
            return R(response=catocommon.ObjectOutput.IterableAsXML(items, "Results", "Result"))
    
    def list_processes(self, args):        
        """
        Lists all Cato Processes.
        """
        db = catocommon.new_conn()
        sSQL = """select app_instance as Instance,
            app_name as Component,
            heartbeat as Heartbeat,
            case master when 1 then 'Yes' else 'No' end as Enabled,
            timestampdiff(MINUTE, heartbeat, now()) as MinutesIdle,
            load_value as LoadValue, platform, hostname
            from application_registry
            order by component, master desc"""
        
        rows = db.select_all_dict(sSQL)
        db.close()

        if rows:
            if args["output_format"] == "json":
                resp = catocommon.ObjectOutput.IterableAsJSON(rows)
                return R(response=resp)
            elif args["output_format"] == "text":
                keys = ['Instance', 'Component', 'Heartbeat', 'Enabled', 'LoadValue', 'MinutesIdle']
                outrows = []
                if rows:
                    for row in rows:
                        cols = []
                        for key in keys:
                            cols.append(str(row[key]))
                        outrows.append("\t".join(cols))
                      
                return "%s\n%s" % ("\t".join(keys), "\n".join(outrows))
            else:
                dom = ET.fromstring('<Processes />')
                if rows:
                    for row in rows:
                        xml = catocommon.dict2xml(row, "Process")
                        node = ET.fromstring(xml.tostring())
                        dom.append(node)
                
                return R(response=ET.tostring(dom))
        else:
            return R(err_code=R.Codes.ListError, err_detail="Unable to list Processes.")
