
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
from catoecosystem import ecosystem
from catocloud import cloud
from catocommon import catocommon

class taskMethods:
    """"""

    def get_task_instance_status(self, args):
        """
        Gets just the Status of a Task Instance.
        
        Required Arguments: instance
            The Task Instance identifier.

        Returns: The Instance Status.
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

                return R(response=obj.Instance["task_status"])
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Status for Task Instance [%s]." % args["instance"])
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

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
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Task Instance [%s]." % args["instance"])
            
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

    def run_task(self, args):
        """
        Gets the run log for a Task Instance.
        
        Required Arguments: 
            task - Either the Task ID or Name.
            version - The Task Version.  (Unnecessary if 'task' is an ID.)
            
        Optional Arguments:
            debug - an integer (0-4) where 0 is none, 2 is normal and 4 is verbose.  Default is 2.
            ecosystem - the ID or Name of an Ecosystem.  Certain Task commands are scoped to this Ecosystem.
            account - the ID or Name of a Cloud Account.  Certain Task commands require a Cloud Account.
            parameter_xml - An XML document defining parameters for the Task.

        Returns: A JSON object, the Task Instance.
            If 'output_format' is set to 'text', returns only a Task Instance ID.
        """
        try:
            required_params = ["task"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp
            
            ver = args["version"] if args.has_key("version") else ""

            # find the task
            obj = task.Task()
            obj.FromNameVersion(args["task"], ver)
            if obj:
                task_id = obj.ID
                debug = args["debug"] if args.has_key("debug") else "2"
                
                # annoying, but we need to reconcile the ecosystem arg to an ID
                ecosystem = args["ecosystem"] if args.has_key("ecosystem") else ""
                ecosystem_id = ""
                if ecosystem:
                    e = ecosystem.Ecosystem()
                    e.FromName(args["ecosystem"])
                    if e:
                        ecosystem_id = e.ID
                
                # same for account
                account_id = ""
                account = args["account"] if args.has_key("account") else ""
                if account:
                    ca = cloud.CloudAccount()
                    ca.FromName(args["account"])
                    if ca:
                        account_id = ca.ID

                parameter_xml = args["parameter_xml"] if args.has_key("parameter_xml") else ""

                # try to launch it
                ti = catocommon.add_task_instance(task_id, args["_user_id"], debug, parameter_xml, ecosystem_id, account_id, "", "")
                
                if ti:
                    if args["output_format"] == "text":
                        return ti
                    else:
                        instance = task.TaskInstance(ti)
                        if instance:
                            return R(response=instance.AsJSON())

                # uh oh, something went wrong but we don't know what.
                return R(err_code=R.Codes.GetError, err_detail="Unable to run Task [%s %s].  Check the log for details." % (args["task"], ver))
                
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to find Task for ID or Name/Version [%s/%s]." % (args["task"], ver))

        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def stop_task(self, args):
        """
        Stops a running Task Instance.
        
        Required Arguments: instance
            The Task Instance identifier.

        Returns: Nothing if successful, error messages on failure.
        """
        try:
            required_params = ["instance"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp


            ti = task.TaskInstance(args["instance"])
            if ti:
                ti.Stop()
                return R(response="Task successfully stopped.")
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Run Log for Task Instance [%s]." % args["instance"])
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def list_tasks(self, args):        
        """
        Lists all Tasks.
            Only 'Default' versions are shown.
        
        Optional Arguments: 
            filter - will filter a value match in Task Name, Code or Description.
        
        Returns: An array of all Tasks with basic attributes.
        """
        try:
            fltr = args["filter"] if args.has_key("filter") else ""

            obj = task.Tasks(sFilter=fltr)
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText())
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.ListError, err_detail="Unable to list Tasks.")
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

