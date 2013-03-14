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
catoAjax.getConfig = function(username) {"use strict";
	var args = {};
	return ajaxPost("uiMethods/wmGetConfig", args);
}

catoAjax.getQuestion = function(username) {"use strict";
	var args = {};
	args.username = username;
	return ajaxPost("uiMethods/wmGetQuestion", args);
}

// TAG SPECIFIC FUNCTIONS
catoAjax.tags = function() {
	// a class for tagging specific calls
}

catoAjax.tags.getTagsTable = function(filter, page) {"use strict";
	var args = {};
	args.sFilter = filter;
	args.sPage = page;
	return ajaxPost("tagMethods/wmGetTagsTable", args);
}

catoAjax.tags.getTagList = function(object_id) {"use strict";
	var args = {};
	args.sObjectID = object_id;
	return ajaxPost("tagMethods/wmGetTagList", args, "html");
}

catoAjax.tags.getObjectsTags = function(object_id) {"use strict";
	var args = {};
	args.sObjectID = object_id;
	return ajaxPost("tagMethods/wmGetObjectsTags", args, "html");
}

catoAjax.tags.addObjectTag = function(object_id, object_type, tag_name) {"use strict";
	var args = {};
	args.sObjectID = object_id;
	args.sObjectType = object_type;
	args.sTagName = tag_name;
	return ajaxPost("tagMethods/wmAddObjectTag", args);
}

catoAjax.tags.removeObjectTag = function(object_id, object_type, tag_name) {"use strict";
	var args = {};
	args.sObjectID = object_id;
	args.sObjectType = object_type;
	args.sTagName = tag_name;
	return ajaxPost("tagMethods/wmRemoveObjectTag", args);
}

catoAjax.tags.createTag = function(tag_name, desc) {"use strict";
	var args = {};
	args.sTagName = tag_name;
	args.sDescription = desc;
	return ajaxPost("tagMethods/wmCreateTag", args);
}

catoAjax.tags.updateTag = function(tag_name, new_name, desc) {"use strict";
	var args = {};
	args.sTagName = tag_name;
	args.sNewTagName = new_name;
	args.sDescription = desc;
	return ajaxPost("tagMethods/wmUpdateTag", args);
}

catoAjax.tags.deleteTags = function(taglist) {"use strict";
	var args = {};
	args.sDeleteArray = taglist;
	return ajaxPost("tagMethods/wmDeleteTags", args);
}

/*
 * This generic function is used by anything that needs to do an AJAX POST
 * to get back a JSON object.
 *
 * the datatype defaults to json unless explicitly set
 * if explicitly set, must be html, text or xml
 */
function ajaxPost(apiurl, args, datatype, synchronous) {"use strict";
	datatype = typeof datatype !== 'undefined' ? datatype : 'json';
	synchronous = typeof synchronous !== 'undefined' ? synchronous : false;

	// args: a javascript object
	// url: the url of the web api call
	var result;
	$.ajax({
		async : synchronous,
		type : "POST",
		url : apiurl,
		data : JSON.stringify(args),
		contentType : "application/json; charset=utf-8",
		dataType : datatype,
		success : function(response) {
			result = response;
		},
		error : function(response) {
			// if something goes wrong on the server, many times the response will be "None" or "internal server error"
			// trap these two with a nicer error message
			if (response.responseText == "None" || response.status == 500) {
				//only show info, as the real message will already be in the server log
				showInfo("An exception occurred - please check the server logfiles for details.");
			} else {
				showAlert(response.responseText);
			}
		}
	});
	return result;
}

/*
 * This generic function is used by anything that needs to do an AJAX GET
 * to get back a JSON object.
 *
 * the datatype defaults to json unless explicitly set
 * if explicitly set, must be html, text or xml
 */
function ajaxGet(apiurl, datatype) {"use strict";
	datatype = typeof datatype !== 'undefined' ? datatype : 'json';

	// url: the url of the web api call
	var result;
	$.ajax({
		type : "GET",
		url : apiurl,
		contentType : "application/json; charset=utf-8",
		dataType : datatype,
		success : function(response) {
			result = response;
		},
		error : function(response) {
			showAlert(response.responseText);
		}
	});
	return result;
}

