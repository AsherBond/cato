
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
try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

from catolog import catolog
from catoconfig import catoconfig
from catocommon import catocommon
from catosettings import settings
from catoui import uiGlobals
from catouser import catouser
from catotag import tag

logger = catolog.get_logger(__name__)

def log(msg, debuglevel=0):
    """ 
    This function is used by the UI's, because it adds the User ID to the log message.
    """
    if msg:
        user_id = ""
        try:
            user_id = GetSessionUserID()
            msg = "%s :: %s" % (user_id, msg)
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
    
    if uiGlobals.RoleMethods.has_key(method):
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

def CatoEncrypt(s):
    return catocommon.cato_encrypt(s)

def CatoDecrypt(s):
    return catocommon.cato_decrypt(s)

def getAjaxArgs():
    """Just returns the whole posted json as a json dictionary"""
    data = web.data()
    if data:
        return json.loads(data)
    else:
        # maybe it was a GET?  check web.input()
        data = dict(web.input())
        if data:
            return dict(data)
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
            if dic.has_key(sArg):
                if dic[sArg]:
                    return dic[sArg]
                else:
                    return sDefault
            else:
                return sDefault
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

def PrepareAndEncryptParameterXML(sParameterXML):
    if sParameterXML:
        xDoc = ET.fromstring(sParameterXML)
        if xDoc is None:
            log("Parameter XML data is invalid.")

        # now, all we're doing here is:
        #  a) encrypting any new values
        #  b) moving any oev values from an attribute to a value
        
        #  a) encrypt new values
        for xToEncrypt in xDoc.findall("parameter/values/value[@do_encrypt='true']"):
            xToEncrypt.text = CatoEncrypt(xToEncrypt.text)
            del xToEncrypt.attrib["do_encrypt"]

        # b) unbase64 any oev's and move them to values
        for xToEncrypt in xDoc.findall("parameter/values/value[@oev='true']"):
            xToEncrypt.text = unpackJSON(xToEncrypt.text)
            del xToEncrypt.attrib["oev"]
        
        return ET.tostring(xDoc)
    else:
        return ""

def ForceLogout(sMsg=""):
    if not sMsg:
        sMsg = "Session Ended"
    
    log_nouser("Forcing logout with message: " + sMsg, 0)
    
    # logging out kills the session
    uiGlobals.session.kill()
    raise web.seeother('/static/login.html')

def GetSessionUserID():
    uid = GetSessionObject("user", "user_id")
    if uid:
        return uid
    else:
        ForceLogout("Server Session has expired (1). Please log in again.")

def GetSessionUserName():
    un = GetSessionObject("user", "user_name")
    if un:
        return un
    else:
        ForceLogout("Server Session has expired (1a). Please log in again.")

def GetSessionUserFullName():
    fn = GetSessionObject("user", "full_name")
    if fn:
        return fn
    else:
        ForceLogout("Server Session has expired (1b). Please log in again.")

def GetSessionUserRole():
    role = GetSessionObject("user", "role")
    if role:
        return role
    else:
        ForceLogout("Server Session has expired (2). Please log in again.")

def GetSessionUserTags():
    tags = GetSessionObject("user", "tags")
    if tags:
        return tags
    else:
        ForceLogout("Server Session has expired (3). Please log in again.")

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
    
def FilterSetByTag(rows):
    # if permissions checking is turned off, everything is allowed
    if catoconfig.CONFIG["ui_permissions"] == "false":
        return rows
    
    if GetSessionUserRole() == "Administrator":
        return rows
    else:
        tags = tag.ObjectTags(1, GetSessionUserID())
        filtered = []
        if tags:
            for row in rows:
                if set(tags) & set(row["Tags"].split(",") if row["Tags"] else []):
                    filtered.append(row)
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

    
#this one returns just one specific function
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
    
    cot = c.Provider.GetObjectTypeByName(sObjectType)
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

    xDoc = ET.fromstring(sXML)
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
                            newprop.Value = ET.tostring(xeProp)
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
    
def AddTaskInstance(sUserID, sTaskID, sScopeID, sAccountID, sAssetID, sParameterXML, sDebugLevel):
    if not sUserID: return ""
    if not sTaskID: return ""
    
    sParameterXML = unpackJSON(sParameterXML)
                    
    # we gotta peek into the XML and encrypt any newly keyed values
    sParameterXML = PrepareAndEncryptParameterXML(sParameterXML);                

    if catocommon.is_guid(sTaskID) and catocommon.is_guid(sUserID):
        ti = catocommon.add_task_instance(sTaskID, sUserID, sDebugLevel, sParameterXML, sScopeID, sAccountID, "", "")
        log("Starting Task [%s] ... Instance is [%s]" % (sTaskID, ti), 3)
        return ti
    else:
        log("Unable to run task. Missing or invalid task [" + sTaskID + "] or user [" + sUserID + "] id.")

    # uh oh, return nothing
    return ""
    
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
        xd = ET.fromstring(sXML)
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
        xNew = ET.fromstring(sXMLToAdd)
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
        sSQL = "update " + sTable + " set " + sXMLColumn + " = '" + catocommon.tick_slash(ET.tostring(xd)) + "'" \
            " where " + sWhereClause
        if not db.exec_db_noexcep(sSQL):
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
        xd = ET.fromstring(sXML)
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
            sSQL = "update " + sTable + " set " + sXMLColumn + " = '" + catocommon.tick_slash(ET.tostring(xd)) + "' where " + sWhereClause
            if not db.exec_db_noexcep(sSQL):
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
        xd = ET.fromstring(sXML)
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
        sSQL = "update " + sTable + " set " + sXMLColumn + " = '" + catocommon.tick_slash(ET.tostring(xd)) + "'" \
            " where " + sWhereClause
        if not db.exec_db_noexcep(sSQL):
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
        xd = ET.fromstring(sXML)
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

        sSQL = "update " + sTable + " set " + sXMLColumn + " = '" + catocommon.tick_slash(ET.tostring(xd)) + "'" \
            " where " + sWhereClause
        if not db.exec_db_noexcep(sSQL):
            log("Unable to update XML Column [" + sXMLColumn + "] on [" + sTable + "]." + db.error)

    return

