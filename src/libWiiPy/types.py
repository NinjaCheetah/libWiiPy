# "types.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy

from dataclasses import dataclass


@dataclass
class _ContentRecord:
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
