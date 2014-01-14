
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
 
from catolog import catolog
logger = catolog.get_logger(__name__)

from catocommon import catocommon

# FunctionCategories contains a list of all Category objects, 
# as well as a dictionary of function objects.
# it's useful for spinning categories and functions hierarchically, as when building the command toolbox
class FunctionCategories(object):
    Categories = []  # all the categories - NOTE that categories contain a list of their own functions
    Functions = {}  # a dictionary of ALL FUNCTIONS - for when you need to look up a function directly by name without recursing categories
    
    # method to load from the disk
    def Load(self, sFileName):
        logger.debug("Loading commands from extension file [%s]" % sFileName)
        xRoot = catocommon.ET.parse(sFileName)
        if xRoot is None:
            # crash... we can't do anything if the XML is busted
            logger.warning("Invalid XML [%s]" % sFileName)
        else:
            xCategories = xRoot.findall(".//category")
            for xCategory in xCategories:
                self.BuildCategory(xCategory)


    def BuildCategory(self, xCategory):

        catname = xCategory.get("name", None)
        # not crashing... just skipping
        if not catname:
            return None
        
        # if this category has already been added, find it and append to it instead
        cat = None
        for c in self.Categories:
            if c.Name == xCategory.get("name"):
                logger.debug("Appending extension category = [%s]" % c.Name)
                cat = c

        if not cat:
            # new category.
            cat = Category()
            cat.Name = xCategory.get("name")
            cat.Label = xCategory.get("label", cat.Name)
            cat.Description = xCategory.get("description", "")
            cat.Icon = xCategory.get("icon", "")
            logger.debug("Creating extension category = [%s]" % cat.Name)
            self.Categories.append(cat)

        # NOW, the category MIGHT have subcategories
        lst_subcats = xCategory.findall("subcategory")
        if len(lst_subcats) > 0:
            logger.debug("[%s] has subcategories." % cat.Name)
            for xSubcat in lst_subcats:
                self.BuildSubcategory(cat, xSubcat)

        # a Category can also have commands directly under it.
        commands = xCategory.findall("commands/command")
        for xFunction in commands:
            self.BuildFunction(cat, xFunction)


    def BuildSubcategory(self, catobj, xSubcategory):

        subcatname = xSubcategory.get("name", None)
        # not crashing... just skipping
        if not subcatname:
            return None
        
        # if this category has already been added, find it and append to it instead
        subcat = None
        for sc in catobj.Subcategories:
            if sc.Name == xSubcategory.get("name"):
                logger.debug("Appending to subcategory [%s]..." % sc.Name)
                subcat = sc

        if not subcat:
            # new category.
            subcat = Category()
            subcat.Name = xSubcategory.get("name")
            subcat.Label = xSubcategory.get("label", subcat.Name)
            subcat.Description = xSubcategory.get("description", "")
            subcat.Icon = xSubcategory.get("icon", "")
            logger.debug("Creating [%s] subcategory [%s]" % (catobj.Name, subcat.Name))
            catobj.Subcategories.append(subcat)

        commands = xSubcategory.findall("commands/command")
        for xFunction in commands:
            self.BuildFunction(subcat, xFunction)


    def BuildFunction(self, parent_obj, xFunction):
        # xParent might be a Category or a Subcategory, doesn't matter to us in here

        # not crashing... just skipping
        if not xFunction.get("name", None):
            return None

        # ok, minimal data is intact... proceed...
        fn = Function(parent_obj)
        fn.Name = xFunction.get("name")
        fn.Label = xFunction.get("label", fn.Name)
        fn.Description = xFunction.get("description", "")
        fn.Help = xFunction.get("help", "")
        fn.Icon = xFunction.get("icon", "")
        
        func = xFunction.find("function")
        if func is not None:
            fn.TemplateXML = catocommon.ET.tostring(func)
            fn.TemplateXDoc = func

        # logger.debug("Adding [%s] to [%s]" % (fn.Name, parent_obj.Name))
        parent_obj.Functions.append(fn)
        
        # while we're here, it's a good place to append this funcion to the 
        # complete dict on this class
        self.Functions[fn.Name] = fn

class Category(object):
    def __init__(self):
        self.Name = None
        self.Label = None
        self.Description = None
        self.Icon = None
        # Category MIGHT contain either a list of Subcategory OR Function objects, but never both.
        self.Subcategories = []
        self.Functions = []

class Subcategory(object):
    def __init__(self):
        self.Name = None
        self.Label = None
        self.Description = None
        self.Icon = None
        # Subcategory CONTAINS a list of Function objects
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
