# -*- coding: utf-8 -*-

__version_info__ = ('0', '1', '4')
__version__ = '.'.join(__version_info__)

from vsphere import Server, VIException, VMPowerState, VM, set_debug, set_prototrace, get_all_property_names
