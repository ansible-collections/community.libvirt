# (c) 2025, Joey Zhang <thinkdoggie@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import tempfile
import math

from ansible_collections.community.libvirt.plugins.module_utils.libvirt import (
    LibvirtConnection, VIRT_SUCCESS
)


OPTION_BOOL_ONOFF = 1


class LibvirtWrapper(object):

    def __init__(self, module):
        self.module = module
        self.uri = module.params.get('uri')

    def __get_conn(self):
        self.conn = LibvirtConnection(self.uri, self.module)
        return self.conn

    def find_vm(self, vmid):
        self.__get_conn()
        return self.conn.find_vm(vmid)

    def create(self, vmid):
        if not self.module.check_mode:
            self.__get_conn()
            return self.conn.create(vmid)

    def shutdown(self, vmid):
        if not self.module.check_mode:
            self.__get_conn()
            return self.conn.shutdown(vmid)

    def destroy(self, vmid):
        if not self.module.check_mode:
            self.__get_conn()
            return self.conn.destroy(vmid)

    def undefine(self, vmid):
        if not self.module.check_mode:
            self.__get_conn()
            self.conn.delete_domain_volumes(vmid)
            return self.conn.undefine(vmid, 0)


def _get_option_mapping(key, mapping):
    if mapping is None:
        return (key, None)

    if key in mapping:
        name, valmap = mapping[key]
        if name is None:
            name = key
        return (name, valmap)
    else:
        return (key, None)


def _dict2options(obj, mapping, prefix=""):

    if obj is None:
        return ""

    if not isinstance(obj, dict):
        return str(obj)

    # Extract primary value if present
    # Priority: _value takes precedence over value
    primary_value = None
    primary_key = None

    if '_value' in obj:
        primary_value = obj['_value']
        primary_key = '_value'
    elif 'value' in obj:
        primary_value = obj['value']
        primary_key = 'value'

    # Create a copy of the dict without the primary key for processing
    obj_copy = obj.copy()
    if primary_key:
        del obj_copy[primary_key]

    parts = []
    for k, v in obj_copy.items():
        if v is None:
            continue

        name, valmap = _get_option_mapping(k, mapping)

        if isinstance(v, dict):
            sub_prefix = "{}{}.".format(prefix, name)
            parts.append(_dict2options(v, valmap, prefix=sub_prefix))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                item_name = "{}{}{}".format(prefix, name, i)
                if isinstance(item, dict):
                    sub_prefix = "{}.".format(item_name)
                    parts.append(
                        _dict2options(
                            item,
                            valmap,
                            prefix=sub_prefix))
                elif isinstance(item, bool):
                    if valmap == OPTION_BOOL_ONOFF:
                        parts.append(
                            "{}={}".format(
                                item_name,
                                'on' if item else 'off'))
                    else:
                        parts.append(
                            "{}={}".format(
                                item_name,
                                'yes' if item else 'no'))
                else:
                    parts.append("{}={}".format(item_name, str(item)))
        elif isinstance(v, bool):
            if valmap == OPTION_BOOL_ONOFF:
                parts.append(
                    "{}{}={}".format(
                        prefix,
                        name,
                        'on' if v else 'off'))
            else:
                parts.append(
                    "{}{}={}".format(
                        prefix,
                        name,
                        'yes' if v else 'no'))
        else:
            parts.append("{}{}={}".format(prefix, name, str(v)))

    # Combine primary value with other parts
    if primary_value is not None:
        primary_str = str(primary_value)

        # If we have a prefix, the primary value should be associated with it
        # Remove trailing dot from prefix for the primary value assignment
        if prefix:
            prefix_without_dot = prefix.rstrip('.')
            primary_part = "{}={}".format(prefix_without_dot, primary_str)
        else:
            # At root level, primary value stands alone
            primary_part = primary_str

        if parts:
            return "{},{}".format(primary_part, ",".join(parts))
        else:
            return primary_part
    elif parts:
        return ",".join(parts)
    else:
        return ""


