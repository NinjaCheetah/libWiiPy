# "archive/u8.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/U8_archive for details about the U8 archive format.

import binascii
import hashlib
import io
import os
import pathlib
from enum import IntEnum as _IntEnum
from dataclasses import dataclass as _dataclass
from typing import List, Tuple
from ..shared import _align_value, _pad_bytes


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
    """
    A U8 object that allows for parsing and editing the contents of a U8 archive.

    Attributes
    ----------
    u8_node_list : List[_U8Node]
        A list of U8Node objects representing the nodes of the U8 archive.
    file_name_list : List[str]
        A list of the names of the files in the U8 archive.
    file_data_list : List[bytes]
        A list of file data for the files in the U8 archive; corresponds with file_name_list.
    header_size : int
        The size of the U8 archive header.
    data_offset : int
        The offset of the data region of the U8 archive.
    imet_header: IMETHeader
        The IMET header of the U8 archive, if one exists. Otherwise, an empty IMETHeader object.
    """
    def __init__(self):
        self.u8_magic = b''
        self.u8_node_list: List[_U8Node] = []  # All the nodes in the header of a U8 file.
        self.file_name_list: List[str] = []
        self.file_data_list: List[bytes] = []
        self.root_node_offset: int = 0
        self.header_size: int = 0
        self.data_offset: int = 0
        self.root_node: _U8Node = _U8Node(0, 0, 0, 0)
        self.imet_header: IMETHeader = IMETHeader()

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
                # Check for an IMET header, if the file doesn't start with the proper magic number. The header magic
                # may be at either 0x40 or 0x80 depending on whether this title has a build tag at the start or not.
                u8_data.seek(0x40)
                self.u8_magic = u8_data.read(4)
                if self.u8_magic == b'\x49\x4D\x45\x54':
                    # IMET with no build tag means the U8 archive should start at 0x600.
                    u8_data.seek(0x600)
                    self.u8_magic = u8_data.read(4)
                    if self.u8_magic != b'\x55\xAA\x38\x2D':
                        raise TypeError("This is not a valid U8 archive!")
                    # Parse the IMET header, then continue parsing the U8 archive.
                    u8_data.seek(0x0)
                    self.imet_header.load(u8_data.read(0x600))
                else:
                    # This check will pass if the IMET comes after a build tag.
                    u8_data.seek(0x80)
                    self.u8_magic = u8_data.read(4)
                    if self.u8_magic == b'\x49\x4D\x45\x54':
                        # IMET with a build tag means the U8 archive should start at 0x640.
                        u8_data.seek(0x640)
                        self.u8_magic = u8_data.read(4)
                        if self.u8_magic != b'\x55\xAA\x38\x2D':
                            raise TypeError("This is not a valid U8 archive!")
                        # Parse the IMET header, then continue parsing the U8 archive.
                        u8_data.seek(0x40)
                        self.imet_header.load(u8_data.read(0x600))
                    else:
                        raise TypeError("This is not a valid U8 archive!")
            # Offset of the root node, which will always be 0x20.
            self.root_node_offset = int.from_bytes(u8_data.read(4))
            # The size of the U8 header.
            self.header_size = int.from_bytes(u8_data.read(4))
            # The offset of the data, which is root_node_offset + header_size, aligned to 0x10.
            self.data_offset = int.from_bytes(u8_data.read(4))
            # Seek past 16 bytes of padding, then load the root node.
            u8_data.seek(u8_data.tell() + 16)
            root_node_type = int.from_bytes(u8_data.read(1))
            root_node_name_offset = int.from_bytes(u8_data.read(3))
            root_node_data_offset = int.from_bytes(u8_data.read(4))
            root_node_size = int.from_bytes(u8_data.read(4))
            self.root_node = _U8Node(root_node_type, root_node_name_offset, root_node_data_offset, root_node_size)
            # Seek back before the root node so that it gets read with all the rest.
            u8_data.seek(u8_data.tell() - 12)
            # Iterate over the number of nodes that the root node lists.
            for node in range(root_node_size):
                node_type = int.from_bytes(u8_data.read(1))
                node_name_offset = int.from_bytes(u8_data.read(3))
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
        # The initial data offset is equal to the file header (32 bytes) + node data aligned to 64 bytes.
        data_offset = _align_value(header_size + 32, 64)
        # Adjust all nodes to place file data in the same order as the nodes. Why isn't it already like this?
        current_data_offset = data_offset
        current_name_offset = 0
        for node in range(len(self.u8_node_list)):
            if self.u8_node_list[node].type == 0:
                self.u8_node_list[node].data_offset = _align_value(current_data_offset, 32)
                current_data_offset += _align_value(self.u8_node_list[node].size, 32)
            # Calculate the name offsets, including the extra 1 for the NULL byte at the end of each name.
            self.u8_node_list[node].name_offset = current_name_offset
            current_name_offset += len(self.file_name_list[node]) + 1
        # Begin joining all the U8 archive data into bytes.
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
            u8_data += int.to_bytes(node.type, 1)
            u8_data += int.to_bytes(node.name_offset, 3)
            u8_data += int.to_bytes(node.data_offset, 4)
            u8_data += int.to_bytes(node.size, 4)
        # Iterate over all file names and dump them. All file names are suffixed by a \x00 byte.
        for file_name in self.file_name_list:
            u8_data += str.encode(file_name) + b'\x00'
        # Apply the extra padding we calculated earlier by padding to where the data offset begins.
        u8_data = _pad_bytes(u8_data, 64)
        # Iterate all file data and dump it.
        for file in self.file_data_list:
            u8_data += _pad_bytes(file, 32)
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
    # This variable stores the order of directory nodes leading to the current working directory, to make sure that
    # things get where they belong.
    parent_dirs = [0]
    for node in range(len(u8_archive.u8_node_list)):
        # Code for a directory node (excluding the root node since that already exists).
        if u8_archive.u8_node_list[node].type == 1 and u8_archive.u8_node_list[node].name_offset != 0:
            if u8_archive.u8_node_list[node].data_offset == parent_dirs[-1]:
                current_dir = current_dir.joinpath(u8_archive.file_name_list[node])
                current_dir.mkdir(exist_ok=True)
                parent_dirs.append(node)
            else:
                # Go up until we're back at the correct level.
                while u8_archive.u8_node_list[node].data_offset != parent_dirs[-1]:
                    parent_dirs.pop()
                parent_dirs.append(node)
                current_dir = output_folder
                # Rebuild current working directory, and make sure all directories in the path exist.
                for directory in parent_dirs:
                    current_dir = current_dir.joinpath(u8_archive.file_name_list[directory])
                    current_dir.mkdir(exist_ok=True)
        # Code for a file node.
        elif u8_archive.u8_node_list[node].type == 0:
            open(current_dir.joinpath(u8_archive.file_name_list[node]), "wb").write(u8_archive.file_data_list[node])
        # Handle an invalid node type.
        elif u8_archive.u8_node_list[node].type != 0 and u8_archive.u8_node_list[node].type != 1:
            raise ValueError(f"A node with an invalid type ({str(u8_archive.u8_node_list[node].type)}) was found!")


