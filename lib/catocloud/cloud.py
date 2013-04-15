
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
try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

from catoconfig import catoconfig
from catocommon import catocommon
from catoerrors import InfoException

from catolog import catolog
logger = catolog.get_logger(__name__)

# Note: this is not a container for CloudAccount objects - it's just a rowset from the database
# with an AsJSON method.
# why? Because the CloudAccount objects contain a full set of Provider information - stuff
# we don't need for list pages and dropdowns.
class Clouds(object): 
    rows = {}
        
    def __init__(self, sFilter=""):
        db = catocommon.new_conn()
        sWhereString = ""
        if sFilter:
            aSearchTerms = sFilter.split()
            for term in aSearchTerms:
                if term:
                    sWhereString += " and (c.cloud_name like '%%" + term + "%%' " \
                        "or ca.account_name like '%%" + term + "%%' " \
                        "or c.provider like '%%" + term + "%%' " \
                        "or c.api_url like '%%" + term + "%%') "

        sSQL = """select 
            c.cloud_id as ID, 
            c.cloud_name as Name, 
            c.provider as Provider, 
            c.api_url as APIUrl, 
            c.api_protocol as APIProtocol, 
            ca.account_name as DefaultAccount
            from clouds c
            left outer join cloud_account ca on c.default_account_id = ca.account_id
            where 1=1 %s order by c.provider, c.cloud_name""" % sWhereString
            
        rows = db.select_all_dict(sSQL)
        self.rows = rows if rows else {}
        db.close()

    def AsJSON(self):
        return catocommon.ObjectOutput.IterableAsJSON(self.rows)

    def AsXML(self):
        return catocommon.ObjectOutput.IterableAsXML(self.rows, "Clouds", "Cloud")

    def AsText(self, delimiter=None):
        return catocommon.ObjectOutput.IterableAsText(self.rows, ['ID', 'Name', 'Provider', 'APIUrl', 'APIProtocol', 'DefaultAccount'], delimiter)

