# Running a full pipeline

What each command costs, which to run per round and which once at the end.

An interrupted build is safe for the lock — `coordination/lock.py` is a
kernel-owned flock, released when the process dies — and unsafe for the package
cache. Every writer renames atomically, so a killed build leaves `__cadgen__/`
holding a mix of new and old files that are each individually complete: exactly
the staleness `step-generation.md` describes under "Shared-library cache
defect", which every deterministic check will agree with. After killing a
build outside a restricted product run, clear only that project's `__cadgen__`
before the retry. Inside a Workshop product run, do not delete protected cache
directories: regenerate every affected target explicitly with `scripts/gen
<targets...> --write --force`, then use the non-`--fresh` iterative preflight.
The trusted host performs the authoritative isolated fresh rebuild.

## Two measurements, and the second inverts the first

Both with `CADGEN_WARM=1`. Left: a 10-part assembly with lofted organic
surfaces. Right: a six-part prismatic mechanism — a vane pump, cylinders,
revolves, polar-patterned cuts, ~110 faces on its largest part, no lofts.

| step | organic 10-part | prismatic 6-part |
|---|---|---|
| `check_layout` | 0.1 s | 0.1 s |
| `gen` (all entries, warm) | 2 m 55 s | 2.8 s |
| `inspect interfere` | 5 m 03 s | **1.0 s** |
| `inspect validate` | 7 m 56 s | **2.2 s** |
| `check_fit` | 47 s | 4.1 s |
| `check_motion` | 5 m 26 s (25 checks) | 10.0 s (8 checks) |
| `check_mount` (1 mount) | 1.4 s | — |
| `render_views` (4 views) | 7 s | 42.1 s with matches + `--compare-step` (before the full-size refine replay; see below) |
| **whole suite once** | **~23 m 25 s** | **1 m 53 s** |

The suite totals were measured while the print gates ran off an exported STL.
The gates are still here and `--print-gates` still runs them, but they now
tessellate each entry's B-rep instead, so the export step in those totals is
gone and the tessellation is inside the gate. Treat both numbers as the right
order of magnitude rather than current figures; the per-command rows above were
measured independently and still hold.

The print gates are opt-in (`verify_project --print-gates`) and cost roughly
7-12 s per printable part per gate, of which ~5 s is the interpreter and
`build123d` import that a standalone gate pays on every call. Thickness is the
dearest of the three because its voxel grid is set by the nozzle: halving
`--nozzle` roughly octuples its grid.

`validate` and `interfere` are more than half the organic run and **3 % of the
prismatic one**. Their cost is B-rep complexity, and a lofted organic assembly
has two orders of magnitude more of it than a barrel with some pockets. So read
the left column as *what an organic multi-part reconstruction costs*, not as
the price of a run: on a prismatic model the expensive commands are the two
that scale with **surface area and pixels** instead.

`check_mount` scales with mounts rather than with the model — one boolean per
obstacle solid the component's bbox reaches, plus two per hole. Its figure, like
`check_layout`'s, excludes the ~2 s interpreter import that
`CADGEN_WARM=1` cannot remove from a standalone gate, so one call is ~3.4 s in
practice.

A freeform obstacle breaks that scaling unless it is cropped: every boolean
and distance costs per face of the obstacle, and a component seated *inside* a
figure passes every bounding-box prefilter. A many-solid board in a
6000-face Bezier skin ran over 30 minutes in `check_mount`, and each sweep step
of `check_motion` cost seconds. Both gates now cut an obstacle of more than
200 faces once to the component's (or the whole sweep's) box plus a margin
before measuring, which leaves every answer exact; the same project then took
5 min and 45 s. Each crop is two booleans, the crop and its complement, and is
used only when their volumes add up to the whole: OCC once returned a box cut
of such a skin as two slivers without raising, and a sweep against it read
clear where the whole skin blocked. A crop that fails the sum falls back to
the whole obstacle.

## Where the pixel-bound commands go

`render_views` is dominated by one import — `import build123d` alone is 5.2 s of
every invocation, after which a view costs ~0.01 s and a searched pose ~20 ms.
On the prismatic model:

| | time | marginal |
|---|---|---|
| `import build123d` alone | 5.2 s | the fixed cost of *every* invocation |
| + build + tessellate + 4 named views | 6.3 s | +1.1 s |
| + `--compare-step` | 11.9 s | +5.6 s — final run only |
| 1 `--match`, one FOV | 13.1 s | +6.8 s per reference |
| 1 `--match`, `--search-fov 0,25,40` | 23.1 s | 2.6x — final run only |
| 3 `--match` **with `--poses-from`** | **7.8 s** | the search skipped, same IoU |

`verify_project --image-derived` runs only the named views and
`--compare-step`. The `--match` rows below describe the standalone
`render_views` tool; no Workshop gate scores a reference pose.

**A searched pose is scored twice, at two sizes.** The coarse sweep and its
halvings run at `SEARCH_SIZE` (240 px) because the sweep is hundreds of
renders; the halvings are then replayed at the size the gate scores
(`--size`, 480 px by default), so the pose kept is the one that maximises the
number the gate prints. The replay is `--refine` rounds of 27 renders at 4x
the pixels, and it roughly doubles a search: measured on a synthetic
three-box shape over a 15-degree grid, 1.25 s and 256 poses at 240 px
throughout against 2.54 s and 338 poses with the replay — and IoU 0.9719
against 0.9869, which is the point. Every `--match` row above predates the
replay; scale the search part of each by about two, and use `--poses-from` on
a rerun, which skips both.


