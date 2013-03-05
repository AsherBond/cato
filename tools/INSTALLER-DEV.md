# Dev Install of Cato

## Intro

This can be adjusted to and merged into INSTALL.md.


## Uninstall the Previous Version of Cato:

Run the follwing commands as root.

Stop services:

	/opt/cato/services/stop_services.sh
	# for cato 1.X, you also need to stop web server:
	# /opt/cato/web/stop_web.sh
	# make sure cato not running
	ps aux|grep /opt/cato
	# move cato out of the way
	# you need to do this fast after stop above, otherwise services will restart automatically
	mv -i /opt/cato /opt/cato.old.2


Drop cato db if it exists, e.g. if this is an update with db schema changes, e.g.:

```
mysqladmin -u root -p{rootpassword} drop cato
```

## Install cato


Adjust the script:

```
cd tools
vi cato_ce_install.sh
```

If this is a dev version, set DEV to 1 and specify CATOSRC:

```
DEV=1
CATOSRC=/home/peter/git-clones/cato2
```

If this is a binary:

DEV=0

Run the installer:

```
./cato_ce_install.sh
```

Make sure services started properly:

```
ps aux|grep cato
```

You should get output that looks something like this:

	root     10932  0.2  0.4  21520  9280 ?        Sl   07:30   0:01 python /opt/cato/services/bin/cato_messenger
	root     10942  0.6  0.4  21272  9188 ?        Sl   07:30   0:03 python /opt/cato/services/bin/cato_poller
	root     10950  0.2  0.5 104728 10720 ?        Sl   07:30   0:01 python /opt/cato/services/bin/cato_rest_api
	root     10958  0.4  0.4  21232  9048 ?        Sl   07:30   0:02 python /opt/cato/services/bin/cato_scheduler
	root     10970  0.3  0.8 111704 16832 ?        Sl   07:30   0:01 python /opt/cato/services/bin/cato_admin_ui
	root     10978  0.2  0.5  22692 10628 ?        Sl   07:30   0:01 python /opt/cato/services/bin/cato_dep_marshall
	root     10991  0.2  0.6 108340 12444 ?        Sl   07:30   0:01 python /opt/cato/services/bin/cato_user_ui

Make sure log files don't indicate a problem:

```
cd /var/log/cato
tail cato_*.log
```

Navigate to the UI

```
http://<serveraddress>
```

## Issues with the Installer:

1) stop_services.sh should stop all services for good - they should not start automatically if the directory move step above is not done fast enough

2) croniter install gives warnings which seem to be benign:

	+ tar -xzf croniter.tz
	+ cd cloudsidekick-croniter-83f6381
	+ python setup.py --quiet install
	file croniter.py (for module croniter) not found
	file croniter_test.py (for module croniter_test) not found
	file croniter.py (for module croniter) not found
	file croniter_test.py (for module croniter_test) not found
	file croniter.py (for module croniter) not found
	file croniter_test.py (for module croniter_test) not found
	zip_safe flag not set; analyzing archive contents...
	+ cd /tmp
	+ rm -rf cloudsidekick-croniter-83f6381 croniter.tz

3) boto install gives benign warnings:

	python setup.py --quiet install
	warning: no files found matching 'boto/mturk/test/*.doctest'
	warning: no files found matching 'boto/mturk/test/.gitignore'
	zip_safe flag not set; analyzing archive contents...
	boto.connection: module references __file__


