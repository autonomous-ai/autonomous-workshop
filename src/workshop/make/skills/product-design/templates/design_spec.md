<!--
  product-design spec — template.

  Fill every bracket. Delete every HTML comment before handing this over.
  Every number carries [observed] | [inferred] | [assumed]:
    [observed]  stated by the user, or read from a cited source (survey row,
                device datasheet, standard, wiki page with its source)
    [inferred]  derived from other numbers — the arithmetic sits beside it
    [assumed]   a default chosen here, phrased as a one-edit correction
  A number in a survey row is [observed] from that row's URL.
  Units are millimetres throughout.
-->

# Design spec — <object name>

**Request:** "<the user's words, verbatim>"

**Project directory:** `output/<object_name>/` — the object's own name in
snake_case, never a placeholder. Every path below (`measure/`, `ref/`,
`part_<role>.step.py`) is relative to it.

**Bed:** `--bed <W>x<D>x<H>` `[observed|assumed]`

---

## 1. Overall read

<One paragraph: what the object does, in one sentence first; who uses it; where;
what it must fit or hold; whether it moves or is powered.>

- **Stated by the user:** <every value, feature and style the request fixes — each `[observed]`>
- **Open:** <form | size | features | mechanism — whatever this spec decides>
- **Archetype / construction family:** <prismatic holder | shell/enclosure | revolved vessel | organic figure | flexi | mechanism> — <why>
- **User and context:** <adult | child, age N `[tag]` | display only> · <desk | wall | handheld | …>
- **Powered or driven:** <no | yes — which load or drive; §8 and `$electromechanical-integration` apply>

---

## 2. Product survey

<Three to five rows; three for a simple object. Commercial products, published
printable designs, and their reviews. Status is used | rejected | MISS |
unavailable. A size nobody listed is "not given", never estimated from a photo.>

| # | Query | Status | Kind | URL | Overall size | Features | Praised | Complained about | Licence / use |
|---|---|---|---|---|---|---|---|---|---|
| 1 | <> | <> | <commercial / printable design / manufacturer spec> | <> | <L × W × H mm `[observed]`, or not given> | <> | <> | <> | <facts only / licence name> |

- **Baseline features** (in most rows): <each → included in §3 as Rn, or rejected with the reason>
- **Recurring complaints:** <each → the §3 row that answers it, or a stated non-goal>
- **Size band:** <smallest–largest governing dimension across the rows `[observed]`>
- **Differentiator:** <what the request asks for that no row has>

**Aesthetic precedents** — the best-looking designs of the kind or of the
character sought (award listings, most-liked models, respected brands):

| # | URL | Why it looks good (not its dimensions) | Taken into the direction as |
|---|---|---|---|
| P1 | <> | <one continuous lean line / a single generous radius / a lifted base / …> | <> |

---

## 3. Requirements

| id | Requirement (measurable target) | Source | Priority | Verified by |
|---|---|---|---|---|
| R1 | <> `[tag]` | <request / survey baseline / survey complaint / wiki `<page>` / standard / bed> | must | <gate, `measure/check_spec.py` assertion, or named inspection> |
| R2 | <> | <> | should | <> |
| R3 | <> | <> | won't | <why not> |
| R4 | <silhouette reads as <what> from the main view> | wiki `product-aesthetics` | must | design review, silhouette render |

**Wiki pages designed from:** <`wiki show <page>` — the section and the rule taken>

---

## 4a. Design direction and concepts

### Direction

<Set before any concept, from `wiki show product-aesthetics`. Every later
choice traces to these lines.>

- **Character:** <three words>
- **Seen from:** <the view people see it from, as AZ,EL> `[assumed]`
- **Geometry family:** <soft | geometric | organic> — <why, from the character>
- **Radius family:** <large / medium / small, and the edge class each belongs to — values in §5>
- **Repeated angle and continuous lines:** <the lean or taper angle `[tag]`; the lines that run across the object>
- **Hierarchy:** primary <form> · secondary <forms> · tertiary <detail> · focal feature <one> · calm surfaces <where>
- **Silhouette and stance:** <what the black silhouette must say from the main view; low and heavy | lifted on an inset base>
- **CMF:** dominant <colour, where> · accent <colour, the focal feature> · boundaries <on which edges or grooves> · finish <matte | silk | textured bed face>
- **A-surfaces:** <the faces people look at; the orientation keeps supports and the seam off them>

### Concepts and selection

<Two or three concepts, each the direction expressed through a different form
idea — not three sizes of one idea. One concept only for an object with one
sensible answer — say why.>

| Concept | Form idea (primary · secondary · silhouette) | R1 | R2 | R4 look | … | Part count | Print risk | Verdict |
|---|---|---|---|---|---|---|---|---|
| A — <name> | <> | pass/fail | <> | <> | <> | <> `[tag]` | <> | **selected** |
| B — <name> | <> | <> | <> | <> | <> | <> `[tag]` | <> | rejected — <reason> |

