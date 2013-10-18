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
 * This file is used by most pages.  IT contains the specific AJAX calls to get data.
 *
 * The individual pages have code to consume that data as needed.
 *
 */

function catoAjax() {
	// just the catoAjax object.
	// might get some properties in the future.
}

// Class methods.
catoAjax.getConfig = function() {"use strict";
	var args = {};
	return ajaxPost("uiMethods/wmGetConfig", args);
};

catoAjax.getSettings = function() {"use strict";
	return ajaxPost("uiMethods/wmGetSettings");
};

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

catoAjax.saveMyAccount = function(values) {"use strict";
	var args = {};
	args.sValues = values;
	return ajaxPost("uiMethods/wmSaveMyAccount", args);
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
/*
 * This generic function is used by anything that needs to do an AJAX POST
 * to get back a JSON object.
 *
 * the datatype defaults to json unless explicitly set
 * if explicitly set, must be html, text or xml
 */
function ajaxPost(apiurl, args, datatype) {"use strict";
	datatype = typeof datatype !== 'undefined' ? datatype : 'json';

	// args: a javascript object
	// url: the url of the web api call
	var result;
	$.ajax({
		async : false,
		type : "POST",
		url : apiurl,
		data : JSON.stringify(args),
		contentType : "application/json; charset=utf-8",
		dataType : datatype,
		success : function(response) {
			result = response;
		},
		error : ajaxErrorCallback
	});
	return result;
}

function ajaxPostAsync(apiurl, args, on_success, datatype) {"use strict";
	// this method is like the ajaxGet - it's asynchronous.
	// which means, the only way to handle it's results is by providing
	// an on_success function.
	datatype = typeof datatype !== 'undefined' ? datatype : 'json';

	$.ajax({
		async : false,
		type : "POST",
		url : apiurl,
		data : JSON.stringify(args),
		contentType : "application/json; charset=utf-8",
		dataType : datatype,
		success : function(response) {
			if ( typeof (on_success) != 'undefined') {
				on_success(response);
			}
		},
		error : ajaxErrorCallback
	});
}

/*
 * This generic function is used by anything that needs to do an AJAX GET
 * to get back a JSON object.
 *
 * the datatype defaults to json unless explicitly set
 * if explicitly set, must be html, text or xml
 */
function ajaxGet(apiurl, on_success, datatype) {"use strict";
	// NOTE: this get type takes an on_success() function.
	// async calls can't return values --- there's no telling when they'll be done.
	// but when it is done, we'll call the on_success function!
	datatype = typeof datatype !== 'undefined' ? datatype : 'json';

	$.ajax({
		type : "GET",
		url : apiurl,
		contentType : "application/json; charset=utf-8",
		dataType : datatype,
		success : function(response) {
			if ( typeof (on_success) != 'undefined') {
				on_success(response);
			}
		},
		error : ajaxErrorCallback
	});
}

ajaxErrorCallback = function(response) {
	var method = response.getResponseHeader("X-CSK-Method");
	if (response.status == 500) {
		//only show info, as the real message will already be in the server log
		showInfo("An exception occurred - please check the server logfiles for details. (500)", method);
	} else if (response.status == 280) {
		// 280 is our custom response code to indicate we want an 'info' message
		showInfo(response.responseText);
	} else if (response.status == 480) {
		// 480 is our custom 'session error' response code ... lock it down
		msg = (response.responseText) ? response.responseText : "Your session has ended or been terminated.";
		lockDown(msg);
	} else {
		msg = (response.responseText == "None") ? "Expected a response and got 'None'." : response.responseText;
		showAlert(msg, method);
	}

	// these might be necessary in many places
	hidePleaseWait();
	$("#update_success_msg").fadeOut(2000);
};
