
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
from catocommon import catocommon
from catolog import catolog
logger = catolog.get_logger(__name__)

class Assets(object): 
    rows = {}
        
    def __init__(self, sFilter=""):
        db = catocommon.new_conn()
        sWhereString = ""
        if sFilter:
            aSearchTerms = sFilter.split()
            for term in aSearchTerms:
                if term:
                    sWhereString += " and (a.asset_name like '%%" + term + "%%' " \
                        "or a.port like '%%" + term + "%%' " \
                        "or a.address like '%%" + term + "%%' " \
                        "or a.db_name like '%%" + term + "%%' " \
                        "or a.asset_status like '%%" + term + "%%' " \
                        "or ac.username like '%%" + term + "%%') "

        sSQL = """select a.asset_id, a.asset_name, a.asset_status, a.address,
            case when ac.shared_or_local = 1 then 'Local - ' else 'Shared - ' end as shared_or_local,
            case when ac.domain <> '' then concat(ac.domain, cast(char(92) as char), ac.username) else ac.username end as credentials,
            group_concat(ot.tag_name order by ot.tag_name separator ',') as tags
            from asset a
            left outer join object_tags ot on a.asset_id = ot.object_id
            left outer join asset_credential ac on ac.credential_id = a.credential_id
            where 1=1 %s group by a.asset_id order by a.asset_name""" % sWhereString

        self.rows = db.select_all_dict(sSQL)
        db.close()

    def AsJSON(self):
        return catocommon.ObjectOutput.IterableAsJSON(self.rows)

