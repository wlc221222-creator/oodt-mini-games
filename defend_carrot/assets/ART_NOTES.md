# Game artwork

## Active original-game resources (2026-10-22)

The game now loads the original Carrot Fantasy graphics mirrored in
[JezaChen/CarrotGuardGame](https://github.com/JezaChen/CarrotGuardGame/tree/478f66092f994b95408fa130e8b0418af4f9828f/Resources/Themes).
This is a third-party recreation, not an official publisher download.
The PNG and plist files in `original/` are copied unchanged. Each source path,
pinned commit and Git blob SHA is recorded in `original/source-manifest.json`.
See the repository's THIRD_PARTY_NOTICES.md for ownership information.

- TBottle/TFan: three original attack poses and the resting pose.
- TSun: original centre sprite and five attack halo frames.
- Monsters01: two distinct poses for each of eight monsters; the original frames
  change silhouette, wings and limbs. They are not static images with a scale effect.
- Items01: original carrot and expression frames.
- Theme1/Theme2 BG0: original sky/jungle backdrops.
- Theme1/Theme2 BG1: road interior textures sampled at runtime and clipped to one
  continuous road surface. Borders and cloud lobes follow the same outline at
  every join; the original map's baked route is not used as our route.

`art.py` restores TexturePacker rotation, source canvas and trim position before
scaling. Keeping the source canvas avoids jitter between animation frames.
`animation.py` advances frames only from `update(dt)`. Drawing, pause, menus and
the guide do not advance simulation time. No GIF decoder or new runtime dependency
is required; the GIF under docs/screenshots is a preview of actual gameplay.

## Road, health and scale revision (2026-10-22)

- Roads are rasterized at 3x resolution and reduced with antialiasing. The whole
  route shares one mirrored texture origin. Straight-tile borders no longer
  overwrite each other at turns. Route shape is independent of traversal order.
- The carrot now has three lives; every monster that reaches it consumes one
  life, independently of that monster's damage against towers.
- Health states use original frames: 3 HP = `hlb10.png`, 2 HP = `hlb6.png`,
  1 HP = `hlb2.png`, 0 HP = `hlb1.png`. These are adaptations of the original
  game's damage stages to the new three-life rule. Damaged states keep their
  shared source canvas, stay anchored to the same ground point and cannot be
  replaced by the healthy expression animation.
- Tower source canvases scale from 48 to 64 pixels, normal monsters from 48 to
  64, the larger monster from 56 to 72, and carrot from 74 to 104. Cards, guide
  icons, previews and health bar positions are adjusted. Collision sizes,
  occupied cells and targeting ranges remain unchanged.

## Eight-stage expansion (2026-10-22)

Five additional original tower atlases (Star, BlueStar, Pin, Rocket, Snow) provide
all three upgrade tiers and animation poses. Desert backdrop and road textures
provide the third theme. Files are copied unchanged; pinned source paths and Git
blob hashes are recorded in `original/expansion-manifest.json`. All eight monster
types already have two original poses in the imported Monsters01 atlas.

The course's legacy class/registry IDs remain `Apple/apple`, `Orange/orange`,
`Melon/melon`; they display bottle, fan and sun graphics respectively. Original
tower roles are now implemented, including fan piercing and sun area attacks.
See `defend_carrot/EXPANSION.md` for the original in-game help reference, authored
stage schedules, three-life balance and persistence behavior.

## Menu and interface presentation (2026-10-22)

`presentation.py` shares cartoon panels, bevelled buttons, leaves, clouds and
garden banks drawn in pygame. The menu reuses the original sky texture and
carrot/monster/tower sprites; level cards preview the actual authored routes.
These layouts and decorative shapes are project UI work, not copied commercial
menu screens. No additional image downloads or runtime dependencies are needed.
The guide previews and home-screen decorations use `GameUI.time`, independent
of combat and its speed multiplier. Drawing never advances either clock.

## Previous generated artwork (retained, no longer displayed)

Created for this project with the built-in image_gen tool on 2026-10-21. Original generated PNGs are retained unchanged; runtime code extracts sprite regions, preserves transparency and scales to the game's existing cells. The terrain art contains no paths; scenery.py draws paths from config.py. No combat rules or collision sizes are encoded in these images.

Files:
- character-atlas.png: apple, orange, watermelon, carrot, slime, bat, golem and stone thrower.
- garden-ground.png: garden grass ground.
- forest-ground.png: forest clearing ground.

## Generation prompts

### carrot_atlas

Use case: stylized-concept. Production asset: one 2D tower-defense character SPRITE SHEET, landscape 2:1 canvas. Exactly FOUR equal columns and TWO equal rows, 8 isolated characters, centered in their own equal rectangular cell, ample transparent gutters, no text, no labels, no grid lines. TRUE transparent background. Top row left to right: (1) plump glossy red apple defender with stem and single green leaf, cute determined face (2) juicy orange defender with peel texture, leaf and cheerful eyes (3) large green striped whole watermelon defender with confident face, distinctly broad oval shape (4) friendly bright orange carrot objective with lush green leafy crown and big kind eyes. Bottom row left to right: (5) lime-green translucent teardrop slime monster (6) purple bat monster with wide outstretched wings and small pink ears (7) chunky blue-gray stone golem, rounded rock segments, sturdy feet, warm glowing small eyes (8) ochre little rock creature holding a round pebble above its head, recognizable ranged stone-thrower. All original non-branded characters, polished premium mobile-game hand-painted 2.5D illustration, rounded forms, crisp dark colored outlines, sculpted soft shading, subtle highlights, tiny elliptical soft contact shadows, expressive faces, top-down/three-quarter game view, entire character including wings and leaves fully inside its cell, consistent scale and lighting. Each silhouette must remain readable at 40 pixels. No ground, landscape, panels or interface. Do not overlap cells.

### carrot_garden

Use case: stylized-concept. Production asset: a landscape 3:2 top-down flat grass terrain background for a cute polished 2D tower-defense game, hand-painted mobile-game art, fresh spring garden. Edge-to-edge grassy ground, warm jade and sage green meadow, very subtle organic patches of clover and fine blades, softly dappled sunlight from upper left, tiny white daisies and yellow petals sparsely concentrated at the extreme corners. Entire center 90 percent open low-contrast buildable grass, no large distinct objects. Fine quiet paper-painted texture with soft round shapes, beautiful but subdued so small colorful game sprites stand out. Strict overhead orthographic ground view, no horizon, no perspective vanishing point. No paths or roads, no grids, no stones blocking cells, no trees, no bushes, no water, no buildings, no characters, no text, no UI, no frames. The game's road will be drawn over this art separately.

### carrot_forest

Use case: stylized-concept. Production asset: a landscape 3:2 top-down flat grass terrain background for a cute polished 2D tower-defense game, hand-painted mobile-game art, peaceful forest clearing. Edge-to-edge mossy grassy ground in muted emerald, sage, and blue-green teal, soft diffuse forest canopy light, subtle moss and tiny fern-like ground leaves sparsely concentrated at extreme corners, a few tiny pale blue flowers. Entire center 90 percent open low-contrast buildable grass. Keep terrain light enough to read green monsters and gray creatures clearly; softly shaded, not nighttime or black. Fine quiet painterly texture and rounded shapes, no photorealism. Strict overhead orthographic ground view, no horizon, no perspective vanishing point. No paths, roads, grid, large stones, trees, bushes, water, buildings, characters, text, UI or frames. A sand road will be drawn over the art by game code.

