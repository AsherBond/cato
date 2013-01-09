
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
 
import traceback
from catoui import uiCommon as UI, uiGlobals
try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

from catotask import task
from catocommon import catocommon
from catocloud import cloud

"""
LIKE uiCommon - this isn't a class that gets instantiated ... it's just a collection of 
all the functions used to draw the Task Steps.
"""

def GetSingleStep(sStepID, sUserID):
    return task.Step.FromIDWithSettings(sStepID, sUserID)
    
def DrawFullStep(oStep):
    sStepID = oStep.ID
    
    # this uses a uiCommon function, because the functions were cached
    fn = UI.GetTaskFunction(oStep.FunctionName)
    if fn:
        oStep.Function = fn
    else:
        #the function doesn't exist (was probably deprecated)
        #we need at least a basic strip with a delete button
        sNoFunc = "<li class=\"step\" id=\"" + sStepID + "\">"            
        sNoFunc += "    <div class=\"ui-state-default ui-state-highlight step_header\" id=\"step_header_" + sStepID + "\">"
        sNoFunc += "        <div class=\"step_header_title\"><img src=\"static/images/icons/status_unknown_16.png\" /></div>"
        sNoFunc += "        <div class=\"step_header_icons\">"
        sNoFunc += "            <span class=\"ui-icon ui-icon-close forceinline step_delete_btn\" remove_id=\"" + sStepID + "\"></span>"
        sNoFunc += "        </div>"
        sNoFunc += "    </div>"
        sNoFunc += "    <div id=\"step_detail_" + sStepID + "\" class=\"ui-widget-content ui-state-highlight ui-corner-bottom step_detail\" >"
        sNoFunc += "Error building Step - Unable to get the details for the command type '" + oStep.FunctionName + "'.<br />"
        sNoFunc += "This command type may have been deprecated - check the latest Cato release notes.<br />"
        sNoFunc += "    </div>"
        sNoFunc += "</li>"

        return sNoFunc

    
    sExpandedClass = ("" if oStep.UserSettings.Visible else "step_collapsed")
    sSkipStepClass = ("step_skip" if oStep.Commented else "")
    sSkipHeaderClass = ("step_header_skip" if oStep.Commented else "")
    sSkipIcon = ("play" if oStep.Commented else "pause")
    sSkipVal = ("1" if oStep.Commented else "0")

    # pay attention
    # this overrides the 'expanded class', making the step collapsed by default if it's commented out.
    # the 'skip' overrides the saved visibility preference.
    if oStep.Commented:
        sExpandedClass = "step_collapsed"
    

    sMainHTML = ""
    
    #what's the 'label' for the step strip?
    #(hate this... wish the label was consistent across all step types)
    #hack for initial loading of the step... don't show the order if it's a "-1"... it's making a
    #strange glitch in the browser...you can see it update
    sIcon = ("" if not oStep.Function.Icon else oStep.Function.Icon)
    sStepOrder = ("" if oStep.Order == -1 else str(oStep.Order))
    sLabel = "<img class=\"step_header_function_icon\" src=\"" + sIcon + "\" alt=\"\" />" \
        "<span class=\"step_order_label\">" + str(sStepOrder) + "</span> : " + \
        oStep.Function.Category.Label + " - " + oStep.Function.Label

    #show a useful snip in the title bar.
    #notes trump values, and not all commands show a value snip
    #but certain ones do.
    sSnip = ""
    if oStep.Description:
        sSnip = UI.GetSnip(oStep.Description, 75)
        #special words get in indicator icon, but only one in highest order
        if "IMPORTANT" in sSnip:
            sSnip = "<img src=\"static/images/icons/flag_red.png\" />" + sSnip.replace("IMPORTANT", "")
        elif "TODO" in sSnip:
            sSnip = "<img src=\"static/images/icons/flag_yellow.png\" />" + sSnip.replace("TODO", "")
        elif "NOTE" in sSnip or "INFO" in sSnip:
            sSnip = "<img src=\"static/images/icons/flag_blue.png\" />" + sSnip.replace("NOTE", "").replace("INFO", "")
    else:
        # SOME commands are defined to show a value snip 
        if oStep.ValueSnip:
            sSnip = oStep.ValueSnip

    
    sLabel += ("" if sSnip == "" else "<span style=\"padding-left:15px; font-style:italic; font-weight:normal\">[" + sSnip + "]</span>")

    sLockClause = (" onclick=\"return false\"" if oStep.Locked else "")

    
    sMainHTML += "<li class=\"step " + sSkipStepClass + "\" id=\"" + sStepID + "\" name=\"" + sStepID + "\" " + sLockClause + ">"
    
    
    # step expand image
    sExpandImage = "triangle-1-s"
    if sExpandedClass == "step_collapsed": 
        sExpandImage = "triangle-1-e"

    sMainHTML += "    <div class=\"ui-state-default step_header " + sSkipHeaderClass + "\"" \
        " id=\"step_header_" + sStepID + "\">"
    sMainHTML += "        <div class=\"step_header_title\">"
    sMainHTML += "            <span class=\"step_toggle_btn\" step_id=\"" + sStepID + "\">" \
    " <img class=\"ui-icon ui-icon-" + sExpandImage + " forceinline expand_image\" title=\"Hide/Show Step\" /></span>"
    sMainHTML += "            <span>" + sLabel + "</span>"
    sMainHTML += "        </div>"
    sMainHTML += "        <div class=\"step_header_icons\">"

    #this button will copy a step into the clipboard.
    sMainHTML += "            <span id=\"step_copy_btn_" + sStepID + "\"" \
        " class=\"ui-icon ui-icon-copy forceinline step_copy_btn\" step_id=\"" + sStepID + "\"" \
        " title=\"Copy this Step to your Clipboard\"></span>"

    #this button is data enabled.  it controls the value of the hidden field at the top of the step.
    sMainHTML += "            <span id=\"step_skip_btn_" + sStepID + "\" skip=\"" + sSkipVal + "\"" \
        " class=\"ui-icon ui-icon-" + sSkipIcon + " forceinline step_skip_btn\" step_id=\"" + sStepID + "\"" \
        " title=\"Skip this Step\"></span>"

    sMainHTML += "            <span class=\"ui-icon ui-icon-close forceinline step_delete_btn\" remove_id=\"" + sStepID + "\" title=\"Delete Step\"></span>"
    sMainHTML += "        </div>"
    sMainHTML += "    </div>"
    sMainHTML += "    <div id=\"step_detail_" + sStepID + "\"" \
        " class=\"ui-widget-content ui-corner-bottom step_detail " + sExpandedClass + "\" >"
    
    #!!! this returns a tuple with optional "options" and "variable" html
    sStepHTML, sOptionHTML, sVariableHTML = GetStepTemplate(oStep)
    sMainHTML += sStepHTML
    
    #comment steps don't have a common section - all others do
    if oStep.FunctionName != "comment":
        sMainHTML += DrawStepCommon(oStep, sOptionHTML, sVariableHTML)
    
    
    sMainHTML += "    </div>"

    sMainHTML += "</li>"

    return sMainHTML

def GetStepTemplate(oStep):
    if oStep.IsValid == False:
        return "This step is damaged.  Check the log file for details.  It may be necessary to delete and recreate it.", "", ""

    sFunction = oStep.FunctionName
    sHTML = ""
    sOptionHTML = ""
    sVariableHTML = ""
    bShowVarButton = True
    # NOTE: If you are adding a new command type, be aware that
    # you MIGHT need to modify the code in taskMethods for the wmAddStep function.
    # (depending on how your new command works)

    # Special Commands have their own render functions.
    # What makes 'em special?  Basically they have dynamic content, or hardcoded rules.
    # several commands have 'embedded' content, and draw a 'drop zone'
    # if a command "populates variables", it currently has to be hardcoded
    # in some cases, they even update the db on render to keep certain values clean
    
    ## PERSONAL NOTE - while converting the hardcoded ones, make use of the Draw Field function
    ## at least then things will be more consistent, and less html in the hardcoding.
    
    ## AND MAKE SURE to reference the old code when building out the xml, to make sure nothing is missed
    # (styles, etc.)

    if sFunction.lower() == "new_connection":
        sHTML = NewConnection(oStep)
    elif sFunction.lower() == "codeblock":
        sHTML = Codeblock(oStep)
    elif sFunction.lower() == "if":
        sHTML = If(oStep)
    elif sFunction.lower() == "sql_exec":
        sHTML, bShowVarButton = SqlExec(oStep)
    elif sFunction.lower() == "set_variable":
        sHTML = SetVariable(oStep)
    elif sFunction.lower() == "clear_variable":
        sHTML = ClearVariable(oStep)
    elif sFunction.lower() == "wait_for_tasks":
        sHTML = WaitForTasks(oStep)
    elif sFunction.lower() == "set_ecosystem_registry":
        sHTML = SetEcosystemRegistry(oStep)
    elif sFunction.lower() == "subtask":
        sHTML = Subtask(oStep)
    elif sFunction.lower() == "run_task":
        sHTML = RunTask(oStep)
    elif sFunction.lower() == "get_ecosystem_objects":
        sHTML = GetEcosystemObjects(oStep)
    elif sFunction.lower() == "transfer":
        sHTML = "Not Yet Available" #Transfer(oStep)
    elif sFunction.lower() == "set_asset_registry":
        sHTML = "Not Yet Available" #SetAssetRegistry(oStep)
    elif sFunction.lower() == "loop":
        sHTML = Loop(oStep)
    elif sFunction.lower() == "while":
        sHTML = While(oStep)
    elif sFunction.lower() == "exists":
        sHTML = Exists(oStep)
    else:
        # We didn't find one of our built in commands.  That's ok - most commands are drawn from their XML.
        sHTML, sOptionHTML = DrawStepFromXMLDocument(oStep)
    
    if bShowVarButton:
        # IF a command "populates variables" it will be noted in the command xml
        # is the variables xml attribute true?
        xd = oStep.FunctionXDoc
        if xd is not None:
            sPopulatesVars = xd.get("variables", "false")
            UI.log("Populates Variables? " + sPopulatesVars, 4)
            if catocommon.is_true(sPopulatesVars):
                sVariableHTML += DrawVariableSectionForDisplay(oStep, True)
    
    # This returns a Tuple with three values.
    return sHTML, sOptionHTML, sVariableHTML

def DrawReadOnlyStep(oStep, bDisplayNotes):
    sStepID = oStep.ID

    fn = UI.GetTaskFunction(oStep.FunctionName)
    if fn is None:
        # the function doesn't exist (was probably deprecated)
        # we need at least a basic strip with a delete button
        sNoFunc = "<li>";            
        sNoFunc += "<div class=\"ui-state-default ui-state-highlightview_step\" id=\"" + sStepID + "\">"
        sNoFunc += "    <div class=\"view_step_header ui-state-default ui-state-highlight\" id=\"view_step_header_" + sStepID + "\"><img src=\"static/images/icons/status_unknown_16.png\" /></div>"
        sNoFunc += "    <div class=\"view_step_detail ui-state-highlight\" id=\"step_detail_" + sStepID + "\">"
        sNoFunc += "Error building Step - Unable to get the details for the command type '" + oStep.FunctionName + "'.<br />"
        sNoFunc += "This command type may have been deprecated - check the latest Cato release notes.<br />"
        sNoFunc += "      </div>"
        sNoFunc += "</div>"
        sNoFunc += "</li>"

        return sNoFunc
    
    # set this global flag so embedded steps will know what to do
    bShowNotes = bDisplayNotes

    sMainHTML = ""
    sOptionHTML = ""

    sStepOrder = ("" if oStep.Order == -1 else str(oStep.Order) + ": ")

    # labels are different here than in Full Steps.
    sLabel = sStepOrder + fn.Category.Label + " - " + fn.Label
    sSkipHeaderClass = ("step_header_skip" if oStep.Commented else "")
    sSkipStepClass = ("step_skip" if oStep.Commented else "")
    
    sSkipClass = ""
    sExpandedClass = ""
    if oStep.Commented:
        sExpandedClass = "step_collapsed"
        sSkipClass = "style=\"color: #ACACAC\""

    sMainHTML += "<li class=\"step " + sSkipStepClass + "\" id=\"" + sStepID + "\">"
    sMainHTML += "<div class=\"view_step " + sSkipHeaderClass + "\" id=\"" + sStepID + "\">"
    sMainHTML += "    <div class=\"ui-state-default view_step_header " + sSkipHeaderClass + "\" id=\"view_step_header_" + sStepID + "\">"
    sMainHTML += "       <span " + sSkipClass + ">" + sLabel + "</span>"
    sMainHTML += "    </div>"
    sMainHTML += "    <div class=\"view_step_detail " + sExpandedClass + "\" id=\"step_detail_" + sStepID + "\">"

    html, sOptionHTML = GetStepTemplate_View(oStep)
    sMainHTML += html

#    if bShowNotes:
#        if oStep.Description:
#            sMainHTML += DrawStepNotes_View(oStep.Description)
#
    if sOptionHTML != "":
        sMainHTML += DrawStepOptions_View(sOptionHTML)

    # sMainHTML += "    </div>"
    sMainHTML += "</div>"
    sMainHTML += "</li>"

    return sMainHTML

def GetStepTemplate_View(oStep):
    sFunction = oStep.FunctionName
    sHTML = ""
    sOptionHTML = ""
    bShowVars = False
    
    if sFunction.lower() == "if":
        sHTML = If_View(oStep)
    elif sFunction.lower() == "loop":
        sHTML = Loop_View(oStep)
    elif sFunction.lower() == "loop":
        sHTML = Loop_View(oStep)
    elif sFunction.lower() == "while":
        sHTML = While_View(oStep)
    elif sFunction.lower() == "exists":
        sHTML = Exists_View(oStep)
    elif sFunction.lower() == "new_connection":
        sHTML = NewConnection_View(oStep)
    elif sFunction.lower() == "run_task":
        sHTML = RunTask_View(oStep)
    elif sFunction.lower() == "subtask":
        sHTML = Subtask_View(oStep)
    elif sFunction.lower() == "sql_exec":
        sHTML = SqlExec_View(oStep)
    else:
        sHTML, sOptionHTML = DrawReadOnlyStepFromXMLDocument(oStep)
        
    # oStep.OutputParseType is how we know to show variables
    # 
    if oStep.OutputParseType > 0:
        sVars = DrawVariableSectionForDisplay(oStep, False)
        if sVars:
            sHTML += "<hr />Variables:" + sVars
    
    return sHTML, sOptionHTML

def DrawReadOnlyStepFromXMLDocument(oStep):
    xd = oStep.FunctionXDoc
    sHTML = ""
    sOptionHTML = ""
    if xd is not None:
        for xe in xd:
            # PAY ATTENTION!
            # there are a few xml nodes inside the function_xml that are reserved for internal features.
            # these nodes WILL NOT BE DRAWN as part of the step editing area.
            
            # "variables" is a reserved node name
            if xe.tag == "step_variables": 
                continue
            
            # now, for embedded content, the step may have an xpath "prefix"
            sXPath = xe.tag
            
            UI.log("Drawing [" + sXPath + "]", 4)
            sNodeHTML, sNodeOptionHTML = DrawReadOnlyNode(xe, sXPath, oStep)
            sHTML += sNodeHTML
            sOptionHTML += sNodeOptionHTML
            
    return sHTML, sOptionHTML

def DrawStepFromXMLDocument(oStep):
    xd = oStep.FunctionXDoc
    # 
    # * This block reads the XML for a step and uses certain node attributes to determine how to draw the step.
    # *
    # * attributes include the type of input control to draw
    # * the size of the field,
    # * whether or not to HTML break after
    # * etc
    # *
    # 
    sHTML = ""
    sOptionHTML = ""
    #UI.log("Command XML:", 4)
    #UI.log(ET.tostring(xd), 4)
    if xd is not None:
        # for each node in the function element
        # each node will become a field on the step.
        # some fields may be defined to go on an "options tab", in which case they will come back as sNodeOptionHTML
        # you'll never get back both NodeHTML and OptionHTML - one will always be blank.
        for xe in xd:
            # PAY ATTENTION!
            # there are a few xml nodes inside the function_xml that are reserved for internal features.
            # these nodes WILL NOT BE DRAWN as part of the step editing area.
            
            # "variables" is a reserved node name
            if xe.tag == "step_variables": 
                continue
            
            # now, for embedded content, the step may have an xpath "prefix"
            sXPath = xe.tag
            
            UI.log("Drawing [" + sXPath + "]", 4)
            sNodeHTML, sNodeOptionHTML = DrawNode(xe, sXPath, oStep)
            sHTML += sNodeHTML
            sOptionHTML += sNodeOptionHTML
            
    return sHTML, sOptionHTML
    
