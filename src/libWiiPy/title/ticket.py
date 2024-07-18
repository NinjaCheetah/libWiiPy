# "title/ticket.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Ticket for details about the ticket format

import io
import binascii
import hashlib
from dataclasses import dataclass as _dataclass
from .crypto import decrypt_title_key
from typing import List


@_dataclass
class _TitleLimit:
    """
    A TitleLimit object that contains the type of restriction and the limit. The limit type can be one of the following:
    0 = None, 1 = Time Limit, 3 = None, or 4 = Launch Count. The maximum usage is then either the time in minutes the
    title can be played or the maximum number of launches allowed for that title, based on the type of limit applied.
    Private class used only by the Ticket class.

    Attributes
    ----------
    limit_type : int
        The type of play limit applied.
    maximum_usage : int
        The maximum value for the type of play limit applied.
    """
    # The type of play limit applied.
    # 0 = None, 1 = Time Limit, 3 = None, 4 = Launch Count
    limit_type: int
    # The maximum value of the limit applied.
    maximum_usage: int


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
        # "Permit mask. The current disc title is ANDed with the inverse of this mask to see if the result matches the
        # Permitted Titles Mask."
        self.permit_mask: bytes = b''
        self.title_export_allowed: int = 0  # Whether title export is allowed with a PRNG key or not.
        self.common_key_index: int = 0  # Which common key should be used. 0 = Common Key, 1 = Korean Key, 2 = vWii Key
        self.unknown2: bytes = b''  # More unknown data. Varies for VC/non-VC titles so reading it to ensure it matches.
        self.content_access_permissions: bytes = b''  # "Content access permissions (one bit for each content)"
        self.title_limits_list: List[_TitleLimit] = []  # List of play limits applied to the title.
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
            self.title_id = binascii.hexlify(ticket_data.read(8))
            # Title ID (as a string).
            self.title_id_str = str(self.title_id.decode())
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
                self.title_limits_list.append(_TitleLimit(limit_type, limit_value))

    def dump(self) -> bytes:
        """
        Dumps the Ticket object back into bytes.

        Returns
        -------
        bytes
            The full Ticket file as bytes.
        """
        ticket_data = b''
        # Signature type.
        ticket_data += self.signature_type
        # Signature data.
        ticket_data += self.signature
        # Padding to 64 bytes.
        ticket_data += b'\x00' * 60
        # Signature issuer.
        ticket_data += str.encode(self.signature_issuer)
        # ECDH data.
        ticket_data += self.ecdh_data
        # Ticket version.
        ticket_data += int.to_bytes(self.ticket_version, 1)
        # Reserved (all \0x00).
        ticket_data += b'\x00\x00'
        # Title Key.
        ticket_data += self.title_key_enc
        # Unknown (write \0x00).
        ticket_data += b'\x00'
        # Ticket ID.
        ticket_data += self.ticket_id
        # Console ID.
        ticket_data += int.to_bytes(self.console_id, 4)
        # Title ID.
        ticket_data += binascii.unhexlify(self.title_id)
        # Unknown data 1.
        ticket_data += self.unknown1
        # Title version.
        title_version_high = round(self.title_version / 256)
        ticket_data += int.to_bytes(title_version_high, 1)
        title_version_low = self.title_version % 256
        ticket_data += int.to_bytes(title_version_low, 1)
        # Permitted titles mask.
        ticket_data += self.permitted_titles
        # Permit mask.
        ticket_data += self.permit_mask
        # Title Export allowed.
        ticket_data += int.to_bytes(self.title_export_allowed, 1)
        # Common Key index.
        ticket_data += int.to_bytes(self.common_key_index, 1)
        # Unknown data 2.
        ticket_data += self.unknown2
        # Content access permissions.
        ticket_data += self.content_access_permissions
        # Padding (always \x00).
        ticket_data += b'\x00\x00'
        # Iterate over Title Limit objects, write them back into raw data, then add them to the Ticket.
        for title_limit in range(len(self.title_limits_list)):
            title_limit_data = b''
            # Write all fields from the title limit entry.
            title_limit_data += int.to_bytes(self.title_limits_list[title_limit].limit_type, 4)
            title_limit_data += int.to_bytes(self.title_limits_list[title_limit].maximum_usage, 4)
            # Write the entry to the ticket.
            ticket_data += title_limit_data
        return ticket_data

    def fakesign(self) -> None:
        """
        Fakesigns this Ticket for the trucha bug.

        This is done by brute-forcing a Ticket body hash starting with 00, causing it to pass signature verification on
        older IOS versions that incorrectly check the hash using strcmp() instead of memcmp(). The signature will also
        be erased and replaced with all NULL bytes.

        This modifies the Ticket object in place. You will need to call this method after any changes, and before
        dumping the Ticket object back into bytes.
        """
        # Clear the signature, so that the hash derived from it is guaranteed to always be
        # '0000000000000000000000000000000000000000'.
        self.signature = b'\x00' * 256
        current_int = 0
        test_hash = ''
        while test_hash[:2] != '00':
            current_int += 1
            # We're using the first 2 bytes of this unused region of the Ticket as a 16-bit integer, and incrementing
            # that to brute-force the hash we need.
            data_to_edit = self.unknown2
            data_to_edit = int.to_bytes(current_int, 2) + data_to_edit[2:]
            self.unknown2 = data_to_edit
            # Trim off the first 320 bytes, because we're only looking for the hash of the Ticket's body.
            # This is a try-except because an OverflowError will be thrown if the number being used to brute-force the
            # hash gets too big, as it is only a 16-bit integer. If that happens, then fakesigning has failed.
            try:
                test_hash = hashlib.sha1(self.dump()[320:]).hexdigest()
            except OverflowError:
                raise Exception("An error occurred during fakesigning. Ticket could not be fakesigned!")

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
