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

import os.path
import sys
from catocryptpy import catocryptpy
import time
import threading
import uuid
from catodb import catodb

# anything including catocommon can get new connections using the settings in 'config'
def new_conn():
    newdb = catodb.Db()
    newdb.connect_db(server=config["server"], port=config["port"], 
        user=config["user"], password=config["password"], database=config["database"])
    return newdb

# this common function will use the encryption key in the config, and DECRYPT the input
def cato_decrypt(encrypted):
    if encrypted:
        return catocryptpy.decrypt_string(encrypted,config["key"])
    else:
        return encrypted
# this common function will use the encryption key in the config, and ENCRYPT the input
def cato_encrypt(s):
    if s:
        return catocryptpy.encrypt_string(s,config["key"])
    else:
        return ""
def get_base_path():
    # try recursion up the abspath looking for 'cato'
    base_path = ""
    dirs = os.path.abspath(sys.argv[0]).split("/")
    path = []
    for d in dirs:
        path.append(d)
        if d == 'cato':
            base_path = "/".join(path)
            break

    return base_path
    
def read_config():
    base_path = get_base_path()

    filename = os.path.join(base_path, "conf/cato.conf")        
    if not os.path.isfile(filename):
        msg = "The configuration file "+ filename +" does not exist."
        raise Exception(msg)
    try:
        fp = open(filename, 'r')
    except IOError as (errno, strerror):
        msg = "Error opening file " + filename +" "+ format(errno, strerror)
        raise IOError(msg)
    
    key_vals = {}
    contents = fp.read().splitlines()
    fp.close
    enc_key = ""
    enc_pass = ""
    for line in contents:
        line = line.strip()
        if len(line) > 0 and not line.startswith("#"):
            row = line.split()
            key = row[0].lower()
            if len(row) > 1:
                value = row[1]
            else:
                value = ""

            if key == "key":
                if not value:
                    raise Exception("ERROR: cato.conf 'key' setting is required.")
                enc_key = value
            elif key == "password":
                if not value:
                    raise Exception("ERROR: cato.conf 'password' setting is required.")
                enc_pass = value
            else:
                key_vals[key] = value
    un_key = catocryptpy.decrypt_string(enc_key,"")
    key_vals["key"] = un_key
    un_pass = catocryptpy.decrypt_string(enc_pass,un_key)
    key_vals["password"] = un_pass
    
    # something else here... 
    # the root cato directory should have a VERSION file.
    # read it's value into a config setting
    verfilename = os.path.join(base_path, "VERSION")
    if os.path.isfile(verfilename):
        with open(verfilename, "r") as version_file:
            ver = version_file.read()
            key_vals["version"] = ver
    else:
        print("Info: VERSION file does not exist.")
    
    
    
    return key_vals

def new_guid():
    return str(uuid.uuid1())

def generate_password():
    import string
    from random import choice
    chars = string.letters + string.digits
    length = 12
    return "".join(choice(chars) for _ in range(length))

def is_true(var):
    # not just regular python truth testing - certain string values are also "true"
    # but false if the string has length but isn't a "true" statement
    # since any object could be passed here (we only want bools, ints or strs)
    # we just cast it to a str
    
    # JUST BE AWARE, this isn't standard python truth testing.
    # So, "foo" will be false... where if "foo" would be true in pure python
    s = str(var).lower()
    if len(s) > 0:
        if str(var).lower() in "true,yes,on,enable,enabled":
            return True
        else:
            # let's see if it was a number, in which case we can just test it
            try:
                i = int(s)
                if i > 0:
                    return True
            except Exception:
                """no exception, it just wasn't parseable into an int"""
    return False

def tick_slash(s):
    """ Prepares string values for string concatenation, or insertion into MySql. """
    if s is not None:
        return s.replace("'", "''").replace("\\", "\\\\").replace("%", "%%")
    
    return ""

