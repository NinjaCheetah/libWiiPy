# "nand/emunand.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# Code for handling setting up and modifying a Wii EmuNAND.

import os
import pathlib
import shutil
from dataclasses import dataclass as _dataclass
from typing import Callable, List

from ..title.ticket import Ticket
from ..title.title import Title
from ..title.tmd import TMD
from ..title.content import SharedContentMap as _SharedContentMap
from .sys import UidSys as _UidSys


class EmuNAND:
    """
    An EmuNAND object that allows for creating and modifying Wii EmuNANDs. Requires the path to the root of the
    EmuNAND, and can optionally take in a callback function to send logs to.

    Parameters
    ----------
    emunand_root : str, pathlib.Path
        The path to the EmuNAND root directory.
    callback : function
        A callback function to send EmuNAND logs to.

    Attributes
    ----------
    emunand_root : pathlib.Path
        The path to the EmuNAND root directory.
    """
    def __init__(self, emunand_root: str | pathlib.Path, callback: Callable | None = None):
        self.emunand_root = pathlib.Path(emunand_root)
        self.log = callback if callback is not None else lambda x: None

        self.import_dir = self.emunand_root.joinpath("import")
        self.meta_dir = self.emunand_root.joinpath("meta")
        self.shared1_dir = self.emunand_root.joinpath("shared1")
        self.shared2_dir = self.emunand_root.joinpath("shared2")
        self.sys_dir = self.emunand_root.joinpath("sys")
        self.ticket_dir = self.emunand_root.joinpath("ticket")
        self.title_dir = self.emunand_root.joinpath("title")
        self.tmp_dir = self.emunand_root.joinpath("tmp")
        self.wfs_dir = self.emunand_root.joinpath("wfs")

        self.import_dir.mkdir(exist_ok=True)
        self.meta_dir.mkdir(exist_ok=True)
        self.shared1_dir.mkdir(exist_ok=True)
        self.shared2_dir.mkdir(exist_ok=True)
        self.sys_dir.mkdir(exist_ok=True)
        self.ticket_dir.mkdir(exist_ok=True)
        self.title_dir.mkdir(exist_ok=True)
        self.tmp_dir.mkdir(exist_ok=True)
        self.wfs_dir.mkdir(exist_ok=True)

    def install_title(self, title: Title, skip_hash=False) -> None:
        """
        Install the provided Title object to the EmuNAND. This mimics a real WAD installation done by ES.

        This will create some system files required if they do not exist, but note that this alone is not enough for
        a working EmuNAND, other than for Dolphin which can fill in the gaps.

        Parameters
        ----------
        title : libWiiPy.title.Title
            The loaded Title object to install.
        skip_hash : bool, optional
            Skip the hash check and install the title regardless of its hashes. Defaults to false.
        """
        self.log(f"[PROGRESS] Starting install of title with Title ID {title.tmd.title_id}...")
        # Save the upper and lower portions of the Title ID, because these are used as target install directories.
        tid_upper = title.tmd.title_id[:8]
        tid_lower = title.tmd.title_id[8:]

        # Tickets are installed as <tid_lower>.tik in /ticket/<tid_upper>/
        ticket_dir = self.ticket_dir.joinpath(tid_upper)
        self.log(f"[PROGRESS] Installing ticket to \"{ticket_dir}\"...")
        ticket_dir.mkdir(exist_ok=True)
        ticket_dir.joinpath(f"{tid_lower}.tik").write_bytes(title.ticket.dump())

        # The TMD and normal contents are installed to /title/<tid_upper>/<tid_lower>/content/, with the tmd being named
        # title.tmd and the contents being named <cid>.app.
        title_dir = self.title_dir.joinpath(tid_upper)
        title_dir.mkdir(exist_ok=True)
        title_dir = title_dir.joinpath(tid_lower)
        title_dir.mkdir(exist_ok=True)
        content_dir = title_dir.joinpath("content")
        self.log(f"[PROGRESS] Installing TMD to \"{content_dir}\"...")
        if content_dir.exists():
            shutil.rmtree(content_dir)  # Clear the content directory so old contents aren't left behind.
        content_dir.mkdir(exist_ok=True)
        content_dir.joinpath("title.tmd").write_bytes(title.tmd.dump())
        self.log(f"[PROGRESS] Installing content to \"{content_dir}\"...")
        if skip_hash:
            self.log("[WARN] Not checking content hashes! Content validity will not be verified.")
        for content_file in range(0, title.tmd.num_contents):
            if title.tmd.content_records[content_file].content_type == 1:
                content_file_name = f"{title.tmd.content_records[content_file].content_id:08X}".lower()
                self.log(f"[PROGRESS] Installing content \"{content_file_name}.app\" to \"{content_dir}\"... ")
                content_dir.joinpath(f"{content_file_name}.app").write_bytes(
                    title.get_content_by_index(content_file, skip_hash=skip_hash))
        title_dir.joinpath("data").mkdir(exist_ok=True)  # Empty directory used for save data for the title.

        # Shared contents need to be installed to /shared1/, with incremental names determined by /shared1/content.map.
        content_map_path = self.shared1_dir.joinpath("content.map")
        self.log(f"[PROGRESS] Installing shared content to \"{self.shared1_dir}\"...")
        content_map = _SharedContentMap()
        existing_hashes = []
        if content_map_path.exists():
            content_map.load(content_map_path.read_bytes())
            for record in content_map.shared_records:
                existing_hashes.append(record.content_hash)
        for content_file in range(0, title.tmd.num_contents):
            if title.tmd.content_records[content_file].content_type == 32769:
                if title.tmd.content_records[content_file].content_hash not in existing_hashes:
                    self.log(f"[PROGRESS] Adding shared content hash to content.map...")
                    content_file_name = content_map.add_content(title.tmd.content_records[content_file].content_hash)
                    self.log(f"[PROGRESS] Installing shared content \"{content_file_name}.app\" to "
                             f"\"{self.shared1_dir}\"...")
                    self.shared1_dir.joinpath(f"{content_file_name}.app").write_bytes(
                        title.get_content_by_index(content_file, skip_hash=skip_hash))
        self.shared1_dir.joinpath("content.map").write_bytes(content_map.dump())

        # The "footer" or meta file is installed as title.met in /meta/<tid_upper>/<tid_lower>/. Only write this if meta
        # is not nothing.
        meta_data = title.wad.get_meta_data()
        if meta_data != b'':
            meta_dir = self.meta_dir.joinpath(tid_upper)
            meta_dir.mkdir(exist_ok=True)
            meta_dir = meta_dir.joinpath(tid_lower)
            self.log(f"[PROGRESS] Installing meta data to \"{meta_dir}\"...")
            meta_dir.mkdir(exist_ok=True)
            meta_dir.joinpath("title.met").write_bytes(title.wad.get_meta_data())

        # Ensure we have a uid.sys file created.
        uid_sys_path = self.sys_dir.joinpath("uid.sys")
        uid_sys = _UidSys()
        if not uid_sys_path.exists():
            self.log("[WARN] uid.sys does not exist! Creating it with the default entry.")
            uid_sys.create()
        else:
            uid_sys.load(uid_sys_path.read_bytes())
        self.log("[PROGRESS] Adding title to uid.sys and assigning a new UID...")
        uid_sys.add(title.tmd.title_id)
        uid_sys_path.write_bytes(uid_sys.dump())

        # Check for a cert.sys and initialize it using the certs in the WAD if it doesn't exist.
        cert_sys_path = self.sys_dir.joinpath("cert.sys")
        if not cert_sys_path.exists():
            self.log("[WARN] cert.sys does not exist! Creating it using certs from the installed title...")
            cert_sys_data = b''
            cert_sys_data += title.cert_chain.ticket_cert.dump()
            cert_sys_data += title.cert_chain.ca_cert.dump()
            cert_sys_data += title.cert_chain.tmd_cert.dump()
            cert_sys_path.write_bytes(cert_sys_data)

        self.log("[PROGRESS] Completed title installation.")

    def uninstall_title(self, tid: str) -> None:
        """
        Uninstall the Title with the specified Title ID from the EmuNAND. This will leave shared contents unmodified.

        Parameters
        ----------
        tid : str
            The Title ID of the Title to uninstall.
        """
        # Save the upper and lower portions of the Title ID, because these are used as target install directories.
        tid_upper = tid[:8]
        tid_lower = tid[8:]

        if not self.title_dir.joinpath(tid_upper).joinpath(tid_lower).exists():
            raise ValueError(f"Title with Title ID {tid} does not appear to be installed!")

        # Begin by removing the Ticket, which is installed to /ticket/<tid_upper>/<tid_lower>.tik
        if self.ticket_dir.joinpath(tid_upper).joinpath(tid_lower + ".tik").exists():
            os.remove(self.ticket_dir.joinpath(tid_upper).joinpath(tid_lower + ".tik"))

        # The TMD and contents are stored in /title/<tid_upper>/<tid_lower>/. Remove the TMD and all contents, but don't
        # delete the entire directory if anything exists in data.
        title_dir = self.title_dir.joinpath(tid_upper).joinpath(tid_lower)
        if not title_dir.joinpath("data").exists():
            shutil.rmtree(title_dir)
        elif title_dir.joinpath("data").exists() and not os.listdir(title_dir.joinpath("data")):
            shutil.rmtree(title_dir)
        else:
            # There are files in data, so we only want to delete the content directory.
            shutil.rmtree(title_dir.joinpath("content"))

        # On the off chance this title has a meta entry, delete that too.
        if self.meta_dir.joinpath(tid_upper).joinpath(tid_lower).joinpath("title.met").exists():
            shutil.rmtree(self.meta_dir.joinpath(tid_upper).joinpath(tid_lower))

    @_dataclass
    class InstalledTitles:
        """
        An InstalledTitles object that is used to track a title type and any titles that belong to that type that are
        installed to an EmuNAND.

        :ivar type: The type (Title ID high) of the installed titles.
        :ivar titles: The Title ID low of each installed title.
        """
        type: str
        titles: List[str]

    def get_installed_titles(self) -> List[InstalledTitles]:
        """
        Scans for installed titles and returns a list of InstalledTitles objects, which each contain a title type
        (Title ID high) and a list of Title ID lows that are installed under it.

        Returns
        -------
        List[InstalledTitles]
            The titles installed to the EmuNAND.
        """
        # Scan for TID highs present.
        tid_highs = [d for d in self.title_dir.iterdir() if d.is_dir()]
        # Iterate through each one, verify that every TID low directory contains a TMD, and then add it to the list.
        installed_titles = []
        for high in tid_highs:
            tid_lows = [d for d in high.iterdir() if d.is_dir()]
            valid_lows = []
            for low in tid_lows:
                if low.joinpath("content", "title.tmd").exists():
                    valid_lows.append(low.name.upper())
            installed_titles.append(self.InstalledTitles(high.name.upper(), valid_lows))
        return installed_titles

    def get_title_tmd(self, tid: str) -> TMD:
        """
        Gets the TMD for a title installed to the EmuNAND, and returns it as a TMD objects. Returns an error if the
        TMD for the specified Title ID does not exist.

        Parameters
        ----------
        tid : str
            The Title ID of the Title to get the TMD for.

        Returns
        -------
        TMD
            The TMD for the Title.
        """
        # Validate the TID, then build a path to the TMD file to verify that it exists.
        if len(tid) != 16:
            raise ValueError(f"Title ID \"{tid}\" is not a valid!")
        tid_high = tid[:8].lower()
        tid_low = tid[8:].lower()
        tmd_path = self.title_dir.joinpath(tid_high, tid_low, "content", "title.tmd")
        if not tmd_path.exists():
            raise FileNotFoundError(f"Title with Title ID {tid} does not appear to be installed!")
        tmd = TMD()
        tmd.load(tmd_path.read_bytes())
        return tmd

    def get_title_ticket(self, tid: str) -> Ticket:
        """
        Gets the Ticket for a title installed to the EmuNAND, and returns it as a Ticket object. Returns an error if
        the Ticket for the specified Title ID does not exist.

        Parameters
        ----------
        tid : str
            The Title ID of the Title to get the Ticket for.

        Returns
        -------
        Ticket
            The Ticket for the Title.
        """
        # Validate the TID, then build a path to the Ticket files to verify that it exists.
        if len(tid) != 16:
            raise ValueError(f"Title ID \"{tid}\" is not a valid!")
        tid_high = tid[:8].lower()
        tid_low = tid[8:].lower()
        ticket_path = self.ticket_dir.joinpath(tid_high, f"{tid_low}.tik")
        if not ticket_path.exists():
            raise FileNotFoundError(f"No Ticket exists for the title with Title ID {tid}!")
        ticket = Ticket()
        ticket.load(ticket_path.read_bytes())
        return ticket
