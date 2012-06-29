
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
 
#these globals are set on init, and anything that imports this file
# has access to these objects

# the web.py "web" object
web = None
# web.py "session"
session = None
# Cato Service "server" is the running Cato service
server = None
# config is the configuration loaded from cato.conf (via catocommon) when the service started
config = None
# this is the root path for the web files
web_root = None

# the debug level (0-4 with 0 being 'none' and 4 being 'verbose')
debuglevel = 2 #defaults to 2

ConnectionTypes = ["ssh - ec2", "ssh", "telnet", "mysql", "oracle", "sqlserver", "sybase", "informix"]
   
class SecurityLogTypes(object):
    Object = "Object"
    Security = "Security"
    Usage = "Usage"
    Other = "Other"
    
class SecurityLogActions(object):
    UserLogin = "UserLogin"
    UserLogout = "UserLogout"
    UserLoginAttempt = "UserLoginAttempt"
    UserPasswordChange = "UserPasswordChange"
    UserSessionDrop = "UserSessionDrop"
    SystemLicenseException = "SystemLicenseException"
    
    ObjectAdd = "ObjectAdd"
    ObjectModify = "ObjectModify"
    ObjectDelete = "ObjectDelete"
    ObjectView = "ObjectView"
    ObjectCopy = "ObjectCopy"
    
    PageView = "PageView"
    ReportView = "ReportView"
    
    APIInterface = "APIInterface"
    
    Other = "Other"
    ConfigChange = "ConfigChange"

class CatoObjectTypes(object):
    NA = 0
    User = 1
    Asset = 2
    Task = 3
    Schedule = 4
    Registry = 6
    Tag = 7
    MessageTemplate = 18
    Parameter = 34
    Credential = 35
    Domain = 36
    CloudAccount = 40
    Cloud = 41
    Ecosystem = 50
    EcoTemplate = 51