def DrawNode(xeNode, sXPath, oStep, bIsRemovable=False):
    """
    Some important notes:
    1) a node IsEditable if it has the attribute "is_array".  (It's an array, therefore it's contents are 'editable'.)
    2) a node IsRemovable if it's PARENT IsEditable.  So, we pass IsEditable down to subsequent recursions as IsRemovable.)
    """
    # the base xpath of this command (will be '' unless this is embedded)
    # NOTE: do not append the base_path on any CommonAttribs calls, it's done inside that function.
    base_xpath = (oStep.XPathPrefix + "/" if oStep.XPathPrefix else "")  

    sHTML = ""
    sNodeName = xeNode.tag
    
    sNodeLabel = xeNode.get("label", sNodeName)
    sIsEditable = xeNode.get("is_array", "")
    bIsEditable = catocommon.is_true(sIsEditable)
    
    sOptionTab = xeNode.get("option_tab", "")
    
    UI.log("-- Label: " + sNodeLabel, 4)
    UI.log("-- Editable: " + sIsEditable + " - " + str(bIsEditable), 4)
    UI.log("-- Removable: " + str(bIsRemovable), 4)
    UI.log("-- Elements: " + str(len(xeNode)), 4)
    UI.log("-- Option Field?: " + sOptionTab, 4)
    
    #if a node has children we'll draw it with some hierarchical styling.
    #AND ALSO if it's editable, even if it has no children, we'll still draw it as a container.
    
    # this dict holds the nodes that have the same name
    # meaning they are part of an array
    dictNodes = {}
    
    if len(xeNode) > 0 or bIsEditable:
        #if there is only one child, AND it's not part of an array
        #don't draw the header or the bounding box, just a composite field label.
        if len(xeNode) == 1 and not bIsEditable:
            UI.log("-- no more children ... drawing ... ", 4)
            #get the first (and only) node
            xeOnlyChild = xeNode[0] #.find("*[1]")
            
            #call DrawNode just on the off chance it actually has children
            sChildXPath = sXPath + "/" + xeOnlyChild.tag
            # DrawNode returns a tuple, but here we only care about the first value
            # because "editable" nodes shouldn't be options.
            sNodeHTML, sOptionHTML = DrawNode(xeOnlyChild, sChildXPath, oStep, bIsEditable)
            if sOptionTab:
                sHTML += sNodeName + "." + sOptionHTML
            else:
                sHTML += sNodeName + "." + sNodeHTML
            
            #since we're making it composite, the parents are gonna be off.  Go ahead and draw the delete link here.
            if bIsRemovable:
                sHTML += "<span class=\"ui-icon ui-icon-close forceinline fn_node_remove_btn pointer\" remove_path=\"" + base_xpath + sXPath + "\" step_id=\"" + oStep.ID + "\"></span>"
        else: #there is more than one child... business as usual
            UI.log("-- more children ... drawing and drilling down ... ", 4)
            sHTML += "<div class=\"ui-widget-content ui-corner-bottom step_group\">" #this section
            sHTML += "  <div class=\"ui-state-default step_group_header\">" #header
            sHTML += "      <div class=\"step_header_title\">" + sNodeLabel + "</div>"
            #look, I know this next bit is crazy... but not really.
            #if THIS NODE is an editable array, it means you can ADD CHILDREN to it.
            #so, it gets an add link.
            sHTML += "<div class=\"step_header_icons\">" #step header icons
            if bIsEditable:
                sHTML += "<div class=\"ui-icon ui-icon-plus forceinline fn_node_add_btn pointer\"" + " step_id=\"" + oStep.ID + "\"" \
                    " function_name=\"" + oStep.FunctionName + "\"" \
                    " template_path=\"" + sXPath + "\"" \
                    " add_to_node=\"" + base_xpath + sXPath + "\"" \
                    " step_id=\"" + oStep.ID + "\">" \
                    "</div>"
    
            #BUT, if this nodes PARENT is editable, that means THIS NODE can be deleted.
            #so, it gets a delete link
            #you can't remove unless there are more than one
            if bIsRemovable:
                sHTML += "<span class=\"ui-icon ui-icon-close forceinline fn_node_remove_btn pointer\" remove_path=\"" + base_xpath + sXPath + "\" step_id=\"" + oStep.ID + "\"></span>"
            sHTML += "</div>" #end step header icons
            sHTML += "  </div>" #end header
    
            sHTML += "<div class=\"clearfloat\">"
            for xeChildNode in xeNode:
                sChildNodeName = xeChildNode.tag
                sChildXPath = sXPath + "/" + sChildNodeName
    
                # here's the magic... are there any children nodes here with the SAME NAME?
                # if so they need an index on the xpath
                if len(xeNode.findall(sChildNodeName)) > 1:
                    # since the document won't necessarily be in perfect order,
                    # we need to keep track of same named nodes and their indexes.
                    # so, stick each array node up in a lookup table.

                    # is it already in my lookup table?
                    iLastIndex = 0
                    if dictNodes.has_key(sChildNodeName):
                        # there, increment it and set it
                        iLastIndex = dictNodes[sChildNodeName] + 1
                        dictNodes[sChildNodeName] = iLastIndex
                    else:
                        # not there, add it
                        iLastIndex = 1
                        dictNodes[sChildNodeName] = iLastIndex

                    sChildXPath = sChildXPath + "[" + str(iLastIndex) + "]"
                    
                # it's not possible for an 'editable' node to be in the options tab if it's parents aren't,
                # so here we ignore the options return
                sNodeHTML, sBunk = DrawNode(xeChildNode, sChildXPath, oStep, bIsEditable)
                if sBunk:
                    UI.log("WARNING: This shouldn't have returned 'option' html.", 2)
                sHTML += sNodeHTML
    
            sHTML += "</div>"
            sHTML += "</div>"
    else: #end section
        sHTML += DrawField(xeNode, sXPath, oStep)
        #it may be that these fields themselves are removable
        if bIsRemovable:
            sHTML += "<span class=\"ui-icon ui-icon-close forceinline fn_node_remove_btn pointer\" remove_path=\"" + base_xpath + sXPath + "\" step_id=\"" + oStep.ID + "\"></span>"
    
    #ok, now that we've drawn it, it might be intended to go on the "options tab".
    #if so, stick it there
    if sOptionTab:
        return "", sHTML
    else:
        return sHTML, ""
        
def DrawReadOnlyNode(xeNode, sXPath, oStep):
    """
    Some important notes:
    1) a node IsEditable if it has the attribute "is_array".  (It's an array, therefore it's contents are 'editable'.)
    """
    sHTML = ""
    sNodeName = xeNode.tag
    
    sNodeLabel = xeNode.get("label", sNodeName)
    sIsEditable = xeNode.get("is_array", "")
    bIsEditable = catocommon.is_true(sIsEditable)
    
    sOptionTab = xeNode.get("option_tab", "")
    
    UI.log("-- Label: " + sNodeLabel, 4)
    UI.log("-- Editable: " + sIsEditable + " - " + str(bIsEditable), 4)
    UI.log("-- Elements: " + str(len(xeNode)), 4)
    UI.log("-- Option Field?: " + sOptionTab, 4)
    
    #if a node has children we'll draw it with some hierarchical styling.
    #AND ALSO if it's editable, even if it has no children, we'll still draw it as a container.
    
    # this dict holds the nodes that have the same name
    # meaning they are part of an array
    dictNodes = {}
    
    if len(xeNode) > 0 or bIsEditable:
        #if there is only one child, AND it's not part of an array
        #don't draw the header or the bounding box, just a composite field label.
        if len(xeNode) == 1 and not bIsEditable:
            UI.log("-- no more children ... drawing ... ", 4)
            #get the first (and only) node
            xeOnlyChild = xeNode[0] #.find("*[1]")
            
            #call DrawNode just on the off chance it actually has children
            sChildXPath = sXPath + "/" + xeOnlyChild.tag
            # DrawNode returns a tuple, but here we only care about the first value
            # because "editable" nodes shouldn't be options.
            sNodeHTML, sOptionHTML = DrawReadOnlyNode(xeOnlyChild, sChildXPath, oStep)
            if sOptionTab:
                sHTML += sNodeName + "." + sOptionHTML
            else:
                sHTML += sNodeName + "." + sNodeHTML
        else: #there is more than one child... business as usual
            UI.log("-- more children ... drawing and drilling down ... ", 4)
            sHTML += "<div class=\"ui-widget-content ui-corner-bottom step_group\">" #this section
            sHTML += "  <div class=\"ui-state-default step_group_header\">" #header
            sHTML += "      <div class=\"step_header_title\">" + sNodeLabel + "</div>"
            sHTML += "  </div>" #end header
    
            for xeChildNode in xeNode:
                sChildNodeName = xeChildNode.tag
                sChildXPath = sXPath + "/" + sChildNodeName
    
                # here's the magic... are there any children nodes here with the SAME NAME?
                # if so they need an index on the xpath
                if len(xeNode.findall(sChildNodeName)) > 1:
                    # since the document won't necessarily be in perfect order,
                    # we need to keep track of same named nodes and their indexes.
                    # so, stick each array node up in a lookup table.

                    # is it already in my lookup table?
                    iLastIndex = 0
                    if dictNodes.has_key(sChildNodeName):
                        # there, increment it and set it
                        iLastIndex = dictNodes[sChildNodeName] + 1
                        dictNodes[sChildNodeName] = iLastIndex
                    else:
                        # not there, add it
                        iLastIndex = 1
                        dictNodes[sChildNodeName] = iLastIndex

                    sChildXPath = sChildXPath + "[" + str(iLastIndex) + "]"
                    
                # it's not possible for an 'editable' node to be in the options tab if it's parents aren't,
                # so here we ignore the options return
                sNodeHTML, sBunk = DrawReadOnlyNode(xeChildNode, sChildXPath, oStep)
                if sBunk:
                    UI.log("WARNING: This shouldn't have returned 'option' html.", 2)
                sHTML += sNodeHTML
    
            sHTML += "</div>"
    else: #end section
        sHTML += DrawReadOnlyField(xeNode, sXPath, oStep)
    
    #ok, now that we've drawn it, it might be intended to go on the "options tab".
    #if so, stick it there
    if sOptionTab:
        return "", sHTML
    else:
        return sHTML, ""
        
def DrawField(xe, sXPath, oStep):
    sHTML = ""
    sNodeValue = (xe.text if xe.text else "")
    UI.log("---- Value :" + sNodeValue, 4)
    
    sNodeLabel = xe.get("label", xe.tag)
    sLabelClasses = xe.get("label_class", "")
    sLabelStyle = xe.get("label_style", "")
    sNodeLabel = "<span class=\"" + sLabelClasses + "\" style=\"" + sLabelStyle + "\">" + sNodeLabel + ": </span>"

    sBreakBefore = xe.get("break_before", "")
    sBreakAfter = xe.get("break_after", "")
    sHRBefore = xe.get("hr_before", "")
    sHRAfter = xe.get("hr_after", "")
    sHelp = xe.get("help", "")
    sCSSClasses = xe.get("class", "")
    sStyle = xe.get("style", "")
    sInputType = xe.get("input_type", "")
    sRequired = xe.get("required", "")
    bRequired = catocommon.is_true(sRequired)
    
    # CommonAttribs takes an options dictionary
    opts = {}
    sConstraint = xe.get("constraint", "")
    if sConstraint:
        opts["constraint"] = sConstraint
    sConstraintMsg = xe.get("constraint_msg", "")
    if sConstraintMsg:
        opts["constraint_msg"] = sConstraintMsg
    sMinLength = xe.get("minlength", "")
    if sMinLength:
        opts["minlength"] = sMinLength
    sMaxLength = xe.get("maxlength", "")
    if sMaxLength:
        opts["maxlength"] = sMaxLength
    sMinValue = xe.get("minvalue", "")
    if sMinValue:
        opts["minvalue"] = sMinValue
    sMaxValue = xe.get("maxvalue", "")
    if sMaxValue:
        opts["maxvalue"] = sMaxValue
        
    if len(opts) > 0:
        UI.log("---- Options :", 4)
        UI.log(opts, 4)
        

    UI.log("---- Input Type :" + sInputType, 4)
    UI.log("---- Break Before/After : %s/%s" % (sBreakBefore, sBreakAfter), 4)
    UI.log("---- HR Before/After : %s/%s" % (sHRBefore, sHRAfter), 4)
    UI.log("---- Required : %s" % (str(bRequired)), 4)


    #some getting started layout possibilities
    if sBreakBefore == catocommon.is_true(sBreakBefore):
        sHTML += "<br />"
    if sHRBefore == catocommon.is_true(sHRBefore):
        sHTML += "<hr />"
    if sInputType == "textarea":
        #textareas have additional properties
        sRows = xe.get("rows", "2")
        sTextareaID = catocommon.new_guid()
        sHTML += sNodeLabel + " <textarea rows=\"" + sRows + "\"" + \
            CommonAttribsWithID(oStep, bRequired, sXPath, sTextareaID, sCSSClasses, opts) + \
            " style=\"" + sStyle + "\"" \
            " help=\"" + sHelp + "\"" \
            ">" + sNodeValue + "</textarea>"
        #big box button
        sHTML += "<span class=\"ui-icon ui-icon-pencil forceinline big_box_btn pointer\" link_to=\"" + sTextareaID + "\"></span><br />"
    elif sInputType == "dropdown":
        # the data source of a drop down can be a) an xml file, b) an internal function or web method or c) an "local" inline list
        # there is no "default" datasource... if nothing is available, it draws an empty picker
        sDatasource = xe.get("datasource", "")
        sDataSet = xe.get("dataset", "")

        sHTML += sNodeLabel + " <select " + CommonAttribs(oStep, False, sXPath, sCSSClasses) + ">\n"
        
        # empty one
        sHTML += "<option " + SetOption("", sNodeValue) + " value=\"\"></option>\n"
        
        # if it's a combo, it's possible we may have a value that isn't actually in the list.
        # but we will need to add it to the list otherwise we can't select it!
        # so, first let's keep track of if we find the value anywhere in the various datasets.
        bValueWasInData = False
        
        if sDatasource == "":
            UI.log("---- 'datasource' attribute not found, defaulting to 'local'.", 4)
        if sDatasource == "file":
            UI.log("---- File datasource ... reading [" + sDataSet + "] ...", 4)
            try:
                # sDataset is a file name.
                # sFormat is the type of data
                # sTable is the parent node in the XML containing the data
                sFormat = xe.get("format", "")

                if sFormat == "":
                    UI.log("---- 'format' attribute not found, defaulting to 'flat'.", 4)
            
                if sFormat.lower() == "xml":
                    sTable = xe.get("table", "")
                    sValueNode = xe.get("valuenode", "")
                    
                    if sTable == "":
                        UI.log("---- 'table' attribute not found, defaulting to 'values'.", 4)
                    if sValueNode == "":
                        UI.log("---- 'valuenode' attribute not found, defaulting to 'value'.", 4)
                    
                    xml = ET.parse("extensions/" + sDataSet)
                    if xml:
                        nodes = xml.findall(".//" + sValueNode)
                        if len(nodes) > 0:
                            UI.log("---- Found data ... parsing ...", 4)
                            for node in nodes:
                                sHTML += "<option " + SetOption(node.text, sNodeValue) + " value=\"" + node.text + "\">" + node.text + "</option>\n"
                                if node.text == sNodeValue: bValueWasInData = True
                        else:
                            UI.log("---- Dataset found but cannot find values in [" + sValueNode + "].", 4)
                    else:
                        UI.log("---- Dataset file not found or unable to read.", 4)
                    
                else:
                    UI.log("---- opening [" + sDataSet + "].", 4)
                    f = open("%s/extensions/%s" % (uiGlobals.web_root, sDataSet), 'rb')
                    if not f:
                        UI.log("ERROR: extensions/" + sDataSet + " not found", 0)

                    for line in f:
                        val = line.strip()
                        sHTML += "<option " + SetOption(val, sNodeValue) + " value=\"" + val + "\">" + val + "</option>\n"
                        if val == sNodeValue: bValueWasInData = True
                        
                    f.close()
            except Exception:
                UI.log_nouser(traceback.format_exc(), 0)
                return "Unable to render input element [" + sXPath + "]. Lookup file [" + sDataSet + "] not found or incorrect format."
        elif sDatasource == "function":
            UI.log("---- Function datasource ... executing [" + sDataSet + "] ...", 4)
            # this executes a function to populate the drop down
            # at this time, the function must exist in this namespace
            # we expect the function to return a dictionary
            try:
                if sDataSet:
                    data = globals()[sDataSet]()
                    if data:
                        for key, val in data.iteritems():
                            sHTML += "<option " + SetOption(key, sNodeValue) + " value=\"" + key + "\">" + val + "</option>\n"
                            if key == sNodeValue: bValueWasInData = True
            except Exception:
                UI.log_nouser(traceback.format_exc(), 0)
        else: # default is "local"
            UI.log("---- Inline datasource ... reading my own 'dataset' attribute ...", 4)
            # data is pipe delimited
            aValues = sDataSet.split('|')
            for sVal in aValues:
                sHTML += "<option " + SetOption(sVal, sNodeValue) + " value=\"" + sVal + "\">" + sVal + "</option>\n"

                if sVal == sNodeValue: bValueWasInData = True
        
        # NOTE: If it has the "combo" style and a value, that means we're allowing the user to enter a value that may not be 
        # in the dataset.  If that's the case, we must add the actual saved value to the list too. 
        if not bValueWasInData: # we didn't find it in the data ..
            if "combo" in sCSSClasses and sNodeValue:   # and it's a combo and not empty
                sHTML += "<option " + SetOption(sNodeValue, sNodeValue) + " value=\"" + sNodeValue + "\">" + sNodeValue + "</option>\n";            

        sHTML += "</select>"
    elif sInputType == "checkbox":
        sElementID = catocommon.new_guid() #some special cases below may need this.
        sHTML += "<label for=\"" + sElementID + "\">" + sNodeLabel + "</label> <input type=\"checkbox\" " + \
            CommonAttribsWithID(oStep, bRequired, sXPath, sElementID, sCSSClasses) + \
            " style=\"" + sStyle + "\"" \
            " help=\"" + sHelp + "\"" \
            " value=\"" + sNodeValue + "\" />"
        
    else: #input is the default
        sElementID = catocommon.new_guid() #some special cases below may need this.
        sHTML += sNodeLabel + " <input type=\"text\" " + \
            CommonAttribsWithID(oStep, bRequired, sXPath, sElementID, sCSSClasses, opts) + \
            " style=\"" + sStyle + "\"" \
            " help=\"" + sHelp + "\"" \
            " value=\"" + sNodeValue + "\" />"
        #might this be a conn_name field?  If so, we can show the picker.
        sConnPicker = xe.get("connection_picker", "")
        if catocommon.is_true(sConnPicker):
            sHTML += "<span class=\"ui-icon ui-icon-search forceinline conn_picker_btn pointer\" link_to=\"" + sElementID + "\"></span>"

    #some final layout possibilities
    if catocommon.is_true(sBreakAfter):
        sHTML += "<br />"
    if catocommon.is_true(sHRAfter):
        sHTML += "<hr />"

    UI.log("---- ... done", 4)
    return sHTML

