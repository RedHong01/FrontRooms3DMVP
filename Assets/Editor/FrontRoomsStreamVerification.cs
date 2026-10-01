using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Headless checks of the room stream and the Relay. They drive the real
/// FrontRoomsRoomStream and FrontRoomsHunterBrain with a simulated player at a
/// fixed 60 Hz step; they do not claim rendering, audio or human playtest.
/// Run with -executeMethod FrontRoomsStreamVerification.Run; failures throw after the JSON report is saved.
/// </summary>
public static class FrontRoomsStreamVerification
{
    const float Dt = 1f / 60f;
    const float Walk = 3.2f, Sprint = 5.5f;

    [Serializable]
    sealed class CheckResult
    {
        public string name;
        public bool passed;
        public string detail;
    }

    [Serializable]
    sealed class VerificationReport
    {
        public string suite = "FrontRooms room stream and Relay";
        public string timestampUtc;
        public string unityVersion;
        public string scope = "Room pool, profile order and Relay state machine with a scripted player. Rendering, audio and human playability are separate.";
        public int passed;
        public int failed;
        public List<CheckResult> checks = new List<CheckResult>();
    }

    sealed class Sim : IDisposable
    {
        readonly GameObject root;
        readonly Camera camera;
        readonly Material material;
        public readonly FrontRoomsRoomStream stream;
        public readonly FrontRoomsHunterTuning tuning = new FrontRoomsHunterTuning();
        public FrontRoomsHunterBrain brain;
        public float sinceHandoff;
        public int startRoom;
        public float caughtAt = -1f;
        public float releasedAt = -1f;
        public int releasedPlayerRoom;
        public bool seenAtRelease;
        public int alarms;
        float sprintStep;

        public Sim()
        {
            root = new GameObject("VERIFY / room stream") { hideFlags = HideFlags.HideAndDontSave };
            camera = new GameObject("VERIFY / camera").AddComponent<Camera>();
            camera.gameObject.hideFlags = HideFlags.HideAndDontSave;
            camera.transform.position = new Vector3(FrontRooms3DGame.TitleCenterX, 1.62f, 0f);
            material = new Material(Shader.Find("Standard"));
            var profiles = new[] { material, material, material, material, material };
            stream = root.AddComponent<FrontRoomsRoomStream>();
            stream.Initialize(camera, material, material, material, material, material, material, null, null, null, profiles, profiles, profiles);
        }

        public Vector2 Player => new Vector2(camera.transform.position.x, camera.transform.position.z);
        public int Room => stream.CurrentRoomNumber;

        public void Title(float seconds)
        {
            for (var t = 0f; t < seconds; t += Dt) stream.Tick(Dt);
        }

        public bool Handoff()
        {
            stream.RequestStart();
            for (var t = 0f; t < 15f && !stream.HasControl; t += Dt) stream.Tick(Dt);
            if (!stream.HasControl) return false;
            stream.BeginPlayableSequence();
            startRoom = Room;
            brain = new FrontRoomsHunterBrain(stream, tuning);
            brain.Caught += () => caughtAt = sinceHandoff;
            brain.Alarmed += room => alarms++;
            brain.StateChanged += state =>
            {
                if (releasedAt >= 0f || state == HunterState.Dormant) return;
                releasedAt = sinceHandoff;
                releasedPlayerRoom = Room;
            };
            return true;
        }

        /// <summary>One frame in the same order as FrontRooms3DGame: stream, player, Relay.</summary>
        public void Step(float speed)
        {
            stream.Tick(Dt);
            if (speed > 0f) stream.Move(new Vector2(0f, speed * Dt));
            if (speed >= Sprint)
            {
                sprintStep += Dt;
                if (sprintStep > .3f)
                {
                    sprintStep = 0f;
                    brain.Noise(Player, tuning.sprintNoiseRadius);
                }
            }
            var wasReleased = brain.Released;
            brain.Tick(Dt, Player);
            if (!wasReleased && brain.Released) seenAtRelease = brain.SeesPlayer;
            sinceHandoff += Dt;
        }

