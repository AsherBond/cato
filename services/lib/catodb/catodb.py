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
		self.conn = ""

	def connect_db(self, server="", port=3306, database="", user="", password=""):
		"""Establishes a connection as a class property."""

		try:
			self.conn = pymysql.connect(host=server, port=int(port), 
				user=user, passwd=password, db=database)
		except Exception, e:
			print e
			return None
	
	def select_all(self, sql):
		"""Gets a row set for a provided query."""
		if sql == "":
			print "select_all: SQL cannot be empty."
			return None
		
		try:
			c = self.conn.cursor()
			c.execute(sql)
			result = c.fetchall()
			c.close()
		except Exception, e:
			print e
			return None

		return result	


	def select_row(self, sql):
		"""Gets a single row for a provided query.  If there are multiple rows, the first is returned."""
		if sql == "":
			print "select_row: SQL cannot be empty."
			return None
		
		try:
			c = self.conn.cursor()
			c.execute(sql)
			result = c.fetchone()
			c.close()
		except Exception, e:
			print e
			return None

		return result

	def select_col(self, sql):
		"""Gets a single value from the database.  If the query returns more than one column, the first is used."""
		if sql == "":
			print "select_column: SQL cannot be empty."
			return None
		
		try:
			c = self.conn.cursor()
			c.execute(sql)
			result = c.fetchone()
			c.close()
		except Exception, e:
			print e
			return None

		return result[0]

	def exec_db(self, sql):
		"""Used for updates, inserts and deletes"""
		if sql == "":
			print "update: SQL cannot be empty."
			return None
		
		try:
			c = self.conn.cursor()
			c.execute(sql)
			self.conn.commit()
			c.close()
		except Exception, e:
			print e
			return False

		return True

        def close(self):
		"""Closes the database connection."""
                self.conn.close()