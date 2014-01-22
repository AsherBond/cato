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
    '<div id="error_dialog" title="Error" class="ui-state-error hidden">' +
    '<p>' +
    '    <span class="ui-icon ui-icon-alert" style="float: left; margin: 0 7px 50px 0;"></span>' +
    '    <span id="error_dialog_message"></span>' +
    '</p>' +
    '<p>' +
    '    <span id="error_dialog_info"></span>' +
    '</p>' +
    '<div id="stack_trace" class="hidden">' +
    '    <p class="clearfloat">' +
    '        <span id="show_stack_trace" class="ui-icon ui-icon-triangle-1-e" style="float: left; margin: 0 7px 50px 0;"></span>Show Details' +
    '    </p>' +
    '    <p class="ui-widget-content ui-corner-bottom ui-state-error hidden" style="overflow: auto; padding: 4px; font-size: .7em; margin-top:10px;">' +
    '        Stack Trace: <br />' +
    '        <span id="error_dialog_trace"></span>' +
    '    </p>' +
    '</div>' +
    '</div>' +
    '<!-- End popup error message dialog template.  -->' +
    '<!-- This is the popup informational message template. -->' +
    '<div id="info_dialog" title="Info" class="ui-state-highlight hidden">' +
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
    '<!-- Log View dialog. -->' +
    '<div id="log_view_dialog" class="hidden" title="Change Log"></div>' +
    '<!-- End Log View dialog. -->' +
    '' +
    '';

document.write(d);
