# "title/commonkeys.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy

import binascii

common_key = 'ebe42a225e8593e448d9c5457381aaf7'
korean_key = '63b82bb4f4614e2e13f2fefbba4c9b7e'
vwii_key = '30bfc76e7c19afbb23163330ced7c28d'


def get_common_key(common_key_index) -> bytes:
    """
    Gets the specified Wii Common Key based on the index provided. If an invalid common key index is provided, this
    function falls back on always returning key 0 (the Common Key).

    Possible values for common_key_index: 0: Common Key, 1: Korean Key, 2: vWii Key

    Parameters
    ----------
    common_key_index : int
        The index of the common key to be returned.

    Returns
    -------
    bytes
        The specified common key, in binary format.
    """
    match common_key_index:
        case 0:
            common_key_bin = binascii.unhexlify(common_key)
        case 1:
            common_key_bin = binascii.unhexlify(korean_key)
        case 2:
            common_key_bin = binascii.unhexlify(vwii_key)
        case _:
            common_key_bin = binascii.unhexlify(common_key)
    return common_key_bin
