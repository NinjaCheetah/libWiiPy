# "title/tmd.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Title_metadata for details about the TMD format

import io
import binascii
import hashlib
import struct
from typing import List
from enum import IntEnum as _IntEnum
from ..types import _ContentRecord
from ..shared import _bitmask
from .util import title_ver_dec_to_standard, title_ver_standard_to_dec


class TMD:
    """
    A TMD object that allows for either loading and editing an existing TMD or creating one manually if desired.

    Attributes
    ----------
    title_id : str
        The title ID of the title listed in the TMD.
    title_version : int
        The version of the title listed in the TMD.
    tmd_version : int
        The version of the TMD.
    ios_tid : str
        The title ID of the IOS the title runs on.
    ios_version : int
        The IOS version the title runs on.
    num_contents : int
        The number of contents listed in the TMD.
    """
    def __init__(self):
        self.blob_header: bytes = b''
        self.signature_type: int = 0
        self.signature: bytes = b''
        self.signature_issuer: str = ""  # Follows the format "Root-CA%08x-CP%08x"
        self.tmd_version: int = 0  # This seems to always be 0 no matter what?
        self.ca_crl_version: int = 0  # Certificate Authority Certificate Revocation List version
        self.signer_crl_version: int = 0  # Certificate Policy Certificate Revocation List version
        self.vwii: int = 0  # Whether the title is for the vWii. 0 = No, 1 = Yes
        self.ios_tid: str = ""  # The Title ID of the IOS version the associated title runs on.
        self.ios_version: int = 0  # The IOS version the associated title runs on.
        self.title_id: str = ""  # The Title ID of the associated title.
        self.title_type: bytes = b''  # The type of the associated title. Should always be 00000001 in a Wii TMD.
        self.group_id: int = 0  # The ID of the publisher of the associated title.
        self.region: int = 0  # The ID of the region of the associated title.
        self.ratings: bytes = b''  # The parental controls rating of the associated title.
        self.reserved1: bytes = b''  # Unknown data labeled "Reserved" on WiiBrew.
        self.ipc_mask: bytes = b''
        self.reserved2: bytes = b''  # Other "Reserved" data from WiiBrew.
        self.access_rights: int = 0
        self.title_version: int = 0  # The version of the associated title.
        self.title_version_converted: int = 0  # The title version in vX.X format.
        self.num_contents: int = 0  # The number of contents contained in the associated title.
        self.boot_index: int = 0  # The content index that contains the bootable executable.
        self.minor_version: int = 0  # Minor version (unused typically).
        self.content_records: List[_ContentRecord] = []

    def load(self, tmd: bytes) -> None:
        """
        Loads raw TMD data and sets all attributes of the TMD object. This allows for manipulating an already
        existing TMD.

        Parameters
        ----------
        tmd : bytes
            The data for the TMD you wish to load.
        """
        with io.BytesIO(tmd) as tmd_data:
            # ====================================================================================
            # Parses each of the keys contained in the TMD.
            # ====================================================================================
            # Signature type.
            tmd_data.seek(0x0)
            self.signature_type = tmd_data.read(4)
            # Signature data.
            tmd_data.seek(0x04)
            self.signature = tmd_data.read(256)
            # Signing certificate issuer.
            tmd_data.seek(0x140)
            self.signature_issuer = str(tmd_data.read(64).decode())
            # TMD version, seems to usually be 0, but I've seen references to other numbers.
            tmd_data.seek(0x180)
            self.tmd_version = int.from_bytes(tmd_data.read(1))
            # Certificate Authority CRL version.
            tmd_data.seek(0x181)
            self.ca_crl_version = int.from_bytes(tmd_data.read(1))
            # Certificate Policy CRL version.
            tmd_data.seek(0x182)
            self.signer_crl_version = int.from_bytes(tmd_data.read(1))
            # If this is a vWii title or not.
            tmd_data.seek(0x183)
            self.vwii = int.from_bytes(tmd_data.read(1))
            # TID of the IOS to use for the title, set to 0 if this title is the IOS, set to boot2 version if boot2.
            tmd_data.seek(0x184)
            ios_version_bin = tmd_data.read(8)
            ios_version_hex = binascii.hexlify(ios_version_bin)
            self.ios_tid = str(ios_version_hex.decode())
            # Get IOS version based on TID.
            self.ios_version = int(self.ios_tid[-2:], 16)
            # Title ID of the title.
            tmd_data.seek(0x18C)
            title_id_bin = tmd_data.read(8)
            title_id_hex = binascii.hexlify(title_id_bin)
            self.title_id = str(title_id_hex.decode())
            # Type of the title. This is an internal property used to show if this title is for the ill-fated
            # NetCard (0), or the Wii (1), and is therefore always 1 for Wii TMDs.
            tmd_data.seek(0x194)
            self.title_type = tmd_data.read(4)
            # Publisher of the title.
            tmd_data.seek(0x198)
            self.group_id = int.from_bytes(tmd_data.read(2))
            # Region of the title, 0 = JAP, 1 = USA, 2 = EUR, 3 = WORLD, 4 = KOR.
            tmd_data.seek(0x19C)
            region_hex = tmd_data.read(2)
            self.region = int.from_bytes(region_hex)
            # Content rating of the title for parental controls. Likely based on ESRB, CERO, PEGI, etc. rating.
            tmd_data.seek(0x19E)
            self.ratings = tmd_data.read(16)
            # "Reserved" data 1.
            tmd_data.seek(0x1AE)
            self.reserved1 = tmd_data.read(12)
            # IPC mask.
            tmd_data.seek(0x1BA)
            self.ipc_mask = tmd_data.read(12)
            # "Reserved" data 2.
            tmd_data.seek(0x1C6)
            self.reserved2 = tmd_data.read(18)
            # Access rights of the title; DVD-video and AHB access.
            tmd_data.seek(0x1D8)
            self.access_rights = int.from_bytes(tmd_data.read(4))
            # Version number straight from the TMD.
            tmd_data.seek(0x1DC)
            self.title_version = int.from_bytes(tmd_data.read(2))
            # Calculate the converted version number via util module.
            self.title_version_converted = title_ver_dec_to_standard(self.title_version, self.title_id, bool(self.vwii))
            # The number of contents listed in the TMD.
            tmd_data.seek(0x1DE)
            self.num_contents = int.from_bytes(tmd_data.read(2))
            # The content index that contains the bootable executable.
            tmd_data.seek(0x1E0)
            self.boot_index = int.from_bytes(tmd_data.read(2))
            # The minor version of the title (typically unused).
            tmd_data.seek(0x1E2)
            self.minor_version = int.from_bytes(tmd_data.read(2))
            # Get content records for the number of contents in num_contents.
            self.content_records = []
            for content in range(0, self.num_contents):
                tmd_data.seek(0x1E4 + (36 * content))
                content_record_hdr = struct.unpack(">LHH4x4s20s", tmd_data.read(36))
                self.content_records.append(
                    _ContentRecord(int(content_record_hdr[0]), int(content_record_hdr[1]),
                                   int(content_record_hdr[2]), int.from_bytes(content_record_hdr[3]),
                                   binascii.hexlify(content_record_hdr[4])))

    def dump(self) -> bytes:
        """
        Dumps the TMD object back into bytes.

        Returns
        -------
        bytes
            The full TMD file as bytes.
        """
        tmd_data = b''
        # Signature type.
        tmd_data += self.signature_type
        # Signature data.
        tmd_data += self.signature
        # Padding to 64 bytes.
        tmd_data += b'\x00' * 60
        # Signing certificate issuer.
        tmd_data += str.encode(self.signature_issuer)
        # TMD version.
        tmd_data += int.to_bytes(self.tmd_version, 1)
        # Certificate Authority CRL version.
        tmd_data += int.to_bytes(self.ca_crl_version, 1)
        # Certificate Policy CRL version.
        tmd_data += int.to_bytes(self.signer_crl_version, 1)
        # If this is a vWii title or not.
        tmd_data += int.to_bytes(self.vwii, 1)
        # IOS Title ID.
        tmd_data += binascii.unhexlify(self.ios_tid)
        # Title's Title ID.
        tmd_data += binascii.unhexlify(self.title_id)
        # Title type.
        tmd_data += self.title_type
        # Group ID.
        tmd_data += int.to_bytes(self.group_id, 2)
        # 2 bytes of zero for reasons.
        tmd_data += b'\x00\x00'
        # Region.
        tmd_data += int.to_bytes(self.region, 2)
        # Parental Controls Ratings.
        tmd_data += self.ratings
        # "Reserved" 1.
        tmd_data += self.reserved1
        # IPC mask.
        tmd_data += self.ipc_mask
        # "Reserved" 2.
        tmd_data += self.reserved2
        # Access rights.
        tmd_data += int.to_bytes(self.access_rights, 4)
        # Title version.
        tmd_data += int.to_bytes(self.title_version, 2)
        # Number of contents.
        tmd_data += int.to_bytes(self.num_contents, 2)
        # Boot index.
        tmd_data += int.to_bytes(self.boot_index, 2)
        # Minor version.
        tmd_data += int.to_bytes(self.minor_version, 2)
        # Iterate over content records, write them back into raw data, then add them to the TMD.
        for content_record in range(self.num_contents):
            content_data = b''
            # Write all fields from the content record.
            content_data += int.to_bytes(self.content_records[content_record].content_id, 4)
            content_data += int.to_bytes(self.content_records[content_record].index, 2)
            content_data += int.to_bytes(self.content_records[content_record].content_type, 2)
            content_data += int.to_bytes(self.content_records[content_record].content_size, 8)
            content_data += binascii.unhexlify(self.content_records[content_record].content_hash)
            # Write the record to the TMD.
            tmd_data += content_data
        return tmd_data

    def fakesign(self) -> None:
        """
        Fakesigns this TMD for the trucha bug.

        This is done by brute-forcing a TMD body hash starting with 00, causing it to pass signature verification on
        older IOS versions that incorrectly check the hash using strcmp() instead of memcmp(). The signature will also
        be erased and replaced with all NULL bytes.

        The hash is brute-forced by incrementing an unused 16-bit integer in the TMD by 1 until an appropriate hash is
        found.

        This modifies the TMD object in place. You will need to call this method after any changes, and before dumping
        the TMD object back into bytes.
        """
        # Clear the signature, so that the hash derived from it is guaranteed to always be
        # '0000000000000000000000000000000000000000'.
        self.signature = b'\x00' * 256
        current_int = 0
        test_hash = ''
        while test_hash[:2] != '00':
            current_int += 1
            self.minor_version = current_int
            # Trim off the first 320 bytes, because we're only looking for the hash of the TMD's body.
            # This is a try-except because an OverflowError will be thrown if the number being used to brute-force the
            # hash gets too big, as it is only a 16-bit integer. If that happens, then fakesigning has failed.
            try:
                test_hash = hashlib.sha1(self.dump()[320:]).hexdigest()
            except OverflowError:
                raise Exception("An error occurred during fakesigning. TMD could not be fakesigned!")

    def get_is_fakesigned(self) -> bool:
        """
        Checks the TMD object to see if it is currently fakesigned. For a description of fakesigning, refer to the
        fakesign() method.

        Returns
        -------
        bool:
            True if the TMD is fakesigned, False otherwise.

        See Also
        --------
        libWiiPy.title.tmd.TMD.fakesign()
        """
        if self.signature != b'\x00' * 256:
            return False
        test_hash = hashlib.sha1(self.dump()[320:]).hexdigest()
        if test_hash[:2] != '00':
            return False
        return True

    def get_title_region(self) -> str:
        """
        Gets the system region specified in the TMD. This is not necessarily the true region of the title, but is the
        hardware region that this title is designed and allowed to be run on.

        Can be one of several possible values:
        'JPN', 'USA', 'EUR', 'None', or 'KOR'.

        Returns
        -------
        str
            The region of the title.
        """
        match self.region:
            case 0:
                return "JPN"
            case 1:
                return "USA"
            case 2:
                return "EUR"
            case 3:
                return "None"
            case 4:
                return "KOR"

    def get_title_type(self) -> str:
        """
        Gets the type of the title this TMD describes. The title_type field is not related to these types.

        Can be one of several possible values:
        'System', 'Game', 'Channel', 'SystemChannel', 'GameChannel', or 'HiddenChannel'

        Returns
        -------
        str
            The type of the title.
        """
        match self.title_id[:8]:
            case '00000001':
                return "System"
            case '00010000':
                return "Game"
            case '00010001':
                return "Channel"
            case '00010002':
                return "SystemChannel"
            case '00010004':
                return "GameChannel"
            case '00010005':
                return "DLC"
            case '00010008':
                return "HiddenChannel"
            case _:
                return "Unknown"

    def get_content_type(self, content_index: int) -> str:
        """
        Gets the type of content contained in the TMD's associated title.

        Can be one of several possible values:
        'Normal', 'Development/Unknown', 'Hash Tree', 'DLC', or 'Shared'

        Parameters
        ----------
        content_index : int
            The index of the content you want the type of.

        Returns
        -------
        str
            The type of content.
        """
        # Get a list of the current content indices, so we can make sure the target one exists. Doing it this way
        # ensures we can find the target, even if the highest content index is greater than the highest literal index.
        current_indices = []
        for record in self.content_records:
            current_indices.append(record.index)
        # This is the literal index in the list of content that we're going to get.
        target_index = current_indices.index(content_index)
        match self.content_records[target_index].content_type:
            case 1:
                return "Normal"
            case 2:
                return "Development/Unknown"
            case 3:
                return "Hash Tree"
            case 16385:
                return "DLC"
            case 32769:
                return "Shared"
            case _:
                return "Unknown"

    def get_content_record(self, record) -> _ContentRecord:
        """
        Gets the content record at the specified index.

        Parameters
        ----------
        record : int
            The content record to be retrieved.

        Returns
        -------
        _ContentRecord
            A ContentRecord object containing the data in the content record.
        """
        if record < self.num_contents:
            return self.content_records[record]
        else:
            raise IndexError("Invalid content record! TMD lists '" + str(self.num_contents - 1) +
                             "' contents but index was '" + str(record) + "'!")

    class AccessFlags(_IntEnum):
        AHB = 0
        DVD_VIDEO = 1

    def get_access_right(self, flag: int) -> bool:
        """
        Gets whether an access rights flag is enabled or not. This is done by checking the specified bit. Possible flags
        and their corresponding bits are defined in the AccessFlags enum.

        Parameters
        ----------
        flag : int
            The flag to check.

        Returns
        -------
        bool
            True if the flag is enabled, False otherwise.
        """
        return bool(self.access_rights & _bitmask(flag))

    def set_title_id(self, title_id) -> None:
        """
        Sets the Title ID property of the TMD. Recommended over setting the property directly because of input
        validation.

        Parameters
        ----------
        title_id : str
            The new Title ID of the title.
        """
        if len(title_id) != 16:
            raise ValueError("Invalid Title ID! Title IDs must be 8 bytes long.")
        self.title_id = title_id

    def set_title_version(self, new_version: str | int) -> None:
        """
        Sets the version of the title in the TMD. Recommended over setting the data directly because of input
        validation.

        Accepts either standard form (vX.X) as a string or decimal form (vXXX) as an integer.

        Parameters
        ----------
        new_version : str, int
            The new version of the title. See description for valid formats.
        """
        if type(new_version) is str:
            # Validate string input is in the correct format, then validate that the version isn't higher than v255.0.
            # If checks pass, set that as the converted version, then convert to decimal form and set that as well.
            version_str_split = new_version.split(".")
            if len(version_str_split) != 2:
                raise ValueError("Title version is not valid! String version must be entered in format \"X.X\".")
            if int(version_str_split[0]) > 255 or int(version_str_split[1]) > 255:
                raise ValueError("Title version is not valid! String version number cannot exceed v255.255.")
            self.title_version_converted = new_version
            version_converted = title_ver_standard_to_dec(new_version, self.title_id)
            self.title_version = version_converted
        elif type(new_version) is int:
            # Validate that the version isn't higher than v65280. If the check passes, set that as the title version,
            # then convert to standard form and set that as well.
            if new_version > 65535:
                raise ValueError("Title version is not valid! Integer version number cannot exceed v65535.")
            self.title_version = new_version
            version_converted = title_ver_dec_to_standard(new_version, self.title_id, bool(self.vwii))
            self.title_version_converted = version_converted
        else:
            raise TypeError("Title version type is not valid! Type must be either integer or string.")
