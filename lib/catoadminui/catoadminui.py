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


from catoconfig import catoconfig
from catolog import catolog
import web
import os
import sys
import shelve

app_name = "cato_admin_ui"
logger = catolog.get_logger(app_name)

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
web_root = os.path.join(base_path, "ui/admin")
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)
sys.path.append(web_root)

try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

from catocommon import catocommon, catoprocess
from catolicense import catolicense
from catoerrors import WebmethodInfo
from catoui import uiGlobals
from taskMethods import taskMethods

# to avoid any path issues, "cd" to the web root.
os.chdir(web_root)

"""
 wmHandler is the default handler for any urls not defined in the urls mapping below.
 (web.py required explicit url mapping)
 
 web.py will instantiate this class, and invoke either the GET or POST method.
 
 We take it from there (in catocommon), parse the URI, and try to load the right module 
 and find the proper function to handle the request.
"""
class wmHandler:
    #the GET and POST methods here are hooked by web.py.
    #whatever method is requested, that function is called.
    def GET(self, method):
        return catocommon.FindAndCall("catoadminui." + method)

    def POST(self, method):
        return catocommon.FindAndCall("catoadminui." + method)

class getlog():
    """
    delivers an html page with a refresh timer.  content is the last n rows of the logfile
    """
    def GET(self):
        return uiCommon.GetLog()
        
class setdebug():
    """
    sets the debug level of the service.
    """
    def GET(self):
        return uiCommon.SetDebug()
        
def notfound():
    return web.notfound("Sorry, the page you were looking for was not found.")

class bypass:        
    def GET(self):
        return "This page isn't subject to the auth processor"

class version:        
    def GET(self):
        return catoconfig.VERSION
            
# the login announcement hits the Cloud Sidekick web site for a news snip
class announcement:        
    def GET(self):
        s = catocommon.http_get_nofail("http://community.cloudsidekick.com/login-page-announcement?utm_source=cato_app&utm_medium=loginpage&utm_campaign=app")
        if s:
            return s
        else:
            return ""

class getlicense:        
    def GET(self):
        try:
            result, msg, lic = catolicense.check_license()
            if lic:
                lic = uiCommon.packJSON(uiCommon.FixBreaks(uiCommon.SafeHTML(lic)))
            return "{\"result\":\"%s\",\"message\":\"%s\",\"license\":\"%s\"}" % (result, msg, lic)
        except Exception as ex:
            logger.error(ex.__str__())
            

# the default page if no URI is given, just an information message
class index:        
    def GET(self):
        return render.home()

class home:        
    def GET(self):
        return render.home()

class notAllowed:        
    def GET(self):
        i = web.input(msg="")
        return render.notAllowed(i.msg)

class settings:        
    def GET(self):
        return render.settings()

class assetEdit:        
    def GET(self):
        return render.assetEdit()

class credentialEdit:        
    def GET(self):
        return render.credentialEdit()

class tagEdit:        
    def GET(self):
        return render.tagEdit()

class imageEdit:        
    def GET(self):
        return render.imageEdit()

class userEdit:        
    def GET(self):
        return render.userEdit()

class taskManage:        
    def GET(self):
        return render.taskManage()

class taskEdit:        
    def GET(self):
        # NOTE: Getting the task edit page has a safety check.
        # An "Approved" task cannot be opened in the editor... so...
        # we check the status here before doing anything, and redirect accordingly.
        i = web.input(task_id=None)
        if i.task_id:
            # do we have permission to see this task?
            allowed = taskMethods.IsTaskAllowed(i.task_id)
            if allowed:
                task_status = taskMethods.GetTaskStatus(i.task_id)
                if task_status == "Approved":
                    logger.warning("Attempt to explicitly access an Approved Task in the editor.", 2)
                    return render.taskView()
                else:
                    return render.taskEdit()
            else:
                return render.notAllowed("Not allowed to manage this Task.")
                
class taskRunLog:        
    def GET(self):
        return render_popup.taskRunLog()

class taskView:        
    def GET(self):
        # NOTE: Getting the task edit page has a safety check.
        # An "Approved" task cannot be opened in the editor... so...
        # we check the status here before doing anything, and redirect accordingly.
        i = web.input(task_id=None)
        if i.task_id:
            # do we have permission to see this task?
            allowed = taskMethods.IsTaskAllowed(i.task_id)
            if allowed:
                return render.taskView()
            else:
                return render.notAllowed("Not allowed to manage this Task.")

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

class deploymentManage:        
    def GET(self):
        return render.deploymentManage()

class deploymentEdit:        
    def GET(self):
        return render.deploymentEdit()

class depTemplateManage:        
    def GET(self):
        return render.depTemplateManage()

