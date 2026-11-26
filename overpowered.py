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


def apply_tweaks(roms: dict, code: "CodePatcher", date: str, build: int) -> None:
    warning_screen(roms, date, build)
    chain_bar_half_drain(roms)
    ghb_code_patches(code)
    bullet_cancel(roms, code)
    red_ship_speed(roms, code)
    code.commit(roms)


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


def write_web(originals: dict, final: dict, build: int, date: str) -> None:
    mra = MRA_PATH.read_text(encoding="utf-8")
    patches, crcs = {}, {}
    for name, data in final.items():
        mra = re.sub(rf'(<part name="{re.escape(name)}" crc=")[0-9a-f]{{8}}"',
                     lambda m, c=crc32(data): f'{m.group(1)}{c}"', mra)
        if data != originals[name]:
            patches[name] = byte_runs(originals[name], data)
            crcs[name] = crc32(data)
    MRA_PATH.write_text(mra, encoding="utf-8", newline="\n")

    html = WEB_PATH.read_text(encoding="utf-8")
    crc_js = "{ " + ", ".join(f'"{k}": 0x{v}' for k, v in crcs.items()) + " }"
    for pattern, value in (
        (r"^const BUILD = .*;$", f"const BUILD = {build};"),
        (r"^const PATCHES = .*;$", f"const PATCHES = {json.dumps(patches)};"),
        (r"^const PATCHED_CRC = .*;$", f"const PATCHED_CRC = {crc_js};"),
        (r"^const MRA_TEXT = .*;$", f"const MRA_TEXT = {json.dumps(mra)};"),
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
    ap.add_argument("--write-web", action="store_true",
                    help="Also update the .mra CRCs and the web patcher (index.html)")
    ns = ap.parse_args()

    date, build = mra_date_build()
    rom_zip = ns.rom_zip.resolve()

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
        apply_tweaks(roms, code, date, build)
        if ns.shmupmame:
            plain = {n: bytearray(d) for n, d in originals.items()}
            apply_tweaks(plain, CodePatcher(root, "code_in.bin"), date, build)
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
        write_web(originals, final, build, date)
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
