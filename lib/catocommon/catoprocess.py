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
        self.db = catodb.Db()
        conn = self.db.connect_db(server=catoconfig.CONFIG["server"], port=catoconfig.CONFIG["port"],
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
        sql = "select id from application_registry where app_name = '" + self.process_name + \
            "' and app_instance = '" + self.host_domain + "'"

        result = self.db.select_col(sql)
        if not result:
            self.logger.info(self.process_name + " has not been registered, registering...")
            self.register_app()
            result = self.db.select_col(sql)
            self.instance_id = result
        else:
            self.logger.info(self.process_name + " has already been registered, updating...")
            self.instance_id = result
            self.logger.info("application instance = %d" % self.instance_id)
            self.db.exec_db("""update application_registry set hostname = %s, userid = %s,
                 pid = %s, platform = %s where id = %s""",
                (self.host_domain, self.user, str(self.my_pid), self.platform,
                 self.instance_id))

    def register_app(self):
        self.logger.info("Registering application...")

        sql = "insert into application_registry (app_name, app_instance, master, logfile_name, " \
            "hostname, userid, pid, platform) values ('" + self.process_name + \
            "', '" + self.host_domain + "',1, '" + self.process_name.lower() + ".log', \
            '" + self.host + "', '" + self.user + "'," + str(self.my_pid) + ",'" + self.platform + "')"
        self.db.exec_db(sql)
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
        pass

    def startup(self):
        CatoProcess.startup(self)
        self.check_registration()
        self.get_settings
        self.db_heart = catodb.Db()
        conn_heart = self.db_heart.connect_db(server=self.config["server"], port=self.config["port"],
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
