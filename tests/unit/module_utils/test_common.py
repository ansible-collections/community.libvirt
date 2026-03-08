# -*- coding: utf-8 -*-
#
# (c) 2025, Denys Mishchenko <denis@mischenko.org.ua>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import unittest
import yaml

# pylint: disable-next=no-name-in-module,import-error
from ansible_collections.community.libvirt.plugins.module_utils.common import (
    compare_dicts,
    compare_lists,
    ModuleStatus)


class TestCommonCompare(unittest.TestCase):
    """ Testing supporting functions to compare lists and dicts """

    def test_compare_dicts(self) -> None:
        """Test compare_dicts function"""

        a_dict = {1: 'V3', 'k1': "V1", 'k2': "V2", "k3": 56}
        dict_equal = {'k1': "V1", 1: 'V3', 'k2': "V2", "k3": 56}
        dict_valdiff = {1: 'V5', 'k1': "V1", 'k2': "V3", "k3": 56}
        dict_keydiff = {1: 'V3', 'k5': "V1", 'k2': "V2", "k3": 56}

        self.assertTrue(compare_dicts(a_dict, dict_equal))
        self.assertFalse(compare_dicts(a_dict, dict_valdiff))
        self.assertFalse(compare_dicts(a_dict, dict_keydiff))

    def test_compare_lists(self) -> None:
        """ Test compare_lists function """

        a_list = ['apple', 'meloon', 'orange', 65, 'pineaple']
        list_equal = [65, 'apple', 'orange', 'pineaple', 'meloon']
        list_valdiff = ['apple', 'meloon', 'orange', '65', 'pineaple']

        self.assertTrue(compare_lists(a_list, list_equal))
        self.assertFalse(compare_lists(a_list, list_valdiff))


class TestCommonModuleStatus(unittest.TestCase):
    """ Testing dataclass for generating ansible exit response """

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.module_status = ModuleStatus()

    # Test empty initialization
    def test_modulestatus_empty_init(self):
        """ Test module status initialization """
        self.assertFalse(
            self.module_status.changed,
            "Just initialised status should not have changed status")
        self.assertFalse(
            self.module_status.failed,
            "Just initialiased status should not have failed status")

    # Test report generation
    def test_modulestatus_report(self):
        """ Testing various report outputs based on provided data """

        # Test that data appear and use correct key
        self.module_status.data = {
            'result': {'virt-tool': 'libvirt', 'present': True}}
        self.assertIn('result', self.module_status.report.keys())

        # Test diff is produced on changed status when after is not empty
        self.module_status.changed = True
        test_diff = {'vms-list': ['vm1', 'vm2', 'vm3']}

        self.module_status.before = {}
        self.module_status.after = test_diff
        self.assertIn('diff', self.module_status.report.keys())

        # Test that diff yaml and equal to test_diff
        self.assertDictEqual(
            test_diff,
            yaml.safe_load(self.module_status.report['diff']['after']))
