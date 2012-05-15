import urllib
import urllib2
import uiGlobals
import sys
import traceback
import json
import uuid
import base64
import cgi
import re
import pickle
import xml.etree.ElementTree as ET
from catocommon import catocommon

# writes to stdout using the catocommon.server output function
# also prints to the console.
def log(msg, debuglevel = 2):
    if debuglevel <= uiGlobals.debuglevel:
        user_id = ""
        try:
            user_id = GetSessionUserID()
        except:
            """ do nothing if there's no user - it may be pre-login """
            
        if not user_id:
            user_id = ""
            
        log_nouser(msg, debuglevel)

def log_nouser(msg, debuglevel = 2):
    if debuglevel <= uiGlobals.debuglevel:
        try:
            if msg:
                uiGlobals.server.output(str(msg))
                print str(msg)
        except:
            if msg:
                uiGlobals.server.output(msg)
                print msg

def CatoEncrypt(s):
    return catocommon.cato_encrypt(s)

def CatoDecrypt(s):
    return catocommon.cato_decrypt(s)

def getAjaxArgs():
    """Just returns the whole posted json as a json dictionary"""
    data = uiGlobals.web.data()
    return json.loads(data)

def getAjaxArg(sArg, sDefault=""):
    """Picks out and returns a single value."""
    data = uiGlobals.web.data()
    dic = json.loads(data)
    
    if dic.has_key(sArg):
        if dic[sArg]:
            return dic[sArg]
        else:
            return sDefault
    else:
        return sDefault

def GetCookie(sCookie):
    cookie=uiGlobals.web.cookies().get(sCookie)
    if cookie:
        return cookie
    else:
        log("Warning: Attempt to retrieve cookie [%s] failed - cookie doesn't exist.  This is usually OK immediately following a login." % sCookie, 3)
        return ""

def SetCookie(sCookie, sValue):
    try:
        uiGlobals.web.setcookie(sCookie, sValue)
    except Exception:
        log("Warning: Attempt to set cookie [%s] failed." % sCookie, 2)
        uiGlobals.request.Messages.append(traceback.format_exc())

def NewGUID():
    return str(uuid.uuid1())

def IsGUID(s):
    if not s:
        return False

    p = re.compile("^(\{{0,1}([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}-([0-9a-fA-F]){12}\}{0,1})$")
    m = p.match(s)
    if m:
        return True
    else:
        return False

def IsTrue(var):
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
         
def TickSlash(s):
    """ Prepares string values for string concatenation, or insertion into MySql. """
    return s.replace("'", "''").replace("\\", "\\\\").replace("%", "%%")

def packJSON(sIn):
    if not sIn:
        return sIn
    sOut = base64.b64encode(sIn)
    return sOut.replace("/", "%2F").replace("+", "%2B")

def unpackJSON(sIn):
    if not sIn:
        return sIn
    
    sOut = sIn.replace("%2F", "/").replace("%2B", "+")
    return base64.b64decode(sOut)

def QuoteUp(sString):
    retval = ""
    
    for s in sString.split(","):
        retval += "'" + s + "',"
    
    return retval[:-1] #whack the last comma 

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
    return cgi.escape(sInput)

def FixBreaks(sInput):
    return sInput.replace("\r\n", "<br />").replace("\r", "<br />").replace("\n", "<br />").replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")

def AddSecurityLog(LogType, Action, ObjectType, ObjectID, LogMessage):
    uiGlobals.request.Function = __name__ + "." + sys._getframe().f_code.co_name
    
    sTrimmedLog = TickSlash(LogMessage).strip()
    if sTrimmedLog:
        if len(sTrimmedLog) > 7999:
            sTrimmedLog = sTrimmedLog[:7998]
    sSQL = "insert into user_security_log (log_type, action, user_id, log_dt, object_type, object_id, log_msg) \
        values ('" + LogType + "', '" + Action + "', '" + GetSessionUserID() + "', now(), " + str(ObjectType) + ", '" + ObjectID + "', '" + sTrimmedLog + "')"
    if not uiGlobals.request.db.exec_db_noexcep(sSQL):
        uiGlobals.request.Messages.append(uiGlobals.request.db.error)

