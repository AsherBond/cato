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
import urllib
import urllib2
import httplib
import json
import hashlib
import base64
import hmac
import re
from bson import json_util
from datetime import datetime, timedelta
import dateutil.parser as parser
from bson.objectid import ObjectId
from pymongo.errors import InvalidName
from awspy import awspy
from catoconfig import catoconfig

from catocommon import catocommon
from . import classes

RESERVED_COLLECTIONS = ["deployments", "services", "default", "system.indexes"]

def _fix_mongo_query(query_string):
    # since we started with a JSON document, any reference to the _id field will likely be 
    # a string representation of the ObjectId.  We gotta cheat that into a real BSON ObjectId.
    if len(query_string):
        try:
            query = json.loads(query_string)
        except ValueError as e:
            msg = "Datastore Query error: query not properly formed json: %s, %s" % (query_string, str(e))
            raise Exception(msg)
        except Exception as e:
            raise Exception(e)
        if not isinstance(query, dict):
            msg = "Datastore Query error: query is not properly formed json key, value pair object %s" % (query_string)
            raise Exception(msg)
    else:
        query = {}
        
    if query.has_key('_id'):
        if isinstance(query['_id'], unicode) or isinstance(query['_id'], str):
            query['_id'] = ObjectId(query['_id'])
    
    return query

def get_asset_cmd(self, task, step):

    asset, address_out, db_out, port_out, conn_string_out, user_out, pass_out = self.get_command_params(step.command, 
        "asset", "address_out", "db_out", "port_out", "conn_string_out", "user_out", "pass_out")[:]
    asset = self.replace_variables(asset)
    address_out = self.replace_variables(address_out)
    db_out = self.replace_variables(db_out)
    port_out = self.replace_variables(port_out)
    conn_string_out = self.replace_variables(conn_string_out)
    user_out = self.replace_variables(user_out)
    pass_out = self.replace_variables(pass_out)

    if not len(asset):
        msg = "Get Asset Properties required an Asset Name"
        raise Exception(msg)

    if not self.is_uuid(asset):
        # look up the asset by name
        asset = self.get_system_id_from_name(asset)

    try:
        # we've loaded it before
        s = self.systems[asset]
    except KeyError:
        # not been loaded yet, get it from the db
        s = self.gather_system_info(asset)

    if len(address_out):
        self.rt.clear(address_out)
        self.rt.set(address_out, s.address)
        
    if len(db_out):
        self.rt.clear(db_out)
        self.rt.set(db_out, s.db_name)

    if len(port_out):
        self.rt.clear(port_out)
        self.rt.set(port_out, s.port)

    if len(conn_string_out):
        self.rt.clear(conn_string_out)
        self.rt.set(conn_string_out, s.conn_string)

    if len(user_out):
        self.rt.clear(user_out)
        self.rt.set(user_out, s.userid)

    if len(pass_out):
        self.rt.clear(pass_out)
        self.rt.set(pass_out, s.password)
        self.add_to_sensitive(s.password)


def datastore_drop_collection_cmd(self, task, step):

    collection = self.get_command_params(step.command, "collection")[0]
    collection = self.replace_variables(collection)

    if len(collection) == 0:
        raise Exception("Datastore Drop Collection command requires a collection name")

    if collection in RESERVED_COLLECTIONS:
        msg = "Datastore Drop Collection error: %s is a reserved collection name" % (collection)
        raise Exception(msg)

    db = catocommon.new_mongo_conn()
    if collection not in db.collection_names():
        msg = "Datastore Drop Collection warning: a collection named %s does not exist, continuing" % (collection)
    else:
        db.drop_collection(collection)
        msg = "Collection %s dropped" % (collection)

    self.insert_audit(step.function_name, msg, "")
    catocommon.mongo_disconnect(db)


def datastore_create_collection_cmd(self, task, step):

    collection = self.get_command_params(step.command, "collection")[0]
    collection = self.replace_variables(collection)

    if len(collection) == 0:
        raise Exception("Datastore Create Collection command requires a collection name")

    if collection in RESERVED_COLLECTIONS:
        msg = "Datastore Create Collection error: %s is a reserved collection name" % (collection)
        raise Exception(msg)

    db = catocommon.new_mongo_conn()
    if collection in db.collection_names():
        msg = "Datastore Create Collection warning: a collection named %s already exists, continuing ..." % (collection)
        self.insert_audit(step.function_name, msg, "")
    else:
        db.create_collection(collection)
        msg = "Collection %s created" % (collection)
        self.insert_audit(step.function_name, msg, "")

    catocommon.mongo_disconnect(db)


def datastore_insert_cmd(self, task, step):

    collection, object_id = self.get_command_params(step.command, "collection", "object_id")[:]
    pairs = self.get_node_list(step.command, "pairs/pair", "name", "value", "json_value")
    collection = self.replace_variables(collection)
    docvar = self.replace_variables(object_id)

    if len(collection) == 0:
        raise Exception("Set Datastore Value requires a collection name")

    if collection in RESERVED_COLLECTIONS:
        msg = "Datastore Insert Collection error: %s is a reserved collection name" % (collection)
        raise Exception(msg)

    db = catocommon.new_mongo_conn()
    try:
        coll = db[collection]
    except InvalidName:
        db.create_collection(collection)
    except Exception as e:
        raise Exception(e)

    document = {}
    # document["timestamp"] = datetime.now()

    for p in pairs:
        name = self.replace_variables(p[0])
        v = self.replace_variables(p[1])
        if p[2] == "1":
            try:
                v = json.loads(v)
            except ValueError as e:
                msg = "Error converting string %s to json\n%s" % (v, e)
                raise Exception(msg)
        elif v == "datetime.now()":
            v = datetime.now()
        document[name] = v

    self.logger.debug(document)
    doc_id = coll.insert(document)
    msg = "Collection %s, Insert %s, Document Id %s" % (collection, str(document), doc_id)
    self.rt.set(docvar, doc_id)
    self.insert_audit(step.function_name, msg, "")

    catocommon.mongo_disconnect(db)

