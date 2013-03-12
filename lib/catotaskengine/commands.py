########################################################################/
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

import time
import base64
import urllib
import urllib2
import httplib
from datetime import datetime

try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

from catocommon import catocommon
from . import classes



def codeblock_cmd(self, task, step):
    name = self.get_command_params(step.command, "codeblock")[0]
    self.process_codeblock(task, name.upper())


def if_cmd(self, task, step):

    root = ET.fromstring(step.command)
    test_nodes = root.findall("./tests/test")
    action_xml = False
    for test_node in test_nodes:
        test = test_node.findtext("eval", "")
        test = self.replace_html_chars(test)
        test = self.replace_variables(test)
        dummy = {}
        if eval(test, dummy, dummy):
            action = test_node.findall("./action/function")
            if action:
                action_xml = ET.tostring(action[0])
            break
    if not action_xml:
        action = root.findall("./else/function")
        if action:
            action_xml = ET.tostring(action[0])

    if action_xml:
        sub_step = self.get_step_object(step.step_id, action_xml)
        self.process_step(task, sub_step)
        del(sub_step)
    del(root)


def while_cmd(self, task, step):

    orig_test = self.get_command_params(step.command, "test")[0]
    root = ET.fromstring(step.command)
    action = root.findall("./action/function")
    if action:
        action_xml = ET.tostring(action[0])
    else:
        action_xml = False
    del(root)

    if action_xml:
        sub_step = self.get_step_object(step.step_id, action_xml)

        orig_test = self.replace_html_chars(orig_test)
        test = self.replace_variables(orig_test)
        sub_step = self.get_step_object(step.step_id, action_xml)
        dummy = {}
        while eval(test, dummy, dummy):
            if self.loop_break:
                self.loop_break = False
                break
            self.process_step(task, sub_step)
            test = self.replace_variables(orig_test)
            self.logger.debug(test) 

        del(sub_step)


def loop_cmd(self, task, step):

    initial, counter_v_name, loop_test, orig_compare_to, increment, max_iter = self.get_command_params(step.command,
        "start", "counter", "test", "compare_to", "increment", "max")[:]
    root = ET.fromstring(step.command)
    action = root.findall("./action/function")
    if action:
        action_xml = ET.tostring(action[0])
    else:
        action_xml = False
    del(root)
    if action_xml:

        # initial will be what we set the counter to initally
        initial = int(self.replace_variables(initial))
        # counter_v_name is a variable name what will persist and be avaliable to the task steps
        counter_v_name = self.replace_variables(counter_v_name).upper()
        # loop_test is the comparison operator, such as > < <=, etc.
        loop_test = self.replace_html_chars(loop_test)
        # compare_to is the value that we're testing against, most usually a number of items
        compare_to = self.replace_variables(orig_compare_to)
        increment = int(increment)
        if max_iter:
            max_iter = int(max_iter)

        self.logger.debug("initial is %s" % initial),
        self.logger.debug("counter_v_name is %s" % counter_v_name),
        self.logger.debug("loop_test is %s" % loop_test),
        self.logger.debug("orig_compare_to is %s" % orig_compare_to),
        self.logger.debug("actual compare_to is %s" % compare_to),
        self.logger.debug("increment is %s" % increment),
        self.logger.debug("max_iter is %s" % max_iter),


        self.rt.set(counter_v_name, initial)
        counter = initial

        # this part of the test is fixed, such as "<= 10"
        test_part = "%s %s" % (loop_test, compare_to)

        test = "%s %s" % (initial, test_part)
        self.logger.debug(test)
        sub_step = self.get_step_object(step.step_id, action_xml)
        self.logger.debug("counter is %s" % counter)
        dummy = {}
        loop_num = 1
        while eval(test, dummy, dummy):
            if max_iter and loop_num > max_iter:
                    break
            if self.loop_break:
                self.loop_break = False
                break
            self.process_step(task, sub_step)
            # we have to get the counter again since it could be changed in a step
            counter = self.rt.get(counter_v_name)
            self.logger.debug("counter is %s" % counter)
            counter = counter + increment
            self.logger.debug("counter is %s" % counter)
            test = "%s %s" % (counter, test_part)
            self.rt.set(counter_v_name, counter)
            self.logger.debug(test)
            loop_num += 1


