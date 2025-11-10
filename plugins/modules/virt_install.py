#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2025, Joey Zhang <thinkdoggie@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: virt_install
version_added: 2.0.0
author: "Joey Zhang (@thinkdoggie)"
short_description: Provision new virtual machines using virt-install tool
description:
  - Create and install virtual machines using C(virt-install) with a declarative configuration.
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
      - If set to V(absent), remove the VM if it exists.
    default: present
  recreate:
    type: bool
    description:
      - Use with present to force the re-creation of an existing VM.
    default: false
extends_documentation_fragment:
    - community.libvirt.virt.options_uri
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
    - community.libvirt.virt_install.options_cdrom
    - community.libvirt.virt_install.options_location
    - community.libvirt.virt_install.options_pxe
    - community.libvirt.virt_install.options_import
    - community.libvirt.virt_install.options_extra_args
    - community.libvirt.virt_install.options_initrd_inject
    - community.libvirt.virt_install.options_install
    - community.libvirt.virt_install.options_unattended
    - community.libvirt.virt_install.options_cloud_init
    - community.libvirt.virt_install.options_boot
    - community.libvirt.virt_install.options_idmap
    - community.libvirt.virt_install.options_osinfo
    - community.libvirt.virt_install.options_disks
    - community.libvirt.virt_install.options_filesystems
    - community.libvirt.virt_install.options_networks
    - community.libvirt.virt_install.options_graphics_devices
    - community.libvirt.virt_install.options_virt_type
    - community.libvirt.virt_install.options_hvm
    - community.libvirt.virt_install.options_paravirt
    - community.libvirt.virt_install.options_container
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
    - community.libvirt.virt_install.options_transient
    - community.libvirt.virt_install.options_destroy_on_exit
    - community.libvirt.virt_install.options_noreboot
    - community.libvirt.requirements
attributes:
    check_mode:
        description: Supports check_mode.
        support: full
requirements:
    - "virt-install"
notes:
    - The C(virt-install) command is provided by different packages on different distributions.
    - On Debian/Ubuntu, install the C(virtinst) package.
    - On RHEL/CentOS/Fedora and openSUSE, install the C(virt-install) package.
seealso:
  - name: virt-install Man Page
    description: Ubuntu manpage of virt-install tool.
    link: https://manpages.ubuntu.com/manpages/focal/man1/virt-install.1.html
"""

EXAMPLES = """
# Basic VM creation with Fedora installation
- name: Create a basic Fedora VM
  community.libvirt.virt_install:
    name: my-fedora-vm
    memory: 2048
    vcpus: 2
    disks:
      - size: 20
    osinfo:
      name: fedora39
    location: https://download.fedoraproject.org/pub/fedora/linux/releases/39/Server/x86_64/
    graphics:
      type: spice
    networks:
      - network: default

# Windows 10 VM with CDROM installation
- name: Create Windows 10 VM
  community.libvirt.virt_install:
    name: my-win10-vm
    memory: 4096
    vcpus: 4
    disks:
      - size: 40
        format: qcow2
    osinfo:
      name: win10
    cdrom: /path/to/my/win10.iso
    graphics:
      type: vnc
      password: mypassword
    networks:
      - network: default
        model:
          type: e1000

# Import existing disk image
- name: Import existing Debian VM
  community.libvirt.virt_install:
    name: my-debian-vm
    memory: 1024
    vcpus: 2
    disks:
      - path: /home/user/VMs/my-debian9.img
    osinfo:
      name: debian9
    import: true
    networks:
      - bridge: br0

# CentOS installation with custom storage and network configuration
- name: Create CentOS VM with custom configuration
  community.libvirt.virt_install:
    name: centos-server
    memory: 8192
    vcpus: 8
    disks:
      - pool: default
        size: 50
        format: qcow2
        cache: writeback
      - pool: default
        size: 100
        format: qcow2
        bus: virtio
    osinfo:
      name: centos7.0
    location: http://mirror.centos.org/centos-7/7/os/x86_64/
    extra_args: "ks=http://myserver/centos7.ks"
    graphics:
      type: vnc
      listen: 0.0.0.0
      port: 5901
    networks:
      - bridge: br0
        model:
          type: virtio
      - network: isolated-net

# Ubuntu server with unattended installation
- name: Create Ubuntu server with unattended install
  community.libvirt.virt_install:
    name: ubuntu-server
    memory: 2048
    vcpus: 2
    disks:
      - size: 25
    osinfo:
      name: ubuntu20.04
    location: http://archive.ubuntu.com/ubuntu/dists/focal/main/installer-amd64/
    unattended:
      profile: jeos
      admin_password_file: /tmp/root_password
      user_login: ansible
      user_password_file: /tmp/user_password
    networks:
      - network: default