def datastore_delete_cmd(self, task, step):

    collection, query_string = self.get_command_params(step.command, "collection", "query")[:]
    collection = self.replace_variables(collection)
    query_string = self.replace_variables(query_string)

    # validate and prepare the query
    query_dict = _fix_mongo_query(query_string)

    if len(collection) == 0:
        raise Exception("Datastore Delete requires a collection name")

    if collection in RESERVED_COLLECTIONS:
        msg = "Datastore Delete Collection error: %s is a reserved collection name" % (collection)
        raise Exception(msg)

    db = catocommon.new_mongo_conn()
    if collection in db.collection_names():
        coll = db[collection]
    else:
        msg = "Datastore Delete error: a collection named %s does not exist" % (collection)
        raise Exception(msg)

    msg = "Collection %s, Delete %s" % (collection, query_dict)
    coll.remove(query_dict)
    catocommon.mongo_disconnect(db)
    self.insert_audit(step.function_name, msg, "")


def datastore_create_index_cmd(self, task, step):

    collection, unique = self.get_command_params(step.command, "collection", "unique")[:]
    columns = self.get_node_list(step.command, "columns/column", "name")
    collection = self.replace_variables(collection)

    if len(collection) == 0:
        raise Exception("Datastore Create Index requires a collection name")

    if len(columns) == 0:
        msg = "Datastore Create Index error: a list of columns is required"
        raise Exception(msg)

    if collection in RESERVED_COLLECTIONS:
        msg = "Datastore Create Index error: %s is a reserved collection name" % (collection)
        raise Exception(msg)

    db = catocommon.new_mongo_conn()
    if collection in db.collection_names():
        coll = db[collection]
    else:
        db.create_collection(collection)
        coll = db[collection]
        msg = "Collection %s created" % (collection)
        self.insert_audit(step.function_name, msg, "")

    index = []
    for column in columns:
        index.append((column[0], 1))

    msg = "Collection %s index created on columns %s, Unique=%s" % (collection, str(columns), unique)
    if unique == "yes":
        unique = True
    else:
        unique = False
    coll.create_index(index, unique=unique)
    catocommon.mongo_disconnect(db)
    self.insert_audit(step.function_name, msg, "")


def datastore_find_and_modify_cmd(self, task, step):

    collection, query_string, upsert, remove = self.get_command_params(step.command, "collection", "query", "upsert", "remove")[:]
    pairs = self.get_node_list(step.command, "columns/column", "name", "value", "json_value")
    outpairs = self.get_node_list(step.command, "outcolumns/column", "name", "value")
    collection = self.replace_variables(collection)
    query_string = self.replace_variables(query_string)

    # validate and prepare the query
    query_dict = _fix_mongo_query(query_string)

    if len(collection) == 0:
        raise Exception("Datastore Find and Modify requires a collection name")

    db = catocommon.new_mongo_conn()
    if collection in db.collection_names():
        coll = db[collection]
    else:
        msg = "Datastore Find and Modify error: a collection named %s does not exist" % (collection)
        raise Exception(msg)

    _vars = {}
    _outvars = []
    cols = {}
    if remove == "1":
        remove = True
    else:
        remove = False
    if upsert == "1":
        upsert = True
    else:
        upsert = False
    if not remove:
        for p in pairs:
            name = self.replace_variables(p[0])
            v = self.replace_variables(p[1])
            if p[2] == "1":
                try:
                    v = json.loads(v)
                except ValueError as e:
                    msg = "Error converting string %s to json\n%s" % (v, e)
                    raise Exception(msg)
            elif v == "datetime.now()":
                v = datetime.now()
            _vars[name] = v
            if len(name):
                _vars[name] = v

    for p in outpairs:
        name = self.replace_variables(p[0])
        if len(name):
            _outvars.append([name, p[1]])
            cols[name] = True

    if "_id" not in cols.keys():
        cols["_id"] = False

    if len(_vars):
        update_json = {"$set" : _vars}
    else:
        update_json = None
    if not len(cols):
        cols = None
    msg = "Collection %s, Find and Modify %s, Set %s, Columns %s, Upsert %s, Remove %s" % (collection, query_dict, json.dumps(_vars), cols.keys(), upsert, remove)
    row = coll.find_and_modify(query_dict, update=update_json, fields=cols, upsert=upsert, remove=remove)
    msg = "%s\n%s" % (msg, json.dumps(row, default=json_util.default))
    for v in _outvars:
        self.rt.clear(v[1])
    if row:
        for v in _outvars:
            name = v[0]
            variable = v[1]
            try:
                value = row[name]
            except KeyError:
                value = ""
            except Exception as e:
                raise Exception(e)
            # print "name %s, value %s" % (name, value)
            self.rt.set(variable, value)

    catocommon.mongo_disconnect(db)
    self.insert_audit(step.function_name, msg, "")

def datastore_update_cmd(self, task, step):

    collection, query_string, upsert, addtoset = self.get_command_params(step.command, "collection", "query", "upsert", "addtoset")[:]
    pairs = self.get_node_list(step.command, "columns/column", "name", "value", "json_value")
    collection = self.replace_variables(collection)
    query_string = self.replace_variables(query_string)

    # validate and prepare the query
    query_dict = _fix_mongo_query(query_string)
    
    if len(collection) == 0:
        raise Exception("Datastore Update requires a collection name")

    if collection in RESERVED_COLLECTIONS:
        msg = "Datastore Update error: %s is a reserved collection name" % (collection)
        raise Exception(msg)

    db = catocommon.new_mongo_conn()
    if collection in db.collection_names():
        coll = db[collection]
    else:
        msg = "Datastore Update error: a collection named %s does not exist" % (collection)
        raise Exception(msg)

    _vars = {}
    if upsert == "1":
        upsert = True
    else:
        upsert = False

    if addtoset == "1":
        modifier = "$addToSet"
    else:
        modifier = "$set"

    for p in pairs:
        name = self.replace_variables(p[0])
        v = self.replace_variables(p[1])
        if p[2] == "1":
            try:
                v = json.loads(v)
            except ValueError as e:
                msg = "Error converting string %s to json\n%s" % (v, e)
                raise Exception(msg)
        elif v == "datetime.now()":
            v = datetime.now()
        _vars[name] = v

    msg = "Collection %s, Update %s, Set %s, Upsert %s" % (collection, query_dict, json.dumps(_vars), upsert)
    coll.update(query_dict, {modifier : _vars}, multi=True, upsert=upsert)
    catocommon.mongo_disconnect(db)
    self.insert_audit(step.function_name, msg, "")


