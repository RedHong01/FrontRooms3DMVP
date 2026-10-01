# Backrooms wallpaper research → low-cost prototype rule

The film reference is a material and lighting relationship, not a request to copy a
movie frame. The production team tested many paper colours and floral/chevron prints
against the carpet and the ceiling fixtures. The cinematographer describes the
Backrooms shots as lit by the visible ceiling tubes, with the wall shifted warmer to
balance the camera and skin tones. The VFX breakdown also calls out locking the
wallpaper scale while extending the practical set; the pattern is part of the space's
identity. Those observations explain why the prototype begins with beige paper and
fluorescent light rather than baking a saturated yellow texture into every wall.

Sources:

- [Jeremy Cox / ShotDeck interview](https://community.shotdeck.com/articles/an-interview-with-backrooms-cinematographer-jeremy-cox/) — visible ceiling fixtures, no extra film lights, and the yellow as a camera/white-balance decision.
- [Edward J. Douglas / Phantasmag VFX interview](https://www.phantasmag.com/articles-3/backrooms-vfx-supervisor-edward-j-douglas-interview-breakdown-kane-parsons-liminal-horror) — practical wallpaper scale, pattern shifts, and the 50-camera-test development process.
- [Wallpaper* set-design report](https://www.wallpaper.com/art/film/backrooms-film-liminal-spaces) — printed wallpaper/carpet scale and floral/chevron room variation.
- [CC0 chevron recreation](https://commons.wikimedia.org/wiki/File:Backrooms_%27Chevron%27_Wallpaper.png) — a legal pattern reference only; the prototype uses its own procedural variation and does not ship a film still.

## Prototype rule

- One shared 256×256 RGBA tile per room family, mipmapped and trilinear filtered.
- World-size UV repeat of roughly 2.25m horizontally × 2.4m vertically, applied per continuous wall slab so a wide wall does not stretch the print.
- Base colours stay desaturated (Lobby `#BDB18C`, Shift `#A8A07D`, Office `#C4B995`); the ceiling tubes supply the warm cast.
- Chevron, floral, and diamond variants are low contrast and generated once at startup. The pattern is albedo-only: no per-wall normal maps, displacement, real-time GI, or unique 4K images.
- Existing baseboards, paper seams, and door returns carry the physical construction. Far rooms reuse the same material and geometry pool.

This is deliberately a WebGL-friendly approximation: the costly part of the reference
is the camera/fixture relationship, so the prototype spends geometry and light only
on the near rooms and keeps distant repetition cheap.
