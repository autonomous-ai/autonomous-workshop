#!/bin/sh
# Exit 0 when this machine can run the Workshop harness. One line per check;
# Harness shows them. `miss` fails, `warn` does not. cwd = the Workshop checkout.
set -u
cd "$(dirname "$0")/../.."
status=0
say() { printf '%-5s%s\n' "$1" "$2"; }
miss() { say miss "$1"; status=1; }

if command -v uv >/dev/null 2>&1; then say ok "uv $(uv --version 2>/dev/null | awk '{print $2}')"; else miss "uv (https://docs.astral.sh/uv/)"; fi

if [ -x .venv/bin/python ]; then
  version="$(.venv/bin/python -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null || echo unknown)"
  case "$version" in
    3.1[1-9].*|3.[2-9][0-9].*) say ok "python $version (.venv)" ;;
    *) miss "python >= 3.11 in .venv (found $version); rerun harness/toolchain/setup.sh" ;;
  esac
  if .venv/bin/python -c 'import cadgen, build123d' 2>/dev/null; then
    say ok "cadgen + build123d import"
  else
    miss "cadgen/build123d in .venv; rerun harness/toolchain/setup.sh"
  fi
else
  miss ".venv/bin/python; run harness/toolchain/setup.sh"
fi

if command -v codex >/dev/null 2>&1; then say ok "codex $(codex --version 2>/dev/null | awk '{print $2}')"; else miss "codex on PATH (https://developers.openai.com/codex)"; fi

if command -v node >/dev/null 2>&1; then
  major="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
  if [ "$major" -ge 20 ] 2>/dev/null; then say ok "node $(node --version)"; else miss "node >= 20 for the 3D viewer (found $(node --version))"; fi
else
  miss "node >= 20 on PATH for the 3D viewer"
fi

if [ -f harness/viewer/backend/server.mjs ] && [ -f harness/viewer/dist/index.html ]; then
  say ok "3D viewer runtime (harness/viewer)"
else
  miss "harness/viewer/backend/server.mjs or dist/index.html"
fi

if [ -x .venv/bin/python ] && PYTHONPATH="$PWD/harness/viewer/packages/cadpy/src" .venv/bin/python -c 'import cadpy.step_artifact' 2>/dev/null; then
  say ok "STEP-to-GLB converter (cadpy on the .venv)"
else
  miss "cadpy.step_artifact importable on .venv (harness/viewer/packages/cadpy); rerun harness/toolchain/setup.sh"
fi

exit $status
