#!/usr/bin/env python

"""
This module uses 'unittest' to test all the functions we expose via the API.

It DOES NOT test the actual API service, as this requires a running service.

Instead, it executes the method that would be executed by the services HTTP handler.

All the API functions require a dictionary as args.  Dictionary schema varies for each individual method.

Most tests are using the JSON 'output_format', as this is the most likely scenario of API use.

"""

import unittest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.environ["LEGATO_HOME"], "lib"))
sys.path.insert(0, os.path.join(os.environ["CATO_HOME"], "lib"))

from catoapi import sysMethods
from catoapi import cloudMethods
from catoapi import taskMethods
from catoapi import dsMethods
from catoapi import api
from catouser.catouser import User

# IMPORTANT NOTE: Many API methods require a user, and have code to verify permissions.
# We're forcing the api._ADMIN flag to be True - this will allow all functions to work.
api._USER_ID = None
api._ADMIN = True
api._DEVELOPER = True

# this sysMethods object can be used for testing all the functions
SM = sysMethods.sysMethods()
CM = cloudMethods.cloudMethods()
TM = taskMethods.taskMethods()
DM = dsMethods.dsMethods()

# for x in dir(TM):
#     print "    def test_%s(self):\n        pass\n\n" % (x)

def random_name(prefix="", suffix=""):
    # returns the provided name with a random hash added
    return "%s%s%s" % (prefix, os.urandom(8).encode('hex'), suffix)


def evaluate_response(obj, resp):
    # cleans up the tests below, as 99% of the api calls will be looking for the 
    # existence of ErrorCode, and print the ErrorMessage if it exists.
    obj.assertFalse(resp.ErrorCode, "%s%s" % (resp.ErrorMessage, resp.ErrorDetail))
    
