# Third-party material

## Plants vs. Zombies graphics

- Asset reference: https://github.com/marblexu/PythonPlantsVsZombies
- Reference project: `PythonPlantsVsZombies`, maintained by marblexu.
- The reference README describes its use as personal learning and noncommercial use.
- Plants vs. Zombies characters, names and original graphics belong to their respective rights holders, including PopCap / Electronic Arts.
- This repository does not claim ownership of those assets or grant an additional license for them.
- Original shovel sprite: `plants_vs_zombies/assets/graphics/Screen/Shovel.png`, copied unchanged from [FregD156/PvZ_Assets](https://github.com/FregD156/PvZ_Assets/blob/8ba94e95cfe7d0de5682f8258d3b932dbdac885c/images/Shovel.png). That repository identifies the graphics as extracted from the original game's macOS `main.pak`. Git blob SHA: `8b27bd461c636b30254df95e7b609066a9a99eb4`. The sprite remains the property of PopCap / Electronic Arts; no additional rights are granted here.

## Carrot Fantasy / 保卫萝卜 graphics

- Source mirror: [JezaChen/CarrotGuardGame](https://github.com/JezaChen/CarrotGuardGame/tree/478f66092f994b95408fa130e8b0418af4f9828f/Resources/Themes), a third-party cocos2d-x recreation.
- Pinned revision: `478f66092f994b95408fa130e8b0418af4f9828f`.
- Imported PNG/plist files: `defend_carrot/assets/original/`. Source paths and Git blob hashes are listed in `source-manifest.json` and `expansion-manifest.json`; files are retained unchanged and decoded at runtime. The expansion adds Star, BlueStar, Pin, Rocket and Snow tower atlases plus the desert scene.
- These are original-game graphics preserved by that mirror, not graphics supplied by an official publisher asset service. The mirror does not establish a separate license to the commercial game's artwork.
- Carrot Fantasy characters, names and original graphics remain the property of their respective rights holders. This educational project claims no ownership and grants no additional rights to these assets.
- The older generated artwork is retained for project history but is no longer displayed by the game.

## Runtime libraries

Windows executables bundle Python, pygame/SDL and, for Plants vs. Zombies, NumPy. Their upstream notices and licenses are distributed in the Windows download packages under `licenses/`.

- Python: https://www.python.org/psf/license/
- pygame: https://www.pygame.org/docs/LGPL.html
- NumPy: https://numpy.org/doc/stable/license.html
- PyInstaller's bootloader distribution exception: https://pyinstaller.org/en/stable/license.html
