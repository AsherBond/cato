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

import pymysql

class Db(object):

    def __init__(self):
        self.conn = None
        self.error = ""
        self.server = ""
        self.port = ""
        self.database = ""
        self.user = ""
        self.password = ""

    def reconnect_db(self):

        if self.conn:
            del(self.conn)
        try:
            self.conn = pymysql.connect(charset='utf8', host=self.server, port=self.port, 
                user=self.user, passwd=self.password, db=self.database)
            self.conn.autocommit(1)
        except Exception as e:
            raise Exception(e)
    
        
    def connect_db(self, server="", port=3306, database="", user="", password=""):
        """Establishes a connection as a class property."""

        self.server = server
        self.port = int(port)
        self.database = database
        self.user = user
        self.password = password

        try:
            self.conn = pymysql.connect(charset='utf8', host=server, port=int(port), 
                user=user, passwd=password, db=database)
            self.conn.autocommit(1)
        except Exception as e:
            raise Exception(e)
    
    def ping_db(self):
        self.conn.ping(True)
    
    def select_all(self, sql, params=()):
        """Gets a row set for a provided query."""
        if sql == "":
            raise Exception("select_all: SQL cannot be empty.")
            return None
        
        try:
            c = self.conn.cursor()
            c.execute(sql, params)
            result = c.fetchall()
            c.close()
        except Exception as e:
            raise Exception(e)

        if result:
            return result
        else:
            return None


    def select_row(self, sql, params=()):
        """Gets a single row for a provided query.  If there are multiple rows, the first is returned."""
        if sql == "":
            raise Exception("select_row: SQL cannot be empty.")
            return None
        
        try:
            c = self.conn.cursor()
            c.execute(sql, params)
            result = c.fetchone()
            c.close()
        except Exception as e:
            raise Exception(e)

        if result:
            return result
        else:
            return None

    def select_col(self, sql, params=()):
        """Gets a single value from the database.  If the query returns more than one column, the first is used."""
        if sql == "":
            raise Exception("select_column: SQL cannot be empty.")
            return None
        
        try:
            c = self.conn.cursor()
            c.execute(sql, params)
            result = c.fetchone()
            c.close()
        except Exception as e:
            raise Exception(e)

        if result:
            return result[0]
        else:
            return None

    def exec_db(self, sql, params=()):
        """Used for updates, inserts and deletes"""
        if sql == "":
            raise Exception("update: SQL cannot be empty.")
            return None
        
        try:
            c = self.conn.cursor()
            c.execute(sql, params)
            self.conn.commit()
            c.close()
        except Exception as e:
            raise Exception(e)

        return True

    def tran_exec(self, sql, params=()):
        """DOES NOT perform a commit!"""
        if sql == "":
            raise Exception("update: SQL cannot be empty.")
            return None
        
        try:
            c = self.conn.cursor()
            c.execute(sql, params)
            c.close()
        except Exception as e:
            raise Exception(e)

        return True

    def tran_rollback(self):
        """Rolls back anything on the current connection."""
        self.conn.rollback()

    def tran_commit(self):
        """Commits anything on the current connection."""
        self.conn.commit()

    def close(self):
        """Closes the database connection."""
        self.conn.close()

    def select_csv(self, sql, quoted=False):
        """Selects a set of rows, and returns the first column as a comma delimited string."""
        rows = self.select_all(sql)
        lst = []
        if rows:
            for row in rows:
                if quoted:
                    lst.append("'%s'" % str(row[0]))
                else:
                    lst.append("%s" % str(row[0]))
            
        return ",".join(lst)
    
    
    # These next functions are the same as their predecessors, except they return the results in a dict.
    # This is handy for referencing valued by column name instead of index.

    def select_all_dict(self, sql, params=()):
        """Gets a row set for a provided query."""
        if sql == "":
            raise Exception("select_all: SQL cannot be empty.")
            return None
        
        try:
            c = self.conn.cursor(pymysql.cursors.DictCursor)
            c.execute(sql, params)
            result = c.fetchall()
            c.close()
        except Exception as e:
            raise Exception(e)

        if result:
            return result
        else:
            return None


    def select_row_dict(self, sql, params=()):
        """Gets a single row for a provided query.  If there are multiple rows, the first is returned."""
        if sql == "":
            raise Exception("select_row: SQL cannot be empty.")
            return None
        
        try:
            c = self.conn.cursor(pymysql.cursors.DictCursor)
            c.execute(sql, params)
            result = c.fetchone()
            c.close()
        except Exception as e:
            raise Exception(e)

        if result:
            return result
        else:
            return None

    # Calling a procedure is a bit different.  For our purpuses, we'll assume the proc returns data using a "select"
    # at the end.  Multiple result sets are not supported.
    def exec_proc(self, sql, params=()):
        """Executes a procedure.  If there is a result set, it is returned."""
        if sql == "":
            raise Exception("exec_proc: SQL cannot be empty.")
            return None
        
        try:
            c = self.conn.cursor(pymysql.cursors.DictCursor)
            c.execute(sql, params)
            self.conn.commit()
            result = c.fetchall()
            c.close()
            # we will discard any additional result sets
            self.conn.next_result()
        except Exception as e:
            raise Exception(e)

        if result:
            return result
        else:
            return None



    # Now something interesting...
    # these functions all just call the ones above...
    # with one difference - none of these throw exceptions.
    # instead, they set the 'error' property of the class.
    # GUI calls and other crash-proof services are made to expect messages, and display them nicely,
    # and not be filled with lots of wasteful try:except blocks.

    def select_col_noexcep(self, sql, params=()):
        try:
            result = self.select_col(sql, params)
            if result is not None: # select_col returns a value, or False
                return result # result is already a single column
            else:
                return "" # returns an empty string, not a boolean!
        except Exception as e:
            self.error = e.__str__()
            
        return None

    def exec_db_noexcep(self, sql, params=()):
        try:
            self.exec_db(sql, params)
        except Exception as e:
            if "1062" in e.__str__():
                self.error = "key_violation"
            else:
                self.error = e.__str__()
            return False

        return True

    def tran_exec_noexcep(self, sql, params=()):
        try:
            self.tran_exec(sql, params)
        except Exception as e:
            self.conn.rollback()
            if "1062" in e.__str__():
                self.error = "key_violation"
            else:
                self.error = e.__str__()
            return False

        return True

