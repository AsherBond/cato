# -*- coding: utf-8 -*-
"""Encapsulates libcloud access for cato purposes.

This module abstracts access to libcloud library. The objective is to
 allow to adjust the interface to  seamlessly integrate with cato

Initial functionality:

* connect to libcloud endpoint
* list images
* list vm properties

Prerequisites:

* libcloud

"""
import os
import logging
import libcloud
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.deployment import MultiStepDeployment, ScriptDeployment, SSHKeyDeployment

from catoerrors import MissingArgumentError, UnknownPropertyError, UnsupportedVersionError
from tarfile import SUPPORTED_TYPES

# __all__ = [ 'CloudProvider', 'Image', 'Instance']

SUPPORTED_LIBCLOUD_VERSION = '0.11.1'
if libcloud.__version__ != SUPPORTED_LIBCLOUD_VERSION:
    raise UnsupportedVersionError('catolc only supports libcloud v%s, but this is v%s' %
                 (SUPPORTED_LIBCLOUD_VERSION, libcloud.__version__))

# default logging location.
# logging to stdout
LOGFILE_DEFAULT = '/dev/tty'
# LOGFILE_DEFAULT = '/opt/log/catolc.log'
FORMAT = '%(asctime)-15s %(message)s'
logger = None

# openstack specific support info
AUTH_VERSION = '2.0_password'

# providers that require use of auth_url
OPENSTACK_PROVIDERS = [Provider.RACKSPACE_NOVA_BETA, Provider.RACKSPACE_NOVA_DFW, Provider.OPENSTACK]

# libcloud.compute.types implements class Provider
# we are using the definition as of libcloud-0.11.1 9/18/12
# to enumerate all providers
# this may change in a future version, therefore we enforce libcloud version
# at load time

ALL_PROVIDERS_MAP = {
    "DUMMY": 0,
    "EC2": 1,  # deprecated name
    "EC2_US_EAST": 1,
    "EC2_EU": 2,  # deprecated name
    "EC2_EU_WEST": 2,
    "RACKSPACE": 3,
    "SLICEHOST": 4,
    "GOGRID": 5,
    "VPSNET": 6,
    "LINODE": 7,
    "VCLOUD": 8,
    "RIMUHOSTING": 9,
    "EC2_US_WEST": 10,
    "VOXEL": 11,
    "SOFTLAYER": 12,
    "EUCALYPTUS": 13,
    "ECP": 14,
    "IBM": 15,
    "OPENNEBULA": 16,
    "DREAMHOST": 17,
    "ELASTICHOSTS": 18,
    "ELASTICHOSTS_UK1": 19,
    "ELASTICHOSTS_UK2": 20,
    "ELASTICHOSTS_US1": 21,
    "EC2_AP_SOUTHEAST": 22,
    "RACKSPACE_UK": 23,
    "BRIGHTBOX": 24,
    "CLOUDSIGMA": 25,
    "EC2_AP_NORTHEAST": 26,
    "NIMBUS": 27,
    "BLUEBOX": 28,
    "GANDI": 29,
    "OPSOURCE": 30,
    "OPENSTACK": 31,
    "SKALICLOUD": 32,
    "SERVERLOVE": 33,
    "NINEFOLD": 34,
    "TERREMARK": 35,
    "EC2_US_WEST_OREGON": 36,
    "CLOUDSTACK": 37,
    "CLOUDSIGMA_US": 38,
    "EC2_SA_EAST": 39,
    "RACKSPACE_NOVA_BETA": 40,
    "RACKSPACE_NOVA_DFW": 41,
    "LIBVIRT": 42,
    "ELASTICHOSTS_US2": 43,
    "ELASTICHOSTS_CA1": 44,
    "JOYENT": 45,
    "VCL": 46,
    "KTUCLOUD": 47,
    "RACKSPACE_NOVA_LON": 48,
    "GRIDSPOT": 49,
    }


def set_debug(level, filename='/dev/tty'):
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
    logger = logging.getLogger('catolc')
    logger.setLevel(level)

set_debug(logging.INFO)
# set_debug(logging.INFO, '/tmp/catolc.log')

def list_providers(filterspec=None):
    """ Lists all providers
    
    Sample usage:
    
    >>> catolc.list_providers('rack')
    ['RACKSPACE_NOVA_DFW', 'RACKSPACE', 'RACKSPACE_UK', 'RACKSPACE_NOVA_LON', 'RACKSPACE_NOVA_BETA']
    >>> catolc.list_providers('ec2')
    ['EC2_AP_SOUTHEAST', 'EC2_US_EAST', 'EC2_US_WEST_OREGON', 'EC2_US_WEST', 'EC2_AP_NORTHEAST', 'EC2', 'EC2_EU', 'EC2_EU_WEST', 'EC2_SA_EAST']
    
        :type filter: string
        :param filterspec: Case insensitive filter string to use to filter the providers. 
    
        :rtype: list
        :return: A list of strings    
    """
    ret = ALL_PROVIDERS_MAP.keys()

    # apply filter if specified
    if filterspec:
        fs = filterspec.upper()
        ret = filter(lambda x: x.upper().find(fs) >= 0, ret)

    return ret

