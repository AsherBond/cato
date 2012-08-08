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

"""Common API functions."""

import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta
import time
from catocryptpy import catocryptpy
from catocommon import catocommon

try:
	import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
	import xml.etree.ElementTree as ET
try:
	ET.ElementTree.iterfind
except AttributeError as ex:
	del(ET)
	import catoxml.etree.ElementTree as ET

def authentivalidate(method_name, server, args, required_params=[]):
	print("Request: %s" % method_name)
	print("Args: %s" % args)
	print("\n\n")

	is_authenticated, user_id = authenticate(server, method_name, args)
	if not is_authenticated:
		resp = response(method=method_name,
			error_code="AuthenticationFailure", error_detail="")
		return None, resp.Write()
	
	
	has_required, resp = check_required_params(method_name, required_params, args)
	if not has_required:
		return None, resp

	return user_id, None

def authenticate(server, action, args):
	#if it fails anywhere along the way just return false ...
	# we're not returning error messages that would help a hacker.
	
	#here's how it works - we need the "action", the "key", the "timestamp" and the signed string
	
	#using the action, key and timestamp, we will:
	# a) build our own string to sign
	# b) sign it
	# c) compare it to what was sent.
	key = getattr(args, 'key', '')
	ts = getattr(args, 'timestamp', '')
	sig = getattr(args, 'signature', '')
	
	#ALERT: for internal testing purposes, a hardcoded key will always pass
	if key == "12:34:56:78:90":
		return True, "0002bdaf-bfd5-4b9d-82d1-fd39c2947d19"
	#REMOVE BEFORE RELEASE
	
	#Not enough arguments for the authentication? Fail.
	if action == '' or key == '' or ts == '' or sig == '':
		return False, None
	
	#test the timestamp for er, timeliness
	fmt = "%Y-%m-%dT%H:%M:%S"
	arg_ts = datetime.fromtimestamp(time.mktime(time.strptime(ts, fmt)))
	now_ts = datetime.utcnow()
	
	if (now_ts - arg_ts) > timedelta (seconds=15):
		return False, None
	
	#the timestamp used for the signature was URLencoded.  reencode before building our signature.
	ts = ts.replace(":", "%3A")
	string_to_sign = "%s?key=%s&timestamp=%s" % (action, key, ts)
	
	server.db.ping_db()
	#we need the password for the provided key (user_id)... that's what we use to build the signature.
	sql = """select user_password from users where user_id = %s""" 
	encpwd = server.db.select_col(sql, key)
	
	if not encpwd:
		return False, None
	
	#decrypt the password so we can use it to generate the signature
	pwd = catocryptpy.decrypt_string(encpwd, server.config["key"])
	
	signed = base64.b64encode(hmac.new(pwd, msg=string_to_sign, digestmod=hashlib.sha256).digest())
	
	if signed != sig:
		return False, None
	
	#made it here... we're authenticated!
	return True, key

def perform_callback(web, callback, response):
	"""
		IF there is an arg called "callback", that means we want the results formatted as a javascript function call.
		
		(of course, if we wanna eventually support both XML and JSON result types that's fine...
		it just means the payload *inside* the jsonp callback will be xml or json as requested.)
	"""
	payload = response.Write()
	#base64 encode it (don't forget the three special chars)
	payload = base64.b64encode(payload)
	payload = payload.replace("=", "%3D").replace("+", "%2B").replace("/", "%2F")
	
	web.header('Content-Type', 'application/json')
	return "%s('%s')" % (callback, payload)

def check_required_params(meth, required_params, args):
	"""
		Ensure required argument(s) are provided and not empty.
		
		Returns 'True' if there are no args and no required params list.
	"""
	if required_params and args:
		for param in required_params:
			if param:
				if not args.has_key(param):
					resp = response(method=meth,
						error_code="MissingParameter", error_detail="Required parameter '%s' missing." % param)
					x = resp.Write()
					print x
					return False, x
				elif len(args[param]) == 0:
					print "4"
					resp = response(method=meth,
						error_code="EmptyParameter", error_detail="Required parameter '%s' empty." % param)
					x = resp.Write()
					print x
					return False, x

		# all good
		return True, None
	else:
		return True, None

class response:
	"""The apiResponse class is used for all API calls.  It's the standard response for everything."""
	def __init__(self, method="", response="", error_code="", error_message="", error_detail=""):
		self.Method = method
		self.Response = response
		self.ErrorCode = error_code
		self.ErrorMessage = error_message
		self.ErrorDetail = error_detail

	def asXMLString(self):
		"""Returns the response as an XML string"""
		
		dom = ET.fromstring('<apiResponse />')
		ET.SubElement(dom, "method").text = self.Method
		
		#try to parse it and catch ... if it's xml add it, else add it as text
		try:
			test = ET.fromstring(self.Response)
			r = ET.SubElement(dom, "response")
			r.append(test)
		except Exception: #(ElementTree.ParseError is a subclass of SyntaxError)
			#no need to print the exception... it just means the self.Response couldn't be converted to xml
			#that's ok, a non-xml response is allowed and handled here.
			#if ex:
				#print str(ex)
			ET.SubElement(dom, "response").text = self.Response
		
		#include an error section if necessary
		if self.ErrorCode != "":
			e = ET.SubElement(dom, "error")
			ET.SubElement(e, "code").text = self.ErrorCode
			ET.SubElement(e, "message").text = self.ErrorMessage
			ET.SubElement(e, "detail").text = self.ErrorDetail
		
		return ET.tostring(dom)

	def asJSON(self):
		"""Returns the response as a JSON string"""
		try:
			print "@@@"
			print self.Method
			print self.__dict__
			return json.dumps(self.__dict__, default=catocommon.jsonSerializeHandler)
		except Exception as ex:
			return ex.__str__()

	def asText(self):
		"""
		Returns ONY THE RESPONSE as plain text.
		If there's no response, it'll cascade across the error fields,
		ultimately returning a generic message if nothing is available.
		"""
		try:
			if self.Response:
				return self.Response
			elif self.ErrorMessage:
				return self.ErrorMessage
			elif self.ErrorDetail:
				return self.ErrorDetail
			elif self.ErrorCode:
				return self.ErrorCode
			else:
				return "The response is empty."
		except Exception as ex:
			return ex.__str__()

	def Write(self, output_format=""):
		"""Returns the response in whatever format is specified here."""
		if output_format == "text":
			return self.asText()
		elif output_format == "json":
			return self.asJSON()
		else:
			return self.asXMLString()
		