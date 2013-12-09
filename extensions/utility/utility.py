# !/usr/bin/env tclsh

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
Functions for the 'filesystem' extension commands.
"""

def read_file(TE, step):
	# TE.get_command_params returns the VALUES of each provided property
	# step.command is the raw XML of the command
	path = TE.get_command_params(step.command, "path")[0]
	target_var = TE.get_command_params(step.command, "variable")[0]
	
	# TE.replace_variables will look on the runtime variable stack, and replace any [[vars]] 
	# defined in your property
	path = TE.replace_variables(path)
	
	# try to open the file, write log messages on exceptions.
	try:
		import os
		fn = os.path.expanduser(path)
		with open(fn, 'r') as f_in:
			if not f_in:
				TE.insert_audit("read_file", "Unable to open file [%s]." % (fn), "")
				TE.logger.critical("Unable to open file [%s]." % (fn))
			data = f_in.read()
			
			TE.rt.set(target_var, data)
			
	except Exception as ex:  # write the exception to the logfile
		TE.logger.critical("Exception opening file [%s].\n%s" % (fn, ex.__str__()))
	

def write_file(TE, step):
	# TE.get_command_params returns the VALUES of each provided property
	# step.command is the raw XML of the command
	path = TE.get_command_params(step.command, "path")[0]
	contents = TE.get_command_params(step.command, "contents")[0]
	
	# TE.replace_variables will look on the runtime variable stack, and replace any [[vars]] 
	# defined in your property
	path = TE.replace_variables(path)
	contents = TE.replace_variables(contents)
	
	# try to write the file, write log messages on exceptions.
	try:
		import os
		fn = os.path.expanduser(path)
		with open(fn, 'w+') as f_out:
			if not f_out:
				TE.insert_audit("read_file", "Unable to open file [%s]." % (fn), "")
				TE.logger.critical("Unable to open file [%s]." % (fn))
			f_out.write(contents.encode("utf-8", "ignore") if contents else "")
	except Exception as ex:  # write the exception to the logfile
		TE.logger.critical("Exception opening file [%s].\n%s" % (fn, ex.__str__()))
	

def exec_python(TE, step):
	# TE.get_command_params returns the VALUES of each provided property
	# step.command is the raw XML of the command
	code = TE.get_command_params(step.command, "code")[0]
	
	# TE.replace_variables will look on the runtime variable stack, and replace any [[vars]] 
	# defined in your property
	code = TE.replace_variables(code)
	
	try:
		"""
		Sandbox - we'll do our best to build a secure'ish sandbox.  However, there is just really no such thing.
		We do have a little bit of comfort here - a Task developer is by their very nature an advanced programmer,
		with access to run scripts in the environment.
		
		So, as a general rule, we tend to trust our Task Developers. 
		"""
		# first, get a copy of __builtins__
		import copy
		
		bi = copy.copy(__builtins__)
		# make safe by removing the most dangerous features...
 		UNSAFE = ['open', 'file', 'execfile', 'compile', 'reload', 'input', '__import__', 'eval']
 		for func in UNSAFE:
 			del bi[func]
			
		# let's give explicit access to only a few Task Engine features.
		features = { 
			"LOG" : TE.logger,
			"AUDIT" : TE.insert_audit,
			"VARS" : TE.rt
		}
		
		# now, let's eval the code we were provided
		exec(code, bi, features)

	except SystemExit as ex:
		# if the code we exec'd throws a SystemEdit... kill the Task
		TE.logger.info("Code raised a SystemExit... exiting...\n%s" % (ex))
		TE.result_summary()
		TE.release_all()
		TE.update_status("Completed")
		exit()
	except Exception as ex:  # write the exception to the logfile
		TE.logger.critical("Exception in 'exec_python.\n%s" % (ex))
	
	