class Asset(object):
    def __init__(self):
        self.ID = ""
        self.Name = ""
        self.Status = ""
        self.Port = ""
        self.DBName = ""
        self.Address = ""
        self.UserName = ""
        self.SharedOrLocal = ""
        self.CredentialID = ""
        self.Password = ""
        self.Domain = ""
        self.SharedCredName = ""
        self.SharedCredDesc = ""
        self.ConnString = ""

    def FromName(self, sAssetName):
        self.PopulateAsset(asset_name=sAssetName)
        
    def FromID(self, sAssetID):
        self.PopulateAsset(asset_id=sAssetID)

    def PopulateAsset(self, asset_id="", asset_name=""):
        """
            Note the absence of password or privileged_password in this method.
            We don't store passwords, even encrypted, in the object.
        """
        db = catocommon.new_conn()
        if not asset_id and not asset_name:
            raise Exception("Error building Asset object: ID or Name is required.");    
        
        sSQL = """select a.asset_id, a.asset_name, a.asset_status, a.port, a.db_name, a.conn_string,
            a.address, ac.username, ac.domain,
            ac.shared_cred_desc, ac.credential_name, a.credential_id,
            case when ac.shared_or_local = '0' then 'Shared' else 'Local' end as shared_or_local
            from asset a
            left outer join asset_credential ac on ac.credential_id = a.credential_id
            """
        
        if asset_id:
            sSQL += " where a.asset_id = '%s'""" % asset_id
        elif asset_name:
            sSQL += " where a.asset_name = '%s'""" % asset_name

        dr = db.select_row_dict(sSQL)
        db.close()        
        
        if dr is not None:
            self.ID = dr["asset_id"]
            self.Name = dr["asset_name"]
            self.Status = dr["asset_status"]
            self.Port = ("" if not dr["port"] else str(dr["port"]))
            self.DBName = ("" if not dr["db_name"] else dr["db_name"])
            self.Address = ("" if not dr["address"] else dr["address"])
            self.UserName = ("" if not dr["username"] else dr["username"])
            self.SharedOrLocal = ("" if not dr["shared_or_local"] else dr["shared_or_local"])
            self.CredentialID = ("" if not dr["credential_id"] else dr["credential_id"])
            self.Domain = ("" if not dr["domain"] else dr["domain"])
            self.SharedCredName = ("" if not dr["credential_name"] else dr["credential_name"])
            self.SharedCredDesc = ("" if not dr["shared_cred_desc"] else dr["shared_cred_desc"])
            self.ConnString = ("" if not dr["conn_string"] else dr["conn_string"])
        else: 
            raise Exception("Unable to build Asset object. Either no Assets are defined, or no Asset by ID/Name could be found.")

    def AsJSON(self):
        return catocommon.ObjectOutput.AsJSON(self.__dict__)

    @staticmethod
    def HasHistory(asset_id):
        """Returns True if the asset has historical data."""
        db = catocommon.new_conn()
        sql = "select count(*) from task_instance where asset_id = %s"
        iResults = db.select_col(sql, (asset_id))
        db.close()        
        return catocommon.is_true(iResults)

    @staticmethod
    def DBCreateNew(sAssetName, sStatus, sDbName, sPort, sAddress, sConnString, tags, credential_update_mode, credential=None):
        """
        Creates a new Asset.  Requires a credential object to be sent along.  If not provided, the 
        Asset is created with no credentials.
        
        As a convenience, any tags sent along will also be added.
        """
        db = catocommon.new_conn()

        sAssetID = catocommon.new_guid()

        if credential:
            c = Credential()
            c.FromDict(credential)
        
            sCredentialID = (c.ID if c.ID else "")

            #  there are three CredentialType's 
            #  1) 'selected' = user selected a different credential, just save the credential_id
            #  2) 'new' = user created a new shared or local credential
            #  3) 'existing' = same credential, just update the username,description ad password
            if credential_update_mode == "new":
                # if it's a local credential, the credential_name is the asset_id.
                # if it's shared, there will be a name.
                if c.SharedOrLocal == "1":
                    c.Name = sAssetID

                result, msg = c.DBCreateNew()
                if not result:
                    return None, msg
            elif credential_update_mode == "selected":
                #  user selected a shared credential
                #  remove the local credential if one exists
                sSQL = """delete from asset_credential
                    where shared_or_local = 1
                    and credential_id in (select credential_id from asset where asset_id = '%s')""" % sAssetID
                if not db.tran_exec_noexcep(sSQL):
                    return False, db.error


        sSQL = "insert into asset" \
        " (asset_id, asset_name, asset_status, address, conn_string, db_name, port, credential_id)" \
        " values (" \
        "'" + sAssetID + "'," \
        "'" + sAssetName + "'," \
        "'" + sStatus + "'," \
        "'" + sAddress + "'," \
        "'" + sConnString + "'," \
        "'" + sDbName + "'," + \
        ("NULL" if sPort == "" else "'" + sPort + "'") + "," \
        "'" + sCredentialID + "'" \
        ")"
        if not db.tran_exec_noexcep(sSQL):
            logger.error(db.error)
            if db.error == "key_violation":
                return None, "Asset Name '" + sAssetName + "' already in use, choose another."
            else: 
                return None, db.error

        db.tran_commit()
        db.close()        
        
        # now it's inserted... lets get it back from the db as a complete object for confirmation.
        a = Asset()
        a.FromID(sAssetID)
        a.RefreshTags(tags)
        return a, None

    def DBUpdate(self, tags="", credential_update_mode="", credential=None):
        """
        Updates the current Asset to the database.  Does not requre a credential or credential update 'mode'.
        
        As a convenience, it will update credentials or tags if provided.
        """
        db = catocommon.new_conn()

        #  there are three CredentialType's 
        #  1) 'selected' = user selected a different credential, just save the credential_id
        #  2) 'new' = user created a new shared or local credential
        #  3) 'existing' = same credential, just update the username,description ad password
        if credential:
            c = Credential()
            c.FromDict(credential)
        
            self.CredentialID = (c.ID if c.ID else "")
            
            if credential_update_mode == "new":
                # if it's a local credential, the credential_name is the asset_id.
                # if it's shared, there will be a name.
                if c.SharedOrLocal == "1":
                    c.Name = self.ID

                result, msg = c.DBCreateNew()
                if not result:
                    return None, msg
            elif credential_update_mode == "existing":
                result, msg = c.DBUpdate()
                if not result:
                    return None, msg
            elif credential_update_mode == "selected":
                #  user selected a shared credential
                #  remove the local credential if one exists
                sSQL = """delete from asset_credential
                    where shared_or_local = 1
                    and credential_id in (select credential_id from asset where asset_id = '%s')""" % self.ID
                if not db.tran_exec_noexcep(sSQL):
                    return False, db.error

        sSQL = "update asset set asset_name = '" + self.Name + "'," \
            " asset_status = '" + self.Status + "'," \
            " address = '" + self.Address + "'" + "," \
            " conn_string = '" + self.ConnString + "'" + "," \
            " db_name = '" + self.DBName + "'," \
            " port = " + ("'" + self.Port + "'" if self.Port else "null") + "," \
            " credential_id = '" + self.CredentialID + "'" \
            " where asset_id = '" + self.ID + "'"
        if not db.tran_exec_noexcep(sSQL):
            if db.error == "key_violation":
                return None, "Asset Name '" + self.Name + "' already in use, choose another."
            else: 
                return None, db.error

        db.tran_commit()
        db.close()        

        self.RefreshTags(tags)

        return True, None


    def RefreshTags(self, tags):
        """
        Refresh the tag associations with this object.
        """
        db = catocommon.new_conn()
        if tags:
            #  remove the existing tags
            sSQL = "delete from object_tags where object_id = '" + self.ID + "'"
            db.exec_db(sSQL)

            # if we can't create tags we don't actually fail...
            for tag in tags:
                sql = "insert object_tags (object_type, object_id, tag_name) values (2, '%s','%s')" % (self.ID, tag)
                db.exec_db(sql)

        db.close()        



