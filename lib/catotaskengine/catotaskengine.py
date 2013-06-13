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
from jsonpath import jsonpath

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
import uuid
from awspy import awspy
import base64
from matheval import matheval
from . import commands
from . import classes


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

        self.logger = catolog.get_logger(process_name)

        
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
            self.logger.error(traceback.format_exc())
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

        # remove any trailing newline
        return c.before.rstrip("\n")


    def remove_pk(self, kf_name):

        # we successfully logged in, let's get rid of the private key
        try:
            os.remove(kf_name)
        except:
            pass


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
            "No route to host|Permission denied|Network is unreachable|onnection reset by peer|onnection refused|onnection closed by|Read from socket failed|Name or service not known|Connection timed out",
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
                    self.logger.warning("The password for user %s will expire soon! Continuing ..." % (user))
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
                    try: 
                        msg = msg + "\n" + c.before + c.match.group() + c.after
                    except:
                        pass
                    if key:
                        self.remove_pk(kf_name)
                    raise Exception(msg)

        self.remove_pk(kf_name)

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

        self.logger.info("ssh connected to address %s with user %s established" % (host, user))

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
                    self.logger.info("Oracle listener not available. Sleeping and retrying")
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
                # self.logger.debug(subnode)
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
            self.logger.debug("Field: %s" % (node))
            self.logger.debug("Value: %s" % (root.findtext(node, "")))
            return_list.append(root.findtext(node, ""))
        del(root)
        return return_list

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

                self.logger.info(log)
            if at == 1:
                self.audit_trail_on = 0


    def task_conn_log(self, address, userid, conn_type):
        
        self.logger.info("Registering connection in task conn log")
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

    def process_list_buffer(self, buff, variables):
        for v in variables:
            self.rt.clear(v[0])
  
        for ii, row in enumerate(buff):
            for v in variables:
                name = v[0]
                index = int(v[1]) - 1
                t_index = ii + 1
                self.logger.debug("%s, %s, %s, %s" % (name, index, t_index, row))
                self.rt.set(name, row[index], t_index)
            
    def get_step_object(self, step_id, step_xml):

        root = ET.fromstring(step_xml)
        function_name = root.attrib.get("name")
        parse_method = root.attrib.get("parse_method")
        row_del = root.attrib.get("row_delimiter")
        col_del = root.attrib.get("col_delimiter")
        del(root)
        return classes.Step(step_id, function_name, step_xml, parse_method, row_del, col_del)

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
                elif found_var.startswith("$"):
                    # this is an "object" lookup (likely set by Read JSON)
                    index = 1 # in case no index is explicitly set, so we don't need two lookup blocks in if cases below
                    new_found_var = found_var
                    if "," in found_var:
                        # it's got a comma, so it's either an array value or count
                        comma = found_var.find(",")
                        index = found_var[comma + 1:]
                        new_found_var = found_var[:comma]

                    if index == "*":
                        # we want the array count, set that as the value and move on
                        value = self.rt.count(new_found_var)
                    else:
                        # not a count, so set value based on var name and index
                        # if the index is not a valid integer, error
                        try:
                            int_index = int(index)
                        except ValueError:
                            msg = "The array index [%s] for variable [%s] is not a valid integer." % (index, new_found_var)
                            raise Exception(msg)
                        except Exception as ex:
                            raise Exception(ex)

                        parts = new_found_var[1:].split(":", 1)
                        varname = parts[0]
                        keypath = "" if len(parts) == 1 else parts[1]
                        
                        var = self.rt.get(varname, int_index)
                        self.logger.debug("Object variable - variable is [%s]." % (varname))
                        
                        if not keypath:
                            value = var
                        else:
                            self.logger.debug("Object variable - keypath is [%s]." % (keypath))
                             
                            # [[objvar:*]] will return the number of keys INSIDE this object
                            # if the 'keypath' starts with a $, that's a JSONPATH so we'll apply that
                            # otherwise we'll try a simple root level name.
                            if keypath == "*":
                                value = len(var)
                            elif keypath.startswith("$"):
                                value = jsonpath(var, keypath)
                            elif var.has_key(keypath):
                                value = var.get(keypath)
                            else:
                                self.logger.info("Object variable [%s] - key [%s] not found." % (varname, keypath))
                    
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
                            # if the index is not a valid integer, error
                            try:
                                int_index = int(index)
                            except ValueError:
                                msg = "The array index [%s] for variable [%s] is not a valid integer." % (index, new_found_var)
                                raise Exception(msg)
                            except Exception as ex:
                                raise Exception(ex)

                            value = self.rt.get(new_found_var, int_index)
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
        elif s == "_INSTANCE_INDEX":
            v = self.instance_index if hasattr(self, "instance_index") else ""
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
        elif s == "_CLOUD_PROVIDER":
            v = self.provider
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

    def process_buffer(self, buff, step):

        row_count = 1
        if step.row_delimiter:
            r_del = self.tochar(step.row_delimiter)
            buff = buff.split(r_del)
            row_count = len(buff)

        variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
            "range_begin", "prefix", "range_end", "suffix", "regex", "xpath")

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
                    self.logger.debug("col delim = " + step.col_delimiter)
                    c_del = self.tochar(step.col_delimiter)
                    self.logger.debug(">>>" + c_del + "<<<<")
                    self.logger.debug(line.split(c_del))
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
                    xml = line
                    if len(xml):
                        value = self.aws_get_result_var(xml, v[8])
                    else:
                        value = ""

                self.rt.set(name, value, ii + 1)


    def retrieve_private_key(self, keyname, cloud):

        sql = """select private_key, passphrase from clouds_keypair ck, clouds c 
            where c.cloud_name = %s and ck.keypair_name = %s and c.cloud_id = ck.cloud_id"""
        row = self.db.select_row(sql, (cloud, keyname))
        return row

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
            self.logger.info("Unable to find Handle by name [%s]." % (handle))

        return value
        

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
            self.logger.info("Handle %s refreshed ..." % (h.handle_name))

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

            s = classes.System(row[0], address=row[1], port=row[2], db_name=row[3], conn_type=row[4], userid=row[5],
                password=password, p_password=p_password, domain=row[7], conn_string=row[9])

            self.systems[asset_id] = s

        else:
            msg = "The asset id %s does not exist in the database" % (asset_id)
            raise Exception(msg)
        return s

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
                    msg = "Instance id [%s] state is pending. Sleeping and retrying..." % (instance_id)
                    self.insert_audit("", msg, "")
                    time.sleep(10)
                else:
                    msg = "Instance ID [%s] state is neither running or pending, state found is [%s], cannot connect." % (instance_id, state)
                    raise Exception(msg)
            except Exception as ex:
                if ii == num_retries:
                    msg = "DescribeInstances returned -> [%s]. Exiting..." % (ex)
                    self.logger.info(msg)
                else:
                    msg = "DescribeInstances returned -> [%s]. Sleeping and retrying..." % (ex)
                    self.insert_audit("", msg, "")
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

        s = classes.System(instance_id, address=address, userid=user_id, password=password,
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
            cloud = classes.Cloud(cloud_name)
            self.cloud_conns[cloud_name] = cloud
        
        # this is a hack for the ncsu load balancer service
        if product == "elb" and cloud.provider == "Eucalyptus":
            path = "/"
        else:
            path = cloud.path

        conn = awspy.AWSConn(self.cloud_login_id, self.cloud_login_password, region=cloud_name, product=product,
            endpoint=cloud.url, path=path, protocol=cloud.protocol, timeout=None, api_version=cloud.api_version)
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

        num_retries = 5
        result = None
        for ii in range(1, num_retries + 1):
            try:
                result = self.call_aws(cloud_name, product, action, params)
                break
            except Exception as ex:
                if "<Code>InvalidInstanceID.NotFound</Code>" in str(ex) and ii <= num_retries:
                    self.logger.info("Instance ID not found. Sleeping and retrying")
                    time.sleep(ii * 2)
                elif "<Code>ServiceUnavailable</Code>" in str(ex) and ii <= num_retries:
                    self.logger.info("Amazon Service unavailable. Sleeping and retrying")
                    time.sleep(ii * 2)
                else:
                    msg = "%s command %s failed: %s" % (product, action, ex)
                    raise Exception(msg)
                    

        if result:
            msg = "%s %s\n%s" % (step.function_name, params, result)
            self.rt.set(result_var, result)
            self.insert_audit("aws_cmd", msg, "")
        else:
            msg = "%s command %s failed." % (product, action)
            raise Exception(msg)
        

    def process_step(self, task, step):
        msg = """
        **************************************************************
        **** PROCESSING STEP %s ****
        **************************************************************
        """ % step.step_id
        self.logger.info(msg)
        self.logger.info("function name is %s" % (step.function_name))

        self.current_step_id = step.step_id
        f = step.function_name

        # if the commands module has this function defined, use it
        cmdfuncname = "%s_cmd" % f
        if hasattr(commands, cmdfuncname):
            method_to_call = getattr(commands, cmdfuncname, None)
            # we pass a pointer to the TaskEngine instance itself, so the command code has access to everything!
            # also pass in the logger, since it's global and not a TE property
            return method_to_call(self, task, step)

        # it wasn't a built-in command... maybe an aws command or an extension?
        if f.startswith('aws_'):
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
        self.logger.info("[%s] Not a built-in command, checking extensions..." % (name))
        root = ET.fromstring(step.command)
        extension = root.attrib.get("extension")
        del(root)
        if not extension:
            msg = "Unable to get 'extension' property from extension command xml for extension %s" % (name)
            self.logger.error(msg)
            raise Exception(msg)
        
        self.logger.info("loading extension [%s] ..." % (extension))
        try:
            mod = importlib.import_module(extension)
        except ImportError as ex:
            self.logger.error(ex.__str__())
            msg = "Extension module [%s] does not exist." % (extension)
            raise Exception(msg)

        # evidently the module exists... try to call the function
        method_to_call = getattr(mod, name, None)

        if method_to_call:
            if callable(method_to_call):
                # we pass a pointer to the TaskEngine instance itself, so the extension code has access to everything!
                return method_to_call(self, step)
            else:
                msg = "Extension found, method [%s] found, but not callable." % (name)
                raise Exception(msg)
        else:
            msg = "Extension found, but method [%s] not found." % (name)
            raise Exception(msg)
        
    def process_codeblock(self, task, codeblock_name):

        if not codeblock_name:
            msg = "Codeblock command cannot be empty."
            raise Exception(msg)
            
        self.logger.info("##### Processing Codeblock %s" % (codeblock_name))
        if task.codeblocks.get(codeblock_name):
            for step in task.codeblocks[codeblock_name].step_list:
                self.process_step(task, step)
        else:
            msg = "Codeblock Step references a non-existant Codeblock [%s]." % (codeblock_name)
            raise Exception(msg)
            
    def process_task(self, task_id):

        try:
            task = self.tasks[task_id]
        except KeyError as ex:
            task = classes.Task(task_id)
            self.tasks[task_id] = task

        self.process_codeblock(task, "MAIN")
            
    def get_task_instance(self):

        sql = """select B.task_name, A.asset_id, 
                C.asset_name, A.submitted_by, 
                B.task_id, B.version, A.debug_level, A.schedule_instance, A.schedule_id,
                A.ecosystem_id, A.account_id, A.cloud_id
            from task_instance A 
            join task B on A.task_id = B.task_id
            left outer join asset C on A.asset_id = C.asset_id
            where  A.task_instance = %s"""

        row = self.db.select_row(sql, (self.task_instance))

        if row:
            self.task_name, self.system_id, self.system_name, self.submitted_by, self.task_id, \
                self.task_version, self.debug_level, self.plan_id, self.schedule_id, self.instance_id, \
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
            where ca.account_id=%s"""
        row = self.db.select_row(sql, (account_id))
        if row:
            self.provider, self.cloud_login_id, password = row[:]
            self.cloud_login_password = catocommon.cato_decrypt(password)


    def release_all(self):

        self.logger.info("Releasing all connections")
        for c in self.connections.keys():
            self.drop_connection(c)
            
    def drop_connection(self, conn_name):

        try:
            # get the connection object
            c = self.connections[conn_name]
        except KeyError as ex:
            # well, we have no record of it so move on
            msg = "Connection named %s not found, skipping" % (conn_name)
            self.logger.info(msg)
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
                    self.logger.info(msg)
            elif c.conn_type == "sqlserver":
                self.disconnect_mssql(c.handle)
            elif c.conn_type == "sqlanywhere":
                self.disconnect_sqlany(c.handle)
            elif c.conn_type == "oracle":
                self.disconnect_oracle(c.handle)
            del(c)
            del(self.connections[conn_name])    

    def connect_system(self, c):

        msg = "Going into system %s userid %s with conn type of %s" % (c.system.address, c.system.userid, c.conn_type)
        self.logger.info(msg)

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
            a = classes.Asset(asset_id)
            self.assets[asset_id] = a


    def get_cloud_connection(self, endpoint_name):

        if endpoint_name == "":
            endpoint_name = self.cloud_name
        try:
            cloud = self.cloud_conns[endpoint_name]
        except KeyError as ex:
            cloud = classes.Cloud(endpoint_name)
            self.cloud_conns[endpoint_name] = cloud
            cloud.connect(self.cloud_login_id, self.cloud_login_password)
   
        return cloud

    def select_all(self, sql, conn=None):

        if not conn:
            conn = self.db
        return conn.select_all(sql)

    def update_status(self, task_status):

        self.logger.info("Updating task instance %s to %s" % (self.task_instance, task_status))

        sql = "update task_instance set task_status = %s, completed_dt = now() where task_instance = %s" 
        self.db.exec_db(sql, (task_status, self.task_instance))

    def update_ti_pid(self):

        sql = """update task_instance set pid = %s, task_status = 'Processing', 
            started_dt = now() where task_instance = %s""" 
        self.db.exec_db(sql, (os.getpid(), self.task_instance))


    def extract_xml_string(self, xml, node_name):

        root = ET.fromstring(xml)
        node_name = "./" + node_name
        r = root.findall(node_name)
        if r:
            z = ET.tostring(r[0])
        else:
            z = None
        del(root)
        return z

    def merge_parameters(self, default_xml, override_xml):
        
        # this will merge the two parameter documents, with 
        # values from the second overriding values from the first
        
        # if there's no parameters, do nothing...
        if not default_xml:
            return None
        if not override_xml:
            return None
    
        xdefaults = ET.fromstring(default_xml)
        xoverrides = ET.fromstring(override_xml)
        
        # spin the nodes in the DEFAULTS xml, then dig in to the task XML and UPDATE the value if found.
        # (if the node no longer exists, delete the node from the defaults xml IF IT WAS AN ACTION)
        # and default "values" take precedence over task values.
        for xoverride in xoverrides.findall("parameter"):
            # nothing to do if it's empty
            if xoverride is None:
                break
    
            # look it up in the task param xml
            xovername = xoverride.findtext("name", "")
            xovervals = xoverride.find("values")
            
            # nothing to do if there is no values node... or if it contains no values... or if there is no parameter name
            if xovervals is None or not len(xovervals) or not xovername:
                break
        
        
            # so, we have some valid data in the override xml... let's merge!

            # NOTE! elementtree doesn't track parents of nodes.  We need to build a parent map...
            parent_map = dict((c, p) for p in xdefaults.getiterator() for c in p)
            
            # we have the name of the parameter... go spin and find the matching node in the TASK param XML
            xdefaultparam = None
            for node in xdefaults.findall("parameter/name"):
                if node.text == xovername:
                    # now we have the "name" node, what's the parent?
                    xdefaultparam = parent_map[node]
                    
                    
            if xdefaultparam is not None:
                # the "values" collection will be the 'next' node
                xdefaultparamvalues = xdefaultparam.find("values")
        
                sPresentAs = xdefaultparamvalues.get("present_as", "")
                if sPresentAs == "list":
                    # replace the whole list with the defaults if they exist
                    xdefaultparam.remove(xdefaultparamvalues)
                    xdefaultparam.append(xovervals)
                else:
                    # it's a single value, so just replace it with the default.
                    xval = xdefaultparamvalues.find("value[1]")
                    if xval is not None:
                        if xovervals.find("value") is not None:
                            xval.text = xovervals.findtext("value", "")

        if xdefaults is not None:    
            resp = ET.tostring(xdefaults)
            if resp:
                return resp
        
        
    def parse_input_params(self, params):

        try:
            root = ET.fromstring(params)
            nodes = root.findall("./parameter")
            for node in nodes:
                name = node.findtext("name", "").strip()

                encrypt = node.attrib.get("encrypt")
                if encrypt and encrypt == "true":
                    encrypt_flag = True
                else:
                    encrypt_flag = False

                v_nodes = node.findall("./values/value")
                ii = 0
                for v_node in v_nodes:
                    ii += 1
                    val = v_node.text.strip() if v_node.text is not None else ""
                    if encrypt_flag:
                        val = catocommon.cato_decrypt(val)
                    self.rt.set(name, val, ii)
            del(root)
        except ET.ParseError:
            raise Exception("Invalid or missing XML for parameters.")

    def send_email(self, to, cc, bcc, sub, body):

        msg = "Inserting into message queue : TO:{%s} SUBJECT:{%s} BODY:{%s}" % (to, sub, body)
        self.insert_audit("", msg, "")
        # note - this logic is skipping the file attachment piece, to do
        # also - there may need to be some additional processing to handle html, etc. messages

        sql = """insert into message (date_time_entered,process_type,status,msg_to,msg_from,msg_subject,msg_body, msg_cc, msg_bcc) 
            values (now(),1,0,%s,%s,%s,%s, %s, %s)"""
        self.db.exec_db(sql, (to, self.host_domain, sub, body, cc, bcc))

    def notify_error(self, msg):

        sql = "select admin_email from messenger_settings where id = 1"
        row = self.db.select_row(sql)
        if row and len(row[0]):
            s = "Task Error on %s: Task = %s, Task Instance = %s" % (os.uname()[1], self.task_name, self.task_instance)
            b = "<html>Task Error on %s<br><br>Task = %s<br>Task Instance = %s<br><br>Error:%s</html>" % (os.uname()[1], self.task_name, self.task_instance, msg)
            self.send_email(row[0], "", "", s, b)

    def get_task_params(self):

        sql = "select parameter_xml from task_instance_parameter where task_instance = %s"
        row = self.db.select_row(sql, (self.task_instance))
        if row:
            self.parse_input_params(row[0])


    def set_debug(self, dl):
        # this actually changes the debug level of the logger
        catolog.set_debug(dl)
        
        # this resets the variable, which is used for run_task, etc
        self.debug_level = int(dl)
        

    def startup(self):
        try:
            self.logger.info("""
    #######################################
        Starting up %s
    #######################################""" % self.process_name)
            self.db = catodb.Db()
            self.db.connect_db(server=catoconfig.CONFIG["server"], port=catoconfig.CONFIG["port"],
                user=catoconfig.CONFIG["user"],
                password=catoconfig.CONFIG["password"], database=catoconfig.CONFIG["database"])
            self.config = catoconfig.CONFIG
    
    
            self.logger.info("Task Instance: %s - PID: %s" % 
                (self.task_instance, os.getpid()))
            self.update_ti_pid()
            self.get_task_instance()
            self.get_task_params()
            self.logger.info("Task Name: %s - Version: %s, DEBUG LEVEL: %s, Service Instance id: %s" % 
                (self.task_name, self.task_version, self.debug_level, self.instance_id))
    
    
            self.cloud_name = None
            if self.cloud_account:
                self.gather_account_info(self.cloud_account)
            if self.cloud_id:
                self.cloud_name = self.get_cloud_name(self.cloud_id)
            elif self.cloud_account:
                self.cloud_id = self.get_default_cloud_for_account(self.cloud_account)
                self.cloud_name = self.get_cloud_name(self.cloud_id)
                
    
            self.logger.info("cloud_account is %s, cloud_name is %s " % (self.cloud_account, self.cloud_name))
    
            
    
            # extension paths are defined in config.
            if catoconfig.CONFIG.has_key("extension_path"):
                expath = catoconfig.CONFIG["extension_path"].split(";")
                for p in expath:
                    self.logger.info("Appending extension path [%s]" % p)
                    sys.path.append(p)
            
                    for root, subdirs, files in os.walk(p):
                        for f in files:
                            if f == "augment_te.py":
                                self.augment("%s.augment_te" % os.path.basename(root))
        except Exception as e:
            self.logger.info(e)
            self.update_status('Error')
            raise Exception(e)
        

    def augment(self, modname):
        
        self.logger.info("augmenting from [%s] ..." % modname)
        try:
            mod = importlib.import_module(modname)
        except ImportError as ex:
            raise ex

        # evidently the module exists... try to call the function
        method_to_call = getattr(mod, "__augment__", None)

        if method_to_call:
            if callable(method_to_call):
                # we pass a pointer to the TaskEngine instance itself, so the extension code has access to everything!
                return method_to_call(self)
            else:
                self.logger.error("augment_te module found, but __augment__ is not callable.")
        else:
            self.logger.error("augment_te module found, but doesn't contain __augment__()")
        


    def end(self):
        self.db.close()
        

    def result_summary(self):
        if len(self.summary) > 0:
            msg = "<result_summary><items>%s</items></result_summary>" % (self.summary)
            self.insert_audit("result_summary", msg, "")
        
    
    def run(self):
        try: 
            self.process_task(self.task_id)
            self.update_status('Completed')
            self.result_summary()
            self.release_all()
        except Exception as e:
            msg = "ERROR -> %s" % (e)
            self.logger.info(msg)
            traceback.print_exc(file=sys.stderr)
            self.insert_audit("", msg, "")
            self.update_status('Error')
            self.result_summary()
            self.release_all()
            self.notify_error(msg)
            raise Exception(msg)
