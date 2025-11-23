#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2025, Denys Mishchenko <denis@mischenko.org.ua>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# ansible module_utils uses own path structure and must be imported first
# pylint: disable-next=no-name-in-module,import-error,wrong-import-order
from ansible_collections.community.libvirt.plugins.module_utils.common import (
    VirtModule, libvirt_error_to_none, STATE_CHOICES)
from dataclasses import dataclass, asdict
# from copy import deepcopy
import epdb;

try:
    from libvirt import libvirtError
except ImportError:
    pass  # do nothing, exception handling will happen in a common module

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
    uuid: str| None  # We might not have uuid defined in the module
    usage: str
    usageid: str
    ephemeral: bool = False
    private: bool = True
    description: str|None = ''

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

        existing_virtsecret = self.get_virsecret()
        existing_element = self._form_element_from_virtsecret(
            existing_virtsecret)

        # TODO: Check if defined element was at all defined
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

    def _form_element_from_virtsecret(self, element) -> SecretElement|None:
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
    def defined_xml(self) -> str|None:
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
    def defined_element(self) -> SecretElement|None:
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
    def defined_xml_uuid(self) -> str|None:
        """ Finds if we have defined UUID in the XML param """
        xml = self.ansible.params.get('xml')
        if xml is None:
            return None
        secret_element = etree.fromstring(xml)
        return secret_element.findtext('uuid')

    @property
    def defined_uuid(self) -> str|None:
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

    def _parse_xml_secret(self, xml:str) -> SecretElement|None:
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
            'ephemeral': {'type': bool, 'default': False},
            'private': {'type': bool, 'default': True},
            'usage': {'type': 'str',
                      'choices': VIR_SECRET_USAGE_TYPE.values()},
            'usage_id': {'type': 'list', 'elements': 'str'},
            'description': {'type': 'str'}},
        'password': {'type': 'str', 'no_log': True},
        'uri': {'type': 'str', 'default': 'qemu:///system'},
        'state': {'type': 'str', 'choices': STATE_CHOICES},
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
    required_one_of=[('state', 'command')]

    module = LibvirtSecretModule(argument_spec=argument_spec,
                                 required_if=required_if,
                                 mutually_exclusive=mutually_exclusive,
                                 required_one_of=required_one_of,
                                 supports_check_mode=True)
    module.run()


if __name__ == '__main__':
    main()
