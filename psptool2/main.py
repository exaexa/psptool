# PSPTool - Display, extract and manipulate PSP firmware inside UEFI images
# Copyright (C) 2019 Christian Werling, Robert Buhren
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from prettytable import PrettyTable
from .blob import Blob

import operator

class PSPTool:
    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as f:
            rom_bytes = bytearray(f.read())

        pt = PSPTool(rom_bytes)
        pt.filename = filename

        return pt

    def __init__(self, rom_bytes):
        self.blob = Blob(rom_bytes, len(rom_bytes))
        self.filename = None

    def __repr__(self):
        if self.filename is not None:
            return f'PSPTool(filename={self.filename})'
        else:
            return f'PSPTool(len(rom_bytes)={self.blob.buffer_size}'

    def to_file(self, filename):
        with open(filename, 'wb') as f:
            f.write(self.blob.get_buffer())

    def ls(self, no_duplicates=False, display_entry_header=False):
        for index, directory in enumerate(self.blob.directories):
            t = PrettyTable(['Directory', 'Addr', 'Type', 'Magic', 'Secondary Directory'])
            t.add_row([
                index,
                hex(directory.get_address()),
                directory.type,
                directory.magic.decode('utf-8', 'backslashreplace'),
                hex(directory.secondary_directory_address) if directory.secondary_directory_address else '--'
            ])

            print(t)

            self.ls_dir(index)
            print('\n')

    def ls_dir(self, directory_index):
        directory = self.blob.directories[directory_index]
        self.ls_entries(entries=directory.entries)

    def ls_entries(self, entries=None):
        # list all entries of all directories by default (sorted by their address)
        if entries is None:
            entries = sorted(self.blob.unique_entries)

        basic_fields = [' ', 'Entry', 'Address', 'Size', 'Type', 'Type Name', 'Magic', 'Version', 'Signed by']
        t = PrettyTable(basic_fields)
        t.align = 'r'

        for index, entry in enumerate(entries):
            t.add_row([
                '',
                index,
                hex(entry.get_address()),
                hex(entry.buffer_size),
                hex(entry.type),
                entry.get_readable_type(),
                entry.get_readable_magic(),
                entry.get_readable_version(),
                entry.get_readable_signed_by()
            ])

        print(t.get_string(fields=basic_fields))
