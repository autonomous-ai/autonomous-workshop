You write the Concept Checklist (ADR 0096): the traits that make the chosen
Concept Image this toy and not a generic one, so a later reader can tell
whether the Contract Proof kept them.

Look only at the chosen Concept Image at `<CONCEPT>` and its three views in
`<VIEWS>`. Read no contract, spec, note or other image: you see what the owner
saw when they chose it.

Write `<OUT>/CONCEPT-CHECKLIST.md`: 8 to 12 traits, each one line that a
reader can check by looking at a render from one of the concept's cameras.
Prefer a measured ratio to a word: "the head is 0.42 of the total height
(view 1)", "the tail rises 30 degrees above the back (view 2)", "three
toes per foot, each 1/4 of the foot's width". Measure on the image with the
image-to-cad skill's `measure_image.py`
(`src/workshop/make/skills/image-to-cad/`) where an edge is clear; say "by
eye" where it is not.

Use a table with columns: id (T1, T2, ...), trait, view, measure, and an
empty "owner" column. Choose traits that are the toy's character (the
silhouette, a proportion, a gesture, a signature detail, a count), not
colours or surface finish the contract owns. Leave the "owner" column empty:
the owner marks each trait required or changeable.

Change nothing outside `<OUT>`. Reply with the number of traits and the path
of the checklist.
