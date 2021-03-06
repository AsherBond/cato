
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
 
from catolog import catolog
logger = catolog.get_logger(__name__)

import json

from catoapi import api
from catoapi.api import response as R
from catotask import task
from catocloud import cloud
from catocommon import catocommon

class taskMethods:
    """"""

    def create_task(self, args):        
        """Create a new Task.

Required Arguments: 

* `name` - a name for the new Task.
    
Optional Arguments:

* `code` - a Task code.
* `desc` - a Task description.

Returns: A [Task Object](restapi/api-response-objects.html#Task){:target="_blank"}.
"""
        # define the required parameters for this call
        required_params = ["name"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        code = args["code"] if "code" in args else ""
        desc = args["desc"] if "desc" in args else ""

        t = task.Task().DBCreateNew(args["name"], code, desc)
        catocommon.write_add_log(api._USER_ID, catocommon.CatoObjectTypes.Task, t.ID, t.Name, "Task created.")
        
        if args.get("output_format") == "json":
            return R(response=t.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=t.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=t.AsXML())
            
    def create_task_from_json(self, args):        
        """Create a new Task from a JSON Task backup document.

Required Arguments: 

* `json` - A properly formatted JSON representation of a Task.
    
Returns: A [Task Object](restapi/api-response-objects.html#Task){:target="_blank"}.
"""
        # define the required parameters for this call
        required_params = ["json"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        t = task.Task()
        t.FromJSON(args["json"], args.get("on_conflict"))
        result, msg = t.DBSave()

        if result:
            catocommon.write_add_log(api._USER_ID, catocommon.CatoObjectTypes.Task, t.ID, t.Name, "Task created.")
            if args.get("output_format") == "json":
                return R(response=t.AsJSON())
            elif args.get("output_format") == "text":
                return R(response=t.AsText(args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=t.AsXML())
        else:
            return R(err_code=R.Codes.CreateError, err_detail=msg)
            
    def get_task_instance_status(self, args):
        """Gets just the Status of a Task Instance.

Required Arguments: 

* `instance` - The Task Instance identifier.

Returns: The 'Status' from a [Task Instance Object](restapi/api-response-objects.html#TaskInstance){:target="_blank"}.
"""
        required_params = ["instance"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = task.TaskInstance(args["instance"])
        if obj.Error:
            return R(err_code=R.Codes.GetError, err_detail=obj.Error)

        if args.get("output_format") == "json":
            return R(response={"task_status": obj.task_status})
        elif args.get("output_format") == "xml":
            return R(response='<task_status>%s</task_status>' % obj.task_status)
        else:
            return R(response=obj.task_status)
            
    def get_task_instance(self, args):
        """Gets the details of a Task Instance.

Required Arguments: 

* `instance` - The Task Instance identifier.

Returns: A [Task Instance Object](restapi/api-response-objects.html#TaskInstance){:target="_blank"}.
"""
        required_params = ["instance"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = task.TaskInstance(args["instance"])
        if obj.Error:
            return R(err_code=R.Codes.GetError, err_detail=obj.Error)

        if not api.is_object_allowed(obj.task_id, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to details of this Task.")
            
        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())
            
    def resubmit_task_instance(self, args):
        """Resubmits an Errored or Cancelled Task Instance.  Resubmit is *only* valid on Errored or Cancelled Task Instances.

Required Arguments:
 
* `instance` - The Task Instance identifier.

Returns: Returns: Nothing if successful, error messages on failure.
"""
        # this is a developer function
        if not api._DEVELOPER:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Developers or Administrators can perform this function.")
        
        required_params = ["instance"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = task.TaskInstance(args["instance"])
        if obj.Error:
            return R(err_code=R.Codes.GetError, err_detail=obj.Error)

#                if deployment_id and sequence_instance:
#                    msg = "Task [%s] Instance [%s] resubmitted by [%s]." % (ti.task_name_label, ti.task_instance, username)
#                    deployment.WriteDeploymentLog(msg, dep_id=deployment_id, seq_inst=sequence_instance)

        if not api.is_object_allowed(obj.task_id, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to details of this Task.")
            
        result, err = obj.Resubmit(api._USER_ID)
        if result:
            return R(response="Instance [%s] successfully resubmitted." % args["instance"])
        else:
            return R(err_code=R.Codes.StartFailure, err_detail=err)

    def get_task_log(self, args):
        """Gets the run log for a Task Instance.

Required Arguments: 

* `instance` - The Task Instance identifier.

Returns: A [Task Log Object](restapi/api-response-objects.html#TaskLog){:target="_blank"}.
"""
        required_params = ["instance"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = task.TaskRunLog(args["instance"])

        if not api.is_object_allowed(obj.task_id, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Task.")
            
        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())

    def run_task(self, args):
        """Runs a Task.

Required Arguments: 

* `task` - Either the Task ID or Name.
* `version` - The Task Version.  (Unnecessary if 'task' is an ID.)
    
Optional Arguments:

* `log_level` - an integer (0-4) where 0 is none, 2 is normal and 4 is verbose.  Default is 2.
* `account` - the ID or Name of a Cloud Account.  Certain Task commands require a Cloud Account.
* `parameters` - A JSON or XML document defining parameters for the Task.
* `options` - a JSON object defining certain options for this Task.  Typically used to provide scope for extensions to the Task Engine.
* `run_later` - if provided, the Task will be scheduled to run at the specified date/time.  ex. "7/4/1776 15:30"
    
Returns: A [Task Instance Object](restapi/api-response-objects.html#TaskInstance){:target="_blank"}.

* If 'output_format' is set to 'text', returns only a Task Instance ID.
* If 'run_later' was specified, will return a success or error message.
"""
        # this is a developer function
        if not api._DEVELOPER:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Developers or Administrators can perform this function.")
        
        required_params = ["task"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp
        
        ver = args["version"] if "version" in args else ""

        # find the task
        obj = task.Task()
        obj.FromNameVersion(args["task"], ver, False)

        if not api.is_object_allowed(obj.ID, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Task.")
            
        task_id = obj.ID
        debug = args.get("log_level", "20")
        
        # not verifying this optional value because that would require importing a maestro lib
        # just use it as-is
        options = args.get("options", "")
        
        # same for account
        account_id = ""
        account = args.get("account", "")
        if account:
            ca = cloud.CloudAccount()
            ca.FromName(args["account"])
            if ca:
                account_id = ca.ID

        parameters = args.get("parameters", "")
        pxml = ""
        if parameters:
            # this will convert json OR xml params into the xml format we need
            pxml = catocommon.params2xml(parameters)

        if args.get("run_later"):
            obj.RunLater(args.get("run_later"), pxml, debug, account_id)
            return R(response="[%s] successfully scheduled." % obj.Name)
        else:
            # try to launch it
            ti = catocommon.add_task_instance(task_id, api._USER_ID, debug, pxml, account_id=account_id, options=options)
            
            if ti:
                if args.get("output_format") == "text":
                    return R(response=ti)
                else:
                    instance = task.TaskInstance(ti)
                    if args.get("output_format") == "json":
                        return R(response=instance.__dict__)
                    else:
                        return R(response=instance.AsXML())

        # uh oh, something went wrong but we don't know what.
        return R(err_code=R.Codes.GetError, err_detail="Unable to run Task [%s%s].  Check the log for details." % (args["task"], " %s" % (ver) if ver else ""))
        
    def stop_task(self, args):
        """Stops a running Task Instance.

Required Arguments: 

* `instance` - The Task Instance identifier.

Returns: Nothing if successful, error messages on failure.
"""
        # this is a developer function
        if not api._DEVELOPER:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Developers or Administrators can perform this function.")
        
        required_params = ["instance"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        ti = task.TaskInstance(args["instance"])

        if not api.is_object_allowed(ti.task_id, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Task.")
            
        ti.Stop()
        return R(response="Instance [%s] successfully stopped." % args["instance"])
            
    def delete_task(self, args):
        """Deletes all versions of a Task.

Required Arguments: 

* `task` - Either the Task ID or Name.

Optional Arguments:

* `force_delete` - Delete the Task, even if there are historical rows and references.  (Valid values: 1, yes, true)

Returns: Nothing if successful, error messages on failure.
"""
        # this is a admin function
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")
        
        required_params = ["task"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        force = catocommon.is_true(args.get("force_delete"))

        obj = task.Task()
        obj.FromNameVersion(name=args["task"], include_code=False)

        if not api.is_object_allowed(obj.ID, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Task.")
            
        task.Tasks.Delete(["'%s'" % obj.ID], force)
        
        catocommon.write_delete_log(api._USER_ID, catocommon.CatoObjectTypes.Task, obj.ID, obj.Name, "Deleted via API.")
        return R(response="[%s] successfully deleted." % obj.Name)
            
    def list_tasks(self, args):        
        """Lists all Tasks.

> Only 'Default' versions are shown.

Optional Arguments:
 
* `filter` - will filter a value match in Task Name, Code or Description.  (Multiple filter arguments can be provided, delimited by spaces.)
* `show_all_versions` - if provided, will display all versions. ('False' if omitted.)

Returns: A list of [Task Objects](restapi/api-response-objects.html#Task){:target="_blank"}.

> The Task Objects returned to this function are streamlined - they do not contain all the properties available in the `get_task` endpoint.
"""
        fltr = args["filter"] if "filter" in args else ""
        showall = True if "show_all_versions" in args else False

        obj = task.Tasks(sFilter=fltr, show_all_versions=showall)
        obj.rows = obj.rows if api._ADMIN else api.filter_set_by_tag(obj.rows)
        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())


    def get_task_instances(self, args):
        """Gets a list of Task Instances.

Optional Arguments:

* `filter` - A filter to limit the results.
* `status` - A comma separated list of statuses to filter the results.
* `from` - a date string to set as the "from" marker. (mm/dd/yyyy format)
* `to` - a date string to set as the "to" marker. (mm/dd/yyyy format)
* `records` - a maximum number of results to get.
    
Returns: A list of [Task Instance Objects](restapi/api-response-objects.html#TaskInstance){:target="_blank"}.
"""
        fltr = args["filter"] if "filter" in args else ""
        frm = args["from"] if "from" in args else ""
        to = args["to"] if "to" in args else ""
        records = args["records"] if "records" in args else ""
        status = args["status"] if "status" in args else ""
        status = "" if status.lower() == "all" else status
        
        obj = task.TaskInstances(sFilter=fltr,
                                 sStatus=status,
                                 sFrom=frm,
                                 sTo=to,
                                 sRecords=records)

        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())
            
    def get_task(self, args):        
        """Gets a Task object.

Required Arguments: 

* `task` - Value can be either a Task ID or Name.

Optional Arguments:

* `version` - A specific version.  ('Default' if omitted.)
* `include_code` - Whether to include Codeblocks and Steps.  (Only included if 'output_format' is 'json' or 'xml'.  'False' if omitted.)
    
Returns: A [Task Object](restapi/api-response-objects.html#Task){:target="_blank"}.
"""
        # define the required parameters for this call
        required_params = ["task"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        ver = args["version"] if "version" in args else ""
        ic = True if "include_code" in args else False

        obj = task.Task()
        obj.FromNameVersion(args["task"], ver)
        
        if not api.is_object_allowed(obj.ID, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Task.")
            
        if args.get("output_format") == "json":
            return R(response=obj.AsJSON(include_code=ic))
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML(include_code=ic))
            
    def describe_task_parameters(self, args):        
        """Describes the Parameters for a Task.

Required Arguments: 

* `task` - Value can be either a Task ID, Code or Name.

Optional Arguments:

* `version` - A specific version.  ('Default' if omitted.)
    
Returns: A help document describing the Task Parameters.
"""
        # define the required parameters for this call
        required_params = ["task"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        ver = args["version"] if "version" in args else ""

        obj = task.Task()
        obj.FromNameVersion(args["task"], ver)

        if not api.is_object_allowed(obj.ID, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Task.")
            
        if obj.ParameterXDoc:
            """
                Describe the parameters for the Task in a text (help) format.
                Used for the command line tools and API.
                The UI has it's own more complex logic for presentation and interaction.
            """
            out = []
            
            xParams = obj.ParameterXDoc.findall("parameter")
            out.append("Number of Parameters: " + str(len(xParams)))
            for xParam in xParams:
                out.append("Parameter: %s" % xParam.findtext("name"))
                if xParam.findtext("desc"):
                    out.append("%s" % xParam.findtext("desc"))
                if xParam.get("required", ""):
                    out.append("\tRequired: %s" % xParam.get("required", ""))
                if xParam.get("constraint", ""):
                    out.append("\tConstraint: %s" % xParam.get("constraint", ""))
                if xParam.get("constraint_msg", ""):
                    out.append("\tConstraint Message: %s" % xParam.get("constraint_msg", ""))
                if xParam.get("minlength", ""):
                    out.append("\tMin Length: %s" % xParam.get("minlength", ""))
                if xParam.get("maxlength", ""):
                    out.append("\tMax Length: %s" % xParam.get("maxlength", ""))
                if xParam.get("minvalue", ""):
                    out.append("\tMin Value: %s" % xParam.get("minvalue", ""))
                if xParam.get("maxvalue", ""):
                    out.append("\tMax Value: %s" % xParam.get("maxvalue", ""))
                
                # analyze the value definitions
                xValues = xParam.find("values")
                if xValues is not None:
                    if xValues.get("present_as", ""):
                        if xValues.get("present_as", "") == "list":
                            # if it's a list type, say so
                            out.append("\tType: List (Can have more than one value.)")
                        elif xValues.get("present_as", "") == "dropdown":
                            # if it's a dropdown type, show the allowed values.
                            xValue = xValues.findall("value")
                            if xValue is not None:
                                out.append("\tAllowed Values:")
                                for val in xValue:
                                    out.append("\t\t%s" % val.text)
                                    
            return R(response="\n".join(out))
        else:
            return R(response="Task has no parameters defined.")
            
    def get_task_plans(self, args):        
        """Gets a list of the queued execution plans for a Task.

Required Arguments: 

* `task` - Value can be either a Task ID or Name.

Optional Arguments:

* `version` - A specific version.  ('Default' if omitted.)
    
Returns: A list of [Execution Plan Objects](restapi/api-response-objects.html#ExecutionPlan){:target="_blank"}.
"""
        # define the required parameters for this call
        required_params = ["task"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        ver = args["version"] if "version" in args else ""

        obj = task.Task()
        obj.FromNameVersion(args["task"], ver)
        
        if not api.is_object_allowed(obj.ID, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Task.")
        
        if args.get("output_format") == "json":
            return R(response=obj.PlansAsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.PlansAsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.PlansAsXML())
            
    def get_task_schedules(self, args):        
        """Gets a list of Schedule definitions for a Task.

Required Arguments: 

* `task` - Value can be either a Task ID or Name.

Optional Arguments:

* `version` - A specific version.  ('Default' if omitted.)
    
Returns: A list of [Task Schedule Objects](restapi/api-response-objects.html#TaskSchedule){:target="_blank"}.

* Text results do not include timing details.
* JSON results include Schedule definitions suitable for use in the 'schedule_task' function.
"""
        # define the required parameters for this call
        required_params = ["task"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        ver = args["version"] if "version" in args else ""

        obj = task.Task()
        obj.FromNameVersion(args["task"], ver)
        
        if not api.is_object_allowed(obj.ID, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Task.")
        
        if args.get("output_format") == "json":
            return R(response=obj.SchedulesAsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.SchedulesAsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.SchedulesAsXML())
            
    def get_task_parameters(self, args):        
        """Gets a Parameters template for a Task.

Required Arguments: 

* `task` - Value can be either a Task ID, Code or Name.

Optional Arguments:

* `version` - A specific version.  ('Default' if omitted.)
* `basic` - in JSON mode, if provided, will omit descriptive details.
    
Returns: An XML template defining the Parameters for a Task.

> This function is not affected by the output_format option.  The Response is always an XML document.

"""
        # define the required parameters for this call
        required_params = ["task"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        ver = args["version"] if "version" in args else ""
        basic = args["basic"] if "basic" in args else None

        obj = task.Task()
        obj.FromNameVersion(args["task"], ver)

        if not api.is_object_allowed(obj.ID, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Task.")
            
        if obj.ParameterXDoc:
            """
                Build a template for a parameter xml document, suitable for editing and submission.
                Used for the command line tools and API.
                The UI has it's own more complex logic for presentation and interaction.
            """
            
            # provide XML params if requested... the default is json.
            if args.get("output_format") == "xml":
                # the xml document is *almost* suitable for this purpose.
                # we just wanna strip out the presentation metadata
                xdoc = obj.ParameterXDoc
                # all we need to do is remove the additional dropdown values.
                # they're "allowed values", NOT an array.
                xParamValues = xdoc.findall("parameter/values")
                if xParamValues is not None:
                    for xValues in xParamValues: 
                        if xValues.get("present_as", ""):
                            if xValues.get("present_as", "") == "dropdown":
                                # if it's a dropdown type, show the allowed values.
                                xValue = xValues.findall("value")
                                if xValue is not None:
                                    if len(xValue) > 1:
                                        for val in xValue[1:]:
                                            xValues.remove(val)
                                        
                xmlstr = catocommon.pretty_print_xml(catocommon.ET.tostring(xdoc))
                                        
                return R(response=xmlstr)
            else:
                # the deployment module has a function that will convert this xml to suitable json
                pxml = catocommon.ET.tostring(obj.ParameterXDoc)
                lst = catocommon.paramxml2json(pxml, basic)
                return R(response=catocommon.ObjectOutput.AsJSON(lst))
                
        else:
            return R(err_code=R.Codes.GetError, err_detail="Task has no parameters defined.")

    def export_task(self, args):
        """Create a backup file for a single Task.

> The behavior of this command is different depending on the output_format.

* If 'json', it will return a JSON LIST of individual Task XML documents.
* If 'xml' (default) OR 'text', it will return a single XML document of Tasks.

Required Arguments: 

* `task` - Value can be either a Task ID, Code or Name.

Optional Arguments:

* `version`` - A specific version.  ('Default' if omitted.)
* `include_refs`` - If true, will analyze each task and include any referenced Tasks.
    
Returns: A collection of Task backup objects.
"""
        
        # define the required parameters for this call
        required_params = ["task"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = task.Task()
        obj.FromNameVersion(args["task"], args.get("version"))

        if not api.is_object_allowed(obj.ID, catocommon.CatoObjectTypes.Task):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Task.")
            
        tids = [obj.ID]
        
        docs = task.Tasks.Export(tids, args.get("include_refs"), args.get("output_format"))

        if args.get("output_format") == "json":
            return R(response="[%s]" % "".join(docs))
        else:
            return R(response="<tasks>%s</tasks>" % "".join(docs))
            
    def schedule_tasks(self, args):
        """Schedules one or more Tasks.

Required Arguments: 

* `tasks` - a JSON document containing a list of Tasks and schedule details.
    
Schedule definition format:

> All lists are _zero based_ integers.

> The [Task Schedule Object](restapi/api-response-objects.html#TaskSchedule){:target="_blank"} response from the `get_task_schedules` command in JSON format
 can provide schedule definition examples for this command.

    [
        { 
            "Task" : *task name*,
            "Version" : *optional*,
            "Months": "*" or [list of months],
            "DaysOrWeekdays": "Days" = days of the month, "Weekdays" = days of the week (default),
            "Days": "*" or [list of days],
            "Hours": "*" or [list of hours],
            "Minutes": "*" or [list of minutes]
        },
        {
            ...
        }
    ]

Returns: Nothing if successful, error messages on failure.
"""
        # this is a developer function
        if not api._DEVELOPER:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Developers or Administrators can perform this function.")
        
        required_params = ["tasks"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        # so, we'll loop through each task and try to schedule it
        # keeping track of errors, etc.
        tasks = []
        if args.get("tasks"):
            try:
                tasks = json.loads(args["tasks"])
            except Exception as ex:
                return R(err_code=R.Codes.Exception, err_detail="Schedule definition is not valid JSON. %s" % ex)

        out = []
        for t in tasks:
            if not t.get("Task"):
                return R(err_code=R.Codes.CreateError, err_detail="Each item in the schedule definition requires a 'task'.")
                
            obj = task.Task()
            obj.FromNameVersion(t["Task"], t.get("Version"), False)
    
            if not api.is_object_allowed(obj.ID, catocommon.CatoObjectTypes.Task):
                return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Task.")
                
            sched_def = { 
                         "Months": t.get("Months"),
                         "Days": t.get("Days"),
                         "Hours": t.get("Hours"),
                         "Minutes": t.get("Minutes"),
                         "DaysOrWeekdays": t.get("DaysOrWeekdays")
                         }
    
            # parameters coming from the command line are defined as json OR xml, we need xml
            parameters = t.get("Parameters")
            pxml = ""
            if parameters:
                # this will convert json OR xml params into the xml format we need
                pxml = catocommon.params2xml(parameters)

            obj.RunRepeatedly(sched_def, pxml, t.get("Debug"), t.get("AccountID"))
            out.append("[%s] successfully scheduled." % obj.Name)
            
        return R(response="\n".join(out))

    def delete_schedule(self, args):
        """Deletes a Task Schedule and all queued execution Plans.

Required Arguments: 

* `schedule_id` - The UUID of the Schedule to delete.

Returns: Nothing if successful, error messages on failure.
"""
        # this is a admin function
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")
        
        required_params = ["schedule_id"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        task.Task.DeleteSchedules(args["schedule_id"])

        catocommon.write_delete_log(api._USER_ID, catocommon.CatoObjectTypes.Task, "", "", "Schedule [%s] deleted via API." % (args["schedule_id"]))
        
        return R(response="Schedule [%s] successfully deleted." % args["schedule_id"])
            
    def delete_plan(self, args):
        """Deletes a specific queued execution Plan.

Required Arguments: 

* `plan_id` - The integer ID of the Plan to delete.

Returns: Nothing if successful, error messages on failure.
"""
        # this is a admin function
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")
        
        required_params = ["plan_id"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        task.Task.DeletePlan(args["plan_id"])

        catocommon.write_delete_log(api._USER_ID, catocommon.CatoObjectTypes.Task, "", "", "Plan [%s] deleted via API." % (args["plan_id"]))
        
        return R(response="Plan [%s] successfully deleted." % args["plan_id"])
