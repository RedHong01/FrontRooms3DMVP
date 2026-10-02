using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Authored Office furniture kit for the Level 4 stream profile.
///
/// The room stays sparse and the centre lane stays open.  The kit gives the
/// office a small family of believable late-1990s showroom objects, then
/// creates one deterministic "memory bleed" cluster from the same pieces:
/// repeated objects are slightly mis-scaled, rotated or embedded so the room
/// feels copied by a place that does not understand furniture.
///
/// The primary path loads editable Blender-authored FBX models from
/// Resources/Models/Office and reapplies the project's URP materials. The
/// procedural builders remain as a deterministic fallback so an import or
/// asset bundle problem cannot make a streamed room empty.
/// </summary>
public static class FrontRoomsOfficeFurniture
{
    static readonly Dictionary<string, Material> SurfaceCache = new Dictionary<string, Material>();
    static readonly Dictionary<string, GameObject> ModelCache = new Dictionary<string, GameObject>();

    public struct Materials
    {
        public Material wood;
        public Material woodEdge;
        public Material metal;
        public Material vinyl;
        public Material fabric;
        public Material wall;
        public Material plastic;
        public Material glass;
        public Material paper;
        public Material dark;
        public Material product;
    }

    public static Materials CreateMaterials(int sequence)
    {
        // The names include the profile sequence so the cache can retain
        // deterministic warm/cool furniture variants across recycled rooms.
        var warm = (Hash(sequence, 17) & 1) == 0;
        var wood = warm ? new Color(.28f, .25f, .20f) : new Color(.22f, .22f, .20f);
        var edge = warm ? new Color(.38f, .33f, .25f) : new Color(.32f, .30f, .25f);
        var vinyl = warm ? new Color(.54f, .56f, .52f) : new Color(.39f, .47f, .48f);
        return new Materials
        {
            wood = Surface("Office furniture / walnut " + sequence, "OfficeFurniture_Wood", wood, .28f, 0f, .30f),
            woodEdge = Surface("Office furniture / edge " + sequence, "OfficeFurniture_Wood", edge, .34f, 0f, .32f),
            metal = Surface("Office furniture / painted steel " + sequence, "OfficeFurniture_Metal", new Color(.46f, .48f, .45f), .46f, .72f, .24f),
            vinyl = Surface("Office furniture / faded vinyl " + sequence, "OfficeFurniture_Vinyl", vinyl, .58f, 0f, .44f),
            fabric = FrontRoomsSurfaces.CubicleFabric,
            wall = FrontRoomsSurfaces.Room(RoomRule.Office, FrontRoomsSurfaces.Slot.Wall),
            plastic = FrontRoomsSurfaces.Lit("Office furniture / CRT plastic " + sequence, new Color(.30f, .31f, .29f), .36f),
            glass = FrontRoomsSurfaces.Lit("Office furniture / CRT glass " + sequence, new Color(.055f, .10f, .105f), .86f, 0f, new Color(.015f, .035f, .04f)),
            paper = FrontRoomsSurfaces.Lit("Office furniture / paper " + sequence, new Color(.79f, .75f, .64f), .12f),
            dark = FrontRoomsSurfaces.Lit("Office furniture / dead screen " + sequence, new Color(.035f, .045f, .045f), .66f),
            product = FrontRoomsSurfaces.Lit("Office furniture / vending products " + sequence, new Color(.52f, .37f, .20f), .30f)
        };
    }

