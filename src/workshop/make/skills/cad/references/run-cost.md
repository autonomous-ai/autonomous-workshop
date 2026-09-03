# Running a full pipeline

What each command of a run costs, which of them to run per round and which once
at the end, and two things that quietly break a run.

An interrupted build is safe for the lock — `coordination/lock.py` is a
kernel-owned flock, released when the process dies — and unsafe for the package
cache. Every writer renames atomically, so a killed build leaves `__cadgen__/`
holding a mix of new and old files that are each individually complete: exactly
the staleness `step-generation.md` describes under "Shared-library cache
defect", and every deterministic check will agree with it. So after killing a
build outside a restricted product run, clear only that project's `__cadgen__`
before the retry. Inside a Workshop product run, do not delete protected cache
directories: regenerate every affected target explicitly with `scripts/gen
<targets...> --write --force`, then use the non-`--fresh` iterative preflight.
The trusted host performs the authoritative isolated fresh rebuild.

## What a run actually costs

Measured on a 10-part assembly with lofted organic surfaces and `CADGEN_WARM=1`:

| step | time |
|---|---|
| `check_layout <project>` | 0.1 s |
| `check_mesh <part>.stl` | 0.1 s |
| `check_mount <project>` (1 mount) | 1.4 s |
| `render_views --view` (any number of views) | 7 s |
| `render_views --match` (249-pose search) | 12 s |
| `render_views --match --search-fov 0,25,40` | 19 s |
| `export <part>.step.py --stl` | 5.8 s |
| `check_fit <project>` | 47 s |
| `gen --force` (combined entry) | 1 m 11 s |
| `gen --force` (10 part entries, one call) | 2 m 55 s |
| `inspect interfere` (combined) | 5 m 03 s |
| `check_motion` (25 declared checks) | 5 m 26 s |
| `inspect validate` (combined) | 7 m 56 s |
| **every command once, no repair round** | **~23 m 25 s** |

The three `render_views` rows are dominated by one import: build123d alone
costs 5.4 s of them, `import_step` 0.3 s and tessellation 1.5 s, after which a
view costs ~0.01 s and a searched pose ~20 ms. So the number of views is free
and the size of the pose grid is not — and neither scales with the model the
way the B-rep commands below do.

`check_mount` is the one row not from that assembly: it was measured on a
single-mount bracket, and it costs one boolean per obstacle solid the component's
bounding box reaches plus two per mounting hole, so it scales with mounts rather
than with the model. Its figure excludes the ~2 s interpreter import, as
`check_layout`'s and `check_mesh`'s do: `CADGEN_WARM=1` removes that cost from
the `cadgen` CLIs and cannot remove it from a standalone gate, so a single
`check_mount` call costs ~3.4 s in practice.

So every command once is most of half an hour, before the spec is read or a
line of source is written, and **one repair round that re-runs `gen` and
`validate` adds a quarter of an hour again**. What makes it expensive is B-rep
geometry on the *combined* entry: `validate` and `interfere` are more than half
of it between them.

Two of those numbers were taken twice, under load ~25 from a second agent
session and again on a quiet machine. `validate` cost 8 minutes both times; the
`gen` and `check_motion` numbers are the contended ones and are upper bounds.

## A second measurement, and it inverts the table above

The same suite on a **six-part prismatic mechanism** — a vane pump: cylinders,
revolves, polar-patterned cuts, ~110 faces on its largest part, no lofts:

| step | time |
|---|---|
| `check_layout` | 0.1 s |
| `gen` (7 entries, `--write`, warm) | 2.8 s |
| `inspect interfere` | **1.0 s** |
| `inspect validate` | **2.2 s** |
| `measure/check_fit.py` (local) | 2.7 s |
| `measure/check_spec.py` (local) | 3.8 s |
| `measure/check_landmarks.py` (local) | 3.8 s |
| `check_fit` | 4.1 s |
| `check_motion` (8 conditions) | 10.0 s |
| `export --stl` x6 | 1.0 s |
| `check_mesh` x6 | 1.3 s |
| `check_thickness` x6 | **36.9 s** (before the `march` change below) |
| `render_views` (4 views + 3 searched poses + `--compare-step`) | **42.1 s** |
| `check_likeness` | 0.8 s |
| **the whole suite, once** | **1 m 53 s** |

`validate` and `interfere` are 3.2 s between them here — **not** half the run but
3 % of it. Their cost is B-rep complexity, and a lofted organic assembly has two
orders of magnitude more of it than a barrel with some pockets. So read the
first table as *what an organic multi-part reconstruction costs*, not as the
price of a run: on a prismatic model the expensive commands are the two that
scale with **surface area and pixels** instead, `check_thickness` and
`render_views`.

What that changes about how to spend a round:

