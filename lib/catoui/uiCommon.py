
# Copyright 2012 Cloud Sidekick
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:# www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import web
import os
import traceback
import json
import cgi
import re
import copy
import base64

from catolog import catolog
from catoconfig import catoconfig
from catocommon import catocommon
from catosettings import settings
from catoui import uiGlobals
from catouser import catouser
from catotag import tag
from catoerrors import SessionError

logger = catolog.get_logger(__name__)


def set_content_type(path):
    if ".js" in path:
        web.header('Content-Type', 'application/javascript')
    elif ".css" in path:
        web.header('Content-Type', 'text/css')
    elif ".html" in path:
        web.header('Content-Type', 'text/html')
    elif ".xml" in path:
        web.header('Content-Type', 'text/xml')
    elif ".png" in path:
        web.header('Content-type', 'image/png')
    elif ".jpg" in path or ".jpeg" in path:
        web.header('Content-type', 'image/jpeg')
    elif ".gif" in path:
        web.header('Content-type', 'image/gif')
    elif ".ico" in path:
        web.header('Content-type', 'image/x-icon')
    elif ".svg" in path:
        web.header('Content-type', 'image/svg+xml')
    elif ".woff" in path:
        web.header('Content-type', 'font/woff')
    elif ".ttf" in path:
        web.header('Content-type', 'application/x-font-truetype')
    elif ".otf" in path:
        web.header('Content-type', 'application/x-font-opentype')
    elif ".eot" in path:
        web.header('Content-type', 'application/vnd.ms-fontobject')
    elif ".tif" in path or ".tiff" in path:
        web.header('Content-type', 'image/tiff')
    elif ".csv" in path:
        web.header('Content-Type', 'text/csv')
    else:
        web.header('Content-Type', 'text/plain')


def log(msg, debuglevel=0):
    """ 
    This function is used by the UI's, because it adds the User ID to the log message.
    """
    if msg:
        try:
            user = GetSessionUserFullName()
            msg = "%s :: %s" % (user, msg)
        except:
            """ do nothing if there's no user - it may be pre-login """

        log_nouser(msg, debuglevel)

def log_nouser(msg, debuglevel=2):
    # TODO!!! this whole function will go away as logger.foo goes everywhere
    if msg:
        if debuglevel == 4:
            logger.debug(msg)
        elif debuglevel == 3:
            logger.info(msg)
        elif debuglevel == 2:
            logger.warning(msg)
        else:
            logger.error(msg)

def check_roles(method):
    # if you wanna enable verbose page view logging, this is the place to do it.
    s_set = settings.settings.security()
    if s_set.PageViewLogging:
        catocommon.add_security_log(GetSessionUserID(), catocommon.SecurityLogTypes.Usage, catocommon.SecurityLogActions.PageView, 0, method, method)

    user_role = GetSessionUserRole()
    if user_role == "Administrator":
        return True

    if method in uiGlobals.RoleMethods:
        mapping = uiGlobals.RoleMethods[method]
        if mapping is True:
            return True

        if user_role in mapping:
            return True
        else:
            log("User requesting %s - insufficient permissions" % method)
            return False
    else:
        log("ERROR: %s does not have a role mapping." % method)
        return False

def getAjaxArgs():
    """Just returns the whole posted json as a json dictionary"""
        # maybe it was a GET?  check web.input()
    data = dict(web.input())
    if data:
        return dict(data)
    else:
        data = web.data()
        if data:
            return json.loads(data)
        else:
            return {}


def getAjaxArg(sArg, sDefault=""):
    """Picks out and returns a single value."""
    try:
        data = web.data()
        dic = None
        if data:
            dic = json.loads(data)
        else:
            # maybe it was a GET?  check web.input()
            dic = dict(web.input())

        if dic:
            return dic.get(sArg, sDefault)
        else:
            return sDefault
    except ValueError:
        raise Exception("getAjaxArg - no JSON arguments to decode. This method required a POST with JSON arguments.")

def GetCookie(sCookie):
    cookie = web.cookies().get(sCookie)
    if cookie:
        return cookie
    else:
        log_nouser("Warning: Attempt to retrieve cookie [%s] failed - cookie doesn't exist.  This is usually OK immediately following a login." % sCookie, 4)
        return ""

def SetCookie(sCookie, sValue):
    try:
        web.setcookie(sCookie, sValue)
    except Exception:
        log_nouser("Warning: Attempt to set cookie [%s] failed." % sCookie, 2)
        log_nouser(traceback.format_exc(), 0)

