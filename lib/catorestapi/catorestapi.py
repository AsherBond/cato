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

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catoconfig import catoconfig
from catocommon import catocommon, catoprocess
from catoui import uiGlobals, uiCommon
from catoapi import api
from catolog import catolog
from catouser import catouser

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
        args = web.input()
        # web.header('Content-Type', 'text/xml')

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
        try:
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
        except Exception as ex:
            logger.error(ex.__str__())
            
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


def main():

    server = catoprocess.CatoService(app_name)
    server.startup()

    # now that the service is set up, we'll know what the logfile name is.
    # so reget the logger
    logger = catolog.get_logger(app_name)

    if len(sys.argv) < 2:
        port = "4001"
        if "rest_api_port" in catoconfig.CONFIG:
            port = catoconfig.CONFIG["rest_api_port"]
        sys.argv.append(port)

    urls = (
        '/', 'index',
        '/version', 'version',
        '/getlog', 'getlog',
        '/setdebug', 'setdebug',
        '/(.*)', 'wmHandler'
    )

    app = web.application(urls, globals(), autoreload=True)

    uiGlobals.web = web
    
    # setting this to True seems to show a lot more detail in UI exceptions
    web.config.debug = False

    app.run()
    
