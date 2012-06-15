#!/usr/bin/env python

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
import sys
import urllib
import pickle
import shelve
import xml.etree.ElementTree as ET

web_root = os.path.abspath(os.path.dirname(__file__))
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)
sys.path.append(web_root)

# to avoid any path issues, "cd" to the web root.
os.chdir(web_root)

# DON'T REMOVE these that Aptana shows as "unused".
# they are used, just in the URL mapping for web.py down below.
from catocommon import catocommon
from uiMethods import uiMethods
from uiMethods import logout
from uiMethods import login

from taskMethods import taskMethods
from cloudMethods import cloudMethods
from ecoMethods import ecoMethods

import uiCommon
import uiGlobals


def notfound():
    return web.notfound("Sorry, the page you were looking for was not found.")

class bypass:        
    def GET(self):
        return "This page isn't subject to the auth processor"

# the login announcement hits the Cloud Sidekick web site for a news snip
class announcement:        
    def GET(self):
        s = uiCommon.HTTPGetNoFail("http://community.cloudsidekick.com/login-page-announcement?utm_source=cato_app&utm_medium=loginpage&utm_campaign=app")
        if s:
            return s
        else:
            return ""

class getlicense:        
    def GET(self):
        license_text = """<p>
                    Copyright 2012 Cloud Sidekick
                </p>
                <p>
                    Use of this software indicates agreement with the included software LICENSE.
                </p>
                <p>
                    The LICENSE can be found in the application directory where this Cloud Sidekick product is installed.
                </p>"""
        # the value will either be 'agreed' or ''
        from settings import settings
        license_status = settings.settings.get_application_setting("general/license_status")
        if license_status == "agreed":
            return ""
        else:
            # not agreed, return the LICENSE file.
            filename = "%s/LICENSE" % base_path
            with open(filename, 'r') as f_in:
                if f_in:
                    what_came_in = f_in.read()
                    if what_came_in:
                        return uiCommon.FixBreaks(uiCommon.SafeHTML(what_came_in))

            return license_text
            

# the default page if no URI is given, just an information message
class index:        
    def GET(self):
        return render.home()

class home:        
    def GET(self):
        return render.home()

class notAllowed:        
    def GET(self):
        return render.notAllowed()

class settings:        
    def GET(self):
        return render.settings()

class assetEdit:        
    def GET(self):
        return render.assetEdit()

class credentialEdit:        
    def GET(self):
        return render.credentialEdit()

class userEdit:        
    def GET(self):
        return render.userEdit()

class taskManage:        
    def GET(self):
        return render.taskManage()

class taskEdit:        
    def GET(self):
        return render.taskEdit()

class taskRunLog:        
    def GET(self):
        return render_popup.taskRunLog()

class taskPrint:        
    def GET(self):
        return render_popup.taskPrint()

class taskActivityLog:        
    def GET(self):
        return render.taskActivityLog()

class cloudAccountEdit:        
    def GET(self):
        return render.cloudAccountEdit()

class cloudEdit:        
    def GET(self):
        return render.cloudEdit()

class cloudDiscovery:        
    def GET(self):
        return render.cloudDiscovery()

class systemStatus:        
    def GET(self):
        return render.systemStatus()

class taskStatus:        
    def GET(self):
        return render.taskStatus()

class ecoTemplateManage:        
    def GET(self):
        return render.ecoTemplateManage()

class ecoTemplateEdit:        
    def GET(self):
        return render.ecoTemplateEdit()

class ecosystemManage:        
    def GET(self):
        return render.ecosystemManage()

class ecosystemEdit:        
    def GET(self):
        return render.ecosystemEdit()

class importObject:        
    def GET(self):
        return render.importObject()

class upload:
    def GET(self):
        return """This endpoint only accepts POSTS from file_upload.html"""
    def POST(self):
        x = web.input(fupFile={}, ref_id="")
        if x:
            #print x # ref_id
            #web.debug(x['fupFile'].filename) # This is the filename
            #web.debug(x['fupFile'].value) # This is the file contents
            #web.debug(x['fupFile'].file.read()) # Or use a file(-like) object
            # raise web.seeother('/upload')
            
            ref_id = (x.ref_id if x.ref_id else "")
            filepath = "temp/%s-%s.tmp" % (uiCommon.GetSessionUserID(), ref_id)
            fullpath = "%s/%s" % (web_root, filepath)
            with open(fullpath, 'w') as f_out:
                if not f_out:
                    print "ERROR: unable to open %s for writing." % fullpath
                f_out.write(x["fupFile"].file.read()) # writes the uploaded file to the newly created file.
            
            # all done, we loop back to the file_upload.html page, but this time include
            # a qq arg - the file name
            raise web.seeother("static/pages/file_upload.html?ref_id=%s&filename=%s" % (ref_id, filepath))

