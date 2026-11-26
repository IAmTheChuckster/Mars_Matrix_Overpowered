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

## Testing in MAME

The headless MAME env lives in WSL `~/mame` (WSL clears `/tmp` between commands, so keep test ROMs in e.g. `~/mame/roms_mmop`) (see the `mame0.289_dev_headless` repo). MAME doesn't know `mmatrixop`, so test as `mmatrixj` with a MAME-layout zip from `py overpowered.py ... --mame-zip mame_mmatrix.zip`:

```
mkdir -p ~/mame/roms_mmop && cp <mame_mmatrix.zip> ~/mame/roms_mmop/mmatrix.zip && cp ~/mame/roms/qsound.zip ~/mame/roms_mmop/
cd ~/mame && GAME=mmatrixj ROMPATH=~/mame/roms_mmop BT_SNAP=50 scripts/run.sh 900
```

Screenshots go to `work/snap/mmatrixj/`. Frame 50 is the warning screen and frame 200 is the Japan-only notice. "WRONG CHECKSUMS" for the patched files is expected.

## Build rule

Every update bumps the build number (and sets the date) in the `.mra` `<name>`, gets run through `overpowered.py --write-web` (which updates `index.html` and the CRCs), and gets an entry in the README change notes and here.
