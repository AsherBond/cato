
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

import traceback

from catoapi import api
from catoapi.api import response as R
from catotask import task
from catoecosystem import ecosystem
from catocloud import cloud
from catocommon import catocommon
try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

class taskMethods:
    """"""

    def create_task(self, args):        
        """
        Create a new Task.
        
        Required Arguments: 
            name - a name for the new Task.
            
        Optional Arguments:
            code - a Task code.
            desc - a Task description.
        
        Returns: A Task object.
        """
        try:
            # define the required parameters for this call
            required_params = ["name"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp

            code = args["code"] if args.has_key("code") else ""
            desc = args["desc"] if args.has_key("desc") else ""

            t = task.Task()
            t.FromArgs(args["name"], code, desc)

            if not t.Name:
                return R(err_code=R.Codes.Exception, err_detail="Unable to create Task.")

            result, msg = t.DBSave()

            if result:
                catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.Task, t.ID, t.Name, "Task created.")
                if args["output_format"] == "json":
                    return R(response=t.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=t.AsText(args["output_delimiter"]))
                else:
                    return R(response=t.AsXML())
            else:
                return R(err_code=R.Codes.CreateError, err_detail=msg)
            
        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)

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

                if args["output_format"] == "json":
                    return R(response='{"task_status":"%s"}' % obj.task_status)
                elif args["output_format"] == "xml":
                    return R(response='<task_status>%s</task_status>' % obj.task_status)
                else:
                    return R(response=obj.task_status)
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Status for Task Instance [%s]." % args["instance"])
            
        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)

    def get_task_instance(self, args):
        """
        Gets the details of a Task Instance.
        
        Required Arguments: instance
            The Task Instance identifier.

        Returns: A Task Instance object.
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

                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText(args["output_delimiter"]))
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Task Instance [%s]." % args["instance"])
            
        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)

    def resubmit_task_instance(self, args):
        """
        Resubmits a completed,errored or cancelled Task Instance.
        
        Required Arguments: instance
            The Task Instance identifier.

        Returns: Returns: Nothing if successful, error messages on failure.
        """
        try:
            # this is a developer function
            if not args["_developer"]:
                return R(err_code=R.Codes.Forbidden)
            
            required_params = ["instance"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp

            obj = task.TaskInstance(args["instance"])
            if obj:
                if obj.Error:
                    return R(err_code=R.Codes.GetError, err_detail=obj.Error)

#                if deployment_id and sequence_instance:
#                    msg = "Task [%s] Instance [%s] resubmitted by [%s]." % (ti.task_name_label, ti.task_instance, username)
#                    deployment.WriteDeploymentLog(msg, dep_id=deployment_id, seq_inst=sequence_instance)
    
                result, err = obj.Resubmit(args["_user_id"])
                if result:
                    return R(response="Instance [%s] successfully resubmitted." % args["instance"])
                else:
                    return R(err_code=R.Codes.StartFailure, err_detail=err)
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Task Instance [%s]." % args["instance"])
            
        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)

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
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText(args["output_delimiter"]))
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Run Log for Task Instance [%s]." % args["instance"])
            
        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)

    def run_task(self, args):
        """
        Runs a Cato Task.
        
        Required Arguments: 
            task - Either the Task ID, Code or Name.
            version - The Task Version.  (Unnecessary if 'task' is an ID.)
            
        Optional Arguments:
            log_level - an integer (0-4) where 0 is none, 2 is normal and 4 is verbose.  Default is 2.
            ecosystem - the ID or Name of an Ecosystem.  Certain Task commands are scoped to this Ecosystem.
            account - the ID or Name of a Cloud Account.  Certain Task commands require a Cloud Account.
            parameter_xml - An XML document defining parameters for the Task.

        Returns: A JSON object, the Task Instance.
            If 'output_format' is set to 'text', returns only a Task Instance ID.
        """
        try:
            # this is a developer function
            if not args["_developer"]:
                return R(err_code=R.Codes.Forbidden)
            
            required_params = ["task"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp
            
            ver = args["version"] if args.has_key("version") else ""

            # find the task
            obj = task.Task()
            obj.FromNameVersion(args["task"], ver)
            if obj.ID:
                task_id = obj.ID
                debug = args["log_level"] if args.has_key("log_level") else "2"
                
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
                            if args["output_format"] == "json":
                                return R(response=instance.AsJSON())
                            elif args["output_format"] == "xml":
                                return R(response=instance.AsXML())

                # uh oh, something went wrong but we don't know what.
                return R(err_code=R.Codes.GetError, err_detail="Unable to run Task [%s %s].  Check the log for details." % (args["task"], ver))
                
            else:
                identifier ="%s/%s" % (args["task"], ver) if ver else args["task"]
                return R(err_code=R.Codes.GetError, err_detail="Unable to find Task for ID or Name/Version [%s]." % identifier)

        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)

    def stop_task(self, args):
        """
        Stops a running Task Instance.
        
        Required Arguments: instance
            The Task Instance identifier.

        Returns: Nothing if successful, error messages on failure.
        """
        try:
            # this is a developer function
            if not args["_developer"]:
                return R(err_code=R.Codes.Forbidden)
            
            required_params = ["instance"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp


            ti = task.TaskInstance(args["instance"])
            if ti:
                ti.Stop()
                return R(response="Instance [%s] successfully stopped." % args["instance"])
            else:
                return R(err_code=R.Codes.StopFailure, err_detail="Unable to stop Task Instance [%s]." % args["instance"])
            
        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)

    def list_tasks(self, args):        
        """
        Lists all Tasks.
            Only 'Default' versions are shown.
        
        Optional Arguments: 
            filter - will filter a value match in Task Name, Code or Description.
            show_all_versions - if provided, will display all versions. ('False' if omitted.)
        
        Returns: An array of all Tasks with basic attributes.
        """
        try:
            fltr = args["filter"] if args.has_key("filter") else ""
            showall = True if args.has_key("show_all_versions") else False

            obj = task.Tasks(sFilter=fltr, show_all_versions=showall)
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText(args["output_delimiter"]))
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.ListError, err_detail="Unable to list Tasks.")
            
        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)

    def get_task_instances(self, args):
        """
        Gets a list of Task Instances.
        
        Optional Arguments:
            filter - A filter to limit the results.
            status - A comma separated list of statuses to filter the results.
            from - a date string to set as the "from" marker. (mm/dd/yyyy format)
            to - a date string to set as the "to" marker. (mm/dd/yyyy format)
            records - a maximum number of results to get.
            
        Returns: A list of Task Instances.
        """
        try:
            fltr = args["filter"] if args.has_key("filter") else ""
            status = args["status"] if args.has_key("status") else ""
            frm = args["from"] if args.has_key("from") else ""
            to = args["to"] if args.has_key("to") else ""
            records = args["records"] if args.has_key("records") else ""

            obj = task.TaskInstances(sFilter=fltr,
                                     sStatus=status,
                                     sFrom=frm,
                                     sTo=to,
                                     sRecords=records)
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText(args["output_delimiter"]))
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Task Instances.")
            
        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)

    def get_task(self, args):        
        """
        Gets a Task object.
        
        Required Arguments: 
            task - Value can be either a Task ID, Code or Name.
        
        Optional Arguments:
            version - A specific version.  ('Default' if omitted.)
            include_code - Whether to include Codeblocks and Steps.  ('False' if omitted.)
            
        Returns: A Task object.
        """
        try:
            # define the required parameters for this call
            required_params = ["task"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp

            ver = args["version"] if args.has_key("version") else ""
            ic = True if args.has_key("include_code") else False

            obj = task.Task()
            obj.FromNameVersion(args["task"], ver)
            if obj.ID:
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON(include_code=ic))
                elif args["output_format"] == "text":
                    return R(response=obj.AsText(args["output_delimiter"]))
                else:
                    return R(response=obj.AsXML(include_code=ic))
            else:
                identifier ="%s/%s" % (args["task"], ver) if ver else args["task"]
                return R(err_code=R.Codes.GetError, err_detail="Unable to find Task for ID or Name/Version [%s]." % identifier)
            
        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)

    def describe_task_parameters(self, args):        
        """
        Describes the Parameters for a Task.
        
        Required Arguments: 
            task - Value can be either a Task ID, Code or Name.
        
        Optional Arguments:
            version - A specific version.  ('Default' if omitted.)
            
        Returns: A help document describing the Task Parameters.
        """
        try:
            # define the required parameters for this call
            required_params = ["task"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp

            ver = args["version"] if args.has_key("version") else ""

            obj = task.Task()
            obj.FromNameVersion(args["task"], ver)
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
                identifier ="%s/%s" % (args["task"], ver) if ver else args["task"]
                return R(err_code=R.Codes.GetError, err_detail="Unable to find Task for ID or Name/Version [%s]." % identifier)
            
        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)

    def get_task_parameters_template(self, args):        
        """
        Gets a Parameters template for a Task.
        
        Required Arguments: 
            task - Value can be either a Task ID, Code or Name.
        
        Optional Arguments:
            version - A specific version.  ('Default' if omitted.)
            
        Returns: An XML template defining the Parameters for a Task.
            (Used for calling run_task or run_action.)
        """
        try:
            # define the required parameters for this call
            required_params = ["task"]
            has_required, resp = api.check_required_params(required_params, args)
            if not has_required:
                return resp

            ver = args["version"] if args.has_key("version") else ""

            obj = task.Task()
            obj.FromNameVersion(args["task"], ver)
            if obj.ID:
                if obj.ParameterXDoc:
                    """
                        Build a template for a parameter xml document, suitable for editing and submission.
                        Used for the command line tools and API.
                        The UI has it's own more complex logic for presentation and interaction.
                    """
                    
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
                                            
                    xmlstr = catocommon.pretty_print_xml(ET.tostring(xdoc))
                                            
                    return R(response=xmlstr)
                else:
                    return R(err_code=R.Codes.GetError, err_detail="Task has no parameters defined.")
            else:
                identifier ="%s/%s" % (args["task"], ver) if ver else args["task"]
                return R(err_code=R.Codes.GetError, err_detail="Unable to find Task for ID or Name/Version [%s]." % identifier)
            
        except Exception:
            logger.error(traceback.format_exc())
            return R(err_code=R.Codes.Exception)