RoleMethods = {
    "/cloudAccountEdit" : ["Developer"],
    "/cloudDiscovery" : ["Developer"],
    "/cloudEdit" : ["Developer"],
    "/credentialEdit" : ["Developer"],
    "/ecoTemplateEdit" : ["Developer"],
    "/ecoTemplateManage" : ["Developer"],
    "/ecosystemEdit" : True,
    "/ecosystemManage" : True,
    "/home" : True,
    "/importObject" : ["Developer"],
    "/settings" : ["Developer"],
    "/systemStatus" : ["Developer"],
    "/taskActivityLog" : True,
    "/taskEdit" : ["Developer"],
    "/taskManage" : ["Developer"],
    "/taskPrint" : ["Developer"],
    "/taskRunLog" : ["Developer"],
    "/taskStatus" : True,
    "/taskView" : ["Developer"],
    "/upload" : ["Developer"],
    "/uiMethods/wmGetMenu" : True,
    "/uiMethods/wmAddRegistryNode" : ["Developer"],
    "/uiMethods/wmAssetSearch" : ["Developer"],
    "/uiMethods/wmCreateAsset" : ["Developer"],
    "/uiMethods/wmCreateCredential" : ["Developer"],
    "/uiMethods/wmCreateObjectFromXML" : ["Developer"],
    "/uiMethods/wmDeleteActionPlan" : ["Developer"],
    "/uiMethods/wmDeleteAssets" : ["Developer"],
    "/uiMethods/wmDeleteCredentials" : ["Developer"],
    "/uiMethods/wmDeleteRegistryNode" : ["Developer"],
    "/uiMethods/wmDeleteSchedule" : ["Developer"],
    "/uiMethods/wmGetActionPlans" : ["Developer"],
    "/uiMethods/wmGetActionSchedules" : ["Developer"],
    "/uiMethods/wmGetAsset" : ["Developer"],
    "/uiMethods/wmGetAssetsTable" : ["Developer"],
    "/uiMethods/wmGetCloudAccountsForHeader" : True,
    "/uiMethods/wmGetCredential" : ["Developer"],
    "/uiMethods/wmGetCredentialsJSON" : ["Developer"],
    "/uiMethods/wmGetCredentialsTable" : ["Developer"],
    "/uiMethods/wmGetDBInfo" : ["Developer"],
    "/uiMethods/wmGetDatabaseTime" : True,
    "/uiMethods/wmGetGettingStarted" : ["Developer"],
    "/uiMethods/wmGetLog" : ["Developer"],
    "/uiMethods/wmGetMenu" : True,
    "/uiMethods/wmGetMyAccount" : True,
    "/uiMethods/wmGetObjectsTags" : ["Developer"],
    "/uiMethods/wmGetProcessLogfile" : ["Developer"],
    "/uiMethods/wmGetRecurringPlan" : ["Developer"],
    "/uiMethods/wmGetRegistry" : ["Developer"],
    "/uiMethods/wmGetSettings" : ["Developer"],
    "/uiMethods/wmGetSystemStatus" : ["Developer"],
    "/uiMethods/wmGetVersion" : True,
    "/uiMethods/wmHTTPGet" : True,
    "/uiMethods/wmRunLater" : ["Developer"],
    "/uiMethods/wmRunRepeatedly" : ["Developer"],
    "/uiMethods/wmSaveMyAccount" : True,
    "/uiMethods/wmSavePlan" : ["Developer"],
    "/uiMethods/wmSaveSchedule" : ["Developer"],
    "/uiMethods/wmSaveSettings" : ["Developer"],
    "/uiMethods/wmSetApplicationSetting" : ["Developer"],
    "/uiMethods/wmUpdateAsset" : ["Developer"],
    "/uiMethods/wmUpdateCredential" : ["Developer"],
    "/uiMethods/wmUpdateRegistryValue" : ["Developer"],
    "/taskMethods/wmAddCodeblock" : ["Developer"],
    "/taskMethods/wmAddEmbeddedCommandToStep" : ["Developer"],
    "/taskMethods/wmAddStep" : ["Developer"],
    "/taskMethods/wmApproveTask" : ["Developer"],
    "/taskMethods/wmCopyCodeblockStepsToClipboard" : ["Developer"],
    "/taskMethods/wmCopyStepToClipboard" : ["Developer"],
    "/taskMethods/wmCopyTask" : ["Developer"],
    "/taskMethods/wmCreateNewTaskVersion" : ["Developer"],
    "/taskMethods/wmCreateTask" : ["Developer"],
    "/taskMethods/wmDeleteCodeblock" : ["Developer"],
    "/taskMethods/wmDeleteStep" : ["Developer"],
    "/taskMethods/wmDeleteTaskParam" : ["Developer"],
    "/taskMethods/wmDeleteTasks" : ["Developer"],
    "/taskMethods/wmExportTasks" : ["Developer"],
    "/taskMethods/wmFnIfAddSection" : ["Developer"],
    "/taskMethods/wmFnNodeArrayAdd" : ["Developer"],
    "/taskMethods/wmGetAccountEcosystems" : ["Developer"],
    "/taskMethods/wmGetClips" : ["Developer"],
    "/taskMethods/wmGetCodeblocks" : ["Developer"],
    "/taskMethods/wmGetCommands" : ["Developer"],
    "/taskMethods/wmGetMergedParameterXML" : ["Developer"],
    "/taskMethods/wmGetObjectParameterXML" : ["Developer"],
    "/taskMethods/wmGetParameterXML" : ["Developer"],
    "/taskMethods/wmGetParameters" : ["Developer"],
    "/taskMethods/wmGetStep" : ["Developer"],
    "/taskMethods/wmGetStepVarsEdit" : ["Developer"],
    "/taskMethods/wmGetSteps" : ["Developer"],
    "/taskMethods/wmGetStepsPrint" : ["Developer"],
    "/taskMethods/wmGetTask" : ["Developer"],
    "/taskMethods/wmGetTaskCodeFromID" : ["Developer"],
    "/taskMethods/wmGetTaskCodeblockPicker" : ["Developer"],
    "/taskMethods/wmGetTaskConnections" : ["Developer"],
    "/taskMethods/wmGetTaskInstances" : True,
    "/taskMethods/wmGetTaskLogfile" : ["Developer"],
    "/taskMethods/wmGetTaskParam" : ["Developer"],
    "/taskMethods/wmGetTaskRunLog" : ["Developer"],
    "/taskMethods/wmGetTaskRunLogDetails" : ["Developer"],
    "/taskMethods/wmGetTaskStatusCounts" : True,
    "/taskMethods/wmGetTaskVarPickerPopup" : ["Developer"],
    "/taskMethods/wmGetTaskVersions" : ["Developer"],
    "/taskMethods/wmGetTaskVersionsDropdown" : ["Developer"],
    "/taskMethods/wmGetTasksTable" : ["Developer"],
    "/taskMethods/wmRemoveFromClipboard" : ["Developer"],
    "/taskMethods/wmRemoveNodeFromStep" : ["Developer"],
    "/taskMethods/wmRenameCodeblock" : ["Developer"],
    "/taskMethods/wmReorderSteps" : ["Developer"],
    "/taskMethods/wmRunTask" : ["Developer"],
    "/taskMethods/wmSaveDefaultParameterXML" : ["Developer"],
    "/taskMethods/wmStopTask" : ["Developer"],
    "/taskMethods/wmTaskSearch" : ["Developer"],
    "/taskMethods/wmTaskSetDefault" : ["Developer"],
    "/taskMethods/wmToggleStep" : ["Developer"],
    "/taskMethods/wmToggleStepCommonSection" : ["Developer"],
    "/taskMethods/wmToggleStepSkip" : ["Developer"],
    "/taskMethods/wmUpdateStep" : ["Developer"],
    "/taskMethods/wmUpdateTaskDetail" : ["Developer"],
    "/taskMethods/wmUpdateTaskParam" : ["Developer"],
    "/taskMethods/wmUpdateVars" : ["Developer"],
    "/ecoMethods/wmAddEcosystemObjects" : ["Developer"],
    "/ecoMethods/wmAddEcotemplateAction" : ["Developer"],
    "/ecoMethods/wmCallStormAPI" : True,
    "/ecoMethods/wmCopyEcotemplate" : ["Developer"],
    "/ecoMethods/wmCreateEcosystem" : True,
    "/ecoMethods/wmCreateEcotemplate" : ["Developer"],
    "/ecoMethods/wmDeleteEcosystemObject" : True,
    "/ecoMethods/wmDeleteEcosystems" : True,
    "/ecoMethods/wmDeleteEcotemplateAction" : ["Developer"],
    "/ecoMethods/wmDeleteEcotemplates" : ["Developer"],
    "/ecoMethods/wmGetActionIcons" : ["Developer"],
    "/ecoMethods/wmGetEcosystem" : True,
    "/ecoMethods/wmGetEcosystemObjectByType" : True,
    "/ecoMethods/wmGetEcosystemObjects" : True,
    "/ecoMethods/wmGetEcosystemPlans" : True,
    "/ecoMethods/wmGetEcosystemSchedules" : True,
    "/ecoMethods/wmGetEcosystemStormStatus" : True,
    "/ecoMethods/wmGetEcosystemsJSON" : True,
    "/ecoMethods/wmGetEcosystemsTable" : True,
    "/ecoMethods/wmGetEcotemplate" : ["Developer"],
    "/ecoMethods/wmGetEcotemplateAction" : ["Developer"],
    "/ecoMethods/wmGetEcosystemActionButtons" : True,
    "/ecoMethods/wmGetEcosystemActionCategories" : True,
    "/ecoMethods/wmGetEcotemplateActions" : ["Developer"],
    "/ecoMethods/wmGetEcotemplateEcosystems" : ["Developer"],
    "/ecoMethods/wmGetEcotemplateStorm" : ["Developer"],
    "/ecoMethods/wmGetEcotemplateStormParameterXML" : ["Developer"],
    "/ecoMethods/wmGetEcotemplatesJSON" : ["Developer"],
    "/ecoMethods/wmGetEcotemplatesTable" : ["Developer"],
    "/ecoMethods/wmGetStormFileFromURL" : True,
    "/ecoMethods/wmUpdateEcoTemplateAction" : ["Developer"],
    "/ecoMethods/wmUpdateEcosystemDetail" : True,
    "/ecoMethods/wmUpdateEcotemplateDetail" : ["Developer"],
    "/ecoMethods/wmUpdateEcotemplateStorm" : ["Developer"],
    "/cloudMethods/wmDeleteAccounts" : ["Developer"],
    "/cloudMethods/wmDeleteClouds" : ["Developer"],
    "/cloudMethods/wmGetCloud" : ["Developer"],
    "/cloudMethods/wmGetCloudAccount" : ["Developer"],
    "/cloudMethods/wmGetCloudAccountsJSON" : ["Developer"],
    "/cloudMethods/wmGetCloudAccountsTable" : ["Developer"],
    "/cloudMethods/wmGetCloudsTable" : ["Developer"],
    "/cloudMethods/wmGetKeyPairs" : ["Developer"],
    "/cloudMethods/wmGetProvider" : ["Developer"],
    "/cloudMethods/wmGetProvidersList" : ["Developer"],
    "/cloudMethods/wmSaveAccount" : ["Developer"],
    "/cloudMethods/wmSaveCloud" : ["Developer"]
}

#    "/uiMethods/GET" : ["Developer"],
#    "/uiMethods/POST" : ["Developer"],
#    "/taskMethods/GET" : ["Developer"],
#    "/taskMethods/POST" : ["Developer"],
#    "/ecoMethods/GET" : ["Developer"],
#    "/ecoMethods/POST" : ["Developer"],
#    "/cloudMethods/GET" : ["Developer"],
#    "/cloudMethods/POST" : ["Developer"],

            