def packJSON(sIn):
    return catocommon.packData(sIn)

def unpackJSON(sIn):
    return catocommon.unpackData(sIn)

def QuoteUp(sString):
    retval = ""

    for s in sString.split(","):
        retval += "'" + s + "',"

    return retval[:-1]  # whack the last comma

def LastIndexOf(s, pat):
    if not s:
        return -1

    return len(s) - 1 - s[::-1].index(pat)

def GetSnip(sString, iMaxLength):
    # helpful for short notes or long notes with a short title line.

    # odd behavior, but web forms seems to put just a \n as the newline entered in a textarea.
    # so I'll test for both just to be safe.
    sReturn = ""
    if sString:
        bShowElipse = False

        iLength = sString.find("\\n")
        if iLength < 0:
            iLength = sString.find("\\r\\n")
        if iLength < 0:
            iLength = sString.find("\\r")
        if iLength < 0:
            iLength = iMaxLength

        # now, if what we are showing is shorter than the entire field, show an elipse
        # if it is the entire field, set the length
        if iLength < len(sString):
            bShowElipse = True
        else:
            iLength = len(sString)

        sReturn += sString[0:iLength]
        if bShowElipse:
            sReturn += " ... "

    return SafeHTML(sReturn)

def SafeHTML(sInput):
    if sInput is not None:
        return cgi.escape(sInput)
    else:
        return ""

def FixBreaks(sInput):
    if sInput:
        return sInput.replace("\r\n", "<br />").replace("\r", "<br />").replace("\n", "<br />").replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
    else:
        return ""

def WriteObjectAddLog(oType, sObjectID, sObjectName, sLog=""):
    catocommon.write_add_log(GetSessionUserID(), oType, sObjectID, sObjectName, sLog)

def WriteObjectDeleteLog(oType, sObjectID, sObjectName, sLog=""):
    catocommon.write_delete_log(GetSessionUserID(), oType, sObjectID, sObjectName, sLog)

def WriteObjectChangeLog(oType, sObjectID, sObjectName, sLog=""):
    catocommon.write_change_log(GetSessionUserID(), oType, sObjectID, sObjectName, sLog)

def WriteObjectPropertyChangeLog(oType, sObjectID, sLabel, sFrom, sTo):
    catocommon.write_property_change_log(GetSessionUserID(), oType, sObjectID, sLabel, sFrom, sTo)

def ForceLogout(sMsg=""):
    if not sMsg:
        sMsg = "Session Ended"

    log_nouser("Forcing logout with message: " + sMsg, 4)

    # logging out kills the session
    uiGlobals.session.kill()
    raise web.seeother('/static/login.html')

def CheckSession(appname, path):
    uid = GetSessionObject("user", "user_id")
    if uid:
        return True
    else:
        # OH NO, we don't have a session!

        # Now, before we throw the user to the login page, 
        # there are two 'passthru' auth options to check
        # (if anything goes wrong, just redirect to the login page)
        i = web.input(page=None, token=None, applink=None)
        
        # is there a 'token' argument?
        if i.token:
            response = AttemptLogin(appname, token=i.token)
            response = json.loads(response)
            if response.get("result") == "success":
                path = path.replace("token=%s" % (i.token), "")
                raise web.seeother(path)
            else:
                logger.info("Token Authentication failed... [%s]" % response.get("info"))
                uiGlobals.session.kill()
                raise web.seeother('/static/login.html?msg=Token%20Authentication%20failed')
    
        # is there an 'applink' argument?
        if i.applink:
            response = AttemptLogin(appname, sid=i.applink)
            response = json.loads(response)
            if response.get("result") == "success":
                path = path.replace("applink=%s" % (i.applink), "")
                raise web.seeother(path)
            else:
                logger.info("Trust Authentication failed... [%s]" % response.get("info"))
                uiGlobals.session.kill()
                raise web.seeother('/static/login.html?msg=Trust%20Authentication%20failed')

        # putting the path in the session will enable us to 
        # go to the requested page after login
        uiGlobals.session["requested_path"] = path
        
        # DO NOT do a seeother here ... the request may have been ajax.
        # raise a SessionError, and the downstream code will handle it properly
        raise SessionError("Server Session has expired (0). Please log in again.")

