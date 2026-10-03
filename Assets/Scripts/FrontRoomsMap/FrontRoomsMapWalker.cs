using FrontRooms.Map;
using UnityEngine;

/// <summary>
/// First-person walker for the map test scene: WASD and mouse, Shift to
/// sprint on about 5 s of stamina, E to open or shut doors, hold E to break
/// glass. Draws a small debug HUD with the zone, cell, chunk, seed, keys and
/// how many chunks have come back shifted.
/// </summary>
[RequireComponent(typeof(CharacterController))]
public sealed class FrontRoomsMapWalker : MonoBehaviour
{
    const float Walk = 3.2f, Sprint = 5.5f;
    const float StaminaSeconds = 5f, RecoverDelay = 1f, RecoverRate = 1f;
    const float EyeHeight = 1.62f, Reach = 2.4f, LookSpeed = 2f;
    static readonly Color Paper = new Color(.957f, .945f, .91f);
    static readonly Color Muted = new Color(.74f, .73f, .69f);
    static readonly Color Accent = new Color(.957f, .875f, .231f);

    FrontRoomsMapWorld world;
    CharacterController body;
    Camera view;
    float yaw, pitch, fallSpeed, sinceSprint;
    float stamina = StaminaSeconds;
    Collider aimed;
    string prompt;
    bool holdPrompt;
    float holdProgress;
    string flash;
    float flashUntil;
    GUIStyle large, meta, center;

    /// <summary>Move the walker at once (the Level Designer's live rebuild): the controller is off while it moves, and the look resets to the heading.</summary>
    public void Teleport(Vector3 position, float newYaw)
    {
        body.enabled = false;
        transform.SetPositionAndRotation(position, Quaternion.Euler(0f, newYaw, 0f));
        yaw = newYaw;
        pitch = 0f;
        fallSpeed = 0f;
        if (view != null) view.transform.localRotation = Quaternion.identity;
        body.enabled = true;
    }

    /// <summary>Follow the map's build radius after a live profile change: the far plane stops just short of what may not be built.</summary>
    public void RefreshView()
    {
        if (view != null && world != null) view.farClipPlane = world.SightDistance;
    }

    public static FrontRoomsMapWalker Spawn(FrontRoomsMapWorld world, Vector3 position, float yaw = 0f)
    {
        var go = new GameObject("Map test player");
        go.transform.position = position;
        go.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
        var body = go.AddComponent<CharacterController>();
        body.height = 1.75f;
        body.radius = .3f;
        body.center = new Vector3(0f, .875f, 0f);
        body.stepOffset = .3f;
        body.skinWidth = .03f;

        var cameraObject = new GameObject("Map test camera");
        cameraObject.transform.SetParent(go.transform, false);
        cameraObject.transform.localPosition = new Vector3(0f, EyeHeight, 0f);
        cameraObject.tag = "MainCamera";
        var view = cameraObject.AddComponent<Camera>();
        view.fieldOfView = 72f;
        view.nearClipPlane = .05f;
        view.farClipPlane = world.SightDistance;
        view.clearFlags = CameraClearFlags.SolidColor;
        view.backgroundColor = world.FogColor;
        cameraObject.AddComponent<AudioListener>();

        var walker = go.AddComponent<FrontRoomsMapWalker>();
        walker.yaw = yaw;
        walker.world = world;
        walker.body = body;
        walker.view = view;
        return walker;
    }

