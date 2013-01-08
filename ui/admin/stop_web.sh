#!/bin/bash

# Copyright 2012 Cloud Sidekick
#  
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  
#     http:# www.apache.org/licenses/LICENSE-2.0
#  
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
 
date
if [ -z "$CATO_HOME" ]; then

    EX_FILE=`python -c "import os; print os.path.realpath('$0')"`
    EX_HOME=${EX_FILE%/*}
    CATO_HOME=${EX_HOME%/*}
    echo "CATO_HOME not set, assuming $CATO_HOME"
    export CATO_HOME
fi

while read line
do
    CATO_EXE="$CATO_HOME/web/$line"
    if [[ "`uname`" == "Darwin" ]]; then
        PIDS=`ps -A | grep "${CATO_EXE}" | grep -v "grep" | awk '{ print \$1 }'`
    else
        PIDS=`ps -eafl | grep "${CATO_EXE}" | grep -v "grep" | awk '{ print \$4 }'`
    fi

    if [ -z "$PIDS" ]; then
        echo "${CATO_EXE} is not running"
    else
        for PID in $PIDS; do
            echo "Shutting down $i ($PID)"
            kill -9 $PID
        done
    fi 
done < $CATO_HOME/web/cato_ui_services
if [ "$1" = "leavecron" ]; then
	echo "Removing start_web.sh from crontab"
		crontab -l | grep -v start_web.sh > $CATO_HOME/conf/crontab.backup 2>/dev/null
		crontab -r 2>/dev/null
		crontab $CATO_HOME/conf/crontab.backup
		rm $CATO_HOME/conf/crontab.backup
	touch .shutdown
fi

echo "end"
exit
