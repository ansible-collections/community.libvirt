# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):

    OPTIONS_MEMORY = """
options:
  memory:
    type: int
    description:
      - Memory to allocate for the guest, in MiB.
  memory_opts:
    type: dict
    description:
      - Additional options for memory allocation.
    suboptions:
      current_memory:
        type: int
        description:
          - The actual allocation of memory for the guest, in MiB.
      max_memory:
        type: int
        description:
          - The run time maximum memory allocation of the guest, in MiB.
      max_memory_opts:
        type: dict
        description:
          - Additional options for maximum memory configuration.
        suboptions:
          slots:
            type: int
            description:
              - The number of slots available for adding memory to the guest.
    """

    OPTIONS_MEMORYBACKING = """
options:
  memorybacking:
    type: dict
    description:
      - Specify how virtual memory pages are backed by host pages
    suboptions:
      hugepages:
        type: bool
        description:
          - Use huge pages for memory backing.
      hugepage_specs:
        type: list
        elements: dict
        description:
          - Configure hugepage specifications for memory backing.
        suboptions:
          page_size:
            type: int
            description:
              - Specify the hugepage size with a unit suffix.
          nodeset:
            type: str
            description:
              - Specify the guest's NUMA nodes to certain hugepage sizes.
      nosharepages:
        type: bool
        description:
          - Instructs hypervisor to disable shared pages (memory merge, KSM) for this domain.
      locked:
        type: bool
        description:
          - Memory pages will be locked in host's memory and will not be swapped out.
      source:
        type: dict
        description:
          - Configure the source of memory backing.
        version_added: '2.1.0'
        suboptions:
          type:
            type: str
            choices: [ anonymous, file, memfd ]
            description:
              - The type of memory backing source.
      access:
        type: dict
        description:
          - Configure memory access permissions.
        suboptions:
          mode:
            type: str
            choices: [ shared, private ]
            description:
              - The access mode for the memory.
      allocation:
        type: dict
        description:
          - Configure memory allocation behavior.
        suboptions:
          mode:
            type: str
            choices: [ immediate, ondemand ]
            description:
              - Specify when to allocate the memory by supplying either V(immediate) or V(ondemand).
          threads:
            type: int
            description:
              - The number of threads that hypervisor uses to allocate memory.
      discard:
        type: bool
        description:
          - If set to V(true), the memory content is discarded just before guest shuts down (or when DIMM module is unplugged).
    """

    OPTIONS_ARCH = """
options:
  arch:
    type: str
    description:
      - Request a non-native CPU architecture for the guest virtual machine.
      - If omitted, the host CPU architecture will be used in the guest.
    """

    OPTIONS_MACHINE = """
options:
  machine:
    type: str
    description:
      - The machine type to emulate. This will typically not need to be specified for Xen or KVM.
    """

    OPTIONS_METADATA = """
options:
  metadata:
    type: dict
    description:
      - Specify the metadata for the guest virtual machine.
      - The dictionary contains key/value pairs that define individual metadata entries.
      - 'e.g. V({uuid: 4dea22b3-1d52-d8f3-2516-782e98ab3fa0})'
      - Use C(virt-install --metadata=?) to see a list of all available sub options.
    """

    OPTIONS_EVENTS = """
options:
  events:
    type: dict
    description:
      - Specify events values for the guest.
    suboptions:
      on_poweroff:
        type: str
        choices: [ destroy, restart, preserve, rename-restart ]
        description:
          - Action to take when the guest requests a poweroff.
      on_reboot:
        type: str
        choices: [ destroy, restart, preserve, rename-restart ]
        description:
          - Action to take when the guest requests a reboot.
      on_crash:
        type: str
        choices: [ destroy, restart, preserve, rename-restart, coredump-destroy, coredump-restart ]
        description:
          - Action to take when the guest crashes.
      on_lockfailure:
        type: str
        choices: [ poweroff, restart, pause, ignore ]
        description:
          - Action to take when when a lock manager loses resource locks.
    """

    OPTIONS_RESOURCE = """
options:
  resource:
    type: dict
    description:
      - Specify resource partitioning for the guest.
      - The dictionary contains key/value pairs that define individual resource entries.
      - Use C(virt-install --resource=?) to see a list of all available sub options.
    """

    OPTIONS_SYSINFO = """
options:
  sysinfo:
    type: dict
    description:
      - Configure sysinfo/SMBIOS values exposed to the VM OS.
      - The dictionary contains key/value pairs that define individual sysinfo entries.
      - Use C(virt-install --sysinfo=?) to see a list of all available sub options.
    """

    OPTIONS_QEMU_COMMANDLINE = """
options:
  qemu_commandline:
    type: str
    description:
      - Pass options directly to the qemu emulator. Only works for the libvirt qemu driver.
    """

    OPTIONS_VCPUS = """
options:
  vcpus:
    type: int
    description:
      - Number of virtual cpus to configure for the guest.
  vcpus_opts:
    type: dict
    description:
      - Additional options for virtual CPU configuration.
    suboptions:
      maxvcpus:
        type: int
        description:
          - If specified, the guest will be able to hotplug up to MAX vcpus while the guest is running.
      sockets:
        type: int
        description:
          - Total number of CPU sockets
      dies:
        type: int
        description:
          - Number of dies per socket
      clusters:
        type: int
        description:
          - number of clusters per die
      cores:
        type: int
        description:
          - Number of cores per cluster
      threads:
        type: int
        description:
          - Number of threads per core
      current:
        type: int
        description:
          - Specify whether fewer than the maximum number of virtual CPUs should be enabled.
      cpuset:
        type: str
        description:
          - A comma-separated list of physical CPU numbers that domain process and virtual CPUs can be pinned to by default.
      placement:
        type: str
        choices: [ static, auto ]
        description:
          - Indicate the CPU placement mode for domain process
      vcpu_specs:
        type: list
        elements: dict
        description:
          - Configure individual vCPU properties.
          - Each dictionary entry contains a property name and its corresponding value.
    """

    OPTIONS_NUMATUNE = """
options:
  numatune:
    type: dict
    description:
      - Tune NUMA policy for the domain process.
    suboptions:
      memory:
        type: dict
        description:
          - Specifies how to allocate memory for the domain process on a NUMA host.
        suboptions:
          mode:
            type: str
            choices: [ interleave, preferred, strict ]
            description:
              - Can be one of V(interleave), V(preferred), or V(strict) (the default)
          nodeset:
            type: str
            description:
              - Specifies the NUMA nodes to allocate memory from.
          placement:
            type: str
            choices: [ static, auto ]
            description:
              - Indicate the memory placement mode for domain process.
      memnode_specs:
        type: list
        elements: dict
        description:
          - Specify memory allocation policies per each guest NUMA node.
        suboptions:
          cellid:
            type: int
            description:
              - Specify the NUMA node ID.
          mode:
            type: str
            choices: [ interleave, preferred, strict ]
            description:
              - Can be one of V(interleave), V(preferred), or V(strict) (the default)
          nodeset:
            type: str
            description:
              - Specifies the NUMA nodes to allocate memory from.
    """

    OPTIONS_MEMTUNE = """
options:
  memtune:
    type: dict
    description:
      - Tune memory policy for the domain process.
      - The dictionary contains key/value pairs that define individual memtune entries.
    """

    OPTIONS_BLKIOTUNE = """
options:
  blkiotune:
    type: dict
    description:
      - Tune block I/O policy for the domain process.
    suboptions:
      weight:
        type: int
        description:
          - The overall I/O weight of the guest.
          - The value should be in the range [100, 1000]. After kernel 2.6.39, the value could be in the range [10, 1000].
      devices:
        type: list
        elements: dict
        description:
          - Tune the weights for individual host block device used by the guest.
          - Each dictionary entry contains a property name and its corresponding value.
    """

    OPTIONS_CPU = """
options:
  cpu:
    type: dict
    description:
      - Configure the CPU model and CPU features exposed to the guest.
    suboptions:
      model:
        type: str
        description:
          - A valid CPU model or configuration mode for the guest.
          - "The possible values include: V(host-model), V(host-passthrough) and V(maximum)."
      model_opts:
        type: dict
        description:
          - Additional options for CPU model configuration.
        suboptions:
          fallback:
            type: str
            choices: [ forbid, allow ]
            description:
              - Specify whether to automatically fall back to the closest model supported by the hypervisor if unable to use the exact CPU model.
          vendor_id:
            type: str
            description:
              - Set the vendor id seen by the guest. It must be exactly 12 characters long.
              - Typical possible values are I(AuthenticAMD) and I(GenuineIntel).
      match:
        type: str
        choices: [ exact, minimum, strict ]
        description:
          - Specify how strictly the CPU model should be matched.
      migratable:
        type: bool
        description:
          - Specify whether this CPU model is migratable.
      vendor:
        type: str
        description:
          - Specify CPU vendor requested by the guest
          - The list of supported vendors can be found in I(cpu_map/*_vendors.xml).
      features:
        type: dict
        description:
          - Fine-tune features provided by the selected CPU model.
          - The value should be a dictionary where each key is a feature name and the value is a dictionary of options for that feature.
          - An empty object V({}) for a feature indicates to enable that feature.
        suboptions:
          policy:
            type: str
            choices: [ force, require, optional, disable, forbid ]
            description:
              - The policy for the CPU feature.
              - If set to V(force), the vCPU will claim the feature is supported regardless of it being supported by host CPU.
              - If set to V(require), guest creation will fail unless the feature is supported by the host CPU or the hypervisor is able to emulate it.
              - If set to V(optional), the feature will be supported by vCPU if and only if it is supported by host CPU.
              - If set to V(disable), the feature will not be supported by virtual CPU.
              - If set to V(forbid), guest creation will fail if the feature is supported by host CPU.
      cache:
        type: dict
        description:
          - vCPU cache configuration for the guest.
        suboptions:
          mode:
            type: str
            choices: [ emulate, passthrough, disable ]
            description:
              - If set to V(emulate), the hypervisor will provide a fake CPU cache data.
              - If set to V(passthrough), the host CPU cache data reported by the host CPU will be passed through to the vCPU.
              - If set to V(disable), the vCPU will report no CPU cache at all.
          level:
            type: int
            description:
              - Specify the level of CPU cache.
      numa:
        type: dict
        description:
          - Configure NUMA topology for the guest.
        suboptions:
          cell_specs:
            type: list
            elements: dict
            description:
              - Specify a NUMA cell configuration.
            suboptions:
              id:
                type: int
                description:
                  - Specify the NUMA node ID.
              cpus:
                type: str
                description:
                  - Specify the CPU or range of CPUs that are part of this node.
              memory:
                type: int
                description:
                  - Specify the node memory size with a unit suffix.
              mem_access:
                type: str
                choices: [ shared, private ]
                description:
                  - Specify the memory access mode for the NUMA node.
                  - This is valid only for hugepages-backed memory and nvdimm modules.
              discard:
                type: bool
                description:
                  - Fine tune the discard feature for given NUMA node.
              distances:
                type: dict
                description:
                  - Define the distance between NUMA cells.
                suboptions:
                  sibling_specs:
                    type: list
                    elements: dict
                    description:
                      - Specify the distance value between sibling NUMA cells.
                      - Each dictionary entry contains a property name and its corresponding value.
              cache_specs:
                type: list
                elements: dict
                description:
                  - Describe memory side cache for memory proximity domains.
                  - Each dictionary entry contains a property name and its corresponding value.
          interconnects:
            type: list
            elements: dict
            description:
              - Describes the normalized memory read/write latency and bandwidth between Initiator Proximity Domains and Target Proximity Domains.
            suboptions:
              bandwidth_specs:
                type: list
                elements: dict
                description:
                  - Describe bandwidth between two memory nodes.
                  - Each dictionary entry contains a property name and its corresponding value.
              latency_specs:
                type: list
                elements: dict
                description:
                  - Describe latency between two memory nodes.
                  - Each dictionary entry contains a property name and its corresponding value.
    """

    OPTIONS_CPUTUNE = """
options:
  cputune:
    type: dict
    description:
      - Tune CPU parameters for the guest.
    suboptions:
      vcpupin_specs:
        type: list
        elements: dict
        description:
          - Specify which of host's physical CPUs the domain vCPU will be pinned to
        suboptions:
          vcpu:
            type: int
            description:
              - Specify the vCPU ID.
          cpuset:
            type: str
            description:
              - A comma-separated list of physical CPU numbers.
      emulatorpin:
        type: dict
        description:
          - Specify which host CPUs the domain emulator will be pinned to.
        suboptions:
          cpuset:
            type: str
            description:
              - Specify which physical CPUs to pin to.
      iothreadpin_specs:
        type: list
        elements: dict
        description:
          - Specify which of host physical CPUs the IOThreads will be pinned to.
        suboptions:
          iothread:
            type: int
            description:
              - Specify the IOThread ID.
          cpuset:
            type: str
            description:
              - Specify which physical CPUs to pin to.
      vcpusched_specs:
        type: list
        elements: dict
        description:
          - Specify the scheduler type for particular vCPUs.
        suboptions:
          vcpus:
            type: str
            description:
              - Select which vCPUs this setting applies to.
          scheduler:
            type: str
            choices: [ batch, idle, fifo, rr ]
            description:
              - The scheduler type.
          priority:
            type: int
            description:
              - For real-time schedulers (fifo, rr), priority must be specified as well (and is ignored for non-real-time ones).
              - The value range for the priority depends on the host kernel (usually 1-99).
      iothreadsched_specs:
        type: list
        elements: dict
        description:
          - Specify the scheduler type for particular IOThreads.
        suboptions:
          iothreads:
            type: str
            description:
              - Select which IOThreads this setting applies to.
          scheduler:
            type: str
            choices: [ batch, idle, fifo, rr ]
            description:
              - The scheduler type.
          priority:
            type: int
            description:
              - For real-time schedulers (fifo, rr), priority must be specified as well (and is ignored for non-real-time ones).
              - The value range for the priority depends on the host kernel (usually 1-99).
      emulatorsched:
        type: dict
        description:
          - Specify the scheduler type for emulator thread.
        suboptions:
          scheduler:
            type: str
            choices: [ batch, idle, fifo, rr ]
            description:
              - The scheduler type.
          priority:
            type: int
            description:
              - For real-time schedulers (fifo, rr), priority must be specified as well (and is ignored for non-real-time ones).
              - The value range for the priority depends on the host kernel (usually 1-99).
      shares:
        type: int
        description:
          - Specify the proportional weighted share for the domain.
      period:
        type: int
        description:
          - "Specify the enforcement interval (unit: microseconds)."
          - The value should be in range [1000, 1000000]. A period with value 0 means no value.
      quota:
        type: int
        description:
          - "Specify the maximum allowed bandwidth (unit: microseconds)."
          - A domain with quota as any negative value indicates that the domain has infinite bandwidth for vCPU threads.
      global_period:
        type: int
        description:
          - "Specify the enforcement CFS scheduler interval (unit: microseconds) for the whole domain."
      global_quota:
        type: int
        description:
          - "Specify the maximum allowed bandwidth (unit: microseconds) within a period for the whole domain."
      emulator_period:
        type: int
        description:
          - "Specify the enforcement interval (unit: microseconds) for domain's emulator threads."
      emulator_quota:
        type: int
        description:
          - "Specify the maximum allowed bandwidth (unit: microseconds) for domain's emulator threads."
      iothread_period:
        type: int
        description:
          - "Specify the enforcement interval (unit: microseconds) for domain's IOThreads."
      iothread_quota:
        type: int
        description:
          - "Specify the maximum allowed bandwidth (unit: microseconds) for domain's IOThreads."
    """

    OPTIONS_SECURITY = """
options:
  security:
    type: dict
    description:
      - Configure domain seclabel domain settings.
      - The dictionary contains key/value pairs that define individual security entries.
    """

    OPTIONS_KEYWRAP = """
options:
  keywrap:
    type: dict
    description:
      - Configure domain keywrap settings used for S390 cryptographic key management operations.
    suboptions:
      ciphers:
        type: list
        elements: dict
        description:
          - Specify the cipher settings for the domain.
          - Each dictionary entry contains a property name and its corresponding value.
    """
    OPTIONS_IOTHREADS = """
options:
  iothreads:
    type: int
    description:
      - Number of I/O threads to configure for the guest.
  iothreads_opts:
    type: dict
    description:
      - Additional options for I/O threads configuration.
    suboptions:
      iothread_specs:
        type: list
        elements: dict
        description:
          - Provide the capability to specifically define the IOThread ID's for the domain.
        suboptions:
          id:
            type: int
            description:
              - Define the IOThread ID.
          thread_pool_min:
            type: int
            description:
              - Set lower boundary for number of worker threads for given IOThread.
          thread_pool_max:
            type: int
            description:
              - Set upper boundary for number of worker threads for given IOThread.
      defaultiothread:
        type: dict
        description:
          - Provide the capability to define the default event loop within hypervisor.
        suboptions:
          thread_pool_min:
            type: int
            description:
              - Set lower boundary for number of worker threads for given IOThread.
          thread_pool_max:
            type: int
            description:
              - Set upper boundary for number of worker threads for given IOThread.
    """

    OPTIONS_FEATURES = """
options:
  features:
    type: dict
    description:
      - Enable or disable certain machine features.
      - The value should be a dictionary where each key is a feature name and the value is a dictionary of options for that feature.
      - An empty object V({}) for a feature indicates to turn on that feature with default options.
      - 'Example: V(hyperv.spinlocks: {state: off}), V(pvspinlock: {})'
    """

    OPTIONS_CLOCK = """
options:
  clock:
    type: dict
    description:
      - Configure the clock for the guest.
    suboptions:
      offset:
        type: str
        description:
          - Set the clock offset, e.g. V(utc) or V(localtime).
      timers:
        type: list
        elements: dict
        description:
          - Tweak the guest's timer settings on the specific hypervisor.
          - Each dictionary entry contains a property name and its corresponding value.
    """

    OPTIONS_PM = """
options:
  pm:
    type: dict
    description:
      - Configure the power management for the guest.
    suboptions:
      suspend_to_mem:
        type: dict
        description:
          - Configure BIOS support for S3 (suspend-to-mem) ACPI sleep states.
        suboptions:
          enabled:
            type: bool
            description:
              - Enable or disable this sleep state.
      suspend_to_disk:
        type: dict
        description:
          - Configure BIOS support for S4 (suspend-to-disk) ACPI sleep states.
        suboptions:
          enabled:
            type: bool
            description:
              - Enable or disable this sleep state.
    """

    OPTIONS_LAUNCH_SECURITY = """
options:
  launch_security:
    type: dict
    description:
      - Enable launch security for the guest.
    suboptions:
      type:
        type: str
        description:
          - The type of launch security to enable, e.g. V(sev).
        required: true
      policy:
        type: str
        description:
          - The guest policy which must be maintained by the SEV firmware, e.g. V(0x01).
      cbitpos:
        type: int
        description:
          - The C-bit (aka encryption bit) location in guest page table entry.
      reduced_phys_bits:
        type: int
        description:
          - The physical address bit reduction, e.g. V(1).
      dh_cert:
        type: str
        description:
          - The guest owners base64 encoded Diffie-Hellman (DH) key.
      session:
        type: str
        description:
          - The guest owners base64 encoded session blob defined in the SEV API spec.
    """

    OPTIONS_CDROM = """
options:
  cdrom:
    type: str
    description:
      - ISO file or CDROM device to use for VM install media.
    """

    OPTIONS_LOCATION = """
options:
  location:
    type: str
    description:
      - The installation source, which can be a URL or a directory path containing the OS distribution installation media.
  location_opts:
    type: dict
    description:
      - Additional options for the installation source.
    suboptions:
      kernel:
        type: str
        description:
          - The kernel path relative to the specified location.
      initrd:
        type: str
        description:
          - The initrd path relative to the specified location.
    """

    OPTIONS_PXE = """
options:
  pxe:
    type: bool
    description:
      - Install the guest from PXE.
    """

    OPTIONS_IMPORT = """
options:
  import:
    type: bool
    description:
      - Skip the OS installation process, and build a guest around an existing disk image.
    """

    OPTIONS_EXTRA_ARGS = """
options:
  extra_args:
    type: str
    description:
      - Additional kernel command line arguments to pass to the installer when performing a guest install with O(location).
    """

    OPTIONS_INITRD_INJECT = """
options:
  initrd_inject:
    type: str
    description:
      - Add PATH to the root of the initrd fetched with O(location).
    """

    OPTIONS_INSTALL = """
options:
  install:
    type: dict
    description:
      - Additional options for the installation.
      - This option is strictly for VM install operations, essentially configuring the first boot.
    suboptions:
      os:
        type: str
        description:
          - The OS name from I(libosinfo), e.g. V(fedora29).
        required: true
      kernel:
        type: str
        description:
          - Specify a kernel and initrd pair to use as install media.
      initrd:
        type: str
        description:
          - Specify a kernel and initrd pair to use as install media.
      kernel_args:
        type: str
        description:
          - Specify the installation-time kernel arguments.
      kernel_args_overwrite:
        type: bool
        description:
          - Override the virt-install default kernel arguments rather than appending to them.
      bootdev:
        type: str
        description:
          - Specify the install bootdev to boot for the install phase.
      no_install:
        type: bool
        description:
          - Tell virt-install that there isn't actually any install happening, and you just want to create the VM.
    """

    OPTIONS_UNATTENDED = """
options:
  unattended:
    type: dict
    description:
      - Perform an unattended install using libosinfo's install script support.
    suboptions:
      profile:
        type: str
        description:
          - Choose which I(libosinfo) unattended profile to use.
      admin_password_file:
        type: str
        description:
          - A file used to set the VM OS admin/root password from.
      user_login:
        type: str
        description:
          - The user login name to be used in the VM.
      user_password_file:
        type: str
        description:
          - A file used to set the VM user password.
      product_key:
        type: str
        description:
          - Set a Windows product key.
    """

    OPTIONS_CLOUD_INIT = """
options:
  cloud_init:
    type: dict
    description:
      - Pass cloud-init metadata to the VM.
      - A cloud-init NoCloud ISO file is generated, and attached to the VM as a CDROM device.
    suboptions:
      root_password_generate:
        type: bool
        description:
          - Generate a new root password for the VM.
      disable:
        type: bool
        description:
          - Disable cloud-init in the VM for subsequent boots.
          - Without this, cloud-init may reset auth on each boot.
      root_password_file:
        type: str
        description:
          - A file used to set the VM root password from.
      root_ssh_key:
        type: str
        description:
          - Specify a public key file to inject into the guest.
      clouduser_ssh_key:
        type: str
        description:
          - Specify a public key file to inject into the guest, providing ssh access to the default cloud-init user account.
      network_config:
        type: raw
        description:
          - Specify a cloud-init network-config file content.
          - Can be provided as a YAML string (e.g., using the '|' operator in Ansible) or as a dictionary structure.
          - "Note: String values are preferred as dictionary values cannot ensure order preservation."
      meta_data:
        type: raw
        description:
          - Specify a cloud-init meta-data file content.
          - Can be provided as a YAML string (e.g., using the '|' operator in Ansible) or as a dictionary structure.
          - "Note: String values are preferred as dictionary values cannot ensure order preservation."
      user_data:
        type: raw
        description:
          - Specify a cloud-init user-data file content.
          - Can be provided as a YAML string (e.g., using the '|' operator in Ansible) or as a dictionary structure.
          - "Note: String values are preferred as dictionary values cannot ensure order preservation."
    """

    OPTIONS_BOOT = """
options:
  boot:
    type: str
    description:
      - Set the boot device priority for post-install configuration.
  boot_opts:
    type: dict
    description:
      - Additional options for boot configuration.
      - The dictionary contains key/value pairs that define individual boot options.
    """

    OPTIONS_IDMAP = """
options:
  idmap:
    type: dict
    description:
      - Configure the UID or GID mapping for the guest.
    suboptions:
      uid:
        type: dict
        description:
          - The UID mapping configuration.
        suboptions:
          start:
            type: int
            description:
              - First user ID in container.
          target:
            type: int
            description:
              - The first user ID in container will be mapped to this target user ID in host.
          count:
            type: int
            description:
              - How many users in container are allowed to map to host's user.
      gid:
        type: dict
        description:
          - The GID mapping configuration.
        suboptions:
          start:
            type: int
            description:
              - First group ID in container.
          target:
            type: int
            description:
              - The first group ID in container will be mapped to this target user ID in host.
          count:
            type: int
            description:
              - How many groups in container are allowed to map to host's user.
    """

    OPTIONS_OSINFO = """
options:
  osinfo:
    type: dict
    description:
      - Optimize the guest configuration for a specific operating system.
    suboptions:
      name:
        type: str
        aliases: [ short_id ]
        description:
          - The OS name from libosinfo. (e.g. V(fedora32), V(win10))
      id:
        type: str
        description:
          - The full URL style libosinfo ID.
      detect:
        type: bool
        description:
          - Whether C(virt-install) should attempt OS detection from the specified install media.
      require:
        type: bool
        description:
          - Whether C(virt-install) should fail if OS detection fails.
    """

    OPTIONS_DISKS = """
options:
  disks:
    type: list
    elements: dict
    description:
      - Specify the storage devices for the guest.
    suboptions:
      path:
        type: str
        description:
          - The path to some storage media to use, existing or not.
      pool:
        type: str
        description:
          - An existing libvirt storage pool name to create new storage on.
      vol:
        type: str
        description:
          - An existing libvirt storage volume to use.
      size:
        type: int
        description:
          - The size (in GiB) to use if creating new storage.
      sparse:
        type: bool
        description:
          - Whether to skip fully allocating newly created storage.
      format:
        type: str
        description:
          - Disk image format. For file volumes, this can be V(raw), V(qcow2), V(vmdk), etc.
      backing_store:
        type: str
        description:
          - Path to a disk to use as the backing store for the newly created image.
      backing_format:
        type: str
        description:
          - Disk image format of I(backing_store).
      bus:
        type: str
        description:
          - Disk bus type. (e.g. V(ide), V(sata), V(scsi), V(usb), V(virtio), V(xen))
      readonly:
        type: bool
        description:
          - Set drive as readonly
      shareable:
        type: bool
        description:
          - Set drive as shareable
      cache:
        type: str
        choices: [ none, writethrough, directsync, unsafe, writeback ]
        description:
          - The cache mode to be used.
      serial:
        type: str
        description:
          - Serial number of the emulated disk device.
      snapshot:
        type: str
        choices: [ "internal", "external", "no" ]
        description:
          - Indicates the default behavior of the disk during disk snapshots.
      rawio:
        type: bool
        description:
          - Specify whether the disk needs rawio capability.
      sgio:
        type: str
        choices: [ filtered, unfiltered ]
        description:
          - Specify whether unprivileged SG_IO commands are filtered for the disk.
          - Only available when the device is 'lun'.
      transient:
        type: bool
        description:
          - If V(true), this indicates that changes to the device contents should be reverted automatically when the guest exits.
      transient_opts:
        type: dict
        description:
          - Additional options for transient disk configuration.
        suboptions:
          share_backing:
            type: bool
            description:
              - If V(true), the transient disk is supposed to be shared between multiple concurrently running VMs.
      driver:
        type: dict
        description:
          - Specify the details of the hypervisor disk driver.
          - The dictionary contains key/value pairs that define individual properties.
      source:
        type: dict
        description:
          - Specify the details of the disk source.
          - The dictionary contains key/value pairs that define individual properties.
      target:
        type: dict
        description:
          - Specify the details of the target disk device.
          - The dictionary contains key/value pairs that define individual properties.
      address:
        type: dict
        description:
          - Specify the controller properties where the disk should be attached.
          - The dictionary contains key/value pairs that define individual properties.
      boot:
        type: dict
        description:
          - Specify the boot order for the disk device.
          - The dictionary contains key/value pairs that define individual properties.
          - The per-device boot elements cannot be used together with general boot elements in the OS bootloader section.
      iotune:
        type: dict
        description:
          - Specify additional per-device I/O tuning.
          - The dictionary contains key/value pairs that define individual properties.
      blockio:
        type: dict
        description:
          - Override the default block device properties for the disk.
          - The dictionary contains key/value pairs that define individual properties.
      geometry:
        type: dict
        description:
          - Override geometry settings for the disk.
          - The dictionary contains key/value pairs that define individual properties.
    """

    OPTIONS_FILESYSTEMS = """
options:
  filesystems:
    type: list
    elements: dict
    description:
      - Specifies directories on the host to export to the guest.
    suboptions:
      type:
        type: str
        choices: [ mount, template, file, block, ram, bind ]
        description:
          - Specify the source type of the filesystem.
      accessmode:
        type: str
        choices: [ passthrough, mapped, squash ]
        description:
          - Specify the security mode for accessing the source.
      source:
        type: dict
        description:
          - The source directory configuration on the host.
          - The dictionary contains key/value pairs that define individual properties.
      target:
        type: dict
        description:
          - The mount target configuration in the guest.
          - The dictionary contains key/value pairs that define individual properties.
      fmode:
        type: str
        description:
          - The creation mode for files when used with the V(mapped) value for I(accessmode).
      dmode:
        type: str
        description:
          - The creation mode for directories when used with the V(mapped) value for I(accessmode).
      multidevs:
        type: str
        choices: [ default, remap, forbid, warn ]
        description:
          - Specify how to deal with a filesystem export containing more than one device.
      readonly:
        type: bool
        description:
          - Enable exporting filesystem as a readonly mount for guest.
      space_hard_limit:
        type: int
        description:
          - Maximum space available to this guest's filesystem
      space_soft_limit:
        type: int
        description:
          - Maximum space available to this guest's filesystem.
      driver:
        type: dict
        description:
          - Specify the details of the hypervisor driver.
          - The dictionary contains key/value pairs that define individual properties.
      address:
        type: dict
        description:
          - Specify the controller properties where the filesystem should be attached.
          - The dictionary contains key/value pairs that define individual properties.
      binary:
        type: dict
        description:
          - Tune the options for virtiofsd.
          - The dictionary contains key/value pairs that define individual properties.
    """

    OPTIONS_NETWORKS = """
options:
  networks:
    type: list
    elements: dict
    description:
      - Connect the guest to the host network.
      - Empty list V([]) means no default network interface.
    suboptions:
      type:
        type: str
        choices: [ direct ]
        description:
          - The type of network interface.
          - V(direct) provides direct attachment to host network interface using macvtap.
          - If omitted, the type of network interface is determined by other options.
      network:
        type: str
        description:
          - Name of the libvirt virtual network to connect to.
      bridge:
        type: str
        description:
          - Name of the host bridge device to connect to.
      hostdev:
        type: str
        description:
          - Name of the host device to connect to for type=hostdev.
          - This uses PCI passthrough to directly assign a network device.
      mac:
        type: dict
        description:
          - MAC address configuration for the network interface.
        suboptions:
          address:
            type: str
            description:
              - Fixed MAC address for the guest interface.
              - If not specified, a suitable address will be randomly generated.
      mtu:
        type: dict
        description:
          - Configure MTU settings for the virtual network link.
           - The dictionary contains key/value pairs that define individual properties.
      state:
        type: dict
        description:
          - Set state of the virtual network link
          - The dictionary contains key/value pairs that define individual properties.
      model:
        type: dict
        description:
          - Network device model configuration.
        suboptions:
          type:
            type: str
            description:
              - Network device model as seen by the guest.
              - Examples include V(virtio), V(e1000), V(rtl8139).
      driver:
        type: dict
        description:
          - Specify the details of the hypervisor driver.
          - The dictionary contains key/value pairs that define individual properties.
      boot:
        type: dict
        description:
          - Specify the boot order for the network interface.
          - The dictionary contains key/value pairs that define individual properties.
          - The per-device boot elements cannot be used together with general boot elements in the OS bootloader section.
      filterref:
        type: dict
        description:
          - Configure network traffic filter rules for the guest.
          - The dictionary contains key/value pairs that define individual properties.
      rom:
        type: dict
        description:
          - Specify the interface ROM BIOS configuration
          - The dictionary contains key/value pairs that define individual properties.
      source:
        type: dict
        description:
          - Specify the details of the direct attached macvtap interface.
          - The dictionary contains key/value pairs that define individual properties.
          - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
          - "Example: I(source={value: bond0, mode: bridge})"
      target:
        type: dict
        description:
          - Specify the details of the target network device.
          - The dictionary contains key/value pairs that define individual properties.
      address:
        type: dict
        description:
          - Specify the controller properties where the filesystem should be attached.
          - The dictionary contains key/value pairs that define individual properties.
      virtualport:
        type: dict
        description:
          - Configure virtual port settings for the network interface.
          - The dictionary contains key/value pairs that define individual properties.
          - Common properties include I(type) (e.g. V(802.1Qbg), V(802.1Qbh), V(openvswitch), V(midonet)) and C(parameters) containing type-specific settings.
      trust_guest_rx_filters:
        type: bool
        description:
          - When set to V(true), enables the host to trust and accept MAC address changes and receive filter modifications reported by the guest VM.
    """

    OPTIONS_GRAPHICS_DEVICES = """
options:
  graphics:
    type: dict
    description:
      - Configure the graphical display for the guest virtual machine.
      - The dictionary contains key/value pairs that define individual properties.
      - Common properties include I(type) (e.g. V(vnc), V(spice)) and I(listen).
  graphics_devices:
    type: list
    elements: dict
    description:
      - Configure multiple graphics devices for the guest.
    """

    OPTIONS_VIRT_TYPE = """
options:
  virt_type:
    type: str
    description:
      - The hypervisor used to create the VM guest. Example choices are V(kvm), V(qemu), or V(xen).
    """

    OPTIONS_HVM = """
options:
  hvm:
    type: bool
    description:
      - Request the use of full virtualization.
    """

    OPTIONS_PARAVIRT = """
options:
  paravirt:
    type: bool
    description:
      - This guest should be a paravirtualized guest.
    """

    OPTIONS_CONTAINER = """
options:
  container:
    type: bool
    description:
      - This guest should be a container type guest.
    """

    OPTIONS_CONTROLLER_DEVICES = """
options:
  controller:
    type: dict
    description:
      - Attach a controller device to the guest.
      - The dictionary contains key/value pairs that define individual controller properties.
      - Examples include I(type=usb,model=none) to disable USB, or I(type=scsi,model=virtio-scsi) for VirtIO SCSI.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  controller_devices:
    type: list
    elements: dict
    description:
      - Configure multiple controller devices for the guest.
    """

    OPTIONS_INPUT_DEVICES = """
options:
  input:
    type: dict
    description:
      - Attach an input device to the guest.
      - Input device types include mouse, tablet, or keyboard.
      - The dictionary contains key/value pairs that define individual input device properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  input_devices:
    type: list
    elements: dict
    description:
      - Configure multiple input devices for the guest.
    """

    OPTIONS_HOST_DEVICES = """
options:
  hostdev:
    type: dict
    description:
      - Attach a physical host device to the guest.
      - The dictionary contains key/value pairs that define individual host device properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  host_devices:
    type: list
    elements: dict
    description:
      - Configure multiple host devices for the guest.
    """

    OPTIONS_SOUND_DEVICES = """
options:
  sound:
    type: dict
    description:
      - Attach a virtual audio device to the guest.
      - The dictionary contains key/value pairs that define individual sound device properties.
      - Common properties include I(model) (e.g. V(ich6), V(ich9), V(ac97)).
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  sound_devices:
    type: list
    elements: dict
    description:
      - Configure multiple sound devices for the guest.
    """

    OPTIONS_AUDIO_DEVICES = """
options:
  audio:
    type: dict
    description:
      - Configure host audio output for the guest's sound hardware.
      - The dictionary contains key/value pairs that define individual audio backend properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  audio_devices:
    type: list
    elements: dict
    description:
      - Configure multiple audio backends for the guest.
    """

    OPTIONS_WATCHDOG_DEVICES = """
options:
  watchdog:
    type: dict
    description:
      - Attach a virtual hardware watchdog device to the guest.
      - The dictionary contains key/value pairs that define individual watchdog properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  watchdog_devices:
    type: list
    elements: dict
    description:
      - Configure multiple watchdog devices for the guest.
    """

    OPTIONS_SERIAL_DEVICES = """
options:
  serial:
    type: dict
    description:
      - Attach a serial device to the guest with various redirection options.
      - The dictionary contains key/value pairs that define individual serial device properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  serial_devices:
    type: list
    elements: dict
    description:
      - Configure multiple serial devices for the guest.
    """

    OPTIONS_PARALLEL_DEVICES = """
options:
  parallel:
    type: dict
    description:
      - Attach a parallel device to the guest.
      - The dictionary contains key/value pairs that define individual parallel device properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  parallel_devices:
    type: list
    elements: dict
    description:
      - Configure multiple parallel devices for the guest.
    """

    OPTIONS_CHANNEL_DEVICES = """
options:
  channel:
    type: dict
    description:
      - Attach a communication channel device to connect the guest and host machine.
      - The dictionary contains key/value pairs that define individual channel properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  channel_devices:
    type: list
    elements: dict
    description:
      - Configure multiple channel devices for the guest.
    """

    OPTIONS_CONSOLE_DEVICES = """
options:
  console:
    type: dict
    description:
      - Connect a text console between the guest and host.
      - The dictionary contains key/value pairs that define individual console properties.
      - Common properties include I(type) and I(target) for different console types.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  console_devices:
    type: list
    elements: dict
    description:
      - Configure multiple console devices for the guest.
    """

    OPTIONS_VIDEO_DEVICES = """
options:
  video:
    type: dict
    description:
      - Specify what video device model will be attached to the guest.
      - The dictionary contains key/value pairs that define individual video device properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  video_devices:
    type: list
    elements: dict
    description:
      - Configure multiple video devices for the guest.
    """

    OPTIONS_SMARTCARD_DEVICES = """
options:
  smartcard:
    type: dict
    description:
      - Configure a virtual smartcard device.
      - The dictionary contains key/value pairs that define individual smartcard properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  smartcard_devices:
    type: list
    elements: dict
    description:
      - Configure multiple smartcard devices for the guest.
    """

    OPTIONS_REDIRECTED_DEVICES = """
options:
  redirdev:
    type: dict
    description:
      - Add a redirected device for USB or other device redirection.
      - The dictionary contains key/value pairs that define individual redirection properties.
      - Common properties include I(bus=usb), I(type=tcp) or I(type=spicevmc).
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  redirected_devices:
    type: list
    elements: dict
    description:
      - Configure multiple redirected devices for the guest.
    """

    OPTIONS_MEMBALLOON_DEVICES = """
options:
  memballoon:
    type: dict
    description:
      - Attach a virtual memory balloon device to the guest.
      - The dictionary contains key/value pairs that define individual memory balloon properties.
      - Common properties include I(model) (e.g. V(virtio), V(xen)).
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  memballoon_devices:
    type: list
    elements: dict
    description:
      - Configure multiple memory balloon devices for the guest.
    """

    OPTIONS_TPM_DEVICES = """
options:
  tpm:
    type: dict
    description:
      - Configure a virtual TPM (Trusted Platform Module) device.
      - The dictionary contains key/value pairs that define individual TPM properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  tpm_devices:
    type: list
    elements: dict
    description:
      - Configure multiple TPM devices for the guest.
    """

    OPTIONS_RNG_DEVICES = """
options:
  rng:
    type: dict
    description:
      - Configure a virtual random number generator (RNG) device.
      - The dictionary contains key/value pairs that define individual RNG properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  rng_devices:
    type: list
    elements: dict
    description:
      - Configure multiple RNG devices for the guest.
    """

    OPTIONS_PANIC_DEVICES = """
options:
  panic:
    type: dict
    description:
      - Attach a panic notifier device to the guest.
      - The dictionary contains key/value pairs that define individual panic device properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  panic_devices:
    type: list
    elements: dict
    description:
      - Configure multiple panic devices for the guest.
    """

    OPTIONS_SHMEM_DEVICES = """
options:
  shmem:
    type: dict
    description:
      - Attach a shared memory device to the guest.
      - The dictionary contains key/value pairs that define individual shared memory properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  shmem_devices:
    type: list
    elements: dict
    description:
      - Configure multiple shared memory devices for the guest.
    """

    OPTIONS_VSOCK_DEVICES = """
options:
  vsock:
    type: dict
    description:
      - Configure a vsock host/guest interface.
      - The dictionary contains key/value pairs that define individual vsock properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  vsock_devices:
    type: list
    elements: dict
    description:
      - Configure multiple vsock devices for the guest.
    """

    OPTIONS_IOMMU_DEVICES = """
options:
  iommu:
    type: dict
    description:
      - Add an IOMMU device to the guest.
      - The dictionary contains key/value pairs that define individual IOMMU properties.
      - "You can use the special attribute I(value) to specify a primary value that appears before other properties in the command line."
  iommu_devices:
    type: list
    elements: dict
    description:
      - Configure multiple IOMMU devices for the guest.
    """

    OPTIONS_AUTOSTART = """
options:
  autostart:
    type: bool
    description:
      - Set the autostart flag for a domain.
    """

    OPTIONS_TRANSIENT = """
options:
  transient:
    type: bool
    description:
      - If set to V(true), libvirt forgets the XML configuration of the VM after shutdown or host restart.
    """

    OPTIONS_DESTROY_ON_EXIT = """
options:
  destroy_on_exit:
    type: bool
    description:
      - If set to V(true), the VM will be destroyed when the console window is exited.
    """

    OPTIONS_NOREBOOT = """
options:
  noreboot:
    type: bool
    description:
      - If set to V(true), the VM will not automatically reboot after the install has completed.
    """
