
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
 
 This is the default handler for any urls not defined in cato_admin_ui.
 (web.py required explicit url mapping)
 
 web.py will instantiate this class, and invoke either the GET or POST method.
 
 We take it from there, parse the URI, and try to load the right module 
 and find the proper function to handle the request.
 
"""

from catocommon import catocommon

class wmHandler:
    #the GET and POST methods here are hooked by web.py.
    #whatever method is requested, that function is called.
    def GET(self, method):
        return self.FindAndCall(method)

    def POST(self, method):
        return self.FindAndCall(method)

    def FindAndCall(self, method):
        """
        Several rules here:
        1) First, we look in this class for the method.  This shouldn't really happen,
            but if we decided at some point to put a few functions here... fine.
        """
        try:
            self.db = catocommon.new_conn()
            # does it have a / ?  if so let's look for another class.
            # NOTE: this isn't recursive... only the first value before a / is the class
            modname = ""
            methodname = method
            
            if "/" in method:
                modname, methodname = method.split('/', 1)
            
            if modname:    
                try:
                    mod = __import__(modname, None, None, modname)
                    cls = getattr(mod, modname, None)
                    if cls:
                        cls.db = self.db
                        methodToCall = getattr(cls(), methodname, None)
                    else:
                        return "Class [%s] does not exist or could not be loaded." % modname
                except ImportError as ex:
                    print ex.__str__()
                    return "Module [%s] does not exist." % modname
            else:
                methodToCall = getattr(self, methodname, None)

            if methodToCall:
                if callable(methodToCall):
                    return methodToCall()

            return "Method [%s] does not exist or could not be called." % method
            
        except Exception as ex:
            raise ex
        finally:
            if self.db.conn.socket:
                self.db.close()
