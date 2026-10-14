"""Dependency-free QR Code encoder (byte mode, ECC L/M, versions 1-15) with text and PNG renderers.

Implements ISO/IEC 18004 enough for what the CLI needs: encoding an OAuth2 device
verification URL and drawing it either as terminal text (UTF-8 half blocks, ASCII
fallback) or as a 1-bit PNG built with zlib only. The reference tables below are the
standard RS block / alignment pattern tables for versions 1-15.
"""

from __future__ import annotations

import struct
import zlib

_ECC_BITS = {"L": 0b01, "M": 0b00}

_RS_BLOCKS: dict[str, dict[int, tuple[int, ...]]] = {
    "L": {
        1: (1, 26, 19),
        2: (1, 44, 34),
        3: (1, 70, 55),
        4: (1, 100, 80),
        5: (1, 134, 108),
        6: (2, 86, 68),
        7: (2, 98, 78),
        8: (2, 121, 97),
        9: (2, 146, 116),
        10: (2, 86, 68, 2, 87, 69),
        11: (4, 101, 81),
        12: (2, 116, 92, 2, 117, 93),
        13: (4, 133, 107),
        14: (3, 145, 115, 1, 146, 116),
        15: (5, 109, 87, 1, 110, 88),
    },
    "M": {
        1: (1, 26, 16),
        2: (1, 44, 28),
        3: (1, 70, 44),
        4: (2, 50, 32),
        5: (2, 67, 43),
        6: (4, 43, 27),
        7: (4, 49, 31),
        8: (2, 60, 38, 2, 61, 39),
        9: (3, 58, 36, 2, 59, 37),
        10: (4, 69, 43, 1, 70, 44),
        11: (1, 80, 50, 4, 81, 51),
        12: (6, 58, 36, 2, 59, 37),
        13: (8, 59, 37, 1, 60, 38),
        14: (4, 64, 40, 5, 65, 41),
        15: (5, 65, 41, 5, 66, 42),
    },
}

_ALIGN: dict[int, tuple[int, ...]] = {
    1: (),
    2: (6, 18),
    3: (6, 22),
    4: (6, 26),
    5: (6, 30),
    6: (6, 34),
    7: (6, 22, 38),
    8: (6, 24, 42),
    9: (6, 26, 46),
    10: (6, 28, 50),
    11: (6, 30, 54),
    12: (6, 32, 58),
    13: (6, 34, 62),
    14: (6, 26, 46, 66),
    15: (6, 26, 48, 70),
}

_MAX_VERSION = max(_RS_BLOCKS["L"])

_EXP = [0] * 512
_LOG = [0] * 256
_value = 1
for _i in range(255):
    _EXP[_i] = _value
    _LOG[_value] = _i
    _value <<= 1
    if _value & 0x100:
        _value ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def _mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _rs_generator(ec_len: int) -> list[int]:
    poly = [1]
    for i in range(ec_len):
        factor = _EXP[i]
        out = [0] * (len(poly) + 1)
        for j, coef in enumerate(poly):
            out[j] ^= coef
            out[j + 1] ^= _mul(coef, factor)
        poly = out
    return poly


def _rs_ec(data: list[int], ec_len: int) -> list[int]:
    gen = _rs_generator(ec_len)
    res = [0] * ec_len
    for byte in data:
        factor = byte ^ res[0]
        res = res[1:] + [0]
        if factor:
            for i in range(ec_len):
                res[i] ^= _mul(gen[i + 1], factor)
    return res


def _data_codewords(version: int, ecc: str) -> int:
    spec = _RS_BLOCKS[ecc][version]
    if len(spec) == 3:
        return spec[0] * spec[2]
    return spec[0] * spec[2] + spec[3] * spec[5]


def _groups(version: int, ecc: str) -> list[tuple[int, int]]:
    spec = _RS_BLOCKS[ecc][version]
    if len(spec) == 3:
        return [(spec[0], spec[2])]
    return [(spec[0], spec[2]), (spec[3], spec[5])]


def _pick_version(length: int, ecc: str) -> int:
    for version in range(1, _MAX_VERSION + 1):
        overhead = 2 if version <= 9 else 3
        if length + overhead <= _data_codewords(version, ecc):
            return version
    raise ValueError(f"data too long for QR version <= {_MAX_VERSION} at ECC {ecc}: {length} bytes")


def _bitstream(data: bytes, version: int, ecc: str) -> list[int]:
    capacity = _data_codewords(version, ecc) * 8
    bits: list[int] = [0, 1, 0, 0]
    count_bits = 8 if version <= 9 else 16
    for i in range(count_bits - 1, -1, -1):
        bits.append((len(data) >> i) & 1)
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    bits.extend([0] * min(4, capacity - len(bits)))
    while len(bits) % 8:
        bits.append(0)
    codewords = [int("".join(str(b) for b in bits[i : i + 8]), 2) for i in range(0, len(bits), 8)]
    pad = (0xEC, 0x11)
    added = 0
    while len(codewords) < capacity // 8:
        codewords.append(pad[added % 2])
        added += 1
    return codewords


