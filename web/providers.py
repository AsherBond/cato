
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

import json
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import cloud
from catocommon import catocommon

class CloudProviders(dict):
    #CloudProviders is a dictionary of Provider objects

    #the constructor requires an ET Document
    def __init__(self):
        try:
            xRoot = ET.parse("../conf/cloud_providers.xml")
            if not xRoot:
                raise Exception("Error: Invalid or missing Cloud Providers XML.")
            else:
                xProviders = xRoot.findall("providers/provider")
                for xProvider in xProviders:
                    p_name = xProvider.get("name", None)

                    if p_name == None:
                        raise Exception("Cloud Providers XML: All Providers must have the 'name' attribute.")
                    
                    test_product = xProvider.get("test_product", None)
                    test_object = xProvider.get("test_object", None)
                    user_defined_clouds = xProvider.get("user_defined_clouds", True)
                    user_defined_clouds = (False if user_defined_clouds == "false" else True)
                     
                    pv = Provider(p_name, test_product, test_object, user_defined_clouds)
                    xClouds = xProvider.findall("clouds/cloud")
                    #if this provider has hardcoded clouds... get them
                    for xCloud in xClouds:
                        if xCloud.get("id", None) == None:
                            raise Exception("Cloud Providers XML: All Clouds must have the 'id' attribute.")
                        if xCloud.get("name", None) == None:
                            raise Exception("Cloud Providers XML: All Clouds must have the 'name' attribute.")
                        if xCloud.get("api_url", None) == None:
                            raise Exception("Cloud Providers XML: All Clouds must have the 'api_url' attribute.")
                        if xCloud.get("api_protocol", None) == None:
                            raise Exception("Cloud Providers XML: All Clouds must have the 'api_protocol' attribute.")
                        #region is an optional attribute
                        sRegion = xCloud.get("region", "")
                        c = cloud.Cloud()
                        c.FromArgs(pv, False, xCloud.get("id", None), xCloud.get("name", None), xCloud.get("api_url", None), xCloud.get("api_protocol", None), sRegion)
                        if c.ID:
                            pv.Clouds.append(c)

                    #Let's also add any clouds that may be in the database...
                    #IF the "user_defined_clouds" flag is set.
                    if pv.UserDefinedClouds:
                        sSQL = "select cloud_id, cloud_name, api_url, api_protocol from clouds where provider = '" + pv.Name + "' order by cloud_name"
                        db = catocommon.new_conn()
                        dt = db.select_all_dict(sSQL)
                        if dt:
                            for dr in dt:
                                c = cloud.Cloud()
                                c.FromArgs(pv, True, dr["cloud_id"], dr["cloud_name"], dr["api_url"], dr["api_protocol"], "")
                                if c:
                                    pv.Clouds.append(c)
                        else:
                            # DO NOT raise an exception here - user defined clouds are not required.
                            # but print a warning
                            print "Cloud Providers XML: Warning - Provider [%s] allows user defined Clouds, but none exist in the database." % pv.Name
                    
                    #get the cloudobjecttypes for this provider.                    
                    xProducts = xProvider.findall("products/product")
                    for xProduct in xProducts:
                        p_name = xProduct.get("name", None)

                        if p_name == None:
                            raise Exception("Cloud Providers XML: All Products must have the 'name' attribute.")
    
                        p = Product(pv)
                        p.Name = xProduct.get("name", None)
                        #use the name for the label if it doesn't exist.
                        p.Label = xProduct.get("label", p_name)
                        p.APIUrlPrefix = xProduct.get("api_url_prefix", None)
                        p.APIUri = xProduct.get("api_uri", None)
                        p.APIVersion = xProduct.get("api_version", None)
                        
                        #the product contains object type definitions
                        xTypes = xProduct.findall("object_types/type")
                        for xType in xTypes:
                            if xType.get("id", None) == None:
                                raise Exception("Cloud Providers XML: All Object Types must have the 'id' attribute.")
                            if xType.get("label", None) == None:
                                raise Exception("Cloud Providers XML: All Object Types must have the 'label' attribute.")
                            
                            cot = CloudObjectType(p)
                            cot.ID = xType.get("id")
                            cot.Label = xType.get("label")
                            cot.APICall = xType.get("api_call", None)
                            cot.APIRequestGroupFilter = xType.get("request_group_filter", None)
                            cot.APIRequestRecordFilter = xType.get("request_record_filter", None)
                            cot.XMLRecordXPath = xType.get("xml_record_xpath", None)

                            #the type contains property definitions
                            xProperties = xType.findall("property")
                            for xProperty in xProperties:
                                # name="ImageId" label="" xpath="imageId" id_field="1" has_icon="0" short_list="1" sort_order="1"
                                if xProperty.get("name", None) == None:
                                    raise Exception("Cloud Providers XML: All Object Type Properties must have the 'name' attribute.")
                                
                                cotp = CloudObjectTypeProperty(cot)
                                cotp.Name = xProperty.get("name")
                                cotp.XPath = xProperty.get("xpath", None)
                                lbl = xProperty.get("label", None)
                                cotp.Label = (lbl if lbl else cotp.Name)
                                cotp.SortOrder = xProperty.get("sort_order", None)
                                cotp.IsID = (True if xProperty.get("id_field", False) == "1" else False)
                                cotp.HasIcon = (True if xProperty.get("has_icon") == "1" else False)
                                cotp.ShortList = (True if xProperty.get("short_list") == "1" else False)
                                cotp.ValueIsXML = (True if xProperty.get("value_is_xml") == "1" else False)
                                
                                cot.Properties.append(cotp)
                            p.CloudObjectTypes[cot.ID] = cot
                        pv.Products[p.Name] = p
                    self[pv.Name] = pv
        except Exception, ex:
            raise ex
        finally:
            db.close()

