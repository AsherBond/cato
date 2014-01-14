# -*- coding: utf-8 -*-
"""Encapsulates vsphere access for cato purposes.

This module abstracts access to vsphere server and thus:

* insulates the caller from the actual implementation (currently using pysphere)
* allows to morph the interface to seamlessly integrate with cato

Initial functionality:

* connect to vsphere endpoint
* list vms
* list vm properties

Prerequisites:

* pysphere

"""
import os
import logging
from urlparse import urlparse

# use new development version of pysphere when needed in development mode
# import sys
# sys.path.insert(0, '/Users/peter/sw/pysphere-1.7.0.1')

import pysphere
from pysphere import VIServer
from pysphere import MORTypes
from pysphere.version import version as pysphere_version_info
from pysphere.vi_virtual_machine import VMPowerState
from pysphere.resources.vi_exception import VIException


#(0,1,6) -> '0.1.6'
#pysphere_version = '.'.join(pysphere_version_info)

from catoerrors import MissingArgumentError, UnknownPropertyError, \
    UnsupportedVersionError, BadParameterError, InstanceNotFoundError, \
    InternalError
    
# __all__ = [ 'Server', 'VM', 'VMPowerState']

# all property names currently supported
VM_ALL_PROPERTY_NAMES = ['config.instanceUuid',
                          'name',      
                          'overallStatus', 
                          'config.guestFullName',
                          'config.template', 
                          'config.hardware.numCPU',
                          'config.hardware.numCoresPerSocket',
                          'config.hardware.memoryMB',
                          'runtime.powerState',
                          'runtime.host',
                          'guest.ipAddress',
                          'guest.net',
                          'datacenter']

_CUSTOM_PROPERTY_NAMES = {"datacenter": MORTypes.Datacenter}

# default logging location. None for stdout
LOGFILE_DEFAULT = '/dev/tty'
#LOGFILE_DEFAULT = '/opt/log/catosphere.log'
#PROTO_LOGFILE_DEFAULT = '/opt/log/catosphereproto.log'
PROTO_LOGFILE_DEFAULT = '/tmp/catosphereproto.log'
FORMAT = '%(asctime)-15s %(message)s'
logger = None

# determines of protocol details (SOAP request and responses should be logged
prototrace = 0
prototrace_file = None
        
# we are using filtering feature of pysphyere not available prior to trunk r63 
# which is not part of default install via easy_install or pip as of October 2012 
#r63 | argos83@gmail.com | 2012-03-09 04:46:13 -0800 (Fri, 09 Mar 2012) | 3 lines
#Advanced filters parameter in VIServer.get_registered_vms
#see: http://groups.google.com/group/pysphere/browse_thread/thread/15a06606ce774b37/f14f671252b2b82a#f14f671252b2b82a

SUPPORTED_PYSPHERE_VERSION = (0,1,7)
if pysphere_version_info != SUPPORTED_PYSPHERE_VERSION:
    raise UnsupportedVersionError('catosphere only supports pysphere v%s, but this is v%s' % \
                 (SUPPORTED_PYSPHERE_VERSION, pysphere_version_info))


def set_prototrace(dotrace, filename = PROTO_LOGFILE_DEFAULT):
    """Set protocol tracing for SOAP requests and responses.
     
    Example:
    
    >>> set_prototrace(True, '/tmp/vspheresoap.txt')
    
    :type dotrace: bool.
    :param dotrace: determines if protocol tracing should be done
    :param filename: filename to log into. This filename needs to be different 
     from where regular debug logging goes.
    
    """
    global prototrace
    global prototrace_file
    prototrace = dotrace
    if prototrace:
        prototrace_file = filename

def set_debug(level, filename = LOGFILE_DEFAULT):
    """ Initialize logging.
    
     This is useful to override the default if more than one catosphere processes
     are running to prevent writing to the same file. 
     
     To send tracing/debugging information to the console:
     
     >>> set_debug(logging.DEBUG)

     To send tracing/debugging information to a file:
     
     >>> set_debug(logging.DEBUG, '/tmp/catosphere.log')
     
     
    :param level: logging level
    :param filename: filename or filepath to use for logging
    
    """
    global logger
    logging.basicConfig(format=FORMAT, filename=filename)
    logger = logging.getLogger('catosphere')
    logger.setLevel(level)
    
