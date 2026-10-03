# Audio licenses

## Door creak

- **Asset:** Creaking Door #2
- **Source:** [BigSoundBank](https://bigsoundbank.com/grincement-de-porte-2-s3205.html)
- **Direct file:** [WAV download](https://bigsoundbank.com/UPLOAD/bwf-en/3205.wav)
- **License:** CC0 / public domain. The source page allows editing, redistribution, and commercial game use without attribution.
- **Recorded format:** indoor, realistic, mono, 48 kHz / 24-bit (imported at 44.1 kHz with preload enabled for the web and desktop prototypes).

The file is stored at `Assets/Resources/Audio/door-creak.wav`. The streamed-room controller owns one spatial audio source per reusable room and plays the recording once when that room's door changes from closed to opening. Authored keyed doors use the same clip through `FrontRooms3DGame`.

## Recorded library (Freesound)

Originals live untouched in `AudioSource/Recorded/<folder>/`; processed FMOD assets are in `AudioSource/FMOD_Library/` (`LIBRARY.json` maps every asset to its source and second). Regenerate with `python3 Tools/audio/recorded_library.py build`.

### Attribution required (ship these lines in the game credits)

- "wet_soggy_squishy_footsteps.wav" by bewagne, https://freesound.org/people/bewagne/sounds/187617/, licensed under CC-BY 3.0 (https://creativecommons.org/licenses/by/3.0/). Cut into single steps, band-limited, denoised and level-matched for FrontRooms.
- "roomtone emptymall indoors 04 160327_00.wav" by klankbeeld, https://freesound.org/people/klankbeeld/sounds/341512/, licensed under CC-BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Cut, 50 Hz mains hum notched out, filtered, looped and level-matched for FrontRooms.

### All sources

| Freesound ID | Author | Licence | Folder | Used for |
| --- | --- | --- | --- | --- |
| [148466](https://freesound.org/people/conleec/sounds/148466/) | conleec | CC0 | Footsteps | Player carpet body (walk) |
| [256209](https://freesound.org/people/hannagreen/sounds/256209/) | hannagreen | CC0 | Footsteps | Player carpet body (sneakers) |
| [560477](https://freesound.org/people/jeroberts92/sounds/560477/) | jeroberts92 | CC0 | Footsteps | Relay steps (hard sole on carpet) |
| [575318](https://freesound.org/people/taure/sounds/575318/) | taure | CC0 | Footsteps | Player carpet body (run) |
| [575321](https://freesound.org/people/taure/sounds/575321/) | taure | CC0 | Footsteps | Player carpet body (walk) |
| [187617](https://freesound.org/people/bewagne/sounds/187617/) | bewagne | CC-BY 3.0 | Wet | Waterlogged steps + moisture layer |
| [583287](https://freesound.org/people/Profispiesser/sounds/583287/) | Profispiesser | CC0 | Wet | Moisture and peel layers |
| [768656](https://freesound.org/people/Nox_Sound/sounds/768656/) | Nox_Sound | CC0 | Doors | Handle, locked rattle |
| [341176](https://freesound.org/people/klangfabrik/sounds/341176/) | klangfabrik | CC0 | Doors | Unlatch (panic bar), latch strike, slam |
| [843829](https://freesound.org/people/thaighaudio/sounds/843829/) | thaighaudio | CC0 | Doors | Swing, stops, latch |
| [160213](https://freesound.org/people/qubodup/sounds/160213/) | qubodup | CC0 | Doors | Relay blow, break |
| [454098](https://freesound.org/people/kyles/sounds/454098/) | kyles | CC0 | Fluorescent | Hum bed, fixture loop |
| [125064](https://freesound.org/people/EverydaySounds/sounds/125064/) | EverydaySounds | CC0 | Fluorescent | Fixture strike / starter buzz |
| [232447](https://freesound.org/people/mmaruska/sounds/232447/) | mmaruska | CC0 | Fluorescent | Fixture strike, tick, pop |
| [406508](https://freesound.org/people/kyles/sounds/406508/) | kyles | CC0 | RoomTone | Air bed (carpeted hallway) |
| [341512](https://freesound.org/people/klankbeeld/sounds/341512/) | klankbeeld | CC-BY 4.0 | RoomTone | Air bed (large space) |
| [376607](https://freesound.org/people/Soundkrampf/sounds/376607/) | Soundkrampf | CC0 | Glass | Window stress, crack |
| [575283](https://freesound.org/people/TRP/sounds/575283/) | TRP | CC0 | Glass | Window shatter |
| [616835](https://freesound.org/people/TRP/sounds/616835/) | TRP | CC0 | Keys | Key pickup |
| [611276](https://freesound.org/people/xkeril/sounds/611276/) | xkeril | CC0 | Cloth | Cloth layer, cloth event |

The BigSoundBank creak above (CC0) also supplies `Door/door_swing_creak_loop` and `Door/door_stop_soft_03`.

CC0 sources need no credit; they are listed for provenance. Nothing here is from the BBC Sound Effects library (non-commercial licence), the A24 film, or any game.
