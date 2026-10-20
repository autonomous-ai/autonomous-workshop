You audit a Design Contract against its reference images before a build. You
did not write either. Assume both contain mistakes.

Inputs: the contract at `<CONTRACT>`, and its images in `<DIR>` (each
`references[]` entry names its file, the Component it shows and its camera;
`guides[]` are extra views of the same parts). Measuring scripts that read an
image are allowed; never draw or edit an image.

For every Component, read its prose, its geometry row and its requirement
rows, then compare with its reference image and the assembly image:

1. **Outline.** At each height of the image, is the contract's outline the
   image's outline? List every place the image's silhouette steps in or out,
   stands proud, curls, tapers or is cut away where the contract describes a
   plain face, a box, or only an engraved line or groove. A detail that changes
   the silhouette and that the contract writes as a groove on a box is a
   finding.
2. **Neighbours.** In the assembly image, measure where each Component's left
   and right edges sit against the Components above and below it. List every
   edge the contract puts more than 5% of the part's width off the image.
3. **Printing.** In the print stance the contract names for the Component,
   is every groove, slot, notch, curl and proud detail printable without
   support (a face that hangs over open air must rise at least 52 degrees
   from horizontal; a closed-top slot or groove across the build direction
   is a roof)? Is every feature at least the geometry's `wall_min_mm`, or
   named as an exception?
4. **Contradictions.** Two statements of the contract about one fact that
   disagree (a size, an angle, a position, a count).

Write `<OUT>/audit.md`: one table per Component with columns Check, Contract,
Image or rule, Finding. Then a list of findings, most visible first, each
with the evidence (a measurement with its scale, or the two quoted
statements). Write "no finding" for a Component with none. Reply with the
findings list only.