- **Batch `render_views`, and replay its poses while sweeping.** Where its
  42.1 s goes, on this model:

  | | time | marginal |
  |---|---|---|
  | `import build123d` alone | 5.2 s | the fixed cost of *every* invocation |
  | + build + tessellate + 4 named views | 6.3 s | +1.1 s |
  | + `--compare-step` | 11.9 s | +5.6 s — final run only |
  | 1 `--match`, one FOV | 13.1 s | +6.8 s per reference |
  | 1 `--match`, `--search-fov 0,25,40` | 23.1 s | 2.6x — final run only |
  | 3 `--match` **with `--poses-from`** | **7.8 s** | the search skipped, same IoU |

  So one call with every `--view` and every `--match` costs about what one call
  with a single match costs, and adding `--poses-from` to that same command line
  turns 59.2 s of searching into 7.8 s of replay with identical numbers. Search
  once, replay while editing, search again at the end.
- **`check_thickness` was the per-part tax, and is now about a quarter of it.**
  8 s on a 65 cm3 housing and 1.3 s on a vane, both measured before `march`
  stopped stepping rays that had already left the material. That loop runs until
  the *last* ray resolves, and a ray fired down a long axis never resolves at
  all, so a few hundred stragglers carried the whole 400k-sample array 20x
  further than the work required -- 33x on a rocket shell. Re-measured after the
  change, on a five-part lamp at `--nozzle 0.25`: **42.4 s -> 10.6 s** for the
  set and **17.2 s -> 2.4 s** on its worst part, with byte-identical reports, the
  self-check unchanged, and 60/60 synthetic topologies matching the old
  implementation exactly. The figures above this bullet were not re-taken.

  What is left scales with surface area and with grid pitch, and pitch comes
  from the nozzle: `min_wall / 6`, so `--nozzle 0.25` builds a grid two and a
  half times finer than `--nozzle 0.4` and cost 3.1x as much on the same part.
  `--voxel` overrides it, at the price of a wider pass/fail band -- the gate
  fails only below `min_wall - pitch/2`, so a 0.40 mm grid puts +/-0.20 of slack
  on a 0.50 mm limit. The parts are independent files: running the five
  concurrently took that 10.6 s to 4.3 s on a 10-core host. Iterating one part
  at a time is no longer the saving it was.
- **Do not let a local audit go unmeasured.** `measure/check_landmarks.py` on
  this project cost **61.1 s** — 62 % of the entire suite — until one ledger row
  stopped sampling the solid and started reading its edges, which took it to
  0.004 s. `image-derived-verification.md` has the numbers.
- **"One machine, one run" is not advice.** Nine stale audit processes and two
  concurrent parameter sweeps on this host inflated `check_thickness` from 8 s
  to 40 s — a 5x tax on every measurement taken while they were alive, and one
  that looks like a slow tool rather than a busy machine. Check `ps` before
  believing a timing.

## Spend that time deliberately

- **Run `validate` and `interfere` once, at the end.** They are the two most
  expensive commands in the toolchain, and neither answers a question that
  changes between edit rounds of the same shape. Per round, the cheap gates —
  `check_layout` at 0.1 s, `check_fit` at 47 s — catch what actually breaks.
- **Always name the project on the gates.** `check_fit` bare scans the whole
  worktree and builds every part of every project in it — eleven projects' worth
  of geometry to answer a question about one.
- Do not re-run `gen` to look at something. A rebuild spends most of its time
  writing the GLB package, and nothing reads it.
- `CADGEN_WARM=1` on every call. It only removes a ~2 s import, which is noise
  against the numbers above, but it is free.
- One machine, one run. A second agent session on the same host inflates every
  number here; OCP booleans are CPU-bound.

## The two bed flags do not take the same form

Each rejects the other's, and they are one letter apart in the docs:

```bash
python "$CAD_SKILL_ROOT/scripts/check_fit"  <project-dir> --bed 220 220
python "$CAD_SKILL_ROOT/scripts/check_mesh" <project-dir>/part_x.stl --bed 220x220x250
```

`check_fit` takes two numbers because it only asks about the footprint;
`check_mesh` takes `WxDxH` because it also has a height to check. A project
declares its bed once, as a `--bed WxDxH` line in its README or spec, and both
gates read that declaration.

## Keep stale generators out of the worktree

`cadgen` resolves even an explicitly named target by scanning the **whole
worktree** for `*.py` generators. One file with a pre-migration `gen_step()`
envelope takes down `inspect refs` and `inspect validate` for *every* model, and
`validate` reports it as `{"ok":false}` — which reads as a broken model rather
than a scan that never finished, and costs a run its mandatory validation gate.

Old CAD sources belong outside the tree, not merely in `.gitignore`.
