#########################################################################
#
# Copyright 2014 Cloud Sidekick
# __________________
#
#  All Rights Reserved.
#
# NOTICE:  All information contained herein is, and remains
# the property of Cloud Sidekick and its suppliers,
# if any.  The intellectual and technical concepts contained
# herein are proprietary to Cloud Sidekick
# and its suppliers and may be covered by U.S. and Foreign Patents,
# patents in process, and are protected by trade secret or copyright law.
# Dissemination of this information or reproduction of this material
# is strictly forbidden unless prior written permission is obtained
# from Cloud Sidekick.
#
#########################################################################

import os
import sys
import json
import web
import shelve
from web.wsgiserver import CherryPyWSGIServer

if "CSK_HOME" not in os.environ:
    raise Exception("CSK_HOME environment variable not set.")
sys.path.insert(0, os.path.join(os.environ["CSK_HOME"], "cato", "lib"))
sys.path.insert(0, os.path.join(os.environ["CSK_HOME"], "maestro", "lib"))
sys.path.insert(0, os.path.join(os.environ["CSK_HOME"], "legato", "lib"))

from catolog import catolog

app_name = "csk_ui"
logger = catolog.get_logger(app_name)

from catoconfig import catoconfig
from catocommon import catocommon, catoprocess
from catolicense import catolicense
from catoui import uiGlobals, uiCommon
from catoerrors import InfoException, SessionError

web_root = os.path.join(os.environ["CSK_HOME"], "cato", "ui", "cskui")
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
        return catocommon.FindAndCall("cskui." + method)

    def POST(self, method):
        web.header('X-CSK-Method', method)
        return catocommon.FindAndCall("cskui." + method)


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


class not_allowed:
    def GET(self):
        i = web.input(msg="")
        return _inject(render.not_allowed(i.msg))


def notfound():
    return web.notfound("Sorry, the page you were looking for was not found.")


# the default page if no URI is given, just an information message
class index:
    def GET(self):
        return _inject(render.home())


# the login announcement hits the Cloud Sidekick web site for a news snip
class announcement:
    def GET(self):
        s = catocommon.http_get_nofail("http://announcement.cloudsidekick.com/maestro/announcement.html?utm_source=legato_ui&utm_medium=loginpage&utm_campaign=legato")
        if s:
            return s
        else:
            return ""


class version:
    def GET(self):
        return catoconfig.VERSION


class getlicense:
    def GET(self):
        try:
            result, msg, lic = catolicense.check_license("legato")
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
            # NOTE this is different than in catoadminui ...
            # - in this case we're defaulting to the directory in CSK_HOME/cato!
            self.commondir = os.path.join(os.environ["CSK_HOME"], "cato", "ui", "common")

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
        self.uicachepath = catoconfig.CONFIG["uicache"]
        if not os.path.exists(self.uicachepath):
            raise Exception("UI 'cache' directory defined in cato.conf (uicache) does not exist. [%s]" % self.uicachepath)

    def GET(self, path):
        fullpath = os.path.join(self.uicachepath, path)
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


class temp:
    """all we do for temp is deliver the file."""
    def GET(self, filename):
        try:
            f = open(os.path.join(catoconfig.CONFIG["tmpdir"], filename))
            if f:
                return f.read()
        except Exception as ex:
            return ex.__str__()


class home:
    """
    We have a POST handler here, because the login screen does a post after auth...
        (this is so browsers will offer to remember passwords, even tho our auth is ajax.)

    But, when we get a POST, we do a redirect!  Why?  So refreshing the /home page
        won't nag about "are you sure you wanna resubmit this form.

    Why not do a GET login form?  Doh! The credentials would be on the querystring = bad.
    """
    def GET(self):
        return _inject(render.home())

    def POST(self):
        # finally, if the original, pre-login request was a specific path,
        # go ahead and redirect to there, otherwise /home.
        path = uiGlobals.session.get("requested_path", "/home")
        raise web.seeother(path)


class login:
    def GET(self):
        # visiting the login page kills the session and redirects to login.html
        uiGlobals.session.kill()
        return render_plain.login()

    def POST(self):
        return uiCommon.AttemptLogin("Velocity UI")


class logout:
    def GET(self):
        uiCommon.ForceLogout("")


# role based access to specific urls
def _check_roles(method):
    user_role = uiCommon.GetSessionUserRole()
    if user_role == "Administrator":
        return True

    # run this in a shell to get all the uiMethods
    # ",".join(['/uiMethods."%s": True' % (f) for f in dir(uiMethods.uiMethods)])

    permissions = {
        "/home": True,
        "/uiMethods/wmGetConfig": True,
        "/uiMethods/wmGetMyAccount": True,
        "/uiMethods/wmGetSettings": True,
        "/uiMethods/wmSaveMyAccount": True
        }

    if method in permissions:
        mapping = permissions[method]
        if mapping is True:
            return True

        if user_role in mapping:
            return True
        else:
            logger.warning("User requesting [%s] - insufficient permissions" % (method))
            return False
    else:
        logger.error("ERROR: [%s] does not have a role mapping." % (method))
        return False


