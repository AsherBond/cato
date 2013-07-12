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
from catolog import catolog
logger = catolog.get_logger(__name__)

import web
import base64
import hmac
import hashlib
from datetime import datetime, timedelta
from catocommon import catocommon
from catosettings import settings
from catoconfig import catoconfig
from catotag import tag

# An authenticated user sets a few global properties
_USER_ID = None
_USER_FULLNAME = None
_USER_ROLE = None
_USER_TAGS = None
_ADMIN = False
_DEVELOPER = False

"""
Endpoints have a simple name, but the code could exist in one of several modules.

So, this mapping dictionary gives us the proper python module.class.function for an endpoint name.
"""

endpoints = {
			 "list_tasks" : "catoapi.taskMethods/list_tasks",
			 "add_cloud_keypair" : "catoapi.cloudMethods/add_cloud_keypair",
			 "create_cloud" : "catoapi.cloudMethods/create_cloud",
			 "create_account" : "catoapi.cloudMethods/create_account",
			 "create_credential" : "catoapi.sysMethods/create_credential",
			 "create_document" : "catoapi.dsMethods/create_document",
			 "create_tag" : "catoapi.sysMethods/create_tag",
			 "create_task" : "catoapi.taskMethods/create_task",
			 "create_task_from_json" : "catoapi.taskMethods/create_task_from_json",
			 "create_user" : "catoapi.sysMethods/create_user",
			 "delete_cloud_keypair" : "catoapi.cloudMethods/delete_cloud_keypair",
			 "delete_credential" : "catoapi.sysMethods/delete_credential",
			 "delete_tag" : "catoapi.sysMethods/delete_tag",
			 "delete_task" : "catoapi.taskMethods/delete_task",
			 "describe_task_parameters" : "catoapi.taskMethods/describe_task_parameters",
			 "export_task" : "catoapi.taskMethods/export_task",
			 "get_task_instances" : "catoapi.taskMethods/get_task_instances",
			 "get_cloud" : "catoapi.cloudMethods/get_cloud",
			 "get_account" : "catoapi.cloudMethods/get_account",
			 "get_document" : "catoapi.dsMethods/get_document",
			 "get_document_value" : "catoapi.dsMethods/get_document_value",
			 "get_settings" : "catoapi.sysMethods/get_settings",
			 "get_system_log" : "catoapi.sysMethods/get_system_log",
			 "get_task" : "catoapi.taskMethods/get_task",
			 "get_task_instance" : "catoapi.taskMethods/get_task_instance",
			 "get_task_instances" : "catoapi.taskMethods/get_task_instances",
			 "get_task_instance_status" : "catoapi.taskMethods/get_task_instance_status",
			 "get_task_log" : "catoapi.taskMethods/get_task_log",
			 "get_task_parameters" : "catoapi.taskMethods/get_task_parameters",
			 "get_token" : "catoapi.sysMethods/get_token",
			 "import_backup" : "catoapi.sysMethods/import_backup",
			 "list_cloud_accounts" : "catoapi.cloudMethods/list_cloud_accounts",
			 "list_cloud_keypairs" : "catoapi.cloudMethods/list_cloud_keypairs",
			 "list_clouds" : "catoapi.cloudMethods/list_clouds",
			 "list_credentials" : "catoapi.sysMethods/list_credentials",
			 "list_document_collections" : "catoapi.dsMethods/list_document_collections",
			 "list_documents" : "catoapi.dsMethods/list_documents",
			 "list_processes" : "catoapi.sysMethods/list_processes",
			 "list_tags" : "catoapi.sysMethods/list_tags",
			 "list_users" : "catoapi.sysMethods/list_users",
			 "reset_password" : "catoapi.sysMethods/reset_password",
			 "resubmit_task_instance" : "catoapi.taskMethods/resubmit_task_instance",
			 "run_task" : "catoapi.taskMethods/run_task",
			 "set_document_value" : "catoapi.dsMethods/set_document_value",
			 "stop_task" : "catoapi.taskMethods/stop_task",
			 "add_object_tag" : "catoapi.sysMethods/add_object_tag",
			 "remove_object_tag" : "catoapi.sysMethods/remove_object_tag",
			 "update_cloud" : "catoapi.cloudMethods/update_cloud",
			 "update_settings" : "catoapi.sysMethods/update_settings",
			 "update_user" : "catoapi.sysMethods/update_user",
			 "reset_password" : "catoapi.sysMethods/reset_password",
			 "add_object_tag" : "catoapi.sysMethods/add_object_tag"
			 }

