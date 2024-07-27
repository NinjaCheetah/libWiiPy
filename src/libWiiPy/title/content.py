# "title/content.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Title for details about how titles are formatted
import binascii
import io
import hashlib
from typing import List
from dataclasses import dataclass as _dataclass
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
            if content_region_data != b'':
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

        This uses the content index, which is the value tied to each content and used as the IV for encryption, rather
        than the literal index in the array of content, because sometimes the contents end up out of order in a WAD
        while still retaining the original indices.

        Parameters
        ----------
        index : int
            The index of the content you want to get.

        Returns
        -------
        bytes
            The encrypted content listed in the content record.
        """
        # Get a list of the current content indices, so we can make sure the target one exists. Doing it this way
        # ensures we can find the target, even if the highest content index is greater than the highest literal index.
        current_indices = []
        for record in self.content_records:
            current_indices.append(record.index)
        if index not in current_indices:
            raise ValueError("You are trying to get the content at index " + str(index) + ", but no content with that "
                             "index exists!")
        # This is the literal index in the list of content that we're going to get.
        target_index = current_indices.index(index)
        content_enc = self.content_list[target_index]
        return content_enc

    def get_enc_content_by_cid(self, cid: int) -> bytes:
        """
        Gets an individual content from the content region based on the provided Content ID, in encrypted form.

        Parameters
        ----------
        cid : int
            The Content ID of the content you want to get. Expected to be in decimal form, not hex.

        Returns
        -------
        bytes
            The encrypted content listed in the content record.
        """
        # Get a list of the current Content IDs, so we can make sure the target one exists.
        content_ids = []
        for record in self.content_records:
            content_ids.append(record.content_id)
        if cid not in content_ids:
            raise ValueError("You are trying to get a content with Content ID " + str(cid) + ", but no content with "
                             "that ID exists!")
        # Get the content index associated with the CID we now know exists.
        target_index = content_ids.index(cid)
        content_index = self.content_records[target_index].index
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

    def get_content_by_index(self, index: int, title_key: bytes, skip_hash=False) -> bytes:
        """
        Gets an individual content from the content region based on the provided index, in decrypted form.

        This uses the content index, which is the value tied to each content and used as the IV for encryption, rather
        than the literal index in the array of content, because sometimes the contents end up out of order in a WAD
        while still retaining the original indices.

        Parameters
        ----------
        index : int
            The content index of the content you want to get.
        title_key : bytes
            The Title Key for the title the content is from.
        skip_hash : bool, optional
            Skip the hash check and return the content regardless of its hash. Defaults to false.

        Returns
        -------
        bytes
            The decrypted content listed in the content record.
        """
        # Get a list of the current content indices, so we can make sure the target one exists. Doing it this way
        # ensures we can find the target, even if the highest content index is greater than the highest literal index.
        current_indices = []
        for record in self.content_records:
            current_indices.append(record.index)
        # This is the literal index in the list of content that we're going to get.
        target_index = current_indices.index(index)
        content_enc = self.get_enc_content_by_index(index)
        content_dec = decrypt_content(content_enc, title_key, index, self.content_records[target_index].content_size)
        # Hash the decrypted content and ensure that the hash matches the one in its Content Record.
        # If it does not, then something has gone wrong in the decryption, and an error will be thrown.
        content_dec_hash = hashlib.sha1(content_dec).hexdigest()
        content_record_hash = str(self.content_records[target_index].content_hash.decode())
        # Compare the hash and throw a ValueError if the hash doesn't match.
        if content_dec_hash != content_record_hash:
            if skip_hash:
                print("Ignoring hash mismatch for content index " + str(index))
            else:
                raise ValueError("Content hash did not match the expected hash in its record! The incorrect Title Key "
                                 "may have been used!\n"
                                 "Expected hash is: {}\n".format(content_record_hash) +
                                 "Actual hash is: {}".format(content_dec_hash))
        return content_dec

    def get_content_by_cid(self, cid: int, title_key: bytes, skip_hash=False) -> bytes:
        """
        Gets an individual content from the content region based on the provided Content ID, in decrypted form.

        Parameters
        ----------
        cid : int
            The Content ID of the content you want to get. Expected to be in decimal form, not hex.
        title_key : bytes
            The Title Key for the title the content is from.
        skip_hash : bool, optional
            Skip the hash check and return the content regardless of its hash. Defaults to false.

        Returns
        -------
        bytes
            The decrypted content listed in the content record.
        """
        # Get a list of the current Content IDs, so we can make sure the target one exists.
        content_ids = []
        for record in self.content_records:
            content_ids.append(record.content_id)
        if cid not in content_ids:
            raise ValueError("You are trying to get a content with Content ID " + str(cid) + ", but no content with "
                             "that ID exists!")
        # Get the content index associated with the CID we now know exists.
        target_index = content_ids.index(cid)
        content_index = self.content_records[target_index].index
        content_dec = self.get_content_by_index(content_index, title_key, skip_hash)
        return content_dec

    def get_contents(self, title_key: bytes, skip_hash=False) -> List[bytes]:
        """
        Gets a list of all contents from the content region, in decrypted form.

        Parameters
        ----------
        title_key : bytes
            The Title Key for the title the content is from.
        skip_hash : bool, optional
            Skip the hash check and return the content regardless of its hash. Defaults to false.

        Returns
        -------
        List[bytes]
            A list containing all decrypted contents.
        """
        dec_contents: List[bytes] = []
        # Iterate over every content, get the decrypted version of it, then add it to a list and return it.
        for content in range(self.num_contents):
            dec_contents.append(self.get_content_by_index(content, title_key, skip_hash))
        return dec_contents

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
            The index to place the new content at.
        content_type : int
            The type of the new content.
        content_size : int
            The size of the new encrypted content when decrypted.
        content_hash : bytes
            The hash of the new encrypted content when decrypted.
        """
        # Check to make sure this isn't reusing an already existing Content ID or index first.
        for record in self.content_records:
            if record.content_id == cid:
                raise ValueError("Content with a Content ID of " + str(cid) + " already exists!")
            elif record.index == index:
                raise ValueError("Content with an index of " + str(index) + " already exists!")
        # If we're good, then append all the data and create a new ContentRecord().
        self.content_list.append(enc_content)
        self.content_records.append(_ContentRecord(cid, index, content_type, content_size, content_hash))

    def add_content(self, dec_content: bytes, cid: int, index: int, content_type: int, title_key: bytes) -> None:
        """
        Adds a new decrypted content to the ContentRegion, and adds the provided Content ID, index, content type,
        content size, and content hash to a new record in the ContentRecord list.

        This first gets the content hash and size from the provided data, and then encrypts the content with the
        provided Title Key before adding it to the ContentRegion.

        Parameters
        ----------
        dec_content : bytes
            The new decrypted content to add.
        cid : int
            The Content ID to assign the new content in the content record.
        index : int
            The index to place the new content at.
        content_type : int
            The type of the new content.
        title_key : bytes
            The Title Key that matches the other content in the ContentRegion.
        """
        content_size = len(dec_content)
        content_hash = str.encode(hashlib.sha1(dec_content).hexdigest())
        enc_content = encrypt_content(dec_content, title_key, index)
        self.add_enc_content(enc_content, cid, index, content_type, content_size, content_hash)

    def set_enc_content(self, enc_content: bytes, index: int, content_size: int, content_hash: bytes, cid: int = None,
                        content_type: int = None) -> None:
        """
        Sets the content at the provided content index to the provided new encrypted content. The provided hash and
        content size are set in the corresponding content record. A new Content ID or content type can also be
        specified, but if it isn't than the current values are preserved.

        This uses the content index, which is the value tied to each content and used as the IV for encryption, rather
        than the literal index in the array of content, because sometimes the contents end up out of order in a WAD
        while still retaining the original indices.

        Parameters
        ----------
        enc_content : bytes
            The new encrypted content to set.
        index : int
            The target content index to set the new content at.
        content_size : int
            The size of the new encrypted content when decrypted.
        content_hash : bytes
            The hash of the new encrypted content when decrypted.
        cid : int, optional
            The Content ID to assign the new content in the content record. Current value will be preserved if not set.
        content_type : int, optional
            The type of the new content. Current value will be preserved if not set.
        """
        # Get a list of the current content indices, so we can make sure the target one exists. Doing it this way
        # ensures we can find the target, even if the highest content index is greater than the highest literal index.
        current_indices = []
        for record in self.content_records:
            current_indices.append(record.index)
        if index not in current_indices:
            raise ValueError("You are trying to set the content at index " + str(index) + ", but no content with that "
                             "index currently exists!")
        # This is the literal index in the list of content/content records that we're going to change.
        target_index = current_indices.index(index)
        # Reassign the values, but only set the optional ones if they were passed.
        self.content_records[target_index].content_size = content_size
        self.content_records[target_index].content_hash = content_hash
        if cid is not None:
            self.content_records[target_index].content_id = cid
        if content_type is not None:
            self.content_records[target_index].content_type = content_type
        # Add blank entries to the list to ensure that its length matches the length of the content record list.
        while len(self.content_list) < len(self.content_records):
            self.content_list.append(b'')
        self.content_list[target_index] = enc_content

    def set_content(self, dec_content: bytes, index: int, title_key: bytes, cid: int = None,
                    content_type: int = None) -> None:
        """
        Sets the content at the provided content index to the provided new decrypted content. The hash and content size
        of this content will be generated and then set in the corresponding content record. A new Content ID or content
        type can also be specified, but if it isn't than the current values are preserved.

        The provided Title Key is used to encrypt the content so that it can be set in the ContentRegion.

        Parameters
        ----------
        dec_content : bytes
            The new decrypted content to set.
        index : int
            The index to place the new content at.
        title_key : bytes
            The Title Key that matches the new decrypted content.
        cid : int
            The Content ID to assign the new content in the content record.
        content_type : int
            The type of the new content.
        """
        # Store the size of the new content.
        content_size = len(dec_content)
        # Calculate the hash of the new content.
        content_hash = str.encode(hashlib.sha1(dec_content).hexdigest())
        # Encrypt the content using the provided Title Key and index.
        enc_content = encrypt_content(dec_content, title_key, index)
        # Pass values to set_enc_content()
        self.set_enc_content(enc_content, index, content_size, content_hash, cid, content_type)

    def load_enc_content(self, enc_content: bytes, index: int) -> None:
        """
        Loads the provided encrypted content into the content region at the specified index, with the assumption that
        it matches the record at that index. Not recommended for most use cases, use decrypted content and
        load_content() instead.

        This uses the content index, which is the value tied to each content and used as the IV for encryption, rather
        than the literal index in the array of content, because sometimes the contents end up out of order in a WAD
        while still retaining the original indices.

        Parameters
        ----------
        enc_content : bytes
            The encrypted content to load.
        index : int
            The content index to load the content at.
        """
        # Get a list of the current content indices, so we can make sure the target one exists. Doing it this way
        # ensures we can find the target, even if the highest content index is greater than the highest literal index.
        current_indices = []
        for record in self.content_records:
            current_indices.append(record.index)
        if index not in current_indices:
            raise ValueError("You are trying to load the content at index " + str(index) + ", but no content with that "
                             "index currently exists! Make sure the correct content records have been loaded.")
        # Add blank entries to the list to ensure that its length matches the length of the content record list.
        while len(self.content_list) < len(self.content_records):
            self.content_list.append(b'')
        # This is the literal index in the list of content/content records that we're going to change.
        target_index = current_indices.index(index)
        self.content_list[target_index] = enc_content

    def load_content(self, dec_content: bytes, index: int, title_key: bytes) -> None:
        """
        Loads the provided decrypted content into the ContentRegion at the specified index, but first checks to make
        sure that it matches the corresponding record. This content will then be encrypted using the provided Title Key
        before being loaded.

        This uses the content index, which is the value tied to each content and used as the IV for encryption, rather
        than the literal index in the array of content, because sometimes the contents end up out of order in a WAD
        while still retaining the original indices.

        Parameters
        ----------
        dec_content : bytes
            The decrypted content to load.
        index : int
            The content index to load the content at.
        title_key: bytes
            The Title Key that matches the decrypted content.
        """
        # Get a list of the current content indices, so we can make sure the target one exists. Doing it this way
        # ensures we can find the target, even if the highest content index is greater than the highest literal index.
        current_indices = []
        for record in self.content_records:
            current_indices.append(record.index)
        if index not in current_indices:
            raise ValueError("You are trying to load the content at index " + str(index) + ", but no content with that "
                             "index currently exists! Make sure the correct content records have been loaded.")
        # This is the literal index in the list of content/content records that we're going to change.
        target_index = current_indices.index(index)
        # Check the hash of the content against the hash stored in the record to ensure it matches.
        content_hash = hashlib.sha1(dec_content).hexdigest()
        if content_hash != self.content_records[target_index].content_hash.decode():
            raise ValueError("The decrypted content provided does not match the record at the provided index. \n"
                             "Expected hash is: {}\n".format(self.content_records[index].content_hash.decode()) +
                             "Actual hash is: {}".format(content_hash))
        # Add blank entries to the list to ensure that its length matches the length of the content record list.
        while len(self.content_list) < len(self.content_records):
            self.content_list.append(b'')
        # If the hash matches, encrypt the content and set it where it belongs.
        # This uses the index from the content records instead of just the index given, because there are some strange
        # circumstances where the actual index in the array and the assigned content index don't match up, and this
        # needs to accommodate that. Seems to only apply to custom WADs ? (Like cIOS WADs?)
        enc_content = encrypt_content(dec_content, title_key, index)
        self.content_list[target_index] = enc_content


