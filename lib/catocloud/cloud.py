
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
    THIS CLASS has it's own database connections.
    Why?  Because it isn't only used by the UI.
"""
import os
import json
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from catocommon import catocommon

# Note: this is not a container for CloudAccount objects - it's just a rowset from the database
# with an AsJSON method.
# why? Because the CloudAccount objects contain a full set of Provider information - stuff
# we don't need for list pages and dropdowns.
class Clouds(object): 
    rows = {}
        
    def __init__(self, sFilter=""):
        try:
            sWhereString = ""
            if sFilter:
                aSearchTerms = sFilter.split()
                for term in aSearchTerms:
                    if term:
                        sWhereString += " and (cloud_name like '%%" + term + "%%' " \
                            "or provider like '%%" + term + "%%' " \
                            "or api_url like '%%" + term + "%%') "
    
            sSQL = """select cloud_id, cloud_name, provider, api_url, api_protocol
                from clouds
                where 1=1 %s order by provider, cloud_name""" % sWhereString
            
            db = catocommon.new_conn()
            self.rows = db.select_all_dict(sSQL)
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.rows)
        except Exception as ex:
            raise ex


class Cloud(object):
    def __init__(self):
        self.IsUserDefined = True
        self.ID = None
        self.Name = None
        self.APIUrl = None
        self.APIProtocol = None
        self.Region = None
        self.Provider = None

    #the default constructor (manual creation)
    def FromArgs(self, p, bUserDefined, sID, sName, sAPIUrl, sAPIProtocol, sRegion):
        if not sID:
            raise Exception("Error building Cloud object: Cloud ID is required.")

        self.IsUserDefined = bUserDefined
        self.ID = sID
        self.Name = sName
        self.APIUrl = sAPIUrl
        self.APIProtocol = sAPIProtocol
        self.Region = sRegion
        self.Provider = p

    def FromID(self, sCloudID):
        try:
            if not sCloudID:
                raise Exception("Error building Cloud object: Cloud ID is required.")
            
            #search for the sCloudID in the CloudProvider Class -AND- the database
            cp = CloudProviders()
            if not cp:
                raise Exception("Error building Cloud object: Unable to get CloudProviders.")
            #check the CloudProvider class first ... it *should be there unless something is wrong.
            for p in cp.itervalues():
                for c in p.Clouds:
                    if c.ID == sCloudID:
                        self.IsUserDefined = c.IsUserDefined
                        self.ID = c.ID
                        self. Name = c.Name
                        self.APIUrl = c.APIUrl
                        self.APIProtocol = c.APIProtocol
                        self.Region = c.Region
                        self.Provider = c.Provider
                        
                        return
            
            #well, if we got here we have a problem... the ID provided wasn't found anywhere.
            #this should never happen, so bark about it.
            raise Exception("Warning - Unable to find a Cloud with id [%s] on any Providers." % sCloudID)   
        except Exception as ex:
            raise ex

    def IsValidForCalls(self):
        if self.APIUrl and self.APIProtocol:
            return True
        return False

    def AsJSON(self):
        try:
            sb = []
            sb.append("{")
            sb.append("\"%s\" : \"%s\"," % ("ID", self.ID))
            sb.append("\"%s\" : \"%s\"," % ("Name", self.Name))
            sb.append("\"%s\" : \"%s\"," % ("Provider", self.Provider.Name))
            sb.append("\"%s\" : \"%s\"," % ("APIUrl", self.APIUrl))
            sb.append("\"%s\" : \"%s\"," % ("APIProtocol", self.APIProtocol))
            sb.append("\"%s\" : \"%s\"" % ("Region", self.Region))
            sb.append("}")
            return "".join(sb)
        except Exception as ex:
            raise ex

    #STATIC METHOD
    #creates this Cloud as a new record in the db
    #and returns the object
    @staticmethod
    def DBCreateNew(sCloudName, sProvider, sAPIUrl, sAPIProtocol):
        try:
            sSQL = ""
            sNewID = catocommon.new_guid()
            sSQL = "insert into clouds (cloud_id, cloud_name, provider, api_url, api_protocol)" \
                " values ('" + sNewID + "'," + "'" + sCloudName + "'," + "'" + sProvider + "'," + "'" + sAPIUrl + "'," + "'" + sAPIProtocol + "')"
            db = catocommon.new_conn()
            if not db.exec_db_noexcep(sSQL):
                if db.error == "key_violation":
                    return None, "A Cloud with that name already exists.  Please select another name."
                else:
                    return None, db.error
            
            #now it's inserted and in the session... lets get it back from the db as a complete object for confirmation.
            c = Cloud()
            c.FromID(sNewID)
            #yay!
            return c, None
        except Exception as ex:
            raise ex
        finally:
            db.close()

    #INSTANCE METHOD
    #updates the current Cloud object to the db
    def DBUpdate(self):
        try:
            db = catocommon.new_conn()
            #of course we do nothing if this cloud was hardcoded in the xml
            #just return success, which should never happen since the user can't get to edit a hardcoded Cloud anyway.
            if not self.IsUserDefined:
                return True
            #what's the original name?
            sSQL = "select cloud_name from clouds where cloud_id = '" + self.ID + "'"
            sOriginalName = db.select_col_noexcep(sSQL)
            if not sOriginalName:
                if db.error:
                    raise Exception("Error getting original cloud name:" + db.error)
            
            sSQL = "update clouds set" + " cloud_name = '" + self.Name + "'," \
                " provider = '" + self.Provider.Name + "'," \
                " api_protocol = '" + self.APIProtocol + "'," \
                " api_url = '" + self.APIUrl + "'" \
                " where cloud_id = '" + self.ID + "'"
            if not db.exec_db_noexcep(sSQL):
                if db.error == "key_violation":
                    return False, "A Cloud with that name already exists.  Please select another name."
                else:
                    return False, db.error

            return True, None
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()


# Note: this is not a container for CloudAccount objects - it's just a rowset from the database
# with an AsJSON method.
# why? Because the CloudAccount objects contain a full set of Provider information - stuff
# we don't need for list pages and dropdowns.
class CloudAccounts(object): 
    rows = {}
        
    def __init__(self, sFilter="", sProvider=""):
        try:
            sWhereString = ""
            if sFilter:
                aSearchTerms = sFilter.split()
                for term in aSearchTerms:
                    if term:
                        sWhereString += " and (account_name like '%%" + term + "%%' " \
                            "or account_number like '%%" + term + "%%' " \
                            "or provider like '%%" + term + "%%' " \
                            "or login_id like '%%" + term + "%%') "
    
            # if a sProvider arg is passed, we explicitly limit to this provider
            if sProvider:
                sWhereString += " and provider = '%s'" % sProvider
                
            sSQL = """select account_id, account_name, account_number, provider, login_id, auto_manage_security,
                case is_default when 1 then 'Yes' else 'No' end as is_default,
                (select count(*) from ecosystem where account_id = cloud_account.account_id) as has_ecosystems
                from cloud_account
                where 1=1 %s order by is_default desc, account_name""" % sWhereString
            
            db = catocommon.new_conn()
            self.rows = db.select_all_dict(sSQL)
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.rows)
        except Exception as ex:
            raise ex

class CloudAccount(object):
    def __init__(self):
        self.ID = None
        self.Name = None
        self.AccountNumber = None
        self.LoginID = None
        self.LoginPassword = None
        self.IsDefault = None
        self.Provider = None

    def FromID(self, sAccountID):
        try:
            if not sAccountID:
                raise Exception("Error building Cloud Account object: Cloud Account ID is required.");    
            
            sSQL = "select account_name, account_number, provider, login_id, login_password, is_default" \
                " from cloud_account" \
                " where account_id = '" + sAccountID + "'"

            db = catocommon.new_conn()
            dr = db.select_row_dict(sSQL)
            
            if dr is not None:
                self.ID = sAccountID
                self.Name = dr["account_name"]
                self.AccountNumber = ("" if not dr["account_number"] else dr["account_number"])
                self.LoginID = ("" if not dr["login_id"] else dr["login_id"])
                self.LoginPassword = ("" if not dr["login_password"] else catocommon.cato_decrypt(dr["login_password"]))
                self.IsDefault = (True if dr["is_default"] == 1 else False)
                
                # find a provider object
                cp = CloudProviders()
                if not cp:
                    raise Exception("Error building Cloud Account object: Unable to get CloudProviders.")
                    return

                #check the CloudProvider class first ... it *should be there unless something is wrong.
                if cp.has_key(dr["provider"]):
                    self.Provider = cp[dr["provider"]]
                else:
                    raise Exception("Provider [" + dr["provider"] + "] does not exist in the cloud_providers session xml.")

            else: 
                raise Exception("Unable to build Cloud Account object. Either no Cloud Accounts are defined, or no Account with ID [" + sAccountID + "] could be found.")
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def IsValidForCalls(self):
        if self.LoginID and self.LoginPassword:
            return True
        return False

    def AsJSON(self):
        try:
            sb = []
            sb.append("{")
            sb.append("\"%s\" : \"%s\"," % ("ID", self.ID))
            sb.append("\"%s\" : \"%s\"," % ("Name", self.Name))
            sb.append("\"%s\" : \"%s\"," % ("Provider", self.Provider.Name))
            sb.append("\"%s\" : \"%s\"," % ("AccountNumber", self.AccountNumber))
            sb.append("\"%s\" : \"%s\"," % ("LoginID", self.LoginID))
            sb.append("\"%s\" : \"%s\"," % ("LoginPassword", self.LoginPassword))
            sb.append("\"%s\" : \"%s\"," % ("IsDefault", self.IsDefault))
            
            # the clouds hooked to this account
            sb.append("\"Clouds\" : {")
            lst = []
            for c in self.Provider.Clouds:
                #stick em all in a list for now
                s = "\"%s\" : %s" % (c.ID, c.AsJSON())
                lst.append(s)
            #join the list using commas!
            sb.append(",".join(lst))

            sb.append("}")

            
            sb.append("}")
            return "".join(sb)
        except Exception as ex:
            raise ex

    #STATIC METHOD
    #creates this Cloud as a new record in the db
    #and returns the object
    @staticmethod
    def DBCreateNew(sAccountName, sAccountNumber, sProvider, sLoginID, sLoginPassword, sIsDefault):
        try:
            db = catocommon.new_conn()

            # if there are no rows yet, make this one the default even if the box isn't checked.
            if sIsDefault == "0":
                iExists = -1
                
                sSQL = "select count(*) as cnt from cloud_account"
                iExists = db.select_col_noexcep(sSQL)
                if iExists == None:
                    if db.error:
                        db.tran_rollback()
                        return None, "Unable to count Cloud Accounts: " + db.error
                
                if iExists == 0:
                    sIsDefault = "1"

            sNewID = catocommon.new_guid()
            sPW = (catocommon.cato_encrypt(sLoginPassword) if sLoginPassword else "")
            
            sSQL = "insert into cloud_account" \
                " (account_id, account_name, account_number, provider, is_default, login_id, login_password, auto_manage_security)" \
                " values ('" + sNewID + "'," \
                "'" + sAccountName + "'," \
                "'" + sAccountNumber + "'," \
                "'" + sProvider + "'," \
                "'" + sIsDefault + "'," \
                "'" + sLoginID + "'," \
                "'" + sPW + "'," \
                "0)"
            
            if not db.tran_exec_noexcep(sSQL):
                if db.error == "key_violation":
                    sErr = "A Cloud Account with that name already exists.  Please select another name."
                    return None, sErr
                else: 
                    return None, db.error
            
            # if "default" was selected, unset all the others
            if sIsDefault == "1":
                sSQL = "update cloud_account set is_default = 0 where account_id <> '" + sNewID + "'"
                if not db.tran_exec_noexcep(sSQL):
                    raise Exception(db.error)

            db.tran_commit()
            
            # now it's inserted... lets get it back from the db as a complete object for confirmation.
            ca = CloudAccount()
            ca.FromID(sNewID)

            # yay!
            return ca, None
        except Exception as ex:
            raise ex
        finally:
            db.close()

    def DBUpdate(self):
        try:
            db = catocommon.new_conn()
            
            #  only update the passwword if it has changed
            sNewPassword = ""
            if self.LoginPassword != "($%#d@x!&":
                sNewPassword = (", login_password = '" + catocommon.cato_encrypt(self.LoginPassword) + "'" if self.LoginPassword else "")

            sSQL = "update cloud_account set" \
                    " account_name = '" + self.Name + "'," \
                    " account_number = '" + self.AccountNumber + "'," \
                    " provider = '" + self.Provider.Name + "'," \
                    " is_default = '" + ("1" if self.IsDefault else "0") + "'," \
                    " auto_manage_security = 0," \
                    " login_id = '" + self.LoginID + "'" + \
                    sNewPassword + \
                    " where account_id = '" + self.ID + "'"
            
            if not db.exec_db_noexcep(sSQL):
                if db.error == "key_violation":
                    sErr = "A Cloud Account with that name already exists.  Please select another name."
                    return False, sErr
                else: 
                    return False, db.error
            
            # if "default" was selected, unset all the others
            if self.IsDefault:
                sSQL = "update cloud_account set is_default = 0 where account_id <> '" + self.ID + "'"
                # not worth failing... we'll just end up with two defaults.
                db.exec_db_noexcep(sSQL)

            return True, None
        except Exception as ex:
            raise ex
        finally:
            db.close()

class CloudProviders(dict):
    #CloudProviders is a dictionary of Provider objects

    #the constructor requires an ET Document
    def __init__(self):
        try:
            base_path = catocommon._get_base_path()
            filename = os.path.join(base_path, "conf/cloud_providers.xml")
            if not os.path.isfile(filename):
                raise Exception("conf/cloud_providers.xml file does not exist.")
            xRoot = ET.parse(filename)
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
                        c = Cloud()
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
                                c = Cloud()
                                c.FromArgs(pv, True, dr["cloud_id"], dr["cloud_name"], dr["api_url"], dr["api_protocol"], "")
                                if c:
                                    pv.Clouds.append(c)
                        else:
                            # DO NOT raise an exception here - user defined clouds are not required.
                            # but print a warning
                            print("Cloud Providers XML: Warning - Provider [%s] allows user defined Clouds, but none exist in the database." % pv.Name)
                    
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
                        p.Type = xProduct.get("type", None)
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
        except Exception as ex:
            raise ex
        finally:
            db.close()

class Provider(object):
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
        except Exception as ex:
            raise ex

    def GetAllObjectTypes(self):
        try:
            cots = {}
            
            for p in self.Products.itervalues():
                for cot in p.CloudObjectTypes.itervalues():
                    if cot is not None:
                        cots[cot.ID] = cot
            return cots
        except Exception as ex:
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

    def GetProductByType(self, sProductType):
        """Get a Product by it's Type instead of Name."""
        for p in self.Products.itervalues():
            if p.Type == sProductType:
                return p
                    
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
        except Exception as ex:
            raise ex

class Product(object):
    def __init__(self, parent):
        self.Name = None
        self.Label = None
        self.Type = None
        self.APIUrlPrefix = None
        self.APIUri = None
        self.APIVersion = None
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
            sb.append("\"%s\" : \"%s\"," % ("Type", self.Type))
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
        except Exception as ex:
            raise ex
       
class CloudObjectType(object):
    def __init__(self, parent):
        self.ID = None
        self.Label = None
        self.APICall = None
        self.APIRequestGroupFilter = None
        self.APIRequestRecordFilter = None
        self.XMLRecordXPath = None
        self.ParentProduct = parent
        self.Properties = [] #!!! This is a list, not a dictionary
        self.Instances = {} # a dictionary of results, keyed by the unique 'id'

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
        except Exception as ex:
            raise ex
   
class CloudObjectTypeProperty:
    def __init__(self, parent):
        self.Name = None
        self.Label = None
        self.XPath = None
        self.SortOrder = None
        self.HasIcon = False
        self.IsID = False
        self.ShortList = True
        self.ValueIsXML = False
        self.ParentObjectTypeID = parent.ID
        self.Value = None

    def AsJSON(self):
        return json.dumps(self.__dict__)
