using UnityEngine;

/// <summary>
/// Editable prototype rig for The Relay. The mesh is deliberately assembled
/// from a small number of primitives so the creature remains cheap in WebGL,
/// while the hierarchy exposes real bone transforms for authoring and later
/// replacement with a skinned FBX.
/// </summary>
[ExecuteAlways]
public sealed class FrontRoomsRelayRig : MonoBehaviour
{
    public enum MotionState
    {
        IdleListen,
        Walk,
        Run,
        BreakDoor,
        Stagger
    }

    [Header("Materials")]
    [SerializeField] Material bodyMaterial;
    [SerializeField] Material headMaterial;
    [SerializeField] Material detailMaterial;

    [Header("Authoring bones")]
    [SerializeField] Transform rootBone;
    [SerializeField] Transform pelvis;
    [SerializeField] Transform spine;
    [SerializeField] Transform chest;
    [SerializeField] Transform neck;
    [SerializeField] Transform head;
    [SerializeField] Transform armL;
    [SerializeField] Transform forearmL;
    [SerializeField] Transform handL;
    [SerializeField] Transform armR;
    [SerializeField] Transform forearmR;
    [SerializeField] Transform handR;
    [SerializeField] Transform thighL;
    [SerializeField] Transform shinL;
    [SerializeField] Transform footL;
    [SerializeField] Transform thighR;
    [SerializeField] Transform shinR;
    [SerializeField] Transform footR;

    [Header("Motion")]
    [SerializeField] MotionState previewState = MotionState.IdleListen;
    [SerializeField, Range(.4f, 2.5f)] float previewSpeed = 1f;
    [SerializeField, Range(.1f, 1f)] float bodyScale = 1f;

    float animationTime;
    MotionState currentState;
    bool generated;

    public Transform Body => chest;
    public Transform Head => head;
    public Transform ArmLeft => armL;
    public Transform ArmRight => armR;
    public Transform LegLeft => thighL;
    public Transform LegRight => thighR;
    public MotionState State => currentState;

    void OnEnable()
    {
        EnsureRig();
        if (!Application.isPlaying) TickAnimation(0f, previewState, true, previewSpeed);
    }

    void Update()
    {
        if (!Application.isPlaying)
        {
            EnsureRig();
            TickAnimation(Time.deltaTime, previewState, true, previewSpeed);
        }
    }

    /// <summary>Assign materials from the authored FrontRooms palette.</summary>
    public void Configure(Material body, Material headMaterialOverride, Material detail)
    {
        bodyMaterial = body;
        headMaterial = headMaterialOverride;
        detailMaterial = detail;
        EnsureRig();
        ApplyMaterials();
    }

    public void EnsureRig()
    {
        if (rootBone != null && rootBone.IsChildOf(transform))
        {
            generated = true;
            ApplyMaterials();
            return;
        }
        BuildRig();
    }

