
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
Deployment endpoint methods.
"""

import os
import sys
import json
import traceback


# These API endpoints require Maestro
# we look at the MAESTRO_HOME environment variable and load the libs from that path
if not os.environ.has_key("MAESTRO_HOME") or not os.environ["MAESTRO_HOME"]:
    raise Exception("Maestro is required for API methods in this module.  MAESTRO_HOME environment variable not set.")

MAESTRO_HOME = os.environ["MAESTRO_HOME"]
sys.path.insert(0, os.path.join(MAESTRO_HOME, "lib"))


from catolog import catolog
logger = catolog.get_logger(__name__)

from catoapi import api
from catoapi.api import response as R
from catocommon import catocommon
from catodeployment import deployment

class depMethods:
    """These are methods for Deployments, Services and other related items."""

    def list_deployments(self, args):        
        """
        Lists all Deployments.
        
        Optional Arguments: 
            filter - will filter a value match on Deployment Name, Status or Owner.
        
        Returns: An array of all Deployments with basic attributes.
        """
        fltr = args.get("filter", "")
        show_archived = args.get("show_archived", "")
        
        obj = deployment.Deployments(sFilter=fltr, sShowArchived=catocommon.is_true(show_archived))
        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args["output_delimiter"]))
        else:
            return R(response=obj.AsXML())
        
#    def import_deployment(self, args):        
#        """
#        Create a new Deployment from a template file.
#        
#        Required Arguments: 
#            name - the name for the new Deployment being created.
#            template - a JSON formatted Deployment template.
#            
#        Returns: A Deployment object.
#        """
#        try:
#            # define the required parameters for this call
#            required_params = ["name", "template"]
#            has_required, resp = api.check_required_params(required_params, args)
#            if not has_required:
#                return resp
#
#            obj, msg = deployment.Deployment.FromJSON(args["name"], args["template"])
#            if obj:
#                catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.Deployment, obj.ID, obj.Name, "Deployment created.")
#                if args["output_format"] == "json":
#                    return R(response=obj.AsJSON())
#                elif args["output_format"] == "text":
#                    return R(response=obj.AsText(args["output_delimiter"]))
#                else:
#                    return R(response=obj.AsXML())
#            else:
#                return R(err_code=R.Codes.CreateError, err_detail=msg)
#            
#        except Exception:
#            return R(err_code=R.Codes.Exception)

    def create_deployment(self, args):        
        """
        Create a new Deployment.
        
        Required Arguments: 
            name - a name for the new Deployment.
            template - the name of a defined Deployment Template.
            version - the Template version
            
        Optional Arguments:
            description - a description for the Deployment.
            
        Returns: A Deployment object.
        """

        # not yet implemented
