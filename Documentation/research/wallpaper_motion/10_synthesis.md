# Wallpaper as motion graphics: the "sandwich" (research synthesis)

Red's idea, 2026-10-02: the Level 0 wallpaper's printed pattern becomes a motion-graphics layer that can change. A static texture layer sits above it and gives the paper its material feel. Lighting, shading and reflections come from that texture layer only, never from the moving pattern.

STATUS: research complete (2026-10-02). No project file was changed; nothing is implemented. Five research directions ran in parallel, each followed by an adversarial verifier that tried to refute its load-bearing claims. The verifiers' corrections are applied below. Raw reports and verdicts: `agent_reports.json`. Source ledger: `SOURCES.md`.

## 1. Verdict

**It works, it is cheap, and URP already behaves the way the idea needs.**

- **Highlights cannot see the print.** The wallpapers are `_Metallic = 0`. URP 17.3 builds specular colour as `lerp(0.04, albedo, metallic)` (BRDF.hlsl, `InitializeBRDFData`), so specular stays a constant 0.04 whatever the albedo is. An albedo-only print changes only the diffuse term. Highlight shape and size, the normal and the cavity come from the paper layer. (Verified in the package source; confirmed by the verifier.)
- **There is no bounce light to fall out of step.** The project has no lightmaps, realtime GI, light probes or APV. Ambient is a fixed trilight SH set by `FrontRoomsLook`, so an animated albedo can never disagree with indirect light.
- **SSAO ignores both layers.** The shader's DepthNormals pass includes URP's generic `DepthNormalsPass.hlsl`, which writes only the interpolated geometric normal (no `_NORMALMAP` keyword, no PlanarFrame). Corner darkening therefore never traces the print.
- **Real wallpaper is built in the same order.** Substrate → ground coat → printed ink film → clear vinyl/acrylic coat, with embossing applied after printing. Machine-printed ink is "merely a film of colour" on the sheet (V&A). Ink is colour; the paper and coating own the surface. Sources in `SOURCES.md` §A.

What "lighting from the texture layer" means precisely: the print still shows as *colour under the light*. Printed ink does that physically: a dark chevron is darker because it absorbs light, and it goes dark when the lamp dies. What never comes from the print is the surface: the bumps, sheen, highlight shape and occlusion. If the pattern should instead stay visible in the dark like a screen, that is emission. It is a different look and a design decision (§6, fork 1).

## 2. The one real blocker: today's paper *is* the chevron

`Tools/lookdev/gen_surfaces.py` `wallpaper()` bakes the chevron ink into every lighting input, not only the albedo:

| Map | Ink term today |
|---|---|
| height → `_BumpMap` | `0.9 * blur(ink)` (largest term) |
| smoothness (`_MaskMap` R) | `+0.07 * blur(ink)` |
| cavity (`_MaskMap` G) | `-0.10 * ink` |

The shading researcher measured the generator's height terms. Beyond about 0.5 m (mip 1+, FOV 76°, 1080p), the chevron is 94–98% of the slope energy left in the normal map; the 1.17 mm weave term vanishes. So today's lit relief at play distance essentially *is* the chevron. The verifier adds that real normal-map mip averaging flattens even more than the Gaussian proxy used, so the claim is if anything understated. **If only the albedo animates, the old chevron stays visible in the highlights as a ghost.**

