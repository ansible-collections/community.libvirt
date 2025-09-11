# -*- coding: utf-8 -*-
#
# (c) 2025, Joey Zhang <thinkdoggie@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import unittest

from ansible_collections.community.libvirt.tests.unit.compat import mock
from ansible_collections.community.libvirt.plugins.module_utils.libvirt import (
    LibvirtConnection,
    VMNotFound,
    VIRT_FAILED,
    VIRT_SUCCESS,
    VIRT_UNAVAILABLE,
    VIRT_STATE_NAME_MAP,
    HAS_VIRT,
    HAS_XML
)


class TestLibvirtConnectionInit(unittest.TestCase):
    """Test LibvirtConnection initialization"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.run_command.return_value = (0, 'Linux test 5.10.0', '')

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_init_normal_connection(self, mock_libvirt):
        """Test initialization with normal libvirt connection"""
        mock_conn = mock.Mock()
        mock_libvirt.open.return_value = mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)

        self.assertEqual(conn.module, self.mock_module)
        self.assertEqual(conn.conn, mock_conn)
        mock_libvirt.open.assert_called_once_with('qemu:///system')
        self.mock_module.run_command.assert_called_once_with('uname -r')

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_init_xen_connection(self, mock_libvirt):
        """Test initialization with Xen hypervisor detection"""
        mock_conn = mock.Mock()
        mock_libvirt.open.return_value = mock_conn
        self.mock_module.run_command.return_value = (0, 'Linux test 5.10.0-xen', '')

        conn = LibvirtConnection('qemu:///system', self.mock_module)

        self.assertEqual(conn.conn, mock_conn)
        mock_libvirt.open.assert_called_once_with(None)

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_init_esx_connection(self, mock_libvirt):
        """Test initialization with ESX connection"""
        mock_conn = mock.Mock()
        mock_libvirt.VIR_CRED_AUTHNAME = 1
        mock_libvirt.VIR_CRED_NOECHOPROMPT = 2
        mock_libvirt.openAuth.return_value = mock_conn

        conn = LibvirtConnection('esx://host/system', self.mock_module)

        self.assertEqual(conn.conn, mock_conn)
        # Verify the call was made with expected structure
        args, kwargs = mock_libvirt.openAuth.call_args
        self.assertEqual(args[0], 'esx://host/system')
        self.assertEqual(args[1], [[1, 2], [], None])

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_init_connection_failure(self, mock_libvirt):
        """Test initialization when connection fails"""
        mock_libvirt.open.return_value = None

        with self.assertRaises(Exception) as context:
            LibvirtConnection('qemu:///system', self.mock_module)

        self.assertEqual(str(context.exception), "hypervisor connection failure")


class TestLibvirtConnectionVMFinding(unittest.TestCase):
    """Test VM finding functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.run_command.return_value = (0, 'Linux test 5.10.0', '')

        # Create mock VM objects
        self.mock_vm1 = mock.Mock()
        self.mock_vm1.name.return_value = 'test-vm1'
        self.mock_vm2 = mock.Mock()
        self.mock_vm2.name.return_value = 'test-vm2'
        self.mock_vms = [self.mock_vm1, self.mock_vm2]

        # Create mock connection
        self.mock_conn = mock.Mock()
        self.mock_conn.listAllDomains.return_value = self.mock_vms

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_find_vm_by_name(self, mock_libvirt):
        """Test finding VM by name"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.find_vm('test-vm1')

        self.assertEqual(result, self.mock_vm1)
        self.mock_conn.listAllDomains.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_find_vm_not_found(self, mock_libvirt):
        """Test finding non-existent VM"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)

        with self.assertRaises(VMNotFound) as context:
            conn.find_vm('nonexistent-vm')

        self.assertEqual(str(context.exception), "virtual machine nonexistent-vm not found")

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_find_vm_list_all(self, mock_libvirt):
        """Test finding all VMs with vmid=-1"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.find_vm(-1)

        self.assertEqual(result, self.mock_vms)
        self.mock_conn.listAllDomains.assert_called_once()


class TestLibvirtConnectionLifecycleOperations(unittest.TestCase):
    """Test VM lifecycle operations"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.run_command.return_value = (0, 'Linux test 5.10.0', '')

        self.mock_vm = mock.Mock()
        self.mock_vm.name.return_value = 'test-vm'
        self.mock_vm.shutdown.return_value = 0
        self.mock_vm.suspend.return_value = 0
        self.mock_vm.resume.return_value = 0
        self.mock_vm.create.return_value = 0
        self.mock_vm.destroy.return_value = 0
        self.mock_vm.undefineFlags.return_value = 0

        self.mock_conn = mock.Mock()
        self.mock_conn.listAllDomains.return_value = [self.mock_vm]

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_shutdown(self, mock_libvirt):
        """Test VM shutdown"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.shutdown('test-vm')

        self.assertEqual(result, 0)
        self.mock_vm.shutdown.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_pause(self, mock_libvirt):
        """Test VM pause (alias for suspend)"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.pause('test-vm')

        self.assertEqual(result, 0)
        self.mock_vm.suspend.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_unpause(self, mock_libvirt):
        """Test VM unpause (alias for resume)"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.unpause('test-vm')

        self.assertEqual(result, 0)
        self.mock_vm.resume.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_suspend(self, mock_libvirt):
        """Test VM suspend"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.suspend('test-vm')

        self.assertEqual(result, 0)
        self.mock_vm.suspend.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_resume(self, mock_libvirt):
        """Test VM resume"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.resume('test-vm')

        self.assertEqual(result, 0)
        self.mock_vm.resume.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_create(self, mock_libvirt):
        """Test VM create"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.create('test-vm')

        self.assertEqual(result, 0)
        self.mock_vm.create.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_destroy(self, mock_libvirt):
        """Test VM destroy"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.destroy('test-vm')

        self.assertEqual(result, 0)
        self.mock_vm.destroy.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_undefine_without_flag(self, mock_libvirt):
        """Test VM undefine without deletion flag"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.undefine('test-vm', 0)

        self.assertEqual(result, 0)
        self.mock_vm.undefineFlags.assert_called_once_with(0)

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_undefine_with_volume_flag(self, mock_libvirt):
        """Test VM undefine with volume deletion flag"""
        mock_libvirt.open.return_value = self.mock_conn

        # Mock delete_domain_volumes method
        with mock.patch.object(LibvirtConnection, 'delete_domain_volumes') as mock_delete:
            conn = LibvirtConnection('qemu:///system', self.mock_module)
            result = conn.undefine('test-vm', 32)  # 32 = flag with volume deletion bit

            self.assertEqual(result, 0)
            mock_delete.assert_called_once_with('test-vm')
            self.mock_vm.undefineFlags.assert_called_once_with(32)