def GetSessionUserID():
    uid = GetSessionObject("user", "user_id")
    if uid:
        return uid
    else:
        raise SessionError("Server Session has expired (1). Please log in again.")

def GetSessionUserName():
    un = GetSessionObject("user", "user_name")
    if un:
        return un
    else:
        raise SessionError("Server Session has expired (1a). Please log in again.")

def GetSessionUserFullName():
    fn = GetSessionObject("user", "full_name")
    if fn:
        return fn
    else:
        raise SessionError("Server Session has expired (1b). Please log in again.")

def GetSessionUserRole():
    role = GetSessionObject("user", "role")
    if role:
        return role
    else:
        raise SessionError("Server Session has expired (2). Please log in again.")

def GetSessionUserTags():
    tags = GetSessionObject("user", "tags")
    return tags if tags else []

def GetSessionObject(category, key):
    cat = uiGlobals.session.get(category, False)
    if cat:
        val = cat.get(key, None)
        if val:
            return val
        else:
            return ""
    else:
        # no category?  try the session root
        val = uiGlobals.session.get(key, False)
        if val:
            return val
        else:
            return ""

    return ""

def SetSessionObject(key, obj, category=""):
    if category:
        uiGlobals.session[category][key] = obj
    else:
        uiGlobals.session[key] = obj

def GetPermissions():
    """
    Returns a list of ALL permissions for a User.
    """
    tags = GetSessionUserTags()
    if tags:
        x = ["'%s'" % (t) for t in tags]
        tstr = ",".join(x)

        sql = """select permission from tag_permissions
            where tag_name in (%s)""" % (tstr)
        db = catocommon.new_conn()
        result = db.select_all(sql)
        db.close()

        return [x[0] for x in result] if result else []
    return []

def GetPermission(p):
    """
    Returns True if a specific permission exists for a User.
    """
    perms = GetPermissions()
    if p in perms:
        return True
    return False

def UserTagsMatch(tags2check):
    """
    Accepts input of a comma delimited string OR a list of Tags.
    
    Returns a boolean. 

    # if permissions checking is turned off, everything is allowed
    """

    if catoconfig.CONFIG["ui_permissions"] == "false":
        return True

    if GetSessionUserRole() == "Administrator":
        return True
    else:
        usertags = GetSessionUserTags()
        if usertags and tags2check:
            try:
                s2 = []
                if isinstance(tags2check, list):
                    s2 = set(tags2check)
                elif isinstance(tags2check, basestring):
                    s2 = set(tags2check.split(","))

                if s2.intersection(usertags):
                    return True
            except Exception as ex:
                    raise Exception("Unable to reconcile User Tags - input isn't a valid list of Tags.\n%s" % ex.__str__())

        return False

def FilterSetByTag(set_to_filter):
    """
    Accepts input of a comma delimited string OR a list.
    
    Returns a subset of the input - only items that match the user's tags. 

    # if permissions checking is turned off, everything is allowed
    """

    if catoconfig.CONFIG["ui_permissions"] == "false":
        return set_to_filter

    if GetSessionUserRole() == "Administrator":
        return set_to_filter
    else:
        tags = tag.ObjectTags(1, GetSessionUserID())
        filtered = []
        if tags and set_to_filter:
            try:
                s1 = set(tags)
                for item in set_to_filter:
                    # now, if the input isn't a list or csv, raise an exception
                    s2 = []
                    if isinstance(item["Tags"], list):
                        s2 = set(item["Tags"])
                    elif isinstance(item["Tags"], basestring):
                        s2 = set(item["Tags"].split(","))

                    if s1 and s2:
                        if len(s1.intersection(s2)) > 0:
                            filtered.append(item)
            except Exception as ex:
                    raise Exception("Unable to reconcile User/Object Tags - input isn't a valid list of Tags.\n%s" % ex.__str__())

        return filtered

def IsObjectAllowed(object_id, object_type):
    # if permissions checking is turned off, everything is allowed
    if catoconfig.CONFIG["ui_permissions"] == "false":
        return True

    # given a task id, we need to find the original task id,
    # then check if the user can see it based on tags
    if GetSessionUserRole() == "Administrator":
        return True

    if not object_id or not object_type:
        log("Invalid or missing Object ID or Object Type.")
        return False

    sql = """select 1 from object_tags otu
        join object_tags oto on otu.tag_name = oto.tag_name
        where (otu.object_type = 1)
        and otu.object_id = %s
        and oto.object_type = %s
        and oto.object_id = %s"""

    uid = GetSessionUserID()
    db = catocommon.new_conn()
    result = db.select_col_noexcep(sql, (uid, object_type, object_id))
    db.close()

    return catocommon.is_true(result)

