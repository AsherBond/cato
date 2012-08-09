
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
 
 
from catoapi import api
from catoapi.api import response as R
from catotask import task

class taskMethods:
    """"""

    def get_task_instance(self, args):
        """
        Gets the details of a Task Instance.
        
        Required Arguments: instance
            The Task Instance identifier.

        Returns: A JSON object.
        """
        try:
            required_params = ["instance"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp

            obj = task.TaskInstance(args["instance"])
            if obj:
                if obj.Error:
                    return R(err_code=R.Codes.GetError, err_detail=obj.Error)

                return R(response=obj.AsJSON())
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Run Log for Task Instance [%s]." % args["instance"])
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def get_task_log(self, args):
        """
        Gets the run log for a Task Instance.
        
        Required Arguments: instance
            The Task Instance identifier.

        Returns: A JSON array of log entries.
        """
        try:
            required_params = ["instance"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp


            obj = task.TaskRunLog(args["instance"])
            if obj:
                return R(response=obj.AsJSON())
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Run Log for Task Instance [%s]." % args["instance"])
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    
