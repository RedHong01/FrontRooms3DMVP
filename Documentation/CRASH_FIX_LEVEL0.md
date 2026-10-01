# FrontRooms3D player crash fix

The macOS crash report was an `EXC_BREAKPOINT` in `UnityPlayer.dylib` during scene load. The accompanying Unity player log identified the first failure as:

```
The file .../Data/level0 is corrupted! Remove it and launch unity again!
[Position out of bounds!]
```

The scene had serialized `FrontRoomsLightFlicker` components as an inline `MonoScript` file ID (`1086799587`). Unity 6000.3.10f1 could resolve that reference in the editor but reported the component as `Unknown` while building/loading the player. Every room light now points to the standalone script asset `FrontRoomsLightFlicker.cs` by GUID `ee0730b92d38497980eb0eb7bc9ead4e`.

Validation:

- 8/8 editor verification checks passed.
- macOS build completed with 0 errors.
- Null graphics player reached `READY` without corruption or missing-script output.
- Metal player on Apple M3 Max reached `READY` without corruption or missing-script output.
