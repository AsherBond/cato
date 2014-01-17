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

from catocryptpy import catocryptpy
import urllib2
import uuid
import decimal
import base64
import re
import json
import calendar
import sys
from datetime import datetime
import time
from bson.objectid import ObjectId

from catoconfig import catoconfig
from catodb import catodb
from catoerrors import DatastoreError

from catolog import catolog
logger = catolog.get_logger(__name__)

# Select the best available version of ElementTree with the features we need.
if sys.version_info < (2, 7):
    import catoxml.etree.ElementTree as _ET
else:
    try:
        import xml.etree.cElementTree as _ET
    except (AttributeError, ImportError):
        import xml.etree.ElementTree as _ET

# this file is common across all Cato modules, so the following globals are also common

# the "CatoService, if there is one...
CATOSERVICE = None

# so no other modules need to to the try/except for cElementTree
ET = _ET

# anything including catocommon can get new connections using the settings in 'config'
def new_conn():
    newdb = catodb.Db()
    newdb.connect_db(server=catoconfig.CONFIG["server"], port=catoconfig.CONFIG["port"],
        user=catoconfig.CONFIG["user"], password=catoconfig.CONFIG["password"], database=catoconfig.CONFIG["database"])
    return newdb


def new_mongo_conn():
    """
    Connects to mongodb and optionally authenticates.
    
    If mongodb.user is set to empty string, no authentication is performed.
    
    :return: instance of mongodb Database
    """
    try:
        from catomongo import Connection 
        
        mongodb_server = catoconfig.CONFIG["mongodb.server"]
        mongodb_port = int(catoconfig.CONFIG["mongodb.port"]) if catoconfig.CONFIG["mongodb.port"] else 27017
        mongodb_dbname = catoconfig.CONFIG["mongodb.database"]
        mongodb_user = catoconfig.CONFIG["mongodb.user"]
        mongodb_pw = catoconfig.CONFIG["mongodb.password"]

        conn = Connection(mongodb_server, mongodb_port)
        db = conn[mongodb_dbname]

        if mongodb_user:
            # logger.debug("Authenticating with MongoDB using user [%s]" % mongodb_user)
            db.authenticate(mongodb_user, mongodb_pw)
        else:
            # logger.debug("Mongo credentials not defined in cato.conf... skipping authentication.")
            pass
    except Exception as e:
        raise DatastoreError("Couldn't create a Mongo connection to database [%s]" % mongodb_dbname, e)
    return db

def mongo_disconnect(db):
    """
    Disconnects a connection associated with the db previously created via
    a call to new_mongo_conn.
        
    """
    try:
        db.connection.disconnect()
    except Exception, e:
        raise DatastoreError("Error disconnecting %s: %s" % db.name, e)

# this common function will use the encryption key in the config, and DECRYPT the input
def cato_decrypt(encrypted):
    if encrypted:
        return catocryptpy.decrypt_string(encrypted, catoconfig.CONFIG["key"])
    else:
        return encrypted
# this common function will use the encryption key in the config, and ENCRYPT the input
def cato_encrypt(s):
    if s:
        return catocryptpy.encrypt_string(s, catoconfig.CONFIG["key"])
    else:
        return ""

def create_api_token(user_id):
    """
    Will create a row in the api_tokens table.
    """
    token = new_guid()
    now_ts = datetime.utcnow()
    
    sql = """insert into api_tokens 
        (user_id, token, created_dt)
        values ('{0}', '{1}', str_to_date('{2}', '%%Y-%%m-%%d %%H:%%i:%%s'))
        on duplicate key update token='{1}', created_dt=str_to_date('{2}', '%%Y-%%m-%%d %%H:%%i:%%s')
        """.format(user_id, token, now_ts)

    db = new_conn()
    db.exec_db(sql)
    db.close()
    
    return token
    
def send_email_via_messenger(to, subject, body, cc=None, bcc=None):
    msg = "Inserting into message queue:\nTO:[%s]\nSUBJECT:[%s]\nBODY:[%s]" % (to, subject, body)
    logger.info(msg)
    if cc or bcc:
        msg = "Additional:\CC:[%s]\BCC:[%s]" % (cc, bcc)
        logger.info(msg)

    sql = """insert into message (date_time_entered, process_type, status, msg_to, msg_subject, msg_body, msg_cc, msg_bcc) 
        values (now(), 1, 0, %s, %s, %s, %s, %s)"""
    db = new_conn()
    db.exec_db(sql, (to, subject, body, cc, bcc))
    db.close()