#        public bool UserHasTag(string sGroup)
#        {
#            //this looks up roles by name
#            string sGroups = null;
#            sGroups = GetSessionUserTagsByName();
#            if (sGroups.IndexOf(sGroup) > -1)
#                return true;
#            else
#                return false;
#        }


# this one returns just one specific function
def GetTaskFunction(sFunctionName):
    funcs = uiGlobals.FunctionCategories.Functions
    if funcs:
        return funcs.get(sFunctionName)
    else:
        return None

def GetCloudObjectsAsList(sAccountID, sCloudID, sObjectType):
    log("Querying the cloud for %s" % sObjectType, 4)

    from catocloud import cloud

    # first, get the cloud
    c = cloud.Cloud()
    c.FromID(sCloudID)
    if c is None:
        return None, "Unable to get Cloud for ID [" + sCloudID + "]"

    # NOTE: the Cloud object has a *THIN* copy of the Provider (it doesn't include
    #    products or provider clouds.)
    # But, we actually need a full provider here, so go get it!

    full_provider = cloud.Provider.FromName(c.Provider.Name)
    cot = full_provider.GetObjectTypeByName(sObjectType)
    if cot is not None:
        if not cot.ID:
            return None, "Cannot find definition for requested object type [" + sObjectType + "]"
    else:
        return None, "GetCloudObjectType failed for [" + sObjectType + "]"

    # ok, kick out if there are no properties for this type
    if not cot.Properties:
        return None, "No properties defined for type [" + sObjectType + "]"

    # All good, let's hit the API
    sXML = ""

    from catocloud import aws

    if c.Provider.Name.lower() == "openstack":
        """not yet implemented"""
        # ACWebMethods.openstackMethods acOS = new ACWebMethods.openstackMethods()
        # sXML = acOS.GetCloudObjectsAsXML(c.ID, cot, 0000BYREF_ARG0000sErr, null)
    else:  # Amazon aws, Eucalyptus, and OpenStackAws
        awsi = aws.awsInterface()
        sXML, err = awsi.GetCloudObjectsAsXML(sAccountID, sCloudID, cot)

    if err:
        return None, err

    if not sXML:
        return None, "GetCloudObjectsAsXML returned an empty document."


    # Got results, objectify them.

    # OK look, all this namespace nonsense is annoying.  Every AWS result I've witnessed HAS a namespace
    #  (which messes up all our xpaths)
    #  but I've yet to see a result that actually has two namespaces
    #  which is the only scenario I know of where you'd need them at all.

    # So... to eliminate all namespace madness
    # brute force... parse this text and remove anything that looks like [ xmlns="<crud>"] and it's contents.

    sXML = RemoveDefaultNamespacesFromXML(sXML)

    xDoc = catocommon.ET.fromstring(sXML)
    if xDoc is None:
        return None, "API Response XML document is invalid."

    log(sXML, 4)

    # FIRST ,we have to find which properties are the 'id' value.  That'll be the key for our dictionary.
    # an id can be a composite of several property values
    # this is just so we can kick back an error if no IsID exists.
    # we build the actual id from values near the end
    sIDColumnName = ""
    for prop in cot.Properties:
        if prop.IsID:
            sIDColumnName += prop.Name

    # no sIDColumnName means we can't continue
    if not sIDColumnName:
        return None, "ID column(s) not defined for Cloud Object Type" + cot.Name

    # for each result in the xml
    #     for each column
    xRecords = xDoc.findall(cot.XMLRecordXPath)
    if len(xRecords):
        for xRecord in xRecords:
            record_id = ""
            row = []
            for prop in cot.Properties:
                # NOW PAY ATTENTION.
                # the CloudObjectTypeProperty class has a 'Value' attribute.
                # but, we obviously can't set that property of THIS instance (prop)
                # because it's gonna get changed each time.

                # so, we create a clone of that property here, and give that copy the actual value,
                # then append the copy to 'row', not the one we're looping here.

                # cosmic?  yes... it is.
                newprop = copy.copy(prop)
                log("looking for property [%s]" % newprop.Name, 4)

                # ok look, the property may be an xml attribute, or it might be an element.
                # if there is an XPath value on the column, that means it's an element.
                # the absence of an XPath means we'll look for an attribute.
                # NOTE: the attribute we're looking for is the 'name' of this property
                # which is the DataColumn.name.
                if not newprop.XPath:
                    xa = xRecord.attrib[newprop.Name]
                    if xa is not None:
                        log(" -- found (attribute) - [%s]" % xa, 4)
                        newprop.Value = xa
                        row.append(newprop)
                else:
                    # if it's a tagset column put the tagset xml in it
                    #  for all other columns, they get a lookup
                    xeProp = xRecord.find(newprop.XPath)
                    if xeProp is not None:
                        # does this column have the extended property "ValueIsXML"?
                        bAsXML = (True if newprop.ValueIsXML else False)

                        if bAsXML:
                            newprop.Value = catocommon.ET.tostring(xeProp)
                            log(" -- found (as xml) - [%s]" % newprop.Value, 4)
                        else:
                            newprop.Value = xeProp.text
                            log(" -- found - [%s]" % newprop.Value, 4)

                    # just because it's missing from the data doesn't mean we can omit the property
                    # it just has an empty value.
                    row.append(newprop)

                if newprop.IsID:
                    if not newprop.Value:
                        return None, "A property [%s] cannot be defined as an 'ID', and have an empty value." % newprop.Name
                    else:
                        log("[%s] is part of the ID... so [%s] becomes part of the ID" % (newprop.Name, newprop.Value), 4)
                        record_id += (newprop.Value if newprop.Value else "")

                # an id is required
                if not record_id:
                    return None, "Unable to construct an 'id' from property values."

            cot.Instances[record_id] = row

        return cot.Instances, None
    else:
        return None, ""

