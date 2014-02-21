
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
import json

from catoui import uiCommon
from catocommon import catocommon
from catotag import tag

class tagMethods:
    db = None
    
    def wmGetTagsTable(self):
        table_html = ""
        pager_html = ""
        sFilter = uiCommon.getAjaxArg("sFilter")
        sPage = uiCommon.getAjaxArg("sPage")
        maxrows = 25

        t = tag.Tags(sFilter)
        if t.rows:
            start, end, pager_html = uiCommon.GetPager(len(t.rows), maxrows, sPage)

            for row in t.rows[start:end]:
                table_html += "<tr tag_name=\"" + row["tag_name"] + "\">"
                table_html += "<td class=\"chkboxcolumn\">"
                table_html += "<input type=\"checkbox\" class=\"chkbox\"" \
                " id=\"chk_" + row["tag_name"] + "\"" \
                " tag=\"chk\" />"
                table_html += "</td>"
                
                table_html += "<td class=\"selectable\">%s</td>" % row["tag_name"]
                table_html += "<td class=\"selectable desc\">%s</td>" % (row["tag_desc"] if row["tag_desc"] else "")
                table_html += "<td class=\"selectable\">%s</td>" % str(row["in_use"])
                
                table_html += "</tr>"

        out = {}
        out["pager"] = pager_html
        out["rows"] = table_html
        return json.dumps(out)    
        
    def wmCreateTag(self):
        sTagName = uiCommon.getAjaxArg("sTagName")
        sDesc = uiCommon.getAjaxArg("sDescription")
            
        t = tag.Tag(sTagName, sDesc)
        t.DBCreateNew()
        uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Tag, t.Name, t.Name, "Tag Created")

        return t.AsJSON()

    def wmDeleteTags(self):
        sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
        if not sDeleteArray:
            return json.dumps({"info": "Unable to delete - no selection."})

        sDeleteArray = uiCommon.QuoteUp(sDeleteArray)
        
        sSQL = """delete from object_tags where tag_name in (%s)""" % sDeleteArray
        self.db.tran_exec(sSQL)

        sSQL = """delete from tags where tag_name in (%s)""" % sDeleteArray
        self.db.tran_exec(sSQL)

        self.db.tran_commit()
        
        uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.Tag, "", sDeleteArray, "Tag(s) Deleted")

        return json.dumps({"result": "success"})
 
    def wmUpdateTag(self):
        sTagName = uiCommon.getAjaxArg("sTagName")
        sNewTagName = uiCommon.getAjaxArg("sNewTagName")
        sDesc = uiCommon.getAjaxArg("sDescription")
            
        t = tag.Tag(sTagName, sDesc)
        
        # update the description
        if sDesc:
            t.DBUpdate()

        # and possibly rename it
        if sNewTagName:
            t.DBRename(sNewTagName)

        return json.dumps({"result": "success"})

    def wmGetObjectsTags(self):
        sHTML = ""
        oid = uiCommon.getAjaxArg("sObjectID")

        t = tag.Tags(sFilter="", sObjectID=oid)
        if t.rows:
            for row in t.rows:
                sHTML += " <li id=\"ot_" + row["tag_name"].replace(" ", "") + "\" val=\"" + row["tag_name"] + "\" class=\"tag ui-widget-content ui-corner-all\">"
                
                sHTML += "<table class=\"object_tags_table\"><tr>"
                sHTML += "<td style=\"vertical-align: middle;\">" + row["tag_name"] + "</td>"
                sHTML += "<td width=\"1px\"><span class=\"ui-icon ui-icon-close forceinline tag_remove_btn\" remove_id=\"ot_" + row["tag_name"].replace(" ", "") + "\"></span></td>"
                sHTML += "</tr></table>"
                
                sHTML += " </li>"
        return sHTML    
        
    def wmGetTagList(self):
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
        if dt:                
            sHTML += "<ul>"
            for dr in dt:
                desc = (dr["tag_desc"].replace("\"", "").replace("'", "") if dr["tag_desc"] else "")
                sHTML += " <li class=\"tag_picker_tag ui-widget-content ui-corner-all\"" \
                   " id=\"tpt_" + dr["tag_name"] + "\"" \
                   " desc=\"" + desc + "\"" \
                   ">"
                sHTML += dr["tag_name"]
                sHTML += " </li>"
            sHTML += "</ul>"
        else:
            sHTML += "No Unassociated Tags exist."

        return sHTML

    def wmAddObjectTag(self):
        sObjectID = uiCommon.getAjaxArg("sObjectID")
        sObjectType = uiCommon.getAjaxArg("sObjectType")
        sTagName = uiCommon.getAjaxArg("sTagName")


        iObjectType = int(sObjectType)

        # fail on missing values
        if iObjectType < 0:
            raise Exception("Invalid Object Type.")
        if not sObjectID or not sTagName:
            raise Exception("Missing or invalid Object ID or Tag Name.")

        tag.ObjectTags.Add(sTagName, sObjectID, iObjectType)
        uiCommon.WriteObjectChangeLog(iObjectType, sObjectID, "", "Tag [%s] added." % sTagName)

        return json.dumps({"result": "success"})

    def wmRemoveObjectTag(self):
        sObjectID = uiCommon.getAjaxArg("sObjectID")
        sObjectType = uiCommon.getAjaxArg("sObjectType")
        sTagName = uiCommon.getAjaxArg("sTagName")
        iObjectType = int(sObjectType)

        # fail on missing values
        if iObjectType < 0:
            raise Exception("Invalid Object Type.")
        if not sObjectID or not sTagName:
            raise Exception("Missing or invalid Object ID or Tag Name.")

        tag.ObjectTags.Remove(sTagName, sObjectID)
        uiCommon.WriteObjectChangeLog(iObjectType, sObjectID, "", "Tag [%s] removed." % sTagName)

        return json.dumps({"result": "success"})