# ARM VM with custom kernel
- name: Create ARM VM with custom kernel
  community.libvirt.virt_install:
    name: arm-test-vm
    memory: 1024
    vcpus: 2
    arch: armv7l
    machine: vexpress-a9
    disks:
      - path: /home/user/VMs/myarmdisk.img
    boot:
      kernel: /tmp/my-arm-kernel
      initrd: /tmp/my-arm-initrd
      dtb: /tmp/my-arm-dtb
      kernel_args: "console=ttyAMA0 rw root=/dev/mmcblk0p3"
    graphics:
      type: none
    networks:
      - network: default

# VM with SEV launch security (AMD)
- name: Create SEV-enabled VM
  community.libvirt.virt_install:
    name: sev-vm
    memory: 4096
    memtune:
      hard_limit: 4563402
    vcpus: 4
    machine: q35
    boot: uefi
    disks:
      - size: 15
        bus: scsi
    controller_devices:
      - type: scsi
        model: virtio-scsi
        driver:
          iommu: "on"
      - type: virtio-serial
        driver:
          iommu: "on"
    networks:
      - network: default
        model:
          type: virtio
        driver:
          iommu: "on"
    rng:
      backend:
        type: random
        source: /dev/random
      driver:
        iommu: "on"
    memballoon:
      model: virtio
      driver:
        iommu: "on"
    launch_security:
      type: sev
      policy: "0x01"
    osinfo:
      name: fedora39
    import: true


# VM with PCI passthrough for a network device
- name: Create VM with PCI network passthrough
  community.libvirt.virt_install:
    name: passthrough-vm
    memory: 4096
    vcpus: 4
    disks:
      - size: 30
    osinfo:
      name: ubuntu20.04
    import: true
    host_devices:
      - value: "81:00.0"

# Recreate existing VM
- name: Recreate existing VM with new configuration
  community.libvirt.virt_install:
    name: existing-vm
    state: present
    recreate: true
    memory: 4096
    vcpus: 4
    disks:
      - size: 40
    osinfo:
      name: fedora39
    cdrom: /path/to/fedora39.iso
    networks:
      - network: default

# Remove VM
- name: Remove VM
  community.libvirt.virt_install:
    name: unwanted-vm
    state: absent
"""

RETURN = r""" # """

from ansible_collections.community.libvirt.plugins.module_utils import virt_install as virtinst_util
from ansible_collections.community.libvirt.plugins.module_utils.virt_install import (
    LibvirtWrapper, VirtInstallTool
)
from ansible_collections.community.libvirt.plugins.module_utils.libvirt import (
    HAS_VIRT, HAS_XML, VMNotFound, VIRT_SUCCESS
)
from ansible.module_utils.basic import AnsibleModule


def core(module):
    state = module.params.get('state')
    name = module.params.get('name')
    uri = module.params.get('uri')
    recreate = module.params.get('recreate', False)

    result = dict(
        changed=False,
        orignal_message="",
        message="",
    )

    virtConn = LibvirtWrapper(module)
    virtInstall = VirtInstallTool(module)

    if not name:
        module.fail_json(msg="virtual machine name is missing")

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
            if vm.isActive():
                virtConn.destroy(name)
            virtConn.undefine(name)

        # run virt-install to create new vm
        changed, rc, extra_res = virtInstall.execute(dryrun=module.check_mode)
        result['changed'] = changed
        result.update(extra_res)

        return rc, result
    elif state == 'absent':
        if not vm_exists:
            result['message'] = "virtual machine '%s' is already absent" % name
            return VIRT_SUCCESS, result

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
    )

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
    # Installation options
    argument_spec.update(virtinst_util.get_cdrom_args())
    argument_spec.update(virtinst_util.get_location_opts())
    argument_spec.update(virtinst_util.get_pxe_args())
    argument_spec.update(virtinst_util.get_import_args())
    argument_spec.update(virtinst_util.get_extra_args_args())
    argument_spec.update(virtinst_util.get_initrd_inject_args())
    argument_spec.update(virtinst_util.get_install_args())
    argument_spec.update(virtinst_util.get_unattended_args())
    argument_spec.update(virtinst_util.get_cloud_init_args())
    argument_spec.update(virtinst_util.get_boot_args())
    argument_spec.update(virtinst_util.get_idmap_args())
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
    argument_spec.update(virtinst_util.get_container_args())
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
    argument_spec.update(virtinst_util.get_transient_args())
    argument_spec.update(virtinst_util.get_destroy_on_exit_args())
    argument_spec.update(virtinst_util.get_noreboot_args())

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
