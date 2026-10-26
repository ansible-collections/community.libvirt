# community.libvirt integration tests

Integration targets live under `tests/integration/targets/`. Most module targets
are Ansible roles with assertions in `tasks/`; some plugin targets contain shell
runners or inventory fixtures. This document describes the targets present in
the repository, their execution requirements, and their CI selection. A target's
presence or CI group assignment does not by itself mean it currently runs or
passes on every platform.

## Targets and coverage

Group names below abbreviate `shippable/posix/group1` and
`shippable/posix/group2`. The descriptions summarize the checked-in tasks and
fixtures rather than claiming complete coverage of each module's options.

| Target | Purpose / checked behavior | Selection |
| --- | --- | --- |
| [`virt`](targets/virt/tasks/define_check_mode.yml) | Define, start and undefine a domain, with check-mode predictions before and after each action | group1 |
| [`virt_net`](targets/virt_net/tasks/main.yml) | Network definition, activation, facts, listing, removal and repeated operations | group1 |
| [`virt_pool`](targets/virt_pool/tasks/directory_based_pool.yml) | Directory pool definition, activation, deactivation and undefinition, including check mode | group1 |
| [`virt_volume`](targets/virt_volume/tasks/main.yml) | Volume creation, listing, deletion, cloning, wiping, CIDATA creation and resizing | group1 |
| [`virt_secret`](targets/virt_secret/tasks/main.yml) | Secret definition, lookup, updates, values, usage types, listing, deletion and idempotency | group1 |
| [`virt_install`](targets/virt_install/tasks/main.yml) | Provisioning lifecycle, import/no-install modes, real recreation, check mode and input failures | group2 |
| [`virt_cloud_instance`](targets/virt_cloud_instance/tasks/main.yml) | Provisioning lifecycle, local image processing, loopback HTTP downloads, cache, checksums and failures | group2 |
| [`virt_interfaces`](targets/virt_interfaces/tasks/main.yml) | `virt` interface reporting and MAC address assertions | No aliases or CI group |
| [`virt_undefine`](targets/virt_undefine/tasks/main.yml) | `virt` deletion of an attached volume while retaining its backing image | No aliases or CI group |
| [`inventory_libvirt`](targets/inventory_libvirt/runme.sh) | Load QEMU and LXC inventories and display host variables | unsupported |
| [`connection_libvirt_qemu`](targets/connection_libvirt_qemu/test_connection.inventory) | QEMU connection inventory with pipelining enabled/disabled | unsupported; incomplete runner |
| [`connection_libvirt_lxc`](targets/connection_libvirt_lxc/runme.sh) | LXC connection inventory and a reference to the shared connection harness | unsupported; external harness required |
| [`setup_virt_install`](targets/setup_virt_install/tasks/main.yml) | Shared environment and resource helpers for the two provisioning targets | hidden dependency |

## Running tests

Run from the collection root, at a path ending in
`ansible_collections/community/libvirt`. Docker and Podman both use the
`ansible-test --docker` interface. With both installed, select Podman explicitly:

```bash
export ANSIBLE_TEST_PREFER_PODMAN=1
ansible-test integration --help
```

Choose a distribution image listed by the installed ansible-test version when
testing system packages and libvirt services. The `default` sanity/unit image
does not establish that a service-based integration environment will work.

List runnable targets in each group before running them:

```bash
ansible-test integration shippable/posix/group1/ --docker ubuntu2404 --docker-privileged --list-targets
ansible-test integration shippable/posix/group2/ --docker ubuntu2404 --docker-privileged --list-targets
```

Run an individual module or an explicitly selected group:

```bash
ansible-test integration virt --docker ubuntu2404 --docker-privileged
ansible-test integration virt_net --docker ubuntu2404 --docker-privileged
ansible-test integration shippable/posix/group1/ --docker ubuntu2404 --docker-privileged
ansible-test integration shippable/posix/group2/ --docker ubuntu2404 --docker-privileged
```

