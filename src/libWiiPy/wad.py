# "wad.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/WAD_files for details about the WAD format

import io
import binascii
from .shared import align_value, pad_bytes


class WAD:
    """
    A WAD object that allows for either loading and editing an existing WAD or creating a new WAD from raw data.

    Attributes
    ----------
    wad_type : str
        The type of WAD, either ib for boot2 or Is for normal installable WADs.
    wad_cert_size : int
        The size of the WAD's certificate.
    wad_crl_size : int
        The size of the WAD's crl.
    wad_tik_size : int
        The size of the WAD's Ticket.
    wad_tmd_size : int
        The size of the WAD's TMD.
    wad_content_size : int
        The size of WAD's total content region.
    wad_meta_size : int
        The size of the WAD's meta/footer.
    """
    def __init__(self):
        self.wad_hdr_size: int = 64
        self.wad_type: str = "Is"
        self.wad_version: bytes = b'\x00\x00'
        # === Sizes ===
        self.wad_cert_size: int = 0
        self.wad_crl_size: int = 0
        self.wad_tik_size: int = 0
        self.wad_tmd_size: int = 0
        # This is the size of the content region, which contains all app files combined.
        self.wad_content_size: int = 0
        self.wad_meta_size: int = 0
        # === Data ===
        self.wad_cert_data: bytes = b''
        self.wad_crl_data: bytes = b''
        self.wad_tik_data: bytes = b''
        self.wad_tmd_data: bytes = b''
        self.wad_content_data: bytes = b''
        self.wad_meta_data: bytes = b''

    def load(self, wad_data) -> None:
        """
        Loads raw WAD data and sets all attributes of the WAD object. This allows for manipulating an already
        existing WAD file.

        Parameters
        ----------
        wad_data : bytes
            The data for the WAD you wish to load.
        """
        with io.BytesIO(wad_data) as wad_data:
            # Read the first 8 bytes of the file to ensure that it's a WAD. Has two possible valid values for the two
            # different types of WADs that might be encountered.
            wad_data.seek(0x0)
            wad_magic_bin = wad_data.read(8)
            wad_magic_hex = binascii.hexlify(wad_magic_bin)
            wad_magic = str(wad_magic_hex.decode())
            if wad_magic != "0000002049730000" and wad_magic != "0000002069620000":
                raise TypeError("This does not appear to be a valid WAD file.")
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
            wad_cert_offset = self.wad_hdr_size
            # crl isn't ever used, however an entry for its size exists in the header, so its calculated just in case.
            wad_crl_offset = align_value(wad_cert_offset + self.wad_cert_size)
            wad_tik_offset = align_value(wad_crl_offset + self.wad_crl_size)
            wad_tmd_offset = align_value(wad_tik_offset + self.wad_tik_size)
            # meta isn't guaranteed to be used, but some older SDK titles use it, and not reading it breaks things.
            wad_meta_offset = align_value(wad_tmd_offset + self.wad_tmd_size)
            wad_content_offset = align_value(wad_meta_offset + self.wad_meta_size)
            # ====================================================================================
            # Load data for each WAD section based on the previously calculated offsets.
            # ====================================================================================
            # Cert data.
            wad_data.seek(wad_cert_offset)
            self.wad_cert_data = wad_data.read(self.wad_cert_size)
            # Crl data.
            wad_data.seek(wad_crl_offset)
            self.wad_crl_data = wad_data.read(self.wad_crl_size)
            # Ticket data.
            wad_data.seek(wad_tik_offset)
            self.wad_tik_data = wad_data.read(self.wad_tik_size)
            # TMD data.
            wad_data.seek(wad_tmd_offset)
            self.wad_tmd_data = wad_data.read(self.wad_tmd_size)
            # Content data.
            wad_data.seek(wad_content_offset)
            self.wad_content_data = wad_data.read(self.wad_content_size)
            # Meta data.
            wad_data.seek(wad_meta_offset)
            self.wad_meta_data = wad_data.read(self.wad_meta_size)

    def dump(self) -> bytes:
        """
        Dumps the WAD object into the raw WAD file. This allows for creating a WAD file from the data contained in
        the WAD object.

        Returns
        -------
        bytes
            The full WAD file as bytes.
        """
        wad_data = b''
        # Lead-in data.
        wad_data += b'\x00\x00\x00\x20'
        # WAD type.
        wad_data += str.encode(self.wad_type)
        # WAD version.
        wad_data += self.wad_version
        # WAD cert size.
        wad_data += int.to_bytes(self.wad_cert_size, 4)
        # WAD crl size.
        wad_data += int.to_bytes(self.wad_crl_size, 4)
        # WAD ticket size.
        wad_data += int.to_bytes(self.wad_tik_size, 4)
        # WAD TMD size.
        wad_data += int.to_bytes(self.wad_tmd_size, 4)
        # WAD content size.
        wad_data += int.to_bytes(self.wad_content_size, 4)
        # WAD meta size.
        wad_data += int.to_bytes(self.wad_meta_size, 4)
        wad_data = pad_bytes(wad_data)
        # Retrieve the cert data and write it out.
        wad_data += self.get_cert_data()
        wad_data = pad_bytes(wad_data)
        # Retrieve the crl data and write it out.
        wad_data += self.get_crl_data()
        wad_data = pad_bytes(wad_data)
        # Retrieve the ticket data and write it out.
        wad_data += self.get_ticket_data()
        wad_data = pad_bytes(wad_data)
        # Retrieve the TMD data and write it out.
        wad_data += self.get_tmd_data()
        wad_data = pad_bytes(wad_data)
        # Retrieve the meta/footer data and write it out.
        wad_data += self.get_meta_data()
        wad_data = pad_bytes(wad_data)
        # Retrieve the content data and write it out.
        wad_data += self.get_content_data()
        wad_data = pad_bytes(wad_data)
        # Return the raw WAD file for the data contained in the object.
        return wad_data

    def get_wad_type(self) -> str:
        """
        Gets the type of the WAD.

        Returns
        -------
        str
            The type of the WAD. This is 'Is', unless the WAD contains boot2, where it is 'ib'.
        """
        return self.wad_type

    def get_cert_data(self) -> bytes:
        """
        Gets the certificate data from the WAD.

        Returns
        -------
        bytes
            The certificate data.
        """
        return self.wad_cert_data

    def get_crl_data(self) -> bytes:
        """
        Gets the crl data from the WAD, if it exists.

        Returns
        -------
        bytes
            The crl data.
        """
        return self.wad_crl_data

    def get_ticket_data(self) -> bytes:
        """
        Gets the ticket data from the WAD.

        Returns
        -------
        bytes
            The ticket data.
        """
        return self.wad_tik_data

    def get_tmd_data(self) -> bytes:
        """
        Returns the TMD data from the WAD.

        Returns
        -------
        bytes
            The TMD data.
        """
        return self.wad_tmd_data

    def get_content_data(self) -> bytes:
        """
        Gets the content of the WAD.

        Returns
        -------
        bytes
            The content data.
        """
        return self.wad_content_data

    def get_meta_data(self) -> bytes:
        """
        Gets the meta region of the WAD, which is typically unused.

        Returns
        -------
        bytes
            The meta region.
        """
        return self.wad_meta_data

    def set_cert_data(self, cert_data) -> None:
        """
        Sets the certificate data of the WAD. Also calculates the new size.

        Parameters
        ----------
        cert_data : bytes
            The new certificate data.
        """
        self.wad_cert_data = cert_data
        # Calculate the size of the new cert data.
        self.wad_cert_size = len(cert_data)

    def set_crl_data(self, crl_data) -> None:
        """
        Sets the crl data of the WAD. Also calculates the new size.

        Parameters
        ----------
        crl_data : bytes
            The new crl data.
        """
        self.wad_crl_data = crl_data
        # Calculate the size of the new crl data.
        self.wad_crl_size = len(crl_data)

    def set_tmd_data(self, tmd_data) -> None:
        """
        Sets the TMD data of the WAD. Also calculates the new size.

        Parameters
        ----------
        tmd_data : bytes
            The new TMD data.
        """
        self.wad_tmd_data = tmd_data
        # Calculate the size of the new TMD data.
        self.wad_tmd_size = len(tmd_data)

    def set_ticket_data(self, tik_data) -> None:
        """
        Sets the Ticket data of the WAD. Also calculates the new size.

        Parameters
        ----------
        tik_data : bytes
            The new TMD data.
        """
        self.wad_tik_data = tik_data
        # Calculate the size of the new Ticket data.
        self.wad_tik_size = len(tik_data)

    def set_content_data(self, content_data) -> None:
        """
        Sets the content data of the WAD. Also calculates the new size.

        Parameters
        ----------
        content_data : bytes
            The new content data.
        """
        self.wad_content_data = content_data
        # Calculate the size of the new content data.
        self.wad_content_size = len(content_data)

    def set_meta_data(self, meta_data) -> None:
        """
        Sets the meta data of the WAD. Also calculates the new size.

        Parameters
        ----------
        meta_data : bytes
            The new meta data.
        """
        self.wad_meta_data = meta_data
        # Calculate the size of the new meta data.
        self.wad_meta_size = len(meta_data)
