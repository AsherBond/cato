#!/usr/bin/env python

#########################################################################
# 
# Copyright 2012 Cloud Sidekick
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

import web
import sys
import os
import json
from web.wsgiserver import CherryPyWSGIServer

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catoconfig import catoconfig
from catocommon import catocommon, catoprocess
from catoui import uiGlobals, uiCommon
from catoapi import api
from catolog import catolog
from catouser import catouser
from catoerrors import InfoException

app_name = "cato_rest_api"
logger = catolog.get_logger(app_name)

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
        return self.go(method)
    
    def POST(self, method):
        return self.go(method)
    
    def go(self, method):
        args = web.input()
        # web.header('Content-Type', 'text/xml')

        # here's the rub - if this was a POST, there might be lots of additional data in web.data().
        # but the keys in web.input() are valid too.
        # so, merge them.
        if web.data():
            postargs = json.loads(web.data())
            logger.info("Post Data: %s" % postargs)
            for k, v in postargs.iteritems():
                args[k] = v
    

        logger.info("Request: %s" % method)
        logger.info("Args: %s" % args)

        output_format = ""
        if args.has_key("output_format"):
            output_format = args["output_format"]
        
        is_authenticated, user_id = api.authenticate(method, args)
        if not is_authenticated:
            # authentication failures won't return details to the client
            # but will write some info in the api log
            # the second return arg holds a failure code
            if getattr(args, 'key', ''):
                logger.error("Authentication Failure [%s] - [%s]" % (getattr(args, 'key', ''), user_id))
            else:
                logger.error("Authentication Failure [%s]" % user_id)

            response = api.response(err_code="AuthenticationFailure")
            return response.Write(output_format)
        
        # the args collection is passed to the target function, BUT
        # we wanna stick a few things in there we might need.
        # (using an _ prefix to avoid conflicts)
        args["_user_id"] = user_id
        args["output_format"] = output_format
        args["_admin"] = False
        args["_developer"] = False
        
        # the API commands do some logging that use these detail properties
        u = catouser.User()
        u.FromID(user_id)
        if u:
            args["role"] = u.Role
            args["_user_full_name"] = u.FullName
            
            # flags are set so certain methods can have restricted access.
            if u.Role == "Administrator":
                args["_admin"] = True
                args["_developer"] = True
            if u.Role == "Developer":
                args["_developer"] = True
        else:
            logger.error("Authenticated, but unable to build a User object.")
            response = api.response(err_code="Exception", err_msg="Authenticated, but unable to build a User object.")
            return response.Write(output_format)

        response = catocommon.FindAndCall("catoapi." + method, args)
        # FindAndCall can have all sorts of return values.
        # in this case, we expect it would be an api.response object.
        # but never assume
        if hasattr(response, "Method"):
            response.Method = method

            # is this a JSONP request?        
            if "callback" in args:
                """
                    IF there is an arg called "callback", that means we want the results formatted as a javascript function call.
                    
                    (of course, if we wanna eventually support both XML and JSON result types that's fine...
                    it just means the payload *inside* the jsonp callback will be xml or json as requested.)
                """
                payload = response.Write(output_format)
                #base64 encode it (don't forget the three special chars)
                #payload = base64.b64encode(payload)
                #payload = payload.replace("=", "%3D").replace("+", "%2B").replace("/", "%2F")
                
                web.header('Content-Type', 'application/json')
                return "%s('%s')" % (args["callback"], payload)
            else:
                return response.Write(output_format)
        else:
            # the result from FindAndCall wasn't a response object.
            # so make one
            response = api.response(err_code=api.response.Codes.Exception, err_detail=response)
            return response.Write(output_format)

#    def POST(self, method):
#        return catocommon.FindAndCall("catoapi." + method)

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
        
class version:        
    def GET(self):
        args = web.input()
        output_format = args["output_format"] if args.has_key("output_format") else ""
        version = catoconfig.VERSION

        if output_format == "json":
            response = api.response(response='{"Version" : "%s"}' % version)
        elif output_format == "text":
            response = api.response(response=version)
        else:
            response = api.response(response="<Version>%s</Version>" % version)
            
        return response.Write(output_format)
            
