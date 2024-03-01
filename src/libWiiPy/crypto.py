# "crypto.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Ticket for details about the TMD format

from .commonkeys import get_common_key
from Crypto.Cipher import AES


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