def authenticate(action, args):
	db = catocommon.new_conn()
	sset = settings.settings.security()
	# if it fails anywhere along the way just return false ...
	# we're not returning error messages that would help a hacker.
	
	# new feature - if a token is provided instead of a full querystring,
	# check that token for validity and timeliness.
	if args.get("token"):
		# tokens are only allowed if the configuration file says so.
		if catocommon.is_true(catoconfig.CONFIG.get("rest_api_enable_tokenauth")):
			# check the token here - looking it up will return a user_id if it's still valid
			sql = "select user_id, created_dt from api_tokens where token = %s" 
			row = db.select_row_dict(sql, (args.get("token")))
			
			if not row:
				return False, None
			if not row["created_dt"] or not row["user_id"]:
				return False, None
			
			# check the expiration date of the token
			now_ts = datetime.utcnow()
			
			mins = 30
			try:
				mins = int(catoconfig.CONFIG.get("rest_api_token_lifespan"))
			except:
				logger.warning("Config setting [rest_api_token_lifespan] not found or is not a number.  Using the default (30 minutes).")
			
			if (now_ts - row["created_dt"]) > timedelta (minutes=mins):
				return False, None
			
			# still all good?  Update the created_dt.
			sql = """update api_tokens set created_dt = str_to_date('{0}', '%%Y-%%m-%%d %%H:%%i:%%s')
				where user_id = '{1}'""".format(now_ts, row["user_id"])
			db.exec_db(sql)
				
			return True, row["user_id"]
		else:
			return False, None
	

	# no token was provided? Go ahead and look into the querystring for auth information
	
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
		return False, "missing args"
	
	# the timestamp used for the signature was URLencoded.  reencode before building our signature.
	ts = ts.replace(":", "%3A")
	string_to_sign = "%s?key=%s&timestamp=%s" % (action, key, ts)
	
	db.ping_db()
	# we need the password for the provided key (user_id)... that's what we use to build the signature.
	sql = """select user_id, user_password, username, status, force_change, failed_login_attempts
		from users 
		where user_id = '{0}' or username = '{0}'""".format(key) 
	row = db.select_row_dict(sql)
	
	if not row:
		return False, "no user"
	
	# first, a few simple checks for this user.
	# 1) is it enabled?
	if row["status"] < 1:
		return False, "disabled"
	# 2) is it requiring a new password?
	# NOTE: only the user explicitly named 'administrator' can use the API if force_change = 1
	if row["force_change"] > 0 and row["username"] != "administrator":
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
		return False, "signature mismatch"
	
	db.close()

	# made it here... we're authenticated!
	return True, key

def filter_set_by_tag(rows):
	# if permissions checking is turned off, everything is allowed
	if catoconfig.CONFIG["ui_permissions"] == "false":
		return rows

	if _USER_ROLE == "Administrator":
		return rows
	else:
		tags = tag.ObjectTags(1, _USER_ID)
		filtered = []
		if tags and rows:
			for row in rows:
				if set(tags) & set(row["Tags"].split(",") if row["Tags"] else []):
					filtered.append(row)
		return filtered

def is_object_allowed(object_id, object_type):
	# given a task id, we need to find the original task id,
	# then check if the user can see it based on tags
	if _USER_ROLE == "Administrator":
		return True
	
	if not object_id or not object_type:
		logger.error("Invalid or missing Object ID or Object Type.")
		return False
	
	sql = """select 1 from object_tags otu
	    join object_tags oto on otu.tag_name = oto.tag_name
	    where (otu.object_type = 1)
	    and otu.object_id = %s
	    and oto.object_type = %s
	    and oto.object_id = %s""" 
	
	db = catocommon.new_conn()
	result = db.select_col_noexcep(sql, (_USER_ID, object_type, object_id))
	db.close()
	
	return catocommon.is_true(result)

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
		UpdateError = "UpdateError"
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
		
		dom = catocommon.ET.fromstring('<apiResponse />')
		catocommon.ET.SubElement(dom, "method").text = self.Method
		
		# if there was no response, we can't crash
		if self.Response:
			# try to parse it and catch ... if it's xml add it, else add it as text
			try:
				test = catocommon.ET.fromstring(self.Response)
				r = catocommon.ET.SubElement(dom, "response")
				r.append(test)
			except Exception:  # (ElementTree.ParseError is a subclass of SyntaxError)
				# no need to print the exception... it just means the self.Response couldn't be converted to xml
				# that's ok, a non-xml response is allowed and handled here.
				# if ex:
					# print str(ex)
				catocommon.ET.SubElement(dom, "response").text = self.Response
		else:
			catocommon.ET.SubElement(dom, "response").text = ""
		
		# include an error section if necessary
		if self.ErrorCode != "":
			e = catocommon.ET.SubElement(dom, "error")
			catocommon.ET.SubElement(e, "code").text = self.ErrorCode
			catocommon.ET.SubElement(e, "message").text = self.ErrorMessage
			catocommon.ET.SubElement(e, "detail").text = self.ErrorDetail
		
		return catocommon.ET.tostring(dom)

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
		
		# IF there's an error code, set the HTTP status to 400
		if self.ErrorCode:
			web.ctx.status = "400 Bad Request"

		if output_format == "text":
			return self.asText()
		elif output_format == "json":
			return self.asJSON()
		else:
			return self.asXMLString()
		