def http_get(url, timeout=30, headers={}):
    """
    Make an HTTP GET request, with a configurable timeout and optional headers.
    Returns a tuple - the result and an error message.
    """
    if not url:
        return "", "URL not provided."
    
    logger.info("Trying an HTTP GET to %s" % url)

    # WHEN IT's time to do headers, do it this way
#        req = urllib2.Request('http://www.example.com/')
    # spin the headers dict ...
#        req.add_header('Referer', 'http://www.python.org/')
#        r = urllib2.urlopen(req)

    # for now, just use the url directly
    try:
        request = urllib2.Request(url)
        response = urllib2.urlopen(request, timeout=timeout)
        result = response.read()
        if result:
            return result, None

    except urllib2.URLError as ex:
        if hasattr(ex, "reason"):
            logger.warning("http_get: failed to reach a server.")
            logger.error(ex.reason)
            return None, ex.reason
        elif hasattr(ex, "code"):
            logger.warning("http_get: The server couldn\'t fulfill the request.")
            logger.error(ex.__str__())
            return None, ex.__str__()
    
    # if all was well, we won't get here.
    return None, "No results from request."

def http_get_nofail(url):
    """
    This function does not fail.  For any errors it returns an empty result.
    """
    try:
        if not url:
            return ""
        
        logger.info("Trying an HTTP GET to %s" % url)
        request = urllib2.Request(url)
        response = urllib2.urlopen(request, timeout=4)  # a 4 second timeout is enough
        result = response.read()
        
        if result:
            return result
        else:
            return ""
        
    except Exception as ex:
        logger.warning(ex)
        return ""

def params2xml(parameters):
    """
    the add_task_instance command requires parameter XML...
    we accept json OR xml from the client, and convert if necessary
    """
    pxml = ""
    pjson = ""
    # are the parameters json?
    try:
        logger.info("Checking for JSON parameters...")

        # are the parameters already a list?
        if isinstance(parameters, list):
            pjson = parameters
        else:
            pjson = json.loads(parameters)
    except Exception as ex:
        logger.info("Trying to parse parameters as JSON failed. %s" % ex)
            
    if pjson:
        for p in pjson:
            vals = ""
            if p.get("name") and p.get("values"):
                for v in p["values"]:
                    vals += "<value>%s</value>" % v
            pxml += "<parameter><name>%s</name><values>%s</values></parameter>" % (p["name"], vals)
        
        pxml = "<parameters>%s</parameters>" % pxml
    
    # not json, maybe xml?
    if not pxml:
        try:
            logger.info("Parameters are not JSON... trying XML...")
            # just test to see if it's valid so we can throw an error if not.
            ET.fromstring(parameters)
            pxml = parameters  # an xml STRING!!! - it gets parsed by the Task Engine
        except Exception as ex:
            logger.info("Trying to parse parameters as XML failed. %s" % ex)


    # parameters were provided, but could not be validated
    if not pxml:
        raise Exception("Parameters could not be parsed as valid JSON or XML.")
    
    return pxml
    
def paramxml2json(pxml, basic=False):
    """
    Returns a JSON document representing a blank parameters document for running the Sequence.
    
    IMPORTANT!
    This routine MUST create a template exactly like the Maestro UI creates when submitting parameters.
    
    Any design changes must be applied in both places.
    
    ui/user/static/script/runSequenceDialog.js
    """
    xroot = ET.fromstring(pxml)
    if xroot is not None:
        out = []
        for xparam in xroot.findall("parameter"):
            tmp = {}
            tmp["name"] = xparam.findtext("name", "")
            tmp["values"] = []

            xvals = xparam.find("values")
            present_as = xvals.get("present_as", "")
            
            # if present as is list or value we can include the default values
            if present_as:
                if present_as == "list":
                    vals = []
                    for val in xvals.findall("value"):
                        if val.text:
                            vals.append(val.text)
                    tmp["values"] = vals
                elif present_as == "value":
                    val = xvals.findtext("value[1]")
                    if val:
                        tmp["values"].append(val)
                elif not basic and present_as == "dropdown":
                    # for a dropdown we don't include a value, but 
                    # we do stick the valid values in a *different key* as a reference.
                    tmp["allowed_values"] = [val.text for val in xvals.findall("value")]

            out.append(tmp)
        return out
    return None

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
    
    # data being sent might have unicode chars... 
    sIn = sIn.encode("utf-8")

    sOut = base64.b64encode(sIn)
    return sOut.replace("/", "%2F").replace("+", "%2B")

