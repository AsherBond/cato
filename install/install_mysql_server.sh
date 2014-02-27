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

### Cato MySQL database installation script, installs MySQL and sets the root db password

function usage_and_exit()
{
    echo "Usage: $0 [OPTION...]"
    echo ""
    echo "Installs and configures MySQL Server. Will set the initial root db user password"
    echo ""
    echo "Mandatory arguments:"
    echo -e "\t-r PASSWORD        root db password"
    echo -e "\t-? show this help"
    exit 1
}

while getopts r:? flag
do
    case $flag in
        r)
            ROOTDBPASS=$OPTARG;;
        ?)
            usage_and_exit;;
    esac

done

if [[ -z "$ROOTDBPASS" ]];
then 
    echo "Root DB password not set."
    usage_and_exit 
fi

set -ex

echo off
trap "echo !!!!!!!!!!!!!!!!!!!!!!!!!;echo 'Cato install script did not complete successfully!';echo !!!!!!!!!!!!!!!!!!!!!!!!!" ERR
echo on

# this script resides in the CATO_HOME/install directory
INSTALL_DIR=`dirname $0`

# set the CATO_HOME directory based on the INSTALL_DIR
CATO_HOME=`dirname $INSTALL_DIR`

# determine the linux flavor
FLAVOR=`$CATO_HOME/install/determine_flavor.sh`

if [ "$FLAVOR" = "deb" ];
then
    # Ubuntu, Debian or along those lines
    apt-get update -q
    export DEBIAN_FRONTEND=noninteractive
    apt-get -y -q=2 install mysql-server

elif [ "$FLAVOR" = "rh" ];
then 
    # RedHat, CentOS, Amazon AMI, Fedora, etc.
    yum -y --quiet install mysql-server mysql mysql-client
    chkconfig --levels 235 mysqld on
    service mysqld start

elif [ "$FLAVOR" = "suse" ];
then   
    # Suse flavored
    zypper refresh
    zypper --quiet install -y mysql mysql-client
    chkconfig --add mysql
    service mysql start

else
    set +x
    echo "!!!!!!!!!!!!!!!!!"
    echo "This install script does not support your distribution of linux. Exiting"
    echo "You will need to install MySQL manually."
    echo "See http://dev.mysql.com/doc/refman/5.6/en/installing.html"
    echo "for installation guidence"
    echo "!!!!!!!!!!!!!!!!!"
    exit 1
fi

### update the root db password

mysqladmin -u root password $ROOTDBPASS

exit 0
