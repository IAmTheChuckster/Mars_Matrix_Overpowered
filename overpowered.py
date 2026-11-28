#!/usr/bin/env python3
"""
Build Mars Matrix Overpowered.

1. Runs trap15.py (trap15 Mars Matrix Improvement v1.0.0) on your mmatrix.zip.
2. Applies the Overpowered tweaks on top of the trap15 ROMs.
3. Writes mmatrixop.zip with flat file names, matching the MiSTer .mra.

The build date and number come from the .mra <name>, e.g.
"Mars Matrix Overpowered (26/11/26 Build 2)". Change them there.

Usage:
  py overpowered.py mmatrix.zip patches/mmxi_v1.0.0_20250412.zip [--write-web]

--write-web also writes the patched CRCs into the .mra and refreshes the
web patcher (index.html): build number, byte patches, CRCs and the .mra text.
"""

from __future__ import annotations

import argparse
import binascii
import json
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MRA_PATH = HERE / "mister" / "Mars Matrix Overpowered.mra"
WEB_PATH = HERE / "index.html"
TRAP15 = HERE / "trap15.py"
ASM_DIR = HERE / "asm"

# Output name in mmatrixop.zip -> entry name in MAME's mmatrix.zip (Japanese set mmatrixj)
FILES = {
    "mmatrixj.key": "mmatrixj/mmatrixj.key",
    "mmxj.03": "mmatrixj/mmxj.03",
    "mmxj.04": "mmatrixj/mmxj.04",
    "mmxj.05": "mmatrixj/mmxj.05",
    "mmx.01": "mmx.01",
    **{f"mmx.{n}m": f"mmx.{n}m" for n in range(11, 21)},
}
# 68000 program ROMs: each file holds 0x80000 bytes of the address space,
# with the bytes of every 16-bit word swapped.
PROGRAM_ROMS = (("mmxj.03", 0x000000), ("mmxj.04", 0x080000), ("mmxj.05", 0x100000))


def crc32(data: bytes) -> str:
    return f"{binascii.crc32(data) & 0xffffffff:08x}"


def mra_date_build(path: Path = MRA_PATH) -> tuple[str, int]:
    m = re.search(r"<name>[^<]*\((\d\d/\d\d/\d\d) Build (\d+)\)</name>",
                  path.read_text(encoding="utf-8"))
    if not m:
        raise RuntimeError(f"No '(YY/MM/DD Build N)' found in <name> of {path}")
    return m.group(1), int(m.group(2))


# ---------------------------------------------------------------------------
# 68000 address-space access to the (encrypted) program ROMs. Data such as
# text is not encrypted on CPS2, so it can be patched in place.

def rom_location(addr: int) -> tuple[str, int]:
    for name, base in PROGRAM_ROMS:
        if base <= addr < base + 0x80000:
            return name, addr - base
    raise ValueError(f"Address {addr:#x} is outside the program ROMs")


def read_bytes(roms: dict, addr: int, length: int) -> bytes:
    out = bytearray()
    for a in range(addr, addr + length):
        name, off = rom_location(a)
        out.append(roms[name][off ^ 1])
    return bytes(out)


def write_bytes(roms: dict, addr: int, data: bytes) -> None:
    for i, b in enumerate(data):
        name, off = rom_location(addr + i)
        roms[name][off ^ 1] = b


# ---------------------------------------------------------------------------
# Code patches. CPS2 encrypts every word the 68000 fetches as code (opcodes and
# their immediates), per address, with mmatrixj.key. We patch trap15's
# decrypted code image (build/code_out.bin from its work folder), re-encrypt the
# whole image with trap15's bundled encrypt.exe, and copy only the changed
# words into the ROMs.

class CodePatcher:
    def __init__(self, root: Path, image: str = "code_out.bin"):
        # root: .../mmxi_v1.0.0_20250412 in trap15's work folder.
        # image: linear decrypted program to patch: "code_out.bin" = with trap15's
        # code, "code_in.bin" = the original game (for the --shmupmame build).
        self.root = root
        self.build = root / "build"
        self.code = bytearray((self.build / image).read_bytes())
        self.ranges = []

    def patch(self, addr: int, old_hex: str, new_hex: str) -> None:
        old, new = bytes.fromhex(old_hex), bytes.fromhex(new_hex)
        if addr % 2 or len(old) % 2 or len(old) != len(new):
            raise ValueError(f"Code patch at {addr:#x} must be whole words")
        if self.code[addr:addr + len(old)] != old:
            raise RuntimeError(f"Code at {addr:#x}: expected {old_hex}, "
                               f"found {self.code[addr:addr + len(old)].hex()}")
        self.code[addr:addr + len(new)] = new
        self.ranges.append((addr, len(new)))

    def place(self, roms: dict, addr: int, data: bytes) -> None:
        """New code in free ROM space: the ROM bytes there must all be zero (unused)."""
        if addr % 2 or len(data) % 2:
            raise ValueError(f"New code at {addr:#x} must be whole words")
        if any(read_bytes(roms, addr, len(data))):
            raise RuntimeError(f"ROM space at {addr:#x} (+{len(data):#x}) is not free")
        self.code[addr:addr + len(data)] = data
        self.ranges.append((addr, len(data)))

    def assemble(self, source: Path) -> tuple[dict, callable]:
        """Assemble with trap15's AS. Returns (symbols, bytes_at(start, end))."""
        asbin = self.root / "tools" / "as" / "bin"
        work = self.build / "op_asm"
        work.mkdir(exist_ok=True)
        src = work / source.name
        src.write_bytes(source.read_bytes())
        subprocess.run([str(asbin / "asw.exe"), src.name, "-U", "-L", "-olist", "out.lst",
                        "-o", "out.p"], cwd=work, check=True, stdout=subprocess.DEVNULL)
        symbols = {}
        for name, value in re.findall(r"\*?\s*([A-Za-z_][\w.]*)\s*:\s+([0-9A-F]+) C \|",
                                      (work / "out.lst").read_text(errors="replace")):
            symbols[name] = int(value, 16)

        def bytes_at(start: int, end: int) -> bytes:
            out = work / f"out_{start:06x}.bin"
            subprocess.run([str(asbin / "p2bin.exe"), "out.p", out.name, "-r",
                            f"${start:X}-${end - 1:X}"], cwd=work, check=True, stdout=subprocess.DEVNULL)
            return out.read_bytes()[:end - start]
        return symbols, bytes_at

    def encrypt_plain(self, roms: dict, start: int, end: int, expect_hex: str) -> None:
        """Code stored UNENCRYPTED in the ROM (never run on the arcade): encrypt it in place,
        so the CPU's opcode decryption yields the instructions that are there as plain bytes."""
        plain = read_bytes(roms, start, end - start)
        if not plain.startswith(bytes.fromhex(expect_hex)):
            raise RuntimeError(f"Plain code at {start:#x} is not what was expected")
        self.code[start:end] = plain
        self.ranges.append((start, end - start))

    def _tool(self, exe: str, *args: str) -> None:
        subprocess.run([str(self.root / "tools" / exe), *args], cwd=self.root, check=True,
                       stdout=subprocess.DEVNULL)

    def commit(self, roms: dict) -> None:
        if not self.ranges:
            return
        (self.build / "op_code.bin").write_bytes(self.code)
        self._tool("romfuck.exe", "s", "build/op_code_prep.bin", "build/op_code.bin")
        self._tool("encrypt.exe", "build/op_enc.bin", "build/op_code_prep.bin",
                   "orig/mmxj.key", "0x000000")
        self._tool("romfuck.exe", "s", "build/op_enc_lin.bin", "build/op_enc.bin")
        enc = (self.build / "op_enc_lin.bin").read_bytes()
        # Sanity check: an untouched word next to each patch must encrypt to what the ROM has.
        for addr, n in self.ranges:
            probe = addr - 2
            if enc[probe:probe + 2] != read_bytes(roms, probe, 2):
                raise RuntimeError(f"Encryption check failed near {addr:#x}")
            write_bytes(roms, addr, enc[addr:addr + n])