def unpackData(sIn):
    if not sIn:
        return sIn
    
    sOut = sIn.replace("%2F", "/").replace("%2B", "+")

    # unbase64 it
    sOut = base64.b64decode(sOut)
    
    # *most* of the user-provided values run through this function...
    # so here's a nearly universal place to scrub a string for unicode.
    sOut = sOut.decode("utf-8")
    
    return sOut

def unix_now():
    return int(time.time())

def unix_now_millis():
    x = ("%f" % time.time()).replace(".","")
    return int(x)

def new_guid():
    return str(uuid.uuid1())

def is_guid(s):
    if not s:
        return False

    p = re.compile("^(\{{0,1}([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}-([0-9a-fA-F]){12}\}{0,1})$")
    m = p.match(s)
    if m:
        return True
    else:
        return False

def generate_password(length=12):
    import string
    from random import choice
    chars = string.letters + string.digits
    return "".join(choice(chars) for _ in range(length))

"""The following is needed when serializing objects that have datetime or other non-serializable
internal types"""
def jsonSerializeHandler(obj):
    # decimals
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    
    # Mongo results will often have the ObjectId type
    if isinstance(obj, ObjectId):
        return str(obj)
        
    # date time
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return str(obj)

    # another date time option if you wanted an integer
#    if isinstance(obj, datetime.datetime):
#        return int(time.mktime(obj.timetuple()))    
#    elif isinstance(obj, custom_object):
#        tmp = some code to coerce your custom_object into something serializable
#        return tmp
    raise TypeError("Object of type %s with value of %s is not JSON serializable" % (type(obj), repr(obj)))

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


def lookup_shared_cred(alias):
    """ Get a Credential (including passwords!) by ID or Name. """
    sql = "select username, password, private_key from asset_credential where credential_id = %s or credential_name = %s"
    db = new_conn()
    row = db.select_row(sql, (alias, alias))
    db.close()    
    if row:
        user = row[0]
        password = cato_decrypt(row[1])
        pk = cato_decrypt(row[2])
        ret = (user, password, pk)
    else:
        ret = None
    return ret

def add_task_instance(task_id, user_id, debug_level, parameter_xml, account_id=None, plan_id=None, schedule_id=None, submitted_by_instance=None, cloud_id=None, options=None):
    """This *should* be the only place where rows are added to task_instance."""
    # stringify the options dict
    options = ObjectOutput.AsJSON(options) if options else None
    
    # going into the database, the debug level must be set to one of the python logger levels. (10 based)
    # it'll default to INFO (20) if anything goes wrong
    try:
        x = int(debug_level)
        if x < 10:
            debug_level = x * 10
    except:
        logger.warning("Debug Level [%s] could not be normalized.  Setting to INFO (20)" % (debug_level))
        debug_level = 20
    
    db = new_conn()
    sql = """insert into task_instance (
            task_status,
            submitted_dt,
            task_id,
            debug_level,
            submitted_by,
            schedule_instance,
            schedule_id,
            submitted_by_instance,
            account_id,
            cloud_id,
            options
        ) values (
            'Submitted',
            now(),
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )"""
    
    db.tran_exec(sql, (task_id, debug_level, user_id, plan_id, schedule_id, submitted_by_instance, account_id, cloud_id, options))
    task_instance = db.conn.insert_id()
    
    if not task_instance:
        raise Exception("An error occured - unable to get the task_instance id.")
    
    # do the parameters
    if parameter_xml:
        logger.debug("Saving Parameters: [%s]" % (parameter_xml))
        sql = """insert into task_instance_parameter (task_instance, parameter_xml) 
            values (%s, %s)"""
        if not db.tran_exec_noexcep(sql, (task_instance, parameter_xml)):
            logger.warning("Unable to save parameter_xml for instance [%s]." % task_instance)
            raise Exception(db.error)

    db.tran_commit()
    db.close()    
    
    return task_instance
    