def _pack_u8_dir(u8_archive: U8Archive, current_path, node_count, parent_node):
    # First, get the list of everything in current path.
    root_list = os.listdir(current_path)
    file_list = []
    dir_list = []
    # Create separate lists of the files and directories in the current directory so that we can handle the files first.
    # noinspection PyTypeChecker
    root_list.sort(key=str.lower)
    for path in root_list:
        if os.path.isfile(current_path.joinpath(path)):
            file_list.append(path)
        elif os.path.isdir(current_path.joinpath(path)):
            dir_list.append(path)
    # noinspection PyTypeChecker
    file_list.sort(key=str.lower)
    # noinspection PyTypeChecker
    dir_list.sort(key=str.lower)
    # For files, read their data into the file data list, add their name into the file name list, then calculate the
    # offset for their file name and create a new U8Node() for them. -1 values are temporary and are set during dumping.
    for file in file_list:
        node_count += 1
        u8_archive.file_name_list.append(file)
        u8_archive.file_data_list.append(open(current_path.joinpath(file), "rb").read())
        u8_archive.u8_node_list.append(_U8Node(0, -1, -1, len(u8_archive.file_data_list[-1])))
    # For directories, add their name to the file name list, add empty data to the file data list (since they obviously
    # wouldn't have any), find the total number of files and directories inside the directory to calculate the final
    # node included in it, then recursively call this function again on that directory to process it.
    for directory in dir_list:
        node_count += 1
        u8_archive.file_name_list.append(directory)
        u8_archive.file_data_list.append(b'')
        max_node = node_count + sum(1 for _ in current_path.joinpath(directory).rglob('*'))
        u8_archive.u8_node_list.append(_U8Node(1, -1, parent_node, max_node))
        u8_archive, node_count = _pack_u8_dir(u8_archive, current_path.joinpath(directory), node_count,
                                              u8_archive.u8_node_list.index(u8_archive.u8_node_list[-1]))
    # Return the U8Archive object, the current node we're on, and the current name offset.
    return u8_archive, node_count


