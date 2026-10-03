# Kit three-view renderer

`FrontRoomsThreeView.cs` renders every kit asset (Assets/Resources/Props/Models) as transparent PNGs: third-angle top / front / side at one round scale per sheet, plus a 4:3 hero. These PNGs feed the Figma section "FRONTROOMS · PROP KIT · THREE-VIEW + ERA" (page "Indivicual Game Project", section 2324:852).

It is kept outside Assets on purpose, so it never compiles in the editor Red has open. To use it:
1. Clone a project copy (APFS, about 4 s): `cp -Rc <project> <scratch>/proj3v`. Never render in the real project while it is open.
2. Copy this file to `<clone>/Assets/Editor/Rendering/`.
3. Run: `Unity -batchmode -projectPath <clone> -executeMethod FrontRoomsThreeView.RunBatch -threeViewOut <dir> [-threeViewOnly Kit_A,Kit_B] -quit`. It needs graphics, so do not pass -nographics.

Scales: furniture (any side ≥ 0.75 m) is drawn at 250 px/m on the sheet. Small items step up to 500, 1000 or 2000 px/m. PNGs are 2x the sheet scale with 16 px of clear padding. `manifest.json` records sheetPpm, pngPpm, size_m, px sizes, slots and tags per asset.

Fix kept in this version: the render target is single-sampled and AA comes from the supersample. With a multisampled target, URP 17 failed in BlitFinalToBackBuffer ("4 samples but 8 requested") and every PNG came out empty.

To refresh Figma after a model change, re-render only that asset, then call `upload_assets` with `nodeIds` = the existing `img:<Kit_Name>_<view>` rectangles. The layout stays put. If the asset's size changed, also resize its slots. `manifest_2026-10-02.json` is the manifest behind the current sheets.
