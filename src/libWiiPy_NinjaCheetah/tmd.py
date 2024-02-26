import binascii
from dataclasses import dataclass
from typing import List


@dataclass
class ContentRecord:
    cid: int  # content id
    index: int  # number of the file
    content_type: int  # normal: 0x0001; dlc: 0x4001; shared: 0x8001
    content_size: int
    content_hash: bytearray  # SHA1 hash content


class TMD:
    def __init__(self, tmd):
        self.tmd = tmd
        self.sig_type: int
        self.sig: bytearray
        # u8 fill1[60];
        self.issuer: bytearray  # Root-CA%08x-CP%08x
        self.version: bytearray
        self.ca_crl_version: int
        self.signer_crl_version: int
        self.vwii: int
        self.sys_version: int
        self.title_id: bytearray
        self.title_type: int
        self.group_id: int  # publisher
        self.region: int
        self.ratings: int
        # u8 reserved[62];
        self.access_rights: int
        self.title_version: bytearray
        self.num_contents: int
        self.boot_index: int
        self.content_record: List[ContentRecord]
        # Load data from TMD file
        with open(tmd, "rb") as tmdfile:
            tmdfile.seek(0x140)
            self.issuer = tmdfile.read(64)
            tmdfile.seek(0x180)
            self.version = tmdfile.read(1)
            tmdfile.seek(0x181)
            self.ca_crl_version = tmdfile.read(1)
            tmdfile.seek(0x182)
            self.signer_crl_version = tmdfile.read(1)
            tmdfile.seek(0x183)
            self.vwii = tmdfile.read(1)
            tmdfile.seek(0x184)
            self.sys_version = tmdfile.read(8)
            tmdfile.seek(0x18C)
            self.title_id = tmdfile.read(8)
            tmdfile.seek(0x194)
            self.title_type = tmdfile.read(4)
            tmdfile.seek(0x198)
            self.group_id = tmdfile.read(2)
            tmdfile.seek(0x19C)
            self.region = tmdfile.read(2)
            tmdfile.seek(0x19E)
            self.ratings = tmdfile.read(16)
            tmdfile.seek(0x1D8)
            self.access_rights = tmdfile.read(4)
            tmdfile.seek(0x1DC)
            self.title_version = tmdfile.read(2)
            tmdfile.seek(0x1DE)
            self.number_of_groups = tmdfile.read(2)
            tmdfile.seek(0x1E0)
            self.boot_index = tmdfile.read(2)
        print(self.version, self.title_id, self.title_version)
        print(binascii.hexlify(self.version), binascii.hexlify(self.title_id), binascii.hexlify(self.title_version))