        public void Dispose()
        {
            UnityEngine.Object.DestroyImmediate(root);
            UnityEngine.Object.DestroyImmediate(camera.gameObject);
            UnityEngine.Object.DestroyImmediate(material);
        }
    }

    [MenuItem("FrontRooms 3D/Verify room stream")]
    public static void Run()
    {
        var report = new VerificationReport
        {
            timestampUtc = DateTime.UtcNow.ToString("o"),
            unityVersion = Application.unityVersion,
        };
        Check(report, "Handoff keeps every visible room and leads with empty Lobby rooms", VerifyHandoff);
        Check(report, "Two dressed rooms always wait ahead and no loaded room changes profile", VerifyPreparedRooms);
        Check(report, "A walking player is hunted but not caught; the Relay is released out of sight", VerifyWalkingRun);
        Check(report, "A player who stops after the release is caught", VerifyStandingStill);
        Check(report, "A sprinting player escapes", VerifySprintingRun);

        var output = Path.GetFullPath("Verification/stream-verification-latest.json");
        Directory.CreateDirectory(Path.GetDirectoryName(output));
        File.WriteAllText(output, JsonUtility.ToJson(report, true));
        Debug.Log(string.Format("[FrontRoomsStreamVerification] {0} passed, {1} failed. {2}", report.passed, report.failed, output));
        if (report.failed != 0)
            throw new InvalidOperationException("FrontRooms room stream verification failed; inspect " + output);
    }

    static void Check(VerificationReport report, string name, Func<string> verify)
    {
        var result = new CheckResult { name = name };
        try
        {
            result.detail = verify();
            result.passed = true;
            report.passed++;
        }
        catch (Exception exception)
        {
            result.detail = exception.Message;
            report.failed++;
        }
        report.checks.Add(result);
    }

    static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    static string VerifyHandoff()
    {
        using (var sim = new Sim())
        {
            // A long title crawl, so the handoff happens deep into the stream.
            sim.Title(20f);
            var before = new Dictionary<int, RoomRule>();
            for (var room = sim.Room - 3; room <= sim.Room + 4; room++)
                if (sim.stream.IsLoaded(room)) before[room] = sim.stream.RuleAt(room);
            Require(sim.Handoff(), "camera never reached the handoff anchor");
            foreach (var pair in before)
                if (pair.Key <= sim.startRoom || sim.stream.IsDoorPassable(pair.Key - 1))
                    Require(sim.stream.RuleAt(pair.Key) == pair.Value, "visible room " + pair.Key + " changed profile at the handoff");
            var expected = new[] { RoomRule.Lobby, RoomRule.Lobby, RoomRule.Lobby, RoomRule.Shift, RoomRule.Office, RoomRule.Run, RoomRule.Exit, RoomRule.Lobby, RoomRule.Shift };
            for (var i = 0; i < expected.Length; i++)
                Require(sim.stream.RuleAt(sim.startRoom + i) == expected[i], "room +" + i + " is " + sim.stream.RuleAt(sim.startRoom + i) + ", expected " + expected[i]);
            return "handoff room " + sim.startRoom + "; first furnished room +" + (sim.stream.FirstProfileSequence - sim.startRoom) + "; cycle Shift, Office, Run, Exit, Lobby";
        }
    }

    static string VerifyPreparedRooms()
    {
        using (var sim = new Sim())
        {
            sim.Title(3f);
            Require(sim.Handoff(), "camera never reached the handoff anchor");
            var seen = new Dictionary<int, RoomRule>();
            var minimumAhead = int.MaxValue;
            for (var frame = 0; frame < 60 * 90; frame++)
            {
                sim.Step(Walk);
                var ahead = 0;
                while (sim.stream.IsLoaded(sim.Room + ahead + 1)) ahead++;
                minimumAhead = Mathf.Min(minimumAhead, ahead);
                Require(ahead >= 2, "only " + ahead + " room(s) loaded ahead of room " + sim.Room + " at " + sim.sinceHandoff.ToString("0.00") + " s");
                for (var room = sim.Room - 2; room <= sim.Room + 3; room++)
                {
                    if (!sim.stream.IsLoaded(room)) { seen.Remove(room); continue; }
                    var rule = sim.stream.RuleAt(room);
                    if (seen.TryGetValue(room, out var previous))
                        Require(previous == rule, "room " + room + " changed from " + previous + " to " + rule + " while loaded");
                    seen[room] = rule;
                }
            }
            Require(sim.stream.RecycledCount > 10, "the pool barely recycled (" + sim.stream.RecycledCount + ")");
            return "walked " + (sim.Room - sim.startRoom) + " rooms; at least " + minimumAhead + " rooms ready ahead every frame; " + sim.stream.RecycledCount + " recycles";
        }
    }

