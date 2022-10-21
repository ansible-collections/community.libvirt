#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: domain_info
short_description: Retrieves information about I(libvirt) domains.
description:
  - Retrieves information about I(libvirt) domains.
options:
  name:
    description:
      - name of the guest domain to get information about.
    required: true
  state:
    description:
      - If provided, returns the state of the domain I(name)
    type: dict
    options: {}
  xml:
    description:
      - If provided, returns the domain's XML.
    type: dict
    options:
      flags:
        description:
          - The set of flags to pass to libvirt's GetXMLDesc
          - See: https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainGetXMLDesc
        type: list
        elements: str
        choices: [ secure, inactive, update-cpu, migratable ]
  guestinfo:
    description:
      - If provided, returns information about the running guest.
      - Requires qemu-guest-agent on the guest.
    type: dict
    options:
      types:
        description:
          - The types of information to get about the guest.
          - See: https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainGetGuestInfo
          - By default, returns all information.
        type: list
        elements: str
        choices: [ user, os, timezone, hostname, filesystem, disk, interface ]
  ifaddr:
    description:
      - If provided, returns the interfaces and IP addresses of the guest.
      - Requires qemu-guest-agent on the guest when the `guest` source is used.
    type: dict
    options:
      source:
        description:
          - The source libvirt uses to retrieve interface address information.
          - See: https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainInterfaceAddresses
        type: src
        choices: [ lease, agent, arp ]
        default: lease
extends_documentation_fragment:
  - community.libvirt.virt.options_uri
  - community.libvirt.requirements
author:
  - Matt Low
"""

EXAMPLES = """
- name: Get the state of a domain
  community.libvirt.domain_info:
    name: foo
    state:
  register: domain_info

- name: Get the state AND interface addresses of a domain
  community.libvirt.domain_info:
    name: foo
    state:
    ifaddr:
      source: guest

- name: Get the XML of a domain
  community.libvirt.domain_info:
    name: foo
    xml:

- name: Get the migratable XML of a domain
  community.libvirt.domain_info:
    name: foo
    xml:
      flags:
        - migratable
"""

RETURN = """
name:
  description: The name of the domain information was requested for.
  type: str
  returned: success
  sample: foo

uuid:
  description: The UUID of the domain information was requested for.
  type: str
  returned: success
  sample: 2cacfeff-19c5-42ef-8949-2ba656aa813a

exists:
  description: Whether or not the domain exists.
  type: bool
  returned: success
  sample: true

state:
  description: The state the domain is in
  type: str
  returned: if I(state) parameter provided

xml:
  description: The xml defintion of the domain
  type: str
  returned: if I(xml) parameter provided

guestinfo:
  description: Domain guest information (requires qemu-guest-agent)
  type: dict
  returned: if I(guestinfo) parameter provided

ifaddr:
  description: Domain interface address information
  type: dict
  returned: if I(ifaddr) parameter provided