class Provider(object):
    Name = None
    TestProduct = None
    TestObject = None
    UserDefinedClouds = None
    Clouds = {}
    Products = {}
    
    def __init__(self, sName, sTestProduct, sTestObject, bUserDefinedClouds):
        self.Name = sName
        self.TestProduct = sTestProduct
        self.TestObject = sTestObject
        self.UserDefinedClouds = bUserDefinedClouds
        self.Clouds = []
        self.Products = {}

    @staticmethod
    def FromName(sProvider):
        try:
            cp = CloudProviders()
            if cp == None:
                raise Exception("Error building Provider object: Unable to get CloudProviders.")
            if cp.has_key(sProvider):
                return cp[sProvider]
            else:
                raise Exception("Provider [" + sProvider + "] does not exist in the cloud_providers session xml.")
        except Exception, ex:
            raise ex

    def GetAllObjectTypes(self):
        try:
            cots = {}
            
            for p in self.Products.itervalues():
                for cot in p.CloudObjectTypes.itervalues():
                    if cot is not None:
                        cots[cot.ID] = cot
            return cots
        except Exception, ex:
            raise ex


    def GetObjectTypeByName(self, sObjectType):
        """Loops all the products, so you can get an object type by name without knowing the product."""
        cot = None
        for p in self.Products.itervalues():
            # print "looking for %s in %s" % (sObjectType, p.Name)
            try:
                cot = p.CloudObjectTypes[sObjectType]
                if cot:
                    return cot
            except Exception:
                """"""
                #don't crash while it's iterating, it may find it in the next object.
                #don't worry, we'll return null if it doesn't find anything.
                    
        return None

    def AsJSON(self):
        try:
            # this is built manually, because clouds have a provider object, which would be recursive.
            sb = []
            sb.append("{")
            sb.append("\"%s\" : \"%s\"," % ("Name", self.Name))
            sb.append("\"%s\" : \"%s\"," % ("TestProduct", self.TestProduct))
            sb.append("\"%s\" : \"%s\"," % ("UserDefinedClouds", self.UserDefinedClouds))
            sb.append("\"%s\" : \"%s\"," % ("TestObject", self.TestObject))
            
            # the clouds for this provider
            sb.append("\"Clouds\" : {")
            lst = []
            for c in self.Clouds:
                s = "\"%s\" : %s" % (c.ID, c.AsJSON())
                lst.append(s)
            sb.append(",".join(lst))

            sb.append("}, ")

            
            # the products and object types
            sb.append("\"Products\" : {")
            lst = []
            for prod in self.Products.itervalues():
                s = "\"%s\" : %s" % (prod.Name, prod.AsJSON())
                lst.append(s)
            sb.append(",".join(lst))
            sb.append("}")

            
            sb.append("}")
            return "".join(sb)
        except Exception, ex:
            raise ex

