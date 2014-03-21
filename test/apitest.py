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
import time

sys.path.insert(0, os.path.join(os.environ["LEGATO_HOME"], "lib"))
sys.path.insert(0, os.path.join(os.environ["CATO_HOME"], "lib"))

from catoapi import sysMethods
from catoapi import cloudMethods
from catoapi import taskMethods
from catoapi import dsMethods
from catoapi import api
from catouser.catouser import User, Users

# IMPORTANT NOTE: Many API methods require a user, and have code to verify permissions.
# We're forcing the api._ADMIN flag to be True - this will allow all functions to work.
api._USER_ID = None
api._USER_ROLE = "Administrator"
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
        User tests.  At the moment there is no 'delete_user'... 
            so we're manhandling the lib directly for cleanup
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
        _u = users[0]
        # the response is a list, but we filtered so we want the first index
        self.assertEqual(e, _u["Email"], "'update_user' didn't work - email doesn't match.")

        # done last, as the reset_password requires the user to have an email address

        # reset password - there's no way to verify this, as no functions actually return the password
        # so, all we're testing for here is no exceptions
        x = SM.reset_password({"user": n, "password": "newpassword"})
        evaluate_response(self, x)

        # manual delete of user
        Users.Delete([_u["ID"]])

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
        Ensure the Cloud and Account are there using both 'get' and 'list'.
        Add, view and delete a keypair on the cloud.

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
        x = CM.delete_cloud_keypair({
                             "cloud": cloudname,
                             "name": kpname
        })
        evaluate_response(self, x)


    def test_delete_cloud_keypair(self):
        pass


class dsMethodsTests(unittest.TestCase):
    """
    Tests for the methods in 'dsMethods'.

    Create a document, in a new collection.
    Confirm the collection exists in the list.
    Confirm the document exists in the collection.
    Set a new value in the existing document.
    Get that value from the document.

    """
    def test_datastore(self):
        d = {
             "foo": "bar"
        }
        x = DM.create_document({
                                "output_format": "json",
                                "collection": "test_collection",
                                "template": d
                                })
        evaluate_response(self, x)
        # we'll use this below - it'll have the _id in it
        _doc = json.loads(x.Response)

        x = DM.list_document_collections({"output_format": "json", "filter": "test_collection"})
        evaluate_response(self, x)
        _list = json.loads(x.Response)
        self.assertTrue("test_collection" in _list, "'create_document' didn't work - 'test_collection' not found in collection list")

        x = DM.list_documents({
                               "output_format": "json",
                               "collection": "test_collection",
                               "filter": {"_id": _doc["_id"]}
                               })
        evaluate_response(self, x)
        _doclist = json.loads(x.Response)
        self.assertEquals(_doc["_id"], _doclist[0]["_id"], "uh oh - 'list_documents' didn't find a matching document")

        q = json.dumps({"_id": _doc["_id"]})
        x = DM.get_document({
                             "output_format": "json",
                             "collection": "test_collection",
                             "query": q
                             })
        evaluate_response(self, x)
        _doc2 = json.loads(x.Response)
        self.assertEquals(_doc["_id"], _doc2["_id"], "uh oh - 'get_document' _id didn't match the original _id")

        x = DM.get_document_value({
                                   "output_format": "json",
                                   "collection": "test_collection",
                                   "query": q,
                                   "lookupkey": "foo"
        })
        evaluate_response(self, x)
        _vals = json.loads(x.Response)
        self.assertTrue("bar" in _vals, "uh oh - 'get_document_value' didn't give us what we'd hoped for")

        x = DM.set_document_value({
                                   "output_format": "json",
                                   "collection": "test_collection",
                                   "query": q,
                                   "lookupkey": "tom",
                                   "value": "bombadil"
        })
        evaluate_response(self, x)

        x = DM.get_document_value({
                                   "output_format": "json",
                                   "collection": "test_collection",
                                   "query": q,
                                   "lookupkey": "tom"
        })
        evaluate_response(self, x)
        _vals = json.loads(x.Response)
        self.assertTrue("bombadil" in _vals, "uh oh - second try at 'get_document_value' didn't give us what we'd hoped for")