def exists_cmd(self, task, step):
    
    all_true = True
    root = ET.fromstring(step.command)
    variables = root.findall("./variables/variable")
    for v in variables:
        variable_name = v.findtext("name", "").upper()
        is_true = v.findtext("is_true", "")
        self.logger.debug("checking if %s exists ..." % (variable_name))
        
        # if result == "1":
        if self.rt.exists(variable_name):
            if is_true == "1":
                value = self.rt.get(variable_name)
                value = value.lower()
                if value != "true" and value != "yes" and value != "1":
                    all_true = False
                    break
        else:
            all_true = False
            break
    self.logger.debug("all_true = %s" % (all_true))

    action = False
    if all_true:
        action = root.findall("./actions/positive_action/function")
    else:
        action = root.findall("./actions/negative_action/function")

    if action:
        action_xml = ET.tostring(action[0])
    else:
        action_xml = False
    del(root)
    
    if action_xml:
        sub_step = self.get_step_object(step.step_id, action_xml)
        self.process_step(task, sub_step) 
        del(sub_step)


def log_msg_cmd(self, task, step):

    msg = self.get_command_params(step.command, "message")[0]
    msg = self.replace_variables(msg)
    self.insert_audit("log_msg", msg, "")


def subtask_cmd(self, task, step):
    subtask_name, subtask_version = self.get_command_params(step.command, "task_name", "version")[:]

    self.logger.debug("subtask [%s] version [%s]" % (subtask_name, subtask_version))
    if len(subtask_version):
        sql = """select task_id from task where task_name = %s and version = %s"""
        row = self.db.select_row(sql, (subtask_name, subtask_version))
    else:
        sql = """select task_id from task where task_name = %s and default_version = 1"""
        row = self.db.select_row(sql, (subtask_name))

    task_id = row[0]

    self.process_task(task_id)


def run_task_cmd(self, task, step):

    args = self.get_command_params(step.command, "task_name", "version", "handle", "asset_id", "time_to_wait")
    task_name = args[0]
    version = args[1]
    handle = args[2].lower()
    asset_id = self.replace_variables(args[3])
    wait_time = self.replace_variables(args[4])
    
    parameters = self.extract_xml_string(step.command, "parameters")
    parameters = self.replace_variables(parameters)

    if not task_name:
        raise Exception("Handle name undefined. Run Task requires a Task Name.")

    if not handle:
        raise Exception("Handle name undefined. Run Task requires a handle name.")

    try:
        h = self.task_handles[handle]
        log = "Handle name already being used in this task. Overwriting..."
        self.insert_audit("launch_run_task", log)
        del(self.task_handles[handle])
        del(h)
    except KeyError as ex:
        pass
    except Exception as ex:
        msg = "%s" % (ex)
        raise Exception(msg)
        
    sql = """select task_id, version, default_version, parameter_xml, now() from task where task_name = %s"""
    if len(version):
        sql = sql + " and version = %s"
        row = self.db.select_row(sql, (task_name, version))
    else:
        sql = sql + " and default_version = 1"
        row = self.db.select_row(sql, (task_name))

    if row:
        task_id = row[0]
        task_version = row[1]
        default_version = row[2]
        task_params = row[3]
        submitted_dt = row[4]
    else:
        msg = "Run Task - Task [%s] version [%s] does not exist." % (task_name, version)
        raise Exception(msg)

    # one final thing before submitting...
    # the parameters on the run_task command ARE NOT the full set of parameters, 
    # rather likely a subset of what's defined on the task to be ran.
    #     (this allows a user to set a few explicit values on this command,
    #     while leaving other values on the task that can be changed without the need to 
    #     change every reference to the task.)
    
    merged_params = self.merge_parameters(task_params, parameters)
    
    
    ti = catocommon.add_task_instance(task_id=task_id, user_id=self.submitted_by, debug_level=self.debug_level,
        parameter_xml=merged_params, scope_id=self.instance_id, account_id=self.cloud_account,
        schedule_instance=self.schedule_instance, submitted_by_instance=self.task_instance,
        cloud_id=self.cloud_id) 

    h = classes.TaskHandle()
    self.task_handles[handle] = h
    h.instance = ti
    h.handle_name = handle
    h.task_id = task_id
    h.submitted_by = self.submitted_by
    h.task_name = task_name
    h.task_version = task_version
    h.default_version = default_version
    h.submitted_dt = submitted_dt
    h.status = "Submitted"

    log = "Running Task Instance %s :: ID %s, Name %s, Version %s using handle %s." % (ti, task_id, task_name, task_version, handle)
    cmd = "run_task %s" % (ti)
    self.insert_audit(cmd, log)
    
    try:
        sec_wait = int(wait_time)
    except:
        sec_wait = 0 

    # if wait time is 0, don't wait
    # if wait time is -1, wait until task completion
    # if wait time is > 0, wait x seconds and continue
    if sec_wait > 0:
        log = "Waiting %s seconds before continuing" % (wait_time)
        self.insert_audit("run_task", log)
        time.sleep(sec_wait)
    elif sec_wait == -1:
        log = "Waiting until task instance %s completes" % (ti)
        self.insert_audit("run_task", log)
        while True:
            time.sleep(5)
            status = self.get_task_status(ti)
            if status in ["Completed", "Error", "Cancelled"]:
                self.refresh_handle(h)
                break

