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
            ["1.16", [                  
                      ["createtable", "dep_template_category", """(`category_id` VARCHAR(36) NOT NULL ,
                                                            `category_name` VARCHAR(32) NOT NULL ,
                                                            `icon` MEDIUMBLOB NULL ,
                                                            UNIQUE INDEX `category_name_UNIQUE` (`category_name` ASC) ,
                                                            PRIMARY KEY (`category_id`) )"""],
                     ["addcolumn", "deployment_template", "icon", "MEDIUMBLOB NULL"],
                     ["addcolumn", "deployment_template", "categories", "varchar(1024) NULL"],
                     ["addcolumn", "deployment_template", "svc_count", "int(11) NULL DEFAULT 0"],
                     ["addcolumn", "deployment_template", "available", "int(11) NULL DEFAULT 0"],
                     
                     ["dropcolumn", "deployment", "grouping"],
                     
                     ["addcolumn", "deployment_step_service", "original_task_id", "varchar(36)"],
                     ["addcolumn", "deployment_step_service", "task_version", "decimal(18,3)"],
                     ["addcolumn", "deployment_step_service", "run_level", "int(11)"],
                     ["dropcolumn", "deployment_step_service", "initial_state"],
                     
                     ["addcolumn", "deployment_service_inst", "run_level", "int(11)"],
                     
                     ["dropcolumn", "deployment_service_inst", "desired_state"],
                     ["dropcolumn", "deployment_service_inst", "task_instance"],
                     
                     ["dropcolumn", "deployment_log", "state"],
                     ["dropcolumn", "deployment_log", "next_state"],
                     
                     ["dropcolumn", "dep_seq_inst_tran", "state"],
                     ["dropcolumn", "dep_seq_inst_tran", "next_state"],
                     
                     ["dropcolumn", "dep_seq_inst_step_svc", "state"],
                     ["dropcolumn", "dep_seq_inst_step_svc", "next_state"],
                     
                     ["dropcolumn", "dep_seq_tran_params", "state"],
                     ["dropcolumn", "dep_seq_tran_params", "next_state"],
                     
                     ["droptable", "dep_service_inst_params", "NO LONGER NEEDED WAS FOR MANUAL STATE TRANSITION"],

                     ["function", "_v16_updates"],
                     ]
             ],
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
             ]
        ]

import os
import sys
import argparse

base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catoconfig import catoconfig
from catodb import catodb

def main(argv):
    # now, lets go through each defined version, and apply the changes...
    for ver in versions:
        print "Validating Version %s..." % (ver[0])
        
        for item in ver[1]:
            tblexists = None
            colexists = None
            pkexists = None
            
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


def _v16_updates():
    # doing 'noexcep' updates here, so it won't fail if they already exist

    sql = "ALTER TABLE deployment ADD COLUMN `template_id` VARCHAR(36) NULL AFTER `deployment_name`"
    db.exec_db_noexcep(sql)

    sql = """update deployment d
        join deployment_template dt on d.template_name = dt.template_name 
            and d.template_version = dt.template_version
        set d.template_id = dt.template_id"""
    db.exec_db_noexcep(sql)
    
    sql = "ALTER TABLE deployment CHANGE COLUMN `template_id` `template_id` VARCHAR(36) NOT NULL"
    db.exec_db_noexcep(sql)

    # rename the old columns, but keep them for now as a backup in case something crashes
    sql = "ALTER TABLE deployment CHANGE COLUMN `template_name` `_template_name` VARCHAR(64) NULL"
    db.exec_db_noexcep(sql)
    sql = "ALTER TABLE deployment CHANGE COLUMN `template_version` `_template_version` VARCHAR(8) NULL"
    db.exec_db_noexcep(sql)

    # move task info from deployment_service_state to deployment_step_service
    sql = """update deployment_step_service dss
        join deployment_service_state dss2 
          on dss.deployment_service_id = dss2.deployment_service_id
            and dss.initial_state = dss2.state
            and dss.desired_state = dss2.next_state
        set dss.original_task_id = dss2.original_task_id, 
          dss.task_version = dss2.task_version,
          dss.run_level = dss2.run_level"""
    db.exec_db_noexcep(sql)
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="Cato root db user.")
    parser.add_argument("-p", "--password", help="Cato root db password.")
    args = parser.parse_args()
    UID = args.user
    PWD = args.password if args.password else ""

    db = catodb.Db()
    db.connect_db(user=UID, password=PWD, server=catoconfig.CONFIG["server"], port=catoconfig.CONFIG["port"],
        database=catoconfig.CONFIG["database"])
    
    main(sys.argv[1:])
    db.close()

