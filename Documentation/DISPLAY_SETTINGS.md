# Display settings

The 3D prototype exposes a small display setting while the game is paused:

- Press `Esc` during play to pause.
- Press `O` to open **Display Settings**.
- Press `H` to switch the camera between HDR render output and SDR output.
- Press `Esc` again to close the settings panel.

The choice is stored in `PlayerPrefs` under `FrontRooms.Display.HDR` and is
restored on the next launch. The setting changes the camera's render target;
the title logo, wallpaper materials, and room stream remain the same. If the
platform does not support Unity's HDR render texture format, the camera stays
in SDR and the panel reports `HDR RENDER / OFF (SDR)`.
