# Exact-state motion presentation

For coupled mechanisms, export 8–48 ordered state STLs from the exact final
CAD and the same kinematics used by `measure/motion.json`. Run:

```bash
python "$CAD_SKILL_ROOT/scripts/motion_presentation.py" <project> \
  --state-stl measure/states/00.stl --state-stl measure/states/01.stl ...
```

State paths are project-relative. This writes `snap/motion.gif` using one camera
and common framing, and `snap/MOTION-EVIDENCE.json` binding source, state,
motion-condition and animation hashes. Generate after all source edits.

The Workshop Manager uses the workflow's `references/motion-review-v1.md` to
obtain one independent animation read and `snap/MOTION-REVIEW.json` from the
same bounded signature critic. Still images continue to judge finish and form.
Final verification rejects missing or stale evidence for a declared coupled
mechanism before expensive geometry checks. Assembly-only paths do not require
an operating animation. `check_motion` remains mandatory when applicable;
animation and kinematic simulation cannot establish physical operation.
