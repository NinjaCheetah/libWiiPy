from typing import List
from binascii import unhexlify


def hex_string_to_byte_array(hex_string: str) -> List[int]:
    byte_string = unhexlify(hex_string)
    byte_array = list(byte_string)

    return byte_array
