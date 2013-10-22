#!/usr/bin/env bash
set -ex

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

### Cato Community Edition installation script
###
### This script will download Cato CE and install the software including
### dependencies. The end result will be running services and the 
### admin console.

### This version of the script has been testing on Ubuntu Precise.
### It should work on Ubuntu Hardy forward.  


# customize the following values to suit your needs

# the network hostname where these services can be reached, for example 'csk.mycompany.com'
CATO_HOST=`localhost`

# cato target directory
CATO_HOME=`pwd`
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
# the location of cato logfiles
LOGFILESDIR="$CATOFILESDIR/log"
TMPDIR="$CATOFILESDIR/tmp"

MONGOADMIN=admin
MONGOADMINPASS=secret

# Should we create AWS cloud records in the database?
# This will load the AWS region endpoint addresses into
# the Cato database. Default is yes. Comment out or change to 'no'
# if there are no plans to use the AWS Cloud. They can be added or 
# deleted later.

LOADAWSREGIONS="yes"

###
### shouldn't have to edit below this line
###

trap "echo !!!!!!!!!!!!!!!!!!!!!!!!!;echo 'Cato install script did not complete successfully!';echo !!!!!!!!!!!!!!!!!!!!!!!!!" ERR

# the following should be i386 or x64_86 for linux
ARCHITECTURE=`uname -m`
if [ $ARCHITECTURE != "x86_64" ]; then
    ARCHITECTURE="i386"
fi

if [ -f /etc/debian_version ];  
then  
    FLAVOR="deb"
elif [ -f /etc/redhat-release ];  
then  
    FLAVOR="rh"
elif [ -f /etc/SuSE-release ];  
then  
    FLAVOR="suse"
elif [ -f /etc/system-release ];  
then  
    AMAZON=`grep Amazon /etc/system-release |cut -f1 -d' '`
    if [ "$AMAZON" = "Amazon" ];
    then
        FLAVOR="rh"
    else 
        FLAVOR="notsure"
    fi
else 
    FLAVOR="notsure"
fi
echo $FLAVOR

#mkdir $CATO_HOME

# Ubuntu specific
if [ "$FLAVOR" = "deb" ];
then
    apt-get update -q
    apt-get install -y -q python-dev mongodb python-pip build-essential curl

    export DEBIAN_FRONTEND=noninteractive
    echo "mysql-server mysql-server/root_password select $ROOTDBPASS" | debconf-set-selections
    echo "mysql-server mysql-server/root_password_again select $ROOTDBPASS" | debconf-set-selections
    apt-get -y -q=2 install mysql-server
    MONGOSERVICE="mongodb"

elif [ "$FLAVOR" = "rh" ];
then 
    yum -y --quiet install mysql-server mysql mysql-client python-setuptools gcc make python-devel gcc-c++ curl
    easy_install pip
    chkconfig --levels 235 mysqld on
    service mysqld start
    mysqladmin -u root password $ROOTDBPASS
    mysql -u root -p$ROOTDBPASS -e "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('$ROOTDBPASS');"
    mysql -u root -p$ROOTDBPASS -e "SET PASSWORD FOR 'root'@'`hostname`' = PASSWORD('$ROOTDBPASS');"
    mysql -u root -p$ROOTDBPASS -e "DROP USER ''@'localhost';"
    mysql -u root -p$ROOTDBPASS -e "DROP USER ''@'`hostname`';"
    MONGOSERVICE="mongod"
    cat > /etc/yum.repos.d/10gen.repo <<EOF
[10gen]
name=10gen Repository
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64
gpgcheck=0
enabled=1
EOF
    yum -y --quiet install mongo-10gen mongo-10gen-server
    # the following is to work around a bug on redhat / centos
    #sed -i"" -e"s|^pidfilepath.*$|pidfilepath=/var/lib/mongo/mongod.lock|"  /etc/mongod.conf
    service ${MONGOSERVICE} start

elif [ "$FLAVOR" = "suse" ];
then 
    zypper refresh
    zypper --quiet install -y mysql mysql-client python-setuptools python-xml curl

    chkconfig --add mysql
    service mysql start
    mysqladmin -u root password $ROOTDBPASS
    mysql -u root -p$ROOTDBPASS -e "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('$ROOTDBPASS');"
    mysql -u root -p$ROOTDBPASS -e "SET PASSWORD FOR 'root'@'`hostname`' = PASSWORD('$ROOTDBPASS');"
    mysql -u root -p$ROOTDBPASS -e "DROP USER ''@'localhost';"
    mysql -u root -p$ROOTDBPASS -e "DROP USER ''@'`hostname`';"

else
    set +x
    echo "!!!!!!!!!!!!!!!!!"
    echo "This install script does not support your distribution of linux. Exiting"
    echo "!!!!!!!!!!!!!!!!!"
    exit 1
fi

### install third party python packages
pip install -q -r $CATO_HOME/requirements.txt

### compile c++ encryption library
cd $CATO_HOME/src/catocrypt
python setup.py install --install-platlib=$CATO_HOME/lib/catocryptpy
cd $CATO_HOME

### mongodb setup
$CATO_HOME/tools/mongo_secure.py 127.0.0.1 ${MONGOADMIN} ${MONGOADMINPASS} ${CATODBNAME} ${CATODBUSER} ${CATODBPASS}
sed -i"" -e"s|#auth|auth|" /etc/${MONGOSERVICE}.conf
service ${MONGOSERVICE} stop
service ${MONGOSERVICE} start

### Create the supporting application directories
mkdir -p $LOGFILESDIR/te
mkdir -p $LOGFILESDIR/se
mkdir -p $CATOFILESDIR/ui
mkdir -p $TMPDIR

### Create the database, logins and permissions in MySQL
mysqladmin -u root -p$ROOTDBPASS create $CATODBNAME
mysql -u root -p$ROOTDBPASS -e "GRANT EXECUTE, SELECT, INSERT, UPDATE, DELETE, LOCK TABLES, CREATE TEMPORARY TABLES ON $CATODBNAME.* TO '$CATODBUSER'@'localhost' IDENTIFIED BY '$CATODBPASS';"
mysql -u root -p$ROOTDBPASS -e "GRANT SELECT, CREATE TEMPORARY TABLES ON $CATODBNAME.* TO '$CATODBREADUSER'@'localhost' IDENTIFIED BY '$CATODBREADPASS';"
mysql -u root -p$ROOTDBPASS -e "FLUSH PRIVILEGES;"

### Create a new conf file from the default
mkdir -p /etc/cato
CONFFILE=/etc/cato/cato.conf
cp $CATO_HOME/conf/default.cato.conf $CONFFILE

### Use the encryption utility to encrypt passwords to be used in the conf file
NEWKEY=`$CATO_HOME/conf/catoencrypt $ENCRYPTIONKEY ""`
ENCDBPASS=`$CATO_HOME/conf/catoencrypt $CATODBPASS $ENCRYPTIONKEY`
ENCDBREADPASS=`$CATO_HOME/conf/catoencrypt $CATODBREADPASS $ENCRYPTIONKEY`

### Replace placeholders with localized config settings
### See the user configurable settings above
sed -i"" -e"s|#CATO_HOME#|${CATO_HOME}|" $CONFFILE
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


### create the database tables, indexes, etc. etc.
mysql -u root -p$ROOTDBPASS $CATODBNAME < $CATO_HOME/conf/data/cato_ddl.sql

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
