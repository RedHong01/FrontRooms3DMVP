# Wallpaper print tools (the motion layer of the "sandwich" wallpaper)

Design and research: `Documentation/research/wallpaper_motion/10_synthesis.md`.

## Ownership

- **Wallpaper-print chat:** owns everything in this folder: the print content, the pack tool, the importer and the driver.
- **Visual chat (游戏视觉):** owns the paper layer and the `_FR_PRINT` path in `FrontRooms/Surface` (P0).

## Contract with the shader

| Global | Meaning |
|---|---|
| `_FR_Print` | Texture2DArray. One slice = one 0.75 × 1.125 m roll tile, 1024×1536, linear. R = ink density (0 ground, 0.5 mid, 1 deep), G = cream/accent, B = phosphor glow ink, A unused |
| `_FR_PrintClock` | x = frame position [0, n), y = n, z = per-roll phase (frames), w = live mix (0 shows the material's static `_PrintTex` frame 0) |
| `_FR_PrintWarp` | x = amplitude (m), y = phase (rad, [0, 2π), wrapped on the CPU), z = wavelength (m), w = enable. Divergence-free warp, periodic every 3 m. Exact HLSL is in the visual chat's `PrintUV` helper. |

The palette (ground, mid, deep, cream) lives in each material, never in the frames.

## Making a print

Use a Python with numpy and Pillow; on this Mac that is `/usr/bin/python3`.

```bash
/usr/bin/python3 Tools/print/print_tool.py gen-test Tools/print/frames/chevron_test
/usr/bin/python3 Tools/print/print_tool.py validate Tools/print/frames/chevron_test
/usr/bin/python3 Tools/print/print_tool.py pack Tools/print/frames/chevron_test Tools/print/out/FR_Print_ChevronTest.png
/usr/bin/python3 Tools/print/print_tool.py preview Tools/print/frames/chevron_test Tools/print/out/chevron_test_preview.png
```

**Authoring art in Figma or After Effects**
- Make a 750×1125 frame (1 px = 1 mm), with the motif in black on white.
- Duplicate any shape that crosses an edge onto the opposite side, so the tile repeats seamlessly.
- Export one PNG per keyframe (K00.png, K01.png, …) and pass `--art` to `validate`, `pack` and `preview`.

**What the commands do**
- `validate` fails any frame whose wrap seam differs from its interior neighbours by more than 1.5×.
- `pack` refuses to pack frames that fail `validate`.

**Keyframe order matters**: the order is the story. The driver blends only to the adjacent slice (K07 blends back to K00). Jumping to a non-adjacent slice is a hard cut, and it is only allowed while the change is masked (unseen, or during a lamp dropout).

## Test content: `frames/chevron_test`

Eight keyframes built from today's chevron ink, with the same formula as `gen_surfaces.py`. Each step adds one more thing wrong with the paper:

| Frame | Change |
|---|---|
| K00 | original |
| K01 | mirrored |
| K02 | half-drop |
| K03 | double repeat |
| K04 | starved ink |
| K05 | flooded ink |
| K06 | negative |
| K07 | turned |

Every frame passes the seam check. The packed sheet is 4096×3072 (4 × 2 slices). Preview: `out/chevron_test_preview.png`.

## Unity scripts: `unity_staging/` (NOT in Assets yet)

- **`Assets/Scripts/Rendering/FrontRoomsPrintDriver.cs`** writes the three globals above.
  - **Motion:** a `HoldAndJump` module by default (45–90 s holds, 1.2 s smoothstep blends to the next keyframe), an always-on subliminal drift, and `Crawl` beats through `Play(...)`.
  - **Game API:** `JumpNext()`, `CutTo(slice)` (masked only), `Frozen` (Caught, pause) and the persisted `ReduceMotion` accessibility switch, which freezes everything.
  - **Startup:** it boots itself once `Resources/Print/FR_Print_ChevronTest` exists, so no scene edit is needed. With no driver, the globals stay 0 and the walls show the static frame 0.
- **`Assets/Editor/Print/FrontRoomsPrintImporter.cs`** imports `Assets/Resources/Print/*.png` as a Texture2DArray.
  - It reads `columns`/`rows` from the matching `.print.json`.
  - Import settings: linear, mips, Repeat, trilinear, aniso 16, CompressedHQ, max 8192.

**Checked (2026-10-02)**
- Both files compile against Unity 6000.3.10f1's own DLLs with Unity's bundled Roslyn, with warnings treated as errors.
- Logic tests pass under the bundled .NET 6 runtime:
  - jump rate matches the hold settings;
  - per-frame blend steps never exceed the smoothstep peak;
  - the K07→K00 loop blend stays inside [7, 8) and then holds at 0;
  - crawl amplitude and duration match, and print speed stays ≤ 0.12 m/s.
- Not yet run inside Unity.

## Promotion

Do this only after the visual chat promotes P0 and Red agrees, while no other chat is compiling.

1. Copy `unity_staging/Assets/Scripts/Rendering/FrontRoomsPrintDriver.cs` and `unity_staging/Assets/Editor/Print/` into `Assets/`.
2. Create `Assets/Resources/Print/`. Copy `out/FR_Print_ChevronTest.print.json` first, then the `.png`, so the importer finds the sidecar on the first import.
3. In Play mode, check that the `FrontRooms Print` object appears and the walls show frame 0, then a blend about every minute.
