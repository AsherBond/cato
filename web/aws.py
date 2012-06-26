
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

import urllib2
import time
import hmac
import hashlib
import base64
from catocloud import cloud
from uiCommon import HTTPGet

class awsInterface(object):
    def GetCloudObjectsAsXML(self, account_id, cloud_id, cloud_object_type, additional_args={}):
        try:
            sXML = ""

            ca = cloud.CloudAccount()
            ca.FromID(account_id)
            if ca.ID is None:
                msg =  "Failed to get Cloud Account details for Cloud Account ID [" + account_id + "]."
                print(msg)
                return None, msg

            if cloud_object_type is not None:
                # many reasons why we'd bail here.  Rather than a bunch of testing below, let's just crash
                # if a key field is missing.
                if not cloud_object_type.ID:
                    msg = "Cannot find definition for requested object type [" + cloud_object_type.ID + "]"
                    print(msg)
                    return None, msg

            else:
                msg = "GetCloudObjectType failed for [" + cloud_object_type.ID + "]"
                print(msg)
                return None, msg
            
            # get the cloud object
            c = cloud.Cloud()
            c.FromID(cloud_id)
            if c.ID is None:
                msg = "Failed to get Cloud details for Cloud ID [" + cloud_id + "]."
                return None, msg
            
            sURL, err = self.BuildURL(ca, c, cloud_object_type, additional_args);  
            if err:
                return None, err
            
            sXML, err = HTTPGet(sURL, 30)
            if err:
                return None, err

            return sXML, None
        except Exception as ex:
            raise Exception(ex)

    def BuildURL(self, ca, c, cot, additional_args={}):
        try:
            # !!! OK, PAY ATTENTION HERE
            # there's a possibility of a timestamp signature collision when making API calls very quickly back to back.
            # AWS/Eucalyptus recommends trapping for the HTTP 403 error, waiting 1 second, and try:ing again.
            
            # Since our HTTP function is shared in many places even by non-cloud code, we don't wanna muddy it up with 
            # a case specific handler.
            
            # One second isn't terribly long.  So, we're just sleeping a second here before every api call, just to ensure
            #  enough space between.
            
            time.sleep(1)            
            
            # we have to use the provided cloud and object type to construct an endpoint
            # if either of these values is missing, we will attempt to use the other one standalone.
            sHostName = ""
        
            prod = cot.ParentProduct
        
            sHostName = prod.APIUrlPrefix + ("" if not c.Region else c.Region + ".") + c.APIUrl
        
            # Issue #250 - some aws endpoints aren't uniform like the rest.  The proper solution 
            # is use of some variables to give flexibility in building the endpoint url.
            # but, for the immediate need we're just doing an explicity replacement here if it's IAM.
            
            if prod.Name.lower() == "iam" and prod.ParentProviderName.lower() == "amazon aws":
                sHostName = "iam.amazonaws.com"
            
            # following is the right way.
            # the cloud_providers.xml would get product definitions like this:
            # <product name="ec2" label="EC2" api_version="2011-12-01" api_url_prefix="{product}.{region}.">
            
#             # so, there may be variables {xxx} in the url, and we replace them here.
#             # most any property of the product, or cloud, or object could be a variable.
#             # but no goofy looping or being dynamic, just check each one explicitly
#             sHostName = sHostName.replace("{product}", prod.Name)
#             sHostName = sHostName.replace("{region}", c.Region)

            if not sHostName:
                msg = "Unable to reconcile an endpoint from the Cloud [" + c.Name + "] or Cloud Object [" + cot.ID + "] definitions."
                print(msg)
                return None, msg
            
            # HOST URI
            # what's the URI... (if any)
            sResourceURI = ""
            if prod.APIUri:
                sResourceURI = prod.APIUri
            
            # AWS auth parameters
            sAccessKeyID = ca.LoginID
            sSecretAccessKeyID = ca.LoginPassword
            
            params = {}
            params["AWSAccessKeyId"] = sAccessKeyID

            sSignature = ""
            sQueryString = ""
            
            if prod.Name == "s3" or prod.Name == "walrus":
                # HARDCODE ALERT
                # Currently (2-10-2010) AWS has goofy endpoints for the s3 services, using a "s3-" instead of "ec2.", etc.
                # MOREOVER, unlike all the other products, you cannot explicitly ask for the us-east-1 region.
                # so, we do a little interception here.
                sHostName = sHostName.replace("s3-us-east-1","s3")
                # all other regions should work as defined.
                
                # s3 seems to need the epoch time "expires" value
                sEpoch = str(int(time.time()) + 300)
                params["Expires"] = sEpoch

                # per http:# docs.amazonwebservices.com/AmazonS3/latest/dev/RESTAuthentication.html
                uri = ("/" if not sResourceURI else sResourceURI)
                sStringToSign = "GET\n\n\n%s\n%s" % (sEpoch, uri)

                paramsList = params.items()
                paramsList.sort()
                sQueryString = '&'.join(['%s=%s' % (k,urllib2.quote(str(v))) for (k,v) in paramsList if v])

                # and sign it
                digest = hmac.new(sSecretAccessKeyID, sStringToSign, hashlib.sha1).digest()
                sSignature = base64.b64encode(digest)

                # finally, urlencode the signature
                sSignature = urllib2.quote(sSignature)
            else:                 
                # other AWS/Euca calls use the current Timestamp
                params["Timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
                params["Action"] = cot.APICall

                # do we need to apply a group filter?  If it's defined on the table then YES!
                if cot.APIRequestGroupFilter:
                    sTmp = cot.APIRequestGroupFilter.split('=')
                    params[sTmp[0]] = sTmp[1]
        
                # ADDITIONAL ARGUMENTS
                #if AdditionalArguments is not None:
                    # we have custom arguments... use them
                    # for each... add to sortedRequestParams
                    # if the same key from the group filter is defined as sAdditionalArguments it overrides the table!
        
                params["Version"] = prod.APIVersion
                params["SignatureMethod"] = "HmacSHA256"
                params["SignatureVersion"] = "2"
            
                # now we have all the parameters in a list, build a sorted, encoded querystring string
                # After the parameters are sorted in natural byte order and URL encoded, the next step is to concatenate them into a single text string.  
                # The following method uses the PercentEncodeRfc3986 method to create the parameter string.
                paramsList = params.items()
                paramsList.sort()
                sQueryString = '&'.join(['%s=%s' % (k,urllib2.quote(str(v))) for (k,v) in paramsList if v])
        
            
                # use the URL/URI plus the querystring to build the full request to be signed
                # per http:# docs.amazonwebservices.com/AWSEC2/latest/UserGuide/using-query-api.html
                uri = ("/" if not sResourceURI else sResourceURI)
                sStringToSign = "GET\n%s\n%s\n%s" % (sHostName, uri, sQueryString.encode("utf-8"))

                # and sign it
                digest = hmac.new(sSecretAccessKeyID, sStringToSign, hashlib.sha256).digest()
                sSignature = base64.b64encode(digest)

                # finally, urlencode the signature
                sSignature = urllib2.quote(sSignature)

            sHostURL = c.APIProtocol.lower() + "://" + sHostName + sResourceURI
            return sHostURL + "?" + sQueryString + "&Signature=" + sSignature, None

        except Exception as ex:
            raise Exception(ex)
