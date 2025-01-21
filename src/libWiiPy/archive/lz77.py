# "archive/lz77.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/LZ77 for details about the LZ77 compression format.

import io
from dataclasses import dataclass as _dataclass


LZ_MIN_DISTANCE = 0x01   # Minimum distance for each reference.
LZ_MAX_DISTANCE = 0x1000   # Maximum distance for each reference.
LZ_MIN_LENGTH = 0x03   # Minimum length for each reference.
LZ_MAX_LENGTH = 0x12   # Maximum length for each reference.


@_dataclass
class _LZNode:
    dist: int = 0
    len: int = 0
    weight: int = 0


def _compress_compare_bytes(byte1: bytes, offset1: int, byte2: bytes, offset2: int, abs_len_max: int) -> int:
    # Compare bytes up to the maximum length we can match.
    num_matched = 0
    mem1 = memoryview(byte1)
    mem2 = memoryview(byte2)
    while num_matched < abs_len_max:
        if mem1[offset1 + num_matched] != mem2[offset2 + num_matched]:
            break
        num_matched += 1
    return num_matched


def _compress_search_matches(buffer: bytes, pos: int) -> (int, int):
    bytes_left = len(buffer) - pos
    global LZ_MAX_DISTANCE, LZ_MAX_LENGTH, LZ_MIN_DISTANCE
    # Default to only looking back 4096 bytes, unless we've moved fewer than 4096 bytes, in which case we should
    # only look as far back as we've gone.
    max_dist = min(LZ_MAX_DISTANCE, pos)
    # Default to only matching up to 18 bytes, unless fewer than 18 bytes remain, in which case we can only match
    # up to that many bytes.
    max_len = min(LZ_MAX_LENGTH, bytes_left)
    # Log the longest match we found and its offset.
    biggest_match = 0
    biggest_match_pos = 0
    # Search for matches.
    for i in range(LZ_MIN_DISTANCE, max_dist + 1):
        num_matched = _compress_compare_bytes(buffer, pos - i, buffer, pos, max_len)
        if num_matched > biggest_match:
            biggest_match = num_matched
            biggest_match_pos = i
            if biggest_match == max_len:
                break
    return biggest_match, biggest_match_pos


def _compress_node_is_ref(node: _LZNode) -> bool:
    return node.len >= LZ_MIN_LENGTH


def _compress_get_node_cost(length: int) -> int:
    if length >= LZ_MAX_LENGTH:
        num_bytes = 2
    else:
        num_bytes = 1
    return 1 + (num_bytes * 8)