class sysMethodsTests(unittest.TestCase):
    """
    Tests for the methods in 'sysMethods'.
    """


    def test_users(self):
        """
        User tests.  At the moment there is no 'delete_user'.
        """
        n = random_name("user-")

        x = SM.list_users({"filter": "administrator"})
        evaluate_response(self, x)

        x = SM.create_user({"user": n, "role": "User", "name": "Created by Test Script", "password": "password"})
        evaluate_response(self, x)
        
        # a random email address for testing...
        e = random_name("", "@csk.com")

        x = SM.update_user({
                            "user": n, 
                            "name": "Modified by Test Script", 
                            "email": e, 
                            "role": "Developer", 
                            "authtype": "ldap", 
                            "forcechange": "true", 
                            "status": "locked", 
                            "expires": "01/15/2020", 
                            "groups": "group1,group2"
        })
        evaluate_response(self, x)

        x = SM.list_users({"output_format": "json", "filter": n})
        evaluate_response(self, x)
        
        # let's look at the user we just got back, and see if the email matches what we just set it to be
        users = json.loads(x.Response)
        # the response is a list, but we filtered so we want the first index
        self.assertEqual(e, users[0]["Email"], "'update_user' didn't work - email doesn't match.")

        # done last, as the reset_password requires the user to have an email address
        
        # reset password - there's no way to verify this, as no functions actually return the password
        # so, all we're testing for here is no exceptions
        x = SM.reset_password({"user": n, "password": "newpassword"})
        evaluate_response(self, x)


    def test_tags(self):
        """
        Test tagging features.  Note: create_tag will NOT fail if the tag already exists, it just reports success.
        """
        n = random_name("tag-")
        
        x = SM.create_tag({"name": n})
        evaluate_response(self, x)

        x = SM.list_tags({"name": n})
        evaluate_response(self, x)

        # add a tag to user we know exists (administrator)
        x = SM.add_object_tag({"tag": n, "object_id": api._USER_ID, "object_type": "1"})
        evaluate_response(self, x)

        # and remove it
        x = SM.remove_object_tag({"tag": n, "object_id": api._USER_ID, "object_type": "1"})
        evaluate_response(self, x)

        x = SM.delete_tag({"name": n})
        evaluate_response(self, x)


    def test_asset(self):
        """
        Some asset tests.  Creating an Asset will fail if it exists, so we delete first.
        """
        n = random_name("asset-")
        
        # create an asset with a local credential
        x = SM.create_asset({"name": n, "user": "foo", "password": "bar"})
        evaluate_response(self, x)
        
        x = SM.list_assets({})
        evaluate_response(self, x)
        
        x = SM.get_asset({"asset": n})
        evaluate_response(self, x)
        
        x = SM.delete_asset({"asset": n})
        evaluate_response(self, x)


    def test_credentials(self):
        """
        Test creating a shared credential, then creating an asset using that credential.
        """
        cn = random_name("credential-")
        an = random_name("asset-")
        
        # create an asset with a local credential
        x = SM.create_credential({"name": cn, "username": "foo", "password": "bar"})
        evaluate_response(self, x)
        
        x = SM.list_credentials({})
        evaluate_response(self, x)

        # create an asset with a local credential
        x = SM.create_asset({"name": an, "shared_credential": cn})
        evaluate_response(self, x)
        
        x = SM.delete_asset({"asset": an})
        evaluate_response(self, x)
 
        x = SM.delete_credential({"credential": cn})
        evaluate_response(self, x)

        # TODO: create a credential with a private key instead of a username


    def test_get_settings(self):
        x = SM.get_settings({"output_format": "json", "module": "security"})
        evaluate_response(self, x)

        s = json.loads(x.Response)
        s["NewUserMessage"] = "Automated Testing updated this setting."
        
        # using the response, we can change a property and resubmit it
        # then get the settings again and verify it was properly updated 
        x = SM.update_settings({"module": "security", "settings": json.dumps(s)})
        evaluate_response(self, x)
        
        # let's look at the user we just got back, and see if the email matches what we just set it to be
 
 
    def test_get_token(self):
        x = SM.get_token({})
        evaluate_response(self, x)
 
 
    def test_get_system_log(self):
        x = SM.get_system_log({})
        evaluate_response(self, x)
 
 
    def test_list_processes(self):
        x = SM.list_processes({})
        evaluate_response(self, x)
 
 
    def test_send_message(self):
        # at the moment there's no way to test if this worked unless the system is 
        # configured to actually send the emails.
        x = SM.send_message({
                             "to": "shannon.cruey@cloudsidekick.com", 
                             "subject": "Automated test of 'send_message' API.", 
                             "message": "This is the message body."
        })
        evaluate_response(self, x)
 
 



