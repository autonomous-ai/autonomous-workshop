# cadpy (vendored)

This directory is a **build-time vendor target** for `packages/cadpy/` from
the Panda repo root. It is left empty in source control on purpose.

The build script `scripts/build/build-skill-runtimes.sh` (Panda root) copies
the canonical `packages/cadpy/src/cadpy/` tree into this folder so the
cadcode skill remains self-contained at runtime — per Panda's repo rule
that a skill never reaches outside its own directory at runtime.

## During development

This directory ships empty. The runner imports
`cadpy.generation.generate_step` via the standard `import cadpy`
mechanism. Tests inject a fast in-process stub via
`CADCODE_TEST_CADPY_PATH` (see `tests/conftest.py`) so the suite doesn't
pay for full OCCT STEP exports per assertion. The real wrapper landed
with Track A's follow-up and is exercised end-to-end by
`packages/cadpy/tests/test_generate_step_wrapper.py`.

## After Track A merges

Run `scripts/build/build-skill-runtimes.sh` once from the repo root to
populate this directory. Do not hand-edit; edits to the canonical
`packages/cadpy/` source are the only way to change vendored contents.
