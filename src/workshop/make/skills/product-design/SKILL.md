---
name: product-design
description: Design a product the user described in words the way an industrial designer would, before any CAD, so it comes out beautiful as well as working - survey existing products and the best-looking precedents, turn the survey into requirements, set a design direction (character, form vocabulary, proportion, silhouette, stance, colour-material-finish), compare two or three concepts and select one, size it from sourced anchors, and review the built model in recorded design-critique rounds. Ends in the same buildable `<name>_spec.md` that image-to-cad writes. Use when the user asks for an object in prose ("a phone stand", "a walking horse toy", "a candy bowl shaped like a ghost") with no reference image defining its exterior, and its form, size, features or mechanism are still open. Not for a fully dimensioned literal part (that is the cad brief) or an image to reproduce (that is image-to-cad). Writes a document, no geometry.
---

# Product design — design the object before CAD builds it

## Purpose

A reference image arrives with its design already made, and `$image-to-cad`
reads it. A prose request arrives without one: "a phone stand" fixes a category
and nothing else. Handed straight to `$cad`, the CAD turn becomes the designer
and builds the first shape that satisfies the words — a block with a slot, one
small fillet on every edge. No gate notices: every geometry check passes an
object nobody would want on their desk.

This skill is the designer the flow was missing. Work the way an industrial
designer does: understand what the object is for and who lives with it, study
how it is already made and which versions people find beautiful, set a design
direction before drawing anything, explore concepts and choose one on purpose,
and then **critique the built model in rounds until it looks right**. The
object must work, print and fit — and it must be beautiful. Beauty is not left
to whatever the first CAD pass produces; it is a requirement, designed in order
(big form to detail) and reviewed against written rules
(`wiki show product-aesthetics`).

**You produce a document, not geometry.** Fill `templates/design_spec.md` and
hand off to `$cad`; the design-review rounds then run on `$cad`'s renders and are
recorded back in the spec.

**Inside a Workshop product run** resolve
`CAD_SKILL_ROOT="$(workshop skills path)/cad"` and
`IMAGE_TO_CAD_SKILL_ROOT="$(workshop skills path)/image-to-cad"`, and read a
`skills/<name>/...` path in these pages under
`"$(workshop skills path)/<name>/"`. Upstream's `$stl-to-step` and
`$step-to-source` are not Workshop skills; a supplied STL or STEP still does
not fire this one. Five things change there:

- **It fires only while the design is open**: a prose Wish with no sealed
  Invent concept, Design Contract or reference image. A sealed concept or
  contract *is* the design, so its survey, direction and concept selection are
  never reopened here; an image to reproduce goes to `$image-to-cad`.
- **The selected Inventor's `TASTE.md` governs creative judgment.** The design
  direction works inside it, and the Wish's words stand where this page says
  the user's words do. There is no user to ask or to accept a finding.
- **Review rounds spend Make's own allowance.** They run inside the round and
  review budget the host froze, never replace the Make reference's blind
  signature review, and stop when that budget does; a finding still open then
  is reported in the final response, not chased past it.
- **The spec lives in the run's CAD project**, beside the entries `$cad`
  builds, not under `output/`.
- **Final verification is the one the Make reference names.** Do not add
  `--fresh` in a product run: the host performs the isolated fresh rebuild.

## Route

```text
prose names a product, design open   -> product-design -> <name>_spec.md -+
image defines the exterior           -> image-to-cad   -> <name>_spec.md -+-> [electromechanical-integration] -> cad
prose fully dimensions a literal part ------------------> cad brief ------------------------------------------> cad
```

- **Fire** when the request names an object and leaves any of form, size,
  features or mechanism open. Scale the depth: a one-piece holder gets a
  three-row survey, one direction paragraph and a short spec; a toy mechanism
  gets the whole loop. Every depth keeps the direction and the review rounds.
- **Do not fire** for a literal, dimensioned part ("100 × 60 × 6 mm plate,
  four M4 holes") — `$cad`'s `references/cad-brief.md` is enough — nor for an
  edit to an existing project, nor for a supplied STL/STEP (`$stl-to-step`,
  `$step-to-source`).
- **An image supplied as loose inspiration** ("something like this, but for
  two phones") with prose that changes the design: this skill owns the design
  and the image is one survey row. An image to reproduce is `$image-to-cad`.
- **A functional electrical load or a driven part**: the concept selection
  names the mechanism archetype and the power boundary, then
  `$electromechanical-integration` runs before 6g closes.

## The loop

```text
read request -> survey products + precedents -> requirements -> design direction
     -> concepts -> select -> form + size -> decompose + operations -> self-critique
     -> [cad builds] -> design review round -> revise -> review ... -> deliver
```

Diverge, then converge, twice: many survey rows and concepts narrowed to one;
then one concept refined in review rounds. Read this file once at the start of
the design turn; load a wiki page or a sibling template only when its step
names it.

### Step 1 — Read the request (spec §1)

- Copy the request verbatim. Every value the user stated is `[observed]` and no
  survey row overrides it.
- Resolve the job in one sentence, who uses it (adult, a child of a stated or
  assumed age, display only), where it lives and from where it is seen (desk,
  shelf, wall, floor, hand), what it must fit or hold, how it is made (the
  declared bed, material and nozzle) and whether it moves or is powered.
- Name the archetype and the construction family — prismatic holder, shell or
  enclosure, revolved vessel, organic figure, flexi, mechanism.
- Before creating `output/<name>/`, check whether another run already made it;
  several agents may work from one prompt.
- Ask only when a fit-, safety- or compliance-critical fact is missing and no
  source can supply it (a mount for a device the request does not name).
  Everything else — including taste — is decided, tagged `[assumed]` and stated
  in the final response.

### Step 2 — Survey products and precedents (spec §2)

Search the Internet for how the thing is already made before inventing it.
This is the one step where a product-category query is the right query.

1. **Products.** Query the category with the user's qualifiers — `ghost candy
   bowl`, `walking horse toy mechanism`, `phone stand cable` — across commercial
   products, published printable designs (Printables, MakerWorld, Thingiverse,
   Cults) and their reviews. Keep three to five rows: URL, kind, overall size
   and how it was obtained, features, what reviews praise and complain about,
   licence.
2. **Aesthetic precedents.** Separately find two or three of the
   *best-looking* designs of the kind or of the character you are after —
   design-award listings (Red Dot, iF, Good Design), the most-liked published
   models, respected brands. For each, write what gives it its look (one
   continuous lean line, a single generous radius, a lifted base, a two-colour
   split), never its dimensions.
3. Derive: **baseline features** (in most rows; §3 includes or rejects each),
   **recurring complaints** (each becomes a requirement or a stated non-goal),
   the **size band**, and the **differentiator** the user's words ask for.
4. A login wall or network failure is `unavailable`, never a miss. A search
   that ran and found nothing is a recorded `MISS`.
5. The survey informs the design and never supplies geometry. Do not copy or
   trace a design's shape or files unless its licence permits it and §2 records
   that. A unique subject — a character, a particular animal — has no product
   analog: survey how that *kind* of object is built and made appealing
   (flexi figures, designer toys, candy bowls) and say that is what the rows are.

**Boundary with `$design-reference`.** The survey answers *what the product
should be and look like*. `$design-reference` answers *how one feature is
built* and runs later, from §6d, once a construction question exists. Named
devices and standard elements are `$step-parts` and `stdpart` (§6c).

### Step 3 — Requirements (spec §3)

One row per requirement: a measurable target, its source (request, survey
baseline, survey complaint, wiki page, standard, bed), its priority (must,
should, won't) and how it is verified — a named gate, a `measure/check_spec.py`
assertion, or a named review item. A *must* with no verification is a wish.

Appearance requirements are rows like any other: the silhouette reads from the
main view, the governing proportions (asserted ratios), the focal feature, the
colour split. Search the wiki on the product's category and function words
(`python "$(workshop skills path)/wiki/scripts/wiki" search <words>`); the pages that most often apply are
`product-aesthetics`, `form-and-finish-heuristics`, `fdm-surface-finish`,
`handheld-ergonomics`, `stability-and-tipping`, `toy-safety-constraints` and
`design-for-assembly`, plus the printing and mechanism pages.

### Step 4 — Design direction (spec §4a)

Set the direction before any concept, from `wiki show product-aesthetics`:

- **Character** in three words (calm, precise, friendly; playful, chunky,
  bold), taken from the user's words, the user and the precedents.
- **Form vocabulary** — one geometry family (soft, geometric or organic), a
  radius family of two or three sizes each tied to an edge class, one repeated
  lean or taper angle, and the lines that must continue across the object.
- **Proportion and hierarchy** — the primary, secondary and tertiary forms,
  the governing ratios with unequal divisions, the one focal feature, and where
  the calm surfaces are.
- **Silhouette and stance** — the view people see it from, what the black
  silhouette must say from that view, and whether it sits low and heavy or
  lifted on an inset base.
- **CMF** — a dominant colour and an accent (the filament palette the user has,
  or `[assumed]` defaults), where each goes, boundaries on edges or grooves,
  and the finish (matte, silk, textured bed face).
- **Print as part of the look** — which faces are A-surfaces, so print
  orientation keeps supports and the seam off them.

Every later choice traces to these lines; a feature that serves none of them is
removed.

### Step 5 — Concepts and selection (spec §4a)

- Two or three concepts that each express the direction through a *different
  form idea* — not three sizes of one idea. An object with one sensible answer
  (a ring for one finger) carries one concept and the reason.
- Describe each concept by its primary form, its secondary forms and its
  silhouette from the main view.
- Score every concept against the must and should rows, appearance rows
  included, in one table. A concept can lose on looks alone.
- Select one; record the nearest rejected concept, why it lost, and the one
  edit that would switch to it. The selection becomes the exterior-construction
  row of 6g, and the mechanism row when it moves.
- Decide; do not ask the user to choose.

### Step 6 — Form and size (spec §4b, §5)

- **§4b** describes the selected concept big to small: the primary form, then
  each secondary form, then the tertiary detail, then the top, front and side
  views. It names every landmark a person recognises the object by; with no
  photo, this text is the contract the renders are reviewed against.
- **§5** sizes every dimension from an anchor — stated by the user, a cited
  device or standard specification, ergonomics, the survey band, the bed, or
  arithmetic on those — and carries the **proportion ledger** (the governing
  ratios, asserted in `measure/check_spec.py`) and the **radius family** as
  named values. Tag user-stated and cited values `[observed]`, derived ones
  `[inferred]` with the arithmetic, and defaults `[assumed]` as a one-edit
  correction. Never write "about".
- A fit dimension names the value both halves derive from; `$cad` derives the
  second half with `cadfits`. The declared bed goes here as `--bed WxDxH`.

### Step 7 — Decompose, source, operations (spec §6–§8)

From here the spec is the image-to-cad build spec. Fill §6a–§6g, §7 and, when
a load is functional or a part is driven, §8, with the table shapes and rules of
`skills/image-to-cad/templates/build_spec.md` and `build_spec_powered.md`:
one printed part unless the split test fails (a split lands on an edge or a
reveal, never mid-surface), a catalog search on the governing numbers for every
standard element with misses recorded (6c), seats derived from the supplier
STEP (6e), `$design-reference` only for a real construction question (6d), one
selected design per active domain (6g), an operation and a selector for every
feature (§7), and a feasibility `assert` for every driven mechanism (§8).

### Step 8 — Self-critique

Before handing off, confirm:

- every *must* has a verification; every baseline feature and recurring
  complaint is answered;
- the direction is complete and every §4b feature traces to it;
- the size sits inside the survey band, or §3 says why not;
- 6g is complete: `$cad` can build without choosing among alternatives;
- the print pre-read holds — A-surfaces off supports, no overhang past 45°
  without a reason, no wall under two lines, the part fits the bed;
- the document passes its own gate:
  `.venv/bin/python "$CAD_SKILL_ROOT/scripts/check_spec_format" <project>/<name>_spec.md`.

## Design review rounds

The first build is a draft. A designer does not ship the first model, and
neither does this skill: once `$cad` has built the combined entry, review it as
a design critique, in rounds, and record each one in the spec's **Design review**
table.

1. **Render** front, side, top, iso and the view people see (as `AZ,EL`),
   shaded, and the main views as black silhouettes, then look at every image:

   ```bash
   .venv/bin/python "$CAD_SKILL_ROOT/scripts/render_review" <entry> --view front --view right \
     --view top --view iso --view <AZ,EL> -o <project>/snap/review
   .venv/bin/python "$IMAGE_TO_CAD_SKILL_ROOT/scripts/render_views.py" <entry> --view front \
     --view right --view top -o <project>/snap/silhouette
   ```
2. **Critique** against `product-aesthetics`'s design review checklist, in its
   order — silhouette, proportion, hierarchy, radius family, lines, stance,
   colour, A-surfaces, direction — and against §4a and §4b. Write each finding
   as what is wrong, which checklist item it breaks, and the source change that
   fixes it.
3. **Revise** in the generator, rebuild the affected entry in the same round,
   and review again. A change to a parameter, proportion or part count is
   reconciled into the spec.
4. **Stop** when a round finds nothing on the checklist. A visible product gets
   at least two rounds unless the first finds nothing. When the same finding
   survives three rounds of detail edits, the fault is in the primary form or
   the concept: change that, not the detail.

Review renders are visual evidence, not a gate; report them as such. They
never replace validate, interference, fit, mesh or thickness, which run on the
stabilised source as `$cad` requires.

## Handoff to cad

The spec lives at `output/<name>/<name>_spec.md`, inside the project `$cad`
builds; `verify_project` reads it there and runs `check_spec_numbers` and
`check_spec_format` on it in every mode.

| Spec section | Becomes |
|---|---|
| §5 Size, radius family | the named parameters, each with its provenance comment |
| §5 proportion ledger, §3 must rows | `measure/check_spec.py` assertions, or the named gate that owns each |
| §4a direction, §4b landmarks | the design review rounds on `$cad`'s renders |
| §6–§8 | exactly what the image-to-cad handoff table says for those sections |
| Assumptions | the assumptions bullets in `$cad`'s final response |

Final verification is `verify_project <project> --fresh`, with `--print-gates`
when the object will be printed and `--powered` evidence when a load is
functional. It is not `--image-derived`: there is no reference photograph to
score likeness against, so appearance is owned by the recorded review rounds.

When the request was to make the object, continue into `$cad` with this spec in
the same task; stop at the spec only when the user asked for a design or a
spec.

## Non-negotiables

- **The user's words win.** A survey row or a precedent never overrides a
  stated value, feature or style.
- **Survey before concept, direction before concept.** No concept is selected
  before §2 has its rows or a recorded miss and §4a has its direction.
- **Beauty is a requirement.** No handoff without a direction; no delivery
  without a recorded review round that found nothing left on the checklist, or
  the finding the user accepted.
- **No copied geometry** from a design whose licence does not permit it.
- **Every number carries a tag**, and every *must* carries a verification.
- **CAD chooses nothing.** 6g is complete before handoff.
- **No geometry.** This skill writes markdown.

## Required final response

1. **One sentence** — the product, its character in three words, and the
   concept selected.
2. **Survey** — the product rows and aesthetic precedents used (URL each), the
   baseline features, and the complaints the design answers; or the miss.
3. **Direction and selection** — the form vocabulary and proportions in a line
   or two; the chosen concept, the nearest rejected one and why.
4. **Design review** — how many rounds ran and what each changed.
5. **Spec file path** — absolute.
6. **Assumptions** — `[assumed]` values as one-edit corrections, most
   consequential first (colour and style included).
7. **Sourcing** — one line per standard element or bought component: hit used,
   hit rejected with reason, miss, or unavailable.
8. **Next step** — the `$cad` handoff, or the build already under way.
