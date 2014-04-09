#########################################################################
# Copyright 2014 Cloud Sidekick
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
import json
import time
import copy
from catotaskengine import classes
try:
    from digocn import digocn
except ImportError as e:
    msg = "Digital Ocean commands missing Python library digocn. \
            See http://docs.cloudsidekick.com/docs/cato/?cloud/digocn.html for instructions on \
            installing the digocn package on the Cato Task Engine server.\n%s" % (e)
    raise Exception(msg)
except Exception as e:
    raise Exception(e)

def digocn_connect(TE):

    cloud_name = "digital-ocean"
    try:
        cloud = TE.cloud_conns[cloud_name]
    except KeyError as ex:
        cloud = classes.Cloud(cloud_name)
        TE.cloud_conns[cloud_name] = cloud

    if not cloud.conn:
        cloud.conn = digocn.DigOcnConn(TE.cloud_login_id, TE.cloud_login_password, debug=False)

    return cloud

def check_event_status(conn, event_id):
    """A helper that will loop until the even is done"""

    status = None
    while status != "done":
        time.sleep(10)
        r = conn.call("events", action=None, subject=event_id)
        try:
            status = r["event"]["action_status"]
        except KeyError:
            msg = "Event not found: %s, %s" % (event_id, r)
            raise Exception(msg)
        except Exception as ex:
            raise Exception(ex)
    return

def digocn_call(te, step):

    noun, action, subject, status, message, results = te.get_command_params(step.command, "noun", "action",
        "subject", "status", "message", "results")[:]
    noun = te.replace_variables(noun)
    action = te.replace_variables(action)
    subject = te.replace_variables(subject)
    status = te.replace_variables(status)
    message = te.replace_variables(message)
    results = te.replace_variables(results)
    params = te.get_node_list(step.command, "params/param", "name", "value")
    cloud = digocn_connect(te)
    params_dict = {}
    for n,v in params:
        n = te.replace_variables(n)
        v = te.replace_variables(v)
        params_dict[n] = v

    if not len(action):
        action = None
    if not len(subject):
        subject = None
    result = cloud.conn.call(noun, action, subject, params_dict)

    if len(status):
        s = result.get("status", "")
        te.rt.set(status, s)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)
    if len(results):
        te.rt.set(results, result)

def digocn_new_droplet(te, step):

    name, size_id, size_slug, image_id, image_slug, region_id, region_slug, ssh_key_ids, private_networking, \
        backups_enabled, wait, timeout, status, message, droplet_id, event_id, ip_address = te.get_command_params(step.command,  
        "name", "size_id", "size_slug", "image_id", "image_slug", "region_id", "region_slug", "ssh_key_ids", "private_networking",
        "backups_enabled", "wait", "timeout", "status", "message", "droplet_id", "event_id", "ip_address")[:]
    name = te.replace_variables(name)
    size_id = te.replace_variables(size_id)
    size_slug = te.replace_variables(size_slug)
    image_id = te.replace_variables(image_id)
    image_slug = te.replace_variables(image_slug)
    region_id = te.replace_variables(region_id)
    region_slug = te.replace_variables(region_slug)
    ssh_key_ids = te.replace_variables(ssh_key_ids)
    timeout = te.replace_variables(timeout)
    status = te.replace_variables(status)
    message = te.replace_variables(message)
    droplet_id = te.replace_variables(droplet_id)
    event_id = te.replace_variables(event_id)
    if not len(name):
        raise Exception("New Droplet command requires a Name value")
    if not len(size_id) and not len(size_slug):
        raise Exception("New Droplet command requires a Size Id or Size Slug value")
    if not len(image_id) and not len(image_slug):
        raise Exception("New Droplet command requires a Image Id or Image Slug value")
    if not len(region_id) and not len(region_slug):
        raise Exception("New Droplet command requires a Region Id or Region Slug value")

    params_dict = {}
    params_dict["name"] = name
    if not len(size_id):
        params_dict["size_slug"] = size_slug
    else:
        params_dict["size_id"] = size_id
    if not len(image_id):
        params_dict["images_slug"] = images_slug
    else:
        params_dict["image_id"] = image_id
    if not len(region_id):
        params_dict["region_slug"] = region_slug
    else:
        params_dict["region_id"] = region_id
    if len(ssh_key_ids):
        params_dict["ssh_key_ids"] = ssh_key_ids
    if private_networking == "1":
        params_dict["private_networking"] = 1
    if backups_enabled == "1":
        params_dict["backups_enabled"] = 1
    params_dict_copy = copy.copy(params_dict)

    cloud = digocn_connect(te)
    result = cloud.conn.call(noun="droplets", action="new", subject=None, params=params_dict)
    result_status = result.get("status", "")
    msg = "Digital Ocean New Droplet %s\n%s" % (params_dict_copy, json.dumps(result))
    te.insert_audit(step.function_name, msg, "")
    if result_status == "OK":
        result_event_id = result["droplet"].get("event_id", "")

    result_droplet_id = result["droplet"].get("id", "")

    if len(status):
        te.rt.set(status, result_status)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)
    if len(droplet_id):
        te.rt.set(droplet_id, result_droplet_id)
    if len(event_id):
        te.rt.set(event_id, result_event_id)

    if wait == "1" and result_status == "OK":
        te.insert_audit(step.function_name, "waiting for create to be done...", "")
        check_event_status(cloud.conn, result_event_id)
        te.insert_audit(step.function_name, "droplet is ready", "")

        if len(ip_address):
            result = cloud.conn.call(noun="droplets", action=None, subject=result_droplet_id)
            te.rt.set(ip_address, result["droplet"].get("ip_address", ""))
            



