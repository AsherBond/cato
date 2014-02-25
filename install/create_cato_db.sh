#!/usr/bin/env bash
set -e

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

### Cato db setup script
###
### This script will configure the cato db users in MySQL and import tables and data

function usage_and_exit()
{
    echo "Usage: $0 [OPTION...]"
    echo ""
    echo "Mandatory arguments:"
    echo -e "\t-r PASSWORD        root db password"
    echo -e "\t-d DBNAME          database name to create"
    echo -e "\t-u USER            Cato db user name"
    echo -e "\t-p PASSWORD        Cato db user password"
    echo -e "\t-k USER            a read only user name"
    echo -e "\t-l PASSWORD        read only user password"
    echo -e "\t-? show this help"
    exit 1
}

while getopts r:d:u:p:k:l:? flag
do
    case $flag in
        r)
            ROOTDBPASS=$OPTARG;;
        d)
            CATODBNAME=$OPTARG;;
        u)
            CATODBUSER=$OPTARG;;
        p)
            CATODBPASS=$OPTARG;;
        k)
            CATODBREADUSER=$OPTARG;;
        l)
            CATODBREADPASS=$OPTARG;;
        ?)
            usage_and_exit;;
    esac

done

if [[ -z "$ROOTDBPASS" ]];
then 
    echo "Root DB password not set."
    usage_and_exit 
fi
if [[ -z "$CATODBNAME" ]];
then 
    echo "Cato DB name not set"
    usage_and_exit 
fi
if [[ -z "$CATODBUSER" ]];
then 
    echo "Cato DB user name not set"
    usage_and_exit 
fi
if [[ -z "$CATODBPASS" ]];
then 
    echo "Cato DB user password not set"
    usage_and_exit 
fi
if [[ -z "$CATODBREADUSER" ]];
then 
    echo "Cato DB read only user name not set"
    usage_and_exit 
fi
if [[ -z "$CATODBREADPASS" ]];
then 
    echo "Cato DB read only user password not set"
    usage_and_exit 
fi

exit

if [[ -n "$CATO_HOST" ]];
then
	echo "Using Host Address $CATO_HOST"
fi


set -ex

# get this script's path

SCRIPT_HOME=`dirname $0`

trap "echo !!!!!!!!!!!!!!!!!!!!!!!!!;echo 'Cato install script did not complete successfully!';echo !!!!!!!!!!!!!!!!!!!!!!!!!" ERR

### Create the database, logins and permissions in MySQL

mysqladmin -u root -p$ROOTDBPASS create $CATODBNAME
mysql -u root -p$ROOTDBPASS -e "GRANT EXECUTE, SELECT, INSERT, UPDATE, DELETE, LOCK TABLES, CREATE TEMPORARY TABLES ON $CATODBNAME.* TO '$CATODBUSER'@'localhost' IDENTIFIED BY '$CATODBPASS';"
mysql -u root -p$ROOTDBPASS -e "GRANT SELECT, CREATE TEMPORARY TABLES ON $CATODBNAME.* TO '$CATODBREADUSER'@'localhost' IDENTIFIED BY '$CATODBREADPASS';"
mysql -u root -p$ROOTDBPASS -e "FLUSH PRIVILEGES;"

### create the database tables, indexes, etc. etc.
mysql -u root -p$ROOTDBPASS $CATODBNAME < $SCRIPT_HOME/cato_ddl.sql

exit 0