def pack_u8(input_path, generate_imet=False, imet_titles:List[str]=None) -> bytes:
    """
    Packs the provided file or folder into a new U8 archive, and returns the raw file data for it.

    To generate an IMET header for this U8 archive, the archive must contain the required banner files "icon.bin",
    "banner.bin", and "sound.bin", because the sizes of these files are stored in the header.

    Parameters
    ----------
    input_path
        The path to the input file or folder.
    generate_imet : bool, optional
        Whether an IMET header should be generated for this U8 archive or not. IMET headers are only used for channel
        banners (00000000.app), and required banner files must exist to generate this header. Defaults to False.
    imet_titles : List[str], optional
        A list of the channel title in different languages for the IMET header. If only one item is provided, that
        item will be used for all entries in the header. Defaults to None, and is only used when generate_imet is True.

    Returns
    -------
    u8_archive : bytes
        The data for the packed U8 archive.
    """
    input_path = pathlib.Path(input_path)
    if input_path.is_dir():
        # Append empty entries at the start for the root node, and then create the root U8Node() object, using rglob()
        # to read the total count of files and directories that will be packed so that we can add the total node count.
        u8_archive = U8Archive()
        u8_archive.file_name_list.append("")
        u8_archive.file_data_list.append(b'')
        u8_archive.u8_node_list.append(_U8Node(1, 0, 0, sum(1 for _ in input_path.rglob('*')) + 1))
        # Call the private function _pack_u8_dir() on the root note, which will recursively call itself to pack every
        # subdirectory and file. Discard node_count and name_offset since we don't care about them here, as they're
        # really only necessary for the directory recursion.
        u8_archive, _ = _pack_u8_dir(u8_archive, input_path, node_count=1, parent_node=0)
        if generate_imet:
            print("gen imet")
        return u8_archive.dump()
    elif input_path.is_file():
        raise ValueError("This does not appear to be a directory.")
    else:
        raise FileNotFoundError(f"Input directory: \"{input_path}\" does not exist!")