def datastore_query_cmd(self, task, step):

    collection, query_string = self.get_command_params(step.command, "collection", "query")[:]
    pairs = self.get_node_list(step.command, "columns/column", "name", "variable")
    collection = self.replace_variables(collection)
    query_string = self.replace_variables(query_string)

    # validate and prepare the query
    query_dict = _fix_mongo_query(query_string)

    if len(collection) == 0:
        raise Exception("Datastore Query requires a collection name")

    db = catocommon.new_mongo_conn()
    if collection in db.collection_names():
        coll = db[collection]
    else:
        msg = "Datastore Query error: a collection named %s does not exist" % (collection)
        raise Exception(msg)

    _vars = []
    cols = {}
    for p in pairs:
        name = self.replace_variables(p[0])
        variable = self.replace_variables(p[1])
        if len(name):
            if len(variable):
                _vars.append([name, variable])
                self.rt.clear(variable)
            cols[name] = True
    msg = "Collection %s, Query %s, Columns %s" % (collection, query_dict, cols.keys())
    if "_id" not in cols.keys():
        cols["_id"] = False
    cur = coll.find(query_dict, fields=cols)
    if cur:
        rows = list(cur)
    index = 0
    for row in rows:
        index += 1
        msg = "%s\n%s" % (msg, json.dumps(row, default=json_util.default))
        for v in _vars:
            name = v[0]
            variable = v[1]
            try:
                value = row[name]
            except KeyError:
                value = ""
            except Exception as e:
                raise Exception(e)
            # print "name %s, value %s" % (name, value)
            self.rt.set(variable, value, index)

    catocommon.mongo_disconnect(db)
    self.insert_audit(step.function_name, msg, "")



def codeblock_cmd(self, task, step):
    name = self.get_command_params(step.command, "codeblock")[0]
    name = self.replace_variables(name)
    self.process_codeblock(task, name.upper())

def _set_variable_eval(self, expr):
    """
    Set Variable has an 'eval' modifier.  It's has a very strict mapping to 
    a set of keywords we define and translate to python expressions.
    """
    s = ""
    self.logger.debug("Evaluating: [%s]..." % (expr))
    try:
#         # using eval is not the best approach here.
#         bad_strings = ['import', 'os', 'sys', 'open', '#', '"""']
#         for s in bad_strings:
#             if s in expr:
#                 raise Exception("Invalid keyword in evaluation phrase.")

#         keywords = ["parsedate", "datediff"]
#         for k in keywords:
#             if k in test:
#                 self.logger.debug("Evaluating keyword expression [%s]" % (k))
#                 allow_globals = True
         
#         # replace the keywords with their python counterparts
#         expr = expr.replace("parsedate", "parser.parse")
#         expr = expr.replace("datediff", "timedelta")

        # we expose only specific objects in our environment and pass it as 'globals' to eval.
        environment = { 
                       'parsedate': parser.parse,
                       'datetime': datetime,
                       'timedelta': timedelta
                       }
        s = eval(expr, environment, {})
    except Exception as ex:
        raise Exception("Expression [%s] is not valid.\n%s" % (expr, str(ex)))

    return s

def _eval_test_expression(self, test):
    """
    The IF, EXISTS and WHILE command all make use of 'eval' to test expressions.
    To limit the risk, those eval calls do not provide globals or locals.
    To provide some explicit advanced features, we'll parse the test string and open up
        a few things.
    """
    self.logger.debug("Testing expression: [%s]..." % (test))
    try:
        # using eval is not the best approach here.
        return eval(test, {}, {})
    except Exception as ex:
        raise Exception("Expression [%s] is not valid.\n%s" % (test, str(ex)))

def if_cmd(self, task, step):

    root = catocommon.ET.fromstring(step.command)
    test_nodes = root.findall("./tests/test")
    action_xml = False
    for test_node in test_nodes:
        test = test_node.findtext("eval", "")
        test = self.replace_html_chars(test)
        test = self.replace_variables(test)
        
        if _eval_test_expression(self, test):
            self.logger.debug("... True!")
            action = test_node.findall("./action/function")
            if action:
                action_xml = catocommon.ET.tostring(action[0])
            break
        else:
            self.logger.debug("... False.")
            
    if not action_xml:
        action = root.findall("./else/function")
        if action:
            action_xml = catocommon.ET.tostring(action[0])

    if action_xml:
        sub_step = self.get_step_object(step.step_id, action_xml)
        self.process_step(task, sub_step)
        del(sub_step)
    del(root)


