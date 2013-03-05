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

# cato target directory
CATOHOME=`pwd`
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
# the cato administrator password, will have to be changed on initial login anyways
# probably should leave this one
ADMINPASS="password"
# the encryption key, recommend 8 or more random characters. 
ENCRYPTIONKEY="E8Ske%0j5Ih#HF4"
# the root location for cato created files
CATOFILESDIR="/var/cato"
# the location of cato logfiles
LOGFILESDIR="$CATOFILESDIR/log"
TMPDIR="$CATOFILESDIR/tmp"

MONGOADMIN=admin
MONGOADMINPASS=secret

###
### shouldn't have to edit below this line
###

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

#mkdir $CATOHOME

# Ubuntu specific
if [ "$FLAVOR" = "deb" ];
then
    apt-get update -q
    apt-get install -y -q python-dev mongodb python-pip build-essential

    export DEBIAN_FRONTEND=noninteractive
    echo "mysql-server mysql-server/root_password select $ROOTDBPASS" | debconf-set-selections
    echo "mysql-server mysql-server/root_password_again select $ROOTDBPASS" | debconf-set-selections
    apt-get -y -q=2 install mysql-server
    MONGOSERVICE="mongodb"

elif [ "$FLAVOR" = "rh" ];
then 
    yum -y --quiet install mysql-server mysql mysql-client python-setuptools gcc make python-devel gcc-c++
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
    sed -i"" -e"s|^pidfilepath.*$|pidfilepath=/var/lib/mongo/mongod.lock|"  /etc/mongod.conf
    service ${MONGOSERVICE} start

elif [ "$FLAVOR" = "suse" ];
then 
    zypper refresh
    zypper --quiet install -y mysql mysql-client python-setuptools python-xml

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

# install third party python packages
pip install -q -r $CATOHOME/requirements.txt
pip install -q https://github.com/cloudsidekick/awspy/archive/master.zip
pip install -q http://github.com/pdunnigan/pywinrm/archive/master.zip

# compile c++ encryption library
cd $CATOHOME/src/catocrypt
python setup.py install --install-platlib=$CATOHOME/lib/catocryptpy
cd $CATOHOME

# mongodb setup
$CATOHOME/tools/mongo_secure.py 127.0.0.1 ${MONGOADMIN} ${MONGOADMINPASS} ${CATODBNAME} ${CATODBUSER} ${CATODBPASS}
sed -i"" -e"s|#auth|auth|" /etc/${MONGOSERVICE}.conf
service ${MONGOSERVICE} stop
service ${MONGOSERVICE} start

mkdir -p $LOGFILESDIR/ce
mkdir -p $LOGFILESDIR/se
mkdir -p $CATOFILESDIR/ui
mkdir -p $TMPDIR

mysqladmin -u root -p$ROOTDBPASS create $CATODBNAME
mysql -u root -p$ROOTDBPASS -e "GRANT EXECUTE, SELECT, INSERT, UPDATE, DELETE, LOCK TABLES, CREATE TEMPORARY TABLES ON $CATODBNAME.* TO '$CATODBUSER'@'localhost' IDENTIFIED BY '$CATODBPASS';"
mysql -u root -p$ROOTDBPASS -e "GRANT SELECT, CREATE TEMPORARY TABLES ON $CATODBNAME.* TO '$CATODBREADUSER'@'localhost' IDENTIFIED BY '$CATODBREADPASS';"
mysql -u root -p$ROOTDBPASS -e "FLUSH PRIVILEGES;"

cp $CATOHOME/conf/default.cato.conf $CATOHOME/conf/cato.conf
NEWKEY=`$CATOHOME/conf/catoencrypt $ENCRYPTIONKEY ""`
ENCDBPASS=`$CATOHOME/conf/catoencrypt $CATODBPASS $ENCRYPTIONKEY`
ENCDBREADPASS=`$CATOHOME/conf/catoencrypt $CATODBREADPASS $ENCRYPTIONKEY`
ENCADMINPASS=`$CATOHOME/conf/catoencrypt $ADMINPASS $ENCRYPTIONKEY`
sed -i"" -e"s|#CATOHOME#|${CATOHOME}|" $CATOHOME/conf/cato.conf
sed -i"" -e"s|#CATODBNAME#|${CATODBNAME}|" $CATOHOME/conf/cato.conf
sed -i"" -e"s|#CATODBUSER#|${CATODBUSER}|" $CATOHOME/conf/cato.conf
sed -i"" -e"s|#CATODBPASS#|${ENCDBPASS}|" $CATOHOME/conf/cato.conf
sed -i"" -e"s|#CATODBREADUSER#|${CATODBREADUSER}|" $CATOHOME/conf/cato.conf
sed -i"" -e"s|#CATODBREADPASS#|${ENCDBREADPASS}|" $CATOHOME/conf/cato.conf
sed -i"" -e"s|#ENCRYPTIONKEY#|${NEWKEY}|" $CATOHOME/conf/cato.conf
sed -i"" -e"s|#LOGFILESDIR#|${LOGFILESDIR}|" $CATOHOME/conf/cato.conf
sed -i"" -e"s|#TMPDIR#|${TMPDIR}|" $CATOHOME/conf/cato.conf
sed -i"" -e"s|#CATOFILES#|${CATOFILESDIR}|" $CATOHOME/conf/cato.conf
sed -i"" -e"s|#ADMINPASSWORD#|${ENCADMINPASS}|" $CATOHOME/conf/data/cato_data.sql


mysql -u root -p$ROOTDBPASS $CATODBNAME < $CATOHOME/conf/data/cato_ddl.sql
mysql -u root -p$ROOTDBPASS $CATODBNAME < $CATOHOME/conf/data/cato_data.sql

sed -i"" -e"s|${ENCADMINPASS}|#ADMINPASSWORD#|" $CATOHOME/conf/data/cato_data.sql

#$CATOHOME/services/start_services.sh
set +x
echo ""
echo ""
echo ""
echo "!!!!!!!!!!!!!!!!!!!!!"
echo "CATO INSTALL COMPLETE"
echo "All done, make sure services are up and running."
echo "NOTE: You may want to DELETE THIS SCRIPT since it contains passwords and keys"
echo "!!!!!!!!!!!!!!!!!!!!!"
