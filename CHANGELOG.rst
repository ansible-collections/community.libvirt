===============================
Community.Libvirt Release Notes
===============================

.. contents:: Topics

v1.4.0
======

Release Summary
---------------

This is the minor release of the ``community.libvirt`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release.

Minor Changes
-------------

- virt - implement basic check mode functionality (https://github.com/ansible-collections/community.libvirt/issue/98)
- virt - implement the gathering of Dom UUIDs as per FR https://github.com/ansible-collections/community.libvirt/issues/187
- virt - implement the gathering of Dom interface names and mac addresses as per FR https://github.com/ansible-collections/community.libvirt/issues/189
- virt - implement the removal of volumes for a dom as per FR https://github.com/ansible-collections/community.libvirt/issues/177

New Modules
-----------

- community.libvirt.virt_volume - Manage libvirt volumes inside a storage pool

v1.3.1
======

Release Summary
---------------

This is the patch release of the ``community.libvirt`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release.

Bugfixes
--------

- libvirt_lxc - add configuration for libvirt_lxc_noseclabel.

v1.3.0
======

Release Summary
---------------

This is a new release of the ``community.libvirt`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release.

Minor Changes
-------------

- virt - add `mutate_flags` parameter to enable XML mutation (add UUID, MAC addresses from existing domain) (https://github.com/ansible-collections/community.libvirt/pull/142/).
- virt - support ``--diff`` for ``define`` command (https://github.com/ansible-collections/community.libvirt/pull/142/).

Bugfixes
--------

- libvirt_qemu - connection plugin threw a warning about an improperly configured remote target. Fix adds `inventory_hostname` to `options.remote_addr.vars` (https://github.com/ansible-collections/community.libvirt/pull/147).
- libvirt_qemu - fix encoding errors on Windows guests for non-ASCII return values (https://github.com/ansible-collections/community.libvirt/pull/157)
- virt - fix virt module to undefine a domain with nvram, managed_save, snapshot_metadata or checkpoints_metadata (https://github.com/ansible-collections/community.libvirt/issues/40).
- virt_pool - replace discouraged function ``listAllVolumes`` with ``listAllVolumes`` to fix potential race conditions (https://github.com/ansible-collections/community.libvirt/pull/135).
- virt_pool - replace discouraged functions ``listStoragePools`` and ``listDefinedStoragePools`` with ``listAllStoragePools`` to fix potential race conditions (https://github.com/ansible-collections/community.libvirt/pull/134).

v1.2.0
======

Release Summary
---------------

This is the minor release of the ``community.libvirt`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release.

Minor Changes
-------------

- libvirt - add extra guest information to inventory (https://github.com/ansible-collections/community.libvirt/pull/113).
- libvirt - replace the calls to listDomainsID() and listDefinedDomains() with listAllDomains() in find_vm() (https://github.com/ansible-collections/community.libvirt/pull/117)

Bugfixes
--------

- virt_net - fix modify function which was not idempotent, depending on whether the network was active. See https://github.com/ansible-collections/community.libvirt/issues/107.
- virt_pool - crashed out if pool didn't contain a target path. Fix allows this not to be set. (https://github.com/ansible-collections/community.libvirt/issues/129).

v1.1.0
======

Release Summary
---------------

This is the minor release of the ``community.libvirt`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release 1.0.2.

Bugfixes
--------

- replace deprecated ``distutils.spawn.find_executable`` with Ansible's ``get_bin_path`` in ``_search_executable`` function.

v1.0.2
======

Release Summary
---------------

This is the patch release of the ``community.libvirt`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after release 1.0.1.

Bugfixes
--------

- libvirt inventory plugin - Use FQCN for the inventory plugin name for compatibility with Ansible 2.10 and above (https://github.com/ansible-collections/community.libvirt/pull/73).

v1.0.1
======

Bugfixes
--------

- libvirt_qemu - Mitigate a CPU hammering active wait loop
- libvirt_qemu - add import error handling
- virt - Correctly get the error message from libvirt
- virt - Return "changed" status when using "define" command and domain XML was updated
- virt - The define action searchs for the domain name into the xml definition to determine if the domain needs to be created or updated. The xml variable contains the parsed definition but doesn't guarantee the existence of the name tag. This change targets to fix the scenario where the xml var is not empty but doesn't contain a name tag.
- virt_net - The name parameter is not required for the list_nets or facts command so we adjust the module to allow for that.

v1.0.0
======

Major Changes
-------------

- added generic libvirt inventory plugin
- removed libvirt_lxc inventory script
