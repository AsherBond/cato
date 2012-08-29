#!/bin/bash

echo "### REST API ###"
tail -10 $CATO_HOME/logfiles/cato_rest_api.log


echo "### ADMIN UI ###"
tail -10 $CATO_HOME/logfiles/cato_admin_ui.log