class temp:
    """all we do for temp is deliver the file."""
    def GET(self, filename):
        try:
            f = open("%s/temp/%s" % (web_root, filename))
            if f:
                return f.read()
        except Exception, ex:
            return ex.__str__()
    
#Authentication preprocessor
def auth_app_processor(handle):
    path = web.ctx.path
    
    # this is very handy in verbose debugging mode for identifying errors
    uiCommon.log_nouser("Serving %s" % path, 4)
    
    # requests that are allowed, no matter what
    if path in [
        "/uiMethods/wmAttemptLogin", 
        "/uiMethods/wmGetQuestion", 
        "/logout", 
        "/notAllowed", 
        "/notfound", 
        "/announcement", 
        "/getlicense", 
        "/uiMethods/wmLicenseAgree", 
        "/uiMethods/wmUpdateHeartbeat"
        ]:
        return handle()

    # any other request requires an active session ... kick it out if there's not one.
    if not session.get('user', False):
        raise web.seeother('/static/login.html?msg=' + urllib.quote_plus("Session expired."))
    
    # check the role/method mappings to see if the requested page is allowed
    # HERE's the rub! ... some of our requests are for "pages" and others (most) are ajax calls.
    # for the pages, we can redirect to the "notAllowed" page, 
    # but for the ajax calls we can't - we need to return an acceptable ajax response.
    
    # the only way to tell if the request is for a page or an ajax
    # is to look at the name.
    # all of our ajax aware methods are called "wmXXX"
    
    if uiCommon.check_roles(path):
        return handle()
    else:
        print path
        if "Methods\/wm" in path:
            raise web.seeother('notAllowed')
        else:
            return "Some content on this page isn't available to your user."


def SetTaskCommands():
    try:
        from taskCommands import FunctionCategories
        #we load two classes here...
        #first, the category/function hierarchy
        cats = FunctionCategories()
        bCoreSuccess = cats.Load("%s/task_commands.xml" % web_root)
        if not bCoreSuccess:
            raise Exception("Critical: Unable to read/parse task_commands.xml.")

        #try to append any extension files
        #this will read all the xml files in /extensions
        #and append to sErr if it failed, but not crash or die.
        for root, subdirs, files in os.walk("%s/extensions" % web_root):
            for f in files:
                ext = os.path.splitext(f)[-1]
                if ext == ".xml":
                    fullpath = os.path.join(root, f)
                    if not cats.Append(fullpath):
                        uiCommon.log_nouser("WARNING: Unable to load extension command xml file [" + fullpath + "].", 0)

        #put the categories list in the session...
        #uiGlobals.session.function_categories = cats.Categories
        #then the dict of all functions for fastest lookups
        #uiGlobals.session.functions = cats.Functions

        # was told not to put big objects in the session, so since this can actually be shared by all users,
        # lets try saving a pickle
        # it will get created every time a user logs in, but can be read by all.
        with open("%s/datacache/_categories.pickle" % web_root, 'w') as f_out:
            if not f_out:
                print "ERROR: unable to create datacache/_categories.pickle."
            pickle.dump(cats, f_out, pickle.HIGHEST_PROTOCOL)
        
        #rebuild the cache html files
        CacheTaskCommands()

        return True
    except Exception, ex:
        uiCommon.log_nouser("Unable to load Task Commands XML." + ex.__str__(), 0)

