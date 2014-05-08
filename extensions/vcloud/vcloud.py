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

from catotaskengine import classes
try:
    from vcloudpy import vcloudpy
except ImportError as e:
    msg = "vCloud commands missing Python library vcloudpy. \
            See http://docs.cloudsidekick.com/docs/cato/?cloud/vcloud.html for instructions on \
            installing the vcloudpy package on the Cato Task Engine server.\n%s" % (e)
    raise Exception(msg)
except Exception as e:
    raise Exception(e)

def vcloud_connect(TE, step, timeout=30):

    cloud_name = TE.get_command_params(step.command, "endpoint_name")[0]
    cloud_name = TE.replace_variables(cloud_name)

    if not len(cloud_name):
        cloud_name = TE.cloud_name
    try:
        cloud = TE.cloud_conns[cloud_name]
    except KeyError as ex:
        cloud = classes.Cloud(cloud_name)
        TE.cloud_conns[cloud_name] = cloud

    if cloud.provider != "vCloud":
        msg = "The endpoint named %s is not a vCloud configured endpoint" % (cloud_name)
        raise Exception(msg)

    if not cloud.conn:
        if not timeout:
            timeout = 30
        cloud.conn = vcloudpy.VCloudConn(TE.cloud_login_id, TE.cloud_login_password, cloud.url, debug=False, timeout=timeout)

    return cloud

def _convert_timeout(timeout):

    if not len(timeout):
        timeout = None
    else:
        try:
            timeout = float(timeout)
        except ValueError:
            msg = "Invalid timeout value %s, must be integer or floating decimal number" % (timeout)
    return timeout


def vcloud_call_parse(te, step):

    path, meth_or_href, action, data, type, xpath, out_var, timeout = te.get_command_params(step.command, "path", "method_or_href",
        "action", "data", "content_type", "xpath", "output_var", "timeout")[:]
    path = te.replace_variables(path)
    xpath = te.replace_variables(xpath)
    data = te.replace_variables(data)
    type = te.replace_variables(type)
    timeout = te.replace_variables(timeout)
    timeout = _convert_timeout(timeout)
    values = te.get_node_list(step.command, "values/value", "name", "variable", "type")
    cloud = vcloud_connect(te, step, timeout)

    result = _vcloud_make_call(cloud, path, action, data, type, meth_or_href, timeout=timeout)

    msg = "vCloud API Call %s\n%s" % (path, result)
    te.insert_audit(step.function_name, msg, "")
    if len(out_var):
        te.rt.set(out_var, result)

    _vcloud_parse_data(te, result, xpath, values)


def vcloud_call(te, step):

    path, meth_or_href, action, data, type, out_var, timeout = te.get_command_params(step.command, "path", "method_or_href",
        "action", "data", "content_type", "output_var", "timeout")[:]
    path = te.replace_variables(path)
    data = te.replace_variables(data)
    type = te.replace_variables(type)
    timeout = te.replace_variables(timeout)
    timeout = _convert_timeout(timeout)
    cloud = vcloud_connect(te, step, timeout)

    result = _vcloud_make_call(cloud, path, action, data, type, meth_or_href, timeout=timeout)

    msg = "vCloud API Call %s\n%s" % (path, result)
    te.insert_audit(step.function_name, msg, "")
    if len(out_var):
        te.rt.set(out_var, result)

def vcloud_get_vdc_href(te, step):

    vdc_name, vdc_name_out, vdc_href_out = te.get_command_params(step.command, "vdc_name", "vdc_name_out", "vdc_href_out")[:]
    vdc_name = te.replace_variables(vdc_name)
    vdc_name_out = te.replace_variables(vdc_name_out)
    vdc_href_out = te.replace_variables(vdc_href_out)
    cloud = vcloud_connect(te, step)

    if not len(vdc_name):
        vdc_name = None

    result = cloud.conn.get_vdcs(vdc_name)

    msg = "vCloud Get vDC Href %s\n%s" % (vdc_name, result)
    te.insert_audit(step.function_name, msg, "")
    if len(vdc_href_out):
        te.rt.clear(vdc_href_out)
    if len(vdc_name_out):
        te.rt.clear(vdc_name_out)
    if len(result):
        ii = 0
        for r in result:
            ii += 1
            if len(vdc_href_out):
                te.rt.set(vdc_href_out, r["href"], ii)
            if len(vdc_name_out):
                te.rt.set(vdc_name_out, r["name"], ii)
        