Both groups declare `needs/privileged`; without `--docker-privileged` they are
excluded under `--docker`. They also declare `destructive`: unmanaged-host
execution requires `--allow-destructive`. Use disposable test environments;
these tests manage domains, storage, networks, secrets and system packages.

`unsupported` and `disabled` targets are excluded by default. Their override
flags are `--allow-unsupported` and `--allow-disabled`, respectively. Enabling a
flag only changes selection; it does not provide missing guests or runners.
Read the target-specific limitations below before selecting those targets.

Inspect warnings, executed tasks, assertions and JUnit results under
`tests/output/`. An exit status of zero with all targets skipped is not evidence
that integration behavior was tested.

## Connections and environment setup

The `virt`, `virt_net`, `virt_pool`, `virt_volume` and `virt_secret` tasks omit
`uri` and use their modules' `qemu:///system` default. `virt_install`,
`virt_cloud_instance`, `virt_interfaces` and `virt_undefine` specify that URI
explicitly. These module tests connect to real libvirt rather than the in-memory
test driver.

The connection URI and virtualization mode are separate settings. The main
`virt` XML fixture uses `<domain type='qemu'>`, and the two provisioning targets
set `virt_type: qemu` for software emulation. The `virt_interfaces` and
`virt_undefine` XML fixtures instead specify `type='kvm'`; do not infer that all
targets are independent of KVM simply because they use the same URI.

The group1 roles load distribution-specific package variables and start
libvirtd individually. Several stop the service and remove libvirt packages in
their cleanup. They do not use the provisioning targets' shared setup or its
rootless-container profile. Package variables and cleanup behavior must be
checked per target when using another distribution or running multiple groups.

The inventory target has separate `qemu:///system` and `lxc:///` configurations.
The QEMU connection plugin defaults to `qemu:///system`; the LXC connection
plugin uses `lxc:///`. These plugin targets expect an already prepared libvirt
environment. The connection inventories name an existing guest,
`lv-ubuntu-wily-amd64`. The QEMU target currently has no runner, and the LXC runner
references `../connection/test.sh`, which is not included in this collection.
They are not self-contained container tests.

The `virt_interfaces` and `virt_undefine` roles likewise assume libvirt and their
other prerequisites have been prepared. Their accompanying Dockerfiles are not
used by the CI script or automatically built by ansible-test. They reference
external `config/pools/` and `config/networks/` build inputs not present here;
they are not ready-made replacements for ansible-test distribution images.

## CI selection

[`tests/utils/shippable/linux.sh`](../utils/shippable/linux.sh) selects
`shippable/posix/groupN/` from the final number in its job argument. The
[`Azure matrix`](../../.azure-pipelines/azure-pipelines.yml) determines which
core versions and distribution images invoke each group.

| Group | Targets | Configured CI behavior |
| --- | --- | --- |
| group1 | `virt`, `virt_net`, `virt_pool`, `virt_volume`, `virt_secret` | Existing `/1` jobs on core 2.17 through 2.21 and devel omit `--docker-privileged`, so these targets are excluded by their privileged requirement |
| group2 | `virt_install`, `virt_cloud_instance` | Dedicated `/2` jobs on core 2.21 and devel add `--docker-privileged` |

Targets without a group and targets marked `unsupported` are not selected by
these grouped CI jobs. `setup_virt_install` runs as a role dependency of the
provisioning targets. The shared wrapper may also pass `--changed`, which narrows
selection to affected targets. Group1's privilege omission remains a separate
CI limitation; adding the group2 jobs does not enable the older suite.

## Provisioning module tests

`virt_install` and `virt_cloud_instance` use a real `qemu:///system` connection
and QEMU software emulation. They do not require `/dev/kvm`, nested hardware
virtualization, public cloud images, or a guest OS installation. Supported test
hosts are x86_64 Ubuntu and Fedora, using the distribution's system Python.

