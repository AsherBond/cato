
#########################################################################
# Copyright 2011 Cloud Sidekick
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#########################################################################


update task_step set function_xml = 
replace(function_xml,
'<function command_type="sql_exec" parse_method="1>"',
'<function name="sql_exec" variables="true" parse_method="1">')
where function_name = 'sql_exec';

update task_step set function_xml = 
replace(function_xml,
'<function command_type="cmd_line" parse_method="2">',
'<function name="cmd_line" variables="true" parse_method="2">')
where function_name = 'cmd_line';

update task_step set function_xml = 
replace(function_xml,
'<function command_type="read_file" parse_method="2">',
'<<function name="read_file" variables="true" parse_method="2">')
where function_name = 'read_file';

update task_step set function_xml = 
replace(function_xml,
'<function command_type="http" parse_method="2">',
'<function name="http" variables="true" parse_method="2">')
where function_name = 'http';

update task_step set function_xml = 
replace(function_xml,
'<function command_type="parse_text" parse_method="2">',
'<function name="parse_text" variables="true" parse_method="2">')
where function_name = 'parse_text';

## COMMAND LINE command
update task_step set function_xml = 
replace(function_xml,
'<conn_name input_type="text">',
'<conn_name input_type="text" connection_picker="true" label="Connection" break_after="true" required="true">'
)
where function_name = 'cmd_line';
update task_step set function_xml = 
replace(function_xml,
'<conn_name input_type="text" />',
'<conn_name input_type="text" connection_picker="true" label="Connection" break_after="true" required="true" />'
)
where function_name = 'cmd_line';

update task_step set function_xml = 
replace(function_xml,
'<command input_type="text">',
'<command input_type="textarea" rows="3" label="Command" class="w95pct" required="true" label_style="display: block;">'
)
where function_name = 'cmd_line';
update task_step set function_xml = 
replace(function_xml,
'<command input_type="text" />',
'<command input_type="textarea" rows="3" label="Command" class="w95pct" required="true" label_style="display: block;" />'
)
where function_name = 'cmd_line';

update task_step set function_xml = 
replace(function_xml,
'<timeout input_type="text">',
'<timeout input_type="text" option_tab="Options" label="Timeout" break_after="true">'
)
where function_name = 'cmd_line';
update task_step set function_xml = 
replace(function_xml,
'<timeout input_type="text" />',
'<timeout input_type="text" option_tab="Options" label="Timeout" break_after="true" />'
)
where function_name = 'cmd_line';

update task_step set function_xml = 
replace(function_xml,
'<positive_response input_type="text">',
'<positive_response input_type="text" option_tab="Options" label="Positive Response" break_after="true">'
)
where function_name = 'cmd_line';
update task_step set function_xml = 
replace(function_xml,
'<positive_response input_type="text" />',
'<positive_response input_type="text" option_tab="Options" label="Positive Response" break_after="true" />'
)
where function_name = 'cmd_line';

update task_step set function_xml = 
replace(function_xml,
'<negative_response input_type="text">',
'<negative_response input_type="text" option_tab="Options" label="Negative Response" break_after="true">'
)
where function_name = 'cmd_line';
update task_step set function_xml = 
replace(function_xml,
'<negative_response input_type="text" />',
'<negative_response input_type="text" option_tab="Options" label="Negative Response" break_after="true" />'
)
where function_name = 'cmd_line';



# NEW CONNECTION
update task_step set function_xml = 
replace(function_xml,
'<conn_name input_type="text">',
'<conn_name input_type="text" label="as" required="true" class="w200px" help="Name this connection for reference in the Task.">'
)
where function_name = 'new_connection';

# DROP CONNECTION
update task_step set function_xml = 
replace(function_xml,
'<conn_name input_type="text">',
'<conn_name input_type="text" label="Connection">'
),
function_xml = 
replace(function_xml,
'<conn_name input_type="text" />',
'<conn_name input_type="text" label="Connection" />'
)
where function_name = 'drop_connection';