class TestLibvirtConnectionStatusAndInfo(unittest.TestCase):
    """Test VM status and information methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.run_command.return_value = (0, 'Linux test 5.10.0', '')

        self.mock_vm = mock.Mock()
        self.mock_vm.name.return_value = 'test-vm'
        self.mock_vm.info.return_value = [1, 0, 0, 0, 0]  # State 1 = running
        self.mock_vm.XMLDesc.return_value = '<domain>...</domain>'
        self.mock_vm.maxVcpus.return_value = 4
        self.mock_vm.maxMemory.return_value = 4194304
        self.mock_vm.autostart.return_value = True
        self.mock_vm.setAutostart.return_value = 0
        self.mock_vm.UUIDString.return_value = '12345678-1234-5678-9012-123456789abc'

        self.mock_conn = mock.Mock()
        self.mock_conn.listAllDomains.return_value = [self.mock_vm]
        self.mock_conn.lookupByName.return_value = self.mock_vm
        self.mock_conn.getInfo.return_value = (1, 2048, 8, 2500, 1, 2, 4, 1)
        self.mock_conn.getType.return_value = 'QEMU'
        self.mock_conn.getFreeMemory.return_value = 1073741824
        self.mock_conn.defineXML.return_value = self.mock_vm

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_get_status2(self, mock_libvirt):
        """Test get_status2 method with VM object"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.get_status2(self.mock_vm)

        self.assertEqual(result, 'running')
        self.mock_vm.info.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_get_status(self, mock_libvirt):
        """Test get_status method with VM name"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.get_status('test-vm')

        self.assertEqual(result, 'running')

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_get_status_unknown_state(self, mock_libvirt):
        """Test get_status with unknown state"""
        mock_libvirt.open.return_value = self.mock_conn
        self.mock_vm.info.return_value = [99, 0, 0, 0, 0]  # Unknown state

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.get_status('test-vm')

        self.assertEqual(result, 'unknown')

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_nodeinfo(self, mock_libvirt):
        """Test nodeinfo method"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.nodeinfo()

        self.assertEqual(result, (1, 2048, 8, 2500, 1, 2, 4, 1))
        self.mock_conn.getInfo.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_get_type(self, mock_libvirt):
        """Test get_type method"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.get_type()

        self.assertEqual(result, 'QEMU')
        self.mock_conn.getType.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_getFreeMemory(self, mock_libvirt):
        """Test getFreeMemory method"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.getFreeMemory()

        self.assertEqual(result, 1073741824)
        self.mock_conn.getFreeMemory.assert_called_once()