class CloudProvider:
    """Libcloud connection to the cloud service provider"""

    url = os.getenv('LC_AUTH_URL')
    username = os.getenv('LC_AUTH_USERNAME')
    password = os.getenv('LC_AUTH_PASSWORD')

    def __init__(self, provider, auth_url=None, username=None, password=None):
        """Constructs an connection instance with given endpoint and credentials
        
        :param auth_url: end point URL or auth URL to connect to
        :param username: cloud provider account username or access key id
        :param password: cloud provider password or secret access key
        
        """
        # self._connection = VIServer()
        if not provider:
            raise UnsupportedProviderError('Provider %s not supported' % provider)
        providerId = ALL_PROVIDERS_MAP.get(provider)
        if providerId is None:
            raise UnsupportedProviderError('Provider %s not supported' % provider)

        self._provider = provider
        self.providerId = providerId

        # don't set to None if already set from the environment
        if auth_url:
            self.url = auth_url
        if username:
            self.username = username
        if password:
            self.password = password



    def connect(self, auth_url=None, username=None, password=None):
        """Connects to cloud service provider using the optional arguments
         that may override those in the constructor.
        If arguments are not given, previously specified arguments will
        be used for connection in this order:
        
        * last connect arguments (if specified)
        * constructor arguments (if specified)
        * environment variables
        
        If none of the above is specified, MissingArgumentError
        is raised
        
        :type auth_url: string
        :param auth_url: end point URL or auth URL to connect to
        :type username: string
        :param username: cloud provider account username or access key id
        :type password: string
        :param password: cloud provider password or secret access key
        
        """
        if auth_url:
            self.url = auth_url
        if username:
            self.username = username
        if password:
            self.password = password

        # check if all needed properties available for connect
        argErrors = []
        # if not self.url:
        #    argErrors.append('URL unknown')
        if not self.username:
            argErrors.append('username/access key id unknown')
        if not self.password:
            argErrors.append('password/secret access key unknown')

        if argErrors:
            raise MissingArgumentError(', '.join(argErrors))
        driver = get_driver(self.providerId)
        logger.debug('creating connection: username: %s, auth_url: %s' % (self.username, self.url))
        if self.providerId in OPENSTACK_PROVIDERS:
            raise MissingArgumentError('URL unknown')
            self._conn = driver(self.username, self.password,
                            ex_force_auth_url=self.url,
                            ex_force_auth_version=AUTH_VERSION)
        else:
            self._conn = driver(self.username, self.password, auth_url=self.url)

    def disconnect(self):
        """Disconnects from cloud service provider"""
        pass

    def list_instances(self):
        """Lists all instances
        
        :rtype: list
        :return: A list of :class:`catolc.Instance`
        
        """
        return self._conn.list_nodes()

    def list_images(self, filterspec=None):
        """Lists images
        
        :rtype: list
        :return: A list of images
        
        """
        images = self._conn.list_images()
        if filterspec:
            images = filter(lambda x: x.id.find(filterspec) >= 0, images)
        return images

    def list_sizes(self, filterspec=None):
        """Lists sizes
        
        :rtype: list
        :return: A list of sizes
        
        """
        sizes = self._conn.list_sizes()
        if filterspec:
            sizes = filter(lambda x: x.id.find(filterspec) >= 0, sizes)
        return sizes

    def deploy_node(self, **kwargs):
        """Creates/deploys a node
        
        """
        return self._conn.deploy_node(**kwargs)

class Image:
    """Image - a template of virtual server instance.
    
     An Instance can be created by instantiating an image with a specific size
     and other properties.
    
    """
    pass

class Instance:
    """Instance of a virtual server.
    
    """

    def __init__(self, provider, node):
        # wraps underlying libcloud instance/node
        self._conn = provider._conn
        self._node = node

    @property
    def extra(self):
        """Retrieves extra properties for this instance"""
        return self._node.extra

    def get_property_names(self):
        """Returns all supported property names for this Instance.
        
        :rtype: list
        :return: list of strings
        
        """
        return self._node.extra.keys()

    def get_properties(self):
        """ Retrieves all properties from Instance.
        
        :rtype: list
        :return: list of (name, value) tuples
        """
        ret = []
        for n in self._node.extra.keys():
            ret.append((n, self.extra.get(n)))
        return ret

    def __repr__(self):
        return '%s' % self._node.name

    def __str__(self):
        return '%s' % self._node.name
