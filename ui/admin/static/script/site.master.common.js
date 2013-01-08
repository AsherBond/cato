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

// These elements need to be at the bottom of EVERY PAGE
var d = '<!-- This is the popup error message dialog template.  -->' +
    '<div id="error_dialog" title="Error" class="ui-state-error">' +
    '<p>' +
    '    <span class="ui-icon ui-icon-alert" style="float: left; margin: 0 7px 50px 0;"></span>' +
    '    <span id="error_dialog_message"></span>' +
    '</p>' +
    '<p>' +
    '    <span id="error_dialog_info"></span>' +
    '</p>' +
    '<div id="stack_trace" class="hidden">' +
    '	<p class="clearfloat">' +
    '		<span id="show_stack_trace" class="ui-icon ui-icon-triangle-1-e" style="float: left; margin: 0 7px 50px 0;"></span>Show Details' +
    '	</p>' +
    '	<p class="ui-widget-content ui-corner-bottom ui-state-error hidden" style="overflow: auto; padding: 4px; font-size: .7em; margin-top:10px;">' +
    '    	Stack Trace: <br />' +
    '		<span id="error_dialog_trace"></span>' +
    '	</p>' +
    '</div>' +
    '</div>' +
    '<!-- End popup error message dialog template.  -->' +
    '<!-- This is the popup informational message template. -->' +
    '<div id="info_dialog" title="Info" class="ui-state-highlight">' +
    '<p>' +
    '    <span class="ui-icon ui-icon-info" style="float: left; margin: 0 7px 50px 0;"></span>' +
    '    <span id="info_dialog_message"></span>' +
    '</p>' +
    '<br />' +
    '<p>' +
    '    <span id="info_dialog_info"></span>' +
    '</p>' +
    '</div>' +
	'<!-- End popup informational message template. -->' +
    '<!-- This is the popup "about" dialog. -->' +
    '<div id="about_dialog" title="About Cato" class="ui-state-highlight">' +
    '<p>' +
    '    <span class="ui-icon ui-icon-info" style="float: left; margin: 0 7px 0px 0;"></span>' +
    '    <span id="app_name">Cloud Sidekick Cato</span><br /><br />' +
    '    <b>On the Web: </b><span id="app_web">http://www.cloudsidekick.com</span><br /><br />' +
    '    <b>Version: </b><span id="app_version"></span><br />' +
    '    <b>Database: </b><span id="db_info"></span><br />' +
    '<br /><br />Copyright © Cloud Sidekick 2012. All Rights Reserved.' +
    '</p>' +
    '<br />' +
    '<p>' +
    '    <span id="info_dialog_info"></span>' +
    '</p>' +
    '</div>' +
	'<!-- End "about" dialog. -->' +
	'<!-- This is the pop up "tag picker" dialog. -->' +
    '<div id="tag_picker_dialog" class="tag_picker hidden">' +
    '    Select a Tag:' +
    '    <hr />' +
    '    <div style="overflow: auto;">' +
    '        <div id="tag_picker_list">' +
    '        </div>' +
    '    </div>' +
    '    <hr />' +
    '    <div id="tag_picker_description" class="tag_description">' +
    '    </div>' +
    '</div>' +
    '<!-- End "tag picker" dialog. -->' +
	'<!-- Log View dialog. -->' +
	'<div id="log_view_dialog" class="hidden" title="Change Log"></div>' +
	'<!-- End Log View dialog. -->' +
	'<!-- This is the pop up "My Account" dialog. -->' +
    '<div id="my_account_dialog" class="hidden" title="My Account">' +
	'<table>' +
	'<tr><td>Name:</td><td><span id="my_fullname"></span></td></tr>' +
	'<tr><td>User Name:</td><td><span id="my_username"></span></td></tr>' +
	'<tr><td>Email:</td><td><input type="text" id="my_email" name="my_email" class="usertextbox" /></td></tr>' +
	'<tr class="my_localsettings"><td>Password:</td><td><input type="password" id="my_password" name="my_password" class="usertextbox" /></td></tr>' +
	'<tr class="my_localsettings"><td>Password Confirm:</td><td><input type="password" id="my_password_confirm" class="usertextbox" /></td></tr>' +
	'<tr class="my_localsettings"><td style="vertical-align: top;">Security Question:</td><td><textarea id="my_question" name="my_question" class="usertextbox"></textarea></td></tr>' +
	'<tr class="my_localsettings"><td>Security Answer:</td><td><input type="password" id="my_answer" name="my_answer" class="usertextbox" /></td></tr>' +
	'</table>' +
    '</div>' +
    '<!-- End "My Account" dialog. -->' +
	'' +
	'';

document.write(d);
