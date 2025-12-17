# "nand/setting.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki//title/00000001/00000002/data/setting.txt for information about setting.txt.

import io
from typing import List
from ..shared import _pad_bytes


_KEY = 0x73B5DBFA

class SettingTxt:
    """
    A SettingTxt object that allows for decrypting and then parsing a setting.txt file from the Wii.

    Attributes
    ----------
    area : str
        The region of the System Menu this file matches with.
    model : str
        The model of the console, usually RVL-001 or RVL-101.
    dvd : int
        Unknown, might have to do with indicating support for scrapped DVD playback capabilities.
    mpch : str
        Unknown, generally accepted value is "0x7FFE".
    code : str
        Unknown code, may match with manufacturer code in serial number?
    serial_number : str
        Serial number of the console.
    video : str
        Video mode, either NTSC or PAL.
    game : str
        Another region code, possibly set by the hidden region select channel.
    """
    def __init__(self) -> None:
        self.area: str = ""
        self.model: str = ""
        self.dvd: int = 0
        self.mpch: str = ""  # What does this mean, Movie Player Channel? It's also a hex string, it seems.
        self.code: str = ""
        self.serial_number: str = ""
        self.video: str = ""
        self.game: str = ""

    def load(self, setting_txt: bytes) -> None:
        """
        Loads the raw data of an encrypted setting.txt file and decrypts it to parse its arguments

        Parameters
        ----------
        setting_txt : bytes
            The data of an encrypted setting.txt file.
        """
        with io.BytesIO(setting_txt) as setting_data:
            global _KEY  # I still don't actually know what *kind* of encryption this is.
            setting_txt_dec: List[int] = []
            for i in range(0, 256):
                setting_txt_dec.append(int.from_bytes(setting_data.read(1)) ^ (_KEY & 0xff))
                _KEY = (_KEY << 1) | (_KEY >> 31)
        setting_txt_bytes = bytes(setting_txt_dec)
        try:
            setting_str = setting_txt_bytes.decode('utf-8')
        except UnicodeDecodeError:
            last_newline_pos = setting_txt_bytes.rfind(b'\n')  # This makes sure we don't try to decode any garbage data.
            setting_str = setting_txt_bytes[:last_newline_pos + 1].decode('utf-8')
        self.load_decrypted(setting_str)

    def load_decrypted(self, setting_txt: str) -> None:
        """
        Loads the raw data of a decrypted setting.txt file and parses its arguments

        Parameters
        ----------
        setting_txt : str
            The data of a decrypted setting.txt file.
        """
        setting_dict = {}
        # Iterate over every key in the file to create a dictionary.
        for line in setting_txt.splitlines():
            line = line.strip()
            if line is not None:
                key, value = line.split('=', 1)
                setting_dict[key.strip()] = value.strip()
        # Load the values from the dictionary into the object.
        self.area = setting_dict["AREA"]
        self.model = setting_dict["MODEL"]
        self.dvd = int(setting_dict["DVD"])
        self.mpch = setting_dict["MPCH"]
        self.code = setting_dict["CODE"]
        self.serial_number = setting_dict["SERNO"]
        self.video = setting_dict["VIDEO"]
        self.game = setting_dict["GAME"]

    def dump(self) -> bytes:
        """
        Dumps the SettingTxt object back into an encrypted bytes that the Wii can load.

        Returns
        -------
        bytes
            The setting.txt file as encrypted bytes.
        """
        setting_str = self.dump_decrypted()
        setting_txt_dec = setting_str.encode()
        global _KEY
        # This could probably be made more efficient somehow.
        setting_txt_enc: List[int] = []
        with io.BytesIO(setting_txt_dec) as setting_data:
            for i in range(0, len(setting_txt_dec)):
                setting_txt_enc.append(int.from_bytes(setting_data.read(1)) ^ (_KEY & 0xff))
                _KEY = (_KEY << 1) | (_KEY >> 31)
        setting_txt_bytes = _pad_bytes(bytes(setting_txt_enc), 256)
        return setting_txt_bytes

    def dump_decrypted(self) -> str:
        """
        Dumps the SettingTxt object into a decrypted string.

        Returns
        -------
        str
            The setting.txt file as decrypted text.
        """
        # Write the keys back into a text file that can then be manually edited or re-encrypted.
        setting_txt = ""
        setting_txt += f"AREA={self.area}\r\n"
        setting_txt += f"MODEL={self.model}\r\n"
        setting_txt += f"DVD={self.dvd}\r\n"
        setting_txt += f"MPCH={self.mpch}\r\n"
        setting_txt += f"CODE={self.code}\r\n"
        setting_txt += f"SERNO={self.serial_number}\r\n"
        setting_txt += f"VIDEO={self.video}\r\n"
        setting_txt += f"GAME={self.game}\r\n"
        return setting_txt
