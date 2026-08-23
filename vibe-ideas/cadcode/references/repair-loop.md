# Repair loop

Load this when `scripts/cad` or `scripts/check` returns `ok=false`,
`is_solid=false`, or the rendered PNG shows the wrong shape.

Failures are **a normal step in the loop, not an exception**. A real
engineer compiles, sees a red squiggle, fixes the line, recompiles —
that's the same thing you're doing here. Don't apologise; iterate.

## The fix step in detail

1. **Read the failing JSON** (and traceback if present). Don't guess at
   the cause from the prompt — the actual error text usually identifies
   it directly.
2. **Classify the failure** using the table below.
3. **Make the smallest responsible source change.** Change one parameter
   or one line, not a re-architecture. Big rewrites lose the user's
   prior intent and burn iteration budget.
4. **Re-run `scripts/cad` on the same `.py`.**
5. **Look at the PNG, again.** "ok=true" is necessary but not sufficient
   — geometry can compile and still be wrong-shaped.
6. **Cap yourself at 4 iterations** before asking the user a clarifying
   question. Each iteration costs time and tokens. Past 4, you are
   almost certainly guessing about user intent rather than fixing a
   geometry bug.

## Failure classes

### `ok=false` with a Python traceback

**Most common: missing or wrong import.** The CADCode sandbox allows
``cadquery``, ``math``, ``numpy``, and a small set of Python stdlib
modules (``typing``, ``dataclasses``, ``enum``, ``functools``,
``itertools``, ``operator``, ``collections``, ``copy``, ``fractions``,
``decimal``, ``abc``, ``contextlib``, ``warnings``, ``weakref``, ``io``,
``re``, ``string``, ``textwrap``, ``random``). It does **not** allow
``os``, ``subprocess``, ``urllib``, ``requests``, ``cv2``, file system
modules, network modules, etc. (the runner's import allow-list is the
authoritative list and may change — this is the current set.) If your code
needs anything outside the allow-list, you have the wrong tool for the job.

Other common causes:

- Syntax error (typo, unbalanced paren).
- Calling `.val()` on something that's not a `Workplane`.
- Forgetting the entry point: every file must define `gen_step()` at module
  scope (or, for a trivial script, assign a module-level `result`). **Required.**
- Using `from cadquery import *` — fine, but you still need to use the
  fluent API (`cq.Workplane(...)` style).

### `ok=true` but `is_solid=false`

The CadQuery code ran but produced non-manifold geometry. Common causes:

| Symptom | Likely cause | Fix |
|---|---|---|
| Volume is 0 or negative | `.cut(other)` removed everything (the other shape contained the first) | Check sizes; shrink the cutter |
| Volume is tiny vs expected | A hole or cut extends past the part edge, leaving fragments | Use `.cutThruAll()` instead of `.cutBlind(N)`, or increase `N` |
| Volume is huge | `.union(b)` where `b` is way too big | Check `b`'s dimensions; maybe you confused diameter and radius |
| Fillet failed silently | Radius bigger than the local edge | Halve the fillet radius |
| Workplane references the wrong face | `.faces(">Z")` after a `.cut(...)` may select the *cut* face | Explicitly index: `.faces(">Z[1]")` |

### Render looks wrong even though `is_solid=true`

This is the most common case once compile is fixed. Classify by what's wrong:

| What you see | Likely cause | Fix |
|---|---|---|
| Holes in wrong positions | Bad `.pushPoints(...)` or `.rarray(...)` coordinates | Recompute against bbox center |
| Hole shape is a polygon, not a circle | Tessellation tolerance too coarse for that diameter | Re-run with `python scripts/cad <file.py> --mesh-tolerance 0.05` (or 0.02 for very small holes) |
| Part is rotated relative to expected | `.rotate(...)` axis or angle wrong | Check that the rotation point + axis make sense |
| Part is way bigger/smaller than asked | Confused diameter vs radius, or mm vs inches | Re-read the prompt; mm only |
| Two-part assembly: parts overlap | Bad `.translate(...)` after the rotate | Move *before* rotate when offsetting from origin |
| Two-part assembly: parts float, don't touch | Bad alignment of part-local origins | Pick one part as anchor; align the other to one of its faces |
| Flutes/grooves on a tapered surface punch through near the top | Vertical cylinder cutter on a cone | Loft a tapered cutter (see `cadquery-modeling.md`) |

### Workplane / selector errors

`StdFail_NotDone` from OCCT usually means a boolean was infeasible.

- `cq.Workplane.faces(">Z")` returns *nothing* after a complex boolean if
  the top face was destroyed. Use `.faces(">Z[1]")` or restructure.
- `OCP error: cannot find face` — your selector matched zero faces. Print
  `len(result.faces().vals())` to debug.

## When to stop iterating and ask the user

Ask **one** clarifying question after the 4th failed iteration, or earlier
if you find yourself making the same guess about the user's intent:

- Two valid interpretations of the prompt (portrait vs landscape, etc.).
- A web search can't pin the dimensions for a specific device and you'd be
  guessing.
- The prompt requires a fit (press fit, threading) and the user didn't say
  whether they want loose or tight.

A good clarifying question is **one** sentence with **two** named options.
Never list more than four.
