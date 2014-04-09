#########################################################################
# Copyright 2014 Cloud Sidekick
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
import json
from catotaskengine import classes
try:
    from digocn import digocn
except ImportError as e:
    msg = "Digital Ocean commands missing Python library digocn. \
            See http://docs.cloudsidekick.com/docs/cato/?cloud/digocn.html for instructions on \
            installing the digocn package on the Cato Task Engine server.\n%s" % (e)
    raise Exception(msg)
except Exception as e:
    raise Exception(e)

def digocn_connect(TE):

    cloud_name = "digital-ocean"
    try:
        cloud = TE.cloud_conns[cloud_name]
    except KeyError as ex:
        cloud = classes.Cloud(cloud_name)
        TE.cloud_conns[cloud_name] = cloud

    if not cloud.conn:
        cloud.conn = digocn.DigOcnConn(TE.cloud_login_id, TE.cloud_login_password, debug=False)

    return cloud

def digocn_call(te, step):

    noun, action, subject, status, message, results = te.get_command_params(step.command, "noun", "action",
        "subject", "status", "message", "results")[:]
    noun = te.replace_variables(noun)
    action = te.replace_variables(action)
    subject = te.replace_variables(subject)
    status = te.replace_variables(status)
    message = te.replace_variables(message)
    results = te.replace_variables(results)
    params = te.get_node_list(step.command, "params/param", "name", "value")
    cloud = digocn_connect(te)
    params_dict = {}
    for n,v in params:
        n = te.replace_variables(n)
        v = te.replace_variables(v)
        params_dict[n] = v

    if not len(action):
        action = None
    if not len(subject):
        subject = None
    result = cloud.conn.call(noun, action, subject, params_dict)

    if len(status):
        s = result.get("status", "")
        te.rt.set(status, s)
    if len(message):
        m = result.get("message", "")
        te.rt.set(message, m)
    if len(results):
        r = json.dumps(result)
        #r = result
        te.rt.set(results, r)

    msg = "Digital Ocean API Call\n%s" % (result)
    te.insert_audit(step.function_name, msg, "")
    #if len(out_var):
    #    te.rt.set(out_var, result)
