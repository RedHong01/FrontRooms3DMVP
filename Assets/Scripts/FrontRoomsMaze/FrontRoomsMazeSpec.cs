using System;
using System.Collections.Generic;
using UnityEngine;

namespace FrontRooms.Maze
{
    public enum MazeRoomType
    {
        Lobby,
        Standard,
        Shift,
        Office,
        Threat,
        Landmark,
        Exit,
    }

    public enum MazeConnectionKind
    {
        Hall,
        Door,
        Threshold,
        Service,
    }

    [Serializable]
    public sealed class FrontRoomsMazeCell
    {
        public int id;
        public Vector2Int coord;
        public MazeRoomType type;
        public bool isMainRoute;
        public int distanceFromStart;
        public int distanceToExit;
        public int seedRoll;
        public string read;
    }

    [Serializable]
    public sealed class FrontRoomsMazeConnection
    {
        public int id;
        public int from;
        public int to;
        public MazeConnectionKind kind;
        public bool open;
        public bool isMainRoute;
        public bool requiresKey;
        public float traversalSeconds;
    }

    [Serializable]
    public sealed class FrontRoomsMazeValidation
    {
        public bool passed;
        public int reachableCells;
        public int totalCells;
        public int mainPathLength;
        public int openConnections;
        public int loopConnections;
        public float loopRatio;
        public List<string> errors = new List<string>();
    }

    [Serializable]
    public sealed class FrontRoomsMazeSpec
    {
        public int seed;
        public int width;
        public int height;
        public float requestedLoopRatio;
        public Vector2Int start;
        public Vector2Int exit;
        public List<FrontRoomsMazeCell> cells = new List<FrontRoomsMazeCell>();
        public List<FrontRoomsMazeConnection> connections = new List<FrontRoomsMazeConnection>();
        public List<int> mainRoute = new List<int>();
        public FrontRoomsMazeValidation validation;
    }
}
