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
CATO_LOGS=`grep "^logfiles" $CATO_HOME/conf/cato.conf | awk '{print $2}'`
echo "logfile location $CATO_LOGS"
if [ -z "$CATO_LOGS" ]; then
    CATO_LOGS=$CATO_HOME/services/logfiles
fi
export CATO_LOGS

start_other_procs() {
    echo "Looking for processes to start"
    while read line
    do
        CATO_EXE="$CATO_HOME/web/$line"
        CATO_LOG="$CATO_LOGS/$line"
        if [[ "`uname`" == "Darwin" ]]; then
            PID=`ps -A | grep "${CATO_EXE}" | grep -v "grep"`
        else
            PID=`ps -eafl | grep "${CATO_EXE}" | grep -v "grep"`
        fi
        if [ ! "$PID" ]; then
            echo "Starting ${CATO_EXE}"
            nohup ${CATO_EXE} >> ${CATO_LOG} 2>&1 &
        else
            echo "${CATO_EXE} is already running"
        fi
    done < $CATO_HOME/web/cato_ui_services

    echo "Ending starting processes"
}

start_other_procs

CRONID=`pgrep -xn crond`

if [ -z "$CRONID" ]; then
    CRONID=`pgrep -xn cron`
fi

if [ -z "$CRONID" ]; then
    echo "Could not find PID for cron!"
    echo "Cron daemon must be installed and running."
    exit
fi
GPID=`ps -e -o ppid,pid | grep " $PPID$" | awk '{ print $1 }'`

if [ "$CRONID" == "$GPID" ]; then
    if [ -e .shutdown ]; then
        exit
    fi
else
    rm -f .shutdown
fi

crontab -l | grep start_web.sh 2>&1 1>/dev/null
if [ $? -eq 1 ]; then
    echo "Adding start_web.sh to crontab"
    crontab -l > $CATO_HOME/conf/crontab.backup 2>/dev/null
    echo "0-59 * * * * $CATO_HOME/web/start_web.sh >> $CATO_LOGS/startweb.log 2>&1" >> $CATO_HOME/conf/crontab.backup
    crontab -r 2>/dev/null
    crontab $CATO_HOME/conf/crontab.backup
fi

