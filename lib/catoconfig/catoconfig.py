
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
    THIS is the class responsible for reading cato.conf
    and holding the config information in a global.
    
    ALL Cato modules import this file.
    
    In addition to the complete CONFIG dictionary, some commonly used
    properties are defined as separate globals to make referencing easier.
"""

import os.path
from catocryptpy import catocryptpy

# ALL Cato modules import this, and it should be one of the first imports.

#this file has a global 'config' that gets populated automatically.
# it's populated below the function definition
CONFIG = {}

VERSION = "UNKNOWN"
BASEPATH = ""

def _get_base_path():
    # this library file will always be in basepath/lib/catocommon
    # so we will take off two directories and that will be the base_path
    # this function should only be called from catocommon
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
def read_config():
    filename = os.path.join(BASEPATH, "conf/cato.conf")        
    if not os.path.isfile(filename):
        msg = "The configuration file " + filename + " does not exist."
        raise Exception(msg)
    try:
        fp = open(filename, 'r')
    except IOError as (errno, strerror):
        msg = "Error opening file " + filename + " " + format(errno, strerror)
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
    un_key = catocryptpy.decrypt_string(enc_key, "")
    key_vals["key"] = un_key
    un_pass = catocryptpy.decrypt_string(enc_pass, un_key)
    key_vals["password"] = un_pass
    
    # something else here... 
    # the root cato directory should have a VERSION file.
    # read it's value into a config setting
    verfilename = os.path.join(BASEPATH, "VERSION")
    if os.path.isfile(verfilename):
        with open(verfilename, "r") as version_file:
            ver = version_file.read()
            key_vals["version"] = ver
    else:
        raise Exception("Info: VERSION file does not exist.", 0)
 
    return key_vals


BASEPATH = _get_base_path()
CONFIG = read_config()
VERSION = CONFIG["version"] if CONFIG.has_key("version") else "NOT SET"
