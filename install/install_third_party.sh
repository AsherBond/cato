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

set -ex


# this script resides in the CATO_HOME/install directory
THIS_FILE=`readlink -f $0`
INSTALL_DIR=`dirname $THIS_FILE`

# set the CATO_HOME directory based on the INSTALL_DIR
CATO_HOME=`dirname $INSTALL_DIR`

stty -echo
trap "echo !!!!!!!!!!!!!!!!!!!!!!!!!;echo 'Cato install script did not complete successfully!';echo !!!!!!!!!!!!!!!!!!!!!!!!!" ERR
stty echo

FLAVOR=`$CATO_HOME/install/determine_flavor.sh`
echo $FLAVOR

# Ubuntu specific
if [ "$FLAVOR" = "deb" ];
then
    apt-get update -q
    apt-get install -y -q python-dev python-pip build-essential curl

elif [ "$FLAVOR" = "rh" ];
then 
    yum -y --quiet install python-setuptools gcc make python-devel gcc-c++ curl
    easy_install pip

elif [ "$FLAVOR" = "suse" ];
then 
    zypper refresh
    zypper --quiet install -y python-setuptools python-xml curl
else
    set +x
    echo "!!!!!!!!!!!!!!!!!"
    echo "This install script does not support your distribution of linux. Exiting"
    echo "!!!!!!!!!!!!!!!!!"
    exit 1
fi

### install third party python packages
pip install -q -r $CATO_HOME/install/python_requirements.txt

exit 0
