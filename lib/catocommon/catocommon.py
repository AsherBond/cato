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

import os.path
import sys
from catocryptpy import catocryptpy
import time
import threading
import uuid
import decimal
import base64
import os
import pwd
from catodb import catodb

# anything including catocommon can get new connections using the settings in 'config'
def new_conn():
    newdb = catodb.Db()
    newdb.connect_db(server=config["server"], port=config["port"],
        user=config["user"], password=config["password"], database=config["database"])
    return newdb

# this common function will use the encryption key in the config, and DECRYPT the input
def cato_decrypt(encrypted):
    if encrypted:
        return catocryptpy.decrypt_string(encrypted, config["key"])
    else:
        return encrypted
# this common function will use the encryption key in the config, and ENCRYPT the input
def cato_encrypt(s):
    if s:
        return catocryptpy.encrypt_string(s, config["key"])
    else:
        return ""

def _get_base_path():
    # this library file will always be in basepath/lib/catocommon
    # so we will take off two directories and that will be the base_path
    # this function should only be called from catocommon
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return base_path
    
def read_config():
    base_path = _get_base_path()

    filename = os.path.join(base_path, "conf/cato.conf")        
    if not os.path.isfile(filename):
        msg = "The configuration file " + filename + " does not exist."
        raise Exception(msg)
    try:
        fp = open(filename, 'r')
    except IOError as (errno, strerror):
        msg = "Error opening file " + filename + " " + format(errno, strerror)
        raise IOError(msg)
    
    key_vals = {}
    contents = fp.read().splitlines()
    fp.close
    enc_key = ""
    enc_pass = ""
    for line in contents:
        line = line.strip()
        if len(line) > 0 and not line.startswith("#"):
            row = line.split()
            key = row[0].lower()
            if len(row) > 1:
                value = row[1]
            else:
                value = ""

            if key == "key":
                if not value:
                    raise Exception("ERROR: cato.conf 'key' setting is required.")
                enc_key = value
            elif key == "password":
                if not value:
                    raise Exception("ERROR: cato.conf 'password' setting is required.")
                enc_pass = value
            else:
                key_vals[key] = value
    un_key = catocryptpy.decrypt_string(enc_key, "")
    key_vals["key"] = un_key
    un_pass = catocryptpy.decrypt_string(enc_pass, un_key)
    key_vals["password"] = un_pass
    
    # something else here... 
    # the root cato directory should have a VERSION file.
    # read it's value into a config setting
    verfilename = os.path.join(base_path, "VERSION")
    if os.path.isfile(verfilename):
        with open(verfilename, "r") as version_file:
            ver = version_file.read()
            key_vals["version"] = ver
    else:
        print("Info: VERSION file does not exist.")
    
    return key_vals

def pretty_print_xml(xml_string):
    """
        Takes an xml *string* and returns a pretty version.
    """
    import xml.dom.minidom
    xdoc = xml.dom.minidom.parseString(xml_string)
    return xdoc.toprettyxml()

def packData(sIn):
    if not sIn:
        return sIn
    sOut = base64.b64encode(str(sIn))
    return sOut.replace("/", "%2F").replace("+", "%2B")

def unpackData(sIn):
    if not sIn:
        return sIn
    
    sOut = sIn.replace("%2F", "/").replace("%2B", "+")
    return base64.b64decode(sOut)

def new_guid():
    return str(uuid.uuid1())

def generate_password():
    import string
    from random import choice
    chars = string.letters + string.digits
    length = 12
    return "".join(choice(chars) for _ in range(length))

"""The following is needed when serializing objects that have datetime or other non-serializable
internal types"""
def jsonSerializeHandler(obj):
    # decimals
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    
    # date time
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return str(obj)
#    elif isinstance(obj, custom_object):
#        tmp = some code to coerce your custom_object into something serializable
#        return tmp
    raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

def is_true(var):
    # not just regular python truth testing - certain string values are also "true"
    # but false if the string has length but isn't a "true" statement
    # since any object could be passed here (we only want bools, ints or strs)
    # we just cast it to a str
    
    # JUST BE AWARE, this isn't standard python truth testing.
    # So, "foo" will be false... where if "foo" would be true in pure python
    s = str(var).lower()
    if len(s) > 0:
        if str(var).lower() in "true,yes,on,enable,enabled":
            return True
        else:
            # let's see if it was a number, in which case we can just test it
            try:
                i = int(s)
                if i > 0:
                    return True
            except Exception:
                """no exception, it just wasn't parseable into an int"""
    return False

