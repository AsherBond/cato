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

import os
import sys
import time
import signal

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catolog import catolog
from catocommon import catoprocess
from catosettings import settings

class Poller(catoprocess.CatoService):

    poller_enabled = ""

    def start_submitted_tasks(self, get_num):

        task_list = []
        sql = """select ti.task_instance, ti.asset_id, 
            ti.schedule_instance 
            from task_instance ti
            join task t on t.task_id = ti.task_id
            where ti.task_status = 'Submitted'
                and ti.ce_node = %s
            order by task_instance asc limit %s"""
        rows = self.db.select_all(sql, (self.instance_id, get_num))
        if rows:
            for row in rows:
                task_instance = row[0]
                self.logger.info("Considering Task Instance: %d" % (task_instance))
                asset_id = row[1]
                schedule_instance = row[2]

                if task_instance > 0:
                    error_flag = 0
                    self.logger.info("Starting process ...")

                    cmd_line = "nohup %s/services/bin/cato_task_engine %d >> %s/ce/%d.log 2>&1 &" % (self.home, task_instance, catolog.LOGPATH, task_instance)

                    ret = os.system(cmd_line)
                    self.logger.info("Task instance %d started with return code of %d" % (task_instance, ret))
                    sql = """update task_instance set task_status = 'Staged'
                        where task_instance = %s"""
                    self.db.exec_db(sql, (task_instance))
                    time.sleep(0.01)
                        
    def update_to_error(self, the_pid):
    
        self.logger.info("Setting tasks with PID %s and Processing status to Error..." % (the_pid))                  

        sql = """update task_instance set task_status = 'Error',
            completed_dt = now() 
            where pid = %s and task_status = 'Processing'"""
        self.db.exec_db(sql, (the_pid))

    def update_cancelled(self, task_instance):

        sql = """update task_instance set task_status = 'Cancelled', 
            completed_dt = now() where task_instance = %s"""
        self.db.exec_db(sql, (task_instance))

    def kill_ce_pid(self, pid):

        self.logger.info("Killing process %s" % (pid))
        try:
            os.kill(int(pid), signal.SIGKILL)
            #os.wait()
        except Exception, e:
            self.logger.info("Attempt to kill process %s failed: %s"% (pid, str(e)))
            

    def check_processing(self):

        db_pids = []
        os_pids = []
        sql = """select distinct pid from task_instance 
            where ce_node = %s and task_status = 'Processing' 
            and pid is not null"""
        rows = self.db.select_all(sql, (self.instance_id))
        if rows:
            for row in rows:
                db_pids.append(row[0])

        cmd_line = """ps U%s -opid | grep "%s/services/bin/cato_task_engine" | grep -v grep""" % (self.user, self.home)

        #os_pids = os.system(cmd_line)
        #print cmd_line
        #print os_pids
        #print db_pids
        not_running_pids = list(set(db_pids)-set(os_pids))
        for pid in not_running_pids:
            self.update_to_error(pid)

    def update_load(self):
        
        loads = os.getloadavg()
        sql = """update application_registry set load_value = %s 
            where id = %s"""
        self.db.exec_db(sql, (loads[0], self.instance_id))

    def get_settings(self):
        previous_mode = self.poller_enabled
        
        pset = settings.settings.poller()
        if pset:
            self.poller_enabled = pset.Enabled
            self.loop = pset.LoopDelay
            self.max_processes = pset.MaxProcesses
        else:
            self.logger.info("Unable to get settings - using previous values.")
        
        mset = settings.settings.messenger()
        self.admin_email = (mset.AdminEmail if mset.AdminEmail else "")

        if previous_mode != "" and previous_mode != self.poller_enabled:
            self.logger.info("*** Control Change: Enabled is now %s" % 
                (str(self.poller_enabled)))

    def get_aborting(self): 

        sql = """select task_instance, ifnull(pid, 0) from task_instance 
            where task_status = 'Aborting' 
                and ce_node = %s
            order by task_instance asc"""

        rows = self.db.select_all(sql, (self.instance_id))
        if rows:
            for row in rows:
                self.logger.info("Cancelling task_instance %d, pid %d" %
                    (row[0], row[1]))

                if row[1]:
                    self.kill_ce_pid(row[1])
                self.update_cancelled(row[0])

    def main_process(self):
        """main process loop, parent class will call this"""

        self.update_load()
        self.get_aborting()
        #self.check_processing()

        # don't kick off any new work if the poller isn't enabled.
        if self.poller_enabled:
            ### TO DO - need to get process count from linux
            process_count = 0
            get_processes = self.max_processes - process_count
    
            self.start_submitted_tasks(get_processes)

