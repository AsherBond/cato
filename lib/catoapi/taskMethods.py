
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
 
 
import web
import sys
from catoapi import api
from catocommon import catocommon
from catoui import uiGlobals
from catotask import task

class taskMethods:
    """"""

    def get_task_instance(self):
        """
        Gets the details of a Task Instance.
        
        Required Arguments: instance
            The Task Instance identifier.

        Returns: A JSON object.
        """
        try:
            # define the required parameters for this call
            required_params = ["instance"]
                
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
            obj = task.TaskInstance(args["instance"])
            if obj:
                if obj.Error:
                    return "{\"error\":\"%s\"}" % obj.Error

                return_string = obj.AsJSON()
                resp = api.response(method=method_name, response=return_string)
            else:
                resp = api.response(method=method_name,
                    error_code="GetError", error_detail="Unable to get Run Log for Task Instance [%s]." % args["instance"])
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.Write(output_format)
        except Exception as ex:
            resp = api.response(method=method_name,
                error_code="Exception", error_detail=ex.__str__())
            return resp.Write()

    def get_task_log(self):
        """
        Gets the run log for a Task Instance.
        
        Required Arguments: instance
            The Task Instance identifier.

        Returns: A JSON array of log entries.
        """
        try:
            # define the required parameters for this call
            required_params = ["instance"]
                
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
            obj = task.TaskRunLog(args["instance"])
            if obj:
                return_string = obj.AsJSON()
                resp = api.response(method=method_name, response=return_string)
            else:
                resp = api.response(method=method_name,
                    error_code="GetError", error_detail="Unable to get Run Log for Task Instance [%s]." % args["instance"])
            
            # is this a JSONP request?        
            if "callback" in args:
                return api.perform_callback(uiGlobals.web, args["callback"], resp)
            
            #if we made it all the way here, just return the raw xml
            return resp.Write(output_format)
        except Exception as ex:
            resp = api.response(method=method_name,
                error_code="Exception", error_detail=ex.__str__())
            return resp.Write()

    
