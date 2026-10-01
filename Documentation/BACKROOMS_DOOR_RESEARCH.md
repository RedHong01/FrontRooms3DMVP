# FrontRooms door research and low-cost implementation

## Visual reference

The film's readable backroom language is built from ordinary institutional or
commercial construction: yellowed wallpaper, dingy cream carpet and pale
fluorescent strips. The door is therefore treated as a functional interruption
inside the repeating wall field rather than as a black prop floating in the
opening. The film's production design used a very large practical set and many
wallpaper tests, which makes repetition, scale and small construction seams more
important than a high-resolution texture map.

- [W Magazine: the production design of A24's *Backrooms*](https://www.wmagazine.com/culture/backrooms-a24-movie-set-design-details-interview)
- [Fast Company: building the physical liminal-space set](https://www.fastcompany.com/91549406/a24-backrooms-film-production-design-liminal-space)
- [World of Interiors: wallpaper, fluorescent troffers and practical sets](https://www.worldofinteriors.com/story/the-backrooms-a24-production-design)
- [Creative Bloq: the 30,000-square-foot Blender/practical-set workflow](https://www.creativebloq.com/entertainment/movies-tv-shows/people-were-getting-lost-how-the-backrooms-director-used-blender-to-build-a-30k-square-foot-set)

The implementation is an interpretation of those references, not a claim that
the film has one canonical door asset. The useful traits for this prototype are:

1. A warm painted or laminate door face that separates from the darker carpet
   and the yellow wall without becoming a bright focal point.
2. A recessed rectangular panel, dark gasket/edge shadow, and a visible frame
   so the opening reads as a real door at a distance.
3. Small utilitarian hardware: a brushed lever plate and lever, three hinge
   knuckles, a low kick plate and a simple top closer.
4. The same construction on the reverse face, so crossing the threshold does
   not turn the door into an unmodelled dark rectangle.

## Prototype implementation

`FrontRooms3DGame` now uses a dedicated door material family (`painted
laminate`, `shadow gasket`, and `brushed hardware`) for authored gameplay doors.
`FrontRoomsRoomStream` uses the same low-poly assembly on each pooled title door.
The details are primitive cubes with colliders removed; no new texture maps or
per-frame allocations are introduced, keeping the change suitable for WebGL.

The serialized editor preview is repaired idempotently when the component is
loaded, when the editor preview is ensured, and when Play Mode rebinds the
scene. No build output is generated for this change.