class Credentials(object): 
    rows = {}
        
    def __init__(self, sFilter=""):
        db = catocommon.new_conn()
        sWhereString = ""
        if sFilter:
            aSearchTerms = sFilter.split()
            for term in aSearchTerms:
                if term:
                    sWhereString += " and (credential_name like '%%" + term + "%%' " \
                        "or username like '%%" + term + "%%' " \
                        "or domain like '%%" + term + "%%' " \
                        "or shared_cred_desc like '%%" + term + "%%') "

        sSQL = """select credential_id as ID, 
            credential_name as Name, 
            username as Username, 
            domain as Domain, 
            shared_cred_desc as Description
            from asset_credential
            where shared_or_local = 0 %s order by credential_name""" % sWhereString

        self.rows = db.select_all_dict(sSQL)
        db.close()

    def AsJSON(self):
        return catocommon.ObjectOutput.IterableAsJSON(self.rows)

    def AsXML(self):
        return catocommon.ObjectOutput.IterableAsXML(self.rows, "Credentials", "Credential")

    def AsText(self, delimiter=None, headers=None):
        return catocommon.ObjectOutput.IterableAsText(self.rows, ['Name', 'Username', 'Domain', 'Description'], delimiter, headers)

class Credential(object):
    
    def __init__(self):
        self.ID = catocommon.new_guid()
        self.ID = None
        self.Username = None
        self.Password = None
        self.SharedOrLocal = None
        self.Name = None
        self.Description = None
        self.Domain = None
        self.PrivilegedPassword = None
        
    def FromArgs(self, sName, sDesc, sUsername, sPassword, sShared, sDomain, sPrivPassword):
        self.Name = sName
        self.Description = sDesc
        self.Username = sUsername
        self.Password = sPassword
        self.SharedOrLocal = sShared
        self.Domain = sDomain
        self.PrivilegedPassword = sPrivPassword

        # if created by args, it may or may not have an ID.
        # but it needs one.
        if not self.ID:
            self.ID = catocommon.new_guid()

    def FromID(self, credential_id):
        db = catocommon.new_conn()
        sSQL = """select credential_id, credential_name, username, domain, shared_cred_desc, shared_or_local
            from asset_credential
            where credential_id = %s"""

        dr = db.select_row_dict(sSQL, (credential_id))
        db.close()        
        
        if dr is not None:
            self.FromRow(dr)
        else: 
            raise Exception("No Credential found using ID [%s]" % (credential_id))

    def FromName(self, name):
        db = catocommon.new_conn()
        sSQL = """select credential_id, credential_name, username, domain, shared_cred_desc, shared_or_local
            from asset_credential
            where (credential_id = %s or credential_name = %s)"""

        dr = db.select_row_dict(sSQL, (name, name))
        db.close()
        
        if dr is not None:
            self.FromRow(dr)
        else: 
            raise Exception("No Credential found using ID or Name [%s]" % (name))

    def FromRow(self, dr):
        """
            Note the absence of password or privileged_password in this method.
            We don't store passwords, even encrypted, in the object.
        """
        self.ID = dr["credential_id"]
        self.Name = dr["credential_name"]
        self.Username = dr["username"]
        self.SharedOrLocal = dr["shared_or_local"]
        self.Domain = ("" if not dr["domain"] else dr["domain"])
        self.Description = ("" if not dr["shared_cred_desc"] else dr["shared_cred_desc"])


    def FromDict(self, cred):
        for k, v in cred.items():
            setattr(self, k, v)
            
        # if created by args, it may or may not have an ID.
        # but it needs one.
        if not self.ID:
            self.ID = catocommon.new_guid()

    def DBCreateNew(self):
        db = catocommon.new_conn()

        sPriviledgedPasswordUpdate = catocommon.cato_encrypt(self.PrivilegedPassword) if self.PrivilegedPassword else None

        # if it's a local credential, the credential_name is the asset_id.
        # if it's shared, there will be a name.
        if self.SharedOrLocal == "1":
            # whack and add - easiest way to avoid conflicts
            sSQL = "delete from asset_credential where credential_name = %s and shared_or_local = '1'"
            db.exec_db(sSQL, (self.Name))
        
        sSQL = """insert into asset_credential
            (credential_id, credential_name, username, password, domain, shared_or_local, shared_cred_desc, privileged_password)
            values (%s, %s, %s, %s, %s, %s, %s, %s)"""
        params = (self.ID, self.Name, self.Username, catocommon.cato_encrypt(self.Password), self.Domain, self.SharedOrLocal, self.Description, sPriviledgedPasswordUpdate)
        if not db.exec_db_noexcep(sSQL, params):
            if db.error == "key_violation":
                raise Exception("A Credential with that name already exists.  Please select another name.")
            else: 
                raise Exception(db.error)
        
        return True
                
    def DBDelete(self):
        db = catocommon.new_conn()

        sSQL = "delete from asset_credential where credential_id = '%s'" % self.ID
        db.exec_db(sSQL)
        db.close()        

        return True
            
    def DBUpdate(self):
        db = catocommon.new_conn()
    
        # if the password has not changed leave it as is.
        sPasswordUpdate = ""
        if self.Password and self.Password != "~!@@!~":
            sPasswordUpdate = ", password = '" + catocommon.cato_encrypt(self.Password) + "'"
    
        #  same for privileged_password
        sPriviledgedPasswordUpdate = ""
        if self.PrivilegedPassword != "~!@@!~":
            #  updated password
            #  priviledged password can be blank, so if it is, set it to null
            if self.PrivilegedPassword:
                sPriviledgedPasswordUpdate = ", privileged_password = null"
            else:
                sPriviledgedPasswordUpdate = ", privileged_password = '" + catocommon.cato_encrypt(self.PrivilegedPassword) + "'"
    
        sSQL = """update asset_credential set
            credential_name = %s,
            username = %s,
            domain = %s,
            shared_or_local = %s,
            shared_cred_desc = %s {0} {1}
            where credential_id = %s""".format(sPasswordUpdate, sPriviledgedPasswordUpdate) 
            
        db.exec_db(sSQL, (self.Name, self.Username, self.Domain, self.SharedOrLocal, self.Description, self.ID))
        db.close()        
    
        return True

    def AsJSON(self):
        del self.Password
        del self.PrivilegedPassword
        return catocommon.ObjectOutput.AsJSON(self.__dict__)

    def AsXML(self):
        del self.Password
        del self.PrivilegedPassword
        return catocommon.ObjectOutput.AsXML(self.__dict__, "Credential")

    def AsText(self, delimiter):
        return catocommon.ObjectOutput.AsText(self.__dict__, ["Name", "Username", "SharedOrLocal", "Description"], delimiter, headers)

