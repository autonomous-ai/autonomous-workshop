# Review a moving product with motion evidence

Keep the canonical schema-v6 signature review and its independent
critic limit. Images judge appearance. An exact-CAD animation judges whether
the intended action is visible. `check_motion` separately tests the declared
coupled motion, drive contact, collision and retention conditions. None is a
physical print or performance test. Do not demand that still pictures prove
motion or repair sound geometry solely because a still sheet cannot show time.

For an operating mechanism declare its complete cycle as
`coupled_motion_collision` in `measure/motion.json`, including the fixed frame
and driven outputs. Assembly-only paths keep their existing checks and need
no operating animation. Do not omit the coupled cycle to avoid this contract.

Export 8–48 ordered state STLs from the same final CAD source and kinematics
used by the motion conditions. Keep one common world frame. Render once:

```bash
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/motion_presentation.py <cad-project> \
  --state-stl measure/states/00.stl --state-stl measure/states/01.stl ...
```

Paths are relative to the CAD project; repeat the option for every state.
The tool writes `snap/motion.gif` at a fixed camera and common scale, plus
`snap/MOTION-EVIDENCE.json` binding the exact sources, states, motion manifest
and animation. Write all source helpers before rendering; source changes
invalidate it. Do not manually animate disconnected decorative parts.

The same independent critic inspects the actual GIF (or its ordered decoded
frames if its image tool cannot play GIFs), alongside the hero and signature
images, before learning the Wish. It records an unprompted motion observation,
then compares it with the Wish and current concept. It may also inspect the
bound motion conditions after reveal, but must not infer physical performance.
Repair evidence presentation when that is defective; repair geometry when
geometry is defective. Both stay within the existing two review rounds.

Preserve its verdict as canonical JSON in `snap/MOTION-REVIEW.json`:

```json
{"schema_version":1,"evidence_sha256":"<sha256 of MOTION-EVIDENCE.json>","concept_sha256":"<same as signature review>","reviewer":"<same independent critic>","review_rounds":1,"blind_motion_read":"<what the critic actually observed>","motion_matches_wish":true,"simulation_not_physical_test":true}
```

Use the actual review-round count. A failed motion judgment cannot be set
true to advance. Final verification and the finalizer reject missing/stale
animation, sources, states or review for a coupled mechanism. The host still
reruns the existing mechanical and printability gates on the exact product.