def get_security_log(oid=None, otype=0, user=None, logtype="Security", action=None, search=None, num_records=100, _from=None, _to=None):
    whereclause = "(1=1)"
    if oid:
        whereclause += " and usl.object_id = '%s'" % (oid)

    if otype is not None and otype != "":
        try:
            int(otype)
        except:
            raise Exception("get_security_log - ObjectType [%s] must be an integer." % (otype))
        if otype > 0:  # but a 0 object type means we want everything
            whereclause += " and usl.object_type = '%s'" % (otype)
   
    if logtype:
        whereclause += " and usl.log_type = '%s'" % (logtype)

    if action:
        whereclause += " and usl.action = '%s'" % (action)

    if user:
        whereclause += " and (u.user_id = '{0}' or u.username = '{0}' or u.full_name = '{0}')".format(user)

    dateclause = ""
    searchclause = ""
    
    if search:
        searchclause += """ and (usl.log_dt like '%%{0}%%'
            or u.full_name like '%%{0}%%'
            or usl.log_msg like '%%{0}%%') """.format(search.replace("'", "''"))
    
    if _from:
        dateclause += " and usl.log_dt >= str_to_date('{0}', '%%m/%%d/%%Y')".format(_from)
    if _to:
        dateclause += " and usl.log_dt <= str_to_date('{0}', '%%m/%%d/%%Y')".format(_to)
        
    sql = "select usl.log_msg, usl.action, usl.log_type, usl.object_type, usl.object_id," \
        " convert(usl.log_dt, CHAR(20)) as log_dt, u.full_name" \
        " from user_security_log usl" \
        " join users u on u.user_id = usl.user_id" \
        " where " + whereclause + dateclause + searchclause + \
        " order by usl.log_id desc" \
        " limit " + (str(num_records) if num_records else "100")

    db = new_conn()
    rows = db.select_all_dict(sql)
    db.close()
    if rows:
        return rows
    else:
        return ()
    


def add_security_log(UserID, LogType, Action, ObjectType, ObjectID, LogMessage):
    """
    Creates a row in the user_security_log table.  Called from many places.
    
    Note: the calling method is responsible for figuring out the user, as 
    doing so may differ between processes.
    """
    # we don't crash if we can't write the security log, no matter what
    try:
        UserID = UserID if UserID else "Unknown"
        try:
            int(ObjectType)
        except:
            ObjectType = -1
    
        sTrimmedLog = LogMessage.strip()
        if sTrimmedLog:
            if len(sTrimmedLog) > 7999:
                sTrimmedLog = sTrimmedLog[:7998]
        sSQL = """insert into user_security_log (log_type, action, user_id, log_dt, object_type, object_id, log_msg)
            values (%s, %s, %s, now(), %s, %s, %s)"""
        db = new_conn()
        if not db.exec_db_noexcep(sSQL, (LogType, Action, UserID, ObjectType, ObjectID, sTrimmedLog)):
            logger.error(db.error)
        db.close()
    except Exception as ex:
        logger.error(str(ex))

def write_add_log(UserID, oType, sObjectID, sObjectName, sLog=""):
    if not sLog:
        sLog = "Created: [%s]." % (sObjectName)
    else:
        sLog = "Created: [%s] - [%s]" % (sObjectName, sLog)

    add_security_log(UserID, SecurityLogTypes.Object, SecurityLogActions.ObjectAdd, oType, sObjectID, sLog)

def write_delete_log(UserID, oType, sObjectID, sObjectName, sLog=""):
    if not sLog:
        sLog = "Deleted: [%s]." % (sObjectName)
    else:
        sLog = "Deleted: [%s] - [%s]" % (sObjectName, sLog)

    add_security_log(UserID, SecurityLogTypes.Object, SecurityLogActions.ObjectDelete, oType, sObjectID, sLog)

def write_change_log(UserID, oType, sObjectID, sObjectName, sLog=""):
    if not sLog:
        sLog = "Changed: [%s]." % (sObjectName)
    else:
        sLog = "Changed: [%s] - [%s]" % (sObjectName, sLog)

    add_security_log(UserID, SecurityLogTypes.Object, SecurityLogActions.ObjectModify, oType, sObjectID, sLog)

