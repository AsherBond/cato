
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

# this file has a global 'config' that gets populated automatically.
# it's populated below the function definition
CONFIG = {}

def _get_base_path():
    # this library file will always be in basepath/lib/catocommon
    # so we will take off two directories and that will be the base_path
    # this function should only be called from catocommon
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
def read_config():
    """
    Will read the cato.conf file and populate the CONFIG dictionary with settings.
    
    In case of errors reading the file, and to simplify downstream code, 
    default values are defined here.
    """
    cfg = {}
    cfg["server"] = "localhost"
    cfg["database"] = "cato"
    cfg["port"] = "3306"
    cfg["dbUseSSL"] = "false"
    cfg["dbSqlLog"] = "false"
    cfg["dbLog"] = "true"
    cfg["dbConnectionTimeout"] = "15"
    cfg["dbConnectionRetries"] = "15"

    cfg["logfiles"] = "/var/log/cato"
    cfg["uicache"] = "/var/cato/ui"
    cfg["tmpdir"] = "/tmp"
    
    cfg["redirect_stdout"] = "false"
    cfg["write_http_logs"] = "false"
    
    cfg["ui_permissions"] = "true"
    cfg["ui_enable_tokenauth"] = "true"
    cfg["ui_token_lifespan"] = "30"
    
    cfg["admin_ui_hostname"] = "localhost"
    cfg["admin_ui_port"] = "8082"
    cfg["admin_ui_debug"] = "20"
    cfg["admin_ui_use_ssl"] = "false"
    
    cfg["user_ui_hostname"] = "localhost"
    cfg["user_ui_port"] = "8080"
    cfg["user_ui_debug"] = "20"
    cfg["user_ui_client_debug"] = "20"
    cfg["user_ui_enable_refresh"] = "true"
    cfg["user_ui_use_ssl"] = "false"
    
    cfg["rest_api_hostname"] = "localhost"
    cfg["rest_api_port"] = "4001"
    cfg["rest_api_debug"] = "20"
    cfg["rest_api_use_ssl"] = "false"
    cfg["rest_api_enable_tokenauth"] = "true"
    cfg["rest_api_token_lifespan"] = "30"
    
    cfg["dash_api_hostname"] = "localhost"
    cfg["dash_api_port"] = "4002"
    cfg["dash_api_debug"] = "20"
    cfg["dash_api_use_ssl"] = "false"
    cfg["dash_api_tmpdir"] = "/tmp"
    cfg["dash_api_post_index"] = "canvas/index/index-post.layout"
    cfg["dash_api_get_index"] = "canvas/index/index-get.layout"
    
    cfg["newsfeed_api_hostname"] = "localhost"
    cfg["newsfeed_api_port"] = "4004"
    cfg["newsfeed_api_debug"] = "20"
    cfg["newsfeed_api_use_ssl"] = "false"
    
    # extensions are name/value pairs, so the 'extensions' setting is actually a dictionary.
    cfg["extensions"] = {}

    
    if not os.path.isfile(CONFFILE):
        if not os.path.isfile(CONFFILE):
            msg = "CATO_CONFIG file [%s] not found." % (CONFFILE)
            raise Exception(msg)
    try:
        fp = open(CONFFILE, 'r')
    except IOError as (errno, strerror):
        msg = "Error opening file [%s] %s" % (CONFFILE, format(errno, strerror))
        raise IOError(msg)
    
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
            elif key == "mongodb.password":
                enc_mongo_pass = value
            elif key == "extensions":
                # extensions require a little parsing
                pairs = value.split(";")
                for p in pairs:
                    if ":" in p:
                        n, v = p.split(":")
                        if n and v:
                            cfg["extensions"][n.strip()] = v.strip()
            else:
                cfg[key] = value

    un_key = catocryptpy.decrypt_string(enc_key, "")
    cfg["key"] = un_key
    un_pass = catocryptpy.decrypt_string(enc_pass, un_key)
    cfg["password"] = un_pass
    un_mongo_pass = catocryptpy.decrypt_string(enc_mongo_pass, un_key) if enc_mongo_pass else ""
    cfg["mongodb.password"] = un_mongo_pass
    

    # these aren't direct settings, rather derived from other settings
    cfg["admin_ui_protocol"] = "https" if cfg["admin_ui_use_ssl"] == "true" else "http"
    cfg["user_ui_protocol"] = "https" if cfg["user_ui_use_ssl"] == "true" else "http"
    cfg["rest_api_protocol"] = "https" if cfg["rest_api_use_ssl"] == "true" else "http"
    cfg["dash_api_protocol"] = "https" if cfg["dash_api_use_ssl"] == "true" else "http"
    cfg["newsfeed_api_protocol"] = "https" if cfg["newsfeed_api_use_ssl"] == "true" else "http"
    
    cfg["admin_ui_url"] = "%s://%s:%s" % (cfg["admin_ui_protocol"], cfg["admin_ui_hostname"], cfg["admin_ui_port"])
    cfg["user_ui_url"] = "%s://%s:%s" % (cfg["user_ui_protocol"], cfg["user_ui_hostname"], cfg["user_ui_port"])
    cfg["rest_api_url"] = "%s://%s:%s" % (cfg["rest_api_protocol"], cfg["rest_api_hostname"], cfg["rest_api_port"])
    cfg["dash_api_url"] = "%s://%s:%s" % (cfg["dash_api_protocol"], cfg["dash_api_hostname"], cfg["dash_api_port"])
    cfg["newsfeed_api_url"] = "%s://%s:%s" % (cfg["newsfeed_api_protocol"], cfg["newsfeed_api_hostname"], cfg["newsfeed_api_port"])
    
    # something else here... 
    # the root cato directory should have a VERSION file.
    # read it's value into a config setting
    verfilename = os.path.join(BASEPATH, "VERSION")
    if os.path.isfile(verfilename):
        with open(verfilename, "r") as version_file:
            ver = version_file.read()
            cfg["version"] = ver.strip()
    else:
        raise Exception("Info: VERSION file does not exist.", 0)
 
    return cfg