def digocn_destroy_droplet(te, step):

    droplet_id, scrub, wait, timeout, status, message, event_id = te.get_command_params(step.command, \
        "id", "scrub", "wait", "timeout", "status", "message", "event_id")[:]
    droplet_id = te.replace_variables(droplet_id)
    timeout = te.replace_variables(timeout)
    status = te.replace_variables(status)
    message = te.replace_variables(message)
    event_id = te.replace_variables(event_id)
    if not len(droplet_id):
        raise Exception("Destroy Droplet command requires a Droplet Id value")

    params_dict = {}
    if scrub == "1":
        params_dict["scrub_data"] = 1

    cloud = digocn_connect(te)
    result = cloud.conn.call(noun="droplets", action="destroy", subject=droplet_id, params=params_dict)
    result_status = result.get("status", "")
    msg = "Digital Ocean Destroy Droplet %s\n%s" % (droplet_id, json.dumps(result))
    te.insert_audit(step.function_name, msg, "")
    if result_status == "OK":
        result_event_id = result.get("event_id", "")

    if wait == "1" and result_status == "OK":
        te.insert_audit(step.function_name, "waiting for destroy to be done...", "")
        check_event_status(cloud.conn, result_event_id)
        te.insert_audit(step.function_name, "droplet is destroyed", "")

    if len(status):
        te.rt.set(status, result_status)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)
    if len(event_id):
        te.rt.set(event_id, result_event_id)


def digocn_reboot_droplet(te, step):

    droplet_id, wait, timeout, status, message, event_id = te.get_command_params(step.command, \
        "id", "wait", "timeout", "status", "message", "event_id")[:]
    droplet_id = te.replace_variables(droplet_id)
    timeout = te.replace_variables(timeout)
    status = te.replace_variables(status)
    message = te.replace_variables(message)
    event_id = te.replace_variables(event_id)
    if not len(droplet_id):
        raise Exception("Reboot Droplet command requires a Droplet Id value")

    cloud = digocn_connect(te)
    result = cloud.conn.call(noun="droplets", action="reboot", subject=droplet_id)
    result_status = result.get("status", "")
    msg = "Digital Ocean Reboot Droplet %s\n%s" % (droplet_id, json.dumps(result))
    te.insert_audit(step.function_name, msg, "")
    if result_status == "OK":
        result_event_id = result.get("event_id", "")

    if wait == "1" and result_status == "OK":
        te.insert_audit(step.function_name, "waiting for reboot to be done...", "")
        check_event_status(cloud.conn, result_event_id)
        te.insert_audit(step.function_name, "droplet is rebooted", "")

    if len(status):
        te.rt.set(status, result_status)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)
    if len(event_id):
        te.rt.set(event_id, result_event_id)