def DrawReadOnlyField(xe, sXPath, oStep):
    sHTML = ""
    sNodeValue = (xe.text if xe.text else "")
    UI.log("---- Value :" + sNodeValue, 4)
    
    sInputType = xe.get("input_type", "")
    sNodeLabel = xe.get("label", xe.tag)
    sLabelClasses = xe.get("label_class", "")
    sLabelStyle = xe.get("label_style", "")
    sNodeLabel = "<span class=\"" + sLabelClasses + "\" style=\"" + sLabelStyle + "\">" + sNodeLabel + ": </span>"

    sBreakBefore = xe.get("break_before", "")
    sBreakAfter = xe.get("break_after", "")
    sHRBefore = xe.get("hr_before", "")
    sHRAfter = xe.get("hr_after", "")

    UI.log("---- Break Before/After : %s/%s" % (sBreakBefore, sBreakAfter), 4)
    UI.log("---- HR Before/After : %s/%s" % (sHRBefore, sHRAfter), 4)


    #some getting started layout possibilities
    if sBreakBefore == catocommon.is_true(sBreakBefore):
        sHTML += "<br />"
    if sHRBefore == catocommon.is_true(sHRBefore):
        sHTML += "<hr />"

    # HERE IT IS!
    if sInputType == "textarea":
        sHTML += sNodeLabel + "<div class=\"codebox\" style=\"padding-right: 8px;\"> " + UI.SafeHTML(sNodeValue) + "</div>"
    else:
        sHTML += sNodeLabel + "<span class=\"code\" style=\"padding-right: 8px;\"> " + UI.SafeHTML(sNodeValue) + "</span>"

    #some final layout possibilities
    if catocommon.is_true(sBreakAfter):
        sHTML += "<br />"
    if catocommon.is_true(sHRAfter):
        sHTML += "<hr />"

    UI.log("---- ... done", 4)
    return sHTML

def DrawStepOptions_View(sOptionHTML):
    # this is the section that is common to all steps.
    sHTML = ""

    sHTML += "<hr />"
    sHTML += "Options:<br />"
    sHTML += "<div class=\"codebox\">" + sOptionHTML + "</div>"

    return sHTML

def CommonAttribsWithID(oStep, bRequired, sXPath, sElementID, sAdditionalClasses, opts=None):
    # if it's embedded it will have a prefix
    sXPath = (oStep.XPathPrefix + "/" if oStep.XPathPrefix else "") + sXPath
    
    sOpts = ""
    if opts:
        for k, v in opts.iteritems():
            sOpts += " %s=\"%s\"" % (k, v)

    # requires a guid ID passed in - this one will be referenced client side
    return " id=\"" + sElementID + "\"" \
        " step_id=\"" + oStep.ID + "\"" \
        " function=\"" + oStep.FunctionName + "\"" \
        " xpath=\"" + sXPath + "\"" \
        " te_group=\"step_fields\"" \
        " class=\"step_input code " + sAdditionalClasses + "\"" + \
        (" is_required=\"true\"" if bRequired else "") + \
        sOpts + \
        " onchange=\"javascript:onStepFieldChange(this, '" + oStep.ID + "', '" + sXPath + "');\""

def CommonAttribs(oStep, bRequired, sXPath, sAdditionalClasses, opts=None):
    # if it's embedded it will have a prefix
    sXPath = (oStep.XPathPrefix + "/" if oStep.XPathPrefix else "") + sXPath
    
    sOpts = ""
    if opts:
        for k, v in opts:
            sOpts += " %s=\"%s\"" % (k, v)

    # creates a new id
    return " id=\"x" + catocommon.new_guid() + "\"" \
        " step_id=\"" + oStep.ID + "\"" \
        " function=\"" + oStep.FunctionName + "\"" \
        " xpath=\"" + sXPath + "\"" \
        " te_group=\"step_fields\"" \
        " class=\"step_input code " + sAdditionalClasses + "\"" + \
        (" is_required=\"true\"" if bRequired else "") + \
        sOpts + \
        " onchange=\"javascript:onStepFieldChange(this, '" + oStep.ID + "', '" + sXPath + "');\""

def DrawEmbeddedStep(oStep):
    UI.log("** Embedded Step: [%s] prefix [%s]" % (oStep.FunctionName, oStep.XPathPrefix), 4)
    # JUST KNOW!
    # this isn't a "real" step ... meaning it isn't in the task_step table as an individual row
    # it's a step object we manually created.
    # so, some properties will have no values.
    sStepID = oStep.ID
    fn = oStep.Function
    
    # we need the full function, not just the inner part that's on the parent step xml.
    if fn is None:
        # the function doesn't exist (was probably deprecated)
        # we need at least a basic strip with a delete button
        sNoFunc = "<div class=\"embedded_step\">"
        sNoFunc += "    <div class=\"ui-state-default ui-state-highlight step_header\">"
        sNoFunc += "        <div class=\"step_header_title\"><img src=\"static/images/icons/status_unknown_16.png\" /></div>"
        sNoFunc += "        <div class=\"step_header_icons\">"
        sNoFunc += "            <span class=\"ui-icon ui-icon-close forceinline embedded_step_delete_btn\" remove_xpath=\"" + oStep.XPathPrefix + "\" parent_id=\"" + sStepID + "\"></span>"
        sNoFunc += "        </div>"
        sNoFunc += "    </div>"
        sNoFunc += "    <div class=\"ui-widget-content ui-state-highlight ui-corner-bottom step_detail\" >"
        sNoFunc += "Error building Step - Unable to get the details for the command type '" + oStep.FunctionName + "'.<br />"
        sNoFunc += "This command type may have been deprecated - check the latest Cato release notes.<br />"
        sNoFunc += "    </div>"
        sNoFunc += "</div>"

        return sNoFunc
    
    # invalid for embedded
    # sExpandedClass = ("step_collapsed" if oStep.UserSettings.Visible else "")

    sMainHTML = ""

    # labels are different here than in Full Steps.
    sIcon = ("" if not fn.Icon else fn.Icon)
    sLabel = "<img class=\"step_header_function_icon\" src=\"" + sIcon + "\" alt=\"\" /> " + \
        fn.Category.Label + " - " + fn.Label

    # invalid for embedded
    # sSnip = UI.GetSnip(oStep.Description, 75)
    # sLabel += ("" if not oStep.Description) else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[" + sSnip + "]")

    # sLockClause = (" onclick=\"return false;\"" if !oStep.Locked else "")


    #  step expand image
    #sExpandImage = "expand_down.png"
    #if sExpandedClass == "step_collapsed":
    #    sExpandImage = "expand_up.png"

    sMainHTML += "<div class=\"embedded_step\">"
    sMainHTML += "    <div class=\"ui-state-default step_header\">"
    sMainHTML += "        <div class=\"step_header_title\">"
#    sMainHTML += "            <span class=\"step_toggle_btn\"" \
#        " step_id=\"" + sStepID + "\">" \
#        " <img class=\"expand_image\" src=\"static/images/icons/" + sExpandImage + "\" alt=\"\" title=\"Hide/Show Step\" /></span>"
    sMainHTML += "            <span>" + sLabel + "</span>"
    sMainHTML += "        </div>"
    sMainHTML += "        <div class=\"step_header_icons\">"

    # this button will copy a step into the clipboard.
#    sMainHTML += "            <span><img id=\"step_copy_btn_" + sStepID + "\"" \
#        " class=\"step_copy_btn\" step_id=\"" + sStepID + "\"" \
#        " src=\"static/images/icons/editcopy_16.png\" alt=\"\" title=\"Copy this Step to your Clipboard\"/></span>"

    # for deleting, the codeblock_name is the step_id of the parent step.
    sMainHTML += "            <span class=\"ui-icon ui-icon-close forceinline embedded_step_delete_btn\"" \
        " remove_xpath=\"" + oStep.XPathPrefix + "\" parent_id=\"" + sStepID + "\"></span>"
    sMainHTML += "        </div>"
    sMainHTML += "     </div>"
    sMainHTML += "     <div class=\"ui-widget-content ui-corner-bottom step_detail\" >"

    #!!! this returns a tuple with optional "options" and "variable" html
    sStepHTML, sOptionHTML, sVariableHTML = GetStepTemplate(oStep)
    sMainHTML += sStepHTML
    
    #comment steps don't have a common section - all others do
    if oStep.FunctionName != "comment":
        sMainHTML += DrawStepCommon(oStep, sOptionHTML, sVariableHTML, True)

    sMainHTML += "    </div>"
    sMainHTML += "</div>"

    return sMainHTML

def DrawEmbeddedReadOnlyStep(xEmbeddedFunction):
    if xEmbeddedFunction is not None:
        sFunctionName = xEmbeddedFunction.get("name", "")

        fn = UI.GetTaskFunction(sFunctionName)

        # !!!!! This isn't a new step! ... It's an extension of the parent step.
        # but, since it's a different 'function', we'll treat it like a different step for now
        oEmbeddedStep = task.Step() # a new step object
        oEmbeddedStep.Function = fn # a function object
        oEmbeddedStep.FunctionName = sFunctionName
        oEmbeddedStep.FunctionXDoc = xEmbeddedFunction

        # we need the full function, not just the inner part that's on the parent step xml.
        if fn is None:
            # the function doesn't exist (was probably deprecated)
            # we need at least a basic strip with a delete button
            sNoFunc = "<div class=\"embedded_step\">"
            sNoFunc += "    <div class=\"ui-state-default ui-state-highlight step_header\">"
            sNoFunc += "        <div class=\"step_header_title\"><img src=\"static/images/icons/status_unknown_16.png\" /></div>"
            sNoFunc += "    </div>"
            sNoFunc += "    <div class=\"ui-widget-content ui-state-highlight ui-corner-bottom step_detail\" >"
            sNoFunc += "Error building Step - Unable to get the details for the command type '" + sFunctionName + "'.<br />"
            sNoFunc += "This command type may have been deprecated - check the latest Cato release notes.<br />"
            sNoFunc += "    </div>"
            sNoFunc += "</div>"
    
            return sNoFunc
        
        sMainHTML = ""
    
        # labels are different here than in Full Steps.
#        sIcon = ("" if not fn.Icon else fn.Icon)
#        sLabel = "<img class=\"step_header_function_icon\" src=\"" + sIcon + "\" alt=\"\" /> " + \
#            fn.Category.Label + " - " + fn.Label
        sLabel = fn.Category.Label + " - " + fn.Label
    
        sMainHTML += "<div class=\"embedded_step\">"
        sMainHTML += "    <div class=\"ui-state-default step_header\">"
        sMainHTML += "        <div class=\"step_header_title\">"
        sMainHTML += "            <span>" + sLabel + "</span>"
        sMainHTML += "        </div>"
        sMainHTML += "    </div>"
        sMainHTML += "     <div class=\"ui-widget-content ui-corner-bottom step_detail\" >"
    
        #!!! this returns a tuple with optional "options" and "variable" html
        sStepHTML, sOptionHTML = GetStepTemplate_View(oEmbeddedStep)
        sMainHTML += sStepHTML
        
        if sOptionHTML != "":
            sMainHTML += DrawStepOptions_View(sOptionHTML)

        sMainHTML += "</div>"
    
        return sMainHTML

def DrawStepCommon(oStep, sOptionHTML, sVariableHTML, bIsEmbedded = False):
    sStepID = oStep.ID

    # a certain combination of tests means we have nothing to draw at all
    if bIsEmbedded and not sOptionHTML and not sVariableHTML:
        return ""
    
    #this is the section that is common to all steps.
    sHTML = ""
    sHTML += "        <hr />"
    sHTML += "        <div class=\"step_common\" >"
    sHTML += "            <div class=\"step_common_header\">" # header div
    
    sShowOnLoad = oStep.UserSettings.Button
    
    #pill buttons
    if sVariableHTML != "":
        sHTML += "                <span class=\"step_common_button " + ("step_common_button_active" if sShowOnLoad == "variables" else "") + "\"" \
            " id=\"btn_step_common_detail_" + sStepID + "_variables\"" \
            " button=\"variables\"" \
            " step_id=\"" + sStepID + "\">Variables</span>"
    if sOptionHTML != "":
        sHTML += "                <span class=\"step_common_button " + ("step_common_button_active" if sShowOnLoad == "options" else "") + "\"" \
            " id=\"btn_step_common_detail_" + sStepID + "_options\"" \
            " button=\"options\"" + " step_id=\"" + sStepID + "\">Options</span>"

    # embedded commands don't have a notes button (it's the description of the command, which doesn't apply)
    if not bIsEmbedded:
        sHTML += "                <span class=\"step_common_button " + ("step_common_button_active" if sShowOnLoad == "notes" else "") + "\"" \
            " id=\"btn_step_common_detail_" + sStepID + "_notes\"" \
            " button=\"notes\"" + " step_id=\"" + sStepID + "\">Notes</span>"

        # not showing help either... too cluttered
        sHTML += "                <span class=\"step_common_button " + ("step_common_button_active" if sShowOnLoad == "help" else "") + "\"" \
            " id=\"btn_step_common_detail_" + sStepID + "_help\"" \
            " button=\"help\"" \
            " step_id=\"" + sStepID + "\">Help</span>"
    
    
    sHTML += "            </div>" # end header div
    
    #sections
    # embedded commands don't have notes (it's the description of the command, which doesn't apply)
    if not bIsEmbedded:
        sHTML += "            <div id=\"step_common_detail_" + sStepID + "_notes\"" \
            " class=\"step_common_detail " + ("" if sShowOnLoad == "notes" else "step_common_collapsed") + "\">"
            
        sHTML += "                <textarea rows=\"4\" " + CommonAttribs(oStep, False, "step_desc", "") + \
            " help=\"Enter notes for this Command.\" reget_on_change=\"true\">" + oStep.Description + "</textarea>"
        sHTML += "            </div>"

        # embedded commands *could* show the help, but I don't like the look of it.
        # it's cluttered
        sHTML += "            <div id=\"step_common_detail_" + sStepID + "_help\"" \
            " class=\"ui-widget-content step_common_detail " + ("" if sShowOnLoad == "help" else "step_common_collapsed") + "\">"
        sHTML += oStep.Function.Help
        sHTML += "            </div>"
    
    #some steps generate custom options we want in this pane
    #but we don't show the panel if there aren't any
    if sOptionHTML != "":
        sHTML += "          <div id=\"step_common_detail_" + sStepID + "_options\"" \
            " class=\"step_common_detail " + ("" if sShowOnLoad == "options" else "step_common_collapsed") + "\">"
        sHTML += "              <div>"
        sHTML += sOptionHTML
        sHTML += "              </div>"
        sHTML += "          </div>"
    
    #some steps have variables
    #but we don't show the panel if there aren't any
    if sVariableHTML != "":
        sHTML += "          <div id=\"step_common_detail_" + sStepID + "_variables\"" \
            " class=\"step_common_detail " + ("" if sShowOnLoad == "variables" else "step_common_collapsed") + "\">"
        sHTML += "              <div>"
        sHTML += sVariableHTML
        sHTML += "              </div>"
        sHTML += "          </div>"
    #close it out
    sHTML += "        </div>"
    
    return sHTML

def SetOption(s1, s2):
    return " selected=\"selected\"" if s1 == s2 else ""

def SetCheckRadio(s1, s2):
    return " checked=\"checked\"" if s1 == s2 else ""

# NOTE: the following functions are internal, but support dynamic dropdowns on step functions.
# the function name is referenced by the "dataset" value of a dropdown type of input, where the datasource="function"
# dropdowns expect a Dictionary<string,string> object return

def ddDataSource_GetDebugLevels():
    return {"10": "Debug", "20": "Info", "30": "Warning", "40": "Error", "50": "Critical", }

def ddDataSource_GetAWSClouds():
    data = {}
    
    # AWS regions
    p = cloud.Provider.FromName("Amazon AWS")
    if p is not None:
        for c in p.Clouds:
            data[c.Name] = c.Name
    # Eucalyptus clouds
    p = cloud.Provider.FromName("Eucalyptus")
    if p is not None:
        for c in p.Clouds:
            data[c.Name] = c.Name

    return data

def AddToCommandXML(sStepID, sXPath, sXMLToAdd):
    try:
        if not catocommon.is_guid(sStepID):
            UI.log("Unable to modify step. Invalid or missing Step ID. [" + sStepID + "].")

        UI.AddNodeToXMLColumn("task_step", "function_xml", "step_id = '" + sStepID + "'", sXPath, sXMLToAdd)

        return
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)

def SetNodeValueinCommandXML(sStepID, sNodeToSet, sValue):
    try:
        if not catocommon.is_guid(sStepID):
            UI.log("Unable to modify step. Invalid or missing Step ID. [" + sStepID + "] ")

        UI.SetNodeValueinXMLColumn("task_step", "function_xml", "step_id = '" + sStepID + "'", sNodeToSet, sValue)

        return
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)

def SetNodeAttributeinCommandXML(sStepID, sNodeToSet, sAttribute, sValue):
    try:
        if not catocommon.is_guid(sStepID):
            UI.log("Unable to modify step. Invalid or missing Step ID. [" + sStepID + "] ")

        UI.SetNodeAttributeinXMLColumn("task_step", "function_xml", "step_id = '" + sStepID + "'", sNodeToSet, sAttribute, sValue)

        return
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)

