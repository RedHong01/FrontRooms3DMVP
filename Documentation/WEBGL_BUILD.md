# WebGL build profile

The reproducible browser build is exposed in Unity under **FrontRooms 3D → Build WebGL** and from batch mode:

```sh
/Applications/Unity/Hub/Editor/6000.3.10f1/Unity.app/Contents/MacOS/Unity \
  -projectPath /Users/redwang/Developer/Frontrooms3D \
  -executeMethod FrontRooms3DBuild.BuildWebGL -quit -batchmode
```

The build script applies the WebGL profile before creating `Builds/WebGL`:

- Brotli output with decompression fallback enabled. This keeps the small compressed payload while working on static hosts that do not send `Content-Encoding: br`.
- Hashed file names and browser data caching for repeat visits.
- WebAssembly 2023 / Wasm linker, high managed-code stripping, no debug symbols, and no WebGL threads. The no-threads profile works on GitHub Pages without COOP/COEP headers.
- 128 MB initial memory, 1 GB maximum, geometric growth capped at 64 MB per step. The scene is procedural and stays well below this baseline while leaving room for a longer race slice.
- Generic WebGL texture subtarget for broad desktop and mobile browser compatibility.
- 1280×720 browser canvas and the default Unity HTML template. The game remains 1920×1080 for desktop builds.

The generated output is self-contained in `Builds/WebGL/index.html`. Deploy the entire folder, preserving the `Build/` and `TemplateData/` directories. Because decompression fallback is enabled, a static server does not need custom Brotli MIME rules; if a host is configured to serve `.unityweb` with the correct `Content-Encoding` header, the fallback can be disabled later for a slightly faster first load.

The latest local verification build completed with 0 build errors and 0 warnings (`bytes=7656902`). Xcode's optional Metal inspection tool is absent on this machine; any `metal-objdump` messages come from Unity's shader inspection step and do not block WebGL output.
