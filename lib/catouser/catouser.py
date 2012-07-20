
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
import json
import re
from catosettings import settings
from catocommon import catocommon

class Users(object): 
    rows = {}
        
    def __init__(self, sFilter=""):
        try:
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
            
            db = catocommon.new_conn()
            self.rows = db.select_all_dict(sSQL)
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.rows)
        except Exception as ex:
            raise ex

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
        self.SettingsXML = ""
        self.Tags = []
    
    @staticmethod
    def ValidatePassword(uid, pwd):
        """
        Checks a password against the system settings for length, complexity, etc.
        """
        try:
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
        except Exception as ex:
            raise Exception(ex)

    def FromName(self, sUsername):
        self.PopulateUser(login_id=sUsername)
        
    def FromID(self, sUserID):
        self.PopulateUser(user_id=sUserID)

    def PopulateUser(self, user_id="", login_id=""):
        """
            Note the absence of password or security_answer in this method.  There are specialized 
            methods for testing passwords, etc.
        """
        try:
            if not user_id and not login_id:
                raise Exception("Error building User object: User ID or Login is required.");    
            
            sSQL = """select u.user_id, u.username, u.full_name, u.status, u.last_login_dt,
                u.failed_login_attempts, u.email ,u.authentication_type,
                u.security_question, u.force_change, u.settings_xml,
                u.user_role, u.expiration_dt
                from users u"""
            
            if user_id:
                sSQL += " where u.user_id = '%s'""" % user_id
            elif login_id:
                sSQL += " where u.username = '%s'""" % login_id


            db = catocommon.new_conn()
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
                self.Email = ("" if not dr["email"] else dr["email"])
                self.SettingsXML = ("" if not dr["settings_xml"] else dr["settings_xml"])

            else: 
                print("Unable to build User object. Either no Users are defined, or no User with ID/Login [%s%s] could be found." % (user_id, login_id))
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()        

    def AsJSON(self):
        try:
            return json.dumps(self.__dict__)
        except Exception as ex:
            raise ex

    def Authenticate(self, login_id, password, client_ip, change_password=None, answer=None):
        try:
            # Some of the failure to authenticate return values pass back a token.
            # this is so we can know how to prompt the user.
            # but, to make hacking a little more difficult, we don't return too much detail about 
            # usernames or passwords.
            
            # alrighty, lets check the password
            # we do this by encrypting the form submission and comparing, 
            # NOT by decrypting it here.
            db = catocommon.new_conn()
            sset = settings.settings.security()

            self.PopulateUser(login_id=login_id)
            if not self.ID:
                print("User.Authenticate : Unable to find user record for [%s]." % login_id)
                return False, ""
            
            # These checks happen BEFORE we verify the password
            
            # Check for "locked" or "disabled" status
            if self.Status < 1:
                return False, "disabled"

            # Check failed login attempts against the security policy
            if self.FailedLoginAttempts and sset.PassMaxAttempts:
                if self.FailedLoginAttempts >= sset.PassMaxAttempts:
                    print("User.Authenticate : Invalid login attempt - excessive failures.")
                    return False, "failures"
            
            # TODO - check if the account is expired 
            
            # once you've gotten your account locked due to failed attempts, you can no longer
            # use the forgot password feature. 
            # that's why this happens after that.
            
            db = catocommon.new_conn()

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
                    if not db.exec_db_noexcep(sql):
                        print(db.error)
                else:
                    sql = "update users set failed_login_attempts=failed_login_attempts+1 where user_id='%s'" % self.ID
                    if not db.exec_db_noexcep(sql):
                        print(db.error)
                    print("User.Authenticate : Invalid login attempt - [%s] wrong security question answer." % (login_id))
                    return False, "Incorrect security answer."
            
            
            # try the password if it was provided
            if password:
                sql = "select user_password from users where username='%s'" % login_id
                db_pwd = db.select_col_noexcep(sql)
                
                encpwd = catocommon.cato_encrypt(password)
                
                if db_pwd != encpwd:
                    sql = "update users set failed_login_attempts=failed_login_attempts+1 where user_id='%s'" % self.ID
                    if not db.exec_db_noexcep(sql):
                        print(db.error)
                    print("User.Authenticate : Invalid login attempt - [%s] bad password." % (login_id))
                    return False, ""

            # TODO:
            # Check Expiration coming up - for a warning
            
            # force change
            # the user authenticated, but they are required to change their password
            change_clause = ""
            if self.ForceChange:
                if change_password:
                    # a new password was provided
                    result, msg = User.ValidatePassword(self.ID, change_password)
                    if not result:
                        return False, msg

                    # put it in the history
                    self.AddPWToHistory(change_password)
                    
                    # and update with the new one
                    change_clause = ",force_change=0, user_password='%s'" % catocommon.cato_encrypt(change_password)
                else:
                    return False, "change"
            
            
            
            # ALL GOOD!
            # what are the users tags?
            sql = "select tag_name from object_tags where object_type = 1 and object_id='%s'" % (self.ID)
            # NOTE this is "select_all", not "select_all_dict"... because I DO want a list.
            rows = db.select_all(sql)
            tags = []
            if rows:
                for tag in rows:
                    tags.append(tag[0])
                self.Tags = tags
            

            # reset the user counters and last_login
            sql = "update users set failed_login_attempts=0, last_login_dt=now() %s where user_id='%s'" % (change_clause, self.ID)
            if not db.exec_db_noexcep(sql):
                print(db.error)
        
            # whack and add to the user_session table
            if not db.exec_db_noexcep("delete from user_session where user_id = '%s' and address = '%s'" % (self.ID, client_ip)):
                print(db.error)
                return False, "Unable to update session table. (1)"
            
            sql = """insert into user_session (user_id, address, login_dt, heartbeat, kick)
                values ('%s','%s', now(), now(), 0)""" % (self.ID, client_ip)
            if not db.exec_db_noexcep(sql):
                print(db.error)
                return False, "Unable to update session table. (1)"

        
            return True, ""
        except Exception as ex:
            print(ex.__str__())
            return False, ex.__str__()
        finally:
            db.close()        

    #STATIC METHOD
    #creates this Cloud as a new record in the db
    #and returns the object
    @staticmethod
    def DBCreateNew(sUsername, sFullName, sAuthType, sPassword, sGeneratePW, sForcePasswordChange, sUserRole, sEmail, sStatus, sGroupArray):
        try:
            # TODO: All the password testing, etc.
            db = catocommon.new_conn()

            sNewID = catocommon.new_guid()

            if sAuthType == "local":
                if sPassword:
                    if sPassword:
                        result, msg = User.ValidatePassword(None, sPassword)
                        if result:
                            sEncPW = "'%s'" % catocommon.cato_encrypt(sPassword)
                        else:
                            return None, msg
                elif catocommon.is_true(sGeneratePW):
                    sEncPW = "'%s'" % catocommon.cato_encrypt(catocommon.generate_password())
                else:
                    return None, "A password must be provided, or check the box to generate one."
            elif sAuthType == "ldap":
                sEncPW = " null"
            
            sSQL = "insert into users" \
                " (user_id, username, full_name, authentication_type, force_change, email, status, user_role, user_password)" \
                " values ('" + sNewID + "'," \
                "'" + sUsername + "'," \
                "'" + sFullName + "'," \
                "'" + sAuthType + "'," \
                "'" + sForcePasswordChange + "'," \
                "'" + (sEmail if sEmail else "") + "'," \
                "'" + sStatus + "'," \
                "'" + sUserRole + "'," \
                "" + sEncPW + "" \
                ")"
            
            if not db.tran_exec_noexcep(sSQL):
                if db.error == "key_violation":
                    return None, "A User with that Login ID already exists.  Please select another."
                else: 
                    return None, db.error

            db.tran_commit()
            
            if sGroupArray:
                # if we can't create groups we don't actually fail...
                for tag in sGroupArray:
                    sql = "insert object_tags (object_type, object_id, tag_name) values (1, '%s','%s')" % (sNewID, tag)
                    if not db.exec_db_noexcep(sql):
                        print("Error creating Groups for new user %s." % sNewID)
            
            # now it's inserted... lets get it back from the db as a complete object for confirmation.
            u = User()
            u.FromID(sNewID)
            u.AddPWToHistory(sEncPW)
            
            return u, None
        except Exception as ex:
            raise ex
        finally:
            db.close()

    @staticmethod
    def HasHistory(user_id):
        """Returns True if the user has historical data."""
        try:
            db = catocommon.new_conn()
            #  history in user_session.
            sql = "select count(*) from user_session where user_id = '" + user_id + "'"
            iResults = db.select_col_noexcep(sql)
            if db.error:
                raise Exception(db.error)
    
            if iResults:
                return True
    
            #  history in user_security_log
            sql = "select count(*) from user_security_log where user_id = '" + user_id + "'"
            iResults = db.select_col_noexcep(sql)
            if db.error:
                raise Exception(db.error)
    
            if iResults:
                return True
    
            return False
        except Exception as ex:
            raise ex
        finally:
            if db: db.close()

    def AddPWToHistory(self, pw):
        try:
            db = catocommon.new_conn()
            sql = "insert user_password_history (user_id, change_time, password) values ('%s', now(), '%s')" % (self.ID, pw)
            if not db.exec_db_noexcep(sql):
                print(db.error)
        except Exception as ex:
            return False, ex.__str__()
        finally:
            db.close()        

