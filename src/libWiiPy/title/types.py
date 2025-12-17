# "title/types.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# Shared types used across the title module.

from dataclasses import dataclass as _dataclass
from enum import IntEnum as _IntEnum, StrEnum as _StrEnum


@_dataclass
class ContentRecord:
    """
    A content record object that contains the details of a content contained in a title. This information must match
    the content stored at the index in the record, or else the content will not decrypt properly, as the hash of the
    decrypted data will not match the hash in the content record.

    Attributes
    ----------
    content_id : int
        The unique ID of the content.
    index : int
        The index of this content in the content records.
    content_type : int
        The type of the content.
    content_size : int
        The size of the content when decrypted.
    content_hash
        The SHA-1 hash of the decrypted content.
    """
    content_id: int
    index: int
    content_type: int  # Type of content, possible values of: 0x0001: Normal, 0x4001: DLC, 0x8001: Shared.
    content_size: int
    content_hash: bytes


class ContentType(_IntEnum):
    """
    The type of an individual piece of content.
    """
    NORMAL = 0x0001
    DEVELOPMENT = 0x0002
    HASH_TREE = 0x0003
    DLC = 0x4001
    SHARED = 0x8001


class TitleType(_StrEnum):
    """
    The type of a title.
    """
    SYSTEM = "00000001"
    GAME = "00010000"
    CHANNEL = "00010001"
    SYSTEM_CHANNEL = "00010002"
    GAME_CHANNEL = "00010004"
    DLC = "00010005"
    HIDDEN_CHANNEL = "00010008"


class Region(_IntEnum):
    """
    The region of a title.
    """
    JPN = 0
    USA = 1
    EUR = 2
    WORLD = 3
    KOR = 4
