#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2022, Dougal Seeley <git@dougalseeley.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: virt_volume
author:
    - Dougal Seeley (@dseeley)
short_description: Manage libvirt storage volumes
description:
    - Manage I(libvirt) storage volumes.
options:
    name:
        aliases: [ "volume" ]
        description:
            - Name of the storage volume being managed. 
        type: str
    path:
        description:
            - Path to the storage volume being manipulated.  See examples. 
        type: str
    xml:
        description:
            - The XML of the descriptor being created.  See examples. 
        type: str
    command:
        choices: [ "create_cidata_cdrom", "getXMLDesc", "createXML", "createXMLFrom", "delete" ]
        description:
            - Idempotent commands are used to modify the state of the volume
              See examples.
        type: str
 extends_documentation_fragment:
     - community.libvirt.virt.options_uri
     - community.libvirt.virt.options_xml
     - community.libvirt.requirements
requirements:
    - "libvirt"
    - "lxml"
    - "pycdlib"
'''

EXAMPLES = '''
- name: Create volume
  community.libvirt.virt_volume:
    uri: 'qemu+ssh://{{ username }}@{{ libvirt_ip }}/system?keyfile=id_rsa__libvirt_svc'
    command: createXML
    path: "/media/data/"
    xml: |
      <volume type='file'>
        <name>NEWVOL.qcow2</name>
        <capacity unit='bytes'>19327352832</capacity>
        <target><format type='qcow2'/></target>
      </volume>
  
- name: Clone volume
  community.libvirt.virt_volume:
    uri: 'qemu+ssh://{{ username }}@{{ libvirt_ip }}/system?keyfile=id_rsa__libvirt_svc'
    command: createXMLFrom
    path: "/media/data/CLONE_SOURCE.qcow2"
    xml: |
      <volume type='file'>
        <name>CLONE_DEST.qcow2</name>
        <capacity unit='bytes'>19327352832</capacity>
        <target><format type='qcow2'/></target>
      </volume>

- name: Get volume XML
  community.libvirt.virt_volume:
    uri: 'qemu+ssh://{{ username }}@{{ libvirt_ip }}/system?keyfile=id_rsa__libvirt_svc'
    command: getXMLDesc
    path: "/media/data/NEWVOL.qcow2"

- name: Delete volume
  community.libvirt.virt_volume:
    uri: 'qemu+ssh://{{ username }}@{{ libvirt_ip }}/system?keyfile=id_rsa__libvirt_svc'
    path: "/media/data/NEWVOL.qcow2"
    command: delete
  
- name: create CIDATA (cloud-init) cdrom
  community.libvirt.virt_volume:
    uri: 'qemu+ssh://{{ username }}@{{ libvirt_ip }}/system?keyfile=id_rsa__libvirt_svc'
    command: create_cidata_cdrom
    config:
      NETWORK_CONFIG:
        version: 2
        ethernets:
          eth0:
            addresses: ["192.168.7.3/24"]
            nameservers:
              addresses: ["192.168.7.2", "8.8.8.8", "8.8.4.4"]
              search: ["example.com"]
      USERDATA: |
        #cloud-config
        system_info:
          default_user: { name: ansible }
        hostname: MYHOSTNAME
        users:
          - name: dougal
            passwd: $6$j212wezy$7...YPYb2F
            ssh_authorized_keys: ['ssh-rsa AAB3NzAADAQABAACA+...GIMhdojtl6mvX29MzSLQ== ansible@dougalseeley.com']
      METADATA:
        "local-hostname": "MYINTERNALHOSTNAME"
    path: "/media/data/NEWVOL--cidata.iso"
  register: r__virt_volume__cidata_cdrom

- name: debug r__virt_volume__cidata_cdrom
  debug: msg={{r__virt_volume__cidata_cdrom}}
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
import traceback
from os.path import basename, dirname
import yaml
import re

try:
    import pycdlib
    PYCDLIB_IMPORT_ERR = None
except ImportError as pycdlib_import_exception:
    PYCDLIB_IMPORT_ERR = pycdlib_import_exception

try:
    import libvirt
    LIBVIRT_IMPORT_ERR = None
except ImportError as libvirt_import_exception:
    LIBVIRT_IMPORT_ERR = libvirt_import_exception

