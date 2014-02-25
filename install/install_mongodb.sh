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

### Cato Community Edition installation script
###
### This script will download Cato CE and install the software including
### dependencies. The end result will be running services and the 
### admin console.

### This version of the script has been testing on Ubuntu Precise.
### It should work on Ubuntu Hardy forward.  

function usage_and_exit()
{
    echo "Usage: $0 [OPTION...]"
    echo ""
    echo "Mandatory arguments:"
    echo -e "\t-d DBNAME          database name to create"
    echo -e "\t-u USER            Cato db user name"
    echo -e "\t-p PASSWORD        Cato db user password"
    echo -e "\t-? show this help"
    exit 1
}

while getopts d:u:p:? flag
do
    case $flag in
        d)
            CATODBNAME=$OPTARG;;
        u)
            CATODBUSER=$OPTARG;;
        p)
            CATODBPASS=$OPTARG;;
        ?)
            usage_and_exit;;
    esac
done

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

set -ex

# customize the following values to suit your needs


trap "echo !!!!!!!!!!!!!!!!!!!!!!!!!;echo 'Cato install script did not complete successfully!';echo !!!!!!!!!!!!!!!!!!!!!!!!!" ERR

FLAVOR=`$CATO_HOME/install/determine_flavor.sh`

# Ubuntu specific
if [ "$FLAVOR" = "deb" ];
then
    apt-get install -y -q mongodb 

    MONGOSERVICE="mongodb"

elif [ "$FLAVOR" = "rh" ];
then 
    MONGOSERVICE="mongod"
    cat > /etc/yum.repos.d/10gen.repo <<EOF
[10gen]
name=10gen Repository
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64
gpgcheck=0
enabled=1
EOF
o    yum -y --quiet install mongo-10gen mongo-10gen-server
    # the following is to work around a bug on redhat / centos
    #sed -i"" -e"s|^pidfilepath.*$|pidfilepath=/var/lib/mongo/mongod.lock|"  /etc/mongod.conf

    service ${MONGOSERVICE} start

else
    set +x
    echo "!!!!!!!!!!!!!!!!!"
    echo "This install script does not support your distribution of linux. Exiting"
    echo "!!!!!!!!!!!!!!!!!"
    exit 1
fi

# the following sets up the mongodb server with authentication and creates a database for cato
$CATO_HOME/install/mongo_secure.py 127.0.0.1 ${MONGOADMIN} ${MONGOADMINPASS} ${CATODBNAME} ${CATODBUSER} ${CATODBPASS}

# turn authentication on in the mongo conf file
sed -i"" -e"s|#auth|auth|" /etc/${MONGOSERVICE}.conf

# and restart the service
service ${MONGOSERVICE} stop
service ${MONGOSERVICE} start

echo "MongoDB install complete"

exit 0
