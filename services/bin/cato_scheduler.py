#!/usr/bin/env python

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

### requires croniter from https://github.com/taichino/croniter
from croniter import croniter
from datetime import datetime

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catosettings import settings
from catocommon import catocommon

class Scheduler(catocommon.CatoService):

    scheduler_enabled = ""

    def get_settings(self):
        try:
            previous_mode = self.scheduler_enabled
    
            sset = settings.settings.scheduler()
            if sset:
                self.scheduler_enabled = sset.Enabled
                self.loop = sset.LoopDelay
                self.min_depth = sset.ScheduleMinDepth
                self.max_days = sset.ScheduleMaxDays
                self.max_days = sset.ScheduleMaxDays
                
                # doesn't seem to be implemented, but it's a setting on the table.
                # one of the processes cleans up the application_registry table
                self.clean_appreg = sset.CleanAppRegistry
            else:
                self.output("Unable to get settings - using previous values.")
    
            if previous_mode != "" and previous_mode != self.scheduler_enabled:
                self.output("*** Control Change: Enabled is now %s" % 
                    (self.scheduler_enabled))
        except Exception as ex:
            self.output(ex)

    def clear_scheduled_action_plans(self):
        try:
            sql = """delete from action_plan where source = 'schedule'"""
            self.db.exec_db(sql)
        except Exception as ex:
            self.output("Unable to delete from action_plan.\n"+ ex.__str__())

    def expand_this_schedule(self, row):
        try:
            schedule_id = row[0]
            now = row[1]
            months = row[2]
            days_or_weeks = row[3]
            days = row[4]
            #hours [split_clean = row[5]]
            #minutes [split_clean = row[6]]
            hours = row[5]
            minutes = row[6]
            start_dt = row[7]
            task_id = row[8]
            action_id = row[9]
            ecosystem_id = row[10]
            parameter_xml = row[11]
            debug_level = row[12]
            start_instances = row[13]
            account_id = row[14]
    
            #print "Number to start = ", start_instances
            if not start_dt:
                start_dt = now
            else:
                start_dt = start_dt + 1
    
            #days = self.split_clean(self.string map(self.day_map, days))
            #months = self.split_clean(months)
    
            #the_dates = ""
            #print days_or_weeks
            #print days
            if days_or_weeks == 1:
                # this will be days of the week, 0 - 6
                # 0 = sunday, 1 = monday, ... 6 = saturday
                dow = days.rstrip(",")
                dom = "*"
            else:
                # this will be days of the month, 1 - 31
                dow = "*"
                dom = days.rstrip(",")
    
            months = ",".join([str((int(i) + 1)) for i in months.rstrip(",").split(",")])
            #start_dt = start_dt + 600000
            the_start_dt = datetime.fromtimestamp(start_dt)
            cron_string = minutes.rstrip(",") + " " + hours.rstrip(",") + " " + dom + " " +  months + " " + dow
            #print cron_string
            citer = croniter(cron_string, the_start_dt) 
            for _ in range(start_instances):
                date = citer.get_next(datetime)
                #print date
                sql = """insert into action_plan 
                        (task_id,run_on_dt,action_id,ecosystem_id,parameter_xml,debug_level,source,schedule_id, account_id)
                        values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                self.db.exec_db(sql, (task_id, date, action_id, ecosystem_id, parameter_xml, debug_level, 'schedule', schedule_id, account_id))
        except Exception as ex:
            self.output("Unable to expand schedule or insert into action_plan.\n"+ ex.__str__())

    def expand_schedules(self):
        try:
            sql = """select distinct(a.schedule_id), unix_timestamp() as now, a.months, a.days_or_weeks, a.days, 
                        a.hours, a.minutes, max(unix_timestamp(ap.run_on_dt)), a.task_id, a.action_id, a.ecosystem_id,
                        a.parameter_xml, a.debug_level, %s - count(ap.schedule_id) as num_to_start, a.account_id, a.last_modified
                    from action_schedule a
                    left outer join action_plan ap on ap.schedule_id = a.schedule_id
                    group by a.schedule_id
                    having count(*) < %s"""
    
            rows = self.db.select_all(sql, (self.min_depth, self.min_depth))
            if rows:
                for row in rows:
                    #print "row is"
                    #print row
                    self.expand_this_schedule(row)
        except Exception as ex:
            self.output("Error in expand_schedules.\n"+ ex.__str__())

    def run_schedule_instance(self, instance_row):
        try:
            schedule_id = instance_row[0]
            plan_id = instance_row[1]
            task_id = instance_row[2]
            action_id = instance_row[3]
            ecosystem_id = instance_row[4]
            parameter_xml = instance_row[5]
            debug_level = instance_row[6]
            run_on_dt = instance_row[7]
            account_id = instance_row[8]
    
            sql = """call addTaskInstance (%s,NULL,%s,%s,%s,%s,%s,%s)"""
            row = self.db.exec_proc(sql, (task_id, schedule_id, debug_level, plan_id, parameter_xml, ecosystem_id, account_id))
    
            ti = row[0]["_task_instance"]
            #print "task instance is " + ti
            self.output("Started task instance %s for schedule id %s and plan id %s" % (ti, schedule_id, plan_id))
            sql = """insert into action_plan_history (plan_id, task_id, run_on_dt, action_id, 
                    ecosystem_id, parameter_xml, debug_level, source, schedule_id, task_instance, account_id)
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            self.db.exec_db(sql, (plan_id, task_id, run_on_dt, action_id, ecosystem_id, parameter_xml, 
                debug_level, 'schedule', schedule_id, ti, account_id))
            sql = """delete from action_plan where plan_id = %s"""
            self.db.exec_db(sql, (plan_id))
        except Exception as ex:
            self.output("Unable to run schedule instance.  Probable error inserting action_plan_history.\n"+ ex.__str__())


    def check_schedules(self):
        try:
            sql = """select ap.schedule_id, min(ap.plan_id) as plan_id, ap.task_id,
                    ap.action_id, ap.ecosystem_id, ap.parameter_xml, ap.debug_level, min(ap.run_on_dt), ap.account_id
                    from action_plan  ap
                    where run_on_dt < now() group by schedule_id"""
    
            rows = self.db.select_all(sql)
            if rows:
                for row in rows:
                    self.run_schedule_instance(row)
        except Exception as ex:
            self.output("Unable to check_schedules.\n"+ ex.__str__())

    def main_process(self):
        """main process loop, parent class will call this"""

        self.expand_schedules()
        self.check_schedules()

if __name__ == "__main__":

    scheduler = Scheduler("cato_scheduler")
    scheduler.startup()
    scheduler.clear_scheduled_action_plans()
    scheduler.service_loop()

