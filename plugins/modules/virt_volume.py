#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Maciej Delmanowski <drybjed@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: virt_volume
version_added: '1.4.0'
author:
    - Leonardo Galli (@galli-leo)
    - Niclas Kretschmer (@NK308)
short_description: Manage libvirt volumes inside a storage pool
description:
    - Manage I(libvirt) volumes inside a storage pool.
options:
    name:
        aliases: [ "volume" ]
        description:
            - Name of the volume being managed. Note that the volume must be previously
              defined with xml.
        type: str
    pool:
        required: true
        description:
            - Name of the storage pool, where the volume is located.
        type: str
    state:
        choices: [ "present", "absent", "deleted" ]
        description:
            - Specify which state you want a volume to be in.
            - If C(present), ensure that the volume is present but do not change its
              state; if it's missing, you need to specify xml argument.
            - If C(absent), volume will be removed from I(libvirt) configuration (logically only!).
            - If C(deleted), volume will be wiped clean and then removed.
        type: str
    command:
        choices: [ "create", "create_from", "delete", "download", "info", "list_volumes", "get_xml",
                   "resize", "upload", "wipe", "facts"]
        description:
            - In addition to state management, various non-idempotent commands are available.
              See examples.
        type: str
    mode:
        choices: [ 'new', 'repair', 'resize', 'no_overwrite', 'overwrite', 'normal', 'zeroed' ]
        description:
            - Pass additional parameters to 'wipe' command.
        type: str
extends_documentation_fragment:
    - community.libvirt.virt.options_uri
    - community.libvirt.virt.options_xml
    - community.libvirt.requirements
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

- name: Gather facts about storage pools. Facts will be available as 'ansible_libvirt_pools'
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
try:
    import libvirt
except ImportError:
    HAS_VIRT = False
else:
    HAS_VIRT = True

try:
    from lxml import etree
except ImportError:
    HAS_XML = False
else:
    HAS_XML = True


VIRT_FAILED = 1
VIRT_SUCCESS = 0
VIRT_UNAVAILABLE = 2

ALL_COMMANDS = []
ENTRY_COMMANDS = ['create', 'create_from', 'delete', 'download', 'get_xml', 'resize', 'upload',
                  'wipe']
HOST_COMMANDS = ['list_volumes', 'facts', 'info']
ALL_COMMANDS.extend(ENTRY_COMMANDS)
ALL_COMMANDS.extend(HOST_COMMANDS)

ENTRY_STATE_ACTIVE_MAP = {
    0: "inactive",
    1: "active"
}

ENTRY_STATE_AUTOSTART_MAP = {
    0: "no",
    1: "yes"
}

ENTRY_STATE_PERSISTENT_MAP = {
    0: "no",
    1: "yes"
}

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


class EntryNotFound(Exception):
    pass


