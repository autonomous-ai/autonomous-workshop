You write the Concept Checklist (ADR 0096): the traits that make the chosen
Concept Image this toy and not a generic one, so a later reader can tell
whether the Contract Proof kept them.

Look only at the chosen Concept Image at `<CONCEPT>` and its three views in
`<VIEWS>`. Read no contract, spec, note or other image: you see what the owner
saw when they chose it.

Write `<OUT>/CONCEPT-CHECKLIST.md`: one trait per distinct, visible thing
that makes this concept itself: each building, landmark, prop group and
signature detail, and each layout relation ("the palms stand in a row
between the two boardwalk entrances"). The count follows the concept, with
no cap or floor: a simple object may have 4 traits, a city scene 30 or
more. Each trait is one line that a reader can check by looking at a render
from one of the concept's cameras.
Prefer a measured ratio to a word: "the head is 0.42 of the total height
(view 1)", "the tail rises 30 degrees above the back (view 2)", "three
toes per foot, each 1/4 of the foot's width". Measure on the image with the
image-to-cad skill's `measure_image.py`
(`src/workshop/make/skills/image-to-cad/`) where an edge is clear; say "by
eye" where it is not.

Group the traits by region of the concept (left to right, front to back:
"Left: the lighthouse", "Centre: the pool"), one `###` heading and one table
per region, numbering T1, T2, ... across the whole file. Each table has
columns: id, trait, view, measure, and "owner". Choose traits that are the
toy's character (the silhouette, a proportion, a gesture, a signature
detail, a count), not colours or surface finish the contract owns. Write "required" in every "owner" cell: every
trait must be kept. Propose no other mark; only the owner's answer to a
trait that cannot be made changes it.

Change nothing outside `<OUT>`. Reply with the number of traits and the path
of the checklist.
