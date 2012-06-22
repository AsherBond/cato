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

$(document).ready(function() {
	//buttons are defined here so they draw correctly
	$("#tag_add_btn").button({ icons: { primary: "ui-icon-plus"} });
	$("#tag_add_btn").live("click", function() {
		showInfo("Object tagging is available in Cato Enterprise.");
	});

	
	$.getScript("static/script/objectTag.js", function(data, textStatus, jqxhr) {});
});