# END
update task_step set 
function_xml = replace(function_xml,
'<status input_type="select">',
'<status input_type="select" label="Status">'
),
function_xml = replace(function_xml,
'<message input_type="text">',
'<message input_type="textarea" rows="3" label="Message" class="w95pct" label_style="display: block;">'
)
where function_name = 'end';

# SLEEP
update task_step set 
function_xml = replace(function_xml,
'<seconds input_type="text">',
'<seconds input_type="text" label="Sleep">'
)
where function_name = 'sleep';

# CANCEL TASK
update task_step set 
function_xml = replace(function_xml,
'<task_instance input_type="text">',
'<task_instance input_type="text" label="Task Instance ID(s)">'
)
where function_name = 'cancel_task';

# SET LOGGING LEVEL
update task_step set 
function_xml = replace(function_xml,
'<debug_level input_type="text">',
'<debug_level input_type="dropdown" label="Logging Level" datasource="function" dataset="ddDataSource_GetDebugLevels">'
)
where function_name = 'set_debug_level';

# GET TASK INSTANCE
update task_step set 
function_xml = replace(function_xml,
'<instance input_type="text">',
'<instance input_type="text" label="Task Instance">'
),
function_xml = replace(function_xml,
'<handle input_type="text">',
'<handle input_type="text" label="Handle">'
)
where function_name = 'get_instance_handle';

# PARSE_TEXT
update task_step set 
function_xml = replace(function_xml,
'<text input_type="text" />',
'<text input_type="textarea" rows="3" label="Text" class="w95pct" required="true" label_style="display: block;" />'
),
function_xml = replace(function_xml,
'<text input_type="text">',
'<text input_type="textarea" rows="3" label="Text" class="w95pct" required="true" label_style="display: block;">'
)
where function_name = 'parse_text';

# LOG_MSG
update task_step set 
function_xml = replace(function_xml,
'<message input_type="text" />',
'<message input_type="textarea" rows="2" label="Log" class="w95pct" required="true" label_style="display: block;" />'
),
function_xml = replace(function_xml,
'<message input_type="text">',
'<message input_type="textarea" rows="2" label="Log" class="w95pct" required="true" label_style="display: block;">'
)
where function_name = 'log_msg';



# THIS FIXES ANY COMMANDS THAT HAD VARIABLE_XML
update task_step set function_xml = 
replace(function_xml, '</function>', concat(ifnull(replace(replace(variable_xml, '</variables>', '</step_variables>'), '<variables>', '<step_variables>'), ''), '</function>') )
where variable_xml is not null
and function_xml not like '%<step_variables>%';


# THIS changes the "command_type" attribute to "name".
# it wasn't used before but now it is.
update task_step set function_xml = 
replace(function_xml, '<function command_type=', '<function name=')
where function_xml like '<function command_type=%';



# NOTE: these happen AFTER the command_type->name change, because replace operations 
# happen here requiring 'name'

# CLEAR VARIABLE
update task_step set 
function_xml = replace(function_xml,
'<function name="clear_variable"><variable>',
'<function name="clear_variable"><variables><variable>'
),
function_xml = replace(function_xml,
'</variable></function>',
'</variable></variables></function>'
)
where function_name = 'clear_variable';

# SET VARIABLE
update task_step set 
function_xml = replace(function_xml,
'<function name="set_variable"><variable>',
'<function name="set_variable"><variables><variable>'
),
function_xml = replace(function_xml,
'</variable></function>',
'</variable></variables></function>'
)
where function_name = 'set_variable';

# EXISTS
update task_step set 
function_xml = replace(function_xml,
'<function name="exists"><variable>',
'<function name="exists"><variables><variable>'
),
function_xml = replace(function_xml,
'</variable><actions>',
'</variable></variables><actions>'
)
where function_name = 'exists';

# WAIT FOR TASKS
update task_step set 
function_xml = replace(function_xml,
'<function name="wait_for_tasks"><handle>',
'<function name="wait_for_tasks"><handles><handle>'
),
function_xml = replace(function_xml,
'</handle></function>',
'</handle></handles></function>'
)
where function_name = 'wait_for_tasks';




