# -*- coding: utf-8 -*-

import unittest

from ansible_collections.community.libvirt.tests.unit.compat import mock
from ansible_collections.community.libvirt.plugins.modules.virt_install import (
    _dict2options, _get_option_mapping, core,
    VIRT_SUCCESS, VIRT_FAILED, OPTION_BOOL_ONOFF, VirtInstallTool)
from ansible_collections.community.libvirt.plugins.module_utils.libvirt import (
    VMNotFound)


class TestDict2Options(unittest.TestCase):

    def test_none_input(self):
        """Test that None input returns empty string"""
        result = _dict2options(None, None)
        self.assertEqual(result, "")

    def test_non_dict_input(self):
        """Test that non-dict input returns string representation"""
        self.assertEqual(_dict2options(42, None), "42")
        self.assertEqual(_dict2options("test", None), "test")
        self.assertEqual(_dict2options(True, None), "True")

    def test_empty_dict(self):
        """Test that empty dict returns 'none'"""
        result = _dict2options({}, None)
        self.assertEqual(result, "")

    def test_simple_dict_no_mapping(self):
        """Test simple dictionary without mapping"""
        obj = {"memory": 2048, "vcpus": 4}
        result = _dict2options(obj, None)
        # Order might vary, so check both possibilities
        self.assertIn(result, ["memory=2048,vcpus=4", "vcpus=4,memory=2048"])

    def test_simple_dict_with_mapping(self):
        """Test simple dictionary with mapping"""
        obj = {"current_memory": 512}
        mapping = {"current_memory": ("currentMemory", None)}
        result = _dict2options(obj, mapping)
        self.assertEqual(result, "currentMemory=512")

    def test_mapping_with_none_name(self):
        """Test mapping where name is None (should use original key)"""
        obj = {"test_key": "value"}
        mapping = {"test_key": (None, None)}
        result = _dict2options(obj, mapping)
        self.assertEqual(result, "test_key=value")

    def test_bool_values_default(self):
        """Test boolean values with default handling"""
        obj = {"enabled": True, "disabled": False}
        result = _dict2options(obj, None)
        self.assertIn(result,
                      ["enabled=yes,disabled=no",
                       "disabled=no,enabled=yes"])

    def test_bool_values_with_onoff_mapping(self):
        """Test boolean values with OPTION_BOOL_ONOFF mapping"""
        obj = {"enabled": True, "disabled": False}
        mapping = {
            "enabled": (None, OPTION_BOOL_ONOFF),
            "disabled": (None, OPTION_BOOL_ONOFF)
        }
        result = _dict2options(obj, mapping)
        self.assertIn(result,
                      ["enabled=on,disabled=off",
                       "disabled=off,enabled=on"])

    def test_nested_dict(self):
        """Test nested dictionary"""
        obj = {"install": {"no_install": True}}
        result = _dict2options(obj, None)
        self.assertEqual(result, "install.no_install=yes")

    def test_deeply_nested_dict_with_mapping(self):
        """Test deeply nested dict with complex mapping"""
        obj = {"suspend_to_disk": {"enabled": False}}
        mapping = {
            "suspend_to_disk": (None, {"enabled": (None, OPTION_BOOL_ONOFF)})
        }
        result = _dict2options(obj, mapping)
        self.assertEqual(result, "suspend_to_disk.enabled=off")

    def test_list_with_simple_values(self):
        """Test list with simple values"""
        obj = {"devices": ["dev1", "dev2", "dev3"]}
        result = _dict2options(obj, None)
        self.assertEqual(result, "devices0=dev1,devices1=dev2,devices2=dev3")

    def test_list_with_boolean_values(self):
        """Test list with boolean values (default handling)"""
        obj = {"flags": [True, False, True]}
        result = _dict2options(obj, None)
        self.assertEqual(result, "flags0=yes,flags1=no,flags2=yes")

    def test_list_with_boolean_values_onoff(self):
        """Test list with boolean values (OPTION_BOOL_ONOFF handling)"""
        obj = {"flags": [True, False]}
        mapping = {"flags": (None, OPTION_BOOL_ONOFF)}
        result = _dict2options(obj, mapping)
        self.assertEqual(result, "flags0=on,flags1=off")

    def test_list_with_dict_items(self):
        """Test list containing dictionary items"""
        obj = {"devices": [{"name": "dev1", "enabled": True}, {
            "name": "dev2", "enabled": False}]}
        result = _dict2options(obj, None)
        expected_parts = [
            "devices0.name=dev1",
            "devices0.enabled=yes",
            "devices1.name=dev2",
            "devices1.enabled=no"]
        for part in expected_parts:
            self.assertIn(part, result)

    def test_list_with_dict_items_and_mapping(self):
        """Test list with dict items and mapping"""
        obj = {"vcpu_specs": [{"id": 0, "enabled": True}]}
        mapping = {
            "vcpu_specs": (
                "vcpus.vcpu", {
                    "enabled": (
                        None, OPTION_BOOL_ONOFF)})}
        result = _dict2options(obj, mapping)
        self.assertIn("vcpus.vcpu0.id=0", result)
        self.assertIn("vcpus.vcpu0.enabled=on", result)

    def test_complex_nested_structure(self):
        """Test complex nested structure with multiple levels"""
        obj = {
            "cpu": {
                "model": "host-passthrough",
                "features": {
                    "vmx": {"policy": "require"},
                    "svm": {"policy": "disable"}
                }
            }
        }
        result = _dict2options(obj, None)
        expected_parts = [
            "cpu.model=host-passthrough",
            "cpu.features.vmx.policy=require",
            "cpu.features.svm.policy=disable"
        ]
        for part in expected_parts:
            self.assertIn(part, result)

    def test_mixed_types_in_dict(self):
        """Test dictionary with mixed value types"""
        obj = {
            "name": "test-vm",
            "memory": 2048,
            "enabled": True,
            "config": {"debug": False},
            "devices": ["dev1", "dev2"]
        }
        result = _dict2options(obj, None)

        expected_substrings = [
            "name=test-vm",
            "memory=2048",
            "enabled=yes",
            "config.debug=no",
            "devices0=dev1",
            "devices1=dev2"
        ]

        for substring in expected_substrings:
            self.assertIn(substring, result)

    def test_memory_options_example(self):
        """Test example from virt-install memory options"""
        obj = {
            "memory": 2048,
            "currentMemory": 1024,
            "maxMemory": 4096,
            "hugepages": True
        }
        mapping = {
            "currentMemory": ("currentMemory", None),
            "maxMemory": ("maxMemory", None),
            "hugepages": (None, OPTION_BOOL_ONOFF)
        }
        result = _dict2options(obj, mapping)

        expected_parts = [
            "memory=2048",
            "currentMemory=1024",
            "maxMemory=4096",
            "hugepages=on"
        ]

        for part in expected_parts:
            self.assertIn(part, result)

    def test_cpu_features_example(self):
        """Test CPU features with policy mapping"""
        obj = {
            "features": {
                "vmx": {"policy": "require"},
                "lahf_lm": {"policy": "disable"}
            }
        }
        result = _dict2options(obj, None)

        expected_parts = [
            "features.vmx.policy=require",
            "features.lahf_lm.policy=disable"
        ]

        for part in expected_parts:
            self.assertIn(part, result)

    def test_pm_options_example(self):
        """Test PM options from documentation example"""
        obj = {
            "suspend_to_mem": {"enabled": True},
            "suspend_to_disk": {"enabled": False}
        }
        mapping = {
            "suspend_to_mem": (None, {"enabled": (None, OPTION_BOOL_ONOFF)}),
            "suspend_to_disk": (None, {"enabled": (None, OPTION_BOOL_ONOFF)})
        }
        result = _dict2options(obj, mapping)

        expected_parts = [
            "suspend_to_mem.enabled=on",
            "suspend_to_disk.enabled=off"
        ]

        for part in expected_parts:
            self.assertIn(part, result)

    def test_get_option_mapping_helper(self):
        """Test the _get_option_mapping helper function"""
        # Test with None mapping
        name, valmap = _get_option_mapping("test", None)
        self.assertEqual(name, "test")
        self.assertIsNone(valmap)

        # Test with mapping but key not found
        mapping = {"other_key": ("other", None)}
        name, valmap = _get_option_mapping("test", mapping)
        self.assertEqual(name, "test")
        self.assertIsNone(valmap)

        # Test with mapping and key found
        mapping = {"test": ("mapped_name", "mapped_value")}
        name, valmap = _get_option_mapping("test", mapping)
        self.assertEqual(name, "mapped_name")
        self.assertEqual(valmap, "mapped_value")

        # Test with mapping where name is None
        mapping = {"test": (None, "mapped_value")}
        name, valmap = _get_option_mapping("test", mapping)
        self.assertEqual(name, "test")
        self.assertEqual(valmap, "mapped_value")

    def test_prefix_handling(self):
        """Test prefix handling in recursive calls"""
        obj = {"level1": {"level2": {"value": "test"}}}
        result = _dict2options(obj, None, prefix="root.")
        self.assertEqual(result, "root.level1.level2.value=test")

    def test_numeric_values(self):
        """Test various numeric value types"""
        obj = {
            "int_val": 42,
            "float_val": 3.14,
            "zero": 0,
            "negative": -5
        }
        result = _dict2options(obj, None)

        expected_parts = [
            "int_val=42",
            "float_val=3.14",
            "zero=0",
            "negative=-5"
        ]

        for part in expected_parts:
            self.assertIn(part, result)