    static Material Surface(string name, string textureSet, Color tint, float smoothness, float metallic, float macroTone)
    {
        if (SurfaceCache.TryGetValue(name, out var cached) && cached != null) return cached;
        var shader = Shader.Find("FrontRooms/Surface");
        if (shader == null) return FrontRoomsSurfaces.Lit(name, tint, smoothness, metallic);

        var material = new Material(shader) { name = name };
        material.SetColor("_BaseColor", tint);
        material.SetFloat("_Smoothness", smoothness);
        material.SetFloat("_Metallic", metallic);
        material.SetFloat("_BumpScale", .45f);
        material.SetFloat("_OcclusionStrength", .72f);
        material.SetFloat("_MacroTone", macroTone);
        material.SetFloat("_MacroDirt", .18f);
        material.SetVector("_TileSize", new Vector4(1.2f, 1.2f, 0f, 0f));
        material.EnableKeyword("_FR_MESH_UV");
        AssignTexture(material, "_BaseMap", textureSet + "_A");
        AssignTexture(material, "_BumpMap", textureSet + "_N");
        AssignTexture(material, "_MaskMap", textureSet + "_S");
        AssignTexture(material, "_MacroMap", "MacroWear_M");
        SurfaceCache[name] = material;
        return material;
    }

    static void AssignTexture(Material material, string property, string resourceName)
    {
        var texture = Resources.Load<Texture2D>("Surfaces/Textures/" + resourceName);
        if (texture != null) material.SetTexture(property, texture);
    }

    static GameObject LoadModel(string assetName)
    {
        if (ModelCache.TryGetValue(assetName, out var cached) && cached != null) return cached;
        var model = Resources.Load<GameObject>("Models/Office/" + assetName);
        if (model != null) ModelCache[assetName] = model;
        return model;
    }

    static bool TryImportedModel(Transform parent, string assetName, Vector3 position, float yaw, Materials m, Vector3 scale)
    {
        var model = LoadModel(assetName);
        if (model == null) return false;
        var instance = Object.Instantiate(model, parent, false);
        instance.name = assetName + " / authored FBX";
        instance.transform.localPosition = position;
        instance.transform.localRotation = Quaternion.Euler(0f, yaw, 0f);
        // Unity's FBX importer keeps the Blender metre-to-centimetre root
        // factor on these assets. Preserve that 100x root scale when
        // instantiating; setting it to Vector3.one would collapse the mesh to
        // one hundredth of its authored size.
        instance.transform.localScale = scale * 100f;
        ApplyImportedMaterials(instance, m);
        return true;
    }

    static void ApplyImportedMaterials(GameObject root, Materials m)
    {
        foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
        {
            var slots = renderer.sharedMaterials;
            for (var i = 0; i < slots.Length; i++)
            {
                var name = slots[i] == null ? string.Empty : slots[i].name.ToLowerInvariant();
                if (name.Contains("woodedge")) slots[i] = m.woodEdge;
                else if (name.Contains("wood")) slots[i] = m.wood;
                else if (name.Contains("metal")) slots[i] = m.metal;
                else if (name.Contains("fabric")) slots[i] = m.fabric;
                else if (name.Contains("wall")) slots[i] = m.wall;
                else if (name.Contains("vinyl")) slots[i] = m.vinyl;
                else if (name.Contains("screen")) slots[i] = m.glass;
                else if (name.Contains("paper")) slots[i] = m.paper;
                else if (name.Contains("product")) slots[i] = m.product;
                else if (name.Contains("plastic")) slots[i] = m.plastic;
                else if (name.Contains("dark")) slots[i] = m.dark;
            }
            renderer.sharedMaterials = slots;
        }
    }

