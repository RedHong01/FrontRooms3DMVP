# UI sharpness pass

The title UI is rendered by a `ScreenSpaceOverlay` canvas at a 1920×1080 reference size. The previous standalone default was 1600×900, so CanvasScaler reduced the overlay to 0.833× before it was displayed. The Unity Editor Game view was also set to **Scale 2x**; that is an editor preview zoom and interpolates the captured image.

The prototype now:

- launches at 1920×1080 to match the Canvas reference resolution;
- enables 4× MSAA at runtime and in every quality tier;
- disables runtime texture mipmap limits for the authored low-resolution environment textures;
- enables Canvas pixel snapping (`pixelPerfect`);
- removes the outline halo from the flat title copy while retaining contrast outlines in the in-world HUD;
- imports the supplied brand PNG without texture compression for clean alpha edges;
- uses 16px reference copy for the title instructions so the controls remain legible at native resolution.

For a faithful editor check, set the Game view Scale to 1x. The standalone build is the stronger visual check because it uses the 1920×1080 window directly.