class configure:       
    """
    Meant to be called once, on the initial installation of Cato.
    
    Will create the Administrator account, and default values for settings tables.
    
    Will not create any data rows if they already exist.
    """ 
    def GET(self):
        args = web.input()
        db = catocommon.new_conn()
        
        out = []
        out.append("Configuring Cato...\n\n")

        # should we create the Administrator account
        msg = "Administrator Account:"
        out.append(msg)
        logger.info(msg)
        sql = "select count(*) from users where username = 'Administrator'"
        cnt = db.select_col_noexcep(sql)
        if not cnt:
            msg = "    Administrator account not found, creating..."
            out.append(msg)
            logger.info(msg)
            pw = catocommon.cato_encrypt("password")
            sql = """INSERT INTO users 
                (user_id, username, full_name, status, authentication_type, failed_login_attempts, force_change, email, user_role, user_password) 
                VALUES (
                '0002bdaf-bfd5-4b9d-82d1-fd39c2947d19','administrator','Administrator',1,'local',0,1,'','Administrator',%s
                )"""
            db.exec_db_noexcep(sql, (pw))            
            
            sql = """INSERT INTO user_password_history (user_id, change_time, password) 
                VALUES ('0002bdaf-bfd5-4b9d-82d1-fd39c2947d19',now(),%s)"""
            db.exec_db_noexcep(sql, (pw))            

        else:
            msg = "    Administrator account already exists."
            out.append(msg)
            logger.info(msg)


        # settings rows
        msg = "Default Settings:"
        out.append(msg)
        logger.info(msg)
        
        # scheduler
        sql = "select count(*) from scheduler_settings"
        cnt = db.select_col_noexcep(sql)
        if not cnt:
            msg = "    Scheduler settings..."
            out.append(msg)
            logger.info(msg)
            sql = """INSERT INTO scheduler_settings (id, mode_off_on, loop_delay_sec, schedule_min_depth, schedule_max_days, clean_app_registry) 
                VALUES (1,'on',5,10,60,5)"""
            db.exec_db_noexcep(sql)            
        else:
            msg = "    Scheduler settings already exist."
            out.append(msg)
            logger.info(msg)
            
        # poller
        sql = "select count(*) from poller_settings"
        cnt = db.select_col_noexcep(sql)
        if not cnt:
            msg = "    Poller settings..."
            out.append(msg)
            logger.info(msg)
            sql = """INSERT INTO poller_settings (id, mode_off_on, loop_delay_sec, max_processes, app_instance) 
                VALUES (1,'on',3,4,'DEFAULT')"""
            db.exec_db_noexcep(sql)            
        else:
            msg = "    Poller settings already exist."
            out.append(msg)
            logger.info(msg)
            
        # messenger
        sql = "select count(*) from messenger_settings"
        cnt = db.select_col_noexcep(sql)
        if not cnt:
            msg = "    Messenger settings..."
            out.append(msg)
            logger.info(msg)
            sql = """INSERT INTO messenger_settings (id, mode_off_on, loop_delay_sec, retry_delay_min, retry_max_attempts, smtp_server_addr, smtp_server_user, smtp_server_password, smtp_server_port, smtp_timeout, smtp_ssl, from_email, from_name, admin_email) 
                VALUES (1,'off',30,1,5,'','','',25,10,0,'user@example.com','Cloud Sidekick Messenger','')"""
            db.exec_db_noexcep(sql)            
        else:
            msg = "    Messenger settings already exist."
            out.append(msg)
            logger.info(msg)

        # security
        sql = "select count(*) from login_security_settings"
        cnt = db.select_col_noexcep(sql)
        if not cnt:
            msg = "    Security settings..."
            out.append(msg)
            logger.info(msg)
            sql = """INSERT INTO login_security_settings (id, pass_max_age, pass_max_attempts, pass_max_length, pass_min_length, pass_complexity, pass_age_warn_days, pass_require_initial_change, auto_lock_reset, login_message, auth_error_message, pass_history, page_view_logging, report_view_logging, allow_login, new_user_email_message, log_days) 
                VALUES (1,90,99,15,6,0,5,0,5,'New Cato Install','Login Error - Please check your user id and password.',0,0,0,1,'',90)"""
            db.exec_db_noexcep(sql)            
        else:
            msg = "    Security settings already exist."
            out.append(msg)
            logger.info(msg)
            
        # security
        sql = "select count(*) from marshaller_settings"
        cnt = db.select_col_noexcep(sql)
        if not cnt:
            msg = "    Marshaller settings..."
            out.append(msg)
            logger.info(msg)
            sql = """INSERT INTO marshaller_settings (id, mode_off_on, loop_delay_sec) 
                VALUES (1,'on',3)"""
            db.exec_db_noexcep(sql)            
        else:
            msg = "    Marshaller settings already exist."
            out.append(msg)
            logger.info(msg)



        # should we create AWS clouds?
        if args.get("createclouds"):
            from catocloud import cloud
            msg = "Checking Static Clouds..."
            out.append(msg)
            logger.info(msg)
            success = cloud.create_static_clouds()
            if success:
                msg = "... done."
                out.append(msg)
                logger.info(msg)
            else:
                msg = "    Errors occurred while creating Clouds.  Please check the REST API logfile for details."
                out.append(msg)
                logger.info(msg)
                
                


        db.close()
        out.append("\n")
        return "\n".join(out)

        
            