    /// <summary>Builds the normal workstations and the sparse memory-bleed cluster.</summary>
    public static void Build(Transform parent, int sequence, Materials materials)
    {
        // The reference image reads as a wide, under-occupied office rather
        // than a row of desks across the player's path. Keep the centre lane
        // empty and distribute complete desk/CRT/chair units down both sides.
        BuildWorkstation(parent, materials, "foreground left", new Vector3(-4.25f, 0f, 2.65f), -90f, true, -.04f);
        BuildWorkstation(parent, materials, "left middle", new Vector3(-4.15f, 0f, 6.45f), -90f, false, .12f);
        BuildWorkstation(parent, materials, "right middle", new Vector3(4.15f, 0f, 5.85f), 90f, false, -.10f);
        BuildWorkstation(parent, materials, "left rear", new Vector3(-3.65f, 0f, 8.85f), -90f, false, .08f);
        BuildWorkstation(parent, materials, "right rear", new Vector3(3.65f, 0f, 10.20f), 90f, false, -.12f);

        // Shallow structural piers sell the larger office footprint and give
        // the side furniture a believable reason to appear in clusters.
        BuildOfficePillars(parent, materials);

        // Keep the centre sightline and the door approach clear.  The memory
        // bleed lives to the sides and behind the workstations.
        BuildWaterCooler(parent, materials, new Vector3(4.28f, 0f, 3.75f));
        BuildCopier(parent, materials, new Vector3(4.28f, 0f, 7.15f));
        BuildFilingCabinet(parent, materials, new Vector3(4.28f, 0f, 8.75f), 0f);
        BuildDeadVendingMachine(parent, materials, new Vector3(4.88f, 0f, 10.55f));

        var variant = Mathf.Abs(Hash(sequence, 41)) % 3;
        var bleed = new GameObject("office memory bleed / variant " + variant);
        bleed.transform.SetParent(parent, false);
        bleed.transform.localPosition = variant == 1 ? new Vector3(-3.55f, 0f, 10.05f) : new Vector3(3.55f, 0f, 10.15f);
        bleed.transform.localRotation = Quaternion.Euler(0f, variant == 2 ? 5f : -3f, 0f);
        BuildMemoryBleed(bleed.transform, materials, variant);
    }

    static void BuildWorkstation(Transform parent, Materials materials, string label, Vector3 position, float yaw, bool panel, float chairOffset)
    {
        var station = new GameObject("office workstation / " + label);
        station.transform.SetParent(parent, false);
        station.transform.localPosition = position;
        station.transform.localRotation = Quaternion.Euler(0f, yaw, 0f);
        BuildDesk(station.transform, materials);
        BuildCRT(station.transform, materials, new Vector3(0f, .98f, .19f), 0f);
        BuildChair(station.transform, materials, new Vector3(chairOffset, 0f, -.68f), yaw > 90f ? 180f : 0f);
        BuildPaper(station.transform, materials, new Vector3(-.45f, .81f, -.18f));
        if (panel) BuildCubiclePanel(station.transform, materials);
    }

    static void BuildMemoryBleed(Transform parent, Materials m, int variant)
    {
        var desk = new GameObject("copied desk / wrong angle");
        desk.transform.SetParent(parent, false);
        desk.transform.localPosition = new Vector3(-.65f, .58f, .2f);
        desk.transform.localRotation = Quaternion.Euler(variant == 2 ? -9f : 6f, 17f, variant == 1 ? 3f : -2f);
        desk.transform.localScale = new Vector3(1.08f, .92f, .88f);
        BuildDesk(desk.transform, m);

        var cabinet = new GameObject("copied filing cabinet / embedded");
        cabinet.transform.SetParent(parent, false);
        cabinet.transform.localPosition = new Vector3(.60f, .18f, .62f);
        cabinet.transform.localRotation = Quaternion.Euler(variant == 0 ? 6f : -12f, -11f, variant == 2 ? 8f : -3f);
        cabinet.transform.localScale = new Vector3(.88f, 1.18f, 1.02f);
        BuildFilingCabinet(cabinet.transform, m, Vector3.zero, 0f);

        var chair = new GameObject("copied chair / upside down read");
        chair.transform.SetParent(parent, false);
        chair.transform.localPosition = new Vector3(-.15f, .76f, -.48f);
        chair.transform.localRotation = Quaternion.Euler(variant == 1 ? 168f : 156f, 25f, variant == 2 ? -8f : 7f);
        chair.transform.localScale = new Vector3(.92f, 1.05f, .92f);
        BuildChair(chair.transform, m, Vector3.zero, 0f);

        var shelf = new GameObject("copied shelf / clipped into stack");
        shelf.transform.SetParent(parent, false);
        shelf.transform.localPosition = new Vector3(.72f, .05f, -.58f);
        shelf.transform.localRotation = Quaternion.Euler(variant == 0 ? 8f : -5f, variant == 2 ? 27f : -19f, 0f);
        shelf.transform.localScale = new Vector3(.72f, .72f, .72f);
        BuildShelf(shelf.transform, m);

        // A second CRT is almost identical but carries a small offset and a
        // different rotation: the repetition should be recognised, not noisy.
        BuildCRT(parent, m, new Vector3(.18f, 1.73f, -.28f), variant == 0 ? -26f : 21f);
    }

