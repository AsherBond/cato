#!/usr/bin/env python

"""
Some smoke testing - critical things that should work.

Any test failure is a show stopper, it doesn't bother to keep testing.
"""

import unittest
import urllib2

import sys
import os

sys.path.insert(0, os.path.join(os.environ["CSK_HOME"], "cato", "lib"))


# THIS CAN EXPAND - the log file might have various levels of warning indicators
LOGFLAGS = ["Traceback", "CRITICAL", "ERROR"]


def _http(url):
    # the test should not fail because of an http error, just report on it.
    try:
        response = urllib2.urlopen(url)
        return response.read()
    except urllib2.URLError as ex:
        print "Unable to reach [%s]" % (url)
        # print ex.__str__()
        return ""


class httpTests(unittest.TestCase):
    """
    Use HTTP and hit all the services, looking for the /version
    """

    def test_cato_version(self):
        url = "http://localhost:8080/version"
        ver = _http(url)
        self.assertTrue(ver, "no version was returned")


    def test_api_version(self):
        url = "http://localhost:4001/version?output_format=text"
        ver = _http(url)
        self.assertTrue(ver, "no version was returned")

    
    # does the UI serve the login page?
    def test_login(self):
        url = "http://localhost:8080"
        page = _http(url)
        # we should see 'loginpanel' in the response, otherwise we don't have the login page
        self.assertTrue("loginpanel" in page, "Not the login page.")


    # this is slick ... now that we know the api is running,
    # we can use it's built-in feature to read all the log files!
    def test_scheduler(self):
        url = "http://localhost:4001/getlog?process=cato_scheduler"
        log = _http(url)
        for flag in LOGFLAGS:
            self.assertFalse(flag in log, "uh oh - the scheduler log suggests a problem. Found [%s]." % (flag))
    

    def test_poller(self):
        url = "http://localhost:4001/getlog?process=cato_poller"
        log = _http(url)
        for flag in LOGFLAGS:
            self.assertFalse(flag in log, "uh oh - the poller log suggests a problem. Found [%s]." % (flag))
    

    def test_messenger(self):
        url = "http://localhost:4001/getlog?process=cato_messenger"
        log = _http(url)
        for flag in LOGFLAGS:
            self.assertFalse(flag in log, "uh oh - the messenger log suggests a problem. Found [%s]." % (flag))
    

class moduleTests(unittest.TestCase):
    """
    Just confirming that some core modules can be loaded.
    
    For each of our main services, we should be able to instantiate the Class, 
    and call the get_settings() function.
    
    No assertions, it'll just blow up if something is wrong.
    
    The main test here, is since we do our imports at the top of each module, 
    by importing each core service we basically test every module.
    """

    def test_te(self):
        # make sure we can laod the module, TaskEngine has a 'tochar' function - will verify it was instantiated
        from catotaskengine import catotaskengine
        te = catotaskengine.TaskEngine("cato_task_engine", "0")
        self.assertTrue(te.tochar(1), "Unable to instantiate the TaskEngine class.")


    def test_scheduler(self):
        # make sure we can laod the module, TaskEngine has a 'tochar' function - will verify it was instantiated
        from catoscheduler import catoscheduler
        s = catoscheduler.Scheduler("cato_scheduler")
        s.get_settings()


    def test_poller(self):
        # make sure we can laod the module, TaskEngine has a 'tochar' function - will verify it was instantiated
        from catopoller import catopoller
        p = catopoller.Poller("cato_poller")
        p.get_settings()


    def test_messenger(self):
        # make sure we can laod the module and get it's settings
        from catomessenger import catomessenger
        m = catomessenger.Messenger("cato_messenger")
        m.get_settings()


if __name__ == '__main__':
    # consider accepting a version as an argument, so it can validate we are running the right version
    
    unittest.main()
