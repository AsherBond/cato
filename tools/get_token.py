#!/usr/bin/env python

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



import urllib
import urllib2
import httplib
from datetime import datetime
import hashlib
import base64
import sys
import os
import hmac
import json
import time

### Change the following to meet your specific needs

HOST = "http://localhost:8081"
ACCESS_KEY = "catouser"
SECRET_KEY = "password"

if not HOST:
    raise Exception("HOST not provided.")
if not ACCESS_KEY:
    raise Exception("ACCESS_KEY not provided.")
if not SECRET_KEY:
    raise Exception("SECRET_KEY not provided.")


def prepare_args(args): 

    if args:
        arglst = ["&%s=%s" % (k, urllib.quote_plus(v)) for k, v in args.items()]
        argstr = "".join(arglst)
    else:
        argstr = ""
    return argstr

def get_url(method, argstr):

    #timestamp
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    ts = ts.replace(":", "%3A")

    #string to sign
    string_to_sign = "{0}?key={1}&timestamp={2}".format(method, ACCESS_KEY, ts)

    #encoded signature
    sig = base64.b64encode(hmac.new(str(SECRET_KEY), msg=string_to_sign, digestmod=hashlib.sha256).digest())
    sig = "&signature=" + urllib.quote_plus(sig)

    url = "%s/%s%s%s" % (HOST, string_to_sign, sig, argstr)
    return url


def issue_request(method, args):

    argstr = prepare_args(args)
    url = get_url(method, argstr)
    try:
        response = urllib2.urlopen(url, None, 10)
    except urllib2.HTTPError as e:
        msg = json.loads(e.read())
        error_msg = msg["ErrorCode"] + ": " + msg["ErrorDetail"] + " " + msg["ErrorMessage"]
        raise(Exception(error_msg))
    except urllib2.URLError as e:
        error_msg = "URLError = %s" % (str(e.reason))
        raise(Exception(error_msg))
    except httplib.HTTPException as e:
        error_msg = "HTTPException" % str(e)
        raise(Exception(error_msg))
    except Exception as e:
        raise(Exception(e))
    result = response.read()
    return result

def extract_value(response, keys):

    
    for k in keys:
        response = response[k]

    return response

def get_result(method, args, extract_keys):

    r = issue_request(method, args)
    s = json.loads(r)
    result = extract_value(s, extract_keys)
    return result

def get_response_result(method, args, extract_keys):

    extract_keys[:0] = ["Response"]
    return get_result(method, args, extract_keys)    

def run(method, args={}):


    args["output_format"] = "json"

    try:
        result = get_response_result(method, args, [])
    except Exception as e:
        print Exception(e)
        return False
    return result


if __name__ == '__main__':

    print run("get_token")
