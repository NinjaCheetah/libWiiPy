# "types.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy

from dataclasses import dataclass


@dataclass
class ContentRecord:
    """
    Creates a content record object that contains the details of a content contained in a title.

    Attributes:
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
    content_id: int  # Unique ID for the current content
    index: int  # Index in the list of contents
    content_type: int  # Type of content, possible values of: 0x0001: Normal, 0x4001: DLC, 0x8001: Shared
    content_size: int  # Size of the current content
    content_hash: bytes  # SHA1 hash of the current content