    /// <summary>
    /// Drives the rig from the encounter state machine. No Animator component
    /// or per-frame allocations are required; replacing the visual children
    /// with a skinned mesh later does not change the state contract.
    /// </summary>
    public void TickAnimation(float deltaTime, MotionState state, bool moving, float speedScale)
    {
        EnsureRig();
        currentState = state;
        animationTime += Mathf.Max(0f, deltaTime) * Mathf.Max(.1f, speedScale);
        var gaitRate = state == MotionState.Run ? 11.5f : state == MotionState.Walk ? 7.2f : 2.1f;
        var gait = moving ? Mathf.Sin(animationTime * gaitRate) : Mathf.Sin(animationTime * 2.1f) * .08f;
        var opposite = moving ? Mathf.Sin(animationTime * gaitRate + Mathf.PI) : -gait;
        var stride = state == MotionState.Run ? 34f : state == MotionState.Walk ? 22f : 6f;
        var armSwing = state == MotionState.Run ? 30f : state == MotionState.Walk ? 20f : 5f;
        var crouch = state == MotionState.Run ? .08f : state == MotionState.BreakDoor ? .13f : 0f;

        if (pelvis != null)
        {
            pelvis.localPosition = new Vector3(0f, .92f - crouch + Mathf.Abs(gait) * (moving ? .025f : .01f), 0f);
            pelvis.localRotation = Quaternion.Euler(0f, 0f, gait * (moving ? 2.5f : 1.2f));
        }
        if (spine != null) spine.localRotation = Quaternion.Euler(-9f - crouch * 22f, 0f, gait * 1.8f);
        if (chest != null) chest.localRotation = Quaternion.Euler(-4f - crouch * 18f, 0f, -gait * 1.5f);
        if (neck != null) neck.localRotation = Quaternion.Euler(0f, Mathf.Sin(animationTime * 1.8f) * (state == MotionState.IdleListen ? 7f : 2.5f), 0f);
        if (head != null) head.localRotation = Quaternion.Euler(state == MotionState.BreakDoor ? -8f : 0f, Mathf.Sin(animationTime * 1.65f) * (state == MotionState.IdleListen ? 9f : 3f), 0f);

        if (armL != null) armL.localRotation = Quaternion.Euler(gait * armSwing, 0f, -7f);
        if (armR != null) armR.localRotation = Quaternion.Euler(opposite * armSwing, 0f, 7f);
        if (forearmL != null) forearmL.localRotation = Quaternion.Euler(state == MotionState.BreakDoor ? -42f : 12f + opposite * 8f, 0f, 0f);
        if (forearmR != null) forearmR.localRotation = Quaternion.Euler(state == MotionState.BreakDoor ? -42f : 12f + gait * 8f, 0f, 0f);
        if (handL != null) handL.localRotation = Quaternion.Euler(state == MotionState.BreakDoor ? -12f : 0f, 0f, 0f);
        if (handR != null) handR.localRotation = Quaternion.Euler(state == MotionState.BreakDoor ? -12f : 0f, 0f, 0f);

        if (thighL != null) thighL.localRotation = Quaternion.Euler(opposite * stride, 0f, 0f);
        if (thighR != null) thighR.localRotation = Quaternion.Euler(gait * stride, 0f, 0f);
        if (shinL != null) shinL.localRotation = Quaternion.Euler(Mathf.Max(0f, -opposite) * stride * .7f, 0f, 0f);
        if (shinR != null) shinR.localRotation = Quaternion.Euler(Mathf.Max(0f, -gait) * stride * .7f, 0f, 0f);
        if (footL != null) footL.localRotation = Quaternion.Euler(-Mathf.Max(0f, opposite) * 10f, 0f, 0f);
        if (footR != null) footR.localRotation = Quaternion.Euler(-Mathf.Max(0f, gait) * 10f, 0f, 0f);

        if (state == MotionState.Stagger && rootBone != null)
            rootBone.localRotation = Quaternion.Euler(0f, Mathf.Sin(animationTime * 16f) * 4f, Mathf.Sin(animationTime * 13f) * 3f);
        else if (rootBone != null)
            rootBone.localRotation = Quaternion.identity;
    }

