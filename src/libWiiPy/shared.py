# "shared.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# This file defines general functions that may be useful in other modules of libWiiPy. Putting them here cuts down on
# clutter in other files.


def _align_value(value, alignment=64) -> int:
    """
    Aligns the provided value to the set alignment (defaults to 64). Private function used by other libWiiPy modules.

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


def _pad_bytes(data, alignment=64) -> bytes:
    """
    Pads the provided bytes object to the provided alignment (defaults to 64). Private function used by other libWiiPy
    modules.

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