Run from the collection root, using Docker or Podman:

```bash
export ANSIBLE_TEST_PREFER_PODMAN=1
ansible-test integration virt_install virt_cloud_instance --docker ubuntu2404 --docker-privileged
ansible-test integration virt_install virt_cloud_instance --docker ubuntu2204 --docker-privileged
ansible-test integration virt_install virt_cloud_instance --docker fedora43 --docker-privileged
```

The shared `setup_virt_install` role installs distribution packages and starts
libvirtd. In containers only, it runs QEMU as container root and disables nested
DAC owner tracking and private device mount namespaces. This supports rootless
Podman; it does not modify the host's libvirt configuration. Container images and
distribution packages still need to be available through the normal CI mirrors
or caches.

Each target allocates a unique directory and directory storage pool. An `always`
block removes its domains, pool and files even after assertion failures. The HTTP
server binds only to loopback on an automatically allocated port and is stopped
in its own `always` block. Shared packages and the daemon remain available for
the next target; ansible-test discards the container when finished.

### Coverage

Both modules check creation, return values, check mode, idempotency, unchanged
existing definitions, predicted and real recreation of running/stopped domains,
and deletion. Recreation previews must preserve domain XML, UUID, running state
and disk identity; stopped guests also have their disk checksum compared.
State is verified with virsh, domain XML and filesystem queries, independently
of the module under test. The installation target covers both `import` and
`install.no_install`, running/stopped deletion and invalid wait timeouts.

Cloud instance fixtures are generated locally: a 64 MiB raw image containing a
known nonzero data block, its qcow2 conversion, and gzip/bzip2/xz variants. Tests
verify expanded capacity, format and actual copied data after stopping QEMU.
They also test orphan disk protection and explicit `force_disk` replacement.
Missing images, undersized target disks, corrupt compressed images and empty
disk lists must fail before creating a domain or system disk. Checksums verify
that the original raw and qcow2 fixtures survive all provisioning and deletion.

A standard-library HTTP server serves these fixtures from inside the test
container. The tests exercise download, cache reuse, `force_pull`, inline and URL
checksums, checksum mismatch and HTTP 404. Request logs verify that check mode
does not download the image and cache hits avoid another request. A changed
server copy verifies that cache reuse really uses the cached content. Forced
refresh must download that changed content and update both the provisioned disk
and the cached checksum.

Expected negative cases use `ignore_errors` followed by explicit failure/state
assertions; they do not count as unverified ignored failures.

For example, `virt_install` intentionally passes `wait_timeout: 0`. The module
must reject it, so Ansible prints `FAILED` with
`wait_timeout must be a positive integer (seconds)`, followed by `...ignoring`.
The following assertion must then pass. A successful run can therefore end with
`failed=0` and `ignored=1`; check the final `PLAY RECAP` and command exit status
rather than treating each red task message as a suite failure. The cloud target
similarly checks expected disk conflicts, invalid images and HTTP failures.

These resource tests set `wait_for_cloud_init_reboot: false`. They do not cover
guest cloud-init execution, reboots, OS installation or installation waiting.
Those require a separately provisioned, pinned, bootable image fixture. HTTP
authentication, controlled download timeouts and check-mode validation of a
forced refresh with a newly supplied checksum can be added independently.

### Recreation previews

The recreation check-mode regressions run in the normal `virt_install` and
`virt_cloud_instance` targets. No separate disabled target needs to be enabled.
For an existing guest with `recreate: true`, the modules validate basic parameter
combinations and report a change without executing provisioning commands. The
cloud module also skips image processing. These previews predict replacement;
they do not fully validate image contents, disk capacity or resource conflicts,
and do not guarantee that actual recreation will succeed.

When the guest does not exist, `recreate: true` still uses the normal initial
creation dry run. Both targets assert that this path executes `virt-install
--dry-run` and creates no guest or disk. Actual recreation and orphan disk
protection remain covered separately.
