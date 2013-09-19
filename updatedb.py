#!/usr/bin/env python

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
This file will evaluate the database of the current Cato installation,
and apply any database changes needed, by version.

    SUPPORTED OPERATORS:
        droptable - table
        createtable - table, columns and keys (basically the entire statement except the 
            beginning "create table `foo`" bit.
        addcolumn - table, column, options
        modifycolumn - table, column, options (allows changing column options but not name)
        changecolumn - table, column, `newname` options (will allow changing of a column name)
        dropcolumn - table, column
        droppk - table
        addpk - table, options (comma delimited columns making up the PK)
        sql - a sql statement
        function - function name (will execute a funcion in this file, useful only
            when very complicated logic is needed for an update.)
        
    NOTE: BE VERY CAREFUL with 'modifycolumn' - it will execute if a column exists
        regardless of whether or not the change is needed.
        This could result is truncating data if used without care across versions.
        
Finally, any very specific schema or data updates that can't be done
as simply as this, should be added to the bottom.
"""

# For each version supported, add a set of statements to the dictionary
versions = [
            ["1.17", [
                      ["createtable", "api_tokens", """(`user_id` varchar(36) NOT NULL,
                                                            `token` varchar(36) NOT NULL,
                                                            `created_dt` datetime NOT NULL,
                                                            PRIMARY KEY (`user_id`) )"""],
                      ["droptable", "deployment_service_state", "NO LONGER NEEDED WAS FOR STATE BASED SEQUENCES"],
                      ["dropcolumn", "deployment", "_template_name"],
                      ["dropcolumn", "deployment", "_template_version"]
                      ]
             ],
            ["1.18", [
                      ["addcolumn", "deployment", "runstate", "varchar(16) NULL after `health`"],
                      ["addcolumn", "deployment_sequence", "options", "TEXT NULL"],
                      ["addcolumn", "application_settings", "license", "TEXT NULL"],
                      ["changecolumn", "task_step_user_settings", "button", "button varchar(1024)"],
                      ["sql", "delete from task_step_user_settings"]
                      ]
             ],
            ["1.19", [
                      ["addindex", "deployment_log", "IX_dep_log_1", "`deployment_id` ASC"],
                      ["addindex", "deployment_log", "IX_dep_log_2", "`deployment_id` ASC, `task_instance` ASC"],
                      ["addindex", "deployment_log", "IX_dep_log_3", "`deployment_id` ASC, `deployment_service_id` ASC"],
                      ["addindex", "deployment_log", "IX_dep_log_4", "`deployment_id` ASC, `instance_id` ASC"],
                      ["addindex", "deployment_log", "IX_dep_log_5", "`deployment_id` ASC, `seq_instance` ASC"],
                      ["addindex", "task_instance", "IX_task_instance_sched_id", "`schedule_id` ASC"]
                      ]
             ],
            ["1.20", [
                      ["createtable", "dep_action_plan", """(
                          `plan_id` bigint(20) NOT NULL AUTO_INCREMENT,
                          `schedule_id` varchar(36) DEFAULT NULL,
                          `type` varchar(16) NOT NULL DEFAULT '',
                          `original_task_id` varchar(36) NOT NULL DEFAULT '',
                          `task_version` decimal(18, 3) DEFAULT NULL,
                          `run_on_dt` datetime NOT NULL,
                          `instance_id` varchar(36) DEFAULT NULL,
                          `state` varchar(32) DEFAULT NULL,
                          `account_id` varchar(36) DEFAULT NULL,
                          `cloud_id` varchar(36) DEFAULT NULL,
                          `parameter_xml` mediumtext NOT NULL,
                          `debug_level` int(11) DEFAULT NULL,
                          PRIMARY KEY (`plan_id`)
                        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8"""],
                      ["createtable", "dep_action_plan_history", """(
                          `plan_id` bigint(20) NOT NULL AUTO_INCREMENT,
                          `schedule_id` varchar(36) DEFAULT NULL,
                          `type` varchar(16) NOT NULL DEFAULT '',
                          `task_id` varchar(36) NOT NULL DEFAULT '',
                          `task_instance` decimal(18, 3) DEFAULT NULL,
                          `run_on_dt` datetime NOT NULL,
                          `instance_id` varchar(36) DEFAULT NULL,
                          `state` varchar(32) DEFAULT NULL,
                          `account_id` varchar(36) DEFAULT NULL,
                          `cloud_id` varchar(36) DEFAULT NULL,
                          `parameter_xml` mediumtext NOT NULL,
                          `debug_level` int(11) DEFAULT NULL,
                          PRIMARY KEY (`plan_id`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""],
                      ["createtable", "dep_action_schedule", """(
                          `schedule_id` varchar(36) NOT NULL DEFAULT '',
                          `type` varchar(16) NOT NULL DEFAULT '',
                          `original_task_id` varchar(36) NOT NULL DEFAULT '',
                          `task_version` decimal(18, 3) DEFAULT NULL,
                          `instance_id` varchar(36) DEFAULT NULL,
                          `state` varchar(32) DEFAULT NULL,
                          `account_id` varchar(36) DEFAULT NULL,
                          `cloud_id` varchar(36) DEFAULT NULL,
                          `months` varchar(27) DEFAULT NULL,
                          `days_or_weeks` int(11) DEFAULT NULL,
                          `days` varchar(84) DEFAULT NULL,
                          `hours` varchar(62) DEFAULT NULL,
                          `minutes` varchar(172) DEFAULT NULL,
                          `parameter_xml` mediumtext NOT NULL,
                          `debug_level` int(11) DEFAULT NULL,
                          `label` varchar(64) DEFAULT NULL,
                          `descr` varchar(512) DEFAULT NULL,
                          PRIMARY KEY (`schedule_id`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""],
                      ["createtable", "dep_monitor_inst", """(
                          `instance_id` varchar(36) NOT NULL,
                          `task_instance` bigint(20) DEFAULT NULL,
                          `status` varchar(32) NOT NULL,
                          `state` varchar(32) DEFAULT NULL,
                          `task_id` varchar(36) DEFAULT NULL,
                          PRIMARY KEY (`instance_id`,`task_instance`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""],
                      ["createtable", "dash_resource", """(
                          `id` varchar(36) NOT NULL,
                          `project` varchar(32) NOT NULL,
                          `component` varchar(45) NOT NULL,
                          `name` varchar(45) NOT NULL,
                          `data` text,
                          PRIMARY KEY (`id`),
                          UNIQUE KEY `proj_comp_name` (`project`,`component`,`name`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""],
                      ["createtable", "deployment_group", """(
                          `deployment_id` varchar(36) NOT NULL,
                          `group_name` varchar(45) NOT NULL,
                          PRIMARY KEY (`deployment_id`,`group_name`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8"""],
                      ["droptable", "dep_service_inst_mon", "NO LONGER NEEDED with the new Maestro scheduler."],
                      ["droptable", "dep_service_inst_proc", "Removing a demo feature."],
                      ["droptable", "dep_service_inst_proc_inst", "Removing a demo feature."],
                      ["addcolumn", "deployment_template", "groups", "varchar(1024) NULL"],
                      ["addcolumn", "asset_credential", "private_key", "varchar(4096) NULL"],
                      ["changecolumn", "deployment", "runstate", "`runstate` VARCHAR(16) NULL DEFAULT 'stopped'"]                    
                    ]
             ],
            ["1.21", [
                      ["addcolumn", "application_settings", "settings_json", "text NULL"],
                      ["function", "_v121_updates"]
                      ]
             ],
            ["1.22", [
                      ["comment", "droptable", "poller_settings", "Consolidated"],
                      ["comment", "droptable", "scheduler_settings", "Consolidated"],
                      ["comment", "droptable", "marshaller_settings", "Consolidated"],
                      ["comment", "droptable", "login_security_settings", "Consolidated"],
                      ["comment", "droptable", "messenger_settings", "Consolidated"]
                      ]
             ]
        ]

import os
import sys
import json

base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catoconfig import catoconfig
from catodb import catodb
from catocommon import catocommon

def main(argv):
    # now, lets go through each defined version, and apply the changes...
    for ver in versions:
        print "Validating Version %s..." % (ver[0])
        
        for item in ver[1]:
            tblexists = None
            colexists = None
            pkexists = None
            ixexists = None
            
            # these apply to several cases below
            if item[0] in ["addcolumn", "dropcolumn", "modifycolumn", "changecolumn"]:        
                sql = """SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE table_schema = 'cato'
                    AND table_name = %s
                    AND column_name = %s"""
                colexists = db.select_col(sql, (item[1], item[2]))
            if item[0] in ["droptable", "createtable"]:        
                sql = """SELECT TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE table_schema = 'cato'
                    AND table_name = %s"""
                tblexists = db.select_col(sql, (item[1]))
            if item[0] in ["droppk", "addpk"]:        
                sql = """SELECT TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                    WHERE table_schema = 'cato'
                    AND table_name = %s
                    AND constraint_type = 'PRIMARY KEY'"""
                pkexists = db.select_col(sql, (item[1]))
            if item[0] in ["addindex", "dropindex"]:        
                sql = """SELECT count(*) FROM information_schema.statistics 
                    where table_name = %s
                    and index_name = %s"""
                ixexists = db.select_col(sql, (item[1], item[2]))

            sql = ""
            if item[0] == "comment":
                continue
            if item[0] == "droptable":
                if tblexists:
                    sql = "drop table `%s`" % (item[1])
            elif item[0] == "createtable":
                if not tblexists:
                    sql = "create table `%s` %s" % (item[1], item[2])
            elif item[0] == "droppk":
                if pkexists:
                    sql = "alter table `%s` drop primary key" % (item[1])
            elif item[0] == "addpk":
                if not tblexists:
                    sql = "alter table `%s` add primary key (%s)" % (item[1], item[2])
            elif item[0] == "dropindex":
                if ixexists:
                    sql = "alter table `%s` drop index `%s`" % (item[1], item[2])
            elif item[0] == "addindex":
                if not ixexists:
                    sql = "alter table `%s` add index `%s` (%s)" % (item[1], item[2], item[3])
            elif item[0] == "addcolumn":
                if not colexists:
                    sql = "alter table `%s` add column `%s` %s" % (item[1], item[2], item[3])
            elif item[0] == "modifycolumn":
                if colexists:
                    sql = "alter table `%s` modify column `%s` %s" % (item[1], item[2], item[3])
            elif item[0] == "changecolumn":
                if colexists:
                    sql = "alter table `%s` change column `%s` %s" % (item[1], item[2], item[3])
            elif item[0] == "dropcolumn":
                if colexists:
                    sql = "alter table `%s` drop column `%s`" % (item[1], item[2])
            elif item[0] == "sql":
                if len(item) > 1 and item[1]:
                    db.exec_db(item[1])
            elif item[0] == "function":
                funcname = item[1]
                try:
                    globals().get(funcname)()
                except Exception as ex:
                    raise Exception("An error occured trying to execute [%s]\n %s" % (funcname, ex.__str__()))
            else:
                print "    encountered unknown directive [%s]" % (item[0])
            
            if sql:
                print "    Executing [%s]" % (sql)
                db.exec_db(sql)
                

        print "    .... done."


def _v121_updates():
    # the changes to the settings tables in 1.21 ... we need to convert the data
    # from the settings tables into the new json document format
    print "    v1.21 - refactoring settings..."
    
    settings = {}

    # poller
    sql = "select * from poller_settings where id = 1"
    row = db.select_row_dict(sql)
    
    settings["poller"] = {
            "Enabled" : catocommon.is_true(row["mode_off_on"]),
            "LoopDelay" : row["loop_delay_sec"],
            "MaxProcesses" : row["max_processes"]
        }

    # marshaller
    sql = "select * from marshaller_settings where id = 1"
    row = db.select_row_dict(sql)
    
    settings["marshaller"] = {
            "Enabled" : catocommon.is_true(row["mode_off_on"]),
            "LoopDelay" : row["loop_delay_sec"]
        }

    # messenger
    sql = "select * from messenger_settings where id = 1"
    row = db.select_row_dict(sql)
    
    settings["messenger"] = {
            "Enabled" : catocommon.is_true(row["mode_off_on"]),
            "PollLoop" : row["loop_delay_sec"],
            "RetryDelay" : row["retry_delay_min"],
            "RetryMaxAttempts" : row["retry_max_attempts"],
            "SMTPServerAddress" : row["smtp_server_addr"],
            "SMTPUserAccount" : row["smtp_server_user"],
            "SMTPUserPassword" : row["smtp_server_password"],
            "SMTPServerPort" : row["smtp_server_port"],
            "SMTPConnectionTimeout" : row["smtp_timeout"],
            "SMTPLegacySSL" : catocommon.is_true(row["smtp_ssl"]),
            "FromEmail" : row["from_email"],
            "FromName" : row["from_name"],
            "AdminEmail" : row["admin_email"]
        }

    # scheduler
    sql = "select * from scheduler_settings where id = 1"
    row = db.select_row_dict(sql)
    
    settings["scheduler"] = {
            "Enabled" : catocommon.is_true(row["mode_off_on"]),
            "LoopDelay" : row["loop_delay_sec"],
            "ScheduleMinDepth" : row["schedule_min_depth"],
            "ScheduleMaxDays" : row["schedule_max_days"],
            "CleanAppRegistry" : row["clean_app_registry"]
        }

    # security
    sql = "select * from login_security_settings where id = 1"
    row = db.select_row_dict(sql)
    
    settings["security"] = {
            "PassMaxAge" : row["pass_max_age"],
            "PassMaxAttempts" : row["pass_max_attempts"],
            "PassMaxLength" : row["pass_max_length"],
            "PassMinLength" : row["pass_min_length"],
            "PassComplexity" : catocommon.is_true(row["pass_complexity"]),
            "PassAgeWarn" : row["pass_age_warn_days"],
            "PasswordHistory" : row["pass_history"],
            "PassRequireInitialChange" : catocommon.is_true(row["pass_require_initial_change"]),
            "AutoLockReset" : catocommon.is_true(row["auto_lock_reset"]),
            "LoginMessage" : row["login_message"],
            "AuthErrorMessage" : row["auth_error_message"],
            "NewUserMessage" : row["new_user_email_message"],
            "PageViewLogging" : catocommon.is_true(row["page_view_logging"]),
            "ReportViewLogging" : catocommon.is_true(row["report_view_logging"]),
            "AllowLogin" : catocommon.is_true(row["allow_login"])
        }

    sql = "update application_settings set settings_json = %s"
    db.exec_db(sql, (json.dumps(settings, indent=4)))


    
    
if __name__ == "__main__":
    args = None
    if sys.version_info < (2, 7):
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-u", "--user", help="Cato root db user.")
        parser.add_option("-p", "--password", help="Cato root db password.")
         
        (args, arglist) = parser.parse_args()
    else:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("-u", "--user", help="Cato root db user.")
        parser.add_argument("-p", "--password", help="Cato root db password.")
        args = parser.parse_args()
        
    if not args:
        raise Exception("Unable to continue - unable to parse command line arguments.")

    UID = args.user
    PWD = args.password if args.password else ""

    db = catodb.Db()
    db.connect_db(user=UID, password=PWD, server=catoconfig.CONFIG["server"], port=catoconfig.CONFIG["port"],
        database=catoconfig.CONFIG["database"])
    
    main(sys.argv[1:])
    db.close()

