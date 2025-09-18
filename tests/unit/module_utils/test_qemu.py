# -*- coding: utf-8 -*-
#
# (c) 2025, Joey Zhang <thinkdoggie@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import unittest
import json

from ansible_collections.community.libvirt.tests.unit.compat import mock
from ansible_collections.community.libvirt.plugins.module_utils.qemu import QemuImgTool


class TestQemuImgToolInit(unittest.TestCase):
    """Test QemuImgTool initialization"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.check_mode = False

    def test_init_default_command(self):
        """Test initialization with default qemu-img command"""
        tool = QemuImgTool(self.mock_module)

        self.assertEqual(tool.module, self.mock_module)
        self.assertEqual(tool.warnings, [])
        self.assertEqual(tool.command_argv, ['qemu-img'])

    def test_init_custom_command(self):
        """Test initialization with custom command"""
        custom_cmd = '/usr/local/bin/qemu-img'
        tool = QemuImgTool(self.mock_module, qemu_img_path=custom_cmd)

        self.assertEqual(tool.module, self.mock_module)
        self.assertEqual(tool.warnings, [])
        self.assertEqual(tool.command_argv, [custom_cmd])

    def test_init_none_command(self):
        """Test initialization with None command (should use default)"""
        tool = QemuImgTool(self.mock_module, qemu_img_path=None)

        self.assertEqual(tool.command_argv, ['qemu-img'])


class TestQemuImgToolHelperMethods(unittest.TestCase):
    """Test QemuImgTool helper methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.check_mode = False
        self.tool = QemuImgTool(self.mock_module)

    def test_add_flag(self):
        """Test adding a flag to command line"""
        self.tool._add_flag('--verbose')
        self.assertEqual(self.tool.command_argv, ['qemu-img', '--verbose'])

    def test_add_option_with_value(self):
        """Test adding an option with value"""
        self.tool._add_option('-f', 'qcow2')
        self.assertEqual(self.tool.command_argv, ['qemu-img', '-f', 'qcow2'])

    def test_add_option_with_none_value(self):
        """Test adding an option with None value (should be ignored)"""
        self.tool._add_option('-f', None)
        self.assertEqual(self.tool.command_argv, ['qemu-img'])

    def test_add_option_with_numeric_value(self):
        """Test adding an option with numeric value"""
        self.tool._add_option('-m', 4)
        self.assertEqual(self.tool.command_argv, ['qemu-img', '-m', '4'])

    def test_add_option_list_empty(self):
        """Test adding option list with empty list"""
        self.tool._add_option_list('-o', [])
        self.assertEqual(self.tool.command_argv, ['qemu-img'])

    def test_add_option_list_with_values(self):
        """Test adding option list with values"""
        self.tool._add_option_list(
            '-o', ['preallocation=metadata', 'lazy_refcounts=on'])
        expected = ['qemu-img', '-o', 'preallocation=metadata',
                    '-o', 'lazy_refcounts=on']
        self.assertEqual(self.tool.command_argv, expected)

    def test_add_option_list_with_none_values(self):
        """Test adding option list with some None values"""
        self.tool._add_option_list(
            '-o', ['preallocation=metadata', None, 'lazy_refcounts=on'])
        expected = ['qemu-img', '-o', 'preallocation=metadata',
                    '-o', 'lazy_refcounts=on']
        self.assertEqual(self.tool.command_argv, expected)


