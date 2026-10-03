# 04 — Period wardrobe and materials for the Hunter (The Relay)

Status: COMPLETE, 2026-10-02. Researcher: period-wardrobe.
Scope: what a humanoid Backrooms hunter could wear or be made of, if it came out of a late-1980s to mid-1990s American office, furniture store or building-services basement. Palettes are sRGB hex, checked against the game's own surface values.

Rules followed: every claim cites a URL fetched in this pass, or is marked **UNVERIFIED**. No files downloaded. No existing creature design is copied; entities from Kane Pixels, the A24 film, the wiki and games are discussed only as principles.

## 0. Constraints carried in from the project

From the project's own files (read 2026-10-02), not from the web:

| Constraint | Value | Source file |
|---|---|---|
| Body | radius 0.3 m; tested 0.4–1.95 m | `LEVEL_MODULE_SPEC.md` §7 |
| Height | must fit a 1.0 × 2.1 m door and 2.4 m ceilings: **≤ 2.05 m while walking**, or it stoops | same |
| Eye | sight ray from **1.60 m** | same; `ModuleUnits.RelayEye` |
| States | Listen / Search, Hunt (walk), Chase (run), BreakDoor (both forearms load forward), Stagger | `FrontRoomsMapHunter.cs`, `FrontRoomsRelayRig.cs` |
| Rig budget | 24–36 bones, 4 influences, no cloth or physics (WebGL) | `RELAY_MODEL_RIG_RESEARCH.md` |
| Current materials | body **#2B2928**, head **#D8D4C8**, detail **#A99E78** | `FrontRooms3DGame.cs` line 227 |
| Kit albedo range | nothing above sRGB #E6 or below #10 | `research/office_and_film/10_synthesis.md` §5.2 |

What wardrobe has to sit against (albedo values the game already uses):

| Surface | sRGB | Where it comes from |
|---|---|---|
| Level 0 paper, ground / mid / deep / cream | #D2C27C / #AC9A52 / #766A34 / #E3D594 | `Tools/lookdev/gen_surfaces.py` `wallpaper()` |
| Level 0 carpet | #9A8558 | `carpet()` |
| Level 0 ceiling tile | #D9D2BF | `ceiling()` |
| Exit paper (cold run) | #AFC0B6 | `wallpaper_cold()` |
| Office drywall (greige) | #BDB6A4 | `drywall()` |
| Office carpet tile | #5B636B | `office_carpet()` |
| Office ceiling 2×2 | #DCD8CC | `office_ceiling()` |
| Cubicle fabric slot | #4A535C | synthesis §5.2 `Prop_FabricCubicle` |
| Beige ABS (sides / yellowed tops) | #D3C9AE / #C8B98F | `Prop_PlasticBeige` |
| Putty steel | #A8A08A | `Prop_SteelPutty` |
| Oak / cherry veneer | #9A6A3A / #5A2A18 | `Prop_WoodOak`, `Prop_WoodCherry` |
| Run VCT (lit red) | #DAD7CC | `vct()` |