class IMETHeader:
    """
    An IMETHeader object that allows for parsing, editing, and generating an IMET header. These headers precede the
    data of a channel banner (00000000.app), and are used to store metadata about the banner and verify its data.

    An IMET header is always 1,536 (0x600) bytes long.

    Attributes
    ----------
    magic : str
        Magic number for the header, should be "IMD5".
    header_size : int
        Length of the M
    imet_version : int
        Version of the IMET header. Normally always 3.
    sizes : List[int]
        The file sizes of icon.bin, banner.bin, and sound.bin.
    flag1 : int
        Unknown.
    channel_names : List[str]
        The name of the channel this header is for in Japanese, English, German, French, Spanish, Italian, Dutch,
        Simplified Chinese, Traditional Chinese, and Korean, in that order.
    md5_hash : bytes
        MD5 sum of the entire header, with this field being all zeros during the hashing.
    """
    def __init__(self):
        self.magic: str = ""  # Should always be "IMET"
        self.header_size: int = 0  # Always 1536? I assumed this would mean something, but it's just the header length.
        self.imet_version: int = 0  # Always 3?
        self.sizes: List[int] = []  # Should only have 3 items
        self.flag1: int = 0  # Unknown
        self.channel_names: List[str] = []  # Should have 10 items
        self.md5_hash: bytes = b''

    class LocalizedTitles(_IntEnum):
        TITLE_JAPANESE = 0
        TITLE_ENGLISH = 1
        TITLE_GERMAN = 2
        TITLE_FRENCH = 3
        TITLE_SPANISH = 4
        TITLE_ITALIAN = 5
        TITLE_DUTCH = 6
        TITLE_CHINESE_SIMPLIFIED = 7
        TITLE_CHINESE_TRADITIONAL = 8
        TITLE_KOREAN = 9

    def load(self, imet_data: bytes) -> None:
        """
        Loads the raw data of an IMET header.

        Parameters
        ----------
        imet_data : bytes
            The data for the IMET header to load.
        """
        with io.BytesIO(imet_data) as data:
            data.seek(0x40)
            self.magic = str(data.read(4).decode())
            self.header_size = int.from_bytes(data.read(4))
            self.imet_version = int.from_bytes(data.read(4))
            self.sizes = []
            for _ in range(0, 3):
                self.sizes.append(int.from_bytes(data.read(4)))
            self.flag1 = int.from_bytes(data.read(4))
            self.channel_names = []
            for _ in range(0, 10):
                # Read the translated channel name from the header, then drop all trailing null bytes. The encoding
                # used here is UTF-16 Big Endian.
                new_channel_name = data.read(84)
                self.channel_names.append(str(new_channel_name.decode('utf-16-be')).replace('\x00', ''))
            data.seek(data.tell() + 588)
            self.md5_hash = binascii.hexlify(data.read(16))

    def dump(self) -> bytes:
        """
        Dump the IMETHeader back into raw bytes.

        Returns
        -------
        bytes
            The IMET header as bytes.
        """
        imet_data = b''
        # 64 bytes of padding.
        imet_data += b'\x00' * 64
        # "IMET" magic number.
        imet_data += str.encode("IMET")
        # IMET header size. TODO: check if this is actually always 1536
        imet_data += int.to_bytes(1536, 4)
        # IMET header version.
        imet_data += int.to_bytes(self.imet_version, 4)
        # Banner component sizes.
        for size in self.sizes:
            imet_data += int.to_bytes(size, 4)
        # flag1.
        imet_data += int.to_bytes(self.flag1, 4)
        # Channel names.
        for channel_name in self.channel_names:
            new_channel_name = channel_name.encode('utf-16-be')
            while len(new_channel_name) < 84:
                new_channel_name += b'\x00'
            imet_data += new_channel_name
        # 588 (WHY??) bytes of padding.
        imet_data += b'\x00' * 588
        # MD5 hash. To calculate the real one, we need to write all zeros to it first, then hash the entire header with
        # the zero hash. After that we'll replace this hash with the calculated one.
        imet_data += b'\x00' * 16
        imet_hash = hashlib.md5(imet_data)
        imet_data = imet_data[:-16] + imet_hash.digest()
        return imet_data

    def create(self, sizes: List[int], channel_names: Tuple[int, str] | List[Tuple[int, str]]) -> None:
        """
        Create a new IMET header, specifying the sizes of the banner components and one or more localized channel names.

        Parameters
        ----------
        sizes : List[int]
            The size in bytes of icon.bin, banner.bin, and sound.bin, in that order.
        channel_names : Tuple(int, str), List[Tuple[int, str]]
            A pair or list of pairs of the target language and channel name for that language. Target languages are
            defined in LocalizedTitles.

        See Also
        --------
        libWiiPy.archive.u8.IMETHeader.LocalizedTitles
        """
        # Begin by setting the constant values before we parse the input.
        self.magic = "IMET"
        self.header_size = 1536
        self.imet_version = 3
        self.flag1 = 0  # Still not really sure about this one.
        # Validate the number of entries, then set the provided file sizes.
        if len(sizes) != 3:
            raise ValueError("You must supply 3 file sizes to generate an IMET header!")
        self.sizes = sizes
        # Now we can parse the channel names. This functions the same as setting them later, so just calling
        # set_channel_names() is the most practical.
        self.channel_names = ["" for _ in range(0, 10)]
        self.set_channel_names(channel_names)

    def get_channel_names(self, target_languages: int | List[int]) -> str | List[str]:
        """
        Get one or more channel names from the IMET header based on the specified languages.

        Parameters
        ----------
        target_languages : int, List[int, str]
            One or more target languages. Target languages are defined in LocalizedTitles.

        Returns
        -------
        str, List[str]
            The channel name for the specified language, or a list of channel names in the same order as the specified
            languages.

        See Also
        --------
        libWiiPy.archive.u8.IMETHeader.LocalizedTitles
        """
        # Flatten single instance of LocalizedTitles being passed to a proper int.
        if isinstance(target_languages, self.LocalizedTitles):
            target_languages = int(target_languages)
        # If only one channel name was requested.
        if type(target_languages) == int:
            if target_languages not in self.LocalizedTitles:
                raise ValueError(f"The specified language is not valid!")
            return self.channel_names[target_languages]
        # If multiple channel names were requested.
        else:
            channel_names = []
            for lang in target_languages:
                if lang not in self.LocalizedTitles:
                    raise ValueError(f"The specified language at index {target_languages.index(lang)} is not valid!")
                channel_names.append(self.channel_names[lang])
            return channel_names

    def set_channel_names(self, channel_names: Tuple[int, str] | List[Tuple[int, str]]) -> None:
        """
        Specify one or more new channel names to set in the IMET header.

        Parameters
        ----------
        channel_names : Tuple(int, str), List[Tuple[int, str]]
            A pair or list of pairs of the target language and channel name for that language. Target languages are
            defined in LocalizedTitles.

        See Also
        --------
        libWiiPy.archive.u8.IMETHeader.LocalizedTitles
        """
        # If only one channel name was provided.
        if type(channel_names) == tuple:
            if channel_names[0] not in self.LocalizedTitles:
                raise ValueError(f"The target language \"{channel_names[0]}\" is not valid!")
            if len(channel_names[1]) > 42:
                raise ValueError(f"The channel name \"{channel_names[1]}\" is too long! Channel names cannot exceed "
                                 f"42 characters!")
            self.channel_names[channel_names[0]] = channel_names[1]
        # If a list of channel names was provided.
        else:
            for name in channel_names:
                if name[0] not in self.LocalizedTitles:
                    raise ValueError(f"The target language \"{name[0]}\" for the name at index {channel_names.index(name)} "
                                     f"is not valid!")
                if len(name[1]) > 42:
                    raise ValueError(f"The channel name \"{name[1]}\" at index {channel_names.index(name)} is too long! "
                                     f"Channel names cannot exceed 42 characters!")
                self.channel_names[name[0]] = name[1]
