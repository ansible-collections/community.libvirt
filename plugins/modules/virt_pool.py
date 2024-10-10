#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Maciej Delmanowski <drybjed@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: virt_pool
author: "Maciej Delmanowski (@drybjed)"
short_description: Manage libvirt storage pools
description:
    - Manage I(libvirt) storage pools.
options:
    name:
        aliases: [ "pool" ]
        description:
            - Name of the storage pool being managed. Note that pool must be previously
              defined with xml.
        type: str
    state:
        choices: [ "active", "inactive", "present", "absent", "undefined", "deleted" ]
        description:
            - Specify which state you want a storage pool to be in.
              If 'active', pool will be started.
              If 'present', ensure that pool is present but do not change its
              state; if it is missing, you need to specify xml argument.
              If 'inactive', pool will be stopped.
              If 'undefined' or 'absent', pool will be removed from I(libvirt) configuration.
              If 'deleted', pool contents will be deleted and then pool undefined.
        type: str
    command:
        choices: [ "define", "build", "create", "start", "stop", "destroy",
                   "delete", "undefine", "get_xml", "list_pools", "facts",
                   "info", "status", "refresh" ]
        description:
            - In addition to state management, various non-idempotent commands are available.
              See examples.
        type: str
    autostart:
        type: bool
        description:
            - Specify if a given storage pool should be started automatically on system boot.
    mode:
        choices: [ 'new', 'repair', 'resize', 'no_overwrite', 'overwrite', 'normal', 'zeroed' ]
        description:
            - Pass additional parameters to 'build' or 'delete' commands.
        type: str
extends_documentation_fragment:
    - community.libvirt.virt.options_uri
    - community.libvirt.virt.options_xml
    - community.libvirt.requirements
requirements:
    - "python-lxml"
'''

EXAMPLES = '''
- name: Define a new storage pool
  community.libvirt.virt_pool:
    command: define
    name: vms
    xml: '{{ lookup("template", "pool/dir.xml.j2") }}'

- name: Build a storage pool if it does not exist
  community.libvirt.virt_pool:
    command: build
    name: vms

- name: Start a storage pool
  community.libvirt.virt_pool:
    command: create
    name: vms

- name: List available pools
  community.libvirt.virt_pool:
    command: list_pools

- name: Get XML data of a specified pool
  community.libvirt.virt_pool:
    command: get_xml
    name: vms

- name: Stop a storage pool
  community.libvirt.virt_pool:
    command: destroy
    name: vms

- name: Delete a storage pool (destroys contents)
  community.libvirt.virt_pool:
    command: delete
    name: vms

- name: Undefine a storage pool
  community.libvirt.virt_pool:
    command: undefine
    name: vms

# Gather facts about storage pools
# Facts will be available as 'ansible_libvirt_pools'
- name: Gather facts about storage pools
  community.libvirt.virt_pool:
    command: facts

- name: Gather information about pools managed by 'libvirt' remotely using uri
  community.libvirt.virt_pool:
    command: info
    uri: '{{ item }}'
  with_items: '{{ libvirt_uris }}'
  register: storage_pools

- name: Ensure that a pool is active (needs to be defined and built first)
  community.libvirt.virt_pool:
    state: active
    name: vms

- name: Ensure that a pool is inactive
  community.libvirt.virt_pool:
    state: inactive
    name: vms

- name: Ensure that a given pool will be started at boot
  community.libvirt.virt_pool:
    autostart: true
    name: vms

- name: Disable autostart for a given pool
  community.libvirt.virt_pool:
    autostart: false
    name: vms