    static void BuildOfficePillars(Transform parent, Materials m)
    {
        var wall = FrontRoomsSurfaces.Room(RoomRule.Office, FrontRoomsSurfaces.Slot.Wall);
        foreach (var position in new[]
        {
            new Vector3(-3.35f, 0f, 4.35f),
            new Vector3(3.35f, 0f, 4.35f),
            new Vector3(-3.35f, 0f, 9.15f),
            new Vector3(3.35f, 0f, 9.15f)
        })
        {
            if (TryImportedModel(parent, "OfficePillar", position, 0f, m, Vector3.one)) continue;
            var fallbackPosition = position + new Vector3(0f, 1.35f, 0f);
            var pillar = Bevel(parent, "office structural pier", fallbackPosition, new Vector3(.78f, 2.70f, .78f), .055f, wall);
            Box(pillar.transform, "office pier base", new Vector3(0f, -1.28f, 0f), new Vector3(.88f, .08f, .88f), m.metal, false);
        }
    }

    static void BuildDesk(Transform parent, Materials m)
    {
        if (TryImportedModel(parent, "OfficeDesk", Vector3.zero, 0f, m, Vector3.one)) return;
        Bevel(parent, "desk top", new Vector3(0f, .78f, 0f), new Vector3(1.92f, .11f, .78f), .055f, m.wood);
        Bevel(parent, "desk front edge", new Vector3(0f, .69f, -.33f), new Vector3(1.82f, .10f, .08f), .025f, m.woodEdge);
        Bevel(parent, "desk left pedestal", new Vector3(-.68f, .39f, .03f), new Vector3(.34f, .65f, .58f), .035f, m.wood);
        Bevel(parent, "desk right pedestal", new Vector3(.68f, .39f, .03f), new Vector3(.34f, .65f, .58f), .035f, m.wood);
        for (var side = -1; side <= 1; side += 2)
        {
            for (var drawer = 0; drawer < 2; drawer++)
            {
                var face = Bevel(parent, "desk drawer " + side + " / " + drawer,
                    new Vector3(side * .68f, .43f + drawer * .19f, -.275f), new Vector3(.26f, .14f, .025f), .012f, m.woodEdge);
                Box(parent, "desk drawer pull", new Vector3(side * .68f, .43f + drawer * .19f, -.302f), new Vector3(.08f, .012f, .012f), m.metal, false);
            }
        }
        Bevel(parent, "desk modesty panel", new Vector3(0f, .43f, .22f), new Vector3(1.18f, .48f, .055f), .018f, m.wood);
        for (var side = -1; side <= 1; side += 2)
            Box(parent, "desk steel leg", new Vector3(side * .89f, .36f, .24f), new Vector3(.055f, .66f, .055f), m.metal, false);
    }