def RemoveFromCommandXML(sStepID, sNodeToRemove):
    try:
        if not catocommon.is_guid(sStepID):
            UI.log("Unable to modify step.<br />Invalid or missing Step ID. [" + sStepID + "]<br />")
        
        UI.RemoveNodeFromXMLColumn("task_step", "function_xml", "step_id = '" + sStepID + "'", sNodeToRemove)

        return
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)

def DrawDropZone(oStep, xEmbeddedFunction, sXPath, sLabel, bRequired):
    # drop zones are common for all the steps that can contain embedded steps.
    # they are a div to drop on and a hidden field to hold the embedded step id.
    sHTML = ""
    sHTML += sLabel

    # an embedded step may actually be the child of another embedded step, so
    # check for an xpath prefix
    sXPath = (oStep.XPathPrefix + "/" if oStep.XPathPrefix else "") + sXPath
    
    # manually create a step object, which will basically only have the function_xml.
    if xEmbeddedFunction is not None:
        sFunctionName = xEmbeddedFunction.get("name", "")

        fn = UI.GetTaskFunction(sFunctionName)

        # !!!!! This isn't a new step! ... It's an extension of the parent step.
        # but, since it's a different 'function', we'll treat it like a different step for now
        oEmbeddedStep = task.Step() # a new step object
        oEmbeddedStep.ID = oStep.ID 
        oEmbeddedStep.Function = fn # a function object
        oEmbeddedStep.FunctionName = sFunctionName
        oEmbeddedStep.FunctionXDoc = xEmbeddedFunction
        oEmbeddedStep.Task = oStep.Task
        # THIS IS CRITICAL - this embedded step ... all fields in it will need an xpath prefix 
        oEmbeddedStep.XPathPrefix = sXPath + "/function"
        
        sHTML += DrawEmbeddedStep(oEmbeddedStep)
    else:
        # some of our 'columns' may be complex XPaths.  XPaths have invalid characters for use in 
        # an HTML ID attribute
        # but we need it to be unique... so just 'clean up' the column name
        sXPathBasedID = sXPath.replace("[", "").replace("]", "").replace("/", "")
    
        # the dropzone
        sHTML += "<div" + \
            (" is_required=\"true\" value=\"\"" if bRequired else "") + \
            " id=\"" + oStep.FunctionName + "_" + oStep.ID + "_" + sXPathBasedID + "_dropzone\"" \
            " xpath=\"" + sXPath + "\"" \
            " step_id=\"" + oStep.ID + "\"" \
            " class=\"step_nested_drop_target " + ("is_required" if bRequired else "") + "\">Click here to add a Command.</div>"
    #        " datafield_id=\"" + sElementID + "\"" \
       
    return sHTML

def DrawKeyValueSection(oStep, bShowPicker, bShowMaskOption, sKeyLabel, sValueLabel):
    # the base xpath of this command (will be '' unless this is embedded)
    # NOTE: do not append the base_path on any CommonAttribs calls, it's done inside that function.
    base_xpath = (oStep.XPathPrefix + "/" if oStep.XPathPrefix else "")  

    sStepID = oStep.ID
    sFunction = oStep.FunctionName
    xd = oStep.FunctionXDoc

    sElementID = catocommon.new_guid()
    sValueFieldID = catocommon.new_guid()
    sHTML = ""

    sHTML += "<div id=\"" + sStepID + "_pairs\">"


    xPairs = xd.findall("pairs/pair")
    i = 1
    for xe in xPairs:
        sKey = xe.findtext("key")
        sVal = xe.findtext("value", "")
        sMask = xe.findtext("mask", "")

        sHTML += "<table border=\"0\" class=\"w99pct\" cellpadding=\"0\" cellspacing=\"0\"><tr>\n"
        sHTML += "<td class=\"w1pct\">&nbsp;" + sKeyLabel + ":&nbsp;</td>\n"

        sHTML += "<td class=\"w1pct\"><input type=\"text\" " + CommonAttribsWithID(oStep, True, "pairs/pair[" + str(i) + "]/key", sElementID, "") + \
            " validate_as=\"variable\"" \
            " value=\"" + UI.SafeHTML(sKey) + "\"" \
            " help=\"Enter a name.\"" \
            " /></td>"

        if bShowPicker:
            sHTML += "<td class=\"w1pct\"><span class=\"ui-icon ui-icon-search forceinline key_picker_btn pointer\"" \
                " function=\"" + sFunction + "\"" \
                " target_field_id=\"" + sElementID + "\"" \
                " link_to=\"" + sElementID + "\"></span>\n"

            sHTML += "</td>\n"

        sHTML += "<td class=\"w1pct\">&nbsp;" + sValueLabel + ":&nbsp;</td>"

        #  we gotta get the field id first, but don't show the textarea until after
        sCommonAttribs = CommonAttribsWithID(oStep, True, "pairs/pair[" + str(i) + "]/value", sValueFieldID, "w90pct")

        sHTML += "<td class=\"w50pct\"><input type=\"text\" " + sCommonAttribs + \
            " value=\"" + UI.SafeHTML(sVal) + "\"" \
            " help=\"Enter a value.\"" \
            " />\n"

        # big box button
        sHTML += "<span class=\"ui-icon ui-icon-pencil forceinline big_box_btn pointer\" link_to=\"" + sValueFieldID + "\"></span></td>\n"

        # optional mask option
        if bShowMaskOption:
            sHTML += "<td>"

            sHTML += "&nbsp;Mask?: <input type=\"checkbox\" " + \
                CommonAttribs(oStep, True, "pairs/pair[" + str(i) + "]/mask", "") + " " + SetCheckRadio("1", sMask) + " />\n"


            sHTML += "</td>\n"

        sHTML += "<td class=\"w1pct\" align=\"right\">"
        # can't delete the first one
        if i > 1:
            sHTML += "<span class=\"ui-icon ui-icon-close forceinline fn_node_remove_btn pointer\" remove_path=\"" + base_xpath + "pairs/pair[" + str(i) + "]\" step_id=\"" + sStepID + "\"></span>"
        sHTML += "</td>"

        sHTML += "</tr></table>\n"

        i += 1

    sHTML += "<div class=\"fn_node_add_btn pointer\"" \
        " function_name=\"" + oStep.FunctionName + "\"" \
        " template_path=\"pairs\"" \
        " add_to_node=\"" + base_xpath + "pairs\"" \
        " step_id=\"" + sStepID + "\">" \
        "<span class=\"ui-icon ui-icon-plus forceinline\" title=\"Add another.\"></span>( click to add another )</div>"
    sHTML += "</div>"

    return sHTML

def DrawReadOnlyKeyValueSection(oStep, bShowPicker, bShowMaskOption, sKeyLabel, sValueLabel):
    sStepID = oStep.ID
    xd = oStep.FunctionXDoc

    sHTML = ""

    sHTML += "<div id=\"" + sStepID + "_pairs\">"

    xPairs = xd.findall("pairs/pair")
    i = 1
    for xe in xPairs:
        sKey = xe.findtext("key")
        sVal = xe.findtext("value", "")

        sHTML += "<table border=\"0\" class=\"w99pct\" cellpadding=\"0\" cellspacing=\"0\"><tr>"
        sHTML += "<td class=\"w1pct\">&nbsp;" + sKeyLabel + ":&nbsp;</td>"
        sHTML += "<td class=\"w1pct\"><span class=\"code\">" + UI.SafeHTML(sKey) + "</span></td>"
        sHTML += "<td class=\"w1pct\">&nbsp;" + sValueLabel + ":&nbsp;</td>"
        sHTML += "<td class=\"w75pct\"><span class=\"code\">" + UI.SafeHTML(sVal) + "</span></td>"
        sHTML += "</tr></table>"

        i += 1

    sHTML += "</div>"

    return sHTML

def RemoveStepVars(sStepID):
    RemoveFromCommandXML(sStepID, "variables")

def DrawVariableSectionForDisplay(oStep, bShowEditLink):
    sStepID = oStep.ID

    # we go check if there are vars first, so that way we don't waste space displaying nothing
    # if there are none
    # BUT only hide this empty section on the 'view' page.
    # if it's an edit page, we still show the empty table!

    sVariableHTML = GetVariablesForStepForDisplay(oStep)

    if not bShowEditLink and not sVariableHTML:
        return ""

    iParseType = oStep.OutputParseType
    iRowDelimiter = oStep.OutputRowDelimiter
    iColumnDelimiter = oStep.OutputColumnDelimiter
    UI.log("Parse Type [%d], Row Delimiter [%d], Col Delimiter [%d]" % (iParseType, iRowDelimiter, iColumnDelimiter), 4)

    sHTML = ""
    if bShowEditLink:
        sHTML += "<span class=\"variable_popup_btn\" step_id=\"" + sStepID + "\">" \
            "<img src=\"static/images/icons/kedit_16.png\"" \
            " title=\"Manage Variables\" alt=\"\" /> Manage Variables</span>"

    # some types may only have one of the delimiters
    bRowDelimiterVisibility = (True if iParseType == 2 else False)
    bColDelimiterVisibility = (True if iParseType == 2 else False)

    if bRowDelimiterVisibility:
        sHTML += "<br />Row Break Indicator: " \
            " <span class=\"code 100px\">" + LabelNonprintable(iRowDelimiter) + "</span>"

    if bColDelimiterVisibility:
        sHTML += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Field Break Indicator: " \
            " <span class=\"code 100px\">" + LabelNonprintable(iColumnDelimiter) + "</span>"

    sHTML += sVariableHTML

    return sHTML

def GetVariablesForStepForDisplay(oStep):
    sStepID = oStep.ID
    xDoc = oStep.FunctionXDoc

    sHTML = ""
    if xDoc is not None:
        # UI.log("Command Variable XML:\n%s" % ET.tostring(xDoc), 4)
        xVars = xDoc.findall("step_variables/variable")
        if xVars is None:
            return "Variable XML data for step [" + sStepID + "] does not contain any 'variable' elements."
        
        if len(xVars) > 0:
            UI.log("-- Rendering [%d] variables ..." % len(xVars), 4)
            # build the HTML
            sHTML += "<table class=\"step_variables\" width=\"99%\" border=\"0\">\n"
            sHTML += "<tbody>"
            
            # loop
            for xVar in xVars:
                sName = UI.SafeHTML(xVar.findtext("name", ""))
                sType = xVar.findtext("type", "").lower()
                
                UI.log("---- Variable [%s] is type [%s]" % (sName, sType), 4)
                
                sHTML += "<tr>"
                sHTML += "<td class=\"row\"><span class=\"code\">" + sName + "</span></td>"
                
                if sType == "range":
                    sLProp = ""
                    sRProp = ""
                    # the markers can be a range indicator or a string.
                    if xVar.find("range_begin") is not None:
                        sLProp = " Position [" + xVar.findtext("range_begin", "") + "]"
                    elif xVar.find("prefix") is not None:
                        sLProp = " Prefix [" + xVar.findtext("prefix", "") + "]"
                    else:
                        return "Variable XML data for step [" + sStepID + "] does not contain a valid begin marker."

                    if xVar.find("range_end") is not None:
                        sRProp = " Position [" + xVar.findtext("range_end", "") + "]"
                    elif xVar.find("suffix") is not None:
                        sRProp = " Suffix [" + xVar.findtext("suffix", "") + "]"
                    else:
                        return "Variable XML data for step [" + sStepID + "] does not contain a valid end marker."

                    sHTML += "<td class=\"row\">Characters in Range:</td><td class=\"row\"><span class=\"code\">" + UI.SafeHTML(sLProp) + " - " + UI.SafeHTML(sRProp) + "</span></td>"
                elif sType == "delimited":
                    sHTML += "<td class=\"row\">Value at Index Position:</td><td class=\"row\"><span class=\"code\">" + UI.SafeHTML(xVar.findtext("position", "")) + "</span></td>"
                elif sType == "regex":
                    sHTML += "<td class=\"row\">Regular Expression:</td><td class=\"row\"><span class=\"code\">" + UI.SafeHTML(xVar.findtext("regex", "")) + "</span></td>"
                elif sType == "xpath":
                    sHTML += "<td class=\"row\">Xpath:</td><td class=\"row\"><span class=\"code\">" + UI.SafeHTML(xVar.findtext("xpath", "")) + "</span></td>"
                else:
                    sHTML += "INVALID TYPE"
                
                sHTML += "</tr>"
                 
            # close it out
            sHTML += "</tbody></table>\n"
        return sHTML
    else:
        # yes this is valid. "null" in the database may translate to having no xml.  That's ok.
        return ""

def DrawVariableSectionForEdit(oStep):
    sHTML = ""
    # sStepID = drStep["step_id"]
    # sFunction = drStep["function_name"]
    sParseType = oStep.OutputParseType
    iRowDelimiter = oStep.OutputRowDelimiter
    iColumnDelimiter = oStep.OutputColumnDelimiter

    # now, some sections or items may or may not be available.
    sDelimiterSectionVisiblity = ""
    # only 'parsed' types show delimiter pickers.  The hardcoded "delimited" (1) 
    # type does not allow changes to the delimiter.
    sRowDelimiterVisibility = ("" if sParseType == 2 else "hidden")
    sColDelimiterVisibility = ("" if sParseType == 2 else "hidden")

    # some code here will replace non-printable delimiters with a token string
    sRowDelimiterLabel = LabelNonprintable(iRowDelimiter)
    sColumnDelimiterLabel = LabelNonprintable(iColumnDelimiter)

    sHTML += "<div class=\"" + sDelimiterSectionVisiblity + "\" id=\"div_delimiters\">"
    sHTML += "<span id=\"row_delimiter\" class=\"" + sRowDelimiterVisibility + "\">"
    sHTML += "Row Break Indicator: " \
        " <span id=\"output_row_delimiter_label\"" \
        " class=\"delimiter_label code\">" + sRowDelimiterLabel + "</span>"
    sHTML += "<span class=\"ui-icon ui-icon-search forceinline pointer\" title=\"Select a Delimiter\" name=\"delimiter_picker_btn\" target=\"row\"></span>"
    sHTML += "<span class=\"ui-icon ui-icon-close forceinline pointer\" title=\"Clear this Delimiter\" name=\"delimiter_clear_btn\" target=\"row\"></span>"
    sHTML += "</span>"

    sHTML += "<span id=\"col_delimiter\" class=\"" + sColDelimiterVisibility + "\">"
    sHTML += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Field Break Indicator: " \
        " <span id=\"output_col_delimiter_label\"" \
        " class=\"delimiter_label code\">" + sColumnDelimiterLabel + "</span>"
    sHTML += "<span class=\"ui-icon ui-icon-search forceinline pointer\" title=\"Select a Delimiter\" name=\"delimiter_picker_btn\" target=\"col\"></span>"
    sHTML += "<span class=\"ui-icon ui-icon-close forceinline pointer\" title=\"Clear this Delimiter\" name=\"delimiter_clear_btn\" target=\"col\"></span>"
    sHTML += "</span>"
    sHTML += "</div>"

    sHTML += "</div>"
    # END DELIMITER SECTION


    sHTML += "<div id=\"div_variables\">"
    sHTML += "<div><span id=\"variable_add_btn\">" \
        "<img src=\"static/images/icons/bookmark_add_32.png\" width=\"16\" height=\"16\"" \
        " alt=\"Add Variable\" title=\"Add Variable\"/> Add a Variable</span><span id=\"variable_clearall_btn\">" \
        "<img src=\"static/images/icons/bookmark_delete_32.png\" width=\"16\" height=\"16\"" \
        " alt=\"Clear All Variables\" title=\"Clear All Variables\"/> Clear All Variables</span></div><hr />"
    sHTML += GetVariablesForStepForEdit(oStep)
    sHTML += "</div>"

    return sHTML