# recommended debug/trace settings for production
#set_debug(logging.INFO, '/dev/tty')
set_debug(logging.INFO, '/dev/stdout')
set_prototrace(False)

# for development:
#set_debug(logging.DEBUG)
#set_prototrace(True)
#set_debug(logging.DEBUG, '/dev/tty')

def get_all_property_names():
    """Returns all supported explicit property names for catosphere.
    
    :rtype: list
    :return: list of strings
    
    """
    logger.debug('get_all_property_names')
    return VM_ALL_PROPERTY_NAMES

class Server():
    """Vsphere server that a client can connect to"""
    
    SUPPORTED_FILTER_KEYWORDS = ['uuidSpec', 'pathSpec', 'nameSpec']
    
    url = os.getenv('VSPHERE_URL')
    """URL of vSphere endpoint"""
    
    #: vSphere account username
    username = os.getenv('VSPHERE_USER')
    
    #: vSphere account password
    password = os.getenv('VSPHERE_PASSWORD')
    
    def __init__(self, url = None, username = None, password = None):
        """Constructs an Server instance with given endpoint and credentials
        
        :param url: end point hostname/URL to connect to.
           As of this release, url must be an http url with port 80, e.g.
           like this: http://vsphere.example.com
           
        :param username: vSphere account username
        :param password: vSphere account password
        
        """
        self._server = VIServer()
        self._vm_datacenters = {}
        
        # don't set to None if already set from environment
        if url:
            self.url = url
        if username:
            self.username = username
        if password:
            self.password = password
        
    def connect(self, url = None, username = None, password = None):
        """Connects to vSphere server using optional arguments
         that may override those in Server constructor.
        If arguments are not given, previously specified arguments will
        be used for connection in this order:
        
        * last connect arguments (if specified)
        * constructor arguments (if specified)
        * environment variables
        
        If none of the above is specified, the exception MissingArgumentException
        is raised
        
        
        :type url: string
        :param url: end point hostname/URL to connect to
        :type username: string
        :param username: vSphere account username
        :type password: string
        :param password: vSphere account password
        :type password: string
        :param password: vSphere account password
        
        """
        if url:
            self.url = url
        if username:
            self.username = username
        if password:
            self.password = password
            
        # check if all needed properties available for connect
        argErrors = []
        if not self.url:
            argErrors.append('url unknown') 
        if not self.username:
            argErrors.append('username unknown') 
        if not self.password:
            argErrors.append('password unknown') 
            
        if argErrors:
            raise MissingArgumentError(' '.join(argErrors))
        # parse host from url
        host = urlparse(self.url).hostname
        # perform connect
        logger.debug('connect: %s; %s' % (url, username))
        self._server.connect(host, self.username, self.password, 
                             trace_file = prototrace_file)
    
    def disconnect(self):
        """Disconnects from vSphere server"""
        self._server.disconnect()
        self._server = []
    
    
    def power_on_vm(self, instanceUuid, sync_run=True, host=None):
        """Powers on a virtual machine for a given instanceUuid"""
        return self._get_instance(instanceUuid).power_on(sync_run, host)

    def power_off_vm(self, instanceUuid, sync_run=True):
        """Powers off a virtual machine for a given instanceUuid"""
        return self._get_instance(instanceUuid).power_off(sync_run)

    def clone_vm(self, instanceUuid, name = None, sync_run=True, host=None):
        """Clones a virtual machine for a given instanceUuid.
        
        :param instanceUuid: instanceUuid of VM to clone
        :param name: name to give to the cloned machine.
         if None, a new name will be generated using the original instance
         name with time stamp appended, e.g.:
         'ubuntu_csk1_08-1349968939'
         
        """
        import time
        instance = self._get_instance(instanceUuid)
        if not name:
            name = '%s-%d' % (instance.get_property('name'), time.time())
        return instance.clone(name, sync_run, host=host)

    def reset_vm(self, instanceUuid, sync_run=True):
        """Powers off a virtual machine for a given instanceUuid"""
        return self._get_instance(instanceUuid).reset(sync_run)

    def suspend_vm(self, instanceUuid, sync_run=True):
        """Suspends a virtual machine for a given instanceUuid"""
        return self._get_instance(instanceUuid).suspend(sync_run)

    def list_instances(self, instanceUuid = None, filter = None, datacenter = None):
        """Lists all vmware instances that match the given filter.

        :type instanceUuid: string
        :param instanceUuid: InstanceUuid to filter on. This is a convenience
          parameter that will override a corresponding value in filter, 
          if it exists. 
          
        :param datacenter: name of datacenter to filter VMs registered in that datacenter

        :type filter: dict
        :param filter: represents a filter specification and can consist of 
            any valid properties, such as
            
            { 'config.instanceUuid': [ '50398c64-55ad-7eb2-f14a-6f70b6903b06' ] }
            
            or
            
            {'runtime.powerState': ['poweredOn']}
            
            or
            
            {'runtime.powerState': ['poweredOff'], 'config.instanceUuid': [ '50398c64-55ad-7eb2-f14a-6f70b6903b06' ] }
            


        :rtype: list
        :return: A list of :class:`vmware.vsphere.VM`
        
        """
                
        # get the vm paths
        if instanceUuid and len(instanceUuid):
            if not isinstance(instanceUuid, str):
                raise BadParameterError('instanceUuid parameter must be a string')
            if not filter:
                filter = {}
            filter['config.instanceUuid'] = [instanceUuid]
            
        self._vmspaths = self._server.get_registered_vms(datacenter, advanced_filters = filter)
        logger.debug('list_instances: retrieved %d vm paths' % len(self._vmspaths))
        # instantiate instances for vm paths
        self.vms = []
        for p in self._vmspaths:
            self.vms.append(VM(p, self))
        
        # first time this function runs, fetch information about vm to datacenter mapping
        self._fetch_datacenter_vms()
        return self.vms
    
    def get_hosts(self, datacenter = None):
        """Returns a dictionary of the existing hosts keys are their names
        and values their ManagedObjectReference object.
        
        Example usage:
        >>> server.get_hosts()
        {'host-23': '108.61.71.220', 'host-19': '108.61.71.219', 'host-36': '173.71.195.168'}
        >>> server.get_hosts('datacenter-12')
        >>> from catosphere import Server
        >>> server = Server()
        >>> server.connect()
        >>> server.get_datacenters()
        {'datacenter-12': 'csk3', 'datacenter-2': 'csk1', 'datacenter-7': 'csk2'}
        >>> server.get_hosts('datacenter-2')
        {'host-23': '108.61.71.220', 'host-19': '108.61.71.219'}
        >>> server.get_hosts('datacenter-7')
        {'host-36': '173.71.195.168'}
        >>> server.get_hosts('datacenter-12')
        {}
        >>> server.get_hosts()
        {'host-23': '108.61.71.220', 'host-19': '108.61.71.219', 'host-36': '173.71.195.168'}
        >>> server.disconnect()
        
        
        :return: a dict   
         e.g.
        {'host-23': '108.61.71.220', 'host-19': '108.61.71.219', 'host-36': '173.71.195.168'}
        if not hosts are found, empty dict is returned.

        """
        if datacenter:
            hosts = self._server._get_managed_objects(MORTypes.HostSystem, from_mor=datacenter)
        else:
            hosts = self._server.get_hosts()
        return hosts

    def get_datacenters(self):
        """Returns a dictionary of the existing datacenters. keys are their
        ManagedObjectReference objects and values their names.
                
        :return: a dict   
         e.g.
        {'datacenter-12': 'csk3', 'datacenter-2': 'csk1', 'datacenter-7': 'csk2'}

        """
        return self._server.get_datacenters()
    
    #******************************************************
    # ***************** Private Methods *******************
    #******************************************************

    
    def _fetch_datacenter_vms(self):
        """ Fetch/cache datacenter vm mapping information.
        
        This can be later used to retrieve datacenter information for each
        VM.
        """
        if not self._vm_datacenters:
            dcs = self.get_datacenters()
            for name in dcs.keys():
                self._vm_datacenters[name] = self._server._get_managed_objects(MORTypes.VirtualMachine, from_mor=name)
                
            #logger.debug(': _vm_datacenters: %s' % self._vm_datacenters)
    
    def _get_instance(self, instanceUuid):
        """ Retrieves instance by its instanceUuid.
        
        TODO: make this faster by caching instances.
        """
        instances = self.list_instances(instanceUuid)
        if not instances:
            raise InstanceNotFoundError('Instance %s not found' % instanceUuid)
        else:
            return instances[0]

