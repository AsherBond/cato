# velocity automate

## Requirements

**velocity automate** will run on many different Linux distros and versions, but the most tested is Ubuntu 10.04 - 12.04.
See the Install portion below for the distros and versions supported by the automated install.

### Hardware Requirements

**automate** can run on minimal hardware for demo and development purposes.  Hardware should be scaled depending on the workload and level of activity required.

Minimum requirements are:

- 500M RAM
- 1G Disk Space
- 2 CPU cores
- Python 2.6 or 2.7

## Install

These installation instructions cover installing **automate** on a single linux 
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

### Installation

Select a user other than root to be the application user account on the target machine. Ssh into the machine using this user. 
This user will own the application files and directories as well as run the services. 

The application user account will need to have cron enabled.

Download the supplied tar file to the target server. Unpack the file with the following command. 
Substitute /opt/cato for any target directory desired.

```
export CSK_HOME=/opt/csk
export CATO_HOME=$CSK_HOME/cato
sudo mkdir $CATO_HOME
sudo tar -xvzf cloudsidekickcato.tar.gz -C $CATO_HOME --strip-components=1
```

Change current directory to the target directory.

```
cd $CATO_HOME
```

__Optional__
It is optional to edit the install.sh script to modify user ids, passwords, file locations, etc.

The installation script will create a directory under /var named `cato`. This directory will hold logfiles, cache
files and temporary files. If desired, change these parameters in the top of the install.sh script.

#### Run Install

Run the installation script.

```
cd install
sudo ./install.sh
```

Change the ownership of the application files and directories to the application user account. 
The following example changes it to the ubuntu user. Modify the following commands as appropriate
for the user, group and target directories.

``` 
sudo chown -R ubuntu:ubuntu $CATO_HOME
sudo chown -R ubuntu:ubuntu  /var/cato
```

Add the CSK_HOME environment variable to the .profile (or .bash_profile depending on the flavor of linux).

```
echo "export CSK_HOME=$CSK_HOME" >> ~/.profile
```

Now start all services. Make sure to use the application user account used in the "chown" step above.

```
$CATO_HOME/services/start_services.sh
```


## Post-Install

This script will start several server processes:

- cato_messenger
- cato_rest_api
- cato_admin_ui
- cato_poller
- cato_scheduler

Confirm all processes are running:

```
ps -eafl | grep cato_ | grep -v grep
```

If all processes are not running, check the logfiles for errors. 

```
cd /var/cato/log
ls -l *.log
more <logfile_name>
```

### Initial Configuration

After all services are started, one last step remains - the initial configuration of the system.

Note: in a default install, no Cloud endpoints are defined.  Service providers such as Amazon AWS have a known set of Cloud endpoints.
To configure **automate** with the default AWS Endpoints, add the following option to the configure command.  
(Predefined Clouds can be added at any time in the Cato Admin UI as well.)

This can be done via a web browser, or the *curl* command line utility.

Using curl on localhost _without_ AWS region endpoints
```
curl http://localhost:4001/configure
```
or using curl on localhost _with_ AWS region endpoints
```
curl http://localhost:4001/configure?createclouds=true
```


### Startup / Shutdown

If at any time the services need to be shutdown, the following scripts will stop / start 
the processes and also place monitors in cron. 

To stop the services:

```
$CATO_HOME/services/stop_services.sh
```

To start the services:

```
$CATO_HOME/services/start_services.sh
```

To restart the services:

```
$CATO_HOME/services/restart_services.sh
```

## Firewalls

To enable access to the **automate** application, open the following ports locally 
on the target machine and any external firewalls. 

Ports 8080, 8082

To provide remote access to the REST API, open these additional ports.

Port 4001

To perform a quick test, disable the local firewall via the following commands. 
NOTE: this is not recommened for a production machine. 

RedHat / CentOS:

```
sudo service iptables stop
sudo chkconfig iptables off
```

## Enabling SSL/TLS (https)

By default, the **automate** UI and REST API are configured for standard HTTP.  HTTPS (SSL/TLS) can be easily enabled.

```
vi $CATO_CONFIG/cato.conf (default: /etc/cato/cato.conf)
```

- For the **automate** UI - change the setting *admin_ui_use_ssl* to *true*
- For the REST API - change the setting *rest_api_use_ssl* to *true*
- Install your certificate and private key in $CATO_HOME/conf
- If you want to keep your certificate and key in another location, specify the path and file in the two cato.conf settings: i
```    
admin_ui_ssl_cert <path>/mycert.crt
admin_ui_ssl_key <path>/mykey.key
```

With OpenSSL, it is easy to generate a self signed certificate and private key. However for production use, a certificate authority (CA) is highly recommended.

To create a self signed certificate, use the following command and fill out the prompts.

```openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $CATO_CONFIG/cato.key -out $CATO_CONFIG/cato.crt```

Make sure to restart the services and time a change is made to the cato.conf file:

```
$CATO_HOME/services/restart_services.sh
```

## Administrator UI Login

To login to the Cato Administrator UI, point your browser to: 

```
http://<serveraddress>:8082
```

Username: administrator
Password: password

> You will be required to change the password upon initial login.

##Note on the web server

The **automate** UI runs on a lightweight Python web framework called web.py.
This should be sufficient for most uses, however **automate** can also be configured to use Apache.

