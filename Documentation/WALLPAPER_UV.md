# Wallpaper UV and material notes

The 3D prototype now treats each continuous wall slab as a physical piece of wallpaper.
`AddWallSlab` clones the room material for that slab and sets `_MainTex` scale from
its real run length and height (`paperRepeatX = 2.25m`, `paperRepeatY = 2.4m`). A
one-cell wall and a twelve-cell wall therefore show the same paper motif size rather
than stretching the same 0..1 cube UV across the entire object. The texture phase is
offset from the slab start so adjacent generated slabs keep a continuous seam rhythm.

Wallpaper and carpet procedural sources are 256x256 RGBA32 with trilinear filtering,
4x anisotropy, mipmaps, and a small negative mip bias. This keeps the woven/diamond
pattern legible in the first-person camera while still filtering cleanly at distance.
The procedural colors and room-specific palettes remain unchanged.

The generated scene stores each slab's material instance, so designers can select a
wall in `Assets/Scenes/FrontRooms3D.unity` and tune its texture scale/offset directly.

The palette now starts from a desaturated beige/grey and lets the fluorescent
fixtures create the sickly yellow cast. The shared 256px source rotates through a
low-contrast chevron, sparse floral medallion, and plain diamond variant; each
variant changes only about 5–8% of the albedo. This keeps the familiar 80% of the
room stable while giving long slabs a physical paper scale and a small readable
anomaly. The title's recycled rooms use the Lobby material, so the opening corridor
also reads as wallpaper rather than a flat yellow cube.
