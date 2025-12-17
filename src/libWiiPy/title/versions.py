# "title/versions.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# Functions for converting the format that a title's version is in.

from ..constants import _WII_MENU_VERSIONS, _VWII_MENU_VERSIONS


def title_ver_dec_to_standard(version: int, title_id: str, vwii: bool = False) -> str:
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
    vwii : bool
        Whether this title is for the vWii or not. Only relevant for the System Menu.

    Returns
    -------
    str
        The version of the title, in standard form.
    """
    if title_id == "0000000100000002":
        try:
            if vwii:
                return list(_VWII_MENU_VERSIONS.keys())[list(_VWII_MENU_VERSIONS.values()).index(version)]
            else:
                return list(_WII_MENU_VERSIONS.keys())[list(_WII_MENU_VERSIONS.values()).index(version)]
        except ValueError:
            raise ValueError(f"Unrecognized System Menu version \"{version}\".")
    else:
        # Typical titles use a two-byte version format where the upper byte is the major version, and the lower byte is
        # the minor version.
        return f"{version >> 8}.{version & 0xFF}"


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
    if title_id == "0000000100000002":
        for key in _WII_MENU_VERSIONS.keys():
            if version.casefold() == key.casefold():
                return _WII_MENU_VERSIONS[key]
        for key in _VWII_MENU_VERSIONS.keys():
            if version.casefold() == key.casefold():
                return _VWII_MENU_VERSIONS[key]
        raise ValueError(f"Unrecognized System Menu version \"{version}\".")
    else:
        version_str_split = version.split(".")
        version_out = (int(version_str_split[0]) << 8) + int(version_str_split[1])
        return version_out