def sql_exec_cmd(self, task, step):
    # TODO: add the 'mode' stuff back in for oracle prepared statements, transactions, etc...
    
    conn_name, sql, mode, handle = self.get_command_params(step.command, "conn_name", "sql", "mode", "handle")[:]
    conn_name = self.replace_variables(conn_name)
    sql = self.replace_variables(sql)

    # the following is for oracle only
    handle = self.replace_variables(handle)

    try:
        # get the connection object
        c = self.connections[conn_name]
    except KeyError as ex:
        msg = "A connection with the name of %s has not be established" % (conn_name)
        raise Exception(msg)

    self.logger.debug("conn type is %s" % (c.conn_type))
    variables = self.get_node_list(step.command, "step_variables/variable", "name", "position")
    if c.conn_type == "mysql":
        _sql_exec_mysql(self, sql, variables, c.handle)
    elif c.conn_type in ["sqlanywhere", "sqlserver", "oracle"]:
        _sql_exec_dbi(self, sql, variables, c.handle)

def _sql_exec_dbi(self, sql, variables, conn):

    cursor = conn.cursor()
    try:
        cursor.execute(sql)
    except Exception as e:
        msg = "%s\n%s" % (sql, e)
        raise Exception(msg)

    if cursor.description:
        cols = " ".join(c[0] for c in cursor.description)
        rows = cursor.fetchall()
    else:
        rows = None
    cursor.close()
    
    if rows:
        msg = "%s\n%s\n%s" % (sql, cols, rows)
    else:
        msg = "%s" % (sql)
    self.insert_audit("sql_exec", msg, "")
    if rows:
        self.process_list_buffer(rows, variables)

def _sql_exec_mysql(self, sql, variables, conn):

    rows = self.select_all(sql, conn)
    msg = "%s\n%s" % (sql, rows)
    self.insert_audit("sql_exec", msg, "")
    self.process_list_buffer(rows, variables)


def store_private_key_cmd(self, task, step):

    key_name, cloud_name, private_key = self.get_command_params(step.command, "name", "cloud_name", "private_key")[:]
    key_name = self.replace_variables(key_name)
    cloud_name = self.replace_variables(cloud_name)
    private_key = self.replace_variables(private_key)

    if len(private_key) == 0:
        raise Exception("Private Key value is required")
    if len(cloud_name) == 0:
        raise Exception("Cloud Name is required")
    if len(key_name) == 0:
        raise Exception("Keyname is required")

    sql = """select cloud_id from clouds where cloud_name = %s"""
    row = self.db.select_row(sql, (cloud_name))
    if not row:
        msg = "Cloud Name %s is not configured in Cato" % (cloud_name)
        raise Exception(msg)

    cloud_id = row[0]

    private_key = catocommon.cato_encrypt(private_key)
    sql = """insert into clouds_keypair (keypair_id, cloud_id, keypair_name, private_key) 
        values (uuid(),%s,%s,%s) ON DUPLICATE KEY UPDATE private_key = %s"""
    self.db.exec_db(sql, (cloud_id, key_name, private_key, private_key))
    msg = "Stored private key named %s with cloud named %s" % (key_name, cloud_name)
    self.insert_audit("store_private_key", msg, "")


