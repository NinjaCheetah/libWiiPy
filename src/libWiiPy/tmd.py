# "tmd.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Title_metadata for details about the TMD format

import io
import binascii
import struct
from typing import List
from .types import ContentRecord


class TMD:
    """
    Creates a TMD object to parse a TMD file to retrieve information about a title.

    Parameters
    ----------
    tmd : bytes
        A bytes object containing the contents of a TMD file.

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
    def __init__(self, tmd):
        self.tmd = tmd
        self.sig_type: int
        self.sig: bytearray
        self.issuer: bytearray  # Follows the format "Root-CA%08x-CP%08x"
        self.tmd_version: int  # This seems to always be 0 no matter what?
        self.ca_crl_version: int
        self.signer_crl_version: int
        self.vwii: int  # Whether the title is for the vWii. 0 = No, 1 = Yes
        self.ios_tid: str  # The Title ID of the IOS version the associated title runs on.
        self.ios_version: int  # The IOS version the associated title runs on.
        self.title_id: str  # The Title ID of the associated title.
        self.content_type: str  # The type of content contained within the associated title.
        self.group_id: int  # The ID of the publisher of the associated title.
        self.region: int  # The ID of the region of the associated title.
        self.ratings: int
        self.access_rights: int
        self.title_version: int  # The version of the associated title.
        self.num_contents: int  # The number of contents contained in the associated title.
        self.boot_index: int
        self.content_records: List[ContentRecord] = []
        # Load data from TMD file
        with io.BytesIO(self.tmd) as tmd_data:
            # ====================================================================================
            # Parses each of the keys contained in the TMD.
            # ====================================================================================
            # Signing certificate issuer
            tmd_data.seek(0x140)
            self.issuer = tmd_data.read(64)
            # TMD version, seems to usually be 0, but I've seen references to other numbers
            tmd_data.seek(0x180)
            self.tmd_version = int.from_bytes(tmd_data.read(1))
            # TODO: label
            tmd_data.seek(0x181)
            self.ca_crl_version = tmd_data.read(1)
            # TODO: label
            tmd_data.seek(0x182)
            self.signer_crl_version = tmd_data.read(1)
            # If this is a vWii title or not
            tmd_data.seek(0x183)
            self.vwii = int.from_bytes(tmd_data.read(1))
            # TID of the IOS to use for the title, set to 0 if this title is the IOS, set to boot2 version if boot2
            tmd_data.seek(0x184)
            ios_version_bin = tmd_data.read(8)
            ios_version_hex = binascii.hexlify(ios_version_bin)
            self.ios_tid = str(ios_version_hex.decode())
            # Get IOS version based on TID
            self.ios_version = int(self.ios_tid[-2:], 16)
            # Title ID of the title
            tmd_data.seek(0x18C)
            title_id_bin = tmd_data.read(8)
            title_id_hex = binascii.hexlify(title_id_bin)
            self.title_id = str(title_id_hex.decode())
            # Type of content
            tmd_data.seek(0x194)
            content_type_bin = tmd_data.read(4)
            content_type_hex = binascii.hexlify(content_type_bin)
            self.content_type = str(content_type_hex.decode())
            # Publisher of the title
            tmd_data.seek(0x198)
            self.group_id = tmd_data.read(2)
            # Region of the title, 0 = JAP, 1 = USA, 2 = EUR, 3 = NONE, 4 = KOR
            tmd_data.seek(0x19C)
            region_hex = tmd_data.read(2)
            self.region = int.from_bytes(region_hex)
            # TODO: figure this one out
            tmd_data.seek(0x19E)
            self.ratings = tmd_data.read(16)
            # Access rights of the title; DVD-video access and AHBPROT
            tmd_data.seek(0x1D8)
            self.access_rights = tmd_data.read(4)
            # Calculate the version number by multiplying 0x1DC by 256 and adding 0x1DD
            tmd_data.seek(0x1DC)
            title_version_high = int.from_bytes(tmd_data.read(1)) * 256
            tmd_data.seek(0x1DD)
            title_version_low = int.from_bytes(tmd_data.read(1))
            self.title_version = title_version_high + title_version_low
            # The number of contents listed in the TMD
            tmd_data.seek(0x1DE)
            self.num_contents = int.from_bytes(tmd_data.read(2))
            # Content index in content list that contains the boot file
            tmd_data.seek(0x1E0)
            self.boot_index = tmd_data.read(2)
            # Get content records for the number of contents in num_contents.
            for content in range(0, self.num_contents):
                tmd_data.seek(0x1E4 + (36 * content))
                content_record_hdr = struct.unpack(">LHH4x4s20s", tmd_data.read(36))
                self.content_records.append(
                    ContentRecord(int(content_record_hdr[0]), int(content_record_hdr[1]),
                                  int(content_record_hdr[2]), int.from_bytes(content_record_hdr[3]),
                                  binascii.hexlify(content_record_hdr[4])))

    def get_title_region(self):
        """Gets the region of the TMD's associated title.

        Can be one of several possible values:
        'JAP', 'USA', 'EUR', 'NONE', or 'KOR'.

        Returns
        -------
        str
            The region of the title.
        """
        match self.region:
            case 0:
                return "JAP"
            case 1:
                return "USA"
            case 2:
                return "EUR"
            case 3:
                return "NONE"
            case 4:
                return "KOR"

    def get_is_vwii_title(self):
        """Gets whether the TMD is designed for the vWii or not.

        Returns
        -------
        bool
            If the title is for vWii.
        """
        if self.vwii == 1:
            return True
        else:
            return False

    def get_title_type(self):
        """Gets the type of the TMD's associated title.

        Can be one of several possible values:
        'System', 'Game', 'Channel', 'SystemChannel', 'GameWithChannel', or 'HiddenChannel'

        Returns
        -------
        str
            The type of the title.
        """
        title_id_high = self.title_id[:8]
        match title_id_high:
            case '00000001':
                return "System"
            case '00010000':
                return "Game"
            case '00010001':
                return "Channel"
            case '00010002':
                return "SystemChannel"
            case '00010004':
                return "GameWithChannel"
            case '00010005':
                return "DLC"
            case '00010008':
                return "HiddenChannel"
            case _:
                return "Unknown"

    def get_content_type(self):
        """Gets the type of content contained in the TMD's associated title.

        Can be one of several possible values:
        'Normal', 'Development/Unknown', 'Hash Tree', 'DLC', or 'Shared'

        Returns
        -------
        str
            The type of content.
        """
        match self.content_type:
            case '00000001':
                return "Normal"
            case '00000002':
                return "Development/Unknown"
            case '00000003':
                return "Hash Tree"
            case '00004001':
                return "DLC"
            case '00008001':
                return "Shared"
            case _:
                return "Unknown"

    def get_content_record(self, record):
        """Gets the content record at the specified index.

        Parameters
        ----------
        record : int
            The content record to be retrieved.

        Returns
        -------
        ContentRecord
            A ContentRecord object containing the data in the content record.
        """
        if record < self.num_contents:
            return self.content_records[record]
        else:
            raise IndexError("Invalid content record! TMD lists '" + str(self.num_contents - 1) +
                             "' contents but index was '" + str(record) + "'!")

    def set_title_id(self, title_id):
        """Sets the Title ID of the title in the ticket.

        Parameters
        ----------
        title_id : str
            The new Title ID of the title.
        """
        if len(title_id) != 16:
            raise ValueError("Invalid Title ID! Title IDs must be 8 bytes long.")
        self.title_id = title_id
