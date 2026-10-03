# 02 — Creature craft for the Relay redesign

Status: COMPLETE (2026-10-02). Research report 02 of the Hunter redesign. Scope: the *craft* of designing a liminal / analog-horror chaser that must read in dim fluorescent light in first person. Case studies are studied for principles only; no design is copied or closely imitated.

Rules of evidence: every claim carries the URL it was read from in this pass. Anything not read in this pass is marked **[UNVERIFIED]**. Quotes are one short phrase per source at most.

## 0. Brief and constraints (from the project)

Read from the project, 2026-10-02:

| Constraint | Value | Source in project |
|---|---|---|
| Body | radius 0.3 m, tested between 0.4 and 1.95 m | `LEVEL_MODULE_SPEC.md` §7, `FrontRoomsMapHunter.cs` (`ProbeBottom .4`, `ProbeTop 1.95`) |
| Height | **≤ 2.05 m while walking, or it stoops**; must fit a 1.0 × 2.1 m door, a broken window (sill 0.35, head 2.0) and 2.4 m Low ceilings | spec §3, §7; `ModuleUnits.RelayHeight = 2.05` |
| Eye | sight ray at **1.60 m** (player eye 1.62 m) | `ModuleUnits.RelayEye`; spec §7 |
| States | Dormant → Listen (2 s) → Hunt (walk **2.6 m/s**) → Search (2.5 s) → Chase (**4.2 m/s** in code, ×1.15 anim speed; the brief's "4.2–5.4" upper figure was not found in code or `FrontRoomsLevel0.asset`, so design the run for 4.2 with headroom) → BreakDoor (blows every 0.5 s) ; rig also has Stagger | `FrontRoomsHunterTuning`, `FrontRoomsMapHunter.cs`, `FrontRoomsRelayRig.cs` |
| Senses | sees with a ray (range 12 m), hears sprint (26 m) and door noise (14 m), walks to the *last noise*, "relays" itself closer **unseen** when it trails by > 30 cells | `FrontRoomsHunterTuning`, `FrontRoomsMapHunter` header comment |
| Player | walk 3.2, sprint 5.5 m/s for 5 s; FOV target 72° vertical (≈ 14 mm), eye 1.6–1.62 m | spec §7; `10_synthesis.md` decision 11, §6.8 |
| Catch | 0.7 m while it sees you | `catchDistance` |
| Budget | production rig 24–36 bones, 4 influences, no cloth/hair/physics (WebGL) | `RELAY_MODEL_RIG_RESEARCH.md` |
| Light | overhead troffers only: one 2×4 lens per 3 m cell, downward spot 162°/96°, 4000 K-ish; Office walls render at L ≈ 0.15–0.25, lenses clip | spec §4; `10_synthesis.md` §6.3, §6.9 |
| World | warm mono-yellow Level 0 maze; cool green-grey 1990s Office; film grain; copy-paste furniture piles; nothing newer than early 1990s | `VISUAL_RESEARCH_LOOKDEV.md`, `10_synthesis.md` §0.3 |
| Current language | tall, hunched, blank pale head, one narrow dark face void, charcoal body, muted yellow detail | `RELAY_MODEL_RIG_RESEARCH.md` "Model language" |

What the creature has to *do* in first person, in order of how often the player experiences it: (1) be **heard** through walls (Listen/Hunt footfalls); (2) be **glimpsed** at a threshold or down a 3 m corridor under a troffer; (3) be **read at 6–12 m** while chasing, over the player's shoulder or after a turn; (4) **break a door** (the moment it is closest to the player while still separated); (5) fill the frame at **0.7 m** on catch. The model must work in that order: sound, silhouette, gait, mass, then face.

## 1. Diagnosis: why the current rig reads spindly and odd

Measured from `FrontRoomsRelayRig.BuildRig()` and the serialized `Hunter` in `Assets/Scenes/FrontRooms3D.unity` (`bodyScale 1`, root scale 1), in rest pose, ignoring the small animation pitches. Unity primitives: capsule = 2 m tall × 1 m wide at scale 1, sphere = 1 m.

| Part | Where it actually is | Problem |
|---|---|---|
| Head | head bone at **2.73 m**, egg 0.70 tall → top ≈ **3.0–3.1 m** | ~1.5× the 2.05 m limit. It would clip through every 2.1 m door head and 2.4 m ceiling. |
| Neck | 0.62 m bone, hidden inside the body capsule | No visible neck, so the head sits on the torso like a cap |
| Torso | one capsule 0.68 × 1.56 × 0.53 m, from 1.11 to 2.67 m | A pill, not a ribcage/pelvis: no waist, no shoulder plane, no front/back |
| Hips | pelvis at 0.92 m has **no mesh**; thighs end at 0.61 m | **A 0.5 m empty gap** between legs and torso: the torso floats |
| Legs | chain is 0.55 + 0.60 + 0.56 = **1.71 m long under a 0.92 m pelvis** | Shins and feet sit **0.2–0.8 m under the floor**; only two thigh stubs show. The "oversized feet for carpet impact" are never seen. |
| Arms | bones laid out **sideways** (T-pose) at 2.24 m shoulder height; the capsules are vertical and hang from each bone at x 0.58 / 0.93 / 1.18 m | They read as **six vertical pillars fanned around the body, ≈ 2.6 m wide**, not as arms. The walk swings them about the hidden horizontal bone, so they flap forward and back like boards. 2.6 m will not visually pass a 1.0 m door. |
| Values | body albedo #2B2928 (L* ≈ 17) vs. the Office target's rendered walls #3C392C (L* ≈ 24) and cubicle fabric #2E2F28 (L* ≈ 19) | Contrast ≈ 1.25:1 against walls: the body **vanishes** in the Office. Only the pale head (L* ≈ 85) reads. Caveat: albedo vs. rendered values, so indicative only. |
| Face at catch | at catch distance 0.7 m with a 72° vertical FOV, anything higher than 1.62 + 0.7 × tan 36° ≈ **2.13 m** is above the frame | The current head (2.7–3.1 m) is **out of frame** when it catches you. The ≤ 2.05 m rule is also the rule that keeps its face on screen. |

So "spindly/odd" is not a style problem first: it is a **construction** problem (floating torso, buried legs, T-posed pillar arms, a 3 m head). The redesign should start from a proportion sheet that is measured against the door, the ceiling and the camera, not from a primitive kit.

## 2. Craft principles

### 2.1 Silhouette

**What the sources say.**
- Valve built Team Fortress 2's classes so each could be named "even with no lighting cues", then added a dedicated rim term so characters stay highlighted at range ([TF2 wiki, Art style, summarising Valve's NPAR 2007 paper](https://wiki.teamfortress.com/wiki/Artstyle)).
- Detail has a budget: concentrate it in focal areas and leave visual resting spots; "Having detail everywhere is as good as having no detail at all" ([80.lv](https://80.lv/articles/character-design-shape-language-and-readability/)). Block large shapes zoomed out first.
- Trevor Henderson designs the **environment first and the creature last**, restarting the creature until it sits in that space through light, texture and colour ([Reactor](https://reactormag.com/artist-trevor-henderson-siren-head-interview/)).

**What that means at FrontRooms' camera.** With a 72° vertical FOV the frame is 1.45 × *d* tall at distance *d*. A 2.0 m figure fills:

| Distance | Where it happens | Share of frame height | At 1080p |
|---|---|---|---|
| 12 m (sight range) | end of a 4-cell corridor | 11 % | ≈ 125 px |
| 6 m | across an Office pod / two cells | 23 % | ≈ 250 px |
| 3 m | one cell, through a door | 46 % | ≈ 500 px |
| 0.7 m (catch) | in your face | only the band 1.11–2.13 m is visible | head, shoulders, chest |

So the creature needs **two designed reads**: a full-body silhouette that survives at 125 px (posture, head-to-shoulder relation, arm length, negative space between arms and body, gait), and a **catch portrait** of chest-shoulders-head that fills the frame. A 0.08 m face slit is 5 px at 12 m and 10 px at 6 m: it is a close-range detail, not a silhouette feature.

**Rules.** (1) Design it as a black cut-out in a 3 m corridor under one troffer before modelling anything. (2) One dominant silhouette idea, not three. (3) Keep negative space: arms that separate from the torso when it walks read at range; arms glued to a capsule do not. (4) Its shape must be unmistakable against a doorway (1.0 × 2.1 m bright rectangle): that is the most common framing in this game.

### 2.2 Proportion distortion (elongation, joint count, posture)

**What the sources say.**
- Henderson aims for "slightly off proportions, surreal features" rather than teeth, brows and claws ([Daily Dead Q&A](https://dailydead.com/qa-trevor-henderson-discusses-the-found-footage-style-of-his-fascinating-horror-artwork/)).
- SCP-096's whole identity is one exaggerated ratio: about 2.38 m tall with arms of about 1.5 m and a jaw that opens far past human range ([SCP Wiki, CC BY-SA 3.0](https://scp-wiki.wikidot.com/scp-096)).
- Javier Botet (about 2.01 m, Marfan syndrome, long fingers, hypermobile joints) has played many film creatures with little CGI: a real body slightly outside normal range ([Wikipedia](https://en.wikipedia.org/wiki/Javier_Botet)).
- Slender Man is "unnaturally tall, extremely thin" ([Wikipedia](https://en.wikipedia.org/wiki/Slender_Man)). That is exactly the register Red calls "spindly": thinness alone is not threatening at 2 m.
- Creative Assembly kept Giger's Alien but re-jointed its legs so the walk cycle would hold up under long scrutiny ([Wikipedia, Alien: Isolation](https://en.wikipedia.org/wiki/Alien:_Isolation)). Joint changes are about **motion**, not stills.
- Silent Hill 2's Mannequin recombines human parts (two pairs of legs, no head) rather than inventing new anatomy ([Bogleech essay](https://bogleech.com/halloween/hall15-silenthill2)).

**What that means under a 2.05 m cap.** FrontRooms cannot get its menace from height: the door and the 2.4 m ceiling forbid it. Elongation has to come from **ratios inside 2.05 m**:
- *Heads-tall.* A smaller head makes a 2.0 m body read taller. But the head carries the face read at catch, so shrink it only a little (≈ 8–9 heads instead of 7.5) or move mass elsewhere.
- *One long segment.* Pick one: forearms, fingers, neck or torso. Long forearms with hands that hang to the knee read at 125 px; long fingers only read at catch.
- *Posture as the default.* The spec says it stoops at doors. Make the stoop the resting silhouette (shoulders at ≈ 1.75–1.95 m, head pushed forward and *down* to the 1.60 m eye line) so it never has to change shape at a doorway and the face stays inside the frame at catch (§1).
- *Mass, not sticks.* Red's complaint is "spindly". Give it one heavy mass (padded shoulders, a deep chest, a hump, a load it carries) and keep thinness for the limbs. Thin against thick is a contrast; thin everywhere is a stick figure.
- *Joint count.* An extra or reversed joint should be used only where it changes the gait or the door-break pose, since it costs bones (24–36 budget) and reads only in motion.

### 2.3 Uncanny partial humanness

**What the sources say.**
- Mori's uncanny-valley curve: affinity rises with likeness, then drops sharply just short of full human likeness; **movement steepens both peaks and valleys**; the corpse sits at the bottom. His example: a realistic prosthetic hand turns uncanny the moment you discover it is artificial ([IEEE Spectrum translation](https://spectrum.ieee.org/the-uncanny-valley)).
- Thomas Grip's brief for Amnesia's Grunt: "take something normal and then add a disturbing twist"; a humanoid because nothing else walks like a person and players project onto it. A first, cartoony hunchback concept was rejected as too childlike ([Game Developer, Birth of a Monster pt 1](https://www.gamedeveloper.com/art/amnesia-the-dark-descent-birth-of-a-monster-part-1-)).
- The Exit 8's only other person is a middle-aged man in work clothes with a briefcase; some loops make him the anomaly (wrong proportions, walking quickly at you, blending into the wall tiles) ([Wikipedia](https://en.wikipedia.org/wiki/The_Exit_8)).
- The Mandela Catalogue's alternates are doppelgängers: the fear is that someone familiar has been replaced ([Wikipedia](https://en.wikipedia.org/wiki/The_Mandela_Catalogue)).
- Control's Hiss are the player's possessed co-workers, some named, floating and muttering ([Dread Central](https://www.dreadcentral.com/editorials/493272/monster-mania-controls-hiss-are-a-workplace-nightmare/)).
- [UNVERIFIED: a 2001 making-of quote attributed to Masahiro Ito, seen only in a search snippet] Silent Hill 2's creatures should read as a person in fog at first, then be undermined by strange movement and impossible body angles.

**Principle: an anchor and a tell.** Decide what stays human (the *anchor*: clothing, height, gait at a distance, a hand) and what is wrong (the *tell*: one ratio, one joint, one missing feature, one wrong motion). The tell should be discovered, not announced: a far read says "a person", a closer read says "no". In a 1990s office the strongest anchor is an **employee**: the one figure that belongs there.

### 2.4 Faces and face-voids

**What the sources say.**
- Ito wanted "a monster with a hidden face" for Pyramid Head ([Wikipedia, Pyramid Head](https://en.wikipedia.org/wiki/Pyramid_Head)); his Lying Figure has a zipper down its face, "like a body bag" ([Bogleech](https://bogleech.com/halloween/hall15-silenthill2)).
- Slender Man's face is featureless ([Wikipedia](https://en.wikipedia.org/wiki/Slender_Man)); Sadako's is hidden under hair ([Wikipedia](https://en.wikipedia.org/wiki/Sadako_Yamamura)).
- Henderson removes recognisable features, notably eyes, so the creature's intention stays ambiguous ([Reactor](https://reactormag.com/artist-trevor-henderson-siren-head-interview/)).
- The Last of Us' Clickers have their faces overgrown and are blind; they hunt by sound ([Dread Central](https://www.dreadcentral.com/editorials/492187/monster-mania-in-the-last-of-us-silence-is-your-savior/)).
- SCP-096 makes the face the trigger: seeing it starts the pursuit ([SCP Wiki](https://scp-wiki.wikidot.com/scp-096)); Lethal Company's Bracken backs off when looked at and turns hostile if stared at ([Lethal Company wiki.gg](https://lethalcompany.wiki.gg/wiki/Bracken)).

**For the Relay.** The Relay hunts by **noise**, so a blind or covered face is *honest*: it tells the player how it senses. Options, in order of how well they survive dim overhead light:
1. **A face the light erases.** Overhead light hoods the eye sockets: Gordon Willis' top light left Brando's eyes "hooded in shadow" ([BFI](https://bfi.org.uk/features/gordon-willis-career-12-pictures)). A brow, brim, hood or forward-pitched head under a troffer makes the face void for free and keeps it consistent at every distance.
2. **A covered face**: an object where the face should be (era-appropriate and diegetic; see §5).
3. **A blank face** (the current egg): reads at range as a pale disc, which is good, but it is also the most familiar "faceless" trope.
4. **A painted / printed face** that is not a face (a pattern, a label): reads only near.
Avoid a glowing-eye default; if anything glows, it should be a period object (a CRT-like phosphor, a pilot lamp) and it should mean something (e.g. it is listening).

### 2.5 Costume vs. body

**What the sources say.**
- The Exit 8 man's identity is costume (work clothes, briefcase); the anomaly lives in his body and motion ([Wikipedia](https://en.wikipedia.org/wiki/The_Exit_8)).
- Slender Man's black suit and tie make his body's wrongness legible by contrast ([Wikipedia](https://en.wikipedia.org/wiki/Slender_Man)).
- The Grunt has almost no clothing: bandages and ropes hold a deformed frame together ([Game Developer](https://www.gamedeveloper.com/art/amnesia-the-dark-descent-birth-of-a-monster-part-1-)).
- Dark Deception gives each nightmare its own creature with distinct AI ([Steam](https://store.steampowered.com/app/332950/)); its first-chapter monkeys are dressed in hotel uniforms [UNVERIFIED: fan-wiki search snippet only]: theme carried by costume.
- Period: double-breasted "power suits" in navy, charcoal grey or air-force blue came back in the 1980s ([Wikipedia, 1980s fashion](https://en.wikipedia.org/wiki/1980s_in_fashion)); shoulder pads ran from the mid-1980s to the early 1990s, and early-1990s women's suits were navy, grey or pastel with shoulder pads ([Wikipedia, 1990s fashion](https://en.wikipedia.org/wiki/1990s_in_fashion)).

**Principle.** Costume is the cheapest place to put **era, theme and value blocks**; the body is where the wrongness lives. For FrontRooms:
- A padded-shoulder jacket is an era-correct way to give the Relay the **mass** it lacks (§2.2) and a hard horizontal shoulder line that a hunch can break.
- A light shirt or collar under a dark jacket gives a **light value block at chest height**, which reads in the Office where a charcoal body vanishes (§1, §2.7).
- No cloth simulation is allowed (WebGL budget), so the costume must be **stiff**: boxy jacket, tucked shirt, short tie, no long coat or loose hair. Stiffness also reads as "mannequin".

### 2.6 Motion that sells wrongness

**What the sources say.**
- Movement amplifies the uncanny (Mori, [IEEE Spectrum](https://spectrum.ieee.org/the-uncanny-valley)).
- Ringu's Sadako: a kabuki-trained actress walked **backwards** with jerky, exaggerated movements and the footage was reversed ([Academia-Lab mirror of the Ringu article](https://academia-lab.com/encyclopedia/ringu/); the current English Wikipedia page does not carry this detail).
- Weeping Angels only move when unobserved ([Wikipedia](https://en.wikipedia.org/wiki/Weeping_Angel)); the Coil-head is a bloody mannequin on a spring neck that freezes while watched ([Esports Tales](https://www.esportstales.com/lethal-company/how-to-survive-the-coil-head)).
- It Follows grew from a nightmare of something very slow that was "always coming towards me"; the film also hides figures in the background for the audience to find ([Den of Geek](https://www.denofgeek.com/movies/david-robert-mitchell-interview-it-follows-and-horror/)).
- Exit 8's man becomes an anomaly by walking quickly at you ([Wikipedia](https://en.wikipedia.org/wiki/The_Exit_8)).
- The Alien searches in deliberately sub-optimal patterns so it looks like it is hunting, not path-finding ([Game Developer](https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation)).
- The Hiss float like puppets on strings ([Dread Central](https://www.dreadcentral.com/editorials/493272/monster-mania-controls-hiss-are-a-workplace-nightmare/)); yūrei are drawn without legs, a convention from Edo-period prints carried into kabuki ([Wikipedia](https://en.wikipedia.org/wiki/Y%C5%ABrei)).
- The Bracken straightens up and backs away rapidly when spotted ([wiki.gg](https://lethalcompany.wiki.gg/wiki/Bracken)).

**A vocabulary of wrong motion (each maps to cheap procedural tricks).**

| Wrongness | What it is | Procedural recipe in `TickAnimation` terms |
|---|---|---|
| Stutter | poses held, then snapped | quantise the gait phase to 8–12 steps per cycle ("on twos"), never the root motion |
| Glide | body moves, feet don't sell it | stride amplitude too small for the speed, or feet locked under a hem/skirt panel |
| Metronome | too-regular | constant gait phase, zero variance, head locked level: a person never walks like that |
| Head lock | the head stays on target while the body turns | counter-rotate neck to keep the face void on the last noise / the player |
| Wrong category | the gait changes kind with state | Hunt: upright walk; Chase: drops forward, arms join the stride |
| Reverse | something moving backwards that should not | backing away in Search, or a reversed-phase arm swing |
| Unobserved change | pose differs after a cut | change pose only during a lamp's dark frame or when off-screen (fits "relays when out of sight") |
| Copy-paste | identical repeats | BreakDoor blows exactly the same each 0.5 s, like the film's duplicate furniture |

### 2.7 Lighting tricks for dim fluorescent first person

**What the sources say.**
- Rim highlights keep characters readable at distance (TF2, [wiki](https://wiki.teamfortress.com/wiki/Artstyle)).
- Backlighting separates the subject from the background and raises contrast ([Colbor](https://www.colborlight.com/blogs/articles/how-to-get-lighting-effects-in-film)).
- Top light hoods the eyes (Willis, [BFI](https://bfi.org.uk/features/gordon-willis-career-12-pictures)).
- Henderson blends creatures into photographs through lighting, texture and colour ([Reactor](https://reactormag.com/artist-trevor-henderson-siren-head-interview/)).

**FrontRooms' light is fixed**: one overhead 2×4 troffer per 3 m cell, some dead, some flickering; no film lights; a lit ceiling band near each lens (L* ≈ 72), dark walls in the Office (L* ≈ 24), mid carpet (L* ≈ 38) (`10_synthesis.md` §6.9). So:
1. **Design for top light.** Everything the player should read must face *up*: shoulders, the top of the head, a brim, a collar. Downward-facing planes (face, underside of arms) go dark. Use that to make the face void, not fight it.
2. **Cell strobe.** Walking from a lit cell into a dead one is a natural reveal/hide rhythm. Give the creature one **light-value element** (head, shirt, a tag) that still reads in the dead cell, and a dark mass that only reads against lit surfaces.
3. **Silhouette against the bright band.** In 2.4 m Low rooms the head is 0.35–0.4 m under the lenses: it reads as a cut-out against the ceiling. In the 2.9 m Office the head sits against dark walls, so the light-value element matters more there.
4. **Doorway backlight.** A lit room behind a door turns the 1.0 × 2.1 m opening into a lightbox: the stooped silhouette filling it is the game's most repeatable hero shot.
5. **Flicker as a blink.** A failing lamp's off-frames are the moment to change pose (Weeping Angel rule, §2.6).
6. **Value, not colour.** The Office grade desaturates to 0.08–0.2; colour will not separate the Relay. Muted yellow detail survives only as a value (L* ≈ 65).
7. **Rim term.** If the body shader gets one change, it is a subtle Fresnel rim driven by the nearest troffer, so the silhouette survives against dark walls (TF2's approach).

### 2.8 Sound-driven design

**What the sources say.**
- Clickers' clicking both announces where they are and reminds the player to stay quiet ([Dread Central](https://www.dreadcentral.com/editorials/492187/monster-mania-in-the-last-of-us-silence-is-your-savior/)).
- Ju-On's croak is the director's own voice ("Yes that is me", [Dread Central](https://www.dreadcentral.com/news/3275/shimizu-takashi-the-grudge/)): a cheap, human-made sound can become the signature.
- Petri Alanko built the Hiss by bending tunings and overtones: "When you hear those sounds, they tell you something evil is about to happen" ([Inverse](https://inverse.com/article/59452-control-video-game-petri-alanko-interview-hiss)).
- Alien: Isolation's director raises a menace gauge when the player can **hear** the Alien moving, not only see it, and sends it to the vents to release tension ([Game Developer](https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation)).
- The Bracken is silent while moving and makes noise only when opening a door ([wiki.gg](https://lethalcompany.wiki.gg/wiki/Bracken)).
- Iron Lung shows its world only as low-resolution photos; the threat is assembled from ambiguous images and sound ([Wikipedia](https://en.wikipedia.org/wiki/Iron_Lung_(video_game))).
- Amnesia's unseen water monster is remembered as the scariest because it is never shown [UNVERIFIED: USgamer page returned 503; seen only in a search summary].

**Principle: design the body that makes the sound.** The Relay is heard first (heavy carpet footfalls, low-passed through walls; `RELAY_MODEL_RIG_RESEARCH.md`). The model should explain the sound: what are its feet (hard heels on carpet, a dragging toe, a caster)? What hangs on it that rattles (keys, a badge clip)? What does its breathing or a mechanism do in Listen? Each state needs its own audible signature so the player can read state through walls:
- Listen: silence, or the room's hum **dropping out** near it;
- Hunt: steady, metronomic footfalls (the "metronome" walk);
- Chase: a gait sound that changes category (faster, plus a second layer: cloth, a rattle, a vocal);
- BreakDoor: a repeated identical blow every 0.5 s.
The fluorescent hum is FrontRooms' bed; a creature that **disturbs the hum or the ballasts** (lamps strike or buzz as it passes) is heard through the light system the game already has.

## 3. Case studies (principles only)

Each row: what the case does, the principle FrontRooms can use, and the part that belongs to that work and must **not** be reused (shapes, signature parts, names).

| Case | What it does (sourced) | Principle to take | Do not reuse |
|---|---|---|---|
| **Dark Deception** (Red's primary ref) | Maze-chase where "every nightmare presents a unique creature that has its own distinct AI"; enemies can be stunned and avoided but never killed ([Steam](https://store.steampowered.com/app/332950/)). Its monsters are each one costume concept plus one wrong feature: wind-up monkeys in bellhop uniforms with blades for hands, a child with overlong clawed arms, gold-plated watchers, metal ducks with human teeth; in the Monsters & Mortals spin-off each one's enraged state **recolours** it (eyes red, clothes change) ([GamePretty guide](https://gamepretty.com/dark-deception-monsters-mortals-monsters-guide/)). | **Readable themed monsters**: theme carried by costume and setting, one exaggerated feature, uncatchable, and a visible state change. FrontRooms' theme is the 1990s office/store, so its monster should be "what works there". A visible Chase tell (something on the body changes) is worth borrowing as a rule. | The specific creatures (monkeys, bellhop, blades, ducks, dolls), the cartoon-mascot comedy register. |
| **The Exit 8** | The only other person is an ordinary middle-aged man in work clothes with a briefcase; anomalies include wrong proportions, walking quickly at you, blending into wall tiles; at about 140k polys he is the game's largest asset ([Wikipedia](https://en.wikipedia.org/wiki/The_Exit_8)). | The ordinary worker *is* the anomaly. Spend the asset budget on the human figure; let realism carry the dread and use **small deviations** (scale, speed, camouflage). | The salaryman with briefcase as a look; the tile camouflage gag. |
| **Lethal Company** | Coil-head: a bloody mannequin with a spring for a neck that moves only when not watched ([Esports Tales](https://www.esportstales.com/lethal-company/how-to-survive-the-coil-head)). Bracken: a tall dark-red stalker that straightens up and backs away when seen, angers if stared at, makes no noise moving but does when opening doors ([wiki.gg](https://lethalcompany.wiki.gg/wiki/Bracken); [Wikipedia](https://en.wikipedia.org/wiki/Lethal_Company)). | **Gaze as a mechanic**, and body language that reacts to being seen (straighten up, back off). Silence as a signature, with doors as the only noise. | The spring neck, the CCTV/mannequin head combination, the leafy red body. |
| **SCP-096** | ≈ 2.38 m, emaciated, arms ≈ 1.5 m, depigmented; seeing its face triggers distress and an unstoppable pursuit ([SCP Wiki, CC BY-SA 3.0](https://scp-wiki.wikidot.com/scp-096)). | One exaggerated ratio (arms) as identity; a **trigger** that links a body part to the AI state (the face). | Pale, long-armed, face-trigger combination; CC BY-SA text and images. |
| **Slender Man** | Created by Eric Knudsen in a 2009 Something Awful photo contest; unnaturally tall, thin, featureless face, black suit and tie, sometimes extra appendages; inserted into the background of photos; power from ambiguity and no fixed canon ([Wikipedia](https://en.wikipedia.org/wiki/Slender_Man)). | **Placement over performance**: a figure found in the background of an ordinary image. A plain suit makes wrong anatomy legible. | Featureless face + black suit + extreme thinness + tendrils. It is also the "spindly" register Red rejects. |
| **Trevor Henderson** | Photobashes creatures into real photos, matching light, texture and colour; environment first, creature last; avoids teeth, angry brows and claws; aims for "slightly off proportions"; removes eyes for ambiguity; extreme scale; everyday objects repurposed as anatomy (Siren Head's sirens) ([Reactor](https://reactormag.com/artist-trevor-henderson-siren-head-interview/), [Daily Dead](https://dailydead.com/qa-trevor-henderson-discusses-the-found-footage-style-of-his-fascinating-horror-artwork/), [Wikipedia](https://en.wikipedia.org/wiki/Trevor_Henderson)). | Design **in the room's light**, test the creature as if it were photographed there. Restraint: subtle proportion errors beat fangs. An **everyday object in place of anatomy** is a strong principle. | Any specific creature (Siren Head, Cartoon Cat, Long Horse), sirens/speakers as heads, giant scale. |
| **Amnesia: The Dark Descent (Grunt)** | Brief: take something normal and twist it; humanoid because players project onto it and its walk; cartoony first concept rejected; ~10 arm iterations; crushed jaw with hanging skin, eyes pointing different ways, bandages and ropes ([Game Developer](https://www.gamedeveloper.com/art/amnesia-the-dark-descent-birth-of-a-monster-part-1-)). | Iterate the **arms and the head** most; keep the walk human. A design pass that asks "is it too cartoony?" is a real gate (Dark Deception is cartoony; FrontRooms is grounded). | The jaw, bandages and claw hands. |
| **Alien: Isolation** | Giger's design kept, legs re-jointed so the walk holds up under scrutiny; a ≈ 3 m creature; one-hit kills; director AI with a menace gauge fed by proximity, sight and **hearing it**; retreats to vents to release tension; searches in deliberately sub-optimal patterns ([Wikipedia](https://en.wikipedia.org/wiki/Alien:_Isolation), [Game Developer](https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation), [KitGuru](https://www.kitguru.net/gaming/jon-martindale/kg-talks-alien-isolation-with-creative-assembly/)). | Design the legs **for the walk cycle**; make search behaviour look like hunting; sound as part of pacing. FrontRooms' "relay when unseen" is its backstage mode. | The xenomorph head, tail and biomechanics. |
| **Iron Lung** | No windows: the player sees only low-resolution photos; a face appears in one photo and is gone in the next; the creature is seen as an eye ([Wikipedia](https://en.wikipedia.org/wiki/Iron_Lung_(video_game))). | **Partial, mediated sight**: a creature can be designed to be seen in fragments (a hand at a door edge, a head above a cubicle panel). Ambiguity between object and creature. | The sea monster, the blood ocean. |
| **The Mandela Catalogue** | Alternates are doppelgängers that reveal themselves through hijacked TV broadcasts and PSAs; the fear is replacement of the familiar ([Wikipedia](https://en.wikipedia.org/wiki/The_Mandela_Catalogue)). | **Familiar-but-replaced** and media as the reveal surface (CRTs exist in FrontRooms' Office kit). | The specific alternates, their stretched-smile faces, the PSA format. |
| **Control (the Hiss)** | Possessed co-workers float and mutter constantly ([Dread Central](https://www.dreadcentral.com/editorials/493272/monster-mania-controls-hiss-are-a-workplace-nightmare/)); the score bends tuning and overtones so the sound itself warns of evil ([Inverse](https://inverse.com/article/59452-control-video-game-petri-alanko-interview-hiss)). | **Office workers as the threat**; float/glide; a sound that detunes the environment (FrontRooms: the hum). | Red-glow possession, the floating cluster pose, the chant. |
| **Mannequin horror** | Mori's uncanny valley: the realistic prosthetic hand turns uncanny once its artificiality is noticed; movement deepens it ([IEEE Spectrum](https://spectrum.ieee.org/the-uncanny-valley)). Weeping Angels move only unobserved ([Wikipedia](https://en.wikipedia.org/wiki/Weeping_Angel)). Silent Hill 2's Mannequin rearranges human parts ([Bogleech](https://bogleech.com/halloween/hall15-silenthill2)). Fibreglass display mannequins are more realistic, plastic ones more durable ([Wikipedia](https://en.wikipedia.org/wiki/Mannequin)). Faceless "egghead" display heads spread as retailers cut display staff in the 1990s [UNVERIFIED: search snippet of a mannequin-trade blog]. | A shop dummy is a **period object of a furniture store**: seams, stands, matte fibreglass, a blank head. Its uncanniness comes from motion and from seams in the wrong place. | Spring necks, quantum-locked statues, two-pairs-of-legs. |
| **Film motion craft** | Sadako's reversed backward walk with kabuki jerks ([Academia-Lab mirror](https://academia-lab.com/encyclopedia/ringu/)); It Follows' slow, always-approaching walker hidden in backgrounds ([Den of Geek](https://www.denofgeek.com/movies/david-robert-mitchell-interview-it-follows-and-horror/)); Kayako's croak is the director's own voice ([Dread Central](https://www.dreadcentral.com/news/3275/shimizu-takashi-the-grudge/)); Javier Botet's real elongated, hypermobile body ([Wikipedia](https://en.wikipedia.org/wiki/Javier_Botet)). | Cheap motion and sound tricks beat expensive models: reversal, held poses, a steady walk, a human-made vocal. | Specific performances and sounds. |

## 4. Design levers (8–12)

Each lever is a dial a concept sets explicitly. Numbers are design targets derived in §1–§2 unless a source is given.

| # | Lever | Target / range | Why (section) |
|---|---|---|---|
| L1 | **Height and head line** | Walking top ≤ 2.05 m (shoulder or hump is the top, not the head). Face centre at **1.55–1.70 m**, on the 1.60 m sight ray. Head **at or below the shoulder line**. | Fits door, 2.4 m ceiling and window without a special stoop; keeps the face inside the 72° frame at the 0.7 m catch (needs ≤ 2.13 m); "head lower than shoulders" is a silhouette no person has (§1, §2.2). |
| L2 | **One mass, thin limbs** | One heavy block (shoulders/chest/hump/a carried load) ≈ 45–55 % of the silhouette area above the waist; limbs thinner than human. Never thin everywhere. | Cures "spindly" while keeping elongation; thin-vs-thick is a readable contrast (§2.2). |
| L3 | **One elongated segment** | Choose exactly one: forearm+hand (hands at the knee), neck, or torso. +15–30 % over a human ratio; everything else within human range. | "Slightly off" beats "obviously monstrous" (Henderson); one ratio is the identity (SCP-096) (§2.2). |
| L4 | **Silhouette test** | Must be recognisable as a black cut-out at 125 px tall (12 m), inside a 1.0 × 2.1 m lit doorway, and in a 3 m corridor under one troffer. Negative space between arms and body in the walk. | The three framings the game produces most (§2.1). |
| L5 | **Face treatment** | One of: erased by top light (brow/brim/hood/forward pitch), covered by an object, blank. No default glowing eyes. Whatever it is must say "it hears, it does not see well". | The AI hunts by noise; top light already hoods faces (§2.4, §2.7). |
| L6 | **Value blocking** | Three values: dark mass L* 15–22, mid L* 35–45, **one light element L* 70–85** above 1.5 m that faces up. Check in the Office grade (desaturated) and in mono-yellow Level 0. | The charcoal body vanishes against Office walls (1.25:1); colour will not survive the grade (§1, §2.7). |
| L7 | **Era costume as anchor** | Something an employee wore 1985–1993 (power suit in navy/charcoal, shoulder pads, white or pale shirt, tie; store blazer and name badge; guard or facilities uniform). Stiff, skinned, no cloth sim, no long hems. | Costume carries era, theme and value; the body carries the wrongness; WebGL budget (§2.5). |
| L8 | **Gait grammar per state** | Listen: frozen body, head-only motion toward the sound. Hunt (2.6 m/s): metronome walk, head locked. Chase (4.2 m/s): the gait *changes category* (drops forward, arms join, hands unclasp). BreakDoor: identical repeated blows every 0.5 s. Stagger: the only loose, organic motion. | The player must read state at 6–12 m and through walls; "wrong category" change is Dark Deception's visible state tell done with motion (§2.6). |
| L9 | **Unobserved rule** | Pose and position change only in a lamp's dark frame or off-screen; it is found again in a different pose. Ties to the existing "relay when unseen". | Weeping-Angel / Coil-head principle without their mechanic; makes the name "Relay" visible (§2.6). |
| L10 | **Sound body** | Specify the foot material (heel, toe-drag, caster), one attached rattle (keys, clip, tag), and one state sound per state; low-passed through walls as now. | Heard first, seen second; the model should explain its own Foley (§2.8). |
| L11 | **Light coupling** | Troffers react near it: strike, buzz, or drop out within ≈ one cell (3 m); the hum detunes. | Uses the per-fixture flicker system already built; warns without UI; Control's detuning principle (§2.7, §2.8). |
| L12 | **Copy-paste trait** (optional) | One deliberate duplication in the body or behaviour (two identical hands, an identical repeated blow, identical twins as a decoy). | Rhymes with the film's 20 identical sofas and 39 identical chairs (`10_synthesis.md` §0.3); the game's own visual grammar (§2.6). |

**Rig cost check.** Every lever above fits a 24–36 bone humanoid with four influences: an elongated segment is a longer bone; a hump or padded shoulders are mesh; head-lock and stutter are procedural. Only an *extra* joint (a second elbow, a reversed knee, a turned waist) adds 2–6 bones; pick at most one.

## 5. Seed concepts (5–6) for a 1990s office / furniture-store Backrooms

Original seeds for Red to pick from, each built from the levers. None takes a shape, signature part or name from the case studies; the "Resemblance risk" line says what to steer away from. Period objects: power suits and shoulder pads (1980s–early 1990s, [Wikipedia 1980s](https://en.wikipedia.org/wiki/1980s_in_fashion), [1990s](https://en.wikipedia.org/wiki/1990s_in_fashion)); the Maglite-type long flashlight, introduced 1979 for public-safety users ([Wikipedia](https://en.wikipedia.org/wiki/Maglite)); copiers, CRTs, troffers and furniture from the project's own Office kit and pile research.

### S1 — The Floor Associate *(closest to the current language; lowest risk)*
- **Anchor:** a furniture-showroom salesman: charcoal padded-shoulder blazer, pale shirt, a muted-yellow tie and a name badge with no name.
- **Tell:** forearms and hands too long (hands hang to the knee, L3); the head hangs **below the shoulder line**, bowed into the collar (L1), so at 12 m it reads as a headless boxy figure with long arms.
- **Face:** the pale bald crown catches the troffer; the face beneath is lost in top-light shadow (L5). The existing "narrow dark void" becomes that shadow, not a decal.
- **Values:** charcoal mass, pale shirt V and crown (light element), yellow tie/badge (mid).
- **Motion:** Listen: hands clasped in front, as if presenting a room; head turns only. Hunt: a measured showroom walk, hands still clasped (metronome). Chase: hands unclasp, arms swing in an over-long arc, torso pitches forward. BreakDoor: flat palms, identical shoves.
- **Sound:** hard soles muffled by carpet; the badge clip ticks on each step; a padded-jacket "whump" added in Chase.
- **Catch portrait:** the crown fills the frame, then lifts: no face, just the dark under the brow.
- **Rig:** standard humanoid, longer forearm bones, neck pitched down; no extra joints.
- **Resemblance risk:** suit + featurelessness drifts toward Slender Man; keep it heavy-shouldered, never thin, no extra limbs. Not a commuter with a briefcase (Exit 8).

### S2 — The Display Model
- **Anchor:** a matte fibreglass store mannequin with a blank egg head, dressed in an ill-fitting off-the-rack suit with a price tag still on the sleeve (muted yellow).
- **Tell:** visible **seams** at neck, elbows, wrists and waist, and one of them wrong: the waist is turned 180° while it walks, so its chest faces away while its legs come at you (inverted gait); in Chase it snaps the waist round. One leg still ends in the chrome **display-stand rod and base plate**: step-thud-scrape.
- **Face:** blank; the "face void" is the wig-socket slot across the brow, a dark seam.
- **Motion:** holds poses and snaps between them (stutter, L8); changes pose only during lamp flicker (L9).
- **Sound:** hollow fibreglass knock, joint squeak, the stand plate scraping carpet.
- **Rig:** +2 bones for a waist twist; the stand is a rigid prop on the shin.
- **Resemblance risk:** mannequin chasers exist (Lethal Company's Coil-head). No spring, no blood, no camera head, and do **not** make "freezes when watched" the rule; the sight-chase AI stays.

### S3 — The Lamp Man *(most original; uses the game's own light system)*
- **Anchor:** the building's facilities worker in grey coveralls and a tool belt, stooped as if carrying a ceiling panel.
- **Tell:** where his head should be is a **flat opal troffer lens** (0.6 × 0.6 m, the same lens as the ceiling), worn like a face. Behind the diffuser: the faint grey shadows of two tubes, or something pressed against it (the dead-lens spec already calls for two faint tube shadows).
- **Face and light:** the lens glows dimly in Listen ("it hears"), flickers in sync with real lamps in Hunt, strikes to full in Chase. It is the only **moving light** in the game: a lit panel at 1.7 m drifting through a dead cell is the 12 m read (L11).
- **Values:** dark coveralls; the lens is the light element by definition.
- **Sound:** its voice is ballast hum, pitch rising with state; tool belt rattle; lamps nearby buzz as it passes.
- **Catch portrait:** the glowing panel fills the frame with the shadow behind it.
- **Rig/budget:** standard humanoid + emissive material + one unshadowed point light.
- **Resemblance risk:** "object instead of a head" is a Henderson principle (Siren Head). Keep it flat, silent-ish, human scale, a light not a speaker; avoid TV-head tropes (it is not a screen).

### S4 — The Night Guard
- **Anchor:** a late-1980s night security guard: peaked cap, pale grey-blue uniform shirt, dark trousers, key ring on the belt, a long metal flashlight.
- **Tell:** the neck is too long and carries the head **forward and down**, like it is listening at doors (L1 + L3: head below shoulders via a forward neck). The cap brim and top light hide the face (L5).
- **Light:** the flashlight is **off** while it hunts by noise and switches on in Chase: the cone shows where it is looking (an honest telegraph of its 12 m sight ray) and is seen through doorways before the body.
- **Sound:** keys jingle in a metronome rhythm (Hunt); a radio squelch with no voice on state changes; the beam's click.
- **Rig/budget:** standard humanoid + one spot light while chasing.
- **Resemblance risk:** low; it is generic, so the forward neck and the torch behaviour have to carry it.

### S5 — The Upholstered *(furniture-store theme, pile rooms)*
- **Anchor:** from far away, a wingback/club chair: the furniture piles' own upholstery (floral or oatmeal) with button tufting.
- **Tell:** it is a person locked in a seated hunch with the chair fitted onto them: the tufted back is the hump (L2 mass), padded chair arms over the forearms, trouser legs ending in turned wooden chair feet. A head buried in the cushion; the deepest button tuft is the face void.
- **Copy-paste (L12):** same material variant as the sofas in the pile; it can stand still inside a pile and be furniture (Listen).
- **Motion:** Hunt: hunched shuffle with a wooden knock per step; Chase: lurches with the chair back rocking.
- **Sound:** wood creak, a sofa-spring twang, fabric drag.
- **Rig/budget:** standard humanoid; the chair parts are rigid props on bones.
- **Resemblance risk:** furniture-mimic monsters exist in other games; keep it a human seated pose, not a chair with teeth. Readability at 12 m is weaker than S1/S3; it is strongest as a pile-room variant.

### S6 — The Copy *(explains the name "Relay")*
- **Anchor:** a plain 1990s office worker (pale short-sleeved shirt, tie, grey slacks), and **several identical copies of him**, frozen mid-step, standing in Office rooms as static props.
- **Tell:** every copy is exactly the same, pose included (L12). The live one is the copy whose head has turned toward your last noise; when it "relays", it continues as a different copy, out of sight (L9).
- **Face:** a **photocopied face**: high-contrast black-and-white toner print with streaks, flat on the head. A face at 12 m, paper at 1 m. Ties to the Office kit's copier.
- **Values:** pale shirt + black-and-white face = the strongest read in the Office grade.
- **Sound:** a copier's scan-sweep when it relays; paper rustle in Listen.
- **Rig/budget:** one rigged instance + static mesh copies (cheap, batched).
- **Open question:** Red's Office target has a dark figure-like shape about 25 m down the corridor (`10_synthesis.md` T24, Q12). S6 would make that intentional.
- **Resemblance risk:** doppelgänger horror (Mandela Catalogue). Keep it about copies of a stranger, no stretched smiles, no broadcasts.

### Shortlist suggestion and the early-stage pre-render test

Suggested first round to pre-render: **S1** (fixes the current rig with the least change), **S3** (most original, built from the game's light) and **S6** (the clearest story for "Relay"), with S4/S2/S5 as alternates. Traits combine: S1's body with S6's photocopied face, or S4's torch on S1.

For each concept, the same five panels make the comparison fair:
1. **Proportion sheet**: front and side next to a 1.0 × 2.1 m door, a 2.4 m ceiling, the 1.60 m sight line and the 1.75 m player capsule.
2. **12 m silhouette**: black cut-out in a 3 m corridor under one troffer (≈ 11 % of frame height).
3. **Doorway**: stooped in a lit 1.0 × 2.1 m door at 3 m.
4. **Catch portrait**: 0.7 m, 72° vertical FOV, top light only.
5. **Value check**: the same figure in the Office grade (desaturated olive) and in mono-yellow Level 0.

## 6. Sources

All fetched on 2026-10-02 in this pass. Nothing was downloaded.

**Craft and theory**
- Mori, *The Uncanny Valley* (IEEE Spectrum translation) — https://spectrum.ieee.org/the-uncanny-valley
- Team Fortress 2 wiki, Art style (summarises Valve's NPAR 2007 paper) — https://wiki.teamfortress.com/wiki/Artstyle
- 80.lv, character design, shape language and readability — https://80.lv/articles/character-design-shape-language-and-readability/
- Colbor, lighting effects in film (backlight) — https://www.colborlight.com/blogs/articles/how-to-get-lighting-effects-in-film
- BFI, Gordon Willis: a career in 12 pictures — https://bfi.org.uk/features/gordon-willis-career-12-pictures

**Games**
- Dark Deception, Steam store page — https://store.steampowered.com/app/332950/
- Dark Deception: Monsters & Mortals monsters guide (GamePretty) — https://gamepretty.com/dark-deception-monsters-mortals-monsters-guide/
- Cliqist, Vince Livings interview (concept only: "first person horror Pac-Man") — https://cliqist.com/2015/01/14/dark-deception-interview/
- The Exit 8 (Wikipedia) — https://en.wikipedia.org/wiki/The_Exit_8
- Lethal Company (Wikipedia) — https://en.wikipedia.org/wiki/Lethal_Company
- Bracken (Lethal Company wiki.gg) — https://lethalcompany.wiki.gg/wiki/Bracken
- Coil-head guide (Esports Tales) — https://www.esportstales.com/lethal-company/how-to-survive-the-coil-head
- Amnesia: The Dark Descent, Birth of a Monster pt 1 (Game Developer) — https://www.gamedeveloper.com/art/amnesia-the-dark-descent-birth-of-a-monster-part-1-
- Alien: Isolation (Wikipedia) — https://en.wikipedia.org/wiki/Alien:_Isolation
- The Perfect Organism: the AI of Alien: Isolation (Game Developer) — https://www.gamedeveloper.com/design/the-perfect-organism-the-ai-of-alien-isolation
- KitGuru, Alien: Isolation interview (size only) — https://www.kitguru.net/gaming/jon-martindale/kg-talks-alien-isolation-with-creative-assembly/
- Iron Lung (Wikipedia) — https://en.wikipedia.org/wiki/Iron_Lung_(video_game)
- Control's Hiss (Dread Central) — https://www.dreadcentral.com/editorials/493272/monster-mania-controls-hiss-are-a-workplace-nightmare/
- Petri Alanko on the Hiss (Inverse) — https://inverse.com/article/59452-control-video-game-petri-alanko-interview-hiss
- The Last of Us Clickers (Dread Central) — https://www.dreadcentral.com/editorials/492187/monster-mania-in-the-last-of-us-silence-is-your-savior/
- Pyramid Head (Wikipedia; Ito's "hidden face") — https://en.wikipedia.org/wiki/Pyramid_Head
- Silent Hill 2 monsters essay (Bogleech; Ito's Lying Figure quote) — https://bogleech.com/halloween/hall15-silenthill2

**Internet horror and art**
- SCP-096 (SCP Wiki, CC BY-SA 3.0) — https://scp-wiki.wikidot.com/scp-096
- Slender Man (Wikipedia) — https://en.wikipedia.org/wiki/Slender_Man
- Trevor Henderson (Wikipedia) — https://en.wikipedia.org/wiki/Trevor_Henderson
- Trevor Henderson interview (Reactor) — https://reactormag.com/artist-trevor-henderson-siren-head-interview/
- Trevor Henderson Q&A (Daily Dead) — https://dailydead.com/qa-trevor-henderson-discusses-the-found-footage-style-of-his-fascinating-horror-artwork/
- Trevor Henderson interview (Apex Magazine) — https://www.apexbookcompany.com/blogs/apex-magazine/interview-with-artist-trevor-henderson
- The Mandela Catalogue (Wikipedia) — https://en.wikipedia.org/wiki/The_Mandela_Catalogue

**Film and folklore**
- Ringu, Sadako's reversed walk (Academia-Lab encyclopedia mirror; not in current English Wikipedia) — https://academia-lab.com/encyclopedia/ringu/
- Sadako Yamamura (Wikipedia) — https://en.wikipedia.org/wiki/Sadako_Yamamura
- Takashi Shimizu on the Grudge croak (Dread Central) — https://www.dreadcentral.com/news/3275/shimizu-takashi-the-grudge/
- David Robert Mitchell on It Follows (Den of Geek) — https://www.denofgeek.com/movies/david-robert-mitchell-interview-it-follows-and-horror/
- Javier Botet (Wikipedia) — https://en.wikipedia.org/wiki/Javier_Botet
- Weeping Angel (Wikipedia) — https://en.wikipedia.org/wiki/Weeping_Angel
- Yūrei (Wikipedia) — https://en.wikipedia.org/wiki/Y%C5%ABrei
- Mannequin (Wikipedia) — https://en.wikipedia.org/wiki/Mannequin

**Period**
- 1980s in fashion (Wikipedia) — https://en.wikipedia.org/wiki/1980s_in_fashion
- 1990s in fashion (Wikipedia) — https://en.wikipedia.org/wiki/1990s_in_fashion
- Maglite (Wikipedia) — https://en.wikipedia.org/wiki/Maglite

**UNVERIFIED (search snippets only; do not cite in a deck without a fetch)**
- The Ito 2001 making-of quote about creatures read as people in fog, then undermined by strange movement and angles.
- Dark Deception's chapter-1 monkeys as hotel bellhops, reportedly inspired by a film poster (fan wikis returned 402/403).
- Amnesia's water monster as the one monster players never see (USgamer returned 503).
- Faceless "egghead" mannequins spreading in the 1990s as retailers cut display staff (mannequin-trade blog did not render).
- Price-labelling guns sold since at least 1971 (retailer page returned 403); not used in the seeds.

**Project files read**
`Documentation/RELAY_MODEL_RIG_RESEARCH.md`, `Documentation/LEVELS_AND_ENTITIES.md`, `Documentation/LEVEL_MODULE_SPEC.md` (§2–§8), `Documentation/VISUAL_RESEARCH_LOOKDEV.md`, `Documentation/research/office_and_film/10_synthesis.md` (§0, §6), `Assets/Scripts/FrontRoomsMap/FrontRoomsMapHunter.cs`, `Assets/Scripts/FrontRoomsRelayRig.cs`, `Assets/Scripts/FrontRoomsHunter.cs` (tuning), `Assets/Scripts/FrontRooms3DGame.cs` (rig hookup), `Assets/Scenes/FrontRooms3D.unity` (serialized Hunter transforms).
