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
import json
from web.wsgiserver import CherryPyWSGIServer

app_name = "cato_admin_ui"
logger = catolog.get_logger(app_name)

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
web_root = os.path.join(base_path, "ui/admin")
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)
sys.path.append(web_root)

from catocommon import catocommon, catoprocess
from catolicense import catolicense
from catoerrors import InfoException, SessionError
from catoui import uiGlobals, uiCommon
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
    # the GET and POST methods here are hooked by web.py.
    # whatever method is requested, that function is called.
    def GET(self, method):
        web.header('X-CSK-Method', method)
        return catocommon.FindAndCall("catoadminui." + method)

    def POST(self, method):
        web.header('X-CSK-Method', method)
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


class recache():
    """
    rebuilds the UI cached html (commands, menu)
    for CSK development/support
    """
    def GET(self):
        user_role = uiCommon.GetSessionUserRole()
        if user_role != "Administrator":
            raise Exception("Only Administrators can refresh the UI cache.")
        _build_ui_cache()
        return "Cache successfully refreshed."


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
        s = catocommon.http_get_nofail("http://announcement.cloudsidekick.com/cato/announcement.html?utm_source=cato_app&utm_medium=loginpage&utm_campaign=app")
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
            return json.dumps({"result": result, "message": msg, "license": lic})
        except Exception as ex:
            logger.error(ex.__str__())


class common:
    """ A common directory serving static content. """
    def __init__(self):
        self.commondir = catoconfig.CONFIG.get("ui_common_dir")
        if not self.commondir:
            self.commondir = os.path.join(base_path, "ui", "common")

        if not os.path.exists(self.commondir):
            raise Exception("UI 'common' directory defined in cato.conf (ui_common_dir) does not exist. [%s]" % self.commondir)

    def GET(self, path):
        fullpath = os.path.join(self.commondir, path)
        if os.path.exists(fullpath):
            with open(fullpath, 'r') as f:
                if f:
                    # make an attempt to set the proper content type
                    uiCommon.set_content_type(path)

                    x = f.read()
                    return x if x else ""
                else:
                    return ""
        else:
            web.ctx.status = "404 Not Found"
            return ""


class cache:
    """ Access to the 'uicache' directory, where 3rd party static content was installed. """
    def __init__(self):
        uicachepath = catoconfig.CONFIG["uicache"]
        if not os.path.exists(uicachepath):
            raise Exception("UI 'cache' directory defined in cato.conf (uicache) does not exist. [%s]" % uicachepath)

    def GET(self, path):
        fullpath = os.path.join(uicachepath, path)
        if os.path.exists(fullpath):
            with open(fullpath, 'r') as f:
                if f:
                    # make an attempt to set the proper content type
                    uiCommon.set_content_type(path)

                    x = f.read()
                    return x if x else ""
                else:
                    return ""
        else:
            web.ctx.status = "404 Not Found"
            return ""


# the default page if no URI is given, just an information message
class index:
    def GET(self):
        return render.home()


class home:
    """
    We have a POST handler here, because the login screen does a post after auth...
        (this is so browsers will offer to remember passwords, even tho our auth is ajax.)

    But, when we get a POST, we do a redirect!  Why?  So refreshing the /home page
        won't nag about "are you sure you wanna resubmit this form.

    Why not do a GET login form?  Doh! The credentials would be on the querystring = bad.
    """
    def GET(self):
        return render.home()

    def POST(self):
        # finally, if the original, pre-login request was a specific path, 
        # go ahead and redirect to there, otherwise /home.
        path = uiGlobals.session.get("requested_path", "/home")
        raise web.seeother(path)


class notAllowed:
    def GET(self):
        i = web.input(msg="")
        return render.notAllowed(i.msg)


class settings:
    def GET(self):
        return render.settings()


class search:
    def GET(self):
        return render.search()


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
                    logger.warning("Attempt to explicitly access an Approved Task in the editor.")
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
            # print x # ref_id
            # web.debug(x['fupFile'].filename) # This is the filename
            # web.debug(x['fupFile'].value) # This is the file contents
            # web.debug(x['fupFile'].file.read()) # Or use a file(-like) object
            # raise web.seeother('/upload')

            ref_id = (x.ref_id if x.ref_id else "")
            filename = "%s-%s.tmp" % (uiCommon.GetSessionUserID(), ref_id)
            fullpath = os.path.join(catoconfig.CONFIG["tmpdir"], filename)
            with open(fullpath, 'w') as f_out:
                if not f_out:
                    logger.critical("Unable to open %s for writing." % fullpath)
                f_out.write(x["fupFile"].file.read())  # writes the uploaded file to the newly created file.

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
        # visiting the login page kills the session and redirects to login.html
        uiGlobals.session.kill()
        raise web.seeother('/static/login.html')


