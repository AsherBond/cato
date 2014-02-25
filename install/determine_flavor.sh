#!/usr/bin/env bash
if [ -f /etc/debian_version ];
then
    FLAVOR="deb"
elif [ -f /etc/redhat-release ];
then
    FLAVOR="rh"
elif [ -f /etc/SuSE-release ];
then
    FLAVOR="suse"
elif [ -f /etc/system-release ];
then
    AMAZON=`grep Amazon /etc/system-release |cut -f1 -d' '`
    if [ "$AMAZON" = "Amazon" ];
    then
        FLAVOR="rh"
    else
        FLAVOR="notsure"
    fi
else
    FLAVOR="notsure"
fi
echo $FLAVOR