"""

try:
    import libvirt
    from libvirt import libvirtError
except ImportError:
    HAS_VIRT = False
else:
    HAS_VIRT = True

from ansible.module_utils.basic import AnsibleModule, _load_params
from ansible.module_utils._text import to_native

import traceback

# https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainState
DOM_STATE_MAP = {
    0: "nostate",  # no state
    1: "running",  # the domain is running
    2: "blocked",  # the domain is blocked on resource
    3: "paused",  # the domain is paused by user
    4: "shutdown",  # the domain is being shut down
    5: "shutoff",  # the domain is shut off
    6: "crashed",  # the domain is crashed
    7: "pmsuspended",  # the domain is suspended by guest power management
}

# https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainInterfaceAddresses
DOM_IFADDR_SOURCES = {
    # works for domain interfaces on libvirt-managed networks
    "lease": libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE,
    # works when the domain has qemu_guest_agent installed
    "agent": libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT,
    # uses the ARP table of host
    "arp": libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_ARP,
}

# https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainGetXMLDesc
DOM_XML_FLAGS = {
    "secure": libvirt.VIR_DOMAIN_XML_SECURE,  # dump security sensitive information too
    "inactive": libvirt.VIR_DOMAIN_XML_INACTIVE,  # dump inactive domain information
    "update-cpu": libvirt.VIR_DOMAIN_XML_UPDATE_CPU,  # update guest CPU requirements according to host CPU
    "migratable": libvirt.VIR_DOMAIN_XML_MIGRATABLE,  # dump XML suitable for migration
}

# https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainGetGuestInfo
DOM_GUEST_INFO_TYPES = {
    "user": libvirt.VIR_DOMAIN_GUEST_INFO_USERS,  # report active users
    "os": libvirt.VIR_DOMAIN_GUEST_INFO_OS,  # report operating system information
    "timezone": libvirt.VIR_DOMAIN_GUEST_INFO_TIMEZONE,  # report timezone information
    "hostname": libvirt.VIR_DOMAIN_GUEST_INFO_HOSTNAME,  # report hostname information
    "filesystem": libvirt.VIR_DOMAIN_GUEST_INFO_FILESYSTEM,  # report filesystem information
    "disk": libvirt.VIR_DOMAIN_GUEST_INFO_HOSTNAME,  # report disk information
    "interface": libvirt.VIR_DOMAIN_GUEST_INFO_HOSTNAME,  # report interface information
}

DOM_IFADDR_DEFAULT_SOURCE = "lease"


def execute_module(module):
    conn = libvirt.open()
    result = dict()

    name = module.params.get("name")
    try:
        dom = conn.lookupByName(name)
        result.update(exists=True)
    except:
        result.update(exists=False, msg="No domain with matching name '%s'" % name)
        return result

    # always return the domain's name & uuid
    result.update(name=dom.name())
    result.update(uuid=dom.UUIDString())

    # This allows us to access passed in module params before argument
    # validation. We only use it to see whether certain params have been
    # supplied (even without value) to trigger their 'resolvers' (below)
    # This might break in future versions of Ansible.
    raw_params = _load_params()

    if "state" in raw_params:
        state, _ = dom.state()
        # state is a tuple of ints, in the format of [state.state, state.reason]
        # where state.state is an int coresponding to the domain's current state
        # and state.reason is an int corresponding to the reason the domain ended
        # up in its current state.
        # Currently we don't expose the reason, but it shouldn't be hard to do
        # if this information is desired.
        result.update(state=DOM_STATE_MAP[state])

    if "xml" in raw_params:
        flags = 0
        xml_args = module.params.get("xml")
        if xml_args:
            for flag in xml_args.get("flags"):
                flags |= DOM_XML_FLAGS[flag]
        result.update(xml=dom.XMLDesc(flags))

    if "guestinfo" in raw_params:
        types = 0
        guestinfo_args = module.params.get("guestinfo")
        if guestinfo_args:
            for _type in guestinfo_args.get("types"):
                types |= DOM_GUEST_INFO_TYPES[_type]
        result.update(guestinfo=dom.guestInfo(types))

    if "ifaddr" in raw_params:
        ifaddr_args = module.params.get("ifaddr")
        source = ifaddr_args.get("source") if ifaddr_args else DOM_IFADDR_DEFAULT_SOURCE
        result.update(ifaddr=dom.interfaceAddresses(DOM_IFADDR_SOURCES[source]))

    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type="str", alias="domain", required=True),
            state=dict(type="dict"),
            xml=dict(
                type="dict",
                options=dict(
                    flags=dict(
                        type="list",
                        elements="str",
                        choices=DOM_XML_FLAGS.keys(),
                        default=[],  # emulating `virsh` behavior
                    )
                ),
            ),
            ifaddr=dict(
                type="dict",
                options=dict(
                    source=dict(
                        type="str",
                        choices=DOM_IFADDR_SOURCES.keys(),
                        default=DOM_IFADDR_DEFAULT_SOURCE,  # emulating `virsh` behavior
                    )
                ),
            ),
            guestinfo=dict(
                type="dict",
                options=dict(
                    types=dict(
                        type="list",
                        elements="str",
                        choices=DOM_GUEST_INFO_TYPES.keys(),
                        default=[],  # emulating `virsh` behavior
                    )
                ),
            ),
        ),
    )

    if not HAS_VIRT:
        module.fail_json(
            msg="The `libvirt` module is not importable. Check the requirements."
        )

    result = dict(changed=False)

    try:
        result.update(execute_module(module))
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(**result)


if __name__ == "__main__":
    main()