class TestAddParameter(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.virt_install = VirtInstallTool(self.mock_module)

    def test_add_memory_parameter(self):
        dict_value = {
            "current_memory": 1024,
            "max_memory": 4096,
            "max_memory_opts": {
                "slots": 2
            }
        }
        mapping = {
            'current_memory': ('currentMemory', None),
            'max_memory': ('maxMemory', None),
            'max_memory_opts': ('maxMemory', None),
        }

        self.virt_install._add_parameter(
            '--memory', 2048, dict_value=dict_value, dict_mapping=mapping)
        self.assertEqual(self.virt_install.command_argv[-2], "--memory")
        memory_cmdline = self.virt_install.command_argv[-1]
        self.assertTrue(memory_cmdline.startswith("2048,"))
        self.assertIn("currentMemory=1024", memory_cmdline)
        self.assertIn("maxMemory=4096", memory_cmdline)
        self.assertIn("maxMemory.slots=2", memory_cmdline)

    def test_add_parameter_no_values(self):
        """Test adding a parameter with no values"""
        self.virt_install._add_parameter('--test')
        self.assertEqual(self.virt_install.command_argv[-1], "--test")

    def test_add_parameter_primary_only(self):
        """Test adding a parameter with only primary value"""
        self.virt_install._add_parameter('--vcpus', 4)
        self.assertEqual(self.virt_install.command_argv[-2:], ["--vcpus", "4"])

    def test_add_parameter_dict_only(self):
        """Test adding a parameter with only dict value"""
        dict_value = {
            "hugepages": True,
            "nosharepages": False
        }
        self.virt_install._add_parameter(
            '--memorybacking', dict_value=dict_value)
        self.assertEqual(self.virt_install.command_argv[-2], "--memorybacking")
        memorybacking_cmdline = self.virt_install.command_argv[-1]
        self.assertIn("hugepages=yes", memorybacking_cmdline)
        self.assertIn("nosharepages=no", memorybacking_cmdline)

    def test_add_parameter_with_bool_onoff_mapping(self):
        """Test adding a parameter with OPTION_BOOL_ONOFF mapping"""
        dict_value = {
            "enabled": True,
            "disabled": False
        }
        mapping = {
            'enabled': (None, OPTION_BOOL_ONOFF),
            'disabled': (None, OPTION_BOOL_ONOFF)
        }
        self.virt_install._add_parameter(
            '--test', dict_value=dict_value, dict_mapping=mapping)
        test_arg = self.virt_install.command_argv[-1]
        self.assertIn("enabled=on", test_arg)
        self.assertIn("disabled=off", test_arg)

    def test_add_parameter_with_nested_dict(self):
        """Test adding a parameter with nested dictionary"""
        dict_value = {
            "cpu": {
                "model": "host-passthrough",
                "features": {
                    "vmx": {"policy": "require"}
                }
            }
        }
        self.virt_install._add_parameter('--test', dict_value=dict_value)
        test_arg = self.virt_install.command_argv[-1]
        self.assertIn("cpu.model=host-passthrough", test_arg)
        self.assertIn("cpu.features.vmx.policy=require", test_arg)

    def test_add_parameter_with_list_values(self):
        """Test adding a parameter with list values"""
        dict_value = {
            "devices": ["dev1", "dev2", "dev3"]
        }
        self.virt_install._add_parameter('--test', dict_value=dict_value)
        test_arg = self.virt_install.command_argv[-1]
        self.assertIn("devices0=dev1", test_arg)
        self.assertIn("devices1=dev2", test_arg)
        self.assertIn("devices2=dev3", test_arg)

    def test_add_parameter_with_list_of_dicts(self):
        """Test adding a parameter with list of dictionaries"""
        dict_value = {
            "vcpu_specs": [
                {"id": 0, "enabled": True},
                {"id": 1, "enabled": False}
            ]
        }
        mapping = {
            "vcpu_specs": (
                "vcpus.vcpu", {
                    "enabled": (
                        None, OPTION_BOOL_ONOFF)})}
        self.virt_install._add_parameter(
            '--test', dict_value=dict_value, dict_mapping=mapping)
        test_arg = self.virt_install.command_argv[-1]
        self.assertIn("vcpus.vcpu0.id=0", test_arg)
        self.assertIn("vcpus.vcpu0.enabled=on", test_arg)
        self.assertIn("vcpus.vcpu1.id=1", test_arg)
        self.assertIn("vcpus.vcpu1.enabled=off", test_arg)

    def test_add_flag_parameter_true(self):
        """Test adding a flag parameter"""
        self.virt_install._add_flag_parameter('--test', True)
        self.assertEqual(self.virt_install.command_argv[-1], "--test")

    def test_add_flag_parameter_false(self):
        """Test adding a flag parameter"""
        self.virt_install._add_flag_parameter('--test', False)
        self.assertNotIn("--test", self.virt_install.command_argv[-1])


class TestGetParamCombinedItems(unittest.TestCase):

    def setUp(self):
        """Set up test environment"""
        self.module = mock.Mock()
        self.tool = VirtInstallTool(self.module)

    def test_both_params_none(self):
        """Test when both singular and plural parameters are None"""
        self.tool.params = {}
        result = self.tool._get_param_combined_items('input', 'input_devices')
        self.assertEqual(result, [])

    def test_only_singular_param(self):
        """Test when only singular parameter exists"""
        self.tool.params = {'input': {'type': 'keyboard'}}
        result = self.tool._get_param_combined_items('input', 'input_devices')
        self.assertEqual(result, [{'type': 'keyboard'}])

    def test_only_plural_param(self):
        """Test when only plural parameter exists"""
        self.tool.params = {
            'input_devices': [
                {'type': 'keyboard'},
                {'type': 'mouse'}
            ]
        }
        result = self.tool._get_param_combined_items('input', 'input_devices')
        self.assertEqual(result, [
            {'type': 'keyboard'},
            {'type': 'mouse'}
        ])

    def test_both_params_exist(self):
        """Test when both singular and plural parameters exist"""
        self.tool.params = {
            'input': {'type': 'keyboard'},
            'input_devices': [
                {'type': 'mouse'},
                {'type': 'tablet'}
            ]
        }
        result = self.tool._get_param_combined_items('input', 'input_devices')
        self.assertEqual(result, [
            {'type': 'keyboard'},
            {'type': 'mouse'},
            {'type': 'tablet'}
        ])

    def test_empty_plural_param(self):
        """Test when plural parameter is an empty list"""
        self.tool.params = {
            'input': {'type': 'keyboard'},
            'input_devices': []
        }
        result = self.tool._get_param_combined_items('input', 'input_devices')
        self.assertEqual(result, [{'type': 'keyboard'}])

    def test_none_values_in_params(self):
        """Test when parameters have None values"""
        self.tool.params = {
            'input': None,
            'input_devices': None
        }
        result = self.tool._get_param_combined_items('input', 'input_devices')
        self.assertEqual(result, [])

    def test_complex_nested_structures(self):
        """Test with complex nested data structures"""
        self.tool.params = {
            'controller': {
                'type': 'usb',
                'model': 'qemu-xhci'
            },
            'controller_devices': [
                {
                    'type': 'scsi',
                    'model': 'virtio-scsi',
                    'driver': {'iommu': 'on'}
                },
                {
                    'type': 'pci',
                    'model': 'pcie-root'
                }
            ]
        }
        result = self.tool._get_param_combined_items(
            'controller', 'controller_devices')
        self.assertEqual(result, [
            {
                'type': 'usb',
                'model': 'qemu-xhci'
            },
            {
                'type': 'scsi',
                'model': 'virtio-scsi',
                'driver': {'iommu': 'on'}
            },
            {
                'type': 'pci',
                'model': 'pcie-root'
            }
        ])


class TestBuildCommand(unittest.TestCase):
    """Test the _build_command method of VirtInstallTool"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.params = {}
        self.virt_install = VirtInstallTool(self.mock_module)

    def test_basic_command_structure(self):
        """Test basic command structure with minimal required parameters"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        # Check base command
        self.assertEqual(self.virt_install.command_argv[0], 'virt-install')
        # Check --noautoconsole is always added
        cmdline = ' '.join(self.virt_install.command_argv)
        self.assertIn('--noautoconsole', cmdline)
        # Check name and memory are added
        self.assertIn('--name test-vm', cmdline)
        self.assertIn('--memory 2048', cmdline)

    def test_memory_with_options(self):
        """Test memory parameter with additional options"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 4096,
            'memory_opts': {
                'current_memory': 2048,
                'max_memory': 8192,
                'max_memory_opts': {
                    'slots': 4
                }
            }
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        memory_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--memory' and i + \
                    1 < len(self.virt_install.command_argv):
                memory_args.append(self.virt_install.command_argv[i + 1])

        self.assertEqual(len(memory_args), 1)
        self.assertIn('4096', memory_args[0])
        self.assertIn('currentMemory=2048', memory_args[0])
        self.assertIn('maxMemory=8192', memory_args[0])
        self.assertIn('maxMemory.slots=4', memory_args[0])

    def test_memorybacking_options(self):
        """Test memorybacking parameter"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'memorybacking': {
                'hugepages': True,
                'nosharepages': False,
                'locked': True,
                'hugepage_specs': [
                    {'page_size': 2048, 'nodeset': '0-1'},
                    {'page_size': 1048576, 'nodeset': '2-3'}
                ]
            }
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        try:
            idx = self.virt_install.command_argv.index('--memorybacking')
            memorybacking_cmdline = self.virt_install.command_argv[idx + 1]
        except (ValueError, IndexError):
            memorybacking_cmdline = None

        self.assertIsNotNone(memorybacking_cmdline)
        self.assertIn('hugepages=yes', memorybacking_cmdline)
        self.assertIn('nosharepages=no', memorybacking_cmdline)
        self.assertIn('locked=yes', memorybacking_cmdline)
        self.assertIn('hugepages.page0.size=2048', memorybacking_cmdline)
        self.assertIn('hugepages.page0.nodeset=0-1', memorybacking_cmdline)

    def test_vcpus_configuration(self):
        """Test vcpus parameter with options"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'vcpus': 4,
            'vcpus_opts': {
                'maxvcpus': 8,
                'sockets': 2,
                'cores': 2,
                'threads': 1,
                'current': 2,
                'cpuset': '0-3',
                'placement': 'static'
            }
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        try:
            idx = self.virt_install.command_argv.index('--vcpus')
            vcpus_cmdline = self.virt_install.command_argv[idx + 1]
        except (ValueError, IndexError):
            vcpus_cmdline = None

        self.assertIsNotNone(vcpus_cmdline)
        self.assertTrue(vcpus_cmdline.startswith('4'))
        self.assertIn('maxvcpus=8', vcpus_cmdline)
        self.assertIn('sockets=2', vcpus_cmdline)
        self.assertIn('cores=2', vcpus_cmdline)
        self.assertIn('threads=1', vcpus_cmdline)
        self.assertIn('vcpu.current=2', vcpus_cmdline)
        self.assertIn('cpuset=0-3', vcpus_cmdline)
        self.assertIn('vcpu.placement=static', vcpus_cmdline)

    def test_cpu_configuration(self):
        """Test CPU configuration with complex options"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'cpu': {
                'model': 'host-passthrough',
                'match': 'exact',
                'migratable': True,
                'features': {
                    'vmx': 'require',
                    'svm': 'disable',
                    'lahf_lm': 'optional'
                },
                'cache': {
                    'mode': 'passthrough',
                    'level': 3
                }
            }
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        try:
            idx = self.virt_install.command_argv.index('--cpu')
            cpu_cmdline = self.virt_install.command_argv[idx + 1]
        except (ValueError, IndexError):
            cpu_cmdline = None

        self.assertIsNotNone(cpu_cmdline)
        # Features should be processed as primary value
        self.assertTrue(cpu_cmdline.startswith('host-passthrough'))
        self.assertIn('require=vmx', cpu_cmdline)
        self.assertIn('disable=svm', cpu_cmdline)
        self.assertIn('optional=lahf_lm', cpu_cmdline)
        # Other options should be in dict format
        self.assertIn('match=exact', cpu_cmdline)
        self.assertIn('migratable=yes', cpu_cmdline)
        self.assertIn('cache.mode=passthrough', cpu_cmdline)
        self.assertIn('cache.level=3', cpu_cmdline)

    def test_storage_configuration(self):
        """Test disk storage configuration"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'disks': [
                {
                    'size': 20,
                    'format': 'qcow2',
                    'bus': 'virtio',
                    'cache': 'writeback',
                    'sparse': True
                },
                {
                    'path': '/var/lib/libvirt/images/test-vm-data.qcow2',
                    'size': 100,
                    'format': 'qcow2',
                    'bus': 'virtio',
                    'readonly': False,
                    'shareable': True
                }
            ]
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        disk_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--disk' and i + 1 < len(self.virt_install.command_argv):
                disk_args.append(self.virt_install.command_argv[i + 1])

        self.assertEqual(len(disk_args), 2)
        # Check first disk
        self.assertIn('size=20', disk_args[0])
        self.assertIn('format=qcow2', disk_args[0])
        self.assertIn('bus=virtio', disk_args[0])
        self.assertIn('cache=writeback', disk_args[0])
        self.assertIn('sparse=yes', disk_args[0])

        # Check second disk
        self.assertIn(
            'path=/var/lib/libvirt/images/test-vm-data.qcow2',
            disk_args[1])
        self.assertIn('size=100', disk_args[1])
        self.assertIn('readonly=no', disk_args[1])
        self.assertIn('shareable=yes', disk_args[1])

    def test_network_configuration(self):
        """Test network configuration"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'networks': [
                {
                    'network': 'default',
                    'model': {'type': 'virtio'},
                    'mac': {'address': '52:54:00:12:34:56'}
                },
                {
                    'bridge': 'br0',
                    'model': {'type': 'e1000'},
                    'trust_guest_rx_filters': True
                }
            ]
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        # Find network arguments
        network_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--network' and i + \
                    1 < len(self.virt_install.command_argv):
                network_args.append(self.virt_install.command_argv[i + 1])

        self.assertEqual(len(network_args), 2)

        # Check first network
        self.assertIn('network=default', network_args[0])
        self.assertIn('model.type=virtio', network_args[0])
        self.assertIn('mac.address=52:54:00:12:34:56', network_args[0])

        # Check second network
        self.assertIn('bridge=br0', network_args[1])
        self.assertIn('model.type=e1000', network_args[1])
        self.assertIn('trustGuestRxFilters=yes', network_args[1])

    def test_empty_networks_list(self):
        """Test empty networks list results in no network"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'networks': []
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        # Find network arguments
        network_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--network' and i + \
                    1 < len(self.virt_install.command_argv):
                network_args.append(self.virt_install.command_argv[i + 1])

        self.assertEqual(len(network_args), 1)
        self.assertEqual(network_args[0], 'none')

    def test_graphics_configuration(self):
        """Test graphics configuration"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'graphics': {
                'type': 'vnc',
                'listen': '0.0.0.0',
                'port': 5901,
                'password': 'secret'
            }
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        graphics_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--graphics' and i + \
                    1 < len(self.virt_install.command_argv):
                graphics_args.append(self.virt_install.command_argv[i + 1])

        self.assertEqual(len(graphics_args), 1)
        self.assertTrue(graphics_args[0].startswith('vnc,'))
        self.assertIn('listen=0.0.0.0', graphics_args[0])
        self.assertIn('port=5901', graphics_args[0])
        self.assertIn('password=secret', graphics_args[0])

    def test_graphics_devices_list(self):
        """Test multiple graphics devices"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'graphics_devices': [
                {'type': 'vnc', 'port': 5901},
                {'type': 'spice', 'port': 5902}
            ]
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        graphics_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--graphics' and i + \
                    1 < len(self.virt_install.command_argv):
                graphics_args.append(self.virt_install.command_argv[i + 1])

        self.assertEqual(len(graphics_args), 2)
        self.assertTrue(graphics_args[0].startswith('vnc,'))
        self.assertIn('port=5901', graphics_args[0])
        self.assertTrue(graphics_args[1].startswith('spice,'))
        self.assertIn('port=5902', graphics_args[1])

    def test_no_graphics_configuration(self):
        """Test no graphics configuration results in none"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        # Find graphics arguments
        graphics_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--graphics' and i + \
                    1 < len(self.virt_install.command_argv):
                graphics_args.append(self.virt_install.command_argv[i + 1])

        self.assertEqual(len(graphics_args), 1)
        self.assertEqual(graphics_args[0], 'none')

    def test_installation_options(self):
        """Test installation options"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'location': 'http://mirror.centos.org/centos-7/7/os/x86_64/',
            'location_opts': {
                'kernel': 'images/pxeboot/vmlinuz',
                'initrd': 'images/pxeboot/initrd.img'
            },
            'extra_args': 'console=ttyS0,115200n8 serial',
            'osinfo': {
                'name': 'centos7.0',
                'detect': True,
                'require': False
            }
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        location_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--location' and i + \
                    1 < len(self.virt_install.command_argv):
                location_args.append(self.virt_install.command_argv[i + 1])
        self.assertEqual(len(location_args), 1)
        self.assertIn(
            'http://mirror.centos.org/centos-7/7/os/x86_64/',
            location_args[0])
        self.assertIn('kernel=images/pxeboot/vmlinuz', location_args[0])
        self.assertIn('initrd=images/pxeboot/initrd.img', location_args[0])

        extra_args_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--extra-args' and i + \
                    1 < len(self.virt_install.command_argv):
                extra_args_args.append(self.virt_install.command_argv[i + 1])
        self.assertEqual(len(extra_args_args), 1)
        self.assertEqual('console=ttyS0,115200n8 serial', extra_args_args[0])

        osinfo_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--osinfo' and i + \
                    1 < len(self.virt_install.command_argv):
                osinfo_args.append(self.virt_install.command_argv[i + 1])
        self.assertEqual(len(osinfo_args), 1)
        self.assertIn('name=centos7.0', osinfo_args[0])
        self.assertIn('detect=on', osinfo_args[0])
        self.assertIn('require=off', osinfo_args[0])

    def test_flag_parameters(self):
        """Test flag parameters (pxe, import, etc.)"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'pxe': True,
            'autostart': True,
            'transient': False,
            'noreboot': True
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        # Check that true flags are present
        self.assertIn('--pxe', self.virt_install.command_argv)
        self.assertIn('--autostart', self.virt_install.command_argv)
        self.assertIn('--noreboot', self.virt_install.command_argv)

        # Check that false flags are not present
        self.assertNotIn('--transient', self.virt_install.command_argv)

    def test_import_flag(self):
        """Test the import flag (Python keyword)"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'import': True
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        self.assertIn('--import', self.virt_install.command_argv)

    def test_device_configurations(self):
        """Test various device configurations"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'controller_devices': [
                {'type': 'usb', 'model': 'none'},
                {'type': 'scsi', 'model': 'virtio-scsi'}
            ],
            'input_devices': [
                {'type': 'tablet', 'bus': 'usb'},
                {'type': 'keyboard', 'bus': 'usb'}
            ],
            'sound_devices': [
                {'model': 'ich9'}
            ],
            'video_devices': [
                {'model': 'qxl', 'vram': 65536}
            ]
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        # Check controller devices
        controller_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--controller' and i + \
                    1 < len(self.virt_install.command_argv):
                controller_args.append(self.virt_install.command_argv[i + 1])
        self.assertEqual(len(controller_args), 2)
        self.assertIn('type=usb', controller_args[0])
        self.assertIn('model=none', controller_args[0])
        self.assertIn('type=scsi', controller_args[1])
        self.assertIn('model=virtio-scsi', controller_args[1])

        # Check input devices
        input_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--input' and i + \
                    1 < len(self.virt_install.command_argv):
                input_args.append(self.virt_install.command_argv[i + 1])
        self.assertEqual(len(input_args), 2)

        # Check sound devices
        sound_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--sound' and i + \
                    1 < len(self.virt_install.command_argv):
                sound_args.append(self.virt_install.command_argv[i + 1])
        self.assertEqual(len(sound_args), 1)
        self.assertIn('model=ich9', sound_args[0])

        # Check video devices
        video_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--video' and i + \
                    1 < len(self.virt_install.command_argv):
                video_args.append(self.virt_install.command_argv[i + 1])
        self.assertEqual(len(video_args), 1)
        self.assertIn('model=qxl', video_args[0])
        self.assertIn('vram=65536', video_args[0])

    def test_combined_singular_plural_devices(self):
        """Test combining singular and plural device parameters"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'controller': {'type': 'usb', 'model': 'qemu-xhci'},
            'controller_devices': [
                {'type': 'scsi', 'model': 'virtio-scsi'},
                {'type': 'pci', 'model': 'pcie-root'}
            ]
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        # Should have 3 controller arguments (1 singular + 2 plural)

        controller_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--controller' and i + \
                    1 < len(self.virt_install.command_argv):
                controller_args.append(self.virt_install.command_argv[i + 1])

        self.assertEqual(len(controller_args), 3)
        # Check that singular is included first
        self.assertIn('type=usb', controller_args[0])
        self.assertIn('model=qemu-xhci', controller_args[0])
        self.assertIn('type=scsi', controller_args[1])
        self.assertIn('model=virtio-scsi', controller_args[1])
        self.assertIn('type=pci', controller_args[2])
        self.assertIn('model=pcie-root', controller_args[2])

    def test_cloud_init_configuration(self):
        """Test cloud-init configuration"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'cloud_init': {
                'root_password_generate': True,
                'disable': False,
                'root_ssh_key': '/path/to/key.pub',
                'clouduser_ssh_key': '/path/to/user_key.pub',
                'meta_data': {'instance-id': 'test-vm'},
                'user_data': {
                    'users': [{'name': 'testuser', 'sudo': 'ALL=(ALL) NOPASSWD:ALL'}]
                }
            }
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        cloud_init_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--cloud-init' and i + \
                    1 < len(self.virt_install.command_argv):
                cloud_init_args.append(self.virt_install.command_argv[i + 1])

        self.assertEqual(len(cloud_init_args), 1)
        self.assertIn('root-password-generate=on', cloud_init_args[0])
        self.assertIn('disable=off', cloud_init_args[0])
        self.assertIn('root-ssh-key=/path/to/key.pub', cloud_init_args[0])
        self.assertIn(
            'clouduser-ssh-key=/path/to/user_key.pub',
            cloud_init_args[0])

    def test_launch_security_configuration(self):
        """Test launch security (SEV) configuration"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'launch_security': {
                'type': 'sev',
                'policy': '0x01',
                'cbitpos': 47,
                'reduced_phys_bits': 1
            }
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        launch_security_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--launchSecurity' and i + \
                    1 < len(self.virt_install.command_argv):
                launch_security_args.append(
                    self.virt_install.command_argv[i + 1])

        self.assertEqual(len(launch_security_args), 1)
        self.assertIn('type=sev', launch_security_args[0])
        self.assertIn('policy=0x01', launch_security_args[0])
        self.assertIn('cbitpos=47', launch_security_args[0])
        self.assertIn('reducedPhysBits=1', launch_security_args[0])

    def test_validate_params_error(self):
        """Test parameter validation errors"""
        # Test case where memory_opts is provided without memory
        self.mock_module.params = {
            'name': 'test-vm',
            'memory_opts': {'current_memory': 1024}
        }
        self.mock_module.fail_json = mock.Mock()
        self.virt_install = VirtInstallTool(self.mock_module)

        self.virt_install._build_command()

        # Should call fail_json with validation error
        self.mock_module.fail_json.assert_called_once()
        args, kwargs = self.mock_module.fail_json.call_args
        self.assertIn('memory_opts requires memory', kwargs['msg'])

    def test_complete_vm_configuration(self):
        """Test a complete VM configuration with many options"""
        self.mock_module.params = {
            'name': 'production-vm',
            'memory': 8192,
            'memory_opts': {
                'current_memory': 4096,
                'max_memory': 16384
            },
            'vcpus': 4,
            'vcpus_opts': {
                'maxvcpus': 8,
                'sockets': 2,
                'cores': 2
            },
            'cpu': {
                'model': 'host-passthrough',
                'features': {
                    'vmx': 'require'
                }
            },
            'disks': [
                {
                    'size': 40,
                    'format': 'qcow2',
                    'bus': 'virtio',
                    'cache': 'writeback'
                }
            ],
            'networks': [
                {
                    'network': 'default',
                    'model': {'type': 'virtio'}
                }
            ],
            'graphics': {
                'type': 'spice',
                'listen': '127.0.0.1'
            },
            'osinfo': {
                'name': 'fedora39'
            },
            'location': (
                'https://download.fedoraproject.org/pub/fedora/linux/'
                'releases/39/Server/x86_64/'),
            'autostart': True,
            'noreboot': True
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        # Verify the command structure
        self.assertEqual(self.virt_install.command_argv[0], 'virt-install')
        self.assertIn('--noautoconsole', self.virt_install.command_argv)

        # Verify major components are present
        arg_prefixes = [
            '--name',
            '--memory',
            '--vcpus',
            '--cpu',
            '--disk',
            '--network',
            '--graphics',
            '--osinfo',
            '--location',
            '--autostart',
            '--noreboot']
        for prefix in arg_prefixes:
            found = any(arg.startswith(prefix)
                        for arg in self.virt_install.command_argv)
            self.assertTrue(
                found, f"Expected argument with prefix '{prefix}' not found in command")

    def test_additional_validation_errors(self):
        """Test additional parameter validation errors"""
        # Test case where vcpus_opts is provided without vcpus
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'vcpus_opts': {'maxvcpus': 8}
        }
        self.mock_module.fail_json = mock.Mock()
        self.virt_install = VirtInstallTool(self.mock_module)

        self.virt_install._build_command()

        # Should call fail_json with validation error
        self.mock_module.fail_json.assert_called_once()
        args, kwargs = self.mock_module.fail_json.call_args
        self.assertIn('vcpus_opts requires vcpus', kwargs['msg'])

    def test_filesystem_configuration(self):
        """Test filesystem configuration"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'filesystems': [
                {
                    'type': 'mount',
                    'accessmode': 'passthrough',
                    'source': {'dir': '/host/share'},
                    'target': {'dir': '/guest/share'},
                    'readonly': False
                },
                {
                    'type': 'mount',
                    'accessmode': 'mapped',
                    'source': {'dir': '/host/data'},
                    'target': {'dir': '/guest/data'},
                    'fmode': '0644',
                    'dmode': '0755'
                }
            ]
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        # Find filesystem arguments
        fs_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--filesystem' and i + \
                    1 < len(self.virt_install.command_argv):
                fs_args.append(self.virt_install.command_argv[i + 1])

        self.assertEqual(len(fs_args), 2)

        # Check first filesystem
        self.assertIn('type=mount', fs_args[0])
        self.assertIn('accessmode=passthrough', fs_args[0])
        self.assertIn('source.dir=/host/share', fs_args[0])
        self.assertIn('target.dir=/guest/share', fs_args[0])
        self.assertIn('readonly=no', fs_args[0])

        # Check second filesystem
        self.assertIn('type=mount', fs_args[1])
        self.assertIn('accessmode=mapped', fs_args[1])
        self.assertIn('fmode=0644', fs_args[1])
        self.assertIn('dmode=0755', fs_args[1])

    def test_complex_boolean_mappings(self):
        """Test complex boolean mappings with OPTION_BOOL_ONOFF"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'memballoon_devices': [
                {
                    'model': 'virtio',
                    'freePageReporting': True,
                    'autodeflate': False
                }
            ],
            'tpm_devices': [
                {
                    'model': 'tpm-tis',
                    'backend': {
                        'type': 'emulator',
                        'version': '2.0',
                        'persistent_state': True
                    },
                    'active_pcr_banks': {
                        'sha1': True,
                        'sha256': False
                    }
                }
            ]
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        # Find memballoon arguments
        memballoon_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--memballoon' and i + \
                    1 < len(self.virt_install.command_argv):
                memballoon_args.append(self.virt_install.command_argv[i + 1])
        self.assertEqual(len(memballoon_args), 1)
        self.assertIn('freePageReporting=on', memballoon_args[0])
        self.assertIn('autodeflate=off', memballoon_args[0])

        # Find TPM arguments
        tpm_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--tpm' and i + 1 < len(self.virt_install.command_argv):
                tpm_args.append(self.virt_install.command_argv[i + 1])
        self.assertEqual(len(tpm_args), 1)
        self.assertIn('backend.persistent_state=on', tpm_args[0])
        self.assertIn('active_pcr_banks.sha1=on', tpm_args[0])
        self.assertIn('active_pcr_banks.sha256=off', tpm_args[0])

    def test_installation_medium_combinations(self):
        """Test different installation medium combinations"""
        # Test CDROM installation
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'cdrom': '/path/to/installer.iso'
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        cmdline = ' '.join(self.virt_install.command_argv)
        self.assertIn(
            '--cdrom /path/to/installer.iso',
            cmdline)

    def test_unattended_installation(self):
        """Test unattended installation configuration"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'unattended': {
                'profile': 'desktop',
                'admin_password_file': '/tmp/admin_pass',
                'user_login': 'testuser',
                'user_password_file': '/tmp/user_pass',
                'product_key': 'XXXXX-XXXXX-XXXXX-XXXXX-XXXXX'
            }
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        # Find unattended argument
        unattended_arg = None
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--unattended' and i + \
                    1 < len(self.virt_install.command_argv):
                unattended_arg = self.virt_install.command_argv[i + 1]
                break

        self.assertIsNotNone(unattended_arg)
        self.assertIn('profile=desktop', unattended_arg)
        self.assertIn('admin-password-file=/tmp/admin_pass', unattended_arg)
        self.assertIn('user-login=testuser', unattended_arg)
        self.assertIn('user-password-file=/tmp/user_pass', unattended_arg)
        self.assertIn(
            'product-key=XXXXX-XXXXX-XXXXX-XXXXX-XXXXX',
            unattended_arg)

    def test_virtualization_options(self):
        """Test virtualization-specific options"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'virt_type': 'kvm',
            'hvm': True,
            'paravirt': False,
            'container': False,
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        self.assertIn('--hvm', self.virt_install.command_argv)
        self.assertNotIn('--paravirt', self.virt_install.command_argv)
        self.assertNotIn('--container', self.virt_install.command_argv)

    def test_complex_numa_configuration(self):
        """Test complex NUMA configuration"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'numatune': {
                'memory': {
                    'mode': 'strict',
                    'nodeset': '0-1',
                    'placement': 'static'
                },
                'memnode_specs': [
                    {
                        'cellid': 0,
                        'mode': 'strict',
                        'nodeset': '0'
                    },
                    {
                        'cellid': 1,
                        'mode': 'interleave',
                        'nodeset': '1'
                    }
                ]
            }
        }
        self.virt_install = VirtInstallTool(self.mock_module)
        self.virt_install._build_command()

        numatune_args = []
        for i, arg in enumerate(self.virt_install.command_argv):
            if arg == '--numatune' and i + \
                    1 < len(self.virt_install.command_argv):
                numatune_args.append(self.virt_install.command_argv[i + 1])

        self.assertEqual(len(numatune_args), 1)
        self.assertIn('memory.mode=strict', numatune_args[0])
        self.assertIn('memory.nodeset=0-1', numatune_args[0])
        self.assertIn('memory.placement=static', numatune_args[0])
        self.assertIn('memnode0.cellid=0', numatune_args[0])
        self.assertIn('memnode0.mode=strict', numatune_args[0])
        self.assertIn('memnode1.cellid=1', numatune_args[0])
        self.assertIn('memnode1.mode=interleave', numatune_args[0])

    def test_empty_command_argv_initialization(self):
        """Test that command_argv is properly initialized"""
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048
        }
        self.virt_install = VirtInstallTool(self.mock_module)

        # Before _build_command, should only have base command
        self.assertEqual(len(self.virt_install.command_argv), 1)
        self.assertEqual(self.virt_install.command_argv[0], 'virt-install')

        self.virt_install._build_command()

        # After _build_command, should have more arguments
        self.assertGreater(len(self.virt_install.command_argv), 1)
        self.assertEqual('--noautoconsole', self.virt_install.command_argv[-1])


