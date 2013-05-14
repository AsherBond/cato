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

import base64
import hmac
import hashlib
from datetime import datetime, timedelta
import time
from catocommon import catocommon
from catosettings import settings

try:
	import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
	import xml.etree.ElementTree as ET
try:
	ET.ElementTree.iterfind
except AttributeError as ex:
	del(ET)
	import catoxml.etree.ElementTree as ET


def authenticate(action, args):
	try:
		db = catocommon.new_conn()
		sset = settings.settings.security()
		# if it fails anywhere along the way just return false ...
		# we're not returning error messages that would help a hacker.
		
		# here's how it works - we need the "action", the "key", the "timestamp" and the signed string
		
		# using the action, key and timestamp, we will:
		# a) build our own string to sign
		# b) sign it
		# c) compare it to what was sent.
		key = getattr(args, 'key', '')
		ts = getattr(args, 'timestamp', '')
		sig = getattr(args, 'signature', '')
		
		# Not enough arguments for the authentication? Fail.
		if action == '' or key == '' or ts == '' or sig == '':
			return False, None
		
		# test the timestamp for er, timeliness
		fmt = "%Y-%m-%dT%H:%M:%S"
		arg_ts = datetime.fromtimestamp(time.mktime(time.strptime(ts, fmt)))
		now_ts = datetime.utcnow()
		
		if (now_ts - arg_ts) > timedelta (seconds=15):
			return False, None
		
		# the timestamp used for the signature was URLencoded.  reencode before building our signature.
		ts = ts.replace(":", "%3A")
		string_to_sign = "%s?key=%s&timestamp=%s" % (action, key, ts)
		
		db.ping_db()
		# we need the password for the provided key (user_id)... that's what we use to build the signature.
		sql = """select user_id, user_password, status, force_change, failed_login_attempts
			from users 
			where user_id = '{0}' or username = '{0}'""".format(key) 
		row = db.select_row_dict(sql)
		
		if not row:
			return False, None
		
		# first, a few simple checks for this user.
		# 1) is it enabled?
		if row["status"] < 1:
			return False, "disabled"
		# 2) is it requiring a new password?
		if row["force_change"] > 0:
			return False, "password change"
		# 3) is it locked?
		if row["failed_login_attempts"] >= sset.PassMaxAttempts:
			return False, "locked"
		
		# from here on down, 'key' is the user_id
		key = row["user_id"]
		# decrypt the password so we can use it to generate the signature
		pwd = catocommon.cato_decrypt(row["user_password"])
		
		signed = base64.b64encode(hmac.new(pwd, msg=string_to_sign, digestmod=hashlib.sha256).digest())
		
		if signed != sig:
			return False, None
		
		# made it here... we're authenticated!
		return True, key
	except Exception as ex:
		raise Exception(ex)
	finally:
		db.close()

def check_required_params(required_params, args):
	"""
		Ensure required argument(s) are provided and not empty.
		
		Returns 'True' if there are no args and no required params list.
	"""
	if required_params and args:
		for param in required_params:
			if param:
				if not args.has_key(param):
					resp = response(err_code="MissingParameter", err_detail="Required parameter '%s' missing." % param)
					return False, resp
				elif len(args[param]) == 0:
					resp = response(err_code="EmptyParameter", err_detail="Required parameter '%s' empty." % param)
					return False, resp

		# all good
		return True, None
	else:
		return True, None

class response:
	"""The apiResponse class is used for all API calls.  It's the standard response for everything."""
	class Codes():
		Exception = "Exception"
		Forbidden = "Forbidden"
		CreateError = "CreateError"
		DeleteError = "DeleteError"
		GetError = "GetError"
		ListError = "ListError"
		ProcessError = "ProcessError"
		StartFailure = "StartFailure"
		StopFailure = "StopFailure"	

	def __init__(self, method="", response="", err_code="", err_msg="", err_detail=""):
		self.Method = method
		self.Response = response
		self.ErrorCode = err_code
		self.ErrorMessage = err_msg
		self.ErrorDetail = err_detail
		
	def asXMLString(self):
		"""Returns the response as an XML string"""
		
		dom = ET.fromstring('<apiResponse />')
		ET.SubElement(dom, "method").text = self.Method
		
		# if there was no response, we can't crash
		if self.Response:
			# try to parse it and catch ... if it's xml add it, else add it as text
			try:
				test = ET.fromstring(self.Response)
				r = ET.SubElement(dom, "response")
				r.append(test)
			except Exception:  # (ElementTree.ParseError is a subclass of SyntaxError)
				# no need to print the exception... it just means the self.Response couldn't be converted to xml
				# that's ok, a non-xml response is allowed and handled here.
				# if ex:
					# print str(ex)
				ET.SubElement(dom, "response").text = self.Response
		else:
			ET.SubElement(dom, "response").text = ""
		
		# include an error section if necessary
		if self.ErrorCode != "":
			e = ET.SubElement(dom, "error")
			ET.SubElement(e, "code").text = self.ErrorCode
			ET.SubElement(e, "message").text = self.ErrorMessage
			ET.SubElement(e, "detail").text = self.ErrorDetail
		
		return ET.tostring(dom)

	def asJSON(self):
		"""Returns the response as a JSON string"""
		try:
			# if there was no response, we can't crash
			if self.Response is None:
				self.Response = ""
				
			return catocommon.ObjectOutput.AsJSON(self.__dict__)
		except Exception as ex:
			return ex.__str__()

	def asText(self):
		"""
		Returns ONLY THE RESPONSE as plain text.
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
		
