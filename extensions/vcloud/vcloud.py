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

from catotaskengine import classes
from vcloudpy import vcloudpy

def vcloud_connect(TE, step):

    cloud_name = TE.get_command_params(step.command, "endpoint_name")[0]
    cloud_name = TE.replace_variables(cloud_name)

    if not len(cloud_name):
        cloud_name = TE.cloud_name
    try:
        cloud = TE.cloud_conns[cloud_name]
    except KeyError as ex:
        cloud = classes.Cloud(cloud_name)
        TE.cloud_conns[cloud_name] = cloud

    print "cloudname = %s" % (cloud_name)

    if cloud.provider != "vCloud":
        msg = "The endpoint named cloud_name is not a vCloud configured endpoint" % (cloud_name)
        raise Exception(msg)

    if not cloud.conn:
        cloud.conn = vcloudpy.VCloudConn(TE.cloud_login_id, TE.cloud_login_password, cloud.url, debug=False)

    return cloud


def vcloud_call_parse(te, step):

    cloud = vcloud_connect(te, step)
    path, meth_or_href, action, data, type, xpath = te.get_command_params(step.command, "path", "method_or_href", 
        "action", "data", "content_type", "xpath")[:]
    path = te.replace_variables(path) 
    xpath = te.replace_variables(xpath) 
    data = te.replace_variables(data) 
    type = te.replace_variables(type) 
    values = te.get_node_list(step.command, "values/value", "name", "variable", "type")

    result = _vcloud_make_call(cloud, path, action, data, type, meth_or_href)

    msg = "vCloud API Call %s\n\%s" % (path, result)
    te.insert_audit(step.function_name, msg, "")

    _vcloud_parse_data(te, result, xpath, values)


def vcloud_call(te, step):

    cloud = vcloud_connect(te, step)
    path, meth_or_href, action, data, type, out_var = te.get_command_params(step.command, "path", "method_or_href", 
        "action", "data", "content_type", "output_var")[:]
    path = te.replace_variables(path) 
    data = te.replace_variables(data) 
    type = te.replace_variables(type) 

    result = _vcloud_make_call(cloud, path, action, data, type, meth_or_href)

    msg = "vCloud API Call %s\n%s" % (path, result)
    te.insert_audit(step.function_name, msg, "")
    if len(out_var):
        te.rt.set(out_var, result)

def _vcloud_make_call(cloud, path, action, data, type, meth_or_href):

    if not len(type):
        type = None
    if not len(data):
        data = None

    print meth_or_href

    if meth_or_href == "href":
        result = cloud.conn.make_href_request_path(path, action, data=data, type=type)
    else:
        result = cloud.conn.make_method_request(path, action)

    return result


def vcloud_parse(te, step):

    path, xml = te.get_command_params(step.command, "path", "xml")[:]
    path = te.replace_variables(path) 
    xml = te.replace_variables(xml) 
    values = te.get_node_list(step.command, "values/value", "name", "variable", "type")

    _vcloud_parse_data(te, xml, path, values)

def _vcloud_parse_data(te, xml, path, values):
    
    variables = {}
    attrib_list = []
    elem_list = []
    for v in values:
        if len(v[0]) and len(v[1]):
            if v[2] == "attribute":
                attrib_list.append(v[0])
            else:
                elem_list.append(v[0])
            variables[v[0]] = v[1]
            
    result = vcloudpy.get_node_values(xml, path, attribs=attrib_list, elems=elem_list)
    msg = "vcloud parse\n%s" % (result)
    te.insert_audit("vcloud parse", msg, "")

    ii = 0
    for row in result:
        ii += 1
        for k,v in variables.iteritems():
            if ii == 1:
                te.rt.clear(v)
            print "key %s, variable %s" % (k, v)
            if k in row:
                print "setting %s to %s" % (v,  row[k])
                te.rt.set(v, row[k], ii)
