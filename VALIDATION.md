# FrontRooms 3D validation

- Unity: 6000.3.10f1.
- macOS build: `Builds/Mac/FrontRooms3D.app`, build log reports `Succeeded` with `0` errors.
- Manual runtime: title screen and first-person Lobby view opened successfully on macOS. The view shows 3D walls, floor, ceiling, lighting, a readable note and minimal room/distance/crosshair HUD.
- The scripted headless route harness currently enters the player loop but does not exit reliably under `-batchmode -nographics`; those 3D route results are not claimed as passed. Manual input and human playability still need a focused run.
- Windows build is unavailable on this machine because the Unity Windows module is not installed.

## Assignment-folder Unity project import

The editable copy in the assignment folder was opened by Unity CLI with Unity 6000.3.10f1 and ran the deterministic level verifier successfully: 8 passed, 0 failed. The report is at Logs/FrontRooms/level-verification.json inside this project. This verifies project import and authored level data; it does not turn the separate headless first-person route harness into a passing runtime test.
