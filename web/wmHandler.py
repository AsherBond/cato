
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
        return catocommon.FindAndCall(method)

    def POST(self, method):
        return catocommon.FindAndCall(method)
