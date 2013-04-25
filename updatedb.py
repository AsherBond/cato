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
        addcolumn - table, column, options
        modifycolumn - table, column, options
        dropcolumn - table, column
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
            [
             "1.13", [
                    ["addcolumn", "action_plan", "cloud_id", "varchar(36) DEFAULT NULL"],
                    ["addcolumn", "action_plan_history", "cloud_id", "varchar(36) DEFAULT NULL"],
                    ["addcolumn", "action_schedule", "cloud_id", "varchar(36) DEFAULT NULL"],
                    ["addcolumn", "task_instance", "cloud_id", "varchar(36) DEFAULT NULL"],
                    ["droptable", "ecosystem"],
                    ["droptable", "ecosystem_log"],
                    ["droptable", "ecosystem_object"],
                    ["droptable", "ecosystem_output"],
                    ["droptable", "ecosystem_object_tag"],
                    ["droptable", "ecotemplate"],
                    ["droptable", "ecotemplate_action"],
                    ["droptable", "ecotemplate_runlist"],
                    ["droptable", "image"],
                    ["droptable", "request"],
                    ["droptable", "request_action"],
                    ["function", "_v13_updates"]
                    ]
             ],
            [
             "1.14", [
                    ["addcolumn", "deployment", "options", "text"],
                    ["addcolumn", "deployment_service", "options", "text"]
                    ]
             ],
            [
             "1.15", [
                    ["addcolumn", "task_instance", "schedule_id", "varchar(36) DEFAULT NULL"],
                    ["addcolumn", "dep_action_inst", "instance_id", "varchar(36) DEFAULT NULL"],
                    ["addcolumn", "deployment_service_inst", "instance_num", "int(11) DEFAULT NULL"]
                    ]
             ]
            ]

#                    ["sql", "update deployment set options = '' where archive is null"],
#                    ["sql", """update deployment_service set options = '' where deployment_id in (
#                        select deployment_id from deployment where archive is null)"""]
#                    ]

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
    
            # these apply to several cases below
            if item[0] in ["addcolumn", "dropcolumn", "modifycolumn"]:        
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
    
            sql = ""
            if item[0] == "droptable":
                if tblexists:
                    print "    executing %s" % (item)
                    sql = "drop table `%s`" % (item[1])
            elif item[0] == "addcolumn":
                if not colexists:
                    print "    executing %s" % (item)
                    sql = "alter table `%s` add column `%s` %s" % (item[1], item[2], item[3])
            elif item[0] == "modifycolumn":
                if colexists:
                    print "    executing %s" % (item)
                    sql = "alter table `%s` modify column `%s` %s" % (item[1], item[2], item[3])
            elif item[0] == "dropcolumn":
                if colexists:
                    print "    executing %s" % (item)
                    sql = "alter table `%s` drop column `%s`" % (item[1], item[2])
            elif item[0] == "sql":
                if len(item) > 1 and item[1]:
                    print "    executing %s" % (item)
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
                db.exec_db(sql)
                

        print "    .... done."


def _v13_updates():
    # doing 'noexcep' updates here, so it won't fail if they already exist
    sql = "alter table application_registry ADD KEY `app_name` (`app_name`)"
    db.exec_db_noexcep(sql)
    sql = "alter table clouds drop key `cloud_provider_UNIQUE`, add unique key `CLOUD_NAME` (`cloud_name`)"
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

