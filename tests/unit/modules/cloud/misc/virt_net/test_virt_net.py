# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from ansible_collections.community.libvirt.tests.unit.compat import mock


def test_virt_net_create_already_active(virt_net_obj, dummy_libvirt):
    virt_net_obj.conn.create = mock.Mock()
    assert virt_net_obj.create("active_net") is None
    virt_net_obj.conn.create.assert_not_called()


def test_virt_net_recreate(virt_net_obj, dummy_libvirt):
    virt_net_obj.conn.create = mock.Mock()
    dummy_libvirt.libvirtError.error_code = 'VIR_ERR_NETWORK_EXIST'
    virt_net_obj.conn.create.side_effect = dummy_libvirt.libvirtError
    assert virt_net_obj.create("active_net") is None


def test_virt_stop_ignore_inactive(virt_net_obj):
    virt_net_obj.conn.destroy = mock.Mock()
    virt_net_obj.stop('inactive_net')
    virt_net_obj.conn.destroy.assert_not_called()


def test_virt_stop_active(virt_net_obj, monkeypatch):
    virt_net_obj.conn.destroy = mock.Mock()
    virt_net_obj.stop('active_net')
    virt_net_obj.conn.destroy.assert_called_with('active_net')


def test_virt_net_facts_network_without_bridge(virt_net_obj, dummy_libvirt, monkeypatch):
    # hostdev/passthrough networks have no bridge, libvirt raises an error
    monkeypatch.setattr(dummy_libvirt.libvirtError, "error_code", "VIR_ERR_INTERNAL_ERROR", raising=False)
    conn = virt_net_obj.conn
    conn.get_autostart = mock.Mock(return_value="yes")
    conn.get_persistent = mock.Mock(return_value="yes")
    conn.get_status = mock.Mock(return_value="active")
    conn.get_bridge = mock.Mock(side_effect=dummy_libvirt.libvirtError)
    conn.get_uuid = mock.Mock(return_value="e30530c3-b0e2-494f-8a0f-c8134145e960")
    conn.get_dhcp_leases = mock.Mock(return_value=[])
    conn.get_forward = mock.Mock(return_value="hostdev")
    conn.get_domain = mock.Mock(side_effect=ValueError)
    conn.get_macaddress = mock.Mock(side_effect=ValueError)

    result = virt_net_obj.info()

    for name in ("inactive_net", "active_net"):
        net = result["networks"][name]
        assert "bridge" not in net
        assert net["forward_mode"] == "hostdev"
        assert net["state"] == "active"