def tick_slash(s):
    """ Prepares string values for string concatenation, or insertion into MySql. """
    if s is not None:
        return s.replace("'", "''").replace("\\", "\\\\").replace("%", "%%")
    
    return ""

def add_task_instance(task_id, user_id, debug_level, parameter_xml, ecosystem_id, account_id, schedule_instance, submitted_by_instance):
    """This *should* be the only place where rows are added to task_instance."""
    try:
        user_id = "'%s'" % user_id if user_id else "null"
        account_id = "'%s'" % account_id if account_id else "null"
        ecosystem_id = "'%s'" % ecosystem_id if ecosystem_id else "null"
        schedule_instance = "'%s'" % schedule_instance if schedule_instance else "null"
        submitted_by_instance = "'%s'" % submitted_by_instance if submitted_by_instance else "null"
        # just in case
        debug_level = str(debug_level)

        db = new_conn()
        sql = """insert into task_instance (
                task_status,
                submitted_dt,
                task_id,
                debug_level,
                submitted_by,
                schedule_instance,
                submitted_by_instance,
                ecosystem_id,
                account_id
            ) values (
                'Submitted',
                now(),
                '%s',
                '%s',
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """ % (task_id, debug_level, user_id, schedule_instance, submitted_by_instance, ecosystem_id, account_id) 
        
        if not db.tran_exec_noexcep(sql):
            print "Unable to run task [%s]." % task_id
            raise Exception(db.error)
        
        task_instance = db.conn.insert_id()
        
        if not task_instance:
            print "An error occured - unable to get the task_instance id."
            return None
        
        # do the parameters
        if parameter_xml:
            sql = """insert into task_instance_parameter (task_instance, parameter_xml) 
                values ('%s', '%s')""" % (str(task_instance), tick_slash(parameter_xml))
            if not db.tran_exec_noexcep(sql):
                print "Unable to save parameter_xml for instance [%s]." % str(task_instance)
                raise Exception(db.error)

        db.tran_commit()
        
        return task_instance
    
    except Exception as ex:
        raise ex
    finally:
        if db:
            db.close()    
    
def add_security_log(UserID, LogType, Action, ObjectType, ObjectID, LogMessage):
    """
    Creates a row in the user_security_log table.  Called from many places.
    
    Note: the calling method is responsible for figuring out the user, as 
    doing so may differ between processes.
    """
    UserID = UserID if UserID else "Unknown"
    sTrimmedLog = tick_slash(LogMessage).strip()
    if sTrimmedLog:
        if len(sTrimmedLog) > 7999:
            sTrimmedLog = sTrimmedLog[:7998]
    sSQL = """insert into user_security_log (log_type, action, user_id, log_dt, object_type, object_id, log_msg)
        values ('%s', '%s', '%s', now(), %d, '%s', '%s')""" % (LogType, Action, UserID, ObjectType, ObjectID, sTrimmedLog)
    db = new_conn()
    if not db.exec_db_noexcep(sSQL):
        print db.error
    db.close()

def write_add_log(UserID, oType, sObjectID, sObjectName, sLog=""):
    if sObjectID and sObjectName:
        if not sLog:
            sLog = "Created: [" + tick_slash(sObjectName) + "]."
        else:
            sLog = "Created: [" + tick_slash(sObjectName) + "] - [" + sLog + "]"

        add_security_log(UserID, SecurityLogTypes.Object, SecurityLogActions.ObjectAdd, oType, sObjectID, sLog)

def write_delete_log(UserID, oType, sObjectID, sObjectName, sLog=""):
    if not sLog:
        sLog = "Deleted: [" + tick_slash(sObjectName) + "]."
    else:
        sLog = "Deleted: [" + tick_slash(sObjectName) + "] - [" + sLog + "]"

    add_security_log(UserID, SecurityLogTypes.Object, SecurityLogActions.ObjectDelete, oType, sObjectID, sLog)

def write_change_log(UserID, oType, sObjectID, sObjectName, sLog=""):
    if sObjectID and sObjectName:
        if not sObjectName:
            sObjectName = "[" + tick_slash(sObjectName) + "]."
        else:
            sLog = "Changed: [" + tick_slash(sObjectName) + "] - [" + sLog + "]"

        add_security_log(UserID, SecurityLogTypes.Object, SecurityLogActions.ObjectAdd, oType, sObjectID, sLog)