'''

from ansible.module_utils.basic import AnsibleModule


VIRT_FAILED = 1
VIRT_SUCCESS = 0
VIRT_UNAVAILABLE = 2

ALL_COMMANDS = []
ENTRY_COMMANDS = ['create', 'status', 'start', 'stop', 'build', 'delete',
                  'undefine', 'destroy', 'get_xml', 'define', 'refresh']
HOST_COMMANDS = ['list_pools', 'facts', 'info']
ALL_COMMANDS.extend(ENTRY_COMMANDS)
ALL_COMMANDS.extend(HOST_COMMANDS)

ENTRY_STATE_INFO_MAP = {
    0: "inactive",
    1: "building",
    2: "running",
    3: "degraded",
    4: "inaccessible"
}

ENTRY_BUILD_FLAGS_MAP = {
    "new": 0,
    "repair": 1,
    "resize": 2,
    "no_overwrite": 4,
    "overwrite": 8
}

ENTRY_DELETE_FLAGS_MAP = {
    "normal": 0,
    "zeroed": 1
}

ALL_MODES = []
ALL_MODES.extend(ENTRY_BUILD_FLAGS_MAP.keys())
ALL_MODES.extend(ENTRY_DELETE_FLAGS_MAP.keys())

from ansible_collections.community.libvirt.plugins.module_utils.pool import LibvirtConnection, HAS_VIRT, HAS_XML
from ansible_collections.community.libvirt.plugins.module_utils.entry import EntryNotFound


class VirtStoragePool(object):

    def __init__(self, uri, module):
        self.module = module
        self.uri = uri
        self.conn = LibvirtConnection(self.uri, self.module)

    def get_pool(self, entryid):
        return self.conn.find_entry(entryid)

    def list_pools(self, state=None):
        results = []
        for entry in self.conn.find_entry(-1):
            if state:
                if state == self.conn.get_status2(entry):
                    results.append(entry.name())
            else:
                results.append(entry.name())
        return results

    def state(self):
        results = []
        for entry in self.list_pools():
            state_blurb = self.conn.get_status(entry)
            results.append("%s %s" % (entry, state_blurb))
        return results

    def autostart(self, entryid):
        return self.conn.set_autostart(entryid, True)

    def get_autostart(self, entryid):
        return self.conn.get_autostart2(entryid)

    def set_autostart(self, entryid, state):
        return self.conn.set_autostart(entryid, state)

    def create(self, entryid):
        return self.conn.create(entryid)

    def start(self, entryid):
        return self.conn.create(entryid)

    def stop(self, entryid):
        return self.conn.destroy(entryid)

    def destroy(self, entryid):
        return self.conn.destroy(entryid)

    def undefine(self, entryid):
        return self.conn.undefine(entryid)

    def status(self, entryid):
        return self.conn.get_status(entryid)

    def get_xml(self, entryid):
        return self.conn.get_xml(entryid)

    def define(self, entryid, xml):
        return self.conn.define_from_xml(entryid, xml)

    def build(self, entryid, flags):
        return self.conn.build(entryid, ENTRY_BUILD_FLAGS_MAP.get(flags, 0))

    def delete(self, entryid, flags):
        return self.conn.delete(entryid, ENTRY_DELETE_FLAGS_MAP.get(flags, 0))

    def refresh(self, entryid):
        return self.conn.refresh(entryid)

    def info(self):
        return self.facts(facts_mode='info')

    def facts(self, facts_mode='facts'):
        results = dict()
        for entry in self.list_pools():
            results[entry] = dict()
            if self.conn.find_entry(entry):
                data = self.conn.get_info(entry)
                # libvirt returns maxMem, memory, and cpuTime as long()'s, which
                # xmlrpclib tries to convert to regular int's during serialization.
                # This throws exceptions, so convert them to strings here and
                # assume the other end of the xmlrpc connection can figure things
                # out or doesn't care.
                results[entry] = {
                    "status": ENTRY_STATE_INFO_MAP.get(data[0], "unknown"),
                    "size_total": str(data[1]),
                    "size_used": str(data[2]),
                    "size_available": str(data[3]),
                }
                results[entry]["autostart"] = self.conn.get_autostart(entry)
                results[entry]["persistent"] = self.conn.get_persistent(entry)
                results[entry]["state"] = self.conn.get_status(entry)
                results[entry]["type"] = self.conn.get_type(entry)
                results[entry]["uuid"] = self.conn.get_uuid(entry)
                if self.conn.find_entry(entry).isActive():
                    results[entry]["volume_count"] = self.conn.get_volume_count(entry)
                    results[entry]["volumes"] = list()
                    for volume in self.conn.get_volume_names(entry):
                        results[entry]["volumes"].append(volume.name())
                else:
                    results[entry]["volume_count"] = -1

                try:
                    results[entry]["path"] = self.conn.get_path(entry)
                except ValueError:
                    pass

                try:
                    results[entry]["host"] = self.conn.get_host(entry)
                except ValueError:
                    pass

                try:
                    results[entry]["source_path"] = self.conn.get_source_path(entry)
                except ValueError:
                    pass

                try:
                    results[entry]["format"] = self.conn.get_format(entry)
                except ValueError:
                    pass

                try:
                    devices = self.conn.get_devices(entry)
                    results[entry]["devices"] = devices
                except ValueError:
                    pass

            else:
                results[entry]["state"] = self.conn.get_status(entry)

        facts = dict()
        if facts_mode == 'facts':
            facts["ansible_facts"] = dict()
            facts["ansible_facts"]["ansible_libvirt_pools"] = results
        elif facts_mode == 'info':
            facts['pools'] = results
        return facts


def core(module):

    state = module.params.get('state', None)
    name = module.params.get('name', None)
    command = module.params.get('command', None)
    uri = module.params.get('uri', None)
    xml = module.params.get('xml', None)
    autostart = module.params.get('autostart', None)
    mode = module.params.get('mode', None)

    v = VirtStoragePool(uri, module)
    res = {}

    if state and command == 'list_pools':
        res = v.list_pools(state=state)
        if not isinstance(res, dict):
            res = {command: res}
        return VIRT_SUCCESS, res

    if state:
        if not name:
            module.fail_json(msg="state change requires a specified name")

        res['changed'] = False
        if state in ['active']:
            if v.status(name) != 'active':
                res['changed'] = True
                res['msg'] = v.start(name)
        elif state in ['present']:
            try:
                v.get_pool(name)
            except EntryNotFound:
                if not xml:
                    module.fail_json(msg="storage pool '" + name + "' not present, but xml not specified")
                v.define(name, xml)
                res = {'changed': True, 'created': name}
        elif state in ['inactive']:
            entries = v.list_pools()
            if name in entries:
                if v.status(name) != 'inactive':
                    res['changed'] = True
                    res['msg'] = v.destroy(name)
        elif state in ['undefined', 'absent']:
            entries = v.list_pools()
            if name in entries:
                if v.status(name) != 'inactive':
                    v.destroy(name)
                res['changed'] = True
                res['msg'] = v.undefine(name)
        elif state in ['deleted']:
            entries = v.list_pools()
            if name in entries:
                if v.status(name) != 'inactive':
                    v.destroy(name)
                v.delete(name, mode)
                res['changed'] = True
                res['msg'] = v.undefine(name)
        else:
            module.fail_json(msg="unexpected state")

        return VIRT_SUCCESS, res

    if command:
        if command in ENTRY_COMMANDS:
            if not name:
                module.fail_json(msg="%s requires 1 argument: name" % command)
            if command == 'define':
                if not xml:
                    module.fail_json(msg="define requires xml argument")
                try:
                    v.get_pool(name)
                except EntryNotFound:
                    v.define(name, xml)
                    res = {'changed': True, 'created': name}
                return VIRT_SUCCESS, res
            elif command == 'build':
                res = v.build(name, mode)
                if not isinstance(res, dict):
                    res = {'changed': True, command: res}
                return VIRT_SUCCESS, res
            elif command == 'delete':
                res = v.delete(name, mode)
                if not isinstance(res, dict):
                    res = {'changed': True, command: res}
                return VIRT_SUCCESS, res
            res = getattr(v, command)(name)
            if not isinstance(res, dict):
                res = {command: res}
            return VIRT_SUCCESS, res

        elif hasattr(v, command):
            res = getattr(v, command)()
            if not isinstance(res, dict):
                res = {command: res}
            return VIRT_SUCCESS, res

        else:
            module.fail_json(msg="Command %s not recognized" % command)

    if autostart is not None:
        if not name:
            module.fail_json(msg="state change requires a specified name")

        res['changed'] = False
        if autostart:
            if not v.get_autostart(name):
                res['changed'] = True
                res['msg'] = v.set_autostart(name, True)
        else:
            if v.get_autostart(name):
                res['changed'] = True
                res['msg'] = v.set_autostart(name, False)

        return VIRT_SUCCESS, res

    module.fail_json(msg="expected state or command parameter to be specified")


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(aliases=['pool']),
            state=dict(choices=['active', 'inactive', 'present', 'absent', 'undefined', 'deleted']),
            command=dict(choices=ALL_COMMANDS),
            uri=dict(default='qemu:///system'),
            xml=dict(),
            autostart=dict(type='bool'),
            mode=dict(choices=ALL_MODES),
        ),
        supports_check_mode=True
    )

    if not HAS_VIRT:
        module.fail_json(
            msg='The `libvirt` module is not importable. Check the requirements.'
        )

    if not HAS_XML:
        module.fail_json(
            msg='The `lxml` module is not importable. Check the requirements.'
        )

    rc = VIRT_SUCCESS
    try:
        rc, result = core(module)
    except Exception as e:
        module.fail_json(msg=str(e))

    if rc != 0:  # something went wrong emit the msg
        module.fail_json(rc=rc, msg=result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