So `wallpaper()` must be split (visual chat's file):

1. **Paper skin (static):** albedo as a mean-1 *modulation* (fibre, mottling, blots, foxing, roll-seam shadow), normal (weave + fibre + seam, **no ink**), mask (smoothness and cavity without ink terms). Add an unregistered, period-plausible texture emboss (stipple or linen, ~2–6 mm) so the paper still reads as paper at mip 1–3 once the chevron relief is gone. That is a visible look change and needs visual-chat sign-off.
2. **Print (motion):** a separate ink *density* texture. It must be **continuous, not binary**. Today's albedo is a three-stop duotone (ground → mid → deep), plus `keep_hue` chroma from the source, plus a cream lift where the source is bright. A thresholded SDF and a single ink tint cannot reproduce that (verifier: refuted). Store continuous density, plus a cream/accent channel, and keep the palette (ground/mid/deep/cream) as material colours. That also lets Lobby, Shift and Exit share one print and differ only by palette, retiring `Wallpaper_Chevron_Cold`.
3. **Optional ghost emboss:** the old chevron relief as its own normal map (imported as NormalMap), behind a 0–1 dial. Off by default. This is the deliberate version of the blocker: Gilman's "sub-pattern" that shows only in certain light (§5).

Expected parity: with the clock stopped, frame 0 gives a *close* match to today's look, not an exact one. Validate side by side (§7, T1).

## 3. Shading architecture (recommended)

**Option (a): extend `FrontRooms/Surface` with a print layer.** Rejected alternatives:

- **Shader Graph rebuild:** its DepthNormals uses mesh tangents, which conflicts with the world-planar frame. Use Shader Graph only to author print content if wanted.
- **Complex Lit clear coat:** about 2× lighting cost, and one shared normal.
- **URP decals (DBuffer):** not on WebGL/GLES, not SRP-batched, and the receiving shader needs DBuffer keywords anyway.
- **Detail maps:** a static ×2 multiply on mesh UVs.

Layer order inside `Frag()` (bottom to top):

```
paper modulation (static)      ← _BaseMap  (paper-only, mean ≈ 1)
× print colour (motion)        ← InkRamp(density) from the global print texture
× ageing over the print        ← foxing/blots/seam shadow already inside the paper modulation (multiply commutes),
                                  then the existing macro wear, stains, floor/ceiling grime
→ s.albedo ONLY
normal, smoothness, cavity     ← paper only (_BumpMap, _MaskMap) — the print never writes these
```

Stains and grime must sit *over* the ink. Otherwise the print reads as a projection. The existing macro-wear block already runs after the albedo fetch, so it keeps working unchanged.

Sketch, reconciled from the three shader reports (not applied):

```hlsl
// File scope, OUTSIDE UnityPerMaterial and NOT in Properties{} so Shader.SetGlobal* reaches it.
TEXTURE2D_ARRAY(_FR_Print);   // R = ink density (continuous, linear), G = cream/accent; optional B = SDF for shape morphs
float4 _FR_PrintClock;        // x = frame position [0,n), y = n, z = per-roll phase (frames), w = live mix (0 = static fallback)
// Per material, INSIDE UnityPerMaterial + Properties, written by the SurfaceDef table:
//   half4 _InkGround, _InkMid, _InkDeep, _InkCream; half _PrintAmount;

float Hash01(uint x) { x ^= x >> 16; x *= 0x7feb352du; x ^= x >> 15; x *= 0x846ca68bu; x ^= x >> 16; return (x & 0xffffu) / 65535.0; }

half3 InkRamp(half t)  // today's duotone, ground → mid → deep
{
    return t < 0.5h ? lerp(_InkGround.rgb, _InkMid.rgb, t * 2.0h)
                    : lerp(_InkMid.rgb, _InkDeep.rgb, t * 2.0h - 1.0h);
}

// In Frag(), replacing the albedo line (uv is already metres / _TileSize, i.e. in rolls):
half3 paper = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv).rgb;    // paper-only modulation
float2 dx = ddx(uv), dy = ddy(uv);                                     // gradients from the CONTINUOUS uv: no mip seam on roll lines
uint strip = (uint)(int)floor(uv.x) & 3u;                              // & 3 keeps the "every 3 m module looks the same" rule
float n = _FR_PrintClock.y;
float f = _FR_PrintClock.x + Hash01(strip) * _FR_PrintClock.z;
f -= n * floor(f / n);
float i0 = floor(f), k = f - i0, i1 = (i0 + 1.0 >= n) ? 0.0 : i0 + 1.0;
half2 a = SAMPLE_TEXTURE2D_ARRAY_GRAD(_FR_Print, sampler_BaseMap, uv, i0, dx, dy).rg;  // reuse sampler: Repeat, trilinear, aniso
half2 b = SAMPLE_TEXTURE2D_ARRAY_GRAD(_FR_Print, sampler_BaseMap, uv, i1, dx, dy).rg;
half2 ink = lerp(a, b, k);
half3 print = lerp(InkRamp(ink.r), _InkCream.rgb, ink.g * 0.55h);
albedo.rgb = paper * print * _BaseColor.rgb;
// nTS, mask.r (smoothness) and mask.g (cavity) stay paper-only → lighting comes from the texture layer.
```

Binding rules:

- Shared, time-varying state goes in **globals**: `Shader.SetGlobalTexture` / `SetGlobalVector` with names that are *not* in Properties.
- Per-material palette and strength go in **UnityPerMaterial**, outside any `#if`, so the layout is identical in every pass.
- Add `#pragma shader_feature_local_fragment _FR_PRINT` to the ForwardLit pass only. `FrontRoomsRenderSetup` enables it on `L0_Wallpaper`, `L0_Wallpaper_Shift` and `Exit_Wallpaper`, and its regeneration path must keep the keyword and properties. Turn the print on and off at runtime through the global mix, not keyword toggles.
- An unset global float is 0, so edit mode, lookdev captures and the Level Designer preview fall back to the static print. A small `[ExecuteAlways]` driver can bind a default.
- SRP Batcher note (verifier correction): map wall shells *already* carry a MaterialPropertyBlock (`_CeilingHeight`, `FrontRoomsMapWorld.cs:764-768`), so they are not SRP-batched today. The print adds no new batching loss. Don't add more MPBs; the stream-room walls still batch.

## 4. Where the moving pattern comes from

| Source | Verdict | Why |
|---|---|---|
| **Texture2DArray flipbook of ink keyframes** | **Primary** | Authored in Figma/AE, packed by a script. One global clock drives every wall, so they stay in sync. Mips and aniso are baked offline (the main anti-moiré tool). Works on Metal and WebGL2. Per-roll phase offsets are possible. |
| Procedural pattern in the shader (SDF chevron, `fwidth` AA) | Fallback B | Zero memory, infinitely sharp, but nothing can be drawn in Figma. Good for parametric breathing and drift. |
| UI Toolkit panel → RenderTexture (`PanelSettings.targetTexture`), Figma SVGs via the 6.3 SVG importer | Fallback A | Freeform live motion graphics. Needs `useMipMap` + `GenerateMips` after each write, `anisoLevel` set, wrap Repeat. Loses per-roll phase. |
| CustomRenderTexture (reaction-diffusion, cellular) | Events only | Good for a scripted "mutation" seeded from frame 0, but not reproducible and doesn't look like 1990 printing. |
| VideoPlayer → RenderTexture | No | The Video module isn't in the manifest. WebGL video plays from a URL only. Chroma subsampling smears 37 mm stripes, and seamless looping is unreliable. |
| Compute shader | No | No compute on WebGL2. |

Authoring workflow for the flipbook:

1. **Figma frame setup:** a 750 × 1125 frame, so 1 px = 1 mm and one frame is one roll repeat. Turn on Clip content. Draw the motif black on white.
2. **Seams:** duplicate any shape that crosses an edge at ±750 / ±1125. Keep a 3×3 instance preview to check seams.
3. **Keyframes:** make one frame per keyframe (K0–K15). Keep matching shapes between neighbours so a morph reads well. Export PNG/SVG.
4. **Timed motion:** use After Effects instead. Build a comp in whole-frame loop lengths and check seams with Offset or Motion Tile. Render a greyscale PNG sequence, with no paper texture and no light baked in.
5. **Pack:** a pack script (to be written, visual chat's tools) builds density + cream channels, downsamples to 512 × 768 per frame and lays out an 8 × 4 sheet. A seam validator checks left/right and top/bottom edges in every frame, and frame 0 against frame N for the loop.
6. **Import:** in a **separate folder** with its own rule (Texture Shape = 2D Array, Columns 8, Rows 4, sRGB off, mips on, aniso 16, Repeat). The existing postprocessor caps everything under `Resources/Surfaces/Textures/` at 4096 px with CompressedHQ.
7. **Palette:** colours stay in the material, not in the frames.

Note: Figma's Motion export above 1920×1080 or 30 fps needs a paid plan. Static per-keyframe export is unaffected.

## 5. How it changes across space and with game state

Units (from the map spec):

- **Roll strip:** 0.75 m, `strip = floor(u / 0.75)` on the existing PlanarFrame `u`. Every 3 m cell line is also a strip seam (4 strips per cell).
- **Hash periods:** hashes use world-periodic indices only (`strip & 3` or `& 255`, cell `& 63`), so a 192 m root or rebase reshuffles nothing.
- **Streamed area:** `buildRadius` is 2, so 5×5 chunks are built (120 m), not 3×3.
- **Per-cell state:** a 64 × 64 toroidal state texture (1 texel per 3 m cell, 192 m period) covers the streamed area with no scrolling. A wall face reads the cell it faces: sample at `positionWS + normalWS * 0.5`.

Mechanisms, all CPU → shader globals, with an estimated cost of ~0.1–0.3 ms CPU and ~32 KB upload per frame:

- **"Changes only when unobserved"** (Exit 8 / Layers of Fear):
  - In `RenderPipelineManager.beginCameraRendering`, run a breadth-first search over see-through edges from the camera's cell, then a frustum test with `GeometryUtility.TestPlanesAABB`.
  - A cell advances a reprint only while it has been unseen for a hold time. A cell that comes into view mid-change snaps to the nearer end state before the frame renders.
  - **Fog cannot hide changes:** at density 0.014 a wall 20 m away is ~93% visible. Don't rely on `OnBecameInvisible`.
- **"When the lights flicker, the walls move"** (Haunted Mansion lightning portraits):
  - There is exactly **one troffer per cell** (LEVEL_MODULE_SPEC §4), so the state texture can carry each cell's lamp level, and the shader lets a strip slip only inside its own cell's dark window.
  - Change-blindness research (Rensink, O'Regan & Clark 1997/1999) shows changes during brief flickers are often missed. Players learn a readable rule.
  - Lamp levels are private today; this needs a read-only lamp API from the map chat.
- **Event waves:** an 8-slot global array of events, or a breadth-first search that writes arrival times so the wave travels *along the corridors* like sound. Triggers: Relay → Chase, glass broken, door blows.
  - **Rebase caveat (verifier):** in the title stream a world-space wave origin must shift with the 192 m rebase, or every wall's phase pops.
- **Relay "wake":** cells the Relay walked through get reprinted once unseen. It leaves a diegetic trace for attentive players.
- **Per-zone print run:** a zone-phase hash per cell. Discontinuities fall on cell lines, which are strip seams, and read as "a different batch".
- **Time:** never `_Time` (float, doesn't reset on reload). Accumulate a `double` clock from `Time.timeAsDouble` on the CPU, wrap it, and pass it as a global.

Transition vocabulary, modelled on print-shop failure modes to fit the 1990 era lock (avoid RGB split and pixel blocks, which read as post-1990 digital):

| Transition | Look | Timing (starting points) |
|---|---|---|
| Fibre dissolve, "ink soaking through" | new print where paper-fibre noise < p, with a thin darker wet front | 0.6–1.2 s masked or unseen; 2.5–4 s as an event |
| Strip wipe, "rehung" | per strip, top → bottom, staggered by strip, running away from the source | 0.25–0.4 s per strip, 60–120 ms stagger |
| Reprint roll | a 10–15 cm band sweeps along the wall, with smear and darkening at the band | 1.5–3 m/s |
| Strip slip (half-drop) | one strip slides half a repeat vertically | 0.3–0.8 s, or instant if unseen |
| Roller slip (period-safe glitch) | 2–8 cm horizontal slices offset for 1–3 frames | 1–3 frames |

Pacing tiers, after the Left 4 Dead AI Director's Build-Up / Peak / Relax loop:

- **Subliminal, always on:**
  - phase drift ≤ 1–2 mm/s, and scale breathing ±0.3% at 0.05–0.1 Hz;
  - 1 mm/s ≈ 0.4 px/s at 2 m, so it is felt over seconds and invisible in a still.
- **Noticeable, every 30–90 s, only unseen or lamp-masked:**
  - unseen reprints, lamp-dropout strip slips, one lagging strip, the Relay wake.
- **Event, at most one per 2–4 min:**
  - a corridor wave from the Relay at ~8 m/s (it also points at the threat), aligned with the audio stinger;
  - then subliminal-only for 30–45 s;
  - freeze everything on Caught;
  - only the subliminal tier while the player is still in the title stream rooms.

Dependencies on other chats (ask, don't edit):

- **Map chat:**
  - a read-only `LampLevel(cell)` or `FixtureChanged` event;
  - a sprint-noise event (the game calls `relay.Noise` directly today);
  - optional chunk build/drop events;
  - new logic if the Relay should kill lamps.
- **Sound chat:**
  - expose `Tension`;
  - an optional `PaperSettle` FMOD event and a `PrintPulse` global.
  - Under `AUDIO_CONTRACT.md`, the print must never touch audio files.
- **Visual chat:** owns the shader, `gen_surfaces.py`, `FrontRoomsRenderSetup`, the driver component and lookdev captures.

## 6. Design forks for Red to decide

1. **Reflective ink or glowing ink?**
   - Default: ink is albedo. It is lit by the troffers and goes dark when they die, which honours the rule.
   - Optional rare beat: a hidden *phosphorescent* print layer as emission, revealed only where lamps die. It is masked by the paper's fibre and cavity, so the paper still shades it.
   - Period-correct pigment: copper-activated zinc sulfide. Strontium aluminate dates from 1993–94, at the edge of the era lock.
   - Blacklight/DayGlo fluorescent inks (1930s–) are the other plausible 1990 diegetic frame.
2. **Ghost of the old pattern?** Remove the chevron relief completely, or keep it as a dial so the old pattern shows only at grazing or specular angles, like Gilman's sub-pattern. Suggested: off in Lobby, 0.5–0.8 in Shift.
3. **Do rolls desync?**
   - Per-roll phase with period 4 keeps the rule that every 3 m module looks the same.
   - Period 256 (192 m) breaks that rule. Visual and map owners decide.
4. **Motion style:** discrete, bistable changes with long holds (E Ink, Exit 8; recommended for Level 0), or continuous crawl (reserve for scripted beats).
5. **Accessibility (required, not optional):**
   - Add a "reduce wall motion" setting that freezes the print or limits it to slow one-way drift.
   - Keep stripe contrast reversals under 3 Hz.
   - Test the print and the existing fluorescent flicker as one combined stimulus.

## 7. Risks and validation

Risks, largest first:

1. **Moiré and shimmer.**
   - The print's dominant stripe period is ~37.5 mm (FFT peak at 20 cycles per roll). It reaches screen Nyquist ~13 m away head-on and ~6 m down a corridor at grazing angles.
   - The game uses 4× MSAA with no TAA, and MSAA does not filter texture content.
   - The live print therefore needs mips plus aniso 16 set explicitly. The editor runs Quality High (per-texture aniso), while the Standalone build defaults to Ultra (forced aniso), so they differ.
   - With `fwidth` across roll seams, compute derivatives from the continuous UV.
2. **Lighting still contains the pattern until the split in §2 lands.**
3. **Photosensitivity.** A moving stripe field on top of the existing flicker (§6.5).
4. **Precision.**
   - Wrap time on the CPU in `double`.
   - World precision depends on how far the player walks in the maze after the stream freezes, not on the map root offset. The verifier corrected the risk report: the map is moved under the player.
5. **Process.**
   - The keyword must survive RenderSetup regeneration.
   - Stream-room and Office walls need a mask so they don't read aliased map-cell state.
   - On WebGL2, Texture2DArray and render-to-texture work, but there is no compute, video is URL-only, samplers are coupled, and half may be mediump.

Prototype milestones:

| Milestone | What | Gate |
|---|---|---|
| P0 | Split paper and ink; static chevron through the new path | **T1 parity:** legacy vs split rendered in the same `Capture()` call, wall-region mean \|Δ\| ≤ 1/255 with today's N/S; art sign-off of a raking-light sheet with the new ink-free N/S |
| P0 | Lighting independence | **T2 light sweep:** one point light through 12 positions, grazing to frontal. Specular-only renders of print A vs print B must be bit-identical. Stains/grime masks must match. |
| P1 | Global Texture2DArray print and driver | **T3 grazing moiré:** a 24 m wall at 3°–30°, error ≤ 1.1× today's static texture against a 4× supersampled reference, no wagon-wheel reversal. **T4:** repeat at Quality High, at Ultra and in WebGL. |
| P2 | Transitions in the wall shader (reuse macro noise, no extra fetch) | Flash/pattern check: ≤ 3 flashes/s, no > 3 Hz stripe reversals over > 25% of the screen, including fixture flicker; dissolve fronts continuous across corners and chunk borders |
| P3 | Game-state drive (unseen, lamp mask, waves, wake) | 0 cells changed while flagged visible; same seed and inputs give an identical print timeline; events on screen within 1 frame |
| Every step | Perf gate | Autopilot seeds 2554 / 20388 plus a Level 0 corridor flythrough (those seeds start in Office). Add FrameTimingManager GPU time. Budget: average fps −1, p99 +1.5 ms, GPU median +0.5 ms, texture memory +16 MB. Baseline: 58.7 fps, p99 19.4 ms. |

Cost estimate (to be measured): about 2 extra array fetches plus ALU per wallpaper pixel. That is a few percent at most next to the 16 compare taps per shadowed light at High soft shadows.

## 8. Precedents worth putting in a research frame

All are linked in `SOURCES.md` §D. Lead with the original material, per the research rule.

- **Narrative anchor:**
  - Charlotte Perkins Gilman, *The Yellow Wallpaper* (1892). The wallpaper is literally two layers: a front pattern, and a sub-pattern in a different shade that shows only in certain lights and moves by moonlight.
  - Kane Parsons' Backrooms series links to it: episode 13 is titled with the story's ISBN, and episode 24 shows stretched wallpaper (per Wikipedia; capture clips before use).
- **Trigger precedents:**
  - Haunted Mansion (1969): portraits change during lightning flashes. This is the lamp-dropout rule.
  - Layers of Fear and Antichamber: change while unseen.
  - P.T.: change between loops.
  - The Exit 8 / Platform 8: discrete anomaly against a stable baseline.
  - Control's Ashtray Maze: synced to music (GDC 2020).
- **Lighting must not move:** Superliminal's graphics programmer says a painted-on illusion is ruined if the lighting shifts when it changes. Splatoon is the opposite case: a Nintendo ink-painting patent (Splatoon 3 era, game not named) layers paint over the stage texture, and Nintendo's recruit page says they raised ink specular. There the overlay owns its surface; here it must not.
- **Physical sandwiches:**
  - Lenticular print is the cleanest match: a static clear lens on top owns the gloss, and the image changes beneath.
  - E Ink Prism (2015) and BMW iX Flow (2022) are bistable patterns on architecture and a car body.
  - Philips/Kvadrat Luminous Textile (2011) is image behind fabric, but emissive.
  - Thermochromic wallpaper (Shi Yuan by 2008; Sibren Drenthen 2019, where the changing yarn sits on *top*, the reverse).
  - Pablo Valbuena's *Augmented Sculpture* (2007) states the physical-layer-plus-transforming-layer idea outright.
  - Verifier correction: these do not *all* put the gloss on a static top layer. Only lenticular (and electrophoretic front planes) cleanly do.
- **Film:**
  - Silent Hill (2006, BUF): fog-world walls as a skin peeled to reveal the other world.
  - A Nightmare on Elm Street (1984): Freddy through a spandex wall. This is the one case where the moving layer may push the paper's normal, as a rare scripted beat.
  - Barton Fink (1991): peeling wallpaper.
  - Not found: any pattern *animation* in A24's Backrooms (2026). Its team only fought striation on camera.
- **1990 diegetic frames:**
  - Hypercolor thermochromic clothing (1991);
  - DayGlo / blacklight inks;
  - Magic Eye (Japan 1991, US 1993): a hidden figure encoded in a repeating pattern;
  - Anaglypta / Lincrusta paintable relief papers (1887 / 1877): relief and colour are physically separate layers;
  - lenticular prints (Vari-Vue, 1953–1988).
  - Don't use E Ink or LED wallpaper in-fiction; they postdate 1993.

## 9. Next step (proposed, not started)

P0 is the decisive experiment, and it needs no motion at all. Split `wallpaper()` into paper and print, route today's chevron through the new path as a static print, and run T1 + T2. If the walls look the same and a light sweep proves the highlights don't change when the print does, the sandwich is proven. Everything after that is content and design.

All of P0 lives in the visual chat's files (`FrontRoomsSurface.shader`, `gen_surfaces.py`, `FrontRoomsRenderSetup.cs`, `FrontRoomsLookdevCapture.cs`). Either hand this document to the visual chat, or Red reassigns ownership.
