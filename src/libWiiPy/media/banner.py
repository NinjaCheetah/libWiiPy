# "title/banner.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Opening.bnr for details about the Wii's banner format

import binascii
from dataclasses import dataclass as _dataclass
from enum import IntEnum as _IntEnum
import hashlib
import io
from typing import List, Tuple


@_dataclass
class IMD5Header:
    """
    An IMD5Header object that contains the properties of an IMD5 header. These headers precede the data of banner.bin
    and icon.bin inside the banner (00000000.app) of a channel, and are used to verify the data of those files.

    An IMD5 header is always 32 bytes long.

    Attributes
    ----------
    magic : str
        Magic number for the header, should be "IMD5".
    file_size : int
        The size of the file this header precedes.
    zeros : int
        8 bytes of zero padding.
    md5_hash : bytes
        The MD5 hash of the file this header precedes.
    """
    magic: str  # Should always be "IMD5"
    file_size: int
    zeros: int
    md5_hash: bytes


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
        libWiiPy.title.banner.IMETHeader.LocalizedTitles
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
        libWiiPy.title.banner.IMETHeader.LocalizedTitles
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
        libWiiPy.title.banner.IMETHeader.LocalizedTitles
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
