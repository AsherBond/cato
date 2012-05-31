#!/bin/bash
date
if [ -z "$CATO_HOME" ]; then
    
    EX_FILE=`readlink -f $0`
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

# All other processes go here.  No process should be in both sections though.
FULL_PROCS[0]="$CATO_HOME/web/cato_admin_ui.py"

FULL_LOGFILES[0]="$CATO_LOGS/cato_admin_ui.log"

start_other_procs() {
    count=0
    echo "Looking for processes to start"
    while [[ $count -lt ${#FULL_PROCS[*]} ]]; do
        PID=`ps -eafl | grep "${FULL_PROCS[$count]}$" | grep -v "grep"`
        if [ ! "$PID" ]; then
            echo "Removing sessions..."
        	rm -r sessions/*
            echo "Starting ${FULL_PROCS[$count]}"
            nohup ${FULL_PROCS[$count]} >> ${FULL_LOGFILES[$count]} 2>&1 &
        else
            echo "${FULL_PROCS[$count]} is already running"
        fi
        (( count += 1 ))
    done

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

