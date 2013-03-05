#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Initialize secure mongo database 

The server should be started with a command similar to the below, using and mongodb.conf where
auth is set to true:

mongod --config /opt/apps/mongodb/mongodb.conf --fork --logpath /var/log/mongodb.log --logappend

Sample mongodb.conf:
------
# This is an example config file for MongoDB.
#dbpath = /var/lib/mongodb
#bind_ip = 127.0.0.1
auth = true 
#verbose = true # to disable, comment out.
#rest = true

------

First time mongodb admin setup:

If mongodb has not been used in secure mode (--auth option) before, or if
mongodb is not running in secure mode,
admin credentials can be set like this (please use a secure password)
>>> import pymongo
>>> from mongo_secure import add_admin_user
>>> conn = pymongo.Connection(host, port)   
>>> add_admin_user(conn, 'admin', 'asecurepassword')

If admin credentials have been set before and you are running mongodb in secure
mode, admin password can be changed like this:
>>> import pymongo
>>> from mongo_secure import add_admin_user
>>> conn = pymongo.Connection(host, port)   
>>> admin_auth(conn, 'admin', 'oldpassword')
>>> add_admin_user(conn, 'admin', 'asecurepassword')

------

Other commands:
* shutdown server:
mongo admin
MongoDB shell version: 2.2.0
connecting to: admin
> db.shutdownServer()



"""
import sys
import pymongo

def add_admin_user(conn, adminuser, adminpassword):
    """ Add a user to admin db """
    db = conn['admin']
    return db.add_user(adminuser, adminpassword)

def admin_auth(conn, adminuser, adminpassword):
    """ authenticate to admin db """
    db = conn['admin']
    return db.authenticate(adminuser, adminpassword)
    
    

def add_db_user(conn, dbname, username, password):
    """ Adds user credentials to the database.
    
    Will change the password if user name already exists.

    """    
    db = conn[dbname]
    return db.add_user(username, password)

USAGE = """Usage:
./mongo_secure.py hostname admin_user admin_password dbname, username, password
e.g.:
./mongo_secure.py cato.shinesoft.com admin asecrete dstests3 dstests3user secret
"""
def main(argv=None):
    """ Add user to a mongo database.
    
    Usage:
    ./mongo_secure.py hostname admin_user admin_password dbname, username, password
    e.g.:
    ./mongo_secure.py 127.0.0.1 admin asecrete dstests3 dstests3user secret

    """
    if (len(argv) != 7):
        print(USAGE)
        return 1
    host = argv[1] 
    port = 27017
    adminuser = argv[2] 
    adminpassword = argv[3] 
    dbname = argv[4] 
    username = argv[5] 
    password = argv[6] 
    
    conn = pymongo.Connection(host, port)    
    add_admin_user(conn, adminuser, adminpassword)
    add_db_user(conn, dbname, username, password)
    print('User %s has been added to the database %s' % (username, dbname))
    

if __name__ == '__main__':
    sys.exit(main(sys.argv))


