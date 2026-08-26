---
name: design-reference
description: Search a local index of existing parametric CAD designs and fetch selected build123d examples with source, license, provenance, and checksums. Use when image-to-CAD or CAD work benefits from analogous construction patterns or prior designs. Do not use it for purchasable standard components; use step-parts for those.
---

# Design references

Use analogous designs to learn a construction pattern, never to replace the
user's reference image, dimensions, or requested exterior. The bundled client
indexes the 7,683-model Fusion 360 Gallery build123d conversion without
vendoring the dataset into this repository.

## Boundary

- Use this skill for shape archetypes, feature-order examples, and build123d
  idioms from existing designs.
- Use `step-parts` instead for a bought motor, bearing, fastener, board, or
  other standard component that the new model must physically fit.
- A design reference is not a scale anchor, dimensional authority, or proof of
  likeness. Measure the user's own images and validate the resulting model.
- The indexed Fusion 360 Gallery Modified Set is licensed for
  **non-commercial research only**. Do not use or fetch its source for a
  commercial task. Every search result and fetched provenance record repeats
  this restriction.

## Client

Resolve the materialized skill once, then run from the product workspace with
its active interpreter:

```bash
DESIGN_REFERENCE_SKILL_ROOT="$(workshop skills path)/design-reference"

# First use, or when the pinned source revision changes (~40 MB download)
python "$DESIGN_REFERENCE_SKILL_ROOT/scripts/design_refs.py" sync

# Search offline after sync. Translate non-English requests into a short
# English feature query because the source descriptions are English.
python "$DESIGN_REFERENCE_SKILL_ROOT/scripts/design_refs.py" search \
    "rounded enclosure mounting holes" --limit 8

# Inspect one exact result
python "$DESIGN_REFERENCE_SKILL_ROOT/scripts/design_refs.py" show \
    fusion360-gallery-build123d/model_100221_4d7b66c4_0003

# Fetch only the selected reference into an existing CAD project
python "$DESIGN_REFERENCE_SKILL_ROOT/scripts/design_refs.py" fetch \
    fusion360-gallery-build123d/model_100221_4d7b66c4_0003 \
    --project-dir output/<project>

# Recheck downloaded artifacts later
python "$DESIGN_REFERENCE_SKILL_ROOT/scripts/design_refs.py" verify output/<project>
```

All ordinary commands print JSON. `search --format text` is available for a
compact human-readable list.

## Workflow

1. Read and measure the user's actual reference first. Name the construction
   family and the one or two features for which an analogy would reduce
   uncertainty.
2. Search with form and operation words, not the product name alone: for
   example `tapered shell vent slots`, `rounded bracket mounting holes`, or
   `revolved knob recessed grip`.
3. Review at most five strong candidates. Prefer a candidate because a named
   feature uses a relevant construction pattern, not because its title sounds
   similar.
4. Fetch only candidates that will inform the build. The client writes under
   `<project>/ref/external/<source>/<model>/`:
   - `reference.build123d.txt` — a non-executable excerpt; the `.txt` suffix is
     deliberate because cadgen scans the worktree for Python generators;
   - `contact-sheet.png` — the source batch's visual sheet;
   - `LICENSE.md`;
   - `provenance.json` — immutable revision, URLs, catalog record, and SHA-256
     for every downloaded artifact.
5. Record the selected id, local path, relevant feature, and the precise idea
   taken from it. Re-measure every dimension from the user's reference or spec.
6. Run `verify` before handing off a project that contains fetched references.

If no candidate is relevant, record the query as a miss and continue from the
user's evidence. A weak analogy is worse than no analogy because it silently
pulls the build toward another object's silhouette.

## Integration with image-to-cad

For image-derived work, search after the overall read and before writing the
feature-operation table. Add every used result to the build spec's **Design
references** table. The operation table may borrow a construction idiom; its
numbers, placements, and silhouette still come from the reference-image
measurement ledger.

## Maintenance

The source registry is `data/sources.json`. Read
`references/catalog-schema.md` only when changing a source adapter, the index
format, or provenance layout. Re-run `sync --force` after changing the pinned
revision, then run `self-check` and the tests.
