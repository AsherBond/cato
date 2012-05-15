"""
    All of the settings for the Cato modules.
"""
import json
from catocommon import catocommon

class settings(object):
    #initing the whole parent class gives you DICTIONARIES of every subclass
    def __init__(self):
        self.Security = self.security().__dict__
        self.Poller = self.poller().__dict__
        self.Messenger = self.messenger().__dict__
        self.Scheduler = self.scheduler().__dict__
        
    def AsJSON(self):
        return json.dumps(self.__dict__)

    class security(object):
        """
            These settings are defaults if there are no values in the database.
        """
        PassMaxAge = 90 # how old can a password be?
        PassMaxAttempts = 3
        PassMaxLength = 32
        PassMinLength = 8
        PassComplexity = True # require 'complex' passwords (number and special character)
        PassAgeWarn = 15 # number of days before expiration to begin warning the user about password expiration
        PasswordHistory = 5 # The number of historical passwords to cache and prevent reuse.
        PassRequireInitialChange = True # require change on initial login?
        AutoLockReset = 5 # The number of minutes before failed password lockout expires
        LoginMessage = "" # The message that appears on the login screen
        AuthErrorMessage = "" # a customized message that appears when there are failed login attempts
        NewUserMessage = "" # the body of an email sent to new user accounts
        PageViewLogging = False # whether or not to log user-page access in the security log
        ReportViewLogging = False # whether or not to log user-report views in the security log
        AllowLogin = True # Is the system "up" and allowing users to log in?
        
        def __init__(self):
            try:
                sSQL = "select pass_max_age, pass_max_attempts, pass_max_length, pass_min_length, pass_age_warn_days," \
                        " auto_lock_reset, login_message, auth_error_message, pass_complexity, pass_require_initial_change, pass_history," \
                        " page_view_logging, report_view_logging, allow_login, new_user_email_message" \
                        " from login_security_settings" \
                        " where id = 1"
                
                db = catocommon.new_conn()
                row = db.select_row_dict(sSQL)
                if row:
                    self.PassMaxAge = row["pass_max_age"]
                    self.PassMaxAttempts = row["pass_max_attempts"]
                    self.PassMaxLength = row["pass_max_length"]
                    self.PassMinLength = row["pass_min_length"]
                    self.PassComplexity = catocommon.IsTrue(row["pass_complexity"])
                    self.PassAgeWarn = row["pass_age_warn_days"]
                    self.PasswordHistory = row["pass_history"]
                    self.PassRequireInitialChange = catocommon.IsTrue(row["pass_require_initial_change"])
                    self.AutoLockReset = row["auto_lock_reset"]
                    self.LoginMessage = row["login_message"]
                    self.AuthErrorMessage = row["auth_error_message"]
                    self.NewUserMessage = row["new_user_email_message"]
                    self.PageViewLogging = catocommon.IsTrue(row["page_view_logging"])
                    self.ReportViewLogging = catocommon.IsTrue(row["report_view_logging"])
                    self.AllowLogin = catocommon.IsTrue(row["allow_login"])
            except Exception, ex:
                raise Exception(ex)
            finally:
                db.close()
            
        def DBSave(self):
            try:
                sSQL = "update login_security_settings set" \
                    " pass_max_age='" + self.PassMaxAge + "'," \
                    " pass_max_attempts='" + self.PassMaxAttempts + "'," \
                    " pass_max_length='" + self.PassMaxLength + "'," \
                    " pass_min_length='" + self.PassMinLength + "'," \
                    " pass_complexity='" + ("1" if catocommon.IsTrue(self.PassComplexity) else "0") + "'," \
                    " pass_age_warn_days='" + self.PassAgeWarn + "'," \
                    " pass_history = '" + self.PasswordHistory + "'," \
                    " pass_require_initial_change='" + ("1" if catocommon.IsTrue(self.PassRequireInitialChange) else "0") + "'," \
                    " auto_lock_reset='" + catocommon.IsTrue(self.AutoLockReset) + "'," \
                    " login_message='" + self.LoginMessage.replace("'", "''") + "'," \
                    " auth_error_message='" + self.AuthErrorMessage.replace("'", "''").replace(";", "") + "'," \
                    " new_user_email_message='" + self.NewUserMessage.replace("'", "''").replace(";", "") + "'," \
                    " page_view_logging='" + ("1" if catocommon.IsTrue(self.PageViewLogging) else "0") + "'," \
                    " report_view_logging='" + ("1" if catocommon.IsTrue(self.ReportViewLogging) else "0") + "'," \
                    " allow_login='" + ("1" if self.AllowLogin else "0") + "'" \
                    " where id = 1"

                db = catocommon.new_conn()
                if not db.exec_db_noexcep(sSQL):
                    return False, db.error
            
                return True, ""
            except Exception, ex:
                raise Exception(ex)
            finally:
                db.close()

        def AsJSON(self):
            return json.dumps(self.__dict__)

    class poller(object):
        """
            These settings are defaults if there are no values in the database.
        """
        Enabled = True # is it processing work?
        LoopDelay = 10 # how often does it check for work?
        MaxProcesses = 32 # maximum number of task engines at one time
        
        def __init__(self):
            try:
                sSQL = "select mode_off_on, loop_delay_sec, max_processes" \
                    " from poller_settings" \
                    " where id = 1"
                
                db = catocommon.new_conn()
                row = db.select_row_dict(sSQL)
                if row:
                    self.Enabled = catocommon.IsTrue(row["mode_off_on"])
                    self.LoopDelay = row["loop_delay_sec"]
                    self.MaxProcesses = row["max_processes"]
            except Exception, ex:
                raise Exception(ex)
            finally:
                db.close()
            
        def DBSave(self):
            try:
                sSQL = "update poller_settings set" \
                    " mode_off_on='" + ("1" if catocommon.IsTrue(self.Enabled) else "0") + "'," \
                    " loop_delay_sec='" + str(self.LoopDelay) + "'," \
                    " max_processes='" + str(self.MaxProcesses) + "'"

                db = catocommon.new_conn()
                if not db.exec_db_noexcep(sSQL):
                    return False, db.error
            
                return True, ""
            except Exception, ex:
                raise Exception(ex)
            finally:
                db.close()

        def AsJSON(self):
            return json.dumps(self.__dict__)

    class messenger(object):
        """
            These settings are defaults if there are no values in the database.
        """
        Enabled = True
        PollLoop = 30 # how often to check for new messages
        RetryDelay = 5 # how long to wait before resend on an error
        RetryMaxAttempts = 3 # max re3tries
        SMTPServerAddress = ""
        SMTPUserAccount = ""
        SMTPServerPort = ""
        FromEmail = ""
        FromName = ""
        AdminEmail = ""
        
        def __init__(self):
            try:
                sSQL = "select mode_off_on, loop_delay_sec, retry_delay_min, retry_max_attempts," \
                    " smtp_server_addr, smtp_server_user, smtp_server_password, smtp_server_port, from_email, from_name, admin_email" \
                    " from messenger_settings" \
                    " where id = 1"
                
                db = catocommon.new_conn()
                row = db.select_row_dict(sSQL)
                if row:
                    self.Enabled = catocommon.IsTrue(row["mode_off_on"])
                    self.PollLoop = row["loop_delay_sec"]
                    self.RetryDelay = row["retry_delay_min"]
                    self.RetryMaxAttempts = row["retry_max_attempts"]
                    self.SMTPServerAddress = row["smtp_server_addr"]
                    self.SMTPUserAccount = row["smtp_server_user"]
                    self.SMTPServerPort = row["smtp_server_port"]
                    self.FromEmail = row["from_email"]
                    self.FromName = row["from_name"]
                    self.AdminEmail = row["admin_email"]
            except Exception, ex:
                raise Exception(ex)
            finally:
                db.close()
            
        def DBSave(self):
            try:
                """ The messenger has some special considerations when updating!
                
                ($#d@x!&
                
                ^^^ can't even use that, it was messing up the web.py templator - do something else
                
                """
                sSQL = """update messenger_settings set mode_off_on='{0}', 
                    loop_delay_sec={1}, retry_delay_min={2}, retry_max_attempts={3}, 
                    smtp_server_addr='{4}', smtp_server_user='{5}', smtp_server_port={6}, 
                    from_email='{7}', from_name='{8}', admin_email='{9}'"""
                # only update password if it has been changed.
                sPasswordFiller = "~!@@!~"
                if self.SMTPUserPassword != sPasswordFiller:
                    sSQL += ",smtp_server_password='{10}'";

                sSQL = sSQL.format(("1" if catocommon.IsTrue(self.Enabled) else "0"), 
                       str(self.PollLoop), str(self.RetryDelay),
                        str(self.RetryMaxAttempts), self.SMTPServerAddress, self.SMTPUserAccount, 
                        str(self.SMTPServerPort), self.FromEmail, self.FromName, self.AdminEmail, 
                        catocommon.cato_encrypt(self.SMTPUserPassword))

                db = catocommon.new_conn()
                if not db.exec_db_noexcep(sSQL):
                    return False, db.error
            
                return True, ""
            except Exception, ex:
                print ex.__str__()
                raise Exception(ex)
            finally:
                db.close()

        def AsJSON(self):
            return json.dumps(self.__dict__)

    class scheduler(object):
        """
            These settings are defaults if there are no values in the database.
        """
        Enabled = True # is it processing work?
        LoopDelay = 10 # how often does it check for work?
        ScheduleMinDepth = 10 # minimum number of queue entries
        ScheduleMaxDays = 90 # the maximum distance in the future to que entries
        CleanAppRegistry = 5 # time in minutes when items in application_registry are assumed defunct and removed
        
        def __init__(self):
            try:
                sSQL = "select mode_off_on, loop_delay_sec, schedule_min_depth, schedule_max_days, clean_app_registry" \
                    " from scheduler_settings" \
                    " where id = 1"
                
                db = catocommon.new_conn()
                row = db.select_row_dict(sSQL)
                if row:
                    self.Enabled = catocommon.IsTrue(row["mode_off_on"])
                    self.LoopDelay = row["loop_delay_sec"]
                    self.ScheduleMinDepth = row["schedule_min_depth"]
                    self.ScheduleMaxDays = row["schedule_max_days"]
                    self.CleanAppRegistry = row["clean_app_registry"]
            except Exception, ex:
                raise Exception(ex)
            finally:
                db.close()
            
        def DBSave(self):
            try:
                sSQL = "update scheduler_settings set" \
                " mode_off_on='" + ("1" if catocommon.IsTrue(self.Enabled) else "0") + "'," \
                " loop_delay_sec='" + str(self.LoopDelay) + "'," \
                " schedule_min_depth='" + str(self.ScheduleMinDepth) +"'," \
                " schedule_max_days='" + str(self.ScheduleMaxDays) +"'," \
                " clean_app_registry = '" + str(self.CleanAppRegistry) + "'"

                db = catocommon.new_conn()
                if not db.exec_db_noexcep(sSQL):
                    return False, db.error
            
                return True, ""
            except Exception, ex:
                raise Exception(ex)
            finally:
                db.close()

        def AsJSON(self):
            return json.dumps(self.__dict__)
