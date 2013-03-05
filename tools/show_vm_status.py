#!/usr/bin/env python
""" Tool to continuously show vsphere vm status in a loop """

import sys
import time
import logging
from catosphere import Server, set_debug

# delay between status fetches
DELAY = 5

# avoid writing to another processes libvmware log
set_debug(logging.INFO, '/opt/log/vmtools.log')

def main(argv=None):
    server = Server()
    server.connect()
    instances = server.list_instances()
    print('Retrieved %d instances' % len(instances))
    if len(instances) > 0:
        print('Found the following instances on server %s' % server.url)
        for i in instances:
            print('%s' % i)
    
        if len(instances) > 0:
            i = instances[0]
            print('Status of %s called at 5s interval:' % i)
            while(True):
                print('%s: %s' % (time.asctime(), i.get_status()))   
                time.sleep(DELAY)
    else:
        print("Didn't find any instances on server %s" % server.url)

    server.disconnect()


if __name__ == "__main__":
    sys.exit(main(sys.argv))


