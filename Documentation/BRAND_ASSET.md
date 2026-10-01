# FrontRooms brand mark

`Assets/Brand/FrontRoomsLogo.svg` remains the supplied editable source artwork. Unity 6.3 imports it as a native `VectorImage`; the runtime title loads `FrontRoomsLogo_Left.svg`, `FrontRoomsLogo_S1.svg`, and `FrontRoomsLogo_S2.svg` through a UI Toolkit overlay. The first asset contains the complete wordmark, including its solid final S. The other two contain only the transparent afterimage S paths, so they can start on top of that solid S and slide out without cutting the logo tail. The source SVG stays sharp at 1280px WebGL and 4K macOS windows.

`Assets/Resources/Brand/FrontRoomsLogo.png` remains as a fallback for older Unity versions or platforms without the Vector Graphics module. It is not the normal title path. The generated white SVG replaces the original black fill while preserving the supplied transparent afterimage gradients, and the title keeps the `SlideThenFade` / `FullLockup` motion variation.