class logout:
    def GET(self):
        uiCommon.ForceLogout("")


class appicon:
    def GET(self, name):
        img = uiCommon.GetAppIcon(name)
        web.header('Content-type', 'image/png')
        return img


# Authentication preprocessor
def auth_app_processor(handle):
    """
    This function handles every single request to the server.

    Certain paths are allowed no matter what, the rest require a session.

    Errors are processed according to the type of exception thrown.

    For the UI's, client side code handles the different HTTP responses accordingly.
    """
    path = web.ctx.path

    # requests that are allowed, no matter what
    if path in ["/favicon.ico",
                "/uiMethods/wmAttemptLogin",
                "/uiMethods/wmGetQuestion",
                "/version",
                "/login",
                "/logout",
                "/notAllowed",
                "/notfound",
                "/announcement",
                "/getlicense",
                "/uiMethods/wmLicenseAgree"]:
        return handle()

    # additional allowed requests
    if "/common/" in path or "/cache/" in path:
        return handle()

    # any other request requires an active session ... kick it out if there's not one.
    # (we pass the requested path to this function, so it can go there after login if
    # we're not currently authenticated
    # NOTE: this will REDIRECT to the requested path if it has to do token or applink auth
    uiCommon.CheckSession("Cato Admin UI", web.ctx.fullpath)

    # check the role/method mappings to see if the requested page is allowed
    # HERE's the rub! ... some of our requests are for "pages" and others (most) are ajax calls.
    # for the pages, we can redirect to the "notAllowed" page,
    # but for the ajax calls we can't - we need to return an acceptable ajax response.

    if uiCommon.check_roles(path):
        return handle()
    else:
        logger.debug(path)
        if web.ctx.env.get('HTTP_X_REQUESTED_WITH') == "XMLHttpRequest":
            return ""
        else:
            return "Some content on this page isn't available to your user."