    void BuildRig()
    {
        var rigRoot = new GameObject("RELAY RIG / bones").transform;
        rigRoot.SetParent(transform, false);
        rigRoot.localPosition = Vector3.zero;
        rootBone = rigRoot;

        pelvis = Bone("pelvis", rootBone, new Vector3(0f, .92f, 0f));
        spine = Bone("spine", pelvis, new Vector3(0f, .55f, 0f));
        chest = Bone("chest", spine, new Vector3(0f, .42f, 0f));
        neck = Bone("neck", chest, new Vector3(0f, .62f, 0f));
        head = Bone("head", neck, new Vector3(0f, .22f, .02f));

        armL = Bone("upper arm L", chest, new Vector3(-.40f, .35f, 0f));
        forearmL = Bone("forearm L", armL, new Vector3(-.38f, -.04f, .02f));
        handL = Bone("hand L", forearmL, new Vector3(-.34f, -.04f, .04f));
        armR = Bone("upper arm R", chest, new Vector3(.40f, .35f, 0f));
        forearmR = Bone("forearm R", armR, new Vector3(.38f, -.04f, .02f));
        handR = Bone("hand R", forearmR, new Vector3(.34f, -.04f, .04f));

        thighL = Bone("thigh L", pelvis, new Vector3(-.19f, -.55f, 0f));
        shinL = Bone("shin L", thighL, new Vector3(0f, -.60f, .02f));
        footL = Bone("foot L", shinL, new Vector3(0f, -.56f, .12f));
        thighR = Bone("thigh R", pelvis, new Vector3(.19f, -.55f, 0f));
        shinR = Bone("shin R", thighR, new Vector3(0f, -.60f, .02f));
        footR = Bone("foot R", shinR, new Vector3(0f, -.56f, .12f));

        Visual(PrimitiveType.Capsule, "body / hunched", chest, Vector3.zero, new Vector3(.68f, .78f, .53f), bodyMaterial);
        Visual(PrimitiveType.Cube, "shoulder asymmetry", chest, new Vector3(-.08f, .27f, -.03f), new Vector3(1.02f, .16f, .52f), bodyMaterial);
        Visual(PrimitiveType.Sphere, "blank head", head, Vector3.zero, new Vector3(.58f, .70f, .52f), headMaterial);
        Visual(PrimitiveType.Cube, "face void", head, new Vector3(0f, .02f, .255f), new Vector3(.37f, .08f, .018f), detailMaterial);
        Visual(PrimitiveType.Capsule, "arm upper L", armL, new Vector3(-.18f, -.12f, 0f), new Vector3(.20f, .46f, .20f), bodyMaterial);
        Visual(PrimitiveType.Capsule, "arm fore L", forearmL, new Vector3(-.15f, -.13f, .02f), new Vector3(.16f, .42f, .16f), bodyMaterial);
        Visual(PrimitiveType.Cube, "hand L", handL, new Vector3(-.06f, -.10f, .05f), new Vector3(.22f, .18f, .18f), detailMaterial);
        Visual(PrimitiveType.Capsule, "arm upper R", armR, new Vector3(.18f, -.12f, 0f), new Vector3(.20f, .46f, .20f), bodyMaterial);
        Visual(PrimitiveType.Capsule, "arm fore R", forearmR, new Vector3(.15f, -.13f, .02f), new Vector3(.16f, .42f, .16f), bodyMaterial);
        Visual(PrimitiveType.Cube, "hand R", handR, new Vector3(.06f, -.10f, .05f), new Vector3(.22f, .18f, .18f), detailMaterial);
        Visual(PrimitiveType.Capsule, "thigh L", thighL, new Vector3(0f, -.30f, 0f), new Vector3(.25f, .54f, .25f), bodyMaterial);
        Visual(PrimitiveType.Capsule, "shin L", shinL, new Vector3(0f, -.29f, .03f), new Vector3(.18f, .54f, .18f), bodyMaterial);
        Visual(PrimitiveType.Cube, "foot L", footL, new Vector3(0f, -.08f, .12f), new Vector3(.22f, .15f, .42f), detailMaterial);
        Visual(PrimitiveType.Capsule, "thigh R", thighR, new Vector3(0f, -.30f, 0f), new Vector3(.25f, .54f, .25f), bodyMaterial);
        Visual(PrimitiveType.Capsule, "shin R", shinR, new Vector3(0f, -.29f, .03f), new Vector3(.18f, .54f, .18f), bodyMaterial);
        Visual(PrimitiveType.Cube, "foot R", footR, new Vector3(0f, -.08f, .12f), new Vector3(.22f, .15f, .42f), detailMaterial);
        generated = true;
        ApplyMaterials();
    }

    Transform Bone(string name, Transform parent, Vector3 position)
    {
        var bone = new GameObject(name).transform;
        bone.SetParent(parent, false);
        bone.localPosition = position * bodyScale;
        return bone;
    }

    Transform Visual(PrimitiveType type, string name, Transform parent, Vector3 position, Vector3 scale, Material material)
    {
        var visual = GameObject.CreatePrimitive(type);
        visual.name = name;
        visual.transform.SetParent(parent, false);
        visual.transform.localPosition = position * bodyScale;
        visual.transform.localScale = scale * bodyScale;
        var renderer = visual.GetComponent<Renderer>();
        if (renderer != null) renderer.sharedMaterial = material;
        var collider = visual.GetComponent<Collider>();
        if (collider != null)
        {
            if (Application.isPlaying) Destroy(collider);
            else DestroyImmediate(collider);
        }
        return visual.transform;
    }

    void ApplyMaterials()
    {
        if (!generated) return;
        foreach (var renderer in GetComponentsInChildren<Renderer>(true))
        {
            if (renderer == null) continue;
            var name = renderer.gameObject.name;
            if (name.Contains("head") || name.Contains("blank")) renderer.sharedMaterial = headMaterial ?? bodyMaterial;
            else if (name.Contains("face") || name.Contains("hand") || name.Contains("foot")) renderer.sharedMaterial = detailMaterial ?? bodyMaterial;
            else renderer.sharedMaterial = bodyMaterial;
        }
    }
}
