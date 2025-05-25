# "title/banner.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Opening.bnr for details about the Wii's banner format

from dataclasses import dataclass as _dataclass


@_dataclass
class IMD5Header:
    """
    An IMD5Header object that contains the properties of an IMD5 header. These headers precede the data of banner.bin
    and icon.bin inside the banner (00000000.app) of a channel, and are used to verify the data of those files.

    An IMD5 header is always 32 bytes long.

    :ivar magic: Magic number for the header, should be "IMD5".
    :ivar file_size: The size of the file this header precedes.
    :ivar zeros: 8 bytes of zero padding.
    :ivar md5_hash: The MD5 hash of the file this header precedes.
    """
    magic: str  # Should always be "IMD5"
    file_size: int
    zeros: int
    md5_hash: bytes
