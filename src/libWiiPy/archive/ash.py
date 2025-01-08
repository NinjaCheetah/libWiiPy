# "archive/ash.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# This code in particular is a direct translation of "ash-dec" from ASH0-tools. ASH0-tools is written by Garhoogin and
# co-authored by NinjaCheetah.
# https://github.com/NinjaCheetah/ASH0-tools
#
# See <link pending> for details about the ASH compression format.

import io
from dataclasses import dataclass as _dataclass


@_dataclass
class _ASHBitReader:
    """
    An _ASHBitReader class used to parse individual words in an ASH file. Private class used by the ASH module.

    Attributes
    ----------
    src_data : list[int]
        The entire data of the ASH file being parsed, as a list of integers for each byte.
    size : int
        The size of the ASH file.
    src_pos : int
        The position in the src_data list currently being accessed.
    word : int
        The word currently being decompressed.
    bit_capacity : int
    tree_type : str
        What tree this bit reader is being used with. Used exclusively for debugging, as this value is only used in
        error messages.
    """
    src_data: list[int]
    size: int
    src_pos: int
    word: int
    bit_capacity: int
    tree_type: str


def _ash_bit_reader_feed_word(bit_reader: _ASHBitReader):
    # Ensure that there's enough data to read en entire word, then if there is, read one.
    if not bit_reader.src_pos + 4 <= bit_reader.size:
        print(bit_reader.src_pos)
        raise ValueError("Invalid ASH data! Cannot decompress.")
    bit_reader.word = int.from_bytes(bit_reader.src_data[bit_reader.src_pos:bit_reader.src_pos + 4], 'big')
    bit_reader.bit_capacity = 0
    bit_reader.src_pos += 4


def _ash_bit_reader_init(bit_reader: _ASHBitReader, src: list[int], size: int, start_pos: int):
    # Load data into a bit reader, then have it read its first word.
    bit_reader.src_data = src
    bit_reader.size = size
    bit_reader.src_pos = start_pos
    _ash_bit_reader_feed_word(bit_reader)


def _ash_bit_reader_read_bit(bit_reader: _ASHBitReader):
    # Reads the starting bit of the current word in the provided bit reader. If the capacity is at 31, then we've
    # shifted through the entire word, so a new one should be fed. If not, increase the capacity by one and shift the
    # current word left.
    bit = bit_reader.word >> 31
    if bit_reader.bit_capacity == 31:
        _ash_bit_reader_feed_word(bit_reader)
    else:
        bit_reader.bit_capacity += 1
        bit_reader.word = (bit_reader.word << 1) & 0xFFFFFFFF  # This simulates a 32-bit integer.

    return bit


def _ash_bit_reader_read_bits(bit_reader: _ASHBitReader, num_bits: int):
    # Reads a series of bytes from the current word in the supplied bit reader.
    bits: int
    next_bit = bit_reader.bit_capacity + num_bits

    if next_bit <= 32:
        bits = bit_reader.word >> (32 - num_bits)
        if next_bit != 32:
            bit_reader.word = (bit_reader.word << num_bits) & 0xFFFFFFFF  # This simulates a 32-bit integer (again).
            bit_reader.bit_capacity += num_bits
        else:
            _ash_bit_reader_feed_word(bit_reader)
    else:
        bits = bit_reader.word >> (32 - num_bits)
        _ash_bit_reader_feed_word(bit_reader)
        bits |= (bit_reader.word >> (64 - next_bit))
        bit_reader.word = (bit_reader.word << (next_bit - 32)) & 0xFFFFFFFF  # Simulate 32-bit int.
        bit_reader.bit_capacity = next_bit - 32

    return bits


def _ash_read_tree(bit_reader: _ASHBitReader, width: int, left_tree: [int], right_tree: [int]):
    # Read either the symbol or distance tree from the ASH file, and return the root of that tree.
    work = [0] * (2 * (1 << width))
    work_pos = 0

    r23 = 1 << width
    tree_root = 0
    num_nodes = 0

    while True:
        if _ash_bit_reader_read_bit(bit_reader) != 0:
            work[work_pos] = (r23 | 0x80000000)
            work_pos += 1
            work[work_pos] = (r23 | 0x40000000)
            work_pos += 1
            num_nodes += 2
            r23 += 1
        else:
            tree_root = _ash_bit_reader_read_bits(bit_reader, width)
            while True:
                work_pos -= 1
                node_value = work[work_pos]
                idx = node_value & 0x3FFFFFFF
                num_nodes -= 1
                try:
                    if node_value & 0x80000000:
                        right_tree[idx] = tree_root
                        tree_root = idx
                    else:
                        left_tree[idx] = tree_root
                        break
                except IndexError:
                    raise ValueError("Decompression failed while reading " + bit_reader.tree_type + " tree! Incorrect "
                                     "leaf width may have been used. Try using a different number of bits for the " +
                                     bit_reader.tree_type + " tree leaves.")
                # Simulate a do-while loop.
                if num_nodes == 0:
                    break
        # Also a do-while.
        if num_nodes == 0:
            break

    return tree_root


