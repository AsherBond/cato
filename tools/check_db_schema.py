#!/usr/bin/env python

import os
import sys
import json

if not "CATO_HOME" in os.environ:
    raise Exception("CATO_HOME environment variable not set.  Cato is required.")

CATO_HOME = os.environ["CATO_HOME"]

base_path = CATO_HOME
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catocommon import catocommon

db = catocommon.new_conn()

# a test to print out the database
tables = db.select_all("show tables")
for table in tables:
    print table[0]
    desc = db.select_all("desc %s" % table)
    for col in desc:
        print "    %s" % (json.dumps(col))
        # print "    %s %s %s %s" % (col["Field"], col["Type"], col["Null"], " DEFAULT '%s'" % (col["Default"]) if col["Default"] else "")
        # print "    %s %s %s %s" % (col["Field"], col["Type"], col["Null"], col["Default"])

#{u'Extra': u'', u'Default': None, u'Field': u'tag_name', u'Key': u'PRI', u'Null': u'NO', u'Type': u'varchar(32)'}
db.close()
