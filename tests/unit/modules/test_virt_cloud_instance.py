# -*- coding: utf-8 -*-
#
# (c) 2025, Joey Zhang <thinkdoggie@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import unittest

import os

from ansible_collections.community.libvirt.tests.unit.compat import mock
from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import BaseImageOperator


class TestBaseImageOperatorInit(unittest.TestCase):
    """Test BaseImageOperator initialization"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.tmpdir = '/tmp/ansible_test'
        self.mock_module.check_mode = False

    def test_init_with_required_params(self):
        """Test initialization with required parameters only"""
        operator = BaseImageOperator(self.mock_module, '/path/to/image.qcow2')

        self.assertEqual(operator.module, self.mock_module)
        self.assertEqual(operator.base_image, '/path/to/image.qcow2')
        self.assertIsNone(operator.image_cache_dir)
        self.assertIsNone(operator.image_checksum)
        self.assertIsNone(operator.base_image_path)
        self.assertIsNone(operator.system_disk_path)

    def test_init_with_all_params(self):
        """Test initialization with all parameters"""
        operator = BaseImageOperator(
            self.mock_module,
            'https://example.com/image.qcow2',
            image_cache_dir='/var/cache/images',
            image_checksum='sha256:abc123'
        )

        self.assertEqual(operator.module, self.mock_module)
        self.assertEqual(operator.base_image,
                         'https://example.com/image.qcow2')
        self.assertEqual(operator.image_cache_dir, '/var/cache/images')
        self.assertEqual(operator.image_checksum, 'sha256:abc123')
        self.assertIsNone(operator.base_image_path)
        self.assertIsNone(operator.system_disk_path)


class TestBaseImageOperatorFetchImage(unittest.TestCase):
    """Test BaseImageOperator fetch_image method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.tmpdir = '/tmp/ansible_test'
        self.mock_module.check_mode = False
        self.mock_module.atomic_move = mock.Mock()

    def test_fetch_image_local_file_exists(self):
        """Test fetching local file that exists"""
        operator = BaseImageOperator(
            self.mock_module, '/path/to/local/image.qcow2')

        with mock.patch('os.path.exists', return_value=True):
            result = operator.fetch_image(force_pull=False)

            self.assertEqual(result, '/path/to/local/image.qcow2')
            self.assertEqual(operator.base_image_path,
                             '/path/to/local/image.qcow2')
            self.mock_module.fail_json.assert_not_called()

    def test_fetch_image_local_file_not_exists(self):
        """Test fetching local file that doesn't exist"""
        operator = BaseImageOperator(
            self.mock_module, '/path/to/nonexistent.qcow2')

        with mock.patch('os.path.exists', return_value=False):
            operator.fetch_image(force_pull=False)

            self.mock_module.fail_json.assert_called_once_with(
                msg="Base image file does not exist: /path/to/nonexistent.qcow2"
            )

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_file')
    def test_fetch_image_remote_url_no_cache(self, mock_fetch_file):
        """Test fetching remote URL without cache directory"""
        operator = BaseImageOperator(
            self.mock_module, 'https://example.com/image.qcow2')
        mock_fetch_file.return_value = '/tmp/downloaded_file'

        result = operator.fetch_image(force_pull=False, timeout=30)

        expected_path = os.path.join(self.mock_module.tmpdir, 'image.qcow2')
        self.assertEqual(result, expected_path)
        self.assertEqual(operator.base_image_path, expected_path)
        mock_fetch_file.assert_called_once_with(
            self.mock_module, 'https://example.com/image.qcow2', timeout=30
        )
        self.mock_module.atomic_move.assert_called_once_with(
            '/tmp/downloaded_file', expected_path)

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_file')
    def test_fetch_image_remote_url_with_cache_not_exists(self, mock_fetch_file):
        """Test fetching remote URL with cache directory, file not cached"""
        operator = BaseImageOperator(
            self.mock_module,
            'https://example.com/image.qcow2',
            image_cache_dir='/var/cache'
        )
        mock_fetch_file.return_value = '/tmp/downloaded_file'

        with mock.patch('os.path.exists', return_value=False):
            result = operator.fetch_image(force_pull=False)

            expected_path = '/var/cache/image.qcow2'
            self.assertEqual(result, expected_path)
            self.assertEqual(operator.base_image_path, expected_path)
            mock_fetch_file.assert_called_once()
            self.mock_module.atomic_move.assert_called_once_with(
                '/tmp/downloaded_file', expected_path)

    def test_fetch_image_remote_url_with_cache_exists_no_force(self):
        """Test fetching remote URL with cache directory, file exists, no force pull"""
        operator = BaseImageOperator(
            self.mock_module,
            'https://example.com/image.qcow2',
            image_cache_dir='/var/cache'
        )

        with mock.patch('os.path.exists', return_value=True):
            result = operator.fetch_image(force_pull=False)

            expected_path = '/var/cache/image.qcow2'
            self.assertEqual(result, expected_path)
            self.assertEqual(operator.base_image_path, expected_path)
            self.mock_module.atomic_move.assert_not_called()

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_file')
    def test_fetch_image_remote_url_with_cache_exists_force_pull(self, mock_fetch_file):
        """Test fetching remote URL with cache directory, file exists, force pull enabled"""
        operator = BaseImageOperator(
            self.mock_module,
            'https://example.com/image.qcow2',
            image_cache_dir='/var/cache'
        )
        mock_fetch_file.return_value = '/tmp/downloaded_file'

        with mock.patch('os.path.exists', return_value=True):
            result = operator.fetch_image(force_pull=True)

            expected_path = '/var/cache/image.qcow2'
            self.assertEqual(result, expected_path)
            self.assertEqual(operator.base_image_path, expected_path)
            mock_fetch_file.assert_called_once()
            self.mock_module.atomic_move.assert_called_once_with(
                '/tmp/downloaded_file', expected_path)

    def test_fetch_image_url_without_filename(self):
        """Test fetching URL without filename"""
        operator = BaseImageOperator(self.mock_module, 'https://example.com/')

        # Make fail_json raise an exception to simulate real behavior
        self.mock_module.fail_json.side_effect = Exception("Module failed")

        with self.assertRaises(Exception):
            operator.fetch_image(force_pull=False)

        self.mock_module.fail_json.assert_called_once_with(
            msg="Failed to determine filename from base image URL: https://example.com/"
        )

    def test_fetch_image_unsupported_scheme(self):
        """Test fetching with unsupported URL scheme (should be treated as local file)"""
        operator = BaseImageOperator(
            self.mock_module, 'file:///path/to/image.qcow2')

        with mock.patch('os.path.exists', return_value=True):
            result = operator.fetch_image(force_pull=False)

            self.assertEqual(result, 'file:///path/to/image.qcow2')
            self.assertEqual(operator.base_image_path,
                             'file:///path/to/image.qcow2')


