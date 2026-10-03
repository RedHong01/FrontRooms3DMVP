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

## Chosen pattern: Hard edge (Red, 2026-10-03)

Red picked the precise vector redesign **Hard edge** (Figma section 2407:852, frame WP03 2407:884, master component 2407:2209). Its generator `patterns/hard_edge.py` writes both the SVG and `patterns/out/hard_edge/K00.png`, the static frame 0 the visual chat imports as `_PrintTex`.

```bash
/usr/bin/python3 Tools/print/print_tool.py gen-keys Tools/print/patterns/out/hard_edge/K00.png Tools/print/frames/hard_edge
/usr/bin/python3 Tools/print/print_tool.py pack Tools/print/frames/hard_edge Tools/print/out/FR_Print_HardEdge.png
```

- The 8 keyframes use the same operations as the test set below.
- Every frame passes the seam check.
- Slice 0 is byte-identical to `patterns/out/hard_edge/K00.png`.
- Preview: `out/hard_edge_preview.png`.
- The other directions (faithful_teeth, stepped_grid, hybrid) stay in `patterns/` for reference.

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
  - **Startup:** it boots itself once `Resources/Print/FR_Print_HardEdge` exists, so no scene edit is needed. With no driver, the globals stay 0 and the walls show the static frame 0.
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
2. Create `Assets/Resources/Print/`. Copy `out/FR_Print_HardEdge.print.json` first, then the `.png`, so the importer finds the sidecar on the first import.
3. In Play mode, check that the `FrontRooms Print` object appears and the walls show frame 0, then a blend about every minute.

## Planned: glow-ink textures (spec v1.1, 2026-10-03)

v1 was agreed with the visual chat. v1.1 makes two changes, sent to it for confirmation:
- glyph frames are anchored to each shape, not to the world;
- the substance layers become RG, so the rare overlay can be gated per cell.

The phosphor ink's close-up content does not live in the print's B channel. B is one substance per slice for the whole world, so B stays reserved and 0. The content goes in two global arrays instead. Both are fetched only inside the shader's glow-mask branch.

Generator: `ink_tool.py build <spec.json> <out_dir>`. The draft EGRESS spec is `ink/egress_spec_DRAFT.json`, and its output is in `ink/out_draft/`. The strings belong to the narrative chat, so replace them with its frozen table before shipping.

| Global | Size, format | UV | Layers | Memory |
|---|---|---|---|---|
| `_FR_InkType` | 1024×1024, BC4, linear, mips, Repeat, aniso 16 | Glyph frame / 0.75 (below) | 0 FLOW, 1 FLOW T2+, 2 HERE door, 3 HERE window, 4 STOP, 5 BREACH, 6 pressure chevron, 7 pressure door, 8 forged FLOW, 9–15 reserved | ≈ 10.7 MB |
| `_FR_InkSubstance` | 768×1152, BC5 (RG), linear, mips, Repeat, aniso 16 | The print UV (warped), one 0.75 × 1.125 m roll tile | 0–4 = run tiers 1–5. R = ground (an even 0.8 field with the register marks and roll stamp knocked out). G = rare overlay, shown only where `hash(cell) < _FR_InkOverlayRate` | ≈ 5.9 MB |

**Glyph frames** come from InkShape, in metres. In the textures, v = 0 is the image's bottom row.
- Chevron arms: u runs along the arm from the apex, never upside down; v is the signed offset from the centreline. Rows of text sit at v = 0 and every 34 mm, so 3 rows fall inside a 100 mm stroke.
- Vertical bars: u is measured from the bar's left edge (0–0.10 m), with words centred at 50 mm; v is height above the floor.
- Horizontal bars (STOP): u is measured from the bar's left edge; v from its bottom edge (0–0.12 m). The lockup is centred at v = 60 mm.

**Values:** 1.0 is the solid ink field and about 0.55 is knocked-out type. Strokes must keep a mean of at least 0.6 in any 100 mm square (the draft's worst is 0.89). The shader computes glow × (R + 0.6·G) for the substance.

**Layer selection:** a global `float4 _FR_InkTypeLayer[4]` lookup table, filled by the CPU.

**WebGL:** substance only, at 384×576 RG (≈ 1.5 MB), or the B/A two-family fallback.
