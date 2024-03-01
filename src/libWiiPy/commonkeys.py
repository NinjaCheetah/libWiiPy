# "commonkeys.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy

import binascii

common_key = 'ebe42a225e8593e448d9c5457381aaf7'
korean_key = '63b82bb4f4614e2e13f2fefbba4c9b7e'
vwii_key = '30bfc76e7c19afbb23163330ced7c28d'


def get_common_key(common_key_index):
    """
    Returns the specified Wii Common Key based on the index provided.
    Possible values for common_key_index: 0: Common Key, 1: Korean Key, 2: vWii Key
    """
    match common_key_index:
        case 0:
            common_key_bin = binascii.unhexlify(common_key)
        case 1:
            common_key_bin = binascii.unhexlify(korean_key)
        case 2:
            common_key_bin = binascii.unhexlify(vwii_key)
        case _:
            raise ValueError("The common key index provided, " + str(common_key_index + ", does not exist."))
    return common_key_bin