class Cloud(object):
    def __init__(self):
        self.IsUserDefined = True
        self.ID = None
        self.Name = None
        self.APIUrl = None
        self.APIProtocol = None
        self.Region = None
        self.Provider = None
        self.DefaultAccount = None

    # NOTE: there is a possible circular reference between clouds and accounts.
    # So, to avoid those loops, this is an instance method that populates the attribute
    def GetDefaultAccount(self):
        db = catocommon.new_conn()
        
        sSQL = """select default_account_id from clouds where cloud_id = '%s'""" % self.ID
        row = db.select_row_dict(sSQL)
        db.close()
        if row:
            if row["default_account_id"]:
                ca = CloudAccount()
                ca.FromID(row["default_account_id"])
                if ca.ID:
                    self.DefaultAccount = ca
                    return ca

        return None
        
 
    # the default constructor (manual creation)
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
        if not sCloudID:
            raise Exception("Error building Cloud object: Cloud ID is required.")
        
        cp = CloudProviders()
        if not cp:
            raise Exception("Error building Cloud object: Unable to get CloudProviders.")
        # check the CloudProvider class first ... it *should be there unless something is wrong.
        for p in cp.itervalues():
            for c in p.Clouds:
                if c.ID == sCloudID:
                    self.IsUserDefined = c.IsUserDefined
                    self.ID = c.ID
                    self.Name = c.Name
                    self.APIUrl = c.APIUrl
                    self.APIProtocol = c.APIProtocol
                    self.Region = c.Region
                    self.Provider = c.Provider
                    
                    return
        
        # well, if we got here we have a problem... the ID provided wasn't found anywhere.
        # this should never happen, so bark about it.
        logger.warning("Unable to find a Cloud with id [%s] on any Providers." % sCloudID)   
        return

    def FromName(self, name):
        if not name:
            raise Exception("Error building Cloud object: Cloud Name is required.")
        
        cp = CloudProviders()
        if not cp:
            raise Exception("Error building Cloud object: Unable to get CloudProviders.")
        # check the CloudProvider class first ... it *should be there unless something is wrong.
        for p in cp.itervalues():
            for c in p.Clouds:
                # NOTE: we will match on the name OR id.
                if c.Name == name or c.ID == name:
                    self.IsUserDefined = c.IsUserDefined
                    self.ID = c.ID
                    self.Name = c.Name
                    self.APIUrl = c.APIUrl
                    self.APIProtocol = c.APIProtocol
                    self.Region = c.Region
                    self.Provider = c.Provider
                    
                    return
        
        # well, if we got here we have a problem... the name provided wasn't found anywhere.
        # this should never happen, so bark about it.
        logger.warning("Unable to find a Cloud with name [%s] on any Providers." % name)   
        return

    def IsValidForCalls(self):
        if self.APIUrl and self.APIProtocol:
            return True
        return False

    def AsJSON(self):
        # convert the Provider object to a dictionary for serialization
        self.Provider = self.Provider.__dict__
        self.GetDefaultAccount()
        if self.DefaultAccount:
            del self.DefaultAccount.Provider
            self.DefaultAccount = self.DefaultAccount.__dict__
        else:
            self.DefaultAccount = ""
        
        return catocommon.ObjectOutput.AsJSON(self.__dict__)

    # STATIC METHOD
    # creates this Cloud as a new record in the db
    # and returns the object
    @staticmethod
    def DBCreateNew(sCloudName, sProvider, sAPIUrl, sAPIProtocol, sRegion="", sDefaultAccountID=""):
        db = catocommon.new_conn()
        sNewID = catocommon.new_guid()
        sRegion = "'%s'" % sRegion if sRegion else "null"
        sDefaultAccountID = "'%s'" % sDefaultAccountID if sDefaultAccountID else "null"
        
        sSQL = """insert into clouds (cloud_id, cloud_name, provider, api_url, api_protocol, region, default_account_id)
            values ('%s', '%s', '%s', '%s', '%s', %s, %s)""" % (sNewID, sCloudName, sProvider, sAPIUrl, sAPIProtocol, sRegion, sDefaultAccountID)
        if not db.exec_db_noexcep(sSQL):
            if db.error == "key_violation":
                raise Exception("A Cloud with that name already exists.  Please select another name.")
            else:
                raise Exception(db.error)
        
        # now it's inserted and in the session... lets get it back from the db as a complete object for confirmation.
        c = Cloud()
        c.FromID(sNewID)
        c.GetDefaultAccount()
        
        # yay!
        db.close()
        return c

    # INSTANCE METHOD
    # updates the current Cloud object to the db
    def DBUpdate(self):
        db = catocommon.new_conn()
        # of course we do nothing if this cloud was hardcoded in the xml
        # just return success, which should never happen since the user can't get to edit a hardcoded Cloud anyway.
        if not self.IsUserDefined:
            return True
        # what's the original name?
        sSQL = "select cloud_name from clouds where cloud_id = '%s'" % self.ID
        sOriginalName = db.select_col_noexcep(sSQL)
        if not sOriginalName:
            if db.error:
                raise Exception("Error getting original cloud name:" + db.error)
        
        
        sDefaultAccountID = "null"
        if self.DefaultAccount:
            sDefaultAccountID = "'%s'" % self.DefaultAccount.ID
            
        sSQL = """update clouds set cloud_name = '%s',
            provider = '%s',
            api_protocol = '%s',
            api_url = '%s',
            default_account_id = %s
            where cloud_id = '%s'""" % (self.Name, self.Provider.Name, self.APIProtocol, self.APIUrl, sDefaultAccountID, self.ID)
        if not db.exec_db_noexcep(sSQL):
            if db.error == "key_violation":
                raise InfoException("A Cloud with that name already exists.  Please select another name.")
            else:
                raise Exception(db.error)

        db.close()
        return True