def RemoveDefaultNamespacesFromXML(xml):
    p = re.compile("xmlns=*[\"\"][^\"\"]*[\"\"]")
    allmatches = p.finditer(xml)
    for match in allmatches:
        xml = xml.replace(match.group(), "")
    return xml

def AddNodeToXMLColumn(sTable, sXMLColumn, sWhereClause, sXPath, sXMLToAdd):
    # BE WARNED! this function is shared by many things, and should not be enhanced
    # with sorting or other niceties.  If you need that stuff, build your own function.
    # AddRegistry:Node is a perfect example... we wanted sorting on the registries, and also we don't allow array.
    # but parameters for example are by definition arrays of parameter nodes.
    db = catocommon.new_conn()
    log("Adding node [%s] to [%s] in [%s.%s where %s]." % (sXMLToAdd, sXPath, sTable, sXMLColumn, sWhereClause), 4)
    sSQL = "select " + sXMLColumn + " from " + sTable + " where " + sWhereClause
    sXML = db.select_col_noexcep(sSQL)
    if not sXML:
        log("Unable to get xml." + db.error)
    else:
        # parse the doc from the table
        log(sXML, 4)
        xd = catocommon.ET.fromstring(sXML)
        if xd is None:
            log("Error: Unable to parse XML.")

        # get the specified node from the doc, IF IT'S NOT THE ROOT
        # either a blank xpath, or a single word that matches the root, both match the root.
        # any other path DOES NOT require the root prefix.
        if sXPath == "":
            xNodeToEdit = xd
        elif xd.tag == sXPath:
            xNodeToEdit = xd
        else:
            xNodeToEdit = xd.find(sXPath)

        if xNodeToEdit is None:
            log("Error: XML does not contain path [" + sXPath + "].")
            return

        # now parse the new section from the text passed in
        xNew = catocommon.ET.fromstring(sXMLToAdd)
        if xNew is None:
            log("Error: XML to be added cannot be parsed.")

        # if the node we are adding to has a text value, sadly it has to go.
        # we can't detect that, as the Value property shows the value of all children.
        # but this works, even if it seems backwards.
        # if the node does not have any children, then clear it.  that will safely clear any
        # text but not stomp the text of the children.
        if len(xNodeToEdit) == 0:
            xNodeToEdit.text = ""
        # add it to the doc
        xNodeToEdit.append(xNew)


        # then send the whole doc back to the database
        sSQL = "update " + sTable + " set " + sXMLColumn + " = %s where " + sWhereClause
        if not db.exec_db_noexcep(sSQL, (catocommon.ET.tostring(xd))):
            log("Unable to update XML Column [" + sXMLColumn + "] on [" + sTable + "]." + db.error)

    return

