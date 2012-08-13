
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


            obj = ecosystem.Ecotemplate()
            obj(args["name"], args["description"])
            if obj is not None:
                result, msg = obj.DBSave()
                if result:
                    catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.EcoTemplate, obj.ID, obj.Name, "Ecotemplate created.")
                    if args["output_format"] == "json":
                        return R(response=obj.AsJSON())
                    elif args["output_format"] == "text":
                        return R(response=obj.ID)
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
                    return R(response=obj.ID)
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
                else:
                    return R(response=obj.AsXML())
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
                return R(response=obj.GetObjects(fltr))
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
                return R(response=obj.GetLog(fltr))
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
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Ecotemplate for identifier [%s]." % args["ecotemplate"])
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

