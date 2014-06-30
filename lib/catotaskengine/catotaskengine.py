########################################################################/
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

import sys
import os

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

import logging
import traceback
import time
import re
import pwd
import pexpect
import json

from catolog import catolog
from catoconfig import catoconfig
from catosettings import settings
from catocommon import catocommon
from catodb import catodb
from catoruntimes import runtimes
import uuid
import base64
from matheval import matheval
from . import commands
from . import classes
from jsonpath import jsonpath


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

        # see augment() for details about self.extension_modules
        self.extension_modules = []

        # see augment() and sub_globals() for details about global_variables
        # TODO: Add _PUBLIC_IP, _PRIVATE_IP, _DATE
        self.global_variables = [
                      ("_TASK_INSTANCE", "task_instance"),
                      ("_TASK_ID", "task_id"),
                      ("_TASK_NAME", "task_name"),
                      ("_TASK_VERSION", "task_version"),
                      ("_CLOUD_NAME", "cloud_name"),
                      ("_CLOUD_LOGIN_PASS", "cloud_login_password"),
                      ("_CLOUD_LOGIN_ID", "cloud_login_id"),
                      ("_CLOUD_PROVIDER", "provider"),
                      ("_SUBMITTED_BY_EMAIL", "submitted_by_email"),
                      ("_SUBMITTED_BY", "submitted_by_user"),
                      ("_HTTP_RESPONSE", "http_response"),
                      ("_ASSET", "system_id"),
                      ("_OPTIONS", "options"),
                      ("_SUMMARY", "summary")
                      ]

        # the following errors tell us the connection to the db was severed
        # the first was is because of a pymysql bug, issued a pull request on 2013-11-21
        self.connection_errors = ["Broken pipe", "Connection reset by peer", "global name 'EINTR' is not defined"]

        self.task_instance = task_instance

        # tell catoconfig what the LOGFILE name is, then get a logger
        # if logging has already been set up this won't do anything
        # but if it's not yet, this will set the basic config
        logging.basicConfig(level=logging.DEBUG)

        # tell catolog what the LOGFILE name is, then get a logger
        catolog.set_logfile(os.path.join(catolog.LOGPATH, "te", self.task_instance + ".log"))

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
        self.timeout_value = 60
        self.summary = ""
        self.rt = runtimes.Runtimes()
        self.submitted_by_user = ""
        self.submitted_by_email = ""
        self.http_response = -1
        self.sensitive = []
        self.sensitive_re = None
        self.on_error = None
        self.parameter_xml = None

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
                msg = msg + "\n" + str(c.before) + c.match.group() + str(c.after)
            except:
                pass
            raise Exception(msg)
        elif index == 2:
            msg = "%s\nCommand timed out after %s seconds." % (cmd, timeout)
            raise Exception(msg)
        elif index == 3:
            msg = "Negative response %s received ..." % (neg)
            try:
                msg = cmd + "\n" + msg + "\n" + str(c.before) + c.match.group() + str(c.after)
            except:
                pass
            raise Exception(msg)

        # remove any trailing newline
        return str(c.before).rstrip("\n")


    def remove_pk(self, kf_name):

        # we successfully logged in, let's get rid of the private key
        try:
            os.remove(kf_name)
        except:
            pass


    def connect_expect(self, type, host, user, password=None, passphrase=None, key=None, default_prompt=None, debug=False):

        at_prompt = False
        timeout = 20
        buffer = ""

        if not default_prompt:
            default_prompt = "~ #|# $|% $|\$ $|> $"

        if not host:
            raise Exception("Connection address is required to establish a connection")
        if not user:
            raise Exception("User id is required to establish a connection")

        expect_list = [
            "No route to host|Network is unreachable|onnection reset by peer|onnection refused|onnection closed by|Read from socket failed|Name or service not known|Connection timed out",
            "Please login as the user .* rather than the user|expired|Old password:|Host key verification failed|Authentication failed|Permission denied|denied|incorrect|Login Failed|This Account is NOT Valid",
            "yes/no",
            "passphrase for key.*:",
            default_prompt,
            "password will expire(.*)assword: ",
            "assword: $|assword:$",
            pexpect.EOF,
            pexpect.TIMEOUT]

        if debug == "1":
            verbose = "-vv"
        else:
            verbose = ""

        if key:
            kf_name = "%s/%s.pem" % (self.tmpdir, self.new_uuid())
            kf = file(kf_name, "w",)
            kf.write(key)
            kf.close()
            os.chmod(kf_name, 0400)
            self.insert_audit("new_connection", "Attempting ssh private key authentication to %s@%s" % (user, host), "")
            cmd = "ssh %s -i %s -o ForwardAgent=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null %s@%s" % (verbose, kf_name, user, host)
        else:
            self.insert_audit("new_connection", "Attempting ssh password authentication to %s@%s" % (user, host), "")
            cmd = "ssh %s -o ForwardAgent=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null %s@%s" % (verbose, user, host)

        reattempt = True
        attempt = 1
        while reattempt is True:
            c = pexpect.spawn(cmd, timeout=timeout, logfile=sys.stdout)
            buffer = cmd + "\n"

            # TODO - telnet support
            # TODO - regenerate host key if failure

            msg = None
            cpl = c.compile_pattern_list(expect_list)

            sent_password = False
            while not at_prompt:

                index = c.expect_list(cpl)
                # we had some match here, we can remove the private key file
                if key:
                    self.remove_pk(kf_name)
                try:
                    buffer += str(c.before) + str(c.after)
                except:
                    buffer += str(c.before)
                if debug == "1":
                    self.logger.warning("%s" % str(c))

                if index in [0, 7, 8]:
                    msg = ""
                    if index == 7:
                        msg = "The connection to %s closed unexpectedly." % (host)
                    elif index == 8:
                        if sent_password:
                            msg = "Authenticated but timeout waiting for initial prompt using regular expression \"%s\" on address %s." % (default_prompt, host)
                        else:
                            msg = "Timeout attempting waiting for password prompt on address %s." % (host)
                    if attempt != 10:
                        msg = "%s\nssh connection address %s unreachable on attempt %d. %s Sleeping and reattempting" % (buffer, host, attempt, msg)
                        self.insert_audit("new_connection", msg, "")
                        time.sleep(20)
                        attempt += 1
                        break
                    else:
                        msg = "%s\nThe address %s is unreachable, check network or firewall settings %s" % (buffer, host, msg)
                elif index == 1:
                    if key:
                        more_msg = "key authentication. Check that the private key matches the server public key or that the user has permission to login to this server using ssh."
                    else:
                        more_msg = "password authentication. Check that the password for the user is correct or that the user has permission to login to this server using ssh."
                    msg = "%s\nAuthentication failed for address %s, user %s using ssh %s" % (buffer, host, user, more_msg)
                elif index == 2:
                    c.sendline("yes")
                elif index == 3:
                    if not password:
                        msg = "%s\nA passphrase for the private key requested by the target ssh server %s, but none was provided." % (buffer, host)
                    else:
                        c.sendline(passphrase)
                elif index == 4:
                    at_prompt = True
                    reattempt = False
                elif index == 5:
                    self.logger.warning("The password for user %s will expire soon! Continuing ..." % (user))
                    c.logfile = None
                    if not password:
                        msg = "%s\nA password was requested by the target ssh server %s, but none was provided for the user %s." % (buffer, host, user)
                    else:
                        c.sendline(password)
                        sent_password = True
                elif index == 6:
                    c.logfile = None
                    if not password:
                        msg = "%s\nA password was requested by the target ssh server %s, but none was provided for the user %s." % (buffer, host, user)
                    else:
                        c.sendline(password)
                        sent_password = True
                        c.delaybeforesend = 0
                if msg and len(msg):
                    if key:
                        self.remove_pk(kf_name)
                    raise Exception(msg)

        if key:
            self.remove_pk(kf_name)

        c.sendline("unset PROMPT_COMMAND;export PS1='PROMPT>'")
        index = c.expect(["PROMPT>.*PROMPT>$", pexpect.EOF, pexpect.TIMEOUT])
        buffer += str(c.before) + str(c.after)
        if index == 0:
            pass
        elif index == 1:
            msg = "The connection to %s closed unexpectedly." % (host)
            try:
                msg = msg + "\n" + str(c.before) + c.match.group() + str(c.after)
            except:
                pass
            raise Exception(msg)
        elif index == 2:
            msg = "Timeout resetting command prompt."
            try:
                msg = msg + "\n" + str(c.before) + c.match.group() + str(c.after)
            except:
                pass
            raise Exception(msg)
        c.sendline("stty -onlcr;export PS2='';stty -echo;unalias ls")
        index = c.expect(["PROMPT>$", pexpect.EOF, pexpect.TIMEOUT])
        buffer += str(c.before) + str(c.after)
        if index == 0:
            pass
        elif index == 1:
            msg = "The connection to %s closed unexpectedly." % (host)
            try:
                msg = msg + "\n" + str(c.before) + c.match.group() + str(c.after)
            except:
                pass
            raise Exception(msg)
        elif index == 2:
            msg = "Timeout configuring TTY."
            try:
                msg = msg + "\n" + str(c.before) + c.match.group() + str(c.after)
            except:
                pass
            raise Exception(msg)

        self.insert_audit("New Connection", buffer, "")
        self.logger.info("ssh connected to address [%s] with user [%s] established.\n%s" % (host, user, buffer))

        return c


    def connect_oracle(self, server="", port="", user="", password="", database=""):

        import cx_Oracle
        conn_string = "%s/%s@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=%s)(PORT=%s)))(CONNECT_DATA=(SID=%s)))" % (user,
            password, server, port, database)

        clean_cs = conn_string.replace(password, "!PASSWORD-REMOVED!")
        self.logger.debug("Attempting connection using connection string:")
        self.logger.debug(clean_cs)

        tries = 5
        for ii in range(tries):
            try:
                conn = cx_Oracle.connect(conn_string)
                self.logger.debug("Connection established!")
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


    def connect_mssql(self, system=None):

        from pytds import dbapi, login
        conn = None
        # server=c.system.address, port=port, uid=c.system.userid, pwd=c.system.password, database=c.system.db_name

        # If system.domain is provided ... it's NTLM authentication...
        if system.domain:
            self.logger.debug("SQL Server - Domain provided... attempting NTLM authentication...")
            try:
                conn = dbapi.connect(server=system.address,
                                     port=system.port,
                                     auth=login.NtlmAuth(user_name="%s\\%s" % (system.domain, system.userid), password=system.password),
                                     database=system.db_name,
                                     autocommit=True)
            except Exception as e:
                msg = "Could not connect to the database. Error message -> %s" % (e)
                raise Exception(msg)
            return conn
        else:
            self.logger.debug("SQL Server - authenticating using a local database account...")
            # regular auth using a sql server native account
            try:
                conn = dbapi.connect(server=system.address,
                                     port=system.port,
                                     user=system.userid,
                                     password=system.password,
                                     database=system.db_name,
                                     autocommit=True)
            except Exception as e:
                msg = "Could not connect to the database. Error message -> %s" % (e)
                raise Exception(msg)

        self.logger.debug("Connection established!")
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
            self.logger.debug("Connection established!")
        except Exception as e:
            msg = "Could not connect to the database. Error message -> %s" % (e)
            raise Exception(msg)
        return newdb

    def get_xml_val(self, xml, path, index=0):

        try:
            root = catocommon.ET.fromstring(xml)
        except Exception as e:
            msg = "Could not parse XML %s, %s" % (xml, e)
            raise Exception(msg)

        self.logger.debug("xpath: looking for %s" % (path.strip()))
        nodes = root.findall(path.strip())
        if nodes:
            try:
                node = nodes[index]
            except IndexError as ex:
                self.logger.debug("xpath: ... index error\n%s" % (ex.__str__()))
                v = ""
            else:
                if len(list(node)):
                    v = catocommon.ET.tostring(node)
                else:
                    v = node.text
        else:
            self.logger.debug("xpath: ... no match")
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

        root = catocommon.ET.fromstring(xml)
        nodes = root.findall(node_name)
        if nodes:
            count = len(nodes)
        else:
            count = 0
        del(root)
        return count


    def get_node_list(self, xml, node_name, *args):

        return_list = []
        root = catocommon.ET.fromstring(xml)
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
        root = catocommon.ET.fromstring(xml)
        for node in args:
            node = "./" + node
            self.logger.debug("Field: %s" % (node))
            self.logger.debug("Value: %s" % (root.findtext(node, "")))
            return_list.append(root.findtext(node, ""))
        del(root)
        return return_list

    def new_uuid(self):

        return str(uuid.uuid4())

    def add_to_sensitive(self, s):

        if s and len(s) and s not in self.sensitive:
            self.sensitive.append(s)
            self.sensitive_re = re.compile("|".join(self.sensitive))


    def insert_audit(self, command, log, conn=""):

            at = self.audit_trail_on
            step_id = self.current_step_id
            if at > 0:
                if step_id == "":
                    step_id = "NULL"

                # the following masks passwords and the like
                if self.sensitive_re:
                    log = re.sub(self.sensitive_re, "********", log)

                sql = """insert into task_instance_log 
                    (task_instance, step_id, entered_dt, connection_name, log, command_text) 
                    values 
                    (%s, %s, now(), %s, %s, %s)"""
                self.exec_db(sql, (self.task_instance, step_id, conn, log.decode("utf8", "ignore"), command))

                self.logger.critical(log)

            if at == 1:
                self.audit_trail_on = 0

    def get_node_values(self, xml, path, attribs=[], elems=[], other=""):
        """Given an xml string and path, returns a list of dictionary objects.

        Arguments:
        xml -- a string of properly formatted xml
        path -- an Xpath path. 
                See http://docs.python.org/2/library/xml.etree.elementtree.html#supported-xpath-syntax
        attribs -- an optional list of xml node attribute names to retrieve the values for. 
                "*" will retrieve all attributes per node found.
        elems -- an optional list of xml child elements to retrieve the text value for.
                "*" will retrieve all child elements per node found.
        other -- if the attribute or element is not found, return this value (e.g. "" or None)

        Example:
        
        print get_node_values(z, "./NetworkConnection", elems=["MACAddress", "IpAddress"], 
            attribs=["network", "needsCustomization", "aaaaaaaa"], other=None)

        Might return a list of two interfaces with the following dictionary values:

        [{'needsCustomization': 'false', 'aaaaaaaa': None, 'IpAddress': '212.54.150.58', 'network': 'Direct Internet connection', 'MACAddress': '00:50:56:01:02:eb'}, {'needsCustomization': 'false', 'aaaaaaaa': None, 'IpAddress': '212.54.150.82', 'network': 'Direct Internet connection', 'MACAddress': '00:50:56:01:02:e7'}]
        """

        result = []
        root = catocommon.ET.fromstring(xml)
        if not path.startswith("./"):
            path = "./" + path
        nodes = root.findall(path)

        for n in nodes:
            node_result = {}
            if "*" in attribs:
                node_result = n.attrib
                # we don't care about the rest of the list, move on to elems
            else:
                for a in attribs:
                    if a in n.attrib.keys():
                        node_result[a] = n.attrib.get(a)
                    else:
                        node_result[a] = other
            if "*" in elems:
                for e in n:
                    node_result[e.tag] = e.text
                    # we don't care about the rest of the list, move on to the next node
            else:
                for e in elems:
                    node_result[e] = n.findtext(e, other)
            result.append(node_result)
        del(root)
        # don't forget: result will be a list, empty if path is not found
        return result


    def parse_xml(self, xml, path, values):

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

        result = self.get_node_values(xml, path, attribs=attrib_list, elems=elem_list)
        msg = "parse xml\n%s" % (result)
        self.insert_audit("parse xml", msg, "")

        ii = 0
        for row in result:
            ii += 1
            for k, v in variables.iteritems():
                if ii == 1:
                    self.rt.clear(v)
                # print "key %s, variable %s" % (k, v)
                if k in row:
                    # print "setting %s to %s" % (v,  row[k])
                    self.rt.set(v, row[k], ii)


    def task_conn_log(self, address, userid, conn_type):

        self.logger.info("Registering connection in task conn log")
        sql = """insert into task_conn_log (task_instance, address, userid, conn_type, conn_dt) values (%s,%s,%s,%s,now())"""
        self.exec_db(sql, (self.task_instance, address, userid, conn_type))

    def get_cloud_name(self, cloud_id):

        sql = """select cloud_name from clouds where cloud_id = %s"""
        row = self.select_row(sql, (cloud_id))
        if row:
            return row[0]
        else:
            return ""

    def get_default_cloud_for_account(self, account_id):

        sql = """select ca.default_cloud_id from cloud_account ca 
            where ca.account_id = %s"""
        row = self.select_row(sql, (account_id))
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
                self.logger.debug("rt.set(%s, %s, %s)" % (name, row[index], t_index))
                self.rt.set(name, row[index], t_index)

    def get_step_object(self, step_id, step_xml):

        root = catocommon.ET.fromstring(step_xml)
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
                elif found_var.startswith("#"):
                    # this is a task handle variable
                    value = self.get_handle_var(found_var)
                elif found_var.startswith("$"):
                    # this is an "object" lookup (likely set by Read JSON)
                    index = 1  # in case no index is explicitly set, so we don't need two lookup blocks in if cases below
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
                            self.logger.debug(type(var))

                            if isinstance(var, str):
                                # attempt to load it into a dictionary object
                                var = json.loads(var)

                            # [[objvar:*]] will return the number of keys INSIDE this object
                            # if the 'keypath' starts with a $, that's a JSONPATH so we'll apply that
                            # otherwise we'll try a simple root level name.
                            if keypath == "*":
                                value = len(var)
                            else:
                                try:
                                    value = self._use_jsonpath(varname, var, keypath)
                                except Exception as ex:
                                    self.logger.critical(ex)
                                    value = ""

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

    def replace_vars_new(self, s):
        """ 
        streamlined replacement, for the new storage and access method
        pattern matching algorithm is different too, matches Canvas logic 
        
        Simplified "special" cases:
        
        Starts with:
            _ = a global variable
            # = a task handle
        
        Includes:
            ^ = varname followed by an xpath expression
            ex: foo^//root/node 
        """

        while "[$" in s:
            varname = None
            # We're doing an rfind... coming in from the right(bottom) so nested variables will work
            begin_pos = s.rfind("[$")
            end_pos = s.find("$]", begin_pos)
            varname = s[begin_pos + 2:end_pos]

            if varname:
                if varname.startswith("_"):
                    # it's a global variable, look it up
                    value = self.sub_global(varname)
                elif varname.startswith("#"):
                    # this is a task handle variable
                    value = self.get_handle_var(varname)
                elif "^" in varname:
                    # this is an xpath query
                    carat = varname.find("^")
                    new_varname = varname[:carat]
                    xpath = varname[carat + 1:]
                    xml = self.rt.eval_get(new_varname)

                    self.logger.debug("VARNAME: %s" % (new_varname))
                    self.logger.debug("XPATH: %s" % (xpath))
                    self.logger.debug("XML: %s" % (xml))

                    if len(xml):
                        value = self.aws_get_result_var(xml, xpath)
                    else:
                        value = ""
                else:
                    # a normal variable expression
                    value = self.rt.eval_get(varname)

                # now we substitute the variable with the value in the original string
                sub_string = "[$" + varname + "$]"
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


    def _use_jsonpath(self, vname, obj, keypath):
        """
        NOTE: this function MUST return a string, not an object it might have found using jsonpath
        Also, if the response actually is an object (dict, list), it must be dumped pretty printed
        otherwise nested lists might appear as [[1,2,3]], which replace_vars will assume is a variable and try to replace it! :-(
        """
        if keypath:
            v = jsonpath.jsonpath(obj, keypath)
            if v:
                # finally, jsonpath *always* returns a list, because xpath might have matched multiples
                # but, if there's only one item in the list, just return the item directly.  (90% of cases)
                if len(v) == 1:
                    v = v[0]

                # a list or a dict should be json dumped
                # anything else is directly returned
                if isinstance(v, dict) or isinstance(v, list):
                    return catocommon.ObjectOutput.AsJSON(v)
                else:
                    return v

            # not found :-(
            self.logger.info("Object variable [%s] - key [%s] not found." % (vname, keypath))
        else:
            return catocommon.ObjectOutput.AsJSON(obj)

    def sub_global(self, varname):
        """
        This will spin self.global_variables list, and attempt to reconcile _VARNAMES to self.properties.
        A match means the self.property will be used any time the [[_VARNAME]] is referenced.
        
        NOTE: Two special cases for UUIDS might not actually belong here, as they are functions not properties.
        """


        # we expect the variable name to be upper case
        # $ WE ALSO allow a comma in the variable name, but we don't want it just yet...
        full_var_name = varname
        x = full_var_name.split(",")
        varname = x[0]
        keypath = None
        docount = False
        if len(x) > 1:
            docount = True if x[1] == "*" else False

        if ":" in full_var_name:
            x = full_var_name.split(":", 1)
            varname = x[0]
            keypath = "" if len(x) == 1 else x[1]

        # is it one of our helper functions?
        if varname == "_UUID":
            return self.new_uuid()
        if varname == "_UUID2":
            return self.new_uuid().replace("-", "")
        if varname == "_DEBUG":
            out = []
            for k, v in self.__dict__.iteritems():
                out.append("%s -> %s" % (k, v))
            return "\n".join(out)


        # guess not, so spin the global_variables list
        for g_varname, prop in self.global_variables:
            if varname.upper() == g_varname:
                p = getattr(self, prop, "")

                # very simple... jsonpath can look into complex combinations of lists and dicts.
                # so, if the root object is a list or a dict, use jsonpath
                # otherwise return the whole object
                if isinstance(p, list) or isinstance(p, dict):
                    if docount:
                        return len(p)

                    return self._use_jsonpath(varname, p, keypath)
                else:
                    # we presume it's a string value
                    return p

        # no rules at all matched, but logs indicate why.  Return an empty string.
        return ""


    def replace_variables(self, s):

        # NEW METHOD FIRST
        while re.search(".*\[\$.*\$\]", s):
            s = self.replace_vars_new(s)

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
                    # self.logger.debug(">>>" + c_del + "<<<<")
                    # self.logger.debug(line.split(c_del))
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
                            begin += len(prefix)
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
                    match = re.search(pattern, line, flags=re.MULTILINE)
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
        row = self.select_row(sql, (cloud, keyname))
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


    def connect_winrm(self, server, port, user, password, protocol, winrm_transport):

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

        # unfortunately the pywinrm lib considers protocol and transport the same
        # therefore if kerberos is set, we will override the protocol decision above
        # until we can confirm that kerberos can run on plaintext or ssl
        if winrm_transport == "kerberos":
            transport = "kerberos"
        elif winrm_transport == "ssl":
            transport = "ssl"
        elif winrm_transport == "plaintext":
            transport = "plaintext"
        print "transport is %s" % transport

        address = "%s://%s:%s/wsman" % (protocol, server, port)

        self.logger.debug("Attempting WinRM connection to:")
        self.logger.debug(address)

        from winrm import Protocol
        # TODO - allow the user to specify a transport of kerberos, and also test this
        # depends on ubuntu: sudo apt-get install libkrb5-dev; sudo pip install kerberos

        conn = Protocol(endpoint=address, transport=transport, username=user, password=password)
        self.logger.debug("Connection established!")
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
                    traceback.print_exc(file=sys.stderr)
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
        row = self.select_row(sql, (ti))

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
        row = self.select_row(sql, (ti))
        if row:
            status = row[0]
        else:
            status = False
        return status


    def get_system_id_from_name(self, asset_name):

        sql = """select asset_id from asset where asset_name = %s"""
        row = self.select_row(sql, (asset_name))
        if row:
            return row[0]
        else:
            msg = "The asset named %s does not exist in the database" % (asset_name)
            raise Exception(msg)
            return None


    def gather_system_info(self, asset_id):

        sql = """select a.asset_name, a.address, a.port, a.db_name , a.connection_type, 
            ac.username, ac.password, ac.domain, ac.privileged_password, a.conn_string, ac.private_key
            from asset a left outer join asset_credential ac on a.credential_id = ac.credential_id
            where asset_id = %s"""
        row = self.select_row(sql, (asset_id))
        if row:
            # print row
            password = row[6]
            p_password = row[8]
            pk = row[10]

            if password and len(password) > 0:
                password = catocommon.cato_decrypt(password)
            else:
                password = ""
            if p_password and len(password) > 0:
                p_password = catocommon.cato_decrypt(p_password)
            else:
                p_password = ""
            if pk and len(pk) > 0:
                pk = catocommon.cato_decrypt(pk)
            else:
                pk = ""

            s = classes.System(row[0], address=row[1], port=row[2], db_name=row[3], conn_type=row[4], userid=row[5],
                password=password, p_password=p_password, domain=row[7], conn_string=row[9], private_key=pk)

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


    def get_aws_system_info(self, instance_id, user_id, region, password=None, port=None, debug=False):

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

        platform = self.aws_get_result_var(result, "//instancesSet/item/platform")
        address = self.aws_get_result_var(result, "//instancesSet/item/dnsName")
        if not len(platform):
            platform = "linux"
        if password:
            p_key = None
            keyname = None
        else:
            # if password, we are using password auth, not a private key for auth
            keyname = self.aws_get_result_var(result, "//instancesSet/item/keyName")
            pk = self.retrieve_private_key(keyname, region)
            if not pk:
                msg = "The key named %s for cloud %s is not defined in the database" % (keyname, region)
                raise Exception(msg)
            p_key = catocommon.cato_decrypt(pk[0])
            password = catocommon.cato_decrypt(pk[1])
            del(pk)

        s = classes.System(instance_id, address=address, userid=user_id, password=password,
            private_key=p_key, private_key_name=keyname, cloud_name=region)

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

        try:
            from awspy import awspy
        except ImportError as e:
            msg = """Error importing awspy module, module is not installed\n
                    See https://github.com/cloudsidekick/awspy for installation details"""
            raise Exception(msg)
        except Exception as e:
            raise Exception(e)

        # if cloud name is not specified as a parameter, get the cloud account default
        if not len(cloud_name):
            cloud_name = self.cloud_name
        if not cloud_name or not len(cloud_name):
            raise Exception("No default cloud name is defined. Import the AWS clouds or define a new cloud endpoint and setup a new cloud account with access key and secret key.")
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
        nodes = catocommon.ET.fromstring(step.command)
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
        root = catocommon.ET.fromstring(step.command)
        extension = root.attrib.get("extension")
        del(root)
        if not extension:
            msg = "Unable to get 'extension' property from extension command xml for extension %s" % (name)
            self.logger.error(msg)
            raise Exception(msg)

        self.logger.info("loading extension [%s] ..." % (extension))
        try:
            # mod = importlib.import_module(extension)
            mod = __import__(extension, fromlist=[''])
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
        except KeyError:
            task = classes.Task(task_id)
            self.tasks[task_id] = task

        self.process_codeblock(task, "MAIN")

    def get_task_instance(self):

        sql = """select B.task_name, A.asset_id, 
                C.asset_name, A.submitted_by, 
                B.task_id, B.version, A.debug_level, A.schedule_instance, A.schedule_id,
                A.account_id, A.cloud_id, A.options
            from task_instance A 
            join task B on A.task_id = B.task_id
            left outer join asset C on A.asset_id = C.asset_id
            where  A.task_instance = %s"""

        row = self.select_row(sql, (self.task_instance))

        if row:
            self.task_name, self.system_id, self.system_name, self.submitted_by, self.task_id, \
                self.task_version, self.debug_level, self.plan_id, self.schedule_id, \
                self.cloud_account, self.cloud_id, opts = row[:]

        # options need to be json loaded
        self.options = json.loads(opts) if opts else {}

        if self.submitted_by:
            sql = """select username, email from users where user_id = %s"""
            row = self.select_row(sql, (self.submitted_by))
            if row:
                self.submitted_by_user, self.submitted_by_email = row[:]

            return 1
        else:
            return -1

    def gather_account_info(self, account_id):

        sql = """select ca.provider, ca.login_id, ca.login_password from cloud_account ca 
            where ca.account_id=%s"""
        row = self.select_row(sql, (account_id))
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

        msg = "Going into system [%s] userid [%s] with conn type of [%s]." % (c.system.address, c.system.userid, c.conn_type)
        self.logger.info(msg)

        if c.conn_type == "ssh":

            # c.handle = self.connect_ssh_telnet("ssh", c.system.address, c.system.userid, password=c.system.password)
            c.handle = self.connect_expect("ssh", c.system.address, c.system.userid, password=c.system.password,
                key=c.system.private_key, debug=c.debug, default_prompt=c.initial_prompt)

        elif c.conn_type == "telnet":

            # c.handle = self.connect_ssh_telnet("telnet", c.system.address, c.system.userid, password=c.system.password)
            c.handle = self.connect_expect("telnet", c.system.address, c.system.userid, password=c.system.password, default_prompt=c.initial_prompt)

        elif c.conn_type == "ssh - ec2":

            # c.handle = self.connect_ssh_telnet("ssh", c.system.address, c.system.userid,
            #    pk_password=c.system.p_password, key=c.system.private_key)
            c.handle = self.connect_expect("ssh", c.system.address, c.system.userid, password=c.system.password,
                passphrase=c.system.p_password, key=c.system.private_key, debug=c.debug)

        elif c.conn_type == "winrm":

            c.handle = self.connect_winrm(server=c.system.address, port=c.system.port, user=c.system.userid,
                password=c.system.password, protocol=c.system.protocol, winrm_transport=c.winrm_transport)

            c.shell_id = self.get_winrm_shell(c.handle)

        elif c.conn_type == "mysql":

            if c.system.port:
                port = int(c.system.port)
            else:
                port = 3306

            c.handle = self.connect_mysql(server=c.system.address, port=port, user=c.system.userid,
                password=c.system.password, database=c.system.db_name)

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

            c.handle = self.connect_mssql(system=c.system)
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


    def exec_db(self, sql, params=None, conn=None):

        if not conn:
            # to the cato database
            conn = self.db

        # only going to try one additional attempt
        for ii in range(2):
            try:
                result = conn.exec_db(sql, params)
                break
            except Exception as e:
                if any(m in e.message for m in self.connection_errors) and ii == 0:
                    # the following attempts a reconnect
                    msg = "lost mysql connection, attempting a reconnect and retrying the query"
                    self.logger.critical(msg)
                    time.sleep(.5)
                    conn.reconnect_db()
                    # let's try once more
                    continue
                else:
                    # not a severed connection or we already tried once
                    raise Exception(e)

        # all's well
        return result


    def select_all(self, sql, params=None, conn=None):

        if not conn:
            # to the cato database
            conn = self.db

        # only going to try one additional attempt
        for ii in range(2):
            try:
                result = conn.select_all(sql, params)
                break
            except Exception as e:
                if any(m in e.message for m in self.connection_errors) and ii == 0:
                    # the following attempts a reconnect
                    msg = "lost mysql connection, attempting a reconnect and retrying the query"
                    self.logger.critical(msg)
                    time.sleep(.5)
                    conn.reconnect_db()
                    # let's try once more
                    continue
                else:
                    # not a severed connection or we already tried once
                    raise Exception(e)

        # all's well
        return result


    def select_row(self, sql, params=None, conn=None):

        if not conn:
            # to the cato database
            conn = self.db

        # only going to try one additional attempt
        for ii in range(2):
            try:
                result = conn.select_row(sql, params)
                break
            except Exception as e:
                if any(m in e.message for m in self.connection_errors) and ii == 0:
                    # the following attempts a reconnect
                    msg = "lost mysql connection, attempting a reconnect and retrying the query"
                    self.logger.critical(msg)
                    time.sleep(.5)
                    conn.reconnect_db()
                    # let's try once more
                    continue
                else:
                    # not a severed connection or we already tried once
                    raise Exception(e)

        # all's well
        return result


    def update_status(self, task_status):

        self.logger.info("Updating Task Instance [%s] to [%s]" % (self.task_instance, task_status))

        # we don't update the completed_dt unless it's actually done.
        if task_status in ("Completed", "Error", "Cancelled"):
            sql = "update task_instance set task_status = %s, completed_dt = now() where task_instance = %s"
        else:
            sql = "update task_instance set task_status = %s where task_instance = %s"

        ii = 0
        while True:
            try:
                self.exec_db(sql, (task_status, self.task_instance))
            except Exception as e:
                if e.args[0] == 1213 and ii < 5:
                    time.sleep(1)
                    ii += 1
                else:
                    raise e
            else:
                break

        # EXTENSIONS - spin the extensions and call any update_status defined there.
        # won't fail if the extension doesn't have the function defined.
        for extmod in self.extension_modules:
            try:
                extmod.update_status(task_status)
            except AttributeError:
                pass

    def update_ti_pid(self):

        sql = """update task_instance set pid = %s, started_dt = now() where task_instance = %s"""
        ii = 0
        while True:
            try:
                self.exec_db(sql, (os.getpid(), self.task_instance))
            except Exception as e:
                if e.args[0] == 1213 and ii < 5:
                    time.sleep(1)
                    ii += 1
                else:
                    raise e
            else:
                break


    def time_diff_ms(self, td):

        return int(round(td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6)) / 1000

    def extract_xml_string(self, xml, node_name):

        root = catocommon.ET.fromstring(xml)
        node_name = "./" + node_name
        r = root.findall(node_name)
        if r:
            z = catocommon.ET.tostring(r[0])
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

        xdefaults = catocommon.ET.fromstring(default_xml)
        xoverrides = catocommon.ET.fromstring(override_xml)

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
            resp = catocommon.ET.tostring(xdefaults)
            if resp:
                return resp


    def parse_input_params(self, params):
        if params:
            try:
                root = catocommon.ET.fromstring(params)
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
            except catocommon.ET.ParseError:
                raise Exception("Invalid Parameter XML.")

    def send_email(self, to, sub, body, cc=None, bcc=None):

        msg = "Inserting into message queue : TO:{%s} SUBJECT:{%s} BODY:{%s}" % (to, sub, body)
        self.insert_audit("", msg, "")

        # this used to pass self.host_domain as the 'from' property, but messenger doesn't use that anyway
        catocommon.send_email_via_messenger(to, sub, body, cc, bcc)

    def notify_error(self, msg):

        mset = settings.settings.messenger()
        if mset.AdminEmail:
            s = "Task Error on %s: Task = %s, Task Instance = %s" % (os.uname()[1], self.task_name, self.task_instance)
            b = "<html>Task Error on %s<br><br>Task = %s<br>Task Instance = %s<br><br>Error:%s</html>" % (os.uname()[1], self.task_name, self.task_instance, msg)
            self.send_email(to=mset.AdminEmail, sub=s, body=b)

    def get_task_params(self):

        sql = "select parameter_xml from task_instance_parameter where task_instance = %s"
        row = self.select_row(sql, (self.task_instance))
        if row:
            self.parameter_xml = row[0]
            self.parse_input_params(row[0])


    def set_debug(self, dl):
        dl = int(dl)
        # this actually changes the debug level of the logger
        catolog.set_debug(dl)

        # this resets the variable, which is used for run_task, etc
        self.debug_level = dl
        if dl == 50:
            self.audit_trail_on = 0
        else:
            self.audit_trail_on = 2



    def startup(self):
        """
        The critical order of things...
            establish a database connection
            update the ti row in the db (update_ti_pid)
            get the task instance from the db (get_task_instance)
            set the proper debug level to control the logging output (set_debug)
            update the status (will also call any extensions update_status)
            ... 
        """
        try:
            self.db = catodb.Db()
            self.db.connect_db(server=catoconfig.CONFIG["server"], port=catoconfig.CONFIG["port"],
                user=catoconfig.CONFIG["user"],
                password=catoconfig.CONFIG["password"], database=catoconfig.CONFIG["database"])
            self.config = catoconfig.CONFIG

            self.update_ti_pid()
            self.get_task_instance()
            self.set_debug(self.debug_level)

            self.logger.info("""
    #######################################
        Starting up %s
    #######################################""" % self.process_name)

            self.logger.info("Task Instance: %s - PID: %s" % (self.task_instance, os.getpid()))
            self.logger.info("Task Name: %s - Version: %s, DEBUG LEVEL: %s" %
                (self.task_name, self.task_version, self.debug_level))

            self.get_task_params()

            self.cloud_name = None
            if self.cloud_account:
                self.gather_account_info(self.cloud_account)
            if self.cloud_id:
                self.cloud_name = self.get_cloud_name(self.cloud_id)
            elif self.cloud_account:
                self.cloud_id = self.get_default_cloud_for_account(self.cloud_account)
                self.cloud_name = self.get_cloud_name(self.cloud_id)


            self.logger.info("Cloud Account: %s, Cloud Name: %s " % (self.cloud_account, self.cloud_name))


            # loading extensions has two parts:
            # 1) append into the sys.path, all extensions found in the config
            # 2) if self.options has Augments: [], AND it references one of the defined extension...
            #    ... then try to run the augment_te module from that extension

            # 1) append all extensions to the sys.path
            for exname, expath in catoconfig.CONFIG["extensions"].iteritems():
                self.logger.info("Appending extension [%s] path [%s]" % (exname, expath))
                sys.path.append(expath)

            # 2) check if any extensions are meant to augment the TE
            augs = self.options.get("Augments", [])
            for exname in augs:
                expath = catoconfig.CONFIG["extensions"].get(exname)
                if expath:
                    for root, subdirs, files in os.walk(expath):
                        for f in files:
                            if f == "augment_te.py":
                                self.augment("%s.augment_te" % os.path.basename(root))

            # NOTE: we do NOT update the status to Processing until any extensions are loaded.
            # why?  Because update_status also calls into extensions own status updater functions
            self.update_status("Processing")

            # print all the attributes of the Task Engine if the debug level is high enough
            # just to keep things safe here, we are ...
            # a) removing internals from the results
            # b) not crashing if there's an exception
            x = self.__dict__
            out = []
            try:
                for k, v in x.iteritems():
                    out.append("%s -> %s" % (k, v))

                self.logger.debug("TASK ENGINE CONFIGURATION:\n%s" % ("\n".join(out)))
            except Exception as ex:
                self.logger.error("An exception occured resolving the _DEBUG global variable.\n%s" % (ex.__str__()))


        except Exception as e:
            self.logger.info(e)
            self.update_status('Error')
            raise Exception(e)


    def augment(self, modname):
        """
        Will add properties and other setup to the TaskEngine class.  Used to support full 'extensions' to the Task Engine, 
        such as Maestro.
        
        Each module, when imported, becomes part of the Task Engine.  A ref to each module is stored in
        self.extension_modules.  They can be looped at start/end to perform additional init/cleanup.
        
        If defined in the extension __augment__ function, may also append to the 'extension_globals' property.
        'extension_globals' are additional global [[_VARIABLES]] included with the extension. 
        """

        self.logger.info("... augmenting from [%s] ..." % modname)
        try:
            # mod = importlib.import_module(modname)
            mod = __import__(modname, fromlist=[''])
        except ImportError as ex:
            raise ex

        # put a pointer in self.extension_modules
        self.extension_modules.append(mod)

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


    def create_one_like_me(self):

        ti = catocommon.add_task_instance(task_id=self.task_id, user_id=self.submitted_by, debug_level=self.debug_level,
            parameter_xml=self.parameter_xml, account_id=self.cloud_account,
            plan_id=self.plan_id, schedule_id=self.schedule_id, submitted_by_instance=self.task_instance,
            cloud_id=self.cloud_id, options=self.options)


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
            self.logger.critical(msg)
            traceback.print_exc(file=sys.stderr)
            self.debug_level = 10
            self.audit_trail_on = 2
            self.insert_audit("", msg, "")
            self.update_status('Error')
            self.result_summary()
            self.release_all()
            self.notify_error(msg)
            if self.on_error:
                self.logger.critical("on error directive set, creating a new task based on this one")
                self.create_one_like_me()

            raise Exception(msg)
