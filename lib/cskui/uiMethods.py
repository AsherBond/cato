
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
if "CSK_HOME" not in os.environ:
    raise Exception("CSK_HOME environment variable not set.")
sys.path.insert(0, os.path.join(os.environ["CSK_HOME"], "cato", "lib"))

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
sys.path.insert(0, os.path.join(base_path, "plugins"))


import json
from datetime import datetime
import web

from catolog import catolog
logger = catolog.get_logger(__name__)

from catoconfig import catoconfig
from catocommon import catocommon
from catoui import uiCommon

from catouser import catouser
from catosettings import settings


class uiMethods:
    """
    The web method calls for the base Velocity UI.
    """
    db = None

    def wmLicenseAgree(self):
        # this accepts BOTH the Cato and the Maestro licenses.
        dt = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        settings.settings.set_application_detail("general", "license_status", "agreed")
        settings.settings.set_application_detail("general", "license_datetime", dt)
        settings.settings.set_application_detail("general", "legato_license_status", "agreed")
        settings.settings.set_application_detail("general", "legato_license_datetime", dt)
        return ""

    def wmGetQuestion(self):
        return uiCommon.GetQuestion()

    def wmGetConfig(self):
        # we are adding some Maestro specific stuff to the general config
        cfg = catoconfig.SAFECONFIG

        cfg["csk_ui_url"] = catoconfig.get_url("csk_ui", web.ctx.host.split(":")[0])
        cfg["admin_ui_url"] = catoconfig.get_url("admin_ui", web.ctx.host.split(":")[0])
        cfg["cd_ui_url"] = catoconfig.get_url("cd_ui", web.ctx.host.split(":")[0])
        cfg["user_ui_url"] = catoconfig.get_url("user_ui", web.ctx.host.split(":")[0])
        cfg["dash_api_url"] = catoconfig.get_url("dash_api", web.ctx.host.split(":")[0])
        cfg["msghub_url"] = catoconfig.get_url("msghub", web.ctx.host.split(":")[0])

        return catocommon.ObjectOutput.AsJSON(cfg)

    def wmGetSettings(self):
        # these are user-definable maestro settings
        sset = settings.settings.maestro()
        return sset.AsJSON()

    def wmUpdateHeartbeat(self):
        uiCommon.UpdateHeartbeat()
        return ""

    def wmWriteClientLog(self):
        msg = uiCommon.getAjaxArg("msg")
        debug = uiCommon.getAjaxArg("debug")
        uiCommon.WriteClientLog(msg, debug)
        return ""


    def wmGetMyAccount(self):
        user_id = uiCommon.GetSessionUserID()

        sSQL = """select full_name, username, authentication_type, email,
            ifnull(security_question, '') as security_question,
            ifnull(security_answer, '') as security_answer
            from users
            where user_id = '%s'""" % user_id
        dr = self.db.select_row_dict(sSQL)
        # here's the deal - we aren't even returning the 'local' settings if the type is ldap.
        if dr["authentication_type"] == "local":
            return json.dumps(dr)
        else:
            d = {"full_name": dr["full_name"], "username": dr["username"], "email": dr["email"], "type": dr["authentication_type"]}
            return json.dumps(d)

    def wmSaveMyAccount(self):
        """
            In this method, the values come from the browser in a jQuery serialized array of name/value pairs.
        """
        user_id = uiCommon.GetSessionUserID()
        args = uiCommon.getAjaxArg("values")

        u = catouser.User()
        u.FromID(user_id)

        if u.ID:
            # if a password was provided...
            # these changes are done BEFORE we manipulate the user properties for update.
            new_pw = uiCommon.unpackJSON(args.get("my_password"))
            if new_pw:
                u.ChangePassword(new_password=new_pw)
                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.User, u.ID, u.FullName, "Password changed.")

            # now the other values...
            u.Email = args.get("my_email")
            u.SecurityQuestion = args.get("my_question")
            u.SecurityAnswer = uiCommon.unpackJSON(args.get("my_answer"))

            if u.DBUpdate():
                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.User, u.ID, u.ID, "User updated.")

        return json.dumps({"result": "success"})
