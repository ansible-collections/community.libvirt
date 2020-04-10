#!/bin/sh

# Exit on errors, exit when accessing unset variables and print all commands
set -eux

# Testing qemu connection
export ANSIBLE_INVENTORY="./libvirt_qemu.yml"
ansible-playbook playbooks/test-inventory.yml "$@"


# Testing lxc connection
export ANSIBLE_INVENTORY="./libvirt_lxc.yml"
ansible-playbook playbooks/test-inventory.yml "$@"