# Note: this is not a container for CloudAccount objects - it's just a rowset from the database
# with an AsJSON method.
# why? Because the CloudAccount objects contain a full set of Provider information - stuff
# we don't need for list pages and dropdowns.
class CloudAccounts(object): 
    rows = {}
        
    def __init__(self, sFilter="", sProvider=""):
        db = catocommon.new_conn()
        sWhereString = ""
        if sFilter:
            aSearchTerms = sFilter.split()
            for term in aSearchTerms:
                if term:
                    sWhereString += " and (ca.account_name like '%%" + term + "%%' " \
                        "or ca.account_number like '%%" + term + "%%' " \
                        "or ca.provider like '%%" + term + "%%' " \
                        "or c.cloud_name like '%%" + term + "%%' " \
                        "or ca.login_id like '%%" + term + "%%') "

        # if a sProvider arg is passed, we explicitly limit to this provider
        if sProvider:
            sWhereString += " and ca.provider = '%s'" % sProvider
            
        sSQL = """select 
            ca.account_id as ID, 
            ca.account_name as Name, 
            ca.account_number as AccountNumber, 
            ca.provider as Provider, 
            ca.login_id as LoginID, 
            c.cloud_name as DefaultCloud,
            case is_default when 1 then 'Yes' else 'No' end as IsDefault,
            (select count(*) from deployment_service_inst where cloud_account_id = ca.account_id) as has_services
            from cloud_account ca
            left outer join clouds c on ca.default_cloud_id = c.cloud_id
            where 1=1 %s order by ca.is_default desc, ca.account_name""" % sWhereString
        
        rows = db.select_all_dict(sSQL)
        self.rows = rows if rows else {}
        db.close()

    def AsJSON(self):
        return catocommon.ObjectOutput.IterableAsJSON(self.rows)

    def AsXML(self):
        return catocommon.ObjectOutput.IterableAsXML(self.rows, "Accounts", "Account")

    def AsText(self, delimiter=None):
        return catocommon.ObjectOutput.IterableAsText(self.rows, ['ID', 'Name', 'Provider', 'AccountNumber', 'LoginID', 'DefaultCloud'], delimiter)

