from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
name: libvirt
plugin_type: inventory
extends_documentation_fragment:
    - constructed
short_description: Libvirt inventory source
description:
    - Get libvirt guests in an inventory source
author:
    - Dave Olsthoorn <dave@bewaar.me>
version_added: "2.10"
options:
    plugin:
        description: Token that ensures this is a source file for the 'libvirt' plugin.
        required: True
        choices: ['libvirt']
    uri:
        description: Libvirt Connection URI
        required: True
        type: str
requirements:
    - "libvirt-python"
'''

EXAMPLES = r'''
# Connect to lxc host
plugin: libvirt
uri: 'lxc:///'

# Connect to qemu host
plugin: libvirt
uri: 'qemu:///system'
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.errors import AnsibleError

try:
    import libvirt
except ImportError:
    raise AnsibleError('the libvirt inventory plugin requires libvirt-python.')


class InventoryModule(BaseInventoryPlugin, Constructable):
    NAME = 'community.libvirt.libvirt'

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(
            inventory,
            loader,
            path,
            cache=cache
        )

        config_data = self._read_config_data(path)

        # set _options from config data
        self._consume_options(config_data)

        uri = self.get_option('uri')
        if not uri:
            raise AnsibleError("hypervisor uri not given")

        connection = libvirt.open(uri)
        if not connection:
            raise AnsibleError("hypervisor connection failure")

        # TODO(daveol)
        # make using connection plugins optional
        connection_plugin = dict({
            'LXC': 'community.libvirt.libvirt_lxc',
            'QEMU': 'community.libvirt.libvirt_qemu'
        }).get(connection.getType())

        for server in connection.listAllDomains():
            hostname = server.name()
            self.inventory.add_host(hostname)

            if connection_plugin is not None:
                self.inventory.set_variable(hostname, 'ansible_libvirt_uri', uri)
                self.inventory.set_variable(hostname, 'ansible_connection', connection_plugin)

            # Get variables for compose
            variables = self.inventory.hosts[hostname].get_vars()

            # Set composed variables
            self._set_composite_vars(
                self.get_option('compose'),
                variables,
                hostname,
                self.get_option('strict'),
            )

            # Add host to composed groups
            self._add_host_to_composed_groups(
                self.get_option('groups'),
                variables,
                hostname,
                self.get_option('strict'),
            )

            # Add host to keyed groups
            self._add_host_to_keyed_groups(
                self.get_option('keyed_groups'),
                variables,
                hostname,
                self.get_option('strict'),
            )
