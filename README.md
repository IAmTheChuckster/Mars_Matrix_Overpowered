# Mars Matrix Overpowered

A gameplay patch for `Mars Matrix: Hyper Solid Shooting (Japan 000412)`<br>
This repository holds only source, tools and notes. **No ROM data is included**; you patch your own legally owned dump.
   
## About
Why did I make this? Because it's fun and for my own personal research to see the capabilities of Claude.<br>
While Claude was used I put effort in making sure there are balanced gameplay.<br>
I did all the testing and planning.

## Change Notes

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
Open the **[Web Patcher](https://iamthechuckster.github.io/Mars_Matrix_Overpowered/)** (`index.html`) and drop in your `mmatrix.zip`. It checks the file names and CRCs, builds the patched files automatically, and lets you download the patched `mmatrixop.zip` romset and the MiSTer `.mra`. Everything runs in your browser; nothing is uploaded.

### With Python
Requires Windows (trap15's bundled build tools are .exe files).
```
py overpowered.py mmatrix.zip patches/mmxi_v1.0.0_20250412.zip
```
This writes `mmatrixop.zip`. It runs `trap15.py` (the trap15 Improvement build) first, then applies the Overpowered tweaks.

## Testing
This patch was tested with MAME 0.289<br>
It may even work on a PCB but do so on your own risk.

## Credits

- [IAmTheChuckster](https://github.com/IAmTheChuckster)  project, testing
- [Claude](https://claude.ai) (Anthropic)  reverse engineering and patcher code
- Tested on the MiSTer FPGA by

## Disclaimer

This repository contains a fan-made patch for research and technical analysis. The repository does not intentionally distribute the original game ROM, executable, or game assets. Users must obtain their own copy of the original game. This project is unofficial and is not affiliated with, endorsed by, or authorized by Takumi and Capcom. All rights to the original game and its associated intellectual property remain with their respective rights holders. No license to third-party copyrighted material is granted by this repository.