    static void BuildCRT(Transform parent, Materials m, Vector3 position, float yaw)
    {
        // The authored model is exported in workstation-local coordinates.
        // Convert the old procedural CRT anchor (0,.98,.19) to that origin;
        // this also preserves the elevated placement used by memory bleed.
        var authoredPosition = position - new Vector3(0f, .98f, .19f);
        if (TryImportedModel(parent, "OfficeCRTComputer", authoredPosition, yaw, m, Vector3.one)) return;
        var crt = new GameObject("CRT monitor / repeated asset");
        crt.transform.SetParent(parent, false);
        crt.transform.localPosition = position;
        crt.transform.localRotation = Quaternion.Euler(0f, yaw, 0f);
        Bevel(crt.transform, "CRT casing", new Vector3(0f, .10f, 0f), new Vector3(.66f, .43f, .39f), .06f, m.plastic);
        Bevel(crt.transform, "CRT screen glass", new Vector3(0f, .12f, -.205f), new Vector3(.47f, .29f, .018f), .035f, m.glass);
        Box(crt.transform, "CRT bezel lip", new Vector3(0f, .12f, -.222f), new Vector3(.54f, .34f, .018f), m.dark, false);
        Bevel(crt.transform, "CRT neck", new Vector3(0f, -.19f, .01f), new Vector3(.12f, .18f, .11f), .02f, m.plastic);
        Bevel(crt.transform, "CRT stand foot", new Vector3(0f, -.29f, -.01f), new Vector3(.30f, .045f, .21f), .018f, m.metal);
        for (var i = -1; i <= 1; i++) Box(crt.transform, "CRT side vent", new Vector3(i * .15f, -.02f, .207f), new Vector3(.06f, .018f, .006f), m.dark, false);
        BuildKeyboard(crt.transform, m, new Vector3(0f, -.24f, -.37f));
    }

    static void BuildKeyboard(Transform parent, Materials m, Vector3 position)
    {
        var keyboard = new GameObject("CRT keyboard and mouse");
        keyboard.transform.SetParent(parent, false);
        keyboard.transform.localPosition = position;
        Bevel(keyboard.transform, "keyboard shell", Vector3.zero, new Vector3(.52f, .035f, .20f), .018f, m.plastic);
        for (var row = 0; row < 3; row++)
            Box(keyboard.transform, "keyboard key row " + row, new Vector3(0f, .025f, -.055f + row * .045f), new Vector3(.42f, .012f, .022f), m.paper, false);
        Bevel(keyboard.transform, "mouse", new Vector3(.35f, .012f, .015f), new Vector3(.095f, .025f, .13f), .03f, m.plastic);
        Box(keyboard.transform, "mouse cable", new Vector3(.22f, .02f, .015f), new Vector3(.19f, .008f, .012f), m.dark, false);
    }

    static void BuildChair(Transform parent, Materials m, Vector3 position, float yaw)
    {
        if (TryImportedModel(parent, "OfficeTaskChair", position, yaw, m, Vector3.one)) return;
        var chair = new GameObject("office task chair / repeated asset");
        chair.transform.SetParent(parent, false);
        chair.transform.localPosition = position;
        chair.transform.localRotation = Quaternion.Euler(0f, yaw, 0f);
        Bevel(chair.transform, "chair seat", new Vector3(0f, .52f, 0f), new Vector3(.60f, .14f, .56f), .07f, m.vinyl);
        var back = Bevel(chair.transform, "chair back", new Vector3(0f, .94f, .16f), new Vector3(.60f, .78f, .14f), .075f, m.vinyl);
        back.transform.localRotation = Quaternion.Euler(-5f, 0f, 0f);
        for (var side = -1; side <= 1; side += 2)
            Box(chair.transform, "chair arm", new Vector3(side * .34f, .76f, .02f), new Vector3(.055f, .08f, .34f), m.metal, false);
        Cylinder(chair.transform, "chair gas lift", new Vector3(0f, .28f, 0f), new Vector3(.055f, .26f, .055f), m.metal);
        Cylinder(chair.transform, "chair base", new Vector3(0f, .06f, 0f), new Vector3(.26f, .035f, .26f), m.metal);
        for (var i = 0; i < 5; i++)
        {
            var a = i * Mathf.PI * 2f / 5f;
            var wheel = new GameObject("chair star base arm");
            wheel.transform.SetParent(chair.transform, false);
            wheel.transform.localPosition = new Vector3(Mathf.Cos(a) * .28f, .055f, Mathf.Sin(a) * .28f);
            wheel.transform.localRotation = Quaternion.Euler(0f, -a * Mathf.Rad2Deg, 0f);
            Box(wheel.transform, "chair base arm", new Vector3(.12f, 0f, 0f), new Vector3(.26f, .035f, .035f), m.metal, false);
            Cylinder(wheel.transform, "chair caster", new Vector3(.25f, -.04f, 0f), new Vector3(.045f, .045f, .045f), m.dark);
        }
    }

