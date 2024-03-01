# "wad.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/WAD_files for details about the WAD format

import io
import binascii


class WAD:
    """Creates a WAD object to parse the header of a WAD file and retrieve the data contained in it."""
    def __init__(self, wad):
        self.wad = wad
        self.wad_hdr_size: int
        self.wad_type: str
        self.wad_version: int
        # === Sizes ===
        self.wad_cert_size: int
        self.wad_crl_size: int
        self.wad_tik_size: int
        self.wad_tmd_size: int
        # This is the size of the content region, which contains all app files combined.
        self.wad_content_size: int
        self.wad_meta_size: int
        # === Offsets ===
        self.wad_cert_offset: int
        self.wad_crl_offset: int
        self.wad_tik_offset: int
        self.wad_tmd_offset: int
        self.wad_content_offset: int
        self.wad_meta_offset: int
        # Load header data from WAD stream
        with io.BytesIO(self.wad) as waddata:
            # ====================================================================================
            # Get the sizes of each data region contained within the WAD.
            # ====================================================================================
            # Header length, which will always be 64 bytes, as it is padded out if it is shorter.
            self.wad_hdr_size = 64
            # WAD type, denoting whether this WAD contains boot2 ("ib"), or anything else ("Is").
            waddata.seek(0x04)
            self.wad_type = str(waddata.read(2).decode())
            # WAD version, this is always 0.
            waddata.seek(0x06)
            self.wad_version = waddata.read(2)
            # WAD cert size.
            waddata.seek(0x08)
            self.wad_cert_size = int(binascii.hexlify(waddata.read(4)), 16)
            # WAD crl size.
            waddata.seek(0x0c)
            self.wad_crl_size = int(binascii.hexlify(waddata.read(4)), 16)
            # WAD ticket size.
            waddata.seek(0x10)
            self.wad_tik_size = int(binascii.hexlify(waddata.read(4)), 16)
            # WAD TMD size.
            waddata.seek(0x14)
            self.wad_tmd_size = int(binascii.hexlify(waddata.read(4)), 16)
            # WAD content size.
            waddata.seek(0x18)
            self.wad_content_size = int(binascii.hexlify(waddata.read(4)), 16)
            # Publisher of the title contained in the WAD.
            waddata.seek(0x1c)
            self.wad_meta_size = int(binascii.hexlify(waddata.read(4)), 16)
            # ====================================================================================
            # Calculate file offsets from sizes. Every section of the WAD is padded out to a multiple of 0x40.
            # ====================================================================================
            self.wad_cert_offset = self.wad_hdr_size
            # crl isn't ever used, however an entry for its size exists in the header, so its calculated just in case.
            self.wad_crl_offset = int(64 * round((self.wad_cert_offset + self.wad_cert_size) / 64))
            self.wad_tik_offset = int(64 * round((self.wad_crl_offset + self.wad_crl_size) / 64))
            self.wad_tmd_offset = int(64 * round((self.wad_tik_offset + self.wad_tik_size) / 64))
            self.wad_content_offset = int(64 * round((self.wad_tmd_offset + self.wad_tmd_size) / 64))
            # meta is also never used, but Nintendo's tools calculate it so we should too.
            self.wad_meta_offset = int(64 * round((self.wad_content_offset + self.wad_content_size) / 64))

    def get_cert_region(self):
        """Returns the offset and size for the cert data."""
        return self.wad_cert_offset, self.wad_cert_size

    def get_crl_region(self):
        """Returns the offset and size for the crl data."""
        return self.wad_crl_offset, self.wad_crl_size

    def get_ticket_region(self):
        """Returns the offset and size for the ticket data."""
        return self.wad_tik_offset, self.wad_tik_size

    def get_tmd_region(self):
        """Returns the offset and size for the TMD data."""
        return self.wad_tmd_offset, self.wad_tmd_size

    def get_content_region(self):
        """Returns the offset and size for the content of the WAD."""
        return self.wad_content_offset, self.wad_tmd_size

    def get_wad_type(self):
        """Returns the type of the WAD. This is 'Is' unless the WAD contains boot2 where it is 'ib'."""
        return self.wad_type

    def get_cert_data(self):
        """Returns the certificate data from the WAD."""
        waddata = io.BytesIO(self.wad)
        waddata.seek(self.wad_cert_offset)
        cert_data = waddata.read(self.wad_cert_size)
        return cert_data

    def get_crl_data(self):
        """Returns the crl data from the WAD, if it exists."""
        waddata = io.BytesIO(self.wad)
        waddata.seek(self.wad_crl_offset)
        crl_data = waddata.read(self.wad_crl_size)
        return crl_data

    def get_ticket_data(self):
        """Returns the ticket data from the WAD."""
        waddata = io.BytesIO(self.wad)
        waddata.seek(self.wad_tik_offset)
        ticket_data = waddata.read(self.wad_tik_size)
        return ticket_data

    def get_tmd_data(self):
        """Returns the TMD data from the WAD."""
        waddata = io.BytesIO(self.wad)
        waddata.seek(self.wad_tmd_offset)
        tmd_data = waddata.read(self.wad_tmd_size)
        return tmd_data

    def get_content_data(self):
        """Returns the content of the WAD."""
        waddata = io.BytesIO(self.wad)
        waddata.seek(self.wad_content_offset)
        content_data = waddata.read(self.wad_content_size)
        return content_data