def CacheTaskCommands():
    """
    Creates the html cache file for Task Command categories, functions and help.

    The loops build global html objects, which are ultimately written out to files.
    Even though the FunctionCategories class has a hierarchy, we are writing flat files.
    The browser will take care of showing things according to their hierarchy.
    """
    cathtml = ""
    funhtml = ""
    helphtml = ""

    # this internal def builds the html for a subcategory, and associates it's child functions with it
    # NOTE: the dubcats are in the categories file, but they are hidden and indented with css.
    def _build_subcategory(parent, subcat):
        return """<div class="category subcategory" id="cat_{0}_sub_{1}" name="{1}">
            <div class="ui-widget-content ui-corner-all command_item"">
                <img class="category_icon" src="{3}" alt="" />
                <span>{2}</span>
                <div class="hidden">{4}</div>
            </div>
        </div>""".format(parent.Name, subcat.Name, subcat.Label, subcat.Icon, subcat.Description)

    # this internal def builds the html for a single function
    def _build_func_html(parent, domparentid):
        helpout = ""
        funcout = """<div class="functions hidden" id="{0}_functions">""".format(domparentid)
        # now, let's work out the functions.
        # we can just draw them all... they are hidden and will display on the client as clicked
        for fn in parent.Functions:
            funcout += """
            <div class="ui-widget-content ui-corner-all command_item function" id="fn_{0}" name="fn_{0}">
            <img class="function_icon" src="{2}" alt="" />
            <span>{1}</span>
            <div class="funchelp hidden">{3}</div>
            </div>""".format(fn.Name, fn.Label, fn.Icon, fn.Description)

            helpout = """<div>
            <img src="{0}" alt="" style="height: 16px; width: 16px;" />
            <span style="font-weight: bold; padding-left: 10px;">{1} : {2}</span>
            </div>
            <div style="margin-top: 6px;">{3}</div>
            <hr />""".format(fn.Icon, fn.Category.Label, fn.Label, fn.Help)

        funcout += "</div>"

        return funcout, helpout

    # so, we will use the FunctionCategories class in the session that was loaded at login, and build the list items for the commands tab.
    cats = uiGlobals.FunctionCategories
    if not cats:
        logger.error("Task Function Categories class is not in the datacache.")
    else:
        for cat in cats.Categories:
            cathtml += """<div class="category" id="cat_{0}" name="{0}">
                <div class="ui-widget-content ui-corner-all command_item">
                    <img class="category_icon" src="{2}" alt="" />
                    <span>{1}</span>
                    <div class="cathelp hidden">{3}</div>
                </div>""".format(cat.Name, cat.Label, cat.Icon, cat.Description)

            # So... the category MIGHT have subcategories, which have functions.
            if cat.Subcategories:
                cathtml += """<div class="subcategories hidden">"""
                for subcat in cat.Subcategories:
                    cathtml += _build_subcategory(cat, subcat)

                    f, h = _build_func_html(subcat, "cat_%s_sub_%s" % (cat.Name, subcat.Name))
                    funhtml += f
                    helphtml += h
                cathtml += "</div>"
            cathtml += "</div>"

            # it can also have direct functions.
            f, h = _build_func_html(cat, "cat_%s" % (cat.Name))
            funhtml += f
            helphtml += h

    path = catoconfig.CONFIG["uicache"]

    with open("%s/_categories.html" % (path), 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_categories.html." % (path))
        f_out.write(cathtml)

    with open("%s/_functions.html" % (path), 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_functions.html." % (path))
        f_out.write(funhtml)

    with open("%s/_command_help.html" % (path), 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_command_help.html." % (path))
        f_out.write(helphtml)


def CacheMenu():
    with open(os.path.join(lib_path, "catoadminui/menu.json"), 'r') as f:
        menus = json.load(f)

    # so, we have the cato menu.  Are there any extensions with menu additions?
    # extensions and their paths are defined in config.
    for n, p in catoconfig.CONFIG["extensions"].iteritems():
        logger.debug("Looking for extension menus in [%s - %s]..." % (n, p))
        for root, subdirs, files in os.walk(p):
            for f in files:
                if f == "menu.json":
                    logger.debug("... found one! Loading...")

                    with open(os.path.join(p, f), 'r') as f:
                        extmenus = json.load(f)

                    # now, let's manipulate our menu
                    for extmenu in extmenus:
                        pos = extmenu.get("insert_at")
                        if pos is not None:
                            menus.insert(pos, extmenu)

    sAdminMenu = ""
    sDevMenu = ""
    sUserMenu = ""

    for menu in menus:
        sLabel = menu.get("label", "No Label Defined")
        sHref = " href=\"" + menu.get("href", "") + "\"" if menu.get("href") else ""
        sOnClick = " onclick=\"" + menu.get("onclick", "") + "\"" if menu.get("onclick") else ""
        sIcon = "<img src=\"" + menu.get("icon", "") + "\" alt=\"\" height=\"24px\" width=\"24px\" />" if menu.get("icon") else ""
        sTarget = " target=\"" + menu.get("target", "") + "\"" if menu.get("target") else ""
        sClass = menu.get("class", "")
        sRoles = menu.get("roles", "")

        sAdminItems = ""
        sDevItems = ""
        sUserItems = ""

        for item in menu.get("items", []):
            sItemLabel = item.get("label", "No Label Defined")
            sItemHref = " href=\"" + item.get("href", "") + "\"" if item.get("href") else ""
            sItemOnClick = " onclick=\"" + item.get("onclick", "") + "\"" if item.get("onclick") else ""
            sItemIcon = "<img src=\"" + item.get("icon", "") + "\" alt=\"\" height=\"24px\" width=\"24px\" />" if item.get("icon") else ""
            sItemTarget = " target=\"" + item.get("target", "") + "\"" if item.get("target") else ""
            sItemClass = item.get("class", "")
            sItemRoles = item.get("roles", "")

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


class ExceptionHandlingApplication(web.application):
    """
    CRITICALLY IMPORTANT!
    This is an overload of the standard web.application class.

    Main reason? In application.py, the 'handle_with_processors' function
        converts *any* exception into the generic web.py _InternalError.

    This interferes, because we wanna trap the original error an make determinations
        on how to reply to the client.

    So, we overloaded the function and fixed the error handing.
    """
    def handle_with_processors(self):
        def process(processors):
            try:
                if processors:
                    p, processors = processors[0], processors[1:]
                    return p(lambda: process(processors))
                else:
                    return self.handle()
            except (web.HTTPError, KeyboardInterrupt, SystemExit):
                raise
            except InfoException as ex:
                # we're using a custom HTTP status code to indicate 'information' back to the user.
                web.ctx.status = "280 Informational Response"
                logger.info(ex.__str__())
                return ex.__str__()
            except SessionError as ex:
                logger.info(ex.__str__())
                # now, all our ajax calls are from jQuery, which sets a header - X-Requested-With
                # so if we have that header, it's ajax, otherwise we can redirect to the login page.

                # a session error means we kill the session
                uiGlobals.session.kill()

                if web.ctx.env.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                    web.ctx.status = "480 Session Error"
                    return ex.__str__()
                else:
                    logger.debug("Standard Request - redirecting to the login page...")
                    raise web.seeother('/static/login.html')
            except Exception as ex:
                # web.ctx.env.get('HTTP_X_REQUESTED_WITH')
                web.ctx.status = "400 Bad Request"
                logger.exception(ex.__str__())
                return ex.__str__()

        return process(self.processors)


def _build_ui_cache():
    # we need to build some static html here...
    # caching in the session is a bad idea, and this stuff very very rarely changes.
    # so, when the service is started it will update the files, and the ui
    # will simply pull in the files when requested.

    # put the task commands in a global for our lookups
    # and cache the html in a flat file
    logger.info("Reading configuration files and generating static html...")

    uiCommon.LoadTaskCommands()
    # rebuild the cache html files
    CacheTaskCommands()
    CacheMenu()


"""
    Main Startup
"""

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
    '/search', 'search',
    '/settings', 'settings',
    '/temp/(.*)', 'temp',
    '/bypass', 'bypass',
    '/version', 'version',
    '/getlog', 'getlog',
    '/setdebug', 'setdebug',
    '/recache', 'recache',
    '/appicon/(.*)', 'appicon',
    '/common/(.*)', 'common',
    '/cache/(.*)', 'cache',
    '/(.*)', 'wmHandler'
)

render = web.template.render('templates', base='base')
render_popup = web.template.render('templates', base='popup')
render_plain = web.template.render('templates')

web.config.session_parameters["cookie_name"] = app_name
# cookies won't work in https without this!
web.config.session_parameters.httponly = False
# setting this to True seems to show a lot more detail in UI exceptions
web.config.debug = False

app = ExceptionHandlingApplication(urls, globals(), autoreload=True)

if "uicache" in catoconfig.CONFIG:
    uicachepath = catoconfig.CONFIG["uicache"]
else:
    logger.info("'uicache' not defined in cato.conf... using default /var/cato/ui")
    uicachepath = "/var/cato/ui"

if not os.path.exists(uicachepath):
    raise Exception("UI file cache directory defined in cato.conf does not exist. [%s]" % uicachepath)
    exit()

# Hack to make session play nice with the reloader (in debug mode)
if web.config.get('_session') is None:
    session = web.session.Session(app, web.session.ShelfStore(shelve.open('%s/uisession.shelf' % uicachepath)))
    web.config._session = session
else:
    session = web.config._session

uiGlobals.session = session
uiGlobals.lib_path = lib_path
uiGlobals.web_root = web_root
uiGlobals.app_name = app_name


def main():
    # CATOPROCESS STARTUP

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

    # this is a service, which has a db connection.
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

    # we need to build some static html here...
    # caching in the session is a bad idea, and this stuff very very rarely changes.
    # so, when the service is started it will update the files, and the ui
    # will simply pull in the files when requested.
    _build_ui_cache()

    # WEB.PY STARTUP
    if "admin_ui_port" in catoconfig.CONFIG:
        port = catoconfig.CONFIG["admin_ui_port"]
        sys.argv.append(port)

    # enable ssl?
    if catocommon.is_true(catoconfig.CONFIG.get("admin_ui_use_ssl")):
        logger.info("Using SSL/TLS...")
        sslcert = catoconfig.CONFIG.get("admin_ui_ssl_cert", os.path.join(catoconfig.CONFDIR, "cato.crt"))
        sslkey = catoconfig.CONFIG.get("admin_ui_ssl_key", os.path.join(catoconfig.CONFDIR, "cato.key"))
        try:
            with open(sslcert):
                pass
            logger.debug("SSL Certificate [%s]" % sslcert)
            CherryPyWSGIServer.ssl_certificate = sslcert
        except:
            raise Exception("SSL Certificate not found at [%s]" % sslcert)
        try:
            with open(sslkey):
                pass
            logger.debug("SSL Key [%s]" % sslkey)
            CherryPyWSGIServer.ssl_private_key = sslkey
        except:
            raise Exception("SSL Key not found at [%s]" % sslcert)
    else:
        logger.info("Using standard HTTP. (Set admin_ui_use_ssl to 'true' in cato.conf to enable SSL/TLS.)")

    app.add_processor(auth_app_processor)
    app.notfound = notfound

    app.run()

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
