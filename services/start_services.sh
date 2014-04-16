#!/bin/bash
if [ -a $HOME/.profile ]
then
    . $HOME/.profile
else
    . $HOME/.bash_profile
fi

echo ""
echo "Starting Cato..."
date

if [ -z "$CSK_HOME" ]; then
    echo "CSK_HOME environment variable is not defined."
    exit
fi
echo "CSK_HOME is [$CSK_HOME"]
 
CATO_HOME=$CSK_HOME/cato
echo "CATO_HOME is [$CATO_HOME]"

if [ -z "$CATO_CONFIG" ]; then
    
    CATO_CONFIG=/etc/cato/cato.conf
    echo "    CATO_CONFIG not set, assuming [$CATO_CONFIG]"
    export CATO_CONFIG
fi

CATO_LOGS=`grep "^logfiles" $CATO_CONFIG | awk '{print $2}'`
echo "Logfile location is [$CATO_LOGS]"
if [ -z "$CATO_LOGS" ]; then
    CATO_LOGS=/var/cato/log
    echo "    'logfiles' setting not set, assuming [$CATO_LOGS]"
fi
export CATO_LOGS

start_other_procs() {
    count=0
    while read line
    do
        CATO_EXE="$CATO_HOME/services/bin/$line"
        CATO_LOG="$CATO_LOGS/$line.log"
        if [[ "`uname`" == "Darwin" ]]; then
            PID=`ps -A | grep "${CATO_EXE}" | grep -v "grep"`
        else
            PID=`ps -eafl | grep "${CATO_EXE}" | grep -v "grep"`
        fi
        if [ ! "$PID" ]; then
            echo "Starting ${CATO_EXE}"
            nohup ${CATO_EXE} >> /dev/null 2> ${CATO_LOG} &
        fi
    done < $CATO_HOME/services/cato_services
}

export LD_LIBRARY_PATH=${CATO_HOME}/lib:${LD_LIBRARY_PATH}

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

crontab -l | grep ${CATO_HOME}/services/start_services.sh 2>&1 1>/dev/null
if [ $? -eq 1 ]; then
    echo "Adding start_services.sh to crontab..."
    crontab -l > /tmp/crontab.backup 2>/dev/null
    echo "0-59 * * * * $CATO_HOME/services/start_services.sh >> $CATO_LOGS/startup.log 2>&1" >> /tmp/crontab.backup
    crontab -r 2>/dev/null
    crontab /tmp/crontab.backup
    rm /tmp/crontab.backup
fi

echo ""