try:
    from lxml import etree
    LXML_IMPORT_ERR = None
except ImportError as lxml_import_exception:
    LXML_IMPORT_ERR = lxml_import_exception

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO


class LibvirtConnection(object):
    def __init__(self, uri, module):
        self.module = module
        conn = libvirt.open(uri)
        if not conn:
            raise Exception("hypervisor connection failure")
        self.conn = conn

    def _get_storageVolPtr_by_path(self):
        return self.conn.storageVolLookupByPath(self.module.params.get('path', None))

    def create_cidata_cdrom(self):
        """
        Create a properly formatted CD image containing cloud-init files, then upload it to the host
        """
        if PYCDLIB_IMPORT_ERR:
            raise PYCDLIB_IMPORT_ERR

        ci_config = yaml.safe_load(self.module.params.get('config', None))

        # Ensure we actually have some CIDATA before creating the CIDATA cdrom
        if ci_config and ('METADATA' in ci_config or 'USERDATA' in ci_config or 'NETWORK_CONFIG' in ci_config):
            volname = re.sub(r'^(.*?)(?:\.iso)?$', '\\1.iso', basename(self.module.params.get('path', None)))       # Append .iso to the name if not exists

            iso = pycdlib.PyCdlib()
            iso.new(interchange_level=3, joliet=True, sys_ident='LINUX', rock_ridge='1.09', vol_ident='cidata')

            if 'NETWORK_CONFIG' in ci_config:
                cidata_network = yaml.safe_dump(ci_config['NETWORK_CONFIG'], width=4096, encoding='utf-8')
                iso.add_fp(BytesIO(cidata_network), len(cidata_network), '/NETWORK_CONFIG.;1', rr_name="network-config", joliet_path='/network-config')

            if 'METADATA' in ci_config:
                cidata_metadata = yaml.safe_dump(ci_config['METADATA'], width=4096, encoding='utf-8')
            else:
                cidata_metadata = "# Note: The user-data and meta-data files are both to be present for it to be considered a valid seed ISO.".encode('utf-8')
                # cidata_metadata = yaml.safe_dump({"local-hostname": re.sub(r'^(.*?)--cidata\.iso$', '\\1.iso', volname)}, width=4096, encoding='utf-8')

            if 'USERDATA' in ci_config:
                cidata_userdata = "#cloud-config\n".encode('utf-8') + yaml.safe_dump(ci_config['USERDATA'], width=4096, encoding='utf-8')
            else:
                cidata_userdata = "# Note: The user-data and meta-data files are both to be present for it to be considered a valid seed ISO.".encode('utf-8')

            iso.add_fp(BytesIO(cidata_metadata), len(cidata_metadata), '/METADATA.;1', rr_name="meta-data", joliet_path='/meta-data')
            iso.add_fp(BytesIO(cidata_userdata), len(cidata_userdata), '/USERDATA.;1', rr_name="user-data", joliet_path='/user-data')

            outiso = BytesIO()
            iso.write_fp(outiso)
            # iso.write('new.iso')
            outiso_len = outiso.getbuffer().nbytes

            # Remote iso XML
            vol_xml = """
              <volume type='file'>
                <name>{}</name>
                <capacity unit='bytes'>{}</capacity>
                <target><format type='iso'/></target>
              </volume>""".format(volname, outiso_len)

            storagePoolPtr = self.conn.storagePoolLookupByTargetPath(dirname(self.module.params.get('path', None)))
            try:
                createdStorageVolPtr = storagePoolPtr.storageVolLookupByName(volname)
            except libvirt.libvirtError as e:
                if e.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_VOL:
                    createdStorageVolPtr = storagePoolPtr.createXML(vol_xml)

                    virStreamPtr = self.conn.newStream(0)
                    createdStorageVolPtr.upload(virStreamPtr, 0, outiso_len, 0)
                    virStreamPtr.send(outiso.getvalue())

                    virStreamPtr.finish()
                else:
                    raise e

            iso.close()
            return {'changed': True, 'create_cidata_cdrom': {'XMLDesc': createdStorageVolPtr.XMLDesc(0),
                                                             'name': createdStorageVolPtr.name(),
                                                             'path': createdStorageVolPtr.path(),
                                                             'key': createdStorageVolPtr.key()}}
        else:
            return {'changed': False, 'create_cidata_cdrom': {'Error': 'No CIDATA to create'}}

    def getXMLDesc(self):
        """ Retrieve the XML descriptor for a given volume """
        try:
            res_XMLDesc = self._get_storageVolPtr_by_path().XMLDesc(0)
            return {'changed': False, 'XMLDesc': res_XMLDesc}
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_VOL:
                return {'changed': False, 'XMLDesc': {'Error': 'libvirt.VIR_ERR_NO_STORAGE_VOL: %s' % (e.get_error_message())}}
            else:
                raise e

    def delete(self):
        """ Delete a storage volume """
        try:
            res_delete = self._get_storageVolPtr_by_path().delete()
            return {'changed': True, 'delete': res_delete}
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_VOL:
                return {'changed': False, 'delete': {'Error': 'libvirt.VIR_ERR_NO_STORAGE_VOL: %s' % (e.get_error_message())}}
            else:
                raise e

    def createXMLFrom(self):
        """ Creates a new volume with the XML provided, cloning from the path provided """
        isChanged = False
        storagePoolPtr = self._get_storageVolPtr_by_path().storagePoolLookupByVolume()
        newXmlTemplate = self.module.params.get('xml', None)
        xml_etree = etree.fromstring(newXmlTemplate)

        newname = xml_etree.xpath("/volume/name")[0].text
        try:
            createdStorageVolPtr = storagePoolPtr.storageVolLookupByName(newname)
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_VOL:
                createdStorageVolPtr = storagePoolPtr.createXMLFrom(newXmlTemplate, self._get_storageVolPtr_by_path())

                if xml_etree.xpath("/volume/capacity[@unit=\"bytes\"]"):
                    size_bytes = xml_etree.xpath("/volume/capacity[@unit=\"bytes\"]")[0].text
                    createdStorageVolPtr.resize(int(size_bytes))

                isChanged = True
            else:
                raise e

        return {'changed': isChanged, 'createXMLFrom': {'XMLDesc': createdStorageVolPtr.XMLDesc(0),
                                                        'name': createdStorageVolPtr.name(),
                                                        'path': createdStorageVolPtr.path(),
                                                        'key': createdStorageVolPtr.key()}}

    def createXML(self):
        """ Creates a new volume with the XML provided, creating it in the path provided """
        isChanged = False
        storagePoolPtr = self.conn.storagePoolLookupByTargetPath(self.module.params.get('path', None))

        newXmlTemplate = self.module.params.get('xml', None)
        xml_etree = etree.fromstring(newXmlTemplate)

        newname = xml_etree.xpath("/volume/name")[0].text
        try:
            createdStorageVolPtr = storagePoolPtr.storageVolLookupByName(newname)
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_VOL:
                createdStorageVolPtr = storagePoolPtr.createXML(newXmlTemplate)
                isChanged = True
            else:
                raise e

        return {'changed': isChanged, 'createXML': {'XMLDesc': createdStorageVolPtr.XMLDesc(0),
                                                    'name': createdStorageVolPtr.name(),
                                                    'path': createdStorageVolPtr.path(),
                                                    'key': createdStorageVolPtr.key()}}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(aliases=['pool']),
            state=dict(choices=['present', 'absent']),
            command=dict(),
            uri=dict(default='qemu:///system'),
            path=dict(type='str', default=''),
            xml=dict(),
            config=dict()
        ),
        supports_check_mode=True
    )

    if LIBVIRT_IMPORT_ERR:
        module.fail_json(msg=missing_required_lib("libvirt"), exception=LIBVIRT_IMPORT_ERR)

    if LXML_IMPORT_ERR:
        module.fail_json(msg=missing_required_lib("lxml"), exception=LXML_IMPORT_ERR)

    command = module.params.get('command', None)
    uri = module.params.get('uri', None)

    if command:
        v = LibvirtConnection(uri, module)

        if hasattr(v, command):
            try:
                res = getattr(v, command)()
            except Exception as e:
                module.fail_json(msg=repr(e), exception=traceback.format_exc())
            else:
                if not isinstance(res, dict):
                    res = {command: res}

                module.exit_json(**res)
        else:
            module.fail_json(msg="Command %s not recognized" % command)
    else:
        module.fail_json(msg="expected command parameter to be specified")


if __name__ == '__main__':
    main()
