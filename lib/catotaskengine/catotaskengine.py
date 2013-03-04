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

import logging
from catolog import catolog
from catoconfig import catoconfig

import sys
import os
import traceback
import time
import re
import pwd
import importlib                   
import pexpect

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)


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
from catodb import catodb
from catoruntimes import runtimes
from bson.json_util import dumps
from datetime import datetime
import uuid
from awspy import awspy
import urllib
import urllib2
import httplib
import base64
from . import matheval


# global logger can be used in all classes.
logger = None

class Step:
    def __init__(self, step_id, function_name, function_xml, parse_method, row_delimiter, col_delimiter):
        self.step_id = step_id
        self.function_name = function_name
        self.command = function_xml
        self.parse_method = parse_method
        self.row_delimiter = row_delimiter
        self.col_delimiter = col_delimiter

class Codeblock: 

    def __init__(self, task_id, codeblock_name):
        global logger
        logger.info("loading %s " % codeblock_name)
        self.task_id = task_id
        self.codeblock_name = codeblock_name
        self.step_list = []
        self.get_steps()

    def add_step(self, step):

        self.step_list.append(step)

    def get_steps(self):

        sql = """select lower(step_id), function_name, function_xml
            , ExtractValue(function_xml, 'function/@parse_method') as parse_method
            , ExtractValue(function_xml, 'function/@row_delimiter') as row_delimiter
            , ExtractValue(function_xml, 'function/@col_delimiter') as col_delimiter
        from task_step 
        where task_id = %s and codeblock_name = %s
            and commented = 0
        order by step_order asc"""

        db = catocommon.new_conn()
        rows = db.select_all(sql, (self.task_id, self.codeblock_name))
        db.close()
        if rows:
            for row in rows:
                step_id, function_name, function_xml, parse_method, row_del, col_del = row[:]
                self.add_step(Step(step_id, function_name, function_xml, parse_method, row_del, col_del))

class Task:

    def __init__(self, task_id):

        self.task_id = task_id
        self.codeblocks = {}
        self.get_codeblocks()

    def get_codeblocks(self): 

        sql = """select distinct upper(codeblock_name) from task_codeblock
                where task_id = %s"""
        db = catocommon.new_conn()
        rows = db.select_all(sql, (self.task_id))
        db.close()
        if rows:
            for row in rows:
                cb_name = row[0]
                self.codeblocks[cb_name] = Codeblock(self.task_id, cb_name)


class Asset:

    def __init__(self, asset_id):

        self.asset_id = asset_id
        self.name = None
        self.address = None
        self.port = None
        self.db_name = None
        self.conn_type = None
        self.userid = None
        self.password = None
        self.priv_password = None
        self.domain = None
        self.conn_string = None
        self.private_key = None
        self.private_key_name = None

    def get(self):
        
        db = catocommon.new_conn()
        sql = """select a.asset_name, a.address, a.port, a.db_name , a.connection_type, ac.username, 
                ac.password, ac.domain, ac.privileged_password, a.conn_string 
            from asset a left outer join asset_credential ac on a.credential_id = ac.credential_id
            where asset_id = %s"""
        row = db.select_row(sql, (self.asset_id))
        db.close()
        if len(row) == 0:
            raise Exception("An Asset record for the asset id %s does not exist" % (self.asset_id))

        self.name, self.address, self.port, self.db_name, self.conn_type, self.userid, password, priv_password, \
            self.domain, self.conn_string, self.private_key, self.private_key_name = row[:]

        if len(password):
            self.password = catocommon.cato_decrypt(password)
        if len(priv_password):
            self.priv_password = catocommon.cato_decrypt(priv_password)
        
class System:
    def __init__(self, name, address=None, port=None, db_name=None, conn_type=None, userid=None,
        password=None, p_password=None, domain=None, conn_string=None, private_key=None,
        private_key_name=None, cloud_name=None, protocol=None):

        self.name = name
        self.address = address
        self.port = port
        self.db_name = db_name
        self.conn_type = conn_type
        self.userid = userid
        self.password = password
        self.p_password = p_password
        self.domain = domain
        self.conn_string = conn_string
        self.private_key = private_key
        self.private_key_name = private_key_name
        self.cloud_name = cloud_name
        self.protocol = protocol


class Connection:
    def __init__(self, conn_name, conn_type=None, system=None):

        self.conn_name = conn_name
        self.conn_handle = None
        self.conn_type = conn_type
        self.system = system


class TaskHandle:
    def __init__(self):
        self.instance = None
        self.handle_name = None
        self.task_id = None
        self.submitted_by = None
        self.task_name = None
        self.task_version = None
        self.default_version = None
        self.submitted_dt = None
        self.status = None
        self.started_dt = None
        self.completed_dt = None
        self.cenode = None
        self.pid = None
        self.asset = None
        self.asset_name = None
        self.is_default = None


class Cloud:
    def __init__(self, cloud_name):
        self.cloud_id = None
        self.cloud_name = cloud_name
        self.url = None
        self.protocol = None
        self.region = None
        self.provider = None
        self.default_account = None
        self.path = "/"
    
        db = catocommon.new_conn()
        sql = """select cloud_id, provider, api_url, api_protocol, default_account_id, region
            from clouds where cloud_name = %s"""
        row = db.select_row(sql, (cloud_name))
        db.close()
        if not row:
            msg = "The cloud endpoint name %s is not configured in the Cato database" % cloud_name
            raise Exception(msg) 

        self.cloud_id, self.provider, self.url, self.protocol, self.default_account, self.region = row[:]
        self.cloud_name = cloud_name

        if self.provider == "Amazon AWS":
            self.url = None
        elif self.provider == "Eucalyptus":
            self.path = "/services/Eucalyptus/"
        

    def connect(self, uid, pwd):
        # from vmware.vsphere import Server
        from catosphere import Server
        self.server = Server()
        self.server.connect(url=self.url, username=uid, password=pwd)