def compress_lz77(data: bytes) -> bytes:
    """

    Parameters
    ----------
    data

    Returns
    -------

    """
    nodes = [_LZNode() for _ in range(len(data))]
    # Iterate over the uncompressed data, starting from the end.
    pos = len(data)
    global LZ_MAX_LENGTH, LZ_MIN_LENGTH, LZ_MIN_DISTANCE
    while pos:
        pos -= 1
        node = nodes[pos]
        # Limit the maximum search length when we're near the end of the file.
        max_search_len = LZ_MAX_LENGTH
        if max_search_len > (len(data) - pos):
            max_search_len = len(data) - pos
        if max_search_len < LZ_MIN_DISTANCE:
            max_search_len = 1
        # Initialize as 1 for each, since that's all we could use if we weren't compressing.
        length, dist = 1, 1
        if max_search_len >= LZ_MIN_LENGTH:
            length, dist = _compress_search_matches(data, pos)
        # Treat as direct bytes if it's too short to copy.
        if length == 0 or length < LZ_MIN_LENGTH:
            length = 1
        # If the node goes to the end of the file, the weight is the cost of the node.
        if pos + length == len(data):
            node.len = length
            node.dist = dist
            node.weight = _compress_get_node_cost(length)
        # Otherwise, search for possible matches and determine the one with the best cost.
        else:
            weight_best = 0xFFFFFFFF  # This was originally UINT_MAX, but that isn't a thing here.
            len_best = 1
            while length:
                weight_next = nodes[pos + length].weight
                weight = _compress_get_node_cost(length) + weight_next
                if weight < weight_best:
                    len_best = length
                    weight_best = weight
                length -= 1
                if length != 0 and length < LZ_MIN_LENGTH:
                    length = 1
            node.len = len_best
            node.dist = dist
            node.weight = weight_best
    # Maximum size of the compressed file.
    max_compressed_size = int(4 + len(data) + (len(data) + 7) / 8)
    # Write the header data.
    with io.BytesIO() as buffer:
        # Write the header data.
        buffer.write(b'LZ77\x10')  # The LZ type on the Wii is *always* 0x10.
        buffer.write(len(data).to_bytes(3, 'little'))

        src_pos = 0
        while src_pos < len(data):
            head = 0
            head_pos = buffer.tell()

            i = 0
            while i < 8 and src_pos < len(data):
                current_node = nodes[src_pos]
                length = current_node.len
                dist = current_node.dist
                # This is a reference node.
                if _compress_node_is_ref(current_node):
                    encoded = ((dist - LZ_MIN_DISTANCE) | ((length - LZ_MAX_LENGTH) << 12)) & 0xFFFF  # A uint16_t.
                    buffer.write(((encoded >> 8) & 0xFF).to_bytes(1))
                    buffer.write(((encoded >> 0) & 0xFF).to_bytes(1))
                    head = (head | (1 << (7 - i))) & 0xFF
                # This is a direct copy node.
                else:
                    buffer.write(data[src_pos:src_pos + 1])
                src_pos += length

            pos = buffer.tell()
            buffer.seek(head_pos)
            buffer.write(head.to_bytes(1))
            buffer.seek(pos)

        buffer.seek(0)
        out_data = buffer.read()
    return out_data


def decompress_lz77(lz77_data: bytes) -> bytes:
    """
    Decompresses LZ77-compressed data and returns the decompressed result. Supports data both with and without the
    magic number 'LZ77' (which may not be present if the data is embedded in something else).

    Parameters
    ----------
    lz77_data: bytes
        The LZ77-compressed data to decompress.

    Returns
    -------
    bytes
        The decompressed data.
    """
    with io.BytesIO(lz77_data) as data:
        magic = data.read(4)
        # Assume if we didn't get the magic number that this data starts without it.
        if magic != b'LZ77':
            data.seek(0)
        # Other compression types are used by Nintendo, but only type 0x10 was used on the Wii.
        compression_type = int.from_bytes(data.read(1))
        if compression_type != 0x10:
            raise ValueError("This data is using an unsupported compression type!")
        decompressed_size = int.from_bytes(data.read(3), byteorder='little')
        # Use an integer list for storing decompressed data, this is much faster than using (and appending to) a
        # bytes object.
        out_data = [0] * decompressed_size
        pos = 0
        while pos < decompressed_size:
            flag = int.from_bytes(data.read(1))
            # Read bits in the flag from most to least significant.
            for x in range(7, -1, -1):
                # Avoids a buffer overrun if the final flag isn't fully used.
                if pos >= decompressed_size:
                    break
                # Result of 1, this means we're copying bytes from earlier in the data.
                if flag & (1 << x):
                    reference = int.from_bytes(data.read(2))
                    length = 3 + ((reference >> 12) & 0xF)
                    offset = pos - (reference & 0xFFF) - 1
                    for _ in range(length):
                        out_data[pos] = out_data[offset]
                        pos += 1
                        offset += 1
                        # Avoids a buffer overrun if the copy length would extend past the end of the file.
                        if pos >= decompressed_size:
                            break
                # Result of 0, use the next byte directly.
                else:
                    out_data[pos] = int.from_bytes(data.read(1))
                    pos += 1
        out_bytes = bytes(out_data)
        return out_bytes
