# (c) 2025, Denys Mishchenko <denis@mischenko.org.ua>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import abc
from dataclasses import dataclass
from dataclasses import asdict
from dataclasses import field
from typing import Dict
from typing import List
from typing import Union

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import missing_required_lib


try:
    import libvirt
    LIBVIRT_IMPORT_ERR = None
except ImportError as libvirt_import_exception:
    LIBVIRT_IMPORT_ERR = libvirt_import_exception


try:
    from lxml import etree
    LXML_IMPORT_ERR = None
except ImportError as lxml_import_exception:
    LXML_IMPORT_ERR = lxml_import_exception
    import xml.etree.ElementTree as etree

try:
    from yaml import safe_dump
except ImportError as safe_dump_import_exception:
    SAFE_DUMP_IMPORT_ERR = safe_dump_import_exception
else:
    SAFE_DUMP_IMPORT_ERR = None


STATE_CHOICES = ['present', 'absent']


def compare_dicts(dict_one: dict, dict_two: dict) -> bool:
    """ Compare two dicts.

    Return True if two dict contents are equal
    """
    for item, value in dict_one.items():
        if item not in dict_two.keys():
            return False
        if isinstance(value, dict):
            if not compare_dicts(value, dict_two[item]):
                return False
            continue
        if isinstance(value, list):
            if not compare_lists(value, dict_two[item]):
                return False
            continue
        if value != dict_two[item]:
            return False
    return True


def compare_lists(list_one: list, list_two: list) -> bool:
    """ Compare two unsorted lists """
    if list_one == list_two:
        return True
    # Lists are not sorted and compare is faster than sorting or copying, so...
    # it might be that I am re-inventing the wheel here...
    for item in list_one:
        if item not in list_two:
            return False
    for item in list_two:
        if item not in list_one:
            return False
    return True


def libvirt_error_to_none(func):
    """ Decorator to replace libvirt errors to None value return

    When we search for absent object in libvirt we get exception, but
    sometimes we just want a None value to be returned instead.

    :param func: Callable function to wrap and check the status.
        """

    def wrapper(self, **kwargs):
        try:
            return func(self)
        except libvirt.libvirtError:
            return None
    return wrapper


@dataclass
class ModuleStatus:
    """ Ansible module status """
    changed: bool = False
    failed: bool = False
    msg: Union[str, None] = None  # linter refuse 'str | None'
    exception: Union[str, ImportError, None] = None
    before: Dict = field(default_factory=dict)
    after: Dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    data: Dict = field(default_factory=dict)

    @property
    def report(self):
        """ Forms a dict suitable for ansible return """
        ansible_report = {
            "changed": self.changed,
            "failed": self.failed,
            "msg": self.msg
        }
        if self.failed and self.exception is not None:
            ansible_report['exception'] = self.exception
            return ansible_report
        if self.changed:
            # changes may have diff definition, so diff should be added
            ansible_report['diff'] = {
                'before': safe_dump(self.before),
                'after': safe_dump(self.after)}
            # TODO: Add sort on results to produce better diff
        # We may have additional data supplied for the return from module
        if self.data != {}:
            ansible_report.update(self.data)
        return ansible_report


def data_as_dict(structure):
    """ Transform dataclass instances to a regular dict """
    result = []
    for item in structure:
        if isinstance(item, list) or isinstance(item, dict) == dict:
            dict_item = data_as_dict(item)
        else:
            dict_item = asdict(item)
        result.append(dict_item)
    return result


def parse_xml_etree(xml: str) -> dict:
    """ Parse xml etree and return it as dict """
    result = {}
    for element in etree.fromstring(xml).iterchildren():
        if len(element.items()) > 0:
            result[element.tag] = element.items()
            continue
        result[element.tag] = element.text
    return result


class VirtModule():
    """ Virt Ansible module is a base class for all Virt Module classes """

    def __init__(self, **module_kwargs: dict):
        """ Initialize Virt base class """
        self.mod_status = ModuleStatus()
        # Might be a bad idea and all possible varnames needs to be listed, but
        # initialization of AnsibleModule will definetely validate the input...
        self.ansible = AnsibleModule(**module_kwargs)
        self.check = self.ansible.check_mode
        self.warn = self.ansible.warn
        self.check_imports()
        self.conn = self.libvirt_connect()

    def check_imports(self):
        """ Check imports and fail if libraries imports wasn't successfull """
        if LIBVIRT_IMPORT_ERR:
            self.mod_status.msg = missing_required_lib("libvirt")
            self.mod_status.exception = LIBVIRT_IMPORT_ERR
            self.mod_status.failed = True
            self.exit()
        if LXML_IMPORT_ERR:
            self.mod_status.msg = missing_required_lib("lxml")
            self.mod_status.exception = LXML_IMPORT_ERR
            self.mod_status.failed = True
            self.exit()
        if SAFE_DUMP_IMPORT_ERR:
            self.mod_status.msg = missing_required_lib("pyYAML")
            self.mod_status.exception = SAFE_DUMP_IMPORT_ERR
            self.mod_status.failed = True
            self.exit()

    def libvirt_connect(self):
        """ Connects to libvirt and returns libvirt.virConnect object """
        uri = self.ansible.params.get('uri', 'qemu:///system')
        try:
            connection = libvirt.open(uri)
        except libvirt.libvirtError as exception:
            self.mod_status.msg = "hypervisor connection failure"
            self.mod_status.exception = exception
            self.ansible.fail_json(**self.mod_status.report)
        return connection

    @abc.abstractmethod
    def logic(self):
        """ Abstract methog definition for the module logic """

    def run(self):
        """ Select which function to call based on arguments

        If ansible params contains command it will try to match its value to
        a function name and execute that function. Otherwise it will fallback
        to a logic function which must be defined in a chaild classes.
        """
        command = self.ansible.params.get('command')
        if command:
            the_func = getattr(self, command)
        else:
            the_func = self.logic
        return the_func()

    def exit(self):
        """ Module exit logic """
        if self.mod_status.failed:
            self.ansible.fail_json(**self.mod_status.report)
        else:
            self.ansible.exit_json(**self.mod_status.report)
