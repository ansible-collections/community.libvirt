# (c) 2025, Joey Zhang <thinkdoggie@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json


class QemuImgTool(object):
    """
    A wrapper for invoking qemu-img command-line tool.
    """

    def __init__(self, module,
                 qemu_img_path=None):
        self.module = module
        self.warnings = []
        self._base_command = qemu_img_path if qemu_img_path is not None else 'qemu-img'
        self.command_argv = [self._base_command]

    def _reset_command(self):
        """Reset command_argv to base command for new operation"""
        self.command_argv = [self._base_command]

    def _add_flag(self, flag):
        """Add a flag to the command line"""
        self.command_argv.append(flag)

    def _add_option(self, flag, value):
        """Add an option with value to the command line"""
        if value is not None:
            self.command_argv.append(flag)
            self.command_argv.append(str(value))

    def _add_option_list(self, flag, value_list):
        """Add multiple values for an option"""
        if value_list:
            for value in value_list:
                if value is not None:
                    self.command_argv.append(flag)
                    self.command_argv.append(str(value))

    def convert(self, filename, output_filename,
                source_format=None, output_format=None,
                compressed=False, sparse_size=None, num_coroutines=None):
        """
        Build and execute qemu-img convert command

        This operation creates a new image file and respects check_mode.
        In check_mode, the command is built but not executed.
        """
        self._reset_command()
        self.command_argv.append('convert')

        if source_format:
            self._add_option('-f', source_format)

        if output_format:
            self._add_option('-O', output_format)

        if compressed:
            self._add_flag('-c')

        if sparse_size:
            self._add_option('-S', sparse_size)

        if num_coroutines:
            self._add_option('-m', num_coroutines)

        # Add disk image filename
        self.command_argv.append(str(filename))

        # Add output filename (must be last)
        self.command_argv.append(str(output_filename))

        # Check if we're in check mode
        if self.module.check_mode:
            # In check mode, don't execute the command but return success
            return 0, "Would convert image from %s to %s" % (filename, output_filename), ""

        # Execute the command
        rc, stdout, stderr = self.module.run_command(
            self.command_argv, check_rc=False)

        return rc, stdout, stderr

    def info(self, filename, source_format=None,
             backing_chain=False):
        """
        Build and execute qemu-img info command

        This operation is read-only and does not respect check_mode
        as it doesn't modify the system state.
        """
        self._reset_command()
        self.command_argv.append('info')

        if source_format:
            self._add_option('-f', source_format)

        if backing_chain:
            self._add_flag('--backing-chain')

        self._add_option('--output', "json")
        # Add disk image filename
        self.command_argv.append(str(filename))

        # Execute the command
        rc, stdout, stderr = self.module.run_command(
            self.command_argv, check_rc=False)

        # Parse output based on format
        parsed_output = dict()
        if rc == 0 and stdout.strip():
            try:
                parsed_output = json.loads(stdout)
            except ValueError as e:
                # If JSON parsing fails, add warning
                self.warnings.append(
                    "Failed to parse JSON output: %s" % str(e))

        return rc, parsed_output, stderr

    def resize(self, filename, size, source_format=None,
               preallocation=None, shrink=False):
        """
        Build and execute qemu-img resize command

        This operation modifies an existing image file and respects check_mode.
        In check_mode, the command is built but not executed.

        Args:
            filename (str): Image file path
            size (str): New size with optional +/- prefix and size suffixes (k, M, G, T)
                       Examples: '10G', '+1G', '-500M'
            source_format (str): Disk image format (auto-detected if None)
            preallocation (str): Preallocation mode ('off', 'metadata', 'falloc', 'full')
            shrink (bool): Allow shrinking (required for size reduction)

        Returns:
            tuple: (rc, stdout, stderr)
        """
        self._reset_command()
        self.command_argv.append('resize')

        if source_format:
            self._add_option('-f', source_format)

        if preallocation:
            self._add_option('--preallocation', preallocation)

        if shrink:
            self._add_flag('--shrink')

        # Add disk image filename
        self.command_argv.append(str(filename))

        # Add size (must be last)
        self.command_argv.append(str(size))

        # Check if we're in check mode
        if self.module.check_mode:
            # In check mode, don't execute the command but return success
            return 0, "Would resize image %s to %s" % (filename, size), ""

        # Execute the command
        rc, stdout, stderr = self.module.run_command(
            self.command_argv, check_rc=False)

        return rc, stdout, stderr
