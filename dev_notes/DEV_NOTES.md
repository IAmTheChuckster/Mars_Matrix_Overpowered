# Mars Matrix Overpowered — Dev Notes

The full record of this project. With these notes, your own `mmatrix.zip` and the trap15 patch zip, you can rebuild the whole project from scratch. **Update this file with every change.**

## Target

- Game: Mars Matrix: Hyper Solid Shooting (Japan 000412), MAME set `mmatrixj` (a clone inside `mmatrix.zip`), tested on MAME 0.289.
- Output set name: `mmatrixop` → `mmatrixop.zip` (flat file names, no subfolders).
- Hardware: Capcom CPS2. The program ROMs (`mmxj.03`–`.05`) are encrypted with `mmatrixj.key`. `mmx.01` is the Z80 sound program.

### Input files (from `mmatrix.zip`)

| File in zip | Output name | Size | CRC32 |
|---|---|---|---|
| mmatrixj/mmatrixj.key | mmatrixj.key | 20 | 3b50d889 |
| mmatrixj/mmxj.03 | mmxj.03 | 524288 | 1d5de213 |
| mmatrixj/mmxj.04 | mmxj.04 | 524288 | d943a339 |
| mmatrixj/mmxj.05 | mmxj.05 | 524288 | 0c8b4abb |
| mmx.01 | mmx.01 | 131072 | c57e8171 |
| mmx.11m / 12m (QSound) | same | 4194304 | 4180b39f / 95e22a59 |
| mmx.13m–20m (graphics) | same | 4194304 | 04748718, d52bf491, 38074f44, 23f70780, e4635e35, 2562c9d5, 4400a3f2, 583a9687 |

MiSTer also needs `qsound.zip` (`dl-1425.bin`, CRC d6cf5ef5).

## Repository layout

- `trap15.py`: trap15's build only, unchanged from his workflow. Usage: `py trap15.py mmatrix.zip patches/mmxi_v1.0.0_20250412.zip` writes `mmatrixj_trap15_v1.0.0_patched.zip` (MAME layout). It decrypts the program ROMs, assembles `src/patch.asm` and `src/patch_z80.asm` with the patch's bundled Windows tools (asw, p2bin, decrypt, encrypt, romfuck), then re-encrypts. Windows only.
- `overpowered.py`: **all Overpowered tweaks live here.** It runs `trap15.py` into a temp folder, applies `apply_tweaks()` to the trap15 ROMs, and writes `mmatrixop.zip` (flat names, matching the `.mra`). Options: `--mame-zip FILE` also writes a MAME-layout `mmatrix.zip` for testing as `mmatrixj`; `--write-web` updates the `.mra` CRCs and `index.html`. Reads the date and build from the `.mra` `<name>`.
  - Program ROM access: `read_bytes()` / `write_bytes()` take 68000 addresses. `mmxj.03`/`.04`/`.05` hold `0x000000`/`0x080000`/`0x100000` (+`0x80000` each), and the bytes of each 16-bit word are swapped (file offset `(addr - base) ^ 1`). Data (text, tables) is plain. Every word fetched as code (opcodes *and* their immediates/extension words) is CPS2-encrypted per address with the key. Code changes go through `CodePatcher` (see Build 3).
  - To add a tweak: write a function and call it from `apply_tweaks()`.
- Dreamcast disc (input, git-ignored like all ROMs): `roms/Mars Matrix DC.zip`, the Japanese GDI dump (T-1238M V1.000, track03.bin at LBA 45000). Source of the Arrange layouts (Build 10).
- `asm/bullet_cancel.asm`: 68000 source for the bullet-cancel routine (Build 4). `overpowered.py` assembles it with trap15's bundled AS (`asw.exe` + `p2bin.exe`) and reads label addresses from the listing.
- `patches/mmxi_v1.0.0_20250412.zip`: trap15's Mars Matrix Improvement v1.0.0 (source: http://bitbucket.org/trap15/mmatrix_unfuck/).
- `index.html`: the web patcher (GitHub Pages). It takes `mmatrix.zip`, checks all 15 CRCs, applies byte patches and gives you `mmatrixop.zip` plus the `.mra`. It runs entirely in the browser.
- `mister/Mars Matrix Overpowered.mra`: the MiSTer jtcps2 MRA (setname `mmatrixop`, CRCs of the patched files). Its `<name>` is the **single source for the date and build number**, in the form `Mars Matrix Overpowered (YY/MM/DD Build N)`.
- `roms/`: your own dump, git-ignored. Never commit ROM data.

## How the web patcher data is made

The browser can't run trap15's assembler, so `index.html` embeds the *result* of `overpowered.py`. Run:

```
py overpowered.py roms/mmatrix.zip patches/mmxi_v1.0.0_20250412.zip --write-web
```

`write_web()` in `overpowered.py`:
1. writes each output file's CRC32 into the `.mra` `<part name=... crc=...>` entries;
2. diffs every changed file against the original and records runs of changed bytes as `[offset, new-bytes-hex]` (gaps of 1 byte are merged, runs capped near 64 bytes). These become `const PATCHES` in `index.html`;
3. rewrites the `const BUILD`, `const PATCHES`, `const PATCHED_CRC` and `const MRA_TEXT` lines in `index.html` (each must be a single line).

The page applies `PATCHES` to the user's files and refuses to output anything if the CRCs don't match `PATCHED_CRC`.

The page's styling and zip read/write code came from the earlier Feveron patcher page that `index.html` was copied from.

## Builds

### Build 1 (2026-11-26)

- Baseline: trap15 Mars Matrix Improvement v1.0.0 only. No Overpowered gameplay changes yet.
- Patched CRCs: `mmx.01` 45a29ce5 (2 runs, 49 bytes), `mmxj.03` dec3c9da (1 run, 4 bytes), `mmxj.04` unchanged d943a339, `mmxj.05` c1a306fa (23 runs, 590 bytes).
- Web patcher rewritten for Mars Matrix (it had been a Dangun Feveron page). Output is `mmatrixop.zip`.
- `.mra` CRCs updated to the patched values above. Its `<name>` is "Mars Matrix Overpowered (Build 1)".
- (`trap15.py` output was briefly renamed to `mmatrixop.zip`. In Build 2 it went back to its original name, and `overpowered.py` now makes `mmatrixop.zip`.)
- Verified: `trap15.py` builds cleanly. The page's embedded patches reproduce all three patched CRCs (checked in Python). The page loads without errors. Not yet verified: a full drop-and-download in a browser, and a test in MAME or on MiSTer.

### Build 2 (26/11/26)

- Warning screen (the first screen shown at boot) now shows three centred lines: `MARS MATRIX OVERPOWERED`, the date, and `BUILD N`.
- How: `warning_screen()` in `overpowered.py` writes 25-character fields (text centred with spaces; the byte after each field must be `00`) at these 68000 addresses (all in `mmxj.05`). These strings are data, so CPS2 opcode encryption doesn't touch them.
  - `$156BCA`: title, originally `"       MARS MATRIX       "`.
  - `$156B1C`: date. trap15 set it to `"   00/04/12 + 25/04/12   "` (original game: `"       0 0 0 4 1 2       "`). We write the `.mra` date.
  - `$156BE4`: originally `"        J A P A N        "`. We write `BUILD N`.
  - Next to these: `"WARNING"` at ~`$156C00` and `"PUBLICITY VERSION"` at ~`$156B54`.
- Date and build are read from the `.mra` `<name>` by `mra_date_build()`. Change the date or build there, then run `overpowered.py --write-web`.
- Split: the Overpowered tweaks moved from `trap15.py` into the new `overpowered.py`, and `trap15.py` is back to trap15's build only. Output ROMs are byte-identical to the ones before the split.
- Patched CRCs: `mmx.01` 45a29ce5, `mmxj.03` dec3c9da, `mmxj.04` d943a339 (unchanged), `mmxj.05` 51523a32.
- Verified: booted in headless MAME 0.289 (`bin/cps2`, WSL Ubuntu-24.04, set run as `mmatrixj` from a patched `mmatrix.zip` plus `qsound.zip`). Frame ~50 shows the new warning screen correctly. The page's embedded patches reproduce all patched CRCs (checked in Python).

### Build 3 (26/11/26)

Gameplay findings (player 1 object at `$FF4418`, `a6` in the player routines):

| RAM | Player offset | Meaning |
|---|---|---|
| `$FF0067` | (global) | Chain counter shown as "+N" (byte) |
| `$FF449E` | +$86 | Chain value used by the pickup routine (cleared when the timer hits 0) |
| `$FF44A0` | +$88 | Chain timer (frames). Set on pickup, -1 per frame, chain resets at 0 |
| `$FF4496` | +$7E | GHB gauge, `0`..`$4000` (full) |
| `$FF4492` | +$7A | Frames button 1 held while GHB is allowed (GHB starts at `$10`) |
| `$FF4498` | +$80 | GHB active flag (`$FFFF`) |
| `$FF449C` | +$84 | Set while the bomb is out (blocks restarting) |
| `$FF448A` | +$72 | Bomb power: on release `((0x4000-gauge)>>10)+0x20`; `$78` if the gauge runs out |