def _interleave(codewords: list[int], version: int, ecc: str) -> list[int]:
    spec = _RS_BLOCKS[ecc][version]
    ec_len = spec[1] - spec[2]
    blocks: list[tuple[list[int], list[int]]] = []
    pos = 0
    for count, data_len in _groups(version, ecc):
        for _ in range(count):
            chunk = codewords[pos : pos + data_len]
            pos += data_len
            blocks.append((chunk, _rs_ec(chunk, ec_len)))
    out: list[int] = []
    for i in range(max(len(b[0]) for b in blocks)):
        for data, _ in blocks:
            if i < len(data):
                out.append(data[i])
    for i in range(ec_len):
        for _, ec in blocks:
            out.append(ec[i])
    return out


def _format_bits(ecc: str, mask: int) -> int:
    value = (_ECC_BITS[ecc] << 3) | mask
    rem = value << 10
    while (rem.bit_length() - 1) >= 10:
        rem ^= 0x537 << ((rem.bit_length() - 1) - 10)
    return ((value << 10) | rem) ^ 0x5412


def _version_bits(version: int) -> int:
    rem = version << 12
    while (rem.bit_length() - 1) >= 12:
        rem ^= 0x1F25 << ((rem.bit_length() - 1) - 12)
    return (version << 12) | rem