def vcloud_get_org_network_href(te, step):

    org_net_name, org_href_out, org_name_out = te.get_command_params(step.command, 
                                    "org_net_name", "net_href_out", "net_name_out")[:]
    org_net_name = te.replace_variables(org_net_name)
    org_name_out = te.replace_variables(org_name_out)
    org_href_out = te.replace_variables(org_href_out)
    cloud = vcloud_connect(te, step)

    if not len(org_net_name):
        org_net_name = None
    result = cloud.conn.get_org_networks(org_net_name)

    msg = "vCloud Get Org Network Href\n%s" % (result)
    te.insert_audit(step.function_name, msg, "")
    if len(org_href_out):
        te.rt.clear(org_href_out)
    if len(org_name_out):
        te.rt.clear(org_name_out)
    if len(result):
        ii = 0
        for r in result:
            ii += 1
            if len(org_href_out):
                te.rt.set(org_href_out, r["href"], ii)
            if len(org_name_out):
                te.rt.set(org_name_out, r["name"], ii)

def vcloud_get_vapp_href(te, step):

    vapp_name, temp, vapp_name_out, vapp_href_out = te.get_command_params(step.command, 
                        "vapp_name", "template", "vapp_name_out", "vapp_href_out")[:]
    vapp_name = te.replace_variables(vapp_name)
    vapp_name_out = te.replace_variables(vapp_name_out)
    vapp_href_out = te.replace_variables(vapp_href_out)
    cloud = vcloud_connect(te, step)

    if not len(vapp_name):
        vapp_name = None

    if temp == "no":
        temp = False
    else:
        temp = True

    result = cloud.conn.get_vapps(vapp_name, temp)

    msg = "vCloud Get vApps %s\n%s" % (vapp_name, result)
    te.insert_audit(step.function_name, msg, "")
    if len(vapp_name_out):
        te.rt.clear(vapp_name_out)
    if len(vapp_href_out):
        te.rt.clear(vapp_href_out)
    if len(result):
        ii = 0
        for r in result:
            ii += 1
            if len(vapp_name_out):
                te.rt.set(vapp_name_out, r["name"], ii)
            if len(vapp_href_out):
                te.rt.set(vapp_href_out, r["href"], ii)


def vcloud_compose_vapp(te, step):

    vdc_name, org_net_name, vapp_name, out_var = te.get_command_params(step.command, "vdc_name", "org_net_name",
                                                    "vapp_name", "vapp_href_out")[:]
    vdc_name = te.replace_variables(vdc_name)
    org_net_name = te.replace_variables(org_net_name)
    vapp_name = te.replace_variables(vapp_name)
    out_var = te.replace_variables(out_var)
    cloud = vcloud_connect(te, step)

    values = te.get_node_list(step.command, "values/value", "vm_name", "vm_href", "hostname", "admin_password", "power")

    if not len(vapp_name):
        vapp_name = None
    result = cloud.conn.compose_vapp(vdc_name, org_net_name, vapp_name)

    msg = "vCloud Compose vApp\n%s" % (result)
    te.insert_audit(step.function_name, msg, "")
    if len(out_var):
        te.rt.set(out_var, result)

    for v in values:
        vm_name = te.replace_variables(v[0])
        vm_href = te.replace_variables(v[1])
        hostname = te.replace_variables(v[2])
        admin_password = te.replace_variables(v[3])
        power = te.replace_variables(v[4])
        if not len(vm_name):
            vm_name = None
        if power == "yes":
            power = True
        else:
            power = False
        vm_name = cloud.conn.recompose_vapp(result, vm_href, vm_name)
        vm = cloud.conn.get_vms_from_vapp(result, vm_name)
        if len(vm):
            new_vm_href = vm[0]["href"]
            cloud.conn.customize_vm_guest(new_vm_href, hostname, admin_password)
            cloud.conn.customize_vm_net(new_vm_href, org_net_name)
            cloud.conn.power_on_vm(new_vm_href)


