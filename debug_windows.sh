osascript -e 'tell application "Terminal" to do script "cd $CATO_HOME/logfiles;tail -f cato_admin_ui.log;"'
osascript -e 'tell application "Terminal" to do script "cd $CATO_HOME/logfiles;tail -f cato_rest_api.log;"'