class taskMethodsTests(unittest.TestCase):
    """
    Tests for the methods in 'taskMethods'.
    
    Testing the Task features is as follows:
    
    Create a Task manually
    List Tasks and confirm it's there
    Delete it
    
    Create a Task from JSON
    Export it as XML
    Import from the XML previously obtained.
    Get it
    Delete the Task at the end

    Create a Task
    Mess around with Scheduling
    Delete it
    
    Create a Task with parameters
    Read those parameters
    Delete it
    
    Running Tasks is tricker, so we'll save that for last.
    """


    # ADD import_backup TO THE TASKS testing section

    
    def test_create_task(self):
        # create, list, delete
        n = random_name("task-")
        x = TM.create_task({"name": n})
        evaluate_response(self, x)

        x = TM.list_tasks({"output_format": "json", "filter": n})
        evaluate_response(self, x)
        _tasklist = json.loads(x.Response)
        self.assertEquals(n, _tasklist[0]["Name"], "uh oh - 'list_tasks' didn't find a match")

        x = TM.delete_task({"task": n, "force_delete": "true"})
        evaluate_response(self, x)


    def test_export_import(self):
        # create from json, export, import, delete
        n = random_name("task-")
        task = {
                "Name": n,
                "Codeblocks": [
                        {
                            "Steps": [], 
                            "Name": "MAIN"
                        }
                    ]
                }
        x = TM.create_task_from_json({"json": json.dumps(task)})
        evaluate_response(self, x)

        # export it
        x = TM.export_task({"task": n})
        evaluate_response(self, x)
        _backupdata = x.Response

        # delete the source
        x = TM.delete_task({"task": n, "force_delete": "true"})
        evaluate_response(self, x)
        
        # import the backup
        # NOTE: this is in sysMethods
        x = SM.import_backup({"xml": _backupdata})
        evaluate_response(self, x)
        
        # confirm it's there
        x = TM.get_task({"output_format": "json", "task": n})
        evaluate_response(self, x)
        _task = json.loads(x.Response)
        self.assertEquals(n, _task["Name"], "uh oh - 'get_task' didn't find a match - the import must've failed")
 
        # whack it
        x = TM.delete_task({"task": n, "force_delete": "true"})
        evaluate_response(self, x)


    def test_task_schedule_stuff(self):
        # create, schedule, delete plan, delete schedule, delete
        n = random_name("task-")
        x = TM.create_task({"name": n})
        evaluate_response(self, x)

        scheds = [
            { 
                "Task": n,
                "Months": "*",
                "DaysOrWeekdays": "Weekdays",
                "Days": "*",
                "Hours": [3, 15],
                "Minutes": [0, 30]
            }
        ]
        x = TM.schedule_tasks({"tasks": json.dumps(scheds)})
        evaluate_response(self, x)

        x = TM.get_task_schedules({"output_format": "json", "task": n})
        evaluate_response(self, x)
        _schedules = json.loads(x.Response)
        # get_task_schedules returns a LIST of schedules
        _s = _schedules[0]
        self.assertEquals("*", _s["Months"], "uh oh - Months didn't match.")
        self.assertEquals("Weekdays", _s["DaysOrWeekdays"], "uh oh - DaysOrWeekdays didn't match.")
        self.assertEquals("*", _s["Days"], "uh oh - Days didn't match.")
        self.assertEquals([3, 15], _s["Hours"], "uh oh - Hours didn't match.")
        self.assertEquals([0, 30], _s["Minutes"], "uh oh - Minutes didn't match.")

        # IN ORDER TO TEST DELETING A PLAN, we have to wait for a running scheduler to create the rows
