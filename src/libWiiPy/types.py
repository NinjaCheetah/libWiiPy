# "types.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
from dataclasses import dataclass


@dataclass
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


@dataclass
class TitleLimit:
    """
    A TitleLimit object that contains the type of restriction and the limit. The limit type can be one of the following:
    0 = None, 1 = Time Limit, 3 = None, or 4 = Launch Count. The maximum usage is then either the time in minutes the
    title can be played or the maximum number of launches allowed for that title, based on the type of limit applied.

    Attributes
    ----------
    limit_type : int
        The type of play limit applied.
    maximum_usage : int
        The maximum value for the type of play limit applied.
    """
    # The type of play limit applied.
    # 0 = None, 1 = Time Limit, 3 = None, 4 = Launch Count
    limit_type: int
    # The maximum value of the limit applied.
    maximum_usage: int
