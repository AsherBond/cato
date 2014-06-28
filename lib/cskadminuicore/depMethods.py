
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

# AT THE MOMENT, this is only necessary to enable the deploymentTemplate pages.
try:
    sys.path.insert(0, os.path.join(os.environ["CSK_HOME"], "maestro", "lib"))
    from catodeployment import deployment
except:
    raise Exception("'Maestro' is not installed in $CSK_HOME/maestro.")

from catoui import uiCommon
from catocommon import catocommon
from catoerrors import InfoException

class depMethods:
    db = None

    def wmGetTemplatesTable(self):
        """ Get a list of all Deployment Templates"""
        sHTML = ""
        pager_html = ""
        sFilter = uiCommon.getAjaxArg("sSearch")
        sPage = uiCommon.getAjaxArg("sPage")
        maxrows = 25

        deps = deployment.DeploymentTemplates(sFilter, show_unavailable=True)
        if deps.rows:
            start, end, pager_html = uiCommon.GetPager(len(deps.rows), maxrows, sPage)

            for row in deps.rows[start:end]:
                available = 'Yes' if row["Available"] else 'No'

                sHTML += """
                <tr template_id="{0}">
                <td class="chkboxcolumn">    
                    <input type="checkbox" class="chkbox" id="chk_{0}" object_id="{0}" tag="chk" />
                </td>""".format(row["ID"])

                sHTML += '<td class="selectable">' + row["Name"] + '</td>'
                sHTML += '<td class="selectable">' + row["Version"] + '</td>'
                sHTML += '<td class="selectable">' + (row["Description"] if row["Description"] else "") + '</td>'
                sHTML += '<td class="selectable">' + available + '</td>'

                sHTML += "</tr>"

        return json.dumps({"pager": uiCommon.packJSON(pager_html), "rows": uiCommon.packJSON(sHTML)})

    def wmCreateTemplate(self):
        name = uiCommon.getAjaxArg("name")
        version = uiCommon.getAjaxArg("version")
        desc = uiCommon.getAjaxArg("desc")
        template = uiCommon.getAjaxArg("template")

        t = deployment.DeploymentTemplate.DBCreateNew(name, version, uiCommon.unpackJSON(template), uiCommon.unpackJSON(desc))
        if t is not None:
            # create matching tags... this template gets all the tags this user has.

            uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Deployment, t.ID, t.Name, "Deployment Template created.")
            return json.dumps({"template_id": t.ID})

    def wmCopyTemplate(self):
        name = uiCommon.getAjaxArg("name")
        version = uiCommon.getAjaxArg("version")
        template = uiCommon.getAjaxArg("template")

        t = deployment.DeploymentTemplate()
        t.FromID(template)
        obj = t.DBCopy(name, version)

        if obj is not None:
            # TODO: create matching tags... this template gets all the tags this user has.

            uiCommon.WriteObjectAddLog(catocommon.CatoObjectTypes.Deployment, obj.ID, obj.Name, "Deployment Template created.")
            return json.dumps({"template_id": t.ID})

    def wmDeleteTemplates(self):
        sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")
        if len(sDeleteArray) < 36:
            raise InfoException("Unable to delete - no selection.")

        sDeleteArray = uiCommon.QuoteUp(sDeleteArray)

        # can't delete it if it's referenced.
        sSQL = """select count(*) from deployment d
            join deployment_template dt on d.template_id = dt.template_id
            where dt.template_id in (%s)""" % sDeleteArray

        iResults = self.db.select_col_noexcep(sSQL)

        if not iResults:
            sSQL = "delete from deployment_template where template_id in (" + sDeleteArray + ")"
            if not self.db.tran_exec_noexcep(sSQL):
                uiCommon.log_nouser(self.db.error, 0)

            # if we made it here, save the logs
            uiCommon.WriteObjectDeleteLog(catocommon.CatoObjectTypes.DeploymentTemplate, "", "", "Templates(s) Deleted [" + sDeleteArray + "]")
        else:
            raise InfoException("Unable to delete - %d Deployments are referencing these templates." % iResults)

        return json.dumps({"result": "success"})

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
                sHTML += u"""
                <tr deployment_id="{0}">
                <td class="chkboxcolumn">    
                    <input type="checkbox" class="chkbox" id="chk_{0}" object_id="{0}" tag="chk" />
                </td>
                
                <td class="selectable">{1}</td>
                <td class="selectable">{2}</td>
                <td class="selectable">{3}</td>
                
                </tr>
                """.format(row["ID"], row["Name"], row["RunState"], row.get("Description", ""))

        return json.dumps({"pager": uiCommon.packJSON(pager_html), "rows": uiCommon.packJSON(sHTML)})

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
        dt, validation_err = deployment.DeploymentTemplate.ValidateJSON(template_json)
        if dt:
            return json.dumps({"result": "success"})

        raise InfoException(validation_err.replace("\n", "<br />"))

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

        return json.dumps({"result": "success"})

    def wmAddDeploymentGroup(self):
        sDeploymentID = uiCommon.getAjaxArg("id")
        sGroupName = uiCommon.getAjaxArg("group_name")

        if sGroupName:
            sUserID = uiCommon.GetSessionUserID()

            if catocommon.is_guid(sDeploymentID) and catocommon.is_guid(sUserID):
                d = deployment.Deployment()
                d.FromID(sDeploymentID)

                d.AddGroup(sGroupName)
                uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Deployment, sDeploymentID, d.Name, "Added Group [%s]" % (sGroupName))

        return json.dumps({"result": "success"})

    def wmDeleteDeploymentGroup(self):
        sDeploymentID = uiCommon.getAjaxArg("id")
        sGroupName = uiCommon.getAjaxArg("group_name")

        sUserID = uiCommon.GetSessionUserID()

        if catocommon.is_guid(sDeploymentID) and catocommon.is_guid(sUserID):
            d = deployment.Deployment()
            d.FromID(sDeploymentID)

            d.DeleteGroup(sGroupName)
            uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.Deployment, sDeploymentID, d.Name, "Removed Group [%s]" % (sGroupName))

        return json.dumps({"result": "success"})

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

        # cool, update the class attribute by name, using getattr!
        # python is so cool.. I don't even need to check if the attribute I wanna set exists.
        # just set it
        setattr(dt, sColumn, sValue)

        dt.DBUpdate()
        uiCommon.WriteObjectChangeLog(catocommon.CatoObjectTypes.DeploymentTemplate, sTemplateID, sColumn, sValue)

        return json.dumps({"result": "success"})

    def wmDeleteDeployments(self):
        # this is an admin function
        if uiCommon.GetSessionUserRole() != "Administrator":
            raise InfoException("Only an Administrator can delete a Deployed Application.")


        sDeleteArray = uiCommon.getAjaxArg("sDeleteArray")

        ids_to_delete = sDeleteArray.split(",")
        if ids_to_delete:
            for did in ids_to_delete:
                obj = deployment.Deployment()
                obj.FromID(did)
                # no success check, just carry on
                obj.DBDelete()

        return json.dumps({"result": "success"})