class depTemplateEdit:        
    def GET(self):
        return render.depTemplateEdit()

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
            filename = "%s-%s.tmp" % (uiCommon.GetSessionUserID(), ref_id)
            fullpath = os.path.join(catoconfig.CONFIG["tmpdir"], filename)
            with open(fullpath, 'w') as f_out:
                if not f_out:
                    logger.critical("Unable to open %s for writing." % fullpath)
                f_out.write(x["fupFile"].file.read()) # writes the uploaded file to the newly created file.
            
            # all done, we loop back to the file_upload.html page, but this time include
            # a qq arg - the file name
            raise web.seeother("static/pages/file_upload.html?ref_id=%s&filename=%s" % (ref_id, filename))

class temp:
    """all we do for temp is deliver the file."""
    def GET(self, filename):
        try:
            f = open(os.path.join(catoconfig.CONFIG["tmpdir"], filename))
            if f:
                return f.read()
        except Exception as ex:
            return ex.__str__()

class login:
    def GET(self):
        # visiting the login page kills the session
        uiGlobals.session.kill()
        raise web.seeother('/static/login.html')

class logout:        
    def GET(self):
        uiCommon.ForceLogout("")
        

#Authentication preprocessor
def auth_app_processor(handle):
    path = web.ctx.path
    
    # requests that are allowed, no matter what
    if path in [
        "/uiMethods/wmAttemptLogin",
        "/uiMethods/wmGetQuestion",
        "/version",
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
    if not uiGlobals.session.get('user', False):
        logger.info("Session Expired")
        raise web.seeother('/static/login.html')
    
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
        logger.debug(path)
        if "Methods/wm" in path:
            return ""
        else:
            return "Some content on this page isn't available to your user."

def CacheTaskCommands():
    #creates the html cache file
    try:
        sCatHTML = ""
        sFunHTML = ""
        sHelpHTML = ""

        # so, we will use the FunctionCategories class in the session that was loaded at login, and build the list items for the commands tab.
        cats = uiGlobals.FunctionCategories
        if not cats:
            logger.error("Task Function Categories class is not in the datacache.")
        else:
            for cat in cats.Categories:
                sCatHTML += "<div class=\"ui-widget-content ui-corner-all command_item category\""
                sCatHTML += " id=\"cat_" + cat.Name + "\""
                sCatHTML += " name=\"" + cat.Name + "\">"
                sCatHTML += "<img class=\"category_icon\" src=\"" + cat.Icon + "\" alt=\"\" />"
                sCatHTML += "<span>" + cat.Label + "</span>"
                sCatHTML += "</div>"
                sCatHTML += "<div id=\"help_text_" + cat.Name + "\" class=\"hidden\">"
                sCatHTML += cat.Description
                sCatHTML += "</div>"
                
                sFunHTML += "<div class=\"functions hidden\" id=\"cat_" + cat.Name + "_functions\">"
                # now, let's work out the functions.
                # we can just draw them all... they are hidden and will display on the client as clicked
                for fn in cat.Functions:
                    sFunHTML += "<div class=\"ui-widget-content ui-corner-all command_item function\""
                    sFunHTML += " id=\"fn_" + fn.Name + "\""
                    sFunHTML += " name=\"fn_" + fn.Name + "\">"
                    sFunHTML += "<img class=\"function_icon\" src=\"" + fn.Icon + "\" alt=\"\" />"
                    sFunHTML += "<span>" + fn.Label + "</span>"
                    sFunHTML += "<div id=\"help_text_fn_" + fn.Name + "\" class=\"hidden\">"
                    sFunHTML += fn.Description
                    sFunHTML += "</div>"
                    sFunHTML += "</div>"

                    sHelpHTML += "<div>"
                    sHelpHTML += "<img src=\"" + fn.Icon + "\" alt=\"\" style=\"height: 16px; width: 16px;\" />"
                    sHelpHTML += "<span style=\"font-weight: bold; padding-left: 10px;\">" + fn.Category.Label + " : " + fn.Label + "</span>"
                    sHelpHTML += "</div>"
                    sHelpHTML += "<div style=\"margin-top: 6px;\">"
                    sHelpHTML += fn.Help
                    sHelpHTML += "</div>"
                    sHelpHTML += "<hr />"
    
                sFunHTML += "</div>"

        path = catoconfig.CONFIG["uicache"]
    
        with open("%s/_categories.html" % path, 'w') as f_out:
            if not f_out:
                logger.error("Unable to create %s/_categories.html." % path)
            f_out.write(sCatHTML)

        with open("%s/_functions.html" % path, 'w') as f_out:
            if not f_out:
                logger.error("Unable to create %s/_functions.html." % path)
            f_out.write(sFunHTML)

        with open("%s/_command_help.html" % path, 'w') as f_out:
            if not f_out:
                logger.error("Unable to create %s/_command_help.html." % path)
            f_out.write(sHelpHTML)

    except Exception as ex:
        logger.error(ex.__str__())

def CacheMenu():
    #put the site.master.xml in the session here
    # this is a significant boost to performance
    xRoot = ET.parse("%s/catoadminui/site.master.xml" % lib_path)
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

    path = catoconfig.CONFIG["uicache"]
    
    with open("%s/_amenu.html" % path, 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_amenu.html." % path)
        f_out.write(sAdminMenu)

    with open("%s/_dmenu.html" % path, 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_dmenu.html." % path)
        f_out.write(sDevMenu)

    with open("%s/_umenu.html" % path, 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_umenu.html." % path)
        f_out.write(sUserMenu)


def Housekeeping():
    # first, if they don't exist, move any hardcoded clouds from the cloud_providers.xml file
    # into the clouds table.
    try:
        db = catocommon.new_conn()

        logger.info("Doing a little housekeeping...")
        
        filename = os.path.join(catoconfig.BASEPATH, "conf/cloud_providers.xml")
        if not os.path.isfile(filename):
            raise Exception("conf/cloud_providers.xml file does not exist.")
        xRoot = ET.parse(filename)
        if not xRoot:
            raise Exception("Error: Invalid or missing Cloud Providers XML.")
        else:
            xProviders = xRoot.findall("providers/provider")
            for xProvider in xProviders:
                p_name = xProvider.get("name", None)
                user_defined_clouds = xProvider.get("user_defined_clouds", True)
                user_defined_clouds = (False if user_defined_clouds == "false" else True)
                 
                if not user_defined_clouds:
                    # clouds are NOT user defined, check the database for these records.
                    xClouds = xProvider.findall("clouds/cloud")
                    for xCloud in xClouds:
                        if xCloud.get("name", None) == None:
                            raise Exception("Cloud Providers XML: All Clouds must have the 'name' attribute.")
                        
                        cloud_name = xCloud.get("name", "")

                        sql = "select count(*) from clouds where cloud_name = '%s'" % xCloud.get("name", "")
                        cnt = db.select_col_noexcep(sql)
                        
                        if not cnt:
                            logger.info("Creating Cloud [%s] on Provider [%s]..." % (cloud_name, p_name))

                            if xCloud.get("api_url", None) == None:
                                raise Exception("Cloud Providers XML: All Clouds must have the 'api_url' attribute.")
                            if xCloud.get("api_protocol", None) == None:
                                raise Exception("Cloud Providers XML: All Clouds must have the 'api_protocol' attribute.")
                            
                            from catocloud import cloud
                            c = cloud.Cloud.DBCreateNew(cloud_name, p_name, xCloud.get("api_url", ""), xCloud.get("api_protocol", ""), xCloud.get("region", ""))
                            if not c:
                                logger.warning("Could not create Cloud from cloud_providers.xml definition.\n%s")
                        

    except Exception as ex:
        logger.error(ex.__str__())
    finally:
        db.close()
    
class ExceptionHandlingApplication(web.application):
    def handle(self):
        try:
            return web.application.handle(self)
        except (web.HTTPError, KeyboardInterrupt, SystemExit):
            raise
        except WebmethodInfo as ex:
            # we're using a custom HTTP status code to indicate 'information' back to the user.
            web.ctx.status = "280 Informational Response"
            logger.exception(ex.__str__())
            return ex.__str__()
        except Exception as ex:
            # web.ctx.env.get('HTTP_X_REQUESTED_WITH')
            web.ctx.status = "400 Bad Request"
            logger.exception(ex.__str__())
            return ex.__str__()
        
"""
    Main Startup
"""


if __name__ != app_name:
    dbglvl = 20
    if "admin_ui_debug" in catoconfig.CONFIG:
        try:
            dbglvl = int(catoconfig.CONFIG["admin_ui_debug"])
        except:
            raise Exception("admin_ui_debug setting in cato.conf must be an integer between 0-50.")
    catolog.DEBUG = dbglvl
            
    c_dbglvl = 20
    if "admin_ui_client_debug" in catoconfig.CONFIG:
        try:
            c_dbglvl = int(catoconfig.CONFIG["admin_ui_client_debug"])
        except:
            raise Exception("admin_ui_client_debug setting in cato.conf must be an integer between 0-50.")
    catolog.CLIENTDEBUG = c_dbglvl
            
    #this is a service, which has a db connection.
    # but we're not gonna use that for gui calls - we'll make our own when needed.
    server = catoprocess.CatoService(app_name)
    server.startup()

    # now that the service is set up, we'll know what the logfile name is.
    # so reget the logger
    logger = catolog.get_logger(app_name)
    catolog.set_debug(dbglvl)

    logger.info("Cato UI - Version %s" % catoconfig.VERSION)
    logger.info("DEBUG set to %d..." % dbglvl)
    logger.info("CLIENTDEBUG set to %d..." % c_dbglvl)

    if "admin_ui_port" in catoconfig.CONFIG:
        port = catoconfig.CONFIG["admin_ui_port"]
        sys.argv.append(port)
    
    # the LAST LINE must be our /(.*) catchall, which is handled by uiMethods.
    urls = (
        '/', 'home',
        '/login', 'login',
        '/logout', 'logout',
        '/home', 'home',
        '/importObject', 'importObject',
        '/notAllowed', 'notAllowed',
        '/cloudEdit', 'cloudEdit',
        '/cloudAccountEdit', 'cloudAccountEdit',
        '/cloudDiscovery', 'cloudDiscovery',
        '/taskEdit', 'taskEdit',
        '/taskView', 'taskView',
        '/taskPrint', 'taskPrint',
        '/taskRunLog', 'taskRunLog',
        '/taskActivityLog', 'taskActivityLog',
        '/taskManage', 'taskManage',
        '/systemStatus', 'systemStatus',
        '/taskStatus', 'taskStatus',
        '/deploymentEdit', 'deploymentEdit',
        '/deploymentManage', 'deploymentManage',
        '/depTemplateEdit', 'depTemplateEdit',
        '/depTemplateManage', 'depTemplateManage',
        '/userEdit', 'userEdit',
        '/assetEdit', 'assetEdit',
        '/tagEdit', 'tagEdit',
        '/imageEdit', 'imageEdit',
        '/credentialEdit', 'credentialEdit',
        '/announcement', 'announcement',
        '/getlicense', 'getlicense',
        '/upload', 'upload',
        '/settings', 'settings',
        '/temp/(.*)', 'temp',
        '/bypass', 'bypass',
        '/version', 'version',
        '/getlog', 'getlog',
        '/setdebug', 'setdebug',
        '/(.*)', 'wmHandler'
    )


    render = web.template.render('templates', base='base')
    render_popup = web.template.render('templates', base='popup')
    render_plain = web.template.render('templates')
    
    app = ExceptionHandlingApplication(urls, globals(), autoreload=True)
    web.config.session_parameters["cookie_name"] = app_name
    
    if "uicache" in catoconfig.CONFIG:
        uicachepath = catoconfig.CONFIG["uicache"]
    else:
        logger.info("'uicache' not defined in cato.conf... using default /var/cato/ui")
        uicachepath = "/var/cato/ui"
        
    if not os.path.exists(uicachepath):
        logger.critical("UI file cache directory defined in cato.conf does not exist. [%s]" % uicachepath)
        exit()
        
    session = web.session.Session(app, web.session.ShelfStore(shelve.open('%s/adminsession.shelf' % uicachepath)))
    app.add_processor(auth_app_processor)
    app.notfound = notfound
    
    uiGlobals.session = session
    uiGlobals.lib_path = lib_path
    uiGlobals.web_root = web_root
    
    # setting this to True seems to show a lot more detail in UI exceptions
    web.config.debug = False

    # we need to build some static html here...
    # caching in the session is a bad idea, and this stuff very very rarely changes.
    # so, when the service is started it will update the files, and the ui 
    # will simply pull in the files when requested.
    
    # put the task commands in a global for our lookups
    # and cache the html in a flat file
    logger.info("Reading configuration files and generating static html...")

        #NOTE: this import is here and not at the top ON PURPOSE...
    # if it's imported at the top, catolog won't have a LOGFILE defined yet 
    # and the uiCommon logger won't write to the file
    from catoui import uiCommon
    uiCommon.LoadTaskCommands()
    #rebuild the cache html files
    CacheTaskCommands()

    CacheMenu()

    # Occasionally, for specific updates and other general reasons,
    # we do a little housekeeping when the service is started.
    Housekeeping() 
    
    # Uncomment the following - it will print out all the core methods in the app
    # this will be handy during the conversion, as we add functions to uiGlobals.RoleMethods.
#    for s in dir():
#        logger.debug("\"/%s\" : [\"Developer\"]," % s)
#    for s in dir(uiMethods):
#        logger.debug("\"/uiMethods/%s\" : [\"Developer\"]," % s)
#    for s in dir(taskMethods):
#        logger.debug("\"/taskMethods/%s\" : [\"Developer\"]," % s)
#    for s in dir(cloudMethods):
#        logger.debug("\"/cloudMethods/%s\" : [\"Developer\"]," % s)


    # NOTE: this "application" attribute will only be used if we're attached to as a 
    # wsgi module
    application = app.wsgifunc()

# and this will only run if we're executed directly.
def main():
    app.run()