class TestBaseImageOperatorResolveSystemDisk(unittest.TestCase):
    """Test BaseImageOperator _resolve_system_disk method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.check_mode = False
        self.operator = BaseImageOperator(
            self.mock_module, '/path/to/image.qcow2')

    def test_resolve_system_disk_with_path(self):
        """Test resolving system disk with path parameter"""
        disk_param = {'path': '/var/lib/libvirt/images/vm.qcow2', 'size': 20}

        result = self.operator._resolve_system_disk(disk_param)

        self.assertEqual(result, disk_param)
        self.assertEqual(self.operator.system_disk_path,
                         '/var/lib/libvirt/images/vm.qcow2')

    def test_resolve_system_disk_without_path(self):
        """Test resolving system disk without path parameter"""
        disk_param = {'size': 20}

        with self.assertRaises(ValueError) as context:
            self.operator._resolve_system_disk(disk_param)

        self.assertEqual(str(context.exception),
                         "The first disk must have a path to import the cloud image")

    def test_resolve_system_disk_empty_path(self):
        """Test resolving system disk with empty path"""
        disk_param = {'path': '', 'size': 20}

        with self.assertRaises(ValueError) as context:
            self.operator._resolve_system_disk(disk_param)

        self.assertEqual(str(context.exception),
                         "The first disk must have a path to import the cloud image")

    def test_resolve_system_disk_none_path(self):
        """Test resolving system disk with None path"""
        disk_param = {'path': None, 'size': 20}

        with self.assertRaises(ValueError) as context:
            self.operator._resolve_system_disk(disk_param)

        self.assertEqual(str(context.exception),
                         "The first disk must have a path to import the cloud image")


class TestBaseImageOperatorValidateChecksum(unittest.TestCase):
    """Test BaseImageOperator validate_checksum method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.check_mode = False
        self.mock_module.digest_from_file = mock.Mock()

    def test_validate_checksum_no_checksum(self):
        """Test validation when no checksum is specified"""
        operator = BaseImageOperator(self.mock_module, '/path/to/image.qcow2')

        result = operator.validate_checksum()

        self.assertTrue(result)

    def test_validate_checksum_no_base_image_path(self):
        """Test validation when base image path is not set"""
        operator = BaseImageOperator(
            self.mock_module,
            '/path/to/image.qcow2',
            image_checksum='sha256:abc123'
        )

        operator.validate_checksum()

        self.mock_module.fail_json.assert_called_once_with(
            msg="Base image path not found for checksum validation"
        )

    @mock.patch('os.path.exists', return_value=False)
    def test_validate_checksum_file_not_exists(self, mock_exists):
        """Test validation when base image file doesn't exist"""
        operator = BaseImageOperator(
            self.mock_module,
            '/path/to/image.qcow2',
            image_checksum='sha256:abc123'
        )
        operator.base_image_path = '/path/to/image.qcow2'

        operator.validate_checksum()

        self.mock_module.fail_json.assert_called_once_with(
            msg="Base image path not found for checksum validation"
        )

    def test_validate_checksum_invalid_format(self):
        """Test validation with invalid checksum format"""
        operator = BaseImageOperator(
            self.mock_module,
            '/path/to/image.qcow2',
            image_checksum='invalidformat'
        )
        operator.base_image_path = '/path/to/image.qcow2'

        # Make fail_json raise an exception to simulate real behavior
        self.mock_module.fail_json.side_effect = Exception("Module failed")

        with mock.patch('os.path.exists', return_value=True):
            with self.assertRaises(Exception):
                operator.validate_checksum()

        self.mock_module.fail_json.assert_called_once_with(
            msg="The image_checksum parameter has to be in format <algorithm>:<checksum>"
        )

    @mock.patch('os.path.exists', return_value=True)
    def test_validate_checksum_invalid_hex(self, mock_exists):
        """Test validation with invalid hex checksum"""
        operator = BaseImageOperator(
            self.mock_module,
            '/path/to/image.qcow2',
            image_checksum='sha256:invalid_hex_xyz'
        )
        operator.base_image_path = '/path/to/image.qcow2'

        operator.validate_checksum()

        self.mock_module.fail_json.assert_called_once_with(
            msg='The checksum format is invalid'
        )

    @mock.patch('os.path.exists', return_value=True)
    def test_validate_checksum_successful_match(self, mock_exists):
        """Test successful checksum validation"""
        expected_checksum = 'abc123def456'
        operator = BaseImageOperator(
            self.mock_module,
            '/path/to/image.qcow2',
            image_checksum=f'sha256:{expected_checksum}'
        )
        operator.base_image_path = '/path/to/image.qcow2'
        self.mock_module.digest_from_file.return_value = expected_checksum

        result = operator.validate_checksum()

        self.assertTrue(result)
        self.mock_module.digest_from_file.assert_called_once_with(
            '/path/to/image.qcow2', 'sha256'
        )

    @mock.patch('os.path.exists', return_value=True)
    def test_validate_checksum_mismatch(self, mock_exists):
        """Test checksum validation with mismatch"""
        operator = BaseImageOperator(
            self.mock_module,
            '/path/to/image.qcow2',
            image_checksum='sha256:abc123def456'
        )
        operator.base_image_path = '/path/to/image.qcow2'
        self.mock_module.digest_from_file.return_value = 'different_checksum'

        result = operator.validate_checksum()

        self.assertFalse(result)

    @mock.patch('os.path.exists', return_value=True)
    def test_validate_checksum_digest_error(self, mock_exists):
        """Test checksum validation with digest calculation error"""
        operator = BaseImageOperator(
            self.mock_module,
            '/path/to/image.qcow2',
            image_checksum='sha256:abc123def456'
        )
        operator.base_image_path = '/path/to/image.qcow2'
        self.mock_module.digest_from_file.side_effect = ValueError(
            "Unsupported algorithm")

        # Make fail_json raise an exception to simulate real behavior
        self.mock_module.fail_json.side_effect = Exception("Module failed")

        with self.assertRaises(Exception):
            operator.validate_checksum()

        self.mock_module.fail_json.assert_called_once_with(
            msg="Failed to calculate the actual checksum of the file: Unsupported algorithm"
        )

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_url')
    @mock.patch('os.path.exists', return_value=True)
    def test_validate_checksum_from_url(self, mock_exists, mock_fetch_url):
        """Test checksum validation from URL"""
        # Mock the response object
        mock_response = mock.Mock()
        mock_response.read.return_value = b'abc123def456  image.qcow2\n'
        mock_fetch_url.return_value = (mock_response, {})

        operator = BaseImageOperator(
            self.mock_module,
            'https://example.com/image.qcow2',
            image_checksum='sha256:https://example.com/checksums.sha256'
        )
        operator.base_image_path = '/path/to/image.qcow2'
        self.mock_module.digest_from_file.return_value = 'abc123def456'

        result = operator.validate_checksum()

        self.assertTrue(result)
        mock_fetch_url.assert_called_once_with(
            self.mock_module, 'https://example.com/checksums.sha256', timeout=60
        )

    @mock.patch('os.path.exists', return_value=True)
    def test_validate_checksum_whitespace_handling(self, mock_exists):
        """Test checksum validation with whitespace in checksum"""
        operator = BaseImageOperator(
            self.mock_module,
            '/path/to/image.qcow2',
            image_checksum='sha256: abc 123 def 456 '
        )
        operator.base_image_path = '/path/to/image.qcow2'
        self.mock_module.digest_from_file.return_value = 'abc123def456'

        result = operator.validate_checksum()

        self.assertTrue(result)


