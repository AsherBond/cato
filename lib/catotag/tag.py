
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
            
        sSQL = """select t.tag_name, t.tag_desc, count(ot.tag_name) as in_use
            from tags t
            left outer join object_tags ot on t.tag_name = ot.tag_name
            where (1=1) %s
            group by t.tag_name, t.tag_desc
            order by t.tag_name""" % sWhereString
        
        self.rows = db.select_all_dict(sSQL)
        db.close()

    def AsJSON(self):
        return catocommon.ObjectOutput.IterableAsJSON(self.rows)

class Tag(object):
    def __init__(self, tag_name, description):
        self.Name = tag_name
        self.Description = description

    def DBCreateNew(self):
        """
        Creates a new Tag.
        """
        db = catocommon.new_conn()

        sSQL = """insert into tags (tag_name, tag_desc) values ('%s', '%s')""" % (self.Name, catocommon.tick_slash(self.Description))
        if not db.exec_db_noexcep(sSQL):
            if db.error == "key_violation":
                raise Exception("Tag Name '%s' already in use, choose another." % self.Name)
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

    def DBRename(self, sNewName):
        """
        Tags are different than other objects, because they don't have an additional 'id'.
        The tag name IS it's id, so we need a special case to update that name.
        """
        db = catocommon.new_conn()

        # do the description no matter what just to be quick
        sSQL = "update object_tags set tag_name = %s where tag_name = %s"
        db.tran_exec(sSQL, (sNewName, self.Name))

        sSQL = "update tags set tag_name = %s where tag_name = %s"
        if not db.tran_exec_noexcep(sSQL, (sNewName, self.Name)):
            if db.error == "key_violation":
                raise Exception("Tag Name '%s' already in use, choose another." % self.Name)
            else: 
                raise Exception(db.error)

        db.tran_commit()
        db.close()

        return True

    def AsJSON(self):
        return catocommon.ObjectOutput.AsJSON(self.__dict__)

class ObjectTags(list): 
    """
    This class IS list of all tags associated with the provided object type and id. 
    """
    def __init__(self, object_type, object_id):
        db = catocommon.new_conn()

        sql = """select tag_name
            from object_tags
            where object_type = %s
            and object_id = %s"""
        
        rows = db.select_all(sql, (object_type, object_id))
        list.__init__(self, [r[0] for r in rows])
        db.close()

    def AsJSON(self):
        return catocommon.ObjectOutput.IterableAsJSON(self)