class VirtInstallTool(object):

    def __init__(self, module,
                 virtinst_path=None):
        self.module = module
        self.params = module.params.copy()
        self.warnings = []
        self._base_command = virtinst_path if virtinst_path is not None else 'virt-install'
        self.command_argv = [self._base_command]

        self._vm_name = self.params.get('name')

    def _reset_command(self):
        """Reset command_argv to base command for new operation"""
        self.command_argv = [self._base_command]

    def _save_string_to_tempfile(self, content, suffix='.tmp'):
        fd, path = tempfile.mkstemp(dir=self.module.tmpdir,
                                    suffix=suffix,
                                    text=True)
        with os.fdopen(fd, 'w') as f:
            f.write(content)

        return path

    def _add_parameter(
            self,
            flag,
            primary_value=None,
            dict_value=None,
            dict_mapping=None):
        """Add a command line option to virt-install command"""
        if primary_value:
            if dict_value:
                self.command_argv.append("{}".format(flag))
                self.command_argv.append(
                    "{},{}".format(
                        str(primary_value),
                        _dict2options(
                            dict_value,
                            dict_mapping)))
                return
            else:
                self.command_argv.append("{}".format(flag))
                self.command_argv.append("{}".format(str(primary_value)))
                return
        else:
            if dict_value:
                self.command_argv.append("{}".format(flag))
                self.command_argv.append("{}".format(
                    _dict2options(dict_value, dict_mapping)))
                return
            else:
                self.command_argv.append("{}".format(flag))
                return

    def _add_flag_parameter(self, flag, value):
        """Add a flag command line option to virt-install command"""
        if value:
            self.command_argv.append("{}".format(flag))
            return

    def _get_param_combined_items(self, singular_key, plural_key):
        combined_items = []
        if self.params.get(singular_key) is not None:
            combined_items.append(self.params[singular_key])
        if self.params.get(plural_key) is not None:
            combined_items.extend(self.params[plural_key])

        return combined_items

    def _convert_raw_to_string(self, value):
        """Convert raw type parameter (str or dict) to string content.
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            try:
                import yaml
                return yaml.safe_dump(value, default_flow_style=False, allow_unicode=True)
            except ImportError:
                self.module.fail_json(
                    msg="PyYAML is required to process dictionary cloud-init parameters")
        else:
            # This should not happen due to validation, but provide a fallback
            return str(value)

    def _build_basic_options(self):
        """Build basic VM configuration options"""
        # Required options
        if self.params.get('uri') is not None:
            self._add_parameter('--connect', self.params['uri'])

        if self.params.get('name') is not None:
            self._add_parameter('--name', self.params['name'])

        if self.params.get('memory') is not None:
            memory_mapping = {
                'current_memory': ('currentMemory', None),
                'max_memory': ('maxMemory', None),
                'max_memory_opts': ('maxMemory', None),
            }
            self._add_parameter('--memory', self.params['memory'],
                                dict_value=self.params.get('memory_opts'),
                                dict_mapping=memory_mapping)

        if self.params.get('memorybacking') is not None:
            memorybacking_mapping = {
                'hugepage_specs': ('hugepages.page', {
                    'page_size': ('size', None),
                }),
                'source': ('source', None),
            }
            self._add_parameter('--memorybacking',
                                dict_value=self.params['memorybacking'],
                                dict_mapping=memorybacking_mapping)

        if self.params.get('arch') is not None:
            self._add_parameter('--arch', self.params['arch'])

        if self.params.get('machine') is not None:
            self._add_parameter('--machine', self.params['machine'])

        if self.params.get('metadata') is not None:
            self._add_parameter('--metadata',
                                dict_value=self.params['metadata'])

        if self.params.get('events') is not None:
            self._add_parameter('--events',
                                dict_value=self.params['events'])

        if self.params.get('resource') is not None:
            self._add_parameter('--resource',
                                dict_value=self.params['resource'])

        if self.params.get('sysinfo') is not None:
            self._add_parameter('--sysinfo',
                                dict_value=self.params['sysinfo'])

        if self.params.get('qemu_commandline') is not None:
            self._add_parameter(
                '--qemu-commandline',
                self.params['qemu_commandline'])

        if self.params.get('vcpus') is not None:
            vcpus_mapping = {
                'current': ('vcpu.current', None),
                'placement': ('vcpu.placement', None),
                'vcpu_specs': ('vcpus.vcpu', None),
            }
            self._add_parameter('--vcpus', self.params['vcpus'],
                                dict_value=self.params.get('vcpus_opts'),
                                dict_mapping=vcpus_mapping)

        if self.params.get('numatune') is not None:
            numatune_mapping = {
                'memnode_specs': ('memnode', None)
            }
            self._add_parameter('--numatune',
                                dict_value=self.params['numatune'],
                                dict_mapping=numatune_mapping)

        if self.params.get('memtune') is not None:
            self._add_parameter('--memtune',
                                dict_value=self.params['memtune'])

        if self.params.get('blkiotune') is not None:
            blkiotune_mapping = {
                'devices': ('device', None)
            }
            self._add_parameter('--blkiotune',
                                dict_value=self.params['blkiotune'],
                                dict_mapping=blkiotune_mapping)

        if self.params.get('cpu') is not None:
            cpu_mapping = {
                'model_opts': ('model', None),
                'numa': (None, {
                    'cell_specs': ('cell', {
                        'mem_access': ('memAccess', None),
                        'distances': (None, {
                            'sibling_specs': ('sibling', None)
                        }),
                        'cache_specs': ('cache', None)
                    }),
                    'interconnects': (None, {
                        'bandwidth_specs': ('bandwidth', None),
                        'latency_specs': ('latency', None)
                    })
                })
            }
            cpu_dict_value = self.params['cpu']
            cpu_primary_argv = []
            if 'model' in cpu_dict_value:
                cpu_model = cpu_dict_value.pop('model')
                if cpu_model:
                    cpu_primary_argv.append(cpu_model)
            if 'features' in cpu_dict_value:
                cpu_feature_param = cpu_dict_value.pop('features')
                if cpu_feature_param:
                    for k, v in cpu_feature_param.items():
                        if v in [
                            'force',
                            'require',
                            'optional',
                            'disable',
                                'forbid']:
                            cpu_primary_argv.append("{}={}".format(v, k))
            if cpu_primary_argv:
                cpu_primary_value = ','.join(cpu_primary_argv)
                self._add_parameter('--cpu', cpu_primary_value,
                                    dict_value=cpu_dict_value,
                                    dict_mapping=cpu_mapping)
            else:
                self._add_parameter('--cpu',
                                    dict_value=cpu_dict_value,
                                    dict_mapping=cpu_mapping)

        if self.params.get('cputune') is not None:
            cputune_mapping = {
                'vcpupin_specs': ('vcpupin', None),
                'iothreadpin_specs': ('iothreadpin', None),
                'vcpusched_specs': ('vcpusched', None),
                'iothreadsched_specs': ('iothreadsched', None),
            }
            self._add_parameter('--cputune',
                                dict_value=self.params['cputune'],
                                dict_mapping=cputune_mapping)

        if self.params.get('security') is not None:
            self._add_parameter(
                '--seclabel',
                dict_value=self.params['security'])

        if self.params.get('keywrap') is not None:
            keywrap_mapping = {
                'ciphers': ('cipher', None)
            }
            self._add_parameter('--keywrap',
                                dict_value=self.params['keywrap'],
                                dict_mapping=keywrap_mapping)

        if self.params.get('iothreads') is not None:
            iothreads_mapping = {
                'iothread_specs': ('iothreadids.iothread', None),
            }
            self._add_parameter('--iothreads', self.params['iothreads'],
                                dict_value=self.params.get('iothreads_opts'),
                                dict_mapping=iothreads_mapping)

        if self.params.get('features') is not None:
            self._add_parameter(
                '--features',
                dict_value=self.params['features'])

        if self.params.get('clock') is not None:
            clock_mapping = {
                'timers': ('timer', None)
            }
            self._add_parameter('--clock',
                                dict_value=self.params['clock'],
                                dict_mapping=clock_mapping)

        if self.params.get('pm') is not None:
            self._add_parameter('--pm',
                                dict_value=self.params['pm'])

        if self.params.get('launch_security') is not None:
            launch_security_mapping = {
                'dh_cert': ('dhCert', None),
                'reduced_phys_bits': ('reducedPhysBits', None)
            }
            self._add_parameter('--launchSecurity',
                                dict_value=self.params['launch_security'],
                                dict_mapping=launch_security_mapping)

    def _build_installation_options(self):        # Installation media options
        if self.params.get('cdrom') is not None:
            self._add_parameter('--cdrom', self.params['cdrom'])

        if self.params.get('location') is not None:
            self._add_parameter('--location', self.params['location'],
                                dict_value=self.params.get('location_opts'))

        if self.params.get('pxe') is not None:
            self._add_flag_parameter('--pxe', self.params['pxe'])

        if self.params.get('import'):
            self._add_flag_parameter('--import', self.params['import'])

        if self.params.get('extra_args') is not None:
            self._add_parameter('--extra-args', self.params['extra_args'])

        if self.params.get('initrd_inject') is not None:
            self._add_parameter(
                '--initrd-inject',
                self.params['initrd_inject'])

        if self.params.get('install') is not None:
            self._add_parameter('--install',
                                dict_value=self.params['install'])

        if self.params.get('unattended') is not None:
            unattended_mapping = {
                'admin_password_file': ('admin-password-file', None),
                'user_login': ('user-login', None),
                'user_password_file': ('user-password-file', None),
                'product_key': ('product-key', None),
            }
            self._add_parameter('--unattended',
                                dict_value=self.params['unattended'],
                                dict_mapping=unattended_mapping)

        if self.params.get('cloud_init') is not None:
            cloud_init_params = self.params['cloud_init'].copy()

            if cloud_init_params.get('network_config'):
                network_config_content = self._convert_raw_to_string(cloud_init_params['network_config'])
                cloud_init_params['network-config'] = self._save_string_to_tempfile(network_config_content)
                del cloud_init_params['network_config']
            if cloud_init_params.get('meta_data'):
                meta_data_content = self._convert_raw_to_string(cloud_init_params['meta_data'])
                cloud_init_params['meta-data'] = self._save_string_to_tempfile(meta_data_content)
                del cloud_init_params['meta_data']
            if cloud_init_params.get('user_data'):
                user_data_content = self._convert_raw_to_string(cloud_init_params['user_data'])
                cloud_init_params['user-data'] = self._save_string_to_tempfile(user_data_content)
                del cloud_init_params['user_data']

            cloud_init_mapping = {
                'root_password_generate': (
                    'root-password-generate',
                    OPTION_BOOL_ONOFF),
                'disable': (
                    'disable',
                    OPTION_BOOL_ONOFF),
                'root_password_file': (
                    'root-password-file',
                    None),
                'root_ssh_key': (
                    'root-ssh-key',
                    None),
                'clouduser_ssh_key': (
                    'clouduser-ssh-key',
                    None),
            }
            self._add_parameter('--cloud-init',
                                dict_value=cloud_init_params,
                                dict_mapping=cloud_init_mapping)

        if self.params.get('boot') is not None:
            self._add_parameter('--boot', self.params['boot'],
                                dict_value=self.params.get('boot_opts'))

        if self.params.get('idmap') is not None:
            self._add_parameter('--idmap',
                                dict_value=self.params['idmap'])

    def _build_guest_os_options(self):
        if self.params.get('osinfo') is not None:
            osinfo_mapping = {
                'detect': ('detect', OPTION_BOOL_ONOFF),
                'require': ('require', OPTION_BOOL_ONOFF),
            }
            self._add_parameter('--osinfo',
                                dict_value=self.params['osinfo'],
                                dict_mapping=osinfo_mapping)

    def _build_storage_options(self):
        if self.params.get('disks') is not None:
            disk_mapping = {
                'backing_store': ('backing_store', None),
                'backing_format': ('backing_format', None),
                'transient_opts': ('transient', {
                    'share_backing': ('shareBacking', None)
                })
            }
            for disk in self.params['disks']:
                self._add_parameter('--disk',
                                    dict_value=disk,
                                    dict_mapping=disk_mapping)

        if self.params.get('filesystems') is not None:
            for filesystem in self.params['filesystems']:
                self._add_parameter('--filesystem',
                                    dict_value=filesystem)

    def _build_network_options(self):
        if self.params.get('networks') is not None:
            network_param = self.params['networks']
            if len(network_param) == 0:
                self._add_parameter('--network', 'none')
                return

            network_mapping = {
                'trust_guest_rx_filters': ('trustGuestRxFilters', None),
                'state': ('link.state', None),
            }
            for network in network_param:
                self._add_parameter('--network',
                                    dict_value=network,
                                    dict_mapping=network_mapping)

    def _build_graphics_options(self):
        graphics_params = self._get_param_combined_items(
            'graphics', 'graphics_devices')

        if len(graphics_params) == 0:
            self._add_parameter('--graphics', 'none')
            return

        for item in graphics_params:
            graphics_primary_value = None
            if 'type' in item:
                graphics_primary_value = item.pop('type')
                self._add_parameter('--graphics', graphics_primary_value,
                                    dict_value=item)
            else:
                self._add_parameter('--graphics',
                                    dict_value=item)

    def _build_virt_options(self):
        if self.params.get('virt_type') is not None:
            self._add_parameter('--virt-type', self.params['virt_type'])

        if self.params.get('hvm') is not None:
            self._add_flag_parameter('--hvm', self.params['hvm'])

        if self.params.get('paravirt') is not None:
            self._add_flag_parameter('--paravirt', self.params['paravirt'])

        if self.params.get('container') is not None:
            self._add_flag_parameter('--container', self.params['container'])

    def _build_device_options(self):
        # Controller devices
        controller_params = self._get_param_combined_items(
            'controller', 'controller_devices')
        for item in controller_params:
            self._add_parameter('--controller',
                                dict_value=item)

        # Input devices
        input_params = self._get_param_combined_items('input', 'input_devices')
        for item in input_params:
            self._add_parameter('--input',
                                dict_value=item)

        # Host devices
        hostdev_params = self._get_param_combined_items(
            'hostdev', 'host_devices')
        for item in hostdev_params:
            self._add_parameter('--hostdev',
                                dict_value=item)

        # Sound devices
        sound_params = self._get_param_combined_items('sound', 'sound_devices')
        for item in sound_params:
            self._add_parameter('--sound',
                                dict_value=item)

        # Audio devices
        audio_params = self._get_param_combined_items('audio', 'audio_devices')
        for item in audio_params:
            self._add_parameter('--audio',
                                dict_value=item)

        # Watchdog devices
        watchdog_params = self._get_param_combined_items(
            'watchdog', 'watchdog_devices')
        for item in watchdog_params:
            self._add_parameter('--watchdog',
                                dict_value=item)

        # Serial devices
        serial_params = self._get_param_combined_items(
            'serial', 'serial_devices')
        for item in serial_params:
            self._add_parameter('--serial',
                                dict_value=item)

        # Parallel devices
        parallel_params = self._get_param_combined_items(
            'parallel', 'parallel_devices')
        for item in parallel_params:
            self._add_parameter('--parallel',
                                dict_value=item)

        # Channel devices
        channel_params = self._get_param_combined_items(
            'channel', 'channel_devices')
        for item in channel_params:
            self._add_parameter('--channel',
                                dict_value=item)

        # Console devices
        console_params = self._get_param_combined_items(
            'console', 'console_devices')
        for item in console_params:
            self._add_parameter('--console',
                                dict_value=item)

        # Video devices
        video_params = self._get_param_combined_items('video', 'video_devices')
        for item in video_params:
            self._add_parameter('--video',
                                dict_value=item)

        # Smartcard devices
        smartcard_params = self._get_param_combined_items(
            'smartcard', 'smartcard_devices')
        for item in smartcard_params:
            self._add_parameter('--smartcard',
                                dict_value=item)

        # Redirection devices
        redirdev_params = self._get_param_combined_items(
            'redirdev', 'redirected_devices')
        for item in redirdev_params:
            self._add_parameter('--redirdev',
                                dict_value=item)

        # Memory balloon devices
        memballoon_params = self._get_param_combined_items(
            'memballoon', 'memballoon_devices')
        memballoon_mapping = {
            'freePageReporting': ('freePageReporting', OPTION_BOOL_ONOFF),
            'autodeflate': ('autodeflate', OPTION_BOOL_ONOFF),
        }
        for item in memballoon_params:
            self._add_parameter('--memballoon',
                                dict_value=item,
                                dict_mapping=memballoon_mapping)

        # TPM devices
        tpm_params = self._get_param_combined_items('tpm', 'tpm_devices')
        tpm_mapping = {
            'active_pcr_banks': ('active_pcr_banks', {
                'sha1': ('sha1', OPTION_BOOL_ONOFF),
                'sha256': ('sha256', OPTION_BOOL_ONOFF),
                'sha384': ('sha384', OPTION_BOOL_ONOFF),
                'sha512': ('sha512', OPTION_BOOL_ONOFF),
            }),
            'backend': ('backend', {
                'persistent_state': ('persistent_state', OPTION_BOOL_ONOFF),
            }),
        }
        for item in tpm_params:
            self._add_parameter('--tpm',
                                dict_value=item,
                                dict_mapping=tpm_mapping)

        # RNG devices
        rng_params = self._get_param_combined_items('rng', 'rng_devices')
        for item in rng_params:
            self._add_parameter('--rng',
                                dict_value=item)

        # Panic devices
        panic_params = self._get_param_combined_items('panic', 'panic_devices')
        for item in panic_params:
            self._add_parameter('--panic',
                                dict_value=item)

        # Shared memory devices
        shmem_params = self._get_param_combined_items('shmem', 'shmem_devices')
        shmem_mapping = {
            'msi': ('msi', {
                'ioeventfd': ('ioeventfd', OPTION_BOOL_ONOFF),
            }),
        }
        for item in shmem_params:
            self._add_parameter('--shmem',
                                dict_value=item,
                                dict_mapping=shmem_mapping)

        # Vsock devices
        vsock_params = self._get_param_combined_items('vsock', 'vsock_devices')
        vsock_mapping = {
            'cid': ('cid', {
                'auto': ('auto', OPTION_BOOL_ONOFF),
            }),
        }
        for item in vsock_params:
            self._add_parameter('--vsock',
                                dict_value=item,
                                dict_mapping=vsock_mapping)

        # IOMMU devices
        iommu_params = self._get_param_combined_items('iommu', 'iommu_devices')
        iommu_mapping = {
            'driver': ('driver', {
                'caching_mode': ('caching_mode', OPTION_BOOL_ONOFF),
                'eim': ('eim', OPTION_BOOL_ONOFF),
                'intremap': ('intremap', OPTION_BOOL_ONOFF),
                'iotlb': ('iotlb', OPTION_BOOL_ONOFF),
            }),
        }
        for item in iommu_params:
            self._add_parameter('--iommu',
                                dict_value=item,
                                dict_mapping=iommu_mapping)

    def _build_misc_options(self):
        if self.params.get('autostart') is not None:
            self._add_flag_parameter('--autostart', self.params['autostart'])

        if self.params.get('transient') is not None:
            self._add_flag_parameter('--transient', self.params['transient'])

        if self.params.get('destroy_on_exit') is not None:
            self._add_flag_parameter(
                '--destroy-on-exit',
                self.params['destroy_on_exit'])

        if self.params.get('noreboot') is not None:
            self._add_flag_parameter('--noreboot', self.params['noreboot'])

    def _validate_params(self):
        """Validate parameter combinations and dependencies according to virt-install requirements"""

        extra_key_pairs = [
            ('memory', 'memory_opts'),
            ('vcpus', 'vcpus_opts'),
            ('location', 'location_opts'),
            ('boot', 'boot_opts'),
            ('iothreads', 'iothreads_opts'),
        ]

        for param_key, extra_key in extra_key_pairs:
            if (extra_key in self.params) and (param_key not in self.params):
                self.module.fail_json(
                    msg="{} requires {} to be specified".format(
                        extra_key, param_key))

        # Validate cloud-init raw type parameters
        if self.params.get('cloud_init') is not None:
            cloud_init_params = self.params['cloud_init']
            raw_type_params = ['network_config', 'meta_data', 'user_data']

            for param_name in raw_type_params:
                if cloud_init_params.get(param_name) is not None:
                    param_value = cloud_init_params[param_name]
                    if not isinstance(param_value, (str, dict)):
                        self.module.fail_json(
                            msg="cloud_init.{} must be a string or dictionary, got {}".format(
                                param_name, type(param_value).__name__))

    def _build_command(self):
        """Build the complete virt-install command"""
        self._validate_params()

        # Build command sections
        self._build_basic_options()
        self._build_installation_options()
        self._build_guest_os_options()
        self._build_storage_options()
        self._build_network_options()
        self._build_graphics_options()
        self._build_virt_options()
        self._build_device_options()
        self._build_misc_options()

        # Always add --noautoconsole for non-interactive execution
        self.command_argv.append('--noautoconsole')

    def execute(self, dryrun=False, wait_timeout=None):
        changed = False
        result = dict()

        self._reset_command()
        self._build_command()

        if dryrun:
            self.command_argv.append('--dry-run')

        if wait_timeout:
            wait_minutes = math.ceil(wait_timeout / 60.0)
            self.command_argv.append('--wait')
            self.command_argv.append(str(wait_minutes))

        # Execute the command
        rc, stdout, stderr = self.module.run_command(
            self.command_argv, check_rc=False)

        if rc == 0:
            changed = True
            result["msg"] = "virtual machine '{}' created successfully".format(
                self._vm_name
            )
            return changed, VIRT_SUCCESS, result

        error_msg = "failed to create virtual machine '{}': {}".format(
            self._vm_name, stderr.strip() if stderr else stdout.strip()
        )
        result["msg"] = error_msg
        return changed, rc, result


def get_memory_args():
    return dict(
        memory=dict(type='int'),
        memory_opts=dict(
            type='dict',
            options=dict(
                current_memory=dict(type='int'),
                max_memory=dict(type='int'),
                max_memory_opts=dict(
                    type='dict', options=dict(
                        slots=dict(
                            type='int'))),
            ),
        ),
    )


def get_memorybacking_args():
    return dict(
        memorybacking=dict(
            type='dict',
            options=dict(
                hugepages=dict(type='bool'),
                hugepage_specs=dict(
                    type='list',
                    elements="dict",
                    options=dict(
                        page_size=dict(
                            type='int'), nodeset=dict(
                            type='str')),
                ),
                nosharepages=dict(type='bool'),
                locked=dict(type='bool'),
                source=dict(
                    type='dict',
                    options=dict(
                        type=dict(
                            type='str',
                            choices=['anonymous', 'file', 'memfd']),
                    ),
                ),
                access=dict(
                    type='dict',
                    options=dict(
                        mode=dict(
                            type='str',
                            choices=[
                                'shared',
                                'private'])),
                ),
                allocation=dict(
                    type='dict',
                    options=dict(
                        mode=dict(
                            type='str', choices=[
                                'immediate', 'ondemand']),
                        threads=dict(type='int'),
                    ),
                ),
                discard=dict(type='bool'),
            ),
        ),
    )


def get_arch_args():
    return dict(
        arch=dict(type='str'),
    )


def get_machine_args():
    return dict(
        machine=dict(type='str'),
    )


def get_metadata_args():
    return dict(
        metadata=dict(type='dict'),
    )


def get_events_args():
    return dict(
        events=dict(
            type='dict',
            options=dict(
                on_poweroff=dict(
                    type='str',
                    choices=[
                        'destroy',
                        'restart',
                        'preserve',
                        'rename-restart'],
                ),
                on_reboot=dict(
                    type='str',
                    choices=[
                        'destroy',
                        'restart',
                        'preserve',
                        'rename-restart'],
                ),
                on_crash=dict(
                    type='str',
                    choices=[
                        'destroy',
                        'restart',
                        'preserve',
                        'rename-restart',
                        'coredump-destroy',
                        'coredump-restart',
                    ],
                ),
                on_lockfailure=dict(
                    type='str', choices=['poweroff', 'restart', 'pause', 'ignore']
                ),
            ),
        ),
    )


def get_resource_args():
    return dict(
        resource=dict(type='dict'),
    )


def get_sysinfo_args():
    return dict(
        sysinfo=dict(type='dict'),
    )


def get_qmeu_commandline_args():
    return dict(
        qemu_commandline=dict(type='str'),
    )


def get_vcpu_args():
    return dict(
        vcpus=dict(type='int'),
        vcpus_opts=dict(
            type='dict',
            options=dict(
                maxvcpus=dict(type='int'),
                sockets=dict(type='int'),
                dies=dict(type='int'),
                clusters=dict(type='int'),
                cores=dict(type='int'),
                threads=dict(type='int'),
                current=dict(type='int'),
                cpuset=dict(type='str'),
                placement=dict(type='str', choices=['static', 'auto']),
                vcpu_specs=dict(type='list', elements="dict"),
            ),
        ),
    )


def get_numatune_args():
    return dict(
        numatune=dict(
            type='dict',
            options=dict(
                memory=dict(
                    type='dict',
                    options=dict(
                        mode=dict(
                            type='str', choices=['interleave', 'preferred', 'strict']
                        ),
                        nodeset=dict(type='str'),
                        placement=dict(type='str', choices=['static', 'auto']),
                    ),
                ),
                memnode_specs=dict(
                    type='list',
                    elements="dict",
                    options=dict(
                        cellid=dict(type='int'),
                        mode=dict(
                            type='str', choices=['interleave', 'preferred', 'strict']
                        ),
                        nodeset=dict(type='str'),
                    ),
                ),
            ),
        ),
    )


def get_memtune_args():
    return dict(
        memtune=dict(type='dict'),
    )


def get_blkiotune_args():
    return dict(
        blkiotune=dict(
            type='dict',
            options=dict(
                weight=dict(type='int'), devices=dict(type='list', elements="dict")
            ),
        ),
    )


def get_cpu_args():
    return dict(
        cpu=dict(
            type='dict',
            options=dict(
                model=dict(type='str'),
                model_opts=dict(
                    type='dict',
                    options=dict(
                        fallback=dict(type='str', choices=['forbid', 'allow']),
                        vendor_id=dict(type='str'),
                    ),
                ),
                match=dict(type='str', choices=['exact', 'minimum', 'strict']),
                migratable=dict(type='bool'),
                vendor=dict(type='str'),
                features=dict(type='dict'),
                cache=dict(
                    type='dict',
                    options=dict(
                        mode=dict(
                            type='str', choices=['emulate', 'passthrough', 'disable']
                        ),
                        level=dict(type='int'),
                    ),
                ),
                numa=dict(
                    type='dict',
                    options=dict(
                        cell_specs=dict(
                            type='list',
                            elements="dict",
                            options=dict(
                                id=dict(type='int'),
                                cpus=dict(type='str'),
                                memory=dict(type='int'),
                                mem_access=dict(
                                    type='str', choices=[
                                        'shared', 'private']),
                                discard=dict(type='bool'),
                                distances=dict(
                                    type='dict',
                                    options=dict(
                                        sibling_specs=dict(
                                            type='list', elements="dict"),
                                    ),
                                ),
                                cache_specs=dict(type='list', elements="dict"),
                            ),
                        ),
                        interconnects=dict(
                            type='list',
                            elements="dict",
                            options=dict(
                                bandwidth_specs=dict(
                                    type='list', elements="dict"),
                                latency_specs=dict(
                                    type='list', elements="dict"),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def get_cputune_args():
    return dict(
        cputune=dict(
            type='dict',
            options=dict(
                vcpupin_specs=dict(
                    type='list',
                    elements="dict",
                    options=dict(
                        vcpu=dict(type='int'),
                        cpuset=dict(type='str'),
                    ),
                ),
                emulatorpin=dict(
                    type='dict',
                    options=dict(
                        cpuset=dict(type='str'),
                    )
                ),
                iothreadpin_specs=dict(
                    type='list',
                    elements="dict",
                    options=dict(
                        iothread=dict(type='int'),
                        cpuset=dict(type='str'),
                    ),
                ),
                vcpusched_specs=dict(
                    type='list',
                    elements="dict",
                    options=dict(
                        vcpus=dict(type='str'),
                        scheduler=dict(
                            type='str', choices=[
                                'batch', 'idle', 'fifo', 'rr']),
                        priority=dict(type='int'),
                    ),
                ),
                iothreadsched_specs=dict(
                    type='list',
                    elements="dict",
                    options=dict(
                        iothreads=dict(type='str'),
                        scheduler=dict(
                            type='str', choices=[
                                'batch', 'idle', 'fifo', 'rr']),
                        priority=dict(type='int'),
                    ),
                ),
                emulatorsched=dict(
                    type='dict',
                    options=dict(
                        scheduler=dict(
                            type='str', choices=[
                                'batch', 'idle', 'fifo', 'rr']),
                        priority=dict(type='int'),
                    ),
                ),
                shares=dict(type='int'),
                period=dict(type='int'),
                quota=dict(type='int'),
                global_period=dict(type='int'),
                global_quota=dict(type='int'),
                emulator_period=dict(type='int'),
                emulator_quota=dict(type='int'),
                iothread_period=dict(type='int'),
                iothread_quota=dict(type='int'),
            ),
        ),
    )


def get_security_args():
    return dict(
        security=dict(type='dict'),
    )


def get_keywrap_args():
    return dict(
        keywrap=dict(
            type='dict', options=dict(ciphers=dict(type='list', elements="dict")), no_log=True
        ),
    )


def get_iothreads_args():
    return dict(
        iothreads=dict(type='int'),
        iothreads_opts=dict(
            type='dict',
            options=dict(
                iothread_specs=dict(
                    type='list',
                    elements="dict",
                    options=dict(
                        id=dict(type='int'),
                        thread_pool_min=dict(type='int'),
                        thread_pool_max=dict(type='int'),
                    ),
                ),
                defaultiothread=dict(
                    type='dict',
                    options=dict(
                        thread_pool_min=dict(type='int'),
                        thread_pool_max=dict(type='int'),
                    ),
                ),
            ),
        ),
    )


def get_features_args():
    return dict(
        features=dict(type='dict'),
    )


def get_clock_args():
    return dict(
        clock=dict(
            type='dict',
            options=dict(
                offset=dict(type='str'), timers=dict(type='list', elements="dict")
            ),
        ),
    )


def get_pm_args():
    return dict(
        pm=dict(
            type='dict',
            options=dict(
                suspend_to_mem=dict(
                    type='dict', options=dict(enabled=dict(type='bool'))
                ),
                suspend_to_disk=dict(
                    type='dict', options=dict(enabled=dict(type='bool'))
                ),
            ),
        ),
    )


def get_launch_security_args():
    return dict(
        launch_security=dict(
            type='dict',
            options=dict(
                type=dict(type='str', required=True),
                policy=dict(type='str'),
                cbitpos=dict(type='int'),
                reduced_phys_bits=dict(type='int'),
                dh_cert=dict(type='str'),
                session=dict(type='str'),
            ),
        ),
    )


def get_cdrom_args():
    return dict(
        cdrom=dict(type='str'),
    )


def get_location_opts():
    return dict(
        location=dict(type='str'),
        location_opts=dict(
            type='dict', options=dict(kernel=dict(type='str'), initrd=dict(type='str'))
        ),
    )


def get_pxe_args():
    return dict(
        pxe=dict(type='bool'),
    )


def get_import_args():
    args = dict()
    args['import'] = dict(type='bool')
    return args


def get_extra_args_args():
    return dict(
        extra_args=dict(type='str'),
    )


def get_initrd_inject_args():
    return dict(
        initrd_inject=dict(type='str'),
    )


def get_install_args():
    return dict(
        install=dict(
            type='dict',
            options=dict(
                os=dict(type='str', required=True),
                kernel=dict(type='str'),
                initrd=dict(type='str'),
                kernel_args=dict(type='str'),
                kernel_args_overwrite=dict(type='bool'),
                bootdev=dict(type='str'),
                no_install=dict(type='bool'),
            ),
        ),
    )


def get_unattended_args():
    return dict(
        unattended=dict(
            type='dict',
            options=dict(
                profile=dict(type='str'),
                admin_password_file=dict(type='str'),
                user_login=dict(type='str'),
                user_password_file=dict(type='str'),
                product_key=dict(type='str', no_log=True),
            ),
        ),
    )


def get_cloud_init_args():
    return dict(
        cloud_init=dict(
            type='dict',
            options=dict(
                root_password_generate=dict(type='bool'),
                disable=dict(type='bool'),
                root_password_file=dict(type='str'),
                root_ssh_key=dict(type='str', no_log=True),
                clouduser_ssh_key=dict(type='str', no_log=True),
                network_config=dict(type='raw'),
                meta_data=dict(type='raw'),
                user_data=dict(type='raw'),
            ),
        ),
    )


def get_boot_args():
    return dict(
        boot=dict(type='str'),
        boot_opts=dict(type='dict'),
    )


def get_idmap_args():
    return dict(
        idmap=dict(
            type='dict',
            options=dict(
                uid=dict(
                    type='dict',
                    options=dict(
                        start=dict(type='int'),
                        target=dict(type='int'),
                        count=dict(type='int'),
                    ),
                ),
                gid=dict(
                    type='dict',
                    options=dict(
                        start=dict(type='int'),
                        target=dict(type='int'),
                        count=dict(type='int'),
                    ),
                ),
            ),
        ),
    )


def get_osinfo_args():
    return dict(
        osinfo=dict(
            type='dict',
            options=dict(
                name=dict(type='str', aliases=['short_id']),
                id=dict(type='str'),
                detect=dict(type='bool'),
                require=dict(type='bool'),
            ),
        ),
    )


def get_disks_args():
    return dict(
        disks=dict(
            type='list',
            elements="dict",
            options=dict(
                path=dict(type='str'),
                pool=dict(type='str'),
                vol=dict(type='str'),
                size=dict(type='int'),
                sparse=dict(type='bool'),
                format=dict(type='str'),
                backing_store=dict(type='str'),
                backing_format=dict(type='str'),
                bus=dict(type='str'),
                readonly=dict(type='bool'),
                shareable=dict(type='bool'),
                cache=dict(
                    type='str',
                    choices=[
                        "none",
                        "writethrough",
                        "directsync",
                        "unsafe",
                        "writeback",
                    ],
                ),
                serial=dict(type='str'),
                snapshot=dict(
                    type='str', choices=[
                        'internal', 'external', 'no']),
                rawio=dict(type='bool'),
                sgio=dict(type='str', choices=['filtered', 'unfiltered']),
                transient=dict(type='bool'),
                transient_opts=dict(
                    type='dict', options=dict(share_backing=dict(type='bool'))
                ),
                driver=dict(type='dict'),
                source=dict(type='dict'),
                target=dict(type='dict'),
                address=dict(type='dict'),
                boot=dict(type='dict'),
                iotune=dict(type='dict'),
                blockio=dict(type='dict'),
                geometry=dict(type='dict'),
            ),
        ),
    )


def get_filesystems_args():
    return dict(
        filesystems=dict(
            type='list',
            elements="dict",
            options=dict(
                type=dict(
                    type='str',
                    choices=[
                        'mount',
                        'template',
                        'file',
                        'block',
                        'ram',
                        'bind'],
                ),
                accessmode=dict(
                    type='str', choices=['passthrough', 'mapped', 'squash']
                ),
                source=dict(type='dict'),
                target=dict(type='dict'),
                fmode=dict(type='str'),
                dmode=dict(type='str'),
                multidevs=dict(
                    type='str', choices=['default', 'remap', 'forbid', 'warn']
                ),
                readonly=dict(type='bool'),
                space_hard_limit=dict(type='int'),
                space_soft_limit=dict(type='int'),
                driver=dict(type='dict'),
                address=dict(type='dict'),
                binary=dict(type='dict'),
            ),
        ),
    )


def get_networks_args():
    return dict(
        # Network options
        networks=dict(
            type='list',
            elements="dict",
            options=dict(
                type=dict(type='str', choices=['direct']),
                network=dict(type='str'),
                bridge=dict(type='str'),
                hostdev=dict(type='str'),
                source=dict(type='dict'),
                mac=dict(type='dict', options=dict(address=dict(type='str'))),
                mtu=dict(type='dict'),
                state=dict(type='dict'),
                model=dict(type='dict', options=dict(type=dict(type='str'))),
                driver=dict(type='dict'),
                boot=dict(type='dict'),
                filterref=dict(type='dict'),
                rom=dict(type='dict'),
                target=dict(type='dict'),
                address=dict(type='dict'),
                virtualport=dict(type='dict'),
                trust_guest_rx_filters=dict(type='bool'),
            ),
        ),
    )


def get_graphics_args():
    return dict(
        graphics=dict(type='dict'),
        graphics_devices=dict(type='list', elements="dict"),
    )


def get_virt_type_args():
    return dict(
        # Virtualization options
        virt_type=dict(type='str'),
    )


def get_hvm_args():
    return dict(
        hvm=dict(type='bool'),
    )


def get_paravirt_args():
    return dict(
        paravirt=dict(type='bool'),
    )


def get_container_args():
    return dict(
        container=dict(type='bool'),
    )


def get_controller_args():
    return dict(
        controller=dict(type='dict'),
        controller_devices=dict(type='list', elements="dict"),
    )


def get_input_args():
    return dict(
        input=dict(type='dict'),
        input_devices=dict(type='list', elements="dict"),
    )


def get_hostdev_args():
    return dict(
        hostdev=dict(type='dict'),
        host_devices=dict(type='list', elements="dict"),
    )


def get_sound_args():
    return dict(
        sound=dict(type='dict'),
        sound_devices=dict(type='list', elements="dict"),
    )


def get_audio_args():
    return dict(
        audio=dict(type='dict'),
        audio_devices=dict(type='list', elements="dict"),
    )


def get_watchdog_args():
    return dict(
        watchdog=dict(type='dict'),
        watchdog_devices=dict(type='list', elements="dict"),
    )


def get_serial_args():
    return dict(
        serial=dict(type='dict'),
        serial_devices=dict(type='list', elements="dict"),
    )


def get_parallel_args():
    return dict(
        parallel=dict(type='dict'),
        parallel_devices=dict(type='list', elements="dict"),
    )


def get_channel_args():
    return dict(
        channel=dict(type='dict'),
        channel_devices=dict(type='list', elements="dict"),
    )


def get_console_args():
    return dict(
        console=dict(type='dict'),
        console_devices=dict(type='list', elements="dict"),
    )


def get_video_args():
    return dict(
        video=dict(type='dict'),
        video_devices=dict(type='list', elements="dict"),
    )


def get_smartcard_args():
    return dict(
        smartcard=dict(type='dict'),
        smartcard_devices=dict(type='list', elements="dict"),
    )


def get_redirdev_args():
    return dict(
        redirdev=dict(type='dict'),
        redirected_devices=dict(type='list', elements="dict"),
    )


def get_memballoon_args():
    return dict(
        memballoon=dict(type='dict'),
        memballoon_devices=dict(type='list', elements="dict"),
    )


def get_tpm_args():
    return dict(
        tpm=dict(type='dict'),
        tpm_devices=dict(type='list', elements="dict"),
    )


def get_rng_args():
    return dict(
        rng=dict(type='dict'),
        rng_devices=dict(type='list', elements="dict"),
    )


def get_panic_args():
    return dict(
        panic=dict(type='dict'),
        panic_devices=dict(type='list', elements="dict"),
    )


def get_shmem_args():
    return dict(
        shmem=dict(type='dict'),
        shmem_devices=dict(type='list', elements="dict"),
    )


def get_vsock_args():
    return dict(
        vsock=dict(type='dict'),
        vsock_devices=dict(type='list', elements="dict"),
    )


def get_iommu_args():
    return dict(
        iommu=dict(type='dict'),
        iommu_devices=dict(type='list', elements="dict"),
    )


def get_autostart_args():
    return dict(
        # Miscellaneous options
        autostart=dict(type='bool'),
    )


def get_transient_args():
    return dict(
        transient=dict(type='bool'),
    )


def get_destroy_on_exit_args():
    return dict(
        destroy_on_exit=dict(type='bool'),
    )


def get_noreboot_args():
    return dict(
        noreboot=dict(type='bool'),
    )
