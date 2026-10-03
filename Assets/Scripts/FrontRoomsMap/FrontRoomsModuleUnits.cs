namespace FrontRooms.Map
{
    /// <summary>
    /// The modular unit spec in code (Documentation/LEVEL_MODULE_SPEC.md).
    /// Every architectural piece the map builds, every prop the kits place and
    /// every room a level designer will author is measured against these
    /// numbers. Metres; Y up; a unit's front faces +Z; origin at floor centre.
    /// Changing one moves the geometry, the Relay's crossings and the kits'
    /// fit, so the map chat and the visual chat agree before any change.
    /// Plain C#, no UnityEngine, so the out-of-Unity generator check builds.
    /// </summary>
    public static class ModuleUnits
    {
        // ---------- Grid ----------

        /// <summary>One cell, one corridor wide; every wall, doorway, door and window spans one cell edge.</summary>
        public const float Cell = MapGrid.CellSize;
        /// <summary>The fine module: ceiling tiles, carpet tiles and fixture footprints. Five per cell.</summary>
        public const float Fine = .6f;
        /// <summary>World-projected tile sizes must divide this so every 3 m wall module looks the same.</summary>
        public const float TileAlign = Cell;
        /// <summary>
        /// Surface patterns are world-projected from world (0, 0): a map root,
        /// a capture root or an origin shift must sit on a multiple of this
        /// (the least common multiple of every world period: 0.6 / 1.2 ceiling,
        /// 0.75 paper, 1 carpet, 8 and 12.8 m wear, 24 m chunk), or the patterns
        /// slide against the cell lattice.
        /// </summary>
        public const float WorldPeriod = 192f;

        // ---------- Heights ----------

        public const float LowCeiling = 2.4f, StandardCeiling = 2.9f, TallCeiling = 5.4f;
        public const float FloorSlab = .2f, CeilingSlab = .16f;
        /// <summary>Clearance every prop keeps under the ceiling.</summary>
        public const float CeilingClearance = .05f;

        // ---------- Walls ----------

        /// <summary>Walls are centred on cell lines; each side loses half of this.</summary>
        public const float WallThickness = .16f;
        public const float WallHalf = WallThickness * .5f;

        /// <summary>Clear floor across <paramref name="cells"/> cells between two walls.</summary>
        public static float ClearSpan(int cells) => cells * Cell - WallThickness;

        // ---------- Openings (map-owned sizes) ----------

        /// <summary>Doorless doorway: random width, off-centre, at least <see cref="ArchCornerMargin"/> of wall each side.</summary>
        public const float ArchMinWidth = 1.1f, ArchWidthSpread = .7f, ArchMaxWidth = ArchMinWidth + ArchWidthSpread, ArchCornerMargin = .2f;
        /// <summary>Doorway top: this, or 0.2 m under a lower ceiling.</summary>
        public const float ArchTop = 2.2f, ArchHeaderMin = .2f;

        /// <summary>Door rough opening, centred on the edge. Only on Low ↔ Standard zone borders.</summary>
        public const float DoorWidth = 1f, DoorHeight = 2.1f;
        public const float DoorLeafThickness = .05f, DoorLeafGap = .02f, DoorSwingDegrees = 95f;
        /// <summary>The lock and handle: this high, this far in from the latch jamb, this far proud of the leaf face (ADA 0.86–1.22 m; FrontRoomsMapWorld.LockPoint).</summary>
        public const float DoorHandleHeight = 1f, DoorHandleInset = .08f, DoorHandleProud = .03f;

        /// <summary>Breakable glass, centred on the edge. Only on borders with a Tall zone.</summary>
        public const float WindowWidth = 1.4f, WindowSill = .35f, WindowTop = 2.0f, GlassThickness = .03f;

        /// <summary>Door and window frame: face width, and how far the jamb stands proud of each wall face.</summary>
        public const float TrimFace = .07f, TrimProud = .02f;

        // ---------- Keep-clear strips handed to the kits ----------

        /// <summary>Depth of floor kept clear inside an open, doorway or window stretch of a room's boundary.</summary>
        public const float EntryClearDepth = 1f;
        /// <summary>Depth kept clear inside a door: the leaf swings into the room.</summary>
        public const float DoorClearDepth = 1.2f;
        /// <summary>Narrowest walkable aisle a kit may leave between keep-clear strips.</summary>
        public const float MinAisle = 1f;

        // ---------- Structure and fixtures ----------

        /// <summary>Columns stand on cell corners of the world 6 m grid (every other cell line).</summary>
        public const float ColumnGrid = Cell * 2f;
        /// <summary>Square column: Level 0 rooms take the small one, Office rooms and tall halls the large one.</summary>
        public const float ColumnSmall = .6f, ColumnLarge = .9f;
        /// <summary>Office bulkhead between two columns: as wide as the column, this deep under the ceiling.</summary>
        public const float BulkheadDepth = .35f;
        /// <summary>Cove base on Office columns: height, and how far it stands proud of the column face.</summary>
        public const float CoveHeight = .1f, CoveProud = .006f;
        /// <summary>One troffer per cell: lens long and short sides, thickness, drop of its centre below the ceiling, and the lamp's drop.</summary>
        public const float TrofferLong = 1.2f, TrofferShort = .6f, TrofferLens = .025f, TrofferDrop = .02f, LampDrop = .06f;
        /// <summary>The lens (0.6 along X, 1.2 along Z) fills whole 0.6 m ceiling tiles, so its centre sits this far +Z of the cell centre.</summary>
        public const float TrofferOffsetZ = .3f;

        // ---------- Bodies ----------

        public const float PlayerRadius = .3f, PlayerHeight = 1.75f, PlayerEye = 1.62f;
        /// <summary>The Relay's collision body. It must pass a 1.0 m door and a 2.1 m door head.</summary>
        public const float RelayRadius = .3f, RelayHeight = 2.05f, RelayEye = 1.6f;
    }
}
