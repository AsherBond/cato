# Installing the MS SQL Server client for velocity use

## Requirements

**automate** can interact directly with Microsoft SQL Server databases via a python module called `python-tds`.

## Install

Modify the following line for your application directory. 

```
export CATO_HOME=/opt/cato
```

Install prerequisite packages.

Ubuntu:

```
sudo pip install python-tds
```

If you'll be required to authenticate with SQL Server using Windows Domain (NTLM) credentials, you'll also need to install `PyDes`.

```
sudo pip install pydes
```

Thats it!  **automate** can now access MS SQL Server databases.

