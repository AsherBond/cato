#!/bin/bash

echo ""
echo "Shutting down Cato..."
date

if [ -z "$CSK_HOME" ]; then
    echo "CSK_HOME environment variable is not defined."
    exit
fi
echo "CSK_HOME is [$CSK_HOME"]
 
CATO_HOME=$CSK_HOME/cato
echo "CATO_HOME is [$CATO_HOME]"

while read line
do
    CATO_EXE="$CATO_HOME/services/bin/$line"
    if [[ "`uname`" == "Darwin" ]]; then
        PIDS=`ps -A | grep "${CATO_EXE}" | grep -v "grep" | awk '{ print \$1 }'`
    else
	echo "${CATO_EXE}"
        PIDS=`ps -eafl | grep "${CATO_EXE}" | grep -v "grep" | awk '{ print \$4 }'`
        echo `ps -eafl | grep "${CATO_EXE}" `
	echo $PIDS
    fi

    for PID in $PIDS; do
        echo "Shutting down ${CATO_EXE} ($PID)"
        kill -9 $PID
    done
done < $CATO_HOME/services/cato_services

if [ "$1" != "leavecron" ]; then
	echo "Removing startup.sh from crontab..."
		crontab -l | grep -v "${CATO_HOME}/services/start_services.sh" > /tmp/crontab.backup 2>/dev/null
		crontab -r 2>/dev/null
		crontab /tmp/crontab.backup
		rm /tmp/crontab.backup
fi

echo ""
exit
