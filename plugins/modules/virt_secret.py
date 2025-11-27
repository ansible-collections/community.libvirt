#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2025, Denys Mishchenko <denis@mischenko.org.ua>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: virt_secret
version_added: '2.1.0'
author:
  - Denys Mishchenko (@arddennis)

short_description: Manage libvirt secrets and their values
description:
  - Manage I(libvirt) secrets. Can add, remove or update secrets in libvirt.
  - Can be used to set secrets value.
options:
  uuid:
    description:
      - Secret UUID. The value is unique across all secret types.
      - If UUID value is also defined in the O(xml) this option is ignored.
    type: str
  secret:
    type: dict
    description:
      - Defines a secret as a set of fields instead of raw XML.
      - This property is mutually exclusive with O(xml).
      - If O(uuid) is not defined, O(secret.usage) and O(secret.usage_id) must be defined.
    suboptions:
      ephemeral:
        description:
          - If V(True), secret will only be kept in memory.
          - Default value is V(False).
        type: bool
        default: False
      private:
        description:
          - If V(True), value will not be retrivable from libvirt.
          - Default value is V(False).
        type: bool
        default: True
      usage:
        type: str
        description:
          - Specifies what this secret is used for.
          - Possible values are V(none), V(volume), V(ceph), V(iscsi), V(tls), V(vtpm).
        choices:
          - none
          - volume
          - ceph
          - iscsi
          - tls
          - vtpm
      usage_id:
        description:
          - Defines unique secret_ID. Unique for each O(secret.usage).
        type: str
      description:
        type: str
        description:
          - Defines secret description.
  password:
    description:
      - A value of the secret which will be stored in the libvirt secret.
      - |
        As in majority cases secrets are private, password is defined only
        during secret creation or when O(command=set_value) is executed. If the
        secret already exist and the O(password) is defined, it will not try to
        set it once again. Even if different password is provided.
    type: str
  state:
    description:
      - Alternative for the O(command) option.
      - If V(present), creates a volume described by either O(xml) or O(secret).
      - Can be used to update existing secrets properties.
      - If V(absent), removes secret defined by either O(uuid), O(state) or O(xml).
      - |
        If V(present) and UUID is not specified in either O(uuid) or O(xml), it
        will try to find existing secret using O(secret.usage) and
        O(secret.usage_id)
      - Mutually exclusive with O(command).
    type: str
    choices: [present, absent]
  command:
    choices:
      - create
      - delete
      - list_secrets
      - get_xml
      - set_value
    description:
      - Executes commands to manage secret.
      - |
        If defined V(create), creates secret described by either O(xml)
        or(secret). It is analagous to O(state=present).
      - |
        If defined V(delete), removes secret defined by either O(uuid),
        O(state), O(xml). It is analagous to O(state=absent).
      - |
        If defined V(list_secrets) it will return RV(list_secrets) with all
        existing secrets in XML format.
      - |
        If defined V(get_xml) module will try to get secret definition from
        libvirt. If existing secret found, returns RV(secretXML). Otherwise it
        will return None.
      - |
        If defined V(set_value) module will define a secret value. This command
        is not idempotent and will always show changed. Requires O(password) to
        be defined.
    type: str
extends_documentation_fragment:
  - community.libvirt.virt.options_uri
  - community.libvirt.virt.options_xml
requirements:
  - "libvirt"
  - "lxml"
  - "PyYAML"
attributes:
  check_mode:
    description: Check mode is fully supported.
    support: full
    details:
      - In check mode, secrets are not actually created, updated or deleted.
      - |
        Module compares existing state of the secret in libvirt and check if
        change is required.
      - Will always produce changed with O(command=set_value).
  diff_mode:
    description: Module provides state change as a dict.
    support: full
    details:
      - |
        For all made changes except O(command=set_value) module will return
        diff in a dict form to illustrate was was changed.
      - |
        In check_mode diff will contain the same output as if it was executed
        normally.
  idempotent:
    description: In most cases, this module is idempotent.
    support: partial
    details:
      - |
        If O(command=set_value) the module is not idempotent as it don't try to
        get secrets from libvirt and always return changed.
      - In most of the cases secrets are private and their value is not
        obtainable from the libvirt.
