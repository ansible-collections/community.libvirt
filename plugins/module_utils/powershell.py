# Copyright (c) 2014, Chris Church <chris@ninemoreminutes.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""PowerShell compatibility utilities vendored from ansible-core.

The _parse_clixml() function was extracted from
ansible.plugins.shell.powershell in ansible-core stable-2.20 (the last
release that carried it).  Starting with ansible-core devel (2.21+) the
function was removed and the underlying logic refactored into the private
ansible._internal._powershell._clixml module.

Upstream reference (stable-2.20):
  https://github.com/ansible/ansible/blob/stable-2.20/lib/ansible/plugins/shell/powershell.py

This shim should be removed once the collection's minimum supported
ansible-core version ships its own public replacement.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import re
import xml.etree.ElementTree as ET

from ansible.module_utils._text import to_bytes

_STRING_DESERIAL_FIND = re.compile(rb"\x00_\x00x((?:\x00[a-fA-F0-9]){4})\x00_")


def _parse_clixml(data, stream="Error"):
    """Parse CLIXML-encoded PowerShell output and return the stream message.

    Takes a byte string like ``b'#< CLIXML\\r\\n<Objs...'`` and extracts the
    stream message encoded in the XML data.  CLIXML is used by PowerShell to
    encode multiple objects in stderr.
    """
    lines = []

    def rplcr(matchobj):
        match_hex = matchobj.group(1)
        hex_string = match_hex.decode("utf-16-be")
        return base64.b16decode(hex_string.upper())

    while data:
        start_idx = data.find(b"<Objs ")
        end_idx = data.find(b"</Objs>")
        if start_idx == -1 or end_idx == -1:
            break

        end_idx += 7
        current_element = data[start_idx:end_idx]
        data = data[end_idx:]

        clixml = ET.fromstring(current_element)
        namespace_match = re.match(r'{(.*)}', clixml.tag)
        namespace = "{%s}" % namespace_match.group(1) if namespace_match else ""

        entries = clixml.findall("./%sS" % namespace)
        if not entries:
            continue

        if lines:
            lines.append("\r\n")

        for string_entry in entries:
            actual_stream = string_entry.attrib.get('S', None)
            if actual_stream != stream:
                continue

            b_line = (string_entry.text or "").encode("utf-16-be")
            b_escaped = re.sub(_STRING_DESERIAL_FIND, rplcr, b_line)

            lines.append(b_escaped.decode("utf-16-be", errors="surrogatepass"))

    return to_bytes(''.join(lines), errors="surrogatepass")
