
#########################################################################
# 
# Copyright 2012 Cloud Sidekick
# __________________
# 
#  All Rights Reserved.
# 
# NOTICE:  All information contained herein is, and remains
# the property of Cloud Sidekick and its suppliers,
# if any.  The intellectual and technical concepts contained
# herein are proprietary to Cloud Sidekick
# and its suppliers and may be covered by U.S. and Foreign Patents,
# patents in process, and are protected by trade secret or copyright law.
# Dissemination of this information or reproduction of this material
# is strictly forbidden unless prior written permission is obtained
# from Cloud Sidekick.
#
#########################################################################
 
"""
    Tags are used to establish user-defined relationships between objects.
    For example, by giving a user and a task the same tag, you ensure that user can 
    manage that task.
"""
from catocommon import catocommon

""" Tags is a list of all the defined tags.  It's different from 'ObjectTags', which is a list of relationships."""
class Tags(object): 
    rows = {}

    def __init__(self, sFilter="", sObjectID=""):
        db = catocommon.new_conn()
        sWhereString = ""
        if sFilter:
            aSearchTerms = sFilter.split()
            for term in aSearchTerms:
                if term:
                    sWhereString += " and (t.tag_name like '%%" + term + "%%' " \
                        "or t.tag_desc like '%%" + term + "%%') "

        # if an object id arg is passed, we explicitly limit to that object
        if sObjectID:
            sWhereString += " and ot.object_id = '%s'" % sObjectID
            
        sql = """select t.tag_name, t.tag_desc, count(ot.tag_name) as in_use
            from tags t
            left outer join object_tags ot on t.tag_name = ot.tag_name
            where (1=1) %s
            group by t.tag_name, t.tag_desc
            order by t.tag_name""" % sWhereString
        
        self.rows = db.select_all_dict(sql)
        db.close()

    def AsJSON(self):
        return catocommon.ObjectOutput.IterableAsJSON(self.rows)

    def AsXML(self):
        return catocommon.ObjectOutput.IterableAsXML(self.rows, "Tags", "Tag")

    def AsText(self, delimiter, headers):
        return catocommon.ObjectOutput.IterableAsText(self.rows, ["tag_name", "in_use", "tag_desc"], delimiter, headers)


class Tag(object):
    def __init__(self, tag_name, description=""):
        self.Name = tag_name
        self.Description = description

    def DBCreateNew(self):
        """
        Creates a new Tag.
        """
        db = catocommon.new_conn()

        sql = "insert into tags (tag_name, tag_desc) values (%s, %s)"
        if not db.exec_db_noexcep(sql, (self.Name, self.Description)):
            if db.error == "key_violation":
                # If a Tag already exists, we're golden anyway...
                pass
            else: 
                raise Exception(db.error)

        db.close()
        return True

    def DBUpdate(self):
        db = catocommon.new_conn()
        # do the description no matter what just to be quick
        sql = "update tags set tag_desc = %s where tag_name = %s"
        db.exec_db(sql, (self.Description, self.Name))
        db.close()
        return True

    def DBDelete(self):
        db = catocommon.new_conn()
        sql = """delete from object_tags where tag_name = %s"""
        db.tran_exec(sql, (self.Name))
 
        sql = """delete from tags where tag_name = %s"""
        db.tran_exec(sql, (self.Name))

        db.tran_commit()
        db.close()
        return True

    def DBRename(self, sNewName):
        """
        Tags are different than other objects, because they don't have an additional 'id'.
        The tag name IS it's id, so we need a special case to update that name.
        """
        db = catocommon.new_conn()

        # do the description no matter what just to be quick
        sql = "update object_tags set tag_name = %s where tag_name = %s"
        db.tran_exec(sql, (sNewName, self.Name))

        sql = "update tags set tag_name = %s where tag_name = %s"
        if not db.tran_exec_noexcep(sql, (sNewName, self.Name)):
            if db.error == "key_violation":
                raise Exception("Tag Name '%s' already in use, choose another." % self.Name)
            else: 
                raise Exception(db.error)

        db.tran_commit()
        db.close()

        return True

    def AsJSON(self):
        return catocommon.ObjectOutput.AsJSON(self.__dict__)

    def AsXML(self):
        return catocommon.ObjectOutput.AsXML(self.__dict__, "Tag")

    def AsText(self, delimiter, headers):
        return catocommon.ObjectOutput.AsText(self.__dict__, ["Name", "Description"], delimiter, headers)

class ObjectTags(list): 
    """
    This class IS list of all tags associated with the provided object type and id. 
    """
    def __init__(self, object_type, object_id):
        db = catocommon.new_conn()

        sql = """select tag_name
            from object_tags
            where object_type = %s
            and object_id = %s
            group by tag_name
            order by tag_name"""
        
        rows = db.select_all(sql, (object_type, object_id))
        db.close()
        if rows:
            list.__init__(self, [x[0] for x in rows])

    def AsJSON(self):
        return catocommon.ObjectOutput.IterableAsJSON(self)

    @staticmethod
    def Add(tag, object_id, object_type):
        """
        Adds a Tag to an object.
        """
        db = catocommon.new_conn()

        ot = int(object_type)
        if ot < 0:
            raise Exception("Invalid Object Type.")

        sql = """insert into object_tags
            (object_id, object_type, tag_name)
            values (%s, %s, %s)"""

        if not db.exec_db_noexcep(sql, (object_id, object_type, tag)):
            if db.error == "key_violation":
                # If a reference already exists, we're golden anyway...
                pass
            else: 
                raise Exception(db.error)

        db.close()
        return True

    @staticmethod
    def Remove(tag, object_id):
        """
        Removes a Tag from an object.
        """
        db = catocommon.new_conn()
        sql = "delete from object_tags where object_id = %s and tag_name = %s"
        db.exec_db(sql, (object_id, tag))
        db.close()
        return True