    static void BuildFilingCabinet(Transform parent, Materials m, Vector3 position, float yaw)
    {
        if (TryImportedModel(parent, "OfficeFilingCabinet", position, yaw, m, Vector3.one)) return;
        var cabinet = new GameObject("filing cabinet / repeated asset");
        cabinet.transform.SetParent(parent, false);
        cabinet.transform.localPosition = position;
        cabinet.transform.localRotation = Quaternion.Euler(0f, yaw, 0f);
        Bevel(cabinet.transform, "filing cabinet body", new Vector3(0f, .74f, 0f), new Vector3(.76f, 1.48f, .58f), .045f, m.metal);
        for (var i = 0; i < 3; i++)
        {
            var y = .34f + i * .39f;
            Bevel(cabinet.transform, "filing drawer", new Vector3(0f, y, -.302f), new Vector3(.64f, .32f, .025f), .012f, m.metal);
            Box(cabinet.transform, "filing label pull", new Vector3(0f, y + .03f, -.328f), new Vector3(.16f, .018f, .014f), m.paper, false);
        }
        Box(cabinet.transform, "filing cabinet foot left", new Vector3(-.27f, .045f, 0f), new Vector3(.08f, .09f, .40f), m.dark, false);
        Box(cabinet.transform, "filing cabinet foot right", new Vector3(.27f, .045f, 0f), new Vector3(.08f, .09f, .40f), m.dark, false);
    }

    static void BuildCopier(Transform parent, Materials m, Vector3 position)
    {
        if (TryImportedModel(parent, "OfficeCopier", position, 0f, m, Vector3.one)) return;
        var copier = new GameObject("office copier / repeated asset");
        copier.transform.SetParent(parent, false);
        copier.transform.localPosition = position;
        Bevel(copier.transform, "copier lower body", new Vector3(0f, .58f, 0f), new Vector3(.92f, 1.16f, .76f), .05f, m.metal);
        Bevel(copier.transform, "copier upper body", new Vector3(0f, 1.30f, .02f), new Vector3(.82f, .24f, .72f), .04f, m.plastic);
        Bevel(copier.transform, "copier document lid", new Vector3(0f, 1.47f, .02f), new Vector3(.66f, .035f, .55f), .018f, m.paper);
        Box(copier.transform, "copier output tray", new Vector3(0f, .94f, -.43f), new Vector3(.48f, .045f, .20f), m.dark, false);
        Box(copier.transform, "copier control panel", new Vector3(.27f, 1.39f, -.37f), new Vector3(.18f, .04f, .025f), m.dark, false);
        for (var drawer = 0; drawer < 2; drawer++)
            Bevel(copier.transform, "copier paper drawer " + drawer, new Vector3(0f, .28f + drawer * .32f, -.39f), new Vector3(.62f, .20f, .025f), .012f, m.metal);
        Box(copier.transform, "copier status strip", new Vector3(.12f, 1.39f, -.395f), new Vector3(.12f, .018f, .012f), m.paper, false);
    }

    static void BuildShelf(Transform parent, Materials m)
    {
        if (TryImportedModel(parent, "OfficeShelf", Vector3.zero, 0f, m, Vector3.one)) return;
        for (var side = -1; side <= 1; side += 2)
            Box(parent, "shelf upright", new Vector3(side * .52f, .72f, 0f), new Vector3(.065f, 1.45f, .34f), m.metal, false);
        for (var i = 0; i < 4; i++)
            Bevel(parent, "shelf plank " + i, new Vector3(0f, .12f + i * .40f, 0f), new Vector3(1.12f, .075f, .42f), .018f, m.wood);
    }

