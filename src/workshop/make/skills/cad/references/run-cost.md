# Running a full pipeline

What each command of a run costs, which of them to run per round and which once
at the end, and two things that quietly break a run.

An interrupted build is safe for the lock — `coordination/lock.py` is a
kernel-owned flock, released when the process dies — and unsafe for the package
cache. Every writer renames atomically, so a killed build leaves `__cadgen__/`
holding a mix of new and old files that are each individually complete: exactly
the staleness `step-generation.md` describes under "Shared-library cache
defect", and every deterministic check will agree with it. So after killing a
build, `rm -rf <project-dir>/__cadgen__` before the retry.

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
