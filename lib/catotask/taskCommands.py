
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
 
try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET


from catoui import uiCommon as UI

# FunctionCategories contains a list of all Category objects, 
# as well as a dictionary of function objects.
# it's useful for spinning categories and functions hierarchically, as when building the command toolbox
class FunctionCategories(object):
    Categories = []  # all the categories - NOTE that categories contain a list of their own functions
    Functions = {}  # a dictionary of ALL FUNCTIONS - for when you need to look up a function directly by name without recursing categories
    
    # method to load from the disk
    def Load(self, sFileName):
        try:
            xRoot = ET.parse(sFileName)
            if xRoot == None:
                # crash... we can't do anything if the XML is busted
                return False
            else:
                xCategories = xRoot.findall(".//category")
                for xCategory in xCategories:
                    cat = self.BuildCategory(xCategory)
                    if cat != None:
                        self.Categories.append(cat)
                        
                return True
        except Exception as ex:
            raise ex

    # append extension files to the class
    def Append(self, sFileName):
        try:
            UI.log_nouser("Parsing extension file " + sFileName, 4)
            xRoot = ET.parse(sFileName)
            if xRoot == None:
                # crash... we can't do anything if the XML is busted
                return False
            else:
                xCategories = xRoot.findall(".//category")
                for xCategory in xCategories:
                    cat = self.BuildCategory(xCategory)
                    if cat != None:
                        UI.log_nouser("Parsing extension category = " + cat.Name, 4)
                        self.Categories.append(cat)
                        
                return True
        except Exception as ex:
            # appending does not throw an exception, just a warning in the log
            UI.log_nouser("WARNING: Error parsing extension command file [" + sFileName + "]. " + ex.__str__(), 0)

    def BuildCategory(self, xCategory):

        catname = xCategory.get("name", None)
        
        # not crashing... just skipping
        if not catname:
            return None
        
        # if this category has already been added, find it and append to it instead
        cat = None
        for c in self.Categories:
            if c.Name == xCategory.get("name"):
                cat = c

        if not cat:
            # new category.
            cat = Category()
            cat.Name = xCategory.get("name")
            cat.Label = xCategory.get("label", cat.Name)
            cat.Description = xCategory.get("description", "")
            cat.Icon = xCategory.get("icon", "")
    

        # load up this category with it's functions
        for xFunction in xCategory.findall("commands/command"):
            # not crashing... just skipping
            if not xCategory.get("name", None):
                return None

            # ok, minimal data is intact... proceed...
            fn = Function(cat)
            fn.Name = xFunction.get("name")
            fn.Label = xFunction.get("label", fn.Name)
            fn.Description = xFunction.get("description", "")
            fn.Help = xFunction.get("help", "")
            fn.Icon = xFunction.get("icon", "")
            
            func = xFunction.find("function")
            if func is not None:
                fn.TemplateXML = ET.tostring(func)
                fn.TemplateXDoc = func

            cat.Functions.append(fn)
            
            # while we're here, it's a good place to append this funcion to the 
            # complete dict on this class
            self.Functions[fn.Name] = fn

        return cat


class Category(object):
    def __init__(self):
        self.Name = None
        self.Label = None
        self.Description = None
        self.Icon = None
        # Category CONTAINS a list of Function objects
        self.Functions = []

class Function(object):
    def __init__(self, cat):
        self.Name = None
        self.Label = None
        self.Description = None
        self.Help = None
        self.Icon = None
        self.Category = cat  # Function has a parent Category
        self.TemplateXML = None
        self.TemplateXDoc = None
