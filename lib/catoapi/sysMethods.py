
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
 
 
"""
System endpoint methods.
"""
from catolog import catolog
logger = catolog.get_logger(__name__)

import json

from catoapi import api
from catoapi.api import response as R
from catocommon import catocommon
from catotask import task
from catouser import catouser
from catosettings import settings
from catoasset import asset
from catotag import tag

class sysMethods:
    """These are utility methods for the Cato system."""

    # ## NOTE:
    # ## many of the functions here aren't done up in pretty classes.
    # ## ... this is sort of a catch-all module.
    def get_token(self, args):
        """Gets an authentication token for the API.  This token will persist for a short period of time, 
so several subsequent API calls can share the same authenticated session.

Returns: A UUID authentication token.
"""
        
        # we wouldn't be here if tradiditional authentication failed.
        # so, the _user_id is the user we wanna create a token for
        token = catocommon.create_api_token(api._USER_ID)
        return R(response=token)

    def import_backup(self, args):
        """Imports an XML or JSON backup file.

Required Arguments: 

* `import_text` - An XML or JSON document in the format of a Cato backup file.

Returns: A list of items in the backup file, with the success/failure of each import.
"""

        # NOTE: this function is a near identical copy of catoadminui/uiMethods.wmCreateObjectsFromXML.
        # Any changes here should be considered there as well.

        # define the required parameters for this call
        required_params = ["import_text"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        # what types of things were in this backup?  what are their new ids?
        items = []

        # here's a save function that's used no matter the format
        def _save(t):
            result, err = t.DBSave()
            if result:
                catocommon.write_add_log(api._USER_ID, catocommon.CatoObjectTypes.Task, t.ID, t.Name, "Created by import.")

                items.append({"type": "task", "id": t.ID, "Name": t.Name, "Info": "Success"}) 
            else:
                if err:
                    items.append({"type": "task", "id": t.ID, "Name": t.Name, "Info": err}) 
                else:
                    items.append({"type": "task", "id": t.ID, "Name": t.Name, "Info": "Unable to create Task. No error available."}) 
            
        # parse it as a validation, and to find out what's in it.
        xd = None
        js = None
        try:
            xd = catocommon.ET.fromstring(args["import_text"])
        except catocommon.ET.ParseError:
            try:
                js = json.loads(args["import_text"])
            except:
                return json.dumps({"error": "Data is not properly formatted XML or JSON."})
        
        if xd is not None:
            for xtask in xd.findall("task"):
                logger.debug("Importing Task [%s]" % xtask.get("name", "Unknown"))
                t = task.Task()
                t.FromXML(catocommon.ET.tostring(xtask), args.get("on_conflict"))
                _save(t)
        # otherwise it might have been JSON
        elif js is not None:
            # if js isn't a list, bail...
            if not isinstance(js, list):
                js = [js]
                
            for jstask in js:
                logger.info("Importing Task [%s]" % jstask.get("name", "Unknown"))
                t = task.Task()
                t.FromJSON(json.dumps(jstask), args.get("on_conflict"))
                _save(t)
        else:
            items.append({"info": "Unable to create Task from backup JSON/XML."})
        
        if args.get("output_format") == "json":
            return R(response=catocommon.ObjectOutput.IterableAsJSON(items))
        elif args.get("output_format") == "text":
            return R(response=catocommon.ObjectOutput.IterableAsText(items, ["Name", "Info"], args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=catocommon.ObjectOutput.IterableAsXML(items, "Results", "Result"))
    
    def list_processes(self, args):        
        """Lists all Cato Processes.
        
Returns: A list of [Process Objects](restapi/api-response-objects.html#Process){:target="_blank"}.
"""
        db = catocommon.new_conn()
        sSQL = """select app_instance as Instance,
            app_name as Component,
            heartbeat as Heartbeat,
            case master when 1 then 'Yes' else 'No' end as Enabled,
            timestampdiff(MINUTE, heartbeat, now()) as MinutesIdle,
            load_value as LoadValue, platform, hostname
            from application_registry
            order by component, master desc"""
        
        rows = db.select_all_dict(sSQL)
        db.close()

        if rows:
            if args.get("output_format") == "json":
                resp = catocommon.ObjectOutput.IterableAsJSON(rows)
                return R(response=resp)
            elif args.get("output_format") == "text":
                keys = ['Instance', 'Component', 'Heartbeat', 'Enabled', 'LoadValue', 'MinutesIdle']
                outrows = []
                if rows:
                    for row in rows:
                        cols = []
                        for key in keys:
                            cols.append(str(row[key]))
                        outrows.append("\t".join(cols))
                      
                return "%s\n%s" % ("\t".join(keys), "\n".join(outrows))
            else:
                dom = catocommon.ET.fromstring('<Processes />')
                if rows:
                    for row in rows:
                        xml = catocommon.dict2xml(row, "Process")
                        node = catocommon.ET.fromstring(xml.tostring())
                        dom.append(node)
                
                return R(response=catocommon.ET.tostring(dom))
        else:
            return R(err_code=R.Codes.ListError, err_detail="Unable to list Processes.")
        
    def reset_password(self, args):
        """Resets the password of the authenticated, or a specified User.

If a user is specified, and the authenticated user is an Administrator, 
this will reset the password of the specified user to the provided value.

If no user is specified, the password of the authenticated user will be changed.

NOTE: to prevent accidental change of an Administrators password, an extra trap is in place:
    * the username (or id) MUST be provided, even if the authenticated user 
        is the user being changed.

Required Arguments: 

* `password` - the new password.

Optional Arguments:

* `user` - Either the User ID or Name.

Returns: Success message if successful, error messages on failure.
"""
        user = args.get("user")
        new_pw = args.get("password")

        # this is a admin function, kick out 
        if user and not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")

        # the only way to reset an "Administrator" role password
        # is to BE an Administrator and SPECIFY a user, even if the user is you
        if not user and api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_detail="Administrators must specify a user to change.")

        generate = catocommon.is_true(args.get("generate"))

        obj = catouser.User()
        obj.FromName(user)

        if obj.ID:
            # if a password was provided, or the random flag was set...exclusively
            if new_pw:
                # if the user requesting the change *IS* the user being changed...
                # set force_change to False
                force = True
                if obj.ID == api._USER_ID:
                    force = False
                    
                obj.ChangePassword(new_password=new_pw, force_change=force)
            elif generate:
                obj.ChangePassword(generate=generate)
        else:
            return R(err_code=R.Codes.GetError, err_detail="Unable to update password.")

        
        catocommon.write_change_log(api._USER_ID, catocommon.CatoObjectTypes.User, obj.ID, obj.FullName, "Password change/reset via API.")
        return R(response="[%s] password operation successful." % obj.FullName)
            
    def create_user(self, args):
        """Creates a new user account.

Only an 'Administrator' can create other users.  If the credentials used for this API call 
are not an Administrator, the call will not succeed.

Required Arguments: 

* `user` - A login name for the user.
* `name` - The full name of the user.
* `role` - The users role.  Valid values: 
    
    * Administrator
    * Developer
    * User

Optional Arguments:

* `password` - Password for the user. If password is not provided, a random password will be generated.
* `email` - Email address for the user.  Required if 'password' is omitted.
* `authtype` - 'local' or 'ldap'.  Default is 'local' if omitted.
* `forcechange` - Require user to change password. Default is 'true' if omitted. (Valid values: 'true' or 'false')
* `status` - Status of the new account. Default is 'enabled' if omitted. (Valid values: enabled, disabled, locked)
* `expires` - Expiration date for this account.  Default is 'never expires'. Must be in mm/dd/yyyy format.
* `groups` - A list of groups the user belongs to. Group names cannot contain spaces. Comma delimited list.
* `get_token` - If true, will return an automatic login token.  (Valid values: 1, yes, true)

Returns: A [User Object](restapi/api-response-objects.html#User){:target="_blank"}.
"""

        # this is a admin function, kick out 
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")

        # define the required parameters for this call
        required_params = ["user", "name", "role"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        generate = True if not args.get("password") else False
        if generate and not args.get("email"):
            return R(err_code=R.Codes.Exception, err_detail="Email is required if password is omitted.")

        status = args.get("status", 1)  # default if omitted is 'enabled'

        groups = args.get("groups").split(",") if args.get("groups") else None
        
        # validate the expiration date is properly formatted, otherwise pass None
        import dateutil.parser as parser
        expiration_dt = None
        try:
            tmp = parser.parse(args.get("expires"))
            expiration_dt = tmp.strftime("%m/%d/%Y")
        except:
            pass

        obj = catouser.User.DBCreateNew(username=args["user"],
                                        fullname=args["name"],
                                        role=args["role"],
                                        password=args.get("password"),
                                        generatepw=generate,
                                        authtype=args.get("authtype"),
                                        forcechange=args.get("forcechange"),
                                        email=args.get("email"),
                                        status=status,
                                        expires=expiration_dt,
                                        groups=groups)
        
        # do we get a login token?
        if catocommon.is_true(args.get("get_token")):
            obj.GetToken()

        if obj:
            catocommon.write_add_log(api._USER_ID, catocommon.CatoObjectTypes.User, obj.ID, obj.LoginID, "User created by API.")
            if args.get("output_format") == "json":
                return R(response=obj.AsJSON())
            elif args.get("output_format") == "text":
                return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=obj.AsXML())
        else:
            return R(err_code=R.Codes.CreateError, err_detail="Unable to create User.")
            
    def update_user(self, args):
        """Updates a user account.

Only an 'Administrator' can manage other users.  If the credentials used for this API call 
are not an Administrator, the call will not succeed.

Properties will only be updated if the option is provided.  Omitted properties will not be changed.

NOTE: the "username" of a user cannot be changed.

Password cannot be updated by this method.  Use "reset_password" instead.

If a user has 'locked' their account by numerous failed login attempts, the flag is reset 
by setting any property.  It's easiest to just the status to 'enabled'.

Required Arguments: 

* `user` - ID or Name of the User to update.

Optional Arguments:

* `name` - The full name of the user.
* `role` - The users role.  (Valid values: Administrator, Developer, User)
* `email` - Email address for the user.  Can be cleared with "None".
* `authtype` - 'local' or 'ldap'.
* `forcechange` - Require user to change password on next login. (Valid values: 'true' or 'false')
* `status` - Status of the account. (Valid values: enabled, disabled, locked)
* `expires` - Expiration date for this account.  Must be in mm/dd/yyyy format. Can be cleared with "None".
* `groups` - Add to the list of groups the user belongs to. Group names cannot contain spaces. Comma delimited list.

Returns: A [User Object](restapi/api-response-objects.html#User){:target="_blank"}.
"""

        # this is a admin function, kick out 
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")

        # define the required parameters for this call
        required_params = ["user"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = catouser.User()
        obj.FromName(args["user"])
        if not obj.ID:
            return R(err_code=R.Codes.GetError, err_detail="Cannot find User.")
            
        # now we can change the properties
        
        # these can't be null or empty
        obj.FullName = args.get("name", obj.FullName)
        obj.AuthenticationType = args.get("authtype", obj.AuthenticationType)
        obj.Role = args.get("role", obj.Role)
        obj.Status = args.get("status", obj.Status)
        
        # these can be set to null/empty
        obj.Expires = args.get("expires", obj.Expires)

        obj.Email = args.get("email", obj.Email)
        obj.Email = None if obj.Email.lower() == "none" else obj.Email

        
        # this is always reset from the API... one less argument to mess with.
        obj.FailedLoginAttempts = 0

        # these are figured out manually

        # force change
        if args.get("forcechange"):
            obj.ForceChange = 1 if args["forcechange"] == "true" else 1 if str(args["forcechange"]) == "0" else obj.ForceChange
        
        """
        OK this group stuff is a little tricky.  User.DBUpdate requires us to send in the complete list of Groups we want.

        1) the User object already has a list, self.Tags, of all the tags it has.
        2) the caller might have sent a COMPLETE list of tags (from the UI), or only a list to ADD (from the API)
        doesn't really matter.  
        
        So, we:
            a) MERGE self.Tags with self._Groups, we'll get a distinct list of all groups we HAD or want to ADD
            b) delete all tags
            c) insert our new merged list
        """
        groups = args.get("groups").split(",") if args.get("groups") else []
        if obj.Tags is not None:
            groups = obj.Tags + groups  # merge the lists
        obj._Groups = list(set(groups))  # make it distinct
        
        
        # all the properties are set... call DBUpdate!
        if obj.DBUpdate():
            catocommon.write_change_log(api._USER_ID, catocommon.CatoObjectTypes.User, obj.ID, obj.FullName, "User updated via API.")

        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())
            
    def list_users(self, args):        
        """Lists all registered Users.
        
Optional Arguments: 

* `filter` - will filter a value match on: (Multiple filter arguments can be provided, delimited by spaces.)

    * Full Name
    * Login ID
    * Role
    * Email address

Returns: A list of [User Objects](restapi/api-response-objects.html#User){:target="_blank"}.
"""
        # this is a admin function, kick out 
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")

        fltr = args.get("filter", "")

        obj = catouser.Users(sFilter=fltr)
        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())

    def update_settings(self, args):
        """Updates the settings of a Cato process or module.

NOTE: the update_settings command requires submission of a JSON settings object.
As a guide for updating settings, first execute this command with the output_format set to json.

For example, to update Messenger settings, first do:

get_settings?module=messenger&output_format=json

...then use the result as a template for update_settings.

Required Arguments: 

* `module` - name of the module to apply the settings.
* `settings` - a list of name:value setting objects.

Returns: Nothing if successful, error messages on failure.
"""
        mod = args.get("module")
        sets = args.get("settings")

        # this is a admin function, kick out 
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")

        required_params = ["module", "settings"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        if not sets:
            return R(err_code=R.Codes.UpdateError, err_detail="Settings JSON is required.")
            
        # first, validate the settings JSON
        # are the settings json?
        try:
            setsdict = json.loads(sets)
        except Exception as ex:
            return R(err_code=R.Codes.UpdateError, err_detail="Trying to parse settings as JSON failed. %s" % ex)
        
        
        # sweet, use getattr to actually get the class we want!
        objname = getattr(settings.settings, mod.lower())
        obj = objname()
        if obj:
            # spin the sValues array and set the appropriate properties.
            # setattr is so awesome
            for k, v in setsdict.iteritems():
                setattr(obj, k, v)
                # print  "setting %s to %s" % (pair["name"], pair["value"])
            # of course all of our settings classes must have a DBSave method
            obj.DBSave()
            catocommon.add_security_log(api._USER_ID, catocommon.SecurityLogTypes.Security,
                catocommon.SecurityLogActions.ConfigChange, catocommon.CatoObjectTypes.NA, "",
                "%s settings changed via API." % mod.capitalize())
        
            if args.get("output_format") == "json":
                return R(response=obj.AsJSON())
            elif args.get("output_format") == "text":
                return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=obj.AsXML())

    def get_settings(self, args):
        """Lists all the settings of Cato modules.

Optional Arguments: 

* `module` - name of the module. If omitted, all module settings are returned.

Returns: A [Settings Object](restapi/api-response-objects.html#Settings){:target="_blank"}.
"""
        # this is a admin function, kick out 
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")

        mod = args.get("module")
        obj = None
        
        # if a module is provided, just get that one, otherwise get them all
        if mod:
            objname = getattr(settings.settings, mod.lower())
            obj = objname()
        else:
            obj = settings.settings()

        if obj:
            if args.get("output_format") == "json":
                return R(response=obj.AsJSON())
            elif args.get("output_format") == "text":
                return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=obj.AsXML())

    def create_credential(self, args):
        """Creates a new Shared Credential.

> Only a 'Developer' can create Credentials.

Required Arguments: 

* `name` - The full name of the user.
* `username` - A login name for the user.
* `password` - Password for the user. If password is not provided, a random password will be generated.

Optional Arguments:

* `description` - Description of the Credential.
* `privileged` = Additional password required to put certain devices into 'privileged' mode.
* `domain` - A domain for the Credential.

Returns: A [Credential Object](restapi/api-response-objects.html#Credential){:target="_blank"}.
"""

        # this is a admin function, kick out 
        if not api._DEVELOPER:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Developers or Administrators can perform this function.")

        # define the required parameters for this call
        required_params = ["name", "username", "password"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp
        # a little different than the others ... credential objects must be instantiated before calling DBCreateNew
        obj = asset.Credential()
        obj.FromArgs(args["name"], args.get("description"), args["username"], args["password"],
                 0, args.get("domain"), args.get("privileged"), None)
        result = obj.DBCreateNew()
        if not result:
            return R(err_code=R.Codes.CreateError, err_detail="Unable to create Credential.")

        catocommon.write_add_log(api._USER_ID, catocommon.CatoObjectTypes.Credential, obj.ID, obj.Name, "Credential created by API.")

        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())

    def delete_credential(self, args):
        """Removes a Shared Credential.

Required Arguments:
 
* `credential` - Name or ID of the Credential to delete.
    
Returns: Success message if successful, error message on failure.
"""
        # this is a developer function
        if not api._DEVELOPER:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Developers or Administrators can perform this function.")
        
        required_params = ["credential"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = asset.Credential()
        obj.FromName(args["credential"])
        obj.DBDelete()

        catocommon.write_delete_log(api._USER_ID, catocommon.CatoObjectTypes.Credential, obj.ID, obj.Name, "Credential [%s] deleted via API." % obj.Name)

        return R(response="Delete operation successful.")

    def list_credentials(self, args):        
        """Lists all Shared Credentials.

Optional Arguments:
 
* `filter` - will filter a value match in Credential Name, Username, Domain or Description.  (Multiple filter arguments can be provided, delimited by spaces.)

Returns: A list of [Credential Objects](restapi/api-response-objects.html#Credential){:target="_blank"}.
"""
        fltr = args.get("filter", "")

        obj = asset.Credentials(sFilter=fltr)
        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())


    def get_system_log(self, args):
        """Gets the Cato system log.  If all arguments are omitted, will return the most recent 100 entries.
        
Optional Arguments:

* `object_id` - An object_id filter to limit the results.
* `object_type` - An object_type filter to limit the results.
* `log_type` - A log_type filter. ('Security' or 'Object')
* `action` - An action filter.
* `filter` - A filter to limit the results.
* `from` - a date string to set as the "from" marker. (mm/dd/yyyy format)
* `to` - a date string to set as the "to" marker. (mm/dd/yyyy format)
* `records` - a maximum number of results to get.

Returns: A list of [Log Entry Objects](restapi/api-response-objects.html#LogEntry){:target="_blank"}.
"""
        # this is a admin function, kick out 
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")

        out = []        
        rows = catocommon.get_security_log(oid=args.get("object_id"), otype=args.get("object_type"),
                                           user=args.get("user"), logtype=args.get("log_type"),
                                           action=args.get("action"), search=args.get("filter"),
                                           num_records=args.get("num_records"), _from=args.get("from"), _to=args.get("to"))
        if rows:
            logrow = {}
            for row in rows:
                logrow["LogDate"] = row["log_dt"]
                logrow["Action"] = row["action"]
                logrow["LogType"] = row["log_type"]
                logrow["ObjectType"] = row["object_type"]
                logrow["User"] = row["full_name"]
                logrow["ObjectID"] = row["object_id"]
                logrow["Log"] = row["log_msg"]
                out.append(logrow)

        if out:
            if args.get("output_format") == "json":
                return R(response=catocommon.ObjectOutput.IterableAsJSON(out))
            elif args.get("output_format") == "text":
                return R(response=catocommon.ObjectOutput.IterableAsText(out, ["User", "Action", "LogDate", "Log"], args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=catocommon.ObjectOutput.IterableAsXML(out, "log", "item"))
        else:
            return R(err_code=R.Codes.GetError, err_detail="Error retrieving Log.")
            

    """
    Tagging endpoints.  Only an Administrator can manage Tags.
    """
    def list_tags(self, args):        
        """Lists all Tags.

Optional Arguments: 

* `filter` - will filter a value match in Tag Name.  (Multiple filter arguments can be provided, delimited by spaces.)

Returns: A list of [Tag Objects](restapi/api-response-objects.html#Tag){:target="_blank"}.
"""
        fltr = args.get("filter", "")

        obj = tag.Tags(sFilter=fltr)
        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())


    def create_tag(self, args):
        """Creates a new security Tag.

Required Arguments:

* `name` - The name of the new Tag.  (AlphaNumeric ONLY. Cannot contain spaces, punctuation or special characters.)

Optional Arguments:

* `description` - Describe the Tag.
    
Returns: The new [Tag Object](restapi/api-response-objects.html#Tag){:target="_blank"} if successful, error message on failure.
    """
        # this is a admin function, kick out 
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")
    
        # define the required parameters for this call
        required_params = ["name"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp
    
        obj = tag.Tag(args["name"], args.get("description"))
        obj.DBCreateNew()
        catocommon.write_add_log(api._USER_ID, catocommon.CatoObjectTypes.Tag, obj.Name, obj.Name, "Tag created by API.")
    
        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())

    def delete_tag(self, args):
        """Deletes a security Tag.

Required Arguments:

* `name` - The name of the Tag.
    
Returns: Success message if successful, error message on failure.
"""
        # this is a admin function, kick out 
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")
    
        # define the required parameters for this call
        required_params = ["name"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp
    
        obj = tag.Tag(args["name"], None)
        obj.DBDelete()

        catocommon.write_delete_log(api._USER_ID, catocommon.CatoObjectTypes.Tag, obj.Name, obj.Name, "Tag [%s] deleted via API." % obj.Name)

        return R(response="Delete operation successful.")


    def add_object_tag(self, args):
        """Adds a security Tag to an object.

Required Arguments:

* `tag` - The name of the Tag.
* `object_id` - The ID of the object.
* `object_type` - The numeric type of the object.

Returns: Success message successful, error message on failure.

Valid and currently implemented `object_type` values are:

* `User` = 1
* `Asset` = 2
* `Task` = 3
* `Canvas Item` = 50
* `Deployment` = 70
* `Application Template` = 71
"""
        # this is a admin function
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")
    
        # define the required parameters for this call
        required_params = ["tag", "object_id", "object_type"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        tag.ObjectTags.Add(args["tag"], args["object_id"], args["object_type"])

        catocommon.write_add_log(api._USER_ID, args["object_type"], args["object_id"], args["object_id"], "Tag [%s] added to object via API." % args["tag"])

        return R(response="Tag successfully added to object.")


    def remove_object_tag(self, args):
        """Removes a security Tag from an object.

Required Arguments:

* `tag` - The name of the Tag.
* `object_id` - The ID of the object.
* `object_type` - The numeric type of the object.
    
Returns: Success message if successful, error message on failure.
"""
        # this is a admin function
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")
    
        # define the required parameters for this call
        required_params = ["tag", "object_id", "object_type"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        tag.ObjectTags.Remove(args["tag"], args["object_id"])

        catocommon.write_delete_log(api._USER_ID, args["object_type"], args["object_id"], args["object_id"], "Tag [%s] removed from object via API." % args["tag"])

        return R(response="Tag successfully removed from object.")


    """
    Email and Messaging functions.
    """
    def send_message(self, args):        
        """Sends a message to a registered user.  Message will be 'From' the authenticated API user.

The 'to' argument accepts both email addresses AND Cloud Sidekick Users.  Each item in the 'to' list
will try to look up a Cloud Sidekick User, and if it doesn't match, will assume the entry is an email address.

Required Arguments:

* `to - a single or comma-separated list of valid email addresses or Cloud Sidekick Users.
* `subject - a subject line
* `message - the message body

Optional Arguments: 

* `cc - a carbon copy list of comma-separated email addresses or Cloud Sidekick Users.
* `bcc - a blind carbon copy list of comma-separated email addresses or Cloud Sidekick Users.

Returns: Success message if successful, error message on failure.
"""
        
        required_params = ["to", "subject", "message"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        cc = args.get("cc")
        bcc = args.get("cc")
        
        # NOTE: we're gonna spin through the to, cc and bcc lists and separate
        # the CSK users from plain email addresses.
        
        # since we'll have two sets, we'll actually make two calls to the messenger
        # one will be users and the other emails.
        
        def _reconcile_recip(recip):
            # will check the recip, and return the email address
            try:
                u = catouser.User()
                u.FromFullName(recip.strip())
                if u.Email:
                    return u.Email
                else:
                    logger.info("'send_message' found a User [%s] with no email address defined.  Skipping..." % (u.FullName))
                    return None
            except Exception:
                # didn't find a user or something went wrong, just use this as the address
                return recip

        torecips = []
        ccrecips = []
        bccrecips = []
        
        for to in args.get("to", "").split(","):
            x = _reconcile_recip(to)
            if x:
                torecips.append(x)
        for cc in args.get("cc", "").split(","):
            x = _reconcile_recip(cc)
            if x:
                ccrecips.append(x)
        for bcc in args.get("bcc", "").split(","):
            x = _reconcile_recip(bcc)
            if x:
                bccrecips.append(x)
            
        # fire and forget
        catocommon.send_email_via_messenger(",".join(torecips), args["subject"], args["message"], cc=",".join(ccrecips), bcc=",".join(bccrecips))
        
        return R(response="Message successfully queued.")

    """
    Asset endpoints.
    """
    def list_assets(self, args):        
        """Lists all Assets.

Optional Arguments: 

* `filter` - will filter a value match on: (Multiple filter arguments can be provided, delimited by spaces.)

    * Asset Name
    * Port
    * Address
    * DB Name
    * Status
    * Credential Username

Returns: A list of [Asset Objects](restapi/api-response-objects.html#Asset){:target="_blank"}.
"""
        fltr = args.get("filter", "")

        obj = asset.Assets(sFilter=fltr)
        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())

    def get_asset(self, args):
        """Gets an Asset.

Required Arguments: 

* `asset` - an Asset Name or ID.

Returns: An [Asset Object](restapi/api-response-objects.html#Asset){:target="_blank"}.
"""
        required_params = ["asset"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = asset.Asset()
        obj.FromName(args.get("asset"))

        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())

    def create_asset(self, args):
        """Creates an Asset.

Required Arguments: 

* name - a name for the new Asset.
    
Optional Arguments: 

* `status` - either 'Active' or 'Inactive'. ('Active' if omitted.)
* `db_name` - a Database name.
* `address` - the network address of the Asset.
* `port` - a service port for the Address.
* `conn_string` - some Assets make their connections via an explicit connection string.
* `user` - a User ID to associate with this Asset.
* `password` - a Password to associate with this Asset.
* `shared_credential` - the name of a Shared Credential to use.

**Regarding Credentials:**

Credentials are optional on an Asset, however if provided there are rules.
Explicit details can be associated with *only this Asset*, or a Shared Credential can be specified.

The minimum required to create a LOCAL set of credentials on this Asset are:

* `user` - a User ID for the Credential
* `password` - a Password for the Credential
    
To specify a Shared Credential, provide the `shared_credential` argument, which is the name of an existing Credential.

Returns: An [Asset Object](restapi/api-response-objects.html#Asset){:target="_blank"}.
"""
        # this is a developer function
        if not api._DEVELOPER:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Developers or Administrators can perform this function.")
        
        required_params = ["name"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        # build a dictionary suitable for creating an asset
        _a = {
            "Name": args.get("name"),
            "Status": args.get("status"),
            "DBName": args.get("db_name"),
            "Port": args.get("port"),
            "Address": args.get("address"),
            "ConnString": args.get("conn_string"),
            "Credential": {
                "SharedOrLocal": 0 if args.get("shared_credential") else 1,
                "Username": args.get("user"),
                "Password": args.get("password"),
                "Name": args.get("shared_credential")
           }
        }

        obj, err = asset.Asset.DBCreateNew(_a)
        if err:
            return R(err_code=R.Codes.CreateError, err_detail=err)

        catocommon.write_add_log(api._USER_ID, catocommon.CatoObjectTypes.Asset, obj.ID, obj.Name, "Asset created via API.")

        if args.get("output_format") == "json":
            return R(response=obj.AsJSON())
        elif args.get("output_format") == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())

    def delete_asset(self, args):
        """Deletes an Asset.

Required Arguments:

* asset - Either the Asset ID or Name.

Returns: Nothing if successful, error messages on failure.
"""
        # this is a admin function
        if not api._ADMIN:
            return R(err_code=R.Codes.Forbidden, err_msg="Only Administrators can perform this function.")
        
        required_params = ["asset"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = asset.Asset()
        obj.FromName(args["asset"])

        if not api.is_object_allowed(obj.ID, catocommon.CatoObjectTypes.Asset):
            return R(err_code=R.Codes.Forbidden, err_msg="You do not have access to the details of this Asset.")
            
        asset.Assets.Delete(["'%s'" % obj.ID])
        
        catocommon.write_delete_log(api._USER_ID, catocommon.CatoObjectTypes.Asset, obj.ID, obj.Name, "Deleted via API.")
        return R(response="[%s] successfully deleted." % obj.Name)
