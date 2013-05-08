#########################################################################
# Copyright 2011 Cloud Sidekick
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#########################################################################

try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

def vmw_list_images(TE, step):

    import catosphere
    instance_uuid, endpoint_name = TE.get_command_params(step.command, "instance_uuid", "endpoint_name")[:]
    instance_uuid = TE.replace_variables(instance_uuid)
    endpoint_name = TE.replace_variables(endpoint_name)

    cloud = TE.get_cloud_connection(endpoint_name)

    values = []
    root = ET.fromstring(step.command)
    filters = root.findall("filters/filter")
    if filters:
        the_filter = {}
        for f in filters:
            name = f.findtext("./name", "")
            if len(name):
                values = f.findall("./values/value")
                value_list = []
                for v in values:
                    #TE.logger.debug("value is %s" % (v.findtext(".", "")))
                    value_list.append(v.findtext(".", ""))
                the_filter[name] = value_list
    else:
        the_filter = None
        
    instances = cloud.server.list_instances(instanceUuid=instance_uuid, filter=the_filter)
    #TE.logger.info(instances)

    results = []
    msg = "%s\n" % (catosphere.get_all_property_names())
    if len(instances):

        for i in instances:
            prop_list = i.get_properties()
            results.append(prop_list)
            msg = "%s\n%s" % (msg, prop_list)

    if len(results):
        variables = TE.get_node_list(step.command, "step_variables/variable", "name", "position")
        TE.process_list_buffer(results, variables)

    TE.insert_audit("vmw_list_images", msg, "")

def vmw_clone_image(TE, step):

    instance_uuid, endpoint_name, name, folder, resourcepool, power_on = TE.get_command_params(step.command,
        "instance_uuid", "endpoint_name", "name", "folder", "resourcepool", "power_on")[:]
    instance_uuid = TE.replace_variables(instance_uuid)
    endpoint_name = TE.replace_variables(endpoint_name)
    TE.logger.debug("endpoint name = %s" % (endpoint_name))
    name = TE.replace_variables(name)
    folder = TE.replace_variables(folder)
    resourcepool = TE.replace_variables(resourcepool)
    power_on = TE.replace_variables(power_on)

    if len(instance_uuid) == 0:
        raise Exception("InstanceUUID field is required for VMware Clone command")
    if len(name) == 0:
        raise Exception("Name field is required for VMware Clone command")
    cloud = TE.get_cloud_connection(endpoint_name)
        
    instance = cloud.server.list_instances(instanceUuid=instance_uuid)[0]
    result = instance.clone(name=name)
    msg = "VMware Image Clone %s\nOK" % (instance_uuid)
    TE.insert_audit("vmw_clone_image", msg, "")
    TE.logger.info(result)
        
def vmw_power_on_image(TE, step):
    vmw_power_image(TE, step.command, "on")
            
def vmw_power_off_image(TE, step):
    vmw_power_image(TE, step.command, "off")
            
def vmw_power_image(TE, command, on_off):

    instance_uuid, endpoint_name = TE.get_command_params(command, "instance_uuid", "endpoint_name")[:]
    instance_uuid = TE.replace_variables(instance_uuid)
    endpoint_name = TE.replace_variables(endpoint_name)

    if len(instance_uuid) == 0:
        raise Exception("InstanceUUID field is required for VMware Power commands")

    cloud = TE.get_cloud_connection(endpoint_name)
        
    if on_off == "on":
        result = cloud.server.power_on_vm(instance_uuid)
        msg = "VMware Image Power On %s\nOK" % (instance_uuid)
        TE.insert_audit("vmw_power_on_image", msg, "")
    elif on_off == "off":
        result = cloud.server.power_off_vm(instance_uuid)
        msg = "VMware Image Power Off %s\nOK" % (instance_uuid)
        TE.insert_audit("vmw_power_off_image", msg, "")

    TE.logger.info(result)
    
