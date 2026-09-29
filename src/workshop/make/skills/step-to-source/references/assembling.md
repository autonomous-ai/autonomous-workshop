# Assembling: the right part in the right place

The last stage of the route. By now every part is source (`parts/<role>.py`)
and the references have been released. The assembly entry turns those parts
into one specific model, and it owes two proofs: **every part is the right
part**, and **every part is in the right place**. Neither is a matter of
looking. Each comes from a stated source and a check that fails when it is
wrong.

The design knowledge behind every step below (reading and refuting a
placement verdict, finding the designer's source, datum kinds and frames,
det +1, datum-pair audits, solving linkages, scanning keys and tooth phase)
is in `skills/wiki/pages/reverse-engineering/kit-assembly-poses.md`
(`wiki show kit-assembly-poses`). Reading and classifying clashes is in
`wiki show kit-assembly-clash-diagnosis`.

## Where the pose comes from

Read the verdict `source_plan` printed for the set, and check it against the
parts before believing it
(`wiki show kit-assembly-poses#where-a-pose-can-come-from`):

| verdict | where the pose comes from |
|---|---|
| `assembled` | the files. Record each part's offset as a named placement **before** the references are released |
| `recentred` | datums and mates, derived with `cadfits` |
| `print_plates` (`assumed`) | the designer's photos or manual, then datums |

**"Is the combined file assembled correctly?"** is answered by this verdict
before any other check. For `print_plates` or `recentred`, the answer is no:
quote the evidence from the files (every part on Z = 0, offsets spanning
several plates, no part touching another), then offer the route below. Do not
run `interfere` on a kit layout to "check the assembly".

**Tell the user the cost up front, in one line.** A kit with a linkage takes
hours, not minutes. Show progress early: a mesh render of the solved pose next
to the designer's photos, before any `gen`.

**For `recentred` and `print_plates`, get the designer's source first**, and
check a supplied native assembly file for poses
(`wiki show cad-container-formats#assembly-files-carry-the-poses`). Copy build
photos or the manual into `<project>/ref/source_images/` (they are not
conversion outputs, so releasing the references keeps them), and cite them in
the assembly module's docstring by name and page or ID. How to find and read
them: `wiki show kit-assembly-poses#finding-the-designers-source`.

Write down, before any number:

- the **fixed root**;
- what each moving part **turns about, and on what**;
- the **variants**, and exactly which parts differ between them.

## Right part

- **The assembly builds parts only through `parts/<role>.build()`.** No
  `import_step`, no mesh, no copied geometry. After release, `release_refs`
  would block anything else anyway.
- **Every placed solid carries a label naming its role**, and a part with
  several moving bodies returns each body as its own labelled solid. Identify
  bodies by label, never by bounding-box position.
- **A bill of materials is asserted**: a role → count table per variant in the
  assembly parameters, and an assertion that the built labels match it
  exactly.
- **Parts the kit does not contain are not modelled.** Place their axis and
  state the omission.

## Right place

Datums are part parameters; derived placements are 4 × 4 matrices with no
literals; assembly choices live in their own labelled block. Write the frame
beside every datum. Orientation comes from a measured direction, and every
placement matrix asserts determinant +1. Seat each fixed part by one datum
pair and collect every other pair in an `audit()` that runs before geometry.
Solve moving parts from residuals, never type a pose, and render the pose
before trusting it. Scan D-flat and tooth-phase angles rather than computing
them. Each rule, with the failures that motivated it:
`wiki show kit-assembly-poses#datums-frames-and-orientation` and the
sections after it.

## Proof

Run these on the assembled entry, and report which ran:

1. **`audit()`** on every build: the BOM assertion, the datum pairs, det +1,
   the loop residuals.
2. **`inspect interfere`**, and **read every clash before fixing it**. Locate
   one clash by rebuilding just its two parts in scratch and taking
   `BRepAlgoAPI_Common`, not by rerunning the assembly. Classify it
   (`wiki show kit-assembly-clash-diagnosis#classify-it`), fix placements and
   conversion artefacts, report designed fits as fits, and rerun `interfere`
   once at the end.
3. **`check_motion`** for everything inserted, rotated or captured: both the
   allowed and the blocked direction (`$cad`'s `references/motion-manifests.md`).
4. **Render against the designer's photos** (`$cad`'s `render_review`, the
   views the photos were taken from). Only a render catches a flipped link or a
   part on the wrong side. It is evidence of appearance, not a gate.
5. Each variant is its own entry (`<name>_assembled.step.py`,
   `<name>_assembled_manual.step.py`), `PRINTABLE = False`. Parts print from
   their own `part_*.step.py`.

Import every project module at module scope in the assembly module. A lazy
import inside a function fails under `gen` (`$cad`'s
`references/step-generation.md`, "`sys.path` does not survive into
`gen_step()`").

Search the pose off CAD and build CAD once. Pose solves, phase scans and clash
scans iterate. Run them in scratch code, and `gen` when the answer is known.

## Working beside another session

Re-authoring the parts and assembling them are often two jobs on one project,
and an assembly session has overwritten a re-authoring session's `params.py`
that it had never read. Before writing a shared name, check the project with
`ls` or `git status`, and prefer names only your job uses. Agree who owns
which files. Announce every `gen`/`inspect` run, because the CAD daemon is one
per machine. Tell the re-authoring job which bodies you place one by one, so
it keeps them separate and labelled.
