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

$(document).ready(function () {
    $("#skip_registration_btn").live("click", function () {
		var success = updateSetting("general","register_cato","skipped");
		if (success)
		{
			$("#registercato").remove();
		}
    });

	$("#getting_started_items").load("uiMethods/wmGetGettingStarted", function(responseText) {
		if (responseText) {
			$("#getting_started_message").show();
		}
	});
});
