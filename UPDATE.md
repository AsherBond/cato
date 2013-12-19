# Cloud Sidekick Cato CE (Community Edition) 

## Prerequisite Requirements

These instructions details the steps necessary to upgrade an existing Cato environment.
The steps are typically similar for each release, but version specific instructions _may_ be included, and will be noted below.

### Support

> Need help at any point in this process, please don't hesitate to contact us at support@cloudsidekick.com.

### Version Specific Instructions

> There are no additional instructions specific to this version.

## Update Steps

### Step 1 - Check and Define Version

Define the desired version as an environment variable.

    export VER=1.22

### Step 2 - Environment

Ensure the `CATO_HOME` environment variables is set.

    echo $CATO_HOME
    
If the variables isn't correct, set is as follows.  (If the default install path wasn't used in the original install, substitute the correct path.)

    export CATO_HOME=/opt/cato

Set ownership of the installation directories, to ensure the current user has permission to write to `CATO_HOME`.
    
    export CATO_OWNER=`whoami`
    export CATO_GROUP=`id -g -n $CATO_OWNER`

	sudo chown -R $CATO_OWNER:$CATO_GROUP $CATO_HOME
	
### Step 3 - Update Script

Download the update script and mark it as executable.

	curl -Lk --output /tmp/update-cato.sh http://downloads.cloudsidekick.com/cato/update-cato.sh
	chmod +x /tmp/update-cato.sh

### Step 4 - Update

Run the update script, `update-cato.sh`. This script will update Cato.

> The script must be provided the 'root' database user and password in order to perform database schema updates. (If the installation defaults weren't used, substitute the correct values.)

    /tmp/update-cato.sh ${VER} root cloudsidekick

### Step 5 - Verify Version Number

Verify the application were updated.  The results of the following command should match the desired version set in Step 1.

	cat $CATO_HOME/VERSION


## Wrapping Up

### Check Services and Logs

The start scripts will start up several server processes.

Confirm all Cato processes are running.  There should be five:

    ps -eaf | grep $CATO_HOME | grep -v grep
	
Should show:
    
    cato_admin_ui
    cato_poller
    cato_rest_api
    cato_scheduler
    
> Cato has a `cato_messenger` component as well, but it will not be running unless it is configured.


If all processes are not running, check the logfiles for errors. 


	cd /var/cato/log
	ls -l *.log
	more <logfile_name>

### Step 8 - Client Tools (optional)

If you have a copy of the Client Tools installed on this machine, update them as well.

    sudo -E pip install https://github.com/cloudsidekick/catoclient/archive/${VER}.tar.gz