Code (decrypted addresses, from trap15's `build/code_out.bin`):
- `$11E958`: cube pickup. Looks up the table at `$11E9C4` (5 entries of `[bcd step byte pair, timer word]`: 1→90, 3→120, 5→150, 10→180, 50→250 frames) and stores `max(timer, entry)` to `+$88`.
- `$11EA4E`: `tst.w $88(a6) / beq / subq.w #1,$88(a6)`. Otherwise `clr.w $86(a6)`.
- `$11EB14`–`$11EC02`: GHB. Button 1 held → `cmpi.w #$4000,$7E(a6) / bne` (the only-when-full gate) → `$7A` counts to `$10` → start: `$80=$FFFF`, gauge `-$400`. While active, gauge `-$80`/frame. If it reaches 0 → auto-fire at max power. On release → fire with power from the gauge used. When idle: `$92` delay counts down, then `addi.w #$20,$7E(a6)` and clamp to `$4000` (`$11EBEE`).

Changes:
- **Chain bar drains 2× slower:** the table at `$11E9C4` is doubled (180/240/300/360/500). Plain data, written with `write_bytes()` (`chain_bar_half_drain()`).
- **GHB refills 2× faster:** `$11EBEE` `066e0020007e` → `066e0040007e` (`addi.w #$40`).
- **GHB usable any time:** `$11EB24` `0c6e4000007e 666e` → `0c6e0400007e 656e` (`cmpi.w #$0400` / `bcs`). Requires gauge ≥ `$400` so the start cost can't underflow. Side effect: power is computed as "drained from full", so a bomb started on a part-full gauge counts as stronger, and running a small gauge dry gives a max-power bomb quickly.
- **New `CodePatcher` in `overpowered.py`:** it patches trap15's decrypted image (`build/code_out.bin`, kept by running `trap15.py --work <tmp>`), then runs trap15's tools: `romfuck s` → `encrypt.exe <out> <in> orig/mmxj.key 0x000000` → `romfuck s` back to linear. Only the patched words are copied into the ROMs. Safety: it checks the old code bytes, and checks that the word just before each patch encrypts to what the ROM already has.
- Patched CRCs: `mmx.01` 45a29ce5, `mmxj.03` dec3c9da, `mmxj.04` d943a339 (unchanged), `mmxj.05` b51507c8.
- Verified in MAME (same scripted run before and after, button 1 held 150 / released 150 frames): gauge +3200 per 50 frames (was +1600). GHB fired repeatedly from partial gauges. The chain timer refills to 180 (was 90), the chain reached +10 (was +4), and the bar draws normally. The web data reproduces all CRCs.

How these were found (repeatable):
1. `BT_DUMP=ff0000:10000` records work RAM every frame. Compare it against HUD screenshots (`BT_SNAP=20`, crop the top-left/bottom-left) to find values whose timing matches.
2. Find the writer PC with a Lua write tap (`space:install_write_tap(start, end, name, cb)` logging `cpu.state["PC"].value`). The debugger `wpset`/`logerror` route logged nothing in this headless build.
3. Disassemble `build/code_out.bin` with capstone (M68K). Read data/tables from `build/data_out.bin`, because code_out has the data "decrypted" into garbage.

Input schedule used (frames; K coin, S start, A button 1, L/R): `300 K, 310 -, 400 S, 410 -, 560 A, 570 -, 700 S, 710 -, 760 S, 770 -, 820 S, 830 -`. That starts a game and skips the tutorial, and play begins ~frame 800. Then every 300 frames: `A` for 150, release, and move L/R.

### Build 4 (26/11/26)

**Feature:** when an enemy is killed, every enemy bullet within 24px (distance squared < 24², i.e. a circle) is removed and replaced by a small gold cube. Every bullet within 16px of a cancelled bullet is cancelled as well, breadth-first, until nothing new is in range.

Findings:
- **Object lists** are doubly linked lists with a sentinel node, stored as (head pointer, count word) pairs from `$FF0056`. `$FF0056/$FF005A` is **enemy bullets** (up to ~300). `$FF005C/$FF0060` is **cubes**, and `$FF0062/$FF0066` is a second cube-like list. Then `$68/$6C`, `$6E/$72`, `$74/$78`, `$7C/$80`, `$82/$86`.
- Node layout (bullets and cubes): `+0` next, `+4` prev, `+8` X pixel (word) / `+$A` fraction, `+$C` Y pixel / `+$E` fraction, `+$10`/`+$14` velocity (longs).
- One shared free-node pool: `$31C64` allocates (returns the node in `d0`, negative if none left), `$31C80` frees (node pointer pushed on the stack). Both change only `d0`.
- Bullet spawn `$36822`. Cube spawn core `$39356` (`d0` x, `d1` y, `d2`/`d3` velocity, `d4` type). Wrappers: `$3930E` (falls straight, `vy=+2`) and `$39328` (random drift). Enemies drop cubes with `d4=1` (small cube), and some use 4.
- Cube pickup collision `$39960`: walks the `$FF005C` list, box ±`$1C`, calls the pickup handler (`a0`), unlinks, frees, decrements the count.
- **Enemy killed** `$3222A`, `jsr`'d from 194 places in enemy death code with `a6` = enemy (X `$12(a6)`, Y `$16(a6)`, score `$60(a6)`). It adds score (`$161776`) and EXP (`$161708`). Death code pattern: `btst #1,$C(a6)` → `jsr $3222A` → explosion `$1AA00` → cube drops.
- Found by: tapping writes to the chain timer `$FF44A0` and logging the stack (return address `$399A8` in the cube collision loop, `A1` = cube node). Then searching code for the list-head addresses `$FF0056`–`$FF008A`, and comparing list counts over time in the RAM recordings.
- Free space: ROM `$172F1C`–`$17FDFF` is all zeros (unused, before trap15's code at `$17FE00`; trap15's code ends at `$17FF9A`). RAM `$FFB0B8`–`$FFFEC8` is never touched in stage 1 play (the stack reaches down to `$FFFEC9`).

Implementation (`asm/bullet_cancel.asm`, `bullet_cancel()` in `overpowered.py`):
- Hook: `$3222A` `48e7c000 202e0060` (`movem.l d0-d1,-(a7)` / `move.l $60(a6),d0`) → `jmp $178000.l` / `nop`. The routine replays those two instructions and jumps to `$32232`.
- Routine at `$178000` (198 bytes): save `d0-d7/a0-a5`, then `cancel_around(enemy x, y, r=24)`, then pop queued positions and run `cancel_around(x, y, r=16)` until the queue is empty. The queue is at RAM `$FFE000`, 512 entries × 4 bytes (x, y words); when full it still cancels but stops chaining.
- `cancel_around`: walk the bullet list, quick |dx|,|dy| < r check, then dx²+dy² < r². For each hit: save x/y, unlink, free (`$31C80`), decrement `$FF005A`, push x/y, and spawn a cube with `$3930E` (`d4=1`).
- New `CodePatcher.place()` (checks the ROM is all zero there first) and `CodePatcher.assemble()` (asw + p2bin, symbols parsed from the listing).
- Patched CRCs: `mmx.01` 45a29ce5, `mmxj.03` 7782e303 (hook at `$3222A`), `mmxj.04` d943a339 (unchanged), `mmxj.05` ba185a24.
- (Wrong list, see Build 6.) Verified in MAME (same scripted run as Build 3, 3000 frames, no crash): peak bullets at frame 1100 were 197 (Build 3: 296), the cube count peaked at 70 (was 13), the chain counter reached +68, and the score was 3,557,030 (was 59,880). Screenshots show bullet clusters turning into cube fields around killed enemies. The web data reproduces all CRCs.
- Not yet tested: bosses and later stages, GHB "capture bullets" interaction, and 2-player.

### Build 5 (26/11/26)

**Ship speed:**
- The selected ship is stored at game struct (`$FF009A` → `$FF4978`) `+$3E` (P1) / `+$64` (P2): 0 = Mosquito 01 (red), 1 = Mosquito 02 (blue). `$160C6C` returns it (`d0` bit 0 = P1, bit 1 = P2).
- Player init `$11D44C`: `move.w #$1A,$74(a6)` at `$11D4A2`, then the ship goes into `+$70`, and if it's Mosquito 02, `move.w #$1F,$74(a6)` at `$11D4C4`.
- `+$74` is the speed magnitude. The movement code at `$11ED94` looks up a direction from the stick bits (table `$11EE36`) into `+$1C`, copies `+$74` into `+$1A`, and `$D5786` turns it into X/Y (16.16) added to `+$12`/`+$16`. 26 → 3.25 px/frame, 31 → 3.875 px/frame.
- Patch: `$11D4A2` `3d7c001a0074` → `3d7c001f0074`. Both ships now get `$1F`. Mobility (the turn/bank value `+$76`, ±$70 in steps of $10) is unchanged.

**Select-screen boxes (graphics patch):**
- The stats values column ("Wide", the boxes, "High", the weight) is one sprite, not text. It's drawn by `$16381E` from the per-ship list `$163E5E` (red) / `$16406E` (blue), entry 0: code word `$17BA` / `$180A`, attr `$4413`. On screen (sprite list, mirrored in RAM at `$925E9C`) it's code `$17BA`, attr `$4413`. **CPS2 sprite tile = code + ((attr & $6000) << 3)** → `$217BA`. The size nibbles `$44` mean 5×5 tiles (80×80 px). Tiles go +1 per column and +$10 per row.
- Lessons: the text layer (scroll1) here is ASCII at `$0300 + char` (e.g. "insert coin" at `$909290+`); scroll3 tiles `$5C9…` were background, not stats. To see what's really drawn, dump sprite RAM `$708000` and diff `$900000`–`$92FFFF` between two states.
- Graphics decode (checked byte-for-byte against MAME's `:gfx` region read through Lua): `mmx.13m/15m/17m/19m` (first 16 MB) and `mmx.14m/16m/18m/20m` (second) are loaded 2 bytes each per 8-byte group (ROM_LOAD64_WORD), then every 2 MB bank is "unshuffled" (MAME `cps2_gfx_decode`): `rec(x) = [rec(L)[:q], rec(R)[:q], rec(L)[q:], rec(R)[q:]]` over 8-byte units. 16×16 tile = 128 bytes, each half-row 4 bytes = bitplanes (byte 3 → value bit 3 … byte 0 → bit 0), leftmost pixel in bit 7. `gfx_loc()` maps a decoded byte straight back to (ROM, offset) through the permutation, so only the touched bytes change.
- Mosquito 01's stats sprite: box rows FIRE POWER y 13–17 and MAX SPEED y 25–29. Boxes are 8 px wide plus a 1 px gap (9 px pitch) from x=35, red fill pen `$D` (blue's uses `$E`), transparent `$F`. Blue's 4th/5th boxes are at x 62/71. `red_ship_speed()` checks that x 62–79 on rows 25–29 is transparent, then copies box 3 (x 53–61) to x 62 and x 71. That changes tiles `$217CD`/`$217CE` → `mmx.14m`, `mmx.16m`, `mmx.18m`, `mmx.20m`.
- Patched CRCs: `mmx.01` 45a29ce5, `mmxj.03` 7782e303, `mmxj.05` 45cf59d8, `mmx.14m` 01eb615b, `mmx.16m` d976c4eb, `mmx.18m` f62c1d1e, `mmx.20m` d7dba6c9.
- Verified in MAME: the select screen shows 5 red MAX SPEED boxes on Mosquito 01, lined up with Mosquito 02's, and FIRE POWER still shows 3. In game, Mosquito 01 moves 3.875 px/frame (speed field 31; was 3.25). The web data reproduces all 7 changed files.

### Build 6 (26/11/26)

**Bug in Build 4:** the list at `$FF0056`/`$FF005A` is **not** enemy bullets. It's player shots / effects (it hits ~300 entries along the player's laser and in explosions). Cancelling it made walls of cubes along the laser and left the real enemy bullets untouched (seen in the user's capture video). Build 4's "bullets 296→197" check measured the wrong list.

**Real enemy bullet list:**
- Head pointer `$FF000C` (sentinel node), count `$FF0010` (word), flags `$FF000A`/`$FF000B`. Init `$32C2C`, clear-all `$32C5A`, spawn/append ends at `$32D48` (`addq.w #1,$FF0010`).
- Nodes are `$22` bytes: `+0` next, `+4` prev, `+8` X (16.16), `+$C` Y (16.16), `+$10`/`+$14` velocity, `+$1A` sprite.
- Move/draw `$32D6C` (one of the `$FF0B86` sprite writers). It adds velocity, maps X/Y through tables `$35486`/`$35D26` (negative = off screen) and deletes off-screen bullets. So every node in the list is on screen.
- How it was found: dumped RAM on 3 consecutive frames with blue bullets on screen (frames 1540–1542 of the standard input script), looked for words changing by the same small amount each frame (`$FF6xxx`, `$22` stride), walked the `next` pointers around the ring (18 bullets in triples), and searched low RAM for a pointer to a ring node → `$FF000C`.
- Also learned: the CPS2 sprite RAM at `$700000`/`$708000` read back as zeros during gameplay. The game builds its sprite list through the pointer at `$FF0B86`.

**Fix:** `asm/bullet_cancel.asm` `BUL_HEAD`/`BUL_COUNT` → `$FF000C`/`$FF0010`. Nothing else changed (same radii 24/16, same cube type and hook).

- Patched CRCs: `mmx.01` 45a29ce5, `mmxj.03` 7782e303, `mmxj.05` 36f1ef1c, `mmx.14m` 01eb615b, `mmx.16m` d976c4eb, `mmx.18m` f62c1d1e, `mmx.20m` d7dba6c9.
- Verified in MAME (standard input script, 3000 frames): the cube count peaks at 14 (Build 4: 70). At frames 1532 and 1536 enemy kills turn blue triple shots into 3 cubes each (bullets 26→21→16→11, cubes 0→3→6). Bullets with no kill nearby stay on screen, and screenshots show no cube walls. The web data reproduces all 7 changed files.

### Build 7 (27/11/27)

**Problem:** sound effects sound out of phase (the music is fine). This is in the **original game too**, not caused by trap15 or our patch: L/R correlation over 30 s of play is -0.61 in the original, -0.36 with trap15 and -0.37 in Build 6, dropping to about -0.9 whenever effects play. The title music sits at about +0.9.

**Cause:** the QSound DSP's 3D virtualizer. The Z80 boot code (`mmx.01` `$00AB`) writes 12 DSP registers from the register list at `$00D5` (`DE DF E0 E1 E4 E5 E6 E7 E2 DA DC E3`) and little-endian word values at `$00E1` (`0000 002E 0000 0030 3FFF 3FFF 3FFF 3FFF FFFF 0DB2 0E11 0039`). `$E4`/`$E6` = wet (3D crosstalk-cancelling path) levels and `$E5`/`$E7` = dry levels. The wet path feeds anti-phase into the opposite channel.
- Pan isn't the cause: every pan write (reg `$80+voice` from `$0473`/`$0882`/`$16FF`, value `$0110`+offset) stayed within `$110`–`$12C`, the normal stereo range.

**Fix:** `qsound_plain_stereo()` sets `$E4`/`$E6` to 0 (bytes `mmx.01` `$00E9`/`$00ED`), leaving dry only.
- Experiment: wet=0 → correlation +0.67, out-of-phase quarter-second windows 1/99 (min -0.04), RMS L/R 1507/1214. Dry=0 → also in phase but quiet and lopsided (608/963). Both on: 45/99 windows out of phase (min -0.94), RMS 1194/1048. Build 7 peak 10696/32767, no clipping.

**Tools (repeatable):**
- Audio: `scripts/run.sh <frames> -wavwrite work/out.wav` (works with `-sound none`), then per-window `np.corrcoef(L, R)`.
- QSound register log: Lua write tap on `:audiocpu` program space `$D000`–`$D002` (`$D000` = data hi, `$D001` = data lo, `$D002` = register number, which triggers the write).
- Z80 disassembly: run MAME with `-debug -debugger none` and a Lua harness that calls `manager.machine.debugger:command("dasm work/z80.asm,0,8000,1,:audiocpu")` (`-debugscript` didn't run in this headless build).

- Patched CRCs (Build 7): `mmx.01` 05b770bb, `mmxj.03` 7782e303, `mmxj.05` 748ed38e (date 27/11/27), graphics as Build 5.

### Build 8 (27/11/27)

**Centered sound effects:** with the virtualizer off, sound effects came out of the left speaker only. The voice pan value `(ix+$47)` (0..$20 → QSound pan `$0110`+value) is 0 = hard left for sound effects. The voice structs are at `$F700`, `$50` bytes each, and `(ix+1)` ≠ 0 means a sound effect.
- Pan sites: `$0466` (key-on loop from `$0432`) and `$0871` (logged writer `$089E`), both `ld e,(ix+47h) / ld a,(0F008h) / or a / jr nz,+2 / ld e,10h` (`$F008` = 0 is the game's MONO setting → center). `$16E3` (music pan command, logged `$16FF`) and `$0959` (reset all to `$120`) are untouched.
- `asm/sfx_center.asm`: both sites → `call 7100h` + 8×`nop`. `sfx_pan` at `$7100` (free Z80 ROM after trap15's `$7000` code) returns e = `$10` (center) when MONO is on or `(ix+1)` ≠ 0, otherwise `(ix+$47)`. The Z80 isn't encrypted; `sfx_centered()` assembles it with trap15's AS (`CPU Z80`) and writes `mmx.01` directly, after checking the 11 original bytes at each site and that `$7100` is free.
- Verified (same 30 s run): the effect pan writer now only writes `$120` (was `$110`), and the music pans are unchanged (`$114`–`$12C`). RMS L/R 1508/1558 (was 1507/1214), no quarter-second windows >6 dB to one side (was 9/99), correlation +0.91, 0/99 out of phase.

- Patched CRCs: `mmx.01` a39b5635, `mmxj.03` 7782e303, `mmxj.05` a80db00d (build number), `mmx.14m` 01eb615b, `mmx.16m` d976c4eb, `mmx.18m` f62c1d1e, `mmx.20m` d7dba6c9. The web data reproduces all 7.

### Build 9 (27/11/27)

**Title screen text "OVERPOWERED"** under the logo, in the empty band above the copyright lines.

Findings:
- The title's copyright lines aren't on the 8×8 text layer writes at `$15229C` (that's only "credit"/"press start"). They're printed by `$152446` (print NUL-terminated string, pointer on stack) after `$152232` (set cursor: col.w, row.w on stack; rows/cols in 8 px units). Pattern: `move.w #row,-(a7) / move.w #col,-(a7) / jsr $152232 / pea str(pc) / jsr $152446 / addq.w #8,a7`.
- Japan path `$158060`: rows `$17`/`$18`/`$19`, col 9, strings `$158528`/`$158548`/`$158568` (31 chars incl. padding). USA/Asia path `$157FF4`: rows `$16`–`$19`, strings `$1584A8`… Both continue at `$1580AE` (`move.w #$1F,-(a7) / jsr $152228`).
- Found by: a read tap on the string bytes (`$1584A0`–`$15858F`) logging PC + stack → reader `$15245E`, caller return `$158078`.

Implementation (`asm/title_text.asm`, `title_overpowered()`):
- Hook `$1580AE` `3f3c001f 4eb900152228` → `jmp $178100.l` + 2×`nop`.
- `$178100`: set cursor row `$13`, col `$13` (9 + (31-11)/2, centered on the copyright lines), print the string at `$178180`, replay the two replaced instructions, `jmp $1580B8`.
- The string `"OVERPOWERED",0` at `$178180` is **data** (read by the print routine), so it's written unencrypted with `write_bytes()`; the code goes through `CodePatcher.place()` (encrypted). Lesson: never put data in a `place()` block, because it would be encrypted.
- Patched CRCs: `mmx.01` a39b5635, `mmxj.03` 7782e303, `mmxj.05` 4a11bb64, `mmx.14m` 01eb615b, `mmx.16m` d976c4eb, `mmx.18m` f62c1d1e, `mmx.20m` d7dba6c9.
- Verified in MAME: the title shows OVERPOWERED centered under the logo (screen x ≈ 152–238 of 384, rows ≈ 152–159), and the game still goes title → ship select → tutorial → stage 1 normally. The web data reproduces all 7 files.

### Build 10 (27/11/27)

**Feature:** all 6 stages use the Dreamcast Arrange mode enemy layouts (the backgrounds stay arcade). Source: the user's own Dreamcast disc. Neither the repo nor the web page contains Dreamcast data.

**Dreamcast disc:**
- `.gdi` with track03.bin starting at LBA 45000. Raw sectors are 2352 bytes with user data at +16. ISO-9660 PVD at LBA 45016 (root dir extent LE @158, size @166).
- The boot file `00MMXDC.BIN` (named in IP.BIN) is the whole game program: an SH-4 rewrite of the arcade game (not the 68000 code), loaded at `$8C010000` and unscrambled.
- Mode names: ARCADE, ARRANGE MODE (A)/(B), SCORE ATTACK, GALLERY.
- Other notable files: `MAP.MMX` (6 compressed maps, probably backgrounds), `ST0x.ADX`/`RIMIX.ADX` music, `*.SFD` videos, `G_00`–`G_63.PVR` gallery.

**Arcade stage format (68000):**
- Stage table `$14CEEC`, 6 x `$40`:
  - name "STAGE n" (8 bytes), then 4 map/background pointers;
  - `+$18` event list (→ `$FF0BE4`);
  - `+$1C` **spawn list A** (→ `$FF0BF8`);
  - `+$20` **spawn list B** (→ `$FF0BF4`).
  - Setup routine `$14C742`. The stage number is passed in `D0` to `$14C464`, stored at `$FF0BA2`, and the stage is set up immediately from `D0`.
- Spawn record, 14 bytes, big-endian:
  - `time.w`: the stage clock `$FF0BE8` >> 3, i.e. frames / 8;
  - `x.w`, `y.w`;
  - `flags.b`: low 2 bits → object `+9`, the rest >> 2 → a parameter;
  - `class.b`, `script.l` (behaviour bytecode), `c.b`, `d.b`.
  - The reader (`$14C8EA` / `$14C94E`) spawns while `record.time == clock`. There's no end marker: the lists just run past the end of the stage.
- `class` indexes the **enemy descriptor table `$32676`**. Each descriptor starts with an ASCII name ("Sadako", "KAITEN2", "GIGA", ...) and has code pointers from `+$14`. Spawning goes through `$36356`.
- Clock: the main loop calls `$14C7E8` (clock++ unless `$FF0C00` != 0), but only while `$119C42` (the word at `$FF00DE`) returns 0.

**Dreamcast stage format (SH-4 program):**
- Arcade stage table `$8C033604`: per stage (name, event?, list). The arcade's lists A+B are **merged** into one list: `$8C13D97C`, `$8C13F5AC`, `$8C141290`, `$8C1427B0`, `$8C144890`, `$8C145E58`. They match the arcade ROM record for record (296/296, 349/350, 212/212, 315/315, 236/236, 525/525).
- **Arrange lists** (Arrange A and B share one set), table at `$8C033650`: `$8C148B40`, `$8C14B01C`, `$8C14DD28`, `$8C14FA7C`, `$8C15104C`, `$8C153504`.
- Record, 20 bytes, little-endian: `time, x, y, flags, class, pad` (words), `script.l` (DC address), `c, d` (words). Each list ends at time `$7FFF`, and each starts with an extra time-0 class-`$11` record.
- **Behaviour scripts are the arcade bytecode, stored verbatim** (arcade byte order) and contain no absolute addresses. Each stage's script blob sits right before its list, from the lowest script pointer up to the list head.
- **Class table `$8C15D3B0`** uses the same numbering as the arcade (descriptors are quoted, e.g. `'KAITEN2'`). 151 names match. Dreamcast-only classes (no arcade descriptor): `$74` Hanabi, `$75` TELPO, `$76` Zan.

**Comparison (spawns, arcade → Arrange):**
- Stage 1 296 → 388, stage 2 350 → 480, stage 3 212 → 306, stage 4 315 → 173, stage 5 236 → 386, stage 6 525 → 329.
- The only shared records are each stage's arcade list-A entries (bosses/set pieces).
- Arrange uses 49 classes that no arcade stage uses; 46 of them exist in the arcade descriptor table.

**Import (`arrange_layouts()`; the browser does the same in `arrangeImport()` in index.html):**
- `read_dc_program()` streams track03.bin out of the zip (or reads a track03.bin or 00MMXDC.BIN directly) and parses the ISO.
- Per stage:
  - copy the script blob verbatim;
  - convert the records to 14-byte BE with `script = new_blob + (dc_script - blob_start)`;
  - drop classes `$74`–`$76` (24, 45, 0, 65, 6, 0 records for stages 1–6);
  - append a time-`$7FFF` end record.
- Allocation: first fit in free ROM `$172F20`–`$177FFF`, then `$178200`–`$17FDFF`, rounding sizes up to even.
- The first allocation is a 14-byte list holding only an end record. It's used as **list A** for every stage, because the reader reads list A without a null check. The stage table `+$1C`/`+$20` become (empty list, Arrange list).
- Placement (scripts / list):
  - stage 1 `$172F2E` / `$1732FE`
  - stage 2 `$1746F4` / `$174D6C`
  - stage 3 `$176544` / `$176CBC`
  - stage 4 `$178200` / `$178758`
  - stage 5 `$178D4E` / `$179586`
  - stage 6 `$17AA5C` / `$17B0D8`

**Stage 4 hang and fix:**
- Arrange stage 4 starts with class `$73` KAITEN2, which no arcade stage uses.
- Its sprite routine `$13D21C`–`$13D29D` (descriptor `$13C6F8`, 4th pointer) was **left unencrypted in the arcade ROM**. The CPU decrypts it to garbage, raises an exception, and parks in the `bra *` trap stubs from `$14FA4A`. Symptoms: PC stuck at `$14FA66`, stage clock stopped at `$A`.
- Fix: `fix_unencrypted_kaiten2()` calls `CodePatcher.encrypt_plain()`, which puts the plain bytes into the decrypted image so they get encrypted.
- All other routines of the classes Arrange uses were checked (comparing how well the plain and decrypted bytes disassemble) and are encrypted normally.
- Finding it: `$FF0BEE` (scroll delta) and `$FF0C00`/`$FF00DE` (clock gates) were red herrings. The decisive step was logging the CPU PC every frame after the stall.

**Web patcher:**
- New step 2 drop box for the Dreamcast `.zip` with the `.gdi`. A `.7z` shows a "not supported yet" message.
- `readDcProgram()`:
  - reads the zip's central directory with `File.slice`;
  - streams track03.bin through `DecompressionStream('deflate-raw')`;
  - reads only the sectors it needs, in order (PVD, root dir, 00MMXDC.BIN), with a progress bar.
- `write_web()` now exports the patches as they were **before** the Arrange import, plus `const ARRANGE` (list heads, regions, stage table, dropped classes). The page redoes the import and checks the final CRCs.
- Verified in the browser pane, using the page's own functions extracted from its script:
  - the disc reader on a synthetic `.gdi` zip returns the program byte-for-byte;
  - `arrangeImport()` on the real program slice gives the same bytes as Python (CRC `c3b24fb0`).
  - Not done: the full 395 MB disc in a browser.

**Testing:**
- Stage select in MAME (`stagesel.lua`): a Lua write tap on `$FF0BA2` that, on the first write after frame 450, sets `cpu.state["D0"]` to the wanted stage.
- Results:
  - Stages 1–6 all walk their Arrange lists and show Arrange enemy waves.
  - Stage 4 runs through to its boss.
  - In a dense wave (stage 1, around frame 2200), the shared bullet/cube node pool (`$FF0000` free list) briefly hit 0, then recovered. The game skips bullet/cube allocations that fail.
- Patched CRCs: `mmx.01` a39b5635, `mmxj.03` 7782e303, `mmxj.05` c6003de4, `mmx.14m` 01eb615b, `mmx.16m` d976c4eb, `mmx.18m` f62c1d1e, `mmx.20m` d7dba6c9.
- Not done:
  - the Arrange backgrounds;
  - the three Dreamcast-only enemy types;
  - Arrange A vs B differences other than the layout;
  - 7z input;
  - the full real-disc run in a browser.

### Build 11 (26/11/27)

**Feature 1: ORIGINAL / ARRANGE mode menu** (`asm/mode_menu.asm`, `mode_menu()`).
- After a coin, the credited title state calls `$161952` every frame (prints PRESS START / CREDIT). The 16 bytes at `$157F64` (`moveq #1,d0 / pea (a6) / movea.l $10(a6),a6 / jsr $161952 / movea.l (a7)+,a6`, old `700148562c6e00104eb9001619522c5f`) become `jsr mm_frame` + 5 nops. `mm_frame` ($178200) replays the original call at its end.
- `mm_frame`:
  - sets `MENU_ON` (`$FFE902`) = 1;
  - reads the trap15 edge words `$FFB080` (P1) | `$FFB084` (P2): bit 3 Up → `MODE` (`$FFE900`) = 0, bit 2 Down → `MODE` = 1. RAM is cleared at boot, so the default is ORIGINAL;
  - draws two 12-character lines at column `$12`, rows `$13` (ORIGINAL) and `$15` (ARRANGE), straight into the 8x8 text layer: `$908000 + col*$80 + row*4` = tile.w, attr.w.
- Colours: CREDIT is drawn with attr `$0C` **and a separate gold font** (tile = `$320` + ASCII; found by dumping the text layer in MAME). The text routine `$152446` only has the white font (tile = ASCII), which is why setting the palette alone looked wrong. Selected line: gold font + attr `$0C`, with `>` in front; other line: white font, attr `$1F`. Strings (13 bytes each: unselected, selected) are data at `$1783A0`.
- `title_text.asm` (Build 9's OVERPOWERED) now skips its print while `MENU_ON` ≠ 0, otherwise the two texts flicker over each other. `mm_stage_table` clears `MENU_ON` when a game starts, so OVERPOWERED is back on the title after the game.
- Stage table choice: the stage setup took the table with `lea $14CEEC(pc),a0 / adda.w $FF0BA0,a0` (10 bytes at `$14C6A6`, old `41fa0844d0f900ff0ba0`), now `jsr mm_stage_table` + 2 nops. `mm_stage_table` returns the arcade table for ORIGINAL or `ARR_TABLE` for ARRANGE.
- `arrange_layouts()` no longer overwrites the arcade table: it copies it (6 x `$40`) to `ARR_TABLE` = `$172F20` and writes the Arrange list pointers there. The free regions for scripts/lists became `$1730A0`–`$177FFF` and `$178400`–`$17CFFF`.

**Feature 2: Hanabi, Chubi, Shobi** (`asm/hanabi.asm`, `hanabi_port()`, `hanabi_art()`).
- Class `$74` "Hanabi" (DC descriptor `$8C1EE044`) had no arcade code. Hanabi spawns "Chubi" (`$8C1EE084`), and shooting a Chubi spawns "Shobi" (`$8C1EE0C4`). All three were translated by hand from the DC program (SH-4, a mechanical translation of 68000 code, 68000 registers in RAM at `$8C27E6D0`.., flags N/Z/C at `$8C27E70C/710/714`).
- Arcade object layout (from the spawner `$36356`): the 0x3E-byte descriptor is copied to object `+$2A`. So routines land at `+$3E` init, `+$42` kill, `+$46` update, `+$4A` draw, `+$4E` hit; hp (desc `+$28`) at `$52`; score long (desc `+$36`) at `$60`. Spawn args: d0 x, d1 y, d2 → `$1C` (angle), d3 → `$1A` (speed), a1 → `$20` (script). Private fields start at `$68`. Arcade descriptor: name[16], list.w (3), size.w, 5 routine pointers, hp.w at `+$28`, score.l at `+$36`.
- DC → arcade field mapping: DC words `$1C`/`$1E` = arcade `$1A`/`$1C`; DC `$3C` hp = `$52`; DC `$4C` score = `$60`; DC private `$54+n` = arcade `$68+n`; a DC byte at n = arcade byte n^1 (DC words are little-endian).
- DC → arcade calls (found by aligning the call sequences of enemies that exist in both versions, `callmap.py`, plus a co-occurrence count where that was ambiguous):
  - `$8C03493C` script step = `$40B48`;
  - `$8C034890` angle/speed → velocity = `$D5786`;
  - `$8C0345CE` hitbox = `$119898` (d0..d3 = x, y, w, h; a1 = object; GOTSU follows it with `jsr $3C43C`, which is a bare rts);
  - `$8C0358A4` sprite, list 5 = `$145A44` with the list pointer `$FF0B72`;
  - `$8C010262` bullet = `$32276`; `$8C0344C6` sound = `$151E5E`; `$8C035370` random = `$1197F6`;
  - `$8C0136B8` spawn = `$36456`; `$8C011208` explosion = `$3930E` (d0 x, d1 y, d4 size);
  - `$8C031E5C` + `$8C031FBE` score = `$3222A` (reads `$60`; d1 = player);
  - `$8C03312E` player = `$321E2` (returns a0); `$8C0367D2` angle to = `$C4F56`; `$8C0348B2` turn toward = `$11981E`.
- Behaviour:
  - **Hanabi** (hp 50, score `$30`): init sets speed `$18` and timer 10. Update: script step; on-screen flag bit 4 of `$9` (delete outside -32..416 / -24..248); hitbox 64x48; anim += 8. Then `bset #4,$9; beq end` and the timer counts down each frame (flashing on odd frames). When it goes negative: bullet `$4008`, sound `$16`, 4 Chubi (speed 48) at 90° steps from a random angle, then delete. Shot: score, explosion size 3, the same burst, delete. Arcade object y counts up from the bottom, and the stage spawns Hanabi at y 248 (just above the screen), so it bursts just as it drops into view.
  - **Chubi** (hp 50, score `$10`): moves by angle/speed. State 0 slows by 2 per frame to a stop; state 2 turns its facing (`$70`) toward the player at rate 2 for 64 frames; state 4 keeps turning at rate 1 and speeds up by 1 per frame. Hitbox 32x32. Shot: score, bullet `$8003`/`$4003` (by frame parity), sound, explosion size 1, delete, and 8 Shobi (speed 0) at 45° steps. The DC glow effect (sprite-effect slots `$8C036296`/`$8C036352`) is not ported.
  - **Shobi** (hp 10, score `$10`): init adds `random & 15` to its speed; it spirals (angle +3 per frame, speed +1 on odd frames); hitbox 16x16. Shot: score, hp = -8 and `bclr #6,$8`; it then flashes, counts hp back up to 0 and pops (bullet `$4001`/`$8001`, sound, explosion size 0, delete).
- Placement: code `$17D000`–; descriptors (data) `$17EE00` (Hanabi), `$17EE40` (Chubi, size `$76`), `$17EE80` (Shobi, size `$6E`); Hanabi size `$70`. Spawn class table `$32676` entry `$74` → Hanabi descriptor. `ARC_MISSING_CLASSES` is now just `$75` TELPO and `$76` Zan.

**Hanabi/Chubi/Shobi graphics** (imported from the disc by `hanabi_art()`; the browser does the same in `hanabiArt()`).
- The disc's 692 MB `MAIN.MMX` is filler (the same block repeated; the program only checks its size `$29400000` and a magic word near the end).
- `CG.MMX` (11 MB, read whole into RAM, pointer at `$8C1F551C`) holds every sprite tile:
  - a table of u32 per DC tile number (bit 31 = flag), data from `+$C828C`;
  - each tile is LZ-compressed (decompressor `$8C110474`): MSB-first bit stream; bit 0 = literal byte; bit 1 = match, with the length as interleaved (data bit, stop bit) pairs + 1, and the offset `width` bits + 1. `width` grows to keep 2^width ≥ the output position, max 12; length-1 matches use at most 5 bits;
  - a tile unpacks to 128 bytes = 16x16 at 4bpp in twiddled (Morton) order, y bit lowest; colour 0 is transparent.
- `PAL.MMX`: 16-colour palettes of ARGB1555 LE.
- DC sprite table `$8C1ED9EC`: 3 x 32 entries of 16 bytes (x, y, `$8000`, tile-high, tile, palette, size, 0). The DC tile number is `tile-high << 16 | tile`: Hanabi `$1C10`.., Chubi `$2394E`.., Shobi `$23D4E`... The DC numbers are not the arcade's: arcade `$1C10` is an unrelated sparkle.
- Arcade side:
  - Frames are repacked into empty arcade tile rows, found by scanning the decoded gfx for runs of all-transparent 16-tile rows (isolated blank tiles may belong to other sprites). Hanabi 4x3 frames → `$2D3E0` (24 rows), Chubi 2x2 → `$37230` (8 rows), Shobi 1x1 → `$3D4A0` (2 rows).
  - Arcade sprite tile bank = bits 13–14 of the Y word (`$4000` = bank 2, as the ship-select entry for `$217BA` shows). The second long of a `$145A44` entry is ORed into (x, y), so the converted entry has `bank << 13` there.
  - Pixels: DC colour c → arcade c-1 (0 → 15, the arcade's transparent colour).
  - Palettes go to the arcade palette table `$70996` slots `$3F0`/`$3F1`/`$3F2`. Slots `$2C0`–`$3FF` are identical filler copies; the build checks the slot still holds the filler. Conversion: brightness F, then the top 4 bits of each 5-bit channel, colours shifted down by one.
  - Origin: arcade x = 64 − w/2 where the DC uses −w/2, and arcade y = −(240 − h/2) where the DC uses −(224 − h/2). So the converted x += 64 and y −= 16.
- The converted table goes to `HANABI_SPRITES` = `$17F000` (96 x 16 bytes). Draw offsets: Hanabi `+$000 + (anim & $1F0)`, Chubi `+$200 + (((face + 4) * 2) & $1F0)`, Shobi `+$400 + (anim & $1F0)`.
- `read_dc_files()` replaces `read_dc_program()`: it reads `00MMXDC.BIN`, `CG.MMX` and `PAL.MMX` from the GDI zip / track03.bin in one pass in LBA order (a folder of extracted files also works). The web page's `readDcProgram()` does the same and returns {prog, cg, pal}. `build()` passes every program and gfx ROM to `arrangeImport()`. `write_web()` exports the art settings in `const ARRANGE`.

**Testing:**
- Menu: MAME screenshots after coin + Down: the arrow follows, the selected line is in the gold font, and OVERPOWERED no longer shows through. List B pointer at stage 1: ORIGINAL `$16AB48` (arcade), ARRANGE `$1734B6`.
- Hanabi: a Lua harness (`hanatest.lua`) jumps Arrange stage 1 to clock 486 (it sets `$FF0BF4` to the first record ≥ 486 and the long `$FF0BE8` to 486*8) and logs objects whose `+$2A` name is Hanabi/Chubi/Shobi.
  - Hanabi spawns at y 246, bursts after 11 frames, and 4 Chubi fan out, slow, stop, turn and speed off. Off-screen ones are deleted.
  - The Chubi pods show in MAME with the DC art (silver pod, blue rim) where the logic says they are.
- Debug notes: Chubi was first invisible for three separate reasons, in this order: DC tile numbers ≠ arcade, the missing tile-high word, then the screen origin. Dumping sprite RAM (`$923600` list, `$708000` object RAM) and MAME's `:gfx` region and palette RAM (`$914000`) separated them.
- Web: the page's art functions (copied verbatim from `index.html`), run in the browser pane on a reduced input (blank ROMs plus only the DC bytes they read), give the same CRCs as Python for all 11 touched files. Not done: the full disc in a browser.
- Patched CRCs: `mmxj.03` 803849c0, `mmxj.05` 5e275849, `mmx.01` a39b5635, `mmx.14m` 5cf75f1f, `mmx.16m` 6eccb74b, `mmx.18m` 85fe48df, `mmx.20m` 266fee2d.
- Not done: shooting Chubi/Shobi in play (the kill paths are untested in MAME), Chubi's glow effect, TELPO and Zan.

### Build 12 (26/11/28)

Dates from Build 12 on are written year/month/day (`26/11/28` = 2026-11-28); the `.mra` `<name>` is the source.

**Feature: TELPO** (class `$75`, DC descriptor `$8C1F0B90`, hp 100, score `$30`): 45 spawns in Arrange stage 2 (from stage time 10), 6 in stage 5. Code in `asm/hanabi.asm` (`tp_*`); descriptor at `$17EEC0`, attack-slot data `tp_eff` at `$17EF00`; spawn class table `$32676` entry `$75`. `ARC_MISSING_CLASSES` is now just `$76` (Zan).
- DC routines: init `$8C0F8FC2`, kill `$8C0F908C`, update `$8C0F90AC`, draw `$8C0F9526`, hit `$8C0F9700`, attack callback `$8C0F8DEC`.
- Arcade private fields: `$68` attack-slot block (DC `$54`), `$70` warp counter (DC `$5C`), `$72` state (DC `$5E`), size `$74`.
- Object bytes (DC byte n = arcade n^1): `$A` bit 0 = show warp frames, `$A` bit 1 = stopped (set when shot), `$B` bit 7 = attack slot running, `$B` bit 0 = leave (set by the spawn script, which runs on the arcade's own interpreter `$40B48`).
- Update:
  - if hp < 0 (shot): flash, hp++, and at 0 call `$32362` (d4 = 8), sound `$16`, explosion size 2, delete;
  - else tick the attack slot while `$B` bit 7 is set;
  - hitbox 64x32; stop here if `$A` bit 1;
  - state 0: warp counter 0 → 16, then set `$A` bit 0 and `$B` bit 7, state 2;
  - state 2: script step, on-screen/delete bounds (240/-16/416/-32), and when `$B` bit 0 is set: clear `$B` bit 7, state 4;
  - state 4: clear `$A` bit 0, warp counter 16 → 0, then delete.
- Draw: the body (table entry 16, `$145A44`) once the warp counter is ≥ 7; while `$A` bit 0 is set, also warp frame `counter` (entries 0–16) via `$145A22` (no hit flash, DC `$8C035408`). The marker (entry 17, list 4 = `$FF0B6E` at x+32, y-32, every other frame when DC player struct `+$D4` is set) is **not ported**.
- Hit: standard (score `$3222A`, hp = -8, `bclr #6,$8`), plus set `$A` bit 1, angle `$80`, speed 8.
- Sprite lists: the 4-byte list pointers start at `$FF0B5E`; DC list n = `$FF0B5E + 4n` (list 5 = `$FF0B72`).

**Attack slots** (the arcade's "attack timer" engine, used through DC `$8C1106D8`/`$8C036274`/`$8C036296`/`$8C036352`/`$8C110796`):
- Arcade calls: `$3159E` (d0 = slot count → a0 block, `$2E` bytes per slot after a count word), `$315EE` (a0 block, d0 slot offset, a1 = 0x2A-byte data), `$31648` (tick all slots; a6 = owner), `$315E0` (free).
- On each fire it computes d0 = x + `$8`, d1 = y + `$A`, d2 = angle (`$E` + `$10` + random up to `$F`; aimed at the player when data byte 0 bit 7 is set), d3 = speed (`$11` + `$13` + random up to `$12`), d4 = word `$2`, then `jsr` the routine at `$4`. `$20`/`$24` are per-fire / per-tick callbacks; `$28` = repeat count (-1 = forever).
- DC data (0x28 bytes, LE) → arcade (0x2A, BE), field by field: b0, b1, w2, l4 (routine), w8, w10, b12–b19, w20, **w20 again** (the counter starts at the period), w22, 0, w24, w26, l28, l32, w36. Found by matching NTANK/HOHDAI/GOTSU/UFO blocks in both versions (`effmap.py`).
- DC → arcade fire routines: `$8C012648` = `$32CB8` (on-screen-only bullet, d0..d4; same -8..392 / -8..232 bounds); `$8C013C00` = `$31832` (that plus a `$80000020` muzzle effect; `$8C013C68` is a stack-arg wrapper of it).
- TELPO's slot (DC `$8C1F0B64`): flags `$86`/`$80`, type `$340`, offset (0, -16), angle jitter 7, speed `$10`, timers 1/1/0/0/`$3C`/`$14`. Its fire routine `tp_fire` (DC `$8C0F8DEC`) shoots `$32CB8` with the given type, then 3 x type `$2C0` at speed -1, -2, -3, then `$31832` type `$340` at speed -4. The DC aim/tick callbacks are bare rts.

**Graphics import generalized** (`dc_sprites()` replaces `hanabi_art()`; browser `hanabiArt()` mirrors it):
- `DC_SPRITE_GROUPS` = (DC table, entries, arcade tile base, arcade table): Hanabi `$8C1ED9EC` x32 → tiles `$2D3E0`, table `$17F000`; Chubi `$8C1EDBEC` x32 → `$37230`, `$17F200`; Shobi `$8C1EDDEC` x32 → `$3D4A0`, `$17F400`; TELPO `$8C1F0A44` x18 → `$372B0` (right after Chubi's 8 rows), `$17F600`.
- Each entry's frame size comes from its own size word. Frames are packed left to right in 16-tile rows; a frame that doesn't fit, or has a different height, starts a new band. Hanabi/Chubi/Shobi land exactly where Build 11 put them.
- The DC prio word (`$8000`, or `$6000` for TELPO's marker) is kept.
- Palette slots are handed out from `$3F0` in order of first use: Hanabi `$270`→`$3F0`, Chubi `$271`→`$3F1`, Shobi `$272`→`$3F2`, TELPO warp `$164`→`$3F3`, body `$162`→`$3F4`, marker `$8D`→`$3F5`.
- `write_web()` exports `groups` and `slots` in `const ARRANGE`.

**Testing:**
- MAME Arrange stage 2 (`tptest.lua`: stage-select tap with D0 = 1 plus the ARRANGE menu input, logging objects named TELPO):
  - TELPOs spawn in their formations from stage time 10;
  - the warp counter runs 0 → 16 and the state goes to 2 with the attack slot on;
  - screenshots show the green fighters (matching the DC) firing pink bursts, and later moving off on their scripts.
- Web: the page's generic `hanabiArt()` on a reduced input (Hanabi groups regularized; TELPO warp frames pointed at frame 0, body and marker kept so the band packing is exercised) gives the same CRCs as Python for all 11 files.
- Patched CRCs: `mmxj.03` 1b33ca51, `mmxj.05` bed8848a, `mmx.01` a39b5635, `mmx.14m` fcea1251, `mmx.16m` 784df66f, `mmx.18m` 5a6e0b77, `mmx.20m` 973c81bf.
- Not done: shooting a TELPO in MAME, watching one warp out (needs the script's leave bit), the marker sprite, Zan.

### Build 13 (26/11/28)

**Feature: Zan** (class `$76`, DC descriptor `$8C1F1868`, hp 100, score `$10`): 65 spawns in Arrange stage 4. `ARC_MISSING_CLASSES` is now empty: every class in the Arrange layouts has code. Zan brings two children: **Zz** (`$8C1F18A8`) and **Zc** (`$8C1F18E8`).
- DC routines:
  - Zan: init `$8C0FD088`, kill `$8C0FD1C8`, update `$8C0FD1F8`, draw `$8C0FD618`, hit `$8C0FD6E4`, attack `$8C0FCED8`;
  - Zz: init `$8C0FD7C0`, update `$8C0FD8D0`, draw `$8C0FDB70`, kill/hit `$8C0FD89C` (no-op: it can't be hit);
  - Zc: init `$8C0FDCE0`, update `$8C0FDDA4`; it shares Zan's kill/draw/hit.
- Arcade fields:
  - Zan/Zc: `$68` attack slots (DC `$54`), `$70` spin counter (DC `$5C`), `$72` killer (new: the hit's d1, kept for `$3222A` because the score is awarded later, in update), size `$74`;
  - Zz: `$6C` blink mask (DC `$58`), `$6E` speed step (DC `$5A`), size `$70`.
- **Zan:**
  - init: speed 32 + random 0–15, one attack slot from `zn_eff` (DC `$8C1F1810`: type `$E0`, aimed, speed `$18`, timers 1/1/0/0/`$3C`/`$0A`).
  - update: normally tick the slot, script step, bounds (-16..400 / -16..240), hitbox 32x32, spin += 4 & `$7F`. Then, if moving and `($E & 15) == 0`, spawn a Zz at its position with d2 = its angle and d3 = spin & `$70`.
  - shot (`$A` bit 0): hp counts -8 → 0 while it keeps flying, then spin += 4 per frame up to `$C0` (frames 8–11), then score, sound `$16`, explosion size 1, delete.
  - attack `zn_fire`: `$32CB8` at speed d3, d3+1, d3+2, then `$31832` at d3+3.
  - hit: hp = -8, `$A` bit 0, remember d1.
- **Zz** (flags `$1800`; hp 0 and no hit routine, so it can't be shot): init aims at the player (`$C4F56`) into the angle, mask 1, step 0.
  - update: speed += step; at frame (`$E`) 32 → mask 3 / step 4; at 64 → mask 7 / step 8; at 128 → spawn a Zc (angle = Zz's angle, speed 0) and delete.
  - draw: when `($E & mask) == 0`, Zan's frame `speed & $70` via `$145A22` on sprite list 4 (`$FF0B6E`), so a blinking, spinning-up after-image.
- **Zc** (hp 0, so one hit): init uses slot `zc_eff` (DC `$8C1F183C`: type `$320` through `$31832`, i.e. a flash shot, aimed, angle jitter 15, speed `$18` + random 7, timers 1/1/`$14`/0/0/0) and sets the on-screen flag.
  - update: tick, spin += 16 & `$7F`, move by angle/speed, bounds, hitbox 32x32 (skipped once dying), and on odd frames speed + 1 up to 48.
  - shot: hp -8 → 0 while moving, then `bset #5,$B` (no hitbox), spin up to `$C0`, explode like Zan.
- Graphics: DC table `$8C1F1750`, 12 entries of 2x2 tiles (DC tiles `$15ACE`.., palette `$156` → slot `$3F6`), repacked at tile `$3D4C0` (after Shobi's 2 rows), arcade table `$17F720`. Zz shares it.
- Descriptors and attack-slot data moved from `$17EE00` to **`$17F800`**: with Zan's they no longer fit below the sprite tables at `$17F000`; the build stopped with "ROM space at 0x17f000 is not free".

**Gating note:** stage 4's Zan records (from stage time 471) are in group 1, which the stage 4 mid-boss (St4_MBos) holds. So the Zans only come in once the mid-boss is destroyed. More generally, a formation waits until the previous one in its group is gone, so faster kills mean more spawns. The Dreamcast spawner `$8C013472` and reader `$8C033740` use the same group table and rule as the arcade's `$36356` / `$14C8EA`.

**Testing:**
- Spawn audit of Arrange stages 3–6 in MAME (`spawnlog2.lua`: a read tap on the class table `$32676` logs every spawn attempt and the group table; success is detected by the spawn serial `$FF0054` advancing):
  - every refusal is a group refusal;
  - the original arcade stage 3 run the same way is also refused (10/160);
  - stage 4 (before Zan) spawned 102/102.
- Zan (`zntest.lua`, stage 4, with the mid-boss's hp forced to 1 so the bot can kill it): Zans spawn, move and fire; Zz after-images appear and become Zc at frame 129; screenshots show the green spiked mines with the DC art.
- Web: the generic import code is unchanged (Zan is one more `groups` entry; its tile bank was already exercised by Chubi), so it was not re-run in the browser.
- Patched CRCs: `mmxj.03` 89ea923f, `mmxj.05` 048365d1, `mmx.01` a39b5635, `mmx.14m` 57edf597, `mmx.16m` 6c5b4e10, `mmx.18m` b82b2e3c, `mmx.20m` faefe1f8.
- Not done: shooting Zan/Zc in MAME (the death paths are untested).

### Build 14 (26/11/28)

**Class-number check:** the import assumes a spawn class means the same enemy in both versions. Comparing the descriptor names across every class the Arrange lists use:
- most mismatches are abbreviations of the same enemy (THE TOWER/THE, ST6BUILDING_0x/BUILDING_0x, CFT/CREATE_FT, ...);
- $61 (ATCPRG01 / ATCPRG00), $8C (DAI / HOHDAIY) and $A9 (Kame_Musi / Kame) differ;
- `$A9` is the one reported, fixed below.

**Fix 1: Kame drops gold cubes** (`kame_cubes()`). Class `$A9` = arcade "Kame_Musi" (descriptor `$13D440`, hp 0) = DC "Kame" (`$8C1EEBB4`, hp 150, a rewritten enemy with an attack slot). It's the blue beetle, 74 in Arrange stage 3. Its death code (`$13D494`) spawns the cube with `$3B716(d0 x, d1 y, d4 type)`.
- Cube types (arcade): high word = `$8(a6) >> 3` (picks list `$FF0082`/`$FF0086`); low word = a base `$000/$100/$200/$300/$400` (bigger cubes for higher bases) + `random & $40`. There is a 32-cube cap at `$FF008A`.
- DC cube spawn `$8C011E00` takes a type `4 + random(0–1)`. Pairing enemies that exist in both versions gives DC 4/8/12/16 = arcade `$100/$200/$300/$400`. Kame passes 4; arcade Kame_Musi passes `$000`.
- Patch: `$13D4CA` `move.w #$0,d4` → `move.w #$100,d4`. Only the class table (`$3291A`) points to the descriptor, and no arcade stage uses class `$A9`, so ORIGINAL mode is unaffected.
- Verified in MAME (stage 3, `cubetest.lua`: a write tap on `$FF008A` attributes each new cube to the running object's name): Kame_Musi deaths now add cubes (6 in the test run; 0 before).

**Fix 2: stray shapes under the stage 3 fighters** (`funsha_no_ghost()`). The white fighters before the stage 3 boss are Funsha (`$9C`, 12 spawns) and Funsha2 (`$AC`, 36); neither appears in the arcade stages.
- Their draw routines (`$139CFA`, `$13AEB6`) add a second sprite from a 64-frame table (`$13A9DA` / `$13BB96`, index `$6E`, palette `$8D`) on list 4 at (+32, −16), on odd frames, when the arcade stage flag `$FF0BFC` is clear (`$14C620`).
- The DC draws it under its own condition (player struct `+$D4`, like TELPO's marker), which the arcade backgrounds/events never reproduce. So over the arcade stage 3 it appears where the DC shows nothing: stray shapes under the fighters, varying with their facing.
- Patch at both draws: `btst #5,$D(a6)` / `beq skip` (8 bytes) → `bra.s skip` + 3 nops.
- Ruled out along the way:
  - the imported-art tile rows (no arcade sprite table entry reaches them);
  - the body and shadow frames themselves (identical to the DC's);
  - the shadow palette (all dark);
  - the frame-index tables `$139C62`/`$139C6C`.
- **Lesson:** those two index tables look encrypted in the ROM file, but they are read with `move.w table(pc,d0.w)`. PC-relative reads are program-space accesses, so the CPS2 decrypts them like opcodes, and they are *meant* to be stored encrypted. (An attempt to store them plain broke the indexes: $2A15/$CD03.) Tables reached through `lea table(pc),a0` and then `(a0)+` are data reads and are stored plain.
- Verified only partly: MAME screenshots of Funsha in stage 3 no longer show the extra sprite; the exact moment in the user's video was not reproduced.

**Testing tools added:** `objlog.lua` (walks the 8 object lists at `$FF0032` and logs name/position/`$6C`/`$6E`; clears the group counts each frame so gated waves still appear); OpenCV (`cv2`) reads the user's videos for frame grabs.

- Patched CRCs: `mmxj.03` 89ea923f, `mmxj.05` 1ac66667, `mmx.01` a39b5635, `mmx.14m` 57edf597, `mmx.16m` 6c5b4e10, `mmx.18m` b82b2e3c, `mmx.20m` faefe1f8.
- Not done: checking classes `$61` and `$8C` (names differ between versions; not reported as wrong).

### Build 15 (26/11/28)

**Correction to Build 14's Kame fix:** `$3B716` is **not** the cube spawner. It spawns the burnt **ground wreck** left by a destroyed ground enemy:
- 32 max (`$FF008A`);
- high word bit 0 (= object `$8` bit 3, set for ground objects) picks the ground list `$FF0086`, which scrolls with the background;
- the low word picks the wreck graphic.

Build 14 changed Kame's wreck type to `$100` (so the "cube" counted in that test was a wreck), and no gold cube appeared on the user's MiSTer. That patch is removed: the wreck is back to type 0 on the ground list.

**The gold-cube spawner is `$3930E`** (DC `$8C011208`, called "explosion" in the earlier port notes): d0 x, d1 y, d4 = cube size; it falls down the screen. The cubes go on the list at `$FF005C`, count at `$FF0060`. `bullet_cancel.asm` (Build 4/6) already uses it with size 1. The Hanabi/Chubi/Shobi/TELPO/Zan ports call it at their deaths with the DC's sizes, so those drop cubes too.

**Fix:**
- DC Kame's death: bullet (type 3, speed 8), sound `$16`, wreck (`$8C011E00`, type 4 + random), then cube **`$8C011208` with size 0**.
- Arcade Kame_Musi's death (`$13D494`): bullet, wreck (`$3B716`), sound, and no cube.
- The sound call `jsr $151E5E.l` at `$13D4FE` now calls `kame_drop` (in `asm/hanabi.asm`, patched by `hanabi_port()`). It does `$3930E` (x, y, size 0) with d0/d1/d4 saved, then `jmp $151E5E`, a tail jump so the sound call's stack arguments stay where they were.

**Verified** in MAME stage 3: Kame deaths add cubes at `$FF0060`, small gold cubes appear where the beetles die, and the wrecks are unchanged.

- Patched CRCs: `mmxj.03` 89ea923f, `mmxj.05` af7bc819, `mmx.01` a39b5635, `mmx.14m` 57edf597, `mmx.16m` 6c5b4e10, `mmx.18m` b82b2e3c, `mmx.20m` faefe1f8.
- Not checked: the "+5" value the user expects. Size 0 is what the Dreamcast passes; the cube's pickup value wasn't measured.
- Cube sizes (`$3930E` d4), seen side by side in MAME: 0 = a single small cube, 1 = the double cube (the "+5" one), 2 and 3 = bigger blocks. The user chose to keep size 0 for Kame.

### Build 16 (26/11/28)

**Fix: the stray dash under the stage 3 fighters is in Funsha2's own frames** (`funsha2_stray_line()`). Build 14's guess (the list-4 extra sprite) was wrong, and that patch (`funsha_no_ghost`) is removed again.
- Found with `maskcmp.py`, which compares the opaque-pixel masks of an arcade sprite table with the DC's table for the same enemy, frame by frame and tile by tile:
  - Funsha (`$139DDA` vs `$8C1EB7D0`, 192 frames): identical;
  - Funsha2 (`$13AF96` vs `$8C1EC7D0`, 192 frames): frames 168–173 have extra opaque pixels on their bottom row (y = 31) that the DC's are missing, 3–9 pixels per frame. That's the small light dash under the fighter on those facings.
- Fix: those pixels are set transparent (colour 15) in the 8 tiles involved: `$24F80`, `$24F81`, `$24FA1`, `$24FC1`, `$24FE1`, `$25001`, `$25021`, `$25022` (`FUNSHA2_STRAY_PIXELS`).
  - Only the Funsha2 table entries `$13BA16`–`$13BA66` use these tiles (scan of all sprite tables), so nothing else changes.
  - The step checks each pixel is opaque before clearing it. It runs after `code.commit()` (graphics ROMs only) and is part of the static patches, since no DC data is needed.
- Verified: after the fix, `maskcmp` reports no differences for all 192 Funsha2 frames. Funsha2/Funsha appear only in the Arrange layouts.
- Note: `maskcmp` first printed only 8 differences per frame, and frame 169 has 9; the 9th pixel (tile `$24FA1` x 9) was caught on the re-check.

- Patched CRCs: `mmxj.03` 89ea923f, `mmxj.05` 92d01fd1, `mmx.01` a39b5635, `mmx.14m` 8f2de77d, `mmx.16m` 8790e311, `mmx.18m` 1fb89c96, `mmx.20m` af1f5b11.
- Not done: running `maskcmp` over the other enemies used by the Arrange layouts, to catch similar stray pixels.

### Build 17 (26/11/28)

**KAITEN2 (Arrange stage 4 opening turrets) drops a big gold cube.** The arcade class sets the dead flag (`bset #0,$D(a6)` at `$13D42C`) with no cube; that 6-byte instruction is replaced by `jsr kaiten_hit` (`asm/hanabi.asm`), which does the `bset` and then calls the cube drop `$3930E` with d0/d1 = the enemy's X/Y and d4 = 2 (big cube).
- Started an audit (`cubeaudit.py`) of cube drops per class, arcade (`$3930E`/`$39328`/`$392D2`, size in d4) vs DC (`8C011208`/`8C011220`/`8C01116C`, size in r6). Size differences found so far, not yet changed: SoftBall `$12C23C` (1 vs DC 2), BEE_ZAKO `$12CE24` (1 vs 2, plus a second DC drop), Big_I (no drop vs DC 3), Mini_Battery (1 vs DC 4 on a second drop). CHU_Z800 and Mini_Battery's first DC drop take the size from a register.
- Not verified in MAME yet.

### Build 18 (26/11/28)

**The ORIGINAL / ARRANGE menu only shows with credits.** The `$157F64` hook (`mm_frame`) also runs during the uncredited attract title, so the menu was drawn at CREDIT 0. `mm_frame` now reads the credit count (byte `$FF49A3`, found by comparing RAM dumps after 1 and 2 coins):
- 0 credits: it writes `" OVERPOWERED"` at column `$12`, row `$13` in the gold font (tile `$320` + ASCII, attr `$0C`, as CREDIT) and blanks row `$15`, then makes the original call;
- otherwise it reads Up/Down and draws the menu as before.
- `title_text` (title init) now writes OVERPOWERED straight to the text layer in the same gold font (was the white `$152446` print) and blanks the ARRANGE row, so the title is right on its first frame too.
- `mm_line`'s text loop is split out as `mm_put` (row d2, attr d3, font offset d4); the `bsr`s became `.w` (distance).
- Verified in MAME: attract title at CREDIT 0 shows gold OVERPOWERED and no menu; after a coin, CREDIT 1 shows the menu.
- Patched CRCs: `mmxj.03` 89ea923f, `mmxj.05` c0909d85, `mmx.01` a39b5635.

### Build 19 (26/11/28)

**Gold cube sizes matched to the Dreamcast** (finishing the Build 17 audit, `cubeaudit.py` + reading the DC code by hand):
- SoftBall `$12C23C`, BEE_ZAKO `$12CE24`, CHU_Z800 `$1366CE`: `move.w #1,d4` -> `#2` before `jsr $3930E` (DC: `mov #2,r6` before `8C011208`; CHU's is in a `bf/s` delay slot at `$8C0DEB36`, which the audit missed).
- Big_I: the death sound call `jsr $151E5E` at `$12425E` becomes `jsr bigi_drop` (`asm/hanabi.asm`): a size-3 cube at X/Y, then `jmp $151E5E` (same trick as `kame_drop`, so the stacked sound arguments stay in place). DC: `mov #3,r6` at `$8C0C07CC`.
- Checked and left as is: Mini_Battery (DC first drop is `mov #1,r6` at `$8C0C3F46`, same as arcade; the `#4` drop belongs to the next DC function, past the audit's range). BEE_ZAKO's second DC drop (`$8C0D0BD0`) is also outside the class's routine. The remaining audit differences were register-passed sizes or name mismatches.
- Not verified in MAME (these enemies need the right stage reached); the patches pass the encryption check and build.
- Patched CRCs: `mmxj.03` 89ea923f, `mmxj.05` c53e942c, `mmx.01` a39b5635.

### Build 20 (26/11/28)

**Full cube-drop audit, following control flow** (`tools/flowaudit.py` in the scratchpad). For each class used by the Arrange lists, every routine (descriptor +$14..+$24) is walked on both sides: branches (with SH-4 delay slots), calls 2 levels deep, and DC tail calls (`jmp @rn` through a literal). Drops are calls to `$3930E`/`$39328`/`$392D2` (size in d4) and `8C011208`/`8C011220`/`8C01116C` (size in r6, including `mov #n,r6` in a `bf/s` delay slot). The Build 17 linear scan was wrong in both directions: it read past function ends (Mini_Battery's "#4" drop) and missed tail calls (Roller, KAKASHI and the stage 4 boss parts showed no DC drops).
- Fixed:
  - CHOZ `$135DAE`: d4 0 -> 1 (DC `mov #1,r6`, `$8C0DD440`).
  - Une: the DC drops `8C011220` size 0 (spread, `$8C0FB134`), then tail-calls `8C011208` size 0. The arcade's `jsr $3930E` at `$144774` becomes `jsr une_drop` (`asm/hanabi.asm`), which calls `$39328` (`SPREAD`) with the same d0/d1/d4 and then jumps to `$3930E`.
- Same on both sides once read by hand: St_5OB (arcade size 2 at `$129E98`, reached through the `$129DFA` state table), the boss parts (BS4_*, BS5_ETC_5, BS4_HOU, B_Zako*, GOTSU3, ST2FORT8: same type/size, the DC loops where the arcade is unrolled), and every `$392D2`/`8C01116C` table drop (no size).
- Left as is: THE TOWER (the DC size comes from a variable, `mov.l @r2,r6`); DAI (the DC's class $8C is named HOHDAIY and has no drop in its routines; the arcade drops size 3); Big_BattleShip (the DC drops are outside the class routines). None of these can be matched from the code alone.
- **Placement**: the Arrange lists are copied verbatim (`arrange_layouts`: time, x, y, flags, class, script, c, d; no record dropped since `ARC_MISSING_CLASSES` is empty). Class numbers map to the same enemy on both sides (names match, apart from DC spelling: `B_BShip`, `BUILDING_0x`, `S_BatteryL/R`, `ST3B_00`, and DAI/HOHDAIY, ATCPRG01/ATCPRG00). Classes $00, $47, $72, $84, $90, $B0, $C9, $D0 have no entry in the DC table at `$8C15D3B0` (set up some other way on the DC) and use the arcade's own enemies (Sada_p, SENSYA_00, GIGA, TANK_S, MAN, O_OPNHOU, O_TANK).
- Verified in MAME (Arrange stage 2, held fire, `cube2.lua` counting writes to the cube count `$FF0060` by enemy name): Une 96 -> 117 versus Build 19, all other counts the same, no crash. CHOZ (stage 6) not run.
- Patched CRCs: `mmxj.05` e018ff4d.

### Build 21 (26/11/28)

**Extra life every 10,000,000,000 points** (`asm/extend.asm`, `extra_lives()`).
- Found in MAME: game struct `$FF4978` (`$FF009A` points to it); per player (P1 at +$28, P2 at +$4E): lives word +$8 (P1 `$FF49A8`, P2 `$FF49CE`), score +$A (6 bytes BCD, 12 digits, P1 `$FF49AA`, P2 `$FF49D0`). Lives start from +$22 (`$160BD8`) and drop at `$160C94` (`subq.w #1,$30(a6)`).
- Every frame, `$1618F6` turns each player's pending points into 6 BCD bytes and adds them with `$321B4` (a0 = amount, a1 = score; 6 x `abcd`, capped at 999999999990). Its first 6 bytes (`movem.l d0/a0-a1,-(a7)` / `addq.w #6,a0`) become `jmp ex_add`. `ex_add` saves the score's top byte (the 10- and 100-billion digits, BCD), does the same add and cap, and if a1 is a player's score adds (new - old) to the lives word before it, capped at 99.
- The address check masks a1 to 24 bits: the game reaches RAM as `$FFFFxxxx` too, so the first version never matched.
- Code at `$17CF00`: the second Arrange region now ends at `$17CF00` (was `$17D000`).
- Verified in MAME (`extest.lua`: P1 score set to 99,999,999,000): the player died at frame 1667 (lives 3 -> 2), the score passed 100,000,000,000 at frame 1685 and `ex_add` (`$17CF5E`) set lives back to 3.
- No extend sound or message.
- Patched CRCs: `mmxj.03` ac065c81, `mmxj.05` 3727b060, `mmx.01` a39b5635. 

### Build 22 (26/11/28)

**Extra lives stop at 5** (`asm/extend.asm`, `MAX_LIVES` 99 -> 5).
- `ex_add` now leaves lives alone when they are already 5 or more (so a higher starting-lives setting is never cut down), otherwise adds the steps crossed and caps the result at 5.
- Verified in MAME (`extest5.lua`): with 3 lives, crossing 20,000,000,000 gave 4 (`$17CF66`); with lives set to 5 just before the crossing, there was no write.
- Patched CRCs: `mmxj.03` ac065c81, `mmxj.05` 1678fc6f, `mmx.01` a39b5635.

### Build 23 (26/11/28)

**Extra-life chime for the score extra life** (`asm/extend.asm`).
- The game's own extra lives (weapon level 4 at `$11EC9A`, the 1UP item at `$5658C`) call `$160BEE` (add a life; d0 bit 0 = P1, bit 1 = P2), then play sound `$72` with `clr.l -(a7) / clr.l -(a7) / move.w #$72,-(a7) / clr.w -(a7) / jsr $151E5E / lea 12(a7),a7`.
- `ex_add` makes the same call (all registers saved) right after it raises the lives, so only when a life is really given (not at the cap).
- Verified in MAME (`snd.lua`): at frame 1685 the score passed 100,000,000,000, lives went 2 -> 3 (`$17CF66`) and `$151E5E` put `$72` in the sound queue (`$FFAC86`, `pc=$151E80`) the same frame. Not listened to.
- Patched CRCs: `mmxj.03` ac065c81, `mmxj.05` fb70c5c4, `mmx.01` a39b5635.

## Testing in MAME

The headless MAME env lives in WSL `~/mame` (WSL clears `/tmp` between commands, so keep test ROMs in e.g. `~/mame/roms_mmop`) (see the `mame0.289_dev_headless` repo). MAME doesn't know `mmatrixop`, so test as `mmatrixj` with a MAME-layout zip from `py overpowered.py ... --mame-zip mame_mmatrix.zip`:

```
mkdir -p ~/mame/roms_mmop && cp <mame_mmatrix.zip> ~/mame/roms_mmop/mmatrix.zip && cp ~/mame/roms/qsound.zip ~/mame/roms_mmop/
cd ~/mame && GAME=mmatrixj ROMPATH=~/mame/roms_mmop BT_SNAP=50 scripts/run.sh 900
```

Screenshots go to `work/snap/mmatrixj/`. Frame 50 is the warning screen and frame 200 is the Japan-only notice. "WRONG CHECKSUMS" for the patched files is expected.

## Build rule

Every update bumps the build number (and sets the date) in the `.mra` `<name>`, gets run through `overpowered.py --write-web` (which updates `index.html` and the CRCs), and gets an entry in the README change notes and here.