def SetNodeValueinXMLColumn(sTable, sXMLColumn, sWhereClause, sNodeToSet, sValue):
    db = catocommon.new_conn()
    log("Setting node [%s] to [%s] in [%s.%s where %s]." % (sNodeToSet, sValue, sTable, sXMLColumn, sWhereClause), 4)
    sSQL = "select " + sXMLColumn + " from " + sTable + " where " + sWhereClause
    sXML = db.select_col_noexcep(sSQL)
    if not sXML:
        log("Unable to get xml." + db.error)
    else:
        # parse the doc from the table
        xd = catocommon.ET.fromstring(sXML)
        if xd is None:
            log("Error: Unable to parse XML.")

        # get the specified node from the doc, IF IT'S NOT THE ROOT
        if xd.tag == sNodeToSet:
            xNodeToSet = xd
        else:
            xNodeToSet = xd.find(sNodeToSet)

        if xNodeToSet is not None:
            xNodeToSet.text = sValue

            # then send the whole doc back to the database
            sSQL = "update " + sTable + " set " + sXMLColumn + " = %s where " + sWhereClause
            if not db.exec_db_noexcep(sSQL, (catocommon.ET.tostring(xd))):
                log("Unable to update XML Column [" + sXMLColumn + "] on [" + sTable + "]." + db.error)
        else:
            log("Unable to update XML Column ... [" + sNodeToSet + "] not found.")

    return

def SetNodeAttributeinXMLColumn(sTable, sXMLColumn, sWhereClause, sNodeToSet, sAttribute, sValue):
    # THIS ONE WILL do adds if the attribute doesn't exist, or update it if it does.
    db = catocommon.new_conn()
    log("Setting [%s] attribute [%s] to [%s] in [%s.%s where %s]" % (sNodeToSet, sAttribute, sValue, sTable, sXMLColumn, sWhereClause), 4)

    sXML = ""

    sSQL = "select " + sXMLColumn + " from " + sTable + " where " + sWhereClause
    sXML = db.select_col_noexcep(sSQL)
    if db.error:
        log("Unable to get xml." + db.error)
        return ""

    if sXML:
        # parse the doc from the table
        xd = catocommon.ET.fromstring(sXML)
        if xd is None:
            log("Unable to parse xml." + db.error)
            return ""

        # get the specified node from the doc
        # here's the rub - the request might be or the "root" node,
        # which "find" will not, er ... find.
        # so let's first check if the root node is the name we want.
        xNodeToSet = None

        if xd.tag == sNodeToSet:
            xNodeToSet = xd
        else:
            xNodeToSet = xd.find(sNodeToSet)

        if xNodeToSet is None:
        # do nothing if we didn't find the node
            return ""
        else:
            # set it
            xNodeToSet.attrib[sAttribute] = sValue


        # then send the whole doc back to the database
        sSQL = "update " + sTable + " set " + sXMLColumn + " = %s where " + sWhereClause
        if not db.exec_db_noexcep(sSQL, (catocommon.ET.tostring(xd))):
            log("Unable to update XML Column [" + sXMLColumn + "] on [" + sTable + "]." + db.error)

    return ""

def RemoveNodeFromXMLColumn(sTable, sXMLColumn, sWhereClause, sNodeToRemove):
    db = catocommon.new_conn()
    log("Removing node [%s] from [%s.%s where %s]." % (sNodeToRemove, sTable, sXMLColumn, sWhereClause), 4)
    sSQL = "select " + sXMLColumn + " from " + sTable + " where " + sWhereClause
    sXML = db.select_col_noexcep(sSQL)
    if not sXML:
        log("Unable to get xml." + db.error)
    else:
        # parse the doc from the table
        xd = catocommon.ET.fromstring(sXML)
        if xd is None:
            log("Error: Unable to parse XML.")

        # get the specified node from the doc
        xNodeToWhack = xd.find(sNodeToRemove)
        if xNodeToWhack is None:
            log("INFO: attempt to remove [%s] - the element was not found." % sNodeToRemove, 4)
            # no worries... what you want to delete doesn't exist?  perfect!
            return

        # OK, here's the deal...
        # we have found the node we want to delete, but we found it using an xpath,
        # ElementTree doesn't support deleting by xpath.
        # so, we'll use a parent map to find the immediate parent of the node we found,
        # and on the parent we can call ".remove"
        parent_map = dict((c, p) for p in xd.getiterator() for c in p)
        xParentOfNodeToWhack = parent_map[xNodeToWhack]

        # whack it
        if xParentOfNodeToWhack is not None:
            xParentOfNodeToWhack.remove(xNodeToWhack)

        sSQL = "update " + sTable + " set " + sXMLColumn + " = %s where " + sWhereClause
        if not db.exec_db_noexcep(sSQL, (catocommon.ET.tostring(xd))):
            log("Unable to update XML Column [" + sXMLColumn + "] on [" + sTable + "]." + db.error)

    return

