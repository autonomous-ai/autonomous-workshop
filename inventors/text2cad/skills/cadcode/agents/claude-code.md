# Claude Code overrides

These instructions apply when this skill runs inside Claude Code (the CLI
or the desktop subprocess). Other hosts (Cursor, Codex, etc.) should
follow the main ``SKILL.md`` only.

## You are running the loop

The loop in ``SKILL.md`` —

```
understand → inspect → plan → write → render → read failure → fix → repeat
```

— is the entire point of this skill. Close the loop yourself with the
tools Claude Code already gives you:

| Step in the loop | Claude Code tool |
|---|---|
| **understand** | the user's prompt + any attached reference image (`Read`) |
| **inspect** | `Glob` / `Bash ls` on the workspace, `Read` on prior `.py` files |
| **plan** | reasoning (no extended thinking needed if the prompt is concrete) |
| **write** | `Write` — always an absolute path |
| **render** | `Bash` → ``python ~/.claude/skills/cadcode/scripts/cad <abs.py | project_dir>`` |
| **read failure** | parse the JSON line from stdout — check `ok`, `is_solid`, **`warnings`** |
| **review** | `Bash` → ``python ~/.claude/skills/cadcode/scripts/review <project_dir>``; `Read` each PNG it writes |
| **fix** | `Edit` (or `Write`) — same `.py`, smallest change |
| **repeat** | back to *render* |

If you stop before every part render looks right and `warnings` is empty,
you are leaving the loop half-run. Don't.

## Thinking budget

Claude Code's default models (Opus 4.7, Sonnet 4.6) activate extended
thinking for any non-trivial prompt. For simple parts (cube, plate, hook
with named dimensions) thinking adds 10–30s with no quality benefit.

**When the prompt has explicit dimensions and a single feature**: tell
yourself in the first internal thought "no extended thinking needed,
write the .py directly." Generation latency drops by ~5×.

**When the prompt is ambiguous or multi-feature** (phone stand, doorbell
mount, anything assembling parts): extended thinking is worth its cost —
it reduces compile-fail iterations.

## File writes

Always pass an **absolute path** to the ``Write`` tool. Claude Code's cwd
inside this subprocess is the user's session workspace, not the skill
directory. If you ``Write("foo.py", ...)`` it lands in the session
workspace — that's correct — but downstream ``Bash`` calls into the
skill scripts must use absolute paths because they shell out and may
have different cwds.

## Reading the render

``scripts/cad`` does not write a PNG — it returns the JSON facts
(`ok`, `is_solid`, `volume_mm3`, `bbox`, `warnings`). To *see* the model,
run ``scripts/review <project_dir>``: it renders the assembled model **and
every named part** to multi-view PNGs under ``<stem>_review/`` and re-lists
the warnings. Then ``Read`` each PNG. Claude Code's Read tool returns images
as multimodal content, so you actually see them. **This is mandatory** —
compile-success says the geometry is *valid*; only the per-part renders tell
you it's *right*, and only the per-part views expose a standoff floating
inside a tray or a strut poking through a plate that the assembled preview
hides.

Before declaring done: `warnings` must be empty, every part render must look
correct, and you must be able to say in one line what each part is for and
what it connects to. If any of those fail, edit the ``.py`` and re-run — that's
the loop. Do not skip the visual check.

## Tool budget

Hard limit: 6 model turns per user message (Claude Code's default).
Past that the user sees stalling. The soft cap of 4 iterations in
``SKILL.md`` keeps you safely under the hard limit.
