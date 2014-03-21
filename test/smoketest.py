#!/usr/bin/env python

"""
Some smoke testing - critical things that should work.

Any test failure is a show stopper, it doesn't bother to keep testing.
"""

import unittest

import sys
import os

sys.path.insert(0, os.path.join(os.environ["CATO_HOME"], "lib"))


class moduleTests(unittest.TestCase):
    """
    Confirming that some core modules can be loaded.
    
    For each of our main services, we should be able to instantiate the Class. 
    Each module has at least one property we can check.
    
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
        # make sure we can laod the module, set and verify a property
        from catoscheduler import catoscheduler
        s = catoscheduler.Scheduler("cato_scheduler")
        s.scheduler_enabled = True
        self.assertTrue(s.scheduler_enabled, "Unable to set a property in the Scheduler.")


    def test_poller(self):
        # make sure we can laod the module, Poller has a hardcoded property we can check
        from catopoller import catopoller
        p = catopoller.Poller("cato_poller")
        self.assertTrue(p.rollover_counter == 5, "Unable to set a property in the Poller.")


    def test_messenger(self):
        # make sure we can laod the module and get it's settings
        from catomessenger import catomessenger
        m = catomessenger.Messenger("cato_messenger")
        m.messenger_enabled = True
        self.assertTrue(m.messenger_enabled, "Unable to set a property in the Messenger.")


if __name__ == '__main__':
    # consider accepting a version as an argument, so it can validate we are running the right version
    
    unittest.main()
