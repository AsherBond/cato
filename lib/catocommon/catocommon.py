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
from bson.objectid import ObjectId

from catoconfig import catoconfig
from catodb import catodb
from catoerrors import DatastoreError

from catolog import catolog
logger = catolog.get_logger(__name__)

try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

# this file is common across all Cato modules, so the following globals are also common

# the "CatoService, if there is one...
CATOSERVICE = None

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
        raise DatastoreError(
                    "Error disconnecting %s: %s" \
                    % db.name, e)

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
        response = urllib2.urlopen(url, None, timeout)
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

    NOTE: this function is called by unauthenticated pages.
    DO NOT use any of the helper functions like ".log" - they look for a user and kick back to the login page 
    if none is found.  (infinite_loop = bad)
    
    That's why we're using log_nouser.
    
    """
    try:
        if not url:
            return ""
        
        logger.info("Trying an HTTP GET to %s" % url)
        response = urllib2.urlopen(url, None, 4)  # a 4 second timeout is enough
        result = response.read()
        
        if result:
            return result
        else:
            return ""
        
    except Exception as ex:
        logger.warning(ex)
        return ""

def http_post(url, args, timeout=30, headers={}):
    """
    Make an HTTP GET request, with a configurable timeout and optional headers.
    """
    if not url:
        return "", "URL not provided."
    
    logger.info("Trying an HTTP POST to %s..." % url)
    logger.debug("   using args:\n%s" % args)

    try:
        data = json.dumps(args)
        response = urllib2.urlopen(url, data, timeout)
        result = response.read()
        if result:
            return result, None

    except urllib2.URLError as ex:
        if hasattr(ex, "reason"):
            logger.warning("http_post: failed to reach a server.")
            logger.error(ex.reason)
            return None, ex.reason
        elif hasattr(ex, "code"):
            logger.warning("http_post: The server couldn\'t fulfill the request.")
            logger.error(ex.__str__())
            return None, ex.__str__()
    
    # if all was well, we won't get here.
    return None

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
    
    # Mongo results will often have the ObjectId type
    if isinstance(obj, ObjectId):
        return str(obj)
        
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

def add_task_instance(task_id, user_id, debug_level, parameter_xml, scope_id, account_id, schedule_instance, submitted_by_instance, cloud_id=False):
    """This *should* be the only place where rows are added to task_instance."""
    try:
        user_id = "'%s'" % user_id if user_id else "null"
        account_id = "'%s'" % account_id if account_id else "null"
        scope_id = "'%s'" % scope_id if scope_id else "null"
        schedule_instance = "'%s'" % schedule_instance if schedule_instance else "null"
        submitted_by_instance = "'%s'" % submitted_by_instance if submitted_by_instance else "null"
        cloud_id = "'%s'" % cloud_id if cloud_id else "null"
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
                account_id,
                cloud_id
            ) values (
                'Submitted',
                now(),
                '%s',
                '%s',
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """ % (task_id, debug_level, user_id, schedule_instance, submitted_by_instance, scope_id, account_id, cloud_id)
        
        if not db.tran_exec_noexcep(sql):
            raise Exception("Unable to run task [%s].%s" % (task_id, db.error))
        
        task_instance = db.conn.insert_id()
        
        if not task_instance:
            logger.warning("An error occured - unable to get the task_instance id.")
            return None
        
        # do the parameters
        if parameter_xml:
            sql = """insert into task_instance_parameter (task_instance, parameter_xml) 
                values ('%s', '%s')""" % (str(task_instance), tick_slash(parameter_xml))
            if not db.tran_exec_noexcep(sql):
                logger.warning("Unable to save parameter_xml for instance [%s]." % str(task_instance))
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
        logger.error(db.error)
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
    
