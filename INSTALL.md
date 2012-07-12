# Cloud Sidekick Cato CE (Community Edition) 

## Requirements

Cato CE will run on many different Linux distros and versions, but the most tested is Ubuntu 10.04 - 12.04.
See the Install portion below for the distros and versions supported by the automated install.

**Third party open source packages required for install (these are installed by the automated install script referenced below):**

Python 2.7, MySQL 5.1+, Tcl 8.5+, Web.py, PyMySql, Boto 2.4.1+, Croniter, 
Py-Dom-Xpath, MySQLtcl, Tcl TLS, Tdom, Tcllib, Expect, Tcllib, Tclcloud, Tclwinrm

Optional MS SqlServer connectivity (you must install on your own):
FreeTDS, TclTds

Optional Oracle connectivity (you must install on your own):
Oracle Instant Client, OraTcl

## Install

These installation instructions cover installing Cato on a single linux 
machine with web, database and services residing under the same home 
directory. 

Other installation options such as a multiple server install
are possible and may be recommended under different circumstances and will 
be covered in future revisions of this document. 

 The automated install script has been tested on the following Linux distributions:

#### Name and Version, Amazon AMI used, 32 or 64 bit, login user

- Amazon AMI 2012.03,ami-a0cd60c9,32,ec2-user
- Amazon AMI 2012.03,ami-aecd60c7,64,ec2-user
- CentOS 6,ami-05559b6c,32,root
- CentOS 6,ami-03559b6a,64,root
- Debian 6.0.1,ami-1212ef7b,32,root
- Debian 6.0.1,ami-1e39ca77,64,root
- Fedora 17,ami-08d97e61,32,ec2-user
- Fedora 17,ami-2ea50247,64,ec2-user
- OpenSuse 11.3,ami-acc83bc5,32,root
- OpenSuse 11.3,ami-00c83b69,64,root
- OpenSuse 11.4,ami-e626de8f,32,root
- OpenSuse 11.4,ami-d226debb,64,root
- RHEL 6.3,ami-d258fbbb,32,root
- RHEL 6.3,ami-cc5af9a5,64,root
- Ubuntu 10.04,ami-37af765e,32,ubuntu
- Ubuntu 10.04,ami-0baf7662,64,ubuntu
- Ubuntu 10.10,ami-d38f57ba,32,ubuntu
- Ubuntu 10.10,ami-d78f57be,64,ubuntu
- Ubuntu 11.04,ami-81c31ae8,32,ubuntu
- Ubuntu 11.04,ami-87c31aee,64,ubuntu
- Ubuntu 11.11,ami-4bad7422,32,ubuntu
- Ubuntu 11.11,ami-4dad7424,64,ubuntu
- Ubuntu 12.04,ami-ac9943c5,32,ubuntu
- Ubuntu 12.04,ami-a29943cb,64,ubuntu

The automated install script has been tested and _does not_ work on the following Linuxes for various reasons, mostly to do with unavailable packages. 

#### Automated install script does not work on: 

- CentOS 5.4
- CentOS 5.5
- Debian 5
- Fedora 16
- Suse EL 10
- Suse EL 11

The following commands will download a bash script which will install Cato CE and all 
non-optional dependencies listed above.  

```curl -Lk --output /tmp/cato_ce_install.sh https://s3.amazonaws.com/downloads.cloudsidekick.com/install/cato_ce_install.sh```

#### Optional:
Edit the installation script to customize the Cato release number, database name, passwords, etc if desired. 

```chmod +x /tmp/cato_ce_install.sh
sudo /tmp/cato_ce_install.sh
```

## Post-Install

This script will start 5 server processes: Poller, Scheduler, Messenger, Ecosync and Admin UI. 

Confirm all processes are running:

```ps -eafl | grep cato_ | grep -v grep
```

If all five processes are not running, check the logfiles for errors. 

```cd /var/cato/log
ls -l *.log
more <logfile_name>
```

NOTE: if at any time the services need to be shutdown, the following scripts will stop / start 
the processes and also place monitors in cron. 

To stop the services:

```sudo /opt/cato/services/stop_services.sh
sudo /opt/cato/web/stop_web.sh
```

To start the services:

```sudo /opt/cato/services/start_services.sh
sudo /opt/cato/web/start_web.sh
```

## Administrator UI Login

To login to the Cato CE Administrator UI, point your browser to: 

```http://<serveraddress>
```

Username: __administrator__
Password: __password__

> You will be required to change the password upon initial login.

##Note on the web server

Cato Community Edition runs on a lightweight webserver that comes with Python web framework Web.py.
This should be sufficient for most uses Cato CE, however Cato can also be configured to use Apache.

> Click [here](http://projects.cloudsidekick.com/projects/cato/wiki/ConfigureApache?utm_source=cato_docs&utm_medium=installdoc&utm_campaign=app) for details about configuring Apache to serve the Cato UI.