def _mask_bit(mask: int, row: int, col: int) -> bool:
    if mask == 0:
        return (row + col) % 2 == 0
    if mask == 1:
        return row % 2 == 0
    if mask == 2:
        return col % 3 == 0
    if mask == 3:
        return (row + col) % 3 == 0
    if mask == 4:
        return (row // 2 + col // 3) % 2 == 0
    if mask == 5:
        return (row * col) % 2 + (row * col) % 3 == 0
    if mask == 6:
        return ((row * col) % 2 + (row * col) % 3) % 2 == 0
    return ((row + col) % 2 + (row * col) % 3) % 2 == 0


def _skeleton(version: int) -> tuple[list[list[bool]], list[list[bool]]]:
    size = version * 4 + 17
    mod = [[False] * size for _ in range(size)]
    fixed = [[False] * size for _ in range(size)]

    def place(row: int, col: int, dark: bool) -> None:
        mod[row][col] = dark
        fixed[row][col] = True

    def finder(row0: int, col0: int) -> None:
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                row, col = row0 + dr, col0 + dc
                if 0 <= row < size and 0 <= col < size:
                    dark = 0 <= dr <= 6 and 0 <= dc <= 6 and (dr in (0, 6) or dc in (0, 6) or (2 <= dr <= 4 and 2 <= dc <= 4))
                    place(row, col, dark)

    finder(0, 0)
    finder(0, size - 7)
    finder(size - 7, 0)

    for i in range(8, size - 8):
        place(6, i, i % 2 == 0)
        place(i, 6, i % 2 == 0)

    positions = _ALIGN[version]
    for row in positions:
        for col in positions:
            if (row == 6 and col == 6) or (row == 6 and col == size - 7) or (row == size - 7 and col == 6):
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    place(row + dr, col + dc, max(abs(dr), abs(dc)) != 1)

    place(size - 8, 8, True)

    for i in range(9):
        if i != 6:
            place(8, i, False)
            place(i, 8, False)
    for i in range(8):
        place(8, size - 1 - i, False)
        place(size - 1 - i, 8, False)
    place(8, size - 8, True)

    if version >= 7:
        for i in range(18):
            place(size - 11 + i % 3, i // 3, False)
            place(i // 3, size - 11 + i % 3, False)

    return mod, fixed


def _apply_format(mod: list[list[bool]], ecc: str, mask: int) -> None:
    size = len(mod)
    bits = _format_bits(ecc, mask)
    for i in range(15):
        dark = (bits >> i) & 1 == 1
        if i < 6:
            mod[i][8] = dark
        elif i < 8:
            mod[i + 1][8] = dark
        else:
            mod[size - 15 + i][8] = dark
    for i in range(15):
        dark = (bits >> i) & 1 == 1
        if i < 8:
            mod[8][size - i - 1] = dark
        elif i < 9:
            mod[8][15 - i] = dark
        else:
            mod[8][14 - i] = dark
    mod[size - 8][8] = True


def _apply_version(mod: list[list[bool]], version: int) -> None:
    if version < 7:
        return
    size = len(mod)
    bits = _version_bits(version)
    for i in range(18):
        dark = (bits >> i) & 1 == 1
        mod[size - 11 + i % 3][i // 3] = dark
        mod[i // 3][size - 11 + i % 3] = dark


def _placement_order(version: int, fixed: list[list[bool]]) -> list[tuple[int, int]]:
    size = version * 4 + 17
    order: list[tuple[int, int]] = []
    col = size - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(size - 1, -1, -1) if upward else range(size)
        for row in rows:
            for c in (col, col - 1):
                if not fixed[row][c]:
                    order.append((row, c))
        upward = not upward
        col -= 2
    return order


def _penalty(mod: list[list[bool]]) -> int:
    size = len(mod)
    score = 0
    for line in list(mod) + [list(col) for col in zip(*mod, strict=True)]:
        run = 1
        for i in range(1, size):
            if line[i] == line[i - 1]:
                run += 1
            else:
                if run >= 5:
                    score += 3 + (run - 5)
                run = 1
        if run >= 5:
            score += 3 + (run - 5)
        text = "".join("1" if v else "0" for v in line)
        score += 40 * (text.count("10111010000") + text.count("00001011101"))
    for row in range(size - 1):
        for col in range(size - 1):
            if mod[row][col] == mod[row][col + 1] == mod[row + 1][col] == mod[row + 1][col + 1]:
                score += 3
    dark = sum(sum(1 for v in row if v) for row in mod)
    score += abs(dark * 100 // (size * size) - 50) // 5 * 10
    return score


def _build_matrix(codewords: list[int], version: int, ecc: str) -> list[list[bool]]:
    base, fixed = _skeleton(version)
    order = _placement_order(version, fixed)
    for index, (row, col) in enumerate(order):
        if index >= len(codewords) * 8:
            break
        byte = codewords[index // 8]
        base[row][col] = (byte >> (7 - index % 8)) & 1 == 1

    best: list[list[bool]] | None = None
    best_score = -1
    for mask in range(8):
        candidate = [row[:] for row in base]
        for row, col in order:
            if _mask_bit(mask, row, col):
                candidate[row][col] = not candidate[row][col]
        _apply_version(candidate, version)
        _apply_format(candidate, ecc, mask)
        score = _penalty(candidate)
        if best is None or score < best_score:
            best, best_score = candidate, score
    assert best is not None
    return best


def encode(text: str, ecc: str = "M") -> list[list[bool]]:
    """Encode `text` (byte mode) into a QR module matrix, downgrading M -> L when too long."""
    data = text.encode("utf-8")
    try:
        version = _pick_version(len(data), ecc)
    except ValueError:
        if ecc != "M":
            raise
        ecc = "L"
        version = _pick_version(len(data), ecc)
    codewords = _bitstream(data, version, ecc)
    return _build_matrix(_interleave(codewords, version, ecc), version, ecc)


def render_text(matrix: list[list[bool]], *, unicode: bool = True, quiet_zone: int = 2) -> str:
    """Render the matrix as terminal text: UTF-8 half blocks, or ASCII when `unicode` is False."""
    size = len(matrix)
    width = size + quiet_zone * 2

    def dark(row: int, col: int) -> bool:
        r, c = row - quiet_zone, col - quiet_zone
        return 0 <= r < size and 0 <= c < size and matrix[r][c]

    lines: list[str] = []
    if unicode:
        for row in range(0, width, 2):
            buf = []
            for col in range(width):
                top, bottom = dark(row, col), row + 1 < width and dark(row + 1, col)
                buf.append("█" if top and bottom else "▀" if top else "▄" if bottom else " ")
            lines.append("".join(buf))
    else:
        for row in range(width):
            lines.append("".join("██" if dark(row, col) else "  " for col in range(width)))
    return "\n".join(lines)


def to_png(matrix: list[list[bool]], *, scale: int = 6, quiet_zone: int = 4) -> bytes:
    """Render the matrix as a 1-bit greyscale PNG (black modules on white)."""
    size = len(matrix) + quiet_zone * 2
    pixels = size * scale
    raw = bytearray()
    for y in range(pixels):
        raw.append(0)
        row_bits = bytearray()
        byte = 0
        filled = 0
        for x in range(pixels):
            r, c = y // scale - quiet_zone, x // scale - quiet_zone
            dark = 0 <= r < len(matrix) and 0 <= c < len(matrix) and matrix[r][c]
            byte = (byte << 1) | (0 if dark else 1)
            filled += 1
            if filled == 8:
                row_bits.append(byte)
                byte = 0
                filled = 0
        if filled:
            row_bits.append(byte << (8 - filled))
        raw += row_bits

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", pixels, pixels, 1, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
