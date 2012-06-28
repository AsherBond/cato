#!/bin/bash
DEPLOY_DIR=/opt/cato
COMPONENT=3
SILENT=0
if [ ! -n "$1" ]
then
	read -p "Enter a target directory. (default: $DEPLOY_DIR): " dir
	if [ "$dir" != "" ]; then
		DEPLOY_DIR=$dir
	fi	
	echo ""
	echo "Components, 1 = web, 2 = services, 3 = all"
	read -p "Enter a component to install. (1,2,3; default: 3): " dir
	if [ "$dir" = "" ]; then
		COMPONENT=3
	else
		COMPONENT=$dir
	fi
else
	while getopts ":c:t:s" opt
	do
	    case "$opt" in
	      c)  COMPONENT="$OPTARG";;
	      s)  SILENT=1;;
	      t)  DEPLOY_DIR="$OPTARG";;
	      \?)               # unknown flag
		  echo >&2 \
		  "usage: $0 [-s] [-t targetpath] [-c component (1|2|3)]"
		  echo "        -s      silent operation" 
		  echo "        -t      path to install to" 
		  echo "        -c      1 = web, 2 = service, 3 = both"
		  exit 1;;
	    esac
	done
	shift `expr $OPTIND - 1`
fi
if [ $SILENT = 0 ]
then 
	echo "target = $DEPLOY_DIR, installing component = $COMPONENT, silent = $SILENT"
	echo "Installing to $DEPLOY_DIR ..."
fi

# common for all
if [ $SILENT = 0 ]
then 
	echo "Copying common files..."
fi

mkdir -p $DEPLOY_DIR

cp -R conf $DEPLOY_DIR/.
cp -R util $DEPLOY_DIR/.
cp -R lib $DEPLOY_DIR/.

cp -R NOTICE $DEPLOY_DIR/.
cp -R LICENSE $DEPLOY_DIR/.
cp -R VERSION $DEPLOY_DIR/.
cp -R TODO $DEPLOY_DIR/.
cp -R README $DEPLOY_DIR/.


# web
if [ "$COMPONENT" = "1" -o "$COMPONENT" = "3" ]
then

	if [ $SILENT = 0 ]
	then 
		echo "Copying web files..."
	fi

    cp -R web $DEPLOY_DIR/.

fi

#services
if [ "$COMPONENT" = "2" -o "$COMPONENT" = "3" ]
then

	if [ $SILENT = 0 ]
	then 
		echo "Copying services files..."
	fi

	cp -R services $DEPLOY_DIR/.

	if [ $SILENT = 0 ]
	then 
		echo "Creating services link to conf dir..."
	fi

fi

if [ $SILENT = 0 ]
then 
	echo "... Done"
fi








