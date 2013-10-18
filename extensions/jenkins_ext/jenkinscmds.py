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

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.custom_exceptions import UnknownJob

def jenkins_build(TE, step):

    url, user, password, job, build_var, token = TE.get_command_params(step.command, "url", "user", "password", "job", "build_var", "token")[:]
    pairs = TE.get_node_list(step.command, "parameters/parameter", "name", "value")

    url = TE.replace_variables(url)
    user = TE.replace_variables(user)
    password = TE.replace_variables(password)
    job = TE.replace_variables(job)
    build_var = TE.replace_variables(build_var)
    token = TE.replace_variables(token)

    params = {}
    for p in pairs:
        name = TE.replace_variables(p[0])
        if len(name):
            value = TE.replace_variables(p[1])
            params[name] = value
    print "token is %s" % token

    msg = "Attempting to start Jenkins Job %s at address %s with user %s\nparameters = %s\n please wait ..." % (job, url, user, params)
    TE.insert_audit("jenkins_build", msg, "")

    if not len(user):
        user = None
    if not len(password):
        password = None
    if not len(token):
        token = None

    j = Jenkins(url, user, password)

    try:
        i = j[job].invoke(securitytoken=token, build_params=params)
    except UnknownJob:
        msg = "The Jenkins job named %s does not exist" % (job)
        raise Exception(msg)
    except Exception as e:
            raise Exception(e)

    i.block_until_not_queued(timeout=120, delay=3)
    if len(build_var):
        n = i.get_build_number()
        TE.rt.set(build_var, n)

    msg = "Jenkins Job %s started with build number %s" % (job, n)
    TE.insert_audit("jenkins_build", msg, "")

