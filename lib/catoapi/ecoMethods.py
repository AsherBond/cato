
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

import sys
from catoapi import api
from catocommon import catocommon
from catoui import uiGlobals
from catoecosystem import ecosystem

class ecoMethods:
    db = None

    def create_ecotemplate(self):        
        """Create a new Ecotemplate."""
        try:
            # define the required parameters for this call
            required_params = ["name"]
                
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = uiGlobals.web.input()
            uiGlobals.web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args, required_params)
            if not user_id:
                return resp
            # end consistent

            # this is the call-specific code
            obj = ecosystem.Ecotemplate()
            obj.FromArgs(args["name"], args["description"])
            if obj is not None:
                result, msg = obj.DBSave()
                if result:
                    catocommon.write_add_log(user_id, catocommon.CatoObjectTypes.EcoTemplate, obj.ID, obj.Name, "Ecotemplate created.")
                    return_string = "<EcotemplateId>%s</EcotemplateId>" % obj.ID
                    resp = api.response.fromargs(method=method_name, response=return_string)
                else:
                    # uiCommon.log(msg, 2)
                    resp = api.response.fromargs(method=method_name,
                        error_code="CreateError", error_detail=msg)
            else:
                    resp = api.response.fromargs(method=method_name,
                        error_code="CreateError", error_detail="Unable to create Ecotemplate.")
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.asXMLString()
        except Exception as ex:
            raise ex

    def create_ecosystem(self):        
        """Create a new Ecosystem."""
        try:
            # define the required parameters for this call
            required_params = ["ecotemplate_id", "account_id", "name"]
                
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = uiGlobals.web.input()
            uiGlobals.web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args, required_params)
            if not user_id:
                return resp
            # end consistent

            # this is the call-specific code

            desc = args["description"] if args.has_key("description") else ""

            obj, msg = ecosystem.Ecosystem.DBCreateNew(args["name"],
                 args["ecotemplate_id"], 
                 args["account_id"], 
                 desc)
            if obj:
                catocommon.write_add_log(user_id, catocommon.CatoObjectTypes.Ecosystem, obj.ID, obj.Name, "Ecosystem created.")
                return_string = "<Ecosystem>%s</Ecosystem>" % obj.ID
                resp = api.response.fromargs(method=method_name, response=return_string)
            else:
                resp = api.response.fromargs(method=method_name,
                    error_code="CreateError", error_detail=msg)
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.asXMLString()
        except Exception as ex:
            raise ex

    def list_ecosystems(self):        
        """List all ecosystems."""
        try:
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = uiGlobals.web.input()
            uiGlobals.web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args)
            if not user_id:
                return resp
            # end consistent

            # this is the call-specific code

            filter = args["filter"] if args.has_key("filter") else ""

            obj = ecosystem.Ecosystems(sFilter=filter)
            if obj:
                return_string = obj.AsJSON()
                resp = api.response.fromargs(method=method_name, response=return_string)
            else:
                resp = api.response.fromargs(method=method_name,
                    error_code="ListError", error_detail="Unable to list Ecosystems.")
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.asXMLString()
        except Exception as ex:
            raise ex

    def list_ecotemplates(self):        
        """List all ecotemplates."""
        try:
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = uiGlobals.web.input()
            uiGlobals.web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args)
            if not user_id:
                return resp
            # end consistent

            # this is the call-specific code

            filter = args["filter"] if args.has_key("filter") else ""
            print catocommon.unpackData(args["stormfile"])
            
            obj = ecosystem.Ecotemplates(sFilter=filter)
            if obj:
                return_string = obj.AsJSON()
                resp = api.response.fromargs(method=method_name, response=return_string)
            else:
                resp = api.response.fromargs(method=method_name,
                    error_code="ListError", error_detail="Unable to list Ecotemplates.")
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.asXMLString()
        except Exception as ex:
            raise ex
        
    def get_ecosystem(self):        
        """Create a new Ecosystem."""
        try:
            # define the required parameters for this call
            required_params = ["ecosystem_id"]
                
            # this section should be consistent across most API calls
            this_function_name = sys._getframe().f_code.co_name
            method_name = "%s/%s" % (self.__class__.__name__, this_function_name)

            args = uiGlobals.web.input()
            uiGlobals.web.header('Content-Type', 'text/xml')

            # Authenticate the request and validate the arguments...
            user_id, resp = api.authentivalidate(method_name, uiGlobals.server, args, required_params)
            if not user_id:
                return resp
            # end consistent

            # this is the call-specific code
            obj = ecosystem.Ecosystem()
            obj.FromID(args["ecosystem_id"])
            if obj:
                return_string = obj.AsJSON()
                resp = api.response.fromargs(method=method_name, response=return_string)
            else:
                resp = api.response.fromargs(method=method_name,
                    error_code="GetError", error_detail="Unable to get Ecosystem for ID [%s]." % args["ecosystem_id"])
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.asXMLString()
        except Exception as ex:
            raise ex

        