def vcloud_instantiate_vapp(te, step):

    vdc_name, org_net_name, s_vapp_name, vapp_name, descr, power, wait, out_var = te.get_command_params(step.command, 
                        "vdc_name", "org_net_name", "source_vapp_name", "vapp_name", "descr", "power", "wait", "vapp_href_out")[:]
    vdc_name = te.replace_variables(vdc_name)
    org_net_name = te.replace_variables(org_net_name)
    vapp_name = te.replace_variables(vapp_name)
    s_vapp_name = te.replace_variables(s_vapp_name)
    descr = te.replace_variables(descr)
    out_var = te.replace_variables(out_var)
    cloud = vcloud_connect(te, step)

    if wait == "yes":
        wait = True
    else:
        wait = False

    if power == "yes":
        power = True
    else:
        power = False

    if not len(vapp_name):
        vapp_name = None

    result = cloud.conn.instantiate_vapp_template(vdc_name, org_net_name, s_vapp_name,
                                            vapp_name, descr, power, wait)

    msg = "vCloud Instantiate vApp\n%s" % (result)
    te.insert_audit(step.function_name, msg, "")
    if len(out_var):
        te.rt.set(out_var, result)

def vcloud_terminate_vapp(te, step):

    vapp_name = te.get_command_params(step.command, "vapp_name")[0]
    vapp_name = te.replace_variables(vapp_name)
    cloud = vcloud_connect(te, step)

    cloud.conn.terminate_vapp(vapp_name)

    msg = "vCloud Terminate vApp %s" % (vapp_name)
    te.insert_audit(step.function_name, msg, "")

def vcloud_get_vms_from_vapp(te, step):

    vapp_name, vm_name, temp, vm_href_out, vm_name_out, vm_ip_out = te.get_command_params(step.command, "vapp_name", "vm_name", "template", 
                                        "vm_href_out", "vm_name_out", "vm_ip_out")[:]
    vapp_name = te.replace_variables(vapp_name)
    vm_name = te.replace_variables(vm_name)
    vm_href_out = te.replace_variables(vm_href_out)
    vm_name_out = te.replace_variables(vm_name_out)
    vm_ip_out = te.replace_variables(vm_ip_out)
    cloud = vcloud_connect(te, step)

    if temp == "no":
        t = False
    else:
        t = True
    if not len(vm_name):
        vm_name = None
    result = cloud.conn.get_vms_from_vapp(vapp_name, vm_name, t)

    msg = "vCloud Get Vms from Vapp\n%s" % (result)
    te.insert_audit(step.function_name, msg, "")
    if len(vm_href_out) or len(vm_name_out) or len(vm_ip_out):
        if len(vm_href_out):
            te.rt.clear(vm_href_out)
        if len(vm_name_out):
            te.rt.clear(vm_name_out)
        if len(vm_ip_out):
            te.rt.clear(vm_ip_out)

        if len(result):
            ii = 0
            for r in result:
                ii += 1
                if len(vm_href_out):
                    te.rt.set(vm_href_out, r["href"], ii)
                if len(vm_name_out):
                    te.rt.set(vm_name_out, r["name"], ii)
                if len(vm_ip_out):
                    te.rt.set(vm_ip_out, r["ip_address"], ii)

def _vcloud_make_call(cloud, path, action, data, type, meth_or_href, timeout):

    if not len(type):
        type = None
    if not len(data):
        data = None

    if meth_or_href == "href":
        result = cloud.conn.make_href_request_path(path, action, data=data, type=type, timeout=timeout)
    else:
        result = cloud.conn.make_method_request(path, action, timeout=timeout)

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
        for k, v in variables.iteritems():
            if ii == 1:
                te.rt.clear(v)
            if k in row:
                te.rt.set(v, row[k], ii)