class TestBaseImageOperatorFetchChecksumFromUrl(unittest.TestCase):
    """Test BaseImageOperator _fetch_checksum_from_url method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.check_mode = False
        self.operator = BaseImageOperator(
            self.mock_module,
            'https://example.com/image.qcow2'
        )

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_url')
    def test_fetch_checksum_single_line_format(self, mock_fetch_url):
        """Test fetching checksum from single-line format"""
        mock_response = mock.Mock()
        mock_response.read.return_value = b'abc123def456'
        mock_fetch_url.return_value = (mock_response, {})

        result = self.operator._fetch_checksum_from_url(
            'https://example.com/checksum.txt', 'sha256'
        )

        self.assertEqual(result, 'abc123def456')

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_url')
    def test_fetch_checksum_multi_line_format(self, mock_fetch_url):
        """Test fetching checksum from multi-line format"""
        checksum_content = (
            'abc123def456  image.qcow2\n'
            'def456ghi789  other.qcow2\n'
        )
        mock_response = mock.Mock()
        mock_response.read.return_value = checksum_content.encode()
        mock_fetch_url.return_value = (mock_response, {})

        result = self.operator._fetch_checksum_from_url(
            'https://example.com/checksums.txt', 'sha256'
        )

        self.assertEqual(result, 'abc123def456')

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_url')
    def test_fetch_checksum_binary_mode_marker(self, mock_fetch_url):
        """Test fetching checksum with binary mode marker"""
        checksum_content = 'abc123def456 *image.qcow2\n'
        mock_response = mock.Mock()
        mock_response.read.return_value = checksum_content.encode()
        mock_fetch_url.return_value = (mock_response, {})

        result = self.operator._fetch_checksum_from_url(
            'https://example.com/checksums.txt', 'sha256'
        )

        self.assertEqual(result, 'abc123def456')

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_url')
    def test_fetch_checksum_with_path_prefix(self, mock_fetch_url):
        """Test fetching checksum with path prefix"""
        checksum_content = 'abc123def456  ./image.qcow2\n'
        mock_response = mock.Mock()
        mock_response.read.return_value = checksum_content.encode()
        mock_fetch_url.return_value = (mock_response, {})

        result = self.operator._fetch_checksum_from_url(
            'https://example.com/checksums.txt', 'sha256'
        )

        self.assertEqual(result, 'abc123def456')

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_url')
    def test_fetch_checksum_file_not_found(self, mock_fetch_url):
        """Test fetching checksum when file is not found in checksum file"""
        checksum_content = 'abc123def456  other.qcow2\n'
        mock_response = mock.Mock()
        mock_response.read.return_value = checksum_content.encode()
        mock_fetch_url.return_value = (mock_response, {})

        self.operator._fetch_checksum_from_url(
            'https://example.com/checksums.txt', 'sha256'
        )

        self.mock_module.fail_json.assert_called_once_with(
            msg="Unable to find a checksum for file 'image.qcow2' in 'https://example.com/checksums.txt'"
        )

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_url')
    def test_fetch_checksum_download_failure(self, mock_fetch_url):
        """Test fetching checksum when download fails"""
        mock_fetch_url.return_value = (None, {'msg': 'Connection failed'})

        # Make fail_json raise an exception to simulate real behavior
        self.mock_module.fail_json.side_effect = Exception("Module failed")

        with self.assertRaises(Exception):
            self.operator._fetch_checksum_from_url(
                'https://example.com/checksums.txt', 'sha256'
            )

        self.mock_module.fail_json.assert_called_once_with(
            msg="Failed to download checksum from https://example.com/checksums.txt: Connection failed"
        )


class TestBaseImageOperatorBuildSystemDisk(unittest.TestCase):
    """Test BaseImageOperator build_system_disk method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.check_mode = False
        self.mock_module.preserved_copy = mock.Mock()
        self.operator = BaseImageOperator(
            self.mock_module, '/path/to/image.qcow2')
        self.operator.base_image_path = '/path/to/base.qcow2'

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.QemuImgTool')
    @mock.patch('os.path.exists')
    def test_build_system_disk_basic(self, mock_exists, mock_qemu_tool_class):
        """Test basic system disk building"""
        mock_exists.return_value = False  # System disk doesn't exist

        # Configure the mocked QemuImgTool
        mock_qemu_instance = mock.Mock()
        mock_qemu_tool_class.return_value = mock_qemu_instance
        mock_qemu_instance.info.return_value = (0, {
            'format': 'qcow2',
            'virtual-size': 1073741824  # 1GB
        }, '')
        mock_qemu_instance.resize.return_value = (0, '', '')

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 20,
            'format': 'qcow2'
        }

        result = self.operator.build_system_disk(disk_param)

        self.assertEqual(result, disk_param)
        self.assertEqual(self.operator.system_disk_path,
                         '/var/lib/libvirt/images/vm.qcow2')
        mock_qemu_instance.info.assert_called_once_with('/path/to/base.qcow2')
        self.mock_module.preserved_copy.assert_called_once_with(
            '/path/to/base.qcow2', '/var/lib/libvirt/images/vm.qcow2'
        )
        mock_qemu_instance.resize.assert_called_once_with(
            '/var/lib/libvirt/images/vm.qcow2', '20G'
        )

    @mock.patch('os.path.exists')
    def test_build_system_disk_already_exists(self, mock_exists):
        """Test building system disk when target already exists"""
        mock_exists.return_value = True

        # Make fail_json raise an exception to simulate real behavior
        self.mock_module.fail_json.side_effect = Exception("Module failed")

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 20
        }

        with self.assertRaises(Exception):
            self.operator.build_system_disk(disk_param)

        self.mock_module.fail_json.assert_called_once_with(
            msg="The system disk file already exists: /var/lib/libvirt/images/vm.qcow2"
        )

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.QemuImgTool')
    @mock.patch('os.path.exists')
    def test_build_system_disk_info_failure(self, mock_exists, mock_qemu_tool_class):
        """Test building system disk when qemu-img info fails"""
        mock_exists.return_value = False

        # Configure the mocked QemuImgTool to return failure
        mock_qemu_instance = mock.Mock()
        mock_qemu_tool_class.return_value = mock_qemu_instance
        mock_qemu_instance.info.return_value = (
            1, {}, 'Failed to get image info')

        # Make fail_json raise an exception to simulate real behavior
        self.mock_module.fail_json.side_effect = Exception("Module failed")

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 20
        }

        with self.assertRaises(Exception):
            self.operator.build_system_disk(disk_param)

        self.mock_module.fail_json.assert_called_once_with(
            msg="Failed to get base image info: Failed to get image info"
        )

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.QemuImgTool')
    @mock.patch('os.path.exists')
    def test_build_system_disk_no_format(self, mock_exists, mock_qemu_tool_class):
        """Test building system disk when base image has no format"""
        mock_exists.return_value = False

        # Configure the mocked QemuImgTool to return no format
        mock_qemu_instance = mock.Mock()
        mock_qemu_tool_class.return_value = mock_qemu_instance
        mock_qemu_instance.info.return_value = (0, {
            'virtual-size': 1073741824
        }, '')

        # Make fail_json raise an exception to simulate real behavior
        self.mock_module.fail_json.side_effect = Exception("Module failed")

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 20
        }

        with self.assertRaises(Exception):
            self.operator.build_system_disk(disk_param)

        self.mock_module.fail_json.assert_called_once_with(
            msg="No valid format found for the base image: /path/to/base.qcow2"
        )

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.QemuImgTool')
    @mock.patch('os.path.exists')
    def test_build_system_disk_invalid_size(self, mock_exists, mock_qemu_tool_class):
        """Test building system disk with invalid size"""
        mock_exists.return_value = False

        # Configure the mocked QemuImgTool
        mock_qemu_instance = mock.Mock()
        mock_qemu_tool_class.return_value = mock_qemu_instance
        mock_qemu_instance.info.return_value = (0, {
            'format': 'qcow2',
            'virtual-size': 1073741824
        }, '')

        # Make fail_json raise an exception to simulate real behavior
        self.mock_module.fail_json.side_effect = Exception("Module failed")

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 'invalid'
        }

        with self.assertRaises(Exception):
            self.operator.build_system_disk(disk_param)

        self.mock_module.fail_json.assert_called_once_with(
            msg="The system disk size must be an integer"
        )

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.QemuImgTool')
    @mock.patch('os.path.exists')
    def test_build_system_disk_size_too_small(self, mock_exists, mock_qemu_tool_class):
        """Test building system disk when size is too small"""
        mock_exists.return_value = False

        # Configure the mocked QemuImgTool
        mock_qemu_instance = mock.Mock()
        mock_qemu_tool_class.return_value = mock_qemu_instance
        mock_qemu_instance.info.return_value = (0, {
            'format': 'qcow2',
            'virtual-size': 21474836480  # 20GB
        }, '')

        # Make fail_json raise an exception to simulate real behavior
        self.mock_module.fail_json.side_effect = Exception("Module failed")

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 10  # 10GB, smaller than base image
        }

        with self.assertRaises(Exception):
            self.operator.build_system_disk(disk_param)

        expected_system_size = 10 * 1024 * 1024 * 1024
        self.mock_module.fail_json.assert_called_once_with(
            msg=f"The system disk size is too small to import the base image: {expected_system_size} < 21474836480"
        )

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.QemuImgTool')
    @mock.patch('os.path.exists')
    @mock.patch('os.remove')
    def test_build_system_disk_force_disk_removes_existing(self, mock_remove, mock_exists, mock_qemu_tool_class):
        """Test building system disk with force_disk=True removes existing file"""
        mock_exists.return_value = True  # System disk exists

        # Configure the mocked QemuImgTool
        mock_qemu_instance = mock.Mock()
        mock_qemu_tool_class.return_value = mock_qemu_instance
        mock_qemu_instance.info.return_value = (0, {
            'format': 'qcow2',
            'virtual-size': 1073741824  # 1GB
        }, '')
        mock_qemu_instance.resize.return_value = (0, '', '')

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 20,
            'format': 'qcow2'
        }

        result = self.operator.build_system_disk(disk_param, force_disk=True)

        # Verify the existing file was removed
        mock_remove.assert_called_once_with('/var/lib/libvirt/images/vm.qcow2')
        self.assertEqual(result, disk_param)

        # Verify disk was created after removal
        self.mock_module.preserved_copy.assert_called_once_with(
            '/path/to/base.qcow2', '/var/lib/libvirt/images/vm.qcow2'
        )
        mock_qemu_instance.resize.assert_called_once()

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.QemuImgTool')
    @mock.patch('os.path.exists')
    @mock.patch('os.remove')
    def test_build_system_disk_force_disk_check_mode(self, mock_remove, mock_exists, mock_qemu_tool_class):
        """Test building system disk with force_disk=True in check_mode doesn't remove file"""
        self.mock_module.check_mode = True
        # System disk exists, base image doesn't exist
        mock_exists.side_effect = lambda path: path == '/var/lib/libvirt/images/vm.qcow2'

        # Configure the mocked QemuImgTool
        mock_qemu_instance = mock.Mock()
        mock_qemu_tool_class.return_value = mock_qemu_instance

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 20,
            'format': 'qcow2'
        }

        result = self.operator.build_system_disk(disk_param, force_disk=True)

        # In check_mode, file should NOT be removed
        mock_remove.assert_not_called()

        # Should return disk config without creating files
        self.assertEqual(result, disk_param)
        self.mock_module.preserved_copy.assert_not_called()
        mock_qemu_instance.resize.assert_not_called()

    @mock.patch('os.path.exists')
    def test_build_system_disk_force_disk_false_existing_fails(self, mock_exists):
        """Test building system disk with force_disk=False fails when disk exists"""
        mock_exists.return_value = True  # System disk exists

        # Make fail_json raise an exception to simulate real behavior
        self.mock_module.fail_json.side_effect = Exception("Module failed")

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 20
        }

        with self.assertRaises(Exception):
            self.operator.build_system_disk(disk_param, force_disk=False)

        self.mock_module.fail_json.assert_called_once_with(
            msg="The system disk file already exists: /var/lib/libvirt/images/vm.qcow2"
        )