def GetVariablesForStepForEdit(oStep):
    sStepID = oStep.ID

    sHTML = ""
    
    # build the HTML
    sHTML += "<ul id=\"edit_variables\" class=\"variables\">"
    
    # if the xml is empty, we still need to return the UL so the gui will work.
    xDoc = oStep.FunctionXDoc
    if xDoc is None:
        return sHTML + "</ul>\n"

    # if the document is missing the root node, we still need to return the UL.
    xVars = xDoc.findall("step_variables/variable")
    if xVars is None:
        return sHTML + "</ul>\n"
    
    if len(xVars) > 0:
        # loop
        for xVar in xVars:
            sName = xVar.findtext("name", "")
            sType = xVar.findtext("type", "").lower()
            sVarStrip = sName
            sDetailStrip = ""
            sLProp = ""
            sRProp = ""
            sLIdxChecked = ""
            sRIdxChecked = ""
            sLPosChecked = ""
            sRPosChecked = ""
            sVarGUID = "v" + catocommon.new_guid()
            
            if sType == "range":
                # the markers can be a range indicator or a string.
                if xVar.findtext("range_begin") is not None:
                    sLProp = UI.SafeHTML(xVar.findtext("range_begin", ""))
                    sLIdxChecked = " checked=\"checked\""
                elif xVar.findtext("prefix") is not None:
                    sLProp = UI.SafeHTML(xVar.findtext("prefix", ""))
                    sLPosChecked = " checked=\"checked\""
                else:
                    return "Variable XML data for step [" + sStepID + "] does not contain a valid begin marker."
                if xVar.findtext("range_end") is not None:
                    sRProp = UI.SafeHTML(xVar.findtext("range_end", ""))
                    sRIdxChecked = " checked=\"checked\""
                elif xVar.findtext("suffix") is not None:
                    sRProp = UI.SafeHTML(xVar.findtext("suffix", ""))
                    sRPosChecked = " checked=\"checked\""
                else:
                    return "Variable XML data for step [" + sStepID + "] does not contain a valid end marker."
                sVarStrip = "Variable: " \
                    " <input type=\"text\" class=\"var_name code var_unique\" id=\"" + sVarGUID + "_name\"" \
                        " validate_as=\"variable\"" \
                        " value=\"" + sName + "\" />"
                sDetailStrip = " will contain the output found between <br />" \
                    "<input type=\"radio\" name=\"" + sVarGUID + "_l_mode\" value=\"index\" " + sLIdxChecked + " class=\"prop\" refid=\"" + sVarGUID + "\" />" \
                        " position / " \
                        " <input type=\"radio\" name=\"" + sVarGUID + "_l_mode\" value=\"string\" " + sLPosChecked + " class=\"prop\" refid=\"" + sVarGUID + "\" />" \
                        " prefix " \
                        " <input type=\"text\" class=\"w100px code prop\" id=\"" + sVarGUID + "_l_prop\"" \
                        " value=\"" + sLProp + "\" refid=\"" + sVarGUID + "\" />" \
                        " and " \
                        "<input type=\"radio\" name=\"" + sVarGUID + "_r_mode\" value=\"index\" " + sRIdxChecked + " class=\"prop\" refid=\"" + sVarGUID + "\" />" \
                        " position / " \
                        " <input type=\"radio\" name=\"" + sVarGUID + "_r_mode\" value=\"string\" " + sRPosChecked + " class=\"prop\" refid=\"" + sVarGUID + "\" />" \
                        " suffix " \
                        " <input type=\"text\" class=\"w100px code prop\" id=\"" + sVarGUID + "_r_prop\"" \
                        " value=\"" + sRProp + "\" refid=\"" + sVarGUID + "\" />."
                
            elif sType == "delimited":
                sLProp = xVar.findtext("position", "")
                sVarStrip = "Variable: " \
                    " <input type=\"text\" class=\"var_name code var_unique\" id=\"" + sVarGUID + "_name\"" \
                        " validate_as=\"variable\"" \
                        " value=\"" + sName + "\" />"
                sDetailStrip += "" \
                    " will contain the data from column position" \
                        " <input type=\"text\" class=\"w100px code\" id=\"" + sVarGUID + "_l_prop\"" \
                        " value=\"" + sLProp + "\" validate_as=\"posint\" />."
                
            elif sType == "regex":
                sLProp = UI.SafeHTML(xVar.findtext("regex", ""))
                sVarStrip = "Variable: " \
                    " <input type=\"text\" class=\"var_name code var_unique\" id=\"" + sVarGUID + "_name\"" \
                        " validate_as=\"variable\"" \
                        " value=\"" + sName + "\" />"
                sDetailStrip += "" \
                    " will contain the result of the following regular expression: " \
                        " <br /><input type=\"text\" class=\"w98pct code\"" \
                        " id=\"" + sVarGUID + "_l_prop\"" \
                        " value=\"" + sLProp + "\" />."
            elif sType == "xpath":
                sLProp = UI.SafeHTML(xVar.findtext("xpath", ""))
                sVarStrip = "Variable: " \
                    " <input type=\"text\" class=\"var_name code var_unique\" id=\"" + sVarGUID + "_name\"" \
                        " validate_as=\"variable\"" \
                        " value=\"" + sName + "\" />"
                sDetailStrip += "" \
                    " will contain the Xpath: " \
                        " <br /><input type=\"text\" class=\"w98pct code\"" \
                        " id=\"" + sVarGUID + "_l_prop\"" \
                        " value=\"" + sLProp + "\" />."
            else:
                sHTML += "INVALID TYPE"
            
            
            sHTML += "<li id=\"" + sVarGUID + "\" class=\"variable\" var_type=\"" + sType + "\">"
            sHTML += "<span class=\"variable_name\">" + sVarStrip + "</span>"
            sHTML += "<span class=\"ui-icon ui-icon-close forceinline variable_delete_btn\" remove_id=\"" + sVarGUID + "\" title=\"Delete Variable\"></span>"
            sHTML += "<span class=\"variable_detail\">" + sDetailStrip + "</span>"
            # an error message placeholder
            sHTML += "<br /><span id=\"" + sVarGUID + "_msg\" class=\"var_error_msg\"></span>"
            
            sHTML += "</li>\n"
            

    sHTML += "</ul>\n"

    return sHTML

def LabelNonprintable(iVal):
    if iVal == 0:
        return "N/A"
    elif iVal == 9:
        return "TAB"
    elif iVal == 10:
        return "LF"
    elif iVal == 12:
        return "FF"
    elif iVal == 13:
        return "CR"
    elif iVal == 27:
        return "ESC"
    elif iVal == 32:
        return "SP"
    else:
        return "&#" + str(iVal) + ";"

    

"""
From here to the bottom are the hardcoded commands.
"""

def GetEcosystemObjects(oStep):
    """
        This one could easily be moved out of hardcode and into the commands.xml using a function based lookup.
    """
    try:
        xd = oStep.FunctionXDoc

        sObjectType = xd.findtext("object_type", "")
        sHTML = ""

        sHTML += "Select Object Type:\n"
        sHTML += "<select " + CommonAttribs(oStep, True, "object_type", "") + ">\n"
        sHTML += "  <option " + SetOption("", sObjectType) + " value=\"\"></option>\n"

        # this builds a unique list of all object types, provider agnostic
        otypes = {}
        cp = cloud.CloudProviders(include_clouds = False)
        if cp is not None:
            for p in cp.itervalues():
                cots = p.GetAllObjectTypes()
                for cot in cots.itervalues():
                    if cot.ID not in otypes.iterkeys():
                        otypes[cot.ID] = cot

        for otype in sorted(otypes.itervalues()):
            sHTML += "<option " + SetOption(otype.ID, sObjectType) + " value=\"" + otype.ID + "\">" + otype.Label + "</option>\n";            
        
        sHTML += "</select>\n"

        sCloudFilter = xd.findtext("cloud_filter", "")
        sHTML += "Cloud Filter: \n" + "<input type=\"text\" " + \
        CommonAttribs(oStep, False, "cloud_filter", "") + \
        " help=\"Enter all or part of a cloud name to filter the results.\" value=\"" + sCloudFilter + "\" />\n"

        sResultName = xd.findtext("result_name", "")
        sHTML += "<br />Result Variable: \n" + "<input type=\"text\" " + \
        CommonAttribs(oStep, False, "result_name", "") + \
        " help=\"This variable array will contain the ID of each Ecosystem Object.\" value=\"" + sResultName + "\" />\n"

        sCloudName = xd.findtext("cloud_name", "")
        sHTML += " Cloud Name Variable: \n" + "<input type=\"text\" " + \
        CommonAttribs(oStep, False, "cloud_name", "") + \
        " help=\"This variable array will contain the name of the Cloud for each Ecosystem Object.\" value=\"" + sCloudName + "\" />\n"

        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def SqlExec(oStep):
    """
        This should return a tuple, the html and a flag of whether or not to draw the variable button
    """
    try:
        sStepID = oStep.ID
        xd = oStep.FunctionXDoc

        """TAKE NOTE:
        * 
        * Similar to the windows command...
        * ... we are updating a record here when we GET the data.
        * 
        * Why?  Because this command has modes.
        * The data has different meaning depending on the 'mode'.
        * 
        * So, on the client if the user changes the 'mode', the new command may not need all the fields
        * that the previous selection needed.
        * 
        * So, we just wipe any unused fields based on the current mode.
        * """
        sCommand = xd.findtext("sql", "")
        sConnName = xd.findtext("conn_name", "")
        sMode = xd.findtext("mode", "")
        sHandle = xd.findtext("handle", "")

        sHTML = ""
        sElementID = catocommon.new_guid()
        sFieldID = catocommon.new_guid()
        bDrawVarButton = False
        bDrawSQLBox = False
        bDrawHandle = False
        bDrawKeyValSection = False

        sHTML += "Connection:\n"
        sHTML += "<input type=\"text\" " + CommonAttribsWithID(oStep, True, "conn_name", sElementID, "")
        sHTML += " help=\"Enter an active connection where this SQL will be executed.\" value=\"" + sConnName + "\" />"
        sHTML += "<span class=\"ui-icon ui-icon-search forceinline conn_picker_btn pointer\" link_to=\"" + sElementID + "\"></span>\n"

        sHTML += "Mode:\n"
        sHTML += "<select " + CommonAttribs(oStep, True, "mode", "") + " reget_on_change=\"true\">\n"
        sHTML += "  <option " + SetOption("SQL", sMode) + " value=\"SQL\">SQL</option>\n"
        sHTML += "  <option " + SetOption("BEGIN", sMode) + " value=\"BEGIN\">BEGIN</option>\n"
        sHTML += "  <option " + SetOption("COMMIT", sMode) + " value=\"COMMIT\">COMMIT</option>\n"
        # sHTML += "  <option " + SetOption("COMMIT / BEGIN", sMode) + " value=\"COMMIT / BEGIN\">COMMIT / BEGIN</option>\n"
        sHTML += "  <option " + SetOption("ROLLBACK", sMode) + " value=\"ROLLBACK\">ROLLBACK</option>\n"
        sHTML += "  <option " + SetOption("EXEC", sMode) + " value=\"EXEC\">EXEC</option>\n"
        sHTML += "  <option " + SetOption("PL/SQL", sMode) + " value=\"PL/SQL\">PL/SQL</option>\n"
        sHTML += "  <option " + SetOption("PREPARE", sMode) + " value=\"PREPARE\">PREPARE</option>\n"
        sHTML += "  <option " + SetOption("RUN", sMode) + " value=\"RUN\">RUN</option>\n"
        sHTML += "</select>\n"


        # here we go!
        # certain modes show different fields.

        if sMode == "BEGIN" or sMode == "COMMIT" or sMode == "ROLLBACK":
            # these modes have no SQL or pairs or variables
            SetNodeValueinCommandXML(sStepID, "sql", "")
            SetNodeValueinCommandXML(sStepID, "handle", "")
            RemoveFromCommandXML(sStepID, "pair")
            RemoveStepVars(sStepID)
        elif sMode == "PREPARE":
            bDrawSQLBox = True
            bDrawHandle = True

            # this mode has no pairs or variables
            RemoveFromCommandXML(sStepID, "pair")
            RemoveStepVars(sStepID)
        elif sMode == "RUN":
            bDrawVarButton = True
            bDrawHandle = True
            bDrawKeyValSection = True

            # this mode has no SQL
            SetNodeValueinCommandXML(sStepID, "sql", "")
        else:
            bDrawVarButton = True
            bDrawSQLBox = True

            SetNodeValueinCommandXML(sStepID, "handle", "")
            # the default mode has no pairs
            RemoveFromCommandXML(sStepID, "pair")

        if bDrawHandle:
            sHTML += "Handle:\n"
            sHTML += "<input type=\"text\" " + CommonAttribs(oStep, True, "handle", "")
            sHTML += " help=\"Enter a handle for this prepared statement.\" value=\"" + sHandle + "\" />"

        if bDrawKeyValSection:
            sHTML += DrawKeyValueSection(oStep, False, False, "Bind", "Value")

        if bDrawSQLBox:
            #  we gotta get the field id first, but don't show the textarea until after
            sCommonAttribsForTA = CommonAttribsWithID(oStep, True, "sql", sFieldID, "")

            sHTML += "<br />SQL:\n"
            # big box button
            sHTML += "<img class=\"big_box_btn pointer\" alt=\"\"" \
                " src=\"static/images/icons/edit_16.png\"" \
                " link_to=\"" + sFieldID + "\" /><br />\n"

            sHTML += "<textarea " + sCommonAttribsForTA + " help=\"Enter a SQL query or procedure.\">" + sCommand + "</textarea>"
        return sHTML, bDrawVarButton
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def SqlExec_View(oStep):
    try:
        xd = oStep.FunctionXDoc

        """TAKE NOTE:
        * 
        * Similar to the windows command...
        * ... we are updating a record here when we GET the data.
        * 
        * Why?  Because this command has modes.
        * The data has different meaning depending on the 'mode'.
        * 
        * So, on the client if the user changes the 'mode', the new command may not need all the fields
        * that the previous selection needed.
        * 
        * So, we just wipe any unused fields based on the current mode.
        * """
        sCommand = xd.findtext("sql", "")
        sConnName = xd.findtext("conn_name", "")
        sMode = xd.findtext("mode", "")
        sHandle = xd.findtext("handle", "")

        sHTML = ""
        bDrawSQLBox = False
        bDrawHandle = False
        bDrawKeyValSection = False

        sHTML += "Connection:\n"
        sHTML += "<span class=\"code\">" + sConnName + "</span>"

        sHTML += "Mode:\n"
        sHTML += "<span class=\"code\">" + sMode + "</span>"


        if sMode == "BEGIN" or sMode == "COMMIT" or sMode == "ROLLBACK":
            """Does nothing special"""
        elif sMode == "PREPARE":
            bDrawSQLBox = True
            bDrawHandle = True
        elif sMode == "RUN":
            bDrawHandle = True
            bDrawKeyValSection = True
        else:
            bDrawSQLBox = True

        if bDrawHandle:
            sHTML += "Handle:\n"
            sHTML += "<span class=\"code\">" + sHandle + "</span>"

        if bDrawKeyValSection:
            sHTML += DrawReadOnlyKeyValueSection(oStep, False, False, "Bind", "Value")

        if bDrawSQLBox:
            sHTML += "<br />SQL:\n"
            sHTML += "<div class=\"codebox\">" + UI.SafeHTML(sCommand) + "</div>"
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def RunTask(oStep):
    try:
        db = catocommon.new_conn()

        sStepID = oStep.ID
        xd = oStep.FunctionXDoc
    
        sActualTaskID = ""
        # sOnSuccess = ""
        # sOnError = ""
        sAssetID = ""
        sAssetName = ""
        sLabel = ""
        sHTML = ""
        sParameterXML = ""
        
        sOriginalTaskID = xd.findtext("original_task_id", "")
        sVersion = xd.findtext("version")
        sHandle = xd.findtext("handle", "")
        sTime = xd.findtext("time_to_wait", "")
        sAssetID = xd.findtext("asset_id", "")
    
        # xSuccess = xd.find("# on_success")
        # if xSuccess is None) return "Error: XML does not contain on_success:
        # sOnSuccess = xSuccess.findtext(value, "")
    
        # xError = xd.find("# on_error")
        # if xError is None) return "Error: XML does not contain on_error:
        # sOnError = xError.findtext(value, "")
    
        # get the name and code for belonging to this otid and version
        if catocommon.is_guid(sOriginalTaskID):
            sSQL = "select task_id, task_code, task_name, parameter_xml from task" \
                " where original_task_id = '" + sOriginalTaskID + "'" + \
                (" and default_version = 1" if not sVersion else " and version = '" + sVersion + "'")
    
            dr = db.select_row_dict(sSQL)
            if db.error:
                UI.log_nouser(db.error, 0)
                return "Error retrieving target Task.(1)" + db.error
    
            if dr is not None:
                sLabel = dr["task_code"] + " : " + dr["task_name"]
                sActualTaskID = dr["task_id"]
                sParameterXML = (dr["parameter_xml"] if dr["parameter_xml"] else "")
            else:
                # It's possible that the user changed the task from the picker but had 
                # selected a version, which is still there now but may not apply to the new task.
                # so, if the above SQL failed, try: again by resetting the version box to the default.
                sSQL = "select task_id, task_code, task_name, parameter_xml from task" \
                    " where original_task_id = '" + sOriginalTaskID + "'" \
                    " and default_version = 1"
    
                dr = db.select_row_dict(sSQL)
                if db.error:
                    UI.log_nouser(db.error, 0)
                    return "Error retrieving target Task.(2)<br />" + db.error
    
                if dr is not None:
                    sLabel = dr["task_code"] + " : " + dr["task_name"]
                    sActualTaskID = dr["task_id"]
                    sParameterXML = (dr["parameter_xml"] if dr["parameter_xml"] else "")
    
                    # oh yeah, and set the version field to null since it was wrong.
                    SetNodeValueinCommandXML(sStepID, "//version", "")
                else:
                    # a default doesnt event exist, really fail...
                    return "Unable to find task [" + sOriginalTaskID + "] version [" + sVersion + "]." + db.error
    
    
        # IF IT's A GUID...
        #  get the asset name belonging to this asset_id
        #  OTHERWISE
        #  make the sAssetName value be what's in sAssetID (a literal value in [[variable]] format)
        if catocommon.is_guid(sAssetID):
            sSQL = "select asset_name from asset where asset_id = '" + sAssetID + "'"
    
            sAssetName = db.select_col_noexcep(sSQL)
            if db.error:
                return "Error retrieving Run Task Asset Name." + db.error
    
            if sAssetName == "":
                return "Unable to find Asset by ID - [" + sAssetID + "]." + db.error
        else:
            sAssetName = sAssetID
    
    
    
    
        # all good, draw the widget
        sOTIDField = catocommon.new_guid()
    
        sHTML += "<input type=\"text\" " + \
            CommonAttribsWithID(oStep, True, "original_task_id", sOTIDField, "hidden") + \
            " value=\"" + sOriginalTaskID + "\"" + " reget_on_change=\"true\" />"
    
        sHTML += "Task: \n"
        sHTML += "<input type=\"text\"" \
            " onkeydown=\"return false;\"" \
            " onkeypress=\"return false;\"" \
            " is_required=\"true\"" \
            " step_id=\"" + sStepID + "\"" \
            " class=\"code w75pct\"" \
            " id=\"fn_run_task_taskname_" + sStepID + "\"" \
            " value=\"" + sLabel + "\" />\n"
        sHTML += "<span class=\"ui-icon ui-icon-search forceinline task_picker_btn pointer\" title=\"Pick Task\"" \
            " target_field_id=\"" + sOTIDField + "\"" \
            " step_id=\"" + sStepID + "\"></span>\n"
        if sActualTaskID != "":
            sHTML += "<span class=\"ui-icon ui-icon-pencil forceinline task_open_btn pointer\" title=\"Edit Task\"" \
                " task_id=\"" + sActualTaskID + "\"></span>\n"
            sHTML += "<span class=\"ui-icon ui-icon-print forceinline task_print_btn pointer\" title=\"View Task\"" \
                " task_id=\"" + sActualTaskID + "\"></span>\n"
    
        # versions
        if catocommon.is_guid(sOriginalTaskID):
            sHTML += "<br />"
            sHTML += "Version: \n"
            sHTML += "<select " + CommonAttribs(oStep, False, "version", "") + " reget_on_change=\"true\">\n"
            # default
            sHTML += "<option " + SetOption("", sVersion) + " value=\"\">Default</option>\n"
    
            sSQL = "select version from task" \
                " where original_task_id = '" + sOriginalTaskID + "'" \
                " order by version"
            dt = db.select_all_dict(sSQL)
            if db.error:
                UI.log_nouser(db.error, 0)
                return "Database Error:" + db.error
    
            if dt:
                for dr in dt:
                    sHTML += "<option " + SetOption(str(dr["version"]), sVersion) + " value=\"" + str(dr["version"]) + "\">" + str(dr["version"]) + "</option>\n"
            else:
                return "Unable to continue - Cannot find Version for Task [" + sOriginalTaskID + "]."
    
            sHTML += "</select></span>\n"
    
    
    
        sHTML += "<br />"

        #  asset
        sAssetField = catocommon.new_guid()
        sHTML += "<input type=\"text\" " + \
            CommonAttribsWithID(oStep, False, "asset_id", sAssetField, "hidden") + \
            " value=\"" + sAssetID + "\" />"
    
        sHTML += "Asset: \n"
        sHTML += "<input type=\"text\"" \
            " help=\"Select an Asset or enter a variable.\"" + \
            ("" if catocommon.is_guid(sAssetID) else " syntax=\"variable\"") + \
            " step_id=\"" + sStepID + "\"" \
            " class=\"code w75pct\"" \
            " id=\"fn_run_task_assetname_" + sStepID + "\"" + \
            (" disabled=\"disabled\"" if catocommon.is_guid(sAssetID) else "") + \
            " onchange=\"javascript:pushStepFieldChangeVia(this, '" + sAssetField + "');\"" \
            " value=\"" + sAssetName + "\" />\n"
    
        sHTML += "<span class=\"ui-icon ui-icon-close forceinline fn_field_clear_btn pointer\" clear_id=\"fn_run_task_assetname_" + sStepID + "\"" \
            " title=\"Clear\"></span>"
    
        sHTML += "<span class=\"ui-icon ui-icon-search forceinline asset_picker_btn pointer\" title=\"Select\"" \
            " link_to=\"" + sAssetField + "\"" \
            " target_field_id=\"fn_run_task_assetname_" + sStepID + "\"" \
            " step_id=\"" + sStepID + "\"></span>\n"
    
        sHTML += "<br />"
        sHTML += "Task Handle: <input type=\"text\" " + CommonAttribs(oStep, True, "handle", "") + \
            " value=\"" + sHandle + "\" />\n"
    
        sHTML += "Time to Wait: <input type=\"text\" " + CommonAttribs(oStep, False, "time_to_wait", "") + \
            " value=\"" + sTime + "\" />\n"
    
        # sHTML += "<br />"
        # sHTML += "The following Command will be executed on Success:<br />\n"
        # # enable the dropzone for the Success action
        # sHTML += DrawDropZone(sStepID, sOnSuccess, sFunction, "on_success", "", False)
    
        # sHTML += "The following Command will be executed on Error:<br />\n"
        # # enable the dropzone for the Error action
        # sHTML += DrawDropZone(sStepID, sOnError, sFunction, "on_error", "", False)
        
        
        # edit parameters link - not available unless a task is selected
        if sActualTaskID:
            # this is cheating but it's faster than parsing xml
            # count the occurences of "</parameter>" in the parameter_xml
            x = sParameterXML.count("</parameter>")
            r = sParameterXML.count("required=\"true\"")
            if x:
                # we need to make sure the parameters are saved on the run_task command,
                # even if it's embedded in another command.
                sBaseXPath = (oStep.XPathPrefix if oStep.XPathPrefix else "")
                icon = ("alert" if r else "pencil")
                sHTML += "<hr />"
                sHTML += "<div class=\"fn_runtask_edit_parameters_btn pointer\"" \
                    " base_xpath=\"" + sBaseXPath + "\"" \
                    " task_id=\"" + sActualTaskID + "\"" \
                    " step_id=\"" + sStepID + "\">" \
                    "<span class=\"ui-icon ui-icon-%s forceinline \"></span> Edit Parameters (%s)</div>" % (icon, str(x))
        
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."
    finally:
        if db.conn.socket:
            db.close()

