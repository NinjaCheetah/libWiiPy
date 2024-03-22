# "types.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy

from dataclasses import dataclass


@dataclass
class ContentRecord:
    """
    Creates a content record object that contains the details of a content contained in a title.

    Attributes
    ----------
    content_id : int
        ID of the content.
    index : int
        Index of the content in the list of contents.
    content_type : int
        The type of the content.
    content_size : int
        The size of the content.
    content_hash
        The SHA-1 hash of the decrypted content.
    """
    content_id: int  # The unique ID of the content.
    index: int  # The index of this content in the content record.
    content_type: int  # Type of content, possible values of: 0x0001: Normal, 0x4001: DLC, 0x8001: Shared.
    content_size: int  # Size of the content when decrypted.
    content_hash: bytes  # SHA-1 hash of the content when decrypted.


@dataclass
class TitleLimit:
    """Creates a TitleLimit object that contains the type of restriction and the limit.

    Attributes
    ----------
    limit_type : int
        The type of play limit applied.
    maximum_usage : int
        The maximum value for the type of play limit applied.
    """
    # The type of play limit applied. The following types exist:
    # 0 = None, 1 = Time Limit, 3 = None, 4 = Launch Count
    limit_type: int
    # The maximum value of the limit applied.
    # This is either the number of minutes for a time limit, or the number of launches for a launch limit.
    maximum_usage: int
