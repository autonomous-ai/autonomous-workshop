# Adopted delivery STEP inspection preparation

Prepared only; no CAD inspection was executed in this task. `requests.jsonl` contains 98 native requests: refs with facts, planes and positioning, then full validate for each of 44 sculpture parts and five separate coupon pieces. Targets are the actual adopted files under product/parts and product/coupon-kit. There are no same-stem Python generators beside these files.

`input-bindings.json` pins all 49 delivery STEP hashes, their exact export hashes, both adopted manifests, the current assembly STEP/package, and prior identity/export evidence. Expected count is one positive-volume solid per delivered file, print-bed min Z=0 within 0.00001 mm. Native raw-file packages do not exist yet; their paths/hashes must be recorded after execution, rather than reusing generated-source packages.

From the workspace root, run the cheap preflight:

```bash
<HOME>/.local/share/autonomous-workshop-python/bin/python artifacts/make/r0001/visual-repair-production/inspection/preflight.py
```

Only after the Manager authorizes a CAD process slot, run one attached batch:

```bash
CADGEN_WARM=0 MALLOC_ARENA_MAX=2 MALLOC_TRIM_THRESHOLD_=131072 PYTHONDONTWRITEBYTECODE=1 <HOME>/.local/share/autonomous-workshop-python/bin/python .agents/skills/cad/scripts/inspect batch < artifacts/make/r0001/visual-repair-production/inspection/requests.jsonl > artifacts/make/r0001/visual-repair-production/inspection/results.jsonl 2> artifacts/make/r0001/visual-repair-production/inspection/progress.log
```

Preserve any existing results/logs on retry. Inspect every request's `ok`, `exitCode` and nested native result; outer batch success is insufficient. Verify returned STEP hashes and facts count, record native validation findings or UNVERIFIED operations, and pin native raw package hashes after completion. Native BRep cache reuse is allowed; no custom evidence substitution is proposed. These requests do not add printability, motion, assembly-interference or physical-fit claims. Product and original export evidence are untouched.
