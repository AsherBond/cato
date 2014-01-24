#!/usr/bin/env bash

# This will get all the 3rd party UI libs (js and css) we use.

export INSTALL_TO=/var/cato/ui
echo "installing to $INSTALL_TO..."

echo "jQuery"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery-1.10.2.js http://code.jquery.com/jquery-1.10.2.js
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery-1.10.2.min.js http://code.jquery.com/jquery-1.10.2.min.js
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery-1.10.2.min.map http://code.jquery.com/jquery-1.10.2.min.map

echo "jQuery UI"
curl -o $INSTALL_TO/js/jquery/jquery-ui-1.10.3.min.js http://code.jquery.com/ui/1.10.3/jquery-ui.min.js

echo "jQuery Plugins"

echo "base64"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.base64.js https://raw2.github.com/shannoncruey/jQuery.multibyte.base64/master/jquery.base64.js

echo "blockui"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.blockUI.js https://raw2.github.com/malsup/blockui/v2.65/jquery.blockUI.js

echo "cookie"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.cookie.js https://raw2.github.com/carhartl/jquery-cookie/v1.4.0/jquery.cookie.js

echo "rightClick"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.rightClick.js http://labs.abeautifulsite.net/archived/jquery-rightClick/demo/jquery.rightClick.js

echo "scrollTo"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.scrollTo.js https://raw2.github.com/flesler/jquery.scrollTo/1.4.9/jquery.scrollTo.min.js

echo "sortElements"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.sortElements.js https://raw2.github.com/padolsey/jquery.fn/master/sortElements/jquery.sortElements.js

echo "tabby"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.textarea.js https://raw2.github.com/alanhogan/Tabby/master/jquery.textarea.min.js

echo "timepicker"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.timepicker.js https://raw2.github.com/trentrichardson/jQuery-Timepicker-Addon/v0.9.6/jquery-ui-timepicker-addon.js

echo "timers"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.timers.js https://raw2.github.com/patryk/jquery.timers/1.2/jquery.timers.js

echo "tipTip"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.tipTip.js https://raw2.github.com/drewwilson/TipTip/master/jquery.tipTip.minified.js
# NOTE! Not getting the default tipTip.css because we've modified it.
# but, it's mentioned here just in case...
# curl --create-dirs -o $INSTALL_TO/css/tipTip.css https://raw2.github.com/drewwilson/TipTip/master/tipTip.css

# THE JSON EDITOR IS A LITTLE BIT DIFFERENT
echo "jsoneditor"
curl --create-dirs -o $INSTALL_TO/js/jquery/jsoneditor/jsoneditor.js https://raw2.github.com/josdejong/jsoneditor/v2.3.0/jsoneditor-min.js
curl --create-dirs -o $INSTALL_TO/js/jquery/jsoneditor/jsoneditor.css https://raw2.github.com/josdejong/jsoneditor/v2.3.0/jsoneditor-min.css
curl --create-dirs -o $INSTALL_TO/js/jquery/jsoneditor/img/jsoneditor-icons.png https://raw2.github.com/josdejong/jsoneditor/v2.3.0/img/jsoneditor-icons.png

# SUPERFISH IS ALSO A LITTLE MORE THAN ONE FILE
curl --create-dirs -o $INSTALL_TO/js/jquery/superfish/superfish.js https://raw2.github.com/joeldbirch/superfish/1.7.4/dist/js/superfish.min.js
curl --create-dirs -o $INSTALL_TO/js/jquery/superfish/hoverIntent.js https://raw2.github.com/joeldbirch/superfish/1.7.4/dist/js/hoverIntent.js
curl --create-dirs -o $INSTALL_TO/js/jquery/superfish/supersubs.js https://raw2.github.com/joeldbirch/superfish/1.7.4/dist/js/supersubs.js

# We've modified the superfish.css file, so don't get it unless you intend to update it.
# curl --create-dirs -o $INSTALL_TO/css/superfish/superfish.css https://raw2.github.com/joeldbirch/superfish/1.7.4/dist/css/superfish.css

# echo "vkbeautify"
curl --create-dirs -o $INSTALL_TO/js/vkbeautify.js https://raw2.github.com/vkiryukhin/vkBeautify/master/vkbeautify.js

echo "jsonlint"
# There's an additional jsonlint file called jsl.interactions.js.  We heavily modified it to interact with our ui, therefore
# it's included in the Cato source.  Don't get it from here.
curl --create-dirs -o $INSTALL_TO/js/jsonlint/json2.js https://raw2.github.com/arc90/jsonlintdotcom/master/c/js/json2.js
curl --create-dirs -o $INSTALL_TO/js/jsonlint/jsl.format.js https://raw2.github.com/arc90/jsonlintdotcom/master/c/js/jsl.format.js
curl --create-dirs -o $INSTALL_TO/js/jsonlint/jsl.parser.js https://raw2.github.com/arc90/jsonlintdotcom/master/c/js/jsl.parser.js
curl --create-dirs -o $INSTALL_TO/js/jsonlint/LICENSE https://raw2.github.com/arc90/jsonlintdotcom/master/LICENSE

# FOR MAESTRO/LEGATO

##echo "BA postmessage"
### This is the original, but it had an error (opera) that I had to fix.
# curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.ba-postmessage.min.js https://raw2.github.com/cowboy/jquery-postmessage/master/jquery.ba-postmessage.min.js

echo "meow"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.meow.js https://raw2.github.com/zacstewart/Meow/master/jquery.meow.js
curl --create-dirs -o $INSTALL_TO/css/jquery.meow.css https://raw2.github.com/zacstewart/Meow/master/jquery.meow.css

echo "simplemodal"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.simplemodal.js https://raw2.github.com/ericmmartin/simplemodal/v1.4.4/src/jquery.simplemodal.js

# not sure this is working or *really* necessary, but it's referenced in code.
echo "animate-shadow"
curl --create-dirs -o $INSTALL_TO/js/jquery/jquery.animate-shadow-min.js http://www.bitstorm.org/jquery/shadow-animation/jquery.animate-shadow-min.js

