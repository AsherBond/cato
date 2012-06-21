
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
import json
from catocommon import catocommon
import providers

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
        except Exception, ex:
            raise Exception(ex)
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.rows)
        except Exception, ex:
            raise ex


class Cloud(object):
    IsUserDefined = True
    ID = None
    Name = None
    APIUrl = None
    APIProtocol = None
    Region = None
    Provider = None

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
            cp = providers.CloudProviders()
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
        except Exception, ex:
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
        except Exception, ex:
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
        except Exception, ex:
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
        except Exception, ex:
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
        except Exception, ex:
            raise Exception(ex)
        finally:
            db.close()

    def AsJSON(self):
        try:
            return json.dumps(self.rows)
        except Exception, ex:
            raise ex

class CloudAccount(object):
    ID = None
    Name = None
    AccountNumber = None
    LoginID = None
    LoginPassword = None
    IsDefault = None
    Provider = None

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
                cp = providers.CloudProviders()
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
        except Exception, ex:
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
        except Exception, ex:
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
        except Exception, ex:
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
        except Exception, ex:
            raise ex
        finally:
            db.close()