def digocn_poweroff_droplet(te, step):

    droplet_id, wait, timeout, status, message, event_id = te.get_command_params(step.command, \
        "id", "wait", "timeout", "status", "message", "event_id")[:]
    droplet_id = te.replace_variables(droplet_id)
    timeout = te.replace_variables(timeout)
    status = te.replace_variables(status)
    message = te.replace_variables(message)
    event_id = te.replace_variables(event_id)
    if not len(droplet_id):
        raise Exception("Power Off Droplet command requires a Droplet Id value")

    cloud = digocn_connect(te)
    result = cloud.conn.call(noun="droplets", action="power_off", subject=droplet_id)
    result_status = result.get("status", "")
    msg = "Digital Ocean Power Off Droplet %s\n%s" % (droplet_id, json.dumps(result))
    te.insert_audit(step.function_name, msg, "")
    if result_status == "OK":
        result_event_id = result.get("event_id", "")

    if wait == "1" and result_status == "OK":
        te.insert_audit(step.function_name, "waiting for power off to be done...", "")
        check_event_status(cloud.conn, result_event_id)
        te.insert_audit(step.function_name, "droplet is powered off", "")

    if len(status):
        te.rt.set(status, result_status)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)
    if len(event_id):
        te.rt.set(event_id, result_event_id)


def digocn_poweron_droplet(te, step):

    droplet_id, wait, timeout, status, message, event_id = te.get_command_params(step.command, \
        "id", "wait", "timeout", "status", "message", "event_id")[:]
    droplet_id = te.replace_variables(droplet_id)
    timeout = te.replace_variables(timeout)
    status = te.replace_variables(status)
    message = te.replace_variables(message)
    event_id = te.replace_variables(event_id)
    if not len(droplet_id):
        raise Exception("Power On Droplet command requires a Droplet Id value")

    cloud = digocn_connect(te)
    result = cloud.conn.call(noun="droplets", action="power_on", subject=droplet_id)
    result_status = result.get("status", "")
    msg = "Digital Ocean Power On Droplet %s\n%s" % (droplet_id, json.dumps(result))
    te.insert_audit(step.function_name, msg, "")
    if result_status == "OK":
        result_event_id = result.get("event_id", "")

    if wait == "1" and result_status == "OK":
        te.insert_audit(step.function_name, "waiting for power on to be done...", "")
        check_event_status(cloud.conn, result_event_id)
        te.insert_audit(step.function_name, "droplet is powered on", "")

    if len(status):
        te.rt.set(status, result_status)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)
    if len(event_id):
        te.rt.set(event_id, result_event_id)


def digocn_cycle_droplet(te, step):

    droplet_id, wait, timeout, status, message, event_id = te.get_command_params(step.command, \
        "id", "wait", "timeout", "status", "message", "event_id")[:]
    droplet_id = te.replace_variables(droplet_id)
    timeout = te.replace_variables(timeout)
    status = te.replace_variables(status)
    message = te.replace_variables(message)
    event_id = te.replace_variables(event_id)
    if not len(droplet_id):
        raise Exception("Power Cycle Droplet command requires a Droplet Id value")

    cloud = digocn_connect(te)
    result = cloud.conn.call(noun="droplets", action="power_cycle", subject=droplet_id)
    result_status = result.get("status", "")
    msg = "Digital Ocean Power Cycle Droplet %s\n%s" % (droplet_id, json.dumps(result))
    te.insert_audit(step.function_name, msg, "")
    if result_status == "OK":
        result_event_id = result.get("event_id", "")

    if wait == "1" and result_status == "OK":
        te.insert_audit(step.function_name, "waiting for power cycle to be done...", "")
        check_event_status(cloud.conn, result_event_id)
        te.insert_audit(step.function_name, "droplet is power cycled", "")

    if len(status):
        te.rt.set(status, result_status)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)
    if len(event_id):
        te.rt.set(event_id, result_event_id)


