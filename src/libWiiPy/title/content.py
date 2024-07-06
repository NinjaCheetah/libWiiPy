# "title/content.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Title for details about how titles are formatted

import io
import hashlib
from typing import List
from ..types import _ContentRecord
from ..shared import _pad_bytes, _align_value
from .crypto import decrypt_content, encrypt_content


class ContentRegion:
    """
    A ContentRegion object to parse the continuous content region of a WAD. Allows for retrieving content from the
    region in both encrypted or decrypted form, and setting new content.

    Attributes
    ----------
    content_records : List[_ContentRecord]
        The content records for the content stored in the region.
    num_contents : int
        The total number of contents stored in the region.
    """

    def __init__(self):
        self.content_records: List[_ContentRecord] = []
        self.content_region_size: int = 0  # Size of the content region.
        self.num_contents: int = 0  # Number of contents in the content region.
        self.content_start_offsets: List[int] = [0]  # The start offsets of each content in the content region.
        self.content_list: List[bytes] = []

    def load(self, content_region: bytes, content_records: List[_ContentRecord]) -> None:
        """
        Loads the raw content region and builds a list of all the contents.

        Parameters
        ----------
        content_region : bytes
            The raw data for the content region being loaded.
        content_records : list[_ContentRecord]
            A list of ContentRecord objects detailing all contents contained in the region.
        """
        self.content_records = content_records
        # Get the total size of the content region.
        self.content_region_size = len(content_region)
        with io.BytesIO(content_region) as content_region_data:
            self.num_contents = len(self.content_records)
            # Calculate the offsets of each content in the content region.
            # Content is aligned to 16 bytes, however a new content won't start until the next multiple of 64 bytes.
            # Because of this, we need to add bytes to the next 64 byte offset if the previous content wasn't that long.
            for content in self.content_records[:-1]:
                start_offset = content.content_size + self.content_start_offsets[-1]
                if (content.content_size % 64) != 0:
                    start_offset += 64 - (content.content_size % 64)
                self.content_start_offsets.append(start_offset)
            # Build a list of all the encrypted content data.
            for content in range(self.num_contents):
                # Seek to the start of the content based on the list of offsets.
                content_region_data.seek(self.content_start_offsets[content])
                # Calculate the number of bytes we need to read by adding bytes up the nearest multiple of 16 if needed.
                bytes_to_read = self.content_records[content].content_size
                if (bytes_to_read % 16) != 0:
                    bytes_to_read += 16 - (bytes_to_read % 16)
                # Read the file based on the size of the content in the associated record, then append that data to
                # the list of content.
                content_enc = content_region_data.read(bytes_to_read)
                self.content_list.append(content_enc)

    def dump(self) -> tuple[bytes, int]:
        """
        Takes the list of contents and assembles them back into one content region. Returns this content region as a
        bytes object and sets the raw content region variable to this result, then calls load() again to make sure the
        content list matches the raw data.

        Returns
        -------
        bytes
            The full ContentRegion as bytes, including padding between content.
        int
            The size of the ContentRegion, including padding.
        """
        content_region_data = b''
        for content in self.content_list:
            # If this isn't the first content, pad the whole region to 64 bytes before the next one.
            if content_region_data is not b'':
                content_region_data = _pad_bytes(content_region_data, 64)
            # Calculate padding after this content before the next one.
            padding_bytes = 0
            if (len(content) % 16) != 0:
                padding_bytes = 16 - (len(content) % 16)
            # Write content data, then the padding afterward if necessary.
            content_region_data += content
            if padding_bytes > 0:
                content_region_data += b'\x00' * padding_bytes
        # Calculate the size of the whole content region.
        content_region_size = 0
        for record in range(len(self.content_records)):
            if record is len(self.content_records) - 1:
                content_region_size += self.content_records[record].content_size
            else:
                content_region_size += _align_value(self.content_records[record].content_size, 64)
        return content_region_data, content_region_size

    def get_enc_content_by_index(self, index: int) -> bytes:
        """
        Gets an individual content from the content region based on the provided index, in encrypted form.

        Parameters
        ----------
        index : int
            The index of the content you want to get.

        Returns
        -------
        bytes
            The encrypted content listed in the content record.
        """
        content_enc = self.content_list[index]
        return content_enc

    def get_enc_content_by_cid(self, cid: int) -> bytes:
        """
        Gets an individual content from the content region based on the provided Content ID, in encrypted form.

        Parameters
        ----------
        cid : int
            The Content ID of the content you want to get. Expected to be in decimal form.

        Returns
        -------
        bytes
            The encrypted content listed in the content record.
        """
        # Find the index of the requested Content ID.
        content_index = None
        for content in self.content_records:
            if content.content_id == cid:
                content_index = content.index
        # If finding a matching ID was unsuccessful, that means that no content with that ID is in the TMD, so
        # return a Value Error.
        if content_index is None:
            raise ValueError("The Content ID requested does not exist in the TMD's content records.")
        # Call get_enc_content_by_index() using the index we just found.
        content_enc = self.get_enc_content_by_index(content_index)
        return content_enc

    def get_enc_contents(self) -> List[bytes]:
        """
        Gets a list of all encrypted contents from the content region.

        Returns
        -------
        List[bytes]
            A list containing all encrypted contents.
        """
        return self.content_list

    def get_content_by_index(self, index: int, title_key: bytes) -> bytes:
        """
        Gets an individual content from the content region based on the provided index, in decrypted form.

        Parameters
        ----------
        index : int
            The index of the content you want to get.
        title_key : bytes
            The Title Key for the title the content is from.

        Returns
        -------
        bytes
            The decrypted content listed in the content record.
        """
        # Load the encrypted content at the specified index and then decrypt it with the Title Key.
        content_enc = self.get_enc_content_by_index(index)
        content_dec = decrypt_content(content_enc, title_key, self.content_records[index].index,
                                      self.content_records[index].content_size)
        # Hash the decrypted content and ensure that the hash matches the one in its Content Record.
        # If it does not, then something has gone wrong in the decryption, and an error will be thrown.
        content_dec_hash = hashlib.sha1(content_dec).hexdigest()
        content_record_hash = str(self.content_records[index].content_hash.decode())
        # Compare the hash and throw a ValueError if the hash doesn't match.
        if content_dec_hash != content_record_hash:
            raise ValueError("Content hash did not match the expected hash in its record! The incorrect Title Key may "
                             "have been used!\n"
                             "Expected hash is: {}\n".format(content_record_hash) +
                             "Actual hash is: {}".format(content_dec_hash))
        return content_dec

    def get_content_by_cid(self, cid: int, title_key: bytes) -> bytes:
        """
        Gets an individual content from the content region based on the provided Content ID, in decrypted form.

        Parameters
        ----------
        cid : int
            The Content ID of the content you want to get. Expected to be in decimal form.
        title_key : bytes
            The Title Key for the title the content is from.

        Returns
        -------
        bytes
            The decrypted content listed in the content record.
        """
        # Find the index of the requested Content ID.
        content_index = None
        for content in self.content_records:
            if content.content_id == cid:
                content_index = content.index
        # If finding a matching ID was unsuccessful, that means that no content with that ID is in the TMD, so
        # return a Value Error.
        if content_index is None:
            raise ValueError("The Content ID requested does not exist in the TMD's content records.")
        # Call get_content_by_index() using the index we just found.
        content_dec = self.get_content_by_index(content_index, title_key)
        return content_dec

    def get_contents(self, title_key: bytes) -> List[bytes]:
        """
        Gets a list of all contents from the content region, in decrypted form.

        Parameters
        ----------
        title_key : bytes
            The Title Key for the title the content is from.

        Returns
        -------
        List[bytes]
            A list containing all decrypted contents.
        """
        dec_contents: List[bytes] = []
        # Iterate over every content, get the decrypted version of it, then add it to a list and return it.
        for content in range(self.num_contents):
            dec_contents.append(self.get_content_by_index(content, title_key))
        return dec_contents

    def set_enc_content(self, enc_content: bytes, cid: int, index: int, content_type: int, content_size: int,
                        content_hash: bytes) -> None:
        """
        Sets the provided index to a new content with the provided Content ID. Hashes and size of the content are
        set in the content record, with a new record being added if necessary.

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
        # Save the number of contents currently in the content region and records.
        num_contents = len(self.content_records)
        # Check if a record already exists for this index. If it doesn't, create it.
        if (index + 1) > num_contents:
            # Ensure that you aren't attempting to create a gap before appending.
            if (index + 1) > num_contents + 1:
                raise ValueError("You are trying to set the content at position " + str(index) + ", but no content "
                                 "exists at position " + str(index - 1) + "!")
            self.content_records.append(_ContentRecord(cid, index, content_type, content_size, content_hash))
        # If it does, reassign the values in it.
        else:
            self.content_records[index].content_id = cid
            self.content_records[index].content_type = content_type
            self.content_records[index].content_size = content_size
            self.content_records[index].content_hash = content_hash
        # Check if a content already occupies the provided index. If it does, reassign it to the new content, if it
        # doesn't, then append a new entry.
        if (index + 1) > num_contents:
            self.content_list.append(enc_content)
        else:
            self.content_list[index] = enc_content

    def set_content(self, dec_content: bytes, cid: int, index: int, content_type: int, title_key: bytes) -> None:
        """
        Sets the provided index to a new content with the provided Content ID. Hashes and size of the content are
        set in the content record, with a new record being added if necessary.

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
        title_key : bytes
            The Title Key that matches the new decrypted content.
        """
        # Store the size of the new content.
        dec_content_size = len(dec_content)
        # Calculate the hash of the new content.
        dec_content_hash = str.encode(hashlib.sha1(dec_content).hexdigest())
        # Encrypt the content using the provided Title Key and index.
        enc_content = encrypt_content(dec_content, title_key, index)
        # Pass values to set_enc_content()
        self.set_enc_content(enc_content, cid, index, content_type, dec_content_size, dec_content_hash)

    def load_enc_content(self, enc_content: bytes, index: int) -> None:
        """
        Loads the provided encrypted content into the content region at the specified index, with the assumption that
        it matches the record at that index. Not recommended for most use cases, use decrypted content and
        load_content() instead.

        Parameters
        ----------
        enc_content : bytes
            The encrypted content to load.
        index : int
            The content index to load the content at.
        """
        if (index + 1) > len(self.content_records) or len(self.content_records) == 0:
            raise IndexError("No content records have been loaded, or that index is higher than the highest entry in "
                             "the content records.")
        if (index + 1) > len(self.content_list):
            self.content_list.append(enc_content)
        else:
            self.content_list[index] = enc_content

    def load_content(self, dec_content: bytes, index: int, title_key: bytes) -> None:
        """
        Loads the provided decrypted content into the content region at the specified index, but first checks to make
        sure it matches the record at that index before loading. This content will be encrypted when loaded.

        Parameters
        ----------
        dec_content : bytes
            The decrypted content to load.
        index : int
            The content index to load the content at.
        title_key: bytes
            The Title Key that matches the decrypted content.
        """
        # Make sure that content records exist and that the provided index exists in them.
        if (index + 1) > len(self.content_records) or len(self.content_records) == 0:
            raise IndexError("No content records have been loaded, or that index is higher than the highest entry in "
                             "the content records.")
        # Check the hash of the content against the hash stored in the record to ensure it matches.
        content_hash = hashlib.sha1(dec_content).hexdigest()
        if content_hash != self.content_records[index].content_hash.decode():
            raise ValueError("The decrypted content provided does not match the record at the provided index. \n"
                             "Expected hash is: {}\n".format(self.content_records[index].content_hash.decode()) +
                             "Actual hash is: {}".format(content_hash))
        # If the hash matches, encrypt the content and set it where it belongs.
        enc_content = encrypt_content(dec_content, title_key, index)
        if (index + 1) > len(self.content_list):
            self.content_list.append(enc_content)
        else:
            self.content_list[index] = enc_content
