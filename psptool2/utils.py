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

import sys
import argparse


class ObligingArgumentParser(argparse.ArgumentParser):
    """ Display the full help message whenever there is something wrong with the arguments.
        (from https://groups.google.com/d/msg/argparse-users/LazV_tEQvQw/xJhBOm1qS5IJ) """
    def error(self, message):
        sys.stderr.write('Error: %s\n' % message)
        self.print_help()
        sys.exit(2)


class NestedBuffer:
    def __init__(self, parent_buffer, buffer_size: int, buffer_offset: int = 0):
        self.parent_buffer = parent_buffer
        self.buffer_size = buffer_size
        self.buffer_offset = buffer_offset
        assert(self.buffer_size <= self.buffer_offset + self.buffer_size)

    def __len__(self):
        return self.buffer_size

    def __getitem__(self, item):
        if isinstance(item, slice):
            new_slice = self._offset_slice(item)
            return self.parent_buffer[new_slice]
        else:
            assert(isinstance(item, int))
            return self.parent_buffer[item]

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            new_slice = self._offset_slice(key)
            self.parent_buffer[new_slice] = value
        else:
            assert(isinstance(key, int))
            self.parent_buffer[self.buffer_offset + key] = value

    def _offset_slice(self, old_slice):
        if old_slice.start is None:
            start = self.buffer_offset
        else:
            assert (old_slice.start <= self.buffer_size)
            if old_slice.start < 0:
                start = self.buffer_offset + old_slice.start % self.buffer_size
            else:
                start = self.buffer_offset + old_slice.start
        if old_slice.stop is None:
            stop = self.buffer_offset + self.buffer_size
        else:
            assert (old_slice.stop <= self.buffer_size)
            if old_slice.stop < 0:
                stop = self.buffer_offset + old_slice.stop % self.buffer_size
            else:
                stop = self.buffer_offset + old_slice.stop

        new_slice = slice(start, stop, old_slice.step)
        return new_slice

    def get_address(self) -> int:
        if isinstance(self.parent_buffer, NestedBuffer):
            return self.buffer_offset + self.parent_buffer.get_address()
        else:
            return self.buffer_offset

    def get_buffer(self):
        return self.parent_buffer

    def get_bytes(self, address: int = 0x0, size: int = None) -> bytes:
        size = self.buffer_size if size is None else size
        return bytes(self[address:address + size])

    def set_bytes(self, address: int, size: int, value):
        self[address:address + size] = value

    def get_chunks(self, size: int, offset: int = 0):
        return chunker(self[offset:], size)


def print_error_and_exit(arg0, *nargs, **kwargs):
    """ Wrapper function to print errors to stderr, so we don't interfere with e.g. extraction output. """
    arg0 = 'Error: ' + arg0 + '\n'
    sys.stderr.write(arg0, *nargs, **kwargs)
    sys.exit(1)


def print_warning(arg0, *nargs, **kwargs):
    """ Wrapper function to print warnings to stderr, so we don't interfere with e.g. extraction output. """
    arg0 = 'Warning: ' + arg0 + '\n'
    sys.stderr.write(arg0, *nargs, **kwargs)


def print_info(arg0, *nargs, **kwargs):
    """ Wrapper function to print info to stderr, so we don't interfere with e.g. extraction output. """
    arg0 = 'Info: ' + arg0 + '\n'
    sys.stderr.write(arg0, *nargs, **kwargs)


def chunker(seq, size):
    """ Utility function to chunk seq into a list of size sized sequences. """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def rstrip_padding(bytestring):
    """ Takes a bytestring and strips trailing 0xFFFFFFFF dwords. """
    i = 0
    while bytestring[-(4+i):len(bytestring)-i] == b'\xff\xff\xff\xff':
        i += 4
    return bytestring[:len(bytestring)-i]