    void Update()
    {
        var dt = Time.deltaTime;
        if (Input.GetMouseButtonDown(0) && Cursor.lockState != CursorLockMode.Locked)
        {
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
        }
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }
        if (Cursor.lockState == CursorLockMode.Locked)
        {
            yaw += Input.GetAxisRaw("Mouse X") * LookSpeed;
            pitch = Mathf.Clamp(pitch - Input.GetAxisRaw("Mouse Y") * LookSpeed, -80f, 80f);
        }
        transform.rotation = Quaternion.Euler(0f, yaw, 0f);
        view.transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);

        var h = (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow) ? 1f : 0f) - (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow) ? 1f : 0f);
        var v = (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow) ? 1f : 0f) - (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow) ? 1f : 0f);
        var wish = transform.right * h + transform.forward * v;
        if (wish.sqrMagnitude > 1f) wish.Normalize();
        var sprinting = (Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift)) && wish.sqrMagnitude > .01f && stamina > 0f;
        if (sprinting)
        {
            stamina = Mathf.Max(0f, stamina - dt);
            sinceSprint = 0f;
        }
        else
        {
            sinceSprint += dt;
            if (sinceSprint > RecoverDelay) stamina = Mathf.Min(StaminaSeconds, stamina + RecoverRate * dt);
        }
        fallSpeed = body.isGrounded ? -1f : fallSpeed - 9.81f * dt;
        body.Move((wish * (sprinting ? Sprint : Walk) + Vector3.up * fallSpeed) * dt);

        Aim(dt);
    }

    void Aim(float dt)
    {
        var previous = aimed;
        aimed = null;
        prompt = null;
        holdPrompt = false;
        var ray = new Ray(view.transform.position, view.transform.forward);
        if (Physics.Raycast(ray, out var hit, Reach, ~0, QueryTriggerInteraction.Ignore))
        {
            prompt = world.Describe(hit.collider, out holdPrompt);
            if (prompt != null) aimed = hit.collider;
        }
        if (previous != null && previous != aimed) world.ReleaseHold(previous);
        if (aimed == null) { holdProgress = 0f; return; }
        if (!holdPrompt)
        {
            holdProgress = 0f;
            if (Input.GetKeyDown(KeyCode.E)) world.Use(aimed);
            return;
        }
        if (Input.GetKey(KeyCode.E))
        {
            if (world.Hold(aimed, dt, out holdProgress))
            {
                Flash("GLASS BROKEN  ·  LOUDEST NOISE");
                aimed = null;
                holdProgress = 0f;
            }
        }
        else
        {
            world.ReleaseHold(aimed);
            holdProgress = 0f;
        }
    }

    void Flash(string message)
    {
        flash = message;
        flashUntil = Time.time + 2.5f;
    }

    void OnGUI()
    {
        if (large == null)
        {
            large = new GUIStyle(GUI.skin.label) { fontSize = 30, fontStyle = FontStyle.Bold };
            meta = new GUIStyle(GUI.skin.label) { fontSize = 12 };
            center = new GUIStyle(GUI.skin.label) { fontSize = 16, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
        }
        var cell = world.CellOf(transform.position);
        var zone = world.Cache.ZoneOf(cell);
        var chunk = MapGrid.ChunkOf(cell);

        Rect(new Rect(24f, 24f, 4f, 52f), Accent);
        Text(new Rect(40f, 18f, 900f, 40f), "LEVEL 0  /  " + zone.height.ToString().ToUpperInvariant() + " ZONE", large, Paper);
        Text(new Rect(40f, 56f, 1200f, 20f), "ZONE " + zone.id + "  ·  CEILING " + MapGrid.CeilingHeight(zone.height).ToString("0.0") + " M  ·  CELL " + cell
            + "  ·  CHUNK " + chunk + "  ·  SEED " + world.Seed + "  ·  SHIFTED CHUNKS " + world.ShiftedChunks + "  ·  KEYS " + world.KeysHeld, meta, Muted);

        var cx = Screen.width * .5f;
        var cy = Screen.height * .5f;
        Rect(new Rect(cx - 2f, cy - 2f, 4f, 4f), Accent);
        if (prompt != null) Text(new Rect(cx - 300f, cy + 26f, 600f, 24f), prompt, center, Paper);
        if (holdProgress > 0f)
        {
            Rect(new Rect(cx - 60f, cy + 54f, 120f, 4f), new Color(1f, 1f, 1f, .25f));
            Rect(new Rect(cx - 60f, cy + 54f, 120f * holdProgress, 4f), Accent);
        }
        if (stamina < StaminaSeconds - .01f)
        {
            for (var i = 0; i < 5; i++)
            {
                var filled = stamina >= (i + .5f) * (StaminaSeconds / 5f);
                Rect(new Rect(cx - 72f + i * 30f, cy + 90f, 24f, 6f), filled ? Accent : new Color(1f, 1f, 1f, .25f));
            }
        }
        if (flash != null && Time.time < flashUntil) Text(new Rect(cx - 300f, cy + 110f, 600f, 24f), flash, center, Accent);
        Text(new Rect(24f, Screen.height - 34f, 1000f, 20f), "CLICK TO LOOK  ·  WASD MOVE  ·  SHIFT SPRINT  ·  E DOOR  ·  HOLD E GLASS  ·  ESC CURSOR", meta, Muted);
    }

    static void Rect(Rect r, Color c)
    {
        var old = GUI.color;
        GUI.color = c;
        GUI.DrawTexture(r, Texture2D.whiteTexture);
        GUI.color = old;
    }

    static void Text(Rect r, string text, GUIStyle style, Color c)
    {
        var old = GUI.color;
        GUI.color = c;
        GUI.Label(r, text, style);
        GUI.color = old;
    }
}
