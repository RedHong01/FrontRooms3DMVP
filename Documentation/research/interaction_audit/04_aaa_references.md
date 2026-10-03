# 04 — AAA and horror reference: how first-person games present interactions

Scope: reference research for FrontRooms' interaction "shots" (key use on doors, glass break and window vault, hold-to-act, first-person camera language, short in-engine cinematic moments). Ends with three alternative interaction camera languages for FrontRooms.

## 0. Status / progress log

- 2026-10-02 — file created; code anchors verified; web research in progress.
- 2026-10-02 — first batch of sources read (Alien: Isolation, Outlast, Frictional, Dead Space, Mirror's Edge, Dying Light, Half-Life: Alyx, Nesky, Eiserloh, accessibility, Unity WebGL).
- 2026-10-02 — second batch (RE7, SOMA, Outlast preview, TLOU2 glass, Unrecord, Blair Witch, cutscene sources); catalogue §3 and the three languages §4 written. Status: complete draft; §5 lists what stays UNVERIFIED.

## 1. What FrontRooms does today (code anchors, verified 2026-10-02)

Line numbers were re-checked at the end of this pass on 2026-10-02. Both files were being edited by the map chat while this was written (numbers moved by ~9 lines between two reads), so the symbol name is the stable anchor.

| Interaction | What the code does | Anchor |
|---|---|---|
| Aim | A ray from the camera, 2.4 m reach, picks the collider; `Describe` returns a text prompt | Assets/Scripts/FrontRooms3DGame.cs:149 (`Reach`), :932-938 (`UpdateAim`); Assets/Scripts/FrontRoomsMap/FrontRoomsMapWorld.cs:1503-1520 (`Describe`) |
| Door | `E` press calls `Use`: if locked and no zone key, raises `DoorLocked` (sound only) and returns; otherwise the leaf swings away from the player | FrontRooms3DGame.cs:952; FrontRoomsMapWorld.cs:1522-1532 (`Use`) |
| Door motion | Hinge rotation eased with smoothstep over 0.55 s (0.18 s when broken). No hand, no camera move, no key visible | FrontRoomsMapWorld.cs:1587-1598 (`TickDoors`) |
| Locked prompt | Text only: "LOCKED · NEEDS THIS ZONE'S KEY" | FrontRoomsMapWorld.cs:1512 |
| Key pickup | Walk within 0.9 m of a spinning cube; it is destroyed and `KeyTaken` fires; HUD flashes "KEY / OPENS THIS ZONE'S DOORS" | FrontRoomsMapWorld.cs:1601-1616 (`CollectKeys`); FrontRooms3DGame.cs:789 (`OnKeyTaken`) |
| Key look | Emissive yellow URP/Lit material named "Map test / key" | FrontRoomsMapWorld.cs:1658 |
| Key use | None. Owning the zone key just makes `E` open the door. The key object never appears again | FrontRoomsMapWorld.cs:1582 (`HasKeyHere`), :1522-1532 |
| Glass hold | Hold `E` for 1.0 s; progress feeds a 120 x 4 px HUD bar | FrontRoomsMapWorld.cs:1560-1572 (`Hold`); FrontRooms3DGame.cs:957, :1532-1533 |
| Glass break | At 1.0 s the pane object is destroyed (`Kill` = `Destroy`) and `GlassBroken` fires: Foley, a 40 m noise for the hunter, a HUD flash "GLASS BROKEN / WALK INTO THE FRAME TO CLIMB THROUGH". No shards, no crack stage, no camera response | FrontRoomsMapWorld.cs:478-482, :1570-1571; FrontRooms3DGame.cs:149, :781-785 (`OnGlassBroken`) |
| Window vault | Walk into a broken frame: 0.6 s lerp, 0.35 m lift, camera ducks 0.55 m on a sine arc. No input lock beyond the climb itself, no hands | FrontRooms3DGame.cs:154, :886-929 (`TryStartClimb`, `Climb`) |
| Glass material | URP/Lit transparent, premultiplied, smoothness 0.9, base (.75,.85,.88,.28); built in code | FrontRoomsMapWorld.cs:1659, :1662-1677 (`TransparentGlass`) |
| Camera | FOV 76; no head-bob code in FrontRooms3DGame.cs (grep "bob" = no hits); pitch clamp ±75° | FrontRooms3DGame.cs:226, :812, :827 |
| Film look | Global URP volume: ACES, halation, green-yellow WB, lifted blacks, grain, lens falloff; no post AA (4x MSAA in pipeline) | Assets/Scripts/Rendering/FrontRoomsPostStack.cs:5-10, :72 |
| Platform | Per-platform default quality: WebGL = 3 (High), Standalone = 5 (Ultra); no explicit graphics API list, so the WebGL build uses Unity's default WebGL2 (WebGPU is experimental in 6000.3, S21) | ProjectSettings/QualitySettings.asset:338-339; ProjectSettings/ProjectSettings.asset:543 |
| Hook points | The map already raises `DoorMoved`, `GlassBroken`, `DoorBroken`, `KeyTaken`, `GlassHold(progress)`, `GlassHoldReleased`, `DoorLocked`; the sound director subscribes to them. A shot system can subscribe the same way, but a key-insert shot must also delay the door until the shot ends, which is a change inside `Use` | FrontRoomsMapWorld.cs:59-71; Assets/Scripts/Audio/FrontRoomsSoundDirector.cs:389-390, :443 |
| Engine modules | The manifest lists no Animation module (Animator, AnimationClip), no Particle System module, no Timeline and no Cinemachine. The Relay rig is driven in code "No Animator component" | Packages/manifest.json:1-13; Assets/Scripts/FrontRoomsRelayRig.cs:137-139 |

Summary of the gap: every interaction is resolved by a HUD string plus a sound. There is no "shot": no hand, no key object, no camera move, no glass debris, no crack stage. The window vault is the only camera motion.

## 2. Sources read

All URLs below were opened and read on 2026-10-02 unless marked UNVERIFIED. Several PC Gamer pages returned only their header to the fetch tool; they are not cited.

| # | Source | URL | Used for |
|---|---|---|---|
| S1 | Wikipedia, Alien: Isolation | https://en.wikipedia.org/wiki/Alien:_Isolation | 3 s save pause; animations re-recorded through VHS/Betamax and a portable TV; rule against anything a 1979 film crew could not have built as a prop |
| S2 | Game Developer, "How Creative Assembly brought fear to Alien: Isolation" (Alistair Hope, GDC 2015) | https://gamedeveloper.com/design/how-creative-assembly-brought-fear-to-i-alien-isolation-i- | first person vs third person; lo-fi tech as design |
| S3 | Xbox Wire, gamescom 2014 Alien: Isolation (Jon Rooke) | https://news.xbox.com/en-us/?p=11775 | key-card save that takes seconds; auto-save kills tension |
| S4 | Steam forum thread on the maintenance-jack animation | https://steamcommunity.com/app/214490/discussions/0/600766503721133225 | jack animation: view on the bolt, rod withdraws, heave; player report only |
| S5 | Wikipedia, Outlast | https://en.wikipedia.org/wiki/Outlast | vault, climb, hide; camcorder night vision drains batteries; UE3, 10 people, 14 months; found-footage film influences |
| S6 | Dread Central review of Outlast (Gareth Jones, 2013-09-10) | https://www.dreadcentral.com/reviews/47973/outlast-video-game/ | head bob, visible feet, hand resting on walls to peek; night-vision click and wind-up |
| S7 | GamingBolt interview with Philippe Morin (Red Barrels), 2013-07-12 | https://gamingbolt.com/outlast-interview-with-red-barrels-ps4-version-gameplay-details-indie-gaming-and-more | recording gives notes; team's AAA background |
| S8 | Wikipedia, Amnesia: The Dark Descent | https://en.wikipedia.org/wiki/Amnesia:_The_Dark_Descent | mouse imitates the motion of doors and levers |
| S9 | Wikipedia, Penumbra: Overture | https://en.wikipedia.org/wiki/Penumbra:_Overture | doors, drawers, switches opened with real-world motions |
| S10 | Game Developer, Dino Ignacio Dead Space UI talk (GDC 2013) | https://gamedeveloper.com/design/video-designing-i-dead-space-i-s-immersive-user-interface | diegetic UI on the RIG suit |
| S11 | HUDs and GUIs, Dead Space 2 diegetic interface (Jono Yuen, 2012) | https://www.hudsandguis.com/2012/08/22/dead-space-2-diegetic-interface-design | health on the spine; definition of diegetic |
| S12 | GDC Vault, "Creating First Person Movement for Mirror's Edge" (Dahl, Lagre, DICE) | https://gdcvault.com/play/1012171/Creating-First-Person-Movement-for | full-body first person; animation pipeline |
| S13 | Game Anim blog on the Mirror's Edge talk | https://www.gameanim.com/?p=2058 | mocap head camera failed; hand-keyed camera won |
| S14 | MCV/Develop, "The vaulting dead" (Binkowski, Kulon, Techland, 2016-05-18) | https://www.mcvuk.com/development-news/the-vaulting-dead-implementing-first-person-parkour-in-dying-light/ | arms and occasional feet only; GoPro reference; motion-sickness tuning; input delay at ledges |
| S15 | Game Informer, Valve on Half-Life: Alyx hands (Walker, Kinley, 2020-03-23) | https://www.gameinformer.com/index.php/interview/2020/03/23/valve-talks-half-life-alyx-and-why-arms-dont-work-in-vr | hands only, no arms; wrong arms "stand out" |
| S16 | Game Developer, John Nesky "50 Game Camera Mistakes" (GDC 2014) | https://gamedeveloper.com/design/video-50-common-game-camera-mistakes----and-how-to-fix-them | shake, FOV shifts, walk bounce, taking control |
| S17 | GDC Vault, "50 Camera Mistakes" description | https://gdcvault.com/play/1020460/50-Camera | sim sickness, line-of-sight failures |
| S18 | Game Developer, Squirrel Eiserloh "Juicing Your Cameras With Math" (GDC 2016) | https://gamedeveloper.com/programming/video-sprucing-up-cameras-with-math | screen shake as information; trauma/noise details are from secondary implementations (UNVERIFIED against the talk itself) |
| S19 | Game Accessibility Guidelines, camera vs controller movement | https://gameaccessibilityguidelines.com/avoid-or-provide-option-to-disable-any-difference-between-controller-movement-and-camera-movement/ | head bob, shake, tilt, forced look need a toggle |
| S20 | Game Accessibility Guidelines, holding buttons | https://gameaccessibilityguidelines.com/avoid-provide-alternatives-to-requiring-buttons-to-be-held-down/ | hold-to-act needs a toggle alternative |
| S21 | Unity 6.3 manual, WebGL graphics | https://docs.unity3d.com/6000.3/Documentation/Manual/webgl-graphics.html | WebGPU "experimental" in 6000.3 |
| S22 | Unity manual, Web graphics APIs intro | https://docs.unity3d.com/6000.7/Documentation/Manual/web-graphics-apis-intro.html | WebGL2: compute shaders not natively supported |
| S23 | VFX Graph 17.3 system requirements | https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.3/manual/System-Requirements.html | VFX Graph needs compute shaders and SSBOs |
| S24 | Inverse, RE7 teaser impressions (Steve Haske, 2016-12-05) | https://www.inverse.com/article/24710-resident-evil-7-beginning-horror-impressions | doors as tension; no mechanics detail |
| S25 | Twinfinite, E3 2016 RE7 preview (Zhiqing Wan, 2016-06-19), read in the browser pane | https://twinfinite.net/features/e3-2016-resident-evil-7-preview/ | press to open: door creaks and stays ajar; walk forward to push it fully open |
| S26 | PC Gamer, "Why I love watching my hands in first-person games" (Tom Senior, 2017-01-25), browser | https://www.pcgamer.com/why-i-love-watching-my-hands-in-first-person-games/ | RE7 hands press on walls; hand animations as "a little cutscene"; Alien: Isolation balance |
| S27 | PC Gamer, "The weighty doors and switches of Soma" (Tom Senior, 2015-10-07), browser | https://www.pcgamer.com/the-weighty-doors-and-switches-of-soma/ | grab-and-drag; object lags the cursor for weight; doors drift after release |
| S28 | PC Gamer, Outlast preview (Cassandra Khaw, 2013-03-29), browser | https://www.pcgamer.com/outlast-preview/ | Mirror's Edge influence; hands and feet so players feel they have a body; "normal camcorder" rule; broken-lens tests |
| S29 | Geek Culture, Outlast PS4 review (2014-02-15) | https://geekculture.co/geek-review-outlast-playstation-4 | doors: smash open with noise, or creak open slowly |
| S30 | Game Developer, "Resident Evil — Loading Screens and Doors" (Stephen Trinh, 2020-03-04) | https://www.gamedeveloper.com/design/resident-evil---loading-screens-and-doors | the classic first-person door cutaway hid loading and built tension |
| S31 | BFI, "Half-Life 2: 20 years" (Jacob Heayes, 2024-11-15) | https://www.bfi.org.uk/features/half-life-2-20-years-valve-shooter | control is never taken away in HL2 |
| S32 | Game Anim, "Cinematics Sans Cutscenes" (Jonathan Cooper, 2010-04-23) | https://www.gameanim.com/?p=1081 | cutscenes as "imposed cinematography" |
| S33 | GamingBolt, Cyberpunk 2077 cutscenes (John Mamais, 2019-10-15) | https://gamingbolt.com/cyberpunk-2077-developer-talks-about-the-games-interactive-and-fully-immersive-cutscenes | first-person cutscenes where you keep camera or character control |
| S34 | 80.lv, Naughty Dog on The Last of Us Part II's world | https://80.lv/articles/how-naughty-dog-created-the-immersive-world-of-the-last-of-us-part-ii/ | breakable glass: shards built from a texture, "fractal glass shader" for cracks; sound, lighting and FX complete the effect |
| S35 | Wikipedia, Tempered glass | https://en.wikipedia.org/wiki/Tempered_glass | tempered = small granules; annealed = large jagged shards; codes require tempered near doors |
| S36 | Envato Tuts+, shatter an object in Unity | https://code.tutsplus.com/how-to-make-an-object-shatter-into-smaller-fragments-in-unity--gamedev-11795t | swap the intact mesh for a pre-fractured prefab with rigidbodies; delete pieces after seconds |
| S37 | PC Gamer, Unrecord announcement (Tyler Wilde, 2023-04-20), browser | https://www.pcgamer.com/unrecord-announcemen/ | bodycam look: free hand movement, lens distortion, interlacing; motion-sickness options planned |
| S38 | TechRaptor, Bloober Team interview (Maciek Glomb), browser | https://techraptor.net/gaming/interview/we-spoke-to-bloober-team-about-blair-witch-bullet-and-their-approach-to-horror | camcorder was essential; tape playback alone was not engaging, so rewind/fast-forward changes the world |
| S39 | Wikipedia, Backrooms (web series) | https://en.wikipedia.org/wiki/Backrooms_(web_series) | found footage, Blender + After Effects, 1990s |
| S40 | Wikipedia, The Order: 1886 | https://en.wikipedia.org/wiki/The_Order:_1886 | permanent 2.40:1 letterbox "to make it more cinematic" |
| S41 | Wikipedia, Standard-definition television | https://en.wikipedia.org/wiki/Standard-definition_television | SD video was 4:3 before widescreen |
| S42 | Wikipedia, Amnesia: The Bunker | https://en.wikipedia.org/wiki/Amnesia:_The_Bunker | dynamo flashlight makes noise; wrist watch shows generator fuel |
| S43 | Wikipedia, Mirror's Edge | https://en.wikipedia.org/wiki/Mirror%27s_Edge | visible limbs; centre dot to reduce simulation sickness |
| S44 | Unity manual, Render Objects renderer feature | https://docs.unity3d.com/Manual/urp/renderer-features/renderer-feature-render-objects.html | draw a layer with its own camera FOV/offset (viewmodel) |
| S45 | Cinemachine 3.1 manual, Impulse | https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/CinemachineImpulse.html | event-driven camera shake source/listener |
| S46 | Bevy example, 2D screen shake | https://bevy.org/examples/camera/2d-screen-shake/ | secondary summary of Eiserloh: shake grows with trauma, trauma decays, noise keeps it smooth |

Not reachable: Valve Developer Wiki (func_breakable_surf) sits behind a bot check, so Half-Life 2's pane-glass system is not cited. Fandom (Alien, RE wikis) returned 402/403 to the fetch tool; the RE Village key page loaded in the browser but its "Usage" screenshots could not be viewed, so the RE Village key-insert shot is UNVERIFIED.

## 3. Technique catalogue

Each entry says what the technique is, who uses it (source numbers from §2), what it costs to build, whether it fits FrontRooms (found footage, camcorder-like camera, 1990, the Relay hunting by noise), and what it costs on WebGL. "Fit" and "cost" lines are my judgement unless they carry a source. Cost words: **low** = code and a few assets, no new rig; **medium** = new authored assets or a physics setup, no character rig; **high** = a rigged, animated viewmodel.

### 3.1 Key and item use on doors

**K1. Binary door plus HUD text (FrontRooms today).** The key is an emissive cube you walk over; owning it makes `E` open the zone's doors; "LOCKED" is a text string (§1). Nobody in the reference set does this for a key moment. It is the reason Red sees "no shot".

**K2. The classic Resident Evil door cutaway.** A first-person, non-interactive shot of a door opening that played on every room change. It hid loading and built dread about the next room (S30). Cost: low per door type (one authored camera path, one door animation). Fit: strong for the camcorder idea if it is framed as a camera move, weak if it is a hard cut, because FrontRooms never loads rooms behind a door; the cut would be decoration. WebGL: free.

**K3. Resident Evil 7: "ajar, then push".** Pressing the button unlatches the door; it creaks and stays slightly open; the player must walk into it to push it fully open, and gets only a glimpse first (S25). It keeps control with the player and turns every door into a peek. Cost: low. The leaf angle follows the player's push instead of a fixed 0.55 s tween (FrontRoomsMapWorld.cs:1587-1598). Fit: very high. It pairs with Outlast's two door speeds, "smash the door open and make noise" or creak it slowly (S29), which maps straight onto the Relay noise call FrontRooms already makes for doors (`OnDoorMoved`, FrontRooms3DGame.cs:774-777). WebGL: free.

**K4. Alien: Isolation: the view goes to the device.** Tool moments (maintenance jack, locks, terminals) briefly frame the object. A player report on the jack describes the rod withdrawing and the view moving off the bolt afterwards (S4, a forum post, so the exact framing is UNVERIFIED beyond that). Saving takes a key card and a fixed three-second pause during which you can be killed (S1, S3). PC Gamer calls Alien's mix the balance point: its locks and terminals ask for small manual actions, so you feel you do the work yourself (S26). Creative Assembly's rule that lo-fi tech "isn't the answer" (S2) is close to FrontRooms' 1990 brief. Cost: medium (a framing anchor per device type, device animation; hands optional). Fit: high. WebGL: cheap if the device moves and the hands do not.

**K5. Hands-visible key insert (Resident Evil 7 / Village style).** RE7's hands react to the world: they press against walls and rise to block (S26). The key-insert shot in Village is UNVERIFIED in this pass (the wiki screenshots could not be viewed). Cost: high. It needs a hand rig, one clip per lock type, and the lock at a predictable height (the module spec helps, because doors are modular). Fit: good for "AAA". It risks the problem Valve describes for arms in VR, where wrong proportions "stand out" (S15). WebGL: one skinned mesh is affordable; the bigger cost is adding the Animation module, which is not in the project (Packages/manifest.json:1-13).

**K6. Frictional physics doors (Penumbra, Amnesia, SOMA).** Doors, drawers and levers follow mouse motions that imitate the real motion (S8, S9). The grabbed object lags the cursor, which reads as weight, and a released door drifts on (S27). Cost: medium (hinge joints, a grab mode, gamepad mapping). No animation needed. Fit: good for dread, but it fights the chase pacing of the Relay and replaces the current one-key control scheme. WebGL: fine for a handful of hinge joints.

**K7. Diegetic lock state (Dead Space lineage).** Dead Space moved health, ammo and inventory onto the suit and into the world to remove the "wall" between player and game (S10, S11). For a 1990 office: a brass deadbolt that is visibly thrown, a chain, a red/green keypad LED, a paper "KEY AT FRONT DESK" tag. Then "LOCKED" needs no HUD text, and a locked rattle can show the bolt. Cost: low (props in the visual chat's kit). Fit: very high. WebGL: free.

### 3.2 Glass breaking and windows

**G1. Pane removal (FrontRooms today).** At 1.0 s the pane is destroyed (FrontRoomsMapWorld.cs:1570). No crack, no shard, no camera response.

**G2. Crack stages before the break.** In The Last of Us Part II, breakable glass was new. Artists built the shards from a texture, and a "fractal glass shader" drew the cracks (S34). The team adds that sound, lighting and FX are needed to complete the effect (S34). Glass that cracks first can show hold progress instead of a HUD bar (see H2). Cost: low to medium (a radial crack mask, or 3 crack decals, driven by `GlassHold(progress)`, FrontRoomsMapWorld.cs:67). Fit: very high. WebGL: one extra texture sample on the pane.

**G3. Pre-fractured swap.** At the break, swap the pane for a prefab of pre-cut shards with rigidbodies and delete them after a few seconds (S36). Leave jagged "teeth" in the frame so the opening still reads as broken glass. Cost: medium (one fracture per pane size in Blender, which is already in the visual chat's tools). Physics is installed (Packages/manifest.json:6). Fit: very high. WebGL: keep the shard count low and let them sleep. My estimate is 12 to 30 pieces; each is a transparent draw, and overdraw is the real cost.

**G4. Runtime procedural fracture** (CryEngine-style breakable glass, store assets). Cost: high. Not needed for one pane size.

**G5. Choose the glass type on purpose.** Tempered glass breaks into small granular chunks; annealed (ordinary plate) glass breaks into large jagged shards. US codes require tempered or laminated glass near doorways and in large or low windows (S35). An interior office sidelight next to a door would be tempered, a 1990 partition window may be plate. Pick one per window type, because it sets the debris art. Fit: realism Red will recognise. Cost: none, a decision.

**G6. Vault through with a body.** Outlast lets you vault and climb (S5). Its team took visible hands and feet from Mirror's Edge so players feel they have a body, not a floating camera (S28). Dying Light shows arms and occasional feet, studied GoPro footage from traceurs, and tuned animation speed to limit motion sickness (S14). Mirror's Edge shows arms and legs to convey movement (S43). DICE tried a camera on a motion-captured head, which failed; hand-keyed camera animation won (S13). FrontRooms' 0.6 s duck arc (`ClimbSeconds`, FrontRooms3DGame.cs:154; `Climb`, :916-929) is the camera half of this; the hands on the sill are missing. Cost: medium (camera only, tune the arc) to high (hands on the frame). Fit: high. WebGL: free for the camera; one clip for hands.

**G7. After the break.** Shards that crunch underfoot are reported for TLOU2 in a search summary only (UNVERIFIED). In FrontRooms the break already makes a 40 m noise for the hunter (`GlassNoiseRadius`, FrontRooms3DGame.cs:149; `OnGlassBroken`, :784). A floor shard decal plus a crunch event would let the broken window keep "talking" to the AI. Cost: low.

### 3.3 Hold-to-act without UI

**H1. HUD progress bar (FrontRooms today).** 120 x 4 px, shown while held (FrontRooms3DGame.cs:1532-1533). It works but is the least diegetic option.

**H2. The object shows the progress.** Cracks grow (G2); the door opens wider the more you push (K3, K6); Alien's save asks for a key card and a fixed wait (S1, S3); Amnesia: The Bunker's flashlight is a dynamo you crank, and the cranking makes noise (S42); the same game's wrist watch shows generator fuel (S42). Cost: low. Fit: very high.

**H3. Strikes instead of one hold.** Break the glass in two or three strikes. Each strike adds a crack stage, a small camera shake and a noise ping for the Relay. A trauma-style shake (shake grows with trauma, trauma decays, noise keeps it smooth) is the common recipe from Eiserloh's GDC talk (S18; recipe as summarised by S46). Cost: low. Fit: high, and it gives the sound chat discrete hits to score.

**H4. Accessibility.** Holding buttons is hard for many players, so offer a toggle (S20). H3 avoids the problem, because strikes are presses.

### 3.4 First-person camera language

**C1. Take the camera or keep it.** Half-Life 2 never takes control away (S31). Cyberpunk 2077 keeps cutscenes first person and lets you control "the character or the camera" (S33). Jonathan Cooper calls cutscenes "imposed cinematography" (S32). PC Gamer notes that elaborate hand animations put "a little cutscene" between player and object (S26). Practical reading: for a hunted player, keep the takeover short and partial: lock movement, keep some look, end early if the hunter arrives.

**C2. FOV push-in.** Nesky's camera talk covers rapidly shifting field of view, excessive shake and walk-cycle bounce among its mistakes (S16; the full list of 50 is not on the pages read). A push-in should be a slow eased dolly of the camera position, or a slow lens zoom, not a fast FOV pop. A camcorder zoom is the in-fiction excuse for a slow zoom (see language C).

**C3. Head-bob.** Outlast bobs the view and shows the feet (S6). Accessibility guidance lists head bob, camera shake, tilt and forced look changes as sickness triggers that need a toggle (S19). FrontRooms has no bob today (§1). A handheld camcorder would sway slightly; give it a toggle.

**C4. Hands and viewmodel.** The range runs from hands only with no arms (Half-Life: Alyx, S15), to arms with occasional feet (Dying Light, S14), hands and feet (Outlast, S28), and full body (Mirror's Edge, S12, S43). In URP, a Render Objects renderer feature draws a layer with its own camera FOV and offset, the usual way to keep held objects from clipping into walls (S44).

**C5. Camera shake.** Shake carries information (S18). Unity's Cinemachine Impulse is the packaged source/listener version (S45), but Cinemachine is not installed (Packages/manifest.json:1-13). A 30-line noise shake in the existing camera code is cheaper on WebGL than adding the package (my estimate).

**C6. Centre dot.** Mirror's Edge added a small centre reticle to reduce simulation sickness from free camera movement (S43).

### 3.5 Short in-engine moments: duration, input lock, letterbox

- **Durations on record.** Alien's save waits 3 s (S1). FrontRooms: door 0.55 s, glass hold 1.0 s, vault 0.6 s (§1). I found no published durations for key-insert shots; the proposals in §4 are my estimates.
- **Input lock.** Options: none (HL2, S31); partial, look kept (Cyberpunk, S33); full for a short device moment (Alien jack and save, S1, S4). The save shows a full lock can itself be the horror: the player is stuck while the threat can still arrive (S1, S3).
- **Letterbox.** The Order: 1886 used a permanent 2.40:1 frame "to make it more cinematic" (S40). Letterbox says "film". FrontRooms says "tape": 1990 video was 4:3 (S41). If a moment needs a frame change, narrowing to a 4:3 viewfinder (pillarbox) is the period-correct move, not letterbox bars.
- **Analog treatment.** Alien re-recorded its animations to VHS and Betamax and filmed them on a portable TV while adjusting tracking, so the distortion was real, not a filter (S1). Outlast's rule: only what "a normal camcorder" can do; they tested a broken lens and broken-glass effects (S28). Unrecord sells its look with lens distortion, interlacing and free hand movement, and plans motion-sickness options (S37). Blair Witch found that tape playback alone was not engaging and tied the camcorder to world changes (S38). The Kane Pixels series is found footage built in Blender and After Effects (S39). FrontRooms' own research says to reserve VHS-style damage for camcorder moments (Documentation/research/office_and_film/01_film_production.md:199).

### 3.6 "AAA" against the WebGL target, honestly

- The references above run on console and PC. FrontRooms' WebGL build uses WebGL2 (§1). WebGL2 does not natively support compute shaders (S22); VFX Graph requires compute shaders and SSBOs (S23); WebGPU is experimental in Unity 6000.3 (S21). So GPU particles and compute-driven effects are out on the web build.
- The project also lacks the Animation and Particle System modules (Packages/manifest.json:1-13). Every language below that uses an Animator or Shuriken particles must add a module, which grows the WebGL download (size UNVERIFIED; measure with a build).
- What makes these references read as AAA is mostly timing, framing, sound and debris that persists: RE7's ajar door, Alien's device framing, TLOU2's crack-then-shatter, Outlast's body. None of that needs features WebGL lacks. This is my reading of the sources, not a quote. The render-quality side (glass shading, reflections, quality tier) is covered in 02_glass_and_breakables.md and 03_rendering_quality.md.

## 4. Three interaction camera languages for FrontRooms

All three share K3 (ajar, then push), K7 (diegetic lock state), G2 (crack stages), G3 (pre-fractured shards) and G5 (a chosen glass type). They differ in who performs the action on screen. Durations are proposals.

### A. "Hands in frame": a diegetic hands-only viewmodel

What the player sees:
- **Key:** Approach a locked door; the bolt is visibly thrown (K7). Press E. Movement locks, look stays in a cone of about ±15°. The right hand brings the brass key up from the lower frame, inserts it and turns it a quarter, the bolt clicks back, and the door pops ajar. The hand withdraws and control returns (about 1.4 s); the player pushes through (K3).
- **Glass:** Wrap a sleeve over the fist, or pick up a held object (a desk stapler, a fire extinguisher). Two or three strikes (H3): each one is a short hand clip, a crack stage, a small shake and a noise ping. The last strike shatters the pane into a shard prefab.
- **Vault:** Both hands plant on the sill, then the existing duck arc plays (about 0.8 s).
- **Key pickup:** The hand closes on the key; a 0.4 s glance at it in the palm.

References: RE7 hands (S26), Half-Life: Alyx hands only (S15), Dying Light (S14), Outlast (S28), Mirror's Edge (S12, S13).
Pros: the strongest "AAA" read in one still frame; the player has a body; matches what Red named ("the camera pushes in to the key opening the door").
Cons: the highest cost and risk. Bad hands look worse than none (S15). Every door and window needs a matching hand target. Long clips become "little cutscenes" while a hunter is near (S26).
Cost: high. One rigged hands-and-forearms mesh (sleeves in 1990 clothing). About 8 to 10 clips (idle, key insert/turn, locked rattle, strike x2, sill plant, pickup, wall-touch). A viewmodel layer with a Render Objects pass (S44). Add the Animation module. Map chat: an interaction state machine that holds the door until the clip ends. Visual chat: the rig, the clips, the viewmodel pass. Sound chat: per-clip events.
WebGL: moderate. One skinned mesh and a few clips is fine. Module size and CPU skinning cost are UNVERIFIED until measured.

### B. "The object is the actor": camera push-ins, animated objects, no hands

What the player sees:
- **Key:** Press E. Movement locks; the camera eases 0.25 s toward a framing anchor on the lock (a position dolly, FOV unchanged or narrowed slowly, per C2). The key model slides into the lock from below frame, turns with a click, the bolt retracts, and the door pops ajar about 10°. The camera eases back and control returns (about 1.2 s total); the player pushes the door the rest of the way (K3). A fast push slams the door (loud noise to the Relay); a slow push creaks it (S29).
- **Locked, no key:** A short 0.3 s rattle: the handle jiggles and the visible deadbolt holds (K7). No HUD text.
- **Glass:** Strikes or a hold, each step growing the crack mask (G2, H2/H3) with a small shake (C5). On the break, the pre-fractured swap (G3), a dust puff, and teeth left in the frame.
- **Vault:** The existing camera arc (`Climb`, FrontRooms3DGame.cs:916), plus a slight roll and a shard crunch on landing.
- **Key pickup:** The key lifts toward the camera and holds for 0.4 s in front of the lens, then leaves.

References: Frictional's handless physical interaction (S8, S9, S27), Alien's device framing (S4, S26), RE7's ajar door (S25), TLOU2 glass (S34), Half-Life 2's no-takeover rule as the limit (S31).
Pros: cheapest and safest. It extends what the code already does (procedural hinges and climb, a code-driven rig per FrontRoomsRelayRig.cs:137-139). No Animation module. It reads well on WebGL. Every shot can be cancelled when the Relay appears.
Cons: it can feel telekinetic. PC Gamer credits handless, telekinetic interaction with a more direct link to the world (S26), but also jokes that drag-to-open can look like waving a door open from a distance (S27). A single still frame reads less "AAA" than hands. The push-in alone can feel like a UI zoom unless sound and object motion carry it.
Cost: low to medium. Map chat: framing anchors per door and window type, a short interaction state (lock move, keep look), crack-stage driver, push-to-open door. Visual chat: key model, lock and deadbolt props, crack masks, fractured pane prefabs. Sound chat: key-in, turn, bolt, rattle, strike, shatter, crunch.
WebGL: low. Shards are the only real cost (G3).

### C. "Camcorder grammar": the player is the camera operator

What the player sees: the same object actions as B, but every camera move is something a 1990 camcorder or its operator could do (S28's "normal camcorder" rule).
- **Key:** Instead of a dolly, the autofocus hunts and racks to the lock and the operator nudges the zoom in. One hand enters from the lower frame with the key; it is the free hand, because the other holds the camera (a one-handed rig halves A's clip count). The door pops ajar. The autofocus racks back to the room.
- **Glass:** Each strike jolts the frame (an exposure pump from the camera's auto gain, a tiny vertical-hold slip). The break gets a two-frame tracking tear and a burst of noise in the audio track. Shards fall in the clean picture that follows.
- **Vault:** The frame tilts and drops as the operator climbs one-handed; the picture briefly loses focus.
- **Locked:** A short zoom on the deadbolt; the timecode keeps running.
- **Frame:** Gameplay stays full-screen. Only these moments narrow to a 4:3 viewfinder (S41), never letterbox (S40).

References: Outlast's camcorder and its broken-lens tests (S5, S28), Alien's real VHS re-recording (S1), Unrecord's lens distortion, interlacing and free hand (S37), Blair Witch's camcorder as a mechanic (S38), Kane Pixels (S39), FrontRooms' own advice to keep VHS damage for camcorder moments (01_film_production.md:199).
Pros: the most on-brand for a found-footage Backrooms game set in 1990. It gives FrontRooms a signature instead of copying RE7. Analog damage hides the WebGL fidelity ceiling (Alien used real analog distortion as a style, S1).
Cons: if overused it looks like low quality, which is Red's current complaint. Shake, blur and tears are listed sickness triggers that need toggles (S19). It needs a design call on whether the player is "holding a camera" all game (HUD, REC, battery?), which touches the title and the post stack.
Cost: medium. Everything in B, plus camcorder moves: autofocus rack (URP depth of field), zoom, exposure pump (post exposure), a tracking-tear overlay, and an optional one-handed rig (medium to high). Visual chat owns the post work (FrontRoomsPostStack.cs). Map chat triggers it from the same events.
WebGL: low to medium. Depth of field and a full-screen overlay pass for under a second are affordable. Keep tears to a few frames.

### Comparison

| | A. Hands in frame | B. Object is the actor | C. Camcorder grammar |
|---|---|---|---|
| Reads as "AAA" in a still | Highest | Lowest of the three | Medium; high in motion |
| Fits found footage / 1990 | Neutral | Neutral | Highest |
| Keeps control near the hunter | Weakest (clips) | Strongest (cancellable) | Strong |
| Build cost | High | Low–medium | Medium (+ optional one hand) |
| New engine modules | Animation | None (physics only) | None, or Animation if a hand is shown |
| WebGL risk | Moderate | Low | Low–medium |
| Main risk | Bad hands look worse than none | Feels bodiless | Looks "low quality" if overused |

### Recommendation (my judgement)

Build B as the system for every interaction now: anchors, the ajar door, crack stages, shards, diegetic locks. Then dress it with C's camera grammar for two hero moments (key insert, glass break), and add one free hand (C's one-handed rig) only where the key enters the frame. That answers Red's two named shots for the least rig cost, and it stays cancellable when the Relay arrives. If Red wants hands everywhere, A is the upgrade path; nothing in B is thrown away. Show Red a 10-second capture of the B+C key shot before committing to a rig.

## 5. Open items and UNVERIFIED

- RE Village key-insert framing (hands, camera position): UNVERIFIED; the wiki screenshots could not be viewed.
- Alien: Isolation jack framing comes from one forum post (S4).
- The Mirror's Edge claim that the camera sits at the eyes with reduced bob appeared only in a search snippet from a page that did not load: UNVERIFIED. S43 covers the reticle and visible limbs.
- TLOU2 shards crunching underfoot: search summary only, UNVERIFIED.
- Eiserloh trauma details come from secondary implementations (S46), not the talk itself.
- WebGL cost of the Animation module and CPU skinning: UNVERIFIED; measure with a WebGL build.
- Half-Life 2's pane glass (func_breakable_surf) is not cited because the Valve wiki sits behind a bot check.
- Code line numbers move while the map chat edits; anchor by symbol name (§1).
