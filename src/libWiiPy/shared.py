# "shared.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# This file defines general functions that may be useful in other modules of libWiiPy. Putting them here cuts down on
# clutter in other files.

import binascii


def align_value(value, alignment=64) -> int:
    """
    Aligns the provided value to the set alignment (defaults to 64).

    Parameters
    ----------
    value : int
        The value to align.
    alignment : int
        The number to align to. Defaults to 64.

    Returns
    -------
    int
        The aligned value.
    """
    if (value % alignment) != 0:
        aligned_value = value + (alignment - (value % alignment))
        return aligned_value
    return value


def pad_bytes(data, alignment=64) -> bytes:
    """
    Pads the provided bytes object to the provided alignment (defaults to 64).

    Parameters
    ----------
    data : bytes
        The data to align.
    alignment : int
        The number to align to. Defaults to 64.

    Returns
    -------
    bytes
        The aligned data.
    """
    while (len(data) % alignment) != 0:
        data += b'\x00'
    return data


def convert_tid_to_iv(title_id: str) -> bytes:
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
