# "title/wiiload.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# This code is adapted from "wiiload.py", which can be found on the WiiBrew page for Wiiload.
# https://pastebin.com/4nWAkBpw
#
# See https://wiibrew.org/wiki/Wiiload for details about how Wiiload works

import sys
import zlib
import socket
import struct


def send_bin_wiiload(target_ip: str, bin_data: bytes, name: str) -> None:
    """
    Sends an ELF or DOL binary to The Homebrew Channel via Wiiload. This requires the IP address of the console you
    want to send the binary to.

    Parameters
    ----------
    target_ip: str
        The IP address of the console to send the binary to.
    bin_data: bytes
        The data of the ELF or DOL to send.
    name: str
        The name of the application being sent.
    """
    wii_ip = (target_ip, 4299)

    WIILOAD_VERSION_MAJOR=0
    WIILOAD_VERSION_MINOR=5

    len_uncompressed = len(bin_data)
    c_data = zlib.compress(bin_data, 6)

    chunk_size = 1024*128
    chunks = [c_data[i:i+chunk_size] for i  in range(0, len(c_data), chunk_size)]

    args = [name]
    args = "\x00".join(args) + "\x00"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(wii_ip)

    s.send("HAXX")
    s.send(struct.pack("B", WIILOAD_VERSION_MAJOR)) # one byte, unsigned
    s.send(struct.pack("B", WIILOAD_VERSION_MINOR)) # one byte, unsigned
    s.send(struct.pack(">H",len(args))) # bigendian, 2 bytes, unsigned
    s.send(struct.pack(">L",len(c_data))) # bigendian, 4 bytes, unsigned
    s.send(struct.pack(">L",len_uncompressed)) # bigendian, 4 bytes, unsigned

    print(len(chunks),"chunks to send")
    for piece in chunks:
        s.send(piece)
        sys.stdout.write("."); sys.stdout.flush()
    sys.stdout.write("\n")

    s.send(args)

    s.close()
    print("done")
