
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

class sysMethods:
    """These are utility methods for the Cato system."""

    # ## NOTE:
    # ## many of the functions here aren't done up in pretty classes.
    # ## ... this is sort of a catch-all module.
    def import_backup(self, args):
        """
        Imports an XML backup file.
        
        NOTE: this function is a near identical copy of catoadminui/uiMethods.wmCreateObjectsFromXML.
        Any changes here should be considered there as well.
        """
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
            return R(response=catocommon.ObjectOutput.IterableAsText(items, ["Name", "Info"], args["output_delimiter"]))
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

        Returns: Nothing if successful, error messages on failure.
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
            forcechange - Require user to change password. Default is 'true' if omitted. (Valid values: 'true' or 'false'
            status - Status of the new account. Default is 'enabled' if omitted. (Valid values: enabled, disabled, locked)
            groups - A list of groups the user belongs to. Group names cannot contain spaces. Comma delimited list.

        Returns: Nothing if successful, error messages on failure.
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

        status = 1
        if args.get("status"):
            status = 0 if args.get("status").lower() == "disabled" else (-1 if args.get("status").lower() == "locked" else 1)

        groups = args.get("groups").split(",") if args.get("groups") else None

        obj = catouser.User.DBCreateNew(username=args["user"],
                                        fullname=args["name"],
                                        role=args["role"],
                                        password=args.get("password"),
                                        generatepw=generate,
                                        authtype=args.get("authtype"),
                                        forcechange=args.get("forcechange"),
                                        email=args.get("email"),
                                        status=status, groups=groups)

        if obj:
            catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.User, obj.ID, obj.LoginID, "User created.")
            if args["output_format"] == "json":
                return R(response=obj.AsJSON())
            elif args["output_format"] == "text":
                return R(response=obj.AsText(args["output_delimiter"]))
            else:
                return R(response=obj.AsXML())
        else:
            return R(err_code=R.Codes.CreateError, err_detail="Unable to create User.")
            