def _decompress_ash(input_data: list[int], size: int, sym_bits: int, dist_bits: int):
    # Get the size of the decompressed data by reading the second 4 bytes of the file and masking the first one out.
    decompressed_size = int.from_bytes(input_data[0x4:0x8]) & 0x00FFFFFF
    # Array of decompressed data and the position in that array that we're at. Mimics the memory pointer from the
    # original C source.
    out_buffer = [0] * decompressed_size
    out_buffer_pos = 0
    # Create two empty bit readers, and then initialize them at two different positions for the two trees.
    bit_reader1 = _ASHBitReader([0], 0, 0, 0, 0, "distance")
    _ash_bit_reader_init(bit_reader1, input_data, size, int.from_bytes(input_data[0x8:0xC], byteorder='big'))
    bit_reader2 = _ASHBitReader([0], 0, 0, 0, 0, "symbol")
    _ash_bit_reader_init(bit_reader2, input_data, size, 0xC)
    # Calculate the max for the symbol and distance trees based on the bit lengths that were passed. Then, allocate the
    # arrays for all the trees based on that maximum.
    sym_max = 1 << sym_bits
    dist_max = 1 << dist_bits
    sym_left_tree = [0] * (2 * sym_max - 1)
    sym_right_tree = [0] * (2 * sym_max - 1)
    dist_left_tree = [0] * (2 * dist_max - 1)
    dist_right_tree = [0] * (2 * dist_max - 1)
    # Read the trees to find the symbol and distance tree roots.
    sym_root = _ash_read_tree(bit_reader2, sym_bits, sym_left_tree, sym_right_tree)
    dist_root = _ash_read_tree(bit_reader1, dist_bits, dist_left_tree, dist_right_tree)
    # Main decompression loop.
    while True:
        sym = sym_root
        while sym >= sym_max:
            if _ash_bit_reader_read_bit(bit_reader2) != 0:
                sym = sym_right_tree[sym]
            else:
                sym = sym_left_tree[sym]
        if sym < 0x100:
            out_buffer[out_buffer_pos] = sym
            out_buffer_pos += 1
            decompressed_size -= 1
        else:
            dist_sym = dist_root
            while dist_sym >= dist_max:
                if _ash_bit_reader_read_bit(bit_reader1) != 0:
                    dist_sym = dist_right_tree[dist_sym]
                else:
                    dist_sym = dist_left_tree[dist_sym]
            copy_len = (sym - 0x100) + 3
            srcp_pos = out_buffer_pos - dist_sym - 1
            # Check to make sure we aren't going to exceed the specified decompressed size.
            if not copy_len <= decompressed_size:
                raise ValueError("Invalid ASH data! Cannot decompress.")

            decompressed_size -= copy_len
            while copy_len > 0:
                out_buffer[out_buffer_pos] = out_buffer[srcp_pos]
                out_buffer_pos += 1
                srcp_pos += 1
                copy_len -= 1
        # Simulate a do-while loop.
        if decompressed_size == 0:
            break

    return out_buffer


def decompress_ash(ash_data: bytes, sym_tree_bits: int = 9, dist_tree_bits: int = 11) -> bytes:
    """
    Decompresses the data of an ASH file and returns the decompressed data.

    With the default parameters, this function can decompress ASH files found in the files of the Wii Menu and Animal
    Crossing: City Folk. Some ASH files, notably the ones found in the WiiWare title My Pokémon Ranch, require setting
    dist_tree_bits to 15 instead for a successful decompression. If an ASH file is failing to decompress with the
    default options, trying a dist_tree_bits value of 15 will likely fix it. No other leaf sizes are known to exist,
    however they might be out there.

    Parameters
    ----------
    ash_data : bytes
        The data for the ASH file to decompress.
    sym_tree_bits : int, option
        Number of bits for each leaf in the symbol tree. Defaults to 9.
    dist_tree_bits : int, option
        Number of bits for each leaf in the distance tree. Defaults to 11.
    """
    # Check the magic number to make sure this is an ASH file.
    with io.BytesIO(ash_data) as ash_data2:
        ash_magic = ash_data2.read(4)
        if ash_magic != b'\x41\x53\x48\x30':
            raise TypeError("This is not a valid ASH file!")
    # Begin decompression. Convert the compressed data to an array of ints for processing, then convert the returned
    # decompressed data back into bytes to return it.
    ash_size = len(ash_data)
    ash_data_int = [byte for byte in ash_data]
    decompressed_data = _decompress_ash(ash_data_int, ash_size, sym_tree_bits, dist_tree_bits)
    decompressed_data_bin = bytes(decompressed_data)

    return decompressed_data_bin
