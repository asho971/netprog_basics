#!/usr/bin/env python3
"""
Learning Series: Network Programmability Basics
Module: Network Device APIs
Lesson: Goodbye SNMP hello NETCONF
Author: Hank Preston <hapresto@cisco.com>

example1.py
Illustrate the following concepts:
- Opening a NETCONF connection with ncclient
- Saying <hello> and review capabilities
"""

__author__ = "Hank Preston"
__author_email__ = "hapresto@cisco.com"
__copyright__ = "Copyright (c) 2016 Cisco Systems, Inc."
__license__ = "MIT"

from device_info import ios_xe_sandbox 
from ncclient import manager


# example1.py — manager.connect() block
with manager.connect(host=ios_xe_sandbox["address"],
                     port=ios_xe_sandbox["port"],
                     username=ios_xe_sandbox["username"],
                     password=ios_xe_sandbox["password"],
                     hostkey_verify=False,
                     allow_agent=False,      # don't use ssh-agent
                     look_for_keys=False     # don't try ~/.ssh/id_* keys
                     ) as m:

        print("Here are the NETCONF Capabilities")
        for capability in m.server_capabilities:
            print(capability)
