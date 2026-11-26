# Owner rules

Durable rules and lessons the owner has set for work on autonomous.ai/toys.
Each rule says what to do and why. Where a skill, ADR or doc already holds a
rule, this file only points to it; that source stays the authority.

## Routing

- **Look for an open-source base first.** Before building any toy from
  scratch, search for a design to remix whose licence allows selling (CC0,
  CC BY, CC BY-SA, MIT; not NC, ND or platform-exclusive). Why: a ready base
  saves the whole design.
- **Static or remixed toys go through `autonomous-product-to-cad`.** Build
  them in that sibling repo, pack them with its `toy-archive` skill, and
  publish through this repo ([`docs/PUBLISH_DIRECT.md`](../PUBLISH_DIRECT.md)).
  Only motion toys built from scratch go through Workshop (`design-a-toy`,
  then `build-a-toy`). Why: Workshop's heavy pipeline only pays off for
  mechanisms.

## Choosing ideas

- **Skip marketplace commodities.** Before a concept round or `design-a-toy`,
  check Amazon, Etsy, AliExpress, Temu and Shopee for the same type and a
  near-identical design. If it is already sold, drop it. Why: buyers get it
  cheaper there.
- **Open the real pages in the Paseo browser.** For marketplace and 3D-file
  licence checks (Amazon, Etsy, AliExpress, Temu, MakerWorld, Printables),
  open the search and product pages with the Paseo browser tools
  (`mcp__paseo__browser_*`) and read them, instead of WebFetch or search
  snippets. Use WebSearch only to find links. Close your tabs when done.
  **Shopee is checked by hand:** its bot check returns a captcha after a few
  automated searches even in the owner's session, so list 2-3 Vietnamese
  search terms in the report for the owner or ops to search, and mark
  Shopee "not checked" until they send links. Never solve a captcha, evade
  bot protection (including typing into a site's search box to look human)
  or use proxies. Why: sites block server fetches, so checks that relied on
  snippets missed real listings, prices and licences (owner, 2026-11-09).
- **Sell like the bestsellers.** Compare each idea with Moonlit Atlas, Trotter,
  Windup Warrior and Flexi Axolotl: a beloved, recognisable subject, dense
  detail, many colours, with the mechanism serving a reveal. Why: basic or
  abstract mechanism toys were rejected; desirable subjects sell.
- **Function first.** A new model starts from a concrete everyday job (what
  it holds or does, at real-use sizes), then gets a character that makes it
  unique, like Pelican Catchall. The function may be common; the design may
  not be. Give it one job: one-job items sell better than themed
  multi-function ones. Every compartment holds its real item and empties
  easily, nothing covers a well, a plugged-in cable gets an open slot, and
  every tray belongs to something in the scene. Why: pure decoration
  doesn't sell, and the city trays' bare or covered wells were sent back.
- **Every well reads as a scene element** (owner, 2026-11-13). A well is
  shaped as something that belongs there (a pond, a canal, a boat's hold, a
  tatami deck, a raked garden), so the owner can name it at a glance. Wells
  are never lined up in front of the buildings like bins: the layout reads as
  one scene, such as a lane with buildings facing it. Why: Kyoto's wooden
  tub, stone dish and walled note well read as containers in a row and the
  Stage 4 review was sent back.
- **No cost cap** (owner, 2026-11-10; replaces the US$25 cap of
  2026-11-05). Still estimate and report the price with [Pricing](#pricing),
  but never shrink, hollow or simplify a design to hit a price.
- **Themes are open.** Mix aesthetics (synthwave, vaporwave, art deco…) and
  any subject, not only animals, unless the owner names one.
- **Easter eggs follow the scene.** A hidden story reference comes from a
  moment in that story, preferably in the same place, and is staged
  mid-moment (dropped, thrown, half-done). In the report, name the source
  moment in one line. Why: the owner may not know the story; a lone prop on
  a shelf reads as decoration.
- **No trademarks.** Never use a protected name, logo or official colour set
  (falling-block designs never say Tetris). For a real city, check each
  landmark: avoid post-1990 US buildings and trademarked shapes. Why:
  trade-dress and building-design rights.
- A daily funnel brief for autonomous.ai/toys exists and is the real per-toy
  demand signal; the owner pastes its links when needed.

## Design

- **No Inventor choice in design.** `design-a-toy` does not ask which
  Inventor designs and reads no `TASTE.md`; the contract names `rowan-vale`
  unless the owner names another. Trade-offs follow the owner's answers, the
  chosen concept, readability and printability (owner, 2026-11-10; ADR
  0099). Why: the Inventor only names the listing's author now.
- **Self-review before you show anything.** Before any owner-facing page or
  image, check it against the concept, every Concept Checklist trait, every
  instruction the owner gave in this design (kept as a running list in the
  notes), occlusion from the concept camera, true-scale real objects, and
  printability; fix what you find, then show it with one line per check.
  `design-a-toy`'s "Self-review before the owner sees anything" is the
  authority. Why: results shown unfinished cost the owner many comments.
- **Reference images agree with the contract**, in proportions and landmark
  positions as well as counts. When they disagree and the image looks better,
  amend the contract to match the image. See `design-a-toy` Stage 3b. Why:
  the owner prefers the concept art's look over a blocky contract.
- **The assembly image follows the part images.** Whenever a component image
  or a visible contract feature changes, edit the assembly image in the same
  pass, with the new part images as references, and re-measure it. Why: the
  blind review judges the whole build against it.
- **Concept Checklist traits are required by default.** See `design-a-toy`
  Stage 1 and **Trait at risk** in Stage 3a; ask only with a pictured
  trade-off.
- **Draw objects at true scale.** Headphones, phones and pens in a concept
  image are drawn at real size, with real dimensions stated. Image models
  pull old proportions back from `--ref` inputs; check every image and redraw
  without `--ref` if needed. Still, no AI image decides a size or a fit:
  models shrink real objects (a 51 mm note pad) to make room. Where real
  objects or tight space are involved, show CAD renders at true scale.
- **Judge faces feature by feature.** A whole-trait "agree" missed head tilt,
  eyes, nose and paws the owner saw. Give judges measured close-ups of each
  facial feature.
- **Measure the concept into the contract before redrawing references.**
  References AI-edited from Proof renders inherit the contract's
  simplifications, so a concept-faithful look must reach the contract first.
- **No stickers on surfaces that are often touched or rubbed** (a keycap
  face, a handle, a sliding or gripped part): engrave, emboss or inlay there
  instead. Why: stickers peel off with handling (owner, turtle keycap).
  Decorative surfaces that are rarely touched may use Print Sheet stickers
  ([ADR 0091](../adr/0091-print-sheets-carry-colour-and-detail-on-paper.md)).
- **A person must be able to remove every support by hand.** When designing
  a printed model, check that fingers or pliers reach each support; never
  leave support trapped in a closed or unreachable space. Why: on the
  snowman cap, support above an inner X wall could not be reached, so the
  walls were raised to the ceiling, leaving support only in open chambers
  (owner, 2026-11-05).
- **Prefer one piece in several colours over a separate assembly.** Parts
  that fit in CAD can still be hard to fit together after printing, so print
  them as one piece with a multi-colour print instead. Why: the snowman cap's
  tip and body fitted in CAD but not in real prints (owner, 2026-11-05).
- **A gate's time limit is not a design reason.** When a print-gate check
  times out on a shape, make the mesh lighter and keep the look: union
  strands per sector before the check, use fewer but thicker bundles, or
  tessellate coarser. The shape must still pass at the gate's default
  limit, because Make reruns the gates at that default. Why: the Kyoto
  willow kept a smooth dome cap, which read as an umbrella, because a
  ridged cap's self-intersection check ran past 60 s (2026-11-14).
- **A weeping tree has no cap.** Draw short arching branches off the trunk
  top, with layered strand curtains hanging from them, thicker near the
  top, and gaps through which the trunk and branches show. Why: every dome
  or lump crown on the Kyoto willow read as a mushroom, an umbrella or a
  cloud (2026-11-13/14).
- **Check what shows above the tray rim from the concept camera.** A low
  part just inside the rim shows only its top. A fence there needs both
  rails clearly above the rim. Why: the Kyoto shrine's front fence showed
  only its post tops, which read as a row of red cubes (2026-11-14).
- **A landmark leads its well.** Where a well belongs to a landmark (a
  shrine's stone basin, a temple's pond), the landmark is the area's
  focus by its detail, colour and height, and the well is textured as its
  material, never a plain tub. Why: in the Kyoto precinct the staple basin
  dominated and the shrine read as a shed (2026-11-14). Since 2026-11-16 a
  landmark no longer grows past its true scale to out-area its well (next
  rule).
- **Buildings keep their true relative scale** (owner, 2026-11-16). Size
  each real building from its real dimensions against the scene's scale
  (set by the main building's storeys), and cite the source (a map
  outline, a measured photo) in the notes. Never enlarge a small building
  to make it the focus. Why: the Kyoto Tatsumi shrine, drawn to lead the
  basin, came out far too big beside the machiya and teahouse.
- **One tray or nook, one common scale** (owner, 2026-11-23). Every
  object in it is sized at one scale taken from real objects. Before
  showing the owner, write a scale audit table: each object's real size,
  its correct model size at that scale, its current size and the percent
  off. Fix anything more than 25% off unless a print gate forces it, and
  name that gate. Everything must make sense for a tiny person living
  there: they can walk around, go through doors, climb steps and reach
  the yard. No puzzling object nobody can name. No two solids share a
  face or overlap, because coincident faces flicker in CAD. Why: owner
  review of the New York mini-city organizer.
- **Model a named real object from real photos** (owner, 2026-11-16).
  Before modelling a recognisable real object (a lifeguard tower, a
  basin, a shrine), find 3-5 real photographs, list the cues that make it
  read (a lifeguard tower: hut raised on legs, long ramp, deck rail, flag),
  build those cues, and render the photo beside the model. Why: the Miami
  lifeguard tower was a hut sitting on the sand and read as a food cart.
  Match the photos' colour balance too, at normal viewing distance: the
  colour that covers most of the real object covers most of the model,
  and marks and accents stay small and few. Why: the Kyoto komodaru
  barrels got solid navy and red labels across 140 degrees of each front;
  the real walls read as white straw with black calligraphy and small red
  accents, and the model read as rows of coloured spools or cans.
  A shrine bell (suzu) hangs high under the beam, and its rope hangs from
  the bell (owner, 2026-11-25).
- **Stone reads as stone at a glance** (owner, 2026-11-16). A stone
  vessel or rock is rough-hewn: chiselled faceted sides, no rounded box
  corners, in a grey stone colour, with the props that name it (a bamboo
  spout and ladles for a shrine basin). Why: the smooth cream rounded
  Kyoto basin read as a bathtub.
- **Review every junction in a tight close-up** (owner, 2026-11-16).
  Where two modelled parts meet (a scarf tail under its knot, a lid on its
  box), render the junction at 3-4x zoom from several angles and measure
  the overlap volume between the parts, which must be 0. A whole-part view
  hides a small lip or an interpenetration. Why: the snowman v12 left tail
  poked out above its knot and overlapped it; the leader passed it from
  the normal close-up and the owner caught it.
  Zero measured overlap is not enough: the junction must also look like
  the real thing at normal viewing distance (fabric tucks under a knot
  with a fold and a shadow, never meets it at a flat cut), and fabric
  hangs as it would under gravity. Why: v13 had 0 mm3 overlap but its
  tails still read as tubes stuck onto the knot.
  A visible flaw in geometry carried over from an older version is not
  exempt: fix it, or show it to the owner as an open defect, never pass it
  as "unchanged". Review in the owner's viewer lighting too (flat shading
  with a headlight, as in CAD Assistant). Why: the v5 knot's wedge flaps
  were reported as "kept from v5", and the owner saw them as extra plastic.
  Where parts should meet (a stair's last step and the floor above),
  measure contact at both ends; a render is not evidence (owner,
  2026-11-25). Why: a part can look joined in a render and still end short.
- **A seat reads as its scene object, filled or empty** (owner,
  2026-11-16). Where a real item stands in for a scene object (an earbud
  case as a dry garden's big stone), the seat's own surface carries the
  scene (raked rings round the stone's spot) and the scene continues
  round it, so the owner can name it with and without the item. Why: the
  Kyoto garden's smooth earbud seat read as a blank tray.
- **A device seat is walled on all four sides** (owner, 2026-11-16). A
  seat for a real item (an earbud or iPod case) is enclosed by scene walls
  on every side, open only at the top and at one small finger notch or
  gate just wide enough to lift the item out. It never stands open on a
  yard. Why: the Kyoto earbud case stood open behind a barrel rack and the
  owner wanted it closed in, with only a small way to take it out.
- **Printed fits use total clearance** (owner, 2026-11-13). The value is the
  whole difference between the two sizes, never per side:
  - **Fixed fit** (a tab, peg or leg into a socket): socket = feature +
    0.1 mm. A 1.0 mm square leg goes into a 1.1 mm square socket.
  - **Loose fit** (anything that must rotate or slide: an axle, hinge or
    slider): hole = shaft + 0.2 mm. A 1.0 mm shaft goes into a 1.2 mm hole.

  Write these into every contract joint and Interface. A per-side
  parameter takes half the total (0.05 fixed, 0.10 loose): `cadfits`'
  `fixed`/`snug` 0.05 and `moving`/`slip` 0.10 (the default), and
  `print-details`' `TAB_SLOT_CLEARANCE` 0.05. Where a skill, wiki page or
  tool still gives another value for a printed mate, this rule wins. Why:
  per-side values double the gap the owner wants. Print-in-place joints
  (printed already assembled) keep their larger gaps, and a bought part's
  seat keeps `check_mount`'s 0.10 mm-per-side floor.

- **A slow or timed-out check is never a design reason.** When a gate or
  tool runs too long on the shape the concept needs, fix the check's input
  (union strands, coarser mesh) or its timeout, never the look. Why: a
  Kyoto willow was left as a smooth umbrella dome because the strand
  version's self-intersection check ran past 60 s (2026-11-14).

- **Every scene element is visibly held by the scene.** A rack, stand,
  sign or prop stands on, in or against something that would hold the
  real one (a wall, a storefront, a base that meets the paving), the way
  real photos of it show it mounted. A free end with bare ground beside
  it reads as floating. Look up real mountings and record them with the
  photos' sources. Why: the Kyoto komodaru rack read as standing alone in
  front of its yard until the yard walls were run on behind its end
  (2026-11-17).
- **A same-colour engraving is not a mark.** An engraved or embossed
  pattern in the body's own filament shows only as shadow, and it nearly
  vanishes under flat light at normal distance. Where a mark must read
  (calligraphy, a label), give it a contrasting colour, and check it with
  flat shading and a headlight. Why: engraved Kyoto barrel marks
  disappeared in the flat-light render (2026-11-17).
- **A review page shows the current state only.** Keep a dated, read-only
  copy, then cut the earlier rounds' sections and history from the live
  page. Why: the owner asked for the Kyoto Stage 4 page to be trimmed
  (2026-11-17).

### Assembly kits

Lessons from turning the Amsterdam tray into a user-assembled kit (owner,
2026-11-13/14). Rolife-style kits are the benchmark; their research is in
[`docs/research/book-nook-kits/`](../research/book-nook-kits/README.md), and
[ADR 0092](../adr/0092-kit-assembly-tree-and-manual.md) holds the Assembly
Tree and Manual.

- **A sheet holds only thin flat plates, at most 3 mm thick.** Build volume
  from plates. A part that cannot be flat leaves the sheet as a loose
  printed part, with a written reason. Why: Rolife sheets are all flat
  plates, and thick blocks on a sheet read as a print, not a kit.
- **Build sub-assemblies first, then join them into the whole.** Never slide
  a part between two parts that are already fixed, and never ask for a
  blind insertion. Why: the first pen tower order made the user wedge a
  wall between two fixed walls.
  In a manual review, ask of every step whether an easier assembly exists
  (a sub-assembly built off the model, gears paired before closing). Finish
  everything on a floor before the walls around it go up, unless a check
  shows a wall must go earlier (owner, 2026-11-25). Why: hands need access.
- **Every pushed-in part has a stop** (owner, 2026-11-25), so it cannot go
  too deep and be trapped. Something holds loose paper in place. Prove every
  bar and part insertable along its own path. Why: a part that fits where it
  ends up may still be impossible to put in or take out.
- **No part of another colour shows through the outside of the case.**
  A tab into an outer wall, roof, base or back goes into a blind pocket
  cut from the inside face, leaving at least 0.8 mm of skin outside, at
  the same fixed fit. Hidden LEDs, their leads and lead holes do not show
  either: from outside, a lit part reads as an even glowing shell. Check
  close renders of every outer face, hollows and lit parts before showing
  the owner. Why: the Orrery nook showed the floor's light tabs through
  the walls, a hollow behind the globe niche and an open lamp chimney
  (owner, 2026-11-21).
- **Glue is the last resort.** Join with tabs and slots, pegs, half-laps,
  cross-laps or snaps at the fits above. List any remaining glue joint with
  its reason. Why: the owner counts glue as a design failure; Amsterdam
  went from 9 glue steps to 0.
- **Every freestanding part must survive a knock on the tray.** Trees,
  houses, towers, lamps and boats each need a mechanical hold: deeper
  engagement, a snap or detent, a twist-lock, or a keyed press fit. A
  shallow loose spigot or a slip-over seat is not a hold. If a part must
  lift off, for example a house over its stash cup, use a detent that a
  deliberate lift releases and a knock does not. Show each part's
  engagement depth against its height, and check that it stays seated with
  the tray tilted 45° in any direction. Why: the Amsterdam kit's trees and
  houses fell over when the owner bumped the tray.
- **The whole tray passes a lift test** (owner, 2026-11-19). Lifting or
  tilting the assembled tray must carry every plate and part with it: no
  area without a floor, every plate locked in place, and every pole held by
  press ribs that still hold with the tray upside down. Why: the Miami
  tray's floor and parts did not travel with the tray.
- **Audit the whole Manual before the owner sees it** (owner, 2026-11-19).
  Check every page for every defect class the owner has already named,
  including sub-assemblies first, tilt and hold, and no sliding between fixed
  parts, not only the pages they cited. Why: fixing only the cited pages
  left the same defects on others for the owner to find again.
- **Every gate must be cut with nippers.** Put gates on straight,
  outward-facing edges, never in a channel between protrusions. Keep at
  least 6 mm clear for the jaws on both sides of each gate. Never let a
  fragile tip point at a gate or at the frame, and never tie a tip to the
  frame by a gate on its apex: the cut leaves a stub on the most visible
  point. Turn the part so its points face open sheet space instead. Why: the owner could not see
  how to cut out a parapet whose gates sat between its pinnacles.
- **Minimum loose part size:** at least 1.6 mm thick, a short side of at
  least 4 mm, and at least 35 mm² to grip. Add one spare, marked "+", for
  each part under 15 mm. Why: Rolife cuts nothing smaller than about 4 mm.
  Spares are the default. A kit with very many tiny parts may ship none
  when the owner approves, declared with `"spares": "none"` on its
  `assembly_tree`; then no part carries a spare (owner, 2026-11-26, New
  York kit: spares would nearly double it).
- **Every printed part is one connected solid** (2026-11-16). Check each
  loose part and each sheet part for its solid count before a manual or
  price is shown. Factory splits a STEP by solid, so a sliver cut free by
  a pocket prints as a stray piece the manual never names. Why: Amsterdam
  T03 carried 3 paving bars cut free behind the stash cups.
- **Stored items come out toward the user** (owner, 2026-11-16). A desk
  tray's note pad, card or other item a person takes often comes out
  from the front edge, the side facing the person, never from the side
  or the back. Why: the Miami note pad options opened on the tray's
  side, and the owner wanted it taken from the front as the natural move.
  Front access keeps the rim whole (owner, 2026-11-17): cut one finger
  scallop through the front rim, the smallest that lets two fingers pinch
  the item, its bottom at the seat's floor. The floor under the item stays
  solid: a notch may reach the floor but never pass through it. Why: the
  Miami pad's 51 mm lowered rim and its finger groove through the beach
  plate left an open gap the owner rejected.
- **Hidden storage must be reachable.** A finger cannot reach into a cup
  21 mm deep and 9 mm wide. Use a shallow cup (about 9 mm) that lifts out by
  a pull tab, and say what it holds.
- **Every Manual step reads on its own:**
  - an anchor part already sits on the table;
  - each new part is drawn at its destination, with an arrow that ends on
    the slot or tab it enters;
  - the camera stays the same within a sub-assembly: the same angle and
    the same scale, so do not crop each figure to its own contents;
  - turning the model over is its own step, marked with a turn icon, and
    its text says which face goes down;
  - the text matches the picture;
  - no step only holds parts in mid-air;
  - a step adds one kind of part, or a few that go in the same way.

  Draw new parts in their own colour with a bold outline, and fade earlier
  parts to grey. A white or grey new part is drawn darker than the faded
  parts it lands on. Lighten dark colours. Put a part-ID bubble on every
  figure. Fill each page: no page leaves an empty quarter while its
  figures are small. The cover, page title and every other mention name
  the kit "[Name] Build Kit" (`docs/TOY_NAMING.md` Rule 5). Why: steps 13–15
  of the first pen tower manual could not be followed, and the dark brown
  pages were unreadable; the Miami manual repeated Amsterdam's zoom jumps,
  grey-on-grey steps and empty quarters (owner, 2026-11-15).
- **Do not print fine foliage.** Rolife builds plants from florist wire,
  a crepe-paper trunk and printed paper leaves or flock (DH201-19..23, -44).
  On a printed toy, choose plants whose form prints well, such as cherry
  blossom clusters, over fine strands such as a willow. Otherwise print only
  the trunk and branches and use Rolife's paper or flock layer for leaves.
  Why: the Kyoto willow took nine Proof rounds and still read as a
  mushroom, an umbrella, a palm and then lampshades (owner, 2026-11-14).
- **Make trees simple, not sculpted.** Do not model a tree crown as a 3D
  mass of bumps or puffs. Use a simple technique that reads at once and
  takes few assembly steps: crossed flat silhouette plates, tiered flat
  canopy discs, or a printed trunk with Rolife-style paper or flock
  blossom. Show the owner true-scale mockups of two or three techniques
  before spending Proof rounds on one. Why: the owner called the Kyoto
  cherry's 3D bubble crowns ugly after two Proof rounds (2026-11-15).
- **Every flat decor panel has one exact place.** Paper-cut style blossom
  or leaf panels (printed or bought) mount on keyed tabs or sockets that
  differ per panel, so none fits the wrong place or face. Number each
  panel and its socket to match, and give the manual a labelled placement
  diagram plus steps whose arrows end at each socket. Never "glue the
  clusters along the branch". Why: approving the Kyoto paper-cut cherry,
  the owner required that the assembler know exactly where every panel
  goes (2026-11-15).
- **Do not taper a printed crown's underside to hide its flat print face.**
  A blossom crown that prints right way up keeps a thin flat band under
  its domes. Keep it, and judge the crown from the concept camera, which
  sees mostly its top. A taper steep enough to print without supports
  smooths away the puffs and the drooping lobes on the underside. Why: the
  Kyoto cherry's tapered crowns (round 11) passed every gate but read as
  cupcakes, so they were reverted to round 10's band (2026-11-15).
- **Join neighbouring plates to each other, not only to a base.** Walls,
  floors and parapets that meet should interlock (tab and slot, cross-lap,
  corner half-lap), so each sub-assembly holds on its own before it meets
  the next plate. A ring of parts that each stand only in a base plate is
  weak and harder to build. Why: the owner asked for the Amsterdam pen
  tower's floor and side walls to join as one frame first, and its four
  crown parapets to join at the corners (2026-11-16).

  A joint means **both** plates are cut so they lock into each other: a
  half-lap or cross-lap (each plate slotted half its height), a finger
  joint (each end cut into fingers that interleave), or a tab that passes
  through a slot in the other plate. These are not joints: a plate end
  pushed into a corner groove or rebate of the other plate, or a tab on
  one plate pressed against the other plate's plain face. Every manual
  step must also hold the part it adds: a part let go of right after it
  goes in stays where it is, held by its joint, without waiting for a
  later step or a hand. Stacked parts (shelves and the rows they carry)
  build from the bottom up, each layer locking into the one below. Why:
  in the Kyoto manual review the owner found plate ends set into corner
  grooves again (the shrine hall, the storehouse skirts, the tea deck
  walls), after asking for real joints several times, a barrel rack whose
  rows were only laid in, and stone lanterns whose post frame did not
  join their hat (2026-11-22).
- **Keep a part loose only after trying to build it from plates.** Boxes,
  trays, cups, rings and drums can be built from flat sheet plates, as
  Rolife does. For every loose part, record the plate build you tried and
  why it failed: a visible seam, a plate over 3 mm, or a wall too thin. Why:
  the Miami kit kept 34 loose parts, and the owner saw that more of them
  could be plates (2026-11-16).
- **A small scene prop must read at a glance.** A towel, a bag or a sign
  needs its telling detail (a fringe, bold contrasting stripes, a rumpled
  edge) and a colour that stands out from its ground. Judge it from the
  concept camera. Why: the owner could not read the Miami beach towel as a
  towel (2026-11-16).
- **The manual lists loose parts too.** Besides the sheet maps, a kit
  manual has a loose-parts inventory: every printed part not on a sheet,
  pictured in its colour with its ID, name, count and spares. Every step
  that uses one shows its ID bubble. Why: the Amsterdam manual showed only
  the sheets, so the loose parts had no place in it (owner, 2026-11-16).
- **Bought parts get one picture page** (owner, 2026-11-25), each with its
  ID and count like the printed parts, with no long detail. Say plainly
  which bought items ship and which the buyer supplies.
- **Every listed ID is used in a step**, printed or bought (owner,
  2026-11-25). A kit with LEDs has steps to mount them, route and hold the
  wires, test the light before closing, and reach the battery. Why: an
  unused ID or a missing wiring step leaves the buyer guessing.
- **Kit manuals look alike** (owner, 2026-11-25). Legend, callouts and
  wording are the same across kits; Amsterdam's manual is the model.
- **Every manual step states each part's orientation.** Say in the text
  and show in the picture whether a part stands on its long edge or lies
  flat, and which face points where. A sub-assembly built lying down gets
  no "When done" or "Finished" inset of it standing: the step pictures
  are enough (owner, 2026-11-20, after a repeated inset for the same
  ledges read as a puzzle). Label plates by role ("B03
  front", "B11 floor") where a lying plate could read as a base. Why: the
  owner could not tell whether the Amsterdam back-rests stand or lie, and
  read the pen tower's face-down front wall as its base (2026-11-15).
- **No "After step N" or "Finished" inset in any manual step** (owner,
  2026-11-25). Keep each phase's opening picture, cut views and the final
  Finished page. Why: in the Orrery manual the insets cluttered the steps
  more than they helped.
- **A simple object is one phase** (owner, 2026-11-25). Why: the Orrery
  chair was split into several tiny phases, though it is simple to build.
- **Keep a city kit's details; never join items with a visible bar to cut
  the part count** (owner, 2026-11-25). Why: the owner wants the New York
  kit to keep the details of the approved model, so a smaller count is no
  reason to merge bins, fruit or stepping stones on a strip.
- **Check every manual page for clipping before the owner sees it.** A
  figure, sheet map or text running off the page is a defect even when
  every gate passes. Look at every page at full size, and check
  overflow by machine. Why: the Amsterdam manual sent for approval had a
  sheet map cut off on page 3 and four more clipped pages (owner,
  2026-11-15).
- **Audit a kit against every rule here before the owner sees it.** Write
  a table, one row per Assembly kits rule: status, evidence (page, step or
  render), fix. Show it with the manual. Why: the Miami kit manual repeated
  the Amsterdam kit's defects (camera jumps within a sub-assembly, small
  figures, the tray's name on a kit, thick loose parts) although every one
  was already a rule here (owner, 2026-11-15).
- **Check sheets with the host's own gate while designing.** A kit's
  design scripts must run `kit_sheets.py check` (and the print gates) on
  every sheet before the owner sees a sheet map or manual, never only a
  local copy of the rules. Why: the approved Amsterdam manual's sheets
  failed the host check at seal (4 missing spares, 5 gates the jaws could
  not reach), so the approved manual had to change. The host check reads
  footprints and gates, not print physics: also run the print gates on
  every finished sheet cell, because a tab can print in air while
  `kit_sheets.py check` passes (Miami parapet ring, 2026-11-15).
- **Run the full print gates on every Component before the seal.** The
  seal's preflight (`seal_proof.py preflight`) runs only the cheap gates and
  no print gates; `check_mesh`, `check_overhang` and `check_thickness` first
  run inside the seal itself and again in the build's final verification,
  each pass over an hour. Run them on each Component's `.step.py` yourself
  (minutes each) and fix every wall, taper and overhang first. Why: the
  Miami kit passed preflight, then the seal refused a 0.13 mm tooth and a
  0.55 mm rim wall in the kiosk drum, costing another seal chain (owner,
  2026-11-21).
- **The play feature is the hero.** Size the scene so the mechanism reads
  first, for example by widening the canal so the drawbridge is large.
- **A mechanism concept is not proven by a clash check.** Before
  proposing one, trace the motion: name the faces that touch in each
  direction, the clearance and engagement depth at each, the end stops, and
  what happens if the user turns or pushes the wrong way. Sample the true
  kinematics, not a linear stand-in, and check binding. Why: the Miami kiosk
  drawer passed its clash check, but its yoke slot had no face to push the
  drawer out and nothing stopped the crank from turning the wrong way.
- **Report every visible change against the published toy**, such as a
  dropped post, a loose part or a seam.

### Image models

Model choice per edit is in
[`design-a-toy` LESSONS-REFERENCE-IMAGES.md](../../.claude/skills/design-a-toy/LESSONS-REFERENCE-IMAGES.md)
(sunburst keeps the source best; gpt-5.4 follows spatial instructions best;
run both and pick). Facts it lacks:

- `openai/gpt-image-2.5-sunburst` is image-only: call `POST {base}/images`
  with `input_references`; chat/completions returns 404, and `/images/edits`
  or `/images/generations` ignore the input image.
- When sunburst's safety filter refuses a neutral prompt, run the same prompt
  on gpt-5.4 instead of rewording.
- To show something inside a fold, ask for a cutaway ("sliced in half down
  its middle, look at the cut face"); gemini-3-pro drew the best one.
- A thin part seen edge-on gets drawn as a bent pipe; use a three-quarter
  view or let the contract's numbers carry it.

## Naming

Every public toy name follows [`docs/TOY_NAMING.md`](../TOY_NAMING.md). Run
its checklist on every name you propose or pass on (wish name line,
`--title`, concept pages).

## Pricing

Factory sets the listing price; Workshop sends none
([`docs/PUBLISH_SEALED_PRODUCT.md`](../PUBLISH_SEALED_PRODUCT.md)). To
estimate it:

- price = ceil to the dollar of ($0.052 per gram × measured mass + $15 ops
  fee + extra materials); no print-hours term, 0% margin (since 2026-11-02).
- Mass is measured by OrcaSlicer with one fixed preset for every design:
  Bambu A1, "0.20mm Standard", 15% crosshatch infill, 2 walls, tree support
  past 45°, Bambu PLA Basic, auto-orient and arrange. Support counts.
- The contract's infill and material are never read. So cutting support and
  solid volume lowers price; lowering contract infill does not.
- Source: `autonomous-ai/panda-social-backend`, `models/slice_job.go` and
  `internal/slicer/orca.go`.

## Running builds

- **Pass `--agent claude`** on every `workshop wish` and `workshop fix`, and
  show it in the command the owner approves. Why: the CLI defaults to Codex,
  whose bwrap sandbox failed to start on the owner's build machine, and the
  agent is frozen per run.
- **"workshop fix" means `workshop fix`** on the last completed build, with a
  brief naming only what changes; never a fresh `workshop wish`. Quote the
  owner's exact words about the flow in any handoff. Why: a fresh wish
  rebuilt all ten parts of one toy for ~40 cost units.
- **Answer run needs yourself**, including a fix that changes what a
  reference shows. Decide the fix, record it in the notes and ledger, answer
  the run, and report the decision afterwards; don't bring the owner
  options. Why: only the agent that drives the build knows what the contract
  meant. See `build-a-toy` "Decisions: the loop answers every contract need
  itself".
- **Compare runs by repeated print defects**, not the failure rate (see
  **Repeated Print Defect** in [`CONTEXT.md`](../../CONTEXT.md)). Why:
  repeats show blind repair, which burns tokens.
- **Rank token levers by cost**, not raw count: cached input, fresh input and
  output are priced differently (cost units in
  [`build-a-toy` LEDGER.md](../../.claude/skills/build-a-toy/LEDGER.md)).
  Why: cache-hit polling was 4% of cost despite 11M tokens.
- **Judge a fix run by new rounds and the stage reached**, not by
  `tally.py`'s lock count, which counts Components carried from the source
  run as locked.
- **Let a running build publish** (owner, 2026-11-18): never stop or
  interrupt a build already running with publication on just to hold its
  publish for owner review. Ask first only before launching a new toy's
  `workshop wish` or `workshop fix`, as before. Why: the toys page has no
  audience yet, so an unreviewed publish costs nothing, and stopping a run
  wastes it.

## Approvals

Wait for the owner's explicit OK before any of these:

- a `workshop wish` or `workshop fix` launch (show the exact command). One
  OK per toy for its unattended `build-a-toy` loop covers every launch in
  that loop;
- a publish, or any change to a live listing, including a rename. A
  build already running with publication on publishes without a new OK
  (see **Let a running build publish**);

**Decide obvious choices yourself** (owner, 2026-11-19). When one option
clearly fixes a defect and the other only tolerates it, or when an owner
rule already implies the answer, choose, act and report what you chose and
why. Ask the owner only for a real trade-off of taste or price, or for a
publish or live-listing change. Why: the owner, on the Miami tray floor:
"những quyết định kiểu này bạn cứ tự chọn rồi feedback với tôi" (choose
decisions like this yourself, then report back).

Harness fixes, including those made during a build loop, go through a PR;
never push to `main` and never force-push. **Merge a PR without asking**
(owner, 2026-11-08) once it adds no test failure that `main` does not already
have and weakens no production gate; report what was merged afterwards. Why:
waiting for an OK on every PR kept stalling builds.

## Repository and reports

- **Record every lesson here by PR as soon as you learn it.** Whenever the
  owner corrects work, or you find a rule that would have prevented a
  defect, add it to this file (or to the skill that owns it) in a small PR
  the same day, with its Why. Merge it under the usual rule. Why: lessons
  kept only in an agent's memory do not reach the other agents (owner,
  2026-11-14).
- **Never commit new files under `toys/`, `toys-spec/` or `inbox/`**; see
  `AGENTS.md` working rules. Say they were synced to the main checkout.
- **`inbox/` holds only files the owner sends in.** Read them without
  changing them; never write outputs, renders, reports or new versions
  there. Write work to a folder under `toys/` (for example
  `toys/<model-name>/`). Why: the owner uses `inbox/` only to hand files to
  agents, and work mixed into it cannot be told apart from what they sent.
- **Keep questions and reports short**: only what the decision needs. The
  owner reviews pictures, not contracts; ask about how a toy looks and what
  it does, never about rows or millimetres.
- **Give each file as a full absolute path**, one per file, never a folder
  plus bare names. Why: the owner clicks them.
- **Embed every image in an HTML page for the owner** as base64 (~900px
  WebP). Why: the session runs on a server and the owner opens pages on
  their own machine. Concept pages follow `brainstorm-concepts` (Vietnamese
  page, standalone copy, a pick only marks it chosen).
