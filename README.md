# Mars Matrix Overpowered

A gameplay patch for `Mars Matrix: Hyper Solid Shooting (Japan 000412)`<br>
This repository holds only source, tools and notes. **No ROM data is included**; you patch your own legally owned dump.
   
## About
Why did I make this? Because it's fun and for my own personal research to see the capabilities of Claude.<br>
While Claude was used I put effort in making sure there are balanced gameplay.<br>
I did all the testing and planning.

## Change Notes

### Build 21 (26/11/28)
- An extra life every 10,000,000,000 points (at 10, 20, 30 billion and so on), for both players, in both ORIGINAL and ARRANGE. Lives are capped at 99.

### Build 20 (26/11/28)
- More gold cube fixes to match the Dreamcast: Une (the small fliers of stages 1, 2, 3 and 5) now drops two small cubes, one scattered and one on the spot, and CHOZ (stage 6) drops the double cube instead of the small one.
- Every enemy's cube drops and the Arrange enemy placement were re-checked against the Dreamcast; everything else already matches.

### Build 19 (26/11/28)
- Gold cube drops now match the Dreamcast: SoftBall, BEE_ZAKO and CHU_Z800 drop a bigger cube (size 2 instead of the double cube), and Big_I drops a size-3 cube (it dropped none).

### Build 18 (26/11/28)
- Title screen: with no credits it shows OVERPOWERED (in the gold CREDIT font) under the logo; the ORIGINAL / ARRANGE menu only appears once a coin is inserted. (Before, the menu also showed during the attract title at CREDIT 0.)

### Build 17 (26/11/28)
- Arrange stage 4: the spinning turrets at the start of the stage (KAITEN2) drop a big gold cube when destroyed, as on the Dreamcast.

### Build 16 (26/11/28)
- Arrange stage 3: the small stray dash under the white fighters (Funsha2) is gone: some of their frames had a stray line of pixels that the Dreamcast version doesn't have. (Build 14's change for this is undone; it wasn't the cause.)

### Build 15 (26/11/28)
- Arrange stage 3: the blue beetles (Kame) now really drop a gold cube when destroyed, as on the Dreamcast (Build 14's change didn't make them appear).

### Build 14 (26/11/28)
- Arrange stage 3: the blue beetles (Kame) drop gold cubes when destroyed, as on the Dreamcast.
- Arrange stage 3: the white fighters before the boss (Funsha) no longer leave stray shapes underneath them.

### Build 13 (26/11/28)
- The last Dreamcast-only enemy, Zan (the spinning green mines of Arrange stage 4, after the mid-boss), is ported: Zan fires bursts and leaves blinking after-images that turn into smaller Zc mines and fly at you. Graphics are imported from your own Dreamcast disc. Every enemy in the Arrange layouts is now in the game.

### Build 12 (26/11/28)
- The Dreamcast-only TELPO enemy (the green fighters at the start of Arrange stage 2, also in stage 5) is ported: they warp in, fly their routes firing bullet bursts, and warp out. Graphics are imported from your own Dreamcast disc. Zan (stage 4) is still left out.

### Build 11 (26/11/27)
- After inserting a coin, the title screen shows a mode menu: **ORIGINAL** (the arcade enemy layouts, as in Build 9) and **ARRANGE** (the Dreamcast Arrange mode layouts from Build 10). Up/Down moves the arrow; the selected line is in the same gold as CREDIT.
- The Dreamcast-only Hanabi enemy is back in Arrange mode, ported to the arcade with its two child enemies, Chubi and Shobi. Their graphics are imported from your own Dreamcast disc. TELPO and Zan are still left out.

### Build 10 (27/11/27)
- All 6 stages now use the enemy layouts from the Dreamcast version's Arrange mode, imported from your own Dreamcast disc (the arcade backgrounds stay). Three Dreamcast-only enemy types (Hanabi, TELPO, Zan) don't exist in the arcade game and are left out.
- The web patcher has a second drop box for the Dreamcast disc (a .zip of the .gdi dump). No Dreamcast data is stored in the page.

### Build 9 (27/11/27)
- The title screen shows OVERPOWERED under the Mars Matrix logo.

### Build 8 (27/11/27)
- Sound effects now play centered (they were hard left). Music keeps its normal left/right panning.

### Build 7 (27/11/27)
- Fixed out-of-phase sound effects: QSound's 3D "virtual surround" processing is turned off, leaving plain stereo.

