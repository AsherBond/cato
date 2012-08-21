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

### see examples from 
# http://stackoverflow.com/questions/2701909/using-python-functions-in-tkinter-tcl/2708398#2708398
# http://stackoverflow.com/questions/2519532/example-for-accessing-tcl-functions-from-python
import sys
import os
import traceback
from Tkinter import Tcl

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catocommon import catocommon
from catosettings import settings

task_instance = sys.argv[1]

class TclFunc:
    def __init__(self, interp, func, debug=False):
        self.tclFuncName = func.func_name[4:]
        self.func = func
        interp.createcommand(self.tclFuncName, self)
    def __call__(self, *args):
        try:
            return self.func(*args)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            print("error in %s: %s" % (self.tclFuncName, e))
            traceback.print_exc(file=sys.stderr)
            raise e

class TaskEngine(catocommon.CatoProcess):

    def __init__(self, process_name, task_instance):
        self.task_instance = task_instance
        catocommon.CatoProcess.__init__(self, process_name)

    def set_logfile_name(self):
        '''overrides set_logfile_name() in catocommon'''

        self.logfile_name = os.path.join(self.logfiles_path, "ce",  self.task_instance +".log")

    def convert_tcl(self, data):
        '''Converts Python data to Tcl strings. A must use function to convert
            lists and tuples to Tcl lists.'''

        def _convert_list(data):
            s = ""
            for z in data:
                z = self.convert_tcl(z)
                if len(s) == 0:
                    s = "{%s}" % (z)
                else:
                    s = "%s {%s}" % (s,z)
            return s

        # at the moment, doesn't support dict conversion
        if data is None:
            return ""
        elif isinstance(data,list) or isinstance(data,tuple):
            return _convert_list(data)
            return ""
        else:
            return data

    def register_function(self, interp, func):
        '''Exposes a Python function to the Tcl interpreter'''
        #interp.createcommand(func.func_name[4:], func)
        TclFunc(interp, func)
        

    # a Python command example for Tcl
    #def pycommand(a, b, c, d, e):
    #    '''A sample Python command for Tcl'''
    #    x = "%s %s %s %s %s" % (a, b, c, d, e)
    #    # gotta call convert_tcl for a python return set
    #    return convert_tcl(x)

    def tcl_output(self, *args):
        debug_level_test = int(self.tcl.getvar(name='::DEBUG_LEVEL'))
        if len(args) == 1:
            debug_level = 2
        else:
            debug_level = int(args[1])

        if debug_level_test >= debug_level:    
            self.output(args[0])

    def tcl_decrypt_string(self, s):
        return self.convert_tcl(catocommon.cato_decrypt(s))

    def tcl_encrypt_string(self, s):
        return self.convert_tcl(catocommon.cato_encrypt(s))

    def tcl_exec_db(self, sql):
        self.db.exec_db(sql)

    def tcl_select_row(self, sql):
        row = self.db.select_row(sql)
        new_rows = self.convert_tcl(row)
        return new_rows

    def tcl_select_all(self, sql):
        row = self.db.select_all(sql)
        new_rows = self.convert_tcl(row)
        return new_rows

    def run(self):

        self.tcl = Tcl(useTk=False)
        self.tcl.setvar(name='::HOME', value=self.home)
        self.tcl.setvar(name='::TMP', value=self.tmpdir)

        # put any Python function registrations that need to be exposed to Tcl here
        # example:
        #register_function(tcl, pycommand)

        # maybe we'll make this automatic in the future

        self.register_function(self.tcl, self.tcl_select_row)
        self.register_function(self.tcl, self.tcl_select_all)
        self.register_function(self.tcl, self.tcl_exec_db)
        self.register_function(self.tcl, self.tcl_decrypt_string)
        self.register_function(self.tcl, self.tcl_encrypt_string)
        self.register_function(self.tcl, self.tcl_output)

        self.tcl.eval('source $::HOME/services/bin/cato_task_engine.tcl')
        try:
            tcl_str = self.tcl.eval('main_ce %s' % self.task_instance)
        except Exception as ex:
            err = self.tcl.getvar(name='errorInfo')
            self.output(err)
            raise ex

if __name__ == "__main__":

    ce = TaskEngine("cato_task_engine", task_instance)
    ce.startup()
    ce.output("hello world")
    ce.run()