class TestBaseImageOperatorCheckMode(unittest.TestCase):
    """Test BaseImageOperator check_mode support"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.tmpdir = '/tmp/ansible_test'

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_file')
    @mock.patch('os.path.exists')
    def test_fetch_image_check_mode_local_file(self, mock_exists, mock_fetch_file):
        """Test fetch_image with check_mode for local file"""
        self.mock_module.check_mode = True
        mock_exists.return_value = True

        operator = BaseImageOperator(
            self.mock_module, '/path/to/local/image.qcow2')
        result = operator.fetch_image(force_pull=False)

        # Local files should still be processed in check_mode
        self.assertEqual(result, '/path/to/local/image.qcow2')
        mock_fetch_file.assert_not_called()

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_file')
    @mock.patch('os.path.exists')
    def test_fetch_image_check_mode_url(self, mock_exists, mock_fetch_file):
        """Test fetch_image with check_mode for URL"""
        self.mock_module.check_mode = True
        mock_exists.return_value = False

        operator = BaseImageOperator(
            self.mock_module, 'https://example.com/image.qcow2')
        result = operator.fetch_image(force_pull=False)

        # URL downloads should be skipped in check_mode
        expected_path = '/tmp/ansible_test/image.qcow2'
        self.assertEqual(result, expected_path)
        self.assertEqual(operator.base_image_path, expected_path)
        mock_fetch_file.assert_not_called()
        self.mock_module.atomic_move.assert_not_called()

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.fetch_file')
    @mock.patch('os.path.exists')
    def test_fetch_image_normal_mode_url(self, mock_exists, mock_fetch_file):
        """Test fetch_image with normal mode for URL"""
        self.mock_module.check_mode = False
        mock_exists.return_value = False
        mock_fetch_file.return_value = '/tmp/temp_image'

        operator = BaseImageOperator(
            self.mock_module, 'https://example.com/image.qcow2')
        result = operator.fetch_image(force_pull=False)

        # Normal mode should download the file
        expected_path = '/tmp/ansible_test/image.qcow2'
        self.assertEqual(result, expected_path)
        mock_fetch_file.assert_called_once()
        self.mock_module.atomic_move.assert_called_once_with(
            '/tmp/temp_image', expected_path)

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.QemuImgTool')
    @mock.patch('os.path.exists')
    def test_build_system_disk_check_mode(self, mock_exists, mock_qemu_tool_class):
        """Test build_system_disk with check_mode"""
        self.mock_module.check_mode = True
        mock_exists.side_effect = lambda path: False  # System disk doesn't exist

        # Mock QemuImgTool
        mock_qemu_tool = mock.Mock()
        mock_qemu_tool_class.return_value = mock_qemu_tool

        operator = BaseImageOperator(self.mock_module, '/path/to/image.qcow2')
        operator.base_image_path = '/path/to/base.qcow2'

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 20,
            'format': 'qcow2'
        }

        result = operator.build_system_disk(disk_param)

        # Should return disk config without creating files
        self.assertEqual(result, disk_param)

        # QemuImgTool operations should not be called for file creation
        mock_qemu_tool.convert.assert_not_called()
        mock_qemu_tool.resize.assert_not_called()
        self.mock_module.preserved_copy.assert_not_called()

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.QemuImgTool')
    @mock.patch('os.path.exists')
    def test_build_system_disk_check_mode_with_nonexistent_base_image(self, mock_exists, mock_qemu_tool_class):
        """Test build_system_disk with check_mode when base image doesn't exist"""
        self.mock_module.check_mode = True
        mock_exists.side_effect = lambda path: False  # No files exist

        # Mock QemuImgTool
        mock_qemu_tool = mock.Mock()
        mock_qemu_tool_class.return_value = mock_qemu_tool

        operator = BaseImageOperator(self.mock_module, '/path/to/image.qcow2')
        operator.base_image_path = '/path/to/nonexistent/base.qcow2'

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 20,
            'format': 'qcow2'
        }

        result = operator.build_system_disk(disk_param)

        # Should use mock values for validation when base image doesn't exist
        self.assertEqual(result, disk_param)

        # QemuImgTool.info should not be called since base image doesn't exist
        mock_qemu_tool.info.assert_not_called()

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.QemuImgTool')
    @mock.patch('os.path.exists')
    def test_build_system_disk_normal_mode(self, mock_exists, mock_qemu_tool_class):
        """Test build_system_disk with normal mode"""
        self.mock_module.check_mode = False
        self.mock_module.preserved_copy = mock.Mock()
        # System disk doesn't exist, base image exists
        mock_exists.side_effect = lambda path: path != '/var/lib/libvirt/images/vm.qcow2'

        # Mock QemuImgTool
        mock_qemu_tool = mock.Mock()
        mock_qemu_tool.info.return_value = (0, {
            'format': 'qcow2',
            'virtual-size': 5 * 1024 * 1024 * 1024  # 5GB
        }, '')
        mock_qemu_tool.resize.return_value = (0, '', '')
        mock_qemu_tool_class.return_value = mock_qemu_tool

        operator = BaseImageOperator(self.mock_module, '/path/to/image.qcow2')
        operator.base_image_path = '/path/to/base.qcow2'

        disk_param = {
            'path': '/var/lib/libvirt/images/vm.qcow2',
            'size': 20,
            'format': 'qcow2'
        }

        result = operator.build_system_disk(disk_param)

        # Should create files in normal mode
        self.assertEqual(result, disk_param)

        # File operations should be called
        self.mock_module.preserved_copy.assert_called_once()
        mock_qemu_tool.resize.assert_called_once()

    def test_validate_checksum_check_mode_no_file(self):
        """Test validate_checksum with check_mode when file doesn't exist"""
        self.mock_module.check_mode = True

        operator = BaseImageOperator(
            self.mock_module,
            'https://example.com/image.qcow2',
            image_checksum='sha256:abc123def456'
        )
        operator.base_image_path = '/path/to/nonexistent/image.qcow2'

        # Should return True in check_mode when file doesn't exist
        result = operator.validate_checksum()
        self.assertTrue(result)

    @mock.patch('os.path.exists')
    def test_validate_checksum_check_mode_file_exists(self, mock_exists):
        """Test validate_checksum with check_mode when file exists locally"""
        self.mock_module.check_mode = True
        mock_exists.return_value = True
        self.mock_module.digest_from_file.return_value = 'abc123def456'

        operator = BaseImageOperator(
            self.mock_module,
            '/path/to/local/image.qcow2',
            image_checksum='sha256:abc123def456'
        )
        operator.base_image_path = '/path/to/local/image.qcow2'

        # Should perform actual validation in check_mode when file exists
        result = operator.validate_checksum()
        self.assertTrue(result)
        self.mock_module.digest_from_file.assert_called_once()

    @mock.patch('os.path.exists')
    def test_validate_checksum_normal_mode(self, mock_exists):
        """Test validate_checksum with normal mode"""
        self.mock_module.check_mode = False
        mock_exists.return_value = False  # File doesn't exist

        # Make fail_json raise an exception
        self.mock_module.fail_json.side_effect = Exception(
            "Base image path not found for checksum validation")

        operator = BaseImageOperator(
            self.mock_module,
            'https://example.com/image.qcow2',
            image_checksum='sha256:abc123def456'
        )
        operator.base_image_path = '/path/to/nonexistent/image.qcow2'

        # Should fail in normal mode when file doesn't exist
        with self.assertRaises(Exception):
            operator.validate_checksum()

        self.mock_module.fail_json.assert_called()


