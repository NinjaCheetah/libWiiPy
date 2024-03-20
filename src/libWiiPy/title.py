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

    def set_title_id(self, title_id: str):
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