def WriteObjectAddLog(oType, sObjectID, sObjectName, sLog = ""):
    if sObjectID and sObjectName:
        if not sLog:
            sLog = "Created: [" + TickSlash(sObjectName) + "]."
        else:
            sLog = "Created: [" + TickSlash(sObjectName) + "] - [" + sLog + "]"

        AddSecurityLog(uiGlobals.SecurityLogTypes.Object, uiGlobals.SecurityLogActions.ObjectAdd, oType, sObjectID, sLog)

def WriteObjectDeleteLog(oType, sObjectID, sObjectName, sLog = ""):
    if sObjectID and sObjectName:
        if not sLog:
            sLog = "Deleted: [" + TickSlash(sObjectName) + "]."
        else:
            sLog = "Deleted: [" + TickSlash(sObjectName) + "] - [" + sLog + "]"

        AddSecurityLog(uiGlobals.SecurityLogTypes.Object, uiGlobals.SecurityLogActions.ObjectDelete, oType, sObjectID, sLog)

def WriteObjectChangeLog(oType, sObjectID, sObjectName, sLog = ""):
    if sObjectID and sObjectName:
        if not sObjectName:
            sObjectName = "[" + TickSlash(sObjectName) + "]."
        else:
            sLog = "Changed: [" + TickSlash(sObjectName) + "] - [" + sLog + "]"

        AddSecurityLog(uiGlobals.SecurityLogTypes.Object, uiGlobals.SecurityLogActions.ObjectAdd, oType, sObjectID, sLog)

def WriteObjectPropertyChangeLog(oType, sObjectID, sLabel, sFrom, sTo):
    if sFrom and sTo:
        if sFrom != sTo:
            sLog = "Changed: " + sLabel + " from [" + TickSlash(sFrom) + "] to [" + TickSlash(sTo) + "]."
            AddSecurityLog(uiGlobals.SecurityLogTypes.Object, uiGlobals.SecurityLogActions.ObjectAdd, oType, sObjectID, sLog)

def PrepareAndEncryptParameterXML(sParameterXML):
    try:
        if sParameterXML:
            xDoc = ET.fromstring(sParameterXML)
            if xDoc is None:
                uiGlobals.request.Messages.append("Parameter XML data is invalid.")
    
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
    except Exception:
        uiGlobals.request.Messages.append(traceback.format_exc())

def GenerateScheduleLabel(sMo, sDa, sHo, sMi, sDW):
    sDesc = ""
    sTooltip = ""

    # we can analyze the details and come up with a pretty name for this schedule.
    # this may need to be it's own web method eventually...
    if sMo != "0,1,2,3,4,5,6,7,8,9,10,11,":
        sDesc += "Some Months, "

    if sDW == "0":
        # explicit days 
        if sDa == "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,":
            sDesc += "Every Day, "
    else:
        # weekdays
        if sDa == "0,1,2,3,4,5,6,":
            sDesc += "Every Weekday, "
        else:
            sDesc += "Some Days, "

    # hours and minutes labels play together, and are sometimes exclusive of one another
    # we'll figure that out later...

    if sHo == "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,":
        sDesc += "Hourly, "
    else:
        sDesc += "Selected Hours, "

    if sMi == "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,":
        sDesc += "Every Minute"
    else:
        sDesc += "Selected Minutes"

    # just use the guid if we couldn't derive a label.
    if sDesc != "":
        sDesc += "."




    # build a verbose description too
    sTmp = ""

    # months
    if sMo == "0,1,2,3,4,5,6,7,8,9,10,11,":
        sTmp = "Every Month"
    else:
        sTmp = sMo[:-1].replace("0", "Jan").replace("1", "Feb").replace("2", "Mar").replace("3", "Apr").replace("4", "May").replace("5", "Jun").replace("6", "Jul").replace("7", "Aug").replace("8", "Sep").replace("9", "Oct").replace("10", "Nov").replace("11", "Dec")
    sTooltip += "Months: (" + sTmp + ")<br />\n"

    # days
    sTmp = ""
    if sDW == "0":
        if sDa == "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,":
            sTmp = "Every Day"
        else:
            a = sDa.split(',')
            for s in a:
                # individual days are +1
                a2 = []
                if s:
                    a2.append(str(int(s) + 1))
                    sTmp = ",".join(a2)

        sTooltip += "Days: (" + sTmp + ")<br />\n"
    else:
        if sDa == "0,1,2,3,4,5,6,":
            sTmp = "Every Weekday"
        else:
            sTmp = sDa[:-1].replace("0", "Sun").replace("1", "Mon").replace("2", "Tue").replace("3", "Wed").replace("4", "Thu").replace("5", "Fri").replace("6", "Sat")

        sTooltip += "Weekdays: (" + sTmp + ")<br />\n"

    # hours
    sTmp = ""
    if sHo == "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,":
        sTmp = "Every Hour"
    else:
        sTmp = sHo[:-1]
    sTooltip += "Hours: (" + sTmp + ")<br />\n"

    # minutes
    sTmp = ""
    if sMi == "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,":
        sTmp = "Every Minute"
    else:
        sTmp = sMi[:-1]
    sTooltip += "Minutes: (" + sTmp + ")<br />\n"

    return sDesc, sTooltip