Lit, graded reading of the Office target (synthesis §6.9): walls and fabric sit at **L 0.15–0.25** in desaturated olive (#3C392C, #2E2F28); only the floor and lenses carry light. Level 0 is the opposite: a high-key, mid-saturation yellow field. **A body colour has to work in both: dark against yellow, and either pale or edge-lit against olive-dark.** This is why the current pale head + charcoal body pairing is right in principle and is kept as the baseline in §9.

## 1. Office worker: suits, shirts, ties, ID badges, pagers

### 1.1 What the period actually wore

- **Late 1980s: the power suit.** FIT's fashion-history timeline describes mid-to-late-1980s professional wear as "pin-striped, double breasted suits with wide lapels", wide shoulders and wide ties ([FIT Fashion History, 1980–1989](https://fashionhistory.fitnyc.edu/1980-1989/)). The V&A's 1988 Paul Smith suit is navy wool pin-stripe, wide-shouldered and double-breasted, worn by men who bought into the 1980s "dress-for-success" idea ([V&A O84293](https://collections.vam.ac.uk/item/O84293/suit-smith-paul/)).
- **Early 1990s: the suit softens and casualises.** Levi Strauss mailed its *Guide to Casual Business Wear* to about 25,000 HR managers in **1992**. It pushed khakis with button-down shirts. Survey figures quoted by Levi's: about two-thirds of companies allowed casual dress in 1992 (20% daily); nine in ten by 1995 (33% daily, 42% one day a week) ([Levi Strauss & Co., 2014](https://www.levistrauss.com/2014/07/07/dockers-and-the-birth-of-casual-fridays)). FIT notes that by the mid-1990s "Friday wear" was spreading through the week, with khakis as the alternative to denim ([FIT, 1990–1999](https://fashionhistory.fitnyc.edu/1990-1999/)).
- **Ties.** In 1993 the average tie had grown to about four inches wide, with bold colour and big patterns replacing stripes and solids. The *Christian Science Monitor* called these statement neckties the "T-shirts of the '90s"; the Jerry Garcia line (Stonehenge Ltd.) was one example ([CSM, 1 July 1993](https://www.csmonitor.com/1993/0701/01102.html)). The 1980s "power tie" (red or yellow, small regular motifs) is **UNVERIFIED** here: only secondary blog text was found, no museum source.
- **Short-sleeve dress shirts, white/pale-blue oxford, polyester-cotton blends** as the mid-level office default: **UNVERIFIED** (common knowledge, no source fetched).

### 1.2 ID badges and lanyards

- **Lanyard adoption is datable.** The *New Statesman* dates compulsory lanyards at BBC Broadcasting House to **January 1991** (Gulf War security); before that staff flashed a card at the commissionaire. It calls the lanyard "a symbol of arrival" and links it to 1990s TV (Scully in *The X-Files*) ([New Statesman, 2017](https://www.newstatesman.com/culture/2017/07/chain-command-how-office-lanyard-took-over-corporate-culture)). That is a UK example; US office lanyard adoption in the same years is **UNVERIFIED**, so treat a lanyard as *early-to-mid-1990s*, and a clip-on badge as safe for the whole window.
- **Proximity cards.** HID ("Hughes Identification Device") was formed in 1991 as a Hughes Aircraft subsidiary around 125 kHz proximity technology, and its prox cards became the de facto North American access standard ([Campus ID News, The evolution of HID](https://campusidnews.com/the-evolution-of-hid)). That it displaced contact magnetic-stripe cards in offices comes from a search summary of HID's own history page (403): **UNVERIFIED**. A white PVC photo card on a clip or cord is period-correct for the 1990s; a magnetic-stripe card is the safer late-1980s version.
- **Engraved name plates.** Rowmark's US trademark filings for engraving sheet start in January 1983, and for "personal identification badge blanks to be engraved" in November 1986 (search summary of [Justia trademarks: Rowmark](https://trademarks.justia.com/owners/rowmark-llc-293860/); the page returned 403: **UNVERIFIED**). Two-ply engraving plastic (a coloured cap layer cut through to a contrasting core) is the look: black-on-white, white-on-brown, gold-on-black.

### 1.3 Pagers

- The Science Museum's **Motorola tone pager, 1980–1990** (model 3BMXB/1, distributed by BT) is 30 × 45 × 85 mm, plastic and metal; the museum text says "the heyday of the pager was the 1980s" ([Science Museum Group co8054902](https://collection.sciencemuseumgroup.org.uk/objects/co8054902/motorola-tone-pager-1980-1990)).
- A search result describes NMAH 2007.25.1 as a black Motorola pager with a hinged belt clip, volume dial and red light. **UNVERIFIED**: the object page was not fetched.
- The Motorola Bravo (1986) as the best-selling pager is from secondary pages only: **UNVERIFIED**.

### 1.4 What this gives the Hunter

| Element | Read at 8–15 m in a dark corridor | Use |
|---|---|---|
| Wide padded shoulder, dark suit (navy, charcoal, pinstripe) | **Strong.** The 1980s shoulder is the one wardrobe feature that changes the silhouette. It also fixes Red's "spindly" note: a wide square yoke over a narrow waist. | Torso shape. A shoulder line that is too square and too level, a hanger with nothing in it. |
| Tie | Medium. A long vertical stripe of colour down the centre line. | One accent stripe in oxblood. Mustard is only 2.9:1 on a white shirt (§9). The 1993 wide, loud tie is too busy. |
| White shirt collar against a blank head | **Strong.** A light band under the head separates head from body at the threshold. | Collar ring, slightly too high, no neck visible. |
| Lanyard + white badge card | Weak at range, **strong in close-up** (catch). The badge can carry a photo that is not the creature. | Hero detail for the caught/jump frame. Blank photo, or a photo of an ordinary man. |
| Pager on belt | Weak. A small black box. | Audio, not visual: a pager tone is a diegetic cue for "relay". |

## 2. Janitorial and maintenance: coveralls and work uniforms

### 2.1 What the period actually wore

- **The fabric is 65/35 polyester-cotton twill.** Dickies' Original 874 work pant (1967) is a 65% polyester / 35% cotton blend, still its best seller; Dickies coveralls date from 1933 and the 1574 work shirt from the 1950s ([Dickies history](https://dickiesaustralia.com/pages/history)). Red Kap's CT10 action-back coverall is sold today as 65/35 poly-cotton twill (search summary of [Red Kap CT10 listings](https://www.nafeco.com/products/red-kap-coverall-twill-action-back/CT10-XX); the fetched page confirmed the action-back pleats, chest/hip pockets and rule pocket, not the blend).
- **It was mostly rented and laundered.** Red Kap moved to garments built for industrial laundering in 1947, worked exclusively for the rental-laundry trade in the 1950s, and was bought by VF in 1986 ([Wikipedia: Red Kap](https://en.wikipedia.org/wiki/Red_Kap)). In January 1993 the *Christian Science Monitor* put US uniform-rental revenue at $6 billion (from $2 billion a decade earlier), with about 14% of 53 million uniformed workers in rental uniforms. Clients typically got "11 sets of uniforms per employee" per working week ([CSM, 12 Jan 1993](https://www.csmonitor.com/1993/0112/12071.html)). Practical consequence for the look: **industrial-laundry fade**. Colours go flat and slightly grey, knees and seat shine, name patches stay crisp.
- **Colours.** Current Red Kap CT10 colour names: Postman Blue, Brown, Electric Blue, Charcoal, Navy, White, Orange, Black, Spruce Green ([garmentdecor CT10](https://garmentdecor.com/product/red-kap-ct10)). The SP24 work shirt comes in Grey, Light Blue, Black, Charcoal and Khaki ([Nafeco SP24](https://www.nafeco.com/products/red-kap-industrial-work-shirt-pc-ss/SP24-XX)). These are **current** catalogues; that the same names were sold in 1985–95 is **UNVERIFIED**, though navy, grey, charcoal, khaki and spruce green are the long-standing workwear set.
- **Name patch.** An oval or rectangular embroidered patch over the left chest with a first name in script is the standard rental-uniform identifier. **UNVERIFIED**: the museum object pages found (Heinz History Center) returned 403.

### 2.2 Who wore it, and a caution

The SEIU's Justice for Janitors campaign (in Los Angeles, the strike of spring 1990 and the Century City march of 15 June 1990) organised night-shift office cleaners, in Los Angeles largely immigrant, mostly women, "almost all were Latina/o", employed by contractors that competed on cost ([Wikipedia: Justice for Janitors](https://en.wikipedia.org/wiki/Justice_for_Janitors)).

**Design caution.** The period's real janitor was a low-paid, often immigrant worker. A monster that *is* the cleaner risks reading as "the help is the threat". If maintenance wardrobe is used, keep the cues **institutional rather than personal**: the uniform-rental garment, the action-back pleat, the blank or wrong name patch, the key ring. Avoid ethnic or gendered coding, and give it no face.

### 2.3 What this gives the Hunter

| Element | Read | Use |
|---|---|---|
| One-piece coverall | **Strong.** One continuous dark shape from collar to ankle. It hides the joints, so the gait carries the motion. Fixes "spindly": the CT10 is cut oversized to go over clothes. | Main body garment option B (§10). |
| Action-back pleats | Medium: two vertical folds behind the shoulders. Visible when it turns away. | Back read during Search. |
| Name patch, left chest | Close only. A white oval with a script name. | The catch frame. An empty oval, or the same name on every Relay (copy-paste logic, as in the film's identical furniture). |
| Key ring on a belt loop | Not visual; **audio**. | The Hunter is heard before seen: keys are a period-true walking sound. |
| Industrial-laundry fade | Material, not shape. | Shine on knees and seat (smoothness 0.35 there, 0.15 elsewhere). |

## 3. Furniture-store retail staff: uniforms and name tags

### 3.1 What the record supports

- **The Backrooms is a furniture store.** The founding photo was taken in the upper floor of a building in Oshkosh, Wisconsin that had been **Rohner's Furniture**; a 1977 photo of it as Rohner's was found, and the Backrooms photo itself dates from the HobbyTown racetrack renovation of 2002–03 ([80.lv](https://80.lv/articles/the-internet-finds-the-original-backrooms-location); [WPR, 2026](https://www.wpr.org/news/horror-film-backrooms-meme-oshkosh)). The A24 film also pulls store stock into the backrooms (synthesis §0.3). So a hunter born of the **store**, rather than of the office, is the most canonical origin open to FrontRooms.
- **Store format.** Levitz pioneered selling brand-name furniture from a warehouse-style store, and declined in the 1990s as buyers moved to showrooms "arranged to look like actual rooms" ([Wikipedia: Levitz](https://en.wikipedia.org/wiki/Levitz_Furniture)). IKEA's first US store opened at Plymouth Meeting, PA, on 12 June 1985 (search summary of [Furniture Today](https://www.furnituretoday.com/business-news/happy-30th-birthday-7-things-you-didnt-know-about-ikea), **UNVERIFIED**). The period's furniture floor is the **room-set**: a fake living room under the same troffers. That is the FrontRooms joke already.
- **Name tags.** Permanent name tags are "usually made of lightweight metal or plastic"; the "Hello my name is" sticker dates from C-Line in 1959 ([Wikipedia: Name tag](https://en.wikipedia.org/wiki/Name_tag)). Two-ply engraved plastic badges: see §1.2 (Rowmark dates **UNVERIFIED**).
- **What furniture salespeople wore** (sport coat and tie on commission floors; store-coloured vests or polos at discount chains): **UNVERIFIED**. No catalogue, museum or period source was found. The Walmart blue vest's "late 1980s" origin appears only on content-farm pages: **UNVERIFIED, do not cite**.

### 3.2 What this gives the Hunter

The most useful store object is not clothing but **the merchandise ticket**: a card swing-tag on a string loop, a "SOLD" or "FLOOR SAMPLE" tag, a stock number. That ties the Hunter to the game's copy-paste furniture piles. It is *inventory*, the same as the 39 identical chairs (synthesis §0.3). The same stock number on every Relay is the furniture-pile rule (exact duplicates) applied to the creature.

| Element | Read | Use |
|---|---|---|
| Swing tag on string, at the wrist or tied to a finger | Close and medium. A small pale rectangle that swings with the arm, which sells the gait. | Hero detail. Manila card #D8C9A0 or white #E2DED2, with a stock number. |
| Engraved name badge, left chest | Close. Black-on-white or white-on-brown. | If used, blank, or the name engraved upside down. |
| Room-set logic | Concept. | The Relay "relays" like a display being re-staged: found standing *in* a furniture tableau, posed like a display figure (links to §6). |
| Plastic-wrapped like delivered stock | Medium. Pale sheen over a dark body. | Overlaps with §4.3 poly sheeting. A single material study can serve both. |

## 4. Hazmat: Tyvek and cleanup suits

### 4.1 History (firmly dated)

- **Material.** Tyvek is flashspun high-density polyethylene. A DuPont researcher noticed white fluff coming out of a pipe in 1955; in 1959 DuPont found that spinning it fast gave a durable sheet; it was trademarked in 1965 and sold commercially from April 1967 ([Wikipedia: Tyvek](https://en.wikipedia.org/wiki/Tyvek); [DuPont 50th-anniversary release](https://www.dupont.com/products-and-services/fabrics-fibers-nonwovens/protective-fabrics/press-releases/tyvek-50th-anniversary.html)).
- **Garments from 1966.** Raymond J. Smith's Disposables Inc. was the first to sell Tyvek garments, in 1966, under marketing rights from DuPont, ahead of full commercial production. Demand grew after the 1970 OSH Act because disposables removed laundering and decontamination costs ([Lakeland Industries company history](https://company-histories.com/Lakeland-Industries-Inc-Company-History.html)).
- **Asbestos abatement was the period's defining use.** AHERA was signed on 22 October 1986. An EPA survey from 1984 counted about 34,800 schools with friable asbestos, exposing an estimated 15 million students and 1.4 million staff, and AHERA required accredited abatement ([EPA archive](https://www.epa.gov/archive/epa/aboutepa/signing-asbestos-hazard-emergency-response-act.html); [Wikipedia: AHERA](https://en.wikipedia.org/wiki/Asbestos_Hazard_Emergency_Response_Act)). In the early 1990s many abatement contractors switched from Tyvek to cheaper polypropylene disposables (Lakeland history, same URL). So: **a white disposable suit in a late-1980s building is period-exact, and it belongs to building services, not to a lab.**
- **Appearance.** Tyvek coveralls are "usually white"; the sheet looks like paper and takes print ([Wikipedia: Tyvek](https://en.wikipedia.org/wiki/Tyvek)). Hood worn over the respirator straps, elastic at wrists and ankles, booties, duct tape at the cuffs, and double-layer 4–6 mil polyethylene containment sheeting on walls and floors: these procedure details come from search summaries of abatement specifications and are **UNVERIFIED** (the one PDF tried was unreadable).

### 4.2 Already taken in the IP

A search summary of the Kane Pixels fan wiki says Async researchers wear hazmat suits on expeditions into the Backrooms (**UNVERIFIED**: the wiki page returned 402, and the Wikipedia series article does not mention suits). If true, a hazmat-suited figure in FrontRooms risks reading as **another explorer** rather than as the predator, or as borrowed from the series. Use hazmat cues **as material only** (white crinkled HDPE, taped seams, poly sheeting), never as the full suit-plus-respirator costume.

### 4.3 What this gives the Hunter

| Element | Read | Use |
|---|---|---|
| White crinkled HDPE skin | **Weak in Level 0**: Tyvek white (#E4E2DA, inside the kit's #E6 cap) is 1.14:1 against the paper's cream #E3D594, 1.38:1 against its ground and 1.16:1 against the Level 0 ceiling tile (§9). **Strong in Office and Run**: 4.7–6.0:1 against office carpet and cubicle fabric. | Head or hood material only, not the body (§9). |
| Hood pulled tight over a respirator | **Strong.** Gives a blank face with one dark shape on it: the current "narrow face void" with a real-world reason. | A hood seam that frames a void. No respirator canisters: too explorer-coded (§4.2). |
| Silver duct tape at the wrists and ankles | Medium. Bright bands at the joints mark the gait. | Taped cuffs. Read best in the dark Office. |
| Poly-sheeting skin, translucent, taped | **Strong and original.** A figure wrapped in containment plastic: you see a darker shape moving inside a pale sheet. | Material study for a "relaying" (half-present) state. Needs a cheap fake-translucency shader (rim plus a dithered inner silhouette). |
| Rustle | Audio. Tyvek and poly are loud. | The hunter is heard by its *clothes*; that fits a noise-hunting AI. |

## 5. Security guard uniforms

### 5.1 What the record supports

- **Guards outnumbered police.** The NIJ-sponsored Hallcrest report (Cunningham and Taylor, 1985) found about three times as many private security workers as public police (Penn State World Campus course page: [CRIMJ 304, lesson 2](https://courses.worldcampus.psu.edu/welcome/crimj304/less02_02.html)). The 1980s office lobby and loading dock were guarded by **contract** guards, whose company changed with the contract.
- **The patch is the identifier, and it changes.** Two dated uniform patches from a guard who worked a Manhattan office complex 1979–86 show the format: a shield-shaped dark-blue patch with white embroidery (3.75 × 3 in), and a square black patch with yellow embroidery. The museum notes they record "changes in the companies contracted" ([9/11 Memorial & Museum C.2008.879.25](https://collection.911memorial.org/Detail/objects/122206), [C.2008.879.16](https://collection.911memorial.org/Detail/objects/122205)). These are cited only as dated evidence of the patch format. **Nothing from these objects should be reproduced**, given their context.
- **Shirt and trousers** (light-blue or white uniform shirt with epaulettes and two button pockets, navy or black trousers, duty belt, flashlight, two-way radio): **UNVERIFIED**. A c.1980 grey short-sleeve correctional-officer shirt with epaulettes and sleeve patch (Heinz History Center) appeared only in a search summary; the object page returned 403.

### 5.2 What this gives the Hunter

| Element | Read | Use |
|---|---|---|
| **Flashlight** (a period D-cell metal torch) | **The strongest gameplay read of any item in this report.** A moving cone makes the Hunter's sight ray visible. `Sees()` already casts from 1.60 m. | Optional system hook: a cone from the hand or chest that sweeps during Search and locks during Chase. A spotlight costs one shadowed light: budget it. |
| Two-way radio on the belt or shoulder | Audio. Squelch and static bursts. | *Relay* is also a radio word. A squelch burst could mark the relay teleport. |
| Shoulder patch (shield) | Medium: a bright mark high on the arm that shows which way the body faces. | A blank shield, or an invented generic "BUILDING SERVICES". |
| Epaulettes plus a square shoulder line | **Strong**, as with the suit (§1.4). | Shares the wide-yoke solution. |
| Peaked cap | Strong silhouette, but too police-coded, and it adds height against the 2.05 m cap. | **Avoid.** |

## 6. Display mannequins of the era

### 6.1 What the record supports

- **Material.** Fibreglass was the industry standard by the 1960s ([Collectors Weekly](https://www.collectorsweekly.com/articles/what-mannequins-say-about-us/)). The process runs "from initial modeling in clay to the rendering of the fiberglass end-product", then paint (UAL Fashion Exhibition Making on MAD's 2015 *Ralph Pucci: The Art of the Mannequin*, [fashionexhibitionmaking.arts.ac.uk](https://fashionexhibitionmaking.arts.ac.uk/ralph-pucci-the-art-of-the-mannequin/)). Adel Rootstein made realistic fibreglass figures in London from 1959 and sold the firm to Yoshichu in 1991 ([Wikipedia: Adel Rootstein](https://en.wikipedia.org/wiki/Adel_Rootstein)).
- **Abstraction is dated to exactly this window.** Collectors Weekly: through the 1970s and '80s mannequins grew more abstract, "leading to the ubiquitous faceless, or sometimes headless, figures of the '90s", usually painted solid **white, black or grey** (same URL). A second reading puts the move to torsos and faceless figures in the **late 1980s**, after an era of hyper-realism (search summary of the same Collectors Weekly piece). The reason given in a mannequin-supplier blog (cheaper, low-maintenance, as stores cut visual-merchandising staff in the 1990s) is **UNVERIFIED**: the page would not load.
- **Egg heads now.** Current suppliers sell fibreglass-reinforced polyester figures with a matte white finish and an "abstract balloon head" (search summaries of archiexpo and fixturesanddisplays listings; **UNVERIFIED** as period evidence).

### 6.2 Principles to take (no specific figure copied)

1. **The blank head is a retail object, not only a horror trope.** The current Relay head (#D8D4C8, smooth, no features) already reads as a 1990s abstract mannequin. That gives the design a period reason.
2. **Mannequins come apart at fixed seams**: wrist, upper arm, waist, and sometimes the neck, so clothes can be dressed on. A real seam line at those joints is period-true, and it is the visual for *relaying*: the parts reassembled somewhere else. **UNVERIFIED**: seam positions are common knowledge, not sourced.
3. **Rod and plate.** Display figures stand on a rod into the calf or seat and a floor plate. A rod socket in one calf, or a plate still bolted to one foot, is a cheap, legible "wrong" detail. It also explains a heavy foot sound on carpet (`RELAY_MODEL_RIG_RESEARCH.md`: oversized feet for the carpet impact). **UNVERIFIED** as a sourced fact.
4. **Finish.** Satin lacquer over fibreglass. Chips show a darker or fibrous layer under the paint. Use smoothness 0.45–0.55 on the head, so the troffer catches a soft highlight that a matte skin would not.
5. **Avoid** the full-realism Rootstein look (uncanny but costly, and close to many existing horror mannequins), and avoid the purely abstract art pieces (the MAD show's artist collaborations). Take only the *1990s abstract retail* level: smooth, monochrome, faceless, seamed.

### 6.3 What this gives the Hunter

| Element | Read | Use |
|---|---|---|
| Monochrome fibreglass head, satin | **Strong** in both zones if the value is right (§9). | Keep, and refine to an egg shape with a slight chin plane. |
| Joint seams | Medium. Thin dark lines that show at 5 m under top-light. | At the wrist, mid-upper-arm and waist. A 3–4 mm geometric groove, not a texture, following the synthesis rule that only real reveals cast lines under flat top-light. |
| Body in suit or coverall over a mannequin core | **Strong concept.** A display figure dressed by the store, now walking. | Recommended frame for option A (§10). |
| Calf rod socket | Close. | One per Relay. Pairs with the stagger animation (it was knocked off its stand). |

## 7. Office-chair and cubicle fabrics as skin

### 7.1 What the record supports

- **The cubicle is a 1968 product that became a 1980s condition.** Herman Miller's Action Office II launched in 1968; by the late 1970s its dominant use was the four-sided cubicle; after Propst left in 1980, Jack Kelley and Clino Castelli revised it in **1983**, "updating the materials and colors" ([PIN–UP](https://archive.pinupmagazine.org/articles/the-story-of-action-office-2-and-cubicle-inventor-robert-propst-herman-miller); [The Henry Ford](https://www.thehenryford.org/explore/blog/robert-propst-unorthodox-thinker/)). Wikipedia gives partitions as "usually 5–6 feet (1.5–1.8 m) tall" and dates *Dilbert*'s cubicle satire to 1989 ([Wikipedia: Cubicle](https://en.wikipedia.org/wiki/Cubicle)).
- **Colour of the period.** A 1983 *Christian Science Monitor* piece lists the muted palette in fashion: "taupes, mauves, pink beiges, warm grays, dusty roses, muted corals, blue-greens, and grayed blues", with garnet and teal as accents ([CSM, 4 Nov 1983](https://www.csmonitor.com/1983/1104/110435.html)). The piece is about residential interiors; that offices followed the same palette is **UNVERIFIED** here.
- **Panel fabric.** Guilford of Maine FR701 is described by resellers as the acoustic standard for more than 40 years, heathered, now 100% recycled polyester, and suited to office panel systems (search summaries; the Guilford page refused connection: **UNVERIFIED**).
- **Chairs.** The Henry Ford holds an Equa chair seat frame (Stumpf and Chadwick for Herman Miller, c. 1984): plastic, "Light gray" ([THF 2012.52.18](https://www.thehenryford.org/collections/explore/artifact/372434)). The period task chair is a light-grey or black plastic shell with tweed upholstery. The upholstery part is **UNVERIFIED**.

### 7.2 What this gives the Hunter

- **The panel line is the Office's horizon.** FrontRooms' panels are 1.57 m and the Relay's sight ray is at 1.60 m (`LEVEL_MODULE_SPEC.md` §7). A hunched figure of about 1.95 m shows **head and shoulders above the panel tops** while its body is hidden. So in the Office the head and shoulder line are the whole read, and they are seen against the far wall and haze, not against the carpet. **Design the head and shoulder yoke as the Office silhouette.**
- **Fabric as skin: camouflage, not contrast.** Cubicle slate #4A535C on the body is 4.7:1 against Level 0 paper but only 1.5–1.9:1 against the Office's own panels and carpet (§9). A fabric-skinned Hunter would therefore be *native* to the Office: hard to see among the panels and plain in Level 0. That is a legitimate design ("it belongs to the office"), but it **conflicts with the chase**, where the player must read it. Recommended only as a **texture inside a darker body** (a heathered nap on the coverall or suit cloth), or as a deliberate Office-only ambush variant.
- **Tackable surface.** Pushpins and a pinned memo on the Hunter's back is a close-up detail that turns the body into a panel. **UNVERIFIED** as sourced fact (tackable panels are common knowledge). It costs nothing at range.
- **Mauve, dusty rose, teal.** These sit at mid value (mauve #8A7680: 1.2–2.4:1 against everything), so they are only usable as small accents: a tie, a lanyard, a stripe in a name patch.

## 8. Hardware as body parts: CRT, telephone, relay

### 8.1 What the record supports

- **"Relay" is a signal repeater.** The word appears in electromagnetic contexts from 1860; relays were first used "in long-distance telegraph circuits as signal repeaters". An electromagnetic relay is a coil on an iron core, a yoke, a moving armature and contacts that make or break ([Wikipedia: Relay](https://en.wikipedia.org/wiki/Relay)). **This is the creature's verb.** It relays itself closer, unseen (`FrontRoomsMapHunter.cs` header): a repeater picking up the signal further down the line.
- **The relay exchange died in exactly this period.** Western Electric's No. 5 Crossbar (made from 1947) stayed in Bell System service as a Class 5 switch "until the early 1990s", when electronic switching replaced it ([Wikipedia: 5XB](https://en.wikipedia.org/wiki/Number_Five_Crossbar_Switching_System)). Crossbar switches close contacts by "select and then the hold electromagnets" moving bars ([Wikipedia: Crossbar switch](https://en.wikipedia.org/wiki/Crossbar_switch)). So in 1985–95 the building's phones still ran, somewhere, through rooms of clicking relays.
- **Desk telephone.** The Western Electric 2500 touch-tone set added * and # in 1968 and went modular in 1974. The 500 set came in ivory, green, grey, red, brown, beige, yellow and blue from 1954, and in light grey, aqua, light beige, white and pink by 1957 ([Wikipedia: Model 500](https://en.wikipedia.org/wiki/Model_500_telephone)).
- **CRT.** Monochrome monitors used green (P1), amber (P3) and white (P4) phosphor; they were most common in the early-to-mid-1980s; some showed "a dim afterglow" (ghosting); burn-in was common ([Wikipedia: Monochrome monitor](https://en.wikipedia.org/wiki/Monochrome_monitor)).
- **Beige plastics.** Apple's first Macs were beige, officially "Putty"; Apple moved to the lighter "Platinum" in 1987 ([Vintage Mac Museum](https://vintagemacmuseum.com/?p=2592)). Frog Design's Snow White language (Apple, 1984–90) used grooves "2 mm wide, 2 mm deep, spaced 10 mm apart" ([Wikipedia: Snow White design language](https://en.wikipedia.org/wiki/Snow_White_design_language)).
- **Why beige goes yellow.** A summary of Caden Xu's paper attributes most ABS yellowing to free radicals from the butadiene phase, which form 2-hydroxymuconic acid, a compound that absorbs blue. Brominated flame retardants are "a minor contributor", and stabilisers keep the yellowing near the surface ([Hackaday, 2021](https://hackaday.com/2021/01/23/a-deep-dive-into-the-chemistry-of-retrobright/)). This supports the kit's rule of yellower top faces (#C8B98F) over paler sides (#D3C9AE).

### 8.2 What this gives the Hunter (use sparingly: the game's language is ordinary objects, and a hardware body reads as "robot")

| Idea | Read | Verdict |
|---|---|---|
| **Face void as dark CRT glass**: curved, glossy (#0F1412, smoothness 0.80–0.88, the kit's `Prop_GlassCRT`) | **Strong.** A glossy curved void catches the troffers as moving streaks, in both zones. The current flat black slot cannot do this. | **Recommended.** No new material is needed. |
| **Phosphor afterglow on relay**: a dim ghost of the face left where the Hunter was, fading over 1–2 s | Strong, and it explains the mechanic. | Recommended for the relay VFX. Tint it with the kit's CRT `_On` emission #5E7380 (the game's own), not a saturated green or amber. |
| Snow White grooves (2 mm, 10 mm pitch) on a plastic plate (crown or shoulder yoke) | Close only. A period industrial-design signature. | Optional. A normal-map detail on the head shell. |
| Top-yellowed beige ABS head (crown #C8B98F → sides #D3C9AE) | Medium. Grades the head under top-light. | Recommended at low strength. Too much yellow lowers Level 0 contrast. |
| Relay coil and armature visible in the body (chest or joints) | Weak at range, and reads as steampunk or robot. | **Avoid as anatomy.** Use the relay as **sound**: contact chatter and armature clack when it relays. |
| Handset with coiled cord, hanging from the hand or belt | Close only. The curly cord is a strong silhouette in a jump frame. | Optional prop. Thin cords at range add "spindly"; keep it under the hand. |
| Pager on the belt | Audio. | Pager beep as a relay pre-cue (see §1.3). |

## 9. Palettes (sRGB) against the game's backgrounds

### 9.1 Method

The hex values are albedo targets in the kit's convention (sRGB, after regrade, inside #10–#E6). The candidate wardrobe colours are this report's own estimates of the garments in §1–§8 (laundered and faded, not catalogue-fresh): **approximations, not sampled from sources**. Contrast was computed with a script (WCAG relative luminance; CIE76 ΔE in Lab), albedo against albedo, assuming both surfaces get the same light. For the Office, the colours were also scaled by the factor that turns drywall albedo #BDB6A4 into the measured lit wall #3C392C (k ≈ 0.087, synthesis §6.9), then compared with the measured lit regions. That is a crude model (walls get less top-light than a figure standing under a lens), so treat the Office column as a lower bound.

### 9.2 Contrast table (ratio : 1 / ΔE)

| Candidate | sRGB | L0 paper ground #D2C27C | L0 carpet #9A8558 | L0 ceiling #D9D2BF | Office drywall #BDB6A4 | Office carpet #5B636B | Cubicle #4A535C | Exit paper #AFC0B6 | Cherry #5A2A18 |
|---|---|---|---|---|---|---|---|---|---|
| Current body | #2B2928 | 8.1 / 72 | 4.1 / 48 | 9.6 / 68 | 7.2 / 58 | 2.4 / 26 | 1.9 / 20 | 7.6 / 60 | 1.2 / 29 |
| Suit navy, faded | #262C3A | 7.8 / **77** | 3.9 / 53 | 9.3 / 69 | 6.9 / 60 | 2.3 / 24 | 1.8 / 17 | 7.3 / 60 | 1.2 / 37 |
| Workwear navy, laundered | #2F3644 | 6.8 / 73 | 3.4 / 50 | 8.0 / 65 | 6.0 / 55 | 2.0 / 20 | 1.6 / 13 | 6.4 / 56 | 1.0 / 37 |
| Workwear spruce | #2E3B33 | 6.6 / 65 | 3.3 / 42 | 7.8 / 62 | 5.8 / 52 | 1.9 / 21 | 1.5 / 16 | 6.2 / 53 | 1.0 / 33 |
| Mannequin black | #1D1D1C | **9.4** / 77 | **4.7** / 53 | **11.2** / 74 | **8.4** / 64 | 2.8 / 31 | 2.2 / 25 | **8.9** / 66 | 1.4 / 32 |
| Current head | #D8D4C8 | 1.2 / 32 | 2.4 / 35 | **1.0 / 4** | 1.4 / 11 | 4.1 / 45 | 5.3 / 52 | 1.3 / 12 | 8.0 / 67 |
| Tyvek white | #E4E2DA | 1.4 / 35 | 2.8 / 41 | 1.2 / 8 | 1.6 / 17 | **4.7** / 49 | **6.0** / 56 | 1.5 / 15 | **9.1** / 72 |
| Current detail | #A99E78 | 1.5 / 21 | 1.3 / 11 | 1.8 / 22 | 1.3 / 15 | 2.3 / 36 | 2.9 / 41 | 1.4 / 22 | 4.4 / 47 |
| Khaki twill | #A39272 | 1.7 / 25 | **1.2 / 9** | 2.0 / 25 | 1.5 / 16 | 2.0 / 32 | 2.6 / 37 | 1.6 / 24 | 3.9 / 43 |
| Guard light-blue shirt | #A7B4C2 | 1.2 / 46 | 1.7 / 39 | 1.4 / 22 | **1.0 / 19** | 2.9 / 31 | 3.7 / 38 | 1.1 / 14 | 5.6 / 62 |
| Mannequin grey | #8D8B85 | 1.9 / 40 | **1.1 / 24** | 2.3 / 27 | 1.7 / 18 | 1.8 / 19 | 2.3 / 25 | 1.8 / 20 | 3.5 / 44 |
| Cubicle mauve | #8A7680 | 2.4 / 50 | 1.2 / 31 | 2.8 / 36 | 2.1 / 28 | 1.5 / 15 | 1.9 / 21 | 2.2 / 30 | 2.8 / 39 |
| Cubicle teal | #2F5E5C | 4.1 / 60 | 2.0 / 41 | 4.8 / 52 | 3.6 / 43 | 1.2 / 16 | 1.1 / 16 | 3.8 / 41 | 1.6 / 47 |

Accents on the body: white collar #E2DFD6 on faded navy is **10.5:1**; current head on current body 9.8:1; manila tag #D8C9A0 on navy 8.5:1; oxblood tie #5B2A2A on a white shirt 8.7:1; mustard tie #9C7F34 on a white shirt only 2.9:1; duct tape #B8B8B4 on laundered navy 6.1:1.

Office, lit model (lower bound): every dark body is about **1.7:1 against the lit wall, 1.5:1 against the lit cubicle face, 3.0:1 against the lit carpet and about 9:1 against the ceiling beside a lens**. The pale head is 1.2:1 against the lit wall but 4.5:1 against the lens-lit ceiling.

### 9.3 What reads best (the reading)

1. **Large areas must be dark (sRGB value ≤ #3B, Y ≤ 0.045).** Charcoal, faded navy, laundered navy, spruce and mannequin black all give **5.8–11:1 against Level 0 paper, the Level 0 ceiling, Office drywall and Exit paper**. This confirms the current charcoal body.
2. **Navy beats charcoal in Level 0.** At the same value it has a higher ΔE against the yellow paper than charcoal (77 against 72, level with pure black), because blue sits opposite yellow, and it reads as cloth rather than as a hole. It also keeps 7.3:1 against the cold Exit paper. **Faded navy #262C3A is the recommended body colour.** Spruce #2E3B33 is the alternative if Red wants the body to belong to the green-grey Office grade, at a small Level 0 cost.
3. **Mid values fail everywhere.** Khaki, mannequin grey, mauve, mustard, light-blue shirting and the **current detail colour #A99E78** sit at 1.0–1.9:1 against most surfaces. #A99E78 is 1.05:1 against Level 0 paper mid and 1.03:1 against putty steel: the current hands and feet are camouflaged, which defeats their purpose as the "reveal" detail. Replace with white #E2DFD6 (to show the hands) or with the body colour (to lose them).
4. **In the Office the dark body is lost against the panels** (1.5–1.9:1 albedo; about 1.5:1 lit). The Office read comes from (a) the pale head and white collar band above the 1.57 m panel line, read against the lit ceiling and haze, and (b) the dark legs against the lit carpet (about 3:1). So the head and collar are not decoration; **they are the Office silhouette**.
5. **The pale head is weakest against the Level 0 ceiling** (1.02:1, ΔE 4: the current head is effectively ceiling-tile colour). Against the paper it relies on hue (ΔE 32), not value. Fixes: the CRT-glass face void (§8.2) adds a dark mass in the middle of the head, and a slight top-yellowing to #C8B98F separates it from the cool-white ceiling tile *only if* kept near the crown.
6. **Pale whole-body options (Tyvek, white mannequin, light-blue guard shirt) only work in the Office and Run.** They fail in Level 0, where the game starts. Use them as accents, never as the body.
7. **Cherry and dark-veneer furniture hides any dark body** (1.0–1.4:1). In tall furniture piles, the head and white accents carry the read.

### 9.4 Proposed palettes

**P-A "Floor Sample": a 1990s display figure dressed in a late-1980s suit (recommended)**

| Part | sRGB | Smoothness | Note |
|---|---|---|---|
| Suit cloth (wool, faded navy) | #262C3A | 0.15–0.22 | Shine to 0.30 at the elbows and seat |
| Collar band and cuffs (shirt) | #E2DFD6 | 0.25 | The Office silhouette accent |
| Head shell (satin fibreglass) | #DAD5C9 → crown #C8B98F | 0.45–0.55 | Top-face mask as for kit ABS |
| Face void (CRT glass) | #0F1412 | 0.80–0.88 | Reuse `Prop_GlassCRT` |
| Joint seams (geometry grooves) | ≈ #10100F in cavity | — | Wrist, upper arm, waist |
| Tie (optional) | #5B2A2A oxblood | 0.30 | Mustard fails on a white shirt |
| Lanyard and badge | #2F3644 cord; #E2DFD6 card | 0.20 / 0.45 | Blank card |
| Swing tag | #D8C9A0 manila; #1D1D1C ink | 0.15 | Stock number |
| Shoes | #1D1D1C | 0.40 | Oversized for the carpet foley |

**P-B "Night Shift": building-services coverall (alternative)**

| Part | sRGB | Smoothness | Note |
|---|---|---|---|
| Coverall, 65/35 twill | #2F3644 laundered navy, or #2E3B33 spruce | 0.15; knees and seat 0.35 | Action-back pleats |
| Name patch | #E2DFD6, border thread #5B2A2A | 0.20 | Blank, or the same name on every Relay |
| Tape cuffs | #B8B8B4 | 0.50 | Kit `Prop_Aluminium` value; dielectric here |
| Hood (Tyvek) | #E4E2DA | 0.30 | Tight around the head; no respirator |
| Face void | #0F1412 | 0.80–0.88 | As P-A |
| Key ring | #B08A4A | 0.60, metallic 1 | Kit `Prop_Brass`; mainly a sound |

**P-C "Inventory": a wrapped display figure (relay-state material study)**

| Part | sRGB | Note |
|---|---|---|
| Core | #1D1D1C | Mannequin black, seams |
| Poly sheeting | #E4E2DA at about 0.2–0.3 opacity, via fresnel and rim | Fake translucency; no transparent sorting |
| Tape | #B8B8B4 | Bands at the knees, waist and neck |
| Stock tag | #D8C9A0 / #1D1D1C | As P-A |

**Rejected as a whole outfit: "Contract guard".** The light-blue shirt (#A7B4C2) is 1.2:1 against Level 0 paper and 1.0:1 against Office drywall. Keep its parts: the flashlight (§5.2), a blank shield patch #2F3644 with #E2DFD6 thread, and navy trousers #262C3A.

## 10. Recommendations for the Hunter redesign

### 10.1 Originality guard (read before sketching)

- **Slender Man is the nearest existing design**, and the current Relay is already close to it. It was created on 10 June 2009 by Eric Knudsen ("Victor Surge") on Something Awful: very tall and thin, long arms, a "white and featureless" face, a black suit and tie ([Wikipedia: Slender Man](https://en.wikipedia.org/wiki/Slender_Man)). A tall, pale-headed, suited figure **must** be pushed away from it on every axis:

  | Slender Man | FrontRooms Relay |
  |---|---|
  | Black suit | Faded navy, or a coverall |
  | Thin, upright | Wide square yoke, hunched |
  | Featureless face | A glossy face void |
  | Long tentacle arms | Seamed mannequin limbs at normal length |

  Add the retail markers (swing tag, seams, blank badge), which have no Slender Man equivalent.
- **Living shop mannequins are taken as a premise.** *Doctor Who*'s Autons (1970) are "living plastic mannequins" that step out of shop windows ([Wikipedia: Auton](https://en.wikipedia.org/wiki/Auton)). FrontRooms should use the 1990s abstract retail figure as a **material and period** (fibreglass, satin, seams, faceless), not the "dummies come alive in the window" scene.
- **Async-style hazmat suits are an explorer costume in Kane Pixels' canon** (UNVERIFIED, §4.2). Use hazmat as material only.
- None of the entities from Kane Pixels, the A24 film, the wiki or games were studied for shape in this report. The period sources are garments and objects, which carry no creature-design IP.

### 10.2 Three directions for the early pre-render pass

| | A — "Floor Sample" (recommended) | B — "Night Shift" | C — "Inventory" (relay state) |
|---|---|---|---|
| Origin story it implies | A store display figure, dressed by the store in last decade's suit, now walking the stockrooms | The building's own maintenance or abatement crew, institutional and anonymous | Stock that was delivered, wrapped and tagged |
| Silhouette fix for "spindly" | Padded 1980s shoulder yoke: a wide, level, square top over a narrow waist; trousers break over oversized shoes | Oversized coverall: one continuous mass; action-back pleats widen the back | Taped bands break the limbs into blocks |
| Head | Satin egg shell #DAD5C9, crown-yellowed; CRT-glass face void | Tyvek hood pulled tight around the same shell | Shell visible through the sheeting |
| Signature close-up | Blank badge on a lanyard, swing tag at the wrist, wrist seam | Blank oval name patch, taped cuffs, key ring | Stock tag and a translucent pale skin over a dark core |
| Level 0 read | Faded navy 7.8:1, ΔE 77 | Navy 6.8:1 / spruce 6.6:1 | Black core 9.4:1 |
| Office read | Head and collar band above the 1.57 m panel line | Tyvek hood above the panel line | Pale wrap: 4.7–6.0:1 against carpet and panels |
| Sound it gives the foley | Hard shoe heel, fabric | Keys, twill swish, Tyvek rustle | Plastic crinkle, tape |
| Risk | Slender Man proximity (mitigate per §10.1) | "Monster janitor" class reading (§2.2) | Reads as a prop rather than a predator; transparency cost |

**Proposed combination:** A as the body; C's wrap and phosphor ghost as the *relaying* look (the figure resolves out of a pale wrap where it re-appears); B's sound set (keys, rustle) layered into A's foley. The period story then reads as one sentence: **the store's display figure keeps the building's keys.**

### 10.3 Wardrobe rules that follow from the constraints

1. **Height.** Keep the walking top of head or shoulder at 1.92–2.00 m (≤ 2.05 m). A wide shoulder yoke adds width, not height. No caps or hats (§5.2). The hunch is justified by the code: it puts the face void near the **1.60 m** sight ray, so what the player sees matches where the Relay looks from.
2. **No cloth simulation** (WebGL; `RELAY_MODEL_RIG_RESEARCH.md`). Garments are skinned rigid shells. Tie, lanyard and swing tag are 1–2 bone dangles, or are baked into the clips.
3. **Accents are white or oxblood, never mid-tone** (§9.3). Retire the #A99E78 detail material.
4. **Duplicates are exact.** If several Relays ever appear (relay ghosts, posters, piles), they share the same badge, the same stock number and the same name. This is the furniture-pile rule (synthesis decision 3) applied to the creature.
5. **Material count.** P-A needs 5 slots (cloth, shirt, shell, CRT glass, accents atlas). That fits the kit's ≤ 4–6 slot discussion if the tag, badge and seams go into `Prop_Atlas`.

### 10.4 Open questions for Red

- Navy (best Level 0 contrast) or spruce (belongs to the Office grade)?
- Tie or no tie? A tie brings the figure closer to Slender Man; the blank badge on a lanyard does the same "office" job without that cost.
- Should the flashlight (sight-ray made visible, §5.2) be explored? It changes gameplay readability, not only the look.

## 11. Sources

All fetched on 2026-10-02 unless marked. "Search only" means the claim rests on a search-engine summary and is marked **UNVERIFIED** in the text.

**Office wardrobe and accessories**
- FIT Fashion History Timeline, 1980–1989 — https://fashionhistory.fitnyc.edu/1980-1989/
- FIT Fashion History Timeline, 1990–1999 — https://fashionhistory.fitnyc.edu/1990-1999/
- V&A, Paul Smith suit, 1988 (O84293) — https://collections.vam.ac.uk/item/O84293/suit-smith-paul/
- Levi Strauss & Co., Dockers and the birth of Casual Fridays (2014) — https://www.levistrauss.com/2014/07/07/dockers-and-the-birth-of-casual-fridays
- Christian Science Monitor, ties, 1 July 1993 — https://www.csmonitor.com/1993/0701/01102.html
- New Statesman, the office lanyard (2017) — https://www.newstatesman.com/culture/2017/07/chain-command-how-office-lanyard-took-over-corporate-culture
- Campus ID News, The evolution of HID — https://campusidnews.com/the-evolution-of-hid
- Science Museum Group, Motorola tone pager 1980–1990 (co8054902) — https://collection.sciencemuseumgroup.org.uk/objects/co8054902/motorola-tone-pager-1980-1990
- Wikipedia, Name tag — https://en.wikipedia.org/wiki/Name_tag

**Workwear, building services, hazmat**
- Dickies history — https://dickiesaustralia.com/pages/history
- Wikipedia, Red Kap — https://en.wikipedia.org/wiki/Red_Kap
- Nafeco, Red Kap SP24 work shirt — https://www.nafeco.com/products/red-kap-industrial-work-shirt-pc-ss/SP24-XX
- Nafeco, Red Kap CT10 coverall — https://www.nafeco.com/products/red-kap-coverall-twill-action-back/CT10-XX
- garmentdecor, Red Kap CT10 colours — https://garmentdecor.com/product/red-kap-ct10
- Christian Science Monitor, uniform rental industry, 12 January 1993 — https://www.csmonitor.com/1993/0112/12071.html
- Wikipedia, Justice for Janitors — https://en.wikipedia.org/wiki/Justice_for_Janitors
- Wikipedia, Tyvek — https://en.wikipedia.org/wiki/Tyvek
- DuPont, Tyvek 50th anniversary press release — https://www.dupont.com/products-and-services/fabrics-fibers-nonwovens/protective-fabrics/press-releases/tyvek-50th-anniversary.html
- Lakeland Industries company history — https://company-histories.com/Lakeland-Industries-Inc-Company-History.html
- EPA archive, signing of AHERA — https://www.epa.gov/archive/epa/aboutepa/signing-asbestos-hazard-emergency-response-act.html
- Wikipedia, AHERA — https://en.wikipedia.org/wiki/Asbestos_Hazard_Emergency_Response_Act

**Retail, security, mannequins**
- 80.lv, original Backrooms location (Rohner's Furniture) — https://80.lv/articles/the-internet-finds-the-original-backrooms-location
- WPR, Oshkosh and the Backrooms photo (2026) — https://www.wpr.org/news/horror-film-backrooms-meme-oshkosh
- Wikipedia, Levitz Furniture — https://en.wikipedia.org/wiki/Levitz_Furniture
- Penn State World Campus, CRIMJ 304 lesson 2 (Hallcrest reports) — https://courses.worldcampus.psu.edu/welcome/crimj304/less02_02.html
- 9/11 Memorial & Museum, uniform patches C.2008.879.25 and C.2008.879.16 — https://collection.911memorial.org/Detail/objects/122206 , https://collection.911memorial.org/Detail/objects/122205
- Collectors Weekly, What mannequins say about us — https://www.collectorsweekly.com/articles/what-mannequins-say-about-us/
- UAL Fashion Exhibition Making, *Ralph Pucci: The Art of the Mannequin* (MAD, 2015) — https://fashionexhibitionmaking.arts.ac.uk/ralph-pucci-the-art-of-the-mannequin/
- The Glass Magazine, same exhibition (consulted; little detail) — https://theglassmagazine.com/ralph-pucci-the-art-of-the-mannequin-at-museum-of-arts-and-design
- Wikipedia, Adel Rootstein — https://en.wikipedia.org/wiki/Adel_Rootstein
- Wikipedia, Mannequin — https://en.wikipedia.org/wiki/Mannequin
- EuroShop mag, 60 years of mannequins (consulted; no usable text) — https://www.euroshop-tradefair.com/en/media-news/euroshopmag/shopfitting-store-design/60-years-of-mannequins-as-silent-witnesses-to-the-retail-industry

**Office fabric, furniture and colour**
- PIN–UP, Action Office 2 and Robert Propst — https://archive.pinupmagazine.org/articles/the-story-of-action-office-2-and-cubicle-inventor-robert-propst-herman-miller
- The Henry Ford, Robert Propst: Unorthodox Thinker — https://www.thehenryford.org/explore/blog/robert-propst-unorthodox-thinker/
- The Henry Ford, Equa chair seat frame c. 1984 (2012.52.18) — https://www.thehenryford.org/collections/explore/artifact/372434
- Wikipedia, Cubicle — https://en.wikipedia.org/wiki/Cubicle
- Christian Science Monitor, interior colour, 4 November 1983 — https://www.csmonitor.com/1983/1104/110435.html
- Acoustics First, FR701 colour chart page (consulted; only two colours listed) — https://acousticsfirst.com/guilford-of-maine-fr701-style-2100-color-chart.htm

**Hardware**
- Wikipedia, Relay — https://en.wikipedia.org/wiki/Relay
- Wikipedia, Crossbar switch — https://en.wikipedia.org/wiki/Crossbar_switch
- Wikipedia, Number Five Crossbar Switching System — https://en.wikipedia.org/wiki/Number_Five_Crossbar_Switching_System
- Wikipedia, Model 500 telephone — https://en.wikipedia.org/wiki/Model_500_telephone
- Wikipedia, Monochrome monitor — https://en.wikipedia.org/wiki/Monochrome_monitor
- Wikipedia, Snow White design language — https://en.wikipedia.org/wiki/Snow_White_design_language
- Vintage Mac Museum, Mac Plus beige to Platinum — https://vintagemacmuseum.com/?p=2592
- Hackaday, A deep dive into the chemistry of Retrobright (2021) — https://hackaday.com/2021/01/23/a-deep-dive-into-the-chemistry-of-retrobright/

**Originality checks**
- Wikipedia, Slender Man — https://en.wikipedia.org/wiki/Slender_Man
- Wikipedia, Auton — https://en.wikipedia.org/wiki/Auton
- Wikipedia, Backrooms (web series) — https://en.wikipedia.org/wiki/Backrooms_(web_series)

**Tried and failed (claims resting on them are UNVERIFIED)**

| Source | Failure |
|---|---|
| HID history — https://www.hidglobal.com/de/node/1726 | 403 |
| Justia, Rowmark trademarks — https://trademarks.justia.com/owners/rowmark-llc-293860/ | 403 |
| Mannequin Madness blog — https://blog.mannequinmadness.com/?p=18536 | Connection dropped, twice |
| Dezeen on Pucci | 403 |
| Heinz History Center eMuseum object pages | 403 |
| Guilford of Maine FR701 shop page | Connection refused |
| Kane Pixels fan wiki, *Pitfalls* | 402 |
| Furniture Today on IKEA's 1985 US store | Not fetched |
| Two specification PDFs (UAB asbestos procedure, Acoustics First TecSpecs) | Unreadable |

The WebFetch tool cached those two PDFs automatically in this session's tool-results folder. Nothing was saved to the project, and neither file was used.

**Project files read:** `Documentation/RELAY_MODEL_RIG_RESEARCH.md`, `LEVELS_AND_ENTITIES.md`, `LEVEL_MODULE_SPEC.md` §7, `VISUAL_RESEARCH_LOOKDEV.md`, `research/office_and_film/10_synthesis.md` (§0, §5.1–5.2, §6.9), `Assets/Scripts/FrontRoomsRelayRig.cs`, `Assets/Scripts/FrontRoomsMap/FrontRoomsMapHunter.cs`, `Assets/Scripts/FrontRooms3DGame.cs` line 227, `Tools/lookdev/gen_surfaces.py` (colour constants). The contrast script is in the session scratchpad (`contrast.py`), not in the project.
