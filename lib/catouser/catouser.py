
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
    THIS CLASS has it's own database connections.
    Why?  Because it isn't only used by the UI.
"""
import re
from datetime import datetime, timedelta

from catosettings import settings
from catocommon import catocommon
from catoerrors import InfoException
from catoconfig import catoconfig
from catolog import catolog
logger = catolog.get_logger(__name__)

class Users(object): 
    rows = {}
        
    def __init__(self, sFilter=""):
        db = catocommon.new_conn()
        sWhereString = ""
        if sFilter:
            aSearchTerms = sFilter.split()
            for term in aSearchTerms:
                if term:
                    sWhereString += " and (u.full_name like '%%" + term + "%%' " \
                        "or u.user_role like '%%" + term + "%%' " \
                        "or u.username like '%%" + term + "%%' " \
                        "or u.status like '%%" + term + "%%' " \
                        "or u.last_login_dt like '%%" + term + "%%') "

        sSQL = """select u.user_id, u.username, u.full_name, u.last_login_dt, u.email,
            case when u.status = '1' then 'Enabled' when u.status = '-1' then 'Locked'
            when u.status = '0' then 'Disabled' end as status,
            u.authentication_type, u.user_role as role
            from users u
            where u.status <> 86 %s order by u.full_name""" % sWhereString
        
        self.rows = db.select_all_dict(sSQL)
        db.close()

    def SafeList(self):
        out = []
        if self.rows:
            for user in self.rows:
                u = {}
                u["LoginID"] = user["username"]
                u["FullName"] = user["full_name"]
                u["Role"] = user["role"]
                u["Status"] = user["status"]
                u["AuthenticationType"] = user["authentication_type"]
                u["Email"] = user["email"]
                u["LastLoginDT"] = user["last_login_dt"]
                out.append(u)
        return out
    
    def AsJSON(self):
        # results are tightly controlled
        return catocommon.ObjectOutput.IterableAsJSON(self.SafeList())

    def AsXML(self):
        dom = catocommon.ET.fromstring('<Users />')
        for user in self.SafeList():
            xml = catocommon.dict2xml(user, "User")
            node = catocommon.ET.fromstring(xml.tostring())
            dom.append(node)
        return catocommon.ET.tostring(dom)

    def AsText(self, delimiter=None, headers=None):
        return catocommon.ObjectOutput.IterableAsText(self.SafeList(), ['LoginID', 'FullName', 'Role', 'Status', 'AuthenticationType', 'Email'], delimiter, headers)

class User(object):
    def __init__(self):
        self.ID = ""
        self.FullName = ""
        self.Status = ""
        self.LoginID = ""
        self.Role = ""
        self.LastLoginDT = ""
        self.AuthenticationType = ""
        self.ExpirationDT = ""
        self.SecurityQuestion = ""
        self.FailedLoginAttempts = 0
        self.ForceChange = False
        self.Email = ""
        self.Expires = None
        self.SettingsXML = ""
        self.LoginToken = None
        self.Tags = []
        
        # only set in the Authenticate method - contains the session_id that *was just issued*.
        # NOT a part of a regular user object, as there can be multiple sessions - one per ui.
        self.SessionID = None
    
    def GetToken(self):
        if self.ID:
            self.LoginToken = catocommon.create_api_token(self.ID)
            
    @staticmethod
    def ValidatePassword(uid, pwd):
        """
        Checks a password against the system settings for length, complexity, etc.
        """
        s_set = settings.settings.security()

        # is this password long enough?  too long?
        if len(pwd) < s_set.PassMinLength or len(pwd) > s_set.PassMaxLength:
            return False, "Password must be between %d and %d characters in length." % (s_set.PassMinLength, s_set.PassMaxLength)
        
        # is it complex (if required to be)?
        if s_set.PassComplexity:
            if not re.search(r"[A-Z~!@#$%^&?+=]", pwd):
                return False, "Password must contain at least one capital letter and at least one special character. (~!@#$%^&?+=)"
        
        # has it been used lately (if that's required)?
        # in which case we need to save the old one to history, and delete
        # any rows over this counter.
        
        # this test isn't necessary if no user_id was provided
        if uid and s_set.PasswordHistory:
            db = catocommon.new_conn()
            sql = """select password from user_password_history 
            where user_id = '%s'
            order by change_time desc
            limit %d""" % (uid, s_set.PasswordHistory)
            
            previous_pwds = db.select_csv(sql, False)
            if previous_pwds:
                if catocommon.cato_encrypt(pwd) in previous_pwds:
                    return False, "That password cannot yet be reused."
                    
            db.close()        
            
        return True, None

    def FromFullName(self, sUsername):
        # try to get the user by their "full name", then name, if that fails try it by ID
        try:
            self.PopulateUser(fullname=sUsername)
        except:
            try:
                self.PopulateUser(login_id=sUsername)
            except:
                self.PopulateUser(user_id=sUsername)
        
    def FromName(self, sUsername):
        # try to get the user by name, if that fails try it by ID
        try:
            self.PopulateUser(login_id=sUsername)
        except:
            self.PopulateUser(user_id=sUsername)
        
    def FromID(self, sUserID):
        self.PopulateUser(user_id=sUserID)

    def PopulateUser(self, user_id="", login_id="", fullname=""):
        """
            Note the absence of password or security_answer in this method.  There are specialized 
            methods for testing passwords, etc.
        """
        if not user_id and not login_id and not fullname:
            raise Exception("Error building User object: User ID, Login or Name is required.")
        
        db = catocommon.new_conn()

        sSQL = """select u.user_id, u.username, u.full_name, u.status, u.last_login_dt,
            u.failed_login_attempts, u.email ,u.authentication_type,
            u.security_question, u.force_change, u.settings_xml,
            u.user_role, date_format(u.expiration_dt, '%%m/%%d/%%Y') as expiration_dt
            from users u"""
        
        if user_id:
            sSQL += " where u.user_id = '%s'""" % user_id
        elif login_id:
            sSQL += " where u.username = '%s'""" % login_id
        elif fullname:
            sSQL += " where u.full_name = '%s'""" % fullname

        dr = db.select_row_dict(sSQL)
        
        if dr is not None:
            self.ID = dr["user_id"]
            self.FullName = dr["full_name"]
            self.LoginID = dr["username"]
            self.Status = dr["status"]
            self.Role = dr["user_role"]
            self.AuthenticationType = dr["authentication_type"]
            self.LastLoginDT = ("" if not dr["last_login_dt"] else str(dr["last_login_dt"]))
            self.ExpirationDT = ("" if not dr["expiration_dt"] else str(dr["expiration_dt"]))
            self.SecurityQuestion = ("" if not dr["security_question"] else dr["security_question"])
            self.FailedLoginAttempts = (0 if not dr["failed_login_attempts"] else dr["failed_login_attempts"])
            self.ForceChange = (True if dr["force_change"] == 1 else False)
            self.Email = ("" if not dr["email"] else dr["email"]).strip()
            self.SettingsXML = ("" if not dr["settings_xml"] else dr["settings_xml"])

            # what are the users tags?
            sql = "select tag_name from object_tags where object_type = 1 and object_id='%s'" % (self.ID)
            # NOTE this is "select_all", not "select_all_dict"... because I DO want a list.
            rows = db.select_all(sql)
            db.close()
            
            tags = []
            if rows:
                for tag in rows:
                    tags.append(tag[0])
                self.Tags = tags
        else: 
            raise Exception("Unable to build User object. User with ID/Login/Name [%s%s%s] could be found." % (user_id, login_id, fullname))

    def AsJSON(self):
        if hasattr(self, "_Groups"):
            del self._Groups
        return catocommon.ObjectOutput.AsJSON(self.__dict__)

    def AsText(self, delimiter=None, headers=None):
        return catocommon.ObjectOutput.AsText(self.__dict__, ["FullName", "Status", "AuthenticationType", "Role", "Email"], delimiter, headers)

    def AsXML(self):
        return catocommon.ObjectOutput.AsXML(self.__dict__, "User")

    def ChangePassword(self, new_password=None, generate=False, force_change=True):
        """
        Updating a user password is a different function with extra rules, 
            so it's kept separate from the DBUpdate function.
            
        You cannot explicitly change a password, AND do the Generate function,
            so if a password is set it'll use it and continue, otherwise it'll generate.
        """
        if not new_password and not self.Email:
            raise InfoException("Unable to generate a random password - User [%s] does not have an email address defined." % (self.FullName))
        
        if not new_password and not generate:
            raise InfoException("Unable to reset password - New password is required or random generation option must be specified.")
            return False

        # TODO: maybe have a setting for the application url in the email?
        # TODO: should have the ability to use a configurable "company" name in the email
        
        
        db = catocommon.new_conn()

        # only do the password if _NewPassword exists on the object.
        # NOTE: no function that inits a user will set a password property, so it must've been set explicitly
        if new_password:
            logger.info("Updating password for User [%s]" % (self.FullName))
            result, msg = User.ValidatePassword(self.ID, new_password)
            if result:
                sql = "update users set user_password = %s where user_id = %s"
                db.exec_db(sql, (catocommon.cato_encrypt(new_password), self.ID))
                
                # this flag can be reset from the calling function at it's discretion.  
                # for example, if the user making the request IS the user being changed,
                #     which we don't know at this point.
                
                if not force_change:
                    sql = "update users set force_change = 0 where user_id = %s"
                    db.exec_db(sql, (self.ID))
                    
                body = """%s - your password has been reset by an Administrator.""" % (self.FullName)
                if self.Email:
                    catocommon.send_email_via_messenger(self.Email, "Cato - Account Information", body)
                else:
                    logger.warning("Attempt to send a password message failed - User [%s] has no email defined." % (self.FullName))
            else:
                raise InfoException(msg)

        # Here's something special...
        # If the arg "_NewRandomPassword" was provided and is true...
        # Generate a new password and send out an email.
        
        # IF for some reason this AND a password were provided, it means someone is hacking
        # (We don't do both of them at the same time.)
        # so the provided one takes precedence.
        if generate:
            logger.info("Generating a new password for User [%s]" % (self.FullName))
            sNewPassword = catocommon.generate_password()
            
            sql = "update users set force_change = 1, user_password = %s where user_id = %s"
            db.exec_db(sql, (catocommon.cato_encrypt(sNewPassword), self.ID))
              
            s_set = settings.settings.security()
            body = s_set.NewUserMessage
            if not body:
                body = """%s - your password has been reset by an Administrator.\n\n
                Your temporary password is: %s.""" % (self.FullName, sNewPassword)

            # replace our special tokens with the values
            body = body.replace("##FULLNAME##", self.FullName).replace("##USERNAME##", self.LoginID).replace("##PASSWORD##", sNewPassword)

            if self.Email:
                catocommon.send_email_via_messenger(self.Email, "Cato - Account Information", body)
            else:
                logger.warning("Attempt to send a password message failed - User [%s] has no email defined." % (self.FullName))
            # f !uiCommon.SendEmailMessage(sEmail.strip(), ag.APP_COMPANYNAME + " Account Management", "Account Action in " + ag.APP_NAME, sBody, 0000BYREF_ARG0000sErr:

        db.close()
        return True
        
    def DBUpdate(self):
        db = catocommon.new_conn()

        sql_bits = []
        if self.LoginID:
            sql_bits.append("username='%s'" % (self.LoginID))
        if self.FullName:
            sql_bits.append("full_name='%s'" % (self.FullName))
        if self.AuthenticationType:
            sql_bits.append("authentication_type='%s'" % (self.AuthenticationType))
        if self.Email:
            sql_bits.append("email='%s'" % (self.Email))
        if self.Role:
            sql_bits.append("user_role='%s'" % (self.Role))

        # these can have a value of 0 which is valid, so they need a different test
        if self.Status is not None:
            if self.Status in ("enabled", "disabled", "locked"):
                self.Status = 0 if self.Status.lower() == "disabled" else (-1 if self.Status.lower() == "locked" else 1)

            if self.Status in (-1, 0, 1, "-1", "0", "1"):
                sql_bits.append("status='%s'" % (self.Status))
            else:
                logger.warning("User.DBUpdate : Status must be 'enabled' (1), 'disabled' (0) or 'locked' (-1).")

        # force change must be 0 or 1
        if self.ForceChange is not None:
            fc = 0
            try:
                fc = int(self.ForceChange)
                sql_bits.append("force_change='%s'" % (fc))
            except:
                logger.warning("User.DBUpdate : ForceChange property must be 0 or 1.")
                pass

        # failed login attempts resets on save to 0, UNLESS an explicit value was given
        # (does anything even do this???)
        f = 0
        try:
            if self.FailedLoginAttempts:
                f = int(self.FailedLoginAttempts)
        except:
            logger.warning("User.DBUpdate : FailedLoginAttempts property must be an integer.  Setting to 0.")
            f = 0
        sql_bits.append("failed_login_attempts='%s'" % (f))
        
        # expires can be set to null, so if there's no value make it null. 
        if self.Expires:
            import dateutil.parser as parser
            try:
                tmp = parser.parse(self.Expires)
                self.Expires = tmp.strftime("%m/%d/%Y")
                sql_bits.append("expiration_dt=str_to_date('{0}', '%%m/%%d/%%Y')".format(self.Expires))
            except Exception:
                # it might have been a reset directive in a string format
                if self.Expires.lower() == "none":
                    sql_bits.append("expiration_dt=null")
        else:
            sql_bits.append("expiration_dt=null")
            
        # if there are no properties to update, don't update
        if sql_bits:
            sql = "update users set %s where user_id = '%s'" % (",".join(sql_bits), self.ID)
            db.exec_db(sql)

        if getattr(self, "_Groups", None):
            # WE ARE REQUIRING the caller to take care of reconciling the groups.
            # if the _Groups argument is empty, that means delete them all!
            # no matter what the case, we're doing a whack-n-add here.
            sql = "delete from object_tags where object_id = '%s'" % (self.ID)
            db.exec_db(sql)

            # now, lets do any groups that were passed in. 
            for tag in self._Groups:
                sql = "insert object_tags (object_type, object_id, tag_name) values (1, '%s','%s')" % (self.ID, tag)
                db.exec_db(sql)
                    
        db.close()
        return True
                    
    """ These next few _ functions are shared across the Authenticate methods """
    def _create_user_session(self):
        db = catocommon.new_conn()

        sql = "update users set failed_login_attempts=0, last_login_dt=now() where user_id=%s"
        db.exec_db(sql, (self.ID))
    
        sid = catocommon.unix_now_millis()
        self.SessionID = str(sid)
        sql = """insert into user_session (session_id, user_id, address, login_dt, heartbeat, kick)
            values ('{0}', '{1}', '{2}', now(), now(), 0)
            on duplicate key update session_id = '{0}', user_id = '{1}', address ='{2}'""".format(sid, self.ID, self.ClientIP)
        db.exec_db(sql)

                          
    def AuthenticateSession(self, sid, client_ip):
        """
        Will authenticate from the session_id of another authenticated CSK application.
        """
        self.ClientIP = client_ip

        db = catocommon.new_conn()
        sql = "select user_id from user_session where session_id = %s"
        uid = db.select_col(sql, (sid))
        db.close()
        if not uid:
            msg = "Attempting to trust remote app session failed.  Provided Session ID is not valid."
            logger.warning(msg)
            return False, msg

        self.PopulateUser(user_id=uid)
    
        # Check for "locked" or "disabled" status
        if self.Status < 1:
            return False, "disabled"

        self._create_user_session()
        return True, ""
        
    def AuthenticateToken(self, token, client_ip):
        """
        The rules for authenticating from a token are different than uid/pwd.
        """
        self.ClientIP = client_ip
        
        # tokens are only allowed if the configuration file says so.
        if catocommon.is_true(catoconfig.CONFIG.get("ui_enable_tokenauth")):
            db = catocommon.new_conn()
            
            # check the token here - looking it up will return a user_id if it's still valid
            sql = "select user_id, created_dt from api_tokens where token = %s" 
            row = db.select_row_dict(sql, (token))
            
            if not row:
                return False, "invalid token"
            if not row["created_dt"] or not row["user_id"]:
                return False, "invalid token"
            
            # check the expiration date of the token
            now_ts = datetime.utcnow()
            
            mins = 30
            try:
                mins = int(catoconfig.CONFIG.get("ui_token_lifespan"))
            except:
                logger.warning("Config setting [ui_token_lifespan] not found or is not a number.  Using the default (30 minutes).")
            
            if (now_ts - row["created_dt"]) > timedelta (minutes=mins):
                logger.warning("The provided login token has expired. Tokens are good for %s minutes." % (mins))
                return False, "expired"
            
            # at the moment, UI tokens can't be kept current.  Once they expire they're gone.