def while_cmd(self, task, step):

    orig_test = self.get_command_params(step.command, "test")[0]
    root = catocommon.ET.fromstring(step.command)
    action = root.findall("./action/function")
    if action:
        action_xml = catocommon.ET.tostring(action[0])
    else:
        action_xml = False
    del(root)

    if action_xml:
        sub_step = self.get_step_object(step.step_id, action_xml)

        orig_test = self.replace_html_chars(orig_test)
        test = self.replace_variables(orig_test)
        sub_step = self.get_step_object(step.step_id, action_xml)

        while _eval_test_expression(self, test):
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
    root = catocommon.ET.fromstring(step.command)
    action = root.findall("./action/function")
    if action:
        action_xml = catocommon.ET.tostring(action[0])
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

        self.logger.debug("initial is %s" % initial)
        self.logger.debug("counter_v_name is %s" % counter_v_name)
        self.logger.debug("loop_test is %s" % loop_test)
        self.logger.debug("orig_compare_to is %s" % orig_compare_to)
        self.logger.debug("actual compare_to is %s" % compare_to)
        self.logger.debug("increment is %s" % increment)
        self.logger.debug("max_iter is %s" % max_iter)


        self.rt.set(counter_v_name, initial)
        counter = initial

        # this part of the test is fixed, such as "<= 10"
        test_part = "%s %s" % (loop_test, compare_to)

        test = "%s %s" % (initial, test_part)
        self.logger.debug(test)
        sub_step = self.get_step_object(step.step_id, action_xml)
        self.logger.debug("counter is %s" % counter)

        loop_num = 1
        while _eval_test_expression(self, test):
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
    root = catocommon.ET.fromstring(step.command)
    variables = root.findall("./variables/variable")
    for v in variables:
        variable_name = v.findtext("name", "").upper()
        is_true_flag = v.findtext("is_true", None)
        has_data_flag = v.findtext("has_data", None)
        self.logger.debug("Checking if [%s] exists ..." % (variable_name))
        
        # if result == "1":
        if self.rt.exists(variable_name):
            value = self.rt.get(variable_name)
            if is_true_flag == "1" and not catocommon.is_true(value):
                self.logger.debug("[%s] is not 'true'." % (variable_name))
                all_true = False
            if has_data_flag == "1" and not len(value):
                self.logger.debug("[%s] has no data." % (variable_name))
                all_true = False
        else:
            all_true = False

    self.logger.debug("all_true = %s" % (all_true))

    action = False
    if all_true:
        action = root.findall("./actions/positive_action/function")
    else:
        action = root.findall("./actions/negative_action/function")

    if action:
        action_xml = catocommon.ET.tostring(action[0])
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
    if self.audit_trail_on == 0:
        self.audit_trail_on = 1
    self.insert_audit(step.function_name, msg, "")


def generate_password_cmd(self, task, step):

    length, v_name = self.get_command_params(step.command, "length", "variable")[:]
    length = self.replace_variables(length)
    v_name = self.replace_variables(v_name)
    if not len(v_name):
        raise Exception("Generate Password command requires Variable Name") 
    if not len(length):
        i_len = 12
    else:
        try:
            i_len = int(length)
        except ValueError as e:
            raise Exception("Length value must be integer, %s found" % (length))
        except Exception as e:
            raise Exception(e)

    p = catocommon.generate_password(i_len) 
    self.rt.set(v_name, p)
    msg = "Generated random password of length %s and stored in variable %s" % (i_len, v_name)
    self.insert_audit(step.function_name, msg, "")


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
        raise Exception("Run Task requires a Task Name.")

    if not handle:
        raise Exception("Run Task requires a handle name.")

    try:
        h = self.task_handles[handle]
        log = "Handle name already being used in this task. Overwriting..."
        self.insert_audit(step.function_name, log)
        del(self.task_handles[handle])
        del(h)
    except KeyError as ex:
        pass
    except Exception as ex:
        raise Exception(ex)
        
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
    
    # NOTE, since this command is called from inside a running task, we will send the 'options' of the current
    # task instance along to any child tasks.  This will ensure all extension options are available down the line.
    
    ti = catocommon.add_task_instance(task_id=task_id, user_id=self.submitted_by, debug_level=self.debug_level,
        parameter_xml=merged_params, account_id=self.cloud_account,
        plan_id=self.plan_id, schedule_id=self.schedule_id, submitted_by_instance=self.task_instance,
        cloud_id=self.cloud_id, options=self.options) 

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

    log = "Running Task Instance [%s] :: ID [%s], Name [%s], Version [%s] using handle [%s]." % (ti, task_id, task_name, task_version, handle)
    cmd = "%s %s" % (step.function_name, ti)
    self.insert_audit(cmd, log)
    
    try:
        sec_wait = int(wait_time)
    except:
        sec_wait = 0 

    # if wait time is 0, don't wait
    # if wait time is -1, wait until task completion
    # if wait time is > 0, wait x seconds and continue
    if sec_wait > 0:
        log = "Waiting [%s] seconds before continuing..." % (wait_time)
        self.insert_audit(step.function_name, log)
        time.sleep(sec_wait)
    elif sec_wait == -1:
        log = "Waiting until task instance [%s] completes..." % (ti)
        self.insert_audit(step.function_name, log)
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
    except KeyError:
        msg = "A connection named [%s] has not been established." % (conn_name)
        raise Exception(msg)

    self.logger.debug("conn type is %s" % (c.conn_type))
    variables = self.get_node_list(step.command, "step_variables/variable", "name", "position")
    if c.conn_type == "mysql":
        _sql_exec_mysql(self, sql, variables, c.handle, mode)
    elif c.conn_type in ["sqlanywhere", "sqlserver", "oracle"]:
        _sql_exec_dbi(self, sql, variables, c.handle)

def _sql_exec_dbi(self, sql, variables, conn):

    cursor = conn.cursor()
    try:
        cursor.execute(sql)
    except Exception as ex:
        msg = "%s\n%s" % (sql, ex)
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

def _sql_exec_mysql(self, sql, variables, conn, mode):

    if mode == "COMMIT":
        #conn.tran_commit()
        sql = "commit"
        #rows = ""
    elif mode == "BEGIN":
        sql = "start transaction"
    elif mode == "ROLLBACK":
        #conn.tran_rollback()
        sql = "rollback"
        #rows = ""
    elif mode in ["EXEC", "PL/SQL", "PREPARE", "RUN"]:
        msg = "Mode %s not supported for MySQL connections. Skipping" % (mode)
        self.insert_audit("sql_exec", msg, "")
        return
    rows = self.select_all(sql, conn)
    if rows:
        self.process_list_buffer(rows, variables)
    msg = "%s\n%s" % (sql, rows)
    self.insert_audit("sql_exec", msg, "")


