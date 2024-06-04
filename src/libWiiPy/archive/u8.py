# "archive/u8.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/U8_archive for details about the U8 archive format

import io
import os
from dataclasses import dataclass
from typing import List
from src.libWiiPy.shared import align_value


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
        self.u8_node_list: List[U8Node] = []  # All the nodes in the header of a U8 file.
        self.file_name_list: List[str] = []
        self.file_data_list: List[bytes] = []
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
            # The following code is all skipped because these values really don't matter for extraction. They honestly
            # really only matter to my code when they get calculated and used for packing.

            # Offset of the root node, which will always be 0x20.
            # root_node_offset = int(binascii.hexlify(u8_data.read(4)), 16)
            # The size of the U8 header.
            # header_size = int(binascii.hexlify(u8_data.read(4)), 16)
            # The offset of the data, which is root_node_offset + header_size, aligned to 0x10.
            # data_offset = int(binascii.hexlify(u8_data.read(4)), 16)

            # Seek ahead to the size defined in the root node, because it's the total number of nodes in the file. The
            # rest of the data in the root node (not that it really matters) will get read when we read the whole list.
            u8_data.seek(u8_data.tell() + 36)
            root_node_size = int.from_bytes(u8_data.read(4))
            # Seek back before the root node so that it gets read with all the rest.
            u8_data.seek(u8_data.tell() - 12)
            # Iterate over the number of nodes that the root node lists.
            for node in range(root_node_size):
                node_type = int.from_bytes(u8_data.read(2))
                node_name_offset = int.from_bytes(u8_data.read(2))
                node_data_offset = int.from_bytes(u8_data.read(4))
                node_size = int.from_bytes(u8_data.read(4))
                self.u8_node_list.append(U8Node(node_type, node_name_offset, node_data_offset, node_size))
            # Iterate over all loaded nodes and create a list of file names and a list of file data.
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
                    self.file_data_list.append(u8_data.read(node.size))
                else:
                    self.file_data_list.append(b'')

    def dump(self) -> bytes:
        """
        Dumps the U8Archive object into the raw data of a U8 archive.

        Returns
        -------
        bytes
            The full U8 archive as bytes.
        """
        # This is 0 because the header size DOES NOT include the initial 32 bytes describing the file.
        header_size = 0
        # Add 12 bytes for each node, since that's how many bytes each one is made up of.
        for node in range(len(self.u8_node_list)):
            header_size += 12
        # Add the number of bytes used for each file/folder name in the string table.
        for file_name in self.file_name_list:
            header_size += len(file_name) + 1
        # The initial data offset is equal to the file header (32 bytes) + node data aligned to 16 bytes.
        data_offset = align_value(header_size + 32, 16)
        # Adjust all nodes to place file data in the same order as the nodes. Why isn't it already like this?
        current_data_offset = data_offset
        for node in range(len(self.u8_node_list)):
            if self.u8_node_list[node].type == 0:
                self.u8_node_list[node].data_offset = current_data_offset
                current_data_offset += self.u8_node_list[node].size
        # Begin joining all the U8 archive data into one variable.
        u8_data = b''
        # Magic number.
        u8_data += b'\x55\xAA\x38\x2D'
        # Root node offset (this is always 0x20).
        u8_data += int.to_bytes(0x20, 4)
        # Size of the file header (excluding the first 32 bytes).
        u8_data += int.to_bytes(header_size, 4)
        # Offset of the beginning of the data region of the U8 archive.
        u8_data += int.to_bytes(data_offset, 4)
        # 16 bytes of zeroes.
        u8_data += (b'\x00' * 16)
        # Iterate over all the U8 nodes and dump them.
        for node in self.u8_node_list:
            u8_data += int.to_bytes(node.type, 2)
            u8_data += int.to_bytes(node.name_offset, 2)
            u8_data += int.to_bytes(node.data_offset, 4)
            u8_data += int.to_bytes(node.size, 4)
        # Iterate over all file names and dump them. All file names are suffixed by a \x00 byte.
        for file_name in self.file_name_list:
            u8_data += str.encode(file_name) + b'\x00'
        # Apply the extra padding we calculated earlier by padding to where the data offset begins.
        while len(u8_data) < data_offset:
            u8_data += b'\x00'
        # Iterate all file data and dump it.
        for file in self.file_data_list:
            u8_data += file
        # Return the U8 archive.
        return u8_data


def extract_u8(u8_data, output_folder) -> None:
    if os.path.isdir(output_folder):
        raise ValueError("Output folder already exists!")
    os.mkdir(output_folder)
    # Create a new U8Archive object and load the provided U8 file data into it.
    u8_archive = U8Archive()
    u8_archive.load(u8_data)
    # TODO: Comment this
    # Also TODO: You can go more than two layers! Really should've checked that more before assuming it was the case.
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
                output_file.write(u8_archive.file_data_list[node])
                output_file.close()


def pack_u8(input_path) -> bytes:
    if os.path.isdir(input_path):
        raise ValueError("Only single-file packing is currently supported!")
    elif os.path.isfile(input_path):
        with open(input_path, "rb") as f:
            u8_archive = U8Archive()

            file_name = os.path.basename(input_path)
            file_data = f.read()

            u8_archive.file_name_list.append("")
            u8_archive.file_name_list.append(file_name)

            u8_archive.file_data_list.append(b'')
            u8_archive.file_data_list.append(file_data)

            u8_archive.u8_node_list.append(U8Node(256, 0, 0, 2))
            u8_archive.u8_node_list.append(U8Node(0, 1, 0, len(file_data)))

            return u8_archive.dump()
