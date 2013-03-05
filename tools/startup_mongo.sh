#!/bin/bash
# startup mongodb server
# assumes mongodb.conf resides in /opt/apps/mongodb/mongodb.conf
# run as sudo root on the server that hosts mongodb

# adjust path to mongod on Mac/Windows or other dev system
MONGOD=mongod
LOG=/usr/local/var/log/mongodb/mongo.log

# perform startup
#$MONGOD --config /opt/apps/mongodb/mongodb.conf --fork --logpath /var/log/mongodb.log --logappend
$MONGOD --fork --logpath $LOG --logappend
# Show tail of log file that shows that mongod started OK or that it failed to 
#   start
# if you see something like this:
#   [websvr] admin web console waiting for connections on port 28017
#   it means startup went OK.
echo 'tail $LOG'
tail -f $LOG
