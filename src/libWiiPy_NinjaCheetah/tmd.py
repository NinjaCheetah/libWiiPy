import binascii
from dataclasses import dataclass
from typing import List


@dataclass
class ContentRecord:
    cid: int  # Content ID
    index: int  # Index in the list of contents
    content_type: int  # normal: 0x0001; dlc: 0x4001; shared: 0x8001
    content_size: int
    content_hash: bytearray  # SHA1 hash content


class TMD:
    def __init__(self, tmd):
        self.tmd = tmd
        self.sig_type: int
        self.sig: bytearray
        self.issuer: bytearray  # Root-CA%08x-CP%08x
        self.version: bytearray  # This seems to always be 0 no matter what?
        self.ca_crl_version: int
        self.signer_crl_version: int
        self.vwii: int
        self.sys_version: int
        self.title_id: str
        self.title_type: int
        self.group_id: int  # Publisher of the title
        self.region: int
        self.ratings: int
        self.access_rights: int
        self.title_version: int
        self.num_contents: int
        self.boot_index: int
        self.content_record: List[ContentRecord]
        # Load data from TMD file
        with open(tmd, "rb") as tmdfile:
            # Signing certificate issuer
            tmdfile.seek(0x140)
            self.issuer = tmdfile.read(64)
            # TMD version, always seems to be 0?
            tmdfile.seek(0x180)
            self.version = tmdfile.read(1)
            # TODO: label
            tmdfile.seek(0x181)
            self.ca_crl_version = tmdfile.read(1)
            # TODO: label
            tmdfile.seek(0x182)
            self.signer_crl_version = tmdfile.read(1)
            # If this is a vWii title or not
            tmdfile.seek(0x183)
            self.vwii = tmdfile.read(1)
            # IOS version to use TODO: finish this
            tmdfile.seek(0x184)
            self.sys_version = tmdfile.read(8)
            # Title ID of the title
            tmdfile.seek(0x18C)
            title_id_hex = tmdfile.read(8)
            title_id_bin = binascii.hexlify(title_id_hex)
            self.title_id = str(title_id_bin.decode())
            # Type of title TODO: finish this
            tmdfile.seek(0x194)
            self.title_type = tmdfile.read(4)
            # Publisher of the title
            tmdfile.seek(0x198)
            self.group_id = tmdfile.read(2)
            # Region of the title, 0 = JAP, 1 = USA, 2 = EUR, 3 = NONE, 4 = KOR
            tmdfile.seek(0x19C)
            region_hex = tmdfile.read(2)
            self.region = int.from_bytes(region_hex)
            # TODO: figure this one out
            tmdfile.seek(0x19E)
            self.ratings = tmdfile.read(16)
            # Access rights of the title; DVD-video access and AHBPROT
            tmdfile.seek(0x1D8)
            self.access_rights = tmdfile.read(4)
            # Calculate the version number by multiplying 0x1DC by 256 and adding 0x1DD
            tmdfile.seek(0x1DC)
            title_version_high = int.from_bytes(tmdfile.read(1)) * 256
            tmdfile.seek(0x1DD)
            title_version_low = int.from_bytes(tmdfile.read(1))
            self.title_version = title_version_high + title_version_low
            # The number of contents listed in the TMD
            tmdfile.seek(0x1DE)
            self.num_contents = tmdfile.read(2)
            # TODO: label
            tmdfile.seek(0x1E0)
            self.boot_index = tmdfile.read(2)

    def get_title_id(self):
        return self.title_id

    def get_title_version(self):
        return self.title_version

    def get_title_region(self):
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
        if self.vwii == 1:
            return True
        else:
            return False
