- Let the host CAD gate accept the verifier's per-part `measure/overhang-*.md`
  reports as volatile, exactly like the thickness reports. The resynced CAD
  skill's `check_overhang` echoes its invocation path into each report, so the
  isolated fresh rebuild always rewrote those bytes and every multi-part Make
  failed `declared-cad-output-changed` on the first gate after the resync.
