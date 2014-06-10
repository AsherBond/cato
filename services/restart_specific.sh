#!/usr/bin/env bash

# this is rarely called directly, should be called by csk-restart-service.
# if that command ever goes away, this likely can too.

. $HOME/.profile

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



# will restart only the specified services

for svc in "$@"
do
    if [[ "`uname`" == "Darwin" ]]; then
        PID=`ps -A | grep "$svc" | grep -v "grep" | grep -v "$0" | awk '{ print \$1 }'`
    else
        PID=`ps -eafl | grep "$svc" | grep -v "grep" | grep -v "$0" | awk '{ print \$4 }'`
    fi

    echo "Shutting down $svc ($PID) ..."
    kill -9 $PID
    
    # now this is ugly and brute force, but since we don't run all our services in the same directory
    # we can't know where to start them by just the service name.
    # so... try to start it in all four environments - only one will actually work :-)
    
	echo "Starting $svc ..."
    CATO_LOG="$CATO_LOGS/$svc.log"

	# try all four
	if [ -f $CSK_HOME/cato/services/bin/$svc ]; then 
		nohup $CSK_HOME/cato/services/bin/$svc >> /dev/null 2> ${CATO_LOG} &
	fi
	if [ -f $CSK_HOME/maestro/services/bin/$svc ]; then 
		nohup $CSK_HOME/maestro/services/bin/$svc >> /dev/null 2> ${CATO_LOG} &
	fi
	if [ -f $CSK_HOME/canvas/services/bin/$svc ]; then 
		nohup $CSK_HOME/canvas/services/bin/$svc >> /dev/null 2> ${CATO_LOG} &
	fi
	if [ -f $CSK_HOME/legato/services/bin/$svc ]; then 
		nohup $CSK_HOME/legato/services/bin/$svc >> /dev/null 2> ${CATO_LOG} &
	fi

    NEW=`ps | grep "$svc" | grep -v "grep" | grep -v "$0"`
    echo "Started $NEW"
    
done

exit
