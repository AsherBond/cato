#!/bin/bash
date
#OS=`uname`
#if [ "$OS" == "Darwin" ]; then
#    ### this script does not work on the Mac yet. 
#    echo "this script does not work on the Mac yet. Like to help?"
#    exit 
#fi
if [ -z "$CATO_HOME" ]; then

    #EX_FILE=`readlink -f $0`
    EX_FILE=`python -c "import os; print os.path.realpath('$0')"`
    EX_HOME=${EX_FILE%/*}
    CATO_HOME=${EX_HOME%/*}
    echo "CATO_HOME not set, assuming $CATO_HOME"
    export CATO_HOME
fi

# All other processes go here.  No process should be in both sections though.
FULL_PROCS[0]="$CATO_HOME/services/bin/cato_poller"
FULL_PROCS[1]="$CATO_HOME/services/bin/cato_scheduler"
FULL_PROCS[2]="$CATO_HOME/services/bin/cato_messenger"
FULL_PROCS[3]="$CATO_HOME/services/bin/cato_ecosync"

count=0
while [[ $count -lt ${#FULL_PROCS[*]} ]]; do
    if [[ "`uname`" == "Darwin" ]]; then
        PIDS=`ps -A | grep "${FULL_PROCS[$count]}" | grep -v "grep" | awk '{ print \$1 }'`
    else
        PIDS=`ps -eafl | grep "${FULL_PROCS[$count]}" | grep -v "grep" | awk '{ print \$4 }'`
    fi

    if [ -z "$PIDS" ]; then
        echo "${FULL_PROCS[$count]} is not running"
    else
        for PID in $PIDS; do
            echo "Shutting down ${FULL_PROCS[$count]} ($PID)"
            kill -9 $PID
        done
    fi 
        (( count += 1 ))
done
if [ "$1" = "leavecron" ]; then
	echo "Removing startup.sh from crontab"
		crontab -l | grep -v start_services.sh > $CATO_HOME/conf/crontab.backup 2>/dev/null
		crontab -r 2>/dev/null
		crontab $CATO_HOME/conf/crontab.backup
		rm $CATO_HOME/conf/crontab.backup
	touch .shutdown
fi

echo "end"
exit
