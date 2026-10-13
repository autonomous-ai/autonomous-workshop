---
name: brainstorm-concepts
description: Brainstorm how a toy or product could look in quick Concept Rounds of generated Concept Images, shown side by side for the human to pick from and react to, round after round, until they mark one chosen. Use when the human wants shape or style ideas, a new look for an existing product, or concepts redrawn in another concept's style, before any Design Contract exists.
---

# Brainstorm concepts

A Concept Round is a batch of Concept Images (both terms are in `CONTEXT.md`)
for the human to look at and react to. Their reaction shapes the next round.
The human picks by picture, so pictures are the only thing you ask them to
judge. The skill ends when they mark a concept chosen. It decides no
dimension, writes no contract and hands nothing off.

## Setup, once per subject

1. **Facts are your job.** Read what exists about the subject yourself: its
   product page, its folder under `toys-spec/` and auto-memory. Ask the human
   only for decisions, such as which product they mean.
2. Work in `toys-spec/<subject>/`. Write the **constraints** every image must
   honour at the top of `NOTES.md`. They come from the subject's job (for
   example, a phone taps it, so it needs a solid tap area of at least 28 mm),
   its size and its weight. Under them, start an empty **Rejections** log.

Done when: `NOTES.md` states the subject, its job and its constraints, and
has a Rejections log.

## A Concept Round

1. **Plan.** Make 6–8 concepts unless the human names a count or a split
   ("6 tech, 6 not"). Every concept is a distinct idea. Give the round a
   letter prefix not used before (`K1`, `R1`, `C1`…) so every concept keeps
   a unique name. Write one shared prompt block and one line per concept:
   - The **shared block** carries the constraints and a studio shot: one
     standalone object fully inside the frame with margin, a plain surface,
     soft daylight, a three-quarter view from above, and no text or other
     objects. It also carries an explicit exclusion for everything the human
     has rejected, from the Rejections log in `NOTES.md`.
   - The **concept line** names the idea, its form, its colours and the
     detail that makes it this concept.
2. **Redraw from images** when the human asks for one concept in another's
   style, or sends a picture. Attach images with `--ref`, the concept to keep
   first and the style to copy second, and say so in the prompt ("the first
   image is the concept to keep…"). Save every image the human pasted into
   `concepts/round<N>/inputs/`. Only the human's images and your own Concept
   Images are ever attached; an image found on the web is looked at only.
3. **Generate** every concept in parallel, each with its own prompt file:
   ```
   uv run --no-project --with pillow python \
     .claude/skills/brainstorm-trend/scripts/generate_image.py \
     --prompt-file <prompt.txt> --out toys-spec/<subject>/concepts/round<N>/<id>_<slug>.png \
     --env <.env> [--ref <concept> --ref <style>]
   ```
   The `.env` holds `OPENROUTER_API_KEY` and `OPENROUTER_IMAGE_MODEL`. A
   worktree has none, so point `--env` at the main checkout's `.env`. Never
   print the key. Read the printed path, because the suffix follows the
   decoded format.
4. **Check every image** against its concept line: put them all on one contact
   sheet and look. If an image misses the point of its concept (the wrong count
   or layout, a hollow tap area, a banned element), regenerate it once. Then
   take the image as it stands and write its flaw into its caption and
   `NOTES.md`.
5. **Page.** `toys-spec/<subject>/CONCEPTS.html` is one page in Vietnamese,
   with the newest round on top and earlier rounds below it. Each concept is
   one card: its picture, its id and name, an approximate size, one line on the
   idea, any flaw, and a **Đã chọn** badge on chosen concepts. Publish it with
   the Artifact tool, and republish the same file path so the link stays the
   same. If the artifact was deleted, ask before publishing a new link.
6. **Notes.** Append a round section to `NOTES.md`:
   - the human's ask, in their words;
   - each concept id with its idea;
   - the source of every image (text only, or which `--ref` inputs);
   - every flaw.
7. **Commit and push** the round to the working branch. Pull and rebase first,
   because other sessions push to the same branch.
8. **Report** in the human's language, briefly: a table of id, name and idea,
   then the flaws, two or three picks with a one-line reason each, and one
   question.

Done when: every planned image exists and was checked, every flaw is written
down, and the page, `NOTES.md` and the push all reflect the round.

## Between rounds

The human's reaction is the brief for the next round. Before planning it,
write any **rejection** into the Rejections log in `NOTES.md` with its reason
("too childish", "a snowflake key is someone else's idea"). Every later
round's shared block excludes it. Then run the round again.

## When the human picks

Mark each chosen concept: a **Đã chọn** badge on its card and a dated line in
`NOTES.md` with any changes the human asked for. Republish the page, commit,
push and stop. Brainstorming continues only if the human asks for more.

## Prompt gotchas

These are what the image model gets wrong, and how to steer it:

- **Rejected elements return** unless the shared block excludes them by name
  (a keyring, a face, snowflakes).
- **Exact counts and layouts drift** (rows of glyphs, the number of teeth).
  Use a straight-on top-down view, state each count ("row 2 has exactly 2"),
  and give the first draft as a `--ref` for a redraw.
- **Flat areas get drawn hollow or domed.** Say "solid" and "flat" for the
  area that must stay so.
- **Tilted slabs get drawn standing near upright.** Give the height the back
  edge rises, not just an angle.