def store_private_key_cmd(self, task, step):

    key_name, cloud_name, private_key = self.get_command_params(step.command, "name", "cloud_name", "private_key")[:]
    key_name = self.replace_variables(key_name)
    cloud_name = self.replace_variables(cloud_name)
    private_key = self.replace_variables(private_key)

    if len(private_key) == 0:
        raise Exception("Private Key value is required.")
    if len(cloud_name) == 0:
        raise Exception("Cloud Name is required.")
    if len(key_name) == 0:
        raise Exception("Keyname is required.")

    sql = """select cloud_id from clouds where cloud_name = %s"""
    row = self.db.select_row(sql, (cloud_name))
    if not row:
        msg = "Cloud [%s] is not defined in Cato." % (cloud_name)
        raise Exception(msg)

    cloud_id = row[0]

    private_key = catocommon.cato_encrypt(private_key)
    sql = """insert into clouds_keypair (keypair_id, cloud_id, keypair_name, private_key) 
        values (uuid(),%s,%s,%s) ON DUPLICATE KEY UPDATE private_key = %s"""
    self.db.exec_db(sql, (cloud_id, key_name, private_key, private_key))
    msg = "Stored private key [%s] on Cloud [%s]." % (key_name, cloud_name)
    self.insert_audit(step.function_name, msg, "")


def comment_cmd(self, task, step):
    self.logger.info("Skipping comment...")


def clear_variable_cmd(self, task, step):

    variables = self.get_node_list(step.command, "variables/variable", "name")
    for var in variables:
        var = self.replace_variables(var[0])
        if "," in var:
            name, index = var.split(",", 2)
            index = int(index)
        else:
            index = None
        self.rt.clear(var[0], index=index)


def set_variable_cmd(self, task, step):

    variables = self.get_node_list(step.command, "variables/variable", "name", "value", "modifier")
    for var in variables:
        name, value, modifier = var[:]
        name = self.replace_variables(name)
        value = self.replace_variables(value)
        if "," in name:
            name, index = name.split(",", 2)
            index = int(index)
        else:
            index = None
        # FIXUP - need to do modifers logic here
        self.logger.info("Setting variable [%s] to [%s]..." % (name, value))

        if modifier:
            self.logger.info("... using modifier [%s]..." % (modifier))
            
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
        elif modifier == "EVAL":
            value = _set_variable_eval(self, value)
                
        elif modifier == "TO_JSON":
            # assumes the value is a variable name, containing a dictionary, most likely created by the Read JSON option.
            # DOES NOT use the value returned from self.replace_variables, as this is always cast to a string!
            
            dictvar = self.rt.get(value)
            if type(dictvar) == dict or type(dictvar) == list:
                try:
                    value = json.dumps(dictvar)
                except Exception as ex:
                    self.logger.warning("Set Variable - Write JSON Modifier : Unable to dump variable named [%s] to string. %s" % (value, ex.__str__))
            else:
                self.logger.warning("Set Variable - Write JSON Modifier : Requires the 'value' to be a dictionary variable NAME, not reference!")

        elif modifier == "FROM_JSON":
            # reads a JSON string into a dictionary variable object.
            try:
                self.logger.debug("Set Variable - Read JSON Modifier : parsing %s" % (value))
                value = json.loads(value)
            except Exception as ex:
                self.logger.warning("Set Variable - Read JSON Modifier : Unable to parse string. %s" % (ex.__str__))

            # here's the deal... a json source can be an OBJECT -OR- a LIST of objects
            # if it's a list, we'll create a standard runtime array of objects
            # If that's the case, the 'index' provided above is ignored
            if type(value) == list:
                i = 1
                for v in value:
                    self.rt.set(name, v, i)
                    i += 1
            else:
                self.rt.set(name, value, index)

        self.rt.set(name, value, index)

    
def cancel_task_cmd(self, task, step):

    tis = self.get_command_params(step.command, "task_instance")[0]
    tis = self.replace_variables(tis)
    for ti in tis.split(" "):
        if ti.isdigit():
            msg = "Cancelling task instance [%s]..." % (ti)
            self.insert_audit(step.function_name, msg, "")
            sql = """update task_instance set task_status = 'Aborting' 
                where task_instance = %s and task_status in ('Submitted','Staged','Processing')"""
            self.db.exec_db(sql, (ti))
            log = """Cancelling task instance [%s] by other task instance number [%s]""" % (ti, self.task_instance)
            sql = """insert into task_instance_log 
                (task_instance, step_id, entered_dt, connection_name, log, command_text) 
                values 
                (%s, '', now(), '', %s, '')"""
            self.db.exec_db(sql, (self.task_instance, log))
        else:
            raise Exception("Cancel Task error: invalid Task instance: [%s]. Value must be an integer." % (ti))


def wait_for_tasks_cmd(self, task, step):

    handles = self.get_node_list(step.command, "handles/handle", "name")
    # print handles

    handle_set = []
    for handle in handles:
        # print handle[0]
        handle_name = self.replace_variables(handle[0]).lower()
        # print handle_name
        handle_set.append(handle_name)

    log = "Waiting for the following task handles to complete: [%s]... will check every 5 seconds." % (" ".join(handle_set))
    self.insert_audit(step.function_name, log)

    while len(handle_set) > 0:

        for handle in handle_set:
            try:
                h = self.task_handles[handle]
                self.refresh_handle(h)
                if h.status in ["Completed", "Error", "Cancelled"]:
                    handle_set.remove(handle)
                    log = "Handle [%s] finished with a status of [%s]." % (handle, h.status)
                    self.insert_audit(step.function_name, log)
            except KeyError as ex:
                log = "Handle [%s] does not exist, skipping..." % (handle)
                self.insert_audit(step.function_name, log)
                handle_set.remove(handle)
            except Exception as ex:
                raise Exception(ex)
        if len(handle_set) > 0:
            time.sleep(5)

    log = "All task handles have a finished status."
    self.insert_audit(step.function_name, log)