**Selected:** <concept> — <the trade-off accepted, in one sentence>
**Nearest rejected:** <concept> — <why it lost; the one edit that would switch to it>

---

## 4b. Component descriptions

<The selected concept big to small — primary form, each secondary form, then
tertiary detail — naming every landmark a person recognises the object by.
Ranges are allowed here; §5 fixes the values.>

- **Primary — <form>:** <shape, proportion, stance>
- **Secondary — <form>:** <shape, where it sits, what it does, which line it continues>
- **Tertiary:** <detail, and where the calm surfaces stay clear of it>

**Top view (down −Z):** <outline, symmetry, landmarks>
**Front view (along +Y):** <profile, heights, landmarks>
**Side view (along +X):** <profile, depth, landmarks>

---

## 5. Size

| Dimension | Value (mm) | Confidence | Anchor |
|---|---|---|---|
| Overall L × W × H | <> | `[tag]` | <survey band / device / bed / derived> |
| <governing dimension> | <> | `[tag]` | <cited spec or arithmetic> |
| <fit value both halves derive from> | <> | `[tag]` | <device datasheet URL / standard>; clearance from `cadfits` |
| Wall thickness | <> | `[tag]` | <N × nozzle; wiki `wall-thickness-and-hollowing`> |

**Radius family:**

| Name | Value (mm) | Confidence | Edge class |
|---|---|---|---|
| `R_LARGE` | <> | `[tag]` | <primary silhouette edges> |
| `R_MEDIUM` | <> | `[tag]` | <secondary forms> |
| `R_SMALL` | <> | `[tag]` | <detail; bed edges take a chamfer instead> |

**Proportion ledger** — asserted in `measure/check_spec.py`:

| Ratio | Value | Confidence | Why this proportion |
|---|---|---|---|
| <height ÷ width> | <> | `[tag]` | <the direction, the survey, an unequal 70/30 division> |

**Print sanity:**

- Bed fit: <fits <W>×<D> mm `[tag]` | must be split — how>
- Print orientation: <named orientation, the face on the bed, and why>
- Overhangs: <none past 45° | where, and how the orientation or a chamfer handles it>
- Minimum wall and feature: <> mm `[tag]`

---

## 6. Decomposition

<Fill 6a–6g with the table shapes and rules in
`skills/image-to-cad/templates/build_spec.md` §6. The exterior-construction row
of 6g cites §4a's selection; the mechanism row cites it too when the object
moves. `N/A` with a one-line reason for a subsection that does not apply.>

### 6a. Printed parts
### 6b. Feature tree
### 6c. Off-the-shelf components — catalog search log
### 6d. Analogous design references
### 6e. Mount declarations
### 6f. Removable-light mating interfaces
### 6g. Design selection

---

## 7. Feature detail + build123d operation

<Same table as the build spec §7: every feature in `gen_step()` order, with its
numbers, build123d call and selector. It implements 6g and chooses nothing.>

---

## 8. Powered system / mechanism

<Fill from `skills/image-to-cad/templates/build_spec_powered.md` whenever a load
is functional or a part is driven. Otherwise replace this line with one stating
that nothing is powered or driven.>

---

## Verification checklist

**Per requirement** — one line per *must* row of §3:

- [ ] R1 — <the gate or `measure/check_spec.py` assertion that proves it>

**Survey closure**

- [ ] every baseline feature is in §3 or rejected with a reason
- [ ] every recurring complaint is answered or a stated non-goal
- [ ] the overall size sits in the survey band, or §3 says why not

**Appearance** — no reference photograph, so no likeness gate; the design
review rounds below own it:

- [ ] every §4b landmark is visible in the review renders
- [ ] the last review round found nothing on the `product-aesthetics` checklist

<Then the build spec's "Per sourced component", "Per design reference", "Per
interface" and "Per motion" blocks, and the powered block when §8 applies.
Delete a block only when its trigger is absent, and say so in one line.>

---

## Design review

<One row per finding, filled after `$cad` builds. At least two rounds for a
visible product unless round 1 finds nothing; the same finding surviving three
rounds of detail edits means the primary form or the concept changes.>

| Round | View | Finding | Checklist item | Source change | Result |
|---|---|---|---|---|---|
| 1 | <front / silhouette / AZ,EL> | <what is wrong> | <silhouette / proportion / hierarchy / radius / lines / stance / colour / A-surface / direction> | <parameter or feature changed> | <fixed / accepted by the user> |

---

## Assumptions

<Most consequential first. Each phrased as a one-edit correction.>

1. **<assumption>** `[assumed]` <value> — <what changes if it is wrong>
2. **Colours** `[assumed]` <dominant / accent> — <swap either in §4a; nothing else changes>

---

## Next step

Spec written to `output/<object_name>/<object_name>_spec.md`. Build it with
`$cad`: §5 becomes the named parameters, §3's must rows become
`measure/check_spec.py`, §7 in order becomes `gen_step()`, and §8 the kinematic
parameters and feasibility `assert`.
