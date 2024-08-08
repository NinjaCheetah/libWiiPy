# "title/emunand.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# Code for handling setting up and modifying a Wii EmuNAND.

import os
import pathlib
import shutil
from .title import Title
from .content import SharedContentMap as _SharedContentMap
from .sys import UidSys as _UidSys


class EmuNAND:
    """
    An EmuNAND object that allows for creating and modifying Wii EmuNANDs. Requires the path to the root of the
    EmuNAND, and can optionally take in a callback function to send logs to.

    Parameters
    emunand_root : str
        The path to the EmuNAND root directory.
    callback : function
        A callback function to send EmuNAND logs to.
    """
    def __init__(self, emunand_root: str, callback: callable = None):
        self.emunand_root = pathlib.Path(emunand_root)
        self.log = callback if callback is not None else None

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
        # Save the upper and lower portions of the Title ID, because these are used as target install directories.
        tid_upper = title.tmd.title_id[:8]
        tid_lower = title.tmd.title_id[8:]

        # Tickets are installed as <tid_lower>.tik in /ticket/<tid_upper>/
        ticket_dir = self.ticket_dir.joinpath(tid_upper)
        ticket_dir.mkdir(exist_ok=True)
        open(ticket_dir.joinpath(tid_lower + ".tik"), "wb").write(title.wad.get_ticket_data())

        # The TMD and normal contents are installed to /title/<tid_upper>/<tid_lower>/content/, with the tmd being named
        # title.tmd and the contents being named <cid>.app.
        title_dir = self.title_dir.joinpath(tid_upper)
        title_dir.mkdir(exist_ok=True)
        title_dir = title_dir.joinpath(tid_lower)
        title_dir.mkdir(exist_ok=True)
        content_dir = title_dir.joinpath("content")
        if content_dir.exists():
            shutil.rmtree(content_dir)  # Clear the content directory so old contents aren't left behind.
        content_dir.mkdir(exist_ok=True)
        open(content_dir.joinpath("title.tmd"), "wb").write(title.wad.get_tmd_data())
        for content_file in range(0, title.tmd.num_contents):
            if title.tmd.content_records[content_file].content_type == 1:
                content_file_name = f"{title.tmd.content_records[content_file].content_id:08X}".lower()
                open(content_dir.joinpath(content_file_name + ".app"), "wb").write(
                    title.get_content_by_index(content_file, skip_hash=skip_hash))
        title_dir.joinpath("data").mkdir(exist_ok=True)  # Empty directory used for save data for the title.

        # Shared contents need to be installed to /shared1/, with incremental names determined by /shared1/content.map.
        content_map_path = self.shared1_dir.joinpath("content.map")
        content_map = _SharedContentMap()
        existing_hashes = []
        if content_map_path.exists():
            content_map.load(open(content_map_path, "rb").read())
            for record in content_map.shared_records:
                existing_hashes.append(record.content_hash)
        for content_file in range(0, title.tmd.num_contents):
            if title.tmd.content_records[content_file].content_type == 32769:
                if title.tmd.content_records[content_file].content_hash not in existing_hashes:
                    content_file_name = content_map.add_content(title.tmd.content_records[content_file].content_hash)
                    open(self.shared1_dir.joinpath(content_file_name + ".app"), "wb").write(
                        title.get_content_by_index(content_file, skip_hash=skip_hash))
        open(self.shared1_dir.joinpath("content.map"), "wb").write(content_map.dump())

        # The "footer" or meta file is installed as title.met in /meta/<tid_upper>/<tid_lower>/. Only write this if meta
        # is not nothing.
        meta_data = title.wad.get_meta_data()
        if meta_data != b'':
            meta_dir = self.meta_dir.joinpath(tid_upper)
            meta_dir.mkdir(exist_ok=True)
            meta_dir = meta_dir.joinpath(tid_lower)
            meta_dir.mkdir(exist_ok=True)
            open(meta_dir.joinpath("title.met"), "wb").write(title.wad.get_meta_data())

        # Ensure we have a uid.sys file created.
        uid_sys_path = self.sys_dir.joinpath("uid.sys")
        uid_sys = _UidSys()
        if not uid_sys_path.exists():
            uid_sys.create()

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
