#!/usr/bin/env python

import urllib
import urllib2
from datetime import datetime
import hashlib
import base64
import hmac
import argparse

parser = argparse.ArgumentParser(description='Connect to the Cato API.')
parser.add_argument('--host', required=True, help='The host url of the API service.')
parser.add_argument('--method', '-m', required=True, help='The method to call.')
parser.add_argument('--accesskey', '-k', required=True, help='The access key for the request.')
parser.add_argument('--secretkey', '-s', required=True, help='The secret key for the request.')
#parser.add_argument('--args', '-a', required=True, help='Arguments.')

cmdlineargs = parser.parse_args()
#print args


#provide the args
args = {}
args["filter"] = "qwer"
args["foo"] = "bar"



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



# set the key
access_key=cmdlineargs.accesskey
secret_key=cmdlineargs.secretkey
    
# make the call
result = call_api("http://localhost:8080/", "ecoMethods/list_ecosystems", access_key, secret_key, args)


#result = http_get("http://localhost:8080/ecoMethods/create_ecosystem?key=12:34:56:78:90&name=textes&description=bar&ecotemplate_id=1bad276d-c832-4b42-b895-18681166c238&account_id=856fa6f4-e36e-4029-b436-65dfeb06a36d")
#result = http_get("http://localhost:8080/ecoMethods/list_ecosystems?key=12:34:56:78:90&filter=qwer")

print result