def comment_cmd(self, task, step):
    self.logger.info("skipping comment")


def clear_variable_cmd(self, task, step):

    variables = self.get_node_list(step.command, "variables/variable", "name")
    for var in variables:
        self.rt.clear(var[0])


def set_variable_cmd(self, task, step):

    variables = self.get_node_list(step.command, "variables/variable", "name", "value", "modifier")
    for var in variables:
        name, value, modifier = var[:]
        value = self.replace_variables(value)
        if "," in name:
            name, index = name.split(",", 2)
            index = int(index)
        else:
            index = None
        # FIXUP - need to do modifers logic here
        self.logger.info("v name is %s, value is %s" % (name, value))

        if modifier == "Math":
            value = self.math.eval_expr(value)
        elif modifier == "TO_UPPER":
            value = value.upper()
        elif modifier == "TO_LOWER":
            value = value.lower()
        elif modifier == "TO_BASE64":
            value = base64.b64encode(value)
        elif modifier == "TO_BASE64_UTF16":
            value = base64.b64encode(value.encode("utf_16_le"))
        elif modifier == "FROM_BASE64":
            value = base64.b64decode(value)
        elif modifier == "Write JSON":
            pass  # TODO
        elif modifier == "Read JSON":
            pass  # TODO

        self.rt.set(name, value, index)

    
def cancel_task_cmd(self, task, step):

    tis = self.get_command_params(step.command, "task_instance")[0]
    tis = self.replace_variables(tis)
    for ti in tis.split(" "):
        if ti.isdigit():
            msg = "Cancelling task instance %s" % (ti)
            self.insert_audit("cancel_task", msg, "")
            sql = """update task_instance set task_status = 'Aborting' 
                where task_instance = %s and task_status in ('Submitted','Staged','Processing')"""
            self.db.exec_db(sql, (ti))
            log = """Cancelling task instance %s by other task instance number %s""" % (ti, self.task_instance)
            sql = """insert into task_instance_log (task_instance, step_id, entered_dt, connection_name, log, command_text) 
                values (%s,'', now(),'',%s,'')"""
            self.db.exec_db(sql, (self.task_instance, log))
        else:
            raise Exception("Cancel Task error: invalid task instance: %s. Value must be an integer." % (ti))


def wait_for_tasks_cmd(self, task, step):

    handles = self.get_node_list(step.command, "handles/handle", "name")
    # print handles

    handle_set = []
    for handle in handles:
        # print handle[0]
        handle_name = self.replace_variables(handle[0]).lower()
        # print handle_name
        handle_set.append(handle_name)

    log = "Waiting for the following task handles to complete: %s, will check every 5 seconds." % (" ".join(handle_set))
    self.insert_audit("wait_for_tasks", log)

    while len(handle_set) > 0:

        for handle in handle_set:
            try:
                h = self.task_handles[handle]
                self.refresh_handle(h)
                if h.status in ["Completed", "Error", "Cancelled"]:
                    handle_set.remove(handle)
                    log = "Handle %s finished with a status of %s" % (handle, h.status)
                    self.insert_audit("wait_for_tasks", log)
            except KeyError as ex:
                log = "Handle %s does not exist, skipping" % (handle)
                self.insert_audit("wait_for_tasks", log)
                handle_set.remove(handle)
            except Exception as ex:
                msg = "%s" % (ex)
                raise Exception(msg)
        if len(handle_set) > 0:
            time.sleep(5)

    log = "All task handles have a finished status"
    self.insert_audit("wait_for_tasks", log)


