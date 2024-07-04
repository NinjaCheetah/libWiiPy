# "archive/u8.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/U8_archive for details about the U8 archive format.

import io
import os
import pathlib
from dataclasses import dataclass as _dataclass
from typing import List
from ..shared import _align_value


@_dataclass
class _U8Node:
    """
    A U8Node object that contains the data of a single node in a U8 file header. Each node keeps track of whether this
    node is for a file or directory, the offset of the name of the file/directory, the offset of the data for the file/
    directory, and the size of the data. Private class used by functions and methods in the U8 module.

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
        self.u8_node_list: List[_U8Node] = []  # All the nodes in the header of a U8 file.
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
                self.u8_node_list.append(_U8Node(node_type, node_name_offset, node_data_offset, node_size))
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
        data_offset = _align_value(header_size + 32, 16)
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
    """
    Extracts the provided U8 archive file data into the provided output folder path. Note that the folder must not
    already exist to ensure that the output can correctly represent the file structure of the original U8 archive.

    Parameters
    ----------
    u8_data : bytes
        The data for the U8 file to extract.
    output_folder : str
        The path to a new folder to extract the archive to.
    """
    output_folder = pathlib.Path(output_folder)
    # Check if the path already exists, and if it does, ensure that it is both a directory and empty.
    if output_folder.exists():
        if output_folder.is_dir() and next(os.scandir(output_folder), None):
            raise ValueError("Output folder is not empty!")
        elif output_folder.is_file():
            raise ValueError("A file already exists with the provided name!")
    else:
        os.mkdir(output_folder)
    # Create a new U8Archive object and load the provided U8 file data into it.
    u8_archive = U8Archive()
    u8_archive.load(u8_data)
    # This variable stores the path of the directory we're currently processing.
    current_dir = output_folder
    # This variable stores the final nodes for every directory we've entered, and is used to handle the recursion of
    # those directories to ensure that everything gets where it belongs.
    directory_recursion = [0]
    # Iterate over every node and extract the files and folders.
    for node in range(len(u8_archive.u8_node_list)):
        # Code for a directory node. Second check just ensures we ignore the root node.
        if u8_archive.u8_node_list[node].type == 256 and u8_archive.u8_node_list[node].name_offset != 0:
            # The size value for a directory node is the position of the last node in this directory, with the root node
            # counting as node 1.
            # If the current node is below the end of the current directory, create this directory inside the previous
            # current directory and make the current.
            if node + 1 < directory_recursion[-1]:
                current_dir = current_dir.joinpath(u8_archive.file_name_list[node])
                os.mkdir(current_dir)
            # If the current node is beyond the end of the current directory, we've followed that path all the way down,
            # so reset back to the root directory and put our new directory there.
            elif node + 1 > directory_recursion[-1]:
                current_dir = output_folder.joinpath(u8_archive.file_name_list[node])
                os.mkdir(current_dir)
            # This check is here just in case a directory ever ends with an empty directory and not a file.
            elif node + 1 == directory_recursion[-1]:
                current_dir = current_dir.parent
                directory_recursion.pop()
            # If the last node for the directory we just processed is new (which is always should be), add it to the
            # recursion array.
            if u8_archive.u8_node_list[node].size not in directory_recursion:
                directory_recursion.append(u8_archive.u8_node_list[node].size)
        # Code for a file node.
        elif u8_archive.u8_node_list[node].type == 0:
            # Write out the file to the current directory.
            output_file = open(current_dir.joinpath(u8_archive.file_name_list[node]), "wb")
            output_file.write(u8_archive.file_data_list[node])
            output_file.close()
            # If this file is the final node for the current directory, pop() the recursion array and set the current
            # directory to the parent of the previous current.
            if node + 1 in directory_recursion:
                current_dir = current_dir.parent
                directory_recursion.pop()
        # Code for a totally unrecognized node type, which should not happen.
        elif u8_archive.u8_node_list[node].type != 0 and u8_archive.u8_node_list[node].type != 256:
            raise ValueError("A node with an invalid type (" + str(u8_archive.u8_node_list[node].type) + ") was"
                             "found!")


def _pack_u8_dir(u8_archive: U8Archive, current_path, node_count, name_offset):
    # First, get the list of everything in current path.
    root_list = os.listdir(current_path)
    file_list = []
    dir_list = []
    # Create separate lists of the files and directories in the current directory so that we can handle the files first.
    for path in root_list:
        if os.path.isfile(current_path.joinpath(path)):
            file_list.append(path)
        elif os.path.isdir(current_path.joinpath(path)):
            dir_list.append(path)
    # For files, read their data into the file data list, add their name into the file name list, then calculate the
    # offset for their file name and create a new U8Node() for them.
    for file in file_list:
        node_count += 1
        u8_archive.file_name_list.append(file)
        u8_archive.file_data_list.append(open(current_path.joinpath(file), "rb").read())
        u8_archive.u8_node_list.append(_U8Node(0, name_offset, 0, len(u8_archive.file_data_list[-1])))
        name_offset = name_offset + len(file) + 1  # Add 1 to accommodate the null byte at the end of the name.
    # For directories, add their name to the file name list, add empty data to the file data list (since they obviously
    # wouldn't have any), find the total number of files and directories inside the directory to calculate the final
    # node included in it, then recursively call this function again on that directory to process it.
    for directory in dir_list:
        node_count += 1
        u8_archive.file_name_list.append(directory)
        u8_archive.file_data_list.append(b'')
        max_node = node_count + sum(1 for _ in current_path.joinpath(directory).rglob('*'))
        u8_archive.u8_node_list.append(_U8Node(256, name_offset, 0, max_node))
        name_offset = name_offset + len(directory) + 1  # Add 1 to accommodate the null byte at the end of the name.
        u8_archive, node_count, name_offset = _pack_u8_dir(u8_archive, current_path.joinpath(directory), node_count,
                                                           name_offset)
    # Return the U8Archive object, the current node we're on, and the current name offset.
    return u8_archive, node_count, name_offset


def pack_u8(input_path) -> bytes:
    """
    Packs the provided file or folder into a new U8 archive, and returns the raw file data for it.

    Parameters
    ----------
    input_path
        The path to the input file or folder.

    Returns
    -------
    u8_archive : bytes
        The data for the packed U8 archive.
    """
    input_path = pathlib.Path(input_path)
    if os.path.isdir(input_path):
        # Append empty entries at the start for the root node, and then create the root U8Node() object, using rglob()
        # to read the total count of files and directories that will be packed so that we can add the total node count.
        u8_archive = U8Archive()
        u8_archive.file_name_list.append("")
        u8_archive.file_data_list.append(b'')
        u8_archive.u8_node_list.append(_U8Node(256, 0, 0, sum(1 for _ in input_path.rglob('*')) + 1))
        # Call the private function _pack_u8_dir() on the root note, which will recursively call itself to pack every
        # subdirectory and file. Discard node_count and name_offset since we don't care about them here, as they're
        # really only necessary for the directory recursion.
        u8_archive, _, _ = _pack_u8_dir(u8_archive, input_path, node_count=1, name_offset=1)
        return u8_archive.dump()
    elif os.path.isfile(input_path):
        # Simple code to handle if a single file is provided as input. Not really sure *why* you'd do this, since the
        # whole point of a U8 archive is to stitch files together, but it's here nonetheless.
        with open(input_path, "rb") as f:
            u8_archive = U8Archive()
            file_name = input_path.name
            file_data = f.read()
            # Append blank file name for the root node.
            u8_archive.file_name_list.append("")
            u8_archive.file_name_list.append(file_name)
            # Append blank data for the root node.
            u8_archive.file_data_list.append(b'')
            u8_archive.file_data_list.append(file_data)
            # Append generic U8Node for the root, followed by the actual file's node.
            u8_archive.u8_node_list.append(_U8Node(256, 0, 0, 2))
            u8_archive.u8_node_list.append(_U8Node(0, 1, 0, len(file_data)))
            return u8_archive.dump()
    else:
        raise FileNotFoundError("Input file/directory: \"" + str(input_path) + "\" does not exist!")