# Authentication preprocessor
def auth_app_processor(handle):
    """
    This function handles every single request to the server.

    Certain paths are allowed no matter what, the rest require a session.

    Errors are processed according to the type of exception thrown.

    For the UI's, client side code handles the different HTTP responses accordingly.
    """
    path = web.ctx.path

    # requests that are allowed, no matter what, in order of most commonly requested
    if path in [
        "/uiMethods/wmUpdateHeartbeat",
        "/uiMethods/wmWriteClientLog",
        "/favicon.ico",
        "/login",
        "/announcement",
        "/version",
        "/uiMethods/wmAttemptLogin",
        "/uiMethods/wmGetQuestion",
        "/logout",
        "/not_allowed",
        "/notfound",
        "/getlicense",
        "/uiMethods/wmLicenseAgree"
        ]:
        return handle()

    # additional allowed requests
    if "/common/" in path or "/cache/" in path:
        return handle()

    # any other request requires an active session ... kick it out if there's not one.
    # (we pass the requested path to this function, so it can go there after login if
    # we're not currently authenticated
    uiCommon.CheckSession("CSK UI", web.ctx.fullpath)

    # check the role/method mappings to see if the requested page is allowed
    if _check_roles(path):
        return handle()
    else:
        logger.debug(path)
        # some of our requests are for "pages" and others (most) are ajax calls.
        # for the pages, we can redirect to the "notAllowed" page,
        # but for the ajax calls we can't - we need to return an acceptable ajax response.
        if web.ctx.env.get('HTTP_X_REQUESTED_WITH') == "XMLHttpRequest":
            return ""
        else:
            return _inject(render.not_allowed("Some content on this page isn't available to your user."))


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
                    raise web.seeother('/login')
            except Exception as ex:
                # web.ctx.env.get('HTTP_X_REQUESTED_WITH')
                web.ctx.status = "400 Bad Request"
                logger.exception(ex.__str__())
                return ex.__str__()

        return process(self.processors)


def _inject(templateobj):
    """
    We need to wrap each pages html with a middle 'wrapper' before inserting it into
    the main base page.
    
    So, we take the already rendered html, and do a final replacement on it.
    """
    templateobj["__body__"] = templateobj["__body__"].replace("<!--##HEADER##-->", uiGlobals.static_content["mainheader"])
    return templateobj


"""
    Main Startup
"""

uiGlobals.urls = (
    '/', 'home',
    '/login', 'login',
    '/logout', 'logout',
    '/version', 'version',
    '/home', 'home',
    '/not_allowed', 'not_allowed',
    '/announcement', 'announcement',
    '/getlicense', 'getlicense',
    '/getlog', 'getlog',
    '/setdebug', 'setdebug',
    '/common/(.*)', 'common',
    '/cache/(.*)', 'cache',
    '/temp/(.*)', 'temp'
)

# let's load up whichever subapplications are required.
# this will append to the urls

# AUTOMATE
from cskadminuicore import cskadminuicore
# FLOW
from cskcduicore import cskcduicore

# the LAST LINE must be our /(.*) catchall, which is handled by wmHandler.
uiGlobals.urls += (
   '/(.*)', 'wmHandler'
)

render = web.template.render('templates', base='base')
render_plain = web.template.render('templates')

web.config.session_parameters["cookie_name"] = app_name
# cookies won't work in https without this!
web.config.session_parameters.httponly = False
# setting this to True seems to show a lot more detail in UI exceptions
web.config.debug = False

app = ExceptionHandlingApplication(uiGlobals.urls, globals(), autoreload=True)

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
    session = web.session.Session(app, web.session.ShelfStore(shelve.open('%s/cskuisession.shelf' % uicachepath)))
    web.config._session = session
else:
    session = web.config._session

uiGlobals.session = session
uiGlobals.app_name = app_name

# these globals are read once when the process starts, and are used in each request
uiGlobals.static_content["mainheader"] = uiCommon._loadfile(os.path.join(web_root, "static", "_header.html"))


def main():
    # CATOPROCESS STARTUP

    dbglvl = 20
    if "csk_ui_debug" in catoconfig.CONFIG:
        try:
            dbglvl = int(catoconfig.CONFIG["csk_ui_debug"])
        except:
            raise Exception("csk_ui_debug setting in cato.conf must be an integer between 0-50.")
    catolog.DEBUG = dbglvl

    # this is a service, which has a db connection.
    # but we're not gonna use that for gui calls - we'll make our own when needed.
    server = catoprocess.CatoService(app_name)
    server.startup()

    # now that the service is set up, we'll know what the logfile name is.
    # so reget the logger
    logger = catolog.get_logger(app_name)
    catolog.set_debug(dbglvl)

    logger.info("Velocity UI - Version %s" % catoconfig.VERSION)
    logger.info("DEBUG set to %d..." % dbglvl)

    # WEB.PY STARTUP
    if "csk_ui_port" in catoconfig.CONFIG:
        port = catoconfig.CONFIG["csk_ui_port"]
        sys.argv.append(port)

    # enable ssl?
    if catocommon.is_true(catoconfig.CONFIG.get("csk_ui_use_ssl")):
        logger.info("Using SSL/TLS...")
        sslcert = catoconfig.CONFIG.get("csk_ui_ssl_cert", os.path.join(catoconfig.CONFDIR, "cato.crt"))
        sslkey = catoconfig.CONFIG.get("csk_ui_ssl_key", os.path.join(catoconfig.CONFDIR, "cato.key"))
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
        logger.info("Using standard HTTP. (Set csk_ui_use_ssl to 'true' in cato.conf to enable SSL/TLS.)")

    app.add_processor(auth_app_processor)
    app.notfound = notfound

    app.run()