def RunTask_View(oStep):
    try:
        db = catocommon.new_conn()

        sStepID = oStep.ID
        xd = oStep.FunctionXDoc
    
        sActualTaskID = ""
        # sOnSuccess = ""
        # sOnError = ""
        sAssetID = ""
        sAssetName = ""
        sLabel = ""
        sHTML = ""
        sParameterXML = ""
        
        sOriginalTaskID = xd.findtext("original_task_id", "")
        sVersion = xd.findtext("version")
        sHandle = xd.findtext("handle", "")
        sTime = xd.findtext("time_to_wait", "")
        sAssetID = xd.findtext("asset_id", "")
    
        # get the name and code for belonging to this otid and version
        if catocommon.is_guid(sOriginalTaskID):
            sSQL = "select task_id, task_code, task_name, parameter_xml from task" \
                " where original_task_id = '" + sOriginalTaskID + "'" + \
                (" and default_version = 1" if not sVersion else " and version = '" + sVersion + "'")
    
            dr = db.select_row_dict(sSQL)
            if db.error:
                UI.log_nouser(db.error, 0)
                return "Error retrieving target Task.(1)" + db.error
    
            if dr is not None:
                sLabel = dr["task_code"] + " : " + dr["task_name"]
                sActualTaskID = dr["task_id"]
                sParameterXML = (dr["parameter_xml"] if dr["parameter_xml"] else "")
            else:
                return "Unable to find task [" + sOriginalTaskID + "] version [" + sVersion + "]." + db.error
    
    
        # IF IT's A GUID...
        #  get the asset name belonging to this asset_id
        #  OTHERWISE
        #  make the sAssetName value be what's in sAssetID (a literal value in [[variable]] format)
        if catocommon.is_guid(sAssetID):
            sSQL = "select asset_name from asset where asset_id = '" + sAssetID + "'"
    
            sAssetName = db.select_col_noexcep(sSQL)
            if db.error:
                return "Error retrieving Run Task Asset Name." + db.error
    
            if sAssetName == "":
                return "Unable to find Asset by ID - [" + sAssetID + "]." + db.error
        else:
            sAssetName = sAssetID
    
    
    
    
        # all good, draw the widget
        sHTML += "Task: \n"
        sHTML += "<span class=\"code\">" + sLabel + "</span>"
    
        # versions
        if catocommon.is_guid(sOriginalTaskID):
            sHTML += "<br />"
            sHTML += "Version: \n"
            sHTML += "<span class=\"code\">" + (sVersion if sVersion else "Default") + "</span>"
    
    
    
        sHTML += "<br />"

        #  asset
        sHTML += "Asset: \n"
        sHTML += "<span class=\"code\">" + sAssetName + "</span>"
    
        sHTML += "<br />"
        sHTML += "Task Handle:\n"
        sHTML += "<span class=\"code\">" + sHandle + "</span>"
    
        sHTML += " Time to Wait:\n"
        sHTML += "<span class=\"code\">" + sTime + "</span>"
    
        if sActualTaskID:
            if sParameterXML:
                sHTML += "<hr />"
                sHTML += "Parameters:"
                sHTML += DrawCommandParameterSection(sParameterXML, False, True)
        
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."
    finally:
        if db.conn.socket:
            db.close()

def Subtask(oStep):
    try:
        db = catocommon.new_conn()

        sStepID = oStep.ID
        xd = oStep.FunctionXDoc
    
        sActualTaskID = ""
        sLabel = ""
        sHTML = ""
    
        sOriginalTaskID = xd.findtext("original_task_id", "")
        sVersion = xd.findtext("version", "")
    
        # get the name and code for belonging to this otid and version
        if catocommon.is_guid(sOriginalTaskID):
            sSQL = "select task_id, task_code, task_name from task" \
                " where original_task_id = '" + sOriginalTaskID + "'" + \
                (" and default_version = 1" if not sVersion else " and version = '" + sVersion + "'")
    
            dr = db.select_row_dict(sSQL)
            if db.error:
                UI.log("Error retrieving subtask.(1)<br />" + db.error)
                return "Error retrieving subtask.(1)<br />" + db.error

            if dr is not None:
                sLabel = dr["task_code"] + " : " + dr["task_name"]
                sActualTaskID = dr["task_id"]
            else:
                # It's possible that the user changed the task from the picker but had 
                # selected a version, which is still there now but may not apply to the new task.
                # so, if the above SQL failed, try: again by resetting the version box to the default.
                sSQL = "select task_id, task_code, task_name from task" \
                    " where original_task_id = '" + sOriginalTaskID + "'" \
                    " and default_version = 1"
    
                dr = db.select_row_dict(sSQL)
                if db.error:
                    UI.log("Error retrieving subtask.(2)<br />" + db.error)
                    return "Error retrieving subtask.(2)<br />" + db.error
    
                if dr is not None:
                    sLabel = dr["task_code"] + " : " + dr["task_name"]
                    sActualTaskID = dr["task_id"]
    
                    # oh yeah, and set the version field to null since it was wrong.
                    SetNodeValueinCommandXML(sStepID, "version", "")
                else:
                    # a default doesnt event exist, really fail...
                    UI.log("Unable to find task [" + sOriginalTaskID + "] version [" + sVersion + "].")
                    return "Unable to find task [" + sOriginalTaskID + "] version [" + sVersion + "]."
    
        # all good, draw the widget
        sOTIDField = catocommon.new_guid()
    
        sHTML += "<input type=\"text\" " + \
            CommonAttribsWithID(oStep, True, "original_task_id", sOTIDField, "hidden") + \
            " value=\"" + sOriginalTaskID + "\" reget_on_change=\"true\" />\n"
    
        sHTML += "Task: \n"
        sHTML += "<input type=\"text\"" \
            " onkeydown=\"return false;\"" \
            " onkeypress=\"return false;\"" \
            " is_required=\"true\"" \
            " step_id=\"" + sStepID + "\"" \
            " class=\"code w75pct\"" \
            " id=\"fn_subtask_taskname_" + sStepID + "\"" \
            " value=\"" + sLabel + "\" />\n"
        sHTML += "<span class=\"ui-icon ui-icon-search forceinline task_picker_btn pointer\"" \
            " target_field_id=\"" + sOTIDField + "\"" \
            " step_id=\"" + sStepID + "\"></span>\n"
        if sActualTaskID != "":
            sHTML += "<span class=\"ui-icon ui-icon-pencil forceinline task_open_btn pointer\" title=\"Edit Task\"" \
                " task_id=\"" + sActualTaskID + "\"></span>\n"
            sHTML += "<span class=\"ui-icon ui-icon-print forceinline task_print_btn pointer\" title=\"View Task\"" \
                " task_id=\"" + sActualTaskID + "\"></span>\n"
        # versions
        if catocommon.is_guid(sOriginalTaskID):
            sHTML += "<br />"
            sHTML += "Version: \n"
            sHTML += "<select " + CommonAttribs(oStep, False, "version", "") + \
                " reget_on_change=\"true\">\n"
            # default
            sHTML += "<option " + SetOption("", sVersion) + " value=\"\">Default</option>\n"
    
            sSQL = "select version from task" \
                " where original_task_id = '" + sOriginalTaskID + "'" \
                " order by version"
            dt = db.select_all_dict(sSQL)
            if db.error:
                UI.log_nouser(db.error, 0)
            if dt:
                for dr in dt:
                    sHTML += "<option " + SetOption(str(dr["version"]), sVersion) + " value=\"" + str(dr["version"]) + "\">" + str(dr["version"]) + "</option>\n"
            else:
                return "Unable to continue - Cannot find Version for Task [" + sOriginalTaskID + "]."
    
            sHTML += "</select></span>\n"
    
        # let's display a div for the parameters
        sHTML += "<div>"
        sHTML += "<span class=\"subtask_view_parameters_btn pointer\" id=\"stvp_" + sActualTaskID + "\">"
        sHTML += "<span class=\"ui-icon ui-icon-document forceinline\"></span> ( click to view parameters )</span>"
        sHTML += "<div class=\"subtask_view_parameters\"></div>"
        sHTML += "</div>"
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."
    finally:
        if db.conn.socket:
            db.close()

def Subtask_View(oStep):
    try:
        db = catocommon.new_conn()

        xd = oStep.FunctionXDoc
    
        sActualTaskID = ""
        sLabel = ""
        sHTML = ""
    
        sOriginalTaskID = xd.findtext("original_task_id", "")
        sVersion = xd.findtext("version", "")
    
        # get the name and code for belonging to this otid and version
        if catocommon.is_guid(sOriginalTaskID):
            sSQL = "select task_id, task_code, task_name, parameter_xml from task" \
                " where original_task_id = '" + sOriginalTaskID + "'" + \
                (" and default_version = 1" if not sVersion else " and version = '" + sVersion + "'")
    
            dr = db.select_row_dict(sSQL)
            if db.error:
                UI.log("Error retrieving subtask.(1)<br />" + db.error)
                return "Error retrieving subtask.(1)<br />" + db.error

            if dr is not None:
                sLabel = dr["task_code"] + " : " + dr["task_name"]
                sActualTaskID = dr["task_id"]
                sParameterXML = (dr["parameter_xml"] if dr["parameter_xml"] else "")
            else:
                return "Unable to find task [" + sOriginalTaskID + "] version [" + sVersion + "]."
    
        # all good, draw the widget
        sHTML += "Task: \n"
        sHTML += "<span class=\"code\">" + sLabel + "</span>"
        # versions
        if catocommon.is_guid(sOriginalTaskID):
            sHTML += "<br />"
            sHTML += "Version: \n"
            sHTML += "<span class=\"code\">" + (sVersion if sVersion else "Default") + "</span>"
    
        # let's display a div for the parameters
        if sActualTaskID:
            if sParameterXML:
                sHTML += "<hr />"
                sHTML += "Parameters:"
                sHTML += DrawCommandParameterSection(sParameterXML, False, True)
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."
    finally:
        if db.conn.socket:
            db.close()

def WaitForTasks(oStep):
    try:
        # the base xpath of this command (will be '' unless this is embedded)
        # NOTE: do not append the base_path on any CommonAttribs calls, it's done inside that function.
        base_xpath = (oStep.XPathPrefix + "/" if oStep.XPathPrefix else "")  
    
        sStepID = oStep.ID
        xd = oStep.FunctionXDoc
    
        sHTML = ""
    
        sHTML += "<div id=\"v" + sStepID + "_handles\">"
        sHTML += "Task Handles:<br />"
    
        xPairs = xd.findall("handles/handle")
        i = 1
        for xe in xPairs:
            sKey = xe.findtext("name", "")
    
            sHTML += "&nbsp;&nbsp;&nbsp;<input type=\"text\" " + CommonAttribs(oStep, True, "handles/handle[" + str(i) + "]/name", "") + \
                " validate_as=\"variable\"" \
                " value=\"" + sKey + "\"" \
                " help=\"Enter a Handle name.\"" \
                " />\n"
    
            # can't delete the first one
            if i > 1:
                sHTML += "<span class=\"ui-icon ui-icon-close forceinline fn_node_remove_btn pointer\" remove_path=\"" + base_xpath + "handles/handle[" + str(i) + "]\" step_id=\"" + sStepID + "\"></span>"
    
            # break it every three fields
            if i % 3 == 0 and i >= 3:
                sHTML += "<br />"
    
            i += 1
    
        sHTML += "<div class=\"fn_node_add_btn pointer\"" \
            " function_name=\"" + oStep.FunctionName + "\"" \
            " template_path=\"handles\"" \
            " add_to_node=\"" + base_xpath + "handles\"" \
            " step_id=\"" + sStepID + "\">" \
            "<span class=\"ui-icon ui-icon-plus forceinline\"></span> ( click to add another )</div>"
        sHTML += "</div>"
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def SetEcosystemRegistry(oStep):
    return DrawKeyValueSection(oStep, False, True, "Key", "Value")