### Build 6 (26/11/26)
- Fixed bullet cancelling: only enemy bullets on screen are turned into gold cubes. Build 4 hooked the wrong list (player shots / effects), which made walls of cubes and left enemy bullets alone.

### Build 5 (26/11/26)
- Mosquito 01 (red ship) now has Mosquito 02's (blue ship) top speed.
- The ship select screen shows 5 MAX SPEED boxes for Mosquito 01.

### Build 4 (26/11/26)
- Bullet cancelling: killing an enemy turns every enemy bullet within 24px of it into a gold cube. Any bullet within 16px of a cancelled bullet is cancelled too, so the cancel chains outward through dense bullet patterns.

### Build 3 (26/11/26)
- Chain bar (the "+N" counter under EXP) drains twice as slowly.
- GHB bar refills twice as fast.
- GHB can be used at any time, even while it's still filling (it needs at least 1/16 of the bar).

### Build 2 (26/11/26)
- Warning screen now reads MARS MATRIX OVERPOWERED, the build date and the build number.

### Build 1
- Base build: Mars Matrix Improvement patch v1.0.0 applied, no Overpowered gameplay changes yet.

This patch also includes the Mars Matrix Improvement patch by Alex "trap15" Marshall which was released on the 25th anniversary.<br> 
Source code: http://bitbucket.org/trap15/mmatrix_unfuck/

## Patching the game

### Web Patcher
Open the **[Web Patcher](https://iamthechuckster.github.io/Mars_Matrix_Overpowered/)** (`index.html`) and drop in your `mmatrix.zip` and your Dreamcast Mars Matrix disc (Japan, T-1238M: a `.zip` containing the `.gdi` dump). It checks the files, builds the patched set automatically (importing the Arrange mode enemy layouts from your disc), and lets you download the patched `mmatrixop.zip` romset and the MiSTer `.mra`. Everything runs in your browser; nothing is uploaded.

### From the command line (Python)
You need:
- **Windows** (trap15's bundled build tools, the assembler and encryption tools, are .exe files);
- **Python 3** with **numpy** (`py -m pip install numpy`);
- your MAME **`mmatrix.zip`** (Mars Matrix, parent set with the Japanese `mmatrixj` files);
- trap15's **`mmxi_v1.0.0_20250412.zip`** (already in `patches/`);
- your **Dreamcast Mars Matrix disc** (Japan, T-1238M) as a `.zip` of the `.gdi` dump (the Arrange mode layouts and the Dreamcast-only enemies' graphics are read from it).

Steps, from the repository folder:
1. Put `mmatrix.zip` in `roms/` and the Dreamcast zip at `roms/Mars Matrix DC.zip`.
2. Run:
   ```
   py overpowered.py roms/mmatrix.zip patches/mmxi_v1.0.0_20250412.zip
   ```
3. This writes **`mmatrixop.zip`** (the patched romset, used with `mister/Mars Matrix Overpowered.mra` on MiSTer). It lists each patched file with its CRC32 and the build number from the `.mra`.

The script runs `trap15.py` (the trap15 Improvement build) first, then applies the Overpowered changes and imports the Arrange mode from your disc.

Options:
- `-o <file>`: output file name (default `mmatrixop.zip`).
- `--dc <path>`: the Dreamcast disc somewhere else: a `.zip` of the `.gdi` dump, its `track03.bin`, or a folder holding the extracted `00MMXDC.BIN`, `CG.MMX` and `PAL.MMX`.
- `--mame-zip <file>`: also write a MAME-layout `mmatrix.zip`, to play in MAME as `mmatrixj` (MAME will report wrong checksums for the patched files; that's expected).
- `--write-web`: also update the `.mra` CRCs and the web patcher (`index.html`); used when making a new build.

## Testing
This patch was tested with MAME 0.289<br>
It may even work on a PCB but do so on your own risk.

## Credits

- [IAmTheChuckster](https://github.com/IAmTheChuckster)  project, testing
- Alex "trap15" Marshall  Mars Matrix Improvement patch (the base of this build)
- [Claude](https://claude.ai) (Anthropic)  reverse engineering and patcher code
- Tested on the MiSTer FPGA by

## Disclaimer

This repository contains a fan-made patch for research and technical analysis. The repository does not intentionally distribute the original game ROM, executable, or game assets. Users must obtain their own copy of the original game. This project is unofficial and is not affiliated with, endorsed by, or authorized by Takumi and Capcom. All rights to the original game and its associated intellectual property remain with their respective rights holders. No license to third-party copyrighted material is granted by this repository.