class VM:
    """Vsphere vmware virtual machine as queried from Server.
    
    The internal implementation fetches actual vm path from the server
    on demand, i.e. not until a property is requested or an operation
    invoked.
    
    """
    
    def __init__(self, path, server):
        # wrapped underlying vm
        self._path = path
        # internal vm object cached on demand
        self._vm = None
        self._server = server._server
        self.server = server
        self._custom_properties = {}
    
    @property
    def path(self):
        """Retrieves path for this VM"""
        return self._path


    def _ensureVMFetch(self):
        """Ensure VM is fetched from server"""
        # retrieve vm instance from server, if not already catched
        if not self._vm:
            self._vm = self._server.get_vm_by_path(self._path)
                
    def get_property(self, name):
        """ Retrieves Property from VM.
        
        TODO: provide a way to invalidate cache for regular and custom 
        properties
        
        :type name: string
        :param name: name of property to retrieve
        
        :rtype: string or dict
        :return: Property value or None if the property doesn't exist for this 
         instance. For example ipAddress may not be available unless the 
         instance is powered on and vmware tools are installed on the instance.
         
         All properties are strings, except guest.net which is a dict of this 
         form:
          {'ip_addresses': ['108.61.2.26', 'fe80::250:56ff:feb3:5ba3'], 
            'connected': True, 
            'network': 'VM Network', 
            'mac_address': '00:50:56:b3:5b:a3'}
            
        
        """
        self._ensureVMFetch()
            
        if name == 'config.instanceUuid':
            val = self._vm.properties.config.instanceUuid
        elif name == 'config.uuid':
            val = self._vm.properties.config.uuid
        elif name == 'name':
            val = self._vm.properties.name
        elif name == 'config.template':
            val = self._vm.properties.config.template
        elif name == 'overallStatus':
            val = self._vm.properties.overallStatus
        elif name == 'config.guestFullName':
            val = self._vm.properties.config.guestFullName
        elif name == 'config.alternateGuestName':
            val = self._vm.properties.config.alternateGuestName
        elif name == 'config.hardware.numCPU':
            val = self._vm.properties.config.hardware.numCPU
        elif name == 'config.hardware.numCoresPerSocket':
            val = self._vm.properties.config.hardware.numCoresPerSocket
        elif name == 'config.hardware.memoryMB':
            val = self._vm.properties.config.hardware.memoryMB
        elif name == 'runtime.host':
            val = self._vm.properties.runtime.host._obj
        elif name == 'runtime.powerState':
            val = self._vm.properties.runtime.powerState
        elif name == 'guest.ipAddress':
            if hasattr(self._vm.properties.guest, 'ipAddress'):
                val = self._vm.properties.guest.ipAddress
            else:
                val = None
        elif name == 'guest.net':
            #val = self._vm.properties.guest.net
            # We use an alternative way of retriving property here which unfolds 
            # it into a dict
            val = self._vm._properties.get('net')
            if val and isinstance(val, list) and len(val) == 1:
                val = val[0]
            else:
                if val:
                    # TODO: remove this once it's verified with testing that
                    #  this is expected format.
                    raise InternalError('Unexpected inernal format for net property')
                    #logger.error('Unexpected inernal format for net property')
                
        else:
            if self._is_custom_property(name):
                # check if in cache
                val = self._custom_properties.get(name)
                if val is None:
                    # fetch if not in cache
                    val = self._fetch_custom_property(name)
            else:
                val = self._vm._properties.get(name)
                if val is None:
                    raise UnknownPropertyError(name)
                else:
                    logger.warning('get_property: unregistered property %s=%s' % (name,val))
                    
        return val
        
        #logger.debug("runTestPySphere: after get_vm_by_path: ;%f" % resident())
        #msg = '%s %s %s %s' %( vm.properties.config.guestFullName, vm.properties.name, \
        #  vm.properties.overallStatus, vm.properties.config.template)
    def get_property_names(self):
        """Returns all supported property names for this VM.
        
        :rtype: list
        :return: list of strings
        
        """
        logger.debug('get_property_names')
        return VM_ALL_PROPERTY_NAMES
    
    def get_properties(self):
        """ Retrieves all properties from VM.
        
          Note: this operation is lesss efficient than retrieving one or
          more individual properties by name using get_property method. 
          
        :rtype: list
        :return: list of values
        """
        logger.debug('get_properties')
        ret = []
        self._ensureVMFetch()
        for n in VM_ALL_PROPERTY_NAMES:
            #ret.append((n, self.get_property(n)))
            ret.append(self.get_property(n))            
        return ret

    #******************************************************
    #*************** Power cycle methods ******************
    #******************************************************
    def power_off(self, sync_run=True):
        """ Power off the VM. 
        
        :param sync_run: if False, run in async mode, otherwise run in sync mode
        """
        logger.debug('power_off: %s' % sync_run)
        self._ensureVMFetch()
        return self._vm.power_off(sync_run)

    def power_on(self, sync_run=True,host=None):
        """ Power on the VM. 
        
        :param sync_run: if False, run in async mode, otherwise run in sync mode
        """
        logger.debug('power_on: sunc_run=%s, host=%s' % (sync_run, host))
        self._ensureVMFetch()
        return self._vm.power_on(sync_run, host)

    def reset(self, sync_run=True):
        """ Reset the VM. 
        
        :param sync_run: if False, run in async mode, otherwise run in sync mode
        """
        logger.debug('reset: %s' % sync_run)
        self._ensureVMFetch()
        return self._vm.reset(sync_run)

    def suspend(self, sync_run=True):
        """ Suspend the VM. 
        
        :param sync_run: if False, run in async mode, otherwise run in sync mode
        """
        logger.debug('suspend: %s' % sync_run)
        self._ensureVMFetch()
        return self._vm.suspend(sync_run)

    # in latest v. of pysphere, this is the case:
    #def clone(self, name, sync_run=True, folder=None, resourcepool=None, 
    #          datastore=None, host=None, power_on=True, template=False, 
    #          snapshot=None, linked=False):
        
    def clone(self, name, sync_run=True, folder=None, resourcepool=None, 
              datastore=None, host=None, power_on=True):
        """Clones this Virtual Machine
        
        
        
        TODO: DOC STRING:
        :param name: name of the new virtual machine
        :param sync_run: if True (default) waits for the task to finish, and returns
         a VIVirtualMachine instance with the new VM (raises an exception if 
         the task didn't succeed). If sync_run is set to False the task is 
         started and a VITask instance is returned
        :param folder: name of the folder that will contain the new VM, if not set
         the vm will be added to the folder the original VM belongs to
        :param resourcepool: MOR of the resourcepool to be used for the new vm. 
         If not set, it uses the same resourcepool than the original vm.
        :param datastore: MOR of the datastore where the virtual machine
            should be located. If not specified, the current datastore is used.
        :param host: MOR of the host where the virtual machine should be registered.
            IF not specified:
              * if resourcepool is not specified, current host is used.
              * if resourcepool is specified, and the target pool represents a
                stand-alone host, the host is used.
              * if resourcepool is specified, and the target pool represents a
                DRS-enabled cluster, a host selected by DRS is used.
              * if resource pool is specified and the target pool represents a 
                cluster without DRS enabled, an InvalidArgument exception be
                thrown.
        :param power_on: If the new VM will be powered on after being created. If
            template is set to True, this parameter is ignored.
        :param template: Specifies whether or not the new virtual machine should be 
            marked as a template.         
        :param snapshot: Snaphot MOR, or VISnaphost object, or snapshot name (if a
            name is given, then the first matching occurrence will be used). 
            Is the snapshot reference from which to base the clone. If this 
            parameter is set, the clone is based off of the snapshot point. This 
            means that the newly created virtual machine will have the same 
            configuration as the virtual machine at the time the snapshot was 
            taken. If this parameter is not set then the clone is based off of 
            the virtual machine's current configuration.
        :param linked: If True (requires @snapshot to be set) creates a new child disk
            backing on the destination datastore. None of the virtual disk's 
            existing files should be moved from their current locations.
            Note that in the case of a clone operation, this means that the 
            original virtual machine's disks are now all being shared. This is
            only safe if the clone was taken from a snapshot point, because 
            snapshot points are always read-only. Thus for a clone this option 
            is only valid when cloning from a snapshot
        """
        logger.debug('clone: name, sync_run, folder, resourcepool, datastore, host, power_on : %s, %s, %s, %s, %s, %s, %s' % \
                     (name, sync_run, folder, resourcepool, datastore, host, power_on))
        self._ensureVMFetch()
        
        return self._vm.clone(name, sync_run, folder, resourcepool, datastore,
              host, power_on)

    #******************************************************
    #*************** Status query methods *****************
    #******************************************************
        
    def get_status(self):
        """ Fetches the status/power stage of the VM from the server.
        
        :return: string representing the status / power stage of VM
         See  :class:`vmware.vsphere.VMPowerState`
        """
        self._ensureVMFetch()
        logger.debug('get_status')
        status = self._vm.get_status()
        logger.debug('get_status: %s' % status)
        return status
    
    def is_powering_off(self):
        """Returns True if the VM is being powered off"""
        self._ensureVMFetch()
        return self._vm.is_powering_off()

    def is_powered_off(self):
        """Returns True if the VM is powered off"""
        self._ensureVMFetch()
        return self._vm.is_powered_off()

    def is_powering_on(self):
        """Returns True if the VM is being powered on"""
        self._ensureVMFetch()
        return self._vm.is_powering_on()

    def is_powered_on(self):
        """Returns True if the VM is powered off"""
        self._ensureVMFetch()
        return self._vm.is_powered_on()

    def is_suspending(self):
        """Returns True if the VM is being suspended"""
        self._ensureVMFetch()
        return self._vm.is_suspending()

    def is_suspended(self):
        """Returns True if the VM is suspended"""
        self._ensureVMFetch()
        return self._vm.is_suspended()

    def is_resetting(self):
        """Returns True if the VM is being resetted"""
        self._ensureVMFetch()
        return self._vm.is_resetting()

    def is_blocked_on_msg(self):
        """Returns True if the VM is blocked because of a question message"""
        self._ensureVMFetch()
        return self._vm.is_blocked_on_msg()

    def is_reverting(self):
        """Returns True if the VM is being reverted to a snapshot"""
        self._ensureVMFetch()
        return self._vm.is_reverting()
        
    #******************************************************
    #************ Snapshot Management methods *************
    #******************************************************
    
    def revert_to_snapshot(self, sync_run=True, host=None):
        """ Revert to snaphost. 
        
        :param sync_run: if False, run in async mode, otherwise run in sync mode
        :param host: managed object reference to a host where the VM should be
         reverted at.
        """
        logger.debug('revert_to_snapshot: %s' % sync_run)
        self._ensureVMFetch()
        return self._vm.revert_to_snapshot(sync_run, host=host)
        
    def revert_to_named_snapshot(self, name, sync_run=True, host=None):
        """ Revert to named snaphost. 
        
        :param name: name of snapshot to revert to
        :param sync_run: if False, run in async mode, otherwise run in sync mode
        :param host: managed object reference to a host where the VM should be
         reverted at.
        """
        logger.debug('revert_to_named_snapshot: %s' % sync_run)
        self._ensureVMFetch()
        return self._vm.revert_to_named_snapshot(name, sync_run, host=host)
    
    def revert_to_path(self, path, index=0, sync_run=True, host=None):
        """ Attemps to revert the VM to the snapshot of the given path and index
        (to disambiguate among snapshots with the same path, default 0).
        
        
        :param path: path of snapshot to revert to
        :param index: index of path of snapshot to revert to
        :param sync_run: if False, run in async mode, otherwise run in sync mode
        :param host: managed object reference to a host where the VM should be
         reverted at.
        """
        logger.debug('revert_to_path: %s' % sync_run)
        self._ensureVMFetch()
        return self._vm.revert_to_path(path, index, sync_run, host=host)

    def create_snapshot(self, name, sync_run=True, description=None,
                        memory=True, quiesce=True):
        """
        Takes a snapshot of this VM.
        
        :param name: name of snapshot
        :param sync_run: if True (default) waits for the task to finish, and returns
            (raises an exception if the task didn't succeed). If False the task
            is started an a VITask instance is returned.
        :param description: A description for this snapshot. If omitted, a default
            description may be provided.
        :param memory: If True, a dump of the internal state of the virtual machine
            (basically a memory dump) is included in the snapshot. Memory
            snapshots consume time and resources, and thus take longer to
            create. When set to FALSE, the power state of the snapshot is set to
            powered off.
        :param quiesce: If True and the virtual machine is powered on when the
            snapshot is taken, VMware Tools is used to quiesce the file system
            in the virtual machine. This assures that a disk snapshot represents
            a consistent state of the guest file systems. If the virtual machine
            is powered off or VMware Tools are not available, the quiesce flag
            is ignored. 
        """
        logger.debug('create_snapshot: %s' % sync_run)
        self._ensureVMFetch()
        return self._vm.create_snapshot(name, sync_run, description,
                        memory, quiesce)
        
    def delete_current_snapshot(self, remove_children=False, sync_run=True):
        """Removes the current snapshot. 
        
        :param remove_children: if True, removes
         all the snapshots in the subtree as well.
        :param sync_run: if True (default) waits for the task to finish, and returns
            (raises an exception if the task didn't succeed). If False the task
            is started an a VITask instance is returned.
            
         """
        logger.debug('delete_current_snapshot: %s' % sync_run)
        self._ensureVMFetch()
        return self._vm.delete_current_snapshot(remove_children, sync_run)

    def delete_named_snapshot(self, name, remove_children=False, sync_run=True):
        """Removes the current snapshot. 
        
        :param name: name of snapshot to delete
        :param remove_children: if True, removes
         all the snapshots in the subtree as well.
        :param sync_run: if True (default) waits for the task to finish, and returns
            (raises an exception if the task didn't succeed). If False the task
            is started an a VITask instance is returned.
            
         """
        logger.debug('delete_named_snapshot: %s' % sync_run)
        self._ensureVMFetch()
        return self._vm.delete_named_snapshot(name, remove_children, sync_run)

    def delete_snapshot_by_path(self, path, index = 0, remove_children=False, sync_run=True):
        """ Removes the VM snapshot of the given path and index (to disambiguate
        among snapshots with the same path, default 0).  
        
        :param path: path of snapshot to delete
        :param index: index of path of snapshot to delete
        :param remove_children: if True, removes
         all the snapshots in the subtree as well.
        :param sync_run: if True (default) waits for the task to finish, and returns
            (raises an exception if the task didn't succeed). If False the task
            is started an a VITask instance is returned.
            
         """
        logger.debug('delete_snapshot_by_path: %s' % sync_run)
        self._ensureVMFetch()
        return self._vm.delete_snapshot_by_path(path, index, remove_children, 
                                                sync_run)
    
    def refresh_snapshot_list(self):
        """Refreshes the internal list of snapshots of this VM"""
        logger.debug('refresh_snapshot_list')
        self._ensureVMFetch()
        self._vm.refresh_snapshot_list()    

    def get_snapshots(self):
        """Returns a list of VISnapshot instances of this VM"""
        self._ensureVMFetch()
        return self._vm._snapshot_list[:]

    def get_current_snapshot_name(self):
        """Returns the name of the current snapshot (if any)."""
        self._ensureVMFetch()
        return self._vm.get_current_snapshot_name()
                
    def __repr__(self):
        return '%s' % self._path

    def __str__(self):
        return '%s' % self._path



    # ***************** Private Methods *******************
        
    def _is_custom_property(self, name):
        """Returns true if given name is a custom property name"""
        return name in _CUSTOM_PROPERTY_NAMES


    def _fetch_custom_property(self, name):
        """ Fetches property from server """
        logger.debug("Fetching property %s" % name)
        mortype = _CUSTOM_PROPERTY_NAMES.get(name)
        logger.debug('_fetch_custom_property: retrieving %s for %s' % (mortype, self._vm._mor))
        #value = self._server._get_managed_objects(mortype, from_mor=self._vm._mor)
        
        value = "datacenter-12"
        logger.debug("Fetched %s=%s" % (name, value))
        self._custom_properties[name] = value
        return value