#this file has a global 'config' that gets populated automatically.
config = read_config()

class CatoProcess():
    def __init__(self, process_name):
        # the following line does not work for a service started in the 
        # background. Hardcoding to root until a fix is found
        #self.host_domain = os.getlogin() +'@'+ os.uname()[1]
        self.host_domain = 'root@'+ os.uname()[1]
        self.host = os.uname()[1]
        self.platform = os.uname()[0]
        # the following line does not work for a service started in the 
        # background. Hardcoding to root until a fix is found
        #self.host_domain = os.getlogin() +'@'+ os.uname()[1]
        #self.user = os.getlogin()
        self.user = 'root'
        self.my_pid = os.getpid()
        self.process_name = process_name
        self.initialize_logfile()
        self.home = get_base_path()

    def initialize_logfile(self):
        base_path = get_base_path()
        # logfiles go where defined in cato.conf, but in the base_path if not defined
        self.logfiles_path = (config["logfiles"] if config["logfiles"] else os.path.join(base_path, "logfiles"))
        self.logfile_name = os.path.join(self.logfiles_path,  self.process_name.lower()+".log")

        #stdout/stderr brute force interception can be optionally overridden.
        if config.has_key("redirect_stdout"):
            if config["redirect_stdout"] == "false":
                # we'll just return before it can get redirected
                return

        sys.stderr = open(self.logfile_name, 'a', 1)
        sys.stdout = open(self.logfile_name, 'a', 1)

    def output(self,*args):
        output_string = time.strftime("%Y-%m-%d %H:%M:%S ") + "".join(str(s) for s in args) + "\n"

        #if we're not redirecting stdout, all messages that come through here get sent there too
        if config.has_key("redirect_stdout"):
            if config["redirect_stdout"] == "false":
                print(output_string[:-1])

        # the file is always written
        fp = open(self.logfile_name, 'a')
        fp.write(output_string)
        fp.close

    def startup(self):
        self.output("####################################### Starting up ", 
            self.process_name, 
            " #######################################")
        self.db = catodb.Db()
        conn = self.db.connect_db(server=config["server"], port=config["port"], 
            user=config["user"], 
            password=config["password"], database=config["database"])
        self.config = config


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
        sql = "select id from tv_application_registry where app_name = '"+self.process_name+ \
            "' and app_instance = '"+self.host_domain+"'"

        result = self.db.select_col(sql)
        if not result:
            self.output(self.process_name +" has not been registered, registering...")
            self.register_app()
            result = self.db.select_col(sql)
            self.instance_id = result
        else:
            self.output(self.process_name +" has already been registered, updating...")
            self.instance_id = result
            self.output("application instance = %d" % self.instance_id)
            self.db.exec_db("""update application_registry set hostname = %s, userid = %s,
                 pid = %s, platform = %s where id = %s""", 
                (self.host_domain, self.user, str(self.my_pid), self.platform,
                 self.instance_id))

    def register_app(self):
        self.output("Registering application...")

        sql = "insert into application_registry (app_name, app_instance, master, logfile_name, " \
            "hostname, userid, pid, platform) values ('"+self.process_name+ \
            "', '"+self.host_domain+"',1, '"+self.process_name.lower()+".log', \
            '"+self.host+"', '"+self.user+"',"+str(self.my_pid)+",'"+self.platform+"')"
        self.db.exec_db(sql)
        self.output("Application registered.")

    def heartbeat_loop(self, event):
        while True:
            event.wait(self.loop)
            if event.isSet():
                break
            self.update_heartbeat()

    def update_heartbeat(self):
        sql = "update application_registry set heartbeat = now() where id = %s"
        self.db_heart.exec_db(sql,(self.instance_id))

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

    def end(self):
        self.heartbeat_event.set()
        self.heartbeat_thread.join()
        self.db.close()

    def service_loop(self):
        while True:
            self.get_settings()
            self.main_process()
            time.sleep(self.loop)


