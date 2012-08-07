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


from catocommon import catocommon
from catoui import uiGlobals

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
        return catocommon.FindAndCall("catoapi." + method)

    def POST(self, method):
        return catocommon.FindAndCall("catoapi." + method)


def notfound():
	return web.notfound("Sorry, the page you were looking for was not found.")
		
# the default page if no URI is given, just an information message
class index:        
	def GET(self):
		return 'Cloud Sidekick REST API.'

urls = (
    '/', 'index',
    '/(.*)', 'wmHandler'
)

if __name__ == "__main__":

	server = catocommon.CatoService("storm_front")
	server.startup()

	if len(sys.argv) < 2:
		config = catocommon.read_config()
		if "stormapiport" in config:
			port = config["stormapiport"]
			sys.argv.append(port)

	app = web.application(urls, globals(), autoreload=True)

	uiGlobals.web = web
	uiGlobals.server = server
	uiGlobals.config = config
	
	# setting this to True seems to show a lot more detail in UI exceptions
	web.config.debug = False

	app.run()
	