# the default page if no URI is given, just an information message
class index:        
    def GET(self):
        args = web.input()
        listonly = True if args.has_key("listonly") else False
        
        out = []
        out.append("---------------------------")
        out.append("- Cloud Sidekick REST API -")
        out.append("---------------------------\n")
        
        try:
            from catoapi import taskMethods
            
            for attname in dir(taskMethods.taskMethods):
                att = getattr(taskMethods.taskMethods, attname, None)
                if att:
                    if hasattr(att, "__name__"):
                        if listonly:
                            out.append("taskMethods/%s" % att.__name__)
                        else:
                            out.append("----------\n")
                            out.append("Method: taskMethods/%s" % att.__name__)
                            if att.__doc__:
                                out.append("%s" % att.__doc__)
                        

            from catoapi import sysMethods
            
            for attname in dir(sysMethods.sysMethods):
                att = getattr(sysMethods.sysMethods, attname, None)
                if att:
                    if hasattr(att, "__name__"):
                        if listonly:
                            out.append("sysMethods/%s" % att.__name__)
                        else:
                            out.append("----------\n")
                            out.append("Method: sysMethods/%s" % att.__name__)
                            if att.__doc__:
                                out.append("%s" % att.__doc__)
                        
            try:      
                from catoapi import depMethods
                
                msg = "- The following API commands are available only if Cloud Sidekick Maestro is installed. -"
                out.append("-" * len(msg))
                out.append(msg)
                out.append("-" * len(msg))
                                    
                for attname in dir(depMethods.depMethods):
                    att = getattr(depMethods.depMethods, attname, None)
                    if att:
                        if hasattr(att, "__name__"):
                            if listonly:
                                out.append("depMethods/%s" % att.__name__)
                            else:
                                out.append("----------\n")
                                out.append("Method: depMethods/%s" % att.__name__)
                                if att.__doc__:
                                    out.append("%s" % att.__doc__)
            except ImportError:
                # depMethods is a Maestro module, don't error if it's missing.
                pass

                    
            try:      
                from catoapi import dsMethods
                
                for attname in dir(dsMethods.dsMethods):
                    att = getattr(dsMethods.dsMethods, attname, None)
                    if att:
                        if hasattr(att, "__name__"):
                            if listonly:
                                out.append("dsMethods/%s" % att.__name__)
                            else:
                                out.append("----------\n")
                                out.append("Method: dsMethods/%s" % att.__name__)
                                if att.__doc__:
                                    out.append("%s" % att.__doc__)
            except ImportError:
                # dsMethods is a Maestro module, don't error if it's missing.
                pass

            
            out.append("\n")
                    
                    
        except Exception as ex:
            out.append(ex.__str__())
        finally:
            return "\n".join(out)


class ExceptionHandlingApplication(web.application):
    def handle(self):
        try:
            return web.application.handle(self)
        except (web.HTTPError, KeyboardInterrupt, SystemExit):
            raise
        except InfoException as ex:
            # we're using a custom HTTP status code to indicate 'information' back to the user.
            web.ctx.status = "280 Informational Response"
            logger.exception(ex.__str__())
            return ex.__str__()
        except Exception as ex:
            args = web.input()
            output_format = args["output_format"] if args.has_key("output_format") else ""
            web.ctx.status = "400 Bad Request"
            logger.exception(ex.__str__())
            response = api.response(err_code=api.response.Codes.Exception, err_detail=ex.__str__())
            return response.Write(output_format)
        
def main():
    dbglvl = 20
    if "rest_api_debug" in catoconfig.CONFIG:
        try:
            dbglvl = int(catoconfig.CONFIG["rest_api_debug"])
        except:
            raise Exception("rest_api_debug setting in cato.conf must be an integer between 0-50.")
    catolog.DEBUG = dbglvl

    server = catoprocess.CatoService(app_name)
    server.startup()

    # now that the service is set up, we'll know what the logfile name is.
    # so reget the logger
    logger = catolog.get_logger(app_name)
    catolog.set_debug(dbglvl)

    if len(sys.argv) < 2:
        port = "4001"
        if "rest_api_port" in catoconfig.CONFIG:
            port = catoconfig.CONFIG["rest_api_port"]
        sys.argv.append(port)

    # enable ssl?
    if catocommon.is_true(catoconfig.CONFIG.get("rest_api_use_ssl")):
        logger.info("Using SSL/TLS...")
        sslcert = catoconfig.CONFIG.get("rest_api_ssl_cert", os.path.join(base_path, "conf", "cato.crt"))
        sslkey = catoconfig.CONFIG.get("rest_api_ssl_key", os.path.join(base_path, "conf", "cato.key"))
        try:
            with open(sslcert): pass
            logger.debug("SSL Certificate [%s]" % sslcert)
            CherryPyWSGIServer.ssl_certificate = sslcert
        except:
            raise Exception("SSL Certificate not found at [%s]" % sslcert)
        try:
            with open(sslkey): pass
            logger.debug("SSL Key [%s]" % sslkey)
            CherryPyWSGIServer.ssl_private_key = sslkey
        except:
            raise Exception("SSL Key not found at [%s]" % sslcert)
    else:
        logger.info("Using standard HTTP. (Set rest_api_use_ssl to 'true' in cato.conf to enable SSL/TLS.)")
        
    urls = (
        '/', 'index',
        '/version', 'version',
        '/configure', 'configure',
        '/getlog', 'getlog',
        '/setdebug', 'setdebug',
        '/(.*)', 'wmHandler'
    )

    app = ExceptionHandlingApplication(urls, globals(), autoreload=True)

    uiGlobals.web = web
    
    # setting this to True seems to show a lot more detail in UI exceptions
    web.config.debug = False

    app.run()
    
