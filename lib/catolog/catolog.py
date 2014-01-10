# Copyright 2012 Cloud Sidekick
#  
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  
#     http:# www.apache.org/licenses/LICENSE-2.0
#  
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
    THIS is the class responsible for configuring the Cato logging subsystem
    and handing out loggers to Cato modules.
    
    ALL Cato modules import this file.
"""

# this module SHOULD be loaded first by all other Cato modules
# therefore a basic initial setup of the logger here is necessary.
import logging
from logging import handlers, config
import sys
import os.path
from catoconfig import catoconfig

# ALL Cato modules import this, and it should be one of the first imports.
LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s :: %(message)s\n"
LOGPATH = ""
LOGFILE = ""

# THESE WILL BE SET by the program that imports this module.
# the debug level (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL)  
DEBUG = 20
CLIENTDEBUG = 20

def get_logger(name):
    """
    Will get a logger.  Handlers will be defined by a call to set_logfile.
    """
    # if you're curious what loggers are defined...
    # print logging.Logger.manager.loggerDict

    # print "getting a logger for [%s] at debug level [%s]..." % (name, DEBUG)
    l = logging.getLogger(name)
    l.setLevel(DEBUG)
    return l

def _redirect_stdout():
    """
    Split this into it's own function so we can apply a different formatter to the stdout/err streams.
    
    This will make them more recognizable in the log, plus many 3rd party tools (like web.py)
    report all messages to stderr and we don't want them displayed as ERROR.
    """
    stdout_logger = logging.getLogger('STDOUT')
    stderr_logger = logging.getLogger('STDERR')
    
    # a file handler only for these two streams
    # with a different format
    formatter = logging.Formatter("%(msg)s")
    fh = logging.FileHandler(LOGFILE)
    fh.setFormatter(formatter)

    stdout_logger.propagate = 0
    stdout_logger.addHandler(fh)
    stderr_logger.propagate = 0
    stderr_logger.addHandler(fh)
    
    sys.stdout = StreamToLogger(stdout_logger, logging.INFO)
    sys.stderr = StreamToLogger(stderr_logger, logging.CRITICAL)

    
def _get_logfiles_path():
    # logfiles go where defined in cato.conf, but in the base_path if not defined
    return catoconfig.CONFIG["logfiles"] if catoconfig.CONFIG["logfiles"] else os.path.join(catoconfig.BASEPATH, "logfiles")
    
def set_debug(debug):
    # set the root logger
    l = logging.getLogger()
    l.setLevel(int(debug))

    # and everything else that was defined
    # but this would fail on Placeholder objects, so catch that
    try:
        for l in logging.Logger.manager.loggerDict.itervalues():
            l.level = (int(debug))
    except:
        pass
#    for handler in l.handlers:
#        handler.setLevel(int(debug))
    
# the LOGFILE is set by the parent program.  It's a full path, not just a name.
def set_logfile(logfile):
    """ 
    Initialize logging.  Can be called multiple times to update settings.
    
    THIS SETS UP the global "logging" module. Does not affect any explicit user-defined Logger instances. 
    
    :param filename: filename or filepath to use for logging
    
    """
    global LOGFILE
    LOGFILE = logfile

    # create the log directory if it's not already there
    dirs = os.path.dirname(LOGFILE)
    if not os.path.exists(dirs):
        os.makedirs(dirs)

    # print "...setting up a file handler using [%s]" % LOGFILE
    # add the file handler to the root logger
    root = logging.getLogger()
    
    # doing this removes the originally defined stream handler.
    # this has pros and cons
    # PROS - nothing will be streamed to stdout and need to be shoved off to dev/null
    # CONS - nothing will be streamed to stdout, so if you run the process in a terminal there's no output
    # I've flipped this on and off at least a dozen times... grrrrr...
    for handler in root.handlers:
        root.removeHandler(handler)

    formatter = logging.Formatter(LOGFORMAT)
    # fh = logging.FileHandler(LOGFILE)
    fh = handlers.TimedRotatingFileHandler(LOGFILE, when='d', interval=1, backupCount=30)
    fh.setFormatter(formatter)
    root.addHandler(fh)
    
    # we are redirecting stdout and stderr to the logging system.
    # but it'll have a different file handler and formatter
    redirect = True
        
    if redirect:
        _redirect_stdout()

class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        # self.linebuf = ''
    
    def flush(self):
        pass


    def write(self, buf):
        if buf and buf != "\n":
            msg = buf.rstrip()
            # this also can suppress HTTP messages from the built in web server
            # NOTE: this is a specific pattern that matches the web.py output
            if "write_http_logs" in catoconfig.CONFIG:
                if catoconfig.CONFIG["write_http_logs"] == "false":
                    if 'HTTP/1.1' in "".join(msg):
#                        self.logger.log(logging.INFO, "".join(msg))
                        return
                
            self.logger.log(self.log_level, "".join(msg))

logging.basicConfig(level=logging.DEBUG, format="%(msg)s")
# logging.config.dictConfig({
#     'version': 1,
#     'disable_existing_loggers': False
# })
LOGPATH = _get_logfiles_path()


