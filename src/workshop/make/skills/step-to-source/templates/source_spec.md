<!--
  step-to-source spec - template for a model rebuilt from references.

  Save as <project>/<name>_spec.md and fill every bracket. Delete every HTML
  comment. Write it once the source passes validation.py, and before
  release_refs: after release, this document and validation.py are the only
  record of what the references were.

  Rules the gates enforce (check_spec_format, check_spec_numbers):
  - every millimetre number carries a tag on the same line:
      [observed]  measured on a reference (mesh section, circle fit, step_probe)
      [inferred]  derived from measured values (a pitch radius, a mid-span)
      [assumed]   chosen, not measured (a clearance, a gap, a phase offset)
  - a backticked parameter name followed by a number is a claim about
    params.py and must match it: `MB_WALL` 2.0
  - a motor, crank, linkage or cam that drives anything needs section 8, with
    a feasibility assert and a motion table that has a blocked row for every
    clear one.
-->

# Spec - <object name>

**Project directory:** `output/<name>/`
**Supplied as:** <n> <STL | STEP> files, <how they arrived: print plates | common-origin assembly | recentred parts>
**Designer source:** <product page / manual, with ID and page> in `ref/source_images/`
**Variants:** <names, or "one">

---

## 1. What it is

<One paragraph: what the object is, what it does, how it is driven.>

---

## 2. Bill of materials

One row per role. The assembly asserts this table against its built labels.

| role | supplied as | bodies (labels) | count per variant | exit |
|---|---|---|---|---|
| <role> | <file name> | <label, label> | <variant: n> | <recover | re-author> |

---

## 3. Parts

One subsection per part. Each part lives in its own frame: <footprint bbox
centred on the origin, bed at Z = 0 | other, stated>.

### 3.<n> <role>

<One sentence: what the part is and what it does.>

| dimension | parameter | value | tag | measured how |
|---|---|---|---|---|
| <name> | `<PARAM>` | <value> mm | `[observed]` | <section at z = ..., circle fit r = ..., residual ...> |

Against its reference: volume <+x.xx %>, bbox within <d> mm `[observed]`, worst section IoU <0.xxxx> at <cut>.

---

## 4. Mating datums

Every datum an assembly seats on, as a part parameter, in its part's frame.

| datum | part | parameter | value | tag | mates with |
|---|---|---|---|---|---|
| <bore centre> | <role> | `<PARAM>` | <value> mm | `[observed]` | <role.datum> |

---

## 5. Assembly

- **Pose source:** <the files (assembled) | designer photos p. n | manual step n>
- **Fixed root:** <role>
- **Seats:** <datum pair per part>
- **Audited pairs:** <n>, worst <d> mm `[observed]`
- **Assembly choices (not measured):** <`GEAR_FACE_GAP` 0.1 mm `[assumed]`, phases with their scan evidence>
- **Designed tight fits** (reported by `interfere`, kept on purpose): <pair: mm3>

---

## 6. Not modelled

<Parts the kit does not contain (a motor, fasteners, a battery), and what that
excludes from any claim: powered, printable, fit.>

---

## 7. Verification reached

| check | result |
|---|---|
| `validation.py` | <n parts, worst volume <x %>, worst IoU <0.xxxx>> |
| `check_layout` / `gen --write` | <ok / n entries> |
| `inspect validate` | <result> |
| `inspect interfere` (assembled) | <n clashes, classified> |
| `check_motion` | <ran / not run, why> |
| `release_refs --delete` | <deleted n files, kept n> |

---

## 8. Mechanism

<Delete this section only if nothing is driven.>

**Drive:** <crank | motor> -> <gear train with tooth counts> -> <output>

Feasibility, as asserted in `assemblies/`:

```python
assert abs(centre_distance - MODULE * (Z1 + Z2) / 2) < 0.2   # gears mesh
assert max(abs(link_residuals)) <= LINK_SLOT_PLAY              # loop closes inside the slot
```

| id | motion | expect | result |
|---|---|---|---|
| <joint>-turn | <rotate about axis> | clear | <result> |
| <joint>-retain | <pull along axis> | blocked | <result> |