def ClearVariable(oStep):
    try:
        # the base xpath of this command (will be '' unless this is embedded)
        # NOTE: do not append the base_path on any CommonAttribs calls, it's done inside that function.
        base_xpath = (oStep.XPathPrefix + "/" if oStep.XPathPrefix else "")  
    
        sStepID = oStep.ID
        xd = oStep.FunctionXDoc
    
        sHTML = ""
    
        sHTML += "<div id=\"v" + sStepID + "_vars\">"
        sHTML += "Variables to Clear:<br />"
    
        xPairs = xd.findall("variables/variable")
        i = 1
        for xe in xPairs:
            sKey = xe.findtext("name", "")
    
            # Trac#389 - Make sure variable names are trimmed of whitespace if it exists
            # hokey, but doing it here because the field update function is global.
            if sKey.strip() != sKey:
                SetNodeValueinCommandXML(sStepID, base_xpath + "variables/variable[" + str(i) + "]/name", sKey.strip())
    
            sHTML += "&nbsp;&nbsp;&nbsp;<input type=\"text\" " + CommonAttribs(oStep, True, "variables/variable[" + str(i) + "]/name", "") + \
                " validate_as=\"variable\"" \
                " value=\"" + sKey + "\"" \
                " help=\"Enter a Variable name.\"" \
                " />\n"
    
            # can't delete the first one
            if i > 1:
                sHTML += "<span class=\"ui-icon ui-icon-close forceinline fn_node_remove_btn pointer\" remove_path=\"" + base_xpath + "variables/variable[" + str(i) + "]\" step_id=\"" + sStepID + "\" title=\"Remove\"></span>"
    
            # break it every three fields
            if i % 3 == 0 and i >= 3:
                sHTML += "<br />"
    
            i += 1
    
        sHTML += "<div class=\"fn_node_add_btn pointer\"" \
            " function_name=\"" + oStep.FunctionName + "\"" \
            " template_path=\"variables\"" \
            " add_to_node=\"" + base_xpath + "variables\"" \
            " step_id=\"" + sStepID + "\">" \
            "<span class=\"ui-icon ui-icon-plus forceinline\" title=\"Add another.\"></span>( click to add another )</div>"
        sHTML += "</div>"
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def SetVariable(oStep):
    try:
        # the base xpath of this command (will be '' unless this is embedded)
        # NOTE: do not append the base_path on any CommonAttribs calls, it's done inside that function.
        base_xpath = (oStep.XPathPrefix + "/" if oStep.XPathPrefix else "")  
    
        sStepID = oStep.ID
        xd = oStep.FunctionXDoc
    
        sHTML = ""
    
        sHTML += "<div id=\"v" + sStepID + "_vars\">"
        sHTML += "<table border=\"0\" class=\"w99pct\" cellpadding=\"0\" cellspacing=\"0\">\n"
    
        xPairs = xd.findall("variables/variable")
        i = 1
        for xe in xPairs:
    
            sKey = xe.findtext("name", "")
            sVal = xe.findtext("value", "")
            sMod = xe.findtext("modifier", "")
    
            # Trac#389 - Make sure variable names are trimmed of whitespace if it exists
            # hokey, but doing it here because the field update function is global.
            if sKey.strip() != sKey:
                SetNodeValueinCommandXML(sStepID, base_xpath + "variables/variable[" + str(i) + "]/name", sKey.strip())
    
            sHTML += "<tr>\n"
            sHTML += "<td class=\"w1pct\">&nbsp;Variable:&nbsp;</td>\n"
            sHTML += "<td class=\"w1pct\"><input type=\"text\" " + CommonAttribs(oStep, True, "variables/variable[" + str(i) + "]/name", "") + \
                " validate_as=\"variable\"" \
                " value=\"" + sKey + "\"" \
                " help=\"Enter a Variable name.\"" \
                " /></td>\n"
            sHTML += "<td class=\"w1pct\">&nbsp;Value:&nbsp;</td>"
    
            #  we gotta get the field id first, but don't show the textarea until after
            sValueFieldID = catocommon.new_guid()
            sCommonAttribs = CommonAttribsWithID(oStep, True, "variables/variable[" + str(i) + "]/value", sValueFieldID, "w90pct")
    
            sHTML += "<td class=\"w75pct\" style=\"vertical-align: bottom;\"><textarea rows=\"1\" style=\"height: 18px;\" " + sCommonAttribs + \
                " help=\"Enter a value for the Variable.\"" \
                ">" + UI.SafeHTML(sVal) + "</textarea>\n"
    
            # big box button
            sHTML += "<span class=\"ui-icon ui-icon-pencil forceinline big_box_btn pointer\" link_to=\"" + sValueFieldID + "\"></span></td>\n"
    
    
            sHTML += "<td class=\"w1pct\">&nbsp;Modifier:&nbsp;</td>"
            sHTML += "<td class=\"w75pct\">"
            sHTML += "<select " + CommonAttribs(oStep, False, "variables/variable[" + str(i) + "]/modifier", "") + ">\n"
            sHTML += "  <option " + SetOption("", sMod) + " value=\"\">--None--</option>\n"
            sHTML += "  <option " + SetOption("TO_UPPER", sMod) + " value=\"TO_UPPER\">UPPERCASE</option>\n"
            sHTML += "  <option " + SetOption("TO_LOWER", sMod) + " value=\"TO_LOWER\">lowercase</option>\n"
            sHTML += "  <option " + SetOption("TO_BASE64", sMod) + " value=\"TO_BASE64\">base64 encode</option>\n"
            sHTML += "  <option " + SetOption("FROM_BASE64", sMod) + " value=\"FROM_BASE64\">base64 decode</option>\n"
            sHTML += "  <option " + SetOption("TO_JSON", sMod) + " value=\"TO_JSON\">Write JSON</option>\n"
            sHTML += "  <option " + SetOption("FROM_JSON", sMod) + " value=\"FROM_JSON\">Read JSON</option>\n"
            sHTML += "</select></td>\n"
    
            sHTML += "<td class=\"w1pct\">"
            # can't delete the first one
            if i > 1:
                sHTML += "<span class=\"ui-icon ui-icon-close forceinline fn_node_remove_btn pointer\" remove_path=\"" + base_xpath + "variables/variable[" + str(i) + "]\" step_id=\"" + sStepID + "\"></span>"
            sHTML += "</td>"
    
            sHTML += "</tr>\n"
    
            i += 1
    
        sHTML += "</table>\n"
    
        sHTML += "<div class=\"fn_node_add_btn pointer\"" \
            " function_name=\"" + oStep.FunctionName + "\"" \
            " template_path=\"variables\"" \
            " add_to_node=\"" + base_xpath + "variables\"" \
            " step_id=\"" + sStepID + "\">" \
            "<span class=\"ui-icon ui-icon-plus forceinline\" title=\"Add another.\" />( click to add another )</div>"
        sHTML += "</div>"
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def NewConnection(oStep):
    try:
        UI.log("New Connection command:", 4)
        sStepID = oStep.ID
        xd = oStep.FunctionXDoc
        xAsset = xd.find("asset")
        xConnName = xd.find("conn_name")
        xConnType = xd.find("conn_type")
        xCloudName = xd.find("cloud_name")
        sAssetID = ("" if xAsset is None else ("" if xAsset.text is None else xAsset.text))
        sConnType = ("ssh" if xConnType is None else ("ssh" if xConnType.text is None else xConnType.text))
        sCloudName = ("" if xCloudName is None else ("" if xCloudName.text is None else xCloudName.text))
    
        sHTML = ""
        sHTML += "Connect via: \n"
        sHTML += "<select " + CommonAttribs(oStep, True, "conn_type", "") + " reget_on_change=\"true\">\n"
    
        for ct in uiGlobals.ConnectionTypes:
            sHTML += "<option " + SetOption(ct, sConnType) + " value=\"" + ct + "\">" + ct + "</option>\n"
    
        sHTML += "</select>\n"

        # nothing special here, just draw the field.
        sHTML += DrawField(xConnName, "conn_name", oStep)

        sHTML += "<br />\n"
    
        # now, based on the type, we might show or hide certain things
        if sConnType == "ssh - ec2":
            # if the assetid is a guid, it means the user switched from another connection type... wipe it.
            if catocommon.is_guid(sAssetID):
                SetNodeValueinCommandXML(sStepID, "asset", "")
                sAssetID = ""
            
            sHTML += " to Instance \n"
            sHTML += "<input type=\"text\" " + \
                CommonAttribs(oStep, True, "asset", "w300px code") + \
                " is_required=\"true\"" \
                " value=\"" + sAssetID + "\"" + " />\n"
    
            sHTML += " in Cloud \n"
            
            sHTML += "<select " + CommonAttribs(oStep, False, "cloud_name", "combo") + ">\n"
            # empty one
            sHTML += "<option " + SetOption("", sCloudName) + " value=\"\"></option>\n"
            
            bValueWasInData = False
            data = ddDataSource_GetAWSClouds()

            if data is not None:
                for k, v in data.iteritems():
                    sHTML += "<option " + SetOption(k, sCloudName) + " value=\"" + k + "\">" + v + "</option>\n"
    
                    if k == sCloudName: bValueWasInData = True
            
            # NOTE: we're allowing the user to enter a value that may not be 
            # in the dataset.  If that's the case, we must add the actual saved value to the list too. 
            if not bValueWasInData: #we didn't find it in the data ..:
                if sCloudName: #and it's a combo and not empty
                    sHTML += "<option " + SetOption(sCloudName, sCloudName) + " value=\"" + sCloudName + "\">" + sCloudName + "</option>\n";            
            
            sHTML += "</select>"
    
        else:
            # clear out the cloud_name property... it's not relevant for these types
            if sCloudName:
                SetNodeValueinCommandXML(sStepID, "cloud_name", "")
            
            # ASSET
            # IF IT's A GUID...
            #  get the asset name belonging to this asset_id
            #  OTHERWISE
            #  make the sAssetName value be what's in sAssetID (a literal value in [[variable]] format)
            if catocommon.is_guid(sAssetID):
                sSQL = "select asset_name from asset where asset_id = '" + sAssetID + "'"
                db = catocommon.new_conn()
                sAssetName = db.select_col_noexcep(sSQL)
                if not sAssetName:
                    sAssetName = sAssetID
                    if db.error:
                        UI.log("Unable to look up Asset name." + db.error)
                    else:
                        SetNodeValueinCommandXML(sStepID, "asset", "")
                db.close()
            else:
                sAssetName = sAssetID
    
            sElementID = catocommon.new_guid()
    
            sHTML += " to Asset: \n"
            sHTML += "<span class=\"ui-icon ui-icon-close forceinline fn_field_clear_btn pointer\" clear_id=\"fn_new_connection_assetname_" + sStepID + "\"" \
                " title=\"Clear\"></span>"
    
            sHTML += "<span class=\"ui-icon ui-icon-search forceinline asset_picker_btn pointer\"" \
                " link_to=\"" + sElementID + "\"" \
                " target_field_id=\"fn_new_connection_assetname_" + sStepID + "\"" \
                " step_id=\"" + sStepID + "\"></span>\n"

            sHTML += "<br />\n"

            sHTML += "<input type=\"text\" " + \
                CommonAttribsWithID(oStep, False, "asset", sElementID, "hidden") + \
                " value=\"" + sAssetID + "\"" + " />\n"
            sHTML += "<textarea" \
                " help=\"Select an Asset or enter a variable.\"" \
                " step_id=\"" + sStepID + "\"" \
                " class=\"code\"" \
                " is_required=\"true\"" \
                " id=\"fn_new_connection_assetname_" + sStepID + "\"" \
                " onchange=\"javascript:pushStepFieldChangeVia(this, '" + sElementID + "');\"" \
                " >" + sAssetName + "</textarea>\n"
            
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def NewConnection_View(oStep):
    try:
        UI.log("New Connection command:", 4)
        sStepID = oStep.ID
        xd = oStep.FunctionXDoc
        xAsset = xd.find("asset")
        xConnName = xd.find("conn_name")
        xConnType = xd.find("conn_type")
        xCloudName = xd.find("cloud_name")
        sAssetID = ("" if xAsset is None else ("" if xAsset.text is None else xAsset.text))
        sConnType = ("ssh" if xConnType is None else ("ssh" if xConnType.text is None else xConnType.text))
        sCloudName = ("" if xCloudName is None else ("" if xCloudName.text is None else xCloudName.text))
    
        sHTML = ""
        sHTML += "Connect via: \n"
        sHTML += "<span class=\"code\">" + sConnType + "</span>"

        # now, based on the type, we might show or hide certain things
        if sConnType == "ssh - ec2":
            sHTML += " to Instance \n"
            sHTML += "<span class=\"code\">" + sAssetID + "</span>"
    
            sHTML += " in Cloud \n"
            sHTML += "<span class=\"code\">" + sCloudName + "</span>"
        else:
            # ASSET
            # IF IT's A GUID...
            #  get the asset name belonging to this asset_id
            #  OTHERWISE
            #  make the sAssetName value be what's in sAssetID (a literal value in [[variable]] format)
            if catocommon.is_guid(sAssetID):
                sSQL = "select asset_name from asset where asset_id = '" + sAssetID + "'"
                db = catocommon.new_conn()
                sAssetName = db.select_col_noexcep(sSQL)
                if not sAssetName:
                    sAssetName = sAssetID
                    if db.error:
                        UI.log("Unable to look up Asset name." + db.error)
                    else:
                        SetNodeValueinCommandXML(sStepID, "asset", "")
                db.close()
            else:
                sAssetName = sAssetID
    
            sHTML += " to Asset \n"
            sHTML += "<span class=\"code\">" + sAssetName + "</span>"
           
        # nothing special here, just draw the field.
        sHTML += DrawReadOnlyField(xConnName, "conn_name", oStep)
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def If(oStep):
    try:
        # the base xpath of this command (will be '' unless this is embedded)
        # NOTE: do not append the base_path on any CommonAttribs calls, it's done inside that function.
        base_xpath = (oStep.XPathPrefix + "/" if oStep.XPathPrefix else "")  
    
        sStepID = oStep.ID
        xd = oStep.FunctionXDoc
    
        sHTML = ""
    
        xTests = xd.findall("tests/test")
        sHTML += "<div id=\"if_" + sStepID + "_conditions\" number=\"" + str(len(xTests)) + "\">"
    
        i = 1 # because XPath starts at "1"
        for xTest in xTests:
            sEval = xTest.findtext("eval", None)
            xAction = xTest.find("action", None)
    
            #  we gotta get the field id first, but don't show the textarea until after
            sFieldID = catocommon.new_guid()
            sCol = "tests/test[" + str(i) + "]/eval"
            sCommonAttribsForTA = CommonAttribsWithID(oStep, True, sCol, sFieldID, "")
    
            # a way to delete the section you just added
            if i == 1:
                xGlobals = ET.parse("luCompareTemplates.xml")
    
                if xGlobals is None:
                    sHTML += "(No Compare templates file available)<br />"
                else:
                    sHTML += "Comparison Template: <select class=\"compare_templates\" textarea_id=\"" + sFieldID + "\">\n"
                    sHTML += "  <option value=\"\"></option>\n"
    
                    xTemplates = xGlobals.findall("template")
                    for xEl in xTemplates:
                        sHTML += "  <option value=\"" + xEl.findtext("value", "") + "\">" + xEl.findtext("name", "") + "</option>\n"
                    sHTML += "</select> <br />\n"
    
    
                sHTML += "If:<br />"
            else:
                sHTML += "<div id=\"if_" + sStepID + "_else_" + str(i) + "\" class=\"fn_if_else_section\">"
                sHTML += "<span class=\"ui-icon ui-icon-close forceinline fn_node_remove_btn pointer\" remove_path=\"" + base_xpath + "tests/test[" + str(i) + "]\" step_id=\"" + sStepID + "\" title=\"Remove this Else If condition.\"></span> "
                sHTML += "&nbsp;&nbsp;&nbsp;Else If:<br />"
    
    
            if sEval is not None:
                sHTML += "<textarea " + sCommonAttribsForTA + " help=\"Enter a test condition.\">" + sEval + "</textarea><br />\n"
            else:
                sHTML += "ERROR: Malformed XML for Step ID [" + sStepID + "].  Missing '" + sCol + "' element."
    
    
            # here's the embedded content
            sCol = "tests/test[" + str(i) + "]/action"

            if xAction is not None:
                xEmbeddedFunction = xAction.find("function")
                # xEmbeddedFunction might be None, but we pass it anyway to get the empty zone drawn
                sHTML += DrawDropZone(oStep, xEmbeddedFunction, sCol, "Action:<br />", True)
            else:
                sHTML += "ERROR: Malformed XML for Step ID [" + sStepID + "].  Missing '" + sCol + "' element."
    
    
            if i != 1:
                sHTML += "</div>"
    
            i += 1
    
        sHTML += "</div>"
    
    
        # draw an add link.  The rest will happen on the client.
        sHTML += "<div class=\"fn_if_add_btn pointer\"" \
            " add_to_node=\"" + oStep.XPathPrefix + "\"" \
            " step_id=\"" + sStepID + "\"" \
            " next_index=\"" + str(i) + "\">" \
            "<span class=\"ui-icon ui-icon-plus forceinline\" title=\"Add another Else If section.\"></span>( click to add another 'Else If' section )</div>"
    
    
        sHTML += "<div id=\"if_" + sStepID + "_else\" class=\"fn_if_else_section\">"
    
        # the final 'else' area
        xElse = xd.find("else", "")
        if xElse is not None:
            sHTML += "<span class=\"fn_node_remove_btn pointer\" step_id=\"" + sStepID + "\" remove_path=\"" + base_xpath + "else\">" \
               "<span class=\"ui-icon ui-icon-close forceinline\" title=\"Remove this Else condition.\"></span></span> "
            sHTML += "Else (no 'If' conditions matched):"

            xEmbeddedFunction = xElse.find("function")
            # xEmbeddedFunction might be None, but we pass it anyway to get the empty zone drawn
            sHTML += DrawDropZone(oStep, xEmbeddedFunction, "else", "", True)
        else:
            # draw an add link.  The rest will happen on the client.
            sHTML += "<div class=\"fn_if_addelse_btn pointer\"" \
                " add_to_node=\"" + oStep.XPathPrefix + "\"" \
                " step_id=\"" + sStepID + "\">" \
                "<span class=\"ui-icon ui-icon-plus forceinline\" title=\"Add an Else section.\"></span>( click to add a final 'Else' section )</div>"
    
        sHTML += "</div>"
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def If_View(oStep):
    try:
        sStepID = oStep.ID
        xd = oStep.FunctionXDoc
    
        sHTML = ""
    
        xTests = xd.findall("tests/test")
        sHTML += "<div id=\"if_" + sStepID + "_conditions\" number=\"" + str(len(xTests)) + "\">"
    
        i = 1 # because XPath starts at "1"
        for xTest in xTests:
            sEval = xTest.findtext("eval", None)
            xAction = xTest.find("action", None)
    
            if i == 1:
                sHTML += "If:<br />"
            else:
                sHTML += "Else If:<br />"
    
            if sEval is not None:
                sHTML += "<div class=\"codebox\">" + UI.SafeHTML(sEval) + "</div>"
            else:
                sHTML += "ERROR: Malformed XML for Step ID [" + sStepID + "].  Missing 'eval' element."
    
    
            if xAction is not None:
                xEmbeddedFunction = xAction.find("function")
                sHTML += DrawEmbeddedReadOnlyStep(xEmbeddedFunction)
            else:
                sHTML += "ERROR: Malformed XML for Step ID [" + sStepID + "].  Missing 'action' element."
    
    
            if i != 1:
                sHTML += "</div>"
    
            i += 1
    
        sHTML += "</div>"
    
    
        sHTML += "<div>"
    
        # the final 'else' area
        xElse = xd.find("else", "")
        if xElse is not None:
            sHTML += "Else (no 'If' conditions matched):"

            xEmbeddedFunction = xElse.find("function")
            sHTML += DrawEmbeddedReadOnlyStep(xEmbeddedFunction)
        else:
            sHTML += "<div class=\"no_step\">No 'Else' action defined.</div>"
            
        sHTML += "</div>"
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def Loop(oStep):
    try:
        xd = oStep.FunctionXDoc
    
        sStart = xd.findtext("start", "")
        sIncrement = xd.findtext("increment", "")
        sCounter = xd.findtext("counter", "")
        sTest = xd.findtext("test", "")
        sCompareTo = xd.findtext("compare_to", "")
        sMax = xd.findtext("max", "")
    
        xAction = xd.find("action")
    
        sHTML = ""
    
    
        sHTML += "Counter variable \n"
        sHTML += "<input type=\"text\" " + CommonAttribs(oStep, True, "counter", "") + \
            " validate_as=\"variable\" help=\"Variable to increment.\" value=\"" + sCounter + "\" />\n"
    
        sHTML += " begins at\n"
        sHTML += "<input type=\"text\" " + CommonAttribs(oStep, True, "start", "w100px")
        sHTML += " help=\"Enter an integer value where the loop will begin.\" value=\"" + sStart + "\" />\n"
    
        sHTML += " and increments by \n"
        sHTML += "<input type=\"text\" " + CommonAttribs(oStep, True, "increment", "w100px") + \
            " help=\"The integer value to increment the counter after each loop.\" value=\"" + sIncrement + "\" />.<br />\n"
    
        sHTML += "Loop will continue while variable is \n"
        sHTML += "<select " + CommonAttribs(oStep, False, "test", "") + ">\n"
        sHTML += "  <option " + SetOption("==", sTest) + " value=\"==\">==</option>\n"
        sHTML += "  <option " + SetOption("!=", sTest) + " value=\"!=\">!=</option>\n"
        sHTML += "  <option " + SetOption("<=", sTest) + " value=\"<=\">&lt;=</option>\n"
        sHTML += "  <option " + SetOption("<", sTest) + " value=\"<\">&lt;</option>\n"
        sHTML += "  <option " + SetOption(">=", sTest) + " value=\">=\">&gt;=</option>\n"
        sHTML += "  <option " + SetOption(">", sTest) + " value=\">\">&gt;</option>\n"
        sHTML += "</select>\n"
    
        sHTML += "<input type=\"text\" " + CommonAttribs(oStep, True, "compare_to", "w400px") + \
            " help=\"Loop until variable compared with this value becomes 'false'.\" value=\"" + sCompareTo + "\" />\n"
    
    
        sHTML += "<br /> or \n"
        sHTML += "<input type=\"text\" " + CommonAttribs(oStep, False, "max", "w50px") + \
            " help=\"For safety, enter a maximum number of times to loop before aborting.\" value=\"" + sMax + "\" /> loops have occured.\n"
    
        sHTML += "<hr />\n"
    
        # enable the dropzone for the Action
        if xAction is not None:
            xEmbeddedFunction = xAction.find("function")
            # xEmbeddedFunction might be None, but we pass it anyway to get the empty zone drawn
            sHTML += DrawDropZone(oStep, xEmbeddedFunction, "action", "Action:<br />", True)
        else:
            sHTML += "ERROR: Malformed XML for Step ID [" + oStep.ID + "].  Missing 'action' element."
    
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def Loop_View(oStep):
    try:
        xd = oStep.FunctionXDoc
    
        sStart = xd.findtext("start", "")
        sIncrement = xd.findtext("increment", "")
        sCounter = xd.findtext("counter", "")
        sTest = xd.findtext("test", "")
        sCompareTo = xd.findtext("compare_to", "")
        sMax = xd.findtext("max", "")
    
        xAction = xd.find("action")
    
        sHTML = ""
    
    
        sHTML += "Counter variable"
        sHTML += "<span class=\"code\">" + sCounter + "</span>"
    
        sHTML += " begins at"
        sHTML += "<span class=\"code\">" + sStart + "</span>"
    
        sHTML += " and increments by"
        sHTML += "<span class=\"code\">" + sIncrement + "</span>."
    
        sHTML += "<br />Loop will continue while variable is"
        sHTML += " <span class=\"code\">" + sTest + "</span>"
        sHTML += " <span class=\"code\">" + sCompareTo + "</span>"    
    
        sHTML += " or"
        sHTML += "<span class=\"code\">" + sMax + "</span>"
        sHTML += " loops have occured."
    
        sHTML += "<hr />"
    
        # enable the dropzone for the Action
        if xAction is not None:
            xEmbeddedFunction = xAction.find("function")
            sHTML += DrawEmbeddedReadOnlyStep(xEmbeddedFunction)
        else:
            sHTML += "ERROR: Malformed XML for Step ID [" + oStep.ID + "].  Missing 'action' element."
    
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def While(oStep):
    try:
        xd = oStep.FunctionXDoc
    
        sTest = xd.findtext("test", "")
        xAction = xd.find("action")
    
        sHTML = ""
        sHTML += "While: \n"
        sHTML += "<td class=\"w75pct\" style=\"vertical-align: bottom;\"><textarea rows=\"10\" style=\"height: 18px;\" " + \
            CommonAttribs(oStep, False, "test", "") + " help=\"\"" \
            ">" + UI.SafeHTML(sTest) + "</textarea>\n"
    
    
        # enable the dropzone for the Action
        if xAction is not None:
            xEmbeddedFunction = xAction.find("function")
            # xEmbeddedFunction might be None, but we pass it anyway to get the empty zone drawn
            sHTML += DrawDropZone(oStep, xEmbeddedFunction, "action", "<hr />Action:<br />", True)
        else:
            sHTML += "ERROR: Malformed XML for Step ID [" + oStep.ID + "].  Missing 'action' element."
    
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def While_View(oStep):
    try:
        xd = oStep.FunctionXDoc
    
        sTest = xd.findtext("test", "")
        xAction = xd.find("action")
    
        sHTML = ""
        sHTML += "While: \n"
        sHTML += "<span class=\"code\">" + sTest + "</span>"    
    
        # enable the dropzone for the Action
        if xAction is not None:
            sHTML += "<hr />Action:<br />"
            xEmbeddedFunction = xAction.find("function")
            sHTML += DrawEmbeddedReadOnlyStep(xEmbeddedFunction)
        else:
            sHTML += "ERROR: Malformed XML for Step ID [" + oStep.ID + "].  Missing 'action' element."
    
    
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def Exists(oStep):
    try:
        # the base xpath of this command (will be '' unless this is embedded)
        # NOTE: do not append the base_path on any CommonAttribs calls, it's done inside that function.
        base_xpath = (oStep.XPathPrefix + "/" if oStep.XPathPrefix else "")  
    
        xd = oStep.FunctionXDoc
    
        sHTML = ""
        sHTML += "<div id=\"v" + oStep.ID + "_vars\">"
        sHTML += "Variables to Test:<br />"
    
        xPairs = xd.findall("variables/variable")
        i = 1
        for xe in xPairs:
            sKey = xe.findtext("name", "")
            sIsTrue = xe.findtext("is_true", "")
    
            # Trac#389 - Make sure variable names are trimmed of whitespace if it exists
            # hokey, but doing it here because the field update function is global.
            if sKey.strip() != sKey:
                SetNodeValueinCommandXML(oStep.ID, base_xpath + "variables/variable[" + str(i) + "]/name", sKey.strip())
    
            sHTML += "&nbsp;&nbsp;&nbsp;<input type=\"text\" " + \
                CommonAttribs(oStep, True, "variables/variable[" + str(i) + "]/name", "") + \
                " validate_as=\"variable\"" \
                " value=\"" + sKey + "\"" \
                " help=\"Enter a Variable name.\"" \
                " />"
    
            sHTML += "&nbsp; Is True:<input type=\"checkbox\" " + \
                CommonAttribs(oStep, True, "variables/variable[" + str(i) + "]/is_true", "") + " " + SetCheckRadio("1", sIsTrue) + " />\n"
    
            # can't delete the first one
            if i > 1:
                sHTML += "<span class=\"ui-icon ui-icon-close forceinline fn_node_remove_btn pointer\" remove_path=\"" + base_xpath + "variables/variable[" + str(i) + "]\" step_id=\"" + oStep.ID + "\" title=\"Remove\"></span>"
    
            # break it every three fields
            # if i % 3 == 0 and i >= 3:
            sHTML += "<br />"
    
            i += 1
    
        sHTML += "<div class=\"fn_node_add_btn pointer\"" \
            " function_name=\"" + oStep.FunctionName + "\"" \
            " template_path=\"variables\"" \
            " add_to_node=\"" + base_xpath + "variables\"" \
            " step_id=\"" + oStep.ID + "\">" \
            "<span class=\"ui-icon ui-icon-plus forceinline\" title=\"Add another.\"></span>( click to add another )</div>"
        sHTML += "</div>"
    
        #  Exists have a Positive and Negative action
        xPositiveAction = xd.find("actions/positive_action")
        if xPositiveAction is None:
            return "Error: XML does not contain positive_action"
    
        xNegativeAction = xd.find("actions/negative_action")
        if xNegativeAction is None:
            return "Error: XML does not contain negative_action"
    
        sCol = ""
    
        # here's the embedded content
        sCol = "actions/positive_action"
    
        if xPositiveAction is not None:
            xEmbeddedFunction = xPositiveAction.find("function")
            sHTML += DrawDropZone(oStep, xEmbeddedFunction, sCol, "Positive Action:<br />", True)
        else:
            sHTML += "ERROR: Malformed XML for Step ID [" + oStep.ID + "].  Missing '" + sCol + "' element."
    
    
        sCol = "actions/negative_action"
    
        if xNegativeAction is not None:
            xEmbeddedFunction = xNegativeAction.find("function")
            sHTML += DrawDropZone(oStep, xEmbeddedFunction, sCol, "Negative Action:<br />", True)
        else:
            sHTML += "ERROR: Malformed XML for Step ID [" + oStep.ID + "].  Missing '" + sCol + "' element."
    
        #  The End.
        return sHTML

    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def Exists_View(oStep):
    try:
        xd = oStep.FunctionXDoc
    
        sHTML = ""
        sHTML += "<div id=\"v" + oStep.ID + "_vars\">"
        sHTML += "Variables to Test:<br />"
    
        xPairs = xd.findall("variables/variable")
        i = 1
        for xe in xPairs:
            sKey = xe.findtext("name", "")
            sIsTrue = xe.findtext("is_true", "")
    
            if sIsTrue == "1":
                sHTML += "<span class=\"code\">" + UI.SafeHTML(sKey) + " (IsTrue) </span>"
            else:
                sHTML += "<span class=\"code\">" + UI.SafeHTML(sKey) + "</span>"
        sHTML += "</div>"
    
        #  Exists have a Positive and Negative action
        xPositiveAction = xd.find("actions/positive_action")
        xNegativeAction = xd.find("actions/negative_action")

        sHTML += "<br />Positive Action:<br />"
        if xPositiveAction is not None:
            xEmbeddedFunction = xPositiveAction.find("function")
            sHTML += DrawEmbeddedReadOnlyStep(xEmbeddedFunction)
        else:
            sHTML += "ERROR: Malformed XML for Step ID [" + oStep.ID + "]."
    
        sHTML += "<br />Negative Action:<br />"
        if xNegativeAction is not None:
            xEmbeddedFunction = xNegativeAction.find("function")
            sHTML += DrawEmbeddedReadOnlyStep(xEmbeddedFunction)
        else:
            sHTML += "ERROR: Malformed XML for Step ID [" + oStep.ID + "]."
    
        #  The End.
        return sHTML

    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)
        return "Unable to draw Step - see log for details."

