# "title/banner.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Opening.bnr for details about the Wii's banner format

from dataclasses import dataclass as _dataclass
from typing import List


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


@_dataclass
class IMETHeader:
    """
    An IMETHeader object that contains the properties of an IMET header. These headers precede the data of a channel
    banner (00000000.app), and are used to store metadata about the banner and verify its data.

    An IMET header is always 1,536 bytes long.

    Attributes
    ----------
    zeros : int
        64 bytes of zero padding.
    magic : str
        Magic number for the header, should be "IMD5".
    hash_size : int
        Length of the MD5 hash.
    imet_version : int
        Version of the IMET header. Normally always 3.
    sizes : List[int]
        The file sizes of icon.bin, banner.bin, and sound.bin.
    flag1 : int
        Unknown.
    channel_names : List[str]
        The name of the channel this header is for in Japanese, English, German, French, Spanish, Italian, Dutch,
        Simplified Chinese, Traditional Chinese, and Korean, in that order.
    zeros2 : int
        An additional 588 bytes of zero padding.
    md5_hash : bytes
        "MD5 of 0 to 'hashsize' in header. crypto should be all 0's when calculating final MD5" -WiiBrew
    """
    zeros: int
    magic: str  # Should always be "IMET"
    hash_size: int
    imet_version: int  # Always 3?
    sizes: List[int]  # Should only have 3 items
    flag1: int  # Unknown
    channel_names: List[str]  # Should have 10 items
    zeros2: int
    md5_hash: bytes
