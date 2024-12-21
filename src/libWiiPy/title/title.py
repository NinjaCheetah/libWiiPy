# "title/title.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Title for details about how titles are formatted

import math
from .cert import CertificateChain as _CertificateChain
from .content import ContentRegion as _ContentRegion
from .ticket import Ticket as _Ticket
from .tmd import TMD as _TMD
from .wad import WAD as _WAD
from .crypto import encrypt_title_key


class Title:
    """
    A Title object that contains all components of a title, and allows altering them. Provides higher-level access
    than manually creating WAD, TMD, Ticket, and ContentRegion objects and ensures that any data that needs to match
    between files matches.

    Attributes
    ----------
    wad: WAD
        A WAD object of a WAD containing the title's data.
    cert_chain: CertificateChain
        The chain of certificates used to verify the contents of a title.
    tmd: TMD
        A TMD object of the title's TMD.
    ticket: Ticket
        A Ticket object of the title's Ticket.
    content: ContentRegion
        A ContentRegion object containing the title's contents.
    """
    def __init__(self):
        self.wad: _WAD = _WAD()
        self.cert_chain: _CertificateChain = _CertificateChain()
        self.tmd: _TMD = _TMD()
        self.ticket: _Ticket = _Ticket()
        self.content: _ContentRegion = _ContentRegion()

    def load_wad(self, wad: bytes) -> None:
        """
        Load existing WAD data into the title and create WAD, TMD, Ticket, and ContentRegion objects based off of it
        to allow you to modify that data. Note that this will overwrite any existing data for this title.

        Parameters
        ----------
        wad : bytes
            The data for the WAD you wish to load.
        """
        # Create a new WAD object based on the WAD data provided.
        self.wad = _WAD()
        self.wad.load(wad)
        # Load the certificate chain.
        self.cert_chain = _CertificateChain()
        self.cert_chain.load(self.wad.get_cert_data())
        # Load the TMD.
        self.tmd = _TMD()
        self.tmd.load(self.wad.get_tmd_data())
        # Load the ticket.
        self.ticket = _Ticket()
        self.ticket.load(self.wad.get_ticket_data())
        # Load the content.
        self.content = _ContentRegion()
        self.content.load(self.wad.get_content_data(), self.tmd.content_records)
        # Ensure that the Title IDs of the TMD and Ticket match before doing anything else. If they don't, throw an
        # error because clearly something strange has gone on with the WAD and editing it probably won't work.
        #if self.tmd.title_id != str(self.ticket.title_id.decode()):
        #    raise ValueError("The Title IDs of the TMD and Ticket in this WAD do not match. This WAD appears to be "
        #                     "invalid.")

    def dump_wad(self) -> bytes:
        """
        Dumps all title components (TMD, Ticket, and contents) back into the WAD object, and then dumps the WAD back
        into raw data and returns it.

        Returns
        -------
        wad_data : bytes
            The raw data of the WAD.
        """
        # Set WAD type to ib if the title being packed is boot2.
        if self.tmd.title_id == "0000000100000001":
            self.wad.wad_type = "ib"
        # Dump the certificate chain and set it in the WAD.
        self.wad.set_cert_data(self.cert_chain.dump())
        # Dump the TMD and set it in the WAD.
        # This requires updating the content records and number of contents in the TMD first.
        self.tmd.content_records = self.content.content_records  # This may not be needed because it's a ref already
        self.tmd.num_contents = len(self.content.content_records)
        self.wad.set_tmd_data(self.tmd.dump())
        # Dump the Ticket and set it in the WAD.
        self.wad.set_ticket_data(self.ticket.dump())
        # Dump the ContentRegion and set it in the WAD.
        content_data, content_size = self.content.dump()
        self.wad.set_content_data(content_data, content_size)
        return self.wad.dump()

    def load_cert_chain(self, cert_chain: bytes) -> None:
        """
        Load an existing certificate chain into the title. Note that this will overwrite any existing certificate chain
        data for this title.

        Parameters
        ----------
        cert_chain: bytes
            The data for the certificate chain to load.
        """
        self.cert_chain.load(cert_chain)


    def load_tmd(self, tmd: bytes) -> None:
        """
        Load existing TMD data into the title. Note that this will overwrite any existing TMD data for this title.

        Parameters
        ----------
        tmd : bytes
            The data for the TMD to load.
        """
        self.tmd.load(tmd)

    def load_ticket(self, ticket: bytes) -> None:
        """
        Load existing Ticket data into the title. Note that this will overwrite any existing Ticket data for this
        title.

        Parameters
        ----------
        ticket : bytes
            The data for the Ticket to load.
        """
        self.ticket.load(ticket)

    def load_content_records(self) -> None:
        """
        Load content records from the TMD into the ContentRegion to allow loading content files based on the records.
        This requires that a TMD has already been loaded and will throw an exception if it isn't.
        """
        if not self.tmd.content_records:
            ValueError("No TMD appears to have been loaded, so content records cannot be read from it.")
        # Load the content records into the ContentRegion object, and update the number of contents.
        self.content.content_records = self.tmd.content_records
        self.content.num_contents = self.tmd.num_contents

    def set_title_id(self, title_id: str) -> None:
        """
        Sets the Title ID of the title in both the TMD and Ticket. This also re-encrypts the Title Key as the Title Key
        is used as the IV for decrypting it.

        Parameters
        ----------
        title_id : str
            The new Title ID of the title.
        """
        if len(title_id) != 16:
            raise ValueError("Invalid Title ID! Title IDs must be 8 bytes long.")
        self.tmd.set_title_id(title_id)
        title_key_decrypted = self.ticket.get_title_key()
        self.ticket.set_title_id(title_id)
        title_key_encrypted = encrypt_title_key(title_key_decrypted, self.ticket.common_key_index, title_id,
                                                self.ticket.is_dev)
        self.ticket.title_key_enc = title_key_encrypted

    def set_title_version(self, title_version: str | int) -> None:
        """
        Sets the version of the title in both the TMD and Ticket.

        Accepts either standard form (vX.X) as a string or decimal form (vXXX) as an integer.

        Parameters
        ----------
        title_version : str, int
            The new version of the title. See description for valid formats.
        """
        self.tmd.set_title_version(title_version)
        self.ticket.set_title_version(title_version)

    def get_content_by_index(self, index: id, skip_hash=False) -> bytes:
        """
        Gets an individual content from the content region based on the provided index, in decrypted form.

        Parameters
        ----------
        index : int
            The index of the content you want to get.
        skip_hash : bool, optional
            Skip the hash check and return the content regardless of its hash. Defaults to false.

        Returns
        -------
        bytes
            The decrypted content listed in the content record.
        """
        dec_content = self.content.get_content_by_index(index, self.ticket.get_title_key(), skip_hash)
        return dec_content

    def get_content_by_cid(self, cid: int, skip_hash=False) -> bytes:
        """
        Gets an individual content from the content region based on the provided Content ID, in decrypted form.

        Parameters
        ----------
        cid : int
            The Content ID of the content you want to get. Expected to be in decimal form.
        skip_hash : bool, optional
            Skip the hash check and return the content regardless of its hash. Defaults to false.

        Returns
        -------
        bytes
            The decrypted content listed in the content record.
        """
        dec_content = self.content.get_content_by_cid(cid, self.ticket.get_title_key(), skip_hash)
        return dec_content

    def get_title_size(self, absolute=False) -> int:
        """
        Gets the installed size of the title, including the TMD and Ticket, in bytes. The "absolute" option determines
        whether shared content sizes should be included in the total size or not. This option defaults to False.

        Parameters
        ----------
        absolute : bool, optional
            Whether shared contents should be included in the total size or not. Defaults to False.

        Returns
        -------
        int
            The installed size of the title, in bytes.
        """
        title_size = 0
        # Dumping and measuring the TMD and Ticket this way to ensure that any changes to them are measured properly.
        # Yes, the Ticket size should be a constant, but it's still good to check just in case.
        title_size += len(self.tmd.dump())
        title_size += len(self.ticket.dump())
        # For contents, get their sizes from the content records, because they store the intended sizes of the decrypted
        # contents, which are usually different from the encrypted sizes.
        for record in self.content.content_records:
            if record.content_type == 32769:
                if absolute:
                    title_size += record.content_size
            else:
                title_size += record.content_size
        return title_size

    def get_title_size_blocks(self, absolute=False) -> int:
        """
        Gets the installed size of the title, including the TMD and Ticket, in the Wii's displayed "blocks" format. The
        "absolute" option determines whether shared content sizes should be included in the total size or not. This
        option defaults to False.

        1 Wii block is equal to 128KiB, and if any amount of a block is used, the entire block is considered used.

        Parameters
        ----------
        absolute : bool, optional
            Whether shared contents should be included in the total size or not. Defaults to False.

        Returns
        -------
        int
            The installed size of the title, in blocks.
        """
        title_size_bytes = self.get_title_size(absolute)
        blocks = math.ceil(title_size_bytes / 131072)
        return blocks

    def add_enc_content(self, enc_content: bytes, cid: int, index: int, content_type: int, content_size: int,
                        content_hash: bytes) -> None:
        """
        Adds a new encrypted content to the ContentRegion, and adds the provided Content ID, index, content type,
        content size, and content hash to a new record in the ContentRecord list.

        Parameters
        ----------
        enc_content : bytes
            The new encrypted content to add.
        cid : int
            The Content ID to assign the new content in the content record.
        index : int
            The index used when encrypting the new content.
        content_type : int
            The type of the new content.
        content_size : int
            The size of the new encrypted content when decrypted.
        content_hash : bytes
            The hash of the new encrypted content when decrypted.
        """
        # Add the encrypted content.
        self.content.add_enc_content(enc_content, cid, index, content_type, content_size, content_hash)
        # Update the TMD to match.
        self.tmd.content_records = self.content.content_records

    def add_content(self, dec_content: bytes, cid: int, content_type: int) -> None:
        """
        Adds a new decrypted content to the end of the ContentRegion, and adds the provided Content ID, content type,
        content size, and content hash to a new record in the ContentRecord list. The index will be automatically
        assigned by incrementing the current highest index in the records.

        This first gets the content hash and size from the provided data, and then encrypts the content with the
        Title Key before adding it to the ContentRegion.

        Parameters
        ----------
        dec_content : bytes
            The new decrypted content to add.
        cid : int
            The Content ID to assign the new content in the content record.
        content_type : int
            The type of the new content.
        """
        # Add the decrypted content.
        self.content.add_content(dec_content, cid, content_type, self.ticket.get_title_key())
        # Update the TMD to match.
        self.tmd.content_records = self.content.content_records

    def set_enc_content(self, enc_content: bytes, index: int, content_size: int, content_hash: bytes, cid: int = None,
                        content_type: int = None) -> None:
        """
        Sets the content at the provided index to the provided new encrypted content. The provided hash and content size
        are set in the corresponding content record. A new Content ID or content type can also be specified, but if it
        isn't then the current values are preserved.

        This also updates the content records in the TMD after the content is set.

        Parameters
        ----------
        enc_content : bytes
            The new encrypted content to set.
        index : int
            The index to place the new content at.
        content_size : int
            The size of the new encrypted content when decrypted.
        content_hash : bytes
            The hash of the new encrypted content when decrypted.
        cid : int
            The Content ID to assign the new content in the content record.
        content_type : int
            The type of the new content.
        """
        # Set the encrypted content.
        self.content.set_enc_content(enc_content, index, content_size, content_hash, cid, content_type)
        # Update the TMD to match.
        self.tmd.content_records = self.content.content_records

    def set_content(self, dec_content: bytes, index: int, cid: int = None, content_type: int = None) -> None:
        """
        Sets the content at the provided index to the provided new decrypted content. The hash and content size of this
        content will be generated and then set in the corresponding content record. A new Content ID or content type can
        also be specified, but if it isn't then the current values are preserved.

        This also updates the content records in the TMD after the content is set.

        Parameters
        ----------
        dec_content : bytes
            The new decrypted content to set.
        index : int
            The index to place the new content at.
        cid : int, optional
            The Content ID to assign the new content in the content record.
        content_type : int, optional
            The type of the new content.
        """
        # Set the decrypted content.
        self.content.set_content(dec_content, index, self.ticket.get_title_key(), cid, content_type)
        # Update the TMD to match.
        self.tmd.content_records = self.content.content_records

    def load_content(self, dec_content: bytes, index: int) -> None:
        """
        Loads the provided decrypted content into the ContentRegion at the specified index, but first checks to make
        sure that it matches the corresponding record. This content will then be encrypted using the title's Title Key
        before being loaded.

        Parameters
        ----------
        dec_content : bytes
            The decrypted content to load.
        index : int
            The index to load the content at.
        """
        # Load the decrypted content.
        self.content.load_content(dec_content, index, self.ticket.get_title_key())

    def fakesign(self) -> None:
        """
        Fakesigns this Title for the trucha bug.

        This is done by brute-forcing a TMD and Ticket body hash starting with 00, causing it to pass signature
        verification on older IOS versions that incorrectly check the hash using strcmp() instead of memcmp(). The TMD
        and Ticket signatures will also be erased and replaced with all NULL bytes.

        This modifies the TMD and Ticket objects that are part of this Title in place. You will need to call this method
        after any changes to the TMD or Ticket, and before dumping the Title object into a WAD to ensure that the WAD
        is properly fakesigned.
        """
        self.tmd.num_contents = self.content.num_contents  # This needs to be updated in case it was changed
        self.tmd.fakesign()
        self.ticket.fakesign()

    def get_is_fakesigned(self):
        """
        Checks the Title object to see if it is currently fakesigned. This ensures that both the TMD and Ticket are
        fakesigned. For a description of fakesigning, refer to the fakesign() method.

        Returns
        -------
        bool:
            True if the Title is fakesigned, False otherwise.

        See Also
        --------
        libWiiPy.title.title.Title.fakesign()
        """
        if self.tmd.get_is_fakesigned and self.ticket.get_is_fakesigned():
            return True
        else:
            return False