@_dataclass
class _SharedContentRecord:
    """
    A _SharedContentRecord object used to store the data of a specific content stored in /shared1/. Private class used
    by the content module.

    Attributes
    ----------
    shared_id : str
        The incremental ID used to store the shared content.
    content_hash : bytes
        The SHA-1 hash of the shared content.
    """
    shared_id: str
    content_hash: bytes


class SharedContentMap:
    """
    A SharedContentMap object to parse and edit the content.map file stored in /shared1/ on the Wii's NAND. This file is
    used to keep track of all shared contents installed on the console.

    Attributes
    ----------
    shared_records : List[_SharedContentRecord]
        The shared content records stored in content.map.
    """

    def __init__(self):
        self.shared_records: List[_SharedContentRecord] = []

    def load(self, content_map: bytes) -> None:
        """
        Loads the raw content map and parses the records in it.

        Parameters
        ----------
        content_map : bytes
            The data of a content.map file.
        """
        # Sanity check to ensure the length is divisible by 28 bytes. If it isn't, then it is malformed.
        if (len(content_map) % 28) != 0:
            raise ValueError("The provided content map appears to be corrupted!")
        entry_count = len(content_map) // 28
        with io.BytesIO(content_map) as map_data:
            for i in range(entry_count):
                shared_id = str(map_data.read(8).decode())
                content_hash = binascii.hexlify(map_data.read(20))
                self.shared_records.append(_SharedContentRecord(shared_id, content_hash))

    def dump(self) -> bytes:
        """
        Dumps the SharedContentMap object back into a content.map file.

        Returns
        -------
        bytes
            The raw data of the content.map file.
        """
        map_data = b''
        for record in self.shared_records:
            map_data += record.shared_id.encode()
            map_data += binascii.unhexlify(record.content_hash)
        return map_data

    def add_content(self, content_hash: str | bytes) -> str:
        """
        Adds a new shared content SHA-1 hash to the content map and returns the file name assigned to that hash.

        Parameters
        ----------
        content_hash : str, bytes
            The SHA-1 hash of the new shared content.

        Returns
        -------
        str
            The filename assigned to the provided content hash.
        """
        content_hash_converted = b''
        if type(content_hash) is bytes:
            # This catches the format b'GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG'
            if len(content_hash) == 40:
                pass
            # This catches the format
            # b'\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG\xGG'
            elif len(content_hash) == 20:
                content_hash_converted = binascii.hexlify(content_hash)
            # If it isn't one of those lengths, it cannot possibly be valid, so reject it.
            else:
                raise ValueError("SHA-1 hash is not valid!")
        # Allow for a string like "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
        elif type(content_hash) is str:
            content_hash_converted = binascii.unhexlify(content_hash)
        # If the hash isn't bytes or a string, it isn't valid and is rejected.
        else:
            raise TypeError("SHA-1 hash type is not valid! It must be either type str or bytes.")

        # Generate the file name for the new shared content by incrementing the highest name by 1. Thank you, Nintendo,
        # for not just storing these as integers like you did EVERYWHERE else.
        try:
            maximum_index = int(self.shared_records[-1].shared_id, 16)
            new_index = f"{maximum_index + 1:08X}"
        except IndexError:
            new_index = f"{0:08X}"
        self.shared_records.append(_SharedContentRecord(new_index, content_hash_converted))
        return new_index
