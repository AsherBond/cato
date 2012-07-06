
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
 
try:
    import xml.etree.cElementTree as ET
except (AttributeError, ImportError):
    import xml.etree.ElementTree as ET
try:
    ET.ElementTree.iterfind
except AttributeError as ex:
    del(ET)
    import catoxml.etree.ElementTree as ET

from catocommon import catocommon
from catoui import uiCommon

class Registry(object):
    def __init__(self, object_id):
        self.xml_tree = None
        self.xml_text = None
        
        try:
            db = catocommon.new_conn()
            self.object_id = object_id
            
            if object_id:
                sSQL = "select registry_xml from object_registry where object_id = '%s'" % object_id
                self.xml_text = db.select_col_noexcep(sSQL)
                if db.error:
                    raise Exception("Error: Could not look up Registry XML." + db.error)
    
                if self.xml_text:
                    self.xml_tree = ET.fromstring(self.xml_text)
                else:
                    # if the object_id is a guid, it's an object registry:... add one if it's not there.
                    if uiCommon.IsGUID(object_id):
                        sSQL = "insert into object_registry values ('%s', '<registry />')" % object_id
                        if not db.exec_db_noexcep(sSQL):
                            raise Exception("Error: Could not create Registry." + db.error)
    
                        self.xml_tree = ET.fromstring("<registry />")
                        
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()

    def AddNode(self, xpath, name):
        try:
            if self.xml_tree is None:
                return False, "Registry object has no xml document."
            
            # if the xpath is "registry" or "" ... that's the root
            if xpath == "registry" or xpath == "":
                x_add_to = self.xml_tree
            else:
                x_add_to = self.xml_tree.find(xpath)
                
            if x_add_to is not None:
                x_add_to.append(ET.Element(name))

                # update the xml_text in case we intend to keep using this object
                self.xml_text = ET.tostring(self.xml_tree)
                
                result, msg = self.DBSave()
                if not result:
                    return False, msg
            else:
                return False, "Unable to add - path [%s] was not found in registry." % xpath
            
            return True, ""
        except Exception as ex:
            raise Exception(ex)
            
    def SetNodeText(self, xpath, value, encrypt):
        try:
            if self.xml_tree is None:
                return False, "Registry object has no xml document."
            
            # if the xpath is "registry" or "" ... can't delete the root element
            if xpath == "registry" or xpath == "":
                return False, "Cannot set text on the root registry element."
                
            x_to_set = self.xml_tree.find(xpath)
            if x_to_set is not None:
                # setting the text on an element clears any children
                # we don't allow mixed content
                x_to_set.clear()
                
                # should we encrypt
                if catocommon.is_true(encrypt):
                    value = catocommon.cato_encrypt(value)
                    #encrypting also sets an attribute defining the data as such
                    x_to_set.set("encrypt", encrypt)
                    
                x_to_set.text = (value.replace("\\","\\\\") if value is not None else "")

                # update the xml_text in case we intend to keep using this object
                self.xml_text = ET.tostring(self.xml_tree)
                
                result, msg = self.DBSave()
                if not result:
                    return False, msg
            else:
                return False, "Unable to update - path [%s] was not found in registry." % xpath
            
            return True, ""
        except Exception as ex:
            raise Exception(ex)
           
    def DeleteNode(self, xpath):
        try:
            if self.xml_tree is None:
                return False, "Registry object has no xml document."
            
            # if the xpath is "registry" or "" ... can't delete the root element
            if xpath == "registry" or xpath == "":
                return False, "Cannot delete the root registry element."
                
            x_to_delete = self.xml_tree.find(xpath)
            if x_to_delete is not None:
                # can't delete a node, need it's parent
                parent_map = dict((c, p) for p in self.xml_tree.getiterator() for c in p)
                x_parent = parent_map[x_to_delete]
                x_parent.remove(x_to_delete)

                # update the xml_text in case we intend to keep using this object
                self.xml_text = ET.tostring(self.xml_tree)
                
                result, msg = self.DBSave()
                if not result:
                    return False, msg
            else:
                return False, "Unable to add - path [%s] was not found in registry." % xpath
            
            return True, ""
        except Exception as ex:
            raise Exception(ex)
           
    def DBSave(self):
        try:
            db = catocommon.new_conn()

            sSQL = "update object_registry set registry_xml = '%s' where object_id = '%s'" % (catocommon.tick_slash(self.xml_text), self.object_id)
            if not db.exec_db_noexcep(sSQL):
                return False, "Error: Could not create Registry." + db.error
            
            return True, ""
        except Exception as ex:
            raise Exception(ex)
        finally:
            db.close()
           
         
    def DrawRegistryEditor(self):
        try:
            html = ""
            
            if self.xml_tree is not None:
                html += "<div class=\"ui-widget-content ui-corner-all registry\">"
                html += "<div class=\"ui-widget-header\" xpath=\"registry\">" # header

                html += "<div class=\"floatright\">" # step header icons

                html += "<span id=\"registry_refresh_btn\" class=\"pointer\">" \
                    "<img style=\"width:10px; height:10px;\" src=\"static/images/icons/reload_16.png\"" \
                    " alt=\"\" title=\"Refresh\" /></span>"

                html += "<span class=\"registry_node_add_btn pointer\"" \
                    " xpath=\"registry\">" \
                    "<img style=\"width:10px; height:10px;\" src=\"static/images/icons/edit_add.png\"" \
                    " alt=\"\" title=\"Add another...\" /></span>"

                html += "</div>" #end step header icons
                html += "<span>Registry</span>"
                html += "</div>" # end header
                
                html += "<div style=\"padding: 5px;\">"
                for xe in list(self.xml_tree):
                    html += self.DrawRegistryNode(xe, xe.tag)
                html += "</div>"

                html += "</div>"

            if not html:
                html = "Registry is empty."
            
            return html
        except Exception as ex:
            raise Exception(ex)

    def DrawRegistryNode(self, xeNode, sXPath):
        try:
            html = ""

            sNodeLabel = xeNode.tag
            dictNodes = {}

            # if a node has children we'll draw it with some hierarchical styling.
            # AND ALSO if it's editable, even if it has no children, we'll still draw it as a container.
            if len(xeNode) > 0:
                sGroupID = catocommon.new_guid()

                html += "<div class=\"ui-widget-content ui-corner-bottom registry_section\" id=\"" + sGroupID + "\">" # this section

                html += "  <div class=\"ui-state-default registry_section_header\" xpath=\"" + sXPath + "\">" # header
                html += "      <div class=\"registry_section_header_title editable\" id=\"" + catocommon.new_guid() + "\">" + sNodeLabel + "</div>"

                html += "<div class=\"registry_section_header_icons\">" # step header icons

                html += "<span class=\"registry_node_add_btn pointer\"" \
                    " xpath=\"" + sXPath + "\">" \
                    "<img style=\"width:10px; height:10px;\" src=\"static/images/icons/edit_add.png\"" \
                    " alt=\"\" title=\"Add another...\" /></span>"

                html += "<span class=\"ui-icon ui-icon-close forceinline registry_node_remove_btn pointer\" xpath_to_delete=\"" + sXPath + "\" id_to_remove=\"" + sGroupID + "\" title=\"Remove\"></span>"

                html += "</div>" #end step header icons



                html += "  </div>" # end header

                
                for xeChildNode in list(xeNode):
                    sChildNodeName = xeChildNode.tag
                    sChildXPath = sXPath + "/" + xeChildNode.tag

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

                    html += self.DrawRegistryNode(xeChildNode, sChildXPath)

                html += "</div>" # end section
            else:
                html += self.DrawRegistryItem(xeNode, sXPath)

            return html

        except Exception as ex:
            raise Exception(ex)
        
    def DrawRegistryItem(self, xe, sXPath):
        try:  
            html = ""

            sEncrypt = xe.get("encrypt", "false")

            # if the node value is empty or encrypted, we still need something to click on to edit the value
            # if the value length after trimming is 0, 
            # it only has nonprintable chars in it.  So, it's empty as far as we are concerned.
            if xe.text is not None:
                sNodeValue = (xe.text if len(xe.text.strip()) > 0 else "(empty)")
            else:
                sNodeValue = "(empty)"
            # encrypted placeholder
            if sEncrypt == "true":
                sNodeValue = "(********)"
            # safe for html display
            sNodeValue = uiCommon.SafeHTML(sNodeValue)
            
            sNodeLabel = xe.tag
            sGroupID = catocommon.new_guid()

            html += "<div class=\"ui-widget-content ui-corner-tl ui-corner-bl registry_node\" xpath=\"" + sXPath + "\" id=\"" + sGroupID + "\">"
            html += "<span class=\"registry_node_label editable\" id=\"" + catocommon.new_guid() + "\">" + sNodeLabel + \
                "</span> : <span class=\"registry_node_value editable\" id=\"" + catocommon.new_guid() + "\" encrypt=\"" + sEncrypt + "\">" + sNodeValue + "</span>\n"

            html += "<div class=\"registry_section_header_icons\">" # step header icons

            html += "<span class=\"registry_node_add_btn pointer\"" \
                " xpath=\"" + sXPath + "\">" \
                "<img style=\"width:10px; height:10px;\" src=\"static/images/icons/edit_add.png\"" \
                " alt=\"\" title=\"Add another...\" /></span>"

            html += "<span class=\"ui-icon ui-icon-close forceinline registry_node_remove_btn pointer\" xpath_to_delete=\"" + sXPath + "\" id_to_remove=\"" + sGroupID + "\" title=\"Remove\"></span>"

            html += "</div>"
            html += "</div>"

            return html

        except Exception as ex:
            raise Exception(ex)
        