def write_property_change_log(UserID, oType, sObjectID, sLabel, sFrom, sTo):
    if sFrom and sTo:
        if sFrom != sTo:
            sLog = "Changed: " + sLabel + " from [" + tick_slash(sFrom) + "] to [" + tick_slash(sTo) + "]."
            add_security_log(UserID, SecurityLogTypes.Object, SecurityLogActions.ObjectAdd, oType, sObjectID, sLog)

def FindAndCall(method, args=None):
    """
    Several rules here:
    1) a / in the "method" denotes class/function.  This works if the source file
        is in the same directory as the executable.  All methods *should* have a /.
        If they don't, it's ok, it'll just look in the local namespace for the function.
    2) a . in the "method" is for a package.module.class/function type lookup.
        (This is when the class is in a lib somewhere in the path.)
        In this case, *we have hardcoded that the class and module names must match*.
        So, if the "method" argument is foo.bar/baz, it will do "from foo import bar"
        and then the function being hooked would be "bar.baz()"
    """
    try:
        db = new_conn()
        # does it have a / ?  if so let's look for another class.
        # NOTE: this isn't recursive... only the first value before a / is the class
        modname = ""
        methodname = method
        classname = ""
        
        if "/" in method:
            modname, methodname = method.split('/', 1)
            classname = modname
        if "." in modname:
            modname, classname = modname.split('.', 1)
            modname = "%s.%s" % (modname, classname)
            
        if modname and classname and methodname:    
            try:
                mod = __import__(modname, globals(), locals(), classname)
                cls = getattr(mod, classname, None)

                if cls:
                    cls.db = db
                    methodToCall = getattr(cls(), methodname, None)
                else:
                    return "Class [%s] does not exist or could not be loaded." % modname
            except ImportError as ex:
                print(ex.__str__())
                return "Module [%s] does not exist." % modname
        else:
            methodToCall = getattr(globals, methodname, None)

        if methodToCall:
            if callable(methodToCall):
                if args:
                    return methodToCall(args)
                else:
                    return methodToCall()

        return "Method [%s] does not exist or could not be called." % method
        
    except Exception as ex:
        raise ex
    finally:
        if db:
            db.close()    
    
#this file has a global 'config' that gets populated automatically.
config = read_config()

class CatoProcess():
    def __init__(self, process_name):
        self.host = os.uname()[1]
        self.platform = os.uname()[0]
        self.user = pwd.getpwuid(os.getuid())[0]
        self.host_domain = self.user +'@'+ os.uname()[1]
        self.my_pid = os.getpid()
        self.process_name = process_name
        self.initialize_logfile()
        self.home = _get_base_path()
        self.tmpdir = config["tmpdir"]

    def set_logfile_name(self):
        self.logfile_name = os.path.join(self.logfiles_path, self.process_name.lower() + ".log")

    def initialize_logfile(self):
        base_path = _get_base_path()
        # logfiles go where defined in cato.conf, but in the base_path if not defined
        self.logfiles_path = (config["logfiles"] if config["logfiles"] else os.path.join(base_path, "logfiles"))
        self.set_logfile_name()

        #stdout/stderr brute force interception can be optionally overridden.
        if config.has_key("redirect_stdout"):
            if config["redirect_stdout"] == "false":
                # we'll just return before it can get redirected
                return

        sys.stderr = open(self.logfile_name, 'a', 1)
        sys.stdout = open(self.logfile_name, 'a', 1)

    def output(self, *args):
        output_string = time.strftime("%Y-%m-%d %H:%M:%S ") + "".join(str(s) for s in args) + "\n\n"

        #if we're not redirecting stdout, all messages that come through here get sent there too
        if config.has_key("redirect_stdout"):
            if config["redirect_stdout"] == "false":
                print(output_string[:-1])

        # the file is always written
        fp = open(self.logfile_name, 'a')
        fp.write(output_string)
        fp.close

    def startup(self):
        self.output("####################################### Starting up ",
            self.process_name,
            " #######################################")
        self.db = catodb.Db()
        conn = self.db.connect_db(server=config["server"], port=config["port"],
            user=config["user"],
            password=config["password"], database=config["database"])
        self.config = config


    def end(self):
        self.db.close()


