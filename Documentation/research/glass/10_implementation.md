# 10 — Glass and zone reflections: implementation (G1–G4, G6)

Date: 2026-10-02. Status: IN PROGRESS (written incrementally).

Work done only in the private clone
`/private/tmp/claude-501/-Users-redwang-Desktop-ArtCenter-Fall26T7-EGAM-401A-01-Individual-Game-Project/5656cffd-bc90-45f6-86a3-09b26549df8d/scratchpad/proj_glass`
(called **the clone** below). Nothing in `Frontrooms3D/` was changed except this folder.
The clone is shared with the G11 ray-tracing bench (`Assets/Editor/G11Bench`); every Unity run
here waited for the clone to be free.

Plan and values come from `Documentation/research/interaction_audit/10_audit_report.md` §4.1–4.3
and `Documentation/VISUAL_CHAT_TASKS.md` rows G1–G4, G6.

## Files (clone paths, relative to the project root)

| File | New / changed | What |
|---|---|---|
| `Assets/Resources/Rendering/FrontRoomsGlass.shader` | new | `FrontRooms/Glass` |
| `Assets/Resources/Rendering/FrontRoomsReflectionBlend.shader` | new | `Hidden/FrontRooms/ReflectionBlend` (cube crossfade) |
| `Assets/Scripts/Rendering/FrontRoomsZoneReflection.cs` | new | runtime zone reflection |
| `Assets/Scripts/Rendering/FrontRoomsZoneReflectionDriver.cs` | new | hidden per-frame tick |
| `Assets/Scripts/Rendering/FrontRoomsLook.cs` | changed | `SetZoneReflection` implemented; `ApplyAmbient` re-applies the zone |
| `Assets/Editor/Rendering/FrontRoomsGlassSetup.cs` | new | materials + texture importers |
| `Assets/Editor/Rendering/FrontRoomsReflectionCapture.cs` | new | cube capture in the real map |
| `Assets/Editor/Rendering/FrontRoomsGlassVerification.cs` | new | play-mode proof + look-dev frames |
| `Assets/Editor/Rendering/FrontRoomsRenderSetup.cs` | **one line** | hook after `EnsureGlassMaterials();` |
| `Tools/lookdev/pack_glass_grime.py` | new | packs the CC0 grime maps |
| `Assets/Resources/Surfaces/Textures/GlassGrime_M.png`, `GlassSmear_N.png` | new | packed grime maps |

(Results sections follow as runs finish.)