#             # still all good?  Update the created_dt.
#             sql = """update api_tokens set created_dt = str_to_date('{0}', '%%Y-%%m-%%d %%H:%%i:%%s')
#                 where user_id = '{1}'""".format(now_ts, row["user_id"])
#             db.exec_db(sql)
#                 

            self.PopulateUser(user_id=row["user_id"])
        
            # Check for "locked" or "disabled" status
            if self.Status < 1:
                return False, "disabled"

            db.close()
            
            self._create_user_session()
            return True, ""
        else:
            return False, None
        
    def Authenticate(self, login_id, password, client_ip, change_password=None, answer=None):
        # Some of the failure to authenticate return values pass back a token.
        # this is so we can know how to prompt the user.
        # but, to make hacking a little more difficult, we don't return too much detail about 
        # usernames or passwords.
        if not login_id:
            return False, "id required"
        if not password and not answer:
            return False, "Password required."
        
        self.ClientIP = client_ip
        
        # alrighty, lets check the password
        # we do this by encrypting the form submission and comparing, 
        # NOT by decrypting it here.
        db = catocommon.new_conn()
        sset = settings.settings.security()

        self.PopulateUser(login_id=login_id)
        
        # These checks happen BEFORE we verify the password
        
        # Check for "locked" or "disabled" status
        if self.Status < 1:
            return False, "disabled"

        # Check failed login attempts against the security policy
        if self.FailedLoginAttempts and sset.PassMaxAttempts:
            if self.FailedLoginAttempts >= sset.PassMaxAttempts:
                logger.warning("User.Authenticate : Invalid login attempt - excessive failures.")
                return False, "failures"
        
        # TODO - check if the account is expired 
        
        # once you've gotten your account locked due to failed attempts, you can no longer
        # use the forgot password feature. 
        # that's why this happens after that.
        
        # forgot password
        # if an 'answer' was provided, it can serve as an alternate authentication
        # but it will force a password change.
        if answer:
            sql = "select security_answer from users where username='%s'" % login_id
            db_ans = db.select_col_noexcep(sql)
            
            encans = catocommon.cato_encrypt(answer)
            
            if db_ans == encans:
                self.ForceChange = True
                sql = "update users set force_change=1 where user_id='%s'" % self.ID
                db.exec_db(sql)
            else:
                sql = "update users set failed_login_attempts=failed_login_attempts+1 where user_id='%s'" % self.ID
                db.exec_db(sql)

                logger.warning("User.Authenticate : Invalid login attempt - [%s] wrong security question answer." % (login_id))
                return False, "Incorrect security answer."
        
        
        # try the password if it was provided
        if password:
            sql = "select user_password from users where username='%s'" % login_id
            db_pwd = db.select_col_noexcep(sql)
            
            encpwd = catocommon.cato_encrypt(password)
            
            if db_pwd != encpwd:
                sql = "update users set failed_login_attempts=failed_login_attempts+1 where user_id='%s'" % self.ID
                db.exec_db(sql)

                logger.warning("User.Authenticate : Invalid login attempt - [%s] bad password." % (login_id))
                return False, ""

        # TODO:
        # Check Expiration coming up - for a warning
        
        # force change
        # the user authenticated, but they are required to change their password
        if self.ForceChange:
            if change_password:
                # a new password was provided
                result, msg = User.ValidatePassword(self.ID, change_password)
                if not result:
                    return False, msg

                # put it in the history
                self.AddPWToHistory(change_password)
                
                # and update with the new one
                sql = "update users set force_change=0, user_password=%s where user_id=%s"
                db.exec_db(sql, (catocommon.cato_encrypt(change_password), self.ID))
            else:
                return False, "change"
        
        
        self._create_user_session()
        
        db.close()
        return True, ""

    # STATIC METHOD
    # creates this Cloud as a new record in the db
    # and returns the object
    @staticmethod
    def DBCreateNew(username, fullname, role, password, generatepw, authtype="local", forcechange=1, email=None, status=1, expires=None, groups=None):
        # TODO: All the password testing, etc.
        db = catocommon.new_conn()

        # all sorts of validation
        if re.match("^[\a-zA-Z0-9_.-@]+$", username) is None:
            raise Exception("Usernames cannot contain spaces or any characters other than letters, numbers or these chars [_.@-].")

        newid = catocommon.new_guid()
        authtype = authtype if authtype else "local"
        forcechange = 0 if forcechange == 0 or forcechange == "0" else 1
        email = email if email else ""
        encpw = None
        
        if authtype == "local":
            if password:
                result, msg = User.ValidatePassword(None, password)
                if result:
                    encpw = catocommon.cato_encrypt(password)
                else:
                    raise Exception(msg)
            elif catocommon.is_true(generatepw):
                encpw = catocommon.cato_encrypt(catocommon.generate_password())
            else:
                raise Exception("A password must be provided, or check the box to generate one.")

        if role not in ("Administrator", "Developer", "User"):
            raise Exception("Role must be 'Administrator', 'Developer', or 'User'.")
        
        pw2insert = "'%s'" % encpw if encpw else " null"
        ex2insert = ("str_to_date('{0}', '%%m/%%d/%%Y')".format(expires) if expires else " null")
        sql = """insert into users
            (user_id, username, full_name, authentication_type, force_change, email, status, user_role, user_password, expiration_dt)
            values ('%s', '%s', '%s', '%s', %s, '%s', '%s', '%s', %s, %s)""" % (newid, username, fullname, authtype, forcechange,
                email, status, role, pw2insert, ex2insert)

        if not db.tran_exec_noexcep(sql):
            if db.error == "key_violation":
                raise Exception("A User with that Login ID already exists.  Please select another.")
            else: 
                raise Exception(db.error)

        db.tran_commit()
        
        if groups:
            # if we can't create groups we don't actually fail...
            sql = "select group_concat(tag_name order by tag_name separator ',') as tags from tags"
            alltags = db.select_col_noexcep(sql)
            if alltags:
                alltags = alltags.split(",")
                for tag in groups:
                    if tag in alltags:
                        sql = "insert object_tags (object_type, object_id, tag_name) values (1, '%s','%s')" % (newid, tag)
                        if not db.exec_db_noexcep(sql):
                            logger.error("Error creating Groups for new user %s." % newid)
        
        # now it's inserted... lets get it back from the db as a complete object for confirmation.
        u = User()
        u.FromID(newid)
        u.AddPWToHistory(encpw)
        
        db.close()
        return u

    @staticmethod
    def HasHistory(user_id):
        """Returns True if the user has historical data."""
        db = catocommon.new_conn()
        #  history in user_session.
        sql = "select count(*) from user_session where user_id = '" + user_id + "'"
        iResults = db.select_col(sql)

        if iResults:
            return True

        #  history in user_security_log
        sql = "select count(*) from user_security_log where user_id = '" + user_id + "'"
        iResults = db.select_col(sql)

        if iResults:
            return True

        return False

    def AddPWToHistory(self, pw):
        db = catocommon.new_conn()
        sql = "insert user_password_history (user_id, change_time, password) values (%s, now(), %s)"
        db.exec_db(sql, (self.ID, pw))
        db.close()        