    static void BuildWaterCooler(Transform parent, Materials m, Vector3 position)
    {
        if (TryImportedModel(parent, "OfficeWaterCooler", position, 0f, m, Vector3.one)) return;
        var cooler = new GameObject("office water cooler / sparse prop");
        cooler.transform.SetParent(parent, false);
        cooler.transform.localPosition = position;
        Bevel(cooler.transform, "cooler base", new Vector3(0f, .62f, 0f), new Vector3(.56f, 1.24f, .56f), .07f, m.metal);
        Bevel(cooler.transform, "cooler bottle", new Vector3(0f, 1.52f, 0f), new Vector3(.36f, .52f, .36f), .11f, m.glass);
        Box(cooler.transform, "cooler tap panel", new Vector3(0f, .92f, -.29f), new Vector3(.27f, .19f, .025f), m.dark, false);
    }

    static void BuildDeadVendingMachine(Transform parent, Materials m, Vector3 position)
    {
        if (TryImportedModel(parent, "OfficeVendingMachine", position, 0f, m, Vector3.one)) return;
        var machine = new GameObject("office vending machine / dead");
        machine.transform.SetParent(parent, false);
        machine.transform.localPosition = position;
        Bevel(machine.transform, "vending machine body", new Vector3(0f, 1.10f, 0f), new Vector3(.74f, 2.20f, .58f), .06f, m.metal);
        Box(machine.transform, "vending machine black display", new Vector3(-.02f, 1.55f, -.302f), new Vector3(.52f, .42f, .018f), m.dark, false);
        Box(machine.transform, "vending machine dead label", new Vector3(.04f, .92f, -.31f), new Vector3(.30f, .04f, .015f), m.paper, false);
    }

    static void BuildPaper(Transform parent, Materials m, Vector3 position)
    {
        Box(parent, "office paper / repeated note", position, new Vector3(.24f, .018f, .30f), m.paper, false);
        Box(parent, "office paper / offset sheet", position + new Vector3(.025f, .012f, -.018f), new Vector3(.20f, .014f, .25f), m.paper, false);
    }

    static void BuildCubiclePanel(Transform parent, Materials m)
    {
        if (TryImportedModel(parent, "OfficeCubiclePanel", Vector3.zero, 0f, m, Vector3.one)) return;
        Bevel(parent, "office cubicle panel", new Vector3(0f, 1.20f, .82f), new Vector3(1.45f, 1.0f, .09f), .025f, m.fabric);
        Box(parent, "office cubicle panel cap", new Vector3(0f, 1.69f, .82f), new Vector3(1.38f, .025f, .11f), m.metal, false);
    }

    static GameObject Bevel(Transform parent, string name, Vector3 position, Vector3 scale, float bevel, Material material)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = position;
        var filter = go.AddComponent<MeshFilter>();
        filter.sharedMesh = FrontRoomsFilmMesh.GetBeveledBox(scale, bevel);
        var renderer = go.AddComponent<MeshRenderer>();
        renderer.sharedMaterial = material;
        return go;
    }

    static GameObject Box(Transform parent, string name, Vector3 position, Vector3 scale, Material material, bool collider)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = position;
        var filter = go.AddComponent<MeshFilter>();
        filter.sharedMesh = FrontRoomsFilmMesh.GetPlanarBox(scale);
        var renderer = go.AddComponent<MeshRenderer>();
        renderer.sharedMaterial = material;
        if (collider)
        {
            var box = go.AddComponent<BoxCollider>();
            box.size = scale;
        }
        return go;
    }

    static GameObject Cylinder(Transform parent, string name, Vector3 position, Vector3 scale, Material material)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        go.name = name;
        go.transform.SetParent(parent, false);
        go.transform.localPosition = position;
        go.transform.localScale = scale;
        var renderer = go.GetComponent<Renderer>();
        if (renderer != null) renderer.sharedMaterial = material;
        var collider = go.GetComponent<Collider>();
        if (collider != null)
        {
            if (Application.isPlaying) Object.Destroy(collider);
            else Object.DestroyImmediate(collider);
        }
        return go;
    }

    static int Hash(int value, int salt)
    {
        unchecked
        {
            var x = value * 1103515245 + salt * 12345;
            x ^= x >> 16;
            x *= 16777619;
            return x ^ (x >> 13);
        }
    }
}
