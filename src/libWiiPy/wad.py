# Project: libWiiPy by NinjaCheetah
# File: wad.py by rmc
#
# See https://wiibrew.org/wiki/WAD_files for details about the WAD format

import binascii
from dataclasses import dataclass
from typing import List


@dataclass
class ContentRecord:
    """Creates a content record object that contains the details of a content contained in a title."""
    cid: int  # Content ID
    index: int  # Index in the list of contents
    content_type: int  # normal: 0x0001; dlc: 0x4001; shared: 0x8001
    content_size: int
    content_hash: bytearray  # SHA1 hash content


class wadHeader:
    """Break down 32 byte WAD header."""
    def __init__(self, wadhdr):
        self.wadhdr = wadhdr
        self.wad_hdr_size: int
        self.wad_type: int
        self.wad_version: int
        # Sizes
        self.wad_cert_size: int
        self.wad_crl_size: int
        self.wad_tik_size: int
        self.wad_tmd_size: int
        self.wad_app_size: int  # Note that this is the size of the app region. This is each individual app file bundled together.
        self.wad_meta_size: int
        # Offsets
        self.wad_cert_offset: int
        self.wad_crl_offset: int
        self.wad_tik_offset: int
        self.wad_tmd_offset: int
        self.wad_app_offset: int
        self.wad_meta_offset: int
        #self.content_record: List[ContentRecord]
        # Load header data from WAD file
        with open(wad, "rb") as wadfile:
            #====================================================================================
            # Get the sizes of each data region contained within the WAD. Sorry for mid code!
            #====================================================================================
            # Header length. Always seems to be 32 so we'll ignore it for now.
            wadfile.seek(0x0)
            self.wad_hdr_size = wadfile.read(4)
            # WAD type
            wadfile.seek(0x04)
            self.wad_type = wadfile.read(2)
            # WAD version
            wadfile.seek(0x06)
            self.wad_version = wadfile.read(2)
            # WAD cert size
            wadfile.seek(0x08)
            self.wad_cert_size = wadfile.read(4)
            # WAD crl size
            wadfile.seek(0x0c)
            self.wad_crl_size = wadfile.read(4)
            # WAD ticket size
            wadfile.seek(0x10)
            self.wad_tik_size = wadfile.read(4)
            # WAD TMD size
            wadfile.seek(0x14)
            self.wad_tmd_size = wadfile.read(4)
            # WAD app size
            wadfile.seek(0x18)
            self.wad_app_size = wadfile.read(4)
            # Publisher of the title
            wadfile.seek(0x1c)
            self.wad_meta_size = wadfile.read(4)
            #====================================================================================
            # Calculate file offsets from sizes
            #====================================================================================
            self.wad_cert_offset + self.wad_hdr_size
            # I've never seen crl used (don't even know what it's for) but still calculating in case...
            self.wad_crl_offset + self.wad_cert_offset + self.wad_cert_size
            self.wad_tik_offset + self.wad_crl_offset + self.wad_crl_size
            self.wad_tmd_offset + self.wad_tik_offset + self.wad_tik_size
            self.wad_app_offset + self.wad_tmd_offset + self.wad_tmd_size
            # Same with meta. If private Nintendo tools calculate these then maaaaaybe we should too.
            self.wad_meta_offset + self.wad_app_offset + self.wad_app_size

    def get_cert_region(self):
        """Returns the offset and size for the cert"""
        return self.wad_cert_offset, self.wad_cert_size

    def get_ticket_region(self):
        """Returns the offset and size for the ticket"""
        return self.wad_tik_offset, self.wad_tik_size

    def get_tmd_region(self):
        """Returns the offset and size for the TMD"""
        return self.wad_tmd_offset, self.wad_tmd_size

    def get_app_region(self):
        """Returns the offset and size for the app"""
        return self.wad_app_offset, self.wad_tmd_size
      