#         time.sleep(5)
#         x = TM.get_task_plans({"output_format": "json", "task": n})
#         evaluate_response(self, x)
#         _plans = json.loads(x.Response)
#         _plan_id = _plans[0]["PlanID"]
# 
#         # we can delete a plan, but it'll be a pain to confirm if it actually deleted... 
#         x = TM.delete_plan({"plan_id": str(_plan_id)})
#         evaluate_response(self, x)
# 
#         # will have to loop thru the plans to make sure it's gone
#         x = TM.get_task_plans({"output_format": "json", "task": n})
#         evaluate_response(self, x)
#         _plans = json.loads(x.Response)
#         expr = _plan_id in [x["PlanID"] for x in _plans]
#         self.assertFalse(expr, "uh oh - plan_id is still in the plans list, delete didn't work")
        
        # delete the schedule using it's id
        x = TM.delete_schedule({"schedule_id": _s["ScheduleID"]})
        evaluate_response(self, x)

        # is it gone?
        x = TM.get_task_schedules({"output_format": "json", "task": n})
        evaluate_response(self, x)
        _schedules = json.loads(x.Response)
        self.assertFalse(len(_schedules), "uh oh - Schedule didn't delete.")

        x = TM.delete_task({"task": n, "force_delete": "true"})
        evaluate_response(self, x)


    def test_describe_task_parameters(self):
        # create from json, describe parameters, make sure data is there
        
        # NOTE: Currently parameters can only be xml, yes ... xml in a JSON field. :-/
        n = random_name("task-")
        task = {
                "Name": n,
                "Codeblocks": [
                        {
                            "Steps": [], 
                            "Name": "MAIN"
                        }
                    ],
                "Parameters": "<parameters><parameter constraint=\"\" constraint_msg=\"\" encrypt=\"false\" id=\"p_f11c0c63-b06e-11e3-a30c-c8bcc89c1491\" maxlength=\"\" maxvalue=\"\" minlength=\"\" minvalue=\"\" prompt=\"false\" required=\"false\"><name>foo</name><desc /><values present_as=\"value\"><value id=\"pv_f11d3999-b06e-11e3-8b29-c8bcc89c1491\">bar</value></values></parameter></parameters>"
                }
        x = TM.create_task_from_json({"json": json.dumps(task)})
        evaluate_response(self, x)

        x = TM.describe_task_parameters({"task": n})
        evaluate_response(self, x)
        # simple text in text check
        self.assertTrue("foo" in x.Response, "uh oh - 'describe_task_parameters', doesn't look like our parameter is on the task.")

        x = TM.get_task_parameters({"output_format": "json", "task": n})
        evaluate_response(self, x)
        _params = json.loads(x.Response)
        self.assertEquals("foo", _params[0]["name"], "uh oh - 'get_task_parameters' , doesn't look like our parameter is on the task.")

        x = TM.delete_task({"task": n, "force_delete": "true"})
        evaluate_response(self, x)


    # THESE RUN TASK tests should be in a separate file, since they're potentially long running
#     def test_run_task(self):
#         # create, run, get instance, delete
#         """
#         test_run_task
#         test_get_task_instance
#         """
#         pass
# 
# 
#     def test_stop_task(self):
#         # create (with a long pause), run, stop, get instance status (ensure 'Cancelled), resubmit, delete
#         """
#         test_get_task_instance_status
#         test_resubmit_task_instance
#         test_stop_task
#         """
#         pass
# 
# 
#     def test_task_log(self):
#         # create (with a 'Log Message'), run, wait (this time looking at the whole instances list), get log, delete
#         """
#         test_get_task_instances
#         test_get_task_log
#         """
#         pass


if __name__ == '__main__':

    # running these tests requires a user.
    u = User()
    u.FromName("administrator")
    if not u.ID:
        raise Exception("Unable to run tests - no 'administrator' user defined.")
    api._USER_ID = u.ID

    unittest.main()
