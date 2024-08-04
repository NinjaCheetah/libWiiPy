# "title/iospatcher.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# Module for applying patches to IOS WADs via a Title().

import io
from .title import Title


class IOSPatcher:
    """
    An IOSPatcher object that allows for applying patches to IOS WADs loaded into Title objects.

    Attributes
    ----------
    title : Title
        The loaded Title object to be patched.
    es_module_index : int
        The content index that ES resides in and where ES patches are applied.
    dip_module_index : int
        The content index that DIP resides in and where DIP patches are applied. -1 if DIP patches are not applied.
    """
    def __init__(self):
        self.title: Title = Title()
        self.es_module_index: int = -1
        self.dip_module_index: int = -1

    def load(self, title: Title) -> None:
        """
        Loads a Title object containing an IOS WAD and locates the content containing the ES module that needs to be
        patched.

        Parameters
        ----------
        title : Title
            A Title object containing the IOS to be patched.
        """
        # Check to ensure that this Title contains IOS. IOS always has a TID high of 00000001, and any TID low after
        # 00000002.
        tid = title.tmd.title_id
        if tid[:8] != "00000001" or tid[8:] == "00000001" or tid[8:] == "00000002":
            raise ValueError("This Title does not contain an IOS! Cannot load Title for patching.")

        # Now that we know this is IOS, we need to go ahead and check all of its contents until we find the one that
        # contains the ES module, since that's what we're patching.
        es_content_index = -1
        for content in range(len(title.content.content_records)):
            target_content = title.get_content_by_index(title.content.content_records[content].index)
            es_offset = target_content.find(b'\x45\x53\x3A')  # This is looking for "ES:"
            if es_offset != -1:
                es_content_index = title.content.content_records[content].index
                break

        # If we get here with no content index, then ES wasn't found. That probably means that this isn't IOS.
        if es_content_index == -1:
            raise Exception("ES module could not be found! Please ensure that this is an intact copy of an IOS.")

        self.title = title
        self.es_module_index = es_content_index

    def dump(self) -> Title:
        """
        Returns the patched Title object.

        Returns
        -------
        Title
            The patched Title object.
        """
        return self.title

    def patch_all(self) -> int:
        """
        Applies all patches to patch in fakesigning, ES_Identify access, /dev/flash access, and the version downgrading
        patch.

        Returns
        -------
        int
            The number of patches successfully applied.
        """
        patch_count = 0
        patch_count += self.patch_fakesigning()
        patch_count += self.patch_es_identify()
        patch_count += self.patch_nand_access()
        patch_count += self.patch_version_downgrading()
        return patch_count

    def patch_fakesigning(self) -> int:
        """
        Patches the trucha/fakesigning bug back into the IOS' ES module to allow it to accept fakesigned TMDs and
        Tickets.

        Returns
        -------
        int
            The number of patches successfully applied.
        """
        if self.es_module_index == -1:
            raise Exception("No valid IOS is loaded! Patching cannot continue.")

        target_content = self.title.get_content_by_index(self.es_module_index)

        patch_count = 0
        patch_sequences = [b'\x20\x07\x23\xa2', b'\x20\x07\x4b\x0b']
        for sequence in patch_sequences:
            start_offset = target_content.find(sequence)
            if start_offset != -1:
                with io.BytesIO(target_content) as content_data:
                    content_data.seek(start_offset + 1)
                    content_data.write(b'\x00')
                    content_data.seek(0)
                    target_content = content_data.read()
                    patch_count += 1

        self.title.set_content(target_content, self.es_module_index)

        return patch_count

    def patch_es_identify(self) -> int:
        """
        Patches the ability to call ES_Identify back into the IOS' ES module to allow for changing the permissions of a
        title.

        Returns
        -------
        int
            The number of patches successfully applied.
        """
        if self.es_module_index == -1:
            raise Exception("No valid IOS is loaded! Patching cannot continue.")

        target_content = self.title.get_content_by_index(self.es_module_index)

        patch_count = 0
        patch_sequence = b'\x28\x03\xd1\x23'
        start_offset = target_content.find(patch_sequence)
        if start_offset != -1:
            with io.BytesIO(target_content) as content_data:
                content_data.seek(start_offset + 2)
                content_data.write(b'\x00\x00')
                content_data.seek(0)
                target_content = content_data.read()
                patch_count += 1

        self.title.set_content(target_content, self.es_module_index)

        return patch_count

    def patch_nand_access(self) -> int:
        """
        Patches the ability to directly access /dev/flash back into the IOS' ES module to allow for raw access to the
        Wii's filesystem.

        Returns
        -------
        int
            The number of patches successfully applied.
        """
        if self.es_module_index == -1:
            raise Exception("No valid IOS is loaded! Patching cannot continue.")

        target_content = self.title.get_content_by_index(self.es_module_index)

        patch_count = 0
        patch_sequence = b'\x42\x8b\xd0\x01\x25\x66'
        start_offset = target_content.find(patch_sequence)
        if start_offset != -1:
            with io.BytesIO(target_content) as content_data:
                content_data.seek(start_offset + 2)
                content_data.write(b'\xe0')
                content_data.seek(0)
                target_content = content_data.read()
                patch_count += 1

        self.title.set_content(target_content, self.es_module_index)

        return patch_count

    def patch_version_downgrading(self) -> int:
        """
        Patches the ability to downgrade installed titles into IOS' ES module.

        Returns
        -------
        int
            The number of patches successfully applied.
        """
        if self.es_module_index == -1:
            raise Exception("No valid IOS is loaded! Patching cannot continue.")

        target_content = self.title.get_content_by_index(self.es_module_index)

        patch_count = 0
        patch_sequence = b'\xd2\x01\x4e\x56'
        start_offset = target_content.find(patch_sequence)
        if start_offset != -1:
            with io.BytesIO(target_content) as content_data:
                content_data.seek(start_offset)
                content_data.write(b'\xe0')
                content_data.seek(0)
                target_content = content_data.read()
                patch_count += 1

        self.title.set_content(target_content, self.es_module_index)

        return patch_count

    def patch_drive_inquiry(self) -> int:
        """
        Patches out IOS' drive inquiry on startup, allowing IOS to load without a disc drive. Only required/useful if
        you do not have a disc drive connected to your console.

        This drive inquiry patch is EXPERIMENTAL, and may introduce unexpected side effects on some consoles.

        Returns
        -------
        int
            The number of patches successfully applied.
        """
        if self.es_module_index == -1:
            raise Exception("No valid IOS is loaded! Patching cannot continue.")

        # This patch is applied to the DIP module rather than to ES, so we need to search the contents for the right one
        # first.
        for content in range(len(self.title.content.content_records)):
            target_content = self.title.get_content_by_index(self.title.content.content_records[content].index)
            dip_offset = target_content.find(b'\x44\x49\x50\x3a')  # This is looking for "DIP:"
            if dip_offset != -1:
                self.dip_module_index = self.title.content.content_records[content].index
                break

        # If we get here with no content index, then DIP wasn't found. That probably means that this isn't IOS.
        if self.dip_module_index == -1:
            raise Exception("DIP module could not be found! Please ensure that this is an intact copy of an IOS.")

        target_content = self.title.get_content_by_index(self.dip_module_index)

        patch_count = 0
        patch_sequence = b'\x49\x4c\x23\x90\x68\x0a'  # 49 4c 23 90 68 0a
        start_offset = target_content.find(patch_sequence)
        if start_offset != -1:
            with io.BytesIO(target_content) as content_data:
                content_data.seek(start_offset)
                content_data.write(b'\x20\x00\xe5\x38')
                content_data.seek(0)
                target_content = content_data.read()
                patch_count += 1

        self.title.set_content(target_content, self.dip_module_index)

        return patch_count
