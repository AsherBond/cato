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

### Cato installation script
###
### This script will install third party software, configure configuration files,
### create directories needed to support Cato, etc. 

### customize the following values to suit your needs

# the password for the root@localhost mysql user...
ROOTDBPASS="cloudsidekick"
# the database name to install cato in...
CATODBNAME="cato"
# the database application user...
CATODBUSER="cato"
# the database app user's password...
CATODBPASS="cato"
# the database read only user...
CATODBREADUSER="catoread"
# the database read only user's password...
CATODBREADPASS="catoread"
# the encryption key, recommend 8 or more random characters. 
ENCRYPTIONKEY="E8Ske%0j5Ih#HF4"
# the root location for cato created files
CATOFILESDIR="/var/cato"

# Should we create AWS cloud records in the database?
# This will load the AWS region endpoint addresses into
# the Cato database. Default is yes. Comment out or change to 'no'
# if there are no plans to use the AWS Cloud. They can be added or 
# deleted later.

LOADAWSREGIONS="yes"

###
### shouldn't have to edit below this line
###

function usage_and_exit()
{
    echo "USAGE:"
    echo "$0 -h <host address>"
    echo -e "\t-? show this help"
    exit
}

CATO_HOST=""

while getopts h:? flag
do
    case $flag in
        h)
            CATO_HOST=$OPTARG;;
        ?)
            usage_and_exit;;
    esac

done

if [[ -n "$CATO_HOST" ]];
then
	echo "Using Host Address $CATO_HOST"
fi

set -ex


# this script resides in the CATO_HOME/install directory
INSTALL_DIR=`dirname $0`

# set the CATO_HOME directory based on the INSTALL_DIR
CATO_HOME=`dirname $INSTALL_DIR`

# the location of cato logfiles
LOGFILESDIR="$CATOFILESDIR/log"
TMPDIR="$CATOFILESDIR/tmp"

echo off
trap "echo !!!!!!!!!!!!!!!!!!!!!!!!!;echo 'Cato install script did not complete successfully!';echo !!!!!!!!!!!!!!!!!!!!!!!!!" ERR
echo on

# create the supporting application directories
mkdir -p $LOGFILESDIR/te
mkdir -p $LOGFILESDIR/se
mkdir -p $CATOFILESDIR/ui
mkdir -p $TMPDIR


# check and see if c++ source is included
if [ -d $CATO_HOME/src ]; then
    # this means that we are installing from source
    # not the 'batteries included' tar file
    # therefore we need to install all third party 
    # modules as well as compile the cato 
    # encryption shared library

    # install third party packages and python modules
    $CATO_HOME/install/install_third_party.sh

    # compile c++ encryption library
    WHEREAMI=`pwd`
    cd $CATO_HOME/src/catocrypt
    python setup.py install --install-platlib=$CATO_HOME/lib/catocryptpy
    cd $WHEREAMI
fi

# create a new conf file from the default
mkdir -p /etc/cato
CONFFILE=/etc/cato/cato.conf
cp $CATO_HOME/conf/default.cato.conf $CONFFILE

# use the encryption utility to encrypt passwords to be used in the conf file
# this will not work unless the cato crypt library is compiled
# or the binary distribution is being installed
NEWKEY=`$CATO_HOME/install/catoencrypt $ENCRYPTIONKEY ""`
ENCDBPASS=`$CATO_HOME/install/catoencrypt $CATODBPASS $ENCRYPTIONKEY`
ENCDBREADPASS=`$CATO_HOME/install/catoencrypt $CATODBREADPASS $ENCRYPTIONKEY`
ADMINPASS=`$CATO_HOME/install/catoencrypt password $ENCRYPTIONKEY`

# replace placeholders with localized config settings
# see the user configurable settings above
sed -i"" -e"s|#CATO_HOST#|${CATO_HOST}|" $CONFFILE
sed -i"" -e"s|#CATODBNAME#|${CATODBNAME}|" $CONFFILE
sed -i"" -e"s|#CATODBUSER#|${CATODBUSER}|" $CONFFILE
sed -i"" -e"s|#CATODBPASS#|${ENCDBPASS}|" $CONFFILE
sed -i"" -e"s|#CATODBREADUSER#|${CATODBREADUSER}|" $CONFFILE
sed -i"" -e"s|#CATODBREADPASS#|${ENCDBREADPASS}|" $CONFFILE
sed -i"" -e"s|#ENCRYPTIONKEY#|${NEWKEY}|" $CONFFILE
sed -i"" -e"s|#LOGFILESDIR#|${LOGFILESDIR}|" $CONFFILE
sed -i"" -e"s|#TMPDIR#|${TMPDIR}|" $CONFFILE
sed -i"" -e"s|#CATOFILES#|${CATOFILESDIR}|" $CONFFILE


### install and configure security for mongodb
$CATO_HOME/install/install_mongodb.sh -d ${CATODBNAME} -u ${CATODBUSER} -p ${CATODBPASS}

### install mysql server and client and set the root db password
$CATO_HOME/install/install_mysql_server.sh -r ${ROOTDBPASS}

### setup the mysql cato database, security and tables
$CATO_HOME/install/create_cato_db.sh -r ${ROOTDBPASS} -d ${CATODBNAME} -u ${CATODBUSER} -p ${CATODBPASS} -k ${CATODBREADUSER} -l ${CATODBREADPASS} -a ${ADMINPASS}

set +x
echo ""
echo ""
echo ""
echo "!!!!!!!!!!!!!!!!!!!!!"
echo "CATO INSTALL COMPLETE"
echo "All done, make sure services are up and running."
echo "NOTE: You may want to DELETE THIS SCRIPT since it contains passwords and keys"
echo ""
echo "Proceed with the final installation steps in INSTALL.md now"
echo ""
echo "!!!!!!!!!!!!!!!!!!!!!"
exit 0
