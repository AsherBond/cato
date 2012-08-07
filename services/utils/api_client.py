#!/usr/bin/env python

import os
import sys
import json
import urllib
import urllib2
from datetime import datetime
import hashlib
import base64
import hmac
import argparse

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catocommon import catocommon

parser = argparse.ArgumentParser(description='Connect to the Cato API.')
parser.add_argument('--host', help='The host url of the API service.')
parser.add_argument('--method', '-m', help='The method to call.')
parser.add_argument('--accesskey', '-k', help='The access key for the request.')
parser.add_argument('--secretkey', '-s', help='The secret key for the request.')
parser.add_argument('--file', '-f', type=argparse.FileType('r'), help='Method and arguments.')

cmdlineargs = parser.parse_args()
methodargs = json.loads(cmdlineargs.file.read())

# the command line overrides any similar values from the json file.
host = cmdlineargs.host if cmdlineargs.host else methodargs["host"]
access_key = cmdlineargs.accesskey if cmdlineargs.accesskey else methodargs["accesskey"]
secret_key = cmdlineargs.secretkey if cmdlineargs.secretkey else methodargs["secretkey"]
method = methodargs["method"]
args = methodargs["args"]

# Some API calls require one or more big arguments, too much to pass in
# the method file.  So, anything in the 'files' section of the method file is opened
# and added to the args dictionary using the key name provided.
# NOTE: file contents are always base64 encoded for HTTP...
# ... the receiving methods know which arguments to decode.

if methodargs["files"]:
    for k, v in methodargs["files"].items():
        with open(v, 'r') as f_in:
            if not f_in:
                print("Unable to open file [%s]." % v)
            data = f_in.read()
            if data:
                args[k] = catocommon.packData(data)


def http_get(url, timeout=10):
    try:
        if not url:
            return "URL not provided."
        
        print "Trying an HTTP GET to %s" % url

        # for now, just use the url directly
        try:
            response = urllib2.urlopen(url, None, timeout)
            result = response.read()
            if result:
                return result

        except urllib2.URLError as ex:
            if hasattr(ex, "reason"):
                print "HTTPGet: failed to reach a server."
                print ex.reason
                return ex.reason
            elif hasattr(ex, "code"):
                print "HTTPGet: The server couldn\'t fulfill the request."
                print ex.__str__()
                return ex.__str__()
        
        # if all was well, we won't get here.
        return "No results from request."
        
    except Exception as ex:
        raise ex

def call_api(host, method, key, pw, args):
    try:
        if not host:
            return "HOST not provided."
        if not method:
            return "METHOD not provided."
        if not key:
            return "KEY not provided."

        if host.endswith('/'):
            host = host[:-1]

        arglst = ["&%s=%s" % (k, v) for k, v in args.items()]
        argstr = "".join(arglst)
        
        #timestamp
        ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        ts = ts.replace(":", "%3A")
        
        string_to_sign = "{0}?key={1}&timestamp={2}".format(method, key, ts)
        
        sig = base64.b64encode(hmac.new(pw, msg=string_to_sign, digestmod=hashlib.sha256).digest())
        sig = "&signature=" + urllib.quote_plus(sig)
        
        url = "%s/%s%s%s" % (host, string_to_sign, sig, argstr)
        print url

        return http_get(url)
    except Exception as ex:
        raise ex



# make the call
result = call_api(host, method, access_key, secret_key, args)

print result