def substring_cmd(self, task, step):

    source, v_name, start, end = self.get_command_params(step.command, "source", "variable_name", "start", "end")[:]
    source = self.replace_variables(source)
    v_name = self.replace_variables(v_name)
    start = self.replace_variables(start)
    end = self.replace_variables(end)

    if len(v_name) == 0:
        raise Exception("Substring command requires a Variable Name.")

    if len(start) == 0:
        raise Exception("Substring command requires a Start value.")

    if len(end) == 0:
        raise Exception("Substring command requires an End value.")

    if not start.isdigit():
        raise Exception("Substring command Start Value must be an integer.")

    if (not end.isdigit()) and (end[0] != "+") and (end[0:3] != "end"):
        raise Exception("Substring error: end index must be integer, +integer, end or end-integer.")

    start = int(start) - 1
    if end.isdigit():
        end = int(end)
    elif end == "end":
        end = None
    elif end[0] == "+":
        end = start + int(end)
    elif end[0:3] == "end" and end[3] == "-":
        end = int(end[3:])

    self.logger.debug("End is [%s]" % (end))
    s = source[start:end]
    
    msg = "Substring set variable [%s] to [%s]." % (v_name, s)
    self.insert_audit(step.function_name, msg, "")
    self.rt.set(v_name, s)


def drop_connection_cmd(self, task, step):

    conn_name = self.get_command_params(step.command, "conn_name")[0]
    conn_name = self.replace_variables(conn_name)
    if conn_name in self.connections.keys():
        msg = "Dropping connection named [%s]..." % (conn_name)
        self.insert_audit(step.function_name, msg, "")
        self.drop_connection(conn_name)
        

def get_shared_cred_cmd(self, task, step):

    alias, u, p, d = self.get_command_params(step.command, "alias", "userid", "password", "domain")[:] 
    alias = self.replace_variables(alias)
    u = self.replace_variables(u)
    p = self.replace_variables(p)
    d = self.replace_variables(d)

    c = catocommon.lookup_shared_cred(alias)
    if c:
        userid = c[0]
        password = c[1]
        self.add_to_sensitive(password)
    else:
        raise Exception("Unable to find Shared Credential using name [%s]." % (alias))
    self.rt.set(u, userid)
    self.rt.set(p, password)

def end_cmd(self, task, step):

    message, status = self.get_command_params(step.command, "message", "status")[:]
    message = self.replace_variables(message)
    msg = "Ending task with a status of [%s], message:\n%s" % (status, message)
    self.insert_audit(step.function_name, msg, "")
    if status == "Error":
        raise Exception("Erroring task with message:\n%s" % (message))
    self.result_summary()
    self.release_all()
    self.update_status(status)
    exit()


# work in progress, not complete.
def new_connection_cmd(self, task, step):

    conn_type, conn_name, asset, cloud_name, debug = self.get_command_params(step.command, "conn_type", "conn_name", "asset", "cloud_name", "debug")[:]
    conn_name = self.replace_variables(conn_name)
    asset = self.replace_variables(asset).strip()
    cloud_name = self.replace_variables(cloud_name)

    if len(debug) == 0:
        debug = False

    if len(asset) == 0:
        raise Exception("New Connection command requires an Asset or connection details.")

    try:
        # we've used this conn name before without dropping it
        c = self.connections[conn_name]
    except KeyError:
        # we've never used this conn name before, continue
        pass
    else:
        # close the connection and reopen
        msg = "A connection by the name %s already exists, closing the previous one and openning a new connection..." % (conn_name)
        self.insert_audit(step.function_name, msg, "")

        self.drop_connection(conn_name)

    # for the asset string, we can either have an asset_id, an asset name,
    # a user@instanceid or a dynamically created connection string

    if conn_type == "ssh - ec2":
        # ec2 connection type is special, we need to look up the system info
        # we need to parse the asset field for the initial information
        # format should be like: username@instanceid
        # cloud_name is not required, it will use the account default if not specified

        if "@" in asset:
            # original implementation, user@instanceId

            password = port = None
            userid, instance_id = asset.split("@")[:2]

        else:
            # new way, supports user id and password auth for ec2

            userid = password = port = shared_cred = None
            #debug = False

            for pair in asset.split(" "):
                k, v = pair.split("=")
                if k == "userid":
                    userid = v
                elif k == "instance":
                    instance_id = v
                elif k == "password":
                    password = v
                elif k == "port":
                    port = v
                elif k == "shared_cred":
                    shared_cred = v
                elif k == "shared_credential":
                    shared_cred = v
                else:
                    msg = "Unsupported key-value pair [%s], skipping..." % (pair)
                    self.logger.info(msg)
            if shared_cred:
                c = catocommon.lookup_shared_cred(shared_cred)
                if c:
                    userid = c[0]
                    password = c[1]
                else:
                    raise Exception("Unable to find Shared Credential using name [%s]." % (shared_cred))

            if not instance_id or not userid:
                msg = "ssh - ec2 connection type requires either of the following formats: username@instanceid or instance=instanceid userid=username, found [%s]." % asset
                raise Exception(msg)

        self.add_to_sensitive(password)
        # we need to give this asset a name, so we'll create one based on the hash
        name = hash(asset)
        try:
            # we've loaded it before
            s = self.systems[name]
        except KeyError:
            # not been loaded yet, get it from aws
            s = self.get_aws_system_info(instance_id, userid, cloud_name, password=password, port=port)
            self.systems[name] = s

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

            address = userid = password = port = db_name = protocol = shared_cred = pk = None
            #debug = False

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
                elif k == "shared_cred":
                    shared_cred = v
                elif k == "shared_credential":
                    shared_cred = v
                else:
                    msg = "Unsupported key-value pair [%s], skipping..." % (pair)
                    self.logger.info(msg)
            if shared_cred:
                c = catocommon.lookup_shared_cred(shared_cred)
                if c:
                    if c[0] and len(c[0]):
                        userid = c[0]
                    if c[1] and len(c[1]):
                        password = c[1]
                    if c[2] and len(c[2]):
                        pk = c[2]
                else:
                    raise Exception("Unable to find Shared Credential using name [%s]." % (shared_cred))
                 
            self.add_to_sensitive(password)
            s = classes.System(name, address=address, userid=userid, password=password,
                port=port, db_name=db_name, protocol=protocol, private_key=pk)

            self.systems[name] = s

    # we've made it this far, let's create the new connection object
    conn = classes.Connection(conn_name, conn_type=conn_type, system=s, debug=debug)
    self.connections[conn_name] = conn
        
    # and make the connection. We'll store any connection handle we get back for later use
    self.connect_system(conn)

    msg = "New connection named [%s] to asset [%s] created with a connection type [%s]." % (conn_name, s.address, conn_type)
    self.insert_audit(step.function_name, msg, "")