def digocn_shutdown_droplet(te, step):

    droplet_id, wait, timeout, status, message, event_id = te.get_command_params(step.command, \
        "id", "wait", "timeout", "status", "message", "event_id")[:]
    droplet_id = te.replace_variables(droplet_id)
    timeout = te.replace_variables(timeout)
    status = te.replace_variables(status)
    message = te.replace_variables(message)
    event_id = te.replace_variables(event_id)
    if not len(droplet_id):
        raise Exception("Shutdown Droplet command requires a Droplet Id value")

    cloud = digocn_connect(te)
    result = cloud.conn.call(noun="droplets", action="shutdown", subject=droplet_id)
    result_status = result.get("status", "")
    msg = "Digital Ocean Shutdown Droplet %s\n%s" % (droplet_id, json.dumps(result))
    te.insert_audit(step.function_name, msg, "")
    if result_status == "OK":
        result_event_id = result.get("event_id", "")

    if wait == "1" and result_status == "OK":
        te.insert_audit(step.function_name, "waiting for shutdown to be done...", "")
        check_event_status(cloud.conn, result_event_id)
        te.insert_audit(step.function_name, "droplet is shutdown", "")

    if len(status):
        te.rt.set(status, result_status)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)
    if len(event_id):
        te.rt.set(event_id, result_event_id)


def digocn_resetroot_droplet(te, step):

    droplet_id, wait, timeout, status, message, event_id = te.get_command_params(step.command, \
        "id", "wait", "timeout", "status", "message", "event_id")[:]
    droplet_id = te.replace_variables(droplet_id)
    timeout = te.replace_variables(timeout)
    status = te.replace_variables(status)
    message = te.replace_variables(message)
    event_id = te.replace_variables(event_id)
    if not len(droplet_id):
        raise Exception("Reset Root Password Droplet command requires a Droplet Id value")

    cloud = digocn_connect(te)
    result = cloud.conn.call(noun="droplets", action="password_reset", subject=droplet_id)
    result_status = result.get("status", "")
    msg = "Digital Ocean Reset Root Password Droplet %s\n%s" % (droplet_id, json.dumps(result))
    te.insert_audit(step.function_name, msg, "")
    if result_status == "OK":
        result_event_id = result.get("event_id", "")

    if wait == "1" and result_status == "OK":
        te.insert_audit(step.function_name, "waiting for password reset to be done...", "")
        check_event_status(cloud.conn, result_event_id)
        te.insert_audit(step.function_name, "droplet password is reset", "")

    if len(status):
        te.rt.set(status, result_status)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)
    if len(event_id):
        te.rt.set(event_id, result_event_id)


