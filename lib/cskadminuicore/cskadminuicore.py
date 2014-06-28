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
This module contains all the core features of the 'flow' ui
"""

from catoconfig import catoconfig

from catolog import catolog
import web
import os
import sys
import json

if "CSK_HOME" not in os.environ:
    raise Exception("CSK_HOME environment variable not set.")
sys.path.insert(0, os.path.join(os.environ["CSK_HOME"], "cato", "lib"))
web_root = os.path.join(os.environ["CSK_HOME"], "cato", "ui", "admin")

from catocommon import catocommon
from catoui import uiGlobals, uiCommon
from taskMethods import taskMethods


"""
 wmHandler is the default handler for any urls not defined in the urls mapping below.
 (web.py required explicit url mapping)

 web.py will instantiate this class, and invoke either the GET or POST method.

 We take it from there (in catocommon), parse the URI, and try to load the right module
 and find the proper function to handle the request.
"""


class wmHandler:
    # the GET and POST methods here are hooked by web.py.
    # whatever method is requested, that function is called.
    def GET(self, method):
        web.header('X-CSK-Method', method)
        return catocommon.FindAndCall("cskadminuicore." + method)

    def POST(self, method):
        web.header('X-CSK-Method', method)
        return catocommon.FindAndCall("cskadminuicore." + method)


class getlog():
    """
    delivers an html page with a refresh timer.  content is the last n rows of the logfile
    """
    def GET(self):
        return uiCommon.GetLog()


class recache():
    """
    rebuilds the UI cached html (commands, menu)
    for CSK development/support
    """
    def GET(self):
        user_role = uiCommon.GetSessionUserRole()
        if user_role != "Administrator":
            raise Exception("Only Administrators can refresh the UI cache.")
        _build_ui_cache()
        return "Cache successfully refreshed."


# the default page if no URI is given, just an information message
class index:
    def GET(self):
        return render.home()


class home:
    """
    We have a POST handler here, because the login screen does a post after auth...
        (this is so browsers will offer to remember passwords, even tho our auth is ajax.)

    But, when we get a POST, we do a redirect!  Why?  So refreshing the /home page
        won't nag about "are you sure you wanna resubmit this form.

    Why not do a GET login form?  Doh! The credentials would be on the querystring = bad.
    """
    def GET(self):
        return _inject(render.home())

    def POST(self):
        # finally, if the original, pre-login request was a specific path, 
        # go ahead and redirect to there, otherwise /home.
        path = uiGlobals.session.get("requested_path", "/home")
        raise web.seeother(path)


class settings:
    def GET(self):
        return render.settings()


class search:
    def GET(self):
        return render.search()


class assetEdit:
    def GET(self):
        return render.assetEdit()


class credentialEdit:
    def GET(self):
        return render.credentialEdit()


class tagEdit:
    def GET(self):
        return render.tagEdit()


class imageEdit:
    def GET(self):
        return render.imageEdit()


class userEdit:
    def GET(self):
        return render.userEdit()


class taskManage:
    def GET(self):
        return render.taskManage()


class taskEdit:
    def GET(self):
        # NOTE: Getting the task edit page has a safety check.
        # An "Approved" task cannot be opened in the editor... so...
        # we check the status here before doing anything, and redirect accordingly.
        i = web.input(task_id=None)
        if i.task_id:
            # do we have permission to see this task?
            allowed = taskMethods.IsTaskAllowed(i.task_id)
            if allowed:
                task_status = taskMethods.GetTaskStatus(i.task_id)
                if task_status == "Approved":
                    logger.warning("Attempt to explicitly access an Approved Task in the editor.")
                    return render.taskView()
                else:
                    return render.taskEdit()
            else:
                return render.notAllowed("Not allowed to manage this Task.")


class taskRunLog:
    def GET(self):
        return render_popup.taskRunLog()


class taskView:
    def GET(self):
        # NOTE: Getting the task edit page has a safety check.
        # An "Approved" task cannot be opened in the editor... so...
        # we check the status here before doing anything, and redirect accordingly.
        i = web.input(task_id=None)
        if i.task_id:
            # do we have permission to see this task?
            allowed = taskMethods.IsTaskAllowed(i.task_id)
            if allowed:
                return render.taskView()
            else:
                return render.notAllowed("Not allowed to manage this Task.")


class taskPrint:
    def GET(self):
        return render_popup.taskPrint()


class taskActivityLog:
    def GET(self):
        return render.taskActivityLog()


class cloudAccountEdit:
    def GET(self):
        return render.cloudAccountEdit()


class cloudEdit:
    def GET(self):
        return render.cloudEdit()


class cloudDiscovery:
    def GET(self):
        return render.cloudDiscovery()


class systemStatus:
    def GET(self):
        return render.systemStatus()


class taskStatus:
    def GET(self):
        return render.taskStatus()


class deploymentManage:
    def GET(self):
        return render.deploymentManage()


class deploymentEdit:
    def GET(self):
        return render.deploymentEdit()


class depTemplateManage:
    def GET(self):
        return render.depTemplateManage()


class depTemplateEdit:
    def GET(self):
        return render.depTemplateEdit()


class importObject:
    def GET(self):
        return render.importObject()


class upload:
    def GET(self):
        return """This endpoint only accepts POSTS from file_upload.html"""

    def POST(self):
        x = web.input(fupFile={}, ref_id="")
        if x:
            # print x # ref_id
            # web.debug(x['fupFile'].filename) # This is the filename
            # web.debug(x['fupFile'].value) # This is the file contents
            # web.debug(x['fupFile'].file.read()) # Or use a file(-like) object
            # raise web.seeother('/upload')

            ref_id = (x.ref_id if x.ref_id else "")
            filename = "%s-%s.tmp" % (uiCommon.GetSessionUserID(), ref_id)
            fullpath = os.path.join(catoconfig.CONFIG["tmpdir"], filename)
            with open(fullpath, 'w') as f_out:
                if not f_out:
                    logger.critical("Unable to open %s for writing." % fullpath)
                f_out.write(x["fupFile"].file.read())  # writes the uploaded file to the newly created file.

            # all done, we loop back to the file_upload.html page, but this time include
            # a qq arg - the file name
            raise web.seeother("static/pages/file_upload.html?ref_id=%s&filename=%s" % (ref_id, filename))


class appicon:
    def GET(self, name):
        img = uiCommon.GetAppIcon(name)
        web.header('Content-type', 'image/png')
        return img


def CacheTaskCommands():
    """
    Creates the html cache file for Task Command categories, functions and help.

    The loops build global html objects, which are ultimately written out to files.
    Even though the FunctionCategories class has a hierarchy, we are writing flat files.
    The browser will take care of showing things according to their hierarchy.
    """
    cathtml = ""
    funhtml = ""
    helphtml = ""

    # this internal def builds the html for a subcategory, and associates it's child functions with it
    # NOTE: the dubcats are in the categories file, but they are hidden and indented with css.
    def _build_subcategory(parent, subcat):
        return """<div class="category subcategory" id="cat_{0}_sub_{1}" name="{1}">
            <div class="ui-widget-content ui-corner-all command_item"">
                <img class="category_icon" src="{3}" alt="" />
                <span>{2}</span>
                <div class="hidden">{4}</div>
            </div>
        </div>""".format(parent.Name, subcat.Name, subcat.Label, subcat.Icon, subcat.Description)

    # this internal def builds the html for a single function
    def _build_func_html(parent, domparentid):
        helpout = ""
        funcout = """<div class="functions hidden" id="{0}_functions">""".format(domparentid)
        # now, let's work out the functions.
        # we can just draw them all... they are hidden and will display on the client as clicked
        for fn in parent.Functions:
            funcout += """
            <div class="ui-widget-content ui-corner-all command_item function" id="fn_{0}" name="fn_{0}">
            <img class="function_icon" src="{2}" alt="" />
            <span>{1}</span>
            <div class="funchelp hidden">{3}</div>
            </div>""".format(fn.Name, fn.Label, fn.Icon, fn.Description)

            helpout = """<div>
            <img src="{0}" alt="" style="height: 16px; width: 16px;" />
            <span style="font-weight: bold; padding-left: 10px;">{1} : {2}</span>
            </div>
            <div style="margin-top: 6px;">{3}</div>
            <hr />""".format(fn.Icon, fn.Category.Label, fn.Label, fn.Help)

        funcout += "</div>"

        return funcout, helpout

    # so, we will use the FunctionCategories class in the session that was loaded at login, and build the list items for the commands tab.
    cats = uiGlobals.FunctionCategories
    if not cats:
        logger.error("Task Function Categories class is not in the datacache.")
    else:
        for cat in cats.Categories:
            cathtml += """<div class="category" id="cat_{0}" name="{0}">
                <div class="ui-widget-content ui-corner-all command_item">
                    <img class="category_icon" src="{2}" alt="" />
                    <span>{1}</span>
                    <div class="cathelp hidden">{3}</div>
                </div>""".format(cat.Name, cat.Label, cat.Icon, cat.Description)

            # So... the category MIGHT have subcategories, which have functions.
            if cat.Subcategories:
                cathtml += """<div class="subcategories hidden">"""
                for subcat in cat.Subcategories:
                    cathtml += _build_subcategory(cat, subcat)

                    f, h = _build_func_html(subcat, "cat_%s_sub_%s" % (cat.Name, subcat.Name))
                    funhtml += f
                    helphtml += h
                cathtml += "</div>"
            cathtml += "</div>"

            # it can also have direct functions.
            f, h = _build_func_html(cat, "cat_%s" % (cat.Name))
            funhtml += f
            helphtml += h

    path = catoconfig.CONFIG["uicache"]

    with open("%s/_categories.html" % (path), 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_categories.html." % (path))
        f_out.write(cathtml)

    with open("%s/_functions.html" % (path), 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_functions.html." % (path))
        f_out.write(funhtml)

    with open("%s/_command_help.html" % (path), 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_command_help.html." % (path))
        f_out.write(helphtml)


def CacheMenu():
    with open(os.path.join(os.environ["CSK_HOME"], "cato", "lib", "cskadminuicore", "menu.json"), 'r') as f:
        menus = json.load(f)

    # so, we have the cato menu.  Are there any extensions with menu additions?
    # extensions and their paths are defined in config.
    for n, p in catoconfig.CONFIG["extensions"].iteritems():
        logger.debug("Looking for extension menus in [%s - %s]..." % (n, p))
        for root, subdirs, files in os.walk(p):
            for f in files:
                if f == "menu.json":
                    logger.debug("... found one! Loading...")

                    with open(os.path.join(p, f), 'r') as f:
                        extmenus = json.load(f)

                    # now, let's manipulate our menu
                    for extmenu in extmenus:
                        pos = extmenu.get("insert_at")
                        if pos is not None:
                            menus.insert(pos, extmenu)

    sAdminMenu = ""
    sDevMenu = ""
    sUserMenu = ""

    for menu in menus:
        sLabel = menu.get("label", "No Label Defined")
        sHref = " href=\"" + menu.get("href", "") + "\"" if menu.get("href") else ""
        sOnClick = " onclick=\"" + menu.get("onclick", "") + "\"" if menu.get("onclick") else ""
        sIcon = "<img src=\"" + menu.get("icon", "") + "\" alt=\"\" height=\"24px\" width=\"24px\" />" if menu.get("icon") else ""
        sTarget = " target=\"" + menu.get("target", "") + "\"" if menu.get("target") else ""
        sClass = menu.get("class", "")
        sRoles = menu.get("roles", "")

        sAdminItems = ""
        sDevItems = ""
        sUserItems = ""

        for item in menu.get("items", []):
            sItemLabel = item.get("label", "No Label Defined")
            sItemHref = " href=\"" + item.get("href", "") + "\"" if item.get("href") else ""
            sItemOnClick = " onclick=\"" + item.get("onclick", "") + "\"" if item.get("onclick") else ""
            sItemIcon = "<img src=\"" + item.get("icon", "") + "\" alt=\"\" height=\"24px\" width=\"24px\" />" if item.get("icon") else ""
            sItemTarget = " target=\"" + item.get("target", "") + "\"" if item.get("target") else ""
            sItemClass = item.get("class", "")
            sItemRoles = item.get("roles", "")

            sItem = "<li class=\"ui-widget-header %s\" style=\"cursor: pointer;\"><a %s %s %s> %s %s</a></li>" % (sItemClass, sItemOnClick, sItemHref, sItemTarget, sItemIcon, sItemLabel)

            sAdminItems += sItem

            if "all" in sItemRoles:
                sUserItems += sItem
                sDevItems += sItem
            else:
                if "user" in sItemRoles:
                    sUserItems += sItem
                if "developer" in sItemRoles:
                    sDevItems += sItem

        sUserItems = "<ul>%s</ul>" % sUserItems
        sDevItems = "<ul>%s</ul>" % sDevItems
        sAdminItems = "<ul>%s</ul>" % sAdminItems

        # cool use of .format :-)
        sMenu = "<li class=\"%s\" style=\"cursor: pointer;\"><a %s %s %s>%s %s</a>{0}</li>" % (sClass, sOnClick, sHref, sTarget, sIcon, sLabel)

        sAdminMenu += sMenu.format(sAdminItems)

        if "all" in sRoles:
            sUserMenu += sMenu.format(sUserItems)
            sDevMenu += sMenu.format(sDevItems)
        else:
            if "developer" in sRoles:
                sDevMenu += sMenu.format(sDevItems)
            if "user" in sRoles:
                sUserMenu += sMenu.format(sUserItems)

    path = catoconfig.CONFIG["uicache"]

    with open("%s/_amenu.html" % path, 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_amenu.html." % path)
        f_out.write(sAdminMenu)

    with open("%s/_dmenu.html" % path, 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_dmenu.html." % path)
        f_out.write(sDevMenu)

    with open("%s/_umenu.html" % path, 'w') as f_out:
        if not f_out:
            logger.error("Unable to create %s/_umenu.html." % path)
        f_out.write(sUserMenu)


def _build_ui_cache():
    # we need to build some static html here...
    # caching in the session is a bad idea, and this stuff very very rarely changes.
    # so, when the service is started it will update the files, and the ui
    # will simply pull in the files when requested.

    # put the task commands in a global for our lookups
    # and cache the html in a flat file
    logger.info("Reading configuration files and generating static html...")

    uiCommon.LoadTaskCommands()
    # rebuild the cache html files
    CacheTaskCommands()
    CacheMenu()


def _inject(templateobj):
    """
    We need to wrap each pages html with a middle 'wrapper' before inserting it into
    the main base page.
    
    So, we take the already rendered html, and do a final replacement on it.
    """
    templateobj["__body__"] = templateobj["__body__"].replace("<!--##FOOTER##-->", uiGlobals.static_content["automatefooter"])
    templateobj["__body__"] = templateobj["__body__"].replace("<!--##AFTER##-->", uiGlobals.static_content["automateafter"])
    return templateobj


# THE MAIN STUFF

logger = catolog.get_logger("csk_admin_ui")

uiGlobals.urls += (
    '/automate', 'cskadminuicore.cskadminuicore.home',
    '/automate/home', 'home',
    '/automate/importObject', 'importObject',
    '/automate/cloudEdit', 'cloudEdit',
    '/automate/cloudAccountEdit', 'cloudAccountEdit',
    '/automate/cloudDiscovery', 'cloudDiscovery',
    '/automate/taskEdit', 'taskEdit',
    '/automate/taskView', 'taskView',
    '/automate/taskPrint', 'taskPrint',
    '/automate/taskRunLog', 'taskRunLog',
    '/automate/taskActivityLog', 'taskActivityLog',
    '/automate/taskManage', 'taskManage',
    '/automate/systemStatus', 'systemStatus',
    '/automate/taskStatus', 'taskStatus',
    '/automate/deploymentEdit', 'deploymentEdit',
    '/automate/deploymentManage', 'deploymentManage',
    '/automate/depTemplateEdit', 'depTemplateEdit',
    '/automate/depTemplateManage', 'depTemplateManage',
    '/automate/userEdit', 'userEdit',
    '/automate/assetEdit', 'assetEdit',
    '/automate/tagEdit', 'tagEdit',
    '/automate/imageEdit', 'imageEdit',
    '/automate/credentialEdit', 'credentialEdit',
    '/automate/upload', 'upload',
    '/automate/search', 'search',
    '/automate/settings', 'settings',
    '/automate/recache', 'recache',
    '/automate/appicon/(.*)', 'appicon'
)

basetemplate = os.path.join(os.environ["CSK_HOME"], "cato", "ui", "cskui", "templates", "base")
render = web.template.render(os.path.join(web_root, "templates"), base=basetemplate)
render_plain = web.template.render(os.path.join(web_root, "templates"))
render_popup = web.template.render(os.path.join(web_root, "templates"), base='popup')


# these globals are read once when the process starts, and are used in each request
uiGlobals.static_content["automatefooter"] = uiCommon._loadfile(os.path.join(web_root, "static", "_footer.html"))
uiGlobals.static_content["automateafter"] = uiCommon._loadfile(os.path.join(web_root, "static", "_after.html"))