class PoolConnection(object):

    def __init__(self, uri, module):

        self.module = module

        conn = libvirt.open(uri)

        if not conn:
            raise Exception("hypervisor connection failure")

        self.conn = conn

    def find_entry(self, entryid):
        # entryid = -1 returns a list of everything

        # Get all entries
        results = self.conn.listAllStoragePools()

        if entryid == -1:
            return results

        for entry in results:
            if entry.name() == entryid:
                return entry

        raise EntryNotFound("storage pool %s not found" % entryid)

    def create(self, entryid):
        if not self.module.check_mode:
            return self.find_entry(entryid).create()
        else:
            try:
                state = self.find_entry(entryid).isActive()
            except Exception:
                return self.module.exit_json(changed=True)
            if not state:
                return self.module.exit_json(changed=True)

    def destroy(self, entryid):
        if not self.module.check_mode:
            return self.find_entry(entryid).destroy()
        else:
            if self.find_entry(entryid).isActive():
                return self.module.exit_json(changed=True)

    def undefine(self, entryid):
        if not self.module.check_mode:
            return self.find_entry(entryid).undefine()
        else:
            if not self.find_entry(entryid):
                return self.module.exit_json(changed=True)

    def get_status2(self, entry):
        state = entry.isActive()
        return ENTRY_STATE_ACTIVE_MAP.get(state, "unknown")

    def get_status(self, entryid):
        if not self.module.check_mode:
            state = self.find_entry(entryid).isActive()
            return ENTRY_STATE_ACTIVE_MAP.get(state, "unknown")
        else:
            try:
                state = self.find_entry(entryid).isActive()
                return ENTRY_STATE_ACTIVE_MAP.get(state, "unknown")
            except Exception:
                return ENTRY_STATE_ACTIVE_MAP.get("inactive", "unknown")

    def get_uuid(self, entryid):
        return self.find_entry(entryid).UUIDString()

    def get_xml(self, entryid):
        return self.find_entry(entryid).XMLDesc(0)

    def get_info(self, entryid):
        return self.find_entry(entryid).info()

    def get_volume_count(self, entryid):
        return self.find_entry(entryid).numOfVolumes()

    def get_volume_names(self, entryid):
        return self.find_entry(entryid).listAllVolumes()

    def get_devices(self, entryid):
        xml = etree.fromstring(self.find_entry(entryid).XMLDesc(0))
        if xml.xpath('/pool/source/device'):
            result = []
            for device in xml.xpath('/pool/source/device'):
                result.append(device.get('path'))
        try:
            return result
        except Exception:
            raise ValueError('No devices specified')

    def get_format(self, entryid):
        xml = etree.fromstring(self.find_entry(entryid).XMLDesc(0))
        try:
            result = xml.xpath('/pool/source/format')[0].get('type')
        except Exception:
            raise ValueError('Format not specified')
        return result

    def get_host(self, entryid):
        xml = etree.fromstring(self.find_entry(entryid).XMLDesc(0))
        try:
            result = xml.xpath('/pool/source/host')[0].get('name')
        except Exception:
            raise ValueError('Host not specified')
        return result

    def get_source_path(self, entryid):
        xml = etree.fromstring(self.find_entry(entryid).XMLDesc(0))
        try:
            result = xml.xpath('/pool/source/dir')[0].get('path')
        except Exception:
            raise ValueError('Source path not specified')
        return result

    def get_path(self, entryid):
        xml = etree.fromstring(self.find_entry(entryid).XMLDesc(0))
        try:
            result = xml.xpath('/pool/target/path')[0].text
        except Exception:
            raise ValueError('Target path not specified')
        return result

    def get_type(self, entryid):
        xml = etree.fromstring(self.find_entry(entryid).XMLDesc(0))
        return xml.get('type')

    def build(self, entryid, flags):
        if not self.module.check_mode:
            return self.find_entry(entryid).build(flags)
        else:
            try:
                state = self.find_entry(entryid)
            except Exception:
                return self.module.exit_json(changed=True)
            if not state:
                return self.module.exit_json(changed=True)

    def delete(self, entryid, flags):
        if not self.module.check_mode:
            return self.find_entry(entryid).delete(flags)
        else:
            try:
                state = self.find_entry(entryid)
            except Exception:
                return self.module.exit_json(changed=True)
            if state:
                return self.module.exit_json(changed=True)

    def get_autostart(self, entryid):
        state = self.find_entry(entryid).autostart()
        return ENTRY_STATE_AUTOSTART_MAP.get(state, "unknown")

    def get_autostart2(self, entryid):
        if not self.module.check_mode:
            return self.find_entry(entryid).autostart()
        else:
            try:
                return self.find_entry(entryid).autostart()
            except Exception:
                return self.module.exit_json(changed=True)

    def set_autostart(self, entryid, val):
        if not self.module.check_mode:
            return self.find_entry(entryid).setAutostart(val)
        else:
            try:
                state = self.find_entry(entryid).autostart()
            except Exception:
                return self.module.exit_json(changed=True)
            if bool(state) != val:
                return self.module.exit_json(changed=True)

    def refresh(self, entryid):
        return self.find_entry(entryid).refresh()

    def get_persistent(self, entryid):
        state = self.find_entry(entryid).isPersistent()
        return ENTRY_STATE_PERSISTENT_MAP.get(state, "unknown")

    def define_from_xml(self, entryid, xml):
        if not self.module.check_mode:
            return self.conn.storagePoolDefineXML(xml)
        else:
            try:
                self.find_entry(entryid)
            except Exception:
                return self.module.exit_json(changed=True)