#                Optional Arguments:
#            owner - the name or id of a Cato user to be the owner of this Deployment.
#        

        # define the required parameters for this call
        required_params = ["name", "template", "version"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        name = args["name"]
        template = args["template"]
        version = args["version"]
        
        # owner = args["owner"] if args.has_key("owner") else ""
        desc = args["desc"] if args.has_key("desc") else ""

        # two steps
        # 1) get the template 
        # 2) use it to create a new deployment

        # 1)
        t = deployment.DeploymentTemplate()
        t.FromNameVersion(template, version)
        
        if not t.Text:
            msg = "Deployment Template [%s/%s] has no JSON document." % (template, version)
            return R(err_code=R.Codes.CreateError, err_detail=msg)
            
        # 2)
        obj, msg = deployment.Deployment.FromJSON(name, t.Text, desc)
        if obj:
            catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.Deployment, obj.ID, obj.Name, "Deployment created.")
            if args["output_format"] == "json":
                return R(response=obj.AsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.AsText(args["output_delimiter"]))
            else:
                return R(response=obj.AsXML())
        else:
            return R(err_code=R.Codes.CreateError, err_detail=msg)


    def delete_deployment(self, args):        
        """
        Delete an existing Deployment Step.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
        
        Returns: Nothing if successful, or an error message.
        """
        # this is an admin function
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)
        
        # define the required parameters for this call
        required_params = ["deployment"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        success, msg = obj.DBDelete()
        if success:
            return R(response="Successfully deleted the Deployment.")
        else:
            return R(err_code=R.Codes.DeleteError, err_detail=msg)
            

    def describe_deployment(self, args):        
        """
        Gets a complete Deployment object, including all Services and Steps.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
        
        Returns: A complete Deployment object.
        """
        # define the required parameters for this call
        required_params = ["deployment"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        # kindof a pain... we gotta get the services and steps, then render them properly below
        if args["output_format"] == "json":
            obj.Services = json.loads(obj.ServicesAsJSON())
            obj.Sequences = json.loads(obj.SequencesAsJSON())
            
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            out = []
            out.append("DEPLOYMENT")
            out.append(obj.AsText(args["output_delimiter"]))
            out.append("\nSERVICES")
            out.append(obj.ServicesAsText())
            out.append("\nSEQUENCES")
            out.append(obj.SequencesAsText())
            
            return R(response="\n".join(out))
        else:
            return R(response=obj.AsXML())
            

    def get_deployment(self, args):        
        """
        Gets a Deployment object.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
        
        Returns: A Deployment object.
        """
        # define the required parameters for this call
        required_params = ["deployment"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args["output_delimiter"]))
        else:
            return R(response=obj.AsXML())
            

    def get_deployment_document(self, args):        
        """
        Gets the Datastore document for a Deployment.
        
        Required Arguments: 
            deployment - Value can be either an Deployment ID or Name.
        
        Returns: A Deployment Datastore Document.
        """
        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        # the data document is in json format, so "text" mode returns json
        # but "xml" format will be translated.
        if args["output_format"] in ["json", "text"]:
            return R(response=catocommon.ObjectOutput.AsJSON(obj.Datastore.doc))
        else:
            xml = catocommon.ObjectOutput.AsXML(obj.Datastore.doc, "deployment_data")
            return R(response=xml)
            
        
    def get_deployment_services(self, args):        
        """
        Gets the Services for a Deployment.
        
        Required Arguments: 
            deployment - Value can be either an Deployment ID or Name.
        
        Optional Arguments: 
            filter - will filter a value match on Service Name.
        
        Returns: All Deployment Services.
        """
        fltr = args["filter"] if args.has_key("filter") else ""
        
        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        if args["output_format"] == "json":
            return R(response=obj.ServicesAsJSON(fltr))
        elif args["output_format"] == "text":
            return R(response=obj.ServicesAsText(fltr, args["output_delimiter"]))
        else:
            return R(response=obj.ServicesAsXML(fltr))
            
        
    def get_service_instances(self, args):        
        """
        Gets Service Instances from an Deployment Service.
        
        Required Arguments: 
            deployment - Value can be either an Deployment ID or Name.
            service - can be either a Service ID or Name.
        
        Returns: A list of Service Instances.
        """
        # define the required parameters for this call
        required_params = ["deployment", "service"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        service = obj.GetService(args["service"])
        if args["output_format"] == "json":
            return R(response=service.InstancesAsJSON())
        elif args["output_format"] == "text":
            return R(response=service.InstancesAsText())
        else:
            return R(response=service.InstancesAsXML())

        
    def create_deployment_service(self, args):        
        """
        Create a new Deployment Service.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
            name - a name for the new Service.
            
        Optional Arguments:
            description - the description of the Service.
        
        Returns: A Deployment Service object.
        """
        # this is an admin function
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)
        
        # define the required parameters for this call
        required_params = ["deployment", "name"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        desc = args["desc"] if args.has_key("desc") else ""

        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        service, msg = deployment.DeploymentService.DBCreateNew(deployment=obj, name=args["name"], desc=desc)
        if service:
            catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.DeploymentService, obj.ID, service.Name, "Deployment Service created.")
            # call the other method that returns the list.
            return self.get_deployment_services(args)
        else:
            return R(err_code=R.Codes.CreateError, err_detail=msg)
            

    def get_deployment_sequence(self, args):        
        """
        Gets a specific Sequence from a Deployment.
        
        Required Arguments: 
            deployment - Value can be either an Deployment ID or Name.
            sequence - The name of a Sequence on this Deployment.
        
        
        Returns: A Deployment Sequence with Steps.
        """
        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        seq = deployment.DeploymentSequence(obj)
        seq.FromName(args["sequence"])
        if args["output_format"] == "json":
            return R(response=seq.AsJSON())
        elif args["output_format"] == "text":
            return R(response=seq.AsText(args["output_delimiter"]))
        else:
            return R(response=seq.AsXML())
            
        
    def get_deployment_sequences(self, args):        
        """
        Gets all Sequences from a Deployment.
        
        Required Arguments: 
            deployment - Value can be either an Deployment ID or Name.
        
        Optional Arguments: 
            filter - will filter a value match on Sequence Name.
        
        Returns: All Deployment Sequences.
        """
        fltr = args["filter"] if args.has_key("filter") else ""
        
        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        if args["output_format"] == "json":
            return R(response=obj.SequencesAsJSON(fltr))
        elif args["output_format"] == "text":
            return R(response=obj.SequencesAsText(fltr, args["output_delimiter"]))
        else:
            return R(response=obj.SequencesAsXML(fltr))
            
        
    def add_sequence_step(self, args):        
        """
        Add a new Deployment Sequence Step.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
            sequence - The name of a Sequence on this Deployment.
            
        Optional Arguments:
            before - Insert the new step before the specified existing step.
        
        Returns: The selected Sequence.
        """
        # this is an admin function
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)
        
        # define the required parameters for this call
        required_params = ["deployment", "sequence"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        before = args["before"] if args.has_key("before") else ""

        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        seq = deployment.DeploymentSequence(obj)
        seq.FromName(args["sequence"])
        step, msg = seq.AddStep(before)
        if step:
            # call the other method that returns the list.
            return self.get_deployment_sequence(args)
        else:
            return R(err_code=R.Codes.CreateError, err_detail=msg)
            

    def add_service_to_sequence_step(self, args):        
        """
        Add a Service to an existing Deployment Sequence Step.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
            sequence - The name of a Sequence on this Deployment.
            step - The Step number.
            service - can be either a Service ID or Name.
            initial - The 'initial state' for Instances on this Step.
            desired - The 'desired state' for Instances on this Step.
            
        Returns: The selected Sequence.
        """
        # this is an admin function
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)
        
        # define the required parameters for this call
        required_params = ["deployment", "sequence", "step", "service", "desired"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        initial = args["initial"] if args.has_key("initial") else ""

        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        seq = deployment.DeploymentSequence(obj)
        seq.FromName(args["sequence"])
        step, msg = seq.GetStep(args["step"])
        if step:
            success, msg = step.AddService(args["service"], args["desired"], initial)
            if success:
                # call the other method that returns the list.
                return self.get_deployment_sequence(args)
            else:
                return R(err_code=R.Codes.CreateError, err_detail=msg)
        else:
            return R(err_code=R.Codes.GetError, err_detail=msg)
            

    def remove_service_from_sequence_step(self, args):        
        """
        Remove a Service from a Deployment Sequence Step.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
            sequence - The name of a Sequence on this Deployment.
            step - The Step number.
            service - can be either a Service ID or Name.
        
        Returns: The selected Sequence.
        """
        # this is an admin function
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)
        
        # define the required parameters for this call
        required_params = ["deployment", "sequence", "step", "service"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        seq = deployment.DeploymentSequence(obj)
        seq.FromName(args["sequence"])
        step, msg = seq.GetStep(args["step"])
        if step:
            success, msg = step.RemoveService(args["service"])
            if success:
                # call the other method that returns the list.
                return self.get_deployment_sequence(args)
            else:
                return R(err_code=R.Codes.CreateError, err_detail=msg)
        else:
            return R(err_code=R.Codes.GetError, err_detail=msg)
            

    def delete_sequence_step(self, args):        
        """
        Delete an existing Deployment Step.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
            sequence - The name of a Sequence on this Deployment.
            step - The Step number.
        
        Returns: The selected Sequence.
        """
        # this is an admin function
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)
        
        # define the required parameters for this call
        required_params = ["deployment", "sequence", "step"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        seq = deployment.DeploymentSequence(obj)
        seq.FromName(args["sequence"])
        success, msg = seq.DeleteStep(args["step"])
        if success:
            # call the other method that returns the list.
            return self.get_deployment_sequence(args)
        else:
            return R(err_code=R.Codes.DeleteError, err_detail=msg)
            

    def run_action(self, args):        
        """
        Runs an Action on a Deployment, Service or Service Instance.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
            action - The name of an Action on this Deployment.
        
        Optional Arguments: 
            service - can be either a Service ID or Name.
            service_instance - can be either a Service Instance ID or Name.
            log_level - an integer (0-4) where 0 is none, 2 is normal and 4 is verbose.  Default is 2.
            params - a JSON document of properly formatted parameters for this sequence run.

        Returns: A Task Instance object.
        """
        required_params = ["deployment", "action"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        svc = args["service"] if args.has_key("service") else None
        inst = args["service_instance"] if args.has_key("service_instance") else None
        debug = args["log_level"] if args.has_key("log_level") else None
        params = args["params"] if args.has_key("params") else None
        if params:
            try:
                params = json.loads(params)
            except Exception as ex:
                return R(err_code=R.Codes.Exception, err_detail="Parameters template is not valid JSON. %s" % ex)

        # we're trying this with one command at the moment.
        dep = deployment.Deployment()
        dep.FromName(args["deployment"])
        action = deployment.Action()

        if svc:            
            service = dep.GetService(svc)
            if service:
                action.FromName(args["action"], dep.ID, service.ID)

                # if an 'inst' was passed, see if we can reconcile an existing instance
                if inst:
                    instance = dep.GetServiceInstance(inst)
                    inst = instance.InstanceID
                    
                # the action is for a service so check the scope.
                # kick back an error if it's scoped for 'instance only' or 'service only' but the args don't agree.
                # 0 = action is visible on both Services AND Instances - allow
                # 1 = action is Service Level only, doesn't appear on Instances
                # 2 = Instance level only, doesn't appear at the Service level
                if action.Scope == 1 and inst:
                    return R(err_code=R.Codes.StartFailure, 
                             err_detail="This Action is defined to run on Services only - do not supply a Service Instance.")
                if action.Scope == 2 and not inst:
                    return R(err_code=R.Codes.StartFailure, 
                             err_detail="This Action is defined to run on Service Instances only - please provide a Service Instance.")
        else:    
            action.FromName(args["action"], dep.ID)
        
        
        if not action.ID:
            return R(err_code=R.Codes.GetError, 
                     err_detail="Unable to get Action for [%s - %s]." % (args["action"], args["deployment"], svc))
            
        
        # the Run command will figure out what to run on... just give it the args we have
        taskinstances, msg = action.Run(user_id=args["_user_id"], instance_id=inst, parameters=params, log_level=debug)
        
        if not taskinstances:
            return R(err_code=R.Codes.StartFailure, err_detail=msg)
        

        if args["output_format"] == "json":
            return R(response=catocommon.ObjectOutput.IterableAsJSON(taskinstances))
        elif args["output_format"] == "text":
            return R(response=catocommon.ObjectOutput.IterableAsText(taskinstances, ["Instance"], args["output_delimiter"]))
        else:
            return R(response=catocommon.ObjectOutput.IterableAsXML(taskinstances, "instances", "instance"))
            

    def get_action_parameters(self, args):        
        """
        Gets the Parameters template for a specific Deployment/Service Action.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
            action - The name of an Action on this Deployment.
        
        Optional Arguments: 
            service - can be either a Service ID or Name.

        Returns: A Parameters document template.
        """
        required_params = ["deployment", "action"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        svc = args["service"] if args.has_key("service") else None
        basic = args["basic"] if args.has_key("basic") else None

        # we're trying this with one command at the moment.
        dep = deployment.Deployment()
        dep.FromName(args["deployment"])

        action = deployment.Action()

        if svc:            
            service = dep.GetService(svc)
            if service:
                action.FromName(args["action"], dep.ID, service.ID)
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Service for identifier [%s]." % svc)

        else:    
            action.FromName(args["action"], dep.ID)
        
        
        if not action.ID:
            return R(err_code=R.Codes.GetError, err_detail="Unable to get Action for [%s - %s]." % (args["action"], args["deployment"], svc))
            
        # now we have the action, what are it's task parameters?
        if action.TaskParameterXML:
            lst = catocommon.paramxml2json(action.TaskParameterXML, basic)      
            return R(response=catocommon.ObjectOutput.AsJSON(lst))              
        else:
            return R(err_code=R.Codes.GetError, err_detail="Action has no parameters defined.")
            
    
    def run_sequence(self, args):        
        """
        Starts a Sequence on a Deployment.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
            sequence - The name of a Sequence on this Deployment.
        
        Optional Arguments: 
            onerror - how to react if errors are encountered.  'halt' or 'pause'.  'pause' if omitted.
            params - a JSON document of properly formatted parameters for this sequence run.

        Returns: A Sequence Instance object.
        """
        # define the required parameters for this call
        required_params = ["deployment", "sequence"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        oe = args["onerror"] if args.has_key("onerror") else None
        pms = args["params"] if args.has_key("params") else None
        if pms:
            try:
                pms = json.loads(pms)
            except Exception as ex:
                return R(err_code=R.Codes.Exception, err_detail="Parameters template is not valid JSON. %s" % ex)

        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        si = obj.RunSequence(sequence_id=args["sequence"], on_error=oe, params=pms, user_id=args["_user_id"])
        instance = deployment.SequenceInstance(si)
        msg = "API: Sequence [%s] ran by [%s]." % (instance.Instance["SequenceName"], args["_user_full_name"])
        deployment.WriteDeploymentLog(msg, dep_id=obj.ID)

        if args["output_format"] == "json":
            return R(response=instance.AsJSON())
        elif args["output_format"] == "text":
            return R(response=instance.AsText(args["output_delimiter"]))
        else:
            return R(response=instance.AsXML())
            

    def get_sequence_instance(self, args):        
        """
        Gets a Sequence Instance.
        
        Required Arguments: 
            instance - the Sequence Instance ID.

        Returns: A Sequence Instance object.
        """
        # define the required parameters for this call
        required_params = ["instance"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        instance = deployment.SequenceInstance(args["instance"])
        if instance.Instance:
            if args["output_format"] == "json":
                return R(response=instance.AsJSON())
            elif args["output_format"] == "text":
                return R(response=instance.AsText(args["output_delimiter"]))
            else:
                return R(response=instance.AsXML())
        else:
            return R(err_code=R.Codes.StartFailure, err_detail="Sequence Instance not found using ID [%s]." % args["instance"])


    def get_sequence_instance_status(self, args):        
        """
        Gets a Sequence Instance Status.
        
        Required Arguments: 
            instance - the Sequence Instance ID.

        Returns: A Sequence Instance status.
        """
        # define the required parameters for this call
        required_params = ["instance"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        instance = deployment.SequenceInstance(args["instance"])
        if instance.Instance:
            if args["output_format"] == "json":
                return R(response='{"status":"%s"}' % instance.Instance["Status"])
            elif args["output_format"] == "xml":
                return R(response='<status>%s</status>' % instance.Instance["Status"])
            else:
                return R(response=instance.Instance["Status"])
        else:
            return R(err_code=R.Codes.StartFailure, err_detail="Sequence Instance not found using ID [%s]." % args["instance"])


    def stop_sequence(self, args):
        """
        Stops a running Sequence Instance.
        
        Required Arguments: instance
            The Sequence Instance identifier.

        Returns: Nothing if successful, error messages on failure.
        """
        required_params = ["instance"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        si = deployment.SequenceInstance(args["instance"])
        if si.Instance:
            msg = "API: Sequence [%s] Instance [%s] stopped by [%s]." % (si.Instance["SequenceName"], si.Instance["Instance"], args["_user_full_name"])
            deployment.WriteDeploymentLog(msg, dep_id=si.Instance["DeploymentID"], seq_inst=si.Instance["Instance"])

            result = si.Stop()
            if result:
                return R(response="Instance [%s] successfully stopped." % args["instance"])
            else:
                return R(err_code=R.Codes.StopFailure, err_detail="Unable to stop Sequence Instance [%s]." % args["instance"])
        else:
            return R(err_code=R.Codes.GetError, err_detail="Unable to get Sequence Instance [%s]." % args["instance"])
            

    def resubmit_sequence(self, args):
        """
        Resubmit a halted Sequence Instance.
        
        Required Arguments: instance
            The Sequence Instance identifier.

        Returns: Nothing if successful, error messages on failure.
        """
        required_params = ["instance"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        si = deployment.SequenceInstance(args["instance"])
        if si.Instance:
            msg = "API: Sequence [%s] Instance [%s] resubmitted by [%s]." % (si.Instance["SequenceName"], si.Instance["Instance"], args["_user_full_name"])
            deployment.WriteDeploymentLog(msg, dep_id=si.Instance["DeploymentID"], seq_inst=si.Instance["Instance"])

            result = si.Resubmit()
            if result:
                return R(response="Instance [%s] successfully resubmitted." % args["instance"])
            else:
                return R(err_code=R.Codes.StopFailure, err_detail="Unable to resubmit Sequence Instance [%s]." % args["instance"])
        else:
            return R(err_code=R.Codes.GetError, err_detail="Unable to get Sequence Instance [%s]." % args["instance"])
            

    def add_deployment_service_state(self, args):        
        """
        Add a new State to a Deployment Service.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
            service - can be either a Service ID or Name.
            state - a name for the new State.
            
        Optional Arguments:
            nextstate - the name of the State following this State.
            task - a Task ID, Code or Name.
            version - the Task Version.
                (Unnecessary if 'task' is an ID.)
        
        Returns: A list of Deployment Service States.
        """
        # this is an admin function
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)
        
        # define the required parameters for this call
        required_params = ["deployment", "service", "state"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        nextstate = args["nextstate"] if args.has_key("nextstate") else ""
        task = args["task"] if args.has_key("task") else ""
        ver = args["version"] if args.has_key("version") else ""

        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        service = obj.GetService(args["service"])
        state, msg = service.AddState(args["state"], nextstate, task, ver)
        if state:
            if args["output_format"] == "json":
                return R(response=service.StatesAsJSON())
            elif args["output_format"] == "text":
                return R(response=service.StatesAsText())
            else:
                return R(response=service.StatesAsXML())
        else:
            return R(err_code=R.Codes.CreateError, err_detail=msg)
            

    def delete_deployment_service_state(self, args):        
        """
        Deletes a Deployment Service State.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
            service - can be either a Service ID or Name.
            state - a name for the new State.
            
        Returns: A list of Deployment Service States.
        """
        # this is an admin function
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)
        
        # define the required parameters for this call
        required_params = ["deployment", "service", "state"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        service = obj.GetService(args["service"])
        state, msg = service.RemoveState(args["state"])
        if state:
            if args["output_format"] == "json":
                return R(response=service.StatesAsJSON())
            elif args["output_format"] == "text":
                return R(response=service.StatesAsText())
            else:
                return R(response=service.StatesAsXML())
        else:
            return R(err_code=R.Codes.CreateError, err_detail=msg)
            

    def get_deployment_service_states(self, args):        
        """
        Gets the States for a Deployment Service.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.
            service - can be either a Service ID or Name.
        
        Optional Arguments: 
            filter - will filter a value match on State or NextState.
        
        Returns: A list of Deployment Service States.
        """
        fltr = args["filter"] if args.has_key("filter") else ""
        
        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        service = obj.GetService(args["service"])
        if args["output_format"] == "json":
            return R(response=service.StatesAsJSON(fltr))
        elif args["output_format"] == "text":
            return R(response=service.StatesAsText(fltr, args["output_delimiter"]))
        else:
            return R(response=service.StatesAsXML(fltr))
            
        
    def get_sequence_instances(self, args):
        """
        Gets a list of Sequence Instances.
        
        Required Arguments: 
            deployment - can be either an Deployment ID or Name.

        Optional Arguments:
            filter - A filter to limit the results.
            status - A comma separated list of statuses to filter the results.
            from - a date string to set as the "from" marker. (mm/dd/yyyy format)
            to - a date string to set as the "to" marker. (mm/dd/yyyy format)
            records - a maximum number of results to get.
            
        Returns: A list of Sequence Instances.
        """
        fltr = args["filter"] if args.has_key("filter") else ""
        status = args["status"] if args.has_key("status") else ""
        frm = args["from"] if args.has_key("from") else ""
        to = args["to"] if args.has_key("to") else ""
        records = args["records"] if args.has_key("records") else ""

        obj = deployment.SequenceInstances(fltr=fltr,
                                 status=status,
                                 frm=frm,
                                 to=to,
                                 records=records)
        if obj:
            if args["output_format"] == "json":
                return R(response=obj.AsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.AsText(args["output_delimiter"]))
            else:
                return R(response=obj.AsXML())
        else:
            return R(err_code=R.Codes.GetError, err_detail="Unable to get Sequence Instances.")
            

    def get_deployment_log(self, args):
        """
        Gets a Deployment log.
        
        Required Arguments:
            deployment - can be either an Deployment ID or Name.
            
        Optional Arguments:
            filter - A filter to limit the results.
            from - a date string to set as the "from" marker. (mm/dd/yyyy format)
            to - a date string to set as the "to" marker. (mm/dd/yyyy format)
            records - a maximum number of results to get.

        Returns: A JSON array of log entries.
        """
        # define the required parameters for this call
        required_params = ["deployment"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        # a little different that other functions that return a rowset
        # in this one the filters are sent in a 'criteria' dictionary
        criteria = {}
        criteria["_filter"] = args["filter"] if args.has_key("filter") else ""
        criteria["_from"] = args["from"] if args.has_key("from") else ""
        criteria["_to"] = args["to"] if args.has_key("to") else ""
        criteria["num_records"] = args["records"] if args.has_key("records") else ""
        
        results = obj.GetLog(criteria)
        if results:
            if args["output_format"] == "json":
                return R(response=catocommon.ObjectOutput.IterableAsJSON(results))
            elif args["output_format"] == "text":
                return R(response=catocommon.ObjectOutput.IterableAsText(results, ["log_dt", "log_msg"], args["output_delimiter"]))
            else:
                return R(response=catocommon.ObjectOutput.IterableAsXML(results, "log", "item"))
        else:
            return R(err_code=R.Codes.GetError, err_detail="Error retrieving Deployment Log.")
            

    def get_sequence_parameters(self, args):
        """
        Gets the parameters template for a Sequence.
        
        Required Arguments: 
            deployment - Value can be either an Deployment ID or Name.
            sequence - The name of a Sequence on this Deployment.
        
        Optional Arguments:
            basic - if 'true' the result will contain no extra names, default values or descriptive details.
            
        Returns: A JSON parameters template.
        """
        # define the required parameters for this call
        required_params = ["deployment", "sequence"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        basic = args["basic"] if args.has_key("basic") else None

        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        seq = deployment.DeploymentSequence(obj)
        seq.FromName(args["sequence"])
        t = seq.GetParametersTemplate(basic)
        if t:
            return R(response=t)
        else:
            return R(response="{}")
            

    def list_deployment_templates(self, args):        
        """
        Lists all Deployment Templates.
        
        Optional Arguments: 
            filter - will filter a value match on Template Name, Version or Description.
        
        Returns: An array of all Deployment Templates.
        """
        fltr = args.get("filter", "")
        
        obj = deployment.DeploymentTemplates(sFilter=fltr)
        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args["output_delimiter"]))
        else:
            return R(response=obj.AsXML())
        
    def copy_deployment_template(self, args):        
        """
        Copies a Deployment Template.
        
        Required Arguments: 
            template - the name of a Deployment Template.
            version - the Template version.
            newname - a name for the new Template.
            newversion - a version for the new Template
            
        Returns: A Deployment Template object.
        """

        # define the required parameters for this call
        required_params = ["template", "version", "newname", "newversion"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        newname = args["newname"]
        newversion = args["newversion"]
        template = args["template"]
        version = args["version"]
        
        t = deployment.DeploymentTemplate()
        t.FromNameVersion(template, version)
        obj = t.DBCopy(newname, newversion)

        if obj:
            catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.DeploymentTemplate, obj.ID, obj.Name, "Deployment Template copied.")
            if args["output_format"] == "json":
                return R(response=obj.AsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.AsText(args["output_delimiter"]))
            else:
                return R(response=obj.AsXML())
        else:
            return R(err_code=R.Codes.CreateError, err_detail="Unable to copy Template.")

