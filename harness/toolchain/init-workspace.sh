#!/bin/sh
# Run by Harness after the template copy, cwd = the workspace. Idempotent.
#
# Builds the template's placeholder part once, so the 3D pane shows a body the moment the tab
# opens instead of "no CAD entries" until the agent's first build. Best-effort: a create must
# never fail on it, and a workspace that already has a model keeps it.
set -eu
mkdir -p .harness snap measure
if [ ! -f model.step ] && [ -n "${HARNESS_DSH_DIR:-}" ] && [ -x "$HARNESS_DSH_DIR/.venv/bin/python" ]; then
  "$HARNESS_DSH_DIR/.venv/bin/python" "$HARNESS_DSH_DIR/src/workshop/make/skills/cad/scripts/gen" \
    model.step.py --write --json >/dev/null 2>&1 || true
fi
