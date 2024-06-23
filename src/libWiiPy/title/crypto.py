# "title/crypto.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy

import struct
import binascii
from .commonkeys import get_common_key
from Crypto.Cipher import AES as _AES


def _convert_tid_to_iv(title_id: str) -> bytes:
    # Converts a Title ID in various formats into the format required to act as an IV. Private function used by other
    # crypto functions.
    title_key_iv = b''
    if type(title_id) is bytes:
        # This catches the format b'0000000100000002'
        if len(title_id) == 16:
            title_key_iv = binascii.unhexlify(title_id)
        # This catches the format b'\x00\x00\x00\x01\x00\x00\x00\x02'
        elif len(title_id) == 8:
            pass
        # If it isn't one of those lengths, it cannot possibly be valid, so reject it.
        else:
            raise ValueError("Title ID is not valid!")
    # Allow for a string like "0000000100000002"
    elif type(title_id) is str:
        title_key_iv = binascii.unhexlify(title_id)
    # If the Title ID isn't bytes or a string, it isn't valid and is rejected.
    else:
        raise TypeError("Title ID type is not valid! It must be either type str or bytes.")
    return title_key_iv


def decrypt_title_key(title_key_enc: bytes, common_key_index: int, title_id: bytes | str) -> bytes:
    """
    Gets the decrypted version of the encrypted Title Key provided.

    Requires the index of the common key to use, and the Title ID of the title that the Title Key is for.

    Parameters
    ----------
    title_key_enc : bytes
        The encrypted Title Key.
    common_key_index : int
        The index of the common key used to encrypt the Title Key.
    title_id : bytes, str
        The Title ID of the title that the key is for.

    Returns
    -------
    bytes
        The decrypted Title Key.
    """
    # Load the correct common key for the title.
    common_key = get_common_key(common_key_index)
    # Convert the IV into the correct format based on the type provided.
    title_key_iv = _convert_tid_to_iv(title_id)
    # The IV will always be in the same format by this point, so add the last 8 bytes.
    title_key_iv = title_key_iv + (b'\x00' * 8)
    # Create a new AES object with the values provided.
    aes = _AES.new(common_key, _AES.MODE_CBC, title_key_iv)
    # Decrypt the Title Key using the AES object.
    title_key = aes.decrypt(title_key_enc)
    return title_key


def encrypt_title_key(title_key_dec: bytes, common_key_index: int, title_id: bytes | str) -> bytes:
    """
    Encrypts the provided Title Key with the selected common key.

    Requires the index of the common key to use, and the Title ID of the title that the Title Key is for.

    Parameters
    ----------
    title_key_dec : bytes
        The decrypted Title Key.
    common_key_index : int
        The index of the common key used to encrypt the Title Key.
    title_id : bytes, str
        The Title ID of the title that the key is for.

    Returns
    -------
    bytes
        An encrypted Title Key.
    """
    # Load the correct common key for the title.
    common_key = get_common_key(common_key_index)
    # Convert the IV into the correct format based on the type provided.
    title_key_iv = _convert_tid_to_iv(title_id)
    # The IV will always be in the same format by this point, so add the last 8 bytes.
    title_key_iv = title_key_iv + (b'\x00' * 8)
    # Create a new AES object with the values provided.
    aes = _AES.new(common_key, _AES.MODE_CBC, title_key_iv)
    # Encrypt Title Key using the AES object.
    title_key = aes.encrypt(title_key_dec)
    return title_key


def decrypt_content(content_enc, title_key, content_index, content_length) -> bytes:
    """
    Gets the decrypted version of the encrypted content.

    This requires the index of the content to decrypt as it is used as the IV, as well as the content length to adjust
    padding as necessary.

    Parameters
    ----------
    content_enc : bytes
        The encrypted content.
    title_key : bytes
        The Title Key for the title the content is from.
    content_index : int
        The index in the TMD's content record of the content being decrypted.
    content_length : int
        The length in the TMD's content record of the content being decrypted.

    Returns
    -------
    bytes
        The decrypted content.
    """
    # Generate the IV from the Content Index of the content to be decrypted.
    content_index_bin = struct.pack('>H', content_index)
    while len(content_index_bin) < 16:
        content_index_bin += b'\x00'
    # Align content to 16 bytes to ensure that it works with AES encryption.
    if (len(content_enc) % 16) != 0:
        content_enc = content_enc + (b'\x00' * (16 - (len(content_enc) % 16)))
    # Create a new AES object with the values provided, with the content's unique ID as the IV.
    aes = _AES.new(title_key, _AES.MODE_CBC, content_index_bin)
    # Decrypt the content using the AES object.
    content_dec = aes.decrypt(content_enc)
    # Trim additional bytes that may have been added so the content is the correct size.
    content_dec = content_dec[:content_length]
    return content_dec


def encrypt_content(content_dec, title_key, content_index) -> bytes:
    """
    Gets the encrypted version of the decrypted content.

    This requires the index of the content to encrypt as it is used as the IV, as well as the content length to adjust
    padding as necessary.

    Parameters
    ----------
    content_dec : bytes
        The decrypted content.
    title_key : bytes
        The Title Key for the title the content is from.
    content_index : int
        The index in the TMD's content record of the content being decrypted.

    Returns
    -------
    bytes
        The encrypted content.
    """
    # Generate the IV from the Content Index of the content to be decrypted.
    content_index_bin = struct.pack('>H', content_index)
    while len(content_index_bin) < 16:
        content_index_bin += b'\x00'
    # Calculate the intended size of the encrypted content.
    enc_size = len(content_dec) + (16 - (len(content_dec) % 16))
    # Align content to 16 bytes to ensure that it works with AES encryption.
    if (len(content_dec) % 16) != 0:
        content_dec = content_dec + (b'\x00' * (16 - (len(content_dec) % 16)))
    # Create a new AES object with the values provided, with the content's unique ID as the IV.
    aes = _AES.new(title_key, _AES.MODE_CBC, content_index_bin)
    # Encrypt the content using the AES object.
    content_enc = aes.encrypt(content_dec)
    # Trim down the encrypted content.
    content_enc = content_enc[:enc_size]
    return content_enc
