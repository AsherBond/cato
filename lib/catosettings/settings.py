"""
    All of the settings for the Cato modules.
"""
import json

from catocommon import catocommon
from catolog import catolog
logger = catolog.get_logger(__name__)

class settings(object):
    # initing the whole parent class gives you DICTIONARIES of every subclass
    def __init__(self):
        self.Security = self.security().__dict__
        self.Poller = self.poller().__dict__
        self.Marshaller = self.marshaller().__dict__
        self.Messenger = self.messenger().__dict__
        self.Scheduler = self.scheduler().__dict__
        self.Maestro = self.maestro().__dict__
        self.MaestroScheduler = self.maestroscheduler().__dict__
        
    def AsJSON(self):
        return catocommon.ObjectOutput.AsJSON(self.__dict__)

    def AsXML(self):
        return catocommon.ObjectOutput.AsXML(self.__dict__, "Settings")

    def AsText(self, delimiter, headers=False):
        out = []
        for mod, sets in self.__dict__.iteritems():
            out.append("%s\n" % (mod.capitalize()))
            
            for k, v in sets.iteritems():
                out.append("    %s : %s\n" % (k, v))

            out.append("\n")

        return "".join(out)

    class security(object):
        """
            These settings are defaults if there are no values in the database.
        """
        PassMaxAge = 90  # how old can a password be?
        PassMaxAttempts = 30
        PassMaxLength = 32
        PassMinLength = 8
        PassComplexity = False  # require 'complex' passwords (number and special character)
        PassAgeWarn = 15  # number of days before expiration to begin warning the user about password expiration
        PasswordHistory = 5  # The number of historical passwords to cache and prevent reuse.
        PassRequireInitialChange = True  # require change on initial login?
        AutoLockReset = 1  # The number of minutes before failed password lockout expires
        LoginMessage = ""  # The message that appears on the login screen
        AuthErrorMessage = ""  # a customized message that appears when there are failed login attempts
        NewUserMessage = ""  # the body of an email sent to new user accounts
        PageViewLogging = False  # whether or not to log user-page access in the security log
        ReportViewLogging = False  # whether or not to log user-report views in the security log
        AllowLogin = True  # Is the system "up" and allowing users to log in?
        
        def __init__(self):
            s = settings.get_application_section("security")
            self.PassMaxAge = s.get("PassMaxAge", self.PassMaxAge)
            self.PassMaxAttempts = s.get("PassMaxAttempts", self.PassMaxAttempts)
            self.PassMaxLength = s.get("PassMaxLength", self.PassMaxLength)
            self.PassMinLength = s.get("PassMinLength", self.PassMinLength)
            self.PassComplexity = s.get("PassComplexity", self.PassComplexity)
            self.PassAgeWarn = s.get("PassAgeWarn", self.PassAgeWarn)
            self.PasswordHistory = s.get("PasswordHistory", self.PasswordHistory)
            self.PassRequireInitialChange = s.get("PassRequireInitialChange", self.PassRequireInitialChange)
            self.AutoLockReset = s.get("AutoLockReset", self.AutoLockReset)
            self.LoginMessage = s.get("LoginMessage", self.LoginMessage)
            self.AuthErrorMessage = s.get("AuthErrorMessage", self.AuthErrorMessage)
            self.NewUserMessage = s.get("NewUserMessage", self.NewUserMessage)
            self.PageViewLogging = s.get("PageViewLogging", self.PageViewLogging)
            self.ReportViewLogging = s.get("ReportViewLogging", self.ReportViewLogging)
            self.AllowLogin = s.get("AllowLogin", self.AllowLogin)
            
        def DBSave(self):
            self.PassComplexity = catocommon.is_true(self.PassComplexity)
            self.PassRequireInitialChange = catocommon.is_true(self.PassRequireInitialChange)
            self.PageViewLogging = catocommon.is_true(self.PageViewLogging)
            self.ReportViewLogging = catocommon.is_true(self.ReportViewLogging)
            self.AllowLogin = catocommon.is_true(self.AllowLogin)

            self.PassMaxAge = int(self.PassMaxAge) if str(self.PassMaxAge).isdigit() else 90
            self.PassMaxAttempts = int(self.PassMaxAttempts) if str(self.PassMaxAttempts).isdigit() else 30
            self.PassMaxLength = int(self.PassMaxLength) if str(self.PassMaxLength).isdigit() else 32
            self.PassMinLength = int(self.PassMinLength) if str(self.PassMinLength).isdigit() else 8
            self.PassAgeWarn = int(self.PassAgeWarn) if str(self.PassAgeWarn).isdigit() else 15
            self.PasswordHistory = int(self.PasswordHistory) if str(self.PasswordHistory).isdigit() else 5
            self.AutoLockReset = int(self.AutoLockReset) if str(self.AutoLockReset).isdigit() else 1
            
            settings.set_application_section("security", json.dumps(self.__dict__))
            return True

        def AsJSON(self):
            return catocommon.ObjectOutput.AsJSON(self.__dict__)

        def AsXML(self):
            return catocommon.ObjectOutput.AsXML(self.__dict__, "Security")
    
        def AsText(self, delimiter, headers=False):
            out = []
            for k, v in self.__dict__.iteritems():
                out.append("    %s : %s\n" % (k, v))
            return "".join(out)
    
    class poller(object):
        """
            These settings are defaults if there are no values in the database.
        """
        Enabled = True  # is it processing work?
        LoopDelay = 3  # how often does it check for work?
        MaxProcesses = 32  # maximum number of task engines at one time
        
        def __init__(self):
            s = settings.get_application_section("poller")
            self.Enabled = s.get("Enabled", self.Enabled)
            self.LoopDelay = s.get("LoopDelay", self.LoopDelay)
            self.MaxProcesses = s.get("MaxProcesses", self.MaxProcesses)
            
        def DBSave(self):
            self.Enabled = catocommon.is_true(self.Enabled)
            self.LoopDelay = int(self.LoopDelay) if str(self.LoopDelay).isdigit() else 3
            self.MaxProcesses = int(self.MaxProcesses) if str(self.MaxProcesses).isdigit() else 32
            settings.set_application_section("poller", json.dumps(self.__dict__))
            return True

        def AsJSON(self):
            return catocommon.ObjectOutput.AsJSON(self.__dict__)

        def AsXML(self):
            return catocommon.ObjectOutput.AsXML(self.__dict__, "Poller")
    
        def AsText(self, delimiter, headers=False):
            out = []
            for k, v in self.__dict__.iteritems():
                out.append("    %s : %s\n" % (k, v))
            return "".join(out)
    
    class maestro(object):
        """
            General settings for Maestro.
        """
        MenuCanvas = ""
        HomeCanvas = ""
        PortalCanvas = ""
        
        def __init__(self):
            s = settings.get_application_section("maestro")
            self.MenuCanvas = s.get("MenuCanvas", "")
            self.HomeCanvas = s.get("HomeCanvas", "")
            self.PortalCanvas = s.get("PortalCanvas", "")
            
        def DBSave(self):
            settings.set_application_section("maestro", json.dumps(self.__dict__))
            return True

        def AsJSON(self):
            return catocommon.ObjectOutput.AsJSON(self.__dict__)

        def AsXML(self):
            return catocommon.ObjectOutput.AsXML(self.__dict__, "Maestro")
    
        def AsText(self, delimiter, headers=False):
            out = []
            for k, v in self.__dict__.iteritems():
                out.append("    %s : %s\n" % (k, v))
            return "".join(out)
    
    class marshaller(object):
        """
            These settings are defaults if there are no values in the database.
        """
        Enabled = True  # is it processing work?
        LoopDelay = 10  # how often does it check for work?
        Debug = 20  # the debug level
        
        def __init__(self):
            s = settings.get_application_section("marshaller")
            self.Enabled = s.get("Enabled", self.Enabled)
            self.LoopDelay = s.get("LoopDelay", self.LoopDelay)
            self.Debug = s.get("Debug", self.Debug)
            
        def DBSave(self):
            self.Enabled = catocommon.is_true(self.Enabled)
            self.LoopDelay = int(self.LoopDelay) if str(self.LoopDelay).isdigit() else 10
            self.Debug = int(self.Debug) if str(self.Debug).isdigit() else 20
            settings.set_application_section("marshaller", json.dumps(self.__dict__))
            return True

        def AsJSON(self):
            return catocommon.ObjectOutput.AsJSON(self.__dict__)

        def AsXML(self):
            return catocommon.ObjectOutput.AsXML(self.__dict__, "Marshaller")
    
        def AsText(self, delimiter, headers=False):
            out = []
            for k, v in self.__dict__.iteritems():
                out.append("    %s : %s\n" % (k, v))
            return "".join(out)
    
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
        SMTPServerPort = 25
        SMTPConnectionTimeout = 30
        SMTPLegacySSL = ""
        FromEmail = ""
        FromName = ""
        AdminEmail = ""
        
        def __init__(self):
            s = settings.get_application_section("messenger")
            self.Enabled = s.get("Enabled", self.Enabled)
            self.PollLoop = s.get("PollLoop", self.PollLoop)
            self.RetryDelay = s.get("RetryDelay", self.RetryDelay)
            self.RetryMaxAttempts = s.get("RetryMaxAttempts", self.RetryMaxAttempts)
            self.SMTPServerAddress = s.get("SMTPServerAddress", self.SMTPServerAddress)
            self.SMTPUserAccount = s.get("SMTPUserAccount", self.SMTPUserAccount)
            self.SMTPServerPort = s.get("SMTPServerPort", self.SMTPServerPort)
            self.SMTPConnectionTimeout = s.get("SMTPConnectionTimeout", self.SMTPConnectionTimeout)
            self.SMTPLegacySSL = s.get("SMTPLegacySSL", self.SMTPLegacySSL)
            self.FromEmail = s.get("FromEmail", self.FromEmail)
            self.FromName = s.get("FromName", self.FromName)
            self.AdminEmail = s.get("AdminEmail", self.AdminEmail)

            if s.get("SMTPUserPassword"):
                self.SMTPUserPassword = catocommon.cato_decrypt(s["SMTPUserPassword"])
            
        def DBSave(self):
            """ 
            The messenger has some special considerations when updating!
            """
            self.Enabled = catocommon.is_true(self.Enabled)
            self.SMTPLegacySSL = catocommon.is_true(self.SMTPLegacySSL)

            self.PollLoop = int(self.PollLoop) if str(self.PollLoop).isdigit() else 30
            self.RetryDelay = int(self.RetryDelay) if str(self.RetryDelay).isdigit() else 5
            self.RetryMaxAttempts = int(self.RetryMaxAttempts) if str(self.RetryMaxAttempts).isdigit() else 3
            self.SMTPServerPort = int(self.SMTPServerPort) if str(self.SMTPServerPort).isdigit() else 25
            self.SMTPConnectionTimeout = int(self.SMTPConnectionTimeout) if str(self.SMTPConnectionTimeout).isdigit() else 30

            # only update password if it has been changed.  This "filler" is set in the gui to show stars so ignore it.
            if self.SMTPUserPassword and self.SMTPUserPassword != "~!@@!~":
                self.SMTPUserPassword = catocommon.cato_encrypt(self.SMTPUserPassword)

            # don't put these in the settings, they're utility
            del self.SMTPPasswordConfirm

            settings.set_application_section("messenger", json.dumps(self.__dict__))
            return True

        def AsJSON(self):
            return catocommon.ObjectOutput.AsJSON(self.__dict__)

        def AsXML(self):
            return catocommon.ObjectOutput.AsXML(self.__dict__, "Messenger")
    
        def AsText(self, delimiter, headers=False):
            out = []
            for k, v in self.__dict__.iteritems():
                out.append("    %s : %s\n" % (k, v))
            return "".join(out)
    
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
            s = settings.get_application_section("scheduler")
            self.Enabled = s.get("Enabled", self.Enabled)
            self.LoopDelay = s.get("LoopDelay", self.LoopDelay)
            self.ScheduleMinDepth = s.get("ScheduleMinDepth", self.ScheduleMinDepth)
            self.ScheduleMaxDays = s.get("ScheduleMaxDays", self.ScheduleMaxDays)
            self.CleanAppRegistry = s.get("CleanAppRegistry", self.CleanAppRegistry)
            
        def DBSave(self):
            self.Enabled = catocommon.is_true(self.Enabled)

            self.LoopDelay = int(self.LoopDelay) if str(self.LoopDelay).isdigit() else 10
            self.ScheduleMinDepth = int(self.ScheduleMinDepth) if str(self.ScheduleMinDepth).isdigit() else 10
            self.ScheduleMaxDays = int(self.ScheduleMaxDays) if str(self.ScheduleMaxDays).isdigit() else 90
            self.CleanAppRegistry = int(self.CleanAppRegistry) if str(self.CleanAppRegistry).isdigit() else 5

            settings.set_application_section("scheduler", json.dumps(self.__dict__))
            return True

        def AsJSON(self):
            return catocommon.ObjectOutput.AsJSON(self.__dict__)

        def AsXML(self):
            return catocommon.ObjectOutput.AsXML(self.__dict__, "Scheduler")
    
        def AsText(self, delimiter, headers=False):
            out = []
            for k, v in self.__dict__.iteritems():
                out.append("    %s : %s\n" % (k, v))
            return "".join(out)
    
    
    class maestroscheduler(object):
        """
            These settings are defaults if there are no values in the database.
        """
        Enabled = True  # is it processing work?
        LoopDelay = 10  # how often does it check for work?
        ScheduleMinDepth = 10  # minimum number of queue entries
        ScheduleMaxDays = 90  # the maximum distance in the future to que entries
        
        def __init__(self):
            s = settings.get_application_section("maestroscheduler")
            self.Enabled = s.get("Enabled", self.Enabled)
            self.LoopDelay = s.get("LoopDelay", self.LoopDelay)
            self.ScheduleMinDepth = s.get("ScheduleMinDepth", self.ScheduleMinDepth)
            self.ScheduleMaxDays = s.get("ScheduleMaxDays", self.ScheduleMaxDays)
            
        def DBSave(self):
            self.Enabled = catocommon.is_true(self.Enabled)

            self.LoopDelay = int(self.LoopDelay) if str(self.LoopDelay).isdigit() else 10
            self.ScheduleMinDepth = int(self.ScheduleMinDepth) if str(self.ScheduleMinDepth).isdigit() else 10
            self.ScheduleMaxDays = int(self.ScheduleMaxDays) if str(self.ScheduleMaxDays).isdigit() else 90

            settings.set_application_section("maestroscheduler", json.dumps(self.__dict__))
            return True

        def AsJSON(self):
            return catocommon.ObjectOutput.AsJSON(self.__dict__)

        def AsXML(self):
            return catocommon.ObjectOutput.AsXML(self.__dict__, "MaestroScheduler")
    
        def AsText(self, delimiter, headers=False):
            out = []
            for k, v in self.__dict__.iteritems():
                out.append("    %s : %s\n" % (k, v))
            return "".join(out)
    
    
    
    """
        APPLICATION SETTINGS are stored as JSON.
        These ARE actual user-configurable settings.
        
        The document is a dictionary, and each top level item is a section.
        
        TODO: this method will take over all the individual tables above.
    """
    @staticmethod
    def get_application_section(section):
        # this will return a whole section of the document
        sql = "select settings_json from application_settings where id = 1"
        
        db = catocommon.new_conn()
        sjson = db.select_col(sql)
        db.close()
        if sjson:
            doc = json.loads(sjson)
            return doc.get(section, {})
        return {}
        
    @staticmethod
    def set_application_section(section, value):
        doc = {}
        
        sql = "select settings_json from application_settings where id = 1"
        db = catocommon.new_conn()
        sjson = db.select_col(sql)
        db.close()
        if sjson:
            doc = json.loads(sjson)

        doc[section] = json.loads(value)
        
        sql = "update application_settings set settings_json=%s where id = 1"
        db = catocommon.new_conn()
        if not db.exec_db_noexcep(sql, catocommon.ObjectOutput.AsJSON(doc)):
            raise Exception("Info: attempt to set application section [%s] failed." % (section))

    @staticmethod
    def get_application_setting(section, setting):
        # given a section, this will return a single setting
        sql = "select settings_json from application_settings where id = 1"
        
        db = catocommon.new_conn()
        sjson = db.select_col(sql)
        db.close()
        if sjson:
            doc = json.loads(sjson)
            return doc.get(section, {}).get(setting)
        
