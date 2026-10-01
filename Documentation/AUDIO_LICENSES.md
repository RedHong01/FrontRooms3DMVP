# Audio licenses

## Door creak

- **Asset:** Creaking Door #2
- **Source:** [BigSoundBank](https://bigsoundbank.com/grincement-de-porte-2-s3205.html)
- **Direct file:** [WAV download](https://bigsoundbank.com/UPLOAD/bwf-en/3205.wav)
- **License:** CC0 / public domain. The source page allows editing, redistribution, and commercial game use without attribution.
- **Recorded format:** indoor, realistic, mono, 48 kHz / 24-bit (imported at 44.1 kHz with preload enabled for the web and desktop prototypes).

The file is stored at `Assets/Resources/Audio/door-creak.wav`. The streamed-room controller owns one spatial audio source per reusable room and plays the recording once when that room's door changes from closed to opening. Authored keyed doors use the same clip through `FrontRooms3DGame`.
