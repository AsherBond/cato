"""
    All of the settings for the Cato modules.
"""
try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET

try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET


from catocommon import catocommon
from catolog import catolog
logger = catolog.get_logger(__name__)

class settings(object):
    # initing the whole parent class gives you DICTIONARIES of every subclass
    def __init__(self):
        self.Security = self.security().__dict__
        self.Poller = self.poller().__dict__
        self.Messenger = self.messenger().__dict__
        self.Scheduler = self.scheduler().__dict__
        
    def AsJSON(self):
        return catocommon.ObjectOutput.AsJSON(self.__dict__)

    class security(object):
        """
            These settings are defaults if there are no values in the database.
        """
        PassMaxAge = 90  # how old can a password be?
        PassMaxAttempts = 3
        PassMaxLength = 32
        PassMinLength = 8
        PassComplexity = True  # require 'complex' passwords (number and special character)
        PassAgeWarn = 15  # number of days before expiration to begin warning the user about password expiration
        PasswordHistory = 5  # The number of historical passwords to cache and prevent reuse.
        PassRequireInitialChange = True  # require change on initial login?
        AutoLockReset = 5  # The number of minutes before failed password lockout expires
        LoginMessage = ""  # The message that appears on the login screen
        AuthErrorMessage = ""  # a customized message that appears when there are failed login attempts
        NewUserMessage = ""  # the body of an email sent to new user accounts
        PageViewLogging = False  # whether or not to log user-page access in the security log
        ReportViewLogging = False  # whether or not to log user-report views in the security log
        AllowLogin = True  # Is the system "up" and allowing users to log in?
        
        def __init__(self):
            try:
                sql = """select pass_max_age, pass_max_attempts, pass_max_length, pass_min_length, pass_age_warn_days,
                        auto_lock_reset, login_message, auth_error_message, pass_complexity, pass_require_initial_change, pass_history,
                        page_view_logging, report_view_logging, allow_login, new_user_email_message
                        from login_security_settings
                        where id = 1"""
                
                db = catocommon.new_conn()
                row = db.select_row_dict(sql)
                if row:
                    self.PassMaxAge = row["pass_max_age"]
                    self.PassMaxAttempts = row["pass_max_attempts"]
                    self.PassMaxLength = row["pass_max_length"]
                    self.PassMinLength = row["pass_min_length"]
                    self.PassComplexity = catocommon.is_true(row["pass_complexity"])
                    self.PassAgeWarn = row["pass_age_warn_days"]
                    self.PasswordHistory = row["pass_history"]
                    self.PassRequireInitialChange = catocommon.is_true(row["pass_require_initial_change"])
                    self.AutoLockReset = row["auto_lock_reset"]
                    self.LoginMessage = row["login_message"]
                    self.AuthErrorMessage = row["auth_error_message"]
                    self.NewUserMessage = row["new_user_email_message"]
                    self.PageViewLogging = catocommon.is_true(row["page_view_logging"])
                    self.ReportViewLogging = catocommon.is_true(row["report_view_logging"])
                    self.AllowLogin = catocommon.is_true(row["allow_login"])
            except Exception as ex:
                raise ex
            finally:
                db.close()
            
        def DBSave(self):
            try:
                db = catocommon.new_conn()
                sql = """update login_security_settings set
                    pass_max_age=%s,
                    pass_max_attempts=%s,
                    pass_max_length=%s,
                    pass_min_length=%s,
                    pass_complexity=%s,
                    pass_age_warn_days=%s,
                    pass_history=%s,
                    pass_require_initial_change=%s,
                    auto_lock_reset=%s,
                    login_message=%s,
                    auth_error_message=%s,
                    new_user_email_message=%s,
                    page_view_logging=%s,
                    report_view_logging=%s,
                    allow_login=%s
                    where id = 1"""

                params = (self.PassMaxAge,
                          self.PassMaxAttempts,
                          self.PassMaxLength,
                          self.PassMinLength,
                          ("1" if catocommon.is_true(self.PassComplexity) else "0"),
                          self.PassAgeWarn,
                          self.PasswordHistory,
                          ("1" if catocommon.is_true(self.PassRequireInitialChange) else "0"),
                          ("1" if catocommon.is_true(self.AutoLockReset) else "0"),
                          self.LoginMessage.replace("'", "''"),
                          self.AuthErrorMessage.replace("'", "''").replace(";", ""),
                          self.NewUserMessage.replace("'", "''").replace(";", ""),
                          ("1" if catocommon.is_true(self.PageViewLogging) else "0"),
                          ("1" if catocommon.is_true(self.ReportViewLogging) else "0"),
                          ("1" if self.AllowLogin else "0"))

                if not db.exec_db_noexcep(sql, params):
                    return False, db.error
            
                return True, ""
            except Exception as ex:
                raise ex
            finally:
                db.close()

        def AsJSON(self):
            return catocommon.ObjectOutput.AsJSON(self.__dict__)

    class poller(object):
        """
            These settings are defaults if there are no values in the database.
        """
        Enabled = True  # is it processing work?
        LoopDelay = 10  # how often does it check for work?
        MaxProcesses = 32  # maximum number of task engines at one time
        
        def __init__(self):
            try:
                sql = """select mode_off_on, loop_delay_sec, max_processes
                    from poller_settings
                    where id = 1"""
                
                db = catocommon.new_conn()
                row = db.select_row_dict(sql)
                if row:
                    self.Enabled = catocommon.is_true(row["mode_off_on"])
                    self.LoopDelay = row["loop_delay_sec"]
                    self.MaxProcesses = row["max_processes"]
            except Exception as ex:
                raise ex
            finally:
                db.close()
            
        def DBSave(self):
            try:
                sql = """update poller_settings set
                    mode_off_on=%s
                    loop_delay_sec=%s
                    max_processes=%s"""

                params = (("1" if catocommon.is_true(self.Enabled) else "0"), str(self.LoopDelay), str(self.MaxProcesses))
                
                db = catocommon.new_conn()
                if not db.exec_db_noexcep(sql, params):
                    return False, db.error
            
                return True, ""
            except Exception as ex:
                raise ex
            finally:
                db.close()

        def AsJSON(self):
            return catocommon.ObjectOutput.AsJSON(self.__dict__)

    class messenger(object):
        """
            These settings are defaults if there are no values in the database.
        """
        Enabled = True
        PollLoop = 30  # how often to check for new messages
        RetryDelay = 5  # how long to wait before resend on an error
        RetryMaxAttempts = 3  # max re3tries
        SMTPServerAddress = ""
        SMTPUserAccount = ""
        SMTPUserPassword = ""
        SMTPServerPort = ""
        SMTPConnectionTimeout = ""
        SMTPUseSSL = ""
        FromEmail = ""
        FromName = ""
        AdminEmail = ""
        
        def __init__(self):
            try:
                sql = """select mode_off_on, loop_delay_sec, retry_delay_min, retry_max_attempts,
                    smtp_server_addr, smtp_server_user, smtp_server_password, smtp_server_port, smtp_timeout, smtp_ssl, 
                    from_email, from_name, admin_email
                    from messenger_settings
                    where id = 1"""
                
                db = catocommon.new_conn()
                row = db.select_row_dict(sql)
                if row:
                    self.Enabled = catocommon.is_true(row["mode_off_on"])
                    self.PollLoop = row["loop_delay_sec"]
                    self.RetryDelay = row["retry_delay_min"]
                    self.RetryMaxAttempts = row["retry_max_attempts"]
                    self.SMTPServerAddress = row["smtp_server_addr"]
                    self.SMTPUserAccount = row["smtp_server_user"]
                    self.SMTPUserPassword = catocommon.cato_decrypt(row["smtp_server_password"])
                    self.SMTPServerPort = row["smtp_server_port"]
                    self.SMTPConnectionTimeout = row["smtp_timeout"]
                    self.SMTPUseSSL = row["smtp_ssl"]
                    self.FromEmail = row["from_email"]
                    self.FromName = row["from_name"]
                    self.AdminEmail = row["admin_email"]
            except Exception as ex:
                raise ex
            finally:
                db.close()
            
        def DBSave(self):
            """ 
            The messenger has some special considerations when updating!
            """
            sql = """update messenger_settings set 
                mode_off_on=%s,
                loop_delay_sec=%s,
                retry_delay_min=%s,
                retry_max_attempts=%s,
                smtp_server_addr=%s,
                smtp_server_user=%s,
                smtp_server_port=%s,
                smtp_timeout=%s,
                smtp_ssl=%s,
                from_email=%s,
                from_name=%s,
                admin_email=%s"""
            
            # only update password if it has been changed.
            sPasswordFiller = "~!@@!~"
            if self.SMTPUserPassword != sPasswordFiller:
                sql += ",smtp_server_password='%s'" % catocommon.cato_encrypt(self.SMTPUserPassword)

            params = (("1" if catocommon.is_true(self.Enabled) else "0"),
                    str(self.PollLoop),
                    str(self.RetryDelay),
                    str(self.RetryMaxAttempts),
                    self.SMTPServerAddress,
                    self.SMTPUserAccount,
                    str(self.SMTPServerPort),
                    str(self.SMTPConnectionTimeout),
                    ("1" if catocommon.is_true(self.SMTPUseSSL) else "0"),
                    self.FromEmail,
                    self.FromName,
                    self.AdminEmail)

            db = catocommon.new_conn()
            if not db.exec_db_noexcep(sql, params):
                return False, db.error
        
            return True, ""

        def AsJSON(self):
            return catocommon.ObjectOutput.AsJSON(self.__dict__)

    class scheduler(object):
        """
            These settings are defaults if there are no values in the database.
        """
        Enabled = True  # is it processing work?
        LoopDelay = 10  # how often does it check for work?
        ScheduleMinDepth = 10  # minimum number of queue entries
        ScheduleMaxDays = 90  # the maximum distance in the future to que entries
        CleanAppRegistry = 5  # time in minutes when items in application_registry are assumed defunct and removed
        
        def __init__(self):
            try:
                sql = """select mode_off_on, loop_delay_sec, schedule_min_depth, schedule_max_days, clean_app_registry
                    from scheduler_settings
                    where id = 1"""
                
                db = catocommon.new_conn()
                row = db.select_row_dict(sql)
                if row:
                    self.Enabled = catocommon.is_true(row["mode_off_on"])
                    self.LoopDelay = row["loop_delay_sec"]
                    self.ScheduleMinDepth = row["schedule_min_depth"]
                    self.ScheduleMaxDays = row["schedule_max_days"]
                    self.CleanAppRegistry = row["clean_app_registry"]
            except Exception as ex:
                raise ex
            finally:
                db.close()
            
        def DBSave(self):
            try:
                sql = """update scheduler_settings set
                    mode_off_on=%s,
                    loop_delay_sec=%s,
                    schedule_min_depth=%s,
                    schedule_max_days=%s,
                    clean_app_registry%s"""

                params = (("1" if catocommon.is_true(self.Enabled) else "0"),
                          str(self.LoopDelay),
                          str(self.ScheduleMinDepth),
                          str(self.ScheduleMaxDays),
                          str(self.CleanAppRegistry))

                db = catocommon.new_conn()
                if not db.exec_db_noexcep(sql, params):
                    return False, db.error
            
                return True, ""
            except Exception as ex:
                raise ex
            finally:
                db.close()

        def AsJSON(self):
            return catocommon.ObjectOutput.AsJSON(self.__dict__)

    """
        Application Settings are stored as XML in a separate table.
        They aren't hardcoded settings and aren't required - can be added/deleted as needed.
    """
    @staticmethod
    def get_application_setting(xpath):
        try:
            sql = "select setting_xml from application_settings where id = 1"
            
            db = catocommon.new_conn()
            sxml = db.select_col_noexcep(sql)
            if sxml:
                xdoc = ET.fromstring(sxml)
                if xdoc is not None:
                    return xdoc.findtext(xpath, "")
                
            logger.warning("Info: attempt to find application settings [%s] failed." % xpath)
            return ""
        except Exception as ex:
            raise ex
        finally:
            db.close()
        
    @staticmethod
    def set_application_setting(category, setting, value):
        try:
            # key is required, category is not
            if not setting:
                logger.warning("Info: attempt to set application setting - missing setting name [%s/%s]." % (category, setting))
                return False, "Setting is a required value."
            
            sql = "select setting_xml from application_settings where id = 1"
            
            db = catocommon.new_conn()
            sxml = db.select_col_noexcep(sql)
            # if there's no settings xml row, insert it
            if not sxml:
                sql = "delete from application_settings"
                db.exec_db_noexcep(sql)
                sql = "insert into application_settings (id, setting_xml) values (1, '<settings />')"
                db.exec_db_noexcep(sql)
                sxml = "<settings />"
                
            if sxml:
                xdoc = ET.fromstring(sxml)
                if xdoc is not None:
                    
                    # category is optional - if omitted, the new one goes in the root
                    if category:
                        xcat = xdoc.find(category)
                        if xcat is None:
                            xcat = ET.Element(category)
                            xdoc.append(xcat)

                        xnew = xcat.find(setting)
                        if xnew is None:
                            xnew = ET.Element(setting)
                            xcat.append(xnew)

                        xnew.text = ("" if value is None else value)

                    else:
                        xnew = xdoc.find(setting)
                        if xnew is None:
                            xnew = ET.Element(setting)
                            xdoc.append(xnew)
                        
                        xnew.text = ("" if value is None else value)


                    sql = "update application_settings set setting_xml='%s' where id=1" % ET.tostring(xdoc)
                    db = catocommon.new_conn()
                    if not db.exec_db_noexcep(sql):
                        logger.warning("Info: attempt to set application setting [%s/%s] failed." % (category, setting))
                        return False, db.error
        
            return True, ""
        except Exception as ex:
            raise ex
        finally:
            db.close()