class CloudAccount(object):
    def __init__(self):
        self.ID = None
        self.Name = None
        self.AccountNumber = None
        self.LoginID = None
        self.LoginPassword = None
        self.IsDefault = None
        self.Provider = None
        self.DefaultCloud = None

    def FromName(self, sAccountName):
        """Will get a Cloud Account given either a name OR an id."""
        db = catocommon.new_conn()
        sSQL = "select account_id from cloud_account where account_name = '{0}' or account_id = '{0}'".format(sAccountName)
        
        caid = db.select_col_noexcep(sSQL)
        if db.error:
            raise Exception("Cloud Account Object: Unable to get Cloud Account from database. " + db.error)

        if caid:
            self.FromID(caid)
        else: 
            raise Exception("Error getting Cloud Account ID for Name [%s] - no record found. %s" % (sAccountName, db.error))

        db.close()

    def FromID(self, sAccountID):
        db = catocommon.new_conn()
        if not sAccountID:
            raise Exception("Error building Cloud Account object: Cloud Account ID is required.");    
        
        sSQL = """select account_id, account_name, account_number, provider, login_id, login_password, is_default, default_cloud_id
            from cloud_account
            where account_id = '%s'""" % sAccountID
        dr = db.select_row_dict(sSQL)
        
        if dr is not None:
            self.Populate(dr)
        else: 
            raise Exception("Unable to build Cloud Account object. Either no Cloud Accounts are defined, or no Account with ID [%s] could be found." % sAccountID)

        db.close()

    def FromRow(self, dr):
        if dr is not None:
            self.Populate(dr)
        else: 
            raise Exception("Unable to build Cloud Account object from row - row not provider.")

    def Populate(self, dr):
        if dr is not None:
            self.ID = dr["account_id"]
            self.Name = dr["account_name"]
            self.AccountNumber = ("" if not dr["account_number"] else dr["account_number"])
            self.LoginID = ("" if not dr["login_id"] else dr["login_id"])
            self.LoginPassword = ("" if not dr["login_password"] else catocommon.cato_decrypt(dr["login_password"]))
            self.IsDefault = (True if dr["is_default"] == 1 else False)

            c = Cloud()
            c.FromID(dr["default_cloud_id"])
            if not c:
                raise Exception("Error building Cloud Account object: Unable to get Default Cloud.")
                return
                
            self.DefaultCloud = c
            
            # find a provider object
            cp = CloudProviders()
            if not cp:
                raise Exception("Error building Cloud Account object: Unable to get CloudProviders.")
                return

            # check the CloudProvider class first ... it *should be there unless something is wrong.
            if cp.has_key(dr["provider"]):
                self.Provider = cp[dr["provider"]]
            else:
                raise Exception("Provider [%s] does not exist in the cloud_providers session xml." % dr["provider"])

        else: 
            raise Exception("Unable to build Cloud Account object. Either no Cloud Accounts are defined, or no Account could be found.")

    def IsValidForCalls(self):
        if self.LoginID and self.LoginPassword:
            return True
        return False

    def AsJSON(self):
        self.DefaultCloud = self.DefaultCloud.Name
        self.Provider = self.Provider.Name
        del self.LoginPassword
        return catocommon.ObjectOutput.AsJSON(self.__dict__)

    def AsText(self, delimiter=None):
        self.DefaultCloud = self.DefaultCloud.Name
        self.Provider = self.Provider.Name
        return catocommon.ObjectOutput.AsText(self.__dict__, ["Provider", "Name", "AccountNumber", "DefaultCloud"], delimiter)

    def AsXML(self):
        self.DefaultCloud = self.DefaultCloud.Name
        self.Provider = self.Provider.Name
        del self.LoginPassword
        return catocommon.ObjectOutput.AsXML(self.__dict__, "Account")

    # STATIC METHOD
    # creates this Cloud as a new record in the db
    # and returns the object
    @staticmethod
    def DBCreateNew(sProvider, sAccountName, sLoginID, sLoginPassword, sAccountNumber, sDefaultCloudID, sIsDefault="0"):
        db = catocommon.new_conn()
        
        # some sanity checks...
        # 1) is the provider valid?
        providers = CloudProviders()
        if sProvider not in providers.iterkeys():
            raise InfoException("The specified Provider [%s] is not a valid Cato Cloud Provider." % sProvider)
        
        # 2) if given, does the 'default cloud' exist
        c = Cloud()
        c.FromName(sDefaultCloudID)
        if not c.ID:
            raise InfoException("The specified default Cloud [%s] is not defined." % sDefaultCloudID)


        # if there are no rows yet, make this one the default even if the box isn't checked.
        if sIsDefault == "0":
            sSQL = "select count(*) as cnt from cloud_account"
            iExists = db.select_col(sSQL)
            if not iExists:
                sIsDefault = "1"

        sNewID = catocommon.new_guid()
        sPW = (catocommon.cato_encrypt(sLoginPassword) if sLoginPassword else "")
        
        sSQL = """insert into cloud_account
            (account_id, account_name, account_number, provider, is_default, 
            default_cloud_id, login_id, login_password, auto_manage_security)
            values ('%s','%s','%s','%s','%s','%s','%s','%s',0)""" % (sNewID, sAccountName, sAccountNumber, sProvider, sIsDefault,
                                                                     sDefaultCloudID, sLoginID, sPW)
    
        if not db.tran_exec_noexcep(sSQL):
            if db.error == "key_violation":
                raise InfoException("A Cloud Account with that name already exists.  Please select another name.")
            else: 
                raise Exception(db.error)
        
        # if "default" was selected, unset all the others
        if sIsDefault == "1":
            sSQL = "update cloud_account set is_default = 0 where account_id <> %s"
            db.tran_exec_noexcep(sSQL, (sNewID))

        db.tran_commit()
        db.close()
        
        # now it's inserted... lets get it back from the db as a complete object for confirmation.
        ca = CloudAccount()
        ca.FromID(sNewID)

        # yay!
        return ca

    def DBUpdate(self):
        db = catocommon.new_conn()
        
        #  only update the passwword if it has changed
        sNewPassword = ""
        if self.LoginPassword != "($%#d@x!&":
            sNewPassword = (", login_password = '" + catocommon.cato_encrypt(self.LoginPassword) + "'" if self.LoginPassword else "")

        sSQL = "update cloud_account set" \
                " account_name = '" + self.Name + "'," \
                " account_number = '" + self.AccountNumber + "'," \
                " provider = '" + self.Provider.Name + "'," \
                " default_cloud_id = '" + self.DefaultCloud.ID + "'," \
                " is_default = '" + ("1" if self.IsDefault else "0") + "'," \
                " auto_manage_security = 0," \
                " login_id = '" + self.LoginID + "'" + \
                sNewPassword + \
                " where account_id = '" + self.ID + "'"
        
        if not db.exec_db_noexcep(sSQL):
            if db.error == "key_violation":
                raise InfoException("A Cloud Account with that name already exists.  Please select another name.")
            else: 
                raise Exception(db.error)
        
        # if "default" was selected, unset all the others
        if self.IsDefault:
            sSQL = "update cloud_account set is_default = 0 where account_id <> %s"
            # not worth failing... we'll just end up with two defaults.
            db.exec_db_noexcep(sSQL, (self.ID))

        db.close()
        return True

