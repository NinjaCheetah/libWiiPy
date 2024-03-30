# "content.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Title for details about how titles are formatted

import io
import sys
import hashlib
from typing import List
from .types import ContentRecord
from .crypto import decrypt_content


class ContentRegion:
    """Creates a ContentRegion object to parse the continuous content region of a WAD.

    Parameters
    ----------
    content_region : bytes
        A bytes object containing the content region of a WAD file.
    content_records : list[ContentRecord]
        A list of ContentRecord objects detailing all contents contained in the region.
    """

    def __init__(self, content_region, content_records: List[ContentRecord]):
        self.content_region = content_region
        self.content_records = content_records
        self.content_region_size: int  # Size of the content region.
        self.num_contents: int  # Number of contents in the content region.
        self.content_start_offsets: List[int] = [0]  # The start offsets of each content in the content region.

        with io.BytesIO(content_region) as content_region_data:
            # Get the total size of the content region.
            self.content_region_size = sys.getsizeof(content_region_data)
            self.num_contents = len(self.content_records)
            # Calculate the offsets of each content in the content region.
            # Content is aligned to 16 bytes, however a new content won't start until the next multiple of 64 bytes.
            # Because of this, we need to add bytes to the next 64 byte offset if the previous content wasn't that long.
            for content in self.content_records[:-1]:
                start_offset = content.content_size + self.content_start_offsets[-1]
                if (content.content_size % 64) != 0:
                    start_offset += 64 - (content.content_size % 64)
                self.content_start_offsets.append(start_offset)

    def get_enc_content_by_index(self, index: int) -> bytes:
        """Gets an individual content from the content region based on the provided index, in encrypted form.

        Parameters
        ----------
        index : int
            The index of the content you want to get.

        Returns
        -------
        bytes
            The encrypted content listed in the content record.
        """
        with io.BytesIO(self.content_region) as content_region_data:
            # Seek to the start of the requested content based on the list of offsets.
            content_region_data.seek(self.content_start_offsets[index])
            # Calculate the number of bytes we need to read by adding bytes up the nearest multiple of 16 if needed.
            bytes_to_read = self.content_records[index].content_size
            if (bytes_to_read % 16) != 0:
                bytes_to_read += 16 - (bytes_to_read % 16)
            # Read the file based on the size of the content in the associated record.
            content_enc = content_region_data.read(bytes_to_read)
            return content_enc

    def get_enc_content_by_cid(self, cid: int) -> bytes:
        """Gets an individual content from the content region based on the provided Content ID, in encrypted form.

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
        """Gets a list of all encrypted contents from the content region.

        Returns
        -------
        List[bytes]
            A list containing all encrypted contents.
        """
        enc_contents: List[bytes] = []
        # Iterate over every content and add it to a list, then return it.
        for content in range(self.num_contents):
            enc_contents.append(self.get_enc_content_by_index(content))
        return enc_contents

    def get_content_by_index(self, index: int, title_key: bytes) -> bytes:
        """Gets an individual content from the content region based on the provided index, in decrypted form.

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
        content_dec_hash = hashlib.sha1(content_dec)
        content_record_hash = str(self.content_records[index].content_hash.decode())
        # Compare the hash and throw a ValueError if the hash doesn't match.
        if content_dec_hash.hexdigest() != content_record_hash:
            raise ValueError("Content hash did not match the expected hash in its record! The incorrect Title Key may "
                             "have been used!.\n"
                             "Expected hash is: {}\n".format(content_record_hash) +
                             "Actual hash is: {}".format(content_dec_hash.hexdigest()))
        return content_dec

    def get_content_by_cid(self, cid: int, title_key: bytes) -> bytes:
        """Gets an individual content from the content region based on the provided Content ID, in decrypted form.

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
        """Gets a list of all contents from the content region, in decrypted form.

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