def write_property_change_log(UserID, oType, sObjectID, sLabel, sFrom, sTo):
    if sFrom and sTo:
        if sFrom != sTo:
            sLog = "Changed: %s from [%s] to [%s]." % (sLabel, sFrom, sTo)
            add_security_log(UserID, SecurityLogTypes.Object, SecurityLogActions.ObjectModify, oType, sObjectID, sLog)

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
            logger.error(ex.__str__())
            return "Module [%s] does not exist." % modname
    else:
        methodToCall = getattr(globals, methodname, None)

    if methodToCall:
        if callable(methodToCall):
            if args:
                return methodToCall(args)
            else:
                return methodToCall()

    if db:
        db.close()    

    return "Method [%s] does not exist or could not be called." % method

def ParseScheduleDefinition(sched_def):
    """
    Will pick apart a schedule definition and return a tuple of components.
    """
    months = sched_def["Months"]
    days = sched_def["Days"]
    hours = sched_def["Hours"]
    minutes = sched_def["Minutes"]
    d_or_w = sched_def["DaysOrWeekdays"]

    if not months:
        raise Exception("Task RunRepeatedly requires 'Months'.")
    if not days:
        raise Exception("Task RunRepeatedly requires 'Days'.")
    if not hours:
        raise Exception("Task RunRepeatedly requires 'Hours'.")
    if not minutes:
        raise Exception("Task RunRepeatedly requires 'Minutes'.")

    # we should account for some properties being special directives instead of schedule details
    if months == "*":
        months = range(0, 12)
    if d_or_w.lower() == "days" or d_or_w == "0" or d_or_w == 0:
        d_or_w = 0
    else:
        d_or_w = 1
    if days == "*":
        if d_or_w == 0:
            days = range(0, 31)
        else:
            days = range(0, 7)
    if hours == "*":
        hours = range(0, 24)
    if minutes == "*":
        minutes = range(0, 60)
        
    return months, days, hours, minutes, d_or_w

def GenerateScheduleLabel(aMo, aDa, aHo, aMi, sDW):
    """
    Given the properties of a schedule, will return a printable description
    and short tooltip.
    """
    
    sDesc = ""
    sTooltip = ""

    # we can analyze the details and come up with a pretty name for this schedule.
    # this may need to be it's own web method eventually...
    if aMo != range(0, 12):
        sDesc += "Some Months, "

    if str(sDW) == "0":
        # explicit days 
        if aDa == range(0, 31):
            sDesc += "Every Day, "
    else:
        # weekdays
        if aDa == range(0, 7):
            sDesc += "Every Weekday, "
        else:
            sDesc += "Some Days, "

    # hours and minutes labels play together, and are sometimes exclusive of one another
    # we'll figure that out later...

    if aHo == range(0, 24):
        sDesc += "Hourly, "
    else:
        sDesc += "Selected Hours, "

    if aMi == range(0, 60):
        sDesc += "Every Minute"
    else:
        sDesc += "Selected Minutes"

    # just use the guid if we couldn't derive a label.
    if sDesc != "":
        sDesc += "."




    # build a verbose description too
    sTmp = ""

    # months
    if aMo == range(0, 12):
        sTmp = "Every Month"
    else:
        m2 = []
        for m in aMo:
            # the calendar utility has months based on 1=January
            m2.append(calendar.month_name[m + 1][:3])
    
        sTmp = ",".join(m2)
    sTooltip += "Months: (" + sTmp + ")<br />\n"

    # days
    sTmp = ""
    if str(sDW) == "0":
        if aDa == range(0, 31):
            sTmp = "Every Day"
        else:
            d2 = []
            for i in aDa:
                # individual days are +1
                d2.append(i + 1)

            sTmp = ",".join([str(x) for x in d2])

        sTooltip += "Days: (" + sTmp + ")<br />\n"
    else:
        if aDa == range(0, 7):
            sTmp = "Every Weekday"
        else:
            d2 = []
            for d in aDa:
                # because the python calendar lib has no way to set SUNDAY as the first day of the week
                # we must subtract 1
                d2.append(calendar.day_name[d - 1])
            sTmp = ",".join([str(x) for x in d2])

        sTooltip += "Weekdays: (" + sTmp + ")<br />\n"

    # hours
    sTmp = ""
    if aHo == range(0, 24):
        sTmp = "Every Hour"
    else:
        sTmp = ",".join([str(x) for x in aHo])
    sTooltip += "Hours: (" + sTmp + ")<br />\n"

    # minutes
    sTmp = ""
    if aMi == range(0, 60):
        sTmp = "Every Minute"
    else:
        sTmp = ",".join([str(x) for x in aMi])
    sTooltip += "Minutes: (" + sTmp + ")<br />\n"

    return sDesc, sTooltip


