try:
    import libvirt
except ImportError:
    HAS_VIRT = False
else:
    HAS_VIRT = True

from ansible_collections.community.libvirt.plugins.module_utils.entry import EntryNotFound
from lxml import etree

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

class LibvirtConnection(object):

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
