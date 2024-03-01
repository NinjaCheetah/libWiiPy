# "tmd.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Title_metadata for details about the TMD format

import io
import binascii
import struct
from dataclasses import dataclass
from typing import List


@dataclass
class ContentRecord:
    """Creates a content record object that contains the details of a content contained in a title."""
    cid: int  # Content ID
    index: int  # Index in the list of contents
    content_type: int  # Normal: 0x0001, DLC: 0x4001, Shared: 0x8001
    content_size: int
    content_hash: bytes  # SHA1 hash content


class TMD:
    """Creates a TMD object to parse a TMD file to retrieve information about a title."""
    def __init__(self, tmd):
        self.tmd = tmd
        self.sig_type: int
        self.sig: bytearray
        self.issuer: bytearray  # Follows the format "Root-CA%08x-CP%08x"
        self.version: int  # This seems to always be 0 no matter what?
        self.ca_crl_version: int
        self.signer_crl_version: int
        self.vwii: int
        self.ios_tid: str
        self.ios_version: int
        self.title_id: str
        self.content_type: str
        self.group_id: int  # Publisher of the title
        self.region: int
        self.ratings: int
        self.access_rights: int
        self.title_version: int
        self.num_contents: int
        self.boot_index: int
        self.content_records: List[ContentRecord] = []
        # Load data from TMD file
        with io.BytesIO(tmd) as tmddata:
            # Signing certificate issuer
            tmddata.seek(0x140)
            self.issuer = tmddata.read(64)
            # TMD version, seems to usually be 0, but I've seen references to other numbers
            tmddata.seek(0x180)
            self.version = int.from_bytes(tmddata.read(1))
            # TODO: label
            tmddata.seek(0x181)
            self.ca_crl_version = tmddata.read(1)
            # TODO: label
            tmddata.seek(0x182)
            self.signer_crl_version = tmddata.read(1)
            # If this is a vWii title or not
            tmddata.seek(0x183)
            self.vwii = int.from_bytes(tmddata.read(1))
            # TID of the IOS to use for the title, set to 0 if this title is the IOS, set to boot2 version if boot2
            tmddata.seek(0x184)
            ios_version_bin = tmddata.read(8)
            ios_version_hex = binascii.hexlify(ios_version_bin)
            self.ios_tid = str(ios_version_hex.decode())
            # Get IOS version based on TID
            self.ios_version = int(self.ios_tid[-2:], 16)
            # Title ID of the title
            tmddata.seek(0x18C)
            title_id_bin = tmddata.read(8)
            title_id_hex = binascii.hexlify(title_id_bin)
            self.title_id = str(title_id_hex.decode())
            # Type of content
            tmddata.seek(0x194)
            content_type_bin = tmddata.read(4)
            content_type_hex = binascii.hexlify(content_type_bin)
            self.content_type = str(content_type_hex.decode())
            # Publisher of the title
            tmddata.seek(0x198)
            self.group_id = tmddata.read(2)
            # Region of the title, 0 = JAP, 1 = USA, 2 = EUR, 3 = NONE, 4 = KOR
            tmddata.seek(0x19C)
            region_hex = tmddata.read(2)
            self.region = int.from_bytes(region_hex)
            # TODO: figure this one out
            tmddata.seek(0x19E)
            self.ratings = tmddata.read(16)
            # Access rights of the title; DVD-video access and AHBPROT
            tmddata.seek(0x1D8)
            self.access_rights = tmddata.read(4)
            # Calculate the version number by multiplying 0x1DC by 256 and adding 0x1DD
            tmddata.seek(0x1DC)
            title_version_high = int.from_bytes(tmddata.read(1)) * 256
            tmddata.seek(0x1DD)
            title_version_low = int.from_bytes(tmddata.read(1))
            self.title_version = title_version_high + title_version_low
            # The number of contents listed in the TMD
            tmddata.seek(0x1DE)
            self.num_contents = int.from_bytes(tmddata.read(2))
            # Content index in content list that contains the boot file
            tmddata.seek(0x1E0)
            self.boot_index = tmddata.read(2)
            # Get content records for the number of contents in num_contents.
            for content in range(0, self.num_contents):
                tmddata.seek(0x1E4 + (36 * content))
                content_record_hdr = struct.unpack(">LHH4x4s20s", tmddata.read(36))
                self.content_records.append(
                    ContentRecord(int(content_record_hdr[0]), int(content_record_hdr[1]),
                                  int(content_record_hdr[2]), int.from_bytes(content_record_hdr[3]),
                                  binascii.hexlify(content_record_hdr[4])))

    def get_title_id(self):
        """Returns the TID of the TMD's associated title."""
        return self.title_id

    def get_title_version(self):
        """Returns the version of the TMD's associated title."""
        return self.title_version

    def get_title_region(self):
        """Returns the region of the TMD's associated title."""
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
        """Returns whether the TMD is designed for the vWii or not."""
        if self.vwii == 1:
            return True
        else:
            return False

    def get_tmd_version(self):
        """Returns the version of the TMD."""
        return self.version

    def get_required_ios_tid(self):
        """Returns the TID of the required IOS for the title."""
        return self.ios_tid

    def get_required_ios(self):
        """Returns the required IOS version for the title."""
        return self.ios_version

    def get_title_type(self):
        """Returns the type of the TMD's associated title."""
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
        """Returns the type of content contained in the TMD's associated title."""
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

    def get_num_contents(self):
        """Returns the number of contents listed in the TMD."""
        return self.num_contents

    def get_content_record(self, record):
        """Returns the content record at the specified index."""
        if record < self.num_contents:
            return self.content_records[record]
        else:
            raise IndexError("Invalid content record! TMD lists '" + str(self.num_contents) +
                             "' contents but index was '" + str(record) + "'!")
