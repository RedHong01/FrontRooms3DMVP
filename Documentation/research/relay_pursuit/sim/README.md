# Relay pursuit: measurement and diagram sources

The numbers and diagrams behind `Documentation/RELAY_PURSUIT_REDESIGN.md` and the Figma section RP01–RP10 (2441:3804).

- `mapgen.py`: Python port of the `FrontRoomsMap.cs` edge rules (zones, DFS tree, rooms, borders). Modules, columns and keys are left out. Written by the title-handoff chat and checked here against `Resolve`.
- `hearing_stats.py`: today's straight-line sprint hearing (36.4 m): cells covered, walking distance to them, and the share of spawn cells in earshot (366 positions).
- `new_hearing.py`: proposed path-propagated hearing (3 m per cell, shut door +9 m, window +9 m, walls block), in cells.
- `region_pick.py`: picks the example region (seed 1032392419, cell 78,−20).
- `figdata.py`: diagram data. It reads autopilot `report.json` files from session scratchpads, which may be gone later; `figdata.json` is the snapshot used.
- `mksvg_*.py` → `svg/`: the diagrams imported into Figma as vectors.

Run with `python3` from this folder. The scripts are slow (several minutes); run them in the background.
