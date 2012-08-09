
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

import web
import sys
from catoapi import api
from catocommon import catocommon
from catoui import uiGlobals
from catoecosystem import ecosystem

class ecoMethods:
    """These are methods for Ecosystems, Ecotemplates and other related items."""

    def create_ecotemplate(self):        
        """
        Create a new Ecotemplate.
        
        Required Arguments: name
        Optional Arguments: description
        
        Returns: A JSON Ecotemplate object.
        """
        try:
            # define the required parameters for this call
            required_params = ["name"]
                
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = web.input()
            web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args, required_params)
            if not user_id:
                return resp
            
            output_format = ""
            if args.has_key("output_format"):
                output_format = args["output_format"]
            # end consistent


            # this is the call-specific code
            obj = ecosystem.Ecotemplate()
            obj(args["name"], args["description"])
            if obj is not None:
                result, msg = obj.DBSave()
                if result:
                    catocommon.write_add_log(user_id, catocommon.CatoObjectTypes.EcoTemplate, obj.ID, obj.Name, "Ecotemplate created.")
                    return_string = obj.AsJSON()
                    resp = api.response(method=method_name, response=return_string)
                else:
                    # uiCommon.log(msg, 2)
                    resp = api.response(method=method_name,
                        error_code="CreateError", error_detail=msg)
            else:
                    resp = api.response(method=method_name,
                        error_code="CreateError", error_detail="Unable to create Ecotemplate.")
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.Write(output_format)
        except Exception as ex:
            resp = api.response(method=method_name,
                error_code="Exception", error_detail=ex.__str__())
            return resp.Write()

    def create_ecosystem(self):        
        """
        Create a new Ecosystem.
        
        Required Arguments: 
            ecotemplate - the ID or Name of the Ecotemplate
            account - the ID or Name of a Cloud Account
            name - a name for the new Ecosystem
            
        Optional Arguments: description
        
        Returns: A JSON Ecosystem object.
        """
        try:
            # define the required parameters for this call
            required_params = ["ecotemplate", "account", "name"]
                
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = web.input()
            web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args, required_params)
            if not user_id:
                return resp
            
            output_format = ""
            if args.has_key("output_format"):
                output_format = args["output_format"]
            # end consistent


            # this is the call-specific code

            desc = args["description"] if args.has_key("description") else ""

            obj, msg = ecosystem.Ecosystem.DBCreateNew(args["name"],
                 args["ecotemplate"], 
                 args["account"], 
                 desc)
            if obj:
                catocommon.write_add_log(user_id, catocommon.CatoObjectTypes.Ecosystem, obj.ID, obj.Name, "Ecosystem created.")
                return_string = obj.AsJSON()
                resp = api.response(method=method_name, response=return_string)
            else:
                resp = api.response(method=method_name,
                    error_code="CreateError", error_detail=msg)
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.Write(output_format)
        except Exception as ex:
            resp = api.response(method=method_name,
                error_code="Exception", error_detail=ex.__str__())
            return resp.Write()

    def list_ecosystems(self):        
        """
        Lists all Ecosystems.
        
        Optional Arguments: 
            filter - will filter a value match in Ecosystem Name, Description or Ecotemplate Name.
        
        Returns: A JSON array of all Ecosystems with basic attributes.
        """
        try:
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = web.input()
            web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args)
            if not user_id:
                return resp
            
            output_format = ""
            if args.has_key("output_format"):
                output_format = args["output_format"]
            # end consistent


            # this is the call-specific code

            fltr = args["filter"] if args.has_key("filter") else ""

            obj = ecosystem.Ecosystems(sFilter=fltr)
            if obj:
                return_string = obj.AsJSON()
                resp = api.response(method=method_name, response=return_string)
            else:
                resp = api.response(method=method_name,
                    error_code="ListError", error_detail="Unable to list Ecosystems.")
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.Write(output_format)
        except Exception as ex:
            resp = api.response(method=method_name,
                error_code="Exception", error_detail=ex.__str__())
            return resp.Write()

    def list_ecotemplates(self):        
        """
        Lists all Ecotemplates.
        
        Optional Arguments: 
            filter - will filter a value match in Ecotemplate Name or Description.
        
        Returns: A JSON array of all Ecotemplates with basic attributes.
        """
        try:
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = web.input()
            web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args)
            if not user_id:
                return resp
            
            output_format = ""
            if args.has_key("output_format"):
                output_format = args["output_format"]
            # end consistent


            # this is the call-specific code

            fltr = args["filter"] if args.has_key("filter") else ""
            print catocommon.unpackData(args["stormfile"])
            
            obj = ecosystem.Ecotemplates(sFilter=fltr)
            if obj:
                return_string = obj.AsJSON()
                resp = api.response(method=method_name, response=return_string)
            else:
                resp = api.response(method=method_name,
                    error_code="ListError", error_detail="Unable to list Ecotemplates.")
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.Write(output_format)
        except Exception as ex:
            resp = api.response(method=method_name,
                error_code="Exception", error_detail=ex.__str__())
            return resp.Write()
        
    def get_ecosystem(self):        
        """
        Gets an Ecosystem object.
        
        Required Arguments: ecosystem
            (Value can be either an id or name.)
        
        Returns: A JSON Ecosystem object.
        """
        try:
            # define the required parameters for this call
            required_params = ["ecosystem"]
                
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = web.input()
            web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args, required_params)
            if not user_id:
                return resp

            output_format = ""
            if args.has_key("output_format"):
                output_format = args["output_format"]
            # end consistent

            # this is the call-specific code
            obj = ecosystem.Ecosystem()
            obj.FromName(args["ecosystem"])
            if obj:
                return_string = obj.AsJSON()
                resp = api.response(method=method_name, response=return_string)
            else:
                resp = api.response(method=method_name,
                    error_code="GetError", error_detail="Unable to get Ecosystem for identifier [%s]." % args["ecosystem"])
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.Write(output_format)
        except Exception as ex:
            resp = api.response(method=method_name,
                error_code="Exception", error_detail=ex.__str__())
            return resp.Write()

    def get_ecosystem_objects(self):        
        """
        Gets a list of all cloud objects associated with an Ecosystem.
        
        Required Arguments: ecosystem
            (Value can be either an id or name.)

        Optional Arguments: 
            filter - will filter a value match in Object ID, Object Type, or Cloud Name.
        
        Returns: A JSON array of Ecosystem objects.
        """

        try:
            # define the required parameters for this call
            required_params = ["ecosystem"]
                
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = web.input()
            web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args, required_params)
            if not user_id:
                return resp
            
            output_format = ""
            if args.has_key("output_format"):
                output_format = args["output_format"]
            # end consistent


            # this is the call-specific code
            fltr = args["filter"] if args.has_key("filter") else ""

            obj = ecosystem.Ecosystem()
            obj.FromName(args["ecosystem"])
            if obj:
                return_string = obj.GetObjects(fltr)
                resp = api.response(method=method_name, response=return_string)
            else:
                resp = api.response(method=method_name,
                    error_code="GetError", error_detail="Unable to get Ecosystem for identifier [%s]." % args["ecosystem"])
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.Write(output_format)
        except Exception as ex:
            resp = api.response(method=method_name,
                error_code="Exception", error_detail=ex.__str__())
            return resp.Write()

    def get_ecosystem_log(self):        
        """
        Gets the run log for an Ecosystem.
        
        Required Arguments: ecosystem
            (Value can be either an id or name.)

        Optional Arguments: 
            filter - will filter a value match in Object ID, Object Type, or Logical ID, Status or Log.
        
        Returns: A JSON array of log entries.
        """
        try:
            # define the required parameters for this call
            required_params = ["ecosystem"]
                
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = web.input()
            web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args, required_params)
            if not user_id:
                return resp
            
            output_format = ""
            if args.has_key("output_format"):
                output_format = args["output_format"]
            # end consistent


            # this is the call-specific code
            fltr = args["filter"] if args.has_key("filter") else ""

            obj = ecosystem.Ecosystem()
            obj.FromName(args["ecosystem"])
            if obj:
                return_string = obj.GetLog(fltr)
                resp = api.response(method=method_name, response=return_string)
            else:
                resp = api.response(method=method_name,
                    error_code="GetError", error_detail="Unable to get Ecosystem for identifier [%s]." % args["ecosystem"])
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.Write(output_format)
        except Exception as ex:
            resp = api.response(method=method_name,
                error_code="Exception", error_detail=ex.__str__())
            return resp.Write()

        