def CacheTaskCommands():
    #creates the html cache file
    try:
        sCatHTML = ""
        sFunHTML = ""

        # so, we will use the FunctionCategories class in the session that was loaded at login, and build the list items for the commands tab.
        cats = uiCommon.GetTaskFunctionCategories()
        if not cats:
            print "Error: Task Function Categories class is not in the datacache."
        else:
            for cat in cats:
                sCatHTML += "<li class=\"ui-widget-content ui-corner-all command_item category\""
                sCatHTML += " id=\"cat_" + cat.Name + "\""
                sCatHTML += " name=\"" + cat.Name + "\">"
                sCatHTML += "<div>"
                sCatHTML += "<img class=\"category_icon\" src=\"" + cat.Icon + "\" alt=\"\" />"
                sCatHTML += "<span>" + cat.Label + "</span>"
                sCatHTML += "</div>"
                sCatHTML += "<div id=\"help_text_" + cat.Name + "\" class=\"hidden\">"
                sCatHTML += cat.Description
                sCatHTML += "</div>"
                sCatHTML += "</li>"
                
                sFunHTML += "<div class=\"functions hidden\" id=\"cat_" + cat.Name + "_functions\">"
                # now, let's work out the functions.
                # we can just draw them all... they are hidden and will display on the client as clicked
                for fn in cat.Functions:
                    sFunHTML += "<div class=\"ui-widget-content ui-corner-all command_item function\""
                    sFunHTML += " id=\"fn_" + fn.Name + "\""
                    sFunHTML += " name=\"" + fn.Name + "\">"
                    sFunHTML += "<img class=\"function_icon\" src=\"" + fn.Icon + "\" alt=\"\" />"
                    sFunHTML += "<span>" + fn.Label + "</span>"
                    sFunHTML += "<div id=\"help_text_" + fn.Name + "\" class=\"hidden\">"
                    sFunHTML += fn.Description
                    sFunHTML += "</div>"
                    sFunHTML += "</div>"

                sFunHTML += "</div>"

        with open("%s/static/_categories.html" % web_root, 'w') as f_out:
            if not f_out:
                print "ERROR: unable to create static/_categories.html."
            f_out.write(sCatHTML)

        with open("%s/static/_functions.html" % web_root, 'w') as f_out:
            if not f_out:
                print "ERROR: unable to create static/_functions.html."
            f_out.write(sFunHTML)

    except Exception, ex:
        uiCommon.log_nouser(ex.__str__(), 0)

def CacheMenu():
    #put the site.master.xml in the session here
    # this is a significant boost to performance
    xRoot = ET.parse("%s/site.master.xml" % web_root)
    if not xRoot:
        raise Exception("Critical: Unable to read/parse site.master.xml.")
        
    xMenus = xRoot.findall("mainmenu/menu") 

    sAdminMenu = ""
    sDevMenu = ""
    sUserMenu = ""

    for xMenu in xMenus:
        sLabel = xMenu.get("label", "No Label Defined")
        sHref = (" href=\"" + xMenu.get("href", "") + "\"" if xMenu.get("href") else "")
        sOnClick = (" onclick=\"" + xMenu.get("onclick", "") + "\"" if xMenu.get("onclick") else "")
        sIcon = ("<img src=\"" + xMenu.get("icon", "") + "\" alt=\"\" />" if xMenu.get("icon") else "")
        sTarget = xMenu.get("target", "")
        sClass = xMenu.get("class", "")
        sRoles = xMenu.get("roles", "")
        
        sAdminItems = ""
        sDevItems = ""
        sUserItems = ""
    
        xItems = xMenu.findall("item")
        if str(len(xItems)) > 0:
            for xItem in xItems:
                sItemLabel = xItem.get("label", "No Label Defined")
                sItemHref = (" href=\"" + xItem.get("href", "") + "\"" if xItem.get("href") else "")
                sItemOnClick = (" onclick=\"" + xItem.get("onclick", "") + "\"" if xItem.get("onclick") else "")
                sItemIcon = ("<img src=\"" + xItem.get("icon", "") + "\" alt=\"\" />" if xItem.get("icon") else "")
                sItemTarget = xItem.get("target", "")
                sItemClass = xItem.get("class", "")
                sItemRoles = xItem.get("roles", "")

                sItem = "<li class=\"ui-widget-header %s\" style=\"cursor: pointer;\"><a %s %s %s> %s %s</a></li>" % (sItemClass, sItemOnClick, sItemHref, sItemTarget, sItemIcon, sItemLabel)
                
                sAdminItems += sItem
                
                if "all" in sItemRoles:
                    sUserItems += sItem 
                    sDevItems += sItem 
                else: 
                    if "user" in sItemRoles:
                        sUserItems += sItem 
                    if "developer" in sItemRoles:
                        sDevItems += sItem 

            sUserItems = "<ul>%s</ul>" % sUserItems
            sDevItems = "<ul>%s</ul>" % sDevItems
            sAdminItems = "<ul>%s</ul>" % sAdminItems

        # cool use of .format :-)
        sMenu = "<li class=\"%s\" style=\"cursor: pointer;\"><a %s %s %s>%s %s</a>{0}</li>" % (sClass, sOnClick, sHref, sTarget, sIcon, sLabel)

        sAdminMenu += sMenu.format(sAdminItems)

        if "all" in sRoles:
            sUserMenu += sMenu.format(sUserItems)
            sDevMenu += sMenu.format(sDevItems)
        else:
            if "developer" in sRoles:
                sDevMenu += sMenu.format(sDevItems)
            if "user" in sRoles:
                sUserMenu += sMenu.format(sUserItems)

            
            
    
    with open("%s/static/_amenu.html" % web_root, 'w') as f_out:
        if not f_out:
            print "ERROR: unable to create static/_amenu.html."
        f_out.write(sAdminMenu)

    with open("%s/static/_dmenu.html" % web_root, 'w') as f_out:
        if not f_out:
            print "ERROR: unable to create static/_dmenu.html."
        f_out.write(sDevMenu)

    with open("%s/static/_umenu.html" % web_root, 'w') as f_out:
        if not f_out:
            print "ERROR: unable to create static/_umenu.html."
        f_out.write(sUserMenu)


