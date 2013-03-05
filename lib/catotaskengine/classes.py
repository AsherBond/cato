########################################################################/
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

from catocommon import catocommon

class Step:
    def __init__(self, step_id, function_name, function_xml, parse_method, row_delimiter, col_delimiter):
        self.step_id = step_id
        self.function_name = function_name
        self.command = function_xml
        self.parse_method = parse_method
        self.row_delimiter = row_delimiter
        self.col_delimiter = col_delimiter

class Codeblock: 

    def __init__(self, task_id, codeblock_name):
        self.task_id = task_id
        self.codeblock_name = codeblock_name
        self.step_list = []
        self.get_steps()

    def add_step(self, step):

        self.step_list.append(step)

    def get_steps(self):

        sql = """select lower(step_id), function_name, function_xml
            , ExtractValue(function_xml, 'function/@parse_method') as parse_method
            , ExtractValue(function_xml, 'function/@row_delimiter') as row_delimiter
            , ExtractValue(function_xml, 'function/@col_delimiter') as col_delimiter
        from task_step 
        where task_id = %s and codeblock_name = %s
            and commented = 0
        order by step_order asc"""

        db = catocommon.new_conn()
        rows = db.select_all(sql, (self.task_id, self.codeblock_name))
        db.close()
        if rows:
            for row in rows:
                step_id, function_name, function_xml, parse_method, row_del, col_del = row[:]
                self.add_step(Step(step_id, function_name, function_xml, parse_method, row_del, col_del))

class Task:

    def __init__(self, task_id):

        self.task_id = task_id
        self.codeblocks = {}
        self.get_codeblocks()

    def get_codeblocks(self): 

        sql = """select distinct upper(codeblock_name) from task_codeblock
                where task_id = %s"""
        db = catocommon.new_conn()
        rows = db.select_all(sql, (self.task_id))
        db.close()
        if rows:
            for row in rows:
                cb_name = row[0]
                self.codeblocks[cb_name] = Codeblock(self.task_id, cb_name)


class Asset:

    def __init__(self, asset_id):

        self.asset_id = asset_id
        self.name = None
        self.address = None
        self.port = None
        self.db_name = None
        self.conn_type = None
        self.userid = None
        self.password = None
        self.priv_password = None
        self.domain = None
        self.conn_string = None
        self.private_key = None
        self.private_key_name = None

    def get(self):
        
        db = catocommon.new_conn()
        sql = """select a.asset_name, a.address, a.port, a.db_name , a.connection_type, ac.username, 
                ac.password, ac.domain, ac.privileged_password, a.conn_string 
            from asset a left outer join asset_credential ac on a.credential_id = ac.credential_id
            where asset_id = %s"""
        row = db.select_row(sql, (self.asset_id))
        db.close()
        if len(row) == 0:
            raise Exception("An Asset record for the asset id %s does not exist" % (self.asset_id))

        self.name, self.address, self.port, self.db_name, self.conn_type, self.userid, password, priv_password, \
            self.domain, self.conn_string, self.private_key, self.private_key_name = row[:]

        if len(password):
            self.password = catocommon.cato_decrypt(password)
        if len(priv_password):
            self.priv_password = catocommon.cato_decrypt(priv_password)
        
class System:
    def __init__(self, name, address=None, port=None, db_name=None, conn_type=None, userid=None,
        password=None, p_password=None, domain=None, conn_string=None, private_key=None,
        private_key_name=None, cloud_name=None, protocol=None):

        self.name = name
        self.address = address
        self.port = port
        self.db_name = db_name
        self.conn_type = conn_type
        self.userid = userid
        self.password = password
        self.p_password = p_password
        self.domain = domain
        self.conn_string = conn_string
        self.private_key = private_key
        self.private_key_name = private_key_name
        self.cloud_name = cloud_name
        self.protocol = protocol


class Connection:
    def __init__(self, conn_name, conn_type=None, system=None):

        self.conn_name = conn_name
        self.conn_handle = None
        self.conn_type = conn_type
        self.system = system


class TaskHandle:
    def __init__(self):
        self.instance = None
        self.handle_name = None
        self.task_id = None
        self.submitted_by = None
        self.task_name = None
        self.task_version = None
        self.default_version = None
        self.submitted_dt = None
        self.status = None
        self.started_dt = None
        self.completed_dt = None
        self.cenode = None
        self.pid = None
        self.asset = None
        self.asset_name = None
        self.is_default = None


class Cloud:
    def __init__(self, cloud_name):
        self.cloud_id = None
        self.cloud_name = cloud_name
        self.url = None
        self.protocol = None
        self.region = None
        self.provider = None
        self.default_account = None
        self.path = "/"
    
        db = catocommon.new_conn()
        sql = """select cloud_id, provider, api_url, api_protocol, default_account_id, region
            from clouds where cloud_name = %s"""
        row = db.select_row(sql, (cloud_name))
        db.close()
        if not row:
            msg = "The cloud endpoint name %s is not configured in the Cato database" % cloud_name
            raise Exception(msg) 

        self.cloud_id, self.provider, self.url, self.protocol, self.default_account, self.region = row[:]
        self.cloud_name = cloud_name

        if self.provider == "Amazon AWS":
            self.url = None
        elif self.provider == "Eucalyptus":
            self.path = "/services/Eucalyptus/"
        

    def connect(self, uid, pwd):
        # from vmware.vsphere import Server
        from catosphere import Server
        self.server = Server()
        self.server.connect(url=self.url, username=uid, password=pwd)

