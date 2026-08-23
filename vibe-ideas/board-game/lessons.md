# lessons — hard rules from real builds

Injected into every DRAFT, BUILD and REPAIR prompt. These are not advice;
violating one is how a previous build failed.

Repair rounds append here. **A lesson that appears twice must GRADUATE into
code** — a lint rule in `gate.py`, a threshold, a golden block, or a
constraint in the brief-writer's template — and is then marked
`[GRADUATED -> where]`. Prose that repeats is prose nobody acted on: the
pipeline this replaced knew one fact for three turns and changed nothing.

`improve.py` flags repeats mechanically, but only catches the ones that look
alike. Reading for repeated *meaning* is a human's job, and the auditor's.

A marker is a claim, and `graduation_check.py` holds every one of them to the
tree, so it has to name something a machine can find:

| form | means |
|---|---|
| `module.SYMBOL` | that module defines `SYMBOL` (`def`, `class`, or a constant) |
| `module:"literal"` | that file contains the literal text, for anything that is not a definition |

Several targets may be listed, comma separated. `module` is one of the names
in `graduation_check.MODULES`; anything else fails rather than being skipped.
A graduated lesson leaves the build prompts, so a marker that has quietly
stopped being true is worse than one that never graduated: the lesson is
neither enforced nor remembered.

**Where it lands matters as much as that it landed.** A marker can be entirely
true and still weak: the gate really does catch the blanket fillet, and every
build still writes it, still fails, and still spends a repair round undoing it.
A check is a smoke alarm. It works, and the house burns on schedule. So aim as
far up this ladder as the lesson will go — ordered by how many
non-deterministic hops sit between the fix and the geometry:

| tier | lands in | |
|---|---|---|
| planner | `ideator`, `rules_check` | the defect is never proposed |
| block | `blocks` | one hop, then right by construction |
| brief | `brief_writer` | two hops: writer obeys template, builder obeys brief |
| prompt | `builder` | two hops, and nothing verifies compliance |
| check | `gate`, `ergonomics_check`, `interference`, `pipeline_queue` | after the build is already paid for |

A lesson takes the best tier among its targets, so pairing an upstream fix with
a gate check reads as the upstream fix. Landing at `check` is legal and
sometimes the only honest answer, but `audit.py` raises it every run until the
marker says why nothing above it could hold the fix:

    [GRADUATED -> gate:"bed-size" | ceiling: the bed is 256mm and no amount of planning makes a part fit one that is not]

A marker is read one line at a time, so it never wraps, however long it gets.

Blocks are copied into each build rather than imported, so a graduation into
`blocks.py` only reaches builds that took a fresh copy. `audit.py` names the
in-flight builds holding a stale one, and names a block that no build calls.

---

- [GRADUATED -> gate:"blanket-fillet"] Never fillet all three edge directions of a box at once (`.edges().fillet(r)`). OCCT synthesises a spherical vertex blend at each corner and tessellates it into phantom sliver bodies that pass a no-error check and fail the watertight/body count. Bake corner rounds into the 2D profile and apply top/bottom fillets afterwards.
- [GRADUATED -> gate.check_bill, blocks.add_piece_family] Pieces the rules require to be loose must be separately named `cq.Assembly` children. Never `union()` them: 48 tiles arriving as one continuous mat is what ended fifteen turns of the previous pipeline.
- [GRADUATED -> ergonomics_check.MIN_RELIEF_MM] Relief under 0.6mm is modelled faithfully and then invisible — in the print and in every render. If a motif carries identity, give it depth worth printing.
- [GRADUATED -> blocks.shared_positions] When two layers must line up, generate the pattern once and reuse the same list for both. Two coordinate lists that agree today stop agreeing after one edit.
- Never cut a relief/clearance pocket into the underside of a part that must rest flat on the print bed — it leaves the whole remaining annulus/slab attached only at its outer edge, a dead-flat unsupported overhang. Cut the identical-depth pocket from the opposite (upward-facing) face instead: the bed-contact face stays solid and flat, and an upward-opening pocket never needs support.
- A rotating handle/arm/crank on a repeating pin grid sweeps a full circle at its own radius, at whatever z-band it occupies, past every neighbouring pin at the grid pitch — check its swept radius against every other piece's radius at every z-band they share (not just against the part's own resting footprint), and if it must be offset, route it above or below the tallest neighbour's full envelope rather than trying to dodge sideways at a shared height. The same offset arm also has to be modelled as a solid gusset rising from a wide base (<=45deg outboard taper) rather than a flat plate cantilevered off a cap, or it needs print support too.
- When a brief only states a qualitative constraint on a piece's own radius (e.g. "the crown does not overhang the tooth circle"), satisfying that in isolation is not enough on a shared pin pitch: also assert `own_radius + neighbour's widest radius <= pin_pitch` with real margin. A crown sized only against its own tooth circle can still collide with — or block axial travel beside — every piece on the neighbouring pin, and that check has no other home to fall out of for free.