def Codeblock(oStep):
    xd = oStep.FunctionXDoc

    sCB = xd.findtext("codeblock", "")
    sHTML = ""
    sElementID = catocommon.new_guid()

    sHTML += "Codeblock: \n"
    sHTML += "<input type=\"text\" " + CommonAttribsWithID(oStep, True, "codeblock", sElementID, "") + \
        " reget_on_change=\"true\"" \
        " help=\"Enter a Codeblock Name or variable, or select a Codeblock from the picker.\"" \
        " value=\"" + sCB + "\" />\n"
    sHTML += "<span class=\"ui-icon ui-icon-search forceinline codeblock_picker_btn pointer\" title=\"Pick a Codeblock\"" \
        " link_to=\"" + sElementID + "\"></span>\n"

    if sCB != "":
        # don't enable the jump link if it isn't a valid codeblock on this task.
        # and DON'T CRASH if there isn't a list of codeblocks. (sometimes step objects may not have a full task parent)
        if oStep.Task:
            if oStep.Task.Codeblocks:
                for cb in oStep.Task.Codeblocks.itervalues():
                    if sCB == cb.Name:
                        sHTML += """<span class=\"ui-icon ui-icon-link forceinline codeblock_goto_btn pointer\" title=\"Go To Codeblock\"
                            codeblock=\"%s\"></span>\n""" % sCB
                        break

    return sHTML

def DrawCommandParameterSection(sParameterXML, bEditable, bSnipValues):
    sHTML = ""

    if sParameterXML:
        xParams = ET.fromstring(sParameterXML)
        if xParams is None:
            UI.log("Parameter XML data is invalid.")

        for xParameter in xParams.findall("parameter"):
            sPID = xParameter.get("id", "")
            sName = xParameter.findtext("name", "")
            sDesc = xParameter.findtext("desc", "")

            bEncrypt = catocommon.is_true(xParameter.get("encrypt", ""))

            sHTML += "<div class=\"parameter\">"
            sHTML += "  <div class=\"ui-state-default parameter_header\">"

            sHTML += "<div class=\"step_header_title\"><span class=\"parameter_name"
            sHTML += (" pointer" if bEditable else "") # make the name a pointer if it's editable
            sHTML += "\" id=\"" + sPID + "\">"
            sHTML += sName
            sHTML += "</span></div>"

            sHTML += "<div class=\"step_header_icons\">"
            sHTML += "<span class=\"ui-icon ui-icon-info forceinline parameter_help_btn\" title=\"" + sDesc.replace("\"", "") + "\"></span>"

            if catocommon.is_true(bEditable):
                sHTML += "<span class=\"ui-icon ui-icon-close forceinline parameter_remove_btn pointer\" remove_id=\"" + sPID + "\"></span>"

            sHTML += "</div>"
            sHTML += "</div>"


            sHTML += "<div class=\"ui-widget-content ui-corner-bottom clearfloat parameter_detail\">"

            # desc - a short snip is shown here... 75 chars.

            # if sDesc):
            #     if bSnipValues:
            #         sDesc = UI.GetSnip(sDesc, 75)
            #     else
            #         sDesc = UI.FixBreaks(sDesc)
            # sHTML += "<div class=\"parameter_desc hidden\">" + sDesc + "</div>"


            # values
            xValues = xParameter.find("values")
            if xValues is not None:
                for xValue in xValues.findall("value"):
                    sValue = ("" if not xValue.text else xValue.text)

                    # only show stars IF it's encrypted, but ONLY if it has a value
                    if bEncrypt and sValue:
                        sValue = "********"
                    else:
                        if bSnipValues:
                            sValue = UI.GetSnip(sValue, 64)
                        else:
                            sValue = UI.FixBreaks(sValue, "")

                    sHTML += "<div class=\"ui-widget-content ui-corner-tl ui-corner-bl parameter_value\">" + sValue + "</div>"

            sHTML += "</div>"
            sHTML += "</div>"
    
    return sHTML
    
def BuildReadOnlySteps(oTask, sCodeblockName):
    try:
        sHTML = ""

        if oTask.Codeblocks[sCodeblockName].Steps:
            for order, oStep in oTask.Codeblocks[sCodeblockName].Steps.iteritems():
                UI.log("Building %s - %d : %s" % (sCodeblockName, order, oStep.FunctionName), 4)
                sHTML += DrawReadOnlyStep(oStep, True)
        else:
            sHTML = "<li class=\"no_step\">No Commands defined for this Codeblock.</li>"
        
        return sHTML
    except Exception:
        UI.log_nouser(traceback.format_exc(), 0)

