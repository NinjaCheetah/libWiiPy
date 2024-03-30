# "title.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Title for details about how titles are formatted

from .content import ContentRegion
from .ticket import Ticket
from .tmd import TMD
from .wad import WAD


class Title:
    """Creates a Title object that contains all components of a title, and allows altering them.

    Parameters
    ----------
    wad : WAD
        A WAD object to load data from.

    Attributes
    ----------
    tmd : TMD
        A TMD object of the title's TMD.
    ticket : Ticket
        A Ticket object of the title's Ticket.
    content: ContentRegion
        A ContentRegion object containing the title's contents.
    """
    def __init__(self, wad: WAD):
        self.wad = wad
        self.tmd: TMD
        self.ticket: Ticket
        self.content: ContentRegion
        # Load data from the WAD object, and generate all other objects from the data in it.
        # Load the TMD.
        self.tmd = TMD(self.wad.get_tmd_data())
        # Load the ticket.
        self.ticket = Ticket(self.wad.get_ticket_data())
        # Load the content.
        self.content = ContentRegion(self.wad.get_content_data(), self.tmd.content_records)
        # Ensure that the Title IDs of the TMD and Ticket match before doing anything else. If they don't, throw an
        # error because clearly something strange has gone on with the WAD and editing it probably won't work.
        if self.tmd.title_id != self.ticket.title_id_str:
            raise ValueError("The Title IDs of the TMD and Ticket in this WAD do not match. This WAD appears to be "
                             "invalid.")

    def dump(self) -> bytes:
        """Dumps all title components (TMD, ticket, and content) back into the WAD object, and then dumps the WAD back
        into raw data and returns it.

        Returns
        -------
        wad_data : bytes
            The raw data of the WAD.
        """
        # Dump the TMD.

    def set_title_id(self, title_id: str) -> None:
        """Sets the Title ID of the title in both the TMD and Ticket.

        Parameters
        ----------
        title_id : str
            The new Title ID of the title.
        """
        if len(title_id) != 16:
            raise ValueError("Invalid Title ID! Title IDs must be 8 bytes long.")
        self.tmd.set_title_id(title_id)
        self.ticket.set_title_id(title_id)

    def set_enc_content(self, enc_content: bytes, cid: int, index: int, content_type: int, content_size: int,
                        content_hash: bytes) -> None:
        """Sets the provided index to a new content with the provided Content ID. Hashes and size of the content are
        set in the content record, with a new record being added if necessary. The TMD is also updated to match the new
        records.

        Parameters
        ----------
        enc_content : bytes
            The new encrypted content to set.
        cid : int
            The Content ID to assign the new content in the content record.
        index : int
            The index to place the new content at.
        content_type : int
            The type of the new content.
        content_size : int
            The size of the new encrypted content when decrypted.
        content_hash : bytes
            The hash of the new encrypted content when decrypted.
        """
        # Set the encrypted content.
        self.content.set_enc_content(enc_content, cid, index, content_type, content_size, content_hash)
        # Update the TMD to match.
        self.tmd.content_records = self.content.content_records

    def set_content(self, dec_content: bytes, cid: int, index: int, content_type: int) -> None:
        """Sets the provided index to a new content with the provided Content ID. Hashes and size of the content are
        set in the content record, with a new record being added if necessary. The Title Key is sourced from this
        title's loaded ticket. The TMD is also updated to match the new records.

        Parameters
        ----------
        dec_content : bytes
            The new decrypted content to set.
        cid : int
            The Content ID to assign the new content in the content record.
        index : int
            The index to place the new content at.
        content_type : int
            The type of the new content.
        """
        # Set the decrypted content.
        self.content.set_content(dec_content, cid, index, content_type, self.ticket.get_title_key())
        # Update the TMD to match.
        self.tmd.content_records = self.content.content_records