def send_email_cmd(self, task, step):

    to, cc, bcc, sub, body = self.get_command_params(step.command, "to", "cc", "bcc", "subject", "body")[:]
    to = self.replace_variables(to)
    cc = self.replace_variables(cc)
    bcc = self.replace_variables(bcc)
    sub = self.replace_variables(sub)
    body = self.replace_variables(body)

    self.send_email(to, sub, body, cc, bcc)


def _cato_sign_string(host, method, access_key, secret_key):


    # timestamp
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    ts = ts.replace(":", "%3A")

    # string to sign
    string_to_sign = "{0}?key={1}&timestamp={2}".format(method, access_key, ts)

    # encoded signature
    sig = base64.b64encode(hmac.new(str(secret_key), msg=string_to_sign, digestmod=hashlib.sha256).digest())
    sig = "&signature=" + urllib.quote_plus(sig)


    url = "%s/%s%s" % (host, string_to_sign, sig)
    return url


def cato_web_service_cmd(self, task, step):

    host, method, userid, password, result_var, error_var, timeout, xpath = self.get_command_params(step.command,
        "host", "method", "userid", "password", "result_var", "error_var", "timeout", "xpath")[:]
    host = self.replace_variables(host)
    method = self.replace_variables(method)
    userid = self.replace_variables(userid)
    password = self.replace_variables(password)
    timeout = self.replace_variables(timeout)
    xpath = self.replace_variables(xpath)
    values = self.get_node_list(step.command, "values/value", "name", "variable", "type")
    try:
        timeout = 5 if not timeout else int(timeout)
    except:
        timeout = 5
    

    if not len(host):
        url = catoconfig.CONFIG["rest_api_url"]

    if not len(method):
        raise Exception("Cato Web Service Call command requires Method value")
    if not len(userid):
        raise Exception("Cato Web Service Call command requires UserId value")
    if not len(password):
        raise Exception("Cato Web Service Call command requires Password value")

    pairs = self.get_node_list(step.command, "pairs/pair", "key", "value")

    args = {}  # a dictionary of any arguments required for 20the method
    for (k, v) in pairs:
        k = self.replace_variables(k)
        v = self.replace_variables(v)
        if len(k):
            args[k] = v

    if args:
        arglst = ["&%s=%s" % (k, urllib.quote_plus(v)) for k, v in args.items()]
        argstr = "".join(arglst)
    else:
        argstr = ""

    url = _cato_sign_string(host, method, userid, password)

    if len(argstr):
        url = "%s%s" % (url, argstr)
        
    self.insert_audit(step.function_name, url)
    error_msg = ""
    try:
        before = datetime.now() 
        response = urllib2.urlopen(url, None, timeout)
        after = datetime.now() 
    except urllib2.HTTPError, e:
        error_msg = "HTTPError = %s, %s, %s" % (str(e.code), e.msg, e.read())
    except urllib2.URLError, e:
        error_msg = "URLError = %s" % (str(e.reason))
    except httplib.HTTPException, e:
        error_msg = "HTTPException" % str(e)

    if error_msg: 
        if error_var:
            self.logger.error(error_msg)
            self.insert_audit(step.function_name, error_msg)
            self.rt.set(error_var, error_msg)
            return
        else:
            raise Exception(error_msg)

    buff = response.read()
    del(response)
    #response_ms = int(round((after - before).total_seconds() * 1000))
    response_ms = self.time_diff_ms(after - before)

    log = "%s\012Response time = %s ms" % (buff, response_ms)
    self.insert_audit(step.function_name, log)
    if len(result_var):
        self.rt.set(result_var, buff)

    if len(xpath):
         self.parse_xml(buff, xpath, values)

def route53_cmd(self, task, step):

    path, rtype, data, response_v = self.get_command_params(step.command, "path", "type", "data", "result_name")[:]
    path = self.replace_variables(path)
    data = self.replace_variables(data)
    response_v = self.replace_variables(response_v)
    conn = awspy.AWSConn(self.cloud_login_id, self.cloud_login_password, product="r53") 
    result = conn.aws_query(path, request_type=rtype, data=data)
    del(conn)
    if result:
        result = self._xml_del_namespace(result)
        msg = "%s %s\n%s" % ("Route53", path, result)
        if len(response_v):
            self.rt.set(response_v, result)
        self.insert_audit("Route53", msg, "")
    else:
        msg = "Route53 command %s failed." % (path)
        raise Exception(msg)



