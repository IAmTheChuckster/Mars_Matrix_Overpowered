#!/usr/bin/env python3
"""
Build the Trap15 Mars Matrix Improvement v1.0.0 Japanese ROM set.

This builds from the patch project's included assembly source and its bundled
Windows tools. It does NOT apply the tiny .xdelta3 files (which are not used
by this source-build workflow).

Usage:
  py patch.py mmatrix.zip mmxi_v1.0.0_20250412.zip

Output:
  mmatrixj_trap15_v1.0.0_patched.zip
"""

from __future__ import annotations

import argparse
import binascii
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

EXPECTED_CRC = {
    "mmatrixj/mmatrixj.key": "3b50d889",
    "mmx.01": "c57e8171",
    "mmatrixj/mmxj.03": "1d5de213",
    "mmatrixj/mmxj.04": "d943a339",
    "mmatrixj/mmxj.05": "0c8b4abb",
}

PATCH_ROOT = "mmxi_v1.0.0_20250412"


def crc32(data: bytes) -> str:
    return f"{binascii.crc32(data) & 0xffffffff:08x}"


def safe_extract(zf: zipfile.ZipFile, destination: Path) -> None:
    destination = destination.resolve()
    for info in zf.infolist():
        name = PurePosixPath(info.filename)
        if name.is_absolute() or ".." in name.parts:
            raise RuntimeError(f"Unsafe path in ZIP: {info.filename}")
        target = (destination / Path(*name.parts)).resolve()
        if target != destination and destination not in target.parents:
            raise RuntimeError(f"Unsafe path in ZIP: {info.filename}")
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def run(exe: Path, args: list[str], cwd: Path) -> None:
    cmd = [str(exe), *args]
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom_zip", type=Path, help="Your original MAME mmatrix.zip")
    ap.add_argument("patch_zip", type=Path, help="Trap15 mmxi_v1.0.0_20250412.zip")
    ap.add_argument("-o", "--output", type=Path,
                    default=Path("mmatrixj_trap15_v1.0.0_patched.zip"))
    ap.add_argument("--work", type=Path, default=Path("mmxi_trap15_build"),
                    help="Working directory (default: ./mmxi_trap15_build)")
    ns = ap.parse_args()

    rom_zip = ns.rom_zip.resolve()
    patch_zip = ns.patch_zip.resolve()
    output_zip = ns.output.resolve()
    work = ns.work.resolve()

    if not rom_zip.is_file() or not patch_zip.is_file():
        ap.error("Both input ZIP files must exist.")

    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    original_dir = work / "original"
    project_dir = work / "project"
    original_dir.mkdir()
    project_dir.mkdir()

    with zipfile.ZipFile(rom_zip) as zf:
        names = set(zf.namelist())
        missing = set(EXPECTED_CRC) - names
        if missing:
            raise RuntimeError("ROM ZIP is missing required Japanese ROM entries: "
                               + ", ".join(sorted(missing)))
        originals = {}
        for name, expected in EXPECTED_CRC.items():
            data = zf.read(name)
            actual = crc32(data)
            if actual != expected:
                raise RuntimeError(
                    f"Wrong/unexpected source ROM: {name}: CRC {actual}, "
                    f"expected {expected}. No files were patched."
                )
            originals[name] = data

    with zipfile.ZipFile(patch_zip) as zf:
        safe_extract(zf, project_dir)

    root = project_dir / PATCH_ROOT
    tools = root / "tools"
    assembler = tools / "as" / "bin" / "asw.exe"
    p2bin = tools / "as" / "bin" / "p2bin.exe"
    decrypt = tools / "decrypt.exe"
    encrypt = tools / "encrypt.exe"
    romfuck = tools / "romfuck.exe"

    for required in (assembler, p2bin, decrypt, encrypt, romfuck):
        if not required.is_file():
            raise RuntimeError(f"Required bundled build tool not found: {required}")

    orig = root / "orig"
    build = root / "build"
    out = root / "output"
    orig.mkdir(exist_ok=True)
    build.mkdir(exist_ok=True)
    out.mkdir(exist_ok=True)

    # Stage the exact Japanese encrypted MAME ROMs expected by patch.sh.
    (orig / "mmxj.key").write_bytes(originals["mmatrixj/mmatrixj.key"])
    (orig / "mmxj.01").write_bytes(originals["mmx.01"])
    for suffix in ("03", "04", "05"):
        (orig / f"mmxj.{suffix}").write_bytes(
            originals[f"mmatrixj/mmxj.{suffix}"]
        )

    # Equivalent of the project's tools/patch.sh, using the supplied EXEs.
    run(decrypt, ["build/dec.03", "orig/mmxj.03", "orig/mmxj.key", "0x000000"], root)
    run(decrypt, ["build/dec.04", "orig/mmxj.04", "orig/mmxj.key", "0x080000"], root)
    run(decrypt, ["build/dec.05", "orig/mmxj.05", "orig/mmxj.key", "0x100000"], root)

    (build / "decrypted.bin").write_bytes(
        (build / "dec.03").read_bytes()
        + (build / "dec.04").read_bytes()
        + (build / "dec.05").read_bytes()
    )

    run(romfuck, ["z", "build/z80_in.bin", "orig/mmxj.01", "0x8000"], root)
    run(romfuck, ["s", "build/code_in.bin", "build/decrypted.bin"], root)

    run(assembler, ["src/patch.asm", "-D", "PATCH_CODE", "-i", ".", "-n", "-U",
                    "-L", "-olist", "build/code.lst", "-o", "build/code.obj"], root)
    run(p2bin, ["build/code.obj", "build/code_out.bin",
                "-r", "0x000000-0x17FFFF"], root)

    run(romfuck, ["s", "build/code_out_prep.bin", "build/code_out.bin"], root)
    run(encrypt, ["build/encrypted.bin", "build/code_out_prep.bin",
                  "orig/mmxj.key", "0x000000"], root)
    run(romfuck, ["s", "build/data_in.bin", "build/encrypted.bin"], root)

    run(assembler, ["src/patch.asm", "-D", "PATCH_DATA", "-i", ".", "-n", "-U",
                    "-L", "-olist", "build/data.lst", "-o", "build/data.obj"], root)
    run(p2bin, ["build/data.obj", "build/data_out.bin",
                "-r", "0x000000-0x17FFFF"], root)

    run(assembler, ["src/patch_z80.asm", "-D", "PATCH_Z80", "-i", ".", "-n", "-U",
                    "-L", "-olist", "build/z80.lst", "-o", "build/z80.obj"], root)
    run(p2bin, ["build/z80.obj", "build/z80_out.bin",
                "-r", "0x000000-0x7FFF"], root)

    run(romfuck, ["s", "build/final.bin", "build/data_out.bin"], root)
    run(romfuck, ["Z", "build/final_z80.bin", "build/z80_out.bin",
                  "orig/mmxj.01"], root)
    shutil.copy2(build / "final_z80.bin", out / "mmxj.01")
    run(romfuck, ["x", "output/mmxj.03", "output/mmxj.04",
                  "output/mmxj.05", "build/final.bin"], root)
    shutil.copy2(orig / "mmxj.key", out / "mmxj.key")

    replacements = {
        "mmx.01": (out / "mmxj.01").read_bytes(),
        "mmatrixj/mmxj.03": (out / "mmxj.03").read_bytes(),
        "mmatrixj/mmxj.04": (out / "mmxj.04").read_bytes(),
        "mmatrixj/mmxj.05": (out / "mmxj.05").read_bytes(),
    }

    changed_files = []
    for name, patched in replacements.items():
        changed = patched != originals[name]
        if changed:
            changed_files.append(name)
        status = "changed" if changed else "unchanged (no patch data for this file)"
        print(
            f"{status}: {name}: {len(patched):,} bytes, "
            f"CRC32 {crc32(patched)}"
        )

    # A component ROM is allowed to remain identical. However, if none of
    # the target ROMs changed, the build almost certainly did not apply.
    if not changed_files:
        raise RuntimeError(
            "All four output ROMs are byte-identical to the originals. "
            "No patched archive was created; check the build-tool output."
        )

    # Preserve every other entry in the user's original ROM ZIP unchanged.
    temp_zip = output_zip.with_suffix(output_zip.suffix + ".tmp")
    with zipfile.ZipFile(rom_zip, "r") as src, \
         zipfile.ZipFile(temp_zip, "w") as dst:
        for info in src.infolist():
            data = replacements.get(info.filename)
            if data is None:
                data = src.read(info.filename)
            dst.writestr(info, data)
    temp_zip.replace(output_zip)

    # Re-open and verify all four replacements are present and byte-identical.
    with zipfile.ZipFile(output_zip) as zf:
        for name, expected_data in replacements.items():
            actual = zf.read(name)
            if actual != expected_data:
                raise RuntimeError(f"Output ZIP verification failed for {name}")
    print(f"\nVerified output archive: {output_zip}")
    print("Only the four patched ROM files were replaced; all other ZIP entries were preserved.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"\nBuild tool failed with exit code {exc.returncode}.", file=sys.stderr)
        raise SystemExit(exc.returncode)
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