    static string VerifyWalkingRun()
    {
        using (var sim = new Sim())
        {
            sim.Title(3f);
            Require(sim.Handoff(), "camera never reached the handoff anchor");
            var closest = float.MaxValue;
            var rebases = sim.stream.RebaseCount;
            var lastDistance = -1f;
            for (var frame = 0; frame < 60 * 150 && sim.caughtAt < 0f; frame++)
            {
                sim.Step(Walk);
                if (!sim.brain.Released) continue;
                var distance = Vector2.Distance(sim.Player, sim.brain.Position);
                if (sim.stream.RebaseCount != rebases && lastDistance >= 0f)
                    Require(Mathf.Abs(distance - lastDistance) < 1f, "the Relay jumped " + Mathf.Abs(distance - lastDistance).ToString("0.0") + " m when the stream rebased");
                rebases = sim.stream.RebaseCount;
                lastDistance = distance;
                closest = Mathf.Min(closest, distance);
            }
            Require(sim.releasedAt >= 0f, "the Relay was never released");
            Require(sim.releasedPlayerRoom >= sim.stream.FirstProfileSequence, "released in room " + sim.releasedPlayerRoom + ", before the first furnished room " + sim.stream.FirstProfileSequence);
            Require(!sim.seenAtRelease, "the Relay could see the player the moment it appeared");
            Require(sim.caughtAt < 0f, "a walking player was caught at " + sim.caughtAt.ToString("0.0") + " s");
            Require(sim.alarms > 0, "no Run room alarm fired");
            Require(sim.brain.DoorsBroken > 0, "the Run alarm never put the Relay on the door behind the player");
            Require(sim.stream.RebaseCount > 0, "the walk never crossed a floating-origin rebase");
            return "released " + sim.releasedAt.ToString("0.0") + " s after the handoff in room +" + (sim.releasedPlayerRoom - sim.startRoom)
                + "; closest " + closest.ToString("0.0") + " m; " + sim.brain.DoorsBroken + " doors broken; " + sim.alarms + " Run alarms; "
                + sim.stream.RebaseCount + " rebases; final state " + sim.brain.State;
        }
    }

    static string VerifyStandingStill()
    {
        using (var sim = new Sim())
        {
            sim.Title(3f);
            Require(sim.Handoff(), "camera never reached the handoff anchor");
            for (var frame = 0; frame < 60 * 60 && !sim.brain.Released; frame++) sim.Step(Walk);
            Require(sim.brain.Released, "the Relay was never released");
            var stoppedAt = sim.sinceHandoff;
            for (var frame = 0; frame < 60 * 120 && sim.caughtAt < 0f; frame++) sim.Step(0f);
            Require(sim.caughtAt >= 0f, "the Relay never reached a player standing still for 120 s");
            return "stopped " + stoppedAt.ToString("0.0") + " s after the handoff; caught " + (sim.caughtAt - stoppedAt).ToString("0.0") + " s later after " + sim.brain.DoorsBroken + " door breaks";
        }
    }

    static string VerifySprintingRun()
    {
        using (var sim = new Sim())
        {
            sim.Title(3f);
            Require(sim.Handoff(), "camera never reached the handoff anchor");
            for (var frame = 0; frame < 60 * 120 && sim.caughtAt < 0f; frame++) sim.Step(Sprint);
            Require(sim.caughtAt < 0f, "a sprinting player was caught at " + sim.caughtAt.ToString("0.0") + " s");
            return "sprinted " + (sim.Room - sim.startRoom) + " rooms in 120 s; Relay state " + sim.brain.State + "; " + sim.brain.Relays + " relays";
        }
    }
}
