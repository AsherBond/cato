
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
Ecosystem/Ecotemplate endpoint methods.
"""

from catoapi import api
from catoapi.api import response as R
from catocommon import catocommon
from catoecosystem import ecosystem
from catotask import task

class ecoMethods:
    """These are methods for Ecosystems, Ecotemplates and other related items."""

    def create_ecotemplate(self, args):        
        """
        Create a new Ecotemplate.
        
        Required Arguments: name
        Optional Arguments: description
        
        Returns: A JSON Ecotemplate object.
        """
        try:
            # define the required parameters for this call
            required_params = ["name"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp

            desc = args["description"] if args.has_key("description") else ""
            sftype = args["storm_file_type"] if args.has_key("storm_file_type") else ""
            sftext = args["storm_file_text"] if args.has_key("storm_file_text") else ""

            obj = ecosystem.Ecotemplate()
            obj.FromArgs(args["name"], desc, sftype, sftext)
            if obj is not None:
                result, msg = obj.DBSave()
                if result:
                    catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.EcoTemplate, obj.ID, obj.Name, "Ecotemplate created.")
                    if args["output_format"] == "json":
                        return R(response=obj.AsJSON())
                    elif args["output_format"] == "text":
                        return R(response=obj.AsText())
                    else:
                        return R(response=obj.AsXML())
                else:
                    return R(err_code=R.Codes.CreateError, err_detail=msg)
            else:
                return R(err_code=R.Codes.CreateError, err_detail="Unable to create Ecotemplate.")
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def create_ecosystem(self, args):        
        """
        Create a new Ecosystem.
        
        Required Arguments: 
            ecotemplate - the ID or Name of the Ecotemplate
            account - the ID or Name of a Cloud Account
            name - a name for the new Ecosystem
            
        Optional Arguments: description
        
        Returns: An Ecosystem object.
            If 'output_format' is set to 'text', returns only an Ecosystem ID.
        """
        try:
            # define the required parameters for this call
            required_params = ["ecotemplate", "account", "name"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp


            desc = args["description"] if args.has_key("description") else ""

            obj, msg = ecosystem.Ecosystem.DBCreateNew(args["name"],
                 args["ecotemplate"], 
                 args["account"], 
                 desc)
            if obj:
                catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.Ecosystem, obj.ID, obj.Name, "Ecosystem created.")
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText())
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.CreateError, err_detail=msg)
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def list_ecosystems(self, args):        
        """
        Lists all Ecosystems.
        
        Optional Arguments: 
            filter - will filter a value match in Ecosystem Name, Description or Ecotemplate Name.
        
        Returns: An array of all Ecosystems with basic attributes.
        """
        try:
            fltr = args["filter"] if args.has_key("filter") else ""

            obj = ecosystem.Ecosystems(sFilter=fltr)
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText())
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.ListError, err_detail="Unable to list Ecosystems.")
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def list_ecotemplates(self, args):        
        """
        Lists all Ecotemplates.
        
        Optional Arguments: 
            filter - will filter a value match in Ecotemplate Name or Description.
        
        Returns: An array of all Ecotemplates with basic attributes.
        """
        try:
            fltr = args["filter"] if args.has_key("filter") else ""
            
            obj = ecosystem.Ecotemplates(sFilter=fltr)
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText())
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.ListError, err_detail="Unable to list Ecotemplates.")
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())
        
    def get_ecosystem(self, args):        
        """
        Gets an Ecosystem object.
        
        Required Arguments: ecosystem
            (Value can be either an Ecosystem ID or Name.)
        
        Returns: An Ecosystem object.
        """
        try:
            # define the required parameters for this call
            required_params = ["ecosystem"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp


            obj = ecosystem.Ecosystem()
            obj.FromName(args["ecosystem"])
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText())
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Ecosystem for identifier [%s]." % args["ecosystem"])
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def get_ecosystem_actions(self, args):        
        """
        Gets an list of all Ecosystem Actions.
        
        Required Arguments: ecosystem
            (Value can be either an Ecosystem ID or Name.)
        
        Returns: A list of Actions.
        """
        try:
            # define the required parameters for this call
            required_params = ["ecosystem"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp


            obj = ecosystem.Ecosystem()
            obj.FromName(args["ecosystem"])
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.ActionsAsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.ActionsAsText())
                else:
                    return R(response=obj.ActionsAsXML())
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Ecosystem for identifier [%s]." % args["ecosystem"])
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def get_ecosystem_objects(self, args):        
        """
        Gets a list of all cloud objects associated with an Ecosystem.
        
        Required Arguments: ecosystem
            (Value can be either an Ecosystem ID or Name.)

        Optional Arguments: 
            filter - will filter a value match in Object ID, Object Type, or Cloud Name.
        
        Returns: A JSON array of Ecosystem objects.
        """

        try:
            # define the required parameters for this call
            required_params = ["ecosystem"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp


            fltr = args["filter"] if args.has_key("filter") else ""

            obj = ecosystem.Ecosystem()
            obj.FromName(args["ecosystem"])
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.ObjectsAsJSON(fltr))
                elif args["output_format"] == "text":
                    return R(response=obj.ObjectsAsText(fltr))
                else:
                    return R(response=obj.ObjectsAsXML(fltr))
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Ecosystem for identifier [%s]." % args["ecosystem"])
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def get_ecosystem_log(self, args):        
        """
        Gets the run log for an Ecosystem.
        
        Required Arguments: ecosystem
            (Value can be either an Ecosystem ID or Name.)

        Optional Arguments: 
            filter - will filter a value match in Object ID, Object Type, or Logical ID, Status or Log.
        
        Returns: A JSON array of log entries.
        """
        try:
            # define the required parameters for this call
            required_params = ["ecosystem"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp


            fltr = args["filter"] if args.has_key("filter") else ""

            obj = ecosystem.Ecosystem()
            obj.FromName(args["ecosystem"])
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.LogAsJSON(fltr))
                elif args["output_format"] == "text":
                    return R(response=obj.LogAsText(fltr))
                else:
                    return R(response=obj.LogAsXML(fltr))
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Ecosystem for identifier [%s]." % args["ecosystem"])
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def get_ecotemplate(self, args):        
        """
        Gets an Ecotemplate object.
        
        Required Arguments: ecotemplate
            (Value can be either an Ecotemplate ID or Name.)
        
        Returns: An Ecotemplate object.
        """
        try:
            # define the required parameters for this call
            required_params = ["ecotemplate"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp


            obj = ecosystem.Ecotemplate()
            obj.FromName(args["ecotemplate"])
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText())
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Ecotemplate for identifier [%s]." % args["ecotemplate"])
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def run_ecosystem_action(self, args):
        """
        Runs an Ecosystem Action.
        
        Required Arguments: 
            ecosystem - Either the Ecosystem ID or Name.
            action - The Action name.
            
        Optional Arguments:
            log_level - an integer (0-4) where 0 is none, 2 is normal and 4 is verbose.  Default is 2.
            parameter_xml - An XML document defining parameters for the Task.

        Returns: A JSON object, the Task Instance.
            If 'output_format' is set to 'text', returns only a Task Instance ID.
        """
        try:
            required_params = ["ecosystem", "action"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp
            
            # get the ecosystem
            e = ecosystem.Ecosystem()
            e.FromName(args["ecosystem"])
            if e.ID:
                # find the action
                a = e.GetAction(args["action"])
                if a:
                    # cool so far...
                    debug = args["log_level"] if args.has_key("log_level") else "2"
                    parameter_xml = args["parameter_xml"] if args.has_key("parameter_xml") else ""
    
                    # try to launch it
                    ti = catocommon.add_task_instance(a.TaskID, args["_user_id"], debug, parameter_xml, e.ID, e.AccountID, "", "")
                    
                    if ti:
                        if args["output_format"] == "text":
                            return ti
                        else:
                            instance = task.TaskInstance(ti)
                            if instance:
                                if args["output_format"] == "json":
                                    return R(response=instance.AsJSON())
                                elif args["output_format"] == "xml":
                                    return R(response=instance.AsXML())
    
                    # uh oh, something went wrong but we don't know what.
                    return R(err_code=R.Codes.GetError, err_detail="Unable to run Action [%s].  Check the log for details." % args["action"])
                
                else:
                    return R(err_code=R.Codes.GetError, err_detail="Unable to find Action for ID/Name [%s]." % args["action"])
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to find Ecosystem for ID or Name %[s]." % args["ecosystem"])

        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