# # This object to xml converter inspired from the following code snippet
# # http://code.activestate.com/recipes/577739/

# # It's not a full featured XML object serializer ... simply turns a python dict into an XML document.

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
            tag = self.doc.createTextNode(data.encode('ascii', 'replace'))
            father.appendChild(tag)
    
    def display(self):
        print self.doc.toprettyxml(indent="  ")

    def tostring(self):
        return self.doc.toxml(encoding="utf-8")

class ObjectOutput(object):
    """
    This class handles common serialization of Cato object classes to JSON, XML or Text.
    Some classes may have customized serilizers - this one works for objects with no special considerations.
    """
    @staticmethod
    def AsJSON(dict_obj):
        return json.dumps(dict_obj, default=jsonSerializeHandler, indent=4, sort_keys=True, separators=(',', ': '))

    @staticmethod
    def AsXML(dict_obj, item_node):
        xml = dict2xml(dict_obj, item_node)
        return xml.tostring()
        
    @staticmethod
    def AsText(obj, keys, delimiter=None, header=None):
        if not delimiter:
            delimiter = "\t"
        if header:
            header = is_true(header)
        vals = []
        if hasattr(obj, "__dict__"):
            # might be an object, which has the __dict__ builtin
            for key in keys:
                vals.append(str(obj.__dict__.get(key, "")))
        elif isinstance(obj, dict):
            # but if it actually IS a dict...
            for key in keys:
                vals.append(str(obj.get(key, "")))
        else:
            # assume it's an object and get the attribute by name
            for key in keys:
                vals.append(str(getattr(obj, key, "")))

        if header is False:
            return "%s" % (delimiter.join(vals))
        else:
            return "%s\n%s" % (delimiter.join(keys), delimiter.join(vals))

    @staticmethod
    def IterableAsJSON(iterable):
        lst = []
        if iterable:
            for item in iterable:
                if hasattr(item, "__dict__"):
                    lst.append(item.__dict__)
                else:
                    lst.append(item)
            
        return json.dumps(lst, default=jsonSerializeHandler, indent=4, sort_keys=True, separators=(',', ': '))

    @staticmethod
    def IterableAsXML(iterable, root_node, item_node):
        dom = ET.fromstring("<%s />" % root_node)
        if iterable:
            for row in iterable:
                if hasattr(row, "__dict__"):
                    xml = dict2xml(row.__dict__, item_node)
                else:
                    xml = dict2xml(row, item_node)

                node = ET.fromstring(xml.tostring())
                dom.append(node)
        
        return ET.tostring(dom)

    @staticmethod
    def IterableAsText(iterable, keys, delimiter=None, header=None):
        if not delimiter:
            delimiter = "\t"
        if header:
            header = is_true(header)
        outrows = []
        if iterable:
            for row in iterable:
                cols = []
                if hasattr(row, "__dict__"):
                    # might be an object, which has the __dict__ builtin
                    for key in keys:
                        val = "%s" % row.__dict__.get(key, "")
                        cols.append(val.encode('ascii', 'replace'))
                elif isinstance(row, dict):
                    # but if it actually IS a dict...
                    for key in keys:
                        val = "%s" % row.get(key, "")
                        cols.append(val.encode('ascii', 'replace'))
                else:
                    # but if they're not, just return the whole row
                    cols.append(str(row))
                outrows.append(delimiter.join(cols))
        if header is False:
            return "%s" % ("\n".join(outrows))
        else:
            return "%s\n%s" % (delimiter.join(keys), "\n".join(outrows))

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
    Tag = 7
    Image = 8
    MessageTemplate = 18
    Parameter = 34
    Credential = 35
    Domain = 36
    CloudAccount = 40
    Cloud = 41
    CloudKeyPair = 45
    CanvasItem = 50
    Deployment = 70
    DeploymentTemplate = 71
    DeploymentService = 72
    DeploymentSequence = 73