class TaskEngine():

    def __init__(self, process_name, task_instance):
        self.host = os.uname()[1]
        self.platform = os.uname()[0]
        self.user = pwd.getpwuid(os.getuid())[0]
        self.host_domain = self.user + '@' + os.uname()[1]
        self.my_pid = os.getpid()
        self.process_name = process_name
        self.home = catoconfig.BASEPATH
        self.tmpdir = catoconfig.CONFIG["tmpdir"]
        self.math = matheval.MathEval()

        self.task_instance = task_instance
        
        # tell catoconfig what the LOGFILE name is, then get a logger
        # if logging has already been set up this won't do anything
        # but if it's not yet, this will set the basic config
        logging.basicConfig(level=logging.DEBUG)

        # tell catolog what the LOGFILE name is, then get a logger
        catolog.set_logfile(os.path.join(catolog.LOGPATH, "ce", self.task_instance + ".log"))

        # IMPORTANT! set the global logger in this module, so the other classes 
        # defined in this file can use it!
        global logger
        logger = catolog.get_logger(process_name)

        
        self.mysql_conns = {}
        self.cloud_conns = {}
        self.task_handles = {}
        self.connections = {}
        self.systems = {}
        self.assets = {}
        self.tasks = {}
        self.audit_trail_on = 2
        self.current_step_id = ""
        self.loop_break = False
        self.timeout_value = 20
        self.summary = ""
        self.rt = runtimes.Runtimes()
        self.submitted_by_user = ""
        self.submitted_by_email = ""
        self.http_response = -1
        self.instance_id = ""

    # ## internal methods here

    def _xml_del_namespace(self, xml):
        try:
            p = re.compile("xmlns=*[\"\"][^\"\"]*[\"\"]")
            allmatches = p.finditer(xml)
            for match in allmatches:
                xml = xml.replace(match.group(), "")

            return xml
        except Exception:
            logger.error(traceback.format_exc())
            return ""

    def disconnect_oracle(self, handle):
    
        try:
            handle.close()
        except:
            pass

    def disconnect_mssql(self, handle):
    
        try:
            handle.close()
        except:
            pass

    def disconnect_sqlany(self, handle):
    
        try:
            handle.close()
        except:
            pass

    def disconnect_mysql(self, handle):
    
        try:
            handle.close()
        except:
            pass

    def disconnect_expect(self, handle):

        try:
            handle.close()
        except:
            pass

    def execute_expect(self, c, cmd, pos="PROMPT>", neg=None, timeout=20):

        expect_list = [pos, pexpect.EOF, pexpect.TIMEOUT]
        if neg:
            expect_list.append(neg)

        c.timeout = timeout
        c.sendline(cmd)
        index = c.expect(expect_list)
        if index == 0:
            pass
        elif index == 1:
            msg = "The connection to closed unexpectedly."
            try:
                msg = msg + "\n" + c.before + c.match.group() + c.after
            except:
                pass
            raise Exception(msg)
        elif index == 2:
            msg = "%s\nCommand timed out after %s seconds." % (cmd, timeout)
            raise Exception(msg)
        elif index == 3:
            msg = "Negative response %s received ..." % (neg)
            try:
                msg = cmd + "\n" + msg + "\n" + c.before + c.match.group() + c.after
            except:
                pass
            raise Exception(msg)

        return c.before

    def connect_expect(self, type, host, user, password=None, passphrase=None, key=None, default_prompt=None):

        at_prompt = False
        timeout = 20
            
        if not default_prompt:
            default_prompt = "~ #|# $|% $|\$ $"

        if not host:
            raise Exception("Connection address is required to establish a connection")
        if not user:
            raise Exception("User id is required to establish a connection")
        
        expect_list = [
            "No route to host|Network is unreachable|onnection reset by peer|onnection refused|onnection closed by|Read from socket failed|Name or service not known|Connection timed out",
            "Please login as the user .* rather than the user|expired|Old password:|Host key verification failed|Authentication failed|denied|incorrect|Login Failed|This Account is NOT Valid",
            "yes/no",
            "passphrase for key.*:",
            default_prompt,
            "password will expire(.*)assword: ",
            "assword: $|assword:$",
            pexpect.EOF,
            pexpect.TIMEOUT]

        if key:
            kf_name = "%s/%s.pem" % (self.tmpdir, self.new_uuid())
            kf = file(kf_name, "w",)
            kf.write(key)
            kf.close()
            os.chmod(kf_name, 0400)
            cmd = "ssh -i %s -o ForwardAgent=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null %s@%s" % (kf_name, user, host)
        else:
            cmd = "ssh -o ForwardAgent=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null %s@%s" % (user, host)

        reattempt = True
        attempt = 1
        while reattempt is True:
            c = pexpect.spawn(cmd, timeout=timeout, logfile=sys.stdout)

            # TODO - telnet support
            # TODO - regenerate host key if failure

            msg = None
            cpl = c.compile_pattern_list(expect_list)
                
            while not at_prompt:

                index = c.expect_list(cpl)
                if index == 0 or index == 8:
                    if attempt != 10:
                        log_msg = "ssh connection address %s unreachable on attempt %d. Sleeping and reattempting" % (host, attempt)
                        self.insert_audit("new_connection", log_msg, "")
                        time.sleep(20)
                        attempt += 1
                        break
                    else:
                        msg = "The address %s is unreachable, check network or firewall settings" % (host)
                elif index == 1:
                    msg = "Authentication failed for address %s, user %s" % (host, user)
                elif index == 2:
                    c.sendline ("yes")
                elif index == 3:
                    c.sendline(passphrase)
                elif index == 4:
                    at_prompt = True
                    reattempt = False
                elif index == 5:
                    logger.warning("The password for user %s will expire soon! Continuing ..." % (user))
                    c.logfile = None
                    c.sendline(password)
                    # c.logfile=sys.stdout 
                elif index == 6:
                    c.logfile = None
                    c.sendline(password)
                    # c.logfile=sys.stdout 
                    c.delaybeforesend = 0
                elif index == 7:
                    msg = "The connection to %s closed unexpectedly." % (host)
                if msg:
                    print msg
                    try: 
                        msg = msg + "\n" + c.before + c.match.group() + c.after
                    except:
                        pass
                    raise Exception(msg)

        c.sendline("unset PROMPT_COMMAND;export PS1='PROMPT>'")
        index = c.expect(["PROMPT>.*PROMPT>$", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            pass
        elif index == 1:
            msg = "The connection to %s closed unexpectedly." % (host)
            try:
                msg = msg + "\n" + c.before + c.match.group() + c.after
            except:
                pass
            raise Exception(msg)
        elif index == 2:
            msg = "Timeout resetting command prompt"
            try:
                msg = msg + "\n" + c.before + c.match.group() + c.after
            except:
                pass
            raise Exception(msg)
        c.sendline ("stty -onlcr;export PS2='';stty -echo;unalias ls")
        index = c.expect (["PROMPT>$", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            pass
        elif index == 1:
            msg = "The connection to %s closed unexpectedly." % (host)
            try:
                msg = msg + "\n" + c.before + c.match.group() + c.after
            except:
                pass
            raise Exception(msg)
        elif index == 2:
            msg = "Timeout resetting command prompt"
            try:
                msg = msg + "\n" + c.before + c.match.group() + c.after
            except:
                pass
            raise Exception(msg)

        logger.info("ssh connected to address %s with user %s established" % (host, user))

        return c


    def connect_oracle(self, server="", port="", user="", password="", database=""):

        import cx_Oracle
        conn_string = "%s/%s@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=%s)(PORT=%s)))(CONNECT_DATA=(SID=%s)))" % (user,
            password, server, port, database)

        tries = 5
        for ii in range(tries):
            try:
                conn = cx_Oracle.connect(conn_string)
                break
            except Exception as e:
                if "ORA-12505" in e and ii < tries:
                    # oracle listener, sleep and retry
                    logger.info("Oracle listener not available. Sleeping and retrying")
                    # incremental backoff
                    wait_time = (ii * 5) + 1
                    time.sleep(wait_time)
                else:
                    msg = "Could not connect to the database. Error message -> %s" % (e)
                    raise Exception(msg)

        conn.autocommit = True
        return conn


    def connect_mssql(self, server="", port="", user="", password="", database=""):

        from pytds import dbapi
        try:
            conn = dbapi.connect(server=server, user=user, password=password, database=database)
        except Exception as e:
            msg = "Could not connect to the database. Error message -> %s" % (e)
            raise Exception(msg)
        return conn


    def connect_sqlany(self, server="", port="", user="", password="", database=""):

        import sqlanydb
        try:
            conn = sqlanydb.connect(UID=user, PWD=password, HOST=server, DBN=database)
        except Exception as e:
            msg = "Could not connect to the database. Error message -> %s" % (e)
            raise Exception(msg)
        return conn


    def connect_mysql(self, server="", port="", user="", password="", database=""):

        newdb = catodb.Db()
        try:
            newdb.connect_db(server=server, port=port,
                user=user, password=password, database=database)
        except Exception as e:
            msg = "Could not connect to the database. Error message -> %s" % (e)
            raise Exception(msg)
        return newdb

    def get_xml_val(self, xml, path, index=0):

        root = ET.fromstring(xml)
        nodes = root.findall(path)
        if nodes:
            try:
                node = nodes[index]
            except IndexError:
                v = ""
            else:
                if len(list(node)):
                    v = ET.tostring(node)
                else:
                    v = node.text
        else:
            v = ""
        del(root)
        return v

    def get_xml_by_path(self, xml, path):

        if "," in path:
            comma = path.find(",")
            orig_path = path
            path = orig_path[:comma]
            index = int(orig_path[comma + 1:]) - 1
        else:
            index = 0

        return self.get_xml_val(xml, path, index)


    def get_xml_count(self, xml, node_name):

        root = ET.fromstring(xml)
        nodes = root.findall(node_name)
        if nodes:
            count = len(nodes)
        else:
            count = 0
        del(root)
        return count
        

    def get_node_list(self, xml, node_name, *args):

        return_list = []
        root = ET.fromstring(xml)
        node_name = "./" + node_name
        nodes = root.findall(node_name)

        for node in nodes:
            part_list = []
            for subnode in args:
                logger.debug(subnode)
                subnode = "./" + subnode
                part_list.append(node.findtext(subnode, ""))
            return_list.append(part_list)
        del(root)
        return return_list

    def get_command_params(self, xml, *args):

        return_list = []
        root = ET.fromstring(xml)
        for node in args:
            node = "./" + node
            logger.debug(node)
            return_list.append(root.findtext(node, ""))
        del(root)
        return return_list

    def exists_cmd(self, command):
        
        all_true = True
        root = ET.fromstring(command)
        variables = root.findall("./variables/variable")
        for v in variables:
            variable_name = v.findtext("name", "").upper()
            is_true = v.findtext("is_true", "")
            logger.debug("checking if %s exists ..." % (variable_name))
            
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
        logger.debug("all_true = %s" % (all_true))

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
        return action_xml
    
    def new_uuid(self):

        return str(uuid.uuid4())
    
    def insert_audit(self, command, log, conn=""):

            at = self.audit_trail_on
            step_id = self.current_step_id
            if at > 0:
                if step_id == "":
                    step_id = "NULL"

                sql = """insert into task_instance_log (task_instance, step_id, entered_dt, connection_name,  
                    log, command_text) values (%s,%s, now(),%s,%s,%s)"""
                self.db.exec_db(sql, (self.task_instance, step_id, conn, log, command))

                logger.info(log)
            if at == 1:
                self.audit_trail_on = 0


    def task_conn_log(self, address, userid, conn_type):
        
        logger.info("Registering connection in task conn log")
        sql = """insert into task_conn_log (task_instance, address, userid, conn_type, conn_dt) values (%s,%s,%s,%s,now())"""
        self.db.exec_db(sql, (self.task_instance, address, userid, conn_type))

    def get_cloud_name(self, cloud_id):

        sql = """select cloud_name from clouds where cloud_id = %s"""
        row = self.db.select_row(sql, (cloud_id))
        if row:
            return row[0]
        else:
            return ""

    def get_default_cloud_for_account(self, account_id):

        sql = """select ca.default_cloud_id from cloud_account ca 
            where ca.account_id = %s"""
        row = self.db.select_row(sql, (account_id))
        if row:
            return row[0]

    def clear_variable_cmd(self, step):

        variables = self.get_node_list(step.command, "variables/variable", "name")
        for var in variables:
            self.rt.clear(var[0])


    def set_variable_cmd(self, step):

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
            logger.info("v name is %s, value is %s" % (name, value))

            if modifier == "Math":
                value = self.math.eval_expr(value)
            elif modifier == "TO_UPPER":
                value = value.upper()
            elif modifier == "TO_LOWER":
                value = value.lower()
            elif modifier == "TO_BASE64":
                value = base64.b64encode(value)
            elif modifier == "TO_BASE64_UTF16":
                value = base64.b64encode(value.encode("utf-16"))
            elif modifier == "FROM_BASE64":
                value = base64.b64decode(value)
            elif modifier == "Write JSON":
                pass  # TODO
            elif modifier == "Read JSON":
                pass  # TODO

            self.rt.set(name, value, index)

        
    def process_list_buffer(self, buff, variables):
        for v in variables:
            self.rt.clear(v[0])
  
        for ii, row in enumerate(buff):
            for v in variables:
                name = v[0]
                index = int(v[1]) - 1
                t_index = ii + 1
                logger.debug("%s, %s, %s, %s" % (name, index, t_index, row))
                self.rt.set(name, row[index], t_index)
            
    def get_step_object(self, step_id, step_xml):

        root = ET.fromstring(step_xml)
        function_name = root.attrib.get("name")
        parse_method = root.attrib.get("parse_method")
        row_del = root.attrib.get("row_delimiter")
        col_del = root.attrib.get("col_delimiter")
        del(root)
        return Step(step_id, function_name, step_xml, parse_method, row_del, col_del)

    def subtask_cmd(self, command):
        subtask_name, subtask_version = self.get_command_params(command, "task_name", "version")[:]

        logger.debug("subtask [%s] version [%s]" % (subtask_name, subtask_version))
        if len(subtask_version):
            sql = """select task_id from task where task_name = %s and version = %s"""
            row = self.db.select_row(sql, (subtask_name, subtask_version))
        else:
            sql = """select task_id from task where task_name = %s and default_version = 1"""
            row = self.db.select_row(sql, (subtask_name))

        task_id = row[0]

        self.process_task(task_id)

    def codeblock_cmd(self, task, command):
        name = self.get_command_params(command, "codeblock")[0]
        self.process_codeblock(task, name.upper())
    
    def break_loop_cmd(self, step):
        
        self.insert_audit("break_loop", "Breaking out of loop.", "")
        self.loop_break = True

    
    def replace_vars(self, s):


        # TODO - csk_crypt replacement
        # TODO - datastore variable replacement
        # TODO - json or dictionary replacement or parser

        while re.search(".*\[\[.*\]\]", s):

            # print "before ->" + s
            found_var = self.find_var(s)
            # print "before ->" + s
            if found_var:
                # we found a variable to replace 
                if found_var.startswith("_"):
                    # it's a global variable, look it up
                    value = self.sub_global(found_var)
                elif found_var.startswith("@"):
                    # this is a datastore variable
                    # TODO
                    value = ""
                elif found_var.startswith("#"):
                    # this is a task handle variable
                    value = self.get_handle_var(found_var)
                elif "." in found_var:
                    # this is an xpath query
                    period = found_var.find(".")
                    new_found_var = found_var[:period]
                    xpath = found_var[period + 1:]
                    # print xpath
                    xml = self.rt.get(new_found_var)
                    # print xml
                    if len(xml):
                        value = self.aws_get_result_var(xml, xpath)
                    else:
                        value = ""
                else:
                    # it might be a runtime variable
                    new_found_var = found_var
                    # first test if it has a comma
                    if "," in found_var:
                        # it's got a comma, so it's either an array value or count
                        # we'll determine the index
                        comma = found_var.find(",")
                        new_found_var = found_var[:comma]
                        index = found_var[comma + 1:]
                        if index == "*":
                            # we want the array count, set that as the value and move on
                            value = self.rt.count(new_found_var)
                        else:
                            # not a count, so set value based on var name and index
                            value = self.rt.get(new_found_var, int(index))
                    else:
                        # no index, set the value based on var name
                        value = self.rt.get(new_found_var)

                # now we substitute the variable with the value in the original string
                sub_string = "[[" + found_var + "]]"
                # print "sub_string = " + sub_string + " value = " + str(value)
                s = s.replace(sub_string, str(value))
            # print "after ->" + s
        return s

    def find_var(self, s):

        z = None
        if re.search(".*\[\[.*\]\]", s):

            fst = s.find("[[")
            if fst > -1:
                nxt = s.find("]]", fst)
                if nxt > -1:
                    z = s[fst + 2:nxt]
                    inside = z.rfind("[[")
                    if inside > -1:
                        # print "we have a sub"
                        z = z[inside + 2:]
        return z


    def sub_global(self, s):

        v = ""
        s = s.upper()
        if s == "_TASK_INSTANCE":
            v = self.task_instance
        elif s == "_HOST_ID":
            v = self.host_id
        elif s == "_HOST":
            v = self.host_name
        elif s == "_HOST_ADDRESS":
            v = self.host_address
        elif s == "_INSTANCE_ID":
            v = self.instance_id if hasattr(self, "instance_id") else ""
        elif s == "_INSTANCE_NAME":
            v = self.instance_name if hasattr(self, "instance_name") else ""
        elif s == "_SERVICE_ID":
            v = self.service_id if hasattr(self, "service_id") else ""
        elif s == "_SERVICE_NAME":
            v = self.service_name if hasattr(self, "service_name") else ""
        elif s == "_SERVICE_DOCID":
            v = self.service_docid if hasattr(self, "service_docid") else ""
        elif s == "_DEPLOYMENT_ID":
            v = self.deployment_id if hasattr(self, "deployment_id") else ""
        elif s == "_DEPLOYMENT_NAME":
            v = self.deployment_name if hasattr(self, "deployment_name") else ""
        elif s == "_DEPLOYMENT_DOCID":
            v = self.deployment_docid if hasattr(self, "deployment_docid") else ""
        elif s == "_UUID":
            v = self.new_uuid()
        elif s == "_UUID2":
            v = self.new_uuid().replace("-", "")
        elif s == "_CLOUD_NAME":
            v = self.cloud_name
        elif s == "_CLOUD_LOGIN_PASS":
            v = self.cloud_login_password
        elif s == "_CLOUD_LOGIN_ID":
            v = self.cloud_login_id
        elif s == "_TASK_NAME":
            v = self.task_name
        elif s == "_TASK_VERSION":
            v = self.task_version
        elif s == "_SUBMITTED_BY_EMAIL":
            v = self.submitted_by_email
        elif s == "_SUBMITTED_BY":
            v = self.submitted_by_user
        elif s == "_HTTP_RESPONSE":
            v = self.http_response
        elif s == "_ASSET":
            v = self.system_id
        elif s == "_PUBLIC_IP":
            # TODO
            v = ""
        elif s == "_PRIVATE_IP":
            # TODO
            v = ""
        elif s == "_DATE":
            # TODO
            v = ""
        else:
            v = ""

        return v


    def replace_variables(self, s):

        while re.search(".*\[\[.*\]\]", s):
            s = self.replace_vars(s)
        
        return s

    def replace_html_chars(self, s):

        s = re.sub("&amp;", "&", s)
        s = re.sub("&gt;", ">", s)
        s = re.sub("&lt;", "<", s)
        return s

    def for_loop(self, task, step_id, command):

        initial, counter_v_name, loop_test, orig_compare_to, increment, max_iter = self.get_command_params(command,
            "start", "counter", "test", "compare_to", "increment", "max")[:]
        root = ET.fromstring(command)
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

            logger.debug("initial is %s" % initial),
            logger.debug("counter_v_name is %s" % counter_v_name),
            logger.debug("loop_test is %s" % loop_test),
            logger.debug("orig_compare_to is %s" % orig_compare_to),
            logger.debug("actual compare_to is %s" % compare_to),
            logger.debug("increment is %s" % increment),
            logger.debug("max_iter is %s" % max_iter),


            self.rt.set(counter_v_name, initial)
            counter = initial

            # this part of the test is fixed, such as "<= 10"
            test_part = "%s %s" % (loop_test, compare_to)

            test = "%s %s" % (initial, test_part)
            logger.debug(test)
            sub_step = self.get_step_object(step_id, action_xml)
            logger.debug("counter is %s" % counter)
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
                logger.debug("counter is %s" % counter)
                counter = counter + increment
                logger.debug("counter is %s" % counter)
                test = "%s %s" % (counter, test_part)
                self.rt.set(counter_v_name, counter)
                logger.debug(test)
                loop_num += 1

    def if_cmd(self, task, step_id, command):

        root = ET.fromstring(command)
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
            sub_step = self.get_step_object(step_id, action_xml)
            self.process_step(task, sub_step)
            del(sub_step)
        del(root)

    def substring_cmd(self, step):

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

        logger.info("end is {%s}" % (end))
        s = source[start:end]
        
        msg = "Substring set variable %s to {%s}" % (v_name, s)
        self.insert_audit("substring", msg, "")
        self.rt.set(v_name, s)

    def send_email_cmd(self, step):

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


    def http_cmd(self, step):

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
        except Exception:
            raise Exception("generic exception: " + traceback.format_exc())

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


    def process_buffer(self, buff, step):

        row_count = 1
        if step.row_delimiter:
            r_del = self.tochar(step.row_delimiter)
            buff = buff.split(r_del)
            row_count = len(buff)

        variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
            "range_begin", "prefix", "range_end", "suffix", "regex")

        for ii in range(row_count):

            if step.row_delimiter:
                line = buff[ii]
            else: 
                line = buff

            for v in variables:

                value = ""
                name = v[0]
                typ = v[1]

                if ii == 0:
                    self.rt.clear(name)

                if typ == "delimited":
                    c_pos = int(v[2]) - 1
                    logger.debug("col delim = " + step.col_delimiter)
                    c_del = self.tochar(step.col_delimiter)
                    logger.debug(">>>" + c_del + "<<<<")
                    logger.debug(line.split(c_del))
                    try:
                        value = line.split(c_del)[c_pos]
                    except IndexError:
                        pass
                elif typ == "range":
                    range_begin = v[3]
                    prefix = v[4]
                    range_end = v[5]
                    suffix = v[6]

                    # range (aka position) can either accept a prefix / suffix string or range
                    # begin / end or a combination of the two. 
                    # with range numbers, the 1 is the start index, not 0
                    # the word "end" can be used to get all the way to the end 
                    # of the string.
                    
                    if not len(range_begin):  # we are using a prefix to find the start
                        begin = line.find(prefix)
                        if begin == -1:
                            self.rt.set(name, value, ii + 1)
                            continue
                        else:
                            begin += 1
                    else:  # we are using a number index to find the start
                        begin = int(range_begin) - 1
                    if not len(range_end):  # we are using a suffix to find the end
                        end = line.find(suffix, begin + 1)
                        if end == -1:
                            self.rt.set(name, value, ii + 1)
                            continue
                    else:  # we are using a number index to find the end
                        try:
                            # convert range_end to an int
                            end = int(range_end)
                        except ValueError:
                            # conversion didn't work, must be some sort of reserved word like end
                            # supported range_end values: end, end-1, end-2, etc.
                            if "end" != range_end[0:3]:
                                msg = "The end position %s must either be an integer or start with the word 'end'" % (range_end)
                                raise Exception(msg)
                            elif "end" == range_end:
                                # go all the way to the end of the string
                                end = None
                            else:
                                # this should be a end minus some integer
                                end = int(range_end[3:])

                    value = line[begin:end]
                             
                elif typ == "regex":
                    pattern = v[7]
                    match = re.search(pattern, line)
                    if not match:
                        value = ""
                    else:
                        value = match.group()
                elif typ == "xpath":
                    # TODO
                    pass

                self.rt.set(name, value, ii + 1)


    def parse_text_cmd(self, step):

        buff = self.get_command_params(step.command, "text")[0]
        buff = self.replace_variables(buff)
        log = "parse_text %s" % (buff)
        self.insert_audit("parse_text", log)
        variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
            "range_begin", "prefix", "range_end", "suffix", "regex")
        if len(variables):
            # print variables
            self.process_buffer(buff, step)

    def end_task_cmd(self, step):

        message, status = self.get_command_params(step.command, "message", "status")[:]
        message = self.replace_variables(message)
        msg = "Ending task with a status of %s, message:\n%s" % (status, message)
        self.insert_audit("end_task", msg, "")
        if status == "Error":
            raise Exception("Erroring task with message:\n%s" % (message))
        self.release_all()
        self.update_status(status)
        exit()


    def add_summary_item_cmd(self, step):

        name, detail = self.get_command_params(step.command, "name", "detail")[:]
        name = self.replace_variables(name)
        detail = self.replace_variables(detail)

        if len(name) == 0:
            raise Exception("Add Summary Item error, Item Name required.")
        msg = "<item><name>%s</name><detail>%s</detail></item>" % (name, detail)

        self.summary = "%s%s" % (self.summary, msg)

    def set_debug_level_cmd(self, step):

        dl = self.get_command_params(step.command, "debug_level")[0]
        dl = self.replace_variables(dl)
        logger.info("Setting the debug level to [%s]" % dl)
        
        # this actually changes the debug level of the logger
        catolog.set_debug(dl)
        
        # this resets the variable, which is used for run_task, etc
        self.debug_level = int(dl)
        

    def retrieve_private_key(self, keyname, cloud):

        sql = """select private_key, passphrase from clouds_keypair ck, clouds c 
            where c.cloud_name = %s and ck.keypair_name = %s and c.cloud_id = ck.cloud_id"""
        row = self.db.select_row(sql, (cloud, keyname))
        return row

    def store_private_key_cmd(self, step):

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


    def get_handle_var(self, var):

        # a handle var starts with #, strip it
        var = var[1:].lower()
        split_var = var.split(".")
        handle = split_var[0]
        prop = split_var[1]
        value = ""
        try:
            h = self.task_handles[handle]
            self.refresh_handle(h)
            value = getattr(h, prop)
        except:
            pass
        return value
        

    def get_instance_handle_cmd(self, step):
    
        ti, handle = self.get_command_params(step.command, "instance", "handle")[:]
        ti = self.replace_variables(ti)
        handle = self.replace_variables(handle)

        try:
            h = self.task_handles[handle]
        except KeyError as ex:
            h = TaskHandle()
            self.task_handles[handle] = h

        if h.instance is None:
            # new task handle, set the ti and refresh it
            h.instance = ti
        elif h.instance != ti:
            # unfortunately, the task handle ti doesn't match
            # however, we will get rid of the previous handle and refresh the new one
            del(h)
            h = TaskHandle()
            self.task_handles[handle] = h
            h.instance = ti
            
        self.refresh_handle(h)
        

    def lookup_shared_cred(self, cred):

        sql = "select username, password from asset_credential where credential_name = %s"
        row = self.db.select_row(sql, (cred))
        if row:
            return row
        else:
            return None


    def connect_winrm(self, server, port, user, password, protocol):

        if not port:
            port = "5985"

        if not protocol:
            protocol = "http"

        if protocol not in ["http", "https"]:
            msg = "Connection to winrm endpoint required either https or http protocol. %s is invalid protocol" % (protocol)
            raise Exception(msg)
        
        if protocol == "http":
            transport = "plaintext"
        else:
            transport = "ssl"

        address = "%s://%s:%s/wsman" % (protocol, server, port)
        import winrm
        from winrm import winrm_service
        # TODO - allow the user to specify a transport of kerberos, and also test this
        # depends on ubuntu: sudo apt-get install libkrb5-dev; sudo pip install kerberos
        
        conn = winrm_service.WinRMWebService(endpoint=address, transport=transport, username=user, password=password)
        return conn


    def get_winrm_shell(self, conn):

        s = None
        reattempt = True
        attempt = 1
        while reattempt is True:
            try: 
                s = conn.open_shell()
                reattempt = False
            except Exception as e:
                if ("Operation timed out" in str(e) or "No route to host" in str(e)) and attempt < 11:
                    log_msg = "winrm connection address unreachable on attempt %d. Sleeping and reattempting" % (attempt)
                    self.insert_audit("new_connection", log_msg, "")
                    time.sleep(20)
                    attempt += 1
                else:
                    msg = "winrm connection failed with error %s" % (e)
                    raise Exception(msg)
                    
        return s


    def winrm_cmd(self, step):
        
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

        logger.info(cmd)
        command_id = c.handle.run_command(c.shell_id, cmd)
        buff, err, return_code = c.handle.get_command_output(c.shell_id, command_id)
        if return_code > 0:
            # return code of > 0 seems to be a winrm error. bad
            logger.info(buff)
            raise Exception(err)
        elif return_code == -1:
            # return code of -1 seems to be an error from the command line
            # we will pass this on to the task to figure out what to do with
            if len(buff):
                buff = "%s\n%s" % (buff, err)
            else:
                buff = err

        c.handle.cleanup_command(c.shell_id, command_id)

        logger.info(buff)
        logger.info(err)
        logger.info(return_code)
        
        msg = "%s\n%s" % (cmd, buff)
        self.insert_audit("winrm_cmd", msg)
        variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
            "range_begin", "prefix", "range_end", "suffix", "regex")
        if len(variables):
            self.process_buffer(buff, step)

        

    def wait_for_tasks_cmd(self, step):

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

    
    def run_task_cmd(self, step):

        params = self.get_command_params(step.command, "task_name", "version", "handle", "asset_id", "time_to_wait", "parameters")
        task_name = params[0]
        version = params[1]
        handle = params[2].lower()
        asset_id = self.replace_variables(params[3])
        wait_time = self.replace_variables(params[4])
        parameters = self.replace_variables(params[5])

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
            
        sql = """select task_id, version, default_version, now() from task where task_name = %s"""
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
            submitted_dt = row[3]
        else:
            msg = "Run Task - Task [%s] version [%s] does not exist." % (task_name, version)
            raise Exception(msg)

        ti = catocommon.add_task_instance(task_id=task_id, user_id=self.submitted_by, debug_level=self.debug_level,
            parameter_xml=parameters, scope_id=self.instance_id, account_id=self.cloud_account,
            schedule_instance=self.schedule_instance, submitted_by_instance=self.task_instance,
            cloud_id=self.cloud_id) 

        h = TaskHandle()
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


    def refresh_handle(self, h):

        ti = h.instance
        sql = """select ti.task_status, ti.started_dt, ti.completed_dt, ti.ce_node, ti.pid, 
            a.asset_id, a.asset_name, ti.task_id, t.task_name, ti.submitted_by, t.version, 
            t.default_version, ti.submitted_dt
            from task_instance ti 
            join task t on ti.task_id = t.task_id 
            left outer join asset a on a.asset_id = ti.asset_id 
            where ti.task_instance = %s"""
        row = self.db.select_row(sql, (ti))
    
        if row:
            h.status = row[0]
            h.started_dt = row[1]
            h.completed_dt = row[2]
            h.cenode = row[3]
            h.pid = row[4]
            h.asset = row[5]
            h.asset_name = row[6]
            h.task_id = row[7]
            h.task_name = row[8]
            h.submitted_by = row[9]
            h.task_version = row[10]
            h.is_default = row[11]
            h.submitted_dt = row[12]
            logger.info("Handle %s refreshed ..." % (h.handle_name))

    def get_task_status(self, ti):

        sql = "select task_status from task_instance where task_instance = %s"
        row = self.db.select_row(sql, (ti))
        if row:
            status = row[0]
        else:
            status = False
        return status


    def get_system_id_from_name(self, asset_name):

        sql = """select asset_id from asset where asset_name = %s"""
        row = self.db.select_row(sql, (asset_name))
        if row:
            return row[0]
        else:
            msg = "The asset named %s does not exist in the database" % (asset_name)
            raise Exception(msg)
            return None
        
    def gather_system_info(self, asset_id):

        sql = """select a.asset_name, a.address, a.port, a.db_name , a.connection_type, 
            ac.username, ac.password, ac.domain, ac.privileged_password, a.conn_string 
            from asset a left outer join asset_credential ac on a.credential_id = ac.credential_id
            where asset_id = %s"""
        row = self.db.select_row(sql, (asset_id))
        if row:
            # print row
            password = row[6]
            p_password = row[8]

            if password and len(password) > 0:
                password = catocommon.cato_decrypt(password)
            else:
                password = ""
            if p_password and len(password) > 0:
                p_password = catocommon.cato_decrypt(p_password)
            else:
                p_password = ""

            s = System(row[0], address=row[1], port=row[2], db_name=row[3], conn_type=row[4], userid=row[5],
                password=password, p_password=p_password, domain=row[7], conn_string=row[9])

            self.systems[asset_id] = s

        else:
            msg = "The asset id %s does not exist in the database" % (asset_id)
            raise Exception(msg)
        return s

    def log_msg_cmd(self, step):

        msg = self.get_command_params(step.command, "message")[0]
        msg = self.replace_variables(msg)
        self.insert_audit("log_msg", msg, "")

    def tochar(self, num):

        i = unichr(int(num))

        return str(i)


    def aws_get_result_var(self, result, path):

        if path.startswith("count(") and path.endswith(")"):
            path = "." + path[6:-1]
            # print "result is " + result
            # print "path is " + path
            # print self.get_xml_count(result, path)
            value = self.get_xml_count(result, path)
        else:
            path = "." + path
            value = self.get_xml_by_path(result, path)
            # value = self.get_command_params(result, path)[0]
        return value 


    def get_aws_system_info(self, instance_id, user_id, region):

        # number of times to retry checking the status of the instance
        num_retries = 20
        state = ""
        # if cloud name is not specified as a parameter, get the cloud account default
        if not len(region):
            region = self.cloud_name

        ok_flag = False
        params = []
        params.append(("InstanceId", instance_id))
        for ii in range(1, num_retries):
            try:
                result = self.call_aws(region, "ec2", "DescribeInstances", params)
                state = self.aws_get_result_var(result, "//instancesSet/item/instanceState/name")
                if state == "running":
                    ok_flag = True
                    break
                elif state == "pending":
                    msg = "Instance id %s state is pending, sleeping and retrying" % (instance_id)
                    logger.info(msg)
                    time.sleep(10)
                else:
                    msg = "Instance id %s state is neither running or pending, state found is %s, cannot connect" % (instance_id, state)
                    raise Exception(msg)
            except Exception as ex:
                if ii == num_retries:
                    msg = "DescribeInstances returned -> %s, exiting" % (ex)
                    logger.info(msg)
                else:
                    msg = "DescribeInstances returned -> %s, sleeping and retrying" % (ex)
                    logger.info(msg)
                    time.sleep(10)

        # we got here, so we either timed out or sucessfully retrieved a running instance
        if not ok_flag: 
            msg = "AWS Error - DescribeInstances for instance id %s in region %s failed" % (instance_id, region)
            if state == "pending":
                msg = msg + ", state stuck in a pending status"
            raise Exception(msg)

        keyname = self.aws_get_result_var(result, "//instancesSet/item/keyName")
        platform = self.aws_get_result_var(result, "//instancesSet/item/platform")
        address = self.aws_get_result_var(result, "//instancesSet/item/dnsName")
        if not len(platform):
            platform = "linux"
        pk = self.retrieve_private_key(keyname, region)
        if not pk:
            msg = "The key named %s for cloud %s is not defined in the database" % (keyname, region)
            raise Exception(msg)
        p_key = catocommon.cato_decrypt(pk[0])
        password = catocommon.cato_decrypt(pk[1])
        del(pk)

        s = System(instance_id, address=address, userid=user_id, password=password,
            private_key=p_key, private_key_name=keyname, cloud_name=region)

        self.systems[instance_id] = s

        return s


    def aws_drill_in(self, node, name, params, node_names):

        if len(node):
            # if len is greater than 0, this is an array
            for child in node:
                if name in node_names.keys():
                    node_names[name] += 1
                else:
                    node_names[name] = 1
                level_string = ".%s" % (str(node_names[name]))
                node_name = re.sub("\\.n$|\\.m$|\\.N$|\\.X$", level_string, name)
                if node_name == name:
                    node_name = name + "." + child.tag
                params = self.aws_drill_in(child, node_name, params, node_names)
        elif node.text:
            # get the value
            value = self.replace_variables(node.text)
            if name == "UserData":
                value = base64.b64encode(value)

            params.append((name, value))
        return params

    def call_aws(self, cloud_name, product, action, params):

        # if cloud name is not specified as a parameter, get the cloud account default
        if not len(cloud_name):
            cloud_name = self.cloud_name
        try:
            cloud = self.cloud_conns[cloud_name]
        except KeyError as ex:
            cloud = Cloud(cloud_name)
            self.cloud_conns[cloud_name] = cloud
        
        # this is a hack for the ncsu load balancer service
        if product == "elb" and cloud.provider == "Eucalyptus":
            path = "/"
        else:
            path = cloud.path

        conn = awspy.AWSConn(self.cloud_login_id, self.cloud_login_password, region=cloud_name, product=product,
            endpoint=cloud.url, path=path, protocol=cloud.protocol, timeout=None)
        result = conn.aws_query(action, params)
        del(conn)
        if result:
            result = self._xml_del_namespace(result)
        return result

    def aws_cmd(self, step):

        cloud_name, result_var = self.get_command_params(step.command, "aws_region", "result_name")[:]
        cloud_name = self.replace_variables(cloud_name)

        product, action = step.function_name.split("_")[1:]
        nodes = ET.fromstring(step.command)
        params = []
        node_names = {}
        for node in nodes:
            if node.tag not in ["result_name", "aws_region", "instance_role"]:
                params = self.aws_drill_in(node, node.tag, params, node_names)
        del(nodes)

        result = self.call_aws(cloud_name, product, action, params)

        msg = "%s %s" % (step.function_name, params)
        if result:
            msg = msg + "\n" + result
            self.rt.set(result_var, result)
        self.insert_audit("aws_cmd", msg, "")

    def sleep_cmd(self, step):

        seconds = self.get_command_params(step.command, "seconds")[0]
        seconds = self.replace_variables(seconds)
        try:
            seconds = int(seconds)
        except ValueError:
            raise Exception("Sleep command requires seconds as an integer value. seconds = %s" % (seconds))

        msg = "Sleeping {%s} seconds..." % (seconds)
        self.insert_audit("sleep", msg, "")
        time.sleep(seconds)

    def while_loop(self, task, step_id, command):

        orig_test = self.get_command_params(command, "test")[0]
        root = ET.fromstring(command)
        action = root.findall("./action/function")
        if action:
            action_xml = ET.tostring(action[0])
        else:
            action_xml = False
        del(root)

        if action_xml:
            sub_step = self.get_step_object(step_id, action_xml)

            orig_test = self.replace_html_chars(orig_test)
            test = self.replace_variables(orig_test)
            sub_step = self.get_step_object(step_id, action_xml)
            dummy = {}
            while eval(test, dummy, dummy):
                if self.loop_break:
                    self.loop_break = False
                    break
                self.process_step(task, sub_step)
                test = self.replace_variables(orig_test)
                logger.debug(test) 

            del(sub_step)

    def process_step(self, task, step):
        msg = """
        **************************************************************
        **** PROCESSING STEP %s ****
        **************************************************************
        """ % step.step_id
        logger.info(msg)
        logger.info("function name is %s" % (step.function_name))

        self.current_step_id = step.step_id
        f = step.function_name

        if f == "exists":
            result = self.exists_cmd(step.command)
            if result:
                sub_step = self.get_step_object(step.step_id, result)
                self.process_step(task, sub_step) 
                del(sub_step)
        elif f == "while":
            self.while_loop(task, step.step_id, step.command)
        elif f == "loop":
            self.for_loop(task, step.step_id, step.command)
        elif f == "if":
            self.if_cmd(task, step.step_id, step.command)
        elif f == "codeblock":
            self.codeblock_cmd(task, step.command)
        elif f == "subtask":
            self.subtask_cmd(step.command)
        elif f == "log_msg":
            self.log_msg_cmd(step)
        elif f == "run_task":
            self.run_task_cmd(step)
        elif f == "sql_exec":
            self.sql_exec_cmd(step)
        elif f == "store_private_key":
            self.store_private_key_cmd(step)
        # elif f == "r53_dns_change":
        #    self.tcl.eval('r53_dns_change {%s}' % step.command)
        elif f == "set_variable":
            self.set_variable_cmd(step)
        elif f == "comment":
            # do nothing here
            logger.info("skipping comment")
        # elif f == "transfer":
        #    self.tcl.eval('transfer {%s}' % step.command)
        elif f == "cancel_task":
            self.cancel_tasks_cmd(step)
        elif f == "wait_for_tasks":
            self.wait_for_tasks_cmd(step)
        elif f == "substring":
            self.substring_cmd(step)
        elif f == "drop_connection":
            self.drop_connection_cmd(step)
        elif f == "end":
            self.end_task_cmd(step)
        elif f == "new_connection":
            self.new_connection_cmd(step)
        elif f == "send_email":
            self.send_email_cmd(step)
        elif f == "get_instance_handle":
            self.get_instance_handle_cmd(step)
        elif f == "add_summary_item":
            self.add_summary_item_cmd(step)
        elif f == "clear_variable":
            self.clear_variable_cmd(step)
        elif f == "sleep":
            self.sleep_cmd(step)
        elif f == "set_debug_level":
            self.set_debug_level_cmd(step)
        elif f == "break_loop":
            self.break_loop_cmd(step)
        elif f == "http":
            self.http_cmd(step)
        elif f == "parse_text":
            self.parse_text_cmd(step)
        elif f == "winrm_cmd":
            self.winrm_cmd(step)
        elif f == "cmd_line":
            self.cmd_line_cmd(step)
        elif f.startswith('aws_'):
            self.aws_cmd(step)
        else:
            self.process_extension(f, step)
        
    def process_extension(self, name, step):
        """
        
        This command will attempt to load an extension module, in the 
        path defined by "extension", assuming the function name is the, um, function name.
        
        NOTE: we did something *similar* in startup(), but we didn't load every single module.
        There, we just loaded and ran the "augment" function, which modified the TE class instance
        with extension-wide features.
        
        Here we're going after a specific function.
        
        """
        root = ET.fromstring(step.command)
        extension = root.attrib.get("extension")
        if not extension:
            logger.error("Unable to get 'extension' property from extension command xml.")
            return ""
        
        logger.info("loading extension [%s] ..." % extension)
        try:
            mod = importlib.import_module(extension)
        except ImportError as ex:
            logger.error(ex.__str__())
            return "Extension module [%s] does not exist." % extension

        # evidently the module exists... try to call the function
        method_to_call = getattr(mod, name, None)

        if method_to_call:
            if callable(method_to_call):
                # we pass a pointer to the TaskEngine instance itself, so the extension code has access to everything!
                # also pass in the logger, since it's global and not a TE property
                return method_to_call(self, step, logger)
            else:
                logger.error("Extension found, method [%s] found, but not callable." % name)
        else:
            logger.error("Extension found, but method [%s] not found." % name)
        
    def process_codeblock(self, task, codeblock_name):

        logger.info("##### Processing Codeblock %s" % (codeblock_name))
        for step in task.codeblocks[codeblock_name].step_list:
            self.process_step(task, step)

    def process_task(self, task_id):

        try:
            task = self.tasks[task_id]
        except KeyError as ex:
            task = Task(task_id)
            self.tasks[task_id] = task

        self.process_codeblock(task, "MAIN")
            
    def get_task_instance(self):

        sql = """select B.task_name, A.asset_id, 
                C.asset_name, A.submitted_by, 
                B.task_id, B.version, A.debug_level, A.schedule_instance,
                A.ecosystem_id, A.account_id, A.cloud_id
            from task_instance A 
            join task B on A.task_id = B.task_id
            left outer join asset C on A.asset_id = C.asset_id
            where  A.task_instance = %s"""

        row = self.db.select_row(sql, (self.task_instance))

        if row:
            self.task_name, self.system_id, self.system_name, self.submitted_by, self.task_id, \
                self.task_version, self.debug_level, self.schedule_instance, self.instance_id, \
                self.cloud_account, self.cloud_id = row[:]

        if self.submitted_by:
            sql = """select username, email from users where user_id = %s"""
            row = self.db.select_row(sql, (self.submitted_by))
            if row:
                self.submitted_by_user, self.submitted_by_email = row[:]
            
            return 1
        else:
            return -1

    def gather_account_info(self, account_id):

        sql = """select ca.provider, ca.login_id, ca.login_password from cloud_account ca 
            where ca.account_id= %s"""
        row = self.db.select_row(sql, (account_id))
        if row:
            self.provider, self.cloud_login_id, password = row[:]
            self.cloud_login_password = catocommon.cato_decrypt(password)


    def release_all(self):

        logger.info("Releasing all connections")
        for c in self.connections.keys():
            self.drop_connection(c)
            
    def drop_connection_cmd(self, step):

        conn_name = self.get_command_params(step.command, "conn_name")[0]
        conn_name = self.replace_variables(conn_name)
        if conn_name in self.connections.keys():
            msg = "Dropping connection named %s" % (conn_name)
            self.insert_audit("drop_connection", msg, "")
            self.drop_connection(conn_name)
            

    def drop_connection(self, conn_name):

        try:
            # get the connection object
            c = self.connections[conn_name]
        except KeyError as ex:
            # well, we have no record of it so move on
            msg = "Connection named %s not found, skipping" % (conn_name)
            logger.info(msg)
        else:
            # wack the connection by type
            if c.conn_type in ["ssh", "telnet", "ssh - ec2"]:
                self.disconnect_expect(c.handle)
            elif c.conn_type == "mysql":
                self.disconnect_mysql(c.handle)
            elif c.conn_type == "sybase":
                pass
            elif c.conn_type == "informix":
                pass
            elif c.conn_type == "winrm":
                try:
                    c.handle.close_shell(c.shell_id)
                except Exception as ex:
                    msg = "%s" % (ex)
                    logger.info(msg)
            elif c.conn_type == "sqlserver":
                self.disconnect_mssql(c.handle)
            elif c.conn_type == "sqlanywhere":
                self.disconnect_sqlany(c.handle)
            elif c.conn_type == "oracle":
                self.disconnect_oracle(c.handle)
            del(c)
            del(self.connections[conn_name])    

    # work in progress, not complete.
    def new_connection_cmd(self, step):

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
            except KeyError as ex:
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
            except KeyError as ex:
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
            except KeyError as ex:
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
                        logger.info(msg)
                
                s = System(name, address=address, userid=userid, password=password,
                    port=port, db_name=db_name, protocol=protocol)

                self.systems[name] = s

        # we've made it this far, let's create the new connection object
        conn = Connection(conn_name, conn_type=conn_type, system=s)
        self.connections[conn_name] = conn
            
        # and make the connection. We'll store any connection handle we get back for later use
        self.connect_system(conn)

        msg = "New connection named %s to asset %s created with a connection type %s" % (conn_name, s.address, conn_type)
        self.insert_audit("new_connection", msg, "")


    def connect_system(self, c):

        msg = "Going into system %s userid %s with conn type of %s" % (c.system.address, c.system.userid, c.conn_type)
        logger.info(msg)

        if c.conn_type == "ssh":

            # c.handle = self.connect_ssh_telnet("ssh", c.system.address, c.system.userid, password=c.system.password)
            c.handle = self.connect_expect("ssh", c.system.address, c.system.userid, password=c.system.password)

        elif c.conn_type == "telnet":

            # c.handle = self.connect_ssh_telnet("telnet", c.system.address, c.system.userid, password=c.system.password)
            c.handle = self.connect_expect("telnet", c.system.address, c.system.userid, password=c.system.password)
            
        elif c.conn_type == "ssh - ec2":

            # c.handle = self.connect_ssh_telnet("ssh", c.system.address, c.system.userid, 
            #    pk_password=c.system.p_password, key=c.system.private_key)
            c.handle = self.connect_expect("ssh", c.system.address, c.system.userid, password=c.system.password,
                passphrase=c.system.p_password, key=c.system.private_key)
            
        elif c.conn_type == "winrm":

            c.handle = self.connect_winrm(server=c.system.address, port=c.system.port, user=c.system.userid,
                password=c.system.password, protocol=c.system.protocol)

            c.shell_id = self.get_winrm_shell(c.handle)
            
        elif c.conn_type == "mysql":

            if c.system.port:
                port = int(c.system.port)
            else:
                port = 3306
               
            c.handle = self.connect_mysql(server=c.system.address, port=port, user=c.system.userid,
                password=c.system.password, database=c.system.db_name)

        elif c.conn_type == "sybase":
            pass
        elif c.conn_type == "informix":
            pass
        elif c.conn_type == "sqlanywhere":

            if c.system.port:
                port = c.system.port
            else:
                port = "2638"
               
            c.handle = self.connect_sqlany(server=c.system.address, port=port, user=c.system.userid,
                password=c.system.password, database=c.system.db_name)

        elif c.conn_type == "sqlserver":

            if c.system.port:
                port = int(c.system.port)
            else:
                port = 1433
               
            c.handle = self.connect_mssql(server=c.system.address, port=port, user=c.system.userid,
                password=c.system.password, database=c.system.db_name)

        elif c.conn_type == "oracle":
        
            if not c.system.port or c.system.port == "":
                port = "1521"
            else:
                port = c.system.port

            c.handle = self.connect_oracle(server=c.system.address, port=port, user=c.system.userid,
                password=c.system.password, database=c.system.db_name)

        self.task_conn_log(c.system.address, c.system.userid, c.conn_type)
        
    def is_uuid(self, s):

        t = "[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}"
        if re.match(t, s):
            r = True
        else:
            r = False
        return r

    def get_asset_info(self, asset_id):

        try:
            a = self.assets[asset_id]
        except KeyError as ex:
            a = Asset(asset_id)
            self.assets[asset_id] = a


    def get_cloud_connection(self, endpoint_name):

        if endpoint_name == "":
            endpoint_name = self.cloud_name
        try:
            cloud = self.cloud_conns[endpoint_name]
        except KeyError as ex:
            cloud = Cloud(endpoint_name)
            self.cloud_conns[endpoint_name] = cloud
            cloud.connect(self.cloud_login_id, self.cloud_login_password)
   
        return cloud

    def select_all(self, sql, conn=None):

        if not conn:
            conn = self.db
        return conn.select_all(sql)

    def cancel_tasks_cmd(self, step):

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

    def cmd_line_cmd(self, step):    

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

        logger.info("sending %s to the process" % (cmd))
        buff = self.execute_expect(c.handle, cmd, pos, neg, timeout)
        self.insert_audit("cmd_line", "%s\n%s" % (cmd, buff), conn_name)

        variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
            "range_begin", "prefix", "range_end", "suffix", "regex")
        if len(variables):
            # print variables
            self.process_buffer(buff, step)


    def sql_exec_cmd(self, step):
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

        logger.debug("conn type is %s" % (c.conn_type))
        variables = self.get_node_list(step.command, "step_variables/variable", "name", "position")
        if c.conn_type == "mysql":
            self.sql_exec_mysql(sql, variables, c.handle)
        elif c.conn_type in ["sqlanywhere", "sqlserver", "oracle"]:
            self.sql_exec_dbi(sql, variables, c.handle)

    def sql_exec_dbi(self, sql, variables, conn):
   
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
    
    def sql_exec_mysql(self, sql, variables, conn):
   
        rows = self.select_all(sql, conn)
        msg = "%s\n%s" % (sql, rows)
        self.insert_audit("sql_exec", msg, "")
        self.process_list_buffer(rows, variables)
    


    def update_status(self, task_status):

        logger.info("Updating task instance %s to %s" % (self.task_instance, task_status))

        sql = "update task_instance set task_status = %s, completed_dt = now() where task_instance = %s" 
        self.db.exec_db(sql, (task_status, self.task_instance))

    def update_ti_pid(self):

        sql = """update task_instance set pid = %s, task_status = 'Processing', 
            started_dt = now() where task_instance = %s""" 
        self.db.exec_db(sql, (os.getpid(), self.task_instance))

    def parse_input_params(self, params):

        root = ET.fromstring(params)
        nodes = root.findall("./parameter")
        for node in nodes:
            name = node.findtext("name", "")
            v_nodes = node.findall("./values/value")
            ii = 0
            for v_node in v_nodes:
                ii += 1
                self.rt.set(name, v_node.text, ii)
        del(root)


    def get_task_params(self):

        sql = "select parameter_xml from task_instance_parameter where task_instance = %s"
        row = self.db.select_row(sql, (self.task_instance))
        if row:
            self.parse_input_params(row[0])


    def startup(self):
        logger.info("""
#######################################
    Starting up %s
#######################################""" % self.process_name)
        self.db = catodb.Db()
        self.db.connect_db(server=catoconfig.CONFIG["server"], port=catoconfig.CONFIG["port"],
            user=catoconfig.CONFIG["user"],
            password=catoconfig.CONFIG["password"], database=catoconfig.CONFIG["database"])
        self.config = catoconfig.CONFIG


        logger.info("Task Instance: %s - PID: %s" % 
            (self.task_instance, os.getpid()))
        self.update_ti_pid()
        self.get_task_instance()
        self.get_task_params()
        logger.info("Task Name: %s - Version: %s, DEBUG LEVEL: %s, Service Instance id: %s" % 
            (self.task_name, self.task_version, self.debug_level, self.instance_id))


        self.cloud_name = None
        if self.cloud_account:
            self.gather_account_info(self.cloud_account)
        if self.cloud_id:
            self.cloud_name = self.get_cloud_name(self.cloud_id)
        elif self.cloud_account:
            self.cloud_id = self.get_default_cloud_for_account(self.cloud_account)
            self.cloud_name = self.get_cloud_name(self.cloud_id)
            

        logger.info("cloud_account is %s, cloud_name is %s " % (self.cloud_account, self.cloud_name))

        

        # extension paths are defined in config.
        if catoconfig.CONFIG.has_key("extension_path"):
            expath = catoconfig.CONFIG["extension_path"].split(";")
            for p in expath:
                logger.info("Appending extension path [%s]" % p)
                sys.path.append(p)
        
                for root, subdirs, files in os.walk(p):
                    for f in files:
                        if f == "augment_te.py":
                            self.augment("%s.augment_te" % os.path.basename(root))
        

    def augment(self, modname):
        
        logger.info("augmenting from [%s] ..." % modname)
        try:
            mod = importlib.import_module(modname)
        except ImportError as ex:
            raise ex

        # evidently the module exists... try to call the function
        method_to_call = getattr(mod, "__augment__", None)

        if method_to_call:
            if callable(method_to_call):
                # we pass a pointer to the TaskEngine instance itself, so the extension code has access to everything!
                # also pass in the logger, since it's global and not a TE property
                return method_to_call(self, logger)
            else:
                logger.error("augment_te module found, but __augment__ is not callable.")
        else:
            logger.error("augment_te module found, but doesn't contain __augment__()")
        


    def end(self):
        self.db.close()
        

    def run(self):
        try: 
            self.process_task(self.task_id)
            self.update_status('Completed')
            if len(self.summary) > 0:
                msg = "result_summary" "<result_summary><items>%s</items></result_summary>" % (self.summary)
                self.insert_audit("result_summary", msg, "")
            self.release_all()
        except Exception as e:
            msg = "ERROR -> %s" % (e)
            logger.info(msg)
            traceback.print_exc(file=sys.stderr)
            # traceback.print_exc(file=sys.stderr)
            self.insert_audit("", msg, "")
            self.update_status('Error')
            self.release_all()
            raise Exception(msg)
