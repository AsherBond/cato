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
from Tkinter import Tcl

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catocommon import catocommon

class Ecosync(catocommon.CatoService):

    ecosync_mode = ""

    def check_instance(self, conn, id):
        res = conn.get_all_instances([id])
        if res:
            instance = res[0][0]
            if instance.state not in ["pending", "running", "shutting-down", "stopping", "stopped"]:
                ret_code = 0
            else:
                ret_code = 1
        else:
            ret_code = 0

        return ret_code


    def delete_eco_object(self, acc_id, obj_type, obj_id, cloud_id):

        self.output("Deleting $object_id of type $object_type from account id $account_id and cloud id $cloud_id" %
            (obj_id, obj_type, acc_id, cloud_id))

        sql = """delete eo from ecosystem_object eo join ecosystem e 
                where e.account_id = %s and eo.ecosystem_object_type = %s 
                and eo.ecosystem_object_id = %s and eo.cloud_id = %s"""
        self.db.exec_db(sql, (acc_id, obj_type, obj_id, cloud_id))


    def check_object(self, conn, obj_type, obj_id):

        if obj_type == "AWS::EC2::Instance":
            ret_code = self.check_instance(conn, obj_id)
        elif obj_type == "AWS::EC2::Volume":
            ret_code = self.check_volumes(conn, obj_id)
        elif obj_type == "AWS::S3::Bucket":
            ret_code = self.check_volumes(conn, obj_id)
        elif obj_type == "AWS::EC2::SecurityGroup":
            ret_code = self.check_volumes(conn, obj_id)
        elif obj_type == "AWS::EC2::EIP":
            ret_code = self.check_volumes(conn, obj_id)
        elif obj_type == "AWS::EC2::Volume":
            ret_code = self.check_volumes(conn, obj_id)
        elif obj_type == "AWS::EC2::Volume":
            ret_code = self.check_volumes(conn, obj_id)
        elif obj_type == "AWS::EC2::Volume":
            ret_code = self.check_volumes(conn, obj_id)
        elif obj_type == "AWS::EC2::Volume":
            ret_code = self.check_volumes(conn, obj_id)
        elif obj_type == "AWS::EC2::Volume":
            ret_code = self.check_volumes(conn, obj_id)
        elif obj_type == "AWS::EC2::Volume":
            ret_code = self.check_volumes(conn, obj_id)
        elif obj_type == "AWS::EC2::Volume":
            ret_code = self.check_volumes(conn, obj_id)
        elif obj_type == "AWS::EC2::Volume":
            ret_code = self.check_volumes(conn, obj_id)
        else:
            ret_code = 1
        return ret_code


    def get_cloud_objects(self): 

        sql = """select distinct do.ecosystem_object_id, do.ecosystem_object_type, do.cloud_id, e.account_id
                from ecosystem_object do join ecosystem e
                order by e.account_id"""

        old_account_id = ""
        rows = self.db.select_all(sql)
        if rows:
            for row in rows:
                object_id = row[0]
                obj_type = row[1]
                cloud_id = row[2]
                account_id = row[3]
                if old_account_id != account_id:
                    if conn:
                        del(conn)
                    conn = self.get_cloud_connection(account_id, cloud_id)
                    old_account_id = account_id

                if not self.check_object(conn, obj_type, object_id):
                    self.eco_object(account_id, obj_type, object_id, cloud_id)


    def get_settings(self):
        """
        ### ecosync has no settings table at the moment
        """


    def main_process(self):
        """main process loop, parent class will call this"""

        self.tcl.eval
        self.tcl.eval('main_process')


    def startup(self):

        catocommon.CatoService.startup(self)
        self.tcl = Tcl(useTk=False)
        #catocommon.CatoService.startup()
        self.tcl.setvar(name='::HOME', value=self.home)
        self.tcl.eval('source cato_ecosync.tcl')
        self.tcl.eval('initialize_process')