class TestQemuImgToolConvert(unittest.TestCase):
    """Test QemuImgTool convert method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.check_mode = False
        self.tool = QemuImgTool(self.mock_module)

    def test_convert_basic(self):
        """Test basic convert operation"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.convert('input.qcow2', 'output.qcow2')

        expected_cmd = ['qemu-img', 'convert', 'input.qcow2', 'output.qcow2']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_convert_with_formats(self):
        """Test convert with source and output formats"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.convert(
            'input.img', 'output.qcow2',
            source_format='raw', output_format='qcow2'
        )

        expected_cmd = ['qemu-img', 'convert', '-f', 'raw',
                        '-O', 'qcow2', 'input.img', 'output.qcow2']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_convert_with_compression(self):
        """Test convert with compression enabled"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.convert(
            'input.qcow2', 'output.qcow2',
            compressed=True
        )

        expected_cmd = ['qemu-img', 'convert',
                        '-c', 'input.qcow2', 'output.qcow2']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_convert_with_sparse_size(self):
        """Test convert with sparse size option"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.convert(
            'input.qcow2', 'output.qcow2',
            sparse_size='4k'
        )

        expected_cmd = ['qemu-img', 'convert', '-S',
                        '4k', 'input.qcow2', 'output.qcow2']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_convert_with_num_coroutines(self):
        """Test convert with number of coroutines"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.convert(
            'input.qcow2', 'output.qcow2',
            num_coroutines=4
        )

        expected_cmd = ['qemu-img', 'convert', '-m',
                        '4', 'input.qcow2', 'output.qcow2']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_convert_with_all_options(self):
        """Test convert with all options enabled"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.convert(
            'input.raw', 'output.qcow2',
            source_format='raw',
            output_format='qcow2',
            compressed=True,
            sparse_size='64k',
            num_coroutines=8
        )

        expected_cmd = [
            'qemu-img', 'convert',
            '-f', 'raw',
            '-O', 'qcow2',
            '-c',
            '-S', '64k',
            '-m', '8',
            'input.raw', 'output.qcow2'
        ]
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_convert_failure(self):
        """Test convert operation failure"""
        self.mock_module.run_command.return_value = (
            1, '', 'qemu-img: error: Could not open input file')

        rc, stdout, stderr = self.tool.convert(
            'nonexistent.qcow2', 'output.qcow2')

        self.assertEqual(rc, 1)
        self.assertEqual(stderr, 'qemu-img: error: Could not open input file')

    def test_convert_with_spaces_in_filenames(self):
        """Test convert with filenames containing spaces"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.convert(
            'input file.qcow2', 'output file.qcow2')

        expected_cmd = ['qemu-img', 'convert',
                        'input file.qcow2', 'output file.qcow2']
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)


