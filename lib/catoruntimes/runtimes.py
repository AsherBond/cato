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

import os
import sys
import ast
import base64
import json
import re
from datetime import datetime, timedelta
import dateutil.parser as parser
from bson.objectid import ObjectId

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catolog import catolog

# eval_get requires a safe environment to support some explicit language features for the eval.
# NOTE: some of these are limited in scope and have non-standard names.
EVAL_ENVIRONMENT = {
               'datetime': datetime,
               'timedelta': timedelta,
               'ObjectId': ObjectId,
               'b64encode': base64.b64encode,
               'b64decode': base64.b64decode,
               'parsedate': parser.parse,
               'asjson': json.dumps,
               'fromjson': json.loads
               }

# There are many useful and safe Python built-ins, so let's add them
# to our eval environment.
for f in [
    'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'chr', 'cmp', 'divmod', 'enumerate', 'float', 'format',
    'hex', 'int', 'isinstance', 'len', 'list', 'long', 'max', 'min', 'oct', 'ord', 'pow', 'range', 'repr',
    'round', 'set', 'sorted', 'str', 'sum', 'tuple', 'unichr', 'unicode', 'zip'
]:
    EVAL_ENVIRONMENT[f] = eval(f)

class Runtimes:
    def __init__(self):

        self.logger = catolog.get_logger("Runtimes")

        # initialize the runtime array dictionary
        self.data = {}

        # for the new variable syntax feature
        self.obj_data = {}

    def _objectify(self, s):
        """ attempt to parse a string into a python object """
        self.logger.debug("_objectify got %s" % (s))
        try:
            out = ast.literal_eval(s)
        except:
            out = s

        self.logger.debug("_objectify resulted in %s" % (s))
        return out

    def _fill(self, l, index):
        """fills the array with nothing for specific number of indexes"""

        length = len(l)

        if index >= length:
            l.extend(None for _ in range(length, index + 1))


    def set(self, name, value, index=None):
        """sets a named array given a value and index. index is optional, creates the array if not exist"""

        # NEW FEATURE
        # notice there's no index - 1 here, for consistency with python arrays
        objval = self._objectify(value)
        if index is None:
            self.obj_data[name] = objval
        else:
            if name not in self.obj_data:
                self.obj_data[name] = [objval]
            else:
                self.obj_data[name].insert(index, objval)

        # LEGACY METHOD
        name = name.upper()
        if not index:
            self.data[name] = [value]
        else:
            # task engine index starts at 1, python list starts at 0
            index = index - 1
            try:
                l_len = len(self.data[name])
            except KeyError:
                self.data[name] = []
                l_len = len(self.data[name])
            if index == l_len:
                self.data[name].append(value)
            elif index > l_len:
                self._fill(self.data[name], index)
                self.data[name][index] = value
            else:
                self.data[name][index] = value


    def get(self, name, index=None):
        """gets a single value from named array"""

        name = name.upper()
        if not index:
            index = 0
        else:
            # task engine index starts at 1, python list starts at 0
            index = index - 1
        try:
            val = self.data[name][index]
            if val is None:
                val = ""
        except (IndexError, KeyError):
            val = ""

        return val

    def show(self):
        """prints the full runtime structure, debugging"""

        print self.data

    def count(self, name):
        """returns the count of a named array, 0 if it does not exist"""

        name = name.upper()
        try:
            length = len(self.data[name])
        except KeyError:
            length = 0

        return length

    def get_all(self, name):
        """returns all values of a named array, list format. Empty list if array doesn't exist"""

        name = name.upper()
        try:
            return self.data[name][:]
        except KeyError:
            return []

    def set_all(self, name, vals=[]):
        """sets a named array provided a list"""

        name = name.upper()
        self.data[name] = vals

    def clear(self, name, index=None):
        """deletes all values of named array"""

        name = name.upper()

        if not index:
            try:
                del(self.data[name])
            except:
                pass
        else:
            # task engine index starts at 1, python list starts at 0
            index = index - 1
            try:
                self.data[name].pop(index)
            except:
                pass

    def exists(self, name):
        """does the variable array exist"""

        name = name.upper()
        try:
            z = self.data[name]
            return True
        except KeyError:
            return False

    def eval_set(self, expression, value):
        """
        evaluates an expression to find a specific item in the obj_data collection
        and sets it to a new value
        """
        if len(expression):
            newval = self._objectify(value)
            expression = expression.strip()
            self.logger.debug("update expression is:\n %s" % (expression))
            self.logger.debug("newval is:\n %s" % (newval))
            # exec is dangerous!
            # so, we only allow it to run against our obj_data collection

            # this isn't perfect, but we have to assume if _objectify returned a basestring
            # then the value is a string.
            # HOWEVER, it may very well contain quotes.
            # so let's use it's 'repr'esentation
            if isinstance(newval, basestring):
                newval = repr(newval)

            setexpr = "%s=%s" % (expression, newval)
            self.logger.debug("trying to execute:\n %s" % (setexpr))

            try:
                exec(setexpr, {}, self.obj_data)
            except Exception as ex:
                # write a log message, but fail safely by setting the value to ""
                self.logger.error("Variable assignment is not valid.\n%s" % (str(ex)))

    def eval_get(self, expression):
        """evaluates an expression to retrieve data from the obj_data collection"""
        if len(expression):
            expression = expression.strip()
            self.logger.debug("expression is:\n %s" % (expression))
            # self.logger.debug("obj_data is:\n %s" % (self.obj_data))
            # NOTE: eval is dangerous!
            # so, we only allow it to run against our obj_data collection
            # and a very strict environment
            try:
                result = eval(expression, EVAL_ENVIRONMENT, self.obj_data)
                
                # here's a helper feature
                # "task parameter" values are *always* a list, even if they only have one item.
                # but we don't know here if we're looking at a value that was set by a parameter!
                # So, IF the result is a list, AND the list has one value, AND the expression is a flat name (no fancy stuff),
                # THEN, we'll return the first item in the list
                
                # (this regex will only match a 'flat' variable name
                if re.match("^\w+$", expression) and isinstance(result, list):
                    return result[0]
                else:
                    return result
            except Exception as ex:
                # write a log message, but fail safely by setting the value to ""
                self.logger.error("Variable expression %s is not valid.\n%s" % (expression, str(ex)))
                return ""