# ---------------------------------------------------------------------------
# Tweaks

def warning_screen(roms: dict, date: str, build: int) -> None:
    """Boot warning screen: title, date and build. 25-character centred fields, NUL-terminated."""
    fields = {
        0x156BCA: "MARS MATRIX OVERPOWERED",   # was "MARS MATRIX"
        0x156B1C: date,                        # trap15: "00/04/12 + 25/04/12"
        0x156BE4: f"BUILD {build}",           # was "J A P A N"
    }
    for addr, text in fields.items():
        field = text.center(25).encode("ascii")
        if len(field) != 25:
            raise RuntimeError(f"Warning screen text too long (max 25): {text!r}")
        if read_bytes(roms, addr + 25, 1) != b"\0":
            raise RuntimeError(f"Unexpected data after warning text field {addr:#x}")
        write_bytes(roms, addr, field)


def chain_bar_half_drain(roms: dict) -> None:
    """Chain counter bar (the "+N" under EXP) drains half as fast.

    On each cube pickup the routine at $11E958 loads a timer from this table
    into player+$88 ($FF44A0); $11EA56 subtracts 1 per frame, and the chain
    resets when it reaches 0. Table entries: [bcd chain step, frames], plain data.
    """
    table = 0x11E9C4
    old = [90, 120, 150, 180, 250]
    for i, frames in enumerate(old):
        addr = table + i * 4 + 2
        cur = int.from_bytes(read_bytes(roms, addr, 2), "big")
        if cur != frames:
            raise RuntimeError(f"Chain timer table at {addr:#x}: expected {frames}, found {cur}")
        write_bytes(roms, addr, (frames * 2).to_bytes(2, "big"))


def ghb_code_patches(code: CodePatcher) -> None:
    """GHB (Gravity Hole Bomb) gauge, player+$7E ($FF4496), full = $4000."""
    # Refill twice as fast: addi.w #$20,$7E(a6) -> addi.w #$40,$7E(a6)
    code.patch(0x11EBEE, "066e0020007e", "066e0040007e")
    # Usable any time: holding button 1 only charged GHB when the gauge was
    # exactly full (cmpi.w #$4000,$7E(a6) / bne). Now it needs at least $400,
    # the cost taken when GHB starts (cmpi.w #$0400,$7E(a6) / bcs).
    code.patch(0x11EB24, "0c6e4000007e666e", "0c6e0400007e656e")


def bullet_cancel(roms: dict, code: CodePatcher) -> None:
    """Killing an enemy cancels nearby bullets into cubes, chaining outward.

    Source: asm/bullet_cancel.asm. It hooks the shared "enemy killed" routine at
    $3222A (score/EXP add, a6 = enemy) and puts the new routine in free ROM.
    """
    syms, bytes_at = code.assemble(ASM_DIR / "bullet_cancel.asm")
    hook, hook_end = syms["bc_hook"], syms["bc_hook_end"]
    start, end = syms["bc_enemy_killed"], syms["bc_end"]
    end += end % 2
    code.patch(hook, "48e7c000202e0060", bytes_at(hook, hook_end).hex())
    code.place(roms, start, bytes_at(start, end))


# ---------------------------------------------------------------------------
# Graphics. MAME loads the 8 gfx ROMs ROM_LOAD64_WORD (4 per 16MB half, 2 bytes
# each per 8-byte group), then "unshuffles" every 2MB bank. A 16x16 sprite tile
# is 128 bytes of the result: 16 rows x 8 bytes, each half-row 4 bytes = 4
# bitplanes (byte 3 = bit 3 ... byte 0 = bit 0), leftmost pixel in bit 7.
# Sprite tile code = code word + ((attr & $6000) << 3).