class TestQemuImgToolInfo(unittest.TestCase):
    """Test QemuImgTool info method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.check_mode = False
        self.tool = QemuImgTool(self.mock_module)

    def test_info_basic(self):
        """Test basic info operation"""
        info_output = {
            "virtual-size": 1073741824,
            "filename": "test.qcow2",
            "cluster-size": 65536,
            "format": "qcow2",
            "actual-size": 262144,
            "format-specific": {
                "type": "qcow2",
                "data": {
                    "compat": "1.1",
                    "lazy-refcounts": False,
                    "refcount-bits": 16,
                    "corrupt": False
                }
            }
        }
        self.mock_module.run_command.return_value = (
            0, json.dumps(info_output), '')

        rc, parsed_output, stderr = self.tool.info('test.qcow2')

        expected_cmd = ['qemu-img', 'info', '--output', 'json', 'test.qcow2']
        self.assertEqual(rc, 0)
        self.assertEqual(parsed_output, info_output)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_info_with_source_format(self):
        """Test info with source format specified"""
        self.mock_module.run_command.return_value = (0, '{}', '')

        rc, parsed_output, stderr = self.tool.info(
            'test.img', source_format='raw')

        expected_cmd = ['qemu-img', 'info', '-f',
                        'raw', '--output', 'json', 'test.img']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_info_with_backing_chain(self):
        """Test info with backing chain option"""
        self.mock_module.run_command.return_value = (0, '{}', '')

        rc, parsed_output, stderr = self.tool.info(
            'test.qcow2', backing_chain=True)

        expected_cmd = ['qemu-img', 'info', '--backing-chain',
                        '--output', 'json', 'test.qcow2']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_info_with_all_options(self):
        """Test info with all options"""
        self.mock_module.run_command.return_value = (0, '{}', '')

        rc, parsed_output, stderr = self.tool.info(
            'test.qcow2',
            source_format='qcow2',
            backing_chain=True
        )

        expected_cmd = [
            'qemu-img', 'info',
            '-f', 'qcow2',
            '--backing-chain',
            '--output', 'json',
            'test.qcow2'
        ]
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_info_json_parse_failure(self):
        """Test info with invalid JSON output"""
        self.mock_module.run_command.return_value = (0, 'invalid json', '')

        rc, parsed_output, stderr = self.tool.info('test.qcow2')

        self.assertEqual(rc, 0)
        self.assertEqual(parsed_output, {})
        self.assertEqual(len(self.tool.warnings), 1)
        self.assertIn('Failed to parse JSON output', self.tool.warnings[0])

    def test_info_empty_output(self):
        """Test info with empty output"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, parsed_output, stderr = self.tool.info('test.qcow2')

        self.assertEqual(rc, 0)
        self.assertEqual(parsed_output, {})
        self.assertEqual(len(self.tool.warnings), 0)

    def test_info_whitespace_output(self):
        """Test info with whitespace-only output"""
        self.mock_module.run_command.return_value = (0, '   \n  \t  ', '')

        rc, parsed_output, stderr = self.tool.info('test.qcow2')

        self.assertEqual(rc, 0)
        self.assertEqual(parsed_output, {})

    def test_info_failure(self):
        """Test info operation failure"""
        self.mock_module.run_command.return_value = (
            1, '', 'qemu-img: Could not open file')

        rc, parsed_output, stderr = self.tool.info('nonexistent.qcow2')

        self.assertEqual(rc, 1)
        self.assertEqual(parsed_output, {})
        self.assertEqual(stderr, 'qemu-img: Could not open file')

    def test_info_complex_json(self):
        """Test info with complex JSON output including backing files"""
        complex_info = {
            "virtual-size": 2147483648,
            "filename": "overlay.qcow2",
            "cluster-size": 65536,
            "format": "qcow2",
            "actual-size": 1048576,
            "backing-filename": "base.qcow2",
            "backing-filename-format": "qcow2",
            "format-specific": {
                "type": "qcow2",
                "data": {
                    "compat": "1.1",
                    "lazy-refcounts": True,
                    "refcount-bits": 16,
                    "corrupt": False,
                    "extended-l2": False
                }
            }
        }
        self.mock_module.run_command.return_value = (
            0, json.dumps(complex_info), '')

        rc, parsed_output, stderr = self.tool.info('overlay.qcow2')

        self.assertEqual(rc, 0)
        self.assertEqual(parsed_output, complex_info)
        self.assertIn('backing-filename', parsed_output)
        self.assertEqual(parsed_output['backing-filename'], 'base.qcow2')


