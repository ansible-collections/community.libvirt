# community.libvirt Collection
[![Build Status](
https://dev.azure.com/ansible/community.libvirt/_apis/build/status/CI?branchName=main)](https://dev.azure.com/ansible/community.libvirt/_build?definitionId=27)
[![Codecov](https://img.shields.io/codecov/c/github/ansible-collections/community.libvirt)](https://codecov.io/gh/ansible-collections/community.libvirt)

This repo hosts the `community.libvirt` Ansible Collection.

The collection includes the libvirt modules and plugins supported by Ansible
libvirt community to help the management of virtual machines and/or containers
via the [libvirt][1] API.

This collection is shipped with the `ansible` package.

[1]: https://libvirt.org/

## Tested with Ansible
<!-- List the versions of Ansible the collection has been tested with. Must match what is in galaxy.yml. -->

- 2.9
- 2.10
- 2.11
- devel

## External requirements
<!-- List any external resources the collection depends on, for example minimum versions of an OS, libraries, or utilities. Do not list other Ansible collections here. -->
- python >= 2.6
- [libvirt-python](https://pypi.org/project/libvirt-python/)

## Included content
<!-- Galaxy will eventually list the module docs within the UI, but until that is ready, you may need to either describe your plugins etc here, or point to an external docsite to cover that information. -->
Modules:

- [virt](https://docs.ansible.com/ansible/latest/collections/community/libvirt/virt_module.html)
- [virt_net](https://docs.ansible.com/ansible/latest/collections/community/libvirt/virt_net_module.html)
- [virt_pool](https://docs.ansible.com/ansible/latest/collections/community/libvirt/virt_pool_module.html)

Inventory:

- [libvirt](https://docs.ansible.com/ansible/latest/collections/community/libvirt/libvirt_inventory.html#ansible-collections-community-libvirt-libvirt-inventory)

Connection:

- [libvirt_lxc](https://docs.ansible.com/ansible/latest/collections/community/libvirt/libvirt_lxc_connection.html#ansible-collections-community-libvirt-libvirt-lxc-connection)
- [libvirt_qemu](https://docs.ansible.com/ansible/latest/collections/community/libvirt/libvirt_qemu_connection.html#ansible-collections-community-libvirt-libvirt-qemu-connection)

## Using this collection
<!--Include some quick examples that cover the most common use cases for your collection content. -->

Before using the libvirt collection, you need to install it with the Ansible Galaxy command-line tool:

```bash
ansible-galaxy collection install community.libvirt
```

You can include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: community.libvirt
```

You can also download the tarball from [Ansible Galaxy](https://galaxy.ansible.com/community/libvirt) and install the collection manually wherever you need.

Note that if you install the collection from Ansible Galaxy with the command-line tool or tarball, it will not be upgraded automatically when you upgrade the Ansible package. To upgrade the collection to the latest available version, run the following command:

```bash
ansible-galaxy collection install community.libvirt --upgrade
```

You can also install a specific version of the collection, for example, if you need to downgrade when something is broken in the latest version (please report an issue in this repository). Use the following syntax:

```bash
ansible-galaxy collection install community.libvirt:==X.Y.Z
```

See [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection
<!--Describe how the community can contribute to your collection. At a minimum, include how and where users can create issues to report problems or request features for this collection.  List contribution requirements, including preferred workflows and necessary testing, so you can benefit from community PRs. -->

The content of this collection is made by people just like you, a community of individuals collaborating on making the world better through developing automation software.

We are actively accepting new contributors.

All types of contributions are very welcome.

You don't know how to start? Refer to our [contribution guide](https://github.com/ansible-collections/community.libvirt/blob/main/CONTRIBUTING.md)!

The aspiration is to follow the following general guidelines:

- Changes should include tests and documentation where appropriate.
- Changes will be lint tested using standard python lint tests.
- No changes which do not pass CI testing will be approved/merged.
- The collection plugins must provide the same coverage of python support as
  the versions of Ansible supported.
- The versions of Ansible supported by the collection must be the same as
  those in developed, or those maintained, as shown in the Ansible [Release and Maintenance][3] documentation.

[3]: https://docs.ansible.com/ansible/latest/reference_appendices/release_and_maintenance.html

As a fallback, the [Ansible Community Guide][4] remains our community
reference set of guidelines.

[4]: https://docs.ansible.com/ansible/latest/community/index.html

### Local Testing

If you want to develop new content for this collection or improve what is
already here, the easiest way to work on the collection is to clone it into
one of the configured [COLLECTIONS_PATHS][5] and work on it there.

[5]:  https://docs.ansible.com/ansible/latest/reference_appendices/config.html#collections-paths

### Testing with `ansible-test`

TBD

### Publishing New Version

Basic instructions without release branches:

1. Create `changelogs/fragments/<version>.yml` with `release_summary:` section (which must be a string, not a list).
2. Run `antsibull-changelog release --collection-flatmap yes`
3. Make sure `CHANGELOG.rst` and `changelogs/changelog.yaml` are added to git, and the deleted fragments have been removed.
4. Tag the commit with `<version>`. Push changes and tag to the main repository.
5. Monitor the release job on the [Zuul Status Dashboard](https://dashboard.zuul.ansible.com/t/ansible/status).
6. Verify that the new version is available on [Ansible Galaxy](https://galaxy.ansible.com/community/libvirt).

## More Information
<!-- List out where the user can find additional information, such as working group meeting times, slack/IRC channels, or documentation for the product this collection automates. -->

### Communication

This is a small collection with a small number of contributors. As such, there
is no formal Ansible Working Group. To communicate with the maintainers, please
make contact via one of the following methods:

- IRC on [irc.libera.chat](https://libera.chat/) in the `#ansible-community` channel
- [Issues](https://github.com/ansible-collections/libvirt/issues) on Github

### Reference

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## License
<!-- Include the appropriate license information here and a pointer to the full licensing details. If the collection contains modules migrated from the ansible/ansible repo, you must use the same license that existed in the ansible/ansible repo. See the GNU license example below. -->

GNU General Public License v3.0 or later.

See [LICENCE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
