namespace FrontRooms.Audio
{
    /// <summary>
    /// FMOD event paths and parameter names. Must match SPEC in
    /// Tools/audio/fmod_frontrooms.py, which builds FMOD/FrontRooms.
    /// </summary>
    public static class SoundIds
    {
        // Ambience
        public const string HumBed = "event:/Ambience/HumBed";
        public const string AirBed = "event:/Ambience/AirBed";
        public const string Fixture = "event:/Ambience/Fixture";
        public const string FixtureEvent = "event:/Ambience/FixtureEvent";

        // Door modules
        public const string DoorHandle = "event:/Mechanism/Door/Handle";
        public const string DoorUnlatch = "event:/Mechanism/Door/Unlatch";
        public const string DoorSwing = "event:/Mechanism/Door/Swing";
        public const string DoorStopLimit = "event:/Mechanism/Door/StopLimit";
        public const string DoorStopMid = "event:/Mechanism/Door/StopMid";
        public const string DoorLatchStrike = "event:/Mechanism/Door/LatchStrike";
        public const string DoorLocked = "event:/Mechanism/Door/Locked";
        public const string DoorBlow = "event:/Mechanism/Door/Blow";
        public const string DoorBreak = "event:/Mechanism/Door/Break";
        public const string DoorAutoOperator = "event:/Mechanism/Door/AutoOperator";   // unused since Mode.Stream; A/B only
        public const string DoorStreamOpen = "event:/Mechanism/Door/StreamOpen";     // per leaf, Leaf
        public const string DoorStreamClose = "event:/Mechanism/Door/StreamClose";   // per leaf, Leaf
        public const string DoorStreamLock = "event:/Mechanism/Door/StreamLock";     // once per pair, terminal door only

        // Window
        public const string WindowStress = "event:/Mechanism/Window/Stress";
        public const string WindowCrack = "event:/Mechanism/Window/Crack";
        public const string WindowShatter = "event:/Mechanism/Window/Shatter";

        // Player
        public const string Footstep = "event:/Foley/Player/Footstep";
        public const string Cloth = "event:/Foley/Player/Cloth";
        public const string KeyPickup = "event:/Foley/Player/KeyPickup";

        // The Relay
        public const string RelayFootstep = "event:/Relay/Footstep";
        public const string RelayPresence = "event:/Relay/Presence";
        public const string RelayClicks = "event:/Relay/Clicks";
        public const string RelayStinger = "event:/Relay/Stinger";

        // Subjective
        public const string Breath = "event:/Subjective/Breath";
        public const string Heartbeat = "event:/Subjective/Heartbeat";
        public const string Tinnitus = "event:/Subjective/Tinnitus";

        // Music
        public const string MusicTitle = "event:/Music/Title";

        // Buses
        public const string BusMaster = "bus:/";
        public const string BusAmbience = "bus:/AMB";
        public const string BusSfx = "bus:/SFX";
        public const string BusMusic = "bus:/Music";
        public const string BusSubjective = "bus:/Subjective";

        public static class Param
        {
            // global
            public const string Tension = "Tension";
            public const string Zone = "Zone";             // labels: Low, Standard, Tall, Office
            public const string Tier = "Tier";
            // local
            public const string Openness = "Openness";
            public const string AngularVelocity = "AngularVelocity";
            public const string Impact = "Impact";
            public const string Damage = "Damage";
            public const string Progress = "Progress";
            public const string Level = "Level";
            public const string Stamina = "Stamina";
            public const string Proximity = "Proximity";
            public const string Occlusion = "Occlusion";
            public const string Dampness = "Dampness";     // 0 dry .. 0.4 Level 0 carpet .. >0.75 waterlogged
            public const string Surface = "Surface";       // Carpet, CarpetTile, Metal
            public const string Gait = "Gait";             // Walk, Run, Stop
            public const string RelayGait = "RelayGait";   // Walk, Run, Drag
            public const string RelayState = "RelayState"; // Hunt, Search, Chase, Lost
            public const string FixtureEvent = "FixtureEvent"; // Strike, Tick, Pop
            public const string Leaf = "Leaf";             // Lead, Follow: the two leaves of a stream double door
        }

        // Labeled parameter values are sent as their index.
        public enum Surface { Carpet = 0, CarpetTile = 1, Metal = 2 }
        public enum Gait { Walk = 0, Run = 1, Stop = 2 }
        public enum RelayGait { Walk = 0, Run = 1, Drag = 2 }
        public enum RelayState { Hunt = 0, Search = 1, Chase = 2, Lost = 3 }
        public enum FixtureKind { Strike = 0, Tick = 1, Pop = 2 }
        public enum Zone { Low = 0, Standard = 1, Tall = 2, Office = 3 }
        public enum Leaf { Lead = 0, Follow = 1 }
    }
}