class TestVirtInstallToolExecute(unittest.TestCase):
    """Test cases for VirtInstallTool.execute() method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.params = {
            'name': 'test-vm',
            'memory': 2048,
            'vcpus': 2,
            'disks': [{'size': 20}],
            'networks': [{'network': 'default'}],
            'osinfo': {'name': 'fedora39'},
            'graphics': {'type': 'spice'}
        }
        self.virt_install = VirtInstallTool(self.mock_module)

    def test_execute_success(self):
        """Test successful execution"""
        # Mock successful command execution
        self.mock_module.run_command.return_value = (
            0, "Domain installation proceeding...", "")

        changed, rc, result = self.virt_install.execute()

        # Assert successful execution
        self.assertTrue(changed)
        self.assertEqual(rc, 0)  # VIRT_SUCCESS
        self.assertIn("msg", result)
        self.assertIn(
            "virtual machine 'test-vm' created successfully",
            result["msg"])

        # Verify run_command was called
        self.mock_module.run_command.assert_called_once()

        # Verify command contains expected elements
        called_args = self.mock_module.run_command.call_args[0][0]
        self.assertIn('virt-install', called_args)
        self.assertIn('--noautoconsole', called_args)

    def test_execute_failure(self):
        """Test failed execution"""
        error_message = "ERROR: Unable to connect to libvirt"
        self.mock_module.run_command.return_value = (1, "", error_message)

        changed, rc, result = self.virt_install.execute()

        # Assert failed execution
        self.assertFalse(changed)
        self.assertEqual(rc, 1)
        self.assertIn("msg", result)
        self.assertIn(
            "failed to create virtual machine 'test-vm'",
            result["msg"])
        self.assertIn(error_message, result["msg"])

    def test_execute_failure_with_stdout_error(self):
        """Test failed execution where error info is in stdout"""
        error_message = "ERROR: Domain already exists"
        self.mock_module.run_command.return_value = (2, error_message, "")

        changed, rc, result = self.virt_install.execute()

        # Assert failed execution
        self.assertFalse(changed)
        self.assertEqual(rc, 2)
        self.assertIn("msg", result)
        self.assertIn(
            "failed to create virtual machine 'test-vm'",
            result["msg"])
        self.assertIn(error_message, result["msg"])

    def test_execute_dryrun_success(self):
        """Test dry run execution"""
        self.mock_module.run_command.return_value = (
            0, "Would create domain test-vm", "")

        changed, rc, result = self.virt_install.execute(dryrun=True)

        # Assert successful dry run
        self.assertTrue(changed)
        self.assertEqual(rc, 0)
        self.assertIn("msg", result)
        self.assertIn(
            "virtual machine 'test-vm' created successfully",
            result["msg"])

        # Verify --dry-run was added to command
        called_args = self.mock_module.run_command.call_args[0][0]
        self.assertIn('--dry-run', called_args)

    def test_execute_dryrun_failure(self):
        """Test dry run execution with failure"""
        error_message = "ERROR: Missing required option --cdrom"
        self.mock_module.run_command.return_value = (3, "", error_message)

        changed, rc, result = self.virt_install.execute(dryrun=True)

        # Assert failed dry run
        self.assertFalse(changed)
        self.assertEqual(rc, 3)
        self.assertIn("msg", result)
        self.assertIn(
            "failed to create virtual machine 'test-vm'",
            result["msg"])
        self.assertIn(error_message, result["msg"])

    def test_execute_with_complex_configuration(self):
        """Test execution with complex VM configuration"""
        # Set up complex configuration
        self.mock_module.params.update({
            'memory_opts': {
                'current_memory': 1024,
                'max_memory': 4096
            },
            'vcpus_opts': {
                'maxvcpus': 8,
                'sockets': 2,
                'cores': 2,
                'threads': 2
            },
            'cpu': {
                'model': 'host-passthrough',
                'features': {
                    'vmx': 'require',
                }
            },
            'clock': {
                'offset': 'utc',
                'timers': [
                    {'name': 'rtc', 'tickpolicy': 'catchup'}
                ]
            }
        })

        self.mock_module.run_command.return_value = (
            0, "Installation starting...", "")

        changed, rc, result = self.virt_install.execute()

        # Assert successful execution
        self.assertTrue(changed)
        self.assertEqual(rc, 0)

        # Verify complex options were included in command
        called_args = self.mock_module.run_command.call_args[0][0]
        self.assertIn('virt-install', called_args)

        # Validate memory configuration with memory_opts
        memory_args = []
        for i, arg in enumerate(called_args):
            if arg == '--memory' and i + 1 < len(called_args):
                memory_args.append(called_args[i + 1])
        self.assertEqual(len(memory_args), 1)
        memory_arg = memory_args[0]
        self.assertIn('2048,', memory_arg)  # Base memory value
        self.assertIn('currentMemory=1024', memory_arg)
        self.assertIn('maxMemory=4096', memory_arg)

        # Validate vCPU configuration with vcpus_opts
        vcpus_args = []
        for i, arg in enumerate(called_args):
            if arg == '--vcpus' and i + 1 < len(called_args):
                vcpus_args.append(called_args[i + 1])
        self.assertEqual(len(vcpus_args), 1)
        vcpus_arg = vcpus_args[0]
        self.assertIn('2,', vcpus_arg)  # Base vcpus value
        self.assertIn('maxvcpus=8', vcpus_arg)
        self.assertIn('sockets=2', vcpus_arg)
        self.assertIn('cores=2', vcpus_arg)
        self.assertIn('threads=2', vcpus_arg)

        # Validate CPU configuration with model and features
        cpu_args = []
        for i, arg in enumerate(called_args):
            if arg == '--cpu' and i + 1 < len(called_args):
                cpu_args.append(called_args[i + 1])
        self.assertEqual(len(cpu_args), 1)
        cpu_arg = cpu_args[0]
        # Features should be converted to primary value format
        self.assertIn('require=vmx', cpu_arg)
        # Model should be in dict format
        self.assertIn('host-passthrough', cpu_arg)

        # Validate clock configuration
        clock_args = []
        for i, arg in enumerate(called_args):
            if arg == '--clock' and i + 1 < len(called_args):
                clock_args.append(called_args[i + 1])
        self.assertEqual(len(clock_args), 1)
        clock_arg = clock_args[0]
        self.assertIn('offset=utc', clock_arg)
        self.assertIn('timer0.name=rtc', clock_arg)
        self.assertIn('timer0.tickpolicy=catchup', clock_arg)

        # Validate basic VM parameters are still present
        name_args = []
        for i, arg in enumerate(called_args):
            if arg == '--name' and i + 1 < len(called_args):
                name_args.append(called_args[i + 1])
        self.assertEqual(len(name_args), 1)
        self.assertIn('test-vm', name_args[0])

        # Validate disk configuration from base params
        disk_args = []
        for i, arg in enumerate(called_args):
            if arg == '--disk' and i + 1 < len(called_args):
                disk_args.append(called_args[i + 1])
        self.assertEqual(len(disk_args), 1)
        self.assertIn('size=20', disk_args[0])

        # Validate network configuration from base params
        network_args = []
        for i, arg in enumerate(called_args):
            if arg == '--network' and i + 1 < len(called_args):
                network_args.append(called_args[i + 1])
        self.assertEqual(len(network_args), 1)
        self.assertIn('network=default', network_args[0])

        # Validate OS info configuration from base params
        osinfo_args = []
        for i, arg in enumerate(called_args):
            if arg == '--osinfo' and i + 1 < len(called_args):
                osinfo_args.append(called_args[i + 1])
        self.assertEqual(len(osinfo_args), 1)
        self.assertIn('name=fedora39', osinfo_args[0])

        # Validate graphics configuration from base params
        graphics_args = []
        for i, arg in enumerate(called_args):
            if arg == '--graphics' and i + 1 < len(called_args):
                graphics_args.append(called_args[i + 1])
        self.assertEqual(len(graphics_args), 1)
        self.assertEqual('spice', graphics_args[0])

        # Verify --noautoconsole is always present
        self.assertIn('--noautoconsole', called_args)

    def test_execute_command_building_error(self):
        """Test execution when command building encounters validation error"""
        # Set up invalid configuration that should trigger validation error
        self.mock_module.params['memory_opts'] = {'current_memory': 1024}
        # Remove required 'memory' parameter to trigger validation error
        del self.mock_module.params['memory']

        # Should raise an exception during _validate_params
        with self.assertRaises(Exception):
            self.virt_install.execute()

    def test_execute_preserves_command_structure(self):
        """Test that execute() preserves the command structure"""
        self.mock_module.run_command.return_value = (0, "Success", "")

        # Store original command_argv
        original_argv = self.virt_install.command_argv[:]

        self.virt_install.execute()

        # Verify command was built (should be different from original)
        self.assertNotEqual(original_argv, self.virt_install.command_argv)

        # Verify basic structure
        self.assertEqual('virt-install', self.virt_install.command_argv[0])
        self.assertEqual('--noautoconsole', self.virt_install.command_argv[-1])

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_install.VirtInstallTool._build_command')
    def test_execute_calls_build_command(self, mock_build_command):
        """Test that execute() calls _build_command()"""
        self.mock_module.run_command.return_value = (0, "Success", "")

        self.virt_install.execute()

        # Verify _build_command was called
        mock_build_command.assert_called_once()

    def test_execute_different_return_codes(self):
        """Test execution with various return codes"""
        test_cases = [
            (0, "Success", "", True, 0),   # Success case
            (1, "", "Generic error", False, 1),  # Generic failure
            (2, "Validation error", "", False, 2),  # Validation failure
            (255, "", "Command not found", False, 255),  # Command not found
        ]

        for rc_input, stdout, stderr, expected_changed, expected_rc in test_cases:
            with self.subTest(rc=rc_input):
                self.mock_module.run_command.return_value = (
                    rc_input, stdout, stderr)

                changed, rc, result = self.virt_install.execute()

                self.assertEqual(changed, expected_changed)
                self.assertEqual(rc, expected_rc)
                self.assertIn("msg", result)

    def test_execute_empty_stderr_stdout(self):
        """Test execution when both stderr and stdout are empty"""
        self.mock_module.run_command.return_value = (1, "", "")

        changed, rc, result = self.virt_install.execute()

        # Assert failed execution
        self.assertFalse(changed)
        self.assertEqual(rc, 1)
        self.assertIn("msg", result)
        self.assertIn(
            "failed to create virtual machine 'test-vm'",
            result["msg"])

    def test_execute_with_whitespace_in_output(self):
        """Test execution with whitespace in output"""
        self.mock_module.run_command.return_value = (
            1, "  \n  ", "  Error with spaces  \n")

        changed, rc, result = self.virt_install.execute()

        # Assert error message is properly stripped
        self.assertFalse(changed)
        self.assertEqual(rc, 1)
        self.assertIn("Error with spaces", result["msg"])
        self.assertNotIn("\n", result["msg"])

    def test_execute_command_check_rc_false(self):
        """Test that execute() calls run_command with check_rc=False"""
        self.mock_module.run_command.return_value = (0, "Success", "")

        self.virt_install.execute()

        # Verify run_command was called with check_rc=False
        call_args, call_kwargs = self.mock_module.run_command.call_args
        self.assertEqual(call_kwargs.get('check_rc'), False)

    def test_execute_vm_name_in_messages(self):
        """Test that VM name is correctly included in success/failure messages"""
        # Test with different VM names
        test_names = ['test-vm', 'my_vm_123', 'vm-with-dashes', 'CamelCaseVM']

        for vm_name in test_names:
            with self.subTest(name=vm_name):
                self.virt_install._vm_name = vm_name

                # Test success case
                self.mock_module.run_command.return_value = (0, "Success", "")
                changed, rc, result = self.virt_install.execute()
                self.assertIn(vm_name, result["msg"])

                # Test failure case
                self.mock_module.run_command.return_value = (1, "", "Error")
                changed, rc, result = self.virt_install.execute()
                self.assertIn(vm_name, result["msg"])

    def test_execute_result_structure(self):
        """Test that execute() returns properly structured results"""
        self.mock_module.run_command.return_value = (0, "Success", "")

        changed, rc, result = self.virt_install.execute()

        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn("msg", result)
        self.assertIsInstance(result["msg"], str)
        self.assertTrue(len(result["msg"]) > 0)

        # Verify return types
        self.assertIsInstance(changed, bool)
        self.assertIsInstance(rc, int)


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
    unittest.main()
