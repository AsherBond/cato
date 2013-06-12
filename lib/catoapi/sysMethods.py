
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

import traceback
import json
from datetime import datetime

try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

from catoapi import api
from catoapi.api import response as R
from catocommon import catocommon
from catotask import task
from catouser import catouser
from catosettings import settings
from catoasset import asset

class sysMethods:
    """These are utility methods for the Cato system."""

    # ## NOTE:
    # ## many of the functions here aren't done up in pretty classes.
    # ## ... this is sort of a catch-all module.
    def get_token(self, args):
        """
        Gets an authentication token for the API.  This token will persist for a short period of time, 
        so several subsequent API calls can share the same authenticated session.
        
        Returns: A UUID authentication token.
        """
        
        # we wouldn't be here if tradiditional authentication failed.
        # so, the _user_id is the user we wanna create a token for
        
        token = catocommon.new_guid()
        now_ts = datetime.utcnow()
        
        sql = """insert into api_tokens 
            (user_id, token, created_dt)
            values ('{0}', '{1}', str_to_date('{2}', '%%Y-%%m-%%d %%H:%%i:%%s'))
            on duplicate key update token='{1}', created_dt=str_to_date('{2}', '%%Y-%%m-%%d %%H:%%i:%%s')
            """.format(args["_user_id"], token, now_ts)

        db = catocommon.new_conn()
        db.exec_db(sql)
        db.close()
        
        return R(response=token)

    def import_backup(self, args):
        """
        Imports an XML backup file.
        
        Required Arguments: 
            xml - An XML document in the format of a Cato backup file.
        
        Returns: A list of items in the backup file, with the success/failure of each import.
        """

        # NOTE: this function is a near identical copy of catoadminui/uiMethods.wmCreateObjectsFromXML.
        # Any changes here should be considered there as well.

        # define the required parameters for this call
        required_params = ["xml"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp


        # what types of things were in this backup?  what are their new ids?
        items = []

        # parse it as a validation, and to find out what's in it.
        xd = None
        try:
            xd = ET.fromstring(args["xml"])
        except ET.ParseError as ex:
            return R(err_code=R.Codes.Exception, err_detail="File is not properly formatted XML.")
        
        if xd is not None:
            for xtask in xd.iterfind("task"):
                logger.info("Importing Task [%s]" % xtask.get("name", "Unknown"))
                t = task.Task()
                t.FromXML(ET.tostring(xtask))

                result, err = t.DBSave()
                if result:
                    catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.Task, t.ID, t.Name, "Created by import.")

                    items.append({"type" : "task", "id" : t.ID, "Name" : t.Name, "Info" : "Success"}) 
                else:
                    if err:
                        items.append({"type" : "task", "id" : t.ID, "Name" : t.Name, "Info" : err}) 
                    else:
                        items.append({"type" : "task", "id" : t.ID, "Name" : t.Name, "Info" : "Unable to create Task. No error available."}) 
                

        else:
            items.append({"info" : "Unable to create Task from backup XML."})
        
        if args["output_format"] == "json":
            return R(response=catocommon.ObjectOutput.IterableAsJSON(items))
        elif args["output_format"] == "text":
            return R(response=catocommon.ObjectOutput.IterableAsText(items, ["Name", "Info"], args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=catocommon.ObjectOutput.IterableAsXML(items, "Results", "Result"))
    
    def list_processes(self, args):        
        """
        Lists all Cato Processes.
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
            if args["output_format"] == "json":
                resp = catocommon.ObjectOutput.IterableAsJSON(rows)
                return R(response=resp)
            elif args["output_format"] == "text":
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
                dom = ET.fromstring('<Processes />')
                if rows:
                    for row in rows:
                        xml = catocommon.dict2xml(row, "Process")
                        node = ET.fromstring(xml.tostring())
                        dom.append(node)
                
                return R(response=ET.tostring(dom))
        else:
            return R(err_code=R.Codes.ListError, err_detail="Unable to list Processes.")
        
    def reset_password(self, args):
        """
        Resets the password of the authenticated, or a specified User.

        If a user is specified, and the authenticated user is an Administrator, 
        this will reset the password of the specified user to the provided value.
        
        If no user is specified, the password of the authenticated user will be changed.

        NOTE: to prevent accidental change of an Administrators password, an extra trap is in place:
            * the username (or id) MUST be provided, even if the authenticated user 
                is the user being changed.

        Required Arguments: 
            password - the new password.
        
        Optional Arguments:
            user - Either the User ID or Name.

        Returns: Success message if successful, error messages on failure.
        """
        user = args.get("user")
        new_pw = args.get("password")

        # this is a admin function, kick out 
        if user and not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)

        # the only way to reset an "Administrator" role password
        # is to BE an Administrator and SPECIFY a user, even if the user is you
        if not user and args["_admin"]:
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
                if obj.ID == args["_user_id"]:
                    force = False
                    
                obj.ChangePassword(new_password=new_pw, force_change=force)
            elif generate:
                obj.ChangePassword(generate=generate)
        else:
            return R(err_code=R.Codes.GetError, err_detail="Unable to update password.")

        
        catocommon.write_change_log(args["_user_id"], catocommon.CatoObjectTypes.User, obj.ID, obj.FullName, "Password change/reset via API.")
        return R(response="[%s] password operation successful." % obj.FullName)
            
    def create_user(self, args):
        """
        Creates a new user account.

        Only an 'Administrator' can create other users.  If the credentials used for this API call 
        are not an Administrator, the call will not succeed.

        Required Arguments: 
            user - A login name for the user.
            name - The full name of the user.
            role - The users role.  (Valid values: Administrator, Developer, User)
        
        Optional Arguments:
            password - Password for the user. If password is not provided, a random password will be generated.
            email - Email address for the user.  Required if 'password' is omitted.
            authtype - 'local' or 'ldap'.  Default is 'local' if omitted.
            forcechange - Require user to change password. Default is 'true' if omitted. (Valid values: 'true' or 'false')
            status - Status of the new account. Default is 'enabled' if omitted. (Valid values: enabled, disabled, locked)
            expires - Expiration date for this account.  Default is 'never expires'. Must be in mm/dd/yyyy format.
            groups - A list of groups the user belongs to. Group names cannot contain spaces. Comma delimited list.

        Returns: A User object.
        """

        # this is a admin function, kick out 
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)

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

        if obj:
            catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.User, obj.ID, obj.LoginID, "User created by API.")
            if args["output_format"] == "json":
                return R(response=obj.AsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=obj.AsXML())
        else:
            return R(err_code=R.Codes.CreateError, err_detail="Unable to create User.")
            
    def update_user(self, args):
        """
        Updates a user account.

        Only an 'Administrator' can manage other users.  If the credentials used for this API call 
        are not an Administrator, the call will not succeed.

        Properties will only be updated if the option is provided.  Omitted properties will not be changed.
        
        NOTE: the "username" of a user cannot be changed.
        
        Password cannot be updated by this method.  Use "reset_password" instead.
        
        If a user has 'locked' their account by numerous failed login attempts, the flag is reset 
        by setting any property.  It's easiest to just the status to 'enabled'.

        
        Required Arguments: 
            user - ID or Name of the User to update.
        
        Optional Arguments:
            name - The full name of the user.
            role - The users role.  (Valid values: Administrator, Developer, User)
            email - Email address for the user.  Can be cleared with "None".
            authtype - 'local' or 'ldap'.
            forcechange - Require user to change password on next login. (Valid values: 'true' or 'false')
            status - Status of the account. (Valid values: enabled, disabled, locked)
            expires - Expiration date for this account.  Must be in mm/dd/yyyy format. Can be cleared with "None".
            groups - Add to the list of groups the user belongs to. Group names cannot contain spaces. Comma delimited list.

        Returns: A User object.
        """

        # this is a admin function, kick out 
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)

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
            obj.ForceChange = args.get("forcechange", obj.ForceChange)
        
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
            catocommon.write_change_log(args["_user_id"], catocommon.CatoObjectTypes.User, obj.ID, obj.FullName, "User updated via API.")

        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())
            
    def list_users(self, args):        
        """
        Lists all registered Users.
        
        Optional Arguments: 
            filter - will filter a value match in User's Full Name, Role or Email address.
        
        Returns: A list of all Users.
        """
        # this is a admin function, kick out 
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)

        fltr = args["filter"] if args.has_key("filter") else ""

        obj = catouser.Users(sFilter=fltr)
        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())

    def update_settings(self, args):
        """
        Updates the settings of a Cato process or module.

        NOTE: the update_settings command requires submission of a JSON settings object.
        As a guide for updating settings, first execute this command with the output_format set to json.
        
        For example, to update Messenger settings, first do:
        
        get_settings?module=messenger&output_format=json
        
        ...then use the result as a template for update_settings.
        
        Required Arguments: 
            module - name of the module to apply the settings.
            settings - a list of name:value setting objects.

        Returns: Nothing if successful, error messages on failure.
        """
        mod = args.get("module")
        sets = args.get("settings")

        # this is a admin function, kick out 
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)

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
            catocommon.add_security_log(args["_user_id"], catocommon.SecurityLogTypes.Security,
                catocommon.SecurityLogActions.ConfigChange, catocommon.CatoObjectTypes.NA, "",
                "%s settings changed via API." % mod.capitalize())
        
            if args["output_format"] == "json":
                return R(response=obj.AsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=obj.AsXML())

    def get_settings(self, args):
        """
        Lists all the settings of Cato modules.

        Optional Arguments: 
            module - name of the module. If omitted, all module settings are returned.

        Returns: A collection of settings.
        """
        # this is a admin function, kick out 
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)

        mod = args.get("module")
        obj = None
        
        # if a module is provided, just get that one, otherwise get them all
        if mod:
            objname = getattr(settings.settings, mod.lower())
            obj = objname()
        else:
            obj = settings.settings()

        if obj:
            if args["output_format"] == "json":
                return R(response=obj.AsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=obj.AsXML())

    def create_credential(self, args):
        """
        Creates a new Shared Credential.

        Only a 'Developer' can create Credentials.

        Required Arguments: 
            name - The full name of the user.
            username - A login name for the user.
            password - Password for the user. If password is not provided, a random password will be generated.
        
        Optional Arguments:
            description - Description of the Credential.
            privileged = Additional password required to put certain devices into 'privileged' mode.
            domain - A domain for the Credential.

        Returns: A Credential object.
        """

        # this is a admin function, kick out 
        if not args["_developer"]:
            return R(err_code=R.Codes.Forbidden)

        # define the required parameters for this call
        required_params = ["name", "username", "password"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp
        # a little different than the others ... credential objects must be instantiated before calling DBCreateNew
        obj = asset.Credential()
        obj.FromArgs(args["name"], args.get("description"), args["username"], args["password"],
                 0, args.get("domain"), args.get("privileged"))
        result = obj.DBCreateNew()
        if not result:
            return R(err_code=R.Codes.CreateError, err_detail="Unable to create Credential.")

        catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.Credential, obj.ID, obj.Name, "Credential created by API.")

        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())

    def delete_credential(self, args):
        """
        Removes a Shared Credential.
        
        Required Arguments: 
            credential - Name or ID of the Credential to delete.
            
        Returns: Success message if successful, error message on failure.
        """
        # this is a developer function
        if not args["_developer"]:
            return R(err_code=R.Codes.Forbidden)
        
        required_params = ["credential"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        obj = asset.Credential()
        obj.FromName(args["credential"])
        obj.DBDelete()

        catocommon.write_delete_log(args["_user_id"], catocommon.CatoObjectTypes.Credential, obj.ID, obj.Name, "Credential [%s] deleted via API." % obj.Name)

        return R(response="Delete operation successful.")

    def list_credentials(self, args):        
        """
        Lists all Shared Credentials.
        
        Optional Arguments: 
            filter - will filter a value match in Credential Name, Username, Domain or Description.
        
        Returns: A list of Shared Credentials.
        """
        fltr = args["filter"] if args.has_key("filter") else ""

        obj = asset.Credentials(sFilter=fltr)
        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args.get("output_delimiter"), args.get("header")))
        else:
            return R(response=obj.AsXML())


    def get_system_log(self, args):
        """
        Gets the Cato system log.  If all arguments are omitted, will return the most recent 100 entries.
        
        Optional Arguments:
            object_id - An object_id filter to limit the results.
            object_type - An object_type filter to limit the results.
            log_type - A log_type filter. ('Security' or 'Object')
            action - An action filter.
            filter - A filter to limit the results.
            from - a date string to set as the "from" marker. (mm/dd/yyyy format)
            to - a date string to set as the "to" marker. (mm/dd/yyyy format)
            records - a maximum number of results to get.

        Returns: An array of log entries.
        """
        # this is a admin function, kick out 
        if not args["_admin"]:
            return R(err_code=R.Codes.Forbidden)

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
            if args["output_format"] == "json":
                return R(response=catocommon.ObjectOutput.IterableAsJSON(out))
            elif args["output_format"] == "text":
                return R(response=catocommon.ObjectOutput.IterableAsText(out, ["User", "Action", "LogDate", "Log"], args.get("output_delimiter"), args.get("header")))
            else:
                return R(response=catocommon.ObjectOutput.IterableAsXML(out, "log", "item"))
        else:
            return R(err_code=R.Codes.GetError, err_detail="Error retrieving Log.")
            

