# community.libvirt Collection
<!-- Add CI and code coverage badges here. -->
<!-- Describe the collection and why a user would want to use it. What does the collection do? -->

This repo hosts the `community.libvirt` Ansible Collection.

The collection includes the libvirt modules and plugins supported by Ansible
libvirt community to help the management of virtual machines and/or containers
via the [libvirt][1] API.

[1]: https://libvirt.org/

## Tested with Ansible
<!-- List the versions of Ansible the collection has been tested with. Must match what is in galaxy.yml. -->
TBD

## External requirements
<!-- List any external resources the collection depends on, for example minimum versions of an OS, libraries, or utilities. Do not list other Ansible collections here. -->
TBD

### Supported connections
<!-- Optional. If your collection supports only specific connection types (such as HTTPAPI, netconf, or others), list them here. -->
TBD

## Included content
<!-- Galaxy will eventually list the module docs within the UI, but until that is ready, you may need to either describe your plugins etc here, or point to an external docsite to cover that information. -->
TBD

## Using this collection
<!--Include some quick examples that cover the most common use cases for your collection content. -->

Before using the libvirt community collection, you need to install the
collection with the `ansible-galaxy` CLI:

```bash
ansible-galaxy collection install community.libvirt
```

Alternatively, you can also include it in a `requirements.yml` file and
install it via `ansible-galaxy collection install -r requirements.yml` using
the format:

```yaml
collections:
- name: community.libvirt
```

For more information regarding using collections with Ansible, see the Ansible
[user guide][3].

[3]: https://docs.ansible.com/ansible/latest/user_guide/collections_using.html

## Contributing to this collection
<!--Describe how the community can contribute to your collection. At a minimum, include how and where users can create issues to report problems or request features for this collection.  List contribution requirements, including preferred workflows and necessary testing, so you can benefit from community PRs. -->

While this community is still developing its guidelines, the aspiration is to
follow the following general guidelines:

- Changes should include tests and documentation where appropriate.
- Changes will be lint tested using standard python lint tests.
- No changes which do not pass CI testing will be approved/merged.
- The collection plugins must provide the same coverage of python support as
  the versions of Ansible supported.
- The versions of Ansible supported by the collection must be the same as
  those in developed, or those maintained, as shown in the Ansible [Release
  and Maintenance][4] documentation.

[4]: https://docs.ansible.com/ansible/latest/reference_appendices/release_and_maintenance.html

As a fallback, the [Ansible Community Guide][5] remains our community
reference set of guidelines.

[5]: https://docs.ansible.com/ansible/latest/community/index.html

### Local Testing

If you want to develop new content for this collection or improve what is
already here, the easiest way to work on the collection is to clone it into
one of the configured [COLLECTIONS_PATHS][2] and work on it there.

[2]:  https://docs.ansible.com/ansible/latest/reference_appendices/config.html#collections-paths

### Testing with `ansible-test`

TBD

### Publishing New Version

TBD

## More Information
<!-- List out where the user can find additional information, such as working group meeting times, slack/IRC channels, or documentation for the product this collection automates. -->

### Communication

This is a small collection with a small number of contributors. As such, there
is no formal Ansible Working Group. To communicate with the maintainers, please
make contact via one of the following methods:

- IRC on Freenode in #ansible-community
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
