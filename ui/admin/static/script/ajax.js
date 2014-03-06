//Copyright 2012 Cloud Sidekick
//
//Licensed under the Apache License, Version 2.0 (the "License");
//you may not use this file except in compliance with the License.
//You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
//Unless required by applicable law or agreed to in writing, software
//distributed under the License is distributed on an "AS IS" BASIS,
//WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//See the License for the specific language governing permissions and
//limitations under the License.
//

/*
 * This file is used by most pages.  It contains the specific AJAX calls to get data.
 *
 * The individual pages have code to consume that data as needed.
 *
 */

catoAjax.saveSettings = function(type, values) {"use strict";
	var args = {};
	args.module = type;
	args.settings = values;
	return ajaxPost("uiMethods/wmSaveSettings", args);
};

catoAjax.getCloudAccountsForHeader = function(selected) {"use strict";
	var args = {};
	args.sSelected = selected;
	// NOTE: This is not async for a reason - other 'page load' ajax calls depend on it.
	return ajaxPost("uiMethods/wmGetCloudAccountsForHeader", args, "html");
};

catoAjax.getProcessLogfile = function(component) {"use strict";
	var args = {};
	args.component = component;
	return ajaxPost("uiMethods/wmGetProcessLogfile", args, "text");
};

catoAjax.getLog = function(args) {"use strict";
	return ajaxPost("uiMethods/wmGetLog", args);
};

// TASK SPECIFIC FUNCTIONS
catoAjax.task = function() {
};

catoAjax.task.getTaskStatusCounts = function() {"use strict";
	return ajaxPost("taskMethods/wmGetTaskStatusCounts");
};

catoAjax.task.getTaskInstances = function() {"use strict";
	return ajaxPost("taskMethods/wmGetTaskInstances", args, "html");
};
// Deployment SPECIFIC FUNCTIONS
catoAjax.deployment = function() {
};

catoAjax.deployment.getTemplatesTable = function(filter, page) {"use strict";
	var args = {};
	args.sSearch = filter;
	args.sPage = page;
	return ajaxPost("depMethods/wmGetTemplatesTable", args);
};

catoAjax.deployment.deleteTemplates = function(template_list) {"use strict";
	var args = {};
	args.sDeleteArray = template_list;
	return ajaxPost("depMethods/wmDeleteTemplates", args);
};

catoAjax.deployment.getTemplateFromURL = function(url) {"use strict";
	var args = {};
	args.sURL = url;
	return ajaxPost("depMethods/wmGetTemplateFromURL", args);
};

catoAjax.deployment.getTemplate = function(id) {"use strict";
	var args = {};
	args.id = id;
	return ajaxPost("depMethods/wmGetTemplate", args);
};

catoAjax.deployment.getTemplateDeployments = function(id) {"use strict";
	var args = {};
	args.template_id = id;
	return ajaxPost("depMethods/wmGetTemplateDeployments", args, "html");
};

catoAjax.deployment.createTemplate = function(args) {"use strict";
	return ajaxPost("depMethods/wmCreateTemplate", args);
};

catoAjax.deployment.updateTemplateDetail = function(args) {"use strict";
	return ajaxPost("depMethods/wmUpdateTemplateDetail", args);
};

catoAjax.deployment.validateTemplate = function(template) {"use strict";
	var args = {};
	args.template = template;
	return ajaxPost("depMethods/wmValidateTemplate", args);
};
// TAG SPECIFIC FUNCTIONS
catoAjax.tags = function() {
};

catoAjax.tags.getTagsTable = function(filter, page) {"use strict";
	var args = {};
	args.sFilter = filter;
	args.sPage = page;
	return ajaxPost("tagMethods/wmGetTagsTable", args);
};

catoAjax.tags.getTagList = function(object_id) {"use strict";
	var args = {};
	args.sObjectID = object_id;
	return ajaxPost("tagMethods/wmGetTagList", args, "html");
};

catoAjax.tags.getObjectsTags = function(object_id) {"use strict";
	var args = {};
	args.sObjectID = object_id;
	return ajaxPost("tagMethods/wmGetObjectsTags", args, "html");
};

catoAjax.tags.addObjectTag = function(object_id, object_type, tag_name) {"use strict";
	var args = {};
	args.sObjectID = object_id;
	args.sObjectType = object_type;
	args.sTagName = tag_name;
	return ajaxPost("tagMethods/wmAddObjectTag", args);
};

catoAjax.tags.removeObjectTag = function(object_id, object_type, tag_name) {"use strict";
	var args = {};
	args.sObjectID = object_id;
	args.sObjectType = object_type;
	args.sTagName = tag_name;
	return ajaxPost("tagMethods/wmRemoveObjectTag", args);
};

catoAjax.tags.createTag = function(tag_name, desc) {"use strict";
	var args = {};
	args.sTagName = tag_name;
	args.sDescription = desc;
	return ajaxPost("tagMethods/wmCreateTag", args);
};

catoAjax.tags.updateTag = function(tag_name, new_name, desc) {"use strict";
	var args = {};
	args.sTagName = tag_name;
	args.sNewTagName = new_name;
	args.sDescription = desc;
	return ajaxPost("tagMethods/wmUpdateTag", args);
};

catoAjax.tags.deleteTags = function(taglist) {"use strict";
	var args = {};
	args.sDeleteArray = taglist;
	return ajaxPost("tagMethods/wmDeleteTags", args);
};
