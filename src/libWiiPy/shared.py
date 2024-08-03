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


_wii_menu_versions = {
    "Prelaunch": [0, 1, 2],
    "1.0J": 64,
    "1.0U": 33,
    "1.0E": 34,
    "2.0J": 128,
    "2.0U": 97,
    "2.0E": 130,
    "2.1E": 162,
    "2.2J": 192,
    "2.2U": 193,
    "2.2E": 194,
    "3.0J": 224,
    "3.0U": 225,
    "3.0E": 226,
    "3.1J": 256,
    "3.1U": 257,
    "3.1E": 258,
    "3.2J": 288,
    "3.2U": 289,
    "3.2E": 290,
    "3.3J": 352,
    "3.3U": 353,
    "3.3E": 354,
    "3.3K": 326,
    "3.4J": 384,
    "3.4U": 385,
    "3.4E": 386,
    "3.5K": 390,
    "4.0J": 416,
    "4.0U": 417,
    "4.0E": 418,
    "4.1J": 448,
    "4.1U": 449,
    "4.1E": 450,
    "4.1K": 454,
    "4.2J": 480,
    "4.2U": 481,
    "4.2E": 482,
    "4.2K": 486,
    "4.3J": 512,
    "4.3U": 513,
    "4.3E": 514,
    "4.3K": 518,
    "4.3U-Mini": 4609,
    "4.3E-Mini": 4610
}


_vwii_menu_versions = {
    "vWii-1.0.0J": 512,
    "vWii-1.0.0U": 513,
    "vWii-1.0.0E": 514,
    "vWii-4.0.0J": 544,
    "vWii-4.0.0U": 545,
    "vWii-4.0.0E": 546,
    "vWii-5.2.0J": 608,
    "vWii-5.2.0U": 609,
    "vWii-5.2.0E": 610,
}
