# Component integration — make it actually assemble and work

A part that is a valid solid and looks premium can still be **useless** in two
ways: it can't be **installed** (a MagSafe stand with a neat puck recess, but the
puck's **captive cable + strain-relief collar** won't pass the opening), or it
can't **function** (mating features that don't engage or can't transmit force — a
dial coupling sitting clear of its drive pegs, a smooth pocket over round pegs
that can't carry torque, a tooth perched over a void). Geometry was fine; the
*product* was broken.

This doc is the discipline that prevents both. It is **function-first** — these
checks outrank looks, and a `validate()` assert or a `functional` warning that
fails means the design is not done. Two rules generalize across every interface:
**every mating pair must engage and transmit its intended force**, and **every
feature must sit on solid material** (not over a void, hole, or notch).

## 1. Model the WHOLE real component, not a bounding box

A component is rarely just its body. Before modeling its pocket/mount, write
down everything physically attached to it that must also fit:

- **Captive cables** — a permanently-attached cable has a real diameter, a
  **strain-relief collar / connector** at the device end (wider than the
  jacket), and a length. You must route all three.
- **Connectors / plugs** — USB-C, Lightning, barrel jacks: the connector body is
  bigger than the cable and often a different cross-section.
- **Buttons, ports, lenses, vents** — must stay accessible after assembly.
- **Mating hardware** — screw heads, nuts, inserts need access + tool clearance.

**Web-search the component's real dimensions** (body, cable Ø, connector-collar
Ø×len, mount pattern) and **state them as assumptions the user can correct** in
the plan — don't recall them from memory. For hardware a cadlib helper covers
(bearings, screws, nuts, magnets, inserts), pass the helper a named size instead.

## 2. Write the assembly / setup sequence

Enumerate, **in order**, how a person assembles and sets up the finished print,
and for each step name the clearance it needs:

1. *Install the MagSafe puck:* feed the cable + connector collar (Ø9 mm) through
   the **open** rear channel → seat the puck in its Ø56.4 pocket → lay the cable
   into the channel → it exits the base front. *Needs: open route, ≥Ø9 collar
   clearance, channel ≥ cable Ø.*
2. *Place the phone:* rests on the base ledge, magnet holds the lean. *Needs:
   ledge clears a cased phone; CoM inside the base.*

If a step is physically impossible with the current geometry, the design is
wrong — fix the geometry, not the sequence.

## 3. The rules that catch the common traps

- **Captive cable ⇒ OPEN route.** You can only lay a captive cable in from the
  side; you cannot thread it through a closed tunnel. Use
  `cadlib.cutouts.add_open_cable_channel` (see
  `references/patterns/cable-channel.md`), never a bored hole.
- **Size the opening for the CONNECTOR, not the jacket.** The widest thing that
  must pass is the strain-relief collar / connector body: `opening Ø = collar Ø +
  0.5–1.0 mm`. A channel sized for the cable jacket blocks the wider collar (e.g.
  a 3.6 mm cable vs. its ~9 mm collar).
- **Insertion path must be straight + reachable.** A pocket the part itself
  walls off (no approach for the component or a tool) can't be loaded.
- **Removable when it must be removable.** If the user swaps the component, don't
  trap it behind a one-way snap.
- **Keep ports/buttons/cables accessible** after everything is together.

## 4. Enforce it — two mechanisms, use both

Encode each requirement so it can't silently regress (see the project template
`validation.py` and `references/project-structure.md`):

- **Hard `validate(p)` asserts** for true fit constraints that make the build
  *impossible* — `assert pocket_dia > puck_dia`, `assert back_wall >= 2.0`. A
  failed assert blocks the build (surfaces as `VALIDATION_FAILED`).
- **Soft `functional` warnings** for assembly-feasibility — return them from
  `functional_checks(p)` and merge into the envelope:
  `return {"shape": shape, "warnings": functional_checks(p)}`. Each entry:
  `{"part": <name>, "kind": "functional", "detail": "...", "severity": "warning"}`.
  The part still builds + renders, and the driver's **functional-review loop**
  won't finish while any remain. Example:

  ```python
  def functional_checks(p):
      w = []
      if p.connector_dia + p.channel_clearance < p.connector_dia:
          w.append({"part": "stand", "kind": "functional",
                    "detail": "connector pocket cannot clear the collar — puck "
                              "won't install", "severity": "warning"})
      return w
  ```

See `assets/example_magsafe_stand.py` for the whole pattern done right.

## 5. Verify against the render — the two-group checklist

In the build loop (SKILL.md step 6), after `scripts/review`, clear the plan's
Verification checklist item by item, each with a sanity check (a `validate()`
assert or a `functional` warning) AND a visual check:

- **Per component** — every feature sits on solid material (no tooth / peg / boss
  / rib over a void, hole, or notch); depths reach; no half-supported overhang.
- **Per interface** — each mating pair (peg/socket, clutch, gear, tab/slot,
  lip/groove, cable/opening) actually meets in the right axis, can transmit its
  force (form-fitting, not a smooth pocket over round pegs), has the right
  clearance, and a reachable assembly path.

Exterior PNGs can't show an interior interface — render a cross-section with
`python scripts/review <project_dir> --section <x|y|z>[@offset]` (add
`--part <name>` to cut one part) and look at whether the features actually engage.
Fix and re-run until every item is cleared, `validate()` passes, and
`functional_checks()` returns empty. **Never declare done while a `functional`
warning or a failed assert remains.**
