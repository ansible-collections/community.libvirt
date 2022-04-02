from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
name: libvirt
plugin_type: inventory
extends_documentation_fragment:
    - constructed
    - community.libvirt.requirements
short_description: Libvirt inventory source
description:
    - Get libvirt guests in an inventory source.
author:
    - Dave Olsthoorn <dave@bewaar.me>
version_added: "2.10"
options:
    plugin:
        description: Token that ensures this is a source file for the 'libvirt' plugin.
        required: True
        choices: ['libvirt', 'community.libvirt.libvirt']
    uri:
        description: Libvirt Connection URI
        required: True
        type: str
    inventory_hostname:
        description: |
            What to register as the inventory hostname.
            If set to 'uuid' the uuid of the server will be used and a
            group will be created for the server name.
            If set to 'name' the name of the server will be used unless
            there are more than one server with the same name in which
            case the 'uuid' logic will be used.
            Default is to do 'name'.
        type: string
        choices:
            - name
            - uuid
        default: "name"
'''

EXAMPLES = r'''
# Connect to lxc host
plugin: community.libvirt.libvirt
uri: 'lxc:///'

# Connect to qemu
plugin: community.libvirt.libvirt
uri: 'qemu:///system'
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.errors import AnsibleError
from ansible.module_utils.six import raise_from
from ansible_collections.community.vmware.plugins.plugin_utils.inventory import to_nested_dict
from collections import defaultdict
from xml.etree import ElementTree as ET

try:
    import libvirt
except ImportError as imp_exc:
    LIBVIRT_IMPORT_ERROR = imp_exc
else:
    LIBVIRT_IMPORT_ERROR = None

VIRDOMAINSTATE = ["NOSTATE", "RUNNING", "BLOCKED", "PAUSED", "SHUTDOWN", "SHUTOFF", "CRASHED", "PMSUSPENDED", "LAST"]


# From https://stackoverflow.com/a/10077069/12491741
# Converts XML to JSON using the 'official' (reversible) spec in http://www.xml.com/pub/a/2006/05/31/converting-between-xml-and-json.html
def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


class InventoryModule(BaseInventoryPlugin, Constructable):
    NAME = 'community.libvirt.libvirt'

    def parse(self, inventory, loader, path, cache=True):
        if LIBVIRT_IMPORT_ERROR:
            raise_from(
                AnsibleError('libvirt python bindings must be installed to use this plugin'),
                LIBVIRT_IMPORT_ERROR)

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
            inventory_hostname = dict({
                'uuid': server.UUIDString(),
                'name': server.name()
            }).get(
                self.get_option('inventory_hostname')
            )

            inventory_hostname_alias = dict({
                'name': server.UUIDString(),
                'uuid': server.name()
            }).get(
                self.get_option('inventory_hostname')
            )

            # TODO(daveol): Fix "Invalid characters were found in group names"
            # This warning is generated because of uuid's
            self.inventory.add_host(inventory_hostname)
            self.inventory.add_group(inventory_hostname_alias)
            self.inventory.add_child(inventory_hostname_alias, inventory_hostname)

            if connection_plugin is not None:
                self.inventory.set_variable(
                    inventory_hostname,
                    'ansible_libvirt_uri',
                    uri
                )
                self.inventory.set_variable(
                    inventory_hostname,
                    'ansible_connection',
                    connection_plugin
                )

            try:
                domain = connection.lookupByUUIDString(server.UUIDString())
            except libvirt.libvirtError as e:
                self.inventory.set_variable(
                    inventory_hostname,
                    'ERROR',
                    str(e)
                )
            else:
                _domain_state, _domain_maxmem, _domain_mem, _domain_cpus, _domain_cput = domain.info()
                domain_info = {"state_number": _domain_state, "state": VIRDOMAINSTATE[_domain_state], "maxMem_kb": _domain_maxmem, "memory_kb": _domain_mem, "nrVirtCpu": _domain_cpus, "cpuTime_ns": _domain_cput}
                self.inventory.set_variable(
                    inventory_hostname,
                    'info',
                    domain_info
                )

                domain_XMLDesc = {'xml': domain.XMLDesc()}
                domain_XMLDesc.update({'json': etree_to_dict(ET.fromstring(domain_XMLDesc['xml']))})
                self.inventory.set_variable(
                    inventory_hostname,
                    'XMLDesc',
                    domain_XMLDesc
                )

                # This will fail if qemu-guest-agent is not installed, or org.qemu.guest_agent.0 is not a configured channel, or the guest is not powered-on.
                try:
                    domain_guestInfo = domain.guestInfo(types=0)
                    domain_guestInfo.update(to_nested_dict(domain_guestInfo))
                except Exception as e:
                    domain_guestInfo = {"error": str(e)}
                finally:
                    self.inventory.set_variable(
                        inventory_hostname,
                        'guest_info',
                        domain_guestInfo
                    )

                # This will fail if qemu-guest-agent is not installed, or org.qemu.guest_agent.0 is not a configured channel, or the guest is not powered-on.
                try:
                    domain_interfaceAddresses = domain.interfaceAddresses(source=1)     # VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT
                except Exception as e:
                    domain_interfaceAddresses = {"error": str(e)}
                finally:
                    self.inventory.set_variable(
                        inventory_hostname,
                        'interface_addresses',
                        domain_interfaceAddresses
                    )

            # Get variables for compose
            variables = self.inventory.hosts[inventory_hostname].get_vars()

            # Set composed variables
            self._set_composite_vars(
                self.get_option('compose'),
                variables,
                inventory_hostname,
                self.get_option('strict'),
            )

            # Add host to composed groups
            self._add_host_to_composed_groups(
                self.get_option('groups'),
                variables,
                inventory_hostname,
                self.get_option('strict'),
            )

            # Add host to keyed groups
            self._add_host_to_keyed_groups(
                self.get_option('keyed_groups'),
                variables,
                inventory_hostname,
                self.get_option('strict'),
            )
