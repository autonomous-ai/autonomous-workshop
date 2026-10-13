- Add the `brainstorm-concepts` skill: quick Concept Rounds of generated
  Concept Images that the human picks from by picture, round after round,
  before any Design Contract exists. Each round is saved under
  `toys-spec/<subject>/concepts/`, logged in `NOTES.md` with every flaw and
  rejection, shown on one Vietnamese comparison page, and committed and pushed.
  The skill ends by marking the chosen concept. `generate_image.py` now takes
  `--ref` images, so a concept can be redrawn in another concept's style.
  `brainstorm-trend`'s Preview Image is now a Concept Image, including its
  `concept.*` file names and the `concept_path` log field.