def digocn_show_droplet(te, step):

    droplet_id, name, size_id, image_id, region_id, ip_address, private_ip_address, backups_active, \
        locked, d_status, created_at, status, message, droplet_id_out = te.get_command_params(step.command, \
        "id", "name", "size_id", "image_id", "region_id", "ip_address", "private_ip_address", "backups_active",
        "locked", "d_status", "created_at", "status", "message", "droplet_id")[:]
    droplet_id = te.replace_variables(droplet_id)
    name = te.replace_variables(name)
    size_id = te.replace_variables(size_id)
    image_id = te.replace_variables(image_id)
    region_id = te.replace_variables(region_id)
    ip_address = te.replace_variables(ip_address)
    private_ip_address = te.replace_variables(private_ip_address)
    backups_active = te.replace_variables(backups_active)
    locked = te.replace_variables(locked)
    d_status = te.replace_variables(d_status)
    created_at = te.replace_variables(created_at)
    status = te.replace_variables(status)
    message = te.replace_variables(message)
    droplet_id_out = te.replace_variables(droplet_id_out)

    if not len(droplet_id):
        droplet_id = None

    cloud = digocn_connect(te)
    result = cloud.conn.call(noun="droplets", action=None, subject=droplet_id)
    result_status = result.get("status", "")
    msg = "Digital Ocean Show Droplet %s\n%s" % (droplet_id, json.dumps(result))
    te.insert_audit(step.function_name, msg, "")

    if len(status):
        m = result.get("status", "")
        te.rt.set(status, result_status)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)

    if droplet_id:
        droplets = []
        droplets.append(result["droplet"])
    else:
        droplets = result["droplets"]
    if len(droplet_id_out):
        te.rt.clear(droplet_id_out)
    if len(name):
        te.rt.clear(name)
    if len(size_id):
        te.rt.clear(size_id)
    if len(image_id):
        te.rt.clear(image_id)
    if len(region_id):
        te.rt.clear(region_id)
    if len(ip_address):
        te.rt.clear(ip_address)
    if len(private_ip_address):
        te.rt.clear(private_ip_address)
    if len(backups_active):
        te.rt.clear(backups_active)
    if len(locked):
        te.rt.clear(locked)
    if len(d_status):
        te.rt.clear(d_status)
    if len(created_at):
        te.rt.clear(created_at)
    
    ii = 0
    for d in droplets:
        ii += 1
        if len(droplet_id_out):
            te.rt.set(droplet_id_out, d.get("id", ""), ii)
        if len(name):
            te.rt.set(name, d.get("name", ""), ii)
        if len(size_id):
            te.rt.set(size_id, d.get("size_id", ""), ii)
        if len(image_id):
            te.rt.set(image_id, d.get("image_id", ""), ii)
        if len(region_id):
            te.rt.set(region_id, d.get("region_id", ""), ii)
        if len(ip_address):
            te.rt.set(ip_address, d.get("ip_address", ""), ii)
        if len(private_ip_address):
            te.rt.set(private_ip_address, d.get("private_ip_address", ""), ii)
        if len(backups_active):
            te.rt.set(backups_active, d.get("backups_active", ""), ii)
        if len(locked):
            te.rt.set(locked, d.get("locked", ""), ii)
        if len(d_status):
            te.rt.set(d_status, d.get("status", ""), ii)
        if len(created_at):
            te.rt.set(created_at, d.get("created_at", ""), ii)


def digocn_show_ssh_keys(te, step):

    key_id, name, id_out, name_out, status, message = te.get_command_params(step.command, \
        "key_id", "name", "id_out", "name_out", "status", "message")[:]
    key_id = te.replace_variables(key_id)
    name = te.replace_variables(name)
    id_out = te.replace_variables(id_out)
    name_out = te.replace_variables(name_out)

    if not len(key_id):
        key_id = None

    cloud = digocn_connect(te)
    result = cloud.conn.call(noun="ssh_keys", action=None, subject=key_id)
    result_status = result.get("status", "")
    msg = "Digital Ocean Show Ssh Key %s\n%s" % (key_id, json.dumps(result))
    te.insert_audit(step.function_name, msg, "")

    if len(status):
        m = result.get("status", "")
        te.rt.set(status, result_status)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)

    if key_id:
        keys = []
        keys.append(result["ssh_key"])
    else:
        keys = result["ssh_keys"]

    if len(id_out):
        te.rt.clear(id_out)
    if len(name_out):
        te.rt.clear(name_out)

    if len(name):
        # we're filtering the list by key name
        for k in keys:
            if name == k.get("name"):
                if len(id_out):
                    te.rt.set(id_out, k.get("id", ""))
                if len(name_out):
                    te.rt.set(name_out, k.get("name", ""))
                break
    else:
        ii = 0
        for k in keys:
            ii += 1
            if len(id_out):
                te.rt.set(id_out, k.get("id", ""), ii)
            if len(name_out):
                te.rt.set(name_out, k.get("name", ""), ii)



