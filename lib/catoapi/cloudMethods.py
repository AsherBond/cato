
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
Cloud / Cloud Account endpoint methods.
"""

from catoapi.api import response as R
from catocloud import cloud

class cloudMethods:
    """These are methods for Cloud, Cloud Accounts and other related items."""

    def list_clouds(self, args):        
        """
        Lists all Clouds.
        
        Optional Arguments: 
            filter - will filter a value match in Cloud Name, Provider, Default Account Name or API URL.
        
        Returns: An list of all Clouds.
        """
        try:
            fltr = args["filter"] if args.has_key("filter") else ""

            obj = cloud.Clouds(sFilter=fltr)
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText())
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.ListError, err_detail="Unable to list Clouds.")
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

    def list_cloud_accounts(self, args):        
        """
        Lists all Cloud Accounts.
        
        Optional Arguments: 
            filter - will filter a value match in Account Name, Account Number, Provider, Login ID and Default Cloud Name.
        
        Returns: An list of all Cloud Accounts.
        """
        try:
            fltr = args["filter"] if args.has_key("filter") else ""

            obj = cloud.CloudAccounts(sFilter=fltr)
            if obj:
                if args["output_format"] == "json":
                    return R(response=obj.AsJSON())
                elif args["output_format"] == "text":
                    return R(response=obj.AsText())
                else:
                    return R(response=obj.AsXML())
            else:
                return R(err_code=R.Codes.ListError, err_detail="Unable to list Cloud Accounts.")
            
        except Exception as ex:
            return R(err_code=R.Codes.Exception, err_detail=ex.__str__())