'''


RETURN = r'''
secretXML:
  type: str
  description: When I(command=get_xml) return xml definition of the secret
  returned: success
  sample: |
    <secret ephemeral="no" private="yes">
      <uuid>e4b5978c-ba37-5605-97c1-4a20413d0fc9</uuid>
      <description>test_secret pool secret</description>
      <usage type="ceph">
        <name>test_secret</name>
      </usage>
    </secret>"
list_secrets:
  type: list
  elements: str
  returned: success
  description: When (command=list_secrets) returns secrets_list of secrets in xml format
  sample:
    - |
      <secret ephemeral='no' private='yes'>
        <uuid>fce0c61a-f0fc-5727-90b2-56c92534070f</uuid>
        <description>sample vTPM secret</description>
        <usage type='vtpm'><name>VTPM_example</name></usage></secret>
    - |
      <secret ephemeral='no' private='yes'>
        <uuid>e4b5978c-ba37-5605-97c1-4a20413d0fc9</uuid>
        <description>changed_test pool secret</description>
        <usage type='ceph'><name>test_secret</name></usage>
      </secret>
    - |
      <secret ephemeral='no' private='yes'>
        <uuid>edfa6124-eb0e-4449-a680-66f5fa7aedeb</uuid>
        <description>Secret puppy name</description>
        <usage type='volume'><volume>/var/lib/libvirt/images/puppyname.img</volume></usage>
      </secret>
'''


EXAMPLES = r'''
---
- name: Create new secret using xml definition and command
  community.libvirt.virt_secret:
    command: create
    xml: |
      <secret ephemeral='no' private='yes'>
        <uuid>e4b5978c-ba37-5605-97c1-4a20413d0fc9</uuid>
        <description>test ceph pool secret</description>
        <usage type='ceph'>
        <name>test_secret</name>
        </usage>
      </secret>

- name: Get secret XML by uuid
  community.libvirt.virt_secret:
    uuid: e4b5978c-ba37-5605-97c1-4a20413d0fc9
    command: get_xml
  register: result

- name: Get XML by secret usage and usage_id
  community.libvirt.virt_secret:
    secret:
      usage: ceph
      usage_id: test_secret
    command: get_xml
  register: result

- name: Print found XML
  ansible.builtin.debug:
    var: result.secretXML

- name: Define secret using options secret and uuid
  community.libvirt.virt_secret:
    uuid: e4b5978c-ba37-5605-97c1-4a20413d0fc9
    secret:
      usage: tls
      usage_id: test_secret
      description: Test TLS secret
    state: present

- name: List all currently defined secrets
  community.libvirt.virt_secret:
    command: list_secrets
  register: result

- name: Print found secrets list
  ansible.builtin.debug:
    var: result.secrets_list

- name: Set value of the secret
  community.libvirt.virt_secret:
    uuid: e4b5978c-ba37-5605-97c1-4a20413d0fc9
    command: set_value
    password: somesecureandrandomsecret1234

- name: Remove secret
  community.libvirt.virt_secret:
    uuid: 57ea8fd0-9b82-4e54-9d16-df7d2765844d
    state: absent
