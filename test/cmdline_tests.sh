#!/usr/bin/env bash

# this script should be run from the CATO_HOME directory, not from the test directory

#set -e

echo "running pylint tests ..."
find . -path ./.env -prune -o -name "*.py" | xargs pylint --rcfile=test/pylint.conf -E --disable=E1101,E1103,E0611,E0102,E0702 > test/test_output/pylint.txt

echo "running pep8 tests ..."
pep8 --exclude=.env,.git --ignore=W291,E501,W293,E302,E303,E203,E121,W191,E128,E251,E101,E301,E122,E261,E231,E123,E127,W391,E211 lib extensions src checkdb.py updatedb.py > test/test_output/pep8.txt

echo "running jslint tests, part 1 ..."
jshint --reporter=jslint --config test/jshint.conf ui/admin/static/script/*.js > test/test_output/jslint.txt

echo "running jslint tests, part 2 ..."
jshint --reporter=jslint --config test/jshint.conf ui/admin/static/script/taskedit/*.js >> test/test_output/jslint.txt

echo "command line tests completed"
