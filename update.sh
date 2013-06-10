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

### Cato Community Edition update script
###
### This script will download Cato CE and update an existing installation.

### This version of the script has been testing on Ubuntu Precise.
### It should work on Ubuntu Hardy forward.

# TODO!!!
# release, root db user and password should be command line arguments.

RELEASE=1.15
DBROOTUID="root"
DBROOTPWD="cloudsidekick"

BACKUP_DIR=/tmp

read -p "This will update an existing Cato installation. Are you sure? (yes/no)?" choice
case "$choice" in 
  yes|YES|Yes ) printf "Preparing to update...\n\n";;
  * ) exit 0;;
esac

if [ -z "$CATO_HOME" ]; then
    echo "CATO_HOME not set!"
	exit 0
fi

printf "CATO_HOME is: $CATO_HOME"

NOW=`date +%s`

echo "Stopping Cato services..."
$CATO_HOME/services/stop_services.sh

echo "Backing up to: $BACKUP_DIR"
mkdir -p $BACKUP_DIR
tar -zcv --exclude='.git' --exclude='.gitignore' -f $BACKUP_DIR/catobackup-$NOW.tgz $CATO_HOME

echo "Getting Cato Version $RELEASE..."
curl -Lk --output /tmp/cato-$RELEASE.tar.gz https://github.com/cloudsidekick/cato/tarball/$RELEASE

echo "Updating..."
tar -xvzf /tmp/cato-$RELEASE.tar.gz -C $CATO_HOME --strip-components=1

echo "Updating the Database..."
$CATO_HOME/updatedb.py $DBROOTUID -p$DBROOTPWD

echo "Starting Cato services..."
$CATO_HOME/services/start_services.sh


set +x
echo ""
echo ""
echo ""
echo "!!!!!!!!!!!!!!!!!!!!"
echo "CATO UPDATE COMPLETE"
echo "All done, make sure services are up and running."
echo "!!!!!!!!!!!!!!!!!!!!!"
exit 0