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
  licence checks (Amazon, Etsy, AliExpress, Temu, Shopee, MakerWorld,
  Printables), open the search and product pages with the Paseo browser
  tools (`mcp__paseo__browser_*`) and read them, instead of WebFetch or
  search snippets. Use WebSearch only to find links. Shopee needs the
  owner's logged-in session and sometimes a captcha the owner solves; never
  solve a captcha or evade bot protection yourself, and never use proxies.
  For Shopee, navigate the owner's already-verified Shopee tab (find it with
  `browser_list_tabs`) instead of opening a new one, which gets a captcha;
  leave that tab open. Close your other tabs when done. Why: sites block server fetches, so checks
  that relied on snippets missed real listings, prices and licences
  (owner, 2026-11-09).
- **Sell like the bestsellers.** Compare each idea with Moonlit Atlas, Trotter,
  Windup Warrior and Flexi Axolotl: a beloved, recognisable subject, dense
  detail, many colours, with the mechanism serving a reveal. Why: basic or
  abstract mechanism toys were rejected; desirable subjects sell.
- **Function first.** A new model starts from a concrete everyday job (what
  it holds or does, at real-use sizes), then gets a character that makes it
  unique, like Pelican Catchall. The function may be common; the design may
  not be. Why: pure decoration doesn't sell.
- **Cost cap: under US$25 per unit**, counting print and bought parts (owner,
  2026-11-05). Estimate with [Pricing](#pricing).
- **Themes are open.** Mix aesthetics (synthwave, vaporwave, art deco…) and
  any subject, not only animals, unless the owner names one.
- **Easter eggs follow the scene.** A hidden story reference comes from a
  moment in that story, preferably in the same place, and is staged
  mid-moment (dropped, thrown, half-done). In the report, name the source
  moment in one line. Why: the owner may not know the story; a lone prop on
  a shelf reads as decoration.
- **No trademarks.** Never use a protected name, logo or official colour set
  (falling-block designs never say Tetris). Why: trade-dress risk.
- A daily funnel brief for autonomous.ai/toys exists and is the real per-toy
  demand signal; the owner pastes its links when needed.

## Design

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
  without `--ref` if needed.
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