class TestQemuImgToolResize(unittest.TestCase):
    """Test QemuImgTool resize method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.check_mode = False
        self.tool = QemuImgTool(self.mock_module)

    def test_resize_basic(self):
        """Test basic resize operation"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.resize('test.qcow2', '20G')

        expected_cmd = ['qemu-img', 'resize', 'test.qcow2', '20G']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_resize_with_format(self):
        """Test resize with source format"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.resize(
            'test.img', '10G', source_format='raw')

        expected_cmd = ['qemu-img', 'resize', '-f', 'raw', 'test.img', '10G']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_resize_with_preallocation(self):
        """Test resize with preallocation mode"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.resize(
            'test.qcow2', '30G',
            preallocation='metadata'
        )

        expected_cmd = ['qemu-img', 'resize',
                        '--preallocation', 'metadata', 'test.qcow2', '30G']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_resize_with_shrink(self):
        """Test resize with shrink option"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.resize(
            'test.qcow2', '5G',
            shrink=True
        )

        expected_cmd = ['qemu-img', 'resize', '--shrink', 'test.qcow2', '5G']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_resize_with_all_options(self):
        """Test resize with all options"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.resize(
            'test.qcow2', '15G',
            source_format='qcow2',
            preallocation='full',
            shrink=True
        )

        expected_cmd = [
            'qemu-img', 'resize',
            '-f', 'qcow2',
            '--preallocation', 'full',
            '--shrink',
            'test.qcow2', '15G'
        ]
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_resize_increase_size(self):
        """Test resize with size increase (+prefix)"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.resize('test.qcow2', '+5G')

        expected_cmd = ['qemu-img', 'resize', 'test.qcow2', '+5G']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_resize_decrease_size(self):
        """Test resize with size decrease (-prefix)"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.resize(
            'test.qcow2', '-500M', shrink=True)

        expected_cmd = ['qemu-img', 'resize',
                        '--shrink', 'test.qcow2', '-500M']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_resize_different_size_units(self):
        """Test resize with different size units"""
        size_units = ['1024', '2k', '3M', '4G', '5T']

        for size in size_units:
            with self.subTest(size=size):
                # Reset the tool for each test
                self.tool = QemuImgTool(self.mock_module)
                self.mock_module.run_command.return_value = (0, '', '')

                rc, stdout, stderr = self.tool.resize('test.qcow2', size)

                expected_cmd = ['qemu-img', 'resize', 'test.qcow2', size]
                self.assertEqual(rc, 0)
                self.mock_module.run_command.assert_called_with(
                    expected_cmd, check_rc=False)

    def test_resize_failure(self):
        """Test resize operation failure"""
        self.mock_module.run_command.return_value = (
            1, '', 'qemu-img: Could not resize image')

        rc, stdout, stderr = self.tool.resize('test.qcow2', '10G')

        self.assertEqual(rc, 1)
        self.assertEqual(stderr, 'qemu-img: Could not resize image')

    def test_resize_shrink_without_flag_failure(self):
        """Test resize shrink without shrink flag (should fail)"""
        error_msg = 'qemu-img: Use the --shrink option to perform a shrink operation.'
        self.mock_module.run_command.return_value = (1, '', error_msg)

        rc, stdout, stderr = self.tool.resize(
            'test.qcow2', '5G')  # No shrink=True

        self.assertEqual(rc, 1)
        self.assertEqual(stderr, error_msg)

    def test_resize_numeric_size(self):
        """Test resize with numeric size (should be converted to string)"""
        self.mock_module.run_command.return_value = (0, '', '')

        rc, stdout, stderr = self.tool.resize(
            'test.qcow2', 21474836480)  # 20G in bytes

        expected_cmd = ['qemu-img', 'resize', 'test.qcow2', '21474836480']
        self.assertEqual(rc, 0)
        self.mock_module.run_command.assert_called_once_with(
            expected_cmd, check_rc=False)

    def test_resize_preallocation_modes(self):
        """Test resize with different preallocation modes"""
        prealloc_modes = ['off', 'metadata', 'falloc', 'full']

        for mode in prealloc_modes:
            with self.subTest(mode=mode):
                # Reset the tool for each test
                self.tool = QemuImgTool(self.mock_module)
                self.mock_module.run_command.return_value = (0, '', '')

                rc, stdout, stderr = self.tool.resize(
                    'test.qcow2', '20G',
                    preallocation=mode
                )

                expected_cmd = ['qemu-img', 'resize',
                                '--preallocation', mode, 'test.qcow2', '20G']
                self.assertEqual(rc, 0)
                self.mock_module.run_command.assert_called_with(
                    expected_cmd, check_rc=False)


