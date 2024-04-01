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

    Attributes
    ----------
    tmd : TMD
        A TMD object of the title's TMD.
    ticket : Ticket
        A Ticket object of the title's Ticket.
    content: ContentRegion
        A ContentRegion object containing the title's contents.
    """
    def __init__(self):
        self.wad: WAD = WAD()
        self.tmd: TMD = TMD()
        self.ticket: Ticket = Ticket()
        self.content: ContentRegion = ContentRegion()

    def set_wad(self, wad: bytes) -> None:
        """Load existing WAD data into the title and create WAD, TMD, Ticket, and ContentRegion objects based off of it
        to allow you to modify that data. Note that this will overwrite any existing data for this title.

        Parameters
        ----------
        wad : bytes
            The data for the WAD you wish to load.
        """
        # Create a new WAD object based on the WAD data provided.
        self.wad = WAD()
        self.wad.load(wad)
        # Load the TMD.
        self.tmd = TMD()
        self.tmd.load(self.wad.get_tmd_data())
        # Load the ticket.
        self.ticket = Ticket()
        self.ticket.load(self.wad.get_ticket_data())
        # Load the content.
        self.content = ContentRegion()
        self.content.load(self.wad.get_content_data(), self.tmd.content_records)
        # Ensure that the Title IDs of the TMD and Ticket match before doing anything else. If they don't, throw an
        # error because clearly something strange has gone on with the WAD and editing it probably won't work.
        if self.tmd.title_id != self.ticket.title_id_str:
            raise ValueError("The Title IDs of the TMD and Ticket in this WAD do not match. This WAD appears to be "
                             "invalid.")

    def dump(self) -> bytes:
        """Dumps all title components (TMD, Ticket, and contents) back into the WAD object, and then dumps the WAD back
        into raw data and returns it.

        Returns
        -------
        wad_data : bytes
            The raw data of the WAD.
        """
        # Dump the TMD and set it in the WAD.
        self.wad.set_tmd_data(self.tmd.dump())
        # Dump the Ticket and set it in the WAD.
        self.wad.set_ticket_data(self.ticket.dump())
        # Dump the ContentRegion and set it in the WAD.
        self.wad.set_content_data(self.content.dump())
        # Dump the WAD with the new regions back into raw data and return it.
        wad_data = self.wad.dump()
        return wad_data

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

    def get_content_by_index(self, index: id) -> bytes:
        """Gets an individual content from the content region based on the provided index, in decrypted form.

        Parameters
        ----------
        index : int
            The index of the content you want to get.

        Returns
        -------
        bytes
            The decrypted content listed in the content record.
        """
        # Load the Title Key from the Ticket.
        title_key = self.ticket.get_title_key()
        # Get the decrypted content and return it.
        dec_content = self.content.get_content_by_index(index, title_key)
        return dec_content

    def get_content_by_cid(self, cid: int) -> bytes:
        """Gets an individual content from the content region based on the provided Content ID, in decrypted form.

        Parameters
        ----------
        cid : int
            The Content ID of the content you want to get. Expected to be in decimal form.

        Returns
        -------
        bytes
            The decrypted content listed in the content record.
        """
        # Load the Title Key from the Ticket.
        title_key = self.ticket.get_title_key()
        # Get the decrypted content and return it.
        dec_content = self.content.get_content_by_cid(cid, title_key)
        return dec_content

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