GFX_ROMS = (("mmx.13m", "mmx.15m", "mmx.17m", "mmx.19m"), ("mmx.14m", "mmx.16m", "mmx.18m", "mmx.20m"))
_gfx_perm = None


def gfx_perm():
    """decoded 8-byte unit i of a 2MB bank comes from raw unit perm[i]."""
    global _gfx_perm
    if _gfx_perm is None:
        import numpy as np

        def rec(x):
            if len(x) == 2:
                return x
            h = len(x) // 2
            l, r = rec(x[:h]), rec(x[h:])
            q = h // 2
            return np.concatenate([l[:q], r[:q], l[q:], r[q:]])
        _gfx_perm = rec(np.arange(0x200000 // 8))
    return _gfx_perm


def gfx_loc(offset: int) -> tuple[str, int]:
    """Decoded gfx byte offset -> (ROM name, file offset)."""
    bank, o = divmod(offset, 0x200000)
    raw = bank * 0x200000 + int(gfx_perm()[o // 8]) * 8 + o % 8
    half, r = divmod(raw, 0x1000000)
    return GFX_ROMS[half][(r % 8) // 2], (r // 8) * 2 + r % 2


def gfx_read_tile(roms: dict, code: int) -> list:
    rows = []
    for y in range(16):
        row = []
        for h in range(2):
            b = [roms[n][o] for n, o in (gfx_loc(code * 128 + y * 8 + h * 4 + i) for i in range(4))]
            row += [(((b[3] >> (7 - x)) & 1) << 3) | (((b[2] >> (7 - x)) & 1) << 2) |
                    (((b[1] >> (7 - x)) & 1) << 1) | ((b[0] >> (7 - x)) & 1) for x in range(8)]
        rows.append(row)
    return rows


def gfx_write_tile(roms: dict, code: int, rows: list) -> None:
    for y in range(16):
        for h in range(2):
            b = [0, 0, 0, 0]
            for x in range(8):
                v = rows[y][h * 8 + x]
                for p in range(4):
                    b[p] |= ((v >> p) & 1) << (7 - x)
            for i in range(4):
                n, o = gfx_loc(code * 128 + y * 8 + h * 4 + i)
                roms[n][o] = b[i]


def red_ship_speed(roms: dict, code: CodePatcher) -> None:
    """Mosquito 01 (red) gets Mosquito 02's (blue) top speed, and 5 MAX SPEED boxes.

    Player init $11D44C: move.w #$1A,$74(a6) (speed 26 = 3.25 px/frame), then
    if the ship (player+$70, from game struct +$3E/+$64) is Mosquito 02 it is
    overwritten with #$1F (3.875 px/frame).
    """
    code.patch(0x11D4A2, "3d7c001a0074", "3d7c001f0074")

    # Ship select stats sprite (values column): 5x5 tiles at code $217BA for
    # Mosquito 01 ($2180A for 02), drawn from the list at $163E5E, attr $4413.
    # MAX SPEED boxes: rows 25-29, 9 px apart from x=35. Red has 3; copy box 3
    # (x 53-61) to x 62 and 71, where blue has its 4th and 5th boxes.
    base = 0x217BA
    tiles = {(r, c): gfx_read_tile(roms, base + r * 16 + c) for r in range(5) for c in range(5)}
    px = lambda y, x: tiles[(y // 16, x // 16)][y % 16][x % 16]

    def setpx(y, x, v):
        tiles[(y // 16, x // 16)][y % 16][x % 16] = v
    for y in range(25, 30):
        if any(px(y, x) != 15 for x in range(62, 80)):
            raise RuntimeError("Mosquito 01 stats sprite: space for extra speed boxes is not empty")
        for x in range(9):
            setpx(y, 62 + x, px(y, 53 + x))
            setpx(y, 71 + x, px(y, 53 + x))
    for (r, c), rows in tiles.items():
        gfx_write_tile(roms, base + r * 16 + c, rows)


def qsound_plain_stereo(roms: dict) -> None:
    """Sound effects no longer sound out of phase: turn off QSound's 3D virtualizer.

    At boot the Z80 (mmx.01, loop at $00AB) writes 12 QSound DSP registers from
    a register list at $00D5 and a value table at $00E1 (little-endian words).
    $E4/$E6 are the "wet" (3D crosstalk-cancelling) levels and $E5/$E7 the
    "dry" levels, all $3FFF. The wet path puts anti-phase sound into the other
    channel (L/R correlation down to -0.94 during play). Wet = 0 leaves plain
    stereo with the game's normal panning.
    """
    z80 = roms["mmx.01"]
    regs = z80[0x00D5:0x00E1]
    for reg in (0xE4, 0xE6):
        off = 0x00E1 + 2 * regs.index(reg)
        if z80[off:off + 2] != b"\xff\x3f":
            raise RuntimeError(f"QSound init value for register {reg:#x} is not $3FFF")
        z80[off:off + 2] = b"\x00\x00"


def sfx_centered(roms: dict, code: CodePatcher) -> None:
    """Sound effects play centered instead of hard left (source: asm/sfx_center.asm)."""
    syms, bytes_at = code.assemble(ASM_DIR / "sfx_center.asm")
    z80 = roms["mmx.01"]
    old_site = bytes.fromhex("dd5e473a08f0b720021e10")
    for name in ("sc_hook1", "sc_hook2"):
        start, end = syms[name], syms[name + "_end"]
        if z80[start:end] != old_site:
            raise RuntimeError(f"Z80 pan code at {start:#x} is not what was expected")
        z80[start:end] = bytes_at(start, end)
    start, end = syms["sfx_pan"], syms["sc_end"]
    if any(z80[start:end]):
        raise RuntimeError(f"Z80 ROM space at {start:#x} is not free")
    z80[start:end] = bytes_at(start, end)


def title_overpowered(roms: dict, code: CodePatcher) -> None:
    """"OVERPOWERED" under the title logo (source: asm/title_text.asm)."""
    syms, bytes_at = code.assemble(ASM_DIR / "title_text.asm")
    hook, hook_end = syms["tt_hook"], syms["tt_hook_end"]
    code.patch(hook, "3f3c001f4eb900152228", bytes_at(hook, hook_end).hex())
    start, end = syms["tt_title_text"], syms["tt_code_end"]
    code.place(roms, start, bytes_at(start, end + end % 2))
    s, e = syms["tt_string"], syms["tt_string_end"]
    if any(read_bytes(roms, s, e - s)):
        raise RuntimeError(f"ROM space at {s:#x} is not free")
    write_bytes(roms, s, bytes_at(s, e))          # data: stays unencrypted


def extra_lives(roms: dict, code: CodePatcher) -> None:
    """An extra life every 10,000,000,000 points (source: asm/extend.asm)."""
    syms, bytes_at = code.assemble(ASM_DIR / "extend.asm")
    hook, hook_end = syms["ex_hook"], syms["ex_hook_end"]
    code.patch(hook, "48e780c05c48", bytes_at(hook, hook_end).hex())
    start, end = syms["ex_add"], syms["ex_code_end"]
    code.place(roms, start, bytes_at(start, end + end % 2))


# ---------------------------------------------------------------------------
# Dreamcast Arrange mode enemy layouts

DC_ZIP_DEFAULT = HERE / "roms" / "Mars Matrix DC.zip"
DC_BASE = 0x8C010000                    # 00MMXDC.BIN load address
# Arrange stage spawn lists in 00MMXDC.BIN (table at $8C033650, one per stage)
DC_ARRANGE_LISTS = (0x8C148B40, 0x8C14B01C, 0x8C14DD28, 0x8C14FA7C, 0x8C15104C, 0x8C153504)
ARC_STAGE_TABLE = 0x14CEEC              # 6 x $40: name[8], ..., +$18 events, +$1C list A, +$20 list B
ARC_MISSING_CLASSES = set()             # every Dreamcast-only class is ported (asm/hanabi.asm): $74 Hanabi, $75 TELPO, $76 Zan
ARC_CLASS_TABLE = 0x32676               # spawn class -> enemy descriptor
PORTED_CLASSES = ((0x74, "hb_desc"), (0x75, "tp_desc"), (0x76, "zn_desc"))   # spawn class -> descriptor symbol
ARR_TABLE = 0x172F20                    # Arrange copy of the stage table (6 x $40), used when MODE = ARRANGE
ARRANGE_REGIONS = ((0x1730A0, 0x178000), (0x178400, 0x17CF00))   # free ROM (all zero) for scripts/lists; $17CF00-$17CFFF: extend.asm
# $178000-$1783FF: bullet_cancel, title_text, mode_menu code; $17D000-$17FDFF: Hanabi/Chubi


DC_FILES = ("00MMXDC.BIN", "CG.MMX", "PAL.MMX")   # program, sprite tiles, palettes


def read_dc_files(path: Path) -> dict:
    """Read DC_FILES from the Dreamcast disc: a .zip of the GDI dump or a track03.bin
    (or a folder holding the extracted files)."""
    if path.is_dir():
        return {n: (path / n).read_bytes() for n in DC_FILES}

    def sectors(stream, wanted):              # read sector LBAs (track 3 starts at 45000) in order
        out, pos = {}, 0
        for lba in sorted(wanted):
            off = (lba - 45000) * 2352 + 16
            if off < pos:
                raise RuntimeError("sector order")
            if hasattr(stream, "seekable") and stream.seekable():
                stream.seek(off)
            else:
                stream.read(off - pos)
            out[lba] = stream.read(2048)
            pos = off + 2048
        return out

    def open_track():
        if path.suffix.lower() == ".zip":
            z = zipfile.ZipFile(path)
            name = next(n for n in z.namelist() if n.lower().endswith("track03.bin"))
            return z.open(name)
        return open(path, "rb")

    # pass 1: volume descriptor + root directory
    with open_track() as t:
        pvd = sectors(t, [45016])[45016]
    root_lba, root_len = struct.unpack_from("<I", pvd, 158)[0], struct.unpack_from("<I", pvd, 166)[0]
    with open_track() as t:
        root = b"".join(sectors(t, range(root_lba, root_lba + (root_len + 2047) // 2048)).values())
    found, i = {}, 0
    while i < root_len:
        n = root[i]
        if n == 0:
            i = (i // 2048 + 1) * 2048
            continue
        name = root[i + 33:i + 33 + root[i + 32]].split(b";")[0].decode("latin-1")
        if name in DC_FILES:
            found[name] = (struct.unpack_from("<I", root, i + 2)[0], struct.unpack_from("<I", root, i + 10)[0])
        i += n
    missing = [n for n in DC_FILES if n not in found]
    if missing:
        raise RuntimeError("Not found on the Dreamcast disc: " + ", ".join(missing))
    want = sorted({lba + k for lba, size in found.values() for k in range((size + 2047) // 2048)})
    with open_track() as t:
        sec = sectors(t, want)
    files = {n: b"".join(sec[lba + k] for k in range((size + 2047) // 2048))[:size]
             for n, (lba, size) in found.items()}
    if files["00MMXDC.BIN"].find(b"ARRANGE MODE (A)") < 0:
        raise RuntimeError("00MMXDC.BIN doesn't look like Mars Matrix (Japan)")
    return files


def fix_unencrypted_kaiten2(roms: dict, code: CodePatcher) -> None:
    """Class $73 "KAITEN2" (used by Arrange stage 4, never by the arcade stages):
    its sprite routine at $13D21C-$13D29D (descriptor $13C6F8, 4th pointer) was
    left unencrypted in the arcade ROM. Run as-is it decrypts to garbage, raises
    a CPU exception and the game hangs in the trap loops at $14FA4A. Every other
    enemy routine the Arrange layouts use is encrypted normally.
    """
    code.encrypt_plain(roms, 0x13D21C, 0x13D29E, "302e0012322e0016")


def arrange_layouts(roms: dict, dcf: dict) -> dict:
    """Replace the 6 arcade stages' enemy spawn lists with the Dreamcast Arrange mode's.

    Arcade spawn record (14 bytes, big-endian): time.w (frame/8), x.w, y.w,
    flags.b, class.b (index into spawn table $32676), script.l, c.b, d.b.
    The reader ($14C94E) walks list A ($FF0BF8) and list B ($FF0BF4) in
    parallel. Dreamcast record (20 bytes, little-endian): the same fields as
    words + pad, script as a DC address; lists end at time $7FFF and the
    arcade's lists A and B are merged into one. Behaviour scripts are the
    arcade's bytecode stored verbatim, with no absolute addresses, so each
    stage's script blob (just before its list) is copied as-is.
    """
    dc = dcf["00MMXDC.BIN"]

    def dcw(a, fmt):
        return struct.unpack_from(fmt, dc, a - DC_BASE)

    regions = [list(r) for r in ARRANGE_REGIONS]

    def alloc(size):
        size += size & 1
        for r in regions:
            if r[1] - r[0] >= size:
                a = r[0]
                r[0] += size
                if any(read_bytes(roms, a, size)):
                    raise RuntimeError(f"ROM space at {a:#x} is not free")
                return a
        raise RuntimeError("Not enough free ROM for the Arrange layouts")

    if any(read_bytes(roms, ARR_TABLE, 6 * 0x40)):
        raise RuntimeError(f"ROM space at {ARR_TABLE:#x} is not free")
    write_bytes(roms, ARR_TABLE, read_bytes(roms, ARC_STAGE_TABLE, 6 * 0x40))   # start as a copy of the arcade table
    end_rec = struct.pack(">HHHBBIBB", 0x7FFF, 0, 0, 0, 0, 0, 0, 0)
    empty = alloc(len(end_rec))
    write_bytes(roms, empty, end_rec)

    stats = {}
    for s, head in enumerate(DC_ARRANGE_LISTS):
        recs, a = [], head
        while True:
            t, x, y, fl, cl, pad = dcw(a, "<6H")
            sc, = dcw(a + 12, "<I")
            c, d = dcw(a + 16, "<2H")
            if t == 0x7FFF:
                break
            if max(fl, cl, c, d) > 0xFF or pad:
                raise RuntimeError(f"Unexpected Arrange record at {a:#x}")
            recs.append((t, x, y, fl, cl, sc, c, d))
            a += 20
        lo = min(r[5] for r in recs)
        blob = dc[lo - DC_BASE:head - DC_BASE]
        base = alloc(len(blob))
        write_bytes(roms, base, blob)
        kept = [r for r in recs if r[4] not in ARC_MISSING_CLASSES]
        out = b"".join(struct.pack(">HHHBBIBB", t, x, y, fl, cl, base + (sc - lo), c, d)
                       for t, x, y, fl, cl, sc, c, d in kept) + end_rec
        lst = alloc(len(out))
        write_bytes(roms, lst, out)
        entry = ARR_TABLE + s * 0x40
        if read_bytes(roms, entry, 7) != f"STAGE {s + 1}".encode():
            raise RuntimeError(f"Stage table entry {s + 1} not found")
        write_bytes(roms, entry + 0x1C, struct.pack(">II", empty, lst))   # list A = empty, list B = Arrange
        stats[s + 1] = (len(recs), len(recs) - len(kept), base, lst)
    dc_sprites(roms, dcf)
    return stats


# Hanabi/Chubi/Shobi graphics: Dreamcast-only art, imported from the disc.
# CG.MMX: tile index -> u32 offset table (bit 31 = flag), LZ-compressed tiles from
# CG_DATA; each tile unpacks to 128 bytes = 16x16 4bpp, twiddled (Morton order,
# y bit lowest), colour 0 transparent. PAL.MMX: 16-colour palettes, ARGB1555 LE.
# A DC sprite entry's tile number is (word 3 << 16) | word 4.
CG_DATA = 0xC828C
DC_SPRITE_GROUPS = (                        # DC sprite table, entries, arcade tile base (empty rows), arcade table
    (0x8C1ED9EC, 32, 0x2D3E0, 0x17F000),    # Hanabi 4x3 frames, DC tiles $1C10..
    (0x8C1EDBEC, 32, 0x37230, 0x17F200),    # Chubi 2x2,  DC tiles $2394E..
    (0x8C1EDDEC, 32, 0x3D4A0, 0x17F400),    # Shobi 1x1,  DC tiles $23D4E..
    (0x8C1F0A44, 18, 0x372B0, 0x17F600),    # TELPO: 16 warp frames 4x2, body 4x2, marker 3x2
    (0x8C1F1750, 12, 0x3D4C0, 0x17F720),    # Zan/Zc/Zz: 12 spin frames 2x2 (after Shobi's 2 rows)
)
ARC_PALETTE_SLOTS = range(0x3F0, 0x400)     # handed out in order of first use
DC_SPRITE_DX, DC_SPRITE_DY = 64, -16      # arcade sprite origin vs the DC's (x = 64 - w/2 vs -w/2, y = -(240 - h/2) vs -(224 - h/2))
ARC_PALETTES = 0x70996                      # 32 bytes per palette; $2C0-$3FF are unused filler copies


def cg_tile(cg: bytes, code: int) -> bytes:
    """Decompress one Dreamcast tile (port of $8C110474)."""
    st = [CG_DATA + (struct.unpack_from("<I", cg, code * 4)[0] & 0x7FFFFFFF), 0, 0]  # ptr, byte, bits left
    out = bytearray()

    def bit():
        st[2] -= 1
        if st[2] < 0:
            st[1], st[0], st[2] = cg[st[0]], st[0] + 1, 7
        return (st[1] >> st[2]) & 1
    width, limit = 0, 1
    while len(out) < 128:
        while width < 12 and limit < len(out):
            width, limit = width + 1, limit << 1
        if not bit():
            out.append(cg[st[0]])
            st[0] += 1
            continue
        n = 0
        while True:
            n = n * 2 + bit()
            if bit():
                break
        n += 1
        off = 0
        for _ in range(5 if n == 1 and width > 5 else width):
            off = off * 2 + bit()
        for _ in range(n):
            out.append(out[-off - 1])
    return bytes(out[:128])


def cg_pixels(tile: bytes) -> list:
    """16x16 rows of arcade pixel values (DC colour c -> arcade c-1, so 0 -> 15 = transparent)."""
    rows = []
    for y in range(16):
        row = []
        for x in range(16):
            i = 0
            for b in range(4):
                i |= ((y >> b) & 1) << (2 * b) | ((x >> b) & 1) << (2 * b + 1)
            row.append((((tile[i >> 1] >> (4 * (i & 1))) & 15) - 1) & 15)
        rows.append(row)
    return rows


def dc_palette(pal: bytes, n: int) -> bytes:
    """DC palette n (ARGB1555) -> arcade palette (brightness/R/G/B nibbles), colours shifted down one."""
    out = bytearray()
    for j in range(16):
        v = struct.unpack_from("<H", pal, n * 32 + ((j + 1) & 15) * 2)[0]
        out += struct.pack(">H", 0xF000 | ((v >> 11) & 15) << 8 | ((v >> 6) & 15) << 4 | ((v >> 1) & 15))
    return bytes(out)


def dc_sprites(roms: dict, dcf: dict) -> None:
    """Copy the Dreamcast-only enemies' sprite frames into empty arcade tile rows and
    palette slots, and write each sprite table in arcade form.
    DC entry: x.w, y.w, prio.w, tile-high.w, tile.w, palette.w, size.w, 0 (little-endian).
    Arcade entry: x+64, y-16, prio, bank << 13, tile.w, palette slot, size, 0 (big-endian).
    Frames are packed left to right in 16-tile rows; a frame that doesn't fit, or has a
    different height, starts a new band of rows."""
    dc, cg, pal = dcf["00MMXDC.BIN"], dcf["CG.MMX"], dcf["PAL.MMX"]
    filler = read_bytes(roms, ARC_PALETTES + 0x3FF * 32, 32)
    slots, free = {}, iter(ARC_PALETTE_SLOTS)
    for src_table, count, base, dst_table in DC_SPRITE_GROUPS:
        table, row, col, band = bytearray(), 0, 0, 0
        for k in range(count):
            w = struct.unpack_from("<8H", dc, src_table - DC_BASE + k * 16)
            fw, fh = ((w[6] >> 8) & 15) + 1, ((w[6] >> 12) & 15) + 1
            if w[7] or w[2] & 0x1FFF:
                raise RuntimeError("Unexpected sprite table in the Dreamcast program")
            if col + fw > 16 or (band and fh != band):
                row, col, band = row + band, 0, 0
            dst = base + row * 16 + col
            col, band = col + fw, max(band, fh)
            src = w[3] << 16 | w[4]
            for ty in range(fh):
                for tx in range(fw):
                    code = dst + tx + 16 * ty
                    if any(v != 15 for r in gfx_read_tile(roms, code) for v in r):
                        raise RuntimeError(f"Arcade tile {code:#x} is not empty")
                    gfx_write_tile(roms, code, cg_pixels(cg_tile(cg, src + tx + 16 * ty)))
            dcpal = w[5] & 0x7FF
            if dcpal not in slots:
                slot = slots[dcpal] = next(free)
                if read_bytes(roms, ARC_PALETTES + slot * 32, 32) != filler:
                    raise RuntimeError(f"Arcade palette {slot:#x} is in use")
                write_bytes(roms, ARC_PALETTES + slot * 32, dc_palette(pal, dcpal))
            table += struct.pack(">8H", (w[0] + DC_SPRITE_DX) & 0xFFFF, (w[1] + DC_SPRITE_DY) & 0xFFFF,
                                 w[2], (dst >> 16) << 13, dst & 0xFFFF, slots[dcpal], w[6], 0)
        if any(read_bytes(roms, dst_table, len(table))):
            raise RuntimeError(f"ROM space at {dst_table:#x} is not free")
        write_bytes(roms, dst_table, bytes(table))


# Funsha2 (class $AC, the white fighters before the Arrange stage 3 boss; never
# used by the arcade stages): its frames 168-173 (table $13AF96, entries at $13BA16)
# have a stray line on their bottom pixel row, a small dash under the fighter.
# The Dreamcast's frames are transparent there. Tile -> (x, y) pixels to clear.
FUNSHA2_STRAY_PIXELS = {
    0x24F80: [(14, 15), (15, 15)],
    0x24F81: [(x, 15) for x in range(0, 6)],
    0x24FA1: [(x, 15) for x in range(1, 10)],
    0x24FC1: [(x, 15) for x in range(4, 12)],
    0x24FE1: [(x, 15) for x in range(7, 14)],
    0x25001: [(x, 15) for x in range(10, 16)],
    0x25021: [(15, 15)],
    0x25022: [(0, 15), (1, 15)],
}


def funsha2_stray_line(roms: dict) -> None:
    """Clear the stray bottom-row pixels in Funsha2's frames 168-173 (no other sprite
    uses these 8 tiles)."""
    for code, pixels in FUNSHA2_STRAY_PIXELS.items():
        rows = gfx_read_tile(roms, code)
        for x, y in pixels:
            if rows[y][x] == 15:
                raise RuntimeError(f"Funsha2 tile {code:#x} pixel ({x},{y}) is already clear")
            rows[y][x] = 15
        gfx_write_tile(roms, code, rows)


def mode_menu(roms: dict, code: CodePatcher) -> None:
    """ORIGINAL / ARRANGE select on the credited title screen (source: asm/mode_menu.asm).
    ORIGINAL = arcade stage table $14CEEC, ARRANGE = the copy at ARR_TABLE."""
    syms, bytes_at = code.assemble(ASM_DIR / "mode_menu.asm")
    for hook, old in (("mm_hook_title", "700148562c6e00104eb9001619522c5f"),
                      ("mm_hook_stage", "41fa0844d0f900ff0ba0")):
        a, b = syms[hook], syms[hook + "_end"]
        code.patch(a, old, bytes_at(a, b).hex())
    a, b = syms["mm_frame"], syms["mm_code_end"]
    code.place(roms, a, bytes_at(a, b + b % 2))
    a, b = syms["mm_strings"], syms["mm_strings_end"]
    if any(read_bytes(roms, a, b - a)):
        raise RuntimeError(f"ROM space at {a:#x} is not free")
    write_bytes(roms, a, bytes_at(a, b))          # data: stays unencrypted


def hanabi_port(roms: dict, code: CodePatcher) -> None:
    """Dreamcast-only enemies Hanabi (class $74), Chubi and Shobi, translated to
    68000 (source: asm/hanabi.asm). Code at $17D000, descriptors at $17F800;
    the sprite frames are copied from the Dreamcast disc by arrange_layouts()."""
    syms, bytes_at = code.assemble(ASM_DIR / "hanabi.asm")
    a, b = syms["hb_nop"], syms["hb_code_end"]
    code.place(roms, a, bytes_at(a, b + b % 2))
    a, b = syms["hb_descs"], syms["hb_descs_end"]
    if any(read_bytes(roms, a, b - a)):
        raise RuntimeError(f"ROM space at {a:#x} is not free")
    write_bytes(roms, a, bytes_at(a, b))          # data: stays unencrypted
    # Class $A9 (arcade "Kame_Musi" = DC "Kame", the blue beetles of Arrange stage 3):
    # the DC's death code drops a gold cube ($8C011208 = $3930E, size 0) after the
    # ground wreck ($8C011E00 = $3B716); the arcade's ($13D494) has no cube drop.
    # Its sound call jsr $151E5E at $13D4FE becomes jsr kame_drop (cube, then the sound).
    code.patch(0x13D4FE, "4eb900151e5e", f"4eb9{syms['kame_drop']:08x}")
    # Class $73 KAITEN2: the DC's hit routine drops a big gold cube (size 2); the
    # arcade's ($13D42C) doesn't. bset #0,$D(a6) there becomes jsr kaiten_hit.
    code.patch(0x13D42C, "08ee0000000d", f"4eb9{syms['kaiten_hit']:08x}")
    code.patch(0x12425E, "4eb900151e5e", f"4eb9{syms['bigi_drop']:08x}")   # Big_I: size-3 cube
    # gold cube sizes (d4 for $3930E) that differ from the Dreamcast: size 1 -> 2
    for a in (0x12C23C, 0x12CE24, 0x1366CE):   # SoftBall, BEE_ZAKO, CHU_Z800
        code.patch(a, "383c0001", "383c0002")
    code.patch(0x135DAE, "383c0000", "383c0001")   # CHOZ: size 0 -> 1
    code.patch(0x144774, "4eb90003930e", f"4eb9{syms['une_drop']:08x}")   # Une: + spread cube
    for cls, sym in PORTED_CLASSES:
        entry = ARC_CLASS_TABLE + 4 * cls
        if read_bytes(roms, entry, 4) != bytes(4):
            raise RuntimeError(f"Spawn class {cls:#x} is already in use")
        write_bytes(roms, entry, struct.pack(">I", syms[sym]))


def apply_tweaks(roms: dict, code: "CodePatcher", date: str, build: int, dc: dict) -> dict:
    """Apply everything. Returns the ROMs as they were just before the Arrange
    import (the web patcher ships only those patches and redoes the import from
    the visitor's own Dreamcast disc)."""
    warning_screen(roms, date, build)
    chain_bar_half_drain(roms)
    ghb_code_patches(code)
    bullet_cancel(roms, code)
    red_ship_speed(roms, code)
    qsound_plain_stereo(roms)
    sfx_centered(roms, code)
    title_overpowered(roms, code)
    fix_unencrypted_kaiten2(roms, code)
    mode_menu(roms, code)
    extra_lives(roms, code)
    hanabi_port(roms, code)
    code.commit(roms)
    funsha2_stray_line(roms)
    before_arrange = {n: bytes(d) for n, d in roms.items()}
    for st, (n, dropped, scripts, lst) in arrange_layouts(roms, dc).items():
        print(f"  Arrange stage {st}: {n - dropped} spawns ({dropped} dropped), scripts {scripts:#x}, list {lst:#x}")
    return before_arrange


# ---------------------------------------------------------------------------
# Web patcher export

def byte_runs(old: bytes, new: bytes) -> list:
    """Changed byte runs as [offset, new-bytes-hex]; 1-byte gaps are merged."""
    runs, i = [], 0
    while i < len(old):
        if old[i] != new[i]:
            j = i
            while j < len(old) and (old[j] != new[j] or
                                    (j + 1 < len(old) and old[j + 1] != new[j + 1] and j - i < 64)):
                j += 1
            runs.append([i, new[i:j].hex()])
            i = j
        else:
            i += 1
    return runs


def write_web(originals: dict, final: dict, build: int, date: str, before_arrange: dict) -> None:
    """index.html gets: the byte patches up to (not including) the Arrange import,
    the Arrange import settings (the page redoes it from the visitor's Dreamcast
    disc, so no Dreamcast data is published), and the CRCs of the final files."""
    mra = MRA_PATH.read_text(encoding="utf-8")
    patches, crcs = {}, {}
    for name, data in final.items():
        mra = re.sub(rf'(<part name="{re.escape(name)}" crc=")[0-9a-f]{{8}}"',
                     lambda m, c=crc32(data): f'{m.group(1)}{c}"', mra)
        if before_arrange[name] != originals[name]:
            patches[name] = byte_runs(originals[name], before_arrange[name])
        if data != originals[name]:
            crcs[name] = crc32(data)
    arrange = dict(dcBase=DC_BASE, lists=list(DC_ARRANGE_LISTS), stageTable=ARC_STAGE_TABLE, arrTable=ARR_TABLE,
                   missing=sorted(ARC_MISSING_CLASSES), regions=[list(r) for r in ARRANGE_REGIONS],
                   file="mmxj.05", fileBase=0x100000,
                   groups=[list(g) for g in DC_SPRITE_GROUPS], slots=[ARC_PALETTE_SLOTS.start, ARC_PALETTE_SLOTS.stop],
                   cgData=CG_DATA, palettes=ARC_PALETTES, dx=DC_SPRITE_DX, dy=DC_SPRITE_DY,
                   gfx=[list(g) for g in GFX_ROMS], programRoms=[list(r) for r in PROGRAM_ROMS])
    MRA_PATH.write_text(mra, encoding="utf-8", newline="\n")

    html = WEB_PATH.read_text(encoding="utf-8")
    crc_js = "{ " + ", ".join(f'"{k}": 0x{v}' for k, v in crcs.items()) + " }"
    for pattern, value in (
        (r"^const BUILD = .*;$", f"const BUILD = {build};"),
        (r"^const PATCHES = .*;$", f"const PATCHES = {json.dumps(patches)};"),
        (r"^const PATCHED_CRC = .*;$", f"const PATCHED_CRC = {crc_js};"),
        (r"^const MRA_TEXT = .*;$", f"const MRA_TEXT = {json.dumps(mra)};"),
        (r"^const ARRANGE = .*;$", f"const ARRANGE = {json.dumps(arrange)};"),
    ):
        html, n = re.subn(pattern, lambda _m, v=value: v, html, flags=re.M)
        if n != 1:
            raise RuntimeError(f"index.html: expected one line matching {pattern}")
    WEB_PATH.write_text(html, encoding="utf-8", newline="\n")
    print(f"Updated {MRA_PATH.name} CRCs and {WEB_PATH.name} (Build {build}, {date}).")


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom_zip", type=Path, help="Your original MAME mmatrix.zip")
    ap.add_argument("patch_zip", type=Path, help="Trap15 mmxi_v1.0.0_20250412.zip")
    ap.add_argument("-o", "--output", type=Path, default=Path("mmatrixop.zip"))
    ap.add_argument("--mame-zip", type=Path,
                    help="Also write a MAME-layout mmatrix.zip (for testing as mmatrixj)")
    ap.add_argument("--shmupmame", type=Path,
                    help="Also write a zip WITHOUT trap15's patch (Overpowered tweaks on the original "
                         "ROMs), for ShmupMAME, which applies trap15 itself when it loads mmatrixj. "
                         "Install it as ShmupMAME's roms/mmatrixj.zip.")
    ap.add_argument("--dc", type=Path, default=DC_ZIP_DEFAULT,
                    help="Dreamcast Mars Matrix (Japan) disc: .zip of the GDI dump, track03.bin or 00MMXDC.BIN "
                         "(source of the Arrange mode enemy layouts; default: roms/Mars Matrix DC.zip)")
    ap.add_argument("--write-web", action="store_true",
                    help="Also update the .mra CRCs and the web patcher (index.html)")
    ns = ap.parse_args()

    date, build = mra_date_build()
    rom_zip = ns.rom_zip.resolve()
    print(f"Reading the Dreamcast disc ({len(DC_FILES)} files) from {ns.dc} ...")
    dc = read_dc_files(ns.dc)

    with tempfile.TemporaryDirectory() as tmp:
        trap15_zip = Path(tmp) / "trap15.zip"
        subprocess.run([sys.executable, str(TRAP15), str(rom_zip), str(ns.patch_zip.resolve()),
                        "-o", str(trap15_zip), "--work", str(Path(tmp) / "work")], check=True)
        with zipfile.ZipFile(rom_zip) as zf:
            originals = {n: zf.read(e) for n, e in FILES.items()}
        with zipfile.ZipFile(trap15_zip) as zf:
            roms = {n: bytearray(zf.read(e)) for n, e in FILES.items()}
        root = Path(tmp) / "work" / "project" / "mmxi_v1.0.0_20250412"
        code = CodePatcher(root)
        before_arrange = apply_tweaks(roms, code, date, build, dc)
        if ns.shmupmame:
            plain = {n: bytearray(d) for n, d in originals.items()}
            apply_tweaks(plain, CodePatcher(root, "code_in.bin"), date, build, dc)
            with zipfile.ZipFile(ns.shmupmame, "w", zipfile.ZIP_DEFLATED) as zf:
                for name, data in plain.items():
                    zf.writestr(name, bytes(data))
            print(f"\nShmupMAME build (no trap15) -> {ns.shmupmame.resolve()}")
            for name, data in plain.items():
                if data != originals[name]:
                    print(f"  patched: {name}: CRC32 {crc32(bytes(data))}")

    final = {n: bytes(d) for n, d in roms.items()}

    print(f"\nMars Matrix Overpowered ({date} Build {build})")
    for name, data in final.items():
        if data != originals[name]:
            print(f"  patched: {name}: CRC32 {crc32(data)}")

    with zipfile.ZipFile(ns.output, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in final.items():
            zf.writestr(name, data)
    print(f"Wrote {ns.output.resolve()}")

    if ns.mame_zip:
        back = {e: final[n] for n, e in FILES.items()}
        with zipfile.ZipFile(rom_zip) as src, zipfile.ZipFile(ns.mame_zip, "w") as dst:
            for info in src.infolist():
                dst.writestr(info, back.get(info.filename) or src.read(info.filename))
        print(f"Wrote {ns.mame_zip.resolve()} (MAME layout)")

    if ns.write_web:
        write_web(originals, final, build, date, before_arrange)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"\ntrap15.py failed with exit code {exc.returncode}.", file=sys.stderr)
        raise SystemExit(exc.returncode)
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
