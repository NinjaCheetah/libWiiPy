# "title/util.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# General title-related utilities that don't fit within a specific module.

import math


def title_ver_dec_to_standard(version: int, title_id: str) -> str:
    """
    Converts a title's version from decimal form (vXXX, the way the version is stored in the TMD/Ticket) to its standard
    and human-readable form (vX.X). The Title ID is required as some titles handle this version differently from others.
    For the System Menu, the returned version will include the region code (ex. 4.3U).

    Parameters
    ----------
    version : int
        The version of the title, in decimal form.
    title_id : str
        The Title ID that the version is associated with.

    Returns
    -------
    str
        The version of the title, in standard form.
    """
    version_out = ""
    if title_id == "0000000100000002":
        raise ValueError("The System Menu's version cannot currently be converted.")
    else:
        # For most channels, we need to get the floored value of version / 256 for the major version, and the version %
        # 256 as the minor version. Minor versions > 9 are intended, as Nintendo themselves frequently used them.
        version_upper = math.floor(version / 256)
        version_lower = version % 256
        version_out = f"{version_upper}.{version_lower}"

    return version_out


def title_ver_standard_to_dec(version: str, title_id: str) -> int:
    """
    Converts a title's version from its standard and human-readable form (vX.X) to its decimal form (vXXX, the way the
    version is stored in the TMD/Ticket). The Title ID is required as some titles handle this version differently from
    others. For the System Menu, the supplied version must include the region code (ex. 4.3U) for the conversion to
    work correctly.

    Parameters
    ----------
    version : str
        The version of the title, in standard form.
    title_id : str
        The Title ID that the version is associated with.

    Returns
    -------
    int
        The version of the title, in decimal form.
    """
    version_out = 0
    if title_id == "0000000100000002":
        raise ValueError("The System Menu's version cannot currently be converted.")
    else:
        version_str_split = version.split(".")
        version_upper = int(version_str_split[0]) * 256
        version_lower = int(version_str_split[1])
        version_out = version_upper + version_lower

    return version_out
