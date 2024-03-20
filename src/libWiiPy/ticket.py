# "ticket.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Ticket for details about the ticket format

import io
import binascii
from .crypto import decrypt_title_key
from dataclasses import dataclass
from typing import List


@dataclass
class TitleLimit:
    """Creates a TitleLimit object that contains the type of restriction and the limit.

    Attributes
    ----------
    limit_type : int
        The type of play limit applied.
    maximum_usage : int
        The maximum value for the type of play limit applied.
    """
    # The type of play limit applied. The following types exist:
    # 0 = None, 1 = Time Limit, 3 = None, 4 = Launch Count
    limit_type: int
    # The maximum value of the limit applied.
    # This is either the number of minutes for a time limit, or the number of launches for a launch limit.
    maximum_usage: int


class Ticket:
    """Creates a Ticket object to parse a Ticket file to retrieve the Title Key needed to decrypt it.

    Parameters
    ----------
    ticket : bytes
        A bytes object containing the contents of a ticket file.

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
    def __init__(self, ticket):
        self.ticket = ticket
        # Signature blob header
        self.signature_type: bytes  # Type of signature, always 0x10001 for RSA-2048
        self.signature: bytes  # Actual signature data
        # v0 ticket data
        self.signature_issuer: str  # Who issued the signature for the ticket
        self.ecdh_data: bytes  # Involved in created one-time keys for console-specific title installs.
        self.ticket_version: int  # The version of the current ticket file.
        self.title_key_enc: bytes  # The title key of the ticket's respective title, encrypted by a common key.
        self.ticket_id: bytes  # Used as the IV when decrypting the title key for console-specific title installs.
        self.console_id: int  # ID of the console that the ticket was issued for.
        self.title_id: bytes  # TID/IV used for AES-CBC encryption.
        self.title_id_str: str  # TID in string form for comparing against the TMD.
        self.title_version: int  # Version of the ticket's associated title.
        self.permitted_titles: bytes  # Permitted titles mask
        self.permit_mask: bytes  # "Permit mask. The current disc title is ANDed with the inverse of this mask to see if the result matches the Permitted Titles Mask."
        self.title_export_allowed: int  # Whether title export is allowed with a PRNG key or not.
        self.common_key_index: int  # Which common key should be used. 0 = Common Key, 1 = Korean Key, 2 = vWii Key
        self.content_access_permissions: bytes  # "Content access permissions (one bit for each content)"
        self.title_limits_list: List[TitleLimit] = []  # List of play limits applied to the title.
        # v1 ticket data
        # TODO: Figure out v1 ticket stuff
        with io.BytesIO(self.ticket) as ticket_data:
            # ====================================================================================
            # Parses each of the keys contained in the Ticket.
            # ====================================================================================
            # Signature type
            ticket_data.seek(0x0)
            self.signature_type = ticket_data.read(4)
            # Signature data
            ticket_data.seek(0x04)
            self.signature = ticket_data.read(256)
            # Signature issuer
            ticket_data.seek(0x140)
            self.signature_issuer = str(ticket_data.read(64).decode())
            # ECDH data
            ticket_data.seek(0x180)
            self.ecdh_data = ticket_data.read(60)
            # Ticket version
            ticket_data.seek(0x1BC)
            self.ticket_version = int.from_bytes(ticket_data.read(1))
            # Title Key (Encrypted by a common key)
            ticket_data.seek(0x1BF)
            self.title_key_enc = ticket_data.read(16)
            # Ticket ID
            ticket_data.seek(0x1D0)
            self.ticket_id = ticket_data.read(8)
            # Console ID
            ticket_data.seek(0x1D8)
            self.console_id = int.from_bytes(ticket_data.read(4))
            # Title ID
            ticket_data.seek(0x1DC)
            self.title_id = ticket_data.read(8)
            # Title ID (as a string)
            title_id_hex = binascii.hexlify(self.title_id)
            self.title_id_str = str(title_id_hex.decode())
            # Title version
            ticket_data.seek(0x1E6)
            title_version_high = int.from_bytes(ticket_data.read(1)) * 256
            ticket_data.seek(0x1E7)
            title_version_low = int.from_bytes(ticket_data.read(1))
            self.title_version = title_version_high + title_version_low
            # Permitted titles mask
            ticket_data.seek(0x1E8)
            self.permitted_titles = ticket_data.read(4)
            # Permit mask
            ticket_data.seek(0x1EC)
            self.permit_mask = ticket_data.read(4)
            # Whether title export with a PRNG key is allowed
            ticket_data.seek(0x1F0)
            self.title_export_allowed = int.from_bytes(ticket_data.read(1))
            # Common key index
            ticket_data.seek(0x1F1)
            self.common_key_index = int.from_bytes(ticket_data.read(1))
            # Content access permissions
            ticket_data.seek(0x222)
            self.content_access_permissions = ticket_data.read(64)
            # Content limits
            ticket_data.seek(0x264)
            for limit in range(0, 8):
                limit_type = int.from_bytes(ticket_data.read(4))
                limit_value = int.from_bytes(ticket_data.read(4))
                self.title_limits_list.append(TitleLimit(limit_type, limit_value))

    def get_title_id(self):
        """Gets the Title ID of the ticket's associated title.

        Returns
        -------
        str
            The Title ID of the title.
        """
        title_id_str = str(self.title_id.decode())
        return title_id_str

    def get_common_key_type(self):
        """Gets the name of the common key used to encrypt the Title Key contained in the ticket.

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

    def get_title_key(self):
        """Gets the decrypted title key contained in the ticket.

        Returns
        -------
        bytes
            The decrypted title key.
        """
        title_key = decrypt_title_key(self.title_key_enc, self.common_key_index, self.title_id)
        return title_key

    def set_title_id(self, title_id):
        """Sets the Title ID of the title in the Ticket.

        Parameters
        ----------
        title_id : str
            The new Title ID of the title.
        """
        if len(title_id) != 16:
            raise ValueError("Invalid Title ID! Title IDs must be 8 bytes long.")
        self.title_id_str = title_id
        self.title_id = binascii.unhexlify(title_id)