class cloudMethodsTests(unittest.TestCase):
    """
    Tests for the methods in 'sysMethods'.
    """
    def test_add_cloud_keypair(self):
        pass


    def test_clouds(self):
        """
        Create a cloud, create an Account, set that Account as the default for the new Cloud.
        
        There are currently no methods for deleting Clouds/Accounts
        """
        cloudname = random_name("cloud-")
        x = CM.create_cloud({
                             "name": cloudname, 
                             "provider": "Amazon AWS", 
                             "apiurl": "foo.bar.com",
                             "apiprotocol": "HTTP"
        })
        evaluate_response(self, x)
        
        # get the cloud
        x = CM.get_cloud({"output_format": "json", "name": cloudname})
        evaluate_response(self, x)
        
        # load the cloud and inspect it
        _c = json.loads(x.Response)
        # the response is a list, but we filtered so we want the first index
        self.assertEqual(cloudname, _c["Name"], "'create_cloud' didn't work - Name in 'get_cloud' doesn't match the original template.")
        
        # list the clouds and ensure it's there too
        x = CM.list_clouds({"output_format": "json", "filter": cloudname})
        evaluate_response(self, x)
        
        # load the cloud and inspect it
        _c = json.loads(x.Response)
        # the response is a list, but we filtered so we want the first one
        self.assertEqual(cloudname, _c[0]["Name"], "'create_cloud' didn't work - 'list_clouds' couldn't find it")
        

        acctname = random_name("cloudaccount-")
        x = CM.create_account({
                             "name": acctname, 
                             "provider": "Amazon AWS", 
                             "login": "fakelogin",
                             "password": "password",
                             "default_cloud": cloudname
        })
        evaluate_response(self, x)
        
        # get the account
        x = CM.get_account({"output_format": "json", "name": acctname})
        evaluate_response(self, x)
        
        # load the cloud and inspect it
        _a = json.loads(x.Response)
        # the response is a list, but we filtered so we want the first index
        self.assertEqual(acctname, _a["Name"], "'create_account' didn't work - Name in 'get_account' doesn't match the original template.")
        
        # list the accounts and ensure it's there too
        x = CM.list_cloud_accounts({"output_format": "json", "filter": acctname})
        evaluate_response(self, x)
        
        # load the cloud and inspect it
        _a = json.loads(x.Response)
        # the response is a list, but we filtered so we want the first one
        self.assertEqual(acctname, _a[0]["Name"], "'create_account' didn't work - 'list_accounts' couldn't find it")

        # finally, update the cloud with the new account as the 'default'
        x = CM.update_cloud({
                             "name": cloudname, 
                             "default_account": acctname
        })
        evaluate_response(self, x)
        
        # add a keypair to our new cloud
        kpname = random_name("kp-")
        x = CM.add_cloud_keypair({
                             "cloud": cloudname, 
                             "name": kpname, 
                             "private_key": "password"
        })
        evaluate_response(self, x)
        
        # list the keypairs and ensure it's there
        x = CM.list_cloud_keypairs({"output_format": "json", "cloud": cloudname})
        evaluate_response(self, x)
        
        # load the kp and inspect it
        _kps = json.loads(x.Response)
        # the response is a list, but we filtered so we want the first one
        self.assertEqual(kpname, _kps[0]["Name"], "'add_cloud_keypair' didn't work - 'list_cloud_keypairs' couldn't find it")

        # then delete it


    def test_delete_cloud_keypair(self):
        pass


    def test_list_cloud_keypairs(self):
        pass


class dsMethodsTests(unittest.TestCase):
    """
    Tests for the methods in 'sysMethods'.
    """
    def test_create_document(self):
        pass


    def test_get_document(self):
        pass


    def test_get_document_value(self):
        pass


    def test_list_document_collections(self):
        pass


    def test_list_documents(self):
        pass


    def test_set_document_value(self):
        pass


class taskMethodsTests(unittest.TestCase):
    """
    Tests for the methods in 'sysMethods'.
    """

    
    # ADD import_backup TO THE TASKS testing section
    def test_create_task(self):
        pass


    def test_create_task_from_json(self):
        pass


    def test_delete_plan(self):
        pass


    def test_delete_schedule(self):
        pass


    def test_delete_task(self):
        pass


    def test_describe_task_parameters(self):
        pass


    def test_export_task(self):
        pass


    def test_get_task(self):
        pass


    def test_get_task_instance(self):
        pass


    def test_get_task_instance_status(self):
        pass


    def test_get_task_instances(self):
        pass


    def test_get_task_log(self):
        pass


    def test_get_task_parameters(self):
        pass


    def test_get_task_plans(self):
        pass


    def test_get_task_schedules(self):
        pass


    def test_list_tasks(self):
        pass


    def test_resubmit_task_instance(self):
        pass


    def test_run_task(self):
        pass


    def test_schedule_tasks(self):
        pass


    def test_stop_task(self):
        pass
        
if __name__ == '__main__':
    
    # running these tests requires a user.
    u = User()
    u.FromName("administrator")
    if not u.ID:
        raise Exception("Unable to run tests - no 'administrator' user defined.")
    api._USER_ID = u.ID
    
    unittest.main()