class CloudProviders(dict):
    """
    CloudProviders is a dictionary of Provider objects.
    
    This is a big object, and it reads from xml every time it's instantiated.
    
    Instantiating it with the defaults can be expensive, so there's options to 
    get 'lighter' copies that doesn't include clouds/accounts or products/types.
    
    Unless you need Clouds/Accounts, set include_clouds = False and there will be
    a lot less DB activity.
     
    If you don't need Products/Object Types, set include_products = False.
     
    """
    
    # the constructor requires an ET Document
    def __init__(self, include_products=True, include_clouds=True):
        db = catocommon.new_conn()
        filename = os.path.join(catoconfig.BASEPATH, "conf/cloud_providers.xml")
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
                
                if include_clouds:
                    sSQL = """select cloud_id, cloud_name, api_url, api_protocol, region
                        from clouds where provider = '%s' order by cloud_name""" % pv.Name
                    dt = db.select_all_dict(sSQL)
                    if dt:
                        for dr in dt:
                            c = Cloud()
                            c.FromArgs(pv, True, dr["cloud_id"], dr["cloud_name"], dr["api_url"], dr["api_protocol"], dr["region"])
                            if c:
                                pv.Clouds.append(c)
                    else:
                        # DO NOT raise an exception here - user defined clouds are not required.
                        # but print a debug message
                        logger.debug("Cloud Providers XML: Warning - Provider [%s] allows user defined Clouds, but none exist in the database." % pv.Name)
                
                if include_products:
                    # get the cloudobjecttypes for this provider.                    
                    xProducts = xProvider.findall("products/product")
                    for xProduct in xProducts:
                        p_name = xProduct.get("name", None)

                        if p_name == None:
                            raise Exception("Cloud Providers XML: All Products must have the 'name' attribute.")
    
                        p = Product(pv)
                        p.Name = xProduct.get("name", None)
                        # use the name for the label if it doesn't exist.
                        p.Label = xProduct.get("label", p_name)
                        p.Type = xProduct.get("type", None)
                        p.APIUrlPrefix = xProduct.get("api_url_prefix", None)
                        p.APIUri = xProduct.get("api_uri", None)
                        p.APIVersion = xProduct.get("api_version", None)
                        
                        # the product contains object type definitions
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

                            # the type contains property definitions
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
        cp = CloudProviders()
        if cp == None:
            raise Exception("Error building Provider object: Unable to get CloudProviders.")
        if cp.has_key(sProvider):
            return cp[sProvider]
        else:
            raise Exception("Provider [%s] does not exist in the cloud_providers session xml." % sProvider)

    def GetAllObjectTypes(self):
        cots = {}
        
        for p in self.Products.itervalues():
            for cot in p.CloudObjectTypes.itervalues():
                if cot is not None:
                    cots[cot.ID] = cot
        return cots


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
                # don't crash while it's iterating, it may find it in the next object.
                # don't worry, we'll return null if it doesn't find anything.
                    
        return None

    def GetProductByType(self, sProductType):
        """Get a Product by it's Type instead of Name."""
        for p in self.Products.itervalues():
            if p.Type == sProductType:
                return p
                    
        return None

    def AsJSON(self):
        # this is built manually, because clouds have a provider object, which would be recursive.
        sb = []
        sb.append("{")
        sb.append("\"%s\" : \"%s\"," % ("Name", self.Name))
        sb.append("\"%s\" : \"%s\"," % ("TestProduct", self.TestProduct))
        sb.append("\"%s\" : \"%s\"," % ("UserDefinedClouds", self.UserDefinedClouds))
        sb.append("\"%s\" : \"%s\"," % ("TestObject", self.TestObject))
        
        # the clouds for this provider
        sb.append("\"Clouds\" : {")
        if self.Clouds:
            lst = []
            for c in self.Clouds:
                s = "\"%s\" : %s" % (c.ID, c.AsJSON())
                lst.append(s)
            sb.append(",".join(lst))
        sb.append("}, ")

        
        # the products and object types
        sb.append("\"Products\" : {")
        if self.Products:
            lst = []
            for prod in self.Products.itervalues():
                s = "\"%s\" : %s" % (prod.Name, prod.AsJSON())
                lst.append(s)
            sb.append(",".join(lst))
        sb.append("}")

        
        sb.append("}")
        return "".join(sb)

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
       
