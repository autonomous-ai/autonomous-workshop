- **The full tier's receipt now names the overhang angle, not just the
  nozzle.** ADR 0063 put `--nozzle 0.4` in the command precisely so the receipt
  would record the threshold the print-ready claim was measured against — but
  the overhang gate's threshold was left to `verify_project`'s own default, so
  the receipt did not say which angle the claim rested on and would silently
  follow an upstream default if it ever moved. The full tier's command is now
  `--fresh --strict-fit --print-gates --nozzle 0.4 --overhang-angle 45`, with
  the angle a named constant beside the nozzle. Report bytes are unchanged:
  `verify_project` parses the flag to the same `45.0` its default produced.
- **A CAD-gate rejection no longer banks the wrong anti-pattern in the shared
  game vault.** The finding the host writes for a rejection embeds the tier, and
  the full tier is spelled `full-with-thickness` — so the keyword classifier saw
  `thickness` in *every* full-tier rejection and filed them all under
  `underbuilt-shell`, ahead of the class the evidence named. `_cad_gate_failure`
  now passes `classify_text` (the verifier's tail alone) beside the human-facing
  finding, and `build_make_rows` classifies on it while banking the finding
  unchanged.
- **Host CAD-gate codes that never refused the geometry are protocol slips.**
  `cad-not-print-ready`, `sealed-product-changed`, `verifier-timeout` and
  `verifier-output-limit` join `PROTOCOL_CODES`. Each carries a passing verifier
  log, or none at all, as its finding; matched by keyword such a log reads as a
  design failure — a clean interference pass printing `interfere` banked a
  `sealed-volume-overlap` lesson against a design that had none.
  `verifier-nonzero`, the code that means the verifier measured and refused, is
  still classified.
- **A print gate's own verdict outranks a keyword guess.** New `GATE_VERDICTS`
  reads `RESULT: WALL BELOW MINIMUM` and `RESULT: NEEDS SUPPORT` before the
  keyword sweep. The check names above those lines (`wall >= 0.40 mm`, `no face
  under 45 deg needs support`) print on pass and fail alike, and the sweep runs
  both gates per part, so one tail can carry a passing wall check beside an
  overhang refusal.
- `NativeCadGateEvidence`'s field defaults named the full tier with the lower
  tier's verifier mode — a pair no policy accepts, so any construction relying
  on them raised `native CAD gate verification tier is invalid`. The default is
  now the tier that claims nothing. Stale notes corrected alongside:
  `NATIVE_CAD_LEGACY_FULL_VERIFIER_MODE` said it was retained so a historical
  receipt still parses, which it does not, and `posed_occurrences` still
  described `parts/` as holding STLs.
