===============================
Community.Libvirt Release Notes
===============================

.. contents:: Topics


v1.0.1
======

Bugfixes
--------

- libvirt_qemu - Mitigate a CPU hammering active wait loop
- libvirt_qemu - add import error handling
- virt - Correctly get the error message from libvirt
- virt - Return "changed" status when using "define" command and domain XML was updated
- virt - Fix not domain found for define command
- virt_net - Make name parameter optional

v1.0.0
======

Major Changes
-------------

- added generic libvirt inventory plugin
- removed libvirt_lxc inventory script