A declared `--camera` does not change that budget: the windowed search plus
its two reflection searches (3 × 156 poses over three FOVs) took 2.37 s where
one free search (585 poses) took 2.89 s on the same mesh.

So the number of views is free and the size of the pose grid is not. One call
with every `--view` and every `--match` costs about what a single match costs,
and adding `--poses-from` turns 59.2 s of searching into 7.8 s of replay with
identical numbers. **Search once, replay while editing, search again at the end.**

**Do not let a local audit go unmeasured.** A `measure/check_landmarks.py` that
samples solids where it could read edges has been seen to cost 62 % of an
entire suite; the same ledger reading edges cost 0.004 s.
`image-derived-verification.md` has the numbers.

**"One machine, one run" is not advice.** Concurrent audit processes and
parameter sweeps on one host inflated the since-removed thickness gate 5x — a tax on every
measurement taken while they were alive, and one that looks like a slow tool
rather than a busy machine. Check `ps` before believing a timing.

## Agent-loop cost is not wall-clock

Each model round re-sends the growing transcript — skills, spec, and prior tool
output — so billed tokens scale with **round count × context size**, not with
`gen` seconds. A round whose only job is to queue the next command still pays
for every byte already in the transcript, and anything bulky a tool printed once
is paid for again on every round after it. The tables above are CPU time; they
do not tell you when a round was wasted.

- Apply the source edit and the affected `gen`/`inspect` in the **same** model
  round.
- Run `interfere` standalone as the last check of the last edit round, and only
  then `verify_project`. Final mode rebuilds every entry first, then runs
  validate/interfere before the render tail and print gates and stops on a clash. The
  deliberate price is that `interfere` runs twice on the final shape;
  `verify_project` is not a per-edit probe.
- Read the whole failed pipeline record before editing. The runner collects all
  independent fit/local/spec failures in its cheap preflight group, then, once
  geometry is sound, collects mesh/overhang/thickness failures across every
  printable target. A failed export or mesh blocks only its dependent checks;
  it does not hide failures in later parts. Repair the collected batch in one
  source round instead of rerunning once per failing part.
- Keep catalog search compact. The step-parts script prints items and totals as
  one-line JSON and omits `facets` unless asked. On a ten-result query the old
  pretty-with-facets form measured 43.6 kB against 4.9 kB compact, the facets
  object alone accounting for 32.9 kB — every one of those kilobytes re-sent on
  every later round. `download_step_part.py --self-check` reproduces the shrink.
- Read a reference once. These documents are re-sent with every subsequent
  round, so loading one whose trigger has not fired is not a one-time cost.

## Spend that time deliberately

- **Run `validate` and `interfere` on the finished shape, not per round.**
  Neither answers a question that changes between edit rounds of the same
  shape. Per round the cheap gates catch what actually breaks.
- **Always name the project on the gates.** A bare `check_fit` scans the whole
  worktree and builds every part of every project in it.
- Do not re-run `gen` to look at something. A rebuild spends most of its time
  writing the GLB package, and nothing reads it.
- `CADGEN_WARM=1` on every call. It removes only a ~2 s import, but it is free.
- One machine, one run. OCP booleans are CPU-bound.
- **A coupled motion cycle is paid twice.** Final `verify_project` runs
  `check_motion` again, so a standalone run is worth it only while the
  manifest is still changing. Its cost is the exact booleans between parts
  whose boxes overlap at every sample (a pin inside its running holes,
  same-layer plates), not the mover count: parts in disjoint bands along an
  axis fail the box test and cost nothing. Measured on a plate linkage — 43
  movers, 21 obstacles, 180 samples plus three driven passes — 38 min and
  about 8 GB resident, the largest single gate of its suite.
- **Do not rebuild a body whose inputs did not change.** A generator that
  builds many independent bodies (station-stack sculpts, lofted segments,
  inlay sets) pays for all of them on every `gen`, serially, and deleting
  `__cadgen__/` does not make that cheaper. Build them through
  `scripts/cadcache.py`: `cached_map("module:function", items, root=...,
  inputs=..., sources=...)` keeps each body as a BREP under a hash of its code
  and data, loads the unchanged ones in about a second, and builds the changed
  ones at the same time, one process each, inside the same run. The key must
  name every file and parameter the body reads; a dependency left out of it is
  the one way the cache returns a stale body. Prove the switch once by
  comparing volume, face count and bounding box per body against an uncached
  build. `python "$CAD_SKILL_ROOT/scripts/cadcache.py"` is its self-check.

## Two things that quietly break a run

**The two bed flags do not take the same form**, and each rejects the other's:

```bash
python "$CAD_SKILL_ROOT/scripts/check_fit"      <project-dir> --bed 220 220
python "$CAD_SKILL_ROOT/scripts/verify_project" <project-dir> --bed 220x220x220
```

`check_fit` takes two numbers because it only asks about the footprint; the
runner takes `WxDxH` because a project declaration carries a height too. Declare
the bed once as a `--bed WxDxH` line in the project README/spec and both read it.
`verify_project --self-check` holds a fixture on the distinction.

**Keep stale generators out of the worktree.** `cadgen` resolves even an
explicitly named target by scanning the **whole worktree** for `*.py`
generators, so one file with a pre-migration `gen_step()` envelope takes
`inspect refs` and `inspect validate` down for *every* model, reported as
`{"ok":false}` — which reads as a broken model rather than a scan that never
finished, and costs a run its mandatory validation gate. Old CAD sources belong
outside the tree, not merely in `.gitignore`.