class LibvirtConnection(object):

    def __init__(self, uri, module, poolid):

        self.module = module

        conn = libvirt.open(uri)

        if not conn:
            raise Exception("hypervisor connection failure")

        self.conn = conn
        self.poolid = poolid
        self.poolConn = PoolConnection(uri, module)
        self.pool = self.poolConn.find_entry(poolid)

    def find_entry(self, entryid):
        # entryid = -1 returns a list of everything

        results = []

        for entry in self.pool.listAllVolumes():
            if entryid == -1:
                results.append(entry)
            elif entry.name() == entryid:
                return entry

        if entryid == -1:
            return results

        raise EntryNotFound("volume %s not found" % entryid)

    def create(self, entryid, xml):
        return self.pool.createXML(xml)

    def create_from(self, entryid, xml, to_clone):
        from_vol = self.find_entry(to_clone)
        try:
            return self.pool.createXMLFrom(xml, from_vol)
        except Exception:
            return self.module.exit_json(changed=True)

    def delete(self, entryid):
        if not self.module.check_mode:
            return self.find_entry(entryid).delete()
        else:
            if self.find_entry(entryid):
                return self.module.exit_json(changed=True)

    def wipe(self, entryid, mode):
        if not self.module.check_mode:
            return self.find_entry(entryid).wipe()
        else:
            if not self.find_entry(entryid):
                return self.module.exit_json(changed=True)

    def get_status2(self, entry):
        state = entry.isActive()
        return ENTRY_STATE_ACTIVE_MAP.get(state, "unknown")

    def get_status(self, entryid):
        if not self.module.check_mode:
            state = self.find_entry(entryid).isActive()
            return ENTRY_STATE_ACTIVE_MAP.get(state, "unknown")
        else:
            try:
                state = self.find_entry(entryid).isActive()
                return ENTRY_STATE_ACTIVE_MAP.get(state, "unknown")
            except Exception:
                return ENTRY_STATE_ACTIVE_MAP.get("inactive", "unknown")

    def get_uuid(self, entryid):
        return self.find_entry(entryid).UUIDString()

    def get_xml(self, entryid):
        return self.find_entry(entryid).XMLDesc(0)

    def get_info(self, entryid):
        return self.find_entry(entryid).info()


class VirtVolume(object):

    def __init__(self, uri, module, poolid):
        self.module = module
        self.uri = uri
        self.poolid = poolid
        self.conn = LibvirtConnection(self.uri, self.module, self.poolid)

    def get_volume(self, entryid):
        return self.conn.find_entry(entryid)

    def list_volumes(self, state=None):
        results = []
        for entry in self.conn.find_entry(-1):
            results.append(entry.name())
        return results

    def state(self):
        results = []
        for entry in self.list_pools():
            state_blurb = self.conn.get_status(entry)
            results.append("%s %s" % (entry, state_blurb))
        return results

    def create(self, entryid, xml):
        return self.conn.create(entryid, xml)

    def create_from(self, entryid, xml, to_clone):
        return self.conn.create_from(entryid, xml, to_clone)

    def delete(self, entryid):
        return self.conn.delete(entryid)

    def status(self, entryid):
        return self.conn.get_status(entryid)

    def get_xml(self, entryid):
        return self.conn.get_xml(entryid)

    def wipe(self, entryid, flags):
        return self.conn.wipe(entryid, ENTRY_DELETE_FLAGS_MAP.get(flags, 0))

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
                results[entry]["path"] = self.conn.get_path(entry)
                results[entry]["type"] = self.conn.get_type(entry)
                results[entry]["uuid"] = self.conn.get_uuid(entry)
                if self.conn.find_entry(entry).isActive():
                    results[entry]["volume_count"] = self.conn.get_volume_count(entry)
                    results[entry]["volumes"] = list()
                    for volume in self.conn.get_volume_names(entry):
                        results[entry]["volumes"].append(volume)
                else:
                    results[entry]["volume_count"] = -1

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
    pool = module.params.get('pool', None)
    command = module.params.get('command', None)
    uri = module.params.get('uri', None)
    xml = module.params.get('xml', None)
    mode = module.params.get('mode', None)

    v = VirtVolume(uri, module, pool)
    res = {}

    if state and command == 'list_volumes':
        res = v.list_volumes(state=state)
        if not isinstance(res, dict):
            res = {command: res}
        return VIRT_SUCCESS, res

    if state:
        if not name:
            module.fail_json(msg="state change requires a specified name")

        res['changed'] = False
        if state in ['present']:
            if name not in v.list_volumes():
                if xml:
                    v.create(name, xml)
                    res = {'changed': True, 'created': name}
                else:
                    module.fail_json(msg="volume '" + name + "' not present, but xml not specified")
        elif state in ['absent']:
            entries = v.list_volumes()
            if name in entries:
                res['changed'] = True
                res['msg'] = v.delete(name)
        elif state in ['deleted']:
            entries = v.list_volumes()
            if name in entries:
                v.wipe(name, mode)
                res['changed'] = True
                res['msg'] = v.delete(name)
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

    module.fail_json(msg="expected state or command parameter to be specified")


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(aliases=['volume']),
            pool=dict(required=True),
            state=dict(choices=['present', 'absent', 'deleted']),
            command=dict(choices=ALL_COMMANDS),
            uri=dict(default='qemu:///system'),
            xml=dict(),
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