def http_cmd(self, task, step):

    url, typ, u_data, time_out, retries, stat_code_v, stat_msg_v, header_v, body_v, res_time_v = self.get_command_params(step.command,
        "url", "type", "data", "timeout", "retries", "status_code", "status_msg", "response_header", "response_body", "response_time_ms")[:]

    url = self.replace_variables(url)
    u_data = self.replace_variables(u_data)
    time_out = self.replace_variables(time_out)
    retries = self.replace_variables(retries)
    stat_code_v = self.replace_variables(stat_code_v)
    stat_msg_v = self.replace_variables(stat_msg_v)
    header_v = self.replace_variables(header_v)
    body_v = self.replace_variables(body_v)
    res_time_v = self.replace_variables(res_time_v)

    if not len(url):
        raise Exception("HTTP command error, url is empty.")

    headers = self.get_node_list(step.command, "headers/pair", "key", "value")

    if len(time_out):
        timeout = int(time_out)
    else:
        timeout = 10
    if len(retries):
        retries = int(retries)
    else:
        retries = 0
    attempt = 0 

    req = urllib2.Request(url)
    req.get_method = lambda: typ
    if not len(u_data):
        u_data = None
    
    req.add_data(u_data)    
    for (k, v) in headers:
        k = self.replace_variables(k)
        v = self.replace_variables(v)
        if len(k):
            req.add_header(k, v)

    ok = True
    while attempt <= retries:
        try:
            before = datetime.now() 
            response = urllib2.urlopen(req, None, timeout)
            after = datetime.now() 
            break
        except urllib2.HTTPError, e:
            after = datetime.now() 
            head = e.headers
            msg = e.msg
            buff = e.read()
            code = e.code
            ok = False
            
            # raise Exception("HTTPError = %s, %s, %s\n%s" % (str(e.code), e.msg, e.read(), url))
            break
        except urllib2.URLError, e:
            attempt += 1
            if str(e.reason) == "timed out" and attempt <= retries:
                self.insert_audit(step.function_name, "timeout on attempt number %s, retrying" % attempt)
            else:
                after = datetime.now() 
                head = ""
                msg = e.reason
                buff = ""
                code = e.reason
                ok = False
                # raise Exception("URLError = %s\n%s" % (str(e.reason), url))
                break
        except Exception as e:
            import traceback
            raise Exception("generic exception: " + traceback.format_exc())

    if ok:
        buff = response.read()
        head = response.headers
        code = response.getcode()
        msg = "ok"
        del(response)

    #response_ms = int(round((after - before).total_seconds() * 1000))
    response_ms = self.time_diff_ms(after - before)
    self.http_response = response_ms

    if len(body_v):
        self.rt.set(body_v, buff)
    if len(header_v):
        self.rt.set(header_v, head)
    if len(stat_msg_v):
        self.rt.set(stat_msg_v, msg)
    if len(stat_code_v):
        self.rt.set(stat_code_v, code)
    if len(res_time_v):
        self.rt.set(res_time_v, response_ms)

    log = "http %s %s\012%s - %s\012%s\012Response time = %s ms" % (typ, url, code, msg, buff, response_ms)
    self.insert_audit(step.function_name, log)
    variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
        "range_begin", "prefix", "range_end", "suffix", "regex", "xpath")
    if len(variables):
        self.process_buffer(buff, step)


def get_instance_handle_cmd(self, task, step):

    ti, handle = self.get_command_params(step.command, "instance", "handle")[:]
    ti = self.replace_variables(ti)
    handle = self.replace_variables(handle)
    handle = handle.lower()

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
    log = "%s: %s" % (step.function_name, buff)
    self.insert_audit(step.function_name, log)
    variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
        "range_begin", "prefix", "range_end", "suffix", "regex", "xpath")
    if len(variables):
        self.logger.debug(variables)
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
    if len(dl):
        # changing the logging level raises a critical message, so it's always seen for clarity.
        msg = "Setting the debug level to [%s]..." % (dl)
        self.logger.critical(msg)
        self.insert_audit(step.function_name, msg, "")
        self.set_debug(dl)

def sleep_cmd(self, task, step):

    seconds = self.get_command_params(step.command, "seconds")[0]
    seconds = self.replace_variables(seconds)
    try:
        seconds = int(seconds)
    except ValueError:
        raise Exception("Sleep command requires seconds as an integer value... found [%s]." % (seconds))

    msg = "Sleeping {%s} seconds..." % (seconds)
    self.insert_audit(step.function_name, msg, "")
    time.sleep(seconds)


def break_loop_cmd(self, task, step):
    
    self.insert_audit(step.function_name, "Breaking out of loop.", "")
    self.loop_break = True


def winrm_cmd_cmd(self, task, step):
    
    conn_name, cmd, timeout, return_code = self.get_command_params(step.command, "conn_name", "command", "timeout", "return_code")[:]
    conn_name = self.replace_variables(conn_name)
    cmd = self.replace_variables(cmd)
    return_code = self.replace_variables(return_code)
    timeout = self.replace_variables(timeout)

    try:
        # get the connection object
        c = self.connections[conn_name]
    except KeyError:
        msg = "A connection named [%s] has not been established." % (conn_name)
        raise Exception(msg)

    if timeout:
        to = int(timeout) 
        c.handle.timeout = c.handle.set_timeout(to)

    self.logger.info("WinRM - executing:\n%s" % cmd)
    command_id = c.handle.run_command(c.shell_id, cmd)
    buff, err, r_code = c.handle.get_command_output(c.shell_id, command_id)

    # add stderr to the end of stdout
    buff += err

    # replace CRLF with LF for easier processing
    buff = re.sub("\r\n", "\n", buff).rstrip("\n")
    self.logger.info("WinRM return code >%s<" % r_code)
    self.logger.info("Buffer returned is >%s<" % buff)
    self.logger.info("Error result is >%s<" % err)

    if c.debug:
        self.logger.info(':'.join(x.encode('hex') for x in buff))
    
    c.handle.cleanup_command(c.shell_id, command_id)
    
    if len(return_code):
        self.rt.set(return_code, r_code)
    msg = "%s\n%s" % (cmd, buff)
    self.insert_audit(step.function_name, msg)
    variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
        "range_begin", "prefix", "range_end", "suffix", "regex", "xpath")
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
    except KeyError:
        msg = "A connection named [%s] has not been established." % (conn_name)
        raise Exception(msg)

    if not len(pos):
        pos = "PROMPT>"
    if not len(neg):
        neg = "This is a default response you shouldnt get it 09kjsjkj49"
    if not len(timeout):
        timeout = self.timeout_value
    else:
        timeout = int(timeout)

    self.logger.info("Issuing command:\n%s" % (cmd))
    buff = self.execute_expect(c.handle, cmd, pos, neg, timeout)
    self.insert_audit(step.function_name, "%s\n%s" % (cmd, buff), conn_name)
    # print(':'.join(x.encode('hex') for x in buff))

    variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
        "range_begin", "prefix", "range_end", "suffix", "regex", "xpath")
    if len(variables):
        # print variables
        self.process_buffer(buff, step)

