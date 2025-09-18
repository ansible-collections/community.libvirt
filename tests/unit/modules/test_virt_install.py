# -*- coding: utf-8 -*-
#
# (c) 2025, Joey Zhang <thinkdoggie@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import unittest

from ansible_collections.community.libvirt.tests.unit.compat import mock
from ansible_collections.community.libvirt.plugins.modules.virt_install import core
from ansible_collections.community.libvirt.plugins.module_utils.libvirt import (
    VMNotFound, VIRT_SUCCESS, VIRT_FAILED)


class TestCoreFunction(unittest.TestCase):
    """Test cases for the core() function"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.params = {
            'name': 'test-vm',
            'state': 'present',
            'uri': 'qemu:///system',
            'recreate': False
        }
        self.mock_module.check_mode = False
        self.mock_module.fail_json = mock.Mock(
            side_effect=Exception("fail_json called"))

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_missing_vm_name(
            self,
            mock_libvirt_wrapper,
            mock_virt_install_tool):
        """Test core() when VM name is missing"""
        self.mock_module.params['name'] = None

        with self.assertRaises(Exception) as context:
            core(self.mock_module)

        self.mock_module.fail_json.assert_called_once_with(
            msg="virtual machine name is missing")

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_present_vm_not_exists_create_success(
            self, mock_libvirt_wrapper, mock_virt_install_tool):
        """Test core() when VM doesn't exist and should be created successfully"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        # VM doesn't exist - should raise VMNotFound exception
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")

        # VirtInstallTool.execute returns success
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, {"msg": "VM created successfully"})

        # Call core function
        rc, result = core(self.mock_module)

        # Assertions
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])
        self.assertEqual(result['msg'], "VM created successfully")
        mock_virt_install.execute.assert_called_once_with(dryrun=False)

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_present_vm_not_exists_create_failure(
            self, mock_libvirt_wrapper, mock_virt_install_tool):
        """Test core() when VM doesn't exist and creation fails"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        # VM doesn't exist - should raise VMNotFound exception
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")

        # VirtInstallTool.execute returns failure
        mock_virt_install.execute.return_value = (
            False, VIRT_FAILED, {"msg": "VM creation failed"})

        # Call core function
        rc, result = core(self.mock_module)

        # Assertions
        self.assertEqual(rc, VIRT_FAILED)
        self.assertFalse(result['changed'])
        self.assertEqual(result['msg'], "VM creation failed")

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_present_vm_exists_no_recreate(
            self, mock_libvirt_wrapper, mock_virt_install_tool):
        """Test core() when VM exists and recreate=False"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        # VM exists
        mock_vm = mock.Mock()
        mock_virt_conn.find_vm.return_value = mock_vm

        # Call core function
        rc, result = core(self.mock_module)

        # Assertions
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertFalse(result['changed'])
        self.assertEqual(
            result['message'],
            "virtual machine 'test-vm' already exists")
        mock_virt_install.execute.assert_not_called()

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_present_vm_exists_recreate_inactive(
            self, mock_libvirt_wrapper, mock_virt_install_tool):
        """Test core() when VM exists, recreate=True, and VM is inactive"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        self.mock_module.params['recreate'] = True

        # VM exists and is inactive
        mock_vm = mock.Mock()
        mock_vm.isActive.return_value = False
        mock_virt_conn.find_vm.return_value = mock_vm

        # VirtInstallTool.execute returns success
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, {"msg": "VM recreated successfully"})

        # Call core function
        rc, result = core(self.mock_module)

        # Assertions
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])
        self.assertEqual(result['msg'], "VM recreated successfully")
        # Should not be called if VM is inactive
        mock_virt_conn.destroy.assert_not_called()
        mock_virt_conn.undefine.assert_called_once_with('test-vm')
        mock_virt_install.execute.assert_called_once_with(dryrun=False)

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_present_vm_exists_recreate_active(
            self, mock_libvirt_wrapper, mock_virt_install_tool):
        """Test core() when VM exists, recreate=True, and VM is active"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        self.mock_module.params['recreate'] = True

        # VM exists and is active
        mock_vm = mock.Mock()
        mock_vm.isActive.return_value = True
        mock_virt_conn.find_vm.return_value = mock_vm

        # VirtInstallTool.execute returns success
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, {"msg": "VM recreated successfully"})

        # Call core function
        rc, result = core(self.mock_module)

        # Assertions
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])
        self.assertEqual(result['msg'], "VM recreated successfully")
        mock_virt_conn.destroy.assert_called_once_with('test-vm')
        mock_virt_conn.undefine.assert_called_once_with('test-vm')
        mock_virt_install.execute.assert_called_once_with(dryrun=False)

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_absent_vm_not_exists(
            self,
            mock_libvirt_wrapper,
            mock_virt_install_tool):
        """Test core() when state=absent and VM doesn't exist"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        self.mock_module.params['state'] = 'absent'

        # VM doesn't exist - should raise VMNotFound exception
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")

        # Call core function
        rc, result = core(self.mock_module)

        # Assertions
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertFalse(result['changed'])
        self.assertEqual(
            result['message'],
            "virtual machine 'test-vm' is already absent")
        mock_virt_conn.destroy.assert_not_called()
        mock_virt_conn.undefine.assert_not_called()

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_absent_vm_exists_inactive(
            self, mock_libvirt_wrapper, mock_virt_install_tool):
        """Test core() when state=absent, VM exists, and VM is inactive"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        self.mock_module.params['state'] = 'absent'

        # VM exists and is inactive
        mock_vm = mock.Mock()
        mock_vm.isActive.return_value = False
        mock_virt_conn.find_vm.return_value = mock_vm

        # Call core function
        rc, result = core(self.mock_module)

        # Assertions
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])
        # Should not be called if VM is inactive
        mock_virt_conn.destroy.assert_not_called()
        mock_virt_conn.undefine.assert_called_once_with('test-vm')

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_absent_vm_exists_active(
            self, mock_libvirt_wrapper, mock_virt_install_tool):
        """Test core() when state=absent, VM exists, and VM is active"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        self.mock_module.params['state'] = 'absent'

        # VM exists and is active
        mock_vm = mock.Mock()
        mock_vm.isActive.return_value = True
        mock_virt_conn.find_vm.return_value = mock_vm

        # Call core function
        rc, result = core(self.mock_module)

        # Assertions
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])
        mock_virt_conn.destroy.assert_called_once_with('test-vm')
        mock_virt_conn.undefine.assert_called_once_with('test-vm')

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_unsupported_state(
            self,
            mock_libvirt_wrapper,
            mock_virt_install_tool):
        """Test core() with unsupported state"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        self.mock_module.params['state'] = 'invalid_state'

        # VM doesn't exist (doesn't matter for this test) - should raise
        # VMNotFound exception
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")

        # Call core function and expect failure
        with self.assertRaises(Exception) as context:
            core(self.mock_module)

        self.mock_module.fail_json.assert_called_once_with(
            msg="unsupported state 'invalid_state'")

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_check_mode_enabled(
            self,
            mock_libvirt_wrapper,
            mock_virt_install_tool):
        """Test core() with check_mode enabled"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        self.mock_module.check_mode = True

        # VM doesn't exist - should raise VMNotFound exception
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")

        # VirtInstallTool.execute returns success
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, {"msg": "VM created successfully"})

        # Call core function
        rc, result = core(self.mock_module)

        # Assertions
        self.assertEqual(rc, VIRT_SUCCESS)
        mock_virt_install.execute.assert_called_once_with(dryrun=True)

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_result_structure(
            self,
            mock_libvirt_wrapper,
            mock_virt_install_tool):
        """Test core() returns proper result structure"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        # VM exists and no recreate
        mock_vm = mock.Mock()
        mock_virt_conn.find_vm.return_value = mock_vm

        # Call core function
        rc, result = core(self.mock_module)

        # Assertions - check result structure
        self.assertIsInstance(result, dict)
        self.assertIn('changed', result)
        self.assertIn('orignal_message', result)  # Note: typo in original code
        self.assertIn('message', result)
        self.assertIsInstance(result['changed'], bool)

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_libvirt_wrapper_initialization(
            self, mock_libvirt_wrapper, mock_virt_install_tool):
        """Test core() properly initializes LibvirtWrapper"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        # VM doesn't exist - should raise VMNotFound exception
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, {"msg": "VM created"})

        # Call core function
        rc, result = core(self.mock_module)

        # Verify LibvirtWrapper was initialized with the module
        mock_libvirt_wrapper.assert_called_once_with(self.mock_module)

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_virt_install_tool_initialization(
            self, mock_libvirt_wrapper, mock_virt_install_tool):
        """Test core() properly initializes VirtInstallTool"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        # VM doesn't exist - should raise VMNotFound exception
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, {"msg": "VM created"})

        # Call core function
        rc, result = core(self.mock_module)

        # Verify VirtInstallTool was initialized with the module
        mock_virt_install_tool.assert_called_once_with(self.mock_module)

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_find_vm_called_with_correct_name(
            self, mock_libvirt_wrapper, mock_virt_install_tool):
        """Test core() calls find_vm with correct VM name"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        # VM doesn't exist - should raise VMNotFound exception
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, {"msg": "VM created"})

        # Call core function
        rc, result = core(self.mock_module)

        # Verify find_vm was called with correct name
        mock_virt_conn.find_vm.assert_called_once_with('test-vm')

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_different_vm_names(
            self,
            mock_libvirt_wrapper,
            mock_virt_install_tool):
        """Test core() with different VM names"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        # Test with different VM name
        self.mock_module.params['name'] = 'different-vm-name'

        # VM doesn't exist - should raise VMNotFound exception
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, {"msg": "VM created"})

        # Call core function
        rc, result = core(self.mock_module)

        # Verify find_vm was called with correct name
        mock_virt_conn.find_vm.assert_called_once_with('different-vm-name')

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_empty_vm_name(
            self,
            mock_libvirt_wrapper,
            mock_virt_install_tool):
        """Test core() with empty VM name"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        self.mock_module.params['name'] = ''

        # Call core function and expect failure
        with self.assertRaises(Exception) as context:
            core(self.mock_module)

        self.mock_module.fail_json.assert_called_once_with(
            msg="virtual machine name is missing")

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.LibvirtWrapper')
    def test_core_execute_extra_result_merging(
            self, mock_libvirt_wrapper, mock_virt_install_tool):
        """Test core() properly merges extra results from execute"""
        # Setup mocks
        mock_virt_conn = mock.Mock()
        mock_virt_install = mock.Mock()
        mock_libvirt_wrapper.return_value = mock_virt_conn
        mock_virt_install_tool.return_value = mock_virt_install

        # VM doesn't exist - should raise VMNotFound exception
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")

        # VirtInstallTool.execute returns success with extra data
        extra_data = {
            "msg": "VM created successfully",
            "extra_field": "extra_value",
            "command": "virt-install --name test-vm"
        }
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, extra_data)

        # Call core function
        rc, result = core(self.mock_module)

        # Assertions - check that extra data is merged
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])
        self.assertEqual(result['msg'], "VM created successfully")
        self.assertEqual(result['extra_field'], "extra_value")
        self.assertEqual(result['command'], "virt-install --name test-vm")


if __name__ == '__main__':
    unittest.main(verbosity=2)
