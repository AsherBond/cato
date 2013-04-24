
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

from catolog import catolog
logger = catolog.get_logger(__name__)

from catoapi import api
from catoapi.api import response as R
from catocloud import cloud
from catocommon import catocommon

class cloudMethods:
    """These are methods for Cloud, Cloud Accounts and other related items."""

    def list_clouds(self, args):        
        """
        Lists all Clouds.
        
        Optional Arguments: 
            filter - will filter a value match in Cloud Name, Provider, Default Account Name or API URL.
        
        Returns: An list of all Clouds.
        """
        fltr = args["filter"] if args.has_key("filter") else ""

        obj = cloud.Clouds(sFilter=fltr)
        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args["output_delimiter"]))
        else:
            return R(response=obj.AsXML())

    def list_cloud_accounts(self, args):        
        """
        Lists all Cloud Accounts.
        
        Optional Arguments: 
            filter - will filter a value match in Account Name, Account Number, Provider, Login ID and Default Cloud Name.
        
        Returns: An list of all Cloud Accounts.
        """
        fltr = args["filter"] if args.has_key("filter") else ""

        obj = cloud.CloudAccounts(sFilter=fltr)
        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args["output_delimiter"]))
        else:
            return R(response=obj.AsXML())
        
    def create_account(self, args):
        """
        Creates a Cloud Account.
        
        Required Arguments: 
            name - a name for the new Account.
            provider - one of the valid cloud providers.
            login - the login id (access key) for this Account.
            password - a password (secret key) for this Account.
            default_cloud - the name of a default Cloud for this Account.

        Optional Arguments: 
            account_number - an Account number.
        
        """
        required_params = ["name", "provider", "login", "password", "default_cloud"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        name = args.get("name")
        provider = args.get("provider")
        login = args.get("login")
        pw = args.get("password")
        default_cloud = args.get("default_cloud")
        
        acct_number = args.get("account_number", "")
        
        
        obj = cloud.CloudAccount.DBCreateNew(provider, name, login, pw, acct_number, default_cloud)
        catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.CloudAccount, obj.ID, obj.Name, "Account created.")

        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args["output_delimiter"]))
        else:
            return R(response=obj.AsXML())

    def get_account(self, args):
        """
        Gets a Cloud Account.
        
        Required Arguments: 
            name - a Cloud Account name or ID.

        Returns: A Cloud Account object.
        """
        required_params = ["name"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        name = args.get("name")

        obj = cloud.CloudAccount()
        obj.FromName(name)

        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args["output_delimiter"]))
        else:
            return R(response=obj.AsXML())

    def get_cloud(self, args):
        """
        Gets a Cloud object.
        
        Required Arguments: 
            name - a Cloud name or ID.

        Returns: A Cloud object.
        """
        required_params = ["name"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        name = args.get("name")

        obj = cloud.Cloud()
        obj.FromName(name)

        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args["output_delimiter"]))
        else:
            return R(response=obj.AsXML())

    def create_cloud(self, args):
        """
        Creates a Cloud.
        
        Required Arguments: 
            name - a name for the new Cloud.
            provider - one of the valid cloud providers.
            apiurl - URL of the Cloud API endpoint.
            apiprotocol - Cloud API endpoint protocol.

        Optional Arguments: 
            default_account - the name of a default Account for this Cloud.
        
        """
        required_params = ["name", "provider", "apiurl", "apiprotocol"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        name = args.get("name")
        provider = args.get("provider")
        apiurl = args.get("apiurl")
        apiprotocol = args.get("apiprotocol")
        default_account = args.get("default_account")
        
        obj = cloud.Cloud.DBCreateNew(name, provider, apiurl, apiprotocol, "", default_account)

        catocommon.write_add_log(args["_user_id"], catocommon.CatoObjectTypes.Cloud, obj.ID, obj.Name, "Cloud created.")

        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args["output_delimiter"]))
        else:
            return R(response=obj.AsXML())

    def update_cloud(self, args):
        """
        Updates a Cloud.
        
        Required Arguments: 
            cloud - Name or ID of the cloud to update.

        Optional Arguments: 
            apiurl - URL of the Cloud API endpoint.
            apiprotocol - Cloud API endpoint protocol.
            default_account - the name of a default Account for this Cloud.
        
        """
        required_params = ["name"]
        has_required, resp = api.check_required_params(required_params, args)
        if not has_required:
            return resp

        name = args.get("name")
        apiurl = args.get("apiurl")
        apiprotocol = args.get("apiprotocol")
        default_account = args.get("default_account")
        
        oldvals = []
        newvals = []
        
        obj = cloud.Cloud()
        obj.FromName(name)
        if apiurl:
            oldvals.append("api_url: %s" % (obj.APIUrl))
            newvals.append("api_url: %s" % (apiurl))
            obj.APIUrl = apiurl
        if apiprotocol:
            oldvals.append("api_protocol: %s" % (obj.APIProtocol))
            newvals.append("api_protocol: %s" % (apiprotocol))
            obj.APIProtocol = apiprotocol
        
        if default_account:
            obj.GetDefaultAccount()
            oldvals.append("default_account: %s" % (obj.DefaultAccount.Name if obj.DefaultAccount else "None"))
            # no need to build a complete object, as the update is just updating the ID
            newacct = cloud.CloudAccount()
            newacct.FromName(default_account)
            if newacct.ID:
                if not newacct.Provider.Name == obj.Provider.Name:
                    raise Exception("Default Account must be the same Provider as this Cloud.")
                newvals.append("default_account: %s" % (newacct.Name))
                obj.DefaultAccount = newacct

        obj.DBUpdate()
        
        catocommon.write_property_change_log(args["_user_id"], catocommon.CatoObjectTypes.Cloud, obj.ID, obj.Name, ", ".join(oldvals), ", ".join(newvals))

        if args["output_format"] == "json":
            return R(response=obj.AsJSON())
        elif args["output_format"] == "text":
            return R(response=obj.AsText(args["output_delimiter"]))
        else:
            return R(response=obj.AsXML())


