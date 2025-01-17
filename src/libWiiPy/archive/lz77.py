# "archive/lz77.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/LZ77 for details about the LZ77 compression format.

import io


def compress_lz77(data: bytes) -> bytes:
    """

    Parameters
    ----------
    data

    Returns
    -------

    """
    def compare_bytes(byte1: bytes, offset1: int, byte2: bytes, offset2: int, len_max: int, abs_len_max: int) -> int:
        num_matched = 0
        if len_max > abs_len_max:
            len_max = abs_len_max
        for i in range(0, len_max):
            if byte1[offset1 + 1] == byte2[offset2 + 1]:
                num_matched += 1
            else:
                break
        if num_matched == len_max:
            offset1 -= len_max
            for i in range(0, abs_len_max - len_max):
                if byte1[offset1 + 1] == byte2[offset2 + 1]:
                    num_matched += 1
                else:
                    break
        return num_matched

    def search_match(buffer: bytes, pos: int) -> (int, int):
        bytes_left = len(buffer) - pos
        # Default to only looking back 4096 bytes, unless we've moved fewer than 4096 bytes, in which case we should
        # only look as far back as we've gone.
        max_dist = 0x1000
        if max_dist > pos:
            max_dist = pos
        # We want the longest match we can find.
        biggest_match = 0
        biggest_match_pos = 0
        # Default to only matching up to 18 bytes, unless fewer than 18 bytes remain, in which case we can only match
        # up to that many bytes.
        max_len = 0x12
        if max_len > bytes_left:
            max_len = bytes_left
        for i in range(1, max_dist):
            num_compare = max_len
            if num_compare > i:
                num_compare = i
            if num_compare > max_len:
                num_compare = max_len
            num_matched = compare_bytes(buffer, pos - i, buffer, pos, max_len, 0x12)

    output_data = b'LZ77\x10'
    # Write the header by finding the size of the uncompressed data.
    output_data += int.to_bytes(len(data), 3, 'little')
    search_match(data, 0)


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