#     @staticmethod
#     def set_application_setting(section, setting, value):
#         if not section or not setting:
#             logger.warning("Info: attempt to set application setting - missing section or setting name [%s/%s]." % (section, setting))
#             return False, "Section and Setting are required."
        

    """
        APPLICATION DETAILS are stored as XML.
        These ARE NOT settings - they are hidden details that are set/read programatically.
        Users cannot edit these details.
    """
    @staticmethod
    def get_application_detail(xpath):
        sql = "select setting_xml from application_settings where id = 1"
        
        db = catocommon.new_conn()
        sxml = db.select_col(sql)
        db.close()
        if sxml:
            xdoc = catocommon.ET.fromstring(sxml)
            if xdoc is not None:
                return xdoc.findtext(xpath, "")
        
    @staticmethod
    def set_application_detail(category, setting, value):
        # key is required, category is not
        if not setting:
            logger.warning("Info: attempt to set application setting - missing setting name [%s/%s]." % (category, setting))
            return False, "Setting is a required value."
        
        sql = "select setting_xml from application_settings where id = 1"
        
        db = catocommon.new_conn()
        sxml = db.select_col(sql)
        # if there's no settings xml row, insert it
        if not sxml:
            sql = "delete from application_settings"
            db.exec_db(sql)
            sql = "insert into application_settings (id, setting_xml) values (1, '<settings />')"
            db.exec_db(sql)
            sxml = "<settings />"
            
        if sxml:
            xdoc = catocommon.ET.fromstring(sxml)
            if xdoc is not None:
                
                # category is optional - if omitted, the new one goes in the root
                if category:
                    xcat = xdoc.find(category)
                    if xcat is None:
                        xcat = catocommon.ET.Element(category)
                        xdoc.append(xcat)

                    xnew = xcat.find(setting)
                    if xnew is None:
                        xnew = catocommon.ET.Element(setting)
                        xcat.append(xnew)

                    xnew.text = ("" if value is None else value)

                else:
                    xnew = xdoc.find(setting)
                    if xnew is None:
                        xnew = catocommon.ET.Element(setting)
                        xdoc.append(xnew)
                    
                    xnew.text = ("" if value is None else value)


                sql = "update application_settings set setting_xml='%s' where id=1" % catocommon.ET.tostring(xdoc)
                db = catocommon.new_conn()
                if not db.exec_db_noexcep(sql):
                    raise Exception("Info: attempt to set application setting [%s/%s] failed." % (category, setting))

        return True