def ForceLogout(sMsg):
    if not sMsg:
        sMsg = "Session Ended"
    
    # logging out kills the session
    uiGlobals.session.kill()
    
    log("Forcing logout with message: " + sMsg, 0)
    raise uiGlobals.web.seeother('/login?msg=' + urllib.quote_plus(sMsg))

def GetSessionUserID():
    try:
        uid = GetSessionObject("user", "user_id")
        if uid:
            return uid
        else:
            ForceLogout("Server Session has expired (1). Please log in again.")
    except Exception:
        uiGlobals.request.Messages.append(traceback.format_exc())

def GetSessionObject(category, key):
    try:
        cat = uiGlobals.session.get(category, False)
        if cat:
            val = cat.get(key, None)
            if val:
                return val
            else:
                return ""
        else:
            #no category?  try the session root
            val = uiGlobals.session.get(key, False)
            if val:
                return val
            else:
                return ""
        
        return ""
    except Exception:
        uiGlobals.request.Messages.append(traceback.format_exc())

def SetSessionObject(key, obj, category=""):
    if category:
        uiGlobals.session[category][key] = obj
    else:
        uiGlobals.session[key] = obj
    
#this one returns a list of Categories from the FunctionCategories class
def GetTaskFunctionCategories():
    try:
        f = open("datacache/_categories.pickle", 'rb')
        if not f:
            log("ERROR: Categories pickle missing.", 0)
        obj = pickle.load(f)
        f.close()
        if obj:
            return obj.Categories
        else:
            log("ERROR: Categories pickle could not be read.", 0)
    except Exception:
        log("ERROR: Categories pickle could not be read." + traceback.format_exc(), 0)
        
    return None
        
    # return GetSessionObject("", "function_categories")

#this one returns the Functions dict containing all functions
def GetTaskFunctions():
    try:
        f = open("datacache/_categories.pickle", 'rb')
        if not f:
            log("ERROR: Categories pickle missing.", 0)
        obj = pickle.load(f)
        f.close()
        if obj:
            return obj.Functions
        else:
            log("ERROR: Categories pickle could not be read.", 0)
    except Exception:
        log("ERROR: Categories pickle could not be read." + traceback.format_exc(), 0)
        
    return None
    # return GetSessionObject("", "functions")

#this one returns just one specific function
def GetTaskFunction(sFunctionName):
    funcs = GetTaskFunctions()
    if funcs:
        try:
            fn = funcs[sFunctionName]
            if fn:
                return fn
            else:
                return None
        except Exception:
            return None
    else:
        return None

def HTTPGetNoFail(url):
    """
    This function does not fail.  For any errors it returns an empty result.

    NOTE: this function is called by unauthenticated pages.
    DO NOT use any of the helper functions like uiCommon.log - they look for a user and kick back to the login page 
    if none is found.  (infinite_loop = bad)
    
    That's why we're using log_nouser.
    
    """
    try:
        import socket
        socket.setdefaulttimeout(5)
        
        log_nouser("Trying an HTTP GET to %s" % url, 4)
        if not url:
            return ""
        
        f = urllib2.urlopen(url)
        result = f.read()
        
        # PUT THE SOCKET TIMEOUT BACK! it's global!
        socket.setdefaulttimeout(None)

        if result:
            return result
        else:
            return ""
        
    except Exception:
        log_nouser(traceback.format_exc(), 4)