class CloudObjectType(object):
    def __init__(self, parent):
        self.ID = None
        self.Label = None
        self.APICall = None
        self.APIRequestGroupFilter = None
        self.APIRequestRecordFilter = None
        self.XMLRecordXPath = None
        self.ParentProduct = parent
        self.Properties = []  #!!! This is a list, not a dictionary
        self.Instances = {}  # a dictionary of results, keyed by the unique 'id'

    def IsValidForCalls(self):
        if self.XMLRecordXPath and self.ID:
            return True
        return False

    def AsJSON(self):
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
        return catocommon.ObjectOutput.AsJSON(self.__dict__)


"""
This class method will create database records for all the static clouds.
"""
def create_static_clouds():
    db = catocommon.new_conn()
    
    filename = os.path.join(catoconfig.BASEPATH, "conf/cloud_providers.xml")
    if not os.path.isfile(filename):
        raise Exception("conf/cloud_providers.xml file does not exist.")
    xRoot = ET.parse(filename)
    if not xRoot:
        raise Exception("Error: Invalid or missing Cloud Providers XML.")
    else:
        xProviders = xRoot.findall("providers/provider")
        for xProvider in xProviders:
            p_name = xProvider.get("name", None)
            user_defined_clouds = xProvider.get("user_defined_clouds", True)
            user_defined_clouds = (False if user_defined_clouds == "false" else True)
             
            if not user_defined_clouds:
                # clouds are NOT user defined, check the database for these records.
                xClouds = xProvider.findall("clouds/cloud")
                for xCloud in xClouds:
                    if xCloud.get("name", None) == None:
                        raise Exception("Cloud Providers XML: All Clouds must have the 'name' attribute.")
                    
                    cloud_name = xCloud.get("name", "")

                    sql = "select count(*) from clouds where cloud_name = '%s'" % cloud_name
                    cnt = db.select_col_noexcep(sql)
                    
                    if not cnt:
                        logger.info("    Creating Cloud [%s] on Provider [%s]..." % (cloud_name, p_name))

                        if xCloud.get("api_url", None) == None:
                            raise Exception("Cloud Providers XML: All Clouds must have the 'api_url' attribute.")
                        if xCloud.get("api_protocol", None) == None:
                            raise Exception("Cloud Providers XML: All Clouds must have the 'api_protocol' attribute.")
                        
                        from catocloud import cloud
                        c = cloud.Cloud.DBCreateNew(cloud_name, p_name, xCloud.get("api_url", ""), xCloud.get("api_protocol", ""), xCloud.get("region", ""))
                        if not c:
                            logger.warning("    Could not create Cloud from cloud_providers.xml definition.\n%s")
                    else:
                        logger.info("    Cloud [%s] already exists." % cloud_name)
    
    db.close()
    return True