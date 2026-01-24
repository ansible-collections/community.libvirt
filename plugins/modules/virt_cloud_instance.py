#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2025, Joey Zhang <thinkdoggie@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: virt_cloud_instance
version_added: 2.1.0
author: "Joey Zhang (@thinkdoggie)"
short_description: Provision new virtual machines from cloud images via libvirt
description:
  - Create and customize virtual machines using pre-built cloud images with cloud-init support.
  - Cloud images can be retrieved from local files and remote URLs.
  - Supports automatic conversion and resizing of disk images.
options:
  name:
    type: str
    description:
      - Name of the new guest virtual machine instance.
    required: true
  state:
    choices: [ present, absent ]
    type: str
    description:
      - If set to V(present), create the VM if it does not exist.
    default: present
  recreate:
    type: bool
    description:
      - Use with present to force the re-creation of an existing VM.
    default: false
  base_image:
    type: str
    description:
      - Path or URL to the cloud image.
      - Can be a local file path or a remote URL (http, https, ftp).
      - The image will be automatically downloaded if a URL is provided.
    required: true
  image_cache_dir:
    type: path
    description:
      - Directory where downloaded cloud images will be cached.
      - Only used when O(base_image) is a URL.
      - If not specified, the base image will be downloaded to the temporary directory and not be cached.
  force_pull:
    type: bool
    description:
      - Force pull of the cloud image even if it already exists in the cache.
      - Only used when O(base_image) is a URL.
      - Useful for updating cached images to their latest versions.
    default: false
  force_disk:
    type: bool
    description:
      - Force deletion and recreation of existing disk files.
      - When set to V(true), any existing disk files specified in O(disks) will be removed and recreated.
      - When set to V(false), the module will fail if any disk file already exists.
      - This parameter only affects disk file creation, not VM definition.
      - Use with O(recreate=true) to recreate both the VM and its disk files.
    default: false
  image_checksum:
    type: str
    description:
      - If specified, the digest of the downloaded image will be calculated to verify the integrity of the downloaded image.
      - "Format: <algorithm>:<checksum|url>, e.g. I(sha256:D98291AC[...]B6DC7B97), I(sha256:http://example.com/path/sha256sum.txt)."
      - Only used when O(base_image) is a URL.
      - If you worry about portability, only the sha1 algorithm is available on all platforms and python versions.
  url_timeout:
    type: int
    default: 60
    description:
      - The timeout in seconds for downloading the base image from a URL.
      - Only used when O(base_image) is a URL.
  url_username:
    type: str
    description:
      - The username for HTTP basic authentication.
      - Only used when O(base_image) is a URL.
  url_password:
    type: str
    description:
      - The password for HTTP basic authentication.
      - Only used when O(base_image) is a URL.
  wait_for_cloud_init_reboot:
    type: bool
    default: true
    description:
      - If set to V(true), wait for cloud-init to trigger a reboot and for the VM to come back online.
      - This requires that your cloud-init user-data includes a reboot action, or I(cloud_init_auto_reboot=true).
      - Only applicable when O(cloud_init) configuration is provided.
  cloud_init_auto_reboot:
    type: bool
    default: true
    description:
      - When I(wait_for_cloud_init_reboot=true), automatically inject a reboot instruction into the cloud-init user-data.
      - If set to V(false), the reboot instructions should be included in the cloud-init user-data manually.
      - Only applies when I(wait_for_cloud_init_reboot=true).
  cloud_init_reboot_timeout:
    type: int
    default: 600
    description:
      - Maximum time in seconds to wait for the cloud-init reboot cycle to complete.
      - The timeout is checked at minute intervals, so the actual timeout may be up to 60 seconds longer.
      - Only applies when I(wait_for_cloud_init_reboot=true).
      - If the timeout is exceeded, the task will fail.
extends_documentation_fragment:
    - community.libvirt.virt.options_uri
    - community.libvirt.virt_install.options_cloud_init
    - community.libvirt.virt_install.options_memory
    - community.libvirt.virt_install.options_memorybacking
    - community.libvirt.virt_install.options_arch
    - community.libvirt.virt_install.options_machine
    - community.libvirt.virt_install.options_metadata
    - community.libvirt.virt_install.options_events
    - community.libvirt.virt_install.options_resource
    - community.libvirt.virt_install.options_sysinfo
    - community.libvirt.virt_install.options_qemu_commandline
    - community.libvirt.virt_install.options_vcpus
    - community.libvirt.virt_install.options_numatune
    - community.libvirt.virt_install.options_memtune
    - community.libvirt.virt_install.options_blkiotune
    - community.libvirt.virt_install.options_cpu
    - community.libvirt.virt_install.options_cputune
    - community.libvirt.virt_install.options_security
    - community.libvirt.virt_install.options_keywrap
    - community.libvirt.virt_install.options_iothreads
    - community.libvirt.virt_install.options_features
    - community.libvirt.virt_install.options_clock
    - community.libvirt.virt_install.options_pm
    - community.libvirt.virt_install.options_launch_security
    - community.libvirt.virt_install.options_boot
    - community.libvirt.virt_install.options_osinfo
    - community.libvirt.virt_install.options_disks
    - community.libvirt.virt_install.options_filesystems
    - community.libvirt.virt_install.options_networks
    - community.libvirt.virt_install.options_graphics_devices
    - community.libvirt.virt_install.options_virt_type
    - community.libvirt.virt_install.options_hvm
    - community.libvirt.virt_install.options_paravirt
    - community.libvirt.virt_install.options_controller_devices
    - community.libvirt.virt_install.options_input_devices
    - community.libvirt.virt_install.options_host_devices
    - community.libvirt.virt_install.options_sound_devices
    - community.libvirt.virt_install.options_audio_devices
    - community.libvirt.virt_install.options_watchdog_devices
    - community.libvirt.virt_install.options_serial_devices
    - community.libvirt.virt_install.options_parallel_devices
    - community.libvirt.virt_install.options_channel_devices
    - community.libvirt.virt_install.options_console_devices
    - community.libvirt.virt_install.options_video_devices
    - community.libvirt.virt_install.options_smartcard_devices
    - community.libvirt.virt_install.options_redirected_devices
    - community.libvirt.virt_install.options_memballoon_devices
    - community.libvirt.virt_install.options_tpm_devices
    - community.libvirt.virt_install.options_rng_devices
    - community.libvirt.virt_install.options_panic_devices
    - community.libvirt.virt_install.options_shmem_devices
    - community.libvirt.virt_install.options_vsock_devices
    - community.libvirt.virt_install.options_iommu_devices
    - community.libvirt.virt_install.options_autostart
    - community.libvirt.requirements
attributes:
    check_mode:
        description: Supports check_mode.
        support: full
requirements:
    - "virt-install"
    - "qemu-img"
notes:
    - The C(virt-install) command is provided by different packages on different distributions.
    - On Debian/Ubuntu, install the C(virtinst) package.
    - On RHEL/CentOS/Fedora and openSUSE, install the C(virt-install) package.
    - When O(wait_for_cloud_init_reboot=true), ensure your cloud-init user-data includes appropriate reboot commands or set O(cloud_init_auto_reboot=true).
    - The O(cloud_init_auto_reboot) parameter automatically injects I(power_state.mode=reboot) at the end of user-data when enabled.
    - The module waits through the complete cloud-init process including any reboots specified in the user-data.
    - Use O(cloud_init_reboot_timeout) to control the maximum wait time for complex cloud-init configurations.
seealso:
  - module: community.libvirt.virt_install
    description: More general VM installation module.
  - name: virt-install Man Page
    description: Ubuntu manpage of virt-install tool.
    link: https://manpages.ubuntu.com/manpages/focal/man1/virt-install.1.html
"""


EXAMPLES = """
# Basic example: Create a VM from a local cloud image
- name: Create Ubuntu VM from local cloud image
  community.libvirt.virt_cloud_instance:
    name: ubuntu-vm-01
    base_image: /srv/images/ubuntu-22.04-server-cloudimg-amd64.img
    disks:
      - path: /var/lib/libvirt/images/ubuntu-vm-01.qcow2
        size: 20
        format: qcow2
    memory: 2048
    vcpus: 2
    networks:
      - network: default

# Download cloud image from URL with checksum validation
- name: Create VM from remote Ubuntu cloud image
  community.libvirt.virt_cloud_instance:
    name: ubuntu-vm-02
    base_image: https://cloud-images.ubuntu.com/releases/22.04/release/ubuntu-22.04-server-cloudimg-amd64.img
    image_cache_dir: /srv/cloud-images
    image_checksum: sha256:https://cloud-images.ubuntu.com/releases/22.04/release/SHA256SUMS
    disks:
      - path: /var/lib/libvirt/images/ubuntu-vm-02.qcow2
        size: 30
        format: qcow2
    memory: 4096
    vcpus: 4
    networks:
      - network: default

# Advanced example with cloud-init configuration
- name: Create VM with cloud-init user data
  community.libvirt.virt_cloud_instance:
    name: web-server-01
    base_image: /srv/images/ubuntu-22.04-server-cloudimg-amd64.img
    disks:
      - path: /var/lib/libvirt/images/web-server-01.qcow2
        size: 50
        format: qcow2
    memory: 8192
    vcpus: 4
    networks:
      - network: default
        mac: 52:54:00:12:34:56
    cloud_init:
      user_data: |
        #cloud-config
        users:
          - name: ansible
            groups: sudo
            shell: /bin/bash
            sudo: 'ALL=(ALL) NOPASSWD:ALL'
            ssh_authorized_keys:
              - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB... user@host
        packages:
          - nginx
          - htop
          - vim
        runcmd:
          - systemctl enable nginx
          - systemctl start nginx
      meta_data:
        instance-id: web-server-01
        local-hostname: web-server-01

# Force overwrite existing disk files
- name: Create VM and force overwrite existing disk
  community.libvirt.virt_cloud_instance:
    name: test-vm
    base_image: /srv/images/ubuntu-22.04-server-cloudimg-amd64.img
    force_disk: true
    disks:
      - path: /var/lib/libvirt/images/test-vm.qcow2
        size: 20
        format: qcow2
    memory: 2048
    vcpus: 2
    networks:
      - network: default
"""

RETURN = r"""
base_image_path:
    description:
        - Path to the base cloud image file.
        - This is the local path where the image was downloaded to (if URL was provided) or the original local path.
    type: str
    returned: success
    sample: "/srv/cloud-images/ubuntu-20.04-server-cloudimg-amd64.img"
"""


import os
import re
from urllib.parse import urlparse
from ansible_collections.community.libvirt.plugins.module_utils import virt_install as virtinst_util
from ansible_collections.community.libvirt.plugins.module_utils.virt_install import (
    LibvirtWrapper, VirtInstallTool
)
from ansible_collections.community.libvirt.plugins.module_utils.libvirt import (
    HAS_VIRT, HAS_XML, VMNotFound, VIRT_SUCCESS
)
from ansible_collections.community.libvirt.plugins.module_utils.qemu import QemuImgTool
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_file, fetch_url


class BaseImageOperator(object):
    def __init__(self, module, base_image, image_cache_dir=None, image_checksum=None):
        self.module = module
        self.base_image = base_image
        self.image_cache_dir = image_cache_dir
        self.image_checksum = image_checksum
        self.base_image_path = None
        self.system_disk_path = None

    def fetch_image(self, force_pull, timeout=None):
        """
        Fetch cloud image from URL or use local file.

        This operation may download and create files, so it respects check_mode.
        In check_mode, image download is skipped but local files are still validated.
        """
        parsed_url = urlparse(self.base_image)

        if parsed_url.scheme not in ('http', 'https', 'ftp'):
            # The base image is a local file path
            if not os.path.exists(self.base_image):
                self.module.fail_json(
                    msg="Base image file does not exist: %s" % self.base_image)
            self.base_image_path = self.base_image
            return self.base_image_path

        filename = os.path.basename(parsed_url.path)
        if not filename:
            self.module.fail_json(
                msg="Failed to determine filename from base image URL: %s" % self.base_image)

        if self.image_cache_dir:
            image_path = os.path.join(self.image_cache_dir, filename)
            if os.path.exists(image_path) and not force_pull:
                self.base_image_path = image_path
                return self.base_image_path
        else:
            image_path = os.path.join(self.module.tmpdir, filename)

        # Check if we're in check mode
        if self.module.check_mode:
            # In check mode, don't download but set the expected path
            self.base_image_path = image_path
            return self.base_image_path

        temp_file = fetch_file(self.module, self.base_image, timeout=timeout)
        self.module.atomic_move(temp_file, image_path)

        self.base_image_path = image_path
        return self.base_image_path

    def _resolve_system_disk(self, disk_param):
        # TODO: Support specifying the system disk as a pool volume

        if not disk_param.get('path'):
            raise ValueError(
                "The first disk must have a path to import the cloud image")

        self.system_disk_path = disk_param.get('path')

        return disk_param

    def validate_checksum(self):
        """
        Validate the checksum of the base image.

        This operation is read-only but depends on the actual file.
        In check_mode, validation is skipped if the file doesn't exist locally.
        """
        if not self.image_checksum:
            return True

        # In check_mode, skip validation if file doesn't exist
        # (e.g., when base_image is a URL that wasn't downloaded)
        if self.module.check_mode and (not self.base_image_path or not os.path.exists(self.base_image_path)):
            return True  # Assume validation would pass in check_mode

        if not self.base_image_path or not os.path.exists(self.base_image_path):
            self.module.fail_json(
                msg="Base image path not found for checksum validation")

        # Parse checksum format: <algorithm>:<checksum|url>
        try:
            algorithm, checksum_expr = self.image_checksum.split(':', 1)
        except ValueError:
            self.module.fail_json(
                msg="The image_checksum parameter has to be in format <algorithm>:<checksum>")

        # Check if checksum is a URL
        parsed_url = urlparse(checksum_expr)
        if parsed_url.scheme in ('http', 'https', 'ftp'):
            checksum = self._fetch_checksum_from_url(checksum_expr, algorithm)
        else:
            checksum = checksum_expr

        # Remove any non-alphanumeric characters and convert to lowercase
        checksum = re.sub(r'\W+', '', checksum).lower()

        # Ensure the checksum portion is a hexdigest
        try:
            int(checksum, 16)
        except ValueError:
            self.module.fail_json(msg='The checksum format is invalid')

        # Calculate the actual checksum of the file
        actual_checksum = None
        try:
            actual_checksum = self.module.digest_from_file(
                self.base_image_path, algorithm)
        except ValueError as e:
            self.module.fail_json(
                msg="Failed to calculate the actual checksum of the file: %s" % str(e))

        # Compare checksums
        return checksum == actual_checksum

    def _fetch_checksum_from_url(self, checksum_url, algorithm):
        # Download checksum file
        response, info = fetch_url(self.module, checksum_url, timeout=60)
        if response is None:
            self.module.fail_json(msg="Failed to download checksum from %s: %s" % (
                checksum_url, info.get('msg', 'Unknown error')))

        try:
            checksum_content = response.read().decode('utf-8')
        finally:
            response.close()

        lines = [line.rstrip('\n') for line in checksum_content.splitlines()]
        checksum_map = []

        # Get the filename from the base image URL for matching
        filename = os.path.basename(urlparse(self.base_image).path)

        if len(lines) == 1 and len(lines[0].split()) == 1:
            # Only a single line with a single string - treat it as a checksum only file
            checksum_map.append((lines[0], filename))
        else:
            # The file is in the format of "checksum filename"
            for line in lines:
                # Split by one whitespace to keep the leading type char ' ' (whitespace) for text and '*' for binary
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    # Remove the leading type char if present
                    if parts[1].startswith((" ", "*")):
                        parts[1] = parts[1][1:]

                    # Append checksum and path without potential leading './'
                    checksum_map.append((parts[0], parts[1].lstrip("./")))

        # Look through each line in the checksum file for a hash corresponding to
        # the filename in the url, returning the first hash that is found.
        for cksum in (s for (s, f) in checksum_map if f == filename):
            return cksum

        self.module.fail_json(
            msg="Unable to find a checksum for file '%s' in '%s'" % (filename, checksum_url))

    def build_system_disk(self, disk_param, force_disk=False):
        """
        Build system disk from base image.

        This operation creates and modifies disk files, so it respects check_mode.
        In check_mode, validation is performed but no files are created or modified.

        Args:
            disk_param: Disk configuration dictionary
            force_disk: If True, remove existing disk file before creating new one
        """
        system_disk = self._resolve_system_disk(disk_param)
        disk_path = self.system_disk_path
        base_image_path = self.base_image_path

        if os.path.exists(disk_path):
            if force_disk:
                # In check_mode, don't actually delete the file
                if not self.module.check_mode:
                    os.remove(disk_path)
                    self.module.log("Removed existing disk file: %s" % disk_path)
            else:
                self.module.fail_json(
                    msg="The system disk file already exists: %s" % disk_path)

        qemuImgTool = QemuImgTool(self.module)

        # Get base image info - this is read-only and should work in check_mode
        # However, if we're in check_mode and the base image doesn't exist locally,
        # we may need to skip this check
        if self.module.check_mode and not os.path.exists(base_image_path):
            # In check mode with non-existent base image, create mock info for validation
            base_image_format = "qcow2"  # Assume common format
            base_image_raw_size = 1 * 1024 * 1024 * 1024  # Assume 1GB minimum
        else:
            rc, image_info, stderr = qemuImgTool.info(base_image_path)
            if rc != 0:
                self.module.fail_json(
                    msg="Failed to get base image info: %s" % stderr)
            base_image_format = image_info.get('format')
            base_image_raw_size = image_info.get('virtual-size')

        system_disk_format = system_disk.get('format', "qcow2")
        system_disk_size = system_disk.get('size')
        if not base_image_format:
            self.module.fail_json(
                msg="No valid format found for the base image: %s" % base_image_path)
        if not system_disk_size or not isinstance(system_disk_size, int):
            self.module.fail_json(
                msg="The system disk size must be an integer")
        system_disk_raw_size = system_disk_size * 1024 * 1024 * 1024
        if system_disk_raw_size < base_image_raw_size:
            self.module.fail_json(msg="The system disk size is too small to import the base image: %s < %s" % (
                system_disk_raw_size, base_image_raw_size))

        # Check if we're in check mode
        if self.module.check_mode:
            # In check mode, don't create files but return the disk configuration
            return system_disk

        if base_image_format != system_disk_format:
            rc, stdout, stderr = qemuImgTool.convert(
                base_image_path, disk_path, source_format=base_image_format, output_format=system_disk_format)
            if rc != 0:
                self.module.fail_json(
                    msg="Failed to convert base image to system disk: %s" % stderr)
        else:
            self.module.preserved_copy(base_image_path, disk_path)

        rc, stdout, stderr = qemuImgTool.resize(
            disk_path, "%dG" % system_disk_size)
        if rc != 0:
            self.module.fail_json(
                msg="Failed to resize system disk: %s" % stderr)

        for key in ['format', 'size']:
            if key in system_disk:
                del system_disk[key]

        return system_disk


def validate_disks(disks):
    if not isinstance(disks, list) \
            or len(disks) < 1:
        raise ValueError("At least one disk is required")

    system_disk = disks[0]

    if not (system_disk.get('path') or system_disk.get('pool')):
        raise ValueError(
            "The first disk must have either 'path' or 'pool' to import the cloud image")

    if not system_disk.get('size'):
        raise ValueError("The first disk must have a size")


def update_virtinst_params(module, virtInstall, system_disk, extra_user_data=None):
    disks = virtInstall.params.get('disks')

    if not isinstance(disks, list) \
            or len(disks) < 1:
        raise ValueError("At least one disk is required")

    virtInstall.params['disks'][0] = system_disk
    virtInstall.params['import'] = True

    if extra_user_data:
        if virtInstall.params.get('cloud_init') is None:
            virtInstall.params['cloud_init'] = {}

        orignal_user_data = virtInstall.params['cloud_init'].get('user_data', "")

        if isinstance(orignal_user_data, dict):
            try:
                import yaml
                orignal_user_data = yaml.safe_dump(orignal_user_data, default_flow_style=False, allow_unicode=True)
            except ImportError:
                module.fail_json(
                    msg="PyYAML is required to process dictionary cloud-init parameters")

        modified_user_data = orignal_user_data + extra_user_data
        virtInstall.params['cloud_init']['user_data'] = modified_user_data


def get_autoreboot_user_data():
    return """
# appended by virt_cloud_instance module
power_state:
  delay: 1
  mode: reboot
  message: Rebooting for cloud instance provisioning
"""


def core(module):
    state = module.params.get('state')
    name = module.params.get('name')
    recreate = module.params.get('recreate', False)
    base_image = module.params.get('base_image')
    image_cache_dir = module.params.get('image_cache_dir')
    force_pull = module.params.get('force_pull', False)
    force_disk = module.params.get('force_disk', False)
    disks = module.params.get('disks', [])
    image_checksum = module.params.get('image_checksum')
    url_timeout = module.params.get('url_timeout')
    wait_for_cloud_init_reboot = module.params.get('wait_for_cloud_init_reboot', True)
    cloud_init_auto_reboot = module.params.get('cloud_init_auto_reboot', True)
    cloud_init_reboot_timeout = module.params.get('cloud_init_reboot_timeout')

    validate_disks(disks)

    result = dict(
        changed=False,
        original_message="",
        message="",
        base_image_path="",
    )

    virtConn = LibvirtWrapper(module)
    virtInstall = VirtInstallTool(module)

    if not name:
        module.fail_json(msg="virtual machine name is missing")

    if not base_image:
        module.fail_json(msg="base_image parameter is required")

    vm_exists = False
    try:
        vm = virtConn.find_vm(name)
        vm_exists = True
    except VMNotFound:
        vm_exists = False

    if state == 'present':
        if vm_exists and not recreate:
            result['message'] = "virtual machine '%s' already exists" % name
            return VIRT_SUCCESS, result
        elif vm_exists and recreate:
            # In check_mode, skip VM destruction but continue with validation
            if not module.check_mode:
                if vm.isActive():
                    virtConn.destroy(name)
                virtConn.undefine(name)

        # Create image operator only when we need to process the image
        image_operator = BaseImageOperator(module, base_image,
                                           image_cache_dir=image_cache_dir,
                                           image_checksum=image_checksum)
        image_operator.fetch_image(force_pull, timeout=url_timeout)
        if not image_operator.validate_checksum():
            module.fail_json(
                msg="The checksum of the base image does not match the expected value")
        system_disk = image_operator.build_system_disk(disks[0], force_disk=force_disk)

        # Add base_image_path to result
        result['base_image_path'] = image_operator.base_image_path

        extra_user_data = None
        if wait_for_cloud_init_reboot and cloud_init_auto_reboot:
            extra_user_data = get_autoreboot_user_data()

        wait_timeout = None
        if wait_for_cloud_init_reboot:
            wait_timeout = cloud_init_reboot_timeout

        # run virt-install to create new vm
        update_virtinst_params(module, virtInstall, system_disk, extra_user_data)
        changed, rc, extra_res = virtInstall.execute(dryrun=module.check_mode, wait_timeout=wait_timeout)
        # result['virt_install_command'] = ' '.join(virtInstall.command_argv)
        result['changed'] = changed
        result.update(extra_res)

        if wait_for_cloud_init_reboot and rc == 0:
            virtConn.create(name)

        return rc, result
    elif state == 'absent':
        if not vm_exists:
            result['message'] = "virtual machine '%s' is already absent" % name
            return VIRT_SUCCESS, result

        if not module.check_mode:
            if vm.isActive():
                virtConn.destroy(name)
            virtConn.undefine(name)

        result["changed"] = True
        return VIRT_SUCCESS, result

    module.fail_json(msg="unsupported state '%s'" % state)


def main():
    """Main module entry point"""

    # Define argument specification
    argument_spec = dict(
        # Connection options
        uri=dict(type='str', default="qemu:///system"),
        # Basic VM options
        name=dict(type='str', required=True),
        state=dict(
            type='str',
            choices=['present', 'absent'],
            default='present'),
        recreate=dict(type='bool', default=False),
        # Cloud image specific options
        base_image=dict(type='str', required=True),
        image_cache_dir=dict(type='path'),
        force_pull=dict(type='bool', default=False),
        force_disk=dict(type='bool', default=False),
        image_checksum=dict(type='str'),
        url_timeout=dict(type='int', default=60),
        url_username=dict(type='str'),
        url_password=dict(type='str', no_log=True),
        wait_for_cloud_init_reboot=dict(type='bool', default=True),
        cloud_init_auto_reboot=dict(type='bool', default=True),
        cloud_init_reboot_timeout=dict(type='int', default=600),
    )

    # Cloud-init options
    argument_spec.update(virtinst_util.get_cloud_init_args())
    # General options
    argument_spec.update(virtinst_util.get_memory_args())
    argument_spec.update(virtinst_util.get_memorybacking_args())
    argument_spec.update(virtinst_util.get_arch_args())
    argument_spec.update(virtinst_util.get_machine_args())
    argument_spec.update(virtinst_util.get_metadata_args())
    argument_spec.update(virtinst_util.get_events_args())
    argument_spec.update(virtinst_util.get_resource_args())
    argument_spec.update(virtinst_util.get_sysinfo_args())
    argument_spec.update(virtinst_util.get_qmeu_commandline_args())
    argument_spec.update(virtinst_util.get_vcpu_args())
    argument_spec.update(virtinst_util.get_numatune_args())
    argument_spec.update(virtinst_util.get_memtune_args())
    argument_spec.update(virtinst_util.get_blkiotune_args())
    argument_spec.update(virtinst_util.get_cpu_args())
    argument_spec.update(virtinst_util.get_cputune_args())
    argument_spec.update(virtinst_util.get_security_args())
    argument_spec.update(virtinst_util.get_keywrap_args())
    argument_spec.update(virtinst_util.get_iothreads_args())
    argument_spec.update(virtinst_util.get_features_args())
    argument_spec.update(virtinst_util.get_clock_args())
    argument_spec.update(virtinst_util.get_pm_args())
    argument_spec.update(virtinst_util.get_launch_security_args())
    # Boot options
    argument_spec.update(virtinst_util.get_boot_args())
    # Guest OS options
    argument_spec.update(virtinst_util.get_osinfo_args())
    # Storage options
    argument_spec.update(virtinst_util.get_disks_args())
    argument_spec.update(virtinst_util.get_filesystems_args())
    # Network options
    argument_spec.update(virtinst_util.get_networks_args())
    # Graphics options
    argument_spec.update(virtinst_util.get_graphics_args())
    # Virtualization options
    argument_spec.update(virtinst_util.get_virt_type_args())
    argument_spec.update(virtinst_util.get_hvm_args())
    argument_spec.update(virtinst_util.get_paravirt_args())
    # Device options
    argument_spec.update(virtinst_util.get_controller_args())
    argument_spec.update(virtinst_util.get_input_args())
    argument_spec.update(virtinst_util.get_hostdev_args())
    argument_spec.update(virtinst_util.get_sound_args())
    argument_spec.update(virtinst_util.get_audio_args())
    argument_spec.update(virtinst_util.get_watchdog_args())
    argument_spec.update(virtinst_util.get_serial_args())
    argument_spec.update(virtinst_util.get_parallel_args())
    argument_spec.update(virtinst_util.get_channel_args())
    argument_spec.update(virtinst_util.get_console_args())
    argument_spec.update(virtinst_util.get_video_args())
    argument_spec.update(virtinst_util.get_smartcard_args())
    argument_spec.update(virtinst_util.get_redirdev_args())
    argument_spec.update(virtinst_util.get_memballoon_args())
    argument_spec.update(virtinst_util.get_tpm_args())
    argument_spec.update(virtinst_util.get_rng_args())
    argument_spec.update(virtinst_util.get_panic_args())
    argument_spec.update(virtinst_util.get_shmem_args())
    argument_spec.update(virtinst_util.get_vsock_args())
    argument_spec.update(virtinst_util.get_iommu_args())
    # Miscellaneous options
    argument_spec.update(virtinst_util.get_autostart_args())

    # Create module
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True)

    if not HAS_VIRT:
        module.fail_json(
            msg="The `libvirt` module is not importable. Check the requirements.")

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


if __name__ == "__main__":
    main()
