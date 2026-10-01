# Wish expansion

A short Wish leaves most of the decisions that decide a printed object to
whoever builds it, and a builder who meets them one CAD edit at a time settles
them late and generically. A Wish that already names the defining parts, the
pose, the open spaces, the size and the split builds better. Expansion writes
those decisions down once, before any source exists.

This applies to new Spark Make only, outside Contract Mode and outside an
early-proof turn. Forge and Quest already carry a sealed Invent concept, and a
Design Contract is already the full specification.

## What to write

The expansion exists to generate a 3D model: an AI CAD builder reads it and
turns it into solid printable geometry. Write every sentence as something that
builder can model as a solid shape.

Once the Inventor is selected and before the first `part_<role>.step.py`,
write `<cad-project>/WISH-EXPANSION.md`: plain English prose in four
paragraphs, as long as the Wish needs and no longer, followed by a reference
reading of the images you obtained (below). Write it as the selected Inventor,
using its Taste to decide how, never what.

1. **What must be recognisable.** Name the subject, then every defining part
   that must read as its own distinct element ("individually readable teeth",
   "clearly separated finger bones"), and how each key part is shaped, not
   only that it exists.
2. **Pose and reading.** The pose and composition with directional cues
   (curves, where the head turns, what is spread or tucked); the negative
   spaces that must stay open; the views it must read correctly from (front,
   side, three-quarter).
3. **Size and form discipline.** One overall size in mm. Substantial primary
   forms separated from finer secondary detail, so not everything is equally
   thick. The generic shortcuts to avoid for the most important parts ("not
   generic cylinders or cones", "not a solid torso with grooves"). For each
   primary form, name its construction family from the table in
   `.agents/skills/image-to-cad/references/build123d-operations.md`
   (prismatic, tapered extrude, revolve, loft, sweep, sketch-driven, blended
   organic mass) and why. A form built in the wrong family cannot be rescued
   by parameter edits, so choose it here rather than discovering it in review.

   Then translate every style word of the Wish ("dark fantasy", "cute",
   "sleek", "rustic") into shape. A style kept only as nouns (skulls, spikes,
   ornament) ends up stuck onto a generic round body. Using the selected
   Inventor's Taste to decide the values, state for the primary forms:
   - **Section shape:** round and full, or angular, ridged and planar.
   - **Edges:** crisp chamfers and hard creases, or soft fillets, with the
     largest fillet radius allowed on primary forms in mm.
   - **Silhouette:** tapering points, hooks, spikes, broken or asymmetric
     outlines, or smooth continuous curves.
   - **Proportion:** gaunt and sinewy, or heavy and bulky.

   Each line is something a reviewer can check on a render. Carry them into
   the blind review's `critical_form_requirements` beside the defining parts.
   When the Wish names no style, say which the Taste chose and why.
4. **Function and printing.** Static display or what moves; when static,
   mechanisms are not required. Which parts may be separate for printing, at
   the natural seams the object already has (joints, neck, weapon, armour
   edges, base), and that they join with keyed locating joints. Do not plan
   paired halves of one form; [make](make.md) says when a planar split is
   earned. The work order: silhouette and overall anatomy first, fine detail
   after. The tradeoff rule: when print
   constraints force simplification, keep the defining parts of paragraph 1
   and record the tradeoff in `GEOMETRY-NOTES.md`.

## Reading the references first

Pixels do not survive a compaction; text does. First obtain references as
[visual-reference-inspection.md](visual-reference-inspection.md) directs:
the sealed `wish_references`, images you find, and on a runtime with a
built-in image tool, a generated concept. Then read them into the expansion
before writing the four paragraphs, so every later turn builds from the same
measured record rather than from a remembered look.

1. Open every image yourself. Copy the sealed originals into
   `<project-dir>/ref/` and run the `image-to-cad` skill's `measure_image.py`
   on each. Views of one object shot together go in one call so they share a
   camera scale.
2. Take proportions from its output, not from the eye: `aspect`,
   `row_bands`/`col_bands` for where parts and loft stations change, and
   `symmetry`. One view fixes only two dimensions; the third comes from
   another view or is not observed.
3. Append a `## Reference reading` section to the expansion. For each image:
   its path, its kind (sealed, found with its URL, or generated), the view it
   shows, and what you observed. A sealed image outranks a found or generated
   one, and the Wish text outranks both of those. Then one line per
   defining part from paragraph 1, tagged:
   - `[observed]` when an image you opened shows it, with the image and the
     measured ratio it rests on ("head width : body length = 0.31, ref-01
     side view");
   - `[inferred]` when no image shows it (a hidden back, the far side, the
     underside), with what it was inferred from.
   Guessing a part and tagging it `[observed]` is the worst failure here;
   an honest `[inferred]` is always acceptable.
4. Take size from the Wish or a known object in frame, never from pixels. An
   unscaled image gives ratios only; paragraph 3's size in mm scales them.
5. Where images disagree, or an image disagrees with the Wish text, name the
   conflict and follow the Wish.

Paragraphs 1 to 3 then restate what the reading observed instead of
reinventing it, and paragraph 3's construction families follow the measured
taper (`row_profile`/`col_profile`), not habit. Only when no image was usable is
there no reading section; then say once that the expansion is text-derived.

## The Wish still decides

- The sealed Wish is unchanged and remains the objective. The expansion
  interprets it; it never replaces it.
- Keep every explicit Wish requirement, value and prohibition exactly. Where
  the Wish states something, restate it; do not soften, round or drop it.
- Fill only what the Wish leaves open, with one concrete choice rather than a
  range. Do not add subjects, features, lights, electronics or mechanisms the
  Wish does not imply.
- When the Wish already covers a paragraph, restate it briefly and move on.
  A detailed Wish needs little expansion.
- Where something the Wish permits is not taken up (for example "detachable
  wings are acceptable" and the build is one piece), say which and why.

## How Make uses it

Build components from it, and carry paragraph 1's defining parts and
paragraph 2's negative spaces into the blind review's
`critical_form_requirements` beside the Wish's own explicit requirements, and
compare each make round's views against the reference reading's `[observed]`
ratios, part by part, not only against the whole silhouette. The
review still reveals and judges against the actual Wish; an expansion choice
that the Wish does not require is never a reason to fail a faithful build.
Do not rewrite the expansion to fit what was built. If the build has to
depart from it, record the departure in `GEOMETRY-NOTES.md`.