def AttemptLogin(app_name):
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
    
    # Authenticate will return the codes so we will know
    # how to respond to the login page
    # (must change password, password expired, etc)
    result, code = u.Authenticate(in_name, in_pwd, address, new_pwd, answer)
    if not result:
        if code == "disabled":
            return "{\"info\" : \"Your account has been suspended.  Please contact an Adminstrator.\"}"
        if code == "failures":
            return "{\"info\" : \"Your account has been temporarily locked due to excessive password failures.\"}"
        if code == "change":
            return "{\"result\" : \"change\"}"
        
        # no codes matched, but there is a message in there...
        if code:
            return "{\"info\" : \"%s\"}" % code

        # failed with no code returned
        return "{\"info\" : \"Invalid Username or Password.\"}"

    # So... they authenticated, but based on the users 'role' (Administrator, Developer, User) ...
    # they may not be allowed to log in to certain "app_name"s.
    # specifically, the User role cannot log in to the "Cato Admin UI" app.
    
    # TODO: enable this when the Cato EE Portal is released.
#        if u.Role == "User" and "Admin" in app_name:
#            return "{\"info\" : \"Your account isn't authorized for this application.\"}"

    
    # all good, put a few key things in the session, not the whole object
    # yes, I said SESSION not a cookie, otherwise it could be hacked client side
    
    current_user = {}
    current_user["user_id"] = u.ID
    current_user["user_name"] = u.LoginID
    current_user["full_name"] = u.FullName
    current_user["role"] = u.Role
    current_user["tags"] = u.Tags
    current_user["email"] = u.Email
    current_user["ip_address"] = address
    SetSessionObject("user", current_user)

    log("Login granted for: ", 4)
    log(uiGlobals.session.user, 4)

    # update the security log
    catocommon.add_security_log(u.ID, catocommon.SecurityLogTypes.Security,
        catocommon.SecurityLogActions.UserLogin, catocommon.CatoObjectTypes.User, "",
        "Login to [%s] from [%s] granted." % (app_name, address))

    return json.dumps({"result" : "success"})
            
def GetQuestion():
    in_name = getAjaxArg("username")

    u = catouser.User()
    u.FromName(in_name)

    # again with the generic messages.
    if not u.ID:
        return "{\"info\" : \"Unable to reset password for user.\"}"
    if not u.SecurityQuestion:
        return "{\"info\" : \"Unable to reset password.  Contact an Administrator.\"}"


    return "{\"result\" : \"%s\"}" % packJSON(u.SecurityQuestion)

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
    cats.Load(os.path.join(os.environ["CATO_HOME"], "lib/catotask/task_commands.xml"))

    # we've got the AWS commands in our controlled source.  They're not extensions.
    cats.Load(os.path.join(os.environ["CATO_HOME"], "lib/catotask/aws_commands.xml"))

    # try to append any extension files
    # this will read all the xml files in /extensions
    # and append to sErr if it failed, but not crash or die.
    
    # extension paths are defined in config.
    expath = []
    if catoconfig.CONFIG.has_key("extension_path"):
        expath = catoconfig.CONFIG["extension_path"].split(";")
    
    for p in expath:
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

"""
    These two functions are called by handlers in both the UIs.
"""  
def GetWidget():
    """Simply proxies an HTTP GET to another domain, and returns the results."""
    args = getAjaxArgs()
    url = get_dash_url()
    result, err = catocommon.http_post("%s/widget" % url, args, 15)
    if err:
        return "Unable to reach the Dash API.  Is the service running?\n %s" % err
    
    return result

def GetLayout():
    """Simply proxies an HTTP GET to another domain, and returns the results."""
    args = getAjaxArgs()
    url = get_dash_url()
    result, err = catocommon.http_post("%s/layout" % url, args, 15)
    if err:
        return "Unable to reach the Dash API.  Is the service running?\n %s" % err
    
    return result

def get_dash_url():
    url = "http://localhost"
    if catoconfig.CONFIG.has_key("dash_api_url"):
        url = (catoconfig.CONFIG["dash_api_url"] if catoconfig.CONFIG["dash_api_url"] else "http://localhost")
    else:
        log("Warning: dash_api_url setting not defined in cato.conf... using http://localhost")

    port = "4002"
    if catoconfig.CONFIG.has_key("dash_api_port"):
        port = (catoconfig.CONFIG["dash_api_port"] if catoconfig.CONFIG["rest_api_port"] else "4002")
    else:
        log("Warning: dash_api_port setting not defined in cato.conf... using 4002")
        
    return "%s:%s" % (url, port)


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
    
    l = os.popen("tail -%s %s" % (lines, process)).readlines()
    html = """<!DOCTYPE html>
    <html>
        <head>
        </head>
        <body>
            <pre>%s</pre>
            <a id="bottom">
            <script type="text/javascript">
                location.hash = "#bottom";
                setInterval(location.reload, %d);
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
    