def GenerateScheduleLabel(aMo, aDa, aHo, aMi, sDW):
    """
    Given the properties of a schedule, will return a printable description
    and short tooltip.
    """
    
    sDesc = ""
    sTooltip = ""

    # we can analyze the details and come up with a pretty name for this schedule.
    # this may need to be it's own web method eventually...
    if aMo != [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
        sDesc += "Some Months, "

    if sDW == "0":
        # explicit days 
        if aDa == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]:
            sDesc += "Every Day, "
    else:
        # weekdays
        if aDa == [0, 1, 2, 3, 4, 5, 6]:
            sDesc += "Every Weekday, "
        else:
            sDesc += "Some Days, "

    # hours and minutes labels play together, and are sometimes exclusive of one another
    # we'll figure that out later...

    if aHo == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]:
        sDesc += "Hourly, "
    else:
        sDesc += "Selected Hours, "

    if aMi == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]:
        sDesc += "Every Minute"
    else:
        sDesc += "Selected Minutes"

    # just use the guid if we couldn't derive a label.
    if sDesc != "":
        sDesc += "."




    # build a verbose description too
    sTmp = ""

    # months
    if aMo == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
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
    if sDW == "0":
        if aDa == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]:
            sTmp = "Every Day"
        else:
            d2 = []
            for i in aDa:
                # individual days are +1
                d2.append(i + 1)

            sTmp = ",".join([str(x) for x in d2])

        sTooltip += "Days: (" + sTmp + ")<br />\n"
    else:
        if aDa == [0, 1, 2, 3, 4, 5, 6]:
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
    if aHo == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]:
        sTmp = "Every Hour"
    else:
        sTmp = ",".join([str(x) for x in aHo])
    sTooltip += "Hours: (" + sTmp + ")<br />\n"

    # minutes
    sTmp = ""
    if aMi == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]:
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
            tag = self.doc.createTextNode(data)
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
        return json.dumps(dict_obj, default=jsonSerializeHandler, indent=4)

    @staticmethod
    def AsXML(dict_obj, item_node):
        try:
            xml = dict2xml(dict_obj, item_node)
            return xml.tostring()
        except Exception as ex:
            raise ex
        
    @staticmethod
    def AsText(obj, keys, delimiter=None):
        try:
            if not delimiter:
                delimiter = "\t"
            vals = []
            if hasattr(obj, "__dict__"):
                # might be an object, which has the __dict__ builtin
                for key in keys:
                    vals.append(str(obj.__dict__[key]))
            elif isinstance(obj, dict):
                # but if it actually IS a dict...
                for key in keys:
                    vals.append(str(obj[key]))
            else:
                # assume it's an object and get the attribute by name
                for key in keys:
                    vals.append(str(getattr(obj, key)))

            return "%s\n%s" % (delimiter.join(keys), delimiter.join(vals))
        except Exception as ex:
            raise ex

    @staticmethod
    def IterableAsJSON(iterable):
        try:
            lst = []
            if iterable:
                for item in iterable:
                    if hasattr(item, "__dict__"):
                        lst.append(item.__dict__)
                    else:
                        lst.append(item)
                
            return json.dumps(lst, default=jsonSerializeHandler, indent=4)
        except Exception as ex:
            raise ex

    @staticmethod
    def IterableAsXML(iterable, root_node, item_node):
        try:
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
        except Exception as ex:
            raise ex

    @staticmethod
    def IterableAsText(iterable, keys, delimiter=None):
        try:
            if not delimiter:
                delimiter = "\t"
            outrows = []
            if iterable:
                for row in iterable:
                    cols = []
                    if hasattr(row, "__dict__"):
                        # might be an object, which has the __dict__ builtin
                        for key in keys:
                            cols.append(str(row.__dict__[key]))
                    elif isinstance(row, dict):
                        # but if it actually IS a dict...
                        for key in keys:
                            cols.append(str(row[key]))
                    else:
                        # but if they're not, just return the whole row
                        cols.append(str(row))
                    outrows.append(delimiter.join(cols))
              
            return "%s\n%s" % (delimiter.join(keys), "\n".join(outrows))
        except Exception as ex:
            raise ex

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
    Deployment = 70
    DeploymentTemplate = 71
    DeploymentService = 72
