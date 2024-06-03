# "archive/u8.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/U8_archive for details about the U8 archive format

import io
import binascii
import os
from dataclasses import dataclass
from typing import List


@dataclass
class U8Node:
    """
    A U8Node object that contains the data of a single node in a U8 file header. Each node keeps track of whether this
    node is for a file or directory, the offset of the name of the file/directory, the offset of the data for the file/
    directory, and the size of the data.

    Attributes
    ----------
    type : int
        Whether this node refers to a file or a directory. Either 0x0000 for files, or 0x0100 for directories.
    name_offset : int
        The offset of the name of the file/directory this node refers to.
    data_offset : int
        The offset of the data for the file/directory this node refers to.
    size : int
        The size of the data for this node.
    """
    type: int
    name_offset: int
    data_offset: int
    size: int


class U8Archive:
    def __init__(self):
        """
        A U8 object that allows for managing the contents of a U8 archive.

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

    def dump(self) -> None:
        """
        Dumps the U8Archive object into a U8 file.
        """
        u8_data = b''
        # Magic number.
        u8_data += b'\x55\xAA\x38\x2D'
        # Root node offset (this is always 0x20).
        u8_data += int.to_bytes(0x20, 4)


def extract_u8(u8_data, output_folder) -> None:
    if os.path.isdir(output_folder):
        raise ValueError("Output folder already exists!")

    os.mkdir(output_folder)

    u8_archive = U8Archive()
    u8_archive.load(u8_data)

    current_dir = ""
    for node in range(len(u8_archive.u8_node_list)):
        if u8_archive.u8_node_list[node].name_offset != 0:
            if u8_archive.u8_node_list[node].type == 256:
                if u8_archive.u8_node_list[node].data_offset == 0:
                    os.mkdir(os.path.join(output_folder, u8_archive.file_name_list[node]))
                    current_dir = u8_archive.file_name_list[node]
                elif u8_archive.u8_node_list[node].data_offset < node:
                    lower_path = os.path.join(output_folder, current_dir)
                    os.mkdir(os.path.join(lower_path, u8_archive.file_name_list[node]))
                    current_dir = os.path.join(current_dir, u8_archive.file_name_list[node])
            elif u8_archive.u8_node_list[node].type == 0:
                lower_path = os.path.join(output_folder, current_dir)
                output_file = open(os.path.join(lower_path, u8_archive.file_name_list[node]), "wb")
                output_file.write(u8_archive.u8_file_data_list[node])
                output_file.close()


def pack_u8(input_data) -> None:
    if os.path.isdir(input_data):
        raise ValueError("Only single-file packing is currently supported!")
    elif os.path.isfile(input_data):
        with open(input_data, "rb") as f:
            u8_archive = U8Archive()

            file_name = os.path.basename(input_data)

            u8_archive.file_name_list.append(file_name)
            u8_archive.u8_file_data_list.append(f.read())