class TestCore(unittest.TestCase):
    """Test core() function"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_module = mock.Mock()
        self.mock_module.check_mode = False

        # Default successful params
        self.mock_module.params = {
            'state': 'present',
            'name': 'test-vm',
            'recreate': False,
            'base_image': 'https://example.com/image.qcow2',
            'image_cache_dir': '/tmp/cache',
            'force_pull': False,
            'force_disk': False,
            'disks': [{'path': '/var/lib/libvirt/images/test.qcow2', 'size': 20}],
            'image_checksum': None,
            'url_timeout': None,
            'wait_for_cloud_init_reboot': True,
            'cloud_init_auto_reboot': True,
            'cloud_init_reboot_timeout': 600
        }

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.BaseImageOperator')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.LibvirtWrapper')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.validate_disks')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.update_virtinst_params')
    def test_core_vm_not_exists_create_success(self, mock_update_params, mock_validate_disks,
                                               mock_libvirt_wrapper_class, mock_virt_install_class,
                                               mock_base_image_operator_class):
        """Test core() when VM doesn't exist and creation succeeds"""
        from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import core, VIRT_SUCCESS
        from ansible_collections.community.libvirt.plugins.module_utils.libvirt import VMNotFound

        # Mock LibvirtWrapper - VM doesn't exist
        mock_virt_conn = mock.Mock()
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")
        mock_libvirt_wrapper_class.return_value = mock_virt_conn

        # Mock VirtInstallTool
        mock_virt_install = mock.Mock()
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, {'some': 'data'})
        mock_virt_install_class.return_value = mock_virt_install

        # Mock BaseImageOperator
        mock_operator = mock.Mock()
        mock_operator.validate_checksum.return_value = True
        mock_operator.build_system_disk.return_value = {
            'path': '/var/lib/libvirt/images/test.qcow2'}
        mock_base_image_operator_class.return_value = mock_operator

        # Execute core function
        rc, result = core(self.mock_module)

        # Verify behavior
        mock_validate_disks.assert_called_once()
        mock_virt_conn.find_vm.assert_called_once_with('test-vm')
        mock_operator.fetch_image.assert_called_once_with(False, timeout=None)
        mock_operator.validate_checksum.assert_called_once()
        mock_operator.build_system_disk.assert_called_once()
        mock_update_params.assert_called_once()
        mock_virt_install.execute.assert_called_once_with(dryrun=False, wait_timeout=600)

        # VM should not be destroyed (doesn't exist)
        mock_virt_conn.destroy.assert_not_called()
        mock_virt_conn.undefine.assert_not_called()

        # Should return success
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])
        self.assertEqual(result['some'], 'data')

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.BaseImageOperator')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.LibvirtWrapper')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.validate_disks')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.update_virtinst_params')
    def test_core_vm_exists_no_recreate(self, mock_update_params, mock_validate_disks,
                                        mock_libvirt_wrapper_class, mock_virt_install_class,
                                        mock_base_image_operator_class):
        """Test core() when VM exists and recreate=False"""
        from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import core, VIRT_SUCCESS

        # Mock LibvirtWrapper - VM exists
        mock_virt_conn = mock.Mock()
        mock_vm = mock.Mock()
        mock_virt_conn.find_vm.return_value = mock_vm
        mock_libvirt_wrapper_class.return_value = mock_virt_conn

        # Mock VirtInstallTool (shouldn't be called)
        mock_virt_install = mock.Mock()
        mock_virt_install_class.return_value = mock_virt_install

        # Execute core function
        rc, result = core(self.mock_module)

        # Verify behavior
        mock_validate_disks.assert_called_once()
        mock_virt_conn.find_vm.assert_called_once_with('test-vm')

        # Should not proceed with VM creation
        mock_base_image_operator_class.assert_not_called()
        mock_virt_install.execute.assert_not_called()
        mock_virt_conn.destroy.assert_not_called()
        mock_virt_conn.undefine.assert_not_called()

        # Should return success with message
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertFalse(result['changed'])
        self.assertIn("already exists", result['message'])

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.BaseImageOperator')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.LibvirtWrapper')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.validate_disks')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.update_virtinst_params')
    def test_core_vm_exists_recreate_active(self, mock_update_params, mock_validate_disks,
                                            mock_libvirt_wrapper_class, mock_virt_install_class,
                                            mock_base_image_operator_class):
        """Test core() when VM exists, recreate=True, and VM is active"""
        from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import core, VIRT_SUCCESS

        # Set recreate to True
        self.mock_module.params['recreate'] = True

        # Mock LibvirtWrapper - VM exists and is active
        mock_virt_conn = mock.Mock()
        mock_vm = mock.Mock()
        mock_vm.isActive.return_value = True
        mock_virt_conn.find_vm.return_value = mock_vm
        mock_libvirt_wrapper_class.return_value = mock_virt_conn

        # Mock VirtInstallTool
        mock_virt_install = mock.Mock()
        mock_virt_install.execute.return_value = (True, VIRT_SUCCESS, {})
        mock_virt_install_class.return_value = mock_virt_install

        # Mock BaseImageOperator
        mock_operator = mock.Mock()
        mock_operator.validate_checksum.return_value = True
        mock_operator.build_system_disk.return_value = {
            'path': '/var/lib/libvirt/images/test.qcow2'}
        mock_base_image_operator_class.return_value = mock_operator

        # Execute core function
        rc, result = core(self.mock_module)

        # Verify VM destruction and recreation
        mock_virt_conn.find_vm.assert_called_once_with('test-vm')
        mock_virt_conn.destroy.assert_called_once_with('test-vm')
        mock_virt_conn.undefine.assert_called_once_with('test-vm')

        # Verify VM recreation
        mock_operator.fetch_image.assert_called_once()
        mock_operator.validate_checksum.assert_called_once()
        mock_operator.build_system_disk.assert_called_once()
        mock_virt_install.execute.assert_called_once_with(dryrun=False, wait_timeout=600)

        # Should return success
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.BaseImageOperator')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.LibvirtWrapper')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.validate_disks')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.update_virtinst_params')
    def test_core_vm_exists_recreate_inactive(self, mock_update_params, mock_validate_disks,
                                              mock_libvirt_wrapper_class, mock_virt_install_class,
                                              mock_base_image_operator_class):
        """Test core() when VM exists, recreate=True, and VM is inactive"""
        from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import core, VIRT_SUCCESS

        # Set recreate to True
        self.mock_module.params['recreate'] = True

        # Mock LibvirtWrapper - VM exists but is inactive
        mock_virt_conn = mock.Mock()
        mock_vm = mock.Mock()
        mock_vm.isActive.return_value = False
        mock_virt_conn.find_vm.return_value = mock_vm
        mock_libvirt_wrapper_class.return_value = mock_virt_conn

        # Mock VirtInstallTool
        mock_virt_install = mock.Mock()
        mock_virt_install.execute.return_value = (True, VIRT_SUCCESS, {})
        mock_virt_install_class.return_value = mock_virt_install

        # Mock BaseImageOperator
        mock_operator = mock.Mock()
        mock_operator.validate_checksum.return_value = True
        mock_operator.build_system_disk.return_value = {
            'path': '/var/lib/libvirt/images/test.qcow2'}
        mock_base_image_operator_class.return_value = mock_operator

        # Execute core function
        rc, result = core(self.mock_module)

        # Verify behavior - should not destroy (inactive), but should undefine
        mock_virt_conn.destroy.assert_not_called()  # VM is inactive
        mock_virt_conn.undefine.assert_called_once_with('test-vm')

        # Should return success
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.LibvirtWrapper')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.validate_disks')
    def test_core_missing_name(self, mock_validate_disks, mock_libvirt_wrapper_class, mock_virt_install_class):
        """Test core() fails when VM name is missing"""
        from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import core

        # Mock the module.run_command for LibvirtConnection
        self.mock_module.run_command.return_value = (0, 'kernel-version', '')

        # Remove name from params
        self.mock_module.params['name'] = None

        # Execute core function
        core(self.mock_module)

        # Should fail with appropriate message
        self.mock_module.fail_json.assert_called_once_with(
            msg="virtual machine name is missing")

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.LibvirtWrapper')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.validate_disks')
    def test_core_missing_base_image(self, mock_validate_disks, mock_libvirt_wrapper_class, mock_virt_install_class):
        """Test core() fails when base_image is missing"""
        from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import core

        # Mock the module.run_command for LibvirtConnection
        self.mock_module.run_command.return_value = (0, 'kernel-version', '')

        # Remove base_image from params
        self.mock_module.params['base_image'] = None

        # Execute core function
        core(self.mock_module)

        # Should fail with appropriate message
        self.mock_module.fail_json.assert_called_once_with(
            msg="base_image parameter is required")

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.BaseImageOperator')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.LibvirtWrapper')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.validate_disks')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.update_virtinst_params')
    def test_core_checksum_validation_fails(self, mock_update_params, mock_validate_disks, mock_libvirt_wrapper_class,
                                            mock_virt_install_class, mock_base_image_operator_class):
        """Test core() fails when checksum validation fails"""
        from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import core
        from ansible_collections.community.libvirt.plugins.module_utils.libvirt import VMNotFound

        # Mock LibvirtWrapper - VM doesn't exist
        mock_virt_conn = mock.Mock()
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")
        mock_libvirt_wrapper_class.return_value = mock_virt_conn

        # Mock VirtInstallTool (shouldn't be used due to checksum failure)
        mock_virt_install = mock.Mock()
        mock_virt_install.params = {
            'disks': [{'path': '/tmp/placeholder.qcow2'}]}
        mock_virt_install_class.return_value = mock_virt_install

        # Mock BaseImageOperator - checksum validation fails
        mock_operator = mock.Mock()
        mock_operator.validate_checksum.return_value = False
        mock_base_image_operator_class.return_value = mock_operator

        # Configure fail_json to raise exception (as it should in real code)
        self.mock_module.fail_json.side_effect = Exception("Module failed")

        # Execute core function - should raise exception due to checksum failure
        with self.assertRaises(Exception):
            core(self.mock_module)

        # Should fail with checksum error
        self.mock_module.fail_json.assert_called_once_with(
            msg="The checksum of the base image does not match the expected value")

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.LibvirtWrapper')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.validate_disks')
    def test_core_unsupported_state(self, mock_validate_disks, mock_libvirt_wrapper_class, mock_virt_install_class):
        """Test core() fails with unsupported state"""
        from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import core

        # Mock the module.run_command for LibvirtConnection
        self.mock_module.run_command.return_value = (0, 'kernel-version', '')

        # Set unsupported state
        self.mock_module.params['state'] = 'destroy'

        # Execute core function
        core(self.mock_module)

        # Should fail with unsupported state message
        self.mock_module.fail_json.assert_called_once_with(
            msg="unsupported state 'destroy'")

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.BaseImageOperator')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.LibvirtWrapper')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.validate_disks')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.update_virtinst_params')
    def test_core_check_mode_vm_recreation(self, mock_update_params, mock_validate_disks,
                                           mock_libvirt_wrapper_class, mock_virt_install_class,
                                           mock_base_image_operator_class):
        """Test core() in check_mode when recreating VM"""
        from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import core, VIRT_SUCCESS

        # Enable check_mode and recreate
        self.mock_module.check_mode = True
        self.mock_module.params['recreate'] = True

        # Mock LibvirtWrapper - VM exists and is active
        mock_virt_conn = mock.Mock()
        mock_vm = mock.Mock()
        mock_vm.isActive.return_value = True
        mock_virt_conn.find_vm.return_value = mock_vm
        mock_libvirt_wrapper_class.return_value = mock_virt_conn

        # Mock VirtInstallTool
        mock_virt_install = mock.Mock()
        mock_virt_install.execute.return_value = (True, VIRT_SUCCESS, {})
        mock_virt_install_class.return_value = mock_virt_install

        # Mock BaseImageOperator
        mock_operator = mock.Mock()
        mock_operator.validate_checksum.return_value = True
        mock_operator.build_system_disk.return_value = {
            'path': '/var/lib/libvirt/images/test.qcow2'}
        mock_base_image_operator_class.return_value = mock_operator

        # Execute core function
        rc, result = core(self.mock_module)

        # In check_mode, VM should NOT be destroyed or undefined
        mock_virt_conn.destroy.assert_not_called()
        mock_virt_conn.undefine.assert_not_called()

        # But virt-install should be called with dryrun=True
        mock_virt_install.execute.assert_called_once_with(dryrun=True, wait_timeout=600)

        # Should still return success
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.BaseImageOperator')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.LibvirtWrapper')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.validate_disks')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.update_virtinst_params')
    def test_core_force_disk_passed_to_build_system_disk(self, mock_update_params, mock_validate_disks,
                                                         mock_libvirt_wrapper_class, mock_virt_install_class,
                                                         mock_base_image_operator_class):
        """Test that force_disk parameter is passed to build_system_disk"""
        from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import core, VIRT_SUCCESS
        from ansible_collections.community.libvirt.plugins.module_utils.libvirt import VMNotFound

        # Set force_disk to True
        self.mock_module.params['force_disk'] = True

        # Mock LibvirtWrapper - VM doesn't exist
        mock_virt_conn = mock.Mock()
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")
        mock_libvirt_wrapper_class.return_value = mock_virt_conn

        # Mock VirtInstallTool
        mock_virt_install = mock.Mock()
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, {'some': 'data'})
        mock_virt_install_class.return_value = mock_virt_install

        # Mock BaseImageOperator
        mock_operator = mock.Mock()
        mock_operator.validate_checksum.return_value = True
        mock_operator.build_system_disk.return_value = {
            'path': '/var/lib/libvirt/images/test.qcow2'}
        mock_base_image_operator_class.return_value = mock_operator

        # Execute core function
        rc, result = core(self.mock_module)

        # Verify force_disk=True was passed to build_system_disk
        mock_operator.build_system_disk.assert_called_once_with(
            {'path': '/var/lib/libvirt/images/test.qcow2', 'size': 20},
            force_disk=True
        )

        # Should return success
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])

    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.BaseImageOperator')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.VirtInstallTool')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.LibvirtWrapper')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.validate_disks')
    @mock.patch('ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance.update_virtinst_params')
    def test_core_force_disk_false_passed_to_build_system_disk(self, mock_update_params, mock_validate_disks,
                                                               mock_libvirt_wrapper_class, mock_virt_install_class,
                                                               mock_base_image_operator_class):
        """Test that force_disk=False parameter is passed to build_system_disk"""
        from ansible_collections.community.libvirt.plugins.modules.virt_cloud_instance import core, VIRT_SUCCESS
        from ansible_collections.community.libvirt.plugins.module_utils.libvirt import VMNotFound

        # Ensure force_disk is False (default)
        self.mock_module.params['force_disk'] = False

        # Mock LibvirtWrapper - VM doesn't exist
        mock_virt_conn = mock.Mock()
        mock_virt_conn.find_vm.side_effect = VMNotFound("VM not found")
        mock_libvirt_wrapper_class.return_value = mock_virt_conn

        # Mock VirtInstallTool
        mock_virt_install = mock.Mock()
        mock_virt_install.execute.return_value = (
            True, VIRT_SUCCESS, {'some': 'data'})
        mock_virt_install_class.return_value = mock_virt_install

        # Mock BaseImageOperator
        mock_operator = mock.Mock()
        mock_operator.validate_checksum.return_value = True
        mock_operator.build_system_disk.return_value = {
            'path': '/var/lib/libvirt/images/test.qcow2'}
        mock_base_image_operator_class.return_value = mock_operator

        # Execute core function
        rc, result = core(self.mock_module)

        # Verify force_disk=False was passed to build_system_disk
        mock_operator.build_system_disk.assert_called_once_with(
            {'path': '/var/lib/libvirt/images/test.qcow2', 'size': 20},
            force_disk=False
        )

        # Should return success
        self.assertEqual(rc, VIRT_SUCCESS)
        self.assertTrue(result['changed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
