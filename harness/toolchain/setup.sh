#!/bin/sh
# Run once by Harness at install, cwd = the Workshop checkout. Idempotent.
#
# Creates .venv from the pinned uv.lock on a Python >= 3.11 (cadgen's floor; uv
# downloads one when the machine has none). The 3D viewer under harness/viewer
# is prebuilt and needs only Node, so nothing else is installed here.
set -eu
cd "$(dirname "$0")/../.."
if ! command -v uv >/dev/null 2>&1; then
  echo "miss uv -- install it from https://docs.astral.sh/uv/ and rerun" >&2
  exit 1
fi
uv sync --frozen --python 3.11
echo "ok   python env $(.venv/bin/python -c 'import sys; print(sys.version.split()[0])') at $(pwd)/.venv"
