# Setup

The cadcode skill ships as a directory of Python scripts + markdown
references. To use it, you need:

1. A Python 3.11+ with CadQuery installed.
2. The skill discoverable by your agent (Claude Code, Cursor, etc.).

## 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

That pulls in ``cadquery`` and ``numpy``. CadQuery brings ``OCP`` (the
OpenCASCADE Python bindings, ~150MB). The cadpy artifact pipeline is
vendored into ``scripts/packages/cadpy/`` at build time by Panda's
``scripts/build/build-skill-runtimes.sh``; its own runtime deps
(``trimesh``, ``pygltflib``, …) get satisfied alongside CadQuery in the
shared Python sidecar.

If you use ``uv``:

```bash
uv pip install -r requirements.txt
```

If you keep a venv specifically for the skill, point your agent at that
venv's ``python`` — the skill uses ``sys.executable`` to spawn the
sandboxed worker, so whichever Python invokes the scripts must have
CadQuery.

## 2. Install the skill into your agent

```bash
npx skills add <owner/repo>
```

This symlinks ``skills/cadcode`` into:

- ``~/.claude/skills/cadcode/`` for Claude Code
- ``~/.cursor/skills/cadcode/`` for Cursor
- ``~/.codex/skills/cadcode/`` for Codex
- (etc., per the skills.sh CLI)

Or symlink manually for local development:

```bash
ln -sfn /path/to/this/repo/skills/cadcode ~/.claude/skills/cadcode
```

## 3. Sanity check

```bash
python ~/.claude/skills/cadcode/scripts/cad \
    ~/.claude/skills/cadcode/assets/example_cube_with_hole.py \
    --out-dir /tmp/cadcode-test
```

Expect a JSON line on stdout with ``"ok": true`` and four files in
``/tmp/cadcode-test/``: ``example_cube_with_hole.{py,stl,step,png}``.

If that works the skill is installed correctly. Start a chat with your
agent and say "use the cadcode skill to make a 30mm cube with a 10mm
hole" — it should locate the skill, write a ``.py``, run the script, and
hand you an STL.

## Troubleshooting

- **``ModuleNotFoundError: No module named 'cadquery'``** — the Python
  your agent shells out to doesn't have CadQuery. Either install it
  globally or point your agent at the venv's ``python`` explicitly.

- **``sandbox timeout after 30s``** on complex parts — bump
  ``--wall-clock-s 60`` for that specific run, or simplify the model.

- **``Circular hole renders as polygon``** — re-run with
  ``--mesh-tolerance 0.05`` (or 0.02 for very small holes).

- **macOS Gatekeeper blocks the binary** — CadQuery ships from PyPI and
  doesn't trigger this, but if you use a system OpenCASCADE you may need
  ``xattr -d com.apple.quarantine /path/to/lib``.