class CatoService(CatoProcess):

    def __init__(self, process_name):
        CatoProcess.__init__(self, process_name)
        self.delay = 3
        self.loop = 10
        self.mode = "on"
        self.master = 1


    def check_registration(self):

        # Get the node number
        sql = "select id from application_registry where app_name = '" + self.process_name + \
            "' and app_instance = '" + self.host_domain + "'"

        result = self.db.select_col(sql)
        if not result:
            self.output(self.process_name + " has not been registered, registering...")
            self.register_app()
            result = self.db.select_col(sql)
            self.instance_id = result
        else:
            self.output(self.process_name + " has already been registered, updating...")
            self.instance_id = result
            self.output("application instance = %d" % self.instance_id)
            self.db.exec_db("""update application_registry set hostname = %s, userid = %s,
                 pid = %s, platform = %s where id = %s""",
                (self.host_domain, self.user, str(self.my_pid), self.platform,
                 self.instance_id))

    def register_app(self):
        self.output("Registering application...")

        sql = "insert into application_registry (app_name, app_instance, master, logfile_name, " \
            "hostname, userid, pid, platform) values ('" + self.process_name + \
            "', '" + self.host_domain + "',1, '" + self.process_name.lower() + ".log', \
            '" + self.host + "', '" + self.user + "'," + str(self.my_pid) + ",'" + self.platform + "')"
        self.db.exec_db(sql)
        self.output("Application registered.")

    def heartbeat_loop(self, event):
        while True:
            event.wait(self.loop)
            if event.isSet():
                break
            self.update_heartbeat()

    def update_heartbeat(self):
        sql = "update application_registry set heartbeat = now() where id = %s"
        self.db_heart.exec_db(sql, (self.instance_id))

    def get_settings(self):
        pass

    def startup(self):
        CatoProcess.startup(self)
        self.check_registration()
        self.get_settings
        self.db_heart = catodb.Db()
        conn_heart = self.db_heart.connect_db(server=self.config["server"], port=self.config["port"],
            user=self.config["user"],
            password=self.config["password"], database=self.config["database"])
        self.update_heartbeat()
        self.heartbeat_event = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop, args=(self.heartbeat_event,))
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

    def end(self):
        self.heartbeat_event.set()
        self.heartbeat_thread.join()
        self.db.close()

    def service_loop(self):
        while True:
            self.get_settings()
            self.main_process()
            time.sleep(self.loop)

## This object to xml converter inspired from the following code snippet
## http://code.activestate.com/recipes/577739/

## It's not a full featured XML object serializer ... simply turns a python dict into an XML document.

class dict2xml(object):
    def __init__(self, structure, rootname):
        from xml.dom.minidom import Document

        self.doc = Document()
        if structure:
            if rootname:
                self.root = self.doc.createElement(rootname)
            else:
                self.root = self.doc.createElement("root")

            self.doc.appendChild(self.root)
            
            self.build(self.root, structure)

    def build(self, father, structure):
        # print type(structure)
        if type(structure) == dict:
            for k in structure:
                tag = self.doc.createElement(k)
                father.appendChild(tag)
                self.build(tag, structure[k])
        
        elif type(structure) == list:
            grandFather = father.parentNode
            tagName = father.tagName
            grandFather.removeChild(father)
            for l in structure:
                tag = self.doc.createElement(tagName)
                self.build(tag, l)
                grandFather.appendChild(tag)
            
        else:
            data = str(structure)
            tag = self.doc.createTextNode(data)
            father.appendChild(tag)
    
    def display(self):
        print self.doc.toprettyxml(indent="  ")

    def tostring(self):
        return self.doc.toxml(encoding="utf-8")


class SecurityLogTypes(object):
    Object = "Object"
    Security = "Security"
    Usage = "Usage"
    Other = "Other"
    
class SecurityLogActions(object):
    UserLogin = "UserLogin"
    UserLogout = "UserLogout"
    UserLoginAttempt = "UserLoginAttempt"
    UserPasswordChange = "UserPasswordChange"
    UserSessionDrop = "UserSessionDrop"
    SystemLicenseException = "SystemLicenseException"
    
    ObjectAdd = "ObjectAdd"
    ObjectModify = "ObjectModify"
    ObjectDelete = "ObjectDelete"
    ObjectView = "ObjectView"
    ObjectCopy = "ObjectCopy"
    
    PageView = "PageView"
    ReportView = "ReportView"
    
    APIInterface = "APIInterface"
    
    Other = "Other"
    ConfigChange = "ConfigChange"

class CatoObjectTypes(object):
    NA = 0
    User = 1
    Asset = 2
    Task = 3
    Schedule = 4
    Registry = 6
    Tag = 7
    Image = 8
    MessageTemplate = 18
    Parameter = 34
    Credential = 35
    Domain = 36
    CloudAccount = 40
    Cloud = 41
    Ecosystem = 50
    EcoTemplate = 51
    Request = 61
    Deployment = 70
    DeploymentService = 71
    
