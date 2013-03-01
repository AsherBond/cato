
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
    Unlike the other Cato UI "web method" classes, we're taking a new approach with this one.
    As Cato has evolved, older code converted to Python still reflects it's origins in C#.
    
    Since the catodeployments lib has most of the functionality we need,
    this class is hopefully simply wrappers around those calls.
"""

import traceback

from catoui import uiCommon
from catocommon import catocommon
from catodeployment import deployment

class depMethods:
    db = None

    def wmGetTemplatesTable(self):
        """ Get a list of all Deployment Templates"""
        try:
            sHTML = ""
            pager_html = ""
            sFilter = uiCommon.getAjaxArg("sSearch")
            sPage = uiCommon.getAjaxArg("sPage")
            maxrows = 25

            deps = deployment.DeploymentTemplates(sFilter)
            if deps.rows:
                start, end, pager_html = uiCommon.GetPager(len(deps.rows), maxrows, sPage)

                for row in deps.rows[start:end]:
                    sHTML += """
                    <tr template_id="{0}">
                    <td class="chkboxcolumn">    
                        <input type="checkbox" class="chkbox" id="chk_{0}" object_id="{0}" tag="chk" />
                    </td>
                    
                    <td class="selectable">{1}</td>
                    <td class="selectable">{2}</td>
                    <td class="selectable">{3}</td>
                    
                    </tr>
                    """.format(row["ID"], row["Name"], row["Version"], row["Description"] if row["Description"] else "")
    
            return "{\"pager\" : \"%s\", \"rows\" : \"%s\"}" % (uiCommon.packJSON(pager_html), uiCommon.packJSON(sHTML))    
        except Exception:
            uiCommon.log(traceback.format_exc())
            
    def wmCreateTemplate(self):
        try:
            name = uiCommon.getAjaxArg("name")
            version = uiCommon.getAjaxArg("version")
            desc = uiCommon.getAjaxArg("desc")
            template = uiCommon.getAjaxArg("template")

            t, msg = deployment.DeploymentTemplate.DBCreateNew(name, version, uiCommon.unpackJSON(template), uiCommon.unpackJSON(desc))
            if t is not None:
                uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Deployment, t.ID, t.Name, "Deployment Template created.")
                return "{\"template_id\" : \"%s\"}" % t.ID
            else:
                uiCommon.log(msg)
                return "{\"info\" : \"%s\"}" % msg
        except Exception:
            uiCommon.log(traceback.format_exc())

    def wmDeleteTemplates(self):
        try:
            sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
            if len(sDeleteArray) < 36:
                return "{\"info\" : \"Unable to delete - no selection.\"}"
    
            sDeleteArray = uiCommon.QuoteUp(sDeleteArray)
            
            # can't delete it if it's referenced.
            sSQL = """select count(*) from deployment d
                join deployment_template dt on (d.template_name = dt.template_name
                    and d.template_version = dt.template_version)
                where dt.template_id in (%s)""" % sDeleteArray

            iResults = self.db.select_col_noexcep(sSQL)

            if not iResults:
                sSQL = "delete from deployment_template where template_id in (" + sDeleteArray + ")"
                if not self.db.tran_exec_noexcep(sSQL):
                    uiCommon.log_nouser(self.db.error, 0)
                
                #if we made it here, save the logs
                uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.DeploymentTemplate, "", "", "Templates(s) Deleted [" + sDeleteArray + "]")
            else:
                return "{\"info\" : \"Unable to delete - %d Deployments are referencing these templates.\"}" % iResults
                
            return "{\"result\" : \"success\"}"
            
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)
            return traceback.format_exc()

    def wmGetDeploymentsTable(self):
        """ Get a list of all Deployments"""
        try:
            sHTML = ""
            pager_html = ""
            sFilter = uiCommon.getAjaxArg("sSearch")
            sPage = uiCommon.getAjaxArg("sPage")
            maxrows = 25

            deps = deployment.Deployments(sFilter)
            if deps.rows:
                start, end, pager_html = uiCommon.GetPager(len(deps.rows), maxrows, sPage)

                for row in deps.rows[start:end]:
                    sHTML += """
                    <tr deployment_id="{0}">
                    <td class="chkboxcolumn">    
                        <input type="checkbox" class="chkbox" id="chk_{0}" object_id="{0}" tag="chk" />
                    </td>
                    
                    <td class="selectable">{1}</td>
                    <td class="selectable">{2}</td>
                    <td class="selectable">{3}</td>
                    
                    </tr>
                    """.format(row["ID"], row["Name"], row["Status"], row["Description"] if row["Description"] else "")
    
            return "{\"pager\" : \"%s\", \"rows\" : \"%s\"}" % (uiCommon.packJSON(pager_html), uiCommon.packJSON(sHTML))    
        except Exception:
            uiCommon.log(traceback.format_exc())
            
    def wmCreateDeployment(self):
        try:
            sName = uiCommon.getAjaxArg("name")
            sOwner = uiCommon.getAjaxArg("owner")
            sDescription = uiCommon.getAjaxArg("desc")
    
            dep, msg = deployment.Deployment.DBCreateNew(uiCommon.unpackJSON(sName), sOwner, uiCommon.unpackJSON(sDescription))
            if dep is not None:
                uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Deployment, dep.ID, dep.Name, "Deployment created.")
                return "{\"deployment_id\" : \"%s\"}" % dep.ID
            else:
                uiCommon.log(msg)
                return "{\"info\" : \"%s\"}" % msg
        except Exception:
            uiCommon.log(traceback.format_exc())

    def wmGetDeployment(self):
        try:
            sID = uiCommon.getAjaxArg("id")
            d = deployment.Deployment()
            if d:
                d.FromID(sID)
                if d.ID:
                    return d.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get Deployment details for ID [" + sID + "].\"}"
        except Exception:
            uiCommon.log(traceback.format_exc())
            return traceback.format_exc()

    def wmGetTemplate(self):
        try:
            sID = uiCommon.getAjaxArg("id")
            dt = deployment.DeploymentTemplate()
            dt.FromID(sID)
            if dt.ID:
                return dt.AsJSON()
            
            #should not get here if all is well
            return "{\"result\":\"fail\",\"error\":\"Failed to get Template details for ID [" + sID + "].\"}"
        except Exception:
            uiCommon.log(traceback.format_exc())
            return traceback.format_exc()

    def wmValidateTemplate(self):
        try:
            template_json = uiCommon.getAjaxArg("template")
            dt, validation_err = deployment.Deployment.ValidateJSON(template_json)
            if dt:
                return "{\"result\" : \"success\"}"
            
            #should not get here if all is well
            return catocommon.ObjectOutput.AsJSON({"error" : validation_err})
        except Exception:
            uiCommon.log(traceback.format_exc())
            return traceback.format_exc()

    def wmGetTemplateDeployments(self):
        try:
            template_id = uiCommon.getAjaxArg("template_id")
        
            sHTML = ""

            if template_id:
                t = deployment.DeploymentTemplate()
                t.FromID(template_id)
                if t:
                    deps = t.GetDeployments()
                    sHTML += "<ul>"
                    for d in deps:
                        desc = (d["Description"] if d["Description"] else "")

                        sHTML += "<li class=\"ui-widget-content ui-corner-all\"" \
                            " deployment_id=\"" + d["ID"] + "\"" \
                            "\">"
                        sHTML += "<div class=\"step_header_title deployment_name\">"
                        sHTML += "<img src=\"static/images/icons/deployments_24.png\" alt=\"\" /> " + d["Name"]
                        sHTML += "</div>"

                        sHTML += "<div class=\"step_header_icons\">"

                        # if there's a description, show a tooltip
                        if desc:
                            sHTML += "<span class=\"ui-icon ui-icon-info deployment_tooltip\" title=\"" + desc + "\"></span>"

                        sHTML += "</div>"
                        sHTML += "<div class=\"clearfloat\"></div>"
                        sHTML += "</li>"

                    sHTML += "</ul>"
            else:
                uiCommon.log("Unable to get Deployments - Missing Template ID")

            return sHTML
        except Exception:
            uiCommon.log_nouser(traceback.format_exc(), 0)

    def wmUpdateDeploymentDetail(self):
        try:
            sDeploymentID = uiCommon.getAjaxArg("id")
            sColumn = uiCommon.getAjaxArg("column")
            sValue = uiCommon.getAjaxArg("value")
    
            sUserID = uiCommon.GetSessionUserID()

            if catocommon.is_guid(sDeploymentID) and catocommon.is_guid(sUserID):
                d = deployment.Deployment()
                d.FromID(sDeploymentID)
                
                if d:
                    # we encoded this in javascript before the ajax call.
                    # the safest way to unencode it is to use the same javascript lib.
                    # (sometimes the javascript and .net libs don't translate exactly, google it.)
                    sValue = uiCommon.unpackJSON(sValue)

                    #  check for existing name
                    if sColumn == "Name":
                        if d.Name == sValue:
                            return sValue + " exists, please choose another name."

                    # cool, update the class attribute by name, using getattr!
                    # python is so cool.. I don't even need to check if the attribute I wanna set exists.
                    # just set it
                    setattr(d, sColumn, sValue)
                    
                    bSuccess, msg = d.DBUpdate()
                    if bSuccess:
                        uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Deployment, sDeploymentID, sColumn, sValue)
                        return "{\"result\" : \"success\"}"
                    else:
                        uiCommon.log(msg)
                        return "{\"info\" : \"%s\"}" % msg
                else:
                    uiCommon.log("Unable to update Deployment. Missing or invalid id [%s]." % sDeploymentID)
                    return "Unable to update Deployment. Missing or invalid id [%s]." % sDeploymentID
                
                return ""
        except Exception:
            uiCommon.log(traceback.format_exc())

    def wmUpdateTemplateDetail(self):
        try:
            sTemplateID = uiCommon.getAjaxArg("id")
            sColumn = uiCommon.getAjaxArg("column")
            sValue = uiCommon.getAjaxArg("value")
    
            sUserID = uiCommon.GetSessionUserID()

            if catocommon.is_guid(sTemplateID) and catocommon.is_guid(sUserID):
                d = deployment.DeploymentTemplate()
                d.FromID(sTemplateID)
                
                if d:
                    # we encoded this in javascript before the ajax call.
                    # the safest way to unencode it is to use the same javascript lib.
                    # (sometimes the javascript and .net libs don't translate exactly, google it.)
                    sValue = uiCommon.unpackJSON(sValue)

                    #  check for existing name
                    if sColumn == "Name":
                        if d.Name == sValue:
                            return sValue + " exists, please choose another name."

                    # cool, update the class attribute by name, using getattr!
                    # python is so cool.. I don't even need to check if the attribute I wanna set exists.
                    # just set it
                    setattr(d, sColumn, sValue)
                    
                    bSuccess, msg = d.DBUpdate()
                    if bSuccess:
                        uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.DeploymentTemplate, sTemplateID, sColumn, sValue)
                        return "{\"result\" : \"success\"}"
                    else:
                        uiCommon.log(msg)
                        return "{\"info\" : \"%s\"}" % msg
                else:
                    uiCommon.log("Unable to update Template. Missing or invalid id [%s]." % sTemplateID)
                    return "Unable to update Template. Missing or invalid id [%s]." % sTemplateID
                
                return ""
        except Exception:
            uiCommon.log(traceback.format_exc())