class TestLibvirtConnectionXMLOperations(unittest.TestCase):
    """Test XML operations and VM configuration methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.run_command.return_value = (0, 'Linux test 5.10.0', '')

        self.mock_vm = mock.Mock()
        self.mock_vm.name.return_value = 'test-vm'
        self.mock_vm.XMLDesc.return_value = '''<domain>
            <name>test-vm</name>
            <devices>
                <interface type='network'>
                    <mac address='52:54:00:12:34:56'/>
                    <source network='default'/>
                    <address type='pci' bus='0x00'/>
                </interface>
                <interface type='bridge'>
                    <mac address='52:54:00:12:34:57'/>
                    <source bridge='br0'/>
                    <address type='pci' bus='0x01'/>
                </interface>
                <disk type='file' device='disk'>
                    <source file='/var/lib/libvirt/images/test.qcow2'/>
                </disk>
                <disk type='file' device='disk'>
                    <source file='/var/lib/libvirt/images/data.qcow2'/>
                </disk>
            </devices>
        </domain>'''
        self.mock_vm.maxVcpus.return_value = 4
        self.mock_vm.maxMemory.return_value = 4194304
        self.mock_vm.UUIDString.return_value = '12345678-1234-5678-9012-123456789abc'

        self.mock_conn = mock.Mock()
        self.mock_conn.lookupByName.return_value = self.mock_vm
        self.mock_conn.defineXML.return_value = self.mock_vm

        # Mock storage volumes for disk deletion test
        self.mock_volume1 = mock.Mock()
        self.mock_volume2 = mock.Mock()
        self.mock_conn.storageVolLookupByPath.side_effect = [
            self.mock_volume1, self.mock_volume2
        ]

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_get_xml(self, mock_libvirt):
        """Test get_xml method"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.get_xml('test-vm')

        self.assertIn('<domain>', result)
        self.assertIn('<name>test-vm</name>', result)
        self.mock_conn.lookupByName.assert_called_once_with('test-vm')
        self.mock_vm.XMLDesc.assert_called_once_with(0)

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_get_maxVcpus(self, mock_libvirt):
        """Test get_maxVcpus method"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.get_maxVcpus('test-vm')

        self.assertEqual(result, 4)
        self.mock_conn.lookupByName.assert_called_once_with('test-vm')
        self.mock_vm.maxVcpus.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_get_maxMemory(self, mock_libvirt):
        """Test get_maxMemory method"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.get_maxMemory('test-vm')

        self.assertEqual(result, 4194304)
        self.mock_conn.lookupByName.assert_called_once_with('test-vm')
        self.mock_vm.maxMemory.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_get_uuid(self, mock_libvirt):
        """Test get_uuid method"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.get_uuid('test-vm')

        self.assertEqual(result, '12345678-1234-5678-9012-123456789abc')
        self.mock_conn.lookupByName.assert_called_once_with('test-vm')
        self.mock_vm.UUIDString.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_define_from_xml(self, mock_libvirt):
        """Test define_from_xml method"""
        mock_libvirt.open.return_value = self.mock_conn
        test_xml = '<domain><name>new-vm</name></domain>'

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.define_from_xml(test_xml)

        self.assertEqual(result, self.mock_vm)
        self.mock_conn.defineXML.assert_called_once_with(test_xml)

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.etree', create=True)
    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_get_interfaces(self, mock_libvirt, mock_etree):
        """Test get_interfaces method"""
        mock_libvirt.open.return_value = self.mock_conn

        # Mock etree parsing
        mock_root = mock.Mock()
        mock_etree.fromstring.return_value = mock_root

        # Mock interface elements
        mock_interface1 = mock.Mock()
        mock_interface1.get.return_value = 'network'
        mock_source1 = mock.Mock()
        mock_source1.get.return_value = 'default'
        mock_mac1 = mock.Mock()
        mock_mac1.get.return_value = '52:54:00:12:34:56'
        mock_address1 = mock.Mock()
        mock_address1.get.return_value = '0x00'
        mock_interface1.find.side_effect = [mock_source1, mock_mac1, mock_address1]

        mock_interface2 = mock.Mock()
        mock_interface2.get.return_value = 'bridge'
        mock_source2 = mock.Mock()
        mock_source2.get.return_value = 'br0'
        mock_mac2 = mock.Mock()
        mock_mac2.get.return_value = '52:54:00:12:34:57'
        mock_address2 = mock.Mock()
        mock_address2.get.return_value = '0x01'
        mock_interface2.find.side_effect = [mock_source2, mock_mac2, mock_address2]

        mock_root.findall.return_value = [mock_interface1, mock_interface2]

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.get_interfaces('test-vm')

        expected = {
            'network_interfaces': {
                'interface_1': {
                    'type': 'NAT',
                    'mac': '52:54:00:12:34:56',
                    'pci_bus': '0x00',
                    'source': 'default'
                },
                'interface_2': {
                    'type': 'bridge',
                    'mac': '52:54:00:12:34:57',
                    'pci_bus': '0x01',
                    'source': 'br0'
                }
            }
        }

        self.assertEqual(result, expected)

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.etree', create=True)
    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_delete_domain_volumes(self, mock_libvirt, mock_etree):
        """Test delete_domain_volumes method"""
        mock_libvirt.open.return_value = self.mock_conn

        # Mock etree parsing
        mock_root = mock.Mock()
        mock_etree.fromstring.return_value = mock_root

        # Mock disk elements
        mock_disk1 = mock.Mock()
        mock_disk1.get.return_value = '/var/lib/libvirt/images/test.qcow2'
        mock_disk2 = mock.Mock()
        mock_disk2.get.return_value = '/var/lib/libvirt/images/data.qcow2'
        mock_root.findall.return_value = [mock_disk1, mock_disk2]

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        conn.delete_domain_volumes('test-vm')

        # Verify volumes were looked up and deleted
        expected_calls = [
            mock.call('/var/lib/libvirt/images/test.qcow2'),
            mock.call('/var/lib/libvirt/images/data.qcow2')
        ]
        self.mock_conn.storageVolLookupByPath.assert_has_calls(expected_calls)
        self.mock_volume1.delete.assert_called_once()
        self.mock_volume2.delete.assert_called_once()


class TestLibvirtConnectionAutostart(unittest.TestCase):
    """Test autostart functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.run_command.return_value = (0, 'Linux test 5.10.0', '')

        self.mock_vm = mock.Mock()
        self.mock_vm.autostart.return_value = True
        self.mock_vm.setAutostart.return_value = 0

        self.mock_conn = mock.Mock()
        self.mock_conn.lookupByName.return_value = self.mock_vm

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_get_autostart(self, mock_libvirt):
        """Test get_autostart method"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.get_autostart('test-vm')

        self.assertTrue(result)
        self.mock_conn.lookupByName.assert_called_once_with('test-vm')
        self.mock_vm.autostart.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_set_autostart_enable(self, mock_libvirt):
        """Test set_autostart method to enable autostart"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.set_autostart('test-vm', True)

        self.assertEqual(result, 0)
        self.mock_conn.lookupByName.assert_called_once_with('test-vm')
        self.mock_vm.setAutostart.assert_called_once_with(True)

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_set_autostart_disable(self, mock_libvirt):
        """Test set_autostart method to disable autostart"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)
        result = conn.set_autostart('test-vm', False)

        self.assertEqual(result, 0)
        self.mock_conn.lookupByName.assert_called_once_with('test-vm')
        self.mock_vm.setAutostart.assert_called_once_with(False)


class TestLibvirtConnectionErrorHandling(unittest.TestCase):
    """Test error handling and exception scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.run_command.return_value = (0, 'Linux test 5.10.0', '')

        self.mock_conn = mock.Mock()

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_vm_operations_with_vm_not_found(self, mock_libvirt):
        """Test various operations when VM is not found"""
        mock_libvirt.open.return_value = self.mock_conn
        self.mock_conn.listAllDomains.return_value = []

        conn = LibvirtConnection('qemu:///system', self.mock_module)

        operations = [
            ('shutdown', 'nonexistent-vm'),
            ('pause', 'nonexistent-vm'),
            ('unpause', 'nonexistent-vm'),
            ('suspend', 'nonexistent-vm'),
            ('resume', 'nonexistent-vm'),
            ('create', 'nonexistent-vm'),
            ('destroy', 'nonexistent-vm'),
            ('get_status', 'nonexistent-vm'),
        ]

        for operation, vm_name in operations:
            with self.subTest(operation=operation):
                with self.assertRaises(VMNotFound):
                    getattr(conn, operation)(vm_name)

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_xml_operations_with_missing_vm(self, mock_libvirt):
        """Test XML operations when VM is not found"""
        mock_libvirt.open.return_value = self.mock_conn

        # Simulate VM not found exception from libvirt
        mock_libvirt.libvirtError = Exception
        self.mock_conn.lookupByName.side_effect = Exception("Domain not found")

        conn = LibvirtConnection('qemu:///system', self.mock_module)

        operations = [
            ('get_xml', 'nonexistent-vm'),
            ('get_maxVcpus', 'nonexistent-vm'),
            ('get_maxMemory', 'nonexistent-vm'),
            ('get_uuid', 'nonexistent-vm'),
            ('get_autostart', 'nonexistent-vm'),
        ]

        for operation, vm_name in operations:
            with self.subTest(operation=operation):
                with self.assertRaises(Exception):
                    getattr(conn, operation)(vm_name)

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_undefine_with_volume_deletion_error(self, mock_libvirt):
        """Test undefine when volume deletion fails"""
        mock_libvirt.open.return_value = self.mock_conn

        mock_vm = mock.Mock()
        mock_vm.name.return_value = 'test-vm'
        self.mock_conn.listAllDomains.return_value = [mock_vm]

        # Mock delete_domain_volumes to raise an exception
        with mock.patch.object(LibvirtConnection, 'delete_domain_volumes', side_effect=Exception("Volume not found")):
            conn = LibvirtConnection('qemu:///system', self.mock_module)

            with self.assertRaises(Exception):
                conn.undefine('test-vm', 32)  # Flag with volume deletion bit

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.etree', create=True)
    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_delete_domain_volumes_with_missing_volume(self, mock_libvirt, mock_etree):
        """Test delete_domain_volumes when storage volume is not found"""
        mock_libvirt.open.return_value = self.mock_conn

        # Mock VM with disk
        mock_vm = mock.Mock()
        mock_vm.XMLDesc.return_value = '<domain><devices><disk type="file"><source file="/path/to/disk.qcow2"/></disk></devices></domain>'
        self.mock_conn.lookupByName.return_value = mock_vm

        # Mock etree parsing
        mock_root = mock.Mock()
        mock_etree.fromstring.return_value = mock_root
        mock_disk = mock.Mock()
        mock_disk.get.return_value = '/path/to/disk.qcow2'
        mock_root.findall.return_value = [mock_disk]

        # Simulate volume not found
        self.mock_conn.storageVolLookupByPath.side_effect = Exception("Volume not found")

        conn = LibvirtConnection('qemu:///system', self.mock_module)

        # Should raise exception when volume lookup fails
        with self.assertRaises(Exception):
            conn.delete_domain_volumes('test-vm')