def AttemptLogin(app_name, token=None, sid=None):
    if not app_name:
        raise Exception("Missing Application Name.")
    if not web.ctx.ip:
        raise Exception("Unable to determine client address.")

    address = "%s (%s)" % (web.ctx.ip, app_name)

    in_name = getAjaxArg("username")
    in_pwd = getAjaxArg("password")
    in_pwd = unpackJSON(in_pwd)
    new_pwd = getAjaxArg("change_password")
    new_pwd = unpackJSON(new_pwd)
    answer = getAjaxArg("answer")
    answer = unpackJSON(answer)

    u = catouser.User()

    if token:
        log("Trying Token Authentication using [%s]." % token, 3)
        result, code = u.AuthenticateToken(token, address)
        if not result:
            return json.dumps({"info": code})
    elif sid:
        sid = base64.b64decode(sid)
        log("Attempting to trust another CSK application using [%s]." % sid, 3)
        result, code = u.AuthenticateSession(sid, address)
        if not result:
            return json.dumps({"info": code})

    else:
        log("Attempting Authentication using POST args.", 3)
        # Authenticate will return the codes so we will know
        # how to respond to the login page
        # (must change password, password expired, etc)
        result, code = u.Authenticate(in_name, in_pwd, address, new_pwd, answer)
        if not result:
            if code == "disabled":
                return json.dumps({"info": "Your account has been suspended.  Please contact an Adminstrator."})
            if code == "failures":
                return json.dumps({"info": "Your account has been temporarily locked due to excessive password failures."})
            if code == "change":
                return json.dumps({"result": "change"})

            # no codes matched, but there is a message in there...
            if code:
                return json.dumps({"info": code})

            # failed with no code returned
            return json.dumps({"info": "Invalid Username or Password."})

    # So... they authenticated, but based on the users 'role' (Administrator, Developer, User) ...
    # they may not be allowed to log in to certain "app_name"s.
    # specifically, the User role cannot log in to the "Cato Admin UI" app.

    # TODO: enable this when the Cato EE Portal is released.
#        if u.Role == "User" and "Admin" in app_name:
#            return json.dumps({"info": "Your account isn't authorized for this application."})


    # all good, put a few key things in the session, not the whole object
    # yes, I said SESSION not a cookie, otherwise it could be hacked client side

    current_user = {}
    current_user["session_id"] = u.SessionID
    current_user["user_id"] = u.ID
    current_user["user_name"] = u.LoginID
    current_user["full_name"] = u.FullName
    current_user["role"] = u.Role
    current_user["tags"] = u.Tags
    current_user["email"] = u.Email
    current_user["ip_address"] = address
    SetSessionObject("user", current_user)

    # bit of a hack here... this function was given a pretty "app_name", but we want the non-pretty one.
    cookiename = "%s-applink" % (app_name.replace(" ", "_").lower())
    SetCookie(cookiename, base64.b64encode(u.SessionID))

    log("Login granted for: %s" % (u.FullName), 3)
    log(uiGlobals.session.user, 4)

    # update the security log
    catocommon.add_security_log(u.ID, catocommon.SecurityLogTypes.Security,
        catocommon.SecurityLogActions.UserLogin, catocommon.CatoObjectTypes.User, "",
        "Login to [%s] from [%s] granted." % (app_name, address))

    return json.dumps({"result": "success"})

def GetQuestion():
    in_name = getAjaxArg("username")

    u = catouser.User()
    u.FromName(in_name)

    # again with the generic messages.
    if not u.ID:
        return json.dumps({"info": "Unable to reset password for user."})
    if not u.SecurityQuestion:
        return json.dumps({"info": "Unable to reset password.  Contact an Administrator."})


    return json.dumps({"result": packJSON(u.SecurityQuestion)})

