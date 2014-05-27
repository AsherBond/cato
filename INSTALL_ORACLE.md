# Installing the Oracle client for velocity use

## Requirements

**velocity** can interact directly with Oracle applicaiton databases via the instant client
and an open source Python package called cx_Oracle. The following instructions
are provided to install cx_Oracle

## Install

Modify the following line for your cato application directory. 

```
export CATO_HOME=/opt/cato
```

Install prerequisite packages.

Ubuntu:

```
sudo apt-get install -y unzip  libaio1
```

RedHat / CentOS

```
sudo yum -y install unzip libaio.x86_64
```

Download the Oracle Instant Client and SDK. For convenience, these downloads are
provided with the following commands:


### FOR 32 BIT SERVERS

```
curl -Lk http://downloads.cloudsidekick.com/thirdpartylibs/instantclient-sdk-linux-11.2.0.3.0.zip -o instantclient-sdk-linux-11.2.0.3.0.zip
curl -Lk http://downloads.cloudsidekick.com/thirdpartylibs/instantclient-basiclite-linux-11.2.0.3.0.zip -o instantclient-basiclite-linux-11.2.0.3.0.zip

unzip instantclient-basiclite-linux-11.2.0.3.0.zip -d /tmp
unzip instantclient-sdk-linux-11.2.0.3.0.zip -d /tmp
```

### FOR 64 BIT SERVERS
```
curl -Lk http://downloads.cloudsidekick.com/thirdpartylibs/instantclient-sdk-linux.x64-11.2.0.3.0.zip -o instantclient-sdk-linux.x64-11.2.0.3.0.zip
curl -Lk http://downloads.cloudsidekick.com/thirdpartylibs/instantclient-basiclite-linux.x64-11.2.0.3.0.zip -o instantclient-basiclite-linux.x64-11.2.0.3.0.zip

unzip instantclient-basiclite-linux.x64-11.2.0.3.0.zip -d /tmp
unzip instantclient-sdk-linux.x64-11.2.0.3.0.zip -d /tmp
```

Move the files into the **automate** application directory ($CATO_HOME).

```
mv /tmp/instantclient_11_2 ${CATO_HOME}/lib/.
mv ${CATO_HOME}/lib/instantclient_11_2/sdk/include ${CATO_HOME}/lib/instantclient_11_2/include
```

Create links for shared libraries. 

```
cd ${CATO_HOME}/lib/instantclient_11_2
ln -s libocci.so.11.1 libocci.so
ln -s libclntsh.so.11.1 libclntsh.so
```

Download and install cx_Oracle. Typically this requires root access, but also the ORACLE_HOME
environment variable to be set. The following creates a script that will be run using sudo.

```
cd ~
cat <<EOF > setup_ora.sh
export ORACLE_HOME=${CATO_HOME}/lib/instantclient_11_2
pip install cx_Oracle
EOF
chmod +x setup_ora.sh
sudo ./setup_ora.sh
```

If there are no errors so far, test the install. If the following prints "install successful"
then the oracle client is installed correctly.

```
export ORACLE_HOME=${CATO_HOME}/lib/instantclient_11_2
export LD_LIBRARY_PATH=$ORACLE_HOME
python -c "import cx_Oracle; print 'install successful'"
```

Add ORACLE_HOME and LD_LIBRARY_PATH to the cato application user's profile script. 
First determine the filename of the profile script and then change it below. It may be .bash_profile
depending on your flavor of linux.

```
export PROF=.profile
echo "export ORACLE_HOME=${CATO_HOME}/lib/instantclient_11_2" >> ~/${PROF}
echo "export LD_LIBRARY_PATH=$ORACLE_HOME" >>  ~/${PROF}
```

Restart the Cato services to finish the Oracle client install. 

```
$CATO_HOME/services/restart_services.sh
```


