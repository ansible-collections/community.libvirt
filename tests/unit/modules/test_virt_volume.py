# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import unittest

from lxml import etree

from ansible_collections.community.libvirt.plugins.modules.virt_volume import (
    _get_volume_size)


def _capacity_elem(text, unit=None):
    """ Build a <capacity> lxml element as _get_volume_size() expects it """
    xml = '<capacity>{0}</capacity>'.format(text) if unit is None else \
        '<capacity unit="{0}">{1}</capacity>'.format(unit, text)
    return etree.fromstring(xml)


class TestGetVolumeSize(unittest.TestCase):
    """Test cases for the _get_volume_size() function"""

    def test_no_unit_attribute_defaults_to_bytes(self):
        """No 'unit' attribute at all should be treated as bytes"""
        self.assertEqual(_get_volume_size(_capacity_elem(100)), 100)

    def test_bytes_units(self):
        """'bytes' and 'b' are both a 1-byte multiplier"""
        self.assertEqual(_get_volume_size(_capacity_elem(100, 'bytes')), 100)
        self.assertEqual(_get_volume_size(_capacity_elem(100, 'b')), 100)

    def test_binary_single_letter_units(self):
        """Bare single-letter units are binary (base-1024), per libvirt"""
        cases = {
            'k': 1024,
            'm': 1024 ** 2,
            'g': 1024 ** 3,
            't': 1024 ** 4,
            'p': 1024 ** 5,
            'e': 1024 ** 6,
        }
        for unit, expected in cases.items():
            with self.subTest(unit=unit):
                self.assertEqual(
                    _get_volume_size(_capacity_elem(1, unit)), expected)

    def test_iec_long_form_units_match_single_letter(self):
        """'KiB'/'MiB'/... are the explicit IEC spelling of 'K'/'M'/...
        and must convert to the exact same value"""
        pairs = [('k', 'kib'), ('m', 'mib'), ('g', 'gib'),
                 ('t', 'tib'), ('p', 'pib'), ('e', 'eib')]
        for short, long_form in pairs:
            with self.subTest(unit=long_form):
                self.assertEqual(
                    _get_volume_size(_capacity_elem(5, short)),
                    _get_volume_size(_capacity_elem(5, long_form)))

    def test_decimal_long_form_units(self):
        """'KB'/'MB'/... are decimal (base-1000), distinct from the
        binary 'K'/'M'/... and 'KiB'/'MiB'/... units"""
        cases = {
            'kb': 1000,
            'mb': 1000 ** 2,
            'gb': 1000 ** 3,
            'tb': 1000 ** 4,
            'pb': 1000 ** 5,
            'eb': 1000 ** 6,
        }
        for unit, expected in cases.items():
            with self.subTest(unit=unit):
                self.assertEqual(
                    _get_volume_size(_capacity_elem(1, unit)), expected)

    def test_unit_is_case_insensitive(self):
        """'GiB', 'Gib', 'GIB' and 'gib' must all be equivalent"""
        expected = _get_volume_size(_capacity_elem(100, 'gib'))
        for variant in ('GiB', 'Gib', 'GIB', 'gIB'):
            with self.subTest(unit=variant):
                self.assertEqual(
                    _get_volume_size(_capacity_elem(100, variant)), expected)

    def test_100_gib_matches_real_world_regression(self):
        """Regression test for the exact bug this fix addresses: a
        <capacity unit="GiB">100</capacity> volume definition must convert
        to 100 GiB in bytes, not silently fall back to a multiplier of 1"""
        self.assertEqual(
            _get_volume_size(_capacity_elem(100, 'GiB')), 107374182400)

    def test_unrecognized_unit_raises_value_error(self):
        """An unrecognized unit must raise, not silently default to a
        multiplier of 1"""
        with self.assertRaises(ValueError):
            _get_volume_size(_capacity_elem(100, 'not-a-unit'))

    def test_invalid_capacity_text_raises_value_error(self):
        """Non-numeric capacity text must raise ValueError"""
        with self.assertRaises(ValueError):
            _get_volume_size(_capacity_elem('not-a-number', 'g'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
