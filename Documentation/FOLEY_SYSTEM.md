# FrontRooms Foley System

## Research decisions

The system treats Foley as an interactive composition problem rather than a single sound attached to a button.

1. **Trigger at the physical event.** A footstep is requested when movement crosses a cadence threshold; a door is requested when its latch/hinge animation begins. This keeps sound attached to what the player sees instead of to a generic timer.
2. **Resolve the surface before choosing audio.** The runtime maps the room's floor rule to a Foley surface: Lobby/Shift use carpet, Office uses tile, Run uses concrete and Exit uses metal. This is the same switch-container idea used in Wwise's official Unity demo: a material switch selects a bank, and a random container supplies variation.
3. **Compose layers.** Each step is three short layers: impact (heel/body), surface texture (carpet grit, tile ring, concrete scrape or metal resonance) and a quiet cloth/body layer. Door open is latch + hinge + door travel/settle; close and forced break have their own impact layers.
4. **Use controlled variation.** Each bank has six generated variants and the picker prevents an immediate repeat. Pitch is varied within a small range so the material identity remains stable while the rhythm avoids machine repetition.
5. **Make distance carry meaning.** All world Foley uses logarithmic 3D rolloff, actor-specific priority and a low-pass filter on the hunter. The player's soft carpet steps stay intimate; the hunter's low impact and filtered tail remain readable through walls and distance.
6. **Keep the WebGL path bounded.** The short banks are generated once at startup, not per step. The imported door recording remains a short Decompress-on-Load clip, while long ambience would be a candidate for compressed-in-memory or streaming. Unity's WebGL documentation supports Decompress-on-Load and Compressed-in-Memory for compressed audio, while Unity's Audio Profiler should be used to watch voice count, CPU and memory.
7. **Keep the carpet identity stable at thresholds.** A doorway tile is not owned by either room in the level grid, so the runtime resolves the step surface from the nearest side of the opening. The one step crossing from a yellow carpet room into Office/Run no longer silently changes to the default carpet bank.

## Runtime mapping

| Event | Selection | Layers | Spatial treatment |
| --- | --- | --- | --- |
| Player walk/run | actor + movement state + room surface | impact, surface, cloth | 3D, 18 m max distance |
| Hunter hunt/chase | hunter + movement state + room surface | heavier impact, scrape, body | 3D, 32 m max distance, 1450 Hz low-pass |
| Streamed title door | one-shot per pooled door | latch, recorded hinge, travel/settle | 3D at the door, deterministic pitch offset |
| Key/glass/outcome | existing event clips | single designed cue | existing spatial event path |

## Backrooms carpet treatment

The Backrooms Level 0 reference describes a damp carpeted labyrinth with an
obtrusive fluorescent hum. The sound direction therefore keeps carpet steps
rounded and low rather than adding a bright hard-floor click. Player steps use a
shorter, quieter fibre tail; Relay steps add a lower body transient and a
longer damp-fibre tail. Both use the same carpet surface bank, while actor
weight, cadence, pitch range and the Relay's low-pass filter separate the two
performances. This is an original procedural interpretation; no film or game
audio is bundled.

## Authoring notes

The generated banks are intentionally replaceable. To move from the prototype to recorded Foley, keep the same `FrontRoomsFoleySurface` and actor/movement keys, then replace the generated `AudioClip` arrays with imported heel/toe or shoe/surface takes. The game code does not need to change.

This pass is a functional prototype, so the carpet takes are intentionally generated from deterministic low-frequency impact, fibre release, cloth/body and small pitch variation. They are a production-safe placeholder for a later recorded supermarket-carpet session: the Relay has more sub/body, a longer damp tail and a 1450 Hz low-pass; the player stays lighter and closer. No film or game recording is bundled.

The system is implemented in `Assets/Scripts/FrontRoomsFoley.cs`. The integration points are `FrontRooms3DGame.BuildSound`, `FoleyFootstep`, `FoleyDoor` and the title stream's `BeginDoorOpening`.

## Sources

- Unity Audio Source reference: https://docs.unity.com/en-us/engine/6000.5/manual/audio/reference/class-audio-source/source-reference
- Unity Audio Mixer and snapshots: https://docs.unity3d.com/cn/6000.0/Manual/AudioMixer.html
- Unity Audio Profiler: https://docs.unity3d.com/cn/6000.0/Manual/ProfilerAudio.html
- Unity WebGL audio loading: https://docs.unity3d.com/ja/2022.3/Manual/webgl-audio.html
- Unity AudioClip load types: https://docs.unity3d.com/ja/current/ScriptReference/AudioClipLoadType.html
- Audiokinetic Wwise Project Adventure, footstep switches and heel/toe variation: https://www.audiokinetic.com/download/documents/WwiseProjectAdventure_en.pdf
- Audiokinetic Wwise Unity demo, random containers under a surface switch: https://www.audiokinetic.com/en/public-library/2024.1.8_8898/?id=pg_demoscene.html&source=Unity
- The Backrooms Wiki, Level 0: https://backrooms-wiki.wikidot.com/level-0
- Wired, Kane Parsons interview: https://www.wired.com/story/backrooms-movie-kane-parsons-interview/
- KQED, Kane Parsons interview on the fluorescent hum recordings: https://www.kqed.org/forum/2010101914649/backrooms-director-kane-parsons-on-why-san-jose-is-a-rich-setting-for-horror
