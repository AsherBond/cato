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

JENKINS_CONNS = {}

def jenkins_new_connection(TE, step):

    url, user, password, conn_name = TE.get_command_params(step.command, "url", "user", "password", "conn_name")[:]

    url = TE.replace_variables(url)
    user = TE.replace_variables(user)
    password = TE.replace_variables(password)
    conn_name = TE.replace_variables(conn_name)

    if not len(url):
        msg = "Jenkins Create Connection command requires a url"
        raise Exception(msg)
    if not len(conn_name):
        msg = "Jenkins Create Connection command requires a connection name"
        raise Exception(msg)

    if not len(user):
        user = None
    if not len(password):
        password = None

    try:
        j = Jenkins(url, user, password)
    except Exception as e:
        TE.logger.critical(e)
        if "<title>Error 404 Not Found</title>" in str(e.message):
            msg = "Problem attempting to access Jenkins server. Check the Jenkins URL: %s.\nDoes the url have the proper prefix?" % (url)
            raise Exception(msg)
        elif "Operation timed out" in str(e.message):
            msg = "Timeout attempting to access Jenkins server. Check the Jenkins URL: %s.\nCheck the address, port and protocol." % (url)
            raise Exception(msg)
        elif "Connection refused" in str(e.message):
            msg = "Problem attempting to access Jenkins server, connection refused. Check the Jenkins URL: %s.\nCheck the address, port and protocol." % (url)
            raise Exception(msg)
        elif "unknown protocol" in str(e.message):
            msg = "Problem attempting to access Jenkins server, unknown protocol. Check the Jenkins URL: %s.\nCheck the address, port and protocol." % (url)
            raise Exception(msg)
        elif "<title>Error 401 Bad credentials</title>" in str(e.message):
            msg = "Wrong credentials attempting to login to the Jenkins server. Check the user id and password for user: %s." % (user)
            raise Exception(msg)
        else:
            raise Exception(e)

    JENKINS_CONNS[conn_name] = j

    msg = "Creating a Jenkins connection to url %s, user %s" % (url, user)
    TE.insert_audit("jenkins_new_connection", msg, "")

def jenkins_build_status(TE, step):

    conn_name, job, build_num, status_var = TE.get_command_params(step.command, "conn_name", "job", "build_num", "status_var")[:]

    conn_name = TE.replace_variables(conn_name)
    job = TE.replace_variables(job)
    build_num = TE.replace_variables(build_num)
    status_var = TE.replace_variables(status_var)

    if not len(build_num):
        msg = "Jenkins Get Build Status command requires a Build Number"
        raise Exception(msg)
    else:
        build_num = int(build_num)
    if not len(job):
        msg = "Jenkins Get Build Status command requires a Job Name"
        raise Exception(msg)
    if not len(conn_name):
        msg = "Jenkins Get Build Status command requires a connection name"
        raise Exception(msg)

    try:
        conn = JENKINS_CONNS[conn_name]
    except KeyError:
        msg = "A Jenkins connection by the name of %s does not exist." % (conn_name)
        raise Exception(msg)
    try:
        j = conn[job]
    except KeyError as e:
        msg = "The Jenkins job %s does not exist on the server" % (job)
        raise Exception(msg)
    except Exception as e:
        raise Exception(e)

    try:
        b = j.get_build(build_num)
    except KeyError as e:
        msg = "The build number %s for Jenkins job %s does not exist" % (build_num, job)
        raise Exception(msg)
    except Exception as e:
        raise Exception(e)

    status = b.get_status()
    if not status:
        status = "UNKNOWN"

    msg = "Jenkins Job %s, build number %s has a status of %s" % (job, build_num, status)
    TE.insert_audit("jenkins_build_status", msg, "")

    if len(status_var):
        TE.rt.set(status_var, status)

def jenkins_build(TE, step):

    conn_name, job, build_var = TE.get_command_params(step.command, "conn_name", "job", "build_var")[:]
    pairs = TE.get_node_list(step.command, "parameters/parameter", "name", "value")

    conn_name = TE.replace_variables(conn_name)
    job = TE.replace_variables(job)
    build_var = TE.replace_variables(build_var)

    if not len(conn_name):
        msg = "Jenkins Build Job command requires a connection name"
        raise Exception(msg)
    if not len(job):
        msg = "Jenkins Build Job command requires a job"
        raise Exception(msg)

    params = {}
    for p in pairs:
        name = TE.replace_variables(p[0])
        if len(name):
            value = TE.replace_variables(p[1])
            params[name] = value

    msg = "Attempting to start Jenkins Job %s \nparameters = %s\n please wait ..." % (job, params)
    TE.insert_audit("jenkins_build", msg, "")

    try:
        j = JENKINS_CONNS[conn_name]
    except KeyError:
        msg = "A Jenkins connection by the name of %s does not exist." % (conn_name)
        raise Exception(msg)

    try:
        i = j[job].invoke(build_params=params)
    except UnknownJob:
        msg = "The Jenkins job named %s does not exist on this Jenkins server" % (job)
        raise Exception(msg)
    except Exception as e:
        TE.logger.critical(e)
        if "Operation failed" in str(e.message):
            msg = """Attempting to start the Jenkins job %s failed. Possible causes:
                    - calling a job with parameters when the job is not defined for parameters
                    - calling a job without parameters when the job is defined with parameters""" % (job)
            raise Exception(msg)
        else:
            raise Exception(e)

    i.block_until_not_queued(timeout=1200, delay=3)
    if len(build_var):
        n = i.get_build_number()
        TE.rt.set(build_var, n)

    msg = "Jenkins Job %s started with build number %s" % (job, n)
    TE.insert_audit("jenkins_build", msg, "")

