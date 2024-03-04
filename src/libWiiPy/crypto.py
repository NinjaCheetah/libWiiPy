# "crypto.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Ticket for details about the TMD format

import struct
from .commonkeys import get_common_key
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def decrypt_title_key(title_key_enc, common_key_index, title_id):
    """Gets the decrypted version of the encrypted Title Key provided.

    Requires the index of the common key to use, and the Title ID of the title that the Title Key is for.

    Parameters
    ----------
    title_key_enc : bytes
        The encrypted Title Key.
    common_key_index : int
        The index of the common key to be returned.
    title_id : bytes
        The title ID of the tite that the key is for.

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


def decrypt_content(content_enc, title_key, content_index, content_length):
    """Gets the decrypted version of the encrypted content.

    Requires the index of the common key to use, and the Title ID of the title that the Title Key is for.

    Parameters
    ----------
    content_enc : bytes
        The encrypted content.
    title_key : bytes
        The Title Key for the title the content is from.

    Returns
    -------
    bytes
        The decrypted content.
    """
    # Generate the IV from the Content Index of the content to be decrypted.
    content_index_bin = struct.pack('>H', content_index)
    while len(content_index_bin) < 16:
        content_index_bin += b'\x00'
    # In CBC mode, content must be padded out to a 16-byte boundary, so do that here, and then remove bytes added after.
    padded = False
    if (len(content_enc) % 128) != 0:
        print("needs padding to 16 bytes")
        content_enc = pad(content_enc, 128, "pkcs7")
        padded = True
    # Create a new AES object with the values provided, with the content's unique ID as the IV.
    aes = AES.new(title_key, AES.MODE_CBC, content_index_bin)
    # Decrypt the content using the AES object.
    content_dec = aes.decrypt(content_enc)
    # Remove padding bytes, if any were added.
    if padded:
        while len(content_dec) > content_length:
            content_dec = content_dec[:-1]
    return content_dec