class Product(object):
    ParentProviderName = None
    Name = None
    Label = None
    APIUrlPrefix = None
    APIUri = None
    APIVersion = None
    #Product CONTAINS a named dictionary of CloudObjectTypes
    CloudObjectTypes = {}
    
    #constructor
    def __init__(self, parent):
        self.ParentProviderName = parent.Name
        self.CloudObjectTypes = {}

    def IsValidForCalls(self):
        if self.Name:
            return True
        return False
    
    def AsJSON(self):
        try:
            # this is built manually, because clouds have a provider object, which would be recursive.
            sb = []
            sb.append("{")
            sb.append("\"%s\" : \"%s\"," % ("Name", self.Name))
            sb.append("\"%s\" : \"%s\"," % ("Label", self.Label))
            sb.append("\"%s\" : \"%s\"," % ("APIUrlPrefix", self.APIUrlPrefix))
            sb.append("\"%s\" : \"%s\"," % ("APIUri", self.APIUri))
            sb.append("\"%s\" : \"%s\"," % ("APIVersion", self.APIVersion))
            
            # the clouds for this provider
            sb.append("\"CloudObjectTypes\" : {")
            lst = []
            for c in self.CloudObjectTypes.itervalues():
                s = "\"%s\" : %s" % (c.ID, c.AsJSON())
                lst.append(s)
            sb.append(",".join(lst))
            sb.append("}")

            sb.append("}")
            return "".join(sb)
        except Exception, ex:
            raise ex
       
class CloudObjectType(object):
    ParentProduct = None
    ID = None
    Label = None
    APICall = None
    APIRequestGroupFilter = None
    APIRequestRecordFilter = None
    XMLRecordXPath = None
    Properties = [] #!!! This is a list, not a dictionary
    Instances = {} # a dictionary of results, keyed by the unique 'id'
    
    #constructor
    def __init__(self, parent):
        self.ParentProduct = parent
        self.Properties = []
        self.Instances = {}

    def IsValidForCalls(self):
        if self.XMLRecordXPath and self.ID:
            return True
        return False

    def AsJSON(self):
        try:
            sb = []
            sb.append("{")
            sb.append("\"%s\" : \"%s\"," % ("ID", self.ID))
            sb.append("\"%s\" : \"%s\"," % ("Label", self.Label))
            sb.append("\"%s\" : \"%s\"," % ("APICall", self.APICall))
            sb.append("\"%s\" : \"%s\"," % ("APIRequestGroupFilter", self.APIRequestGroupFilter))
            sb.append("\"%s\" : \"%s\"," % ("APIRequestRecordFilter", self.APIRequestRecordFilter))
            sb.append("\"%s\" : \"%s\"," % ("XMLRecordXPath", self.XMLRecordXPath))
            
            sb.append("\"Properties\" : [")
            lst = []
            for p in self.Properties:
                lst.append(p.AsJSON())
            sb.append(",".join(lst))
            sb.append("]")

            sb.append("}")
            return "".join(sb)
        except Exception, ex:
            raise ex
   
class CloudObjectTypeProperty:
    ParentObjectTypeID = None
    Name = None
    Label = None
    XPath = None
    SortOrder = None
    HasIcon = False
    IsID = False
    ShortList = True
    ValueIsXML = False
    Value = None
    
    #constructor
    def __init__(self, parent):
        self.ParentObjectTypeID = parent.ID
        self.Value = None

    def AsJSON(self):
        return json.dumps(self.__dict__)
    
    