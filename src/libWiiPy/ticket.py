# "ticket.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Ticket for details about the ticket format

import io
import binascii
from .crypto import decrypt_title_key
from .types import TitleLimit
from typing import List


class Ticket:
    """
    A Ticket object that allows for either loading and editing an existing Ticket or creating one manually if desired.

    Attributes
    ----------
    signature : bytes
        The signature applied to the ticket.
    ticket_version : int
        The version of the ticket.
    title_key_enc : bytes
        The Title Key contained in the ticket, in encrypted form.
    ticket_id : bytes
        The unique ID of this ticket, used for console-specific title installations.
    console_id : int
        The unique ID of the console this ticket was designed for, if this is a console-specific ticket.
    title_version : int
        The version of the title this ticket was designed for.
    common_key_index : int
        The index of the common key required to decrypt this ticket's Title Key.
    """
    def __init__(self):
        # Signature blob header
        self.signature_type: bytes = b''  # Type of signature, always 0x10001 for RSA-2048
        self.signature: bytes = b''  # Actual signature data
        # v0 ticket data
        self.signature_issuer: str = ""  # Who issued the signature for the ticket
        self.ecdh_data: bytes = b''  # Involved in created one-time keys for console-specific title installs.
        self.ticket_version: int = 0  # The version of the current ticket file.
        self.title_key_enc: bytes = b''  # The title key of the ticket's respective title, encrypted by a common key.
        self.ticket_id: bytes = b''  # Used as the IV when decrypting the title key for console-specific title installs.
        self.console_id: int = 0  # ID of the console that the ticket was issued for.
        self.title_id: bytes = b''  # TID/IV used for AES-CBC encryption.
        self.title_id_str: str = ""  # TID in string form for comparing against the TMD.
        self.unknown1: bytes = b''  # Some unknown data, not always the same so reading it just in case.
        self.title_version: int = 0  # Version of the ticket's associated title.
        self.permitted_titles: bytes = b''  # Permitted titles mask
        self.permit_mask: bytes = b''  # "Permit mask. The current disc title is ANDed with the inverse of this mask to see if the result matches the Permitted Titles Mask."
        self.title_export_allowed: int = 0  # Whether title export is allowed with a PRNG key or not.
        self.common_key_index: int = 0  # Which common key should be used. 0 = Common Key, 1 = Korean Key, 2 = vWii Key
        self.unknown2: bytes = b''  # More unknown data. Varies for VC/non-VC titles so reading it to ensure it matches.
        self.content_access_permissions: bytes = b''  # "Content access permissions (one bit for each content)"
        self.title_limits_list: List[TitleLimit] = []  # List of play limits applied to the title.
        # v1 ticket data
        # TODO: Write in v1 ticket attributes here. This code can currently only handle v0 tickets, and will reject v1.

    def load(self, ticket: bytes) -> None:
        """
        Loads raw Ticket data and sets all attributes of the WAD object. This allows for manipulating an already
        existing Ticket.

        Parameters
        ----------
        ticket : bytes
            The data for the Ticket you wish to load.
        """
        with io.BytesIO(ticket) as ticket_data:
            # ====================================================================================
            # Parses each of the keys contained in the Ticket.
            # ====================================================================================
            # Signature type.
            ticket_data.seek(0x0)
            self.signature_type = ticket_data.read(4)
            # Signature data.
            ticket_data.seek(0x04)
            self.signature = ticket_data.read(256)
            # Signature issuer.
            ticket_data.seek(0x140)
            self.signature_issuer = str(ticket_data.read(64).decode())
            # ECDH data.
            ticket_data.seek(0x180)
            self.ecdh_data = ticket_data.read(60)
            # Ticket version.
            ticket_data.seek(0x1BC)
            self.ticket_version = int.from_bytes(ticket_data.read(1))
            if self.ticket_version == 1:
                raise ValueError("This appears to be a v1 ticket, which is not currently supported by libWiiPy. This "
                                 "feature is planned for a later release. Only v0 tickets are supported at this time.")
            # Title Key (Encrypted by a common key).
            ticket_data.seek(0x1BF)
            self.title_key_enc = ticket_data.read(16)
            # Ticket ID.
            ticket_data.seek(0x1D0)
            self.ticket_id = ticket_data.read(8)
            # Console ID.
            ticket_data.seek(0x1D8)
            self.console_id = int.from_bytes(ticket_data.read(4))
            # Title ID.
            ticket_data.seek(0x1DC)
            self.title_id = ticket_data.read(8)
            # Title ID (as a string).
            title_id_hex = binascii.hexlify(self.title_id)
            self.title_id_str = str(title_id_hex.decode())
            # Unknown data 1.
            ticket_data.seek(0x1E4)
            self.unknown1 = ticket_data.read(2)
            # Title version.
            ticket_data.seek(0x1E6)
            title_version_high = int.from_bytes(ticket_data.read(1)) * 256
            ticket_data.seek(0x1E7)
            title_version_low = int.from_bytes(ticket_data.read(1))
            self.title_version = title_version_high + title_version_low
            # Permitted titles mask.
            ticket_data.seek(0x1E8)
            self.permitted_titles = ticket_data.read(4)
            # Permit mask.
            ticket_data.seek(0x1EC)
            self.permit_mask = ticket_data.read(4)
            # Whether title export with a PRNG key is allowed.
            ticket_data.seek(0x1F0)
            self.title_export_allowed = int.from_bytes(ticket_data.read(1))
            # Common key index.
            ticket_data.seek(0x1F1)
            self.common_key_index = int.from_bytes(ticket_data.read(1))
            # Unknown data 2.
            ticket_data.seek(0x1F2)
            self.unknown2 = ticket_data.read(48)
            # Content access permissions.
            ticket_data.seek(0x222)
            self.content_access_permissions = ticket_data.read(64)
            # Content limits.
            ticket_data.seek(0x264)
            for limit in range(0, 8):
                limit_type = int.from_bytes(ticket_data.read(4))
                limit_value = int.from_bytes(ticket_data.read(4))
                self.title_limits_list.append(TitleLimit(limit_type, limit_value))

    def dump(self) -> bytes:
        """
        Dumps the Ticket object back into bytes. This also sets the raw Ticket attribute of Ticket object to the
        dumped data, and triggers load() again to ensure that the raw data and object match.

        Returns
        -------
        bytes
            The full Ticket file as bytes.
        """
        # Open the stream and begin writing to it.
        with io.BytesIO() as ticket_data:
            # Signature type.
            ticket_data.write(self.signature_type)
            # Signature data.
            ticket_data.write(self.signature)
            # Padding to 64 bytes.
            ticket_data.write(b'\x00' * 60)
            # Signature issuer.
            ticket_data.write(str.encode(self.signature_issuer))
            # ECDH data.
            ticket_data.write(self.ecdh_data)
            # Ticket version.
            ticket_data.write(int.to_bytes(self.ticket_version, 1))
            # Reserved (all \0x00).
            ticket_data.write(b'\x00\x00')
            # Title Key.
            ticket_data.write(self.title_key_enc)
            # Unknown (write \0x00).
            ticket_data.write(b'\x00')
            # Ticket ID.
            ticket_data.write(self.ticket_id)
            # Console ID.
            ticket_data.write(int.to_bytes(self.console_id, 4))
            # Title ID.
            ticket_data.write(self.title_id)
            # Unknown data 1.
            ticket_data.write(self.unknown1)
            # Title version.
            title_version_high = round(self.title_version / 256)
            ticket_data.write(int.to_bytes(title_version_high, 1))
            title_version_low = self.title_version % 256
            ticket_data.write(int.to_bytes(title_version_low, 1))
            # Permitted titles mask.
            ticket_data.write(self.permitted_titles)
            # Permit mask.
            ticket_data.write(self.permit_mask)
            # Title Export allowed.
            ticket_data.write(int.to_bytes(self.title_export_allowed, 1))
            # Common Key index.
            ticket_data.write(int.to_bytes(self.common_key_index, 1))
            # Unknown data 2.
            ticket_data.write(self.unknown2)
            # Content access permissions.
            ticket_data.write(self.content_access_permissions)
            # Padding (always \x00).
            ticket_data.write(b'\x00\x00')
            # Iterate over Title Limit objects, write them back into raw data, then add them to the Ticket.
            for title_limit in range(len(self.title_limits_list)):
                title_limit_data = io.BytesIO()
                # Write all fields from the title limit entry.
                title_limit_data.write(int.to_bytes(self.title_limits_list[title_limit].limit_type, 4))
                title_limit_data.write(int.to_bytes(self.title_limits_list[title_limit].maximum_usage, 4))
                # Seek to the start and write the entry to the Ticket.
                title_limit_data.seek(0x0)
                ticket_data.write(title_limit_data.read())
                title_limit_data.close()
            # Set the Ticket attribute of the object to the new raw Ticket.
            ticket_data.seek(0x0)
            ticket_data_raw = ticket_data.read()
        # Return the raw TMD for the data contained in the object.
        return ticket_data_raw

    def get_title_id(self) -> str:
        """
        Gets the Title ID of the ticket's associated title.

        Returns
        -------
        str
            The Title ID of the title.
        """
        title_id_str = str(self.title_id.decode())
        return title_id_str

    def get_common_key_type(self) -> str:
        """
        Gets the name of the common key used to encrypt the Title Key contained in the ticket.

        Returns
        -------
        str
            The name of the common key required.

        See Also
        --------
        commonkeys.get_common_key
        """
        match self.common_key_index:
            case 0:
                return "Common"
            case 1:
                return "Korean"
            case 2:
                return "vWii"

    def get_title_key(self) -> bytes:
        """
        Gets the decrypted title key contained in the ticket.

        Returns
        -------
        bytes
            The decrypted title key.
        """
        title_key = decrypt_title_key(self.title_key_enc, self.common_key_index, self.title_id)
        return title_key

    def set_title_id(self, title_id) -> None:
        """
        Sets the Title ID of the title in the Ticket.

        Parameters
        ----------
        title_id : str
            The new Title ID of the title.
        """
        if len(title_id) != 16:
            raise ValueError("Invalid Title ID! Title IDs must be 8 bytes long.")
        self.title_id_str = title_id
        self.title_id = binascii.unhexlify(title_id)
