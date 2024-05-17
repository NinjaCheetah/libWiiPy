# "u8.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/U8_archive for details about the U8 archive format

import io
import binascii
from typing import List
from .types import U8Node


class U8Archive:
    def __init__(self):
        """
        A U8 object that allows for extracting and packing U8 archives.

        Attributes
        ----------
        """
        self.u8_magic = b''
        self.root_node_offset = 0  # Offset of the root node, which will always be 0x20.
        self.header_size = 0  # The size of the U8 header.
        self.data_offset = 0  # The offset of the data, which is root_node_offset + header_size, aligned to 0x40.
        self.header_padding = b''
        self.root_node = U8Node
        self.u8_node_list: List[U8Node] = []  # All the nodes in the header of a U8 file.
        self.file_name_list: List[str] = []
        self.u8_file_data_list: List[bytes] = []
        self.u8_file_structure = dict

    def load(self, u8_data: bytes) -> None:
        """
        Loads raw U8 data into a new U8 object. This allows for extracting the file and updating its contents.

        Parameters
        ----------
        u8_data : bytes
            The data for the U8 file to load.
        """
        with io.BytesIO(u8_data) as u8_data:
            # Read the first 4 bytes of the file to ensure that it's a U8 archive.
            u8_data.seek(0x0)
            self.u8_magic = u8_data.read(4)
            if self.u8_magic != b'\x55\xAA\x38\x2D':
                raise TypeError("This is not a valid U8 archive!")
            self.root_node_offset = int(binascii.hexlify(u8_data.read(4)), 16)
            self.header_size = int(binascii.hexlify(u8_data.read(4)), 16)
            self.data_offset = int(binascii.hexlify(u8_data.read(4)), 16)
            self.header_padding = u8_data.read(16)
            root_node_type = int.from_bytes(u8_data.read(2))
            root_node_name_offset = int.from_bytes(u8_data.read(2))
            root_node_data_offset = int.from_bytes(u8_data.read(4))
            root_node_size = int.from_bytes(u8_data.read(4))
            self.root_node = U8Node(root_node_type, root_node_name_offset, root_node_data_offset, root_node_size)
            self.u8_node_list.append(self.root_node)
            # Iterate over the number of nodes that the root node lists, minus one since the count includes itself.
            for node in range(self.root_node.size - 1):
                node_type = int.from_bytes(u8_data.read(2))
                node_name_offset = int.from_bytes(u8_data.read(2))
                node_data_offset = int.from_bytes(u8_data.read(4))
                node_size = int.from_bytes(u8_data.read(4))
                self.u8_node_list.append(U8Node(node_type, node_name_offset, node_data_offset, node_size))
            # Iterate over all loaded nodes and create a list of file names.
            name_base_offset = u8_data.tell()
            for node in self.u8_node_list:
                u8_data.seek(name_base_offset + node.name_offset)
                name_bin = b''
                while name_bin[-1:] != b'\x00':
                    name_bin += u8_data.read(1)
                name_bin = name_bin[:-1]
                name = str(name_bin.decode())
                self.file_name_list.append(name)
                if node.type == 0:
                    u8_data.seek(node.data_offset)
                    self.u8_file_data_list.append(u8_data.read(node.size))
                else:
                    self.u8_file_data_list.append(b'')
            # This does nothing for now.
            next_dir = 0
            for node in range(len(self.u8_node_list)):
                if self.u8_node_list[node].type == 256 and node != 0:
                    next_dir = self.u8_node_list[node].size

