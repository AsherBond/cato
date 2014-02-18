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

"""
The simplest extension... writes a string to the log file and the database task log.

Extension entry functions MUST have the following argument signature:
	TE = a pointer to the Task Engine object instance, filled with useful functions.
	step = The full details of this command, including the function XML.
		This is where you'll pull out any values captured by the task editor.
	logger = a pointer to the Task Engine logger class, capable of writing to the log file.
	
	
	No return values are required.  Set values in the TE variable array using TE.rt.set(name, value, index)
	
	Raising an Exception will halt the Task Engine process.
	
"""

def hello_world(TE, step):
	# TE.get_command_params returns the VALUES of each provided property
	# step.command is the raw XML of the command
	message = TE.get_command_params(step.command, "message")[0]
	
	# TE.replace_variables will look on the runtime variable stack, and replace any [[vars]] 
	# defined in your property
	message = TE.replace_variables(message)
	
	
	logentry = "Someone said [%s]." % message

	# logger writes to the task log FILE
	TE.logger.critical(logentry)
	
	# insert_audit writes to the task run log in the DATABASE
	TE.insert_audit("hello_world", logentry, "")
	
	
