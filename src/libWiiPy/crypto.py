# "crypto.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy

import struct
from .commonkeys import get_common_key
from Crypto.Cipher import AES


def decrypt_title_key(title_key_enc, common_key_index, title_id) -> bytes:
    """Gets the decrypted version of the encrypted Title Key provided.

    Requires the index of the common key to use, and the Title ID of the title that the Title Key is for.

    Parameters
    ----------
    title_key_enc : bytes
        The encrypted Title Key.
    common_key_index : int
        The index of the common key to be returned.
    title_id : bytes
        The title ID of the title that the key is for.

    Returns
    -------
    bytes
        The decrypted Title Key.
    """
    # Load the correct common key for the title.
    common_key = get_common_key(common_key_index)
    # Calculate the IV by adding 8 bytes to the end of the Title ID.
    title_key_iv = title_id + (b'\x00' * 8)
    # Create a new AES object with the values provided.
    aes = AES.new(common_key, AES.MODE_CBC, title_key_iv)
    # Decrypt the Title Key using the AES object.
    title_key = aes.decrypt(title_key_enc)
    return title_key


def decrypt_content(content_enc, title_key, content_index, content_length) -> bytes:
    """Gets the decrypted version of the encrypted content.

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
    # Align content to 64 bytes to ensure that all the data is being decrypted, and so it works with AES encryption.
    if (len(content_enc) % 64) != 0:
        content_enc = content_enc + (b'\x00' * (64 - (len(content_enc) % 64)))
    # Create a new AES object with the values provided, with the content's unique ID as the IV.
    aes = AES.new(title_key, AES.MODE_CBC, content_index_bin)
    # Decrypt the content using the AES object.
    content_dec = aes.decrypt(content_enc)
    # Trim additional bytes that may have been added so the content is the correct size.
    while len(content_dec) > content_length:
        content_dec = content_dec[:-1]
    return content_dec


def encrypt_content(content_dec, title_key, content_index) -> bytes:
    """Gets the encrypted version of the decrypted content.

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
        The decrypted content.
    """
    # Generate the IV from the Content Index of the content to be decrypted.
    content_index_bin = struct.pack('>H', content_index)
    while len(content_index_bin) < 16:
        content_index_bin += b'\x00'
    # Align content to 64 bytes to ensure that all the data is being encrypted, and so it works with AES encryption.
    bytes_added = None
    if (len(content_dec) % 64) != 0:
        bytes_added = len(b'\x00' * (64 - (len(content_dec) % 64)))
        print(bytes_added)
        content_dec = content_dec + (b'\x00' * (64 - (len(content_dec) % 64)))
    # Create a new AES object with the values provided, with the content's unique ID as the IV.
    aes = AES.new(title_key, AES.MODE_CBC, content_index_bin)
    # Encrypt the content using the AES object.
    content_enc = aes.encrypt(content_dec)
    # Remove any bytes added.
    if bytes_added:
        while bytes_added:
            content_enc = content_enc[:-1]
            bytes_added -= 1
            print("removing " + str(bytes_added))
    print(str(len(content_enc)))
    return content_enc
