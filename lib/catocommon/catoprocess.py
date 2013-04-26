#########################################################################
# Copyright 2011 Cloud Sidekick
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#########################################################################

import logging
import os.path
import time
import threading
import pwd
from catodb import catodb
from catolog import catolog
from catoconfig import catoconfig
import catocommon as CC

class CatoProcess():
    def __init__(self, process_name):
        self.host = os.uname()[1]
        self.platform = os.uname()[0]
        self.user = pwd.getpwuid(os.getuid())[0]
        self.host_domain = self.user + '@' + os.uname()[1]
        self.my_pid = os.getpid()
        self.process_name = process_name
        self.home = catoconfig.BASEPATH
        self.tmpdir = catoconfig.CONFIG["tmpdir"]

        # tell catoconfig what the LOGFILE name is, then get a logger
        # if logging has already been set up this won't do anything
        # but if it's not yet, this will set the basic config
        logging.basicConfig(level=logging.DEBUG)

        catolog.set_logfile(os.path.join(catolog.LOGPATH, self.process_name.lower() + ".log"))
        self.logger = catolog.get_logger(process_name)

    def startup(self):
        self.logger.info("""
#######################################
    Starting up %s
#######################################""" % self.process_name)

        self.logger.info("Configuration File: [%s]" % catoconfig.CONFFILE)

        
        self.db = catodb.Db()
        self.db.connect_db(server=catoconfig.CONFIG["server"], port=catoconfig.CONFIG["port"],
            user=catoconfig.CONFIG["user"],
            password=catoconfig.CONFIG["password"], database=catoconfig.CONFIG["database"])
        self.config = catoconfig.CONFIG


    def end(self):
        self.db.close()


class CatoService(CatoProcess):

    def __init__(self, process_name):
        CatoProcess.__init__(self, process_name)
        self.delay = 3
        self.loop = 10
        self.mode = "on"
        self.master = 1


    def check_registration(self):

        # Get the node number
        sql = """select id from application_registry where app_name = %s and app_instance = %s"""

        result = self.db.select_col(sql, (self.process_name, self.host_domain))
        if not result:
            self.logger.info("[%s] has not been registered, registering..." % self.process_name)
            self.register_app()
            result = self.db.select_col(sql, (self.process_name, self.host_domain))
            self.instance_id = result
        else:
            self.logger.info("[%s] has already been registered, updating..." % self.process_name)
            self.instance_id = result
            self.logger.info("application instance = %d" % self.instance_id)
            sql = """update application_registry set 
                hostname = %s, 
                userid = %s,
                pid = %s, 
                platform = %s 
                where id = %s"""
            self.db.exec_db(sql, (self.host_domain, self.user, self.my_pid, self.platform, self.instance_id))

    def register_app(self):
        self.logger.info("Registering application...")

        sql = """insert into application_registry 
            (app_name, app_instance, master, logfile_name, hostname, userid, pid, platform)
            values 
            (%s, %s, 1, %s, %s, %s, %s, %s)"""
        params = (self.process_name, self.host_domain, "%s.log" % self.process_name.lower(),
                self.host, self.user, self.my_pid, self.platform)
        self.db.exec_db(sql, params)
        self.logger.info("Application registered.")

    def heartbeat_loop(self, event):
        while True:
            event.wait(self.loop)
            if event.isSet():
                break
            self.update_heartbeat()

    def update_heartbeat(self):
        sql = "update application_registry set heartbeat = now() where id = %s"
        self.db_heart.exec_db(sql, (self.instance_id))

    def get_settings(self):
        """
        This does nothing here in the generic format, but is overloaded 
        by any other processes that subclass CatoService.
        """
        pass

    def startup(self):
        CatoProcess.startup(self)
        self.check_registration()
        self.get_settings
        self.db_heart = catodb.Db()
        self.db_heart.connect_db(server=self.config["server"], port=self.config["port"],
            user=self.config["user"],
            password=self.config["password"], database=self.config["database"])
        self.update_heartbeat()
        self.heartbeat_event = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop, args=(self.heartbeat_event,))
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        # catocommon is shared by all modules, so put a reference to this new service there.
        CC.CATOSERVICE = self

    def end(self):
        self.heartbeat_event.set()
        self.heartbeat_thread.join()
        self.db.close()

    def service_loop(self):
        while True:
            self.get_settings()
            self.main_process()
            time.sleep(self.loop)