def substring_cmd(self, task, step):

    source, v_name, start, end = self.get_command_params(step.command, "source", "variable_name", "start", "end")[:]
    source = self.replace_variables(source)
    v_name = self.replace_variables(v_name)
    start = self.replace_variables(start)
    end = self.replace_variables(end)

    if len(v_name) == 0:
        raise Exception("Substring command requires a Variable Name")

    if len(start) == 0:
        raise Exception("Substring command requires a Start value")

    if len(end) == 0:
        raise Exception("Substring command requires an End value")

    if not start.isdigit():
        raise Exception("Substring command start value must be an integer")

    if (not end.isdigit()) and (end[0] != "+") and (end[0:3] != "end"):
        raise Exception("Substring error: end index must be integer, +integer, end or end-integer")

    start = int(start) - 1
    if end.isdigit():
        end = int(end)
    elif end == "end":
        end = None
    elif end[0] == "+":
        end = start + int(end)
    elif end[0:3] == "end" and end[3] == "-":
        end = int(end[3:])

    self.logger.info("end is {%s}" % (end))
    s = source[start:end]
    
    msg = "Substring set variable %s to {%s}" % (v_name, s)
    self.insert_audit("substring", msg, "")
    self.rt.set(v_name, s)


def drop_connection_cmd(self, task, step):

    conn_name = self.get_command_params(step.command, "conn_name")[0]
    conn_name = self.replace_variables(conn_name)
    if conn_name in self.connections.keys():
        msg = "Dropping connection named %s" % (conn_name)
        self.insert_audit("drop_connection", msg, "")
        self.drop_connection(conn_name)
        

def end_cmd(self, task, step):

    message, status = self.get_command_params(step.command, "message", "status")[:]
    message = self.replace_variables(message)
    msg = "Ending task with a status of %s, message:\n%s" % (status, message)
    self.insert_audit("end_task", msg, "")
    if status == "Error":
        raise Exception("Erroring task with message:\n%s" % (message))
    self.release_all()
    self.update_status(status)
    exit()


# work in progress, not complete.
def new_connection_cmd(self, task, step):

    conn_type, conn_name, asset, cloud_name = self.get_command_params(step.command, "conn_type", "conn_name", "asset", "cloud_name")[:]
    conn_name = self.replace_variables(conn_name)
    asset = self.replace_variables(asset)
    cloud_name = self.replace_variables(cloud_name)

    if len(asset) == 0:
        raise Exception("New Connection command requires an asset to connect to")

    try:
        # we've used this conn name before without dropping it
        c = self.connections[conn_name]
    except KeyError as ex:
        # we've never used this conn name before, continue
        pass
    else:
        # close the connection and reopen
        msg = "A connection by the name %s already exists, closing the previous one and openning a new connection" % (conn_name)
        self.insert_audit("new_connection", msg, "")

        self.drop_connection(conn_name)

    # for the asset string, we can either have an asset_id, an asset name,
    # a user@instanceid or a dynamically created connection string

    if conn_type == "ssh - ec2":
        # ec2 connection type is special, we need to look up the system info
        # we need to parse the asset field for the initial information
        # format should be like: username@instanceid
        # cloud_name is not required, it will use the account default if not specified

        if "@" not in asset:
            msg = "ssh - ec2 connection type requires the following format: username@instanceid, found %s" % asset
            raise Exception(msg)
        user_id, instance_id = asset.split("@")[:2]

        try:
            # we've loaded it before
            s = self.systems[asset]
        except KeyError:
            # not been loaded yet, get it from aws
            s = self.get_aws_system_info(instance_id, user_id, cloud_name)

    elif " " not in asset:
        # this is a traditional, fixed asset connection

        if not self.is_uuid(asset):
            # look up the asset by name
            asset = self.get_system_id_from_name(asset)

        try:
            # we've loaded it before
            s = self.systems[asset]
        except KeyError:
            # not been loaded yet, get it from the db
            s = self.gather_system_info(asset)
    else:
        # the connection information should be all included in the asset string
        # in the format key=value key=value key=value
        # valid key values: address, userid, password, port, db_name

        # we need to give this asset a name, so we'll create one based on the hash
        name = hash(asset)

        try:
            # we've loaded it before
            s = self.systems[name]
        except KeyError:
            # we haven't loaded it before, let's disect the asset string

            address = userid = password = port = db_name = protocol = None

            for pair in asset.split(" "):
                k, v = pair.split("=")
                if k == "address":
                    address = v
                elif k == "userid":
                    userid = v
                elif k == "password":
                    password = v
                elif k == "port":
                    port = v
                elif k == "protocol":
                    protocol = v
                elif k == "db_name":
                    db_name = v
                else:
                    msg = "Unsupported key, value pair %s, skipping" % (pair)
                    self.logger.info(msg)
            
            s = classes.System(name, address=address, userid=userid, password=password,
                port=port, db_name=db_name, protocol=protocol)

            self.systems[name] = s

    # we've made it this far, let's create the new connection object
    conn = classes.Connection(conn_name, conn_type=conn_type, system=s)
    self.connections[conn_name] = conn
        
    # and make the connection. We'll store any connection handle we get back for later use
    self.connect_system(conn)

    msg = "New connection named %s to asset %s created with a connection type %s" % (conn_name, s.address, conn_type)
    self.insert_audit("new_connection", msg, "")


