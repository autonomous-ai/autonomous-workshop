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
  focus. From the concept camera its visible area is clearly larger than
  the well's (measure both), and the well is textured as its material,
  never a plain tub. Why: in the Kyoto precinct the staple basin dominated
  and the shrine read as a shed (2026-11-14).
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
- **Glue is the last resort.** Join with tabs and slots, pegs, half-laps,
  cross-laps or snaps at the fits above. List any remaining glue joint with
  its reason. Why: the owner counts glue as a design failure; Amsterdam
  went from 9 glue steps to 0.
- **Every gate must be cut with nippers.** Put gates on straight,
  outward-facing edges, never in a channel between protrusions. Keep at
  least 6 mm clear for the jaws on both sides of each gate. Never let a
  fragile tip point at a gate or at the frame. Why: the owner could not see
  how to cut out a parapet whose gates sat between its pinnacles.
- **Minimum loose part size:** at least 1.6 mm thick, a short side of at
  least 4 mm, and at least 35 mm² to grip. Add one spare, marked "+", for
  each part under 15 mm. Why: Rolife cuts nothing smaller than about 4 mm.
- **Hidden storage must be reachable.** A finger cannot reach into a cup
  21 mm deep and 9 mm wide. Use a shallow cup (about 9 mm) that lifts out by
  a pull tab, and say what it holds.
- **Every Manual step reads on its own:**
  - an anchor part already sits on the table;
  - each new part is drawn at its destination, with an arrow that ends on
    the slot or tab it enters;
  - the camera stays the same within a sub-assembly;
  - the text matches the picture;
  - no step only holds parts in mid-air.

  Draw new parts in their own colour with a bold outline, and fade earlier
  parts to grey. Lighten dark colours. Put a part-ID bubble on every
  figure. Why: steps 13–15 of the first pen tower manual could not be
  followed, and the dark brown pages were unreadable.
- **The play feature is the hero.** Size the scene so the mechanism reads
  first, for example by widening the canal so the drawbridge is large.
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

## Approvals

Wait for the owner's explicit OK before any of these:

- a `workshop wish` or `workshop fix` launch (show the exact command). One
  OK per toy for its unattended `build-a-toy` loop covers every launch in
  that loop;
- a publish, or any change to a live listing, including a rename;

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
