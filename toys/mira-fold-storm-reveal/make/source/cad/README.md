# Storm Reveal CAD project

Storm Reveal is a three-part, hardware-free pocket puzzle. The flat cloud receiver carries a round drive pocket and a blind 90-degree guide track. The outer rainbow's integral square shaft passes through the inner lightning's derived square socket. The lightning's guide pin follows the cloud track, so one clockwise twist moves both motifs to the scene stop; the reverse twist resets the sleepy cloud.

Files:

- `assembled.step.py`: the project's sole combined entry, a deployed labeled assembly at the 90-degree stop (`PRINTABLE = False`).
- `part_cloud.step.py`: printable receiver with pockets facing upward.
- `part_rainbow.step.py`: printable outer rotor with square shaft.
- `part_lightning.step.py`: printable inner rotor with square socket and guide pin.
- `storm_reveal_lib.py`: one shared parameter block plus all part builders and assembly positioning.
- `cadfits.py`: exact run-local CAD-skill derivation helper vendored so isolated builds retain the same fit semantics.
- `measure/check_fit.py`: isolation-safe algebraic audit of the independently derived interfaces.
- `measure/motion.json`: declared 90-degree reveal and reset sweeps.

Assembly and use:

1. Hold the cloud with its sleepy face toward you.
2. Place the lightning rotor against the cloud face, aligning its guide pin with the track's closed end.
3. Pass the rainbow's square drive through the lightning socket and seat the drive in the cloud's round pivot pocket. This is a removable snug/slip assembly, not a snap.
4. Turn the rainbow clockwise to the 90-degree hard stop. Reverse the same motion to reset.

Print plan: all three parts print flat on a 220 x 220 x 220 mm bed with a 0.4 mm nozzle, rigid PLA or PETG, no supports. The cloud entry flips the product coordinate frame so its blind pockets face upward. The two motif entries already place their broad plates on the bed, with the pins/shaft rising vertically.

Digital limitations: rigid-body and geometry checks do not establish printer-specific friction, a successful physical print, long-term wear, drop retention, or uncoached human delight. The removable square connection is intentionally not a brittle latch; if a printer produces a loose socket, tune only the shared `LIGHTNING_SOCKET` derivation after a physical fit coupon.

For byte-identical host-equivalent regeneration, copy this CAD directory into
an otherwise empty temporary parent as `project` (excluding `__cadgen__`),
change to that parent, and run the verifier with the literal target
`project`:

```text
"$WORKSHOP_PYTHON" <cad-skill>/scripts/verify_project project --fresh --exports --strict-fit
```

The literal target name matters because the deterministic thickness reports
record their invocation paths.

The stored closed-state review image was generated from the same shared source with `build_assembly(angle_deg=0.0)`. It is intentionally not a second `*.step.py` entry, so the isolated host verifier can unambiguously auto-select `assembled.step.py`.

Fresh-output reproducibility: the CAD sources intentionally omit STEP presentation colours because the kernel emitted multi-colour presentation records in process-dependent order. Five cache-free generation processes across four Python hash seeds reproduce identical STEP bytes, and complete host-layout runs reproduce identical combined STEP/GLB, part STEP/STL, and thickness-report bytes. The submitted project excludes the disposable `__cadgen__/` cache and the runtime-specific `measure/verification-pipeline.md`; `--fresh` creates both only inside the verifier's isolated temporary copy. Optional print colour remains a user choice; the cloud, arch, and bolt are encoded by geometry.