def send_email_cmd(self, task, step):

    to, sub, body = self.get_command_params(step.command, "to", "subject", "body")[:]
    to = self.replace_variables(to)
    sub = self.replace_variables(sub)
    body = self.replace_variables(body)
    msg = "Inserting into message queue : TO:{%s} SUBJECT:{%s} BODY:{%s}" % (to, sub, body)
    self.insert_audit("send_email", msg, "")

    # note - this logic is skipping the file attachment piece, to do
    # also - there may need to be some additional processing to handle html, etc. messages

    sql = """insert into message (date_time_entered,process_type,status,msg_to,msg_from,msg_subject,msg_body) 
        values (now(),1,0,%s,%s,%s,%s)"""
    self.db.exec_db(sql, (to, self.host_domain, sub, body))


def http_cmd(self, task, step):

    timeout = 5
    url, typ = self.get_command_params(step.command, "url", "type")[:]
    data = {}
    url = self.replace_variables(url)

    if not len(url):
        raise Exception("http command url is empty")

    pairs = self.get_node_list(step.command, "pairs/pair", "key", "value")

    for (k, v) in pairs:
        k = self.replace_variables(k)
        v = self.replace_variables(v)
        if len(k):
            data[k] = v

    if len(data):
        data = urllib.urlencode(data)

    if typ == "GET" and len(data):
        url = url + "?" + data
        data = None
    elif typ == "GET" and not len(data):
        data = None
    elif typ == "POST" and not len(data):
        data = None
    
    # print url
    try:
        before = datetime.now() 
        response = urllib2.urlopen(url, data, timeout)
        after = datetime.now() 
    except urllib2.HTTPError, e:
        raise Exception("HTTPError = %s, %s, %s\n%s" % (str(e.code), e.msg, e.read(), url))
    except urllib2.URLError, e:
        raise Exception("URLError = %s\n%s" % (str(e.reason), url))
    except httplib.HTTPException, e:
        raise Exception("HTTPException")
    except Exception as ex:
        raise Exception("generic exception: " + ex.__str__)

    buff = response.read()
    del(response)
    response_ms = int(round((after - before).total_seconds() * 1000))
    self.http_response = response_ms

    log = "http %s %s\012%s\012%s\012Response time = %s ms" % (typ, url, data, buff, response_ms)
    self.insert_audit("http", log)
    variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
        "range_begin", "prefix", "range_end", "suffix", "regex")
    if len(variables):
        # print variables
        self.process_buffer(buff, step)


def get_instance_handle_cmd(self, task, step):

    ti, handle = self.get_command_params(step.command, "instance", "handle")[:]
    ti = self.replace_variables(ti)
    handle = self.replace_variables(handle)

    try:
        h = self.task_handles[handle]
    except KeyError:
        h = classes.TaskHandle()
        self.task_handles[handle] = h

    if h.instance is None:
        # new task handle, set the ti and refresh it
        h.instance = ti
    elif h.instance != ti:
        # unfortunately, the task handle ti doesn't match
        # however, we will get rid of the previous handle and refresh the new one
        del(h)
        h = classes.TaskHandle()
        self.task_handles[handle] = h
        h.instance = ti
        
    self.refresh_handle(h)
    

def parse_text_cmd(self, task, step):

    buff = self.get_command_params(step.command, "text")[0]
    buff = self.replace_variables(buff)
    log = "parse_text %s" % (buff)
    self.insert_audit("parse_text", log)
    variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
        "range_begin", "prefix", "range_end", "suffix", "regex")
    if len(variables):
        # print variables
        self.process_buffer(buff, step)