class TestQemuImgToolIntegration(unittest.TestCase):
    """Integration tests for QemuImgTool"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.check_mode = False

    def test_automatic_command_reset(self):
        """Test that command_argv is automatically reset for each operation"""
        tool = QemuImgTool(self.mock_module)
        self.mock_module.run_command.return_value = (
            0, '{"format": "qcow2"}', '')

        # Verify initial state
        self.assertEqual(tool.command_argv, ['qemu-img'])
        self.assertEqual(tool._base_command, 'qemu-img')

        # First operation: info
        tool.info('test.qcow2')
        first_call = self.mock_module.run_command.call_args[0][0]
        expected_first = ['qemu-img', 'info', '--output', 'json', 'test.qcow2']
        self.assertEqual(first_call, expected_first)

        # Second operation: convert (should start fresh)
        tool.convert('input.qcow2', 'output.qcow2', compressed=True)
        second_call = self.mock_module.run_command.call_args[0][0]
        expected_second = ['qemu-img', 'convert',
                           '-c', 'input.qcow2', 'output.qcow2']
        self.assertEqual(second_call, expected_second)

        # Third operation: resize (should start fresh)
        tool.resize('test.qcow2', '20G', shrink=True)
        third_call = self.mock_module.run_command.call_args[0][0]
        expected_third = ['qemu-img', 'resize',
                          '--shrink', 'test.qcow2', '20G']
        self.assertEqual(third_call, expected_third)

    def test_automatic_command_reset_custom_tool(self):
        """Test automatic reset works with custom tool command"""
        custom_cmd = '/opt/qemu/bin/qemu-img'
        tool = QemuImgTool(self.mock_module, qemu_img_path=custom_cmd)
        self.mock_module.run_command.return_value = (0, '', '')

        # Verify initial state with custom command
        self.assertEqual(tool.command_argv, [custom_cmd])
        self.assertEqual(tool._base_command, custom_cmd)

        # First operation
        tool.info('test.qcow2')
        first_call = self.mock_module.run_command.call_args[0][0]
        self.assertEqual(first_call[0], custom_cmd)

        # Second operation should reset to custom command
        tool.convert('input.qcow2', 'output.qcow2')
        second_call = self.mock_module.run_command.call_args[0][0]
        self.assertEqual(second_call[0], custom_cmd)
        self.assertEqual(second_call[1], 'convert')

    def test_multiple_operations_same_instance(self):
        """Test performing multiple operations with the same instance"""
        tool = QemuImgTool(self.mock_module)

        # First operation: info
        self.mock_module.run_command.return_value = (
            0, '{"format": "qcow2"}', '')
        rc1, output1, stderr1 = tool.info('test.qcow2')

        # Second operation: resize (should automatically reset command_argv)
        self.mock_module.run_command.return_value = (0, '', '')
        rc2, output2, stderr2 = tool.resize('test.qcow2', '20G')

        # Third operation: convert (should automatically reset command_argv)
        self.mock_module.run_command.return_value = (0, '', '')
        rc3, output3, stderr3 = tool.convert('test.qcow2', 'output.qcow2')

        # Verify all operations succeeded
        self.assertEqual(rc1, 0)
        self.assertEqual(rc2, 0)
        self.assertEqual(rc3, 0)
        self.assertEqual(output1, {"format": "qcow2"})

    def test_command_argv_isolation(self):
        """Test that command_argv is properly isolated between operations"""
        tool = QemuImgTool(self.mock_module)
        self.mock_module.run_command.return_value = (0, '', '')

        # First operation should not affect subsequent operations
        tool.convert('input.qcow2', 'output1.qcow2', compressed=True)
        first_call_args = self.mock_module.run_command.call_args[0][0]

        # Second operation (should automatically reset command_argv)
        tool.convert('input.qcow2', 'output2.qcow2')  # No compression
        second_call_args = self.mock_module.run_command.call_args[0][0]

        # First call should have compression flag, second should not
        self.assertIn('-c', first_call_args)
        self.assertNotIn('-c', second_call_args)

    def test_warnings_accumulation(self):
        """Test that warnings accumulate across operations"""
        tool = QemuImgTool(self.mock_module)

        # First operation with invalid JSON
        self.mock_module.run_command.return_value = (0, 'invalid json 1', '')
        tool.info('test1.qcow2')

        # Second operation with invalid JSON
        self.mock_module.run_command.return_value = (0, 'invalid json 2', '')
        tool.info('test2.qcow2')

        # Should have two warnings
        self.assertEqual(len(tool.warnings), 2)
        self.assertIn('Failed to parse JSON output', tool.warnings[0])
        self.assertIn('Failed to parse JSON output', tool.warnings[1])

    def test_custom_command_path(self):
        """Test using custom qemu-img command path"""
        custom_path = '/opt/qemu/bin/qemu-img'
        tool = QemuImgTool(self.mock_module, qemu_img_path=custom_path)
        self.mock_module.run_command.return_value = (0, '', '')

        tool.info('test.qcow2')

        called_cmd = self.mock_module.run_command.call_args[0][0]
        self.assertEqual(called_cmd[0], custom_path)

    def test_error_handling_consistency(self):
        """Test consistent error handling across all methods"""
        tool = QemuImgTool(self.mock_module)
        error_rc = 2
        error_message = 'Generic qemu-img error'
        self.mock_module.run_command.return_value = (
            error_rc, '', error_message)

        # Test all methods return the same error code and message
        rc1, stdout1, stderr1 = tool.convert('input.qcow2', 'output.qcow2')
        rc2, stdout2, stderr2 = tool.info('test.qcow2')
        rc3, stdout3, stderr3 = tool.resize('test.qcow2', '10G')

        self.assertEqual(rc1, error_rc)
        self.assertEqual(rc2, error_rc)
        self.assertEqual(rc3, error_rc)
        self.assertEqual(stderr1, error_message)
        self.assertEqual(stderr2, error_message)
        self.assertEqual(stderr3, error_message)

    def test_check_mode_convert(self):
        """Test that convert respects check_mode"""
        tool = QemuImgTool(self.mock_module)
        self.mock_module.check_mode = True

        # In check mode, command should not be executed
        rc, stdout, stderr = tool.convert(
            'input.qcow2', 'output.qcow2', compressed=True)

        # Should return success with descriptive message
        self.assertEqual(rc, 0)
        self.assertIn(
            'Would convert image from input.qcow2 to output.qcow2', stdout)
        self.assertEqual(stderr, '')

        # run_command should not have been called
        self.mock_module.run_command.assert_not_called()

    def test_check_mode_resize(self):
        """Test that resize respects check_mode"""
        tool = QemuImgTool(self.mock_module)
        self.mock_module.check_mode = True

        # In check mode, command should not be executed
        rc, stdout, stderr = tool.resize('test.qcow2', '20G', shrink=True)

        # Should return success with descriptive message
        self.assertEqual(rc, 0)
        self.assertIn('Would resize image test.qcow2 to 20G', stdout)
        self.assertEqual(stderr, '')

        # run_command should not have been called
        self.mock_module.run_command.assert_not_called()

    def test_check_mode_info_not_affected(self):
        """Test that info command is not affected by check_mode"""
        tool = QemuImgTool(self.mock_module)
        self.mock_module.check_mode = True
        self.mock_module.run_command.return_value = (
            0, '{"format": "qcow2"}', '')

        # Info should still execute even in check mode (read-only operation)
        rc, output, stderr = tool.info('test.qcow2')

        # Should execute normally and return parsed output
        self.assertEqual(rc, 0)
        self.assertEqual(output, {"format": "qcow2"})
        self.assertEqual(stderr, '')

        # run_command should have been called for info (read-only)
        self.mock_module.run_command.assert_called_once()

    def test_check_mode_false_normal_execution(self):
        """Test that operations execute normally when check_mode is False"""
        tool = QemuImgTool(self.mock_module)
        self.mock_module.check_mode = False
        self.mock_module.run_command.return_value = (0, '', '')

        # All operations should execute normally
        rc1, stdout1, stderr1 = tool.convert('input.qcow2', 'output.qcow2')
        rc2, stdout2, stderr2 = tool.resize('test.qcow2', '20G')

        # Should return normal command output, not check_mode messages
        self.assertEqual(rc1, 0)
        self.assertEqual(rc2, 0)
        self.assertNotIn('Would convert', stdout1)
        self.assertNotIn('Would resize', stdout2)

        # run_command should have been called twice
        self.assertEqual(self.mock_module.run_command.call_count, 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
