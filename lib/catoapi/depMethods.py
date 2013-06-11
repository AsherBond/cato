
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
from catotask import task

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
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
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
#                    return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
#                else:
#                    return R(response=obj.AsXML())
#            else:
#                return R(err_code=R.Codes.CreateError, err_detail=msg)
#            
#        except Exception:
#            return R(err_code=R.Codes.Exception)

    def deploy_application(self, args):        
        """
        Deploy an Application Template.
        
        Required Arguments: 
            name - a name for the new Deployment.
            template - the name of a defined Application Template.
            version - the ApplicationTemplate version
            
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
            msg = "Deployment Template [%s/%s] has no definition document." % (template, version)
            return R(err_code=R.Codes.CreateError, err_detail=msg)
            
        # 2)
        obj, msg = deployment.Deployment.FromTemplate(t, name, desc)
        if obj:
            catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.Deployment, obj.ID, obj.Name, "Deployment created.")
            if args["output_format"] == "json":
                return R(response=obj.AsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
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
            out.append(obj.AsText(args.get("output_delimiter"), args.get("header")))
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
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
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
            return R(response=obj.ServicesAsText(fltr, args.get("output_delimiter")))
        else:
            return R(response=obj.ServicesAsXML(fltr))
            
        
    def get_service_instances(self, args):        
        """
        Gets Service Instances from an Deployment Service.
        
        Required Arguments: 
            deployment - Value can be either an Deployment ID or Name.

        Optional Arguments
            service - can be either a Service ID or Name.
        
        Returns: A list of Services containing a list of Service Instances.
        """
        # define the required parameters for this call
        required_params = ["deployment"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = deployment.Deployment()
        obj.FromName(args["deployment"])
        
        svcs = []
        if args.get("service"):
            # a service was provided, limit it to that
            svcs.append(obj.GetService(args["service"]))
        else:
            svcs = obj.GetServices()
            
        # now we have a list of the service(s) we want... get their instances
        out = []
        for svc in svcs:
            service = {}
            service["ID"] = svc.ID
            service["Name"] = svc.Name
            service["Instances"] = [{"Instance" : x.__dict__} for x in svc.GetInstances()]
                                     
            
            out.append(service)
         
         
        if args["output_format"] == "json":
            return R(response=catocommon.ObjectOutput.IterableAsJSON(out))
        elif args["output_format"] == "text":
            delimiter = "\t" if not args.get("output_delimiter") else args.get("output_delimiter")
            header = catocommon.is_true(args.get("header", True))

            txt = []
            if header:
                txt.append(delimiter.join(['ServiceName', 'ID', 'Label', 'HostName']))
            for svc in out:
                for inst in svc["Instances"]:
                    txt.append(delimiter.join([svc["Name"], inst["InstanceID"], inst["Label"], inst["HostName"]]))
            
            return R(response="\n".join(txt))
        else:
            return R(response=catocommon.ObjectOutput.IterableAsXML(out, "Services", "Service"))

        
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
        service, msg = deployment.Service.DBCreateNew(deployment=obj, name=args["name"], desc=desc)
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
        seq = deployment.Sequence(obj)
        seq.FromName(args["sequence"])
        if args["output_format"] == "json":
            return R(response=seq.AsJSON())
        elif args["output_format"] == "text":
            return R(response=seq.AsText(args.get("output_delimiter"), args.get("header")))
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
            return R(response=obj.SequencesAsText(fltr, args.get("output_delimiter")))
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
        seq = deployment.Sequence(obj)
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
        seq = deployment.Sequence(obj)
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
        seq = deployment.Sequence(obj)
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
        seq = deployment.Sequence(obj)
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
                try:
                    action.FromName(args["action"], dep.ID, service.ID)
                except:
                    return R(err_code=R.Codes.GetError, err_detail="Unable to get *Service* Action for identifier [%s]." % args["action"])

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
            try:
                action.FromName(args["action"], dep.ID)
            except:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get *Deployment* Action for identifier [%s]." % args["action"])
        
        
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
            return R(response=catocommon.ObjectOutput.IterableAsText(taskinstances, ["Instance"], args.get("output_delimiter"), args.get("header")))
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
                try:
                    action.FromName(args["action"], dep.ID, service.ID)
                except:
                    return R(err_code=R.Codes.GetError, err_detail="Unable to get *Service* Action for identifier [%s]." % args["action"])
            else:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get Service for identifier [%s]." % svc)

        else:
            try:
                action.FromName(args["action"], dep.ID)
            except:
                return R(err_code=R.Codes.GetError, err_detail="Unable to get *Deployment* Action for identifier [%s]." % args["action"])
                
        
        
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
            return R(response=instance.AsText(args.get("output_delimiter"), args.get("header")))
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
                return R(response=instance.AsText(args.get("output_delimiter"), args.get("header")))
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
        # define the required parameters for this call
        required_params = ["deployment"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        fltr = args.get("filter", "")
        status = args.get("status", "")
        frm = args.get("from", "")
        to = args.get("to", "")
        records = args.get("records", "")

        d = deployment.Deployment()
        d.FromName(args["deployment"])

        obj = deployment.SequenceInstances(deployment_id=d.ID,
                                        fltr=fltr,
                                        status=status,
                                        frm=frm,
                                        to=to,
                                        records=records)
        if obj:
            if args["output_format"] == "json":
                return R(response=obj.AsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
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
                return R(response=catocommon.ObjectOutput.IterableAsText(results, ["log_dt", "log_msg"], args.get("output_delimiter"), args.get("header")))
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
        seq = deployment.Sequence(obj)
        seq.FromName(args["sequence"])
        t = seq.GetParametersTemplate(basic)
        if t:
            return R(response=t)
        else:
            return R(response="{}")
            

    def list_application_templates(self, args):        
        """
        Lists all Application Templates.
        
        Optional Arguments: 
            filter - will filter a value match on Template Name, Version or Description.
        
        Returns: An array of all Application Templates.
        """
        fltr = args.get("filter", "")
        
        obj = deployment.DeploymentTemplates(sFilter=fltr, show_unavailable=True)
        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())
        

    def copy_application_template(self, args):        
        """
        Copies an Application Template.
        
        Required Arguments: 
            template - the name of an Application Template.
            version - the Template version.
            newname - a name for the new Template.
            newversion - a version for the new Template
            
        Returns: An Application Template object.
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
            catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.DeploymentTemplate, obj.ID, obj.Name, "Application Template copied.")
            if args["output_format"] == "json":
                return R(response=obj.AsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=obj.AsXML())
        else:
            return R(err_code=R.Codes.CreateError, err_detail="Unable to copy Application Template.")


    def create_application_template(self, args):        
        """
        Create a new Application Template.
        
        Required Arguments: 
            name - A name for the Application Template.
            version - The Template version
            template - A JSON document formatted as a Maestro Application definition.
            
        Optional Arguments:
            description - Describe this Application Template.
            icon - a Base64 encoded image file.  (Suitable images are 32x32px in png, gif or jpg format.)
            makeavailable - Immediately make the Application Template available for deployment.
            
            
        Returns: An Application Template object.
        """

        # this is a developer function
        if not args["_developer"]:
            return R(err_code=R.Codes.Forbidden)
        
        # define the required parameters for this call
        required_params = ["name", "version"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        name = args["name"]
        version = args["version"]
        template = args.get("template")
        
        obj = deployment.DeploymentTemplate.DBCreateNew(name, version, template, args.get("description"))
        if obj:
            # after it's created, we can call obj.DBUpdate and set other properties
            obj.Icon = args.get("icon", obj.Icon)
            if catocommon.is_true(args.get("makeavailable")):
                obj.Available = 1
            obj.DBUpdate()
            
            # TODO: create matching tags... this template gets all the tags this user has.
            
            catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.DeploymentTemplate, obj.ID, obj.Name, "Application Template created.")
            if args["output_format"] == "json":
                return R(response=obj.AsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=obj.AsXML())


    def get_application_template(self, args):        
        """
        Gets an Application Template object.
        
        Required Arguments: 
            template - the name of a defined Application Template.
            version - the Application Template version.
        
        Optional Arguments: 
            getdefinition - will only return the JSON definition file.
            geticon - will only return the Base64 encoded icon.
            
            NOTE: the 'get' options are exclusive.  You cannot get both in a single call.
        
        Returns: An Application Template object.
        """
        # define the required parameters for this call
        required_params = ["template", "version"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        obj = deployment.DeploymentTemplate()
        obj.FromNameVersion(args["template"], args["version"])
        

        # if asked, only return the definition.
        if catocommon.is_true(args.get("getdefinition")):
            return R(response=obj.Text)
            
        # if asked, only return the definition.
        if catocommon.is_true(args.get("geticon")):
            return R(response=obj.Icon)
            
        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())
            

    def list_template_tasks(self, args):        
        """
        Lists all Tasks associated with an Application Template.
        
        Required Arguments: 
            template - the name of a defined Application Template.
            version - the Application Template version.

        Returns: An list of Tasks associated with the Application Template.
        """

        # define the required parameters for this call
        required_params = ["template", "version"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        version = args["version"]
        template = args.get("template")
        
        obj = deployment.DeploymentTemplate()
        obj.FromNameVersion(template, version)
        if obj.ID:
            if args["output_format"] == "json":
                return R(response=obj.TasksAsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.TasksAsText(args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=obj.TasksAsXML())

    def export_application_template(self, args):        
        """
        Generates an export JSON document containing everything in an Application Template.
        
        Required Arguments: 
            template - the name of a defined Application Template.
            version - the Application Template version.

        Returns: An JSON document containing the complete Application Template.
        """

        # THIS ONE IS CRAZY AND AMBITIOUS
        # It'll return one gigantic JSON document containing everything in the deployment.
        
        # define the required parameters for this call
        required_params = ["template", "version"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        version = args["version"]
        template = args.get("template")
        
        obj = deployment.DeploymentTemplate()
        obj.FromNameVersion(template, version)
        if not obj.ID:
            return R(err_code=R.Codes.GetError, err_detail="Unable to find Application Template for the provided Name and Version.")

        out = {}
        
        # first, what are the details of the template?
        out["Name"] = obj.Name
        out["Version"] = obj.Version
        out["Description"] = obj.Description
        out["Definition"] = obj.Text
        out["Icon"] = obj.Icon
        
        # Tasks
        apptasks = obj.GetReferencedTasks()
        taskids = [t["ID"] for t in apptasks]

        # TODO: this would be a GREAT time to look again into backup up a task as JSON
        taskbackups = task.Tasks.Export(taskids, True, outformat="json")
        out["Tasks"] = taskbackups
        
        # TODO: This isn't gonna be complete until we figure out all the reporting stuff
        
        return R(response=catocommon.ObjectOutput.AsJSON(out))