def add_summary_item_cmd(self, task, step):

    name, detail = self.get_command_params(step.command, "name", "detail")[:]
    name = self.replace_variables(name)
    detail = self.replace_variables(detail)

    if len(name) == 0:
        raise Exception("Add Summary Item error, Item Name required.")
    msg = "<item><name>%s</name><detail>%s</detail></item>" % (name, detail)

    self.summary = "%s%s" % (self.summary, msg)

def set_debug_level_cmd(self, task, step):

    dl = self.get_command_params(step.command, "debug_level")[0]
    dl = self.replace_variables(dl)
    self.logger.info("Setting the debug level to [%s]" % dl)
    
    self.set_debug(dl)

def sleep_cmd(self, task, step):

    seconds = self.get_command_params(step.command, "seconds")[0]
    seconds = self.replace_variables(seconds)
    try:
        seconds = int(seconds)
    except ValueError:
        raise Exception("Sleep command requires seconds as an integer value. seconds = %s" % (seconds))

    msg = "Sleeping {%s} seconds..." % (seconds)
    self.insert_audit("sleep", msg, "")
    time.sleep(seconds)


def break_loop_cmd(self, task, step):
    
    self.insert_audit("break_loop", "Breaking out of loop.", "")
    self.loop_break = True


def winrm_cmd_cmd(self, task, step):
    
    conn_name, cmd, timeout = self.get_command_params(step.command, "conn_name", "command", "timeout")[:]
    conn_name = self.replace_variables(conn_name)
    cmd = self.replace_variables(cmd)
    timeout = self.replace_variables(timeout)

    try:
        # get the connection object
        c = self.connections[conn_name]
    except KeyError as ex:
        msg = "A connection with the name of %s has not be established" % (conn_name)
        raise Exception(msg)

    if timeout:
        to = int(timeout) 
        c.handle.timeout = c.handle.set_timeout(to)

    self.logger.info(cmd)
    command_id = c.handle.run_command(c.shell_id, cmd)
    buff, err, return_code = c.handle.get_command_output(c.shell_id, command_id)

    self.logger.info("WinRM return code %s" % return_code)
    self.logger.info("Buffer returned is %s" % buff)
    self.logger.info("Error result is %s" % err)
    
    #if return_code > 0:
    #    # return code of > 0 seems to be a winrm error. bad
    #    self.logger.info(buff)
    #    raise Exception(err)
    #elif return_code == -1:
    if return_code != 0:
        # return code of -1 seems to be an error from the command line
        # we will pass this on to the task to figure out what to do with
        if len(err):
            buff = "%s\n%s" % (buff, err)
        #else:
        #    buff = err

    c.handle.cleanup_command(c.shell_id, command_id)

    
    msg = "%s\n%s" % (cmd, buff)
    self.insert_audit("winrm_cmd", msg)
    variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
        "range_begin", "prefix", "range_end", "suffix", "regex")
    if len(variables):
        self.process_buffer(buff, step)

    
def cmd_line_cmd(self, task, step):    

    conn_name, timeout, cmd, pos, neg = self.get_command_params(step.command,
        "conn_name", "timeout", "command", "positive_response", "negative_response")
    conn_name = self.replace_variables(conn_name)
    timeout = self.replace_variables(timeout)
    cmd = self.replace_variables(cmd)
    pos = self.replace_variables(pos)
    neg = self.replace_variables(neg)

    try:
        # get the connection object
        c = self.connections[conn_name]
    except KeyError as ex:
        msg = "A connection with the name of %s has not be established" % (conn_name)
        raise Exception(msg)

    if not len(pos):
        pos = "PROMPT>"
    if not len(neg):
        neg = "This is a default response you shouldnt get it 09kjsjkj49"
    if not len(timeout):
        timeout = self.timeout_value
    else:
        timeout = int(timeout)

    self.logger.info("sending %s to the process" % (cmd))
    buff = self.execute_expect(c.handle, cmd, pos, neg, timeout)
    self.insert_audit("cmd_line", "%s\n%s" % (cmd, buff), conn_name)

    variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
        "range_begin", "prefix", "range_end", "suffix", "regex")
    if len(variables):
        # print variables
        self.process_buffer(buff, step)

