# "wad.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/WAD_files for details about the WAD format

import io
import binascii
from .shared import align_value


class WAD:
    """
    Creates a WAD object to parse the header of a WAD file and retrieve the data contained in it.

    Parameters
    ----------
    wad : bytes
        A bytes object containing the contents of a WAD file.
    """
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
        with io.BytesIO(self.wad) as wad_data:
            # Read the first 8 bytes of the file to ensure that it's a WAD. This will currently reject boot2 WADs, but
            # this tool cannot handle them correctly right now anyway.
            wad_data.seek(0x0)
            wad_magic_bin = wad_data.read(8)
            wad_magic_hex = binascii.hexlify(wad_magic_bin)
            wad_magic = str(wad_magic_hex.decode())
            if wad_magic != "0000002049730000":
                raise TypeError("This does not appear to be a valid WAD file, or is a boot2 WAD, which is not currently"
                                "supported by this library.")
            # ====================================================================================
            # Get the sizes of each data region contained within the WAD.
            # ====================================================================================
            # Header length, which will always be 64 bytes, as it is padded out if it is shorter.
            self.wad_hdr_size = 64
            # WAD type, denoting whether this WAD contains boot2 ("ib"), or anything else ("Is").
            wad_data.seek(0x04)
            self.wad_type = str(wad_data.read(2).decode())
            # WAD version, this is always 0.
            wad_data.seek(0x06)
            self.wad_version = wad_data.read(2)
            # WAD cert size.
            wad_data.seek(0x08)
            self.wad_cert_size = int(binascii.hexlify(wad_data.read(4)), 16)
            # WAD crl size.
            wad_data.seek(0x0c)
            self.wad_crl_size = int(binascii.hexlify(wad_data.read(4)), 16)
            # WAD ticket size.
            wad_data.seek(0x10)
            self.wad_tik_size = int(binascii.hexlify(wad_data.read(4)), 16)
            # WAD TMD size.
            wad_data.seek(0x14)
            self.wad_tmd_size = int(binascii.hexlify(wad_data.read(4)), 16)
            # WAD content size.
            wad_data.seek(0x18)
            self.wad_content_size = int(binascii.hexlify(wad_data.read(4)), 16)
            # Time/build stamp for the title contained in the WAD.
            wad_data.seek(0x1c)
            self.wad_meta_size = int(binascii.hexlify(wad_data.read(4)), 16)
            # ====================================================================================
            # Calculate file offsets from sizes. Every section of the WAD is padded out to a multiple of 0x40.
            # ====================================================================================
            self.wad_cert_offset = self.wad_hdr_size
            # crl isn't ever used, however an entry for its size exists in the header, so its calculated just in case.
            self.wad_crl_offset = align_value(self.wad_cert_offset + self.wad_cert_size)
            self.wad_tik_offset = align_value(self.wad_crl_offset + self.wad_crl_size)
            self.wad_tmd_offset = align_value(self.wad_tik_offset + self.wad_tik_size)
            # meta isn't guaranteed to be used, but some older SDK titles use it, and not reading it breaks things.
            self.wad_meta_offset = align_value(self.wad_tmd_offset + self.wad_tmd_size)
            self.wad_content_offset = align_value(self.wad_meta_offset + self.wad_meta_size)

    def get_cert_region(self):
        """Gets the offset and size of the certificate data.

        Returns
        -------
        int
            The offset of the certificate data in the WAD.
        int
            The size of the certificate data in the WAD.
        """
        return self.wad_cert_offset, self.wad_cert_size

    def get_crl_region(self):
        """Gets the offset and size of the crl data.

        Returns
        -------
        int
            The offset of the crl data in the WAD.
        int
            The size of the crl data in the WAD.
        """
        return self.wad_crl_offset, self.wad_crl_size

    def get_ticket_region(self):
        """Gets the offset and size of the ticket data.

        Returns
        -------
        int
            The offset of the ticket data in the WAD.
        int
            The size of the ticket data in the WAD.
        """
        return self.wad_tik_offset, self.wad_tik_size

    def get_tmd_region(self):
        """Gets the offset and size of the TMD data.

        Returns
        -------
        int
            The offset of the TMD data in the WAD.
        int
            The size of the TMD data in the WAD.
        """
        return self.wad_tmd_offset, self.wad_tmd_size

    def get_content_region(self):
        """Gets the offset and size of the content of the WAD.

        Returns
        -------
        int
            The offset of the content data in the WAD.
        int
            The size of the content data in the WAD.
        """
        return self.wad_content_offset, self.wad_content_size

    def get_meta_region(self):
        """Gets the offset and size of the meta region of the WAD, which is typically unused.

        Returns
        -------
        int
            The offset of the meta region in the WAD.
        int
            The size of the meta region in the WAD.
        """
        return self.wad_meta_offset, self.wad_meta_size

    def get_wad_type(self):
        """Gets the type of the WAD.

        Returns
        -------
        str
            The type of the WAD. This is 'Is', unless the WAD contains boot2, where it is 'ib'.
        """
        return self.wad_type

    def get_cert_data(self):
        """Gets the certificate data from the WAD.

        Returns
        -------
        bytes
            The certificate data.
        """
        wad_data = io.BytesIO(self.wad)
        wad_data.seek(self.wad_cert_offset)
        cert_data = wad_data.read(self.wad_cert_size)
        return cert_data

    def get_crl_data(self):
        """Gets the crl data from the WAD, if it exists.

        Returns
        -------
        bytes
            The crl data.
        """
        wad_data = io.BytesIO(self.wad)
        wad_data.seek(self.wad_crl_offset)
        crl_data = wad_data.read(self.wad_crl_size)
        return crl_data

    def get_ticket_data(self):
        """Gets the ticket data from the WAD.

        Returns
        -------
        bytes
            The ticket data.
        """
        wad_data = io.BytesIO(self.wad)
        wad_data.seek(self.wad_tik_offset)
        ticket_data = wad_data.read(self.wad_tik_size)
        return ticket_data

    def get_tmd_data(self):
        """Returns the TMD data from the WAD.

        Returns
        -------
        bytes
            The TMD data.
        """
        wad_data = io.BytesIO(self.wad)
        wad_data.seek(self.wad_tmd_offset)
        tmd_data = wad_data.read(self.wad_tmd_size)
        return tmd_data

    def get_content_data(self):
        """Gets the content of the WAD.

        Returns
        -------
        bytes
            The content data.
        """
        wad_data = io.BytesIO(self.wad)
        wad_data.seek(self.wad_content_offset)
        content_data = wad_data.read(self.wad_content_size)
        return content_data

    def get_meta_data(self):
        """Gets the meta region of the WAD, which is typically unused.

        Returns
        -------
        bytes
            The meta region.
        """
        wad_data = io.BytesIO(self.wad)
        wad_data.seek(self.wad_meta_offset)
        meta_data = wad_data.read(self.wad_meta_size)
        return meta_data