class TestLibvirtConnectionConstants(unittest.TestCase):
    """Test constants and state mappings"""

    def test_constants_defined(self):
        """Test that constants are properly defined"""
        self.assertEqual(VIRT_FAILED, 1)
        self.assertEqual(VIRT_SUCCESS, 0)
        self.assertEqual(VIRT_UNAVAILABLE, 2)

    def test_state_name_map(self):
        """Test VIRT_STATE_NAME_MAP mappings"""
        expected_mappings = {
            0: 'running',
            1: 'running',
            2: 'running',
            3: 'paused',
            4: 'shutdown',
            5: 'shutdown',
            6: 'crashed',
        }

        self.assertEqual(VIRT_STATE_NAME_MAP, expected_mappings)

    def test_has_virt_and_xml_flags(self):
        """Test HAS_VIRT and HAS_XML flags"""
        # These should be boolean values
        self.assertIsInstance(HAS_VIRT, bool)
        self.assertIsInstance(HAS_XML, bool)


class TestLibvirtConnectionIntegration(unittest.TestCase):
    """Integration tests combining multiple methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.run_command.return_value = (0, 'Linux test 5.10.0', '')

        self.mock_vm = mock.Mock()
        self.mock_vm.name.return_value = 'test-vm'
        self.mock_vm.info.return_value = [1, 2097152, 2097152, 2, 1000000000]
        self.mock_vm.shutdown.return_value = 0
        self.mock_vm.XMLDesc.return_value = '<domain><name>test-vm</name></domain>'

        self.mock_conn = mock.Mock()
        self.mock_conn.listAllDomains.return_value = [self.mock_vm]
        self.mock_conn.lookupByName.return_value = self.mock_vm

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_vm_lifecycle_workflow(self, mock_libvirt):
        """Test a complete VM lifecycle workflow"""
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)

        # Find VM
        vm = conn.find_vm('test-vm')
        self.assertEqual(vm, self.mock_vm)

        # Check status
        status = conn.get_status('test-vm')
        self.assertEqual(status, 'running')

        # Get VM details
        xml = conn.get_xml('test-vm')
        self.assertIn('<domain>', xml)

        # Shutdown VM
        result = conn.shutdown('test-vm')
        self.assertEqual(result, 0)

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_multiple_vm_operations(self, mock_libvirt):
        """Test operations on multiple VMs"""
        # Create multiple mock VMs
        mock_vm1 = mock.Mock()
        mock_vm1.name.return_value = 'vm1'
        mock_vm2 = mock.Mock()
        mock_vm2.name.return_value = 'vm2'

        self.mock_conn.listAllDomains.return_value = [mock_vm1, mock_vm2]
        mock_libvirt.open.return_value = self.mock_conn

        conn = LibvirtConnection('qemu:///system', self.mock_module)

        # Get all VMs
        all_vms = conn.find_vm(-1)
        self.assertEqual(len(all_vms), 2)
        self.assertEqual(all_vms, [mock_vm1, mock_vm2])

        # Find specific VM
        vm1 = conn.find_vm('vm1')
        self.assertEqual(vm1, mock_vm1)

        vm2 = conn.find_vm('vm2')
        self.assertEqual(vm2, mock_vm2)

    @mock.patch('ansible_collections.community.libvirt.plugins.module_utils.libvirt.libvirt', create=True)
    def test_hypervisor_info_operations(self, mock_libvirt):
        """Test hypervisor information operations"""
        mock_libvirt.open.return_value = self.mock_conn
        self.mock_conn.getInfo.return_value = (1, 8192, 16, 2400, 2, 4, 2, 1)
        self.mock_conn.getType.return_value = 'QEMU'
        self.mock_conn.getFreeMemory.return_value = 2147483648

        conn = LibvirtConnection('qemu:///system', self.mock_module)

        # Get node info
        node_info = conn.nodeinfo()
        self.assertEqual(node_info, (1, 8192, 16, 2400, 2, 4, 2, 1))

        # Get hypervisor type
        hv_type = conn.get_type()
        self.assertEqual(hv_type, 'QEMU')

        # Get free memory
        free_mem = conn.getFreeMemory()
        self.assertEqual(free_mem, 2147483648)


if __name__ == '__main__':
    unittest.main(verbosity=2)
