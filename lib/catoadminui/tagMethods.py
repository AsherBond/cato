
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
 
import traceback
from catoui import uiCommon
from catocommon import catocommon
from catotag import tag

class tagMethods:
    db = None
    
    def wmGetTagsTable(self):
        try:
            sHTML = ""
            pager_html = ""
            sFilter = uiCommon.getAjaxArg("sSearch")
            sPage = uiCommon.getAjaxArg("sPage")
            maxrows = 25

            t = tag.Tags(sFilter)
            if t.rows:
                start, end, pager_html = uiCommon.GetPager(len(t.rows), maxrows, sPage)

                for row in t.rows[start:end]:
                    sHTML += "<tr tag_name=\"" + row["tag_name"] + "\">"
                    sHTML += "<td class=\"chkboxcolumn\">"
                    sHTML += "<input type=\"checkbox\" class=\"chkbox\"" \
                    " id=\"chk_" + row["tag_name"] + "\"" \
                    " tag=\"chk\" />"
                    sHTML += "</td>"
                    
                    sHTML += "<td class=\"selectable\">%s</td>" % row["tag_name"]
                    sHTML += "<td class=\"selectable desc\">%s</td>" % (row["tag_desc"] if row["tag_desc"] else "")
                    sHTML += "<td class=\"selectable\">%s</td>" % str(row["in_use"])
                    
                    sHTML += "</tr>"

            return "{\"pager\" : \"%s\", \"rows\" : \"%s\"}" % (uiCommon.packJSON(pager_html), uiCommon.packJSON(sHTML))    
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()           
        
    def wmCreateTag(self):
        try:
            sTagName = uiCommon.getAjaxArg("sTagName")
            sDesc = uiCommon.unpackJSON(uiCommon.getAjaxArg("sDescription"))
                
            t = tag.Tag(sTagName, sDesc)
            t, err = t.DBCreateNew()
            if err:
                return "{\"error\" : \"" + err + "\"}"
            if t == None:
                return "{\"error\" : \"Unable to create Tag.\"}"

            uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Tag, t.Name, t.Name, "Tag Created")

            return t.AsJSON()
        
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmDeleteTags(self):
        try:
            sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
            if not sDeleteArray:
                return "{\"info\" : \"Unable to delete - no selection.\"}"

            sDeleteArray = uiCommon.QuoteUp(sDeleteArray)
            
            sSQL = """delete from object_tags where tag_name in (%s)""" % sDeleteArray
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            sSQL = """delete from tags where tag_name in (%s)""" % sDeleteArray
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.Tag, "", sDeleteArray, "Tag(s) Deleted")

            return "{\"result\" : \"success\"}"
                
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
 
    def wmUpdateTag(self):
        try:
            sTagName = uiCommon.getAjaxArg("sTagName")
            sNewTagName = uiCommon.getAjaxArg("sNewTagName")
            sDesc = uiCommon.unpackJSON(uiCommon.getAjaxArg("sDescription"))
                
            t = tag.Tag(sTagName, sDesc)
            
            # update the description
            if sDesc:
                result, err = t.DBUpdate()
                if err:
                    return "{\"error\" : \"" + err + "\"}"
                if not result:
                    return "{\"error\" : \"Unable to update Tag.\"}"

            # and possibly rename it
            if sNewTagName:
                result, err = t.DBRename(sNewTagName)
                if err:
                    return "{\"error\" : \"" + err + "\"}"
                if not result:
                    return "{\"error\" : \"Unable to rename Tag.\"}"

            return "{\"result\" : \"success\"}"
        
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetObjectsTags(self):
        try:
            sHTML = ""
            oid = uiCommon.getAjaxArg("sObjectID")

            t = tag.Tags(sFilter="", sObjectID=oid)
            if t.rows:
                for row in t.rows:
                    sHTML += " <li id=\"ot_" + row["tag_name"].replace(" ", "") + "\" val=\"" + row["tag_name"] + "\" class=\"tag\">"
                    
                    sHTML += "<table class=\"object_tags_table\"><tr>"
                    sHTML += "<td style=\"vertical-align: middle;\">" + row["tag_name"] + "</td>"
                    sHTML += "<td width=\"1px\"><span class=\"ui-icon ui-icon-close forceinline tag_remove_btn\" remove_id=\"ot_" + row["tag_name"].replace(" ", "") + "\"></span></td>"
                    sHTML += "</tr></table>"
                    
                    sHTML += " </li>"
            return sHTML    
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()           
        
    def wmGetTagList(self):
        try:
            sObjectID = uiCommon.getAjaxArg("sObjectID")
            sHTML = ""
    
            # # this will be from lu_tags table
            # if the passed in objectid is empty, get them all, otherwise filter by it
            if sObjectID:
                sSQL = "select tag_name, tag_desc" \
                    " from tags " \
                    " where tag_name not in (" \
                    " select tag_name from object_tags where object_id = '" + sObjectID + "'" \
                    ")" \
                    " order by tag_name"
            else:
                sSQL = "select tag_name, tag_desc" \
                    " from tags" \
                    " order by tag_name"

            dt = self.db.select_all_dict(sSQL)
            if self.db.error:
                return self.db.error

            if dt:                
                sHTML += "<ul>"
                for dr in dt:
                    desc = (dr["tag_desc"].replace("\"", "").replace("'", "") if dr["tag_desc"] else "")
                    sHTML += " <li class=\"tag_picker_tag\"" \
                       " id=\"tpt_" + dr["tag_name"] + "\"" \
                       " desc=\"" + desc + "\"" \
                       ">"
                    sHTML += dr["tag_name"]
                    sHTML += " </li>"
                sHTML += "</ul>"
            else:
                sHTML += "No Unassociated Tags exist."

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmAddObjectTag(self):
        try:
            sObjectID = uiCommon.getAjaxArg("sObjectID")
            sObjectType = uiCommon.getAjaxArg("sObjectType")
            sTagName = uiCommon.getAjaxArg("sTagName")
    
    
            iObjectType = int(sObjectType)
    
            # fail on missing values
            if iObjectType < 0:
                return "{ \"error\" : \"Invalid Object Type.\" }"
            if not sObjectID or not sTagName:
                return "{ \"error\" : \"Missing or invalid Object ID or Tag Name.\" }"
    
            sSQL = """insert into object_tags
                (object_id, object_type, tag_name)
                values ('%s', '%d', '%s')""" % (sObjectID, iObjectType, sTagName)
    
            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)
    
            uiCommon.WriteObjectChangeLog(iObjectType, sObjectID, "", "Tag [" + sTagName + "] added.")
    
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmRemoveObjectTag(self):
        try:
            sObjectID = uiCommon.getAjaxArg("sObjectID")
            sObjectType = uiCommon.getAjaxArg("sObjectType")
            sTagName = uiCommon.getAjaxArg("sTagName")
    
    
            iObjectType = int(sObjectType)
    
            # fail on missing values
            if iObjectType < 0:
                return "{ \"error\" : \"Invalid Object Type.\" }"
            if not sObjectID or not sTagName:
                return "{ \"error\" : \"Missing or invalid Object ID or Tag Name.\" }"
    
            sSQL = """delete from object_tags where object_id = '%s' and tag_name = '%s'""" % (sObjectID, sTagName)
    
            if not self.db.exec_db_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)
    
            uiCommon.WriteObjectChangeLog(iObjectType, sObjectID, "", "Tag [" + sTagName + "] removed.")
    
            return ""
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

           