'''


# ansible module_utils uses own path structure and must be imported first
# pylint: disable-next=no-name-in-module,import-error,wrong-import-order
from ansible_collections.community.libvirt.plugins.module_utils.common import (
    VirtModule, libvirt_error_to_none)
from dataclasses import dataclass, asdict
from typing import Union

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree


COMMAND_CHOICES = [
    'create',
    'delete',
    'list_secrets',
    'get_xml',
    'set_value'
]


# https://libvirt.org/formatsecret.html
USAGE_TYPES_TAGS = {
    'none': 'name',
    'volume': 'volume',
    'ceph': 'name',
    'iscsi': 'target',
    'tls': 'name',
    'vtpm': 'name'
}


# https://libvirt.org/html/libvirt-libvirt-secret.html#virSecretUsageType
VIR_SECRET_USAGE_TYPE = {
    0: 'none',
    1: 'volume',
    2: 'ceph',
    3: 'iscsi',
    4: 'tls',
    5: 'vtpm'
}


VIR_SECRET_USAGE_ID = {
    'none': 0,
    'volume': 1,
    'ceph': 2,
    'iscsi': 3,
    'tls': 4,
    'vtpm': 5
}


bool_map = {
    'yes': True,
    'no': False
}


@dataclass
class SecretUsage():
    """ libvirt secret usage type """
    type: str
    values: list

    def to_xml(self) -> etree.Element:
        """ Form usage element of the secret element """
        element = etree.Element('usage', type=self.type)
        for sub in self.values:
            subelement = etree.Element('name')
            subelement.text = sub
            element.append(subelement)
        return element


@dataclass
class SecretElement():
    """ Libvirt secret record """
    uuid: Union[str, None]  # We might not have uuid defined in the module
    usage: str
    usageid: str
    ephemeral: bool = False
    private: bool = True
    description: Union[str, None] = ''

    def to_xmlstr(self) -> str:
        """ form xml secret suitable for libvirt """
        is_efemeral = 'yes' if self.ephemeral else 'no'
        is_private = 'yes' if self.private else 'no'
        the_element = etree.Element(
            'secret', ephemeral=is_efemeral, private=is_private)
        if self.uuid:
            the_element.append(self._uuid_element)
        the_element.append(self._description_element)
        the_element.append(self._usage_element)
        return etree.tostring(the_element, encoding='unicode')

    @property
    def _usage_element(self):
        """ Forms usage element """
        usage = etree.Element('usage', type=self.usage)
        usage_id = etree.Element(USAGE_TYPES_TAGS[self.usage])
        usage_id.text = self.usageid
        usage.append(usage_id)
        return usage

    @property
    def _uuid_element(self):
        """ Forms uuid element """
        uuid = etree.Element('uuid')
        uuid.text = self.uuid
        return uuid

    @property
    def _description_element(self):
        """ Forms description element """
        description = etree.Element('description')
        if self.description:
            description.text = self.description
        else:
            description.text = ""
        return description


class LibvirtSecretModule(VirtModule):
    """ Libvirt secrets manipulation module """

    def logic(self):
        """ Module logic not covered by direct function calls

        As state and command are mutual params and one of them is required
        we could get here only if state is already defined and of a correct
        value """

        state = self.ansible.params.get('state')
        if state == 'present':
            self.create()
        elif state == 'absent':
            self.delete()

    def create(self):
        """ Secret create function

        If secret with defined UUID already exist, it will compare its
        attributes to a defined ones. If a difference is found, it will replace
        the secret attributes with the defined ones.
        If we do not have UUID defined it will try to find the secret using its
        usage and usageID which must be unique set. If found UUID of existing
        secret will be assumed as a defined one for the attributes comparsion.
        In case existing secret was not found, a new one will be created.
        """
        self._check_duplicated_uuid()  # A warning for UUID defined twice
        defined_element = self.defined_element
        password = self.ansible.params.get('password')

        existing_virtsecret = self.get_virsecret()
        existing_element = self._form_element_from_virtsecret(
            existing_virtsecret)

        # We might have created secret without uuid supplied, but want to
        # compare objects defined vs existing
        if defined_element.uuid is None and existing_element:
            defined_element.uuid = existing_element.uuid

        if defined_element != existing_element:
            self.mod_status.changed = True
            if existing_element is not None:
                self.mod_status.before = asdict(existing_element)
            else:
                self.mod_status.before = {}
            self.mod_status.after = asdict(defined_element)
            if not self.check:
                self.conn.secretDefineXML(defined_element.to_xmlstr())
                created_secret = self.get_virsecret()
                if created_secret is None:
                    self.mod_status.failed = True
                    self.mod_status.msg = "Failed to create a secret."
                    self.exit()
                if password is not None:
                    created_secret.setValue(password)
        self.exit()

    @libvirt_error_to_none
    def get_virsecret(self):
        """ Lookup of the secret by its uuid or usage

        Ansible module will make sure that uuid, secret or xml is defined.

        :return: libvirt.virSecret object or None if it wasn't found
        """
        if self.defined_uuid:
            return self.conn.secretLookupByUUIDString(self.defined_uuid)
        secret = self.defined_element
        if secret is None:
            return None
        if secret.usage is None or secret.usageid is None:
            self.mod_status.failed = True
            self.mod_status.msg = \
                "Usage and usage_id must be defined if uuid is missing"
            self.exit()
        int_usage = VIR_SECRET_USAGE_ID[secret.usage]
        return self.conn.secretLookupByUsage(int_usage, secret.usageid)

    def _form_element_from_virtsecret(self, element) -> Union[
            SecretElement, None]:
        """ Convert libvirt.virSecret to SecretElement

        :param element: libvirt.virSecret object
        :return: SecretElement class secret
        """
        if element is None:
            return None

        an_xml = etree.fromstring(element.XMLDesc())
        return SecretElement(
            uuid=element.UUIDString(),
            usage=VIR_SECRET_USAGE_TYPE[element.usageType()],
            usageid=element.usageID(),
            ephemeral=bool_map[an_xml.get('ephemeral', 'no')],
            private=bool_map[an_xml.get('private', 'yes')],
            description=an_xml.findtext('description'))

    @property
    def defined_xml(self) -> Union[str, None]:
        """ Forms defined XML

        It looks like this function has chicken and the egg problem, but if
        xml property is defined, defined_element will be calculated first based
        on its values. If it is not, we expect secret to be defined and will
        use it instead.
        """
        defined_xml = self.ansible.params.get('xml')
        if defined_xml is not None:
            return defined_xml
        # To break possible infinity recursion we'll check for secret here as
        # we already know that xml is not defined
        if self.ansible.params.get('secret') is not None:
            element = self.defined_element
            if element is not None:
                return element.to_xmlstr()
        return None

    @property
    def defined_element(self) -> Union[SecretElement, None]:
        """ generate defined secret element """
        secret = self.ansible.params.get('secret')
        if secret is not None:
            return self._parse_secret_param()
        if self.defined_xml is not None:
            return self._parse_xml_secret(self.defined_xml)
        return None

    def _check_duplicated_uuid(self) -> None:
        """ Get UUID provided in the module params

        We need to inform user if uuid was provided multiple times
        UUID from XML takes precedance over uuid param. Function is dedicated
        for exactly this purpose to not produce multiple warnings.
        """

        param_uuid = self.ansible.params.get('uuid')
        if self.defined_xml_uuid is not None and param_uuid is not None:
            self.ansible.warn(
                'UUID provided multiple times, using the one defined in XML!')
        return

    @property
    def defined_xml_uuid(self) -> Union[str, None]:
        """ Finds if we have defined UUID in the XML param """
        xml = self.ansible.params.get('xml')
        if xml is None:
            return None
        secret_element = etree.fromstring(xml)
        return secret_element.findtext('uuid')

    @property
    def defined_uuid(self) -> Union[str, None]:
        """ Defined UUID either in XML or as a separate param """
        xml_uuid = self.defined_xml_uuid
        param_uuid = self.ansible.params.get('uuid')
        return xml_uuid if xml_uuid is not None else param_uuid

    def _parse_secret_param(self) -> SecretElement:
        """ Form SecretElement from secret module params """
        secret_param = self.ansible.params.get('secret')
        usage_id = secret_param.get('usage_id')
        if usage_id is None:
            self.mod_status.failed = True
            self.mod_status.msg = "usageid is requrired to create a secret"
            self.exit()
        element = SecretElement(
            uuid=self.ansible.params.get('uuid'),
            usage=secret_param.get('usage', 'none'),
            usageid=usage_id,
            ephemeral=secret_param.get('ephemeral', False),
            private=secret_param.get('private', True),
            description=secret_param.get('description', '')
        )
        return element

    def _parse_xml_secret(self, xml: str) -> Union[SecretElement, None]:
        """ Parse xml string and return it as SecretElement object

        :param xml: string containing xml of the secret. Param left for future
                    reuse of the function.
        """
        an_xml = etree.fromstring(xml)
        # Usage element must be present along with its usageid
        usage_element = an_xml.find('usage')
        if usage_element is not None:
            usage = usage_element.get('type', 'none')
            childrens = usage_element.getchildren()
            if childrens:
                if len(childrens) > 0:
                    usage_id = childrens[0].text
                else:
                    self.mod_status.failed = True
                    self.mod_status.mgs = 'Unable to find usageid in the xml'
                    self.exit()
                    usage_id = 'error'
            else:
                self.mod_status.failed = True
                self.mod_status.mgs = 'Unable to find usageid in the xml'
                self.exit()
                return None  # never reached, but better than linter asertion
        else:
            self.mod_status.failed = True
            self.mod_status.mgs = 'Unable to find usage element in the xml'
            self.exit()
            return None  # never reached, but better than linter asertion

        uuid_element = an_xml.find('uuid')
        if uuid_element is not None:
            a_uuid = uuid_element.text
        else:
            a_uuid = self.ansible.params.get('uuid')

        element = SecretElement(
            uuid=a_uuid,
            usage=usage,
            usageid=usage_id,
            ephemeral=bool_map[an_xml.get('ephemeral', 'no')],
            private=bool_map[an_xml.get('private', 'yes')],
            description=an_xml.findtext('description'))

        return element

    def delete(self):
        """ Delete defined secret """

        virsecret = self.get_virsecret()
        before = self._form_element_from_virtsecret(virsecret)
        if before is not None:
            self.mod_status.before = asdict(before)
        else:
            self.mod_status.msg = "Requested secret not found"
            self.exit()

        if not self.check:
            virsecret.undefine()  # type: ignore
        self.mod_status.changed = True
        self.mod_status.after = {}
        self.exit()

    def list_secrets(self):
        """ Get list of defined secrets and return them as list of xmls """

        current_secrets = [
            secret.XMLDesc()
            for secret in self.conn.listAllSecrets()]
        if len(current_secrets) > 0:
            self.mod_status.msg = "Found defined secrets"
        else:
            self.mod_status.msg = "No secrets currently defined"
        self.mod_status.data = {
            'secrets_list': current_secrets}
        self.exit()

    def set_value(self):
        """ Set secret value to a defined password """
        password = self.ansible.params.get('password')
        virsecret = self.get_virsecret()
        if virsecret is None:
            self.mod_status.failed = True
            self.mod_status.msg = "Unable to find a secret to set a value"
            self.exit()
        if not self.check:
            result = virsecret.setValue(password)
            if result != 0:
                self.mod_status.failed = True
                self.mod_status.msg = "Failed to set the value"
        self.mod_status.msg = "The value for the secret was successfully set"
        self.mod_status.changed = True
        self.exit()

    def get_xml(self):
        """ Get defined secret XML

        There are two options to get the secret: using uuid and by its usage
        """
        virsecret = self.get_virsecret()
        secret_object = self._form_element_from_virtsecret(virsecret)
        if secret_object:
            result = secret_object.to_xmlstr()
            self.mod_status.msg = "Found secret"
        else:
            self.mod_status.msg = "Secret not found"
            result = None
        self.mod_status.data = {'secretXML': result}
        self.exit()

    def secret_undefine(self):
        """ Undefine secret if it exist """


def main():
    """ Module execution """
    argument_spec = {
        'uuid': {'type': 'str'},
        'secret': {
            'type': 'dict',
            'no_log': False,
            "options": {
                'ephemeral': {'type': 'bool', 'default': False},
                'private': {'type': 'bool', 'default': True},
                'usage': {'type': 'str',
                          'choices': [
                              'none',
                              'volume',
                              'ceph',
                              'iscsi',
                              'tls',
                              'vtpm']},
                'usage_id': {'type': 'str'},
                'description': {'type': 'str'}}},
        'password': {'type': 'str', 'no_log': True},
        'uri': {'type': 'str', 'default': 'qemu:///system'},
        'state': {'type': 'str', 'choices': ['present', 'absent']},
        'command': {'type': 'str', 'choices': COMMAND_CHOICES},
        'xml': {'type': 'str'}}
    required_if = [
        ('state', 'present', ['xml', 'secret'], True),
        ('state', 'absent', ['uuid', 'secret', 'xml'], True),
        ('command', 'create', ['xml', 'secret'], True),
        ('command', 'delete', ['uuid', 'xml', 'secret'], True),
        ('command', 'set_value', ['password'], False),
        ('command', 'get_xml', ['uuid', 'secret'], True)]
    mutually_exclusive = [['state', 'command'], ['xml', 'secret']]
    required_one_of = [('state', 'command')]

    module = LibvirtSecretModule(argument_spec=argument_spec,
                                 required_if=required_if,
                                 mutually_exclusive=mutually_exclusive,
                                 required_one_of=required_one_of,
                                 supports_check_mode=True)
    module.run()


if __name__ == '__main__':
    main()