def UpdateHeartbeat():
    # NOTE: this needs all the kick and warn stuff
    uid = GetSessionUserID()
    ip = GetSessionObject("user", "ip_address")

    if uid and ip:
        sSQL = "update user_session set heartbeat = now() where user_id = '%s' and address = '%s'" % (uid, ip)
        db = catocommon.new_conn()
        if not db.exec_db_noexcep(sSQL):
            log_nouser(db.error, 0)
        db.close()
    return ""

def WriteClientLog(msg, debuglevel=2):
    if msg:
        # logger.warning("TODO: this should write to the client logfile...")
        log("CLIENT - %s" % (msg))  # , debuglevel, "%s_client.log" % app)

    return ""

def GetPager(rowcount, maxrows, page):
    # no pager if there's not enough rows
    if rowcount <= maxrows:
        return 0, None, ""

    maxrows = maxrows if maxrows else 25
    try:
        page = int(page)
    except:
        page = 1

    mod = rowcount % maxrows
    numpages = (rowcount / maxrows) + 1 if mod else (rowcount / maxrows)
    start = (maxrows * page) - maxrows
    end = start + maxrows

    pager_html = ""
    if numpages:
        pager = []
        for i in range(numpages):
            i += 1
            selected = "pager_button_selected" if i == page else ""
            pager.append("<span class=\"pager_button %s\">%d</span>" % (selected, i))

        pager_html = "".join(pager)

    # log("showing page %d items %d to %d" % (page, start, end), 3)

    return start, end, pager_html

def LoadTaskCommands():
    from catotask import taskCommands
    # we load two classes here...
    # first, the category/function hierarchy
    cats = taskCommands.FunctionCategories()
    cats.Load(os.path.join(os.environ["CSK_HOME"], "cato", "lib", "catotask", "task_commands.xml"))

    # we've got the AWS commands in our controlled source.  They're not extensions.
    cats.Load(os.path.join(os.environ["CSK_HOME"], "cato", "lib", "catotask", "aws_commands.xml"))

    # try to append any extension files
    # this will read all the xml files in /extensions
    # and append to sErr if it failed, but not crash or die.

    # extension paths are defined in config.
    for n, p in catoconfig.CONFIG["extensions"].iteritems():
        for root, subdirs, files in os.walk(p):
            for f in files:
                ext = os.path.splitext(f)[-1]
                if ext == ".xml":
                    fullpath = os.path.join(root, f)
                    cats.Load(fullpath)

    # Command categories and functions are an object, loaded from XML when the
    # service starts, and stored on the uiGlobals module.
    uiGlobals.FunctionCategories = cats

    return True


def GetLog():
    """
    delivers an html page with a refresh timer.  content is the last n rows of the logfile
    """
    lines = getAjaxArg("lines")
    lines = lines if lines else "1000"

    refresh = 10000
    r = getAjaxArg("refresh")
    if r:
        try:
            refresh = int(r) * 1000
        except:
            pass

    # if 'process' is omitted, return the logfile for this process
    process = getAjaxArg("process")
    if process:
        process = os.path.join(catolog.LOGPATH, "%s.log" % process)
    else:
        process = catolog.LOGFILE

    l = os.popen("tail -n %s %s" % (lines, process)).readlines()
    html = """<!DOCTYPE html>
    <html>
        <head>
        </head>
        <body>
            <pre>%s</pre>
            <div style="height: 20px;"></div>
            <a id="bottom">
            <script type="text/javascript">
                window.scrollTo(0, document.body.scrollHeight);
                setInterval(function() {location.reload();}, %d);
            </script>
        </body>
    </html>
    """ % ("".join(l), refresh)

    return html

def SetDebug():
    debug = getAjaxArg("debug")
    if debug:
        logger.critical("Changing debug level to %s." % debug)
        catolog.set_debug(debug)

    return "Debug successfully changed."

# For saving/reading a deployment template icon from the database.
def SaveAppIcon(template_id, img):
    db = catocommon.new_conn()
    sql = "update deployment_template set icon = %s where template_id = %s"
    db.exec_db(sql, (base64.b64encode(img), template_id))
    db.close()
    return ""

def GetAppIcon(template_id):
    db = catocommon.new_conn()
    sql = "select icon from deployment_template where template_id = %s"
    img = db.select_col(sql, (template_id))
    db.close()
    if img:
        return base64.b64decode(img)
    else:
        # this is a default image if there's no icon on the template.
        return base64.b64decode("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")