"""
    Main Startup
"""


if __name__ != "cato_admin_ui":
    #this is a service, which has a db connection.
    # but we're not gonna use that for gui calls - we'll make our own when needed.
    server = catocommon.CatoService("cato_admin_ui")
    server.startup()

    config = catocommon.read_config()

    if "version" in config:
        print "Cato UI - Version %s" % config["version"]

    if "web_port" in config:
        port = config["web_port"]
        sys.argv.append(port)
    
    dbglvl = 2
    if "web_debug" in config:
        try:
            dbglvl = int(config["web_debug"])
        except:
            print "Warning: web_debug setting in cato.conf must be an integer between 0-4."
        print "Setting debug level to %d..." % dbglvl
    else:
        print "Setting debug level to default (%d)..." % dbglvl
    uiGlobals.debuglevel = dbglvl
            

    urls = (
        '/', 'home',
        '/uiMethods/(.*)', 'uiMethods',
        '/cloudMethods/(.*)', 'cloudMethods',
        '/taskMethods/(.*)', 'taskMethods',
        '/ecoMethods/(.*)', 'ecoMethods',
        '/login', 'login',
        '/logout', 'logout',
        '/home', 'home',
        '/importObject', 'importObject',
        '/notAllowed', 'notAllowed',
        '/cloudEdit', 'cloudEdit',
        '/cloudAccountEdit', 'cloudAccountEdit',
        '/cloudDiscovery', 'cloudDiscovery',
        '/taskEdit', 'taskEdit',
        '/taskPrint', 'taskPrint',
        '/taskRunLog', 'taskRunLog',
        '/taskActivityLog', 'taskActivityLog',
        '/taskManage', 'taskManage',
        '/systemStatus', 'systemStatus',
        '/taskStatus', 'taskStatus',
        '/ecoTemplateEdit', 'ecoTemplateEdit',
        '/ecoTemplateManage', 'ecoTemplateManage',
        '/ecosystemManage', 'ecosystemManage',
        '/ecosystemEdit', 'ecosystemEdit',
        '/userEdit', 'userEdit',
        '/assetEdit', 'assetEdit',
        '/credentialEdit', 'credentialEdit',
        '/announcement', 'announcement',
        '/getlicense', 'getlicense',
        '/upload', 'upload',
        '/settings', 'settings',
        '/temp/(.*)', 'temp',
        '/bypass', 'bypass'
    )


    render = web.template.render('templates', base='base')
    render_popup = web.template.render('templates', base='popup')
    render_plain = web.template.render('templates')
    
    app = web.application(urls, globals(), autoreload=True)
    session = web.session.Session(app, web.session.ShelfStore(shelve.open('%s/datacache/session.shelf' % web_root)))
    app.add_processor(auth_app_processor)
    app.notfound = notfound
    
    uiGlobals.web = web
    uiGlobals.session = session
    uiGlobals.server = server
    uiGlobals.config = config
    uiGlobals.web_root = web_root
    
    # setting this to True seems to show a lot more detail in UI exceptions
    web.config.debug = False

    # we need to build some static html here...
    # caching in the session is a bad idea, and this stuff very very rarely changes.
    # so, when the service is started it will update the files, and the ui 
    # will simply pull in the files when requested.
    
    # put the task commands in a pickle for our lookups
    # and cache the html in a flat file
    uiCommon.log_nouser("Generating static html...", 3)
    SetTaskCommands()
    CacheMenu()

    
    
    # Uncomment the following - it will print out all the core methods in the app
    # this will be handy during the conversion, as we add functions to uiGlobals.RoleMethods.
#    for s in dir():
#        print "\"/%s\" : [\"Administrator\", \"Developer\"]," % s
#    for s in dir(uiMethods):
#        print "\"%s\" : [\"Administrator\", \"Developer\"]," % s
#    for s in dir(taskMethods):
#        print "\"/%s\" : [\"Administrator\", \"Developer\"]," % s
#    for s in dir(ecoMethods):
#        print "\"%s\" : [\"Administrator\", \"Developer\"]," % s
#    for s in dir(cloudMethods):
#        print "\"%s\" : [\"Administrator\", \"Developer\"]," % s


    # NOTE: this "application" attribute will only be used if we're attached to as a 
    # wsgi module
    application = app.wsgifunc()

# and this will only run if we're executed directly.
if __name__ == "__main__":
    app.run()