def safe_config():
    """
    The safe config is a small set of config settings allowed to be published
    to the web and API clients if requested.
    """
    cfg = {}
    cfg["version"] = CONFIG.get("version", "NOT SET")
    cfg["database"] = CONFIG.get("server", "Unknown")
    cfg["user_ui_enable_refresh"] = CONFIG["user_ui_enable_refresh"]

    cfg["admin_ui_url"] = CONFIG["admin_ui_url"]
    cfg["user_ui_url"] = CONFIG["user_ui_url"]
    cfg["rest_api_url"] = CONFIG["rest_api_url"]
    cfg["dash_api_url"] = CONFIG["dash_api_url"]
    cfg["newsfeed_api_url"] = CONFIG["newsfeed_api_url"]

    cfg["admin_ui_port"] = CONFIG["admin_ui_port"]
    cfg["user_ui_port"] = CONFIG["user_ui_port"]
    cfg["rest_api_port"] = CONFIG["rest_api_port"]
    cfg["dash_api_port"] = CONFIG["dash_api_port"]
    cfg["newsfeed_api_port"] = CONFIG["newsfeed_api_port"]

    cfg["admin_ui_protocol"] = "https" if CONFIG["admin_ui_use_ssl"] == "true" else "http"
    cfg["user_ui_protocol"] = "https" if CONFIG["user_ui_use_ssl"] == "true" else "http"
    cfg["rest_api_protocol"] = "https" if CONFIG["rest_api_use_ssl"] == "true" else "http"
    cfg["dash_api_protocol"] = "https" if CONFIG["dash_api_use_ssl"] == "true" else "http"
    cfg["newsfeed_api_protocol"] = "https" if CONFIG["newsfeed_api_use_ssl"] == "true" else "http"

    return cfg


# if not os.environ.get("CATO_CONFIG"):
#    print "CATO_CONFIG environment variable not set - trying default..."

CONFFILE = os.environ.get("CATO_CONFIG", os.path.join(os.sep, "etc", "cato", "cato.conf"))
CONFDIR = os.path.split(CONFFILE)[0]
BASEPATH = _get_base_path()
CONFIG = read_config()
SAFECONFIG = safe_config()
VERSION = CONFIG.get("version", "NOT SET")

