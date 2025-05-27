# "nand/sys.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki//sys/uid.sys for information about uid.sys.

import io
import binascii
from typing import List
from dataclasses import dataclass as _dataclass


@_dataclass
class _UidSysEntry:
    """
    A _UidSysEntry object used to store an entry in uid.sys. Private class used by the sys module.

    Attributes
    ----------
    title_id : str
        The Title ID of the title this entry corresponds with.
    uid : int
        The UID assigned to the title this entry corresponds with.
    """
    title_id: str
    uid: int


class UidSys:
    """
    A UidSys object to parse and edit the uid.sys file stored in /sys/ on the Wii's NAND. This file is used to track all
    the titles that have been launched on a console.

    Attributes
    ----------
    uid_entries : List[_UidSysEntry]
        The entries stored in the uid.sys file.
    """

    def __init__(self) -> None:
        self.uid_entries: List[_UidSysEntry] = []

    def load(self, uid_sys: bytes) -> None:
        """
        Loads the raw data of uid.sys and parses it into a list of entries.

        Parameters
        ----------
        uid_sys : bytes
            The data of a uid.sys file.
        """
        # Sanity check to ensure the length is divisible by 12 bytes. If it isn't, then it is malformed.
        if (len(uid_sys) % 12) != 0:
            raise ValueError("The provided uid.sys appears to be corrupted!")
        entry_count = len(uid_sys) // 12
        with io.BytesIO(uid_sys) as uid_data:
            for i in range(entry_count):
                title_id = binascii.hexlify(uid_data.read(8)).decode()
                uid_data.seek(uid_data.tell() + 2)
                uid = int.from_bytes(uid_data.read(2))
                self.uid_entries.append(_UidSysEntry(title_id, uid))

    def dump(self) -> bytes:
        """
        Dumps the UidSys object back into a uid.sys file.

        Returns
        -------
        bytes
            The raw data of the uid.sys file.
        """
        uid_data = b''
        for record in self.uid_entries:
            uid_data += binascii.unhexlify(record.title_id.encode())
            uid_data += b'\x00' * 2
            uid_data += int.to_bytes(record.uid, 2)
        return uid_data

    def add(self, title_id: str | bytes) -> int:
        """
        Adds a new Title ID to the uid.sys file and returns the UID assigned to that title. The new entry will only
        be added if the provided Title ID doesn't already have an assigned UID.

        Parameters
        ----------
        title_id : str, bytes
            The Title ID to add.

        Returns
        -------
        int
            The UID assigned to the new Title ID.
        """
        if type(title_id) is bytes:
            # This catches the format b'\x00\x00\x00\x01\x00\x00\x00\x02'
            if len(title_id) == 8:
                title_id_converted = binascii.hexlify(title_id).decode()
            # If it isn't one of those lengths, it cannot possibly be valid, so reject it.
            else:
                raise ValueError("Title ID is not valid!")
        # Allow for a string like "0000000100000002"
        elif type(title_id) is str:
            if len(title_id) != 16:
                raise ValueError("Title ID is not valid!")
            title_id_converted = title_id
        else:
            raise TypeError("Title ID type is not valid! It must be either type str or bytes.")
        # Ensure this TID hasn't already been assigned a UID. If it has, just exit early and return the UID.
        if self.uid_entries.count != 0:
            for entry in self.uid_entries:
                if entry.title_id == title_id_converted:
                    return entry.uid
        # Generate the new UID by incrementing the current highest UID by 1.
        try:
            new_uid = self.uid_entries[-1].uid + 1
        except IndexError:
            new_uid = 4096
        self.uid_entries.append(_UidSysEntry(title_id_converted, new_uid))
        return new_uid

    def create(self) -> None:
        """
        Creates a new uid.sys file and initializes it with the standard first entry of 1-2 with UID 4096. This allows
        for setting up a uid.sys file without having to load an existing one.
        """
        if len(self.uid_entries) != 0:
            raise Exception("A uid.sys file appears to already exist!")
        self.add("0000000100000002")
