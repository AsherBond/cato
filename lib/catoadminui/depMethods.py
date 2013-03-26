
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

import os
import sys
import json

# CATO will check for MAESTRO_HOME environment variable.
# if found, we will add libs from that path

# AT THE MOMENT, this is only necessary to enable the deploymentTemplate pages.
if not os.environ.has_key("MAESTRO_HOME") or not os.environ["MAESTRO_HOME"]:
    raise Exception("MAESTRO_HOME environment variable not set.  Maestro is required for Deployment features.")

MAESTRO_HOME = os.environ["MAESTRO_HOME"]
sys.path.insert(0, os.path.join(MAESTRO_HOME, "lib"))



from catoui import uiCommon
from catocommon import catocommon
from catodeployment import deployment
from catoerrors import WebmethodInfo

class depMethods:
    db = None

    def wmGetTemplatesTable(self):
        """ Get a list of all Deployment Templates"""
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

        return json.dumps({"pager" : uiCommon.packJSON(pager_html), "rows" : uiCommon.packJSON(sHTML)})
            
    def wmCreateTemplate(self):
        name = uiCommon.getAjaxArg("name")
        version = uiCommon.getAjaxArg("version")
        desc = uiCommon.getAjaxArg("desc")
        template = uiCommon.getAjaxArg("template")

        t = deployment.DeploymentTemplate.DBCreateNew(name, version, uiCommon.unpackJSON(template), uiCommon.unpackJSON(desc))
        if t is not None:
            uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Deployment, t.ID, t.Name, "Deployment Template created.")
            return json.dumps({"template_id" : t.ID})

    def wmDeleteTemplates(self):
        sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
        if len(sDeleteArray) < 36:
            raise WebmethodInfo("Unable to delete - no selection.")

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
            
            # if we made it here, save the logs
            uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.DeploymentTemplate, "", "", "Templates(s) Deleted [" + sDeleteArray + "]")
        else:
            raise WebmethodInfo("Unable to delete - %d Deployments are referencing these templates." % iResults)
            
        return json.dumps({"result" : "success"})

    def wmGetDeploymentsTable(self):
        """ Get a list of all Deployments"""
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

        return json.dumps({"pager" : uiCommon.packJSON(pager_html), "rows" : uiCommon.packJSON(sHTML)})
            
    def wmGetDeployment(self):
        sID = uiCommon.getAjaxArg("id")
        d = deployment.Deployment()
        d.FromID(sID)
        return d.AsJSON()

    def wmGetTemplate(self):
        sID = uiCommon.getAjaxArg("id")
        dt = deployment.DeploymentTemplate()
        dt.FromID(sID)
        return dt.AsJSON()

    def wmValidateTemplate(self):
        template_json = uiCommon.getAjaxArg("template")
        dt, validation_err = deployment.Deployment.ValidateJSON(template_json)
        if dt:
            return json.dumps({"result" : "success"})
            
        raise Exception(validation_err.replace("\n", "<br />"))

    def wmGetTemplateDeployments(self):
        template_id = uiCommon.getAjaxArg("template_id")
    
        sHTML = ""

        t = deployment.DeploymentTemplate()
        t.FromID(template_id)
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

        return sHTML

    def wmUpdateDeploymentDetail(self):
        sDeploymentID = uiCommon.getAjaxArg("id")
        sColumn = uiCommon.getAjaxArg("column")
        sValue = uiCommon.getAjaxArg("value")

        sUserID = uiCommon.GetSessionUserID()

        if catocommon.is_guid(sDeploymentID) and catocommon.is_guid(sUserID):
            d = deployment.Deployment()
            d.FromID(sDeploymentID)

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
            
            d.DBUpdate()
            uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Deployment, sDeploymentID, sColumn, sValue)

        return json.dumps({"result" : "success"})

    def wmUpdateTemplateDetail(self):
        sTemplateID = uiCommon.getAjaxArg("id")
        sColumn = uiCommon.getAjaxArg("column")
        sValue = uiCommon.getAjaxArg("value")

        dt = deployment.DeploymentTemplate()
        dt.FromID(sTemplateID)

        # we encoded this in javascript before the ajax call.
        # the safest way to unencode it is to use the same javascript lib.
        # (sometimes the javascript and .net libs don't translate exactly, google it.)
        sValue = uiCommon.unpackJSON(sValue)

        #  check for existing name
        if sColumn == "Name":
            if dt.Name == sValue:
                return sValue + " exists, please choose another name."

        # cool, update the class attribute by name, using getattr!
        # python is so cool.. I don't even need to check if the attribute I wanna set exists.
        # just set it
        setattr(dt, sColumn, sValue)
        
        dt.DBUpdate()
        uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.DeploymentTemplate, sTemplateID, sColumn, sValue)

        return json.dumps({"result" : "success"})

