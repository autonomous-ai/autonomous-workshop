#!/usr/bin/env python3
"""Render a text2game phase-1 result into /root/shared-reports for phone reading."""
import json
import subprocess
import sys
from pathlib import Path

import os
HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / sys.argv[1]
SHARE = Path(os.environ.get("SHARED_REPORTS", "/root/shared-reports"))
MD2HTML = str(Path(os.environ.get("TEXT2CAD_DIR", "/root/text2cad")) / "md2html.py")
SLUG = sys.argv[1]


def render(md_text: str, name: str, title: str, imgs=()):
    tmp = SHARE / f"_{name}.md"
    tmp.write_text(md_text, encoding="utf-8")
    cmd = [sys.executable, MD2HTML, str(tmp), str(SHARE / f"{name}.html"), title]
    for src, cap in imgs:
        cmd += ["--img", f"{src}|{cap}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    tmp.unlink(missing_ok=True)
    if r.returncode:
        print(f"  FAIL {name}: {r.stderr[-200:]}")
    else:
        print(f"  {name}.html")


def sev(items, key="severity"):
    return [i for i in items if i.get(key) == "high"]


comps = json.loads((OUT / "components.json").read_text(encoding="utf-8"))
comps = comps if isinstance(comps, list) else comps.get("components", [])
critic = json.loads((OUT / "critic.json").read_text(encoding="utf-8")) \
    if (OUT / "critic.json").exists() else []
cons = json.loads((OUT / "consistency.json").read_text(encoding="utf-8")) \
    if (OUT / "consistency.json").exists() else []
mech = json.loads((OUT / "mechanisms.json").read_text(encoding="utf-8"))
p1 = json.loads((OUT / "phase1.json").read_text(encoding="utf-8")) \
    if (OUT / "phase1.json").exists() else {}

# --- components table ---
rows = ["| part | qty | class | bbox mm | tol | mates |", "|---|---|---|---|---|---|"]
for c in comps:
    bb = "x".join(str(x) for x in c["target_bbox_mm"])
    rows.append(f"| `{c['id']}` | {c['qty']} | {c['class']} | {bb} | "
                f"{c['tolerance_mm']} | {', '.join(c.get('mates_with') or []) or '-'} |")
duty = ["", "## What each part must physically do", ""]
for c in comps:
    duty.append(f"**`{c['id']}`** — {c['role']}  \n{c['duty']}\n")
render("# Components\n\n" + "\n".join(rows) + "\n" + "\n".join(duty),
       f"{SLUG}-components", "Components")

# --- the docs ---
for src, name, title in (("gdd.md", "gdd", "Game design document"),
                         ("todo.md", "todo", "Build order"),
                         ("referee.md", "referee", "Referee log"),
                         ("revisions.md", "revisions", "What the reviser changed")):
    if (OUT / src).exists():
        render((OUT / src).read_text(encoding="utf-8"), f"{SLUG}-{name}", title)

# --- index ---
ch = (OUT / "checkpoint.md").read_text(encoding="utf-8") if \
    (OUT / "checkpoint.md").exists() else ""
lines = [f"# {SLUG}", "", "## Checkpoint", "", "```", ch.strip(), "```", "",
         "## Read", "",
         f"- [Game design document]({SLUG}-gdd.html) — the rules, every one numbered",
         f"- [Components]({SLUG}-components.html) — {len(comps)} designs, "
         f"{sum(c['qty'] for c in comps)} pieces, what each must physically do",
         f"- [Build order]({SLUG}-todo.html) — 7 groups with exit criteria",
         f"- [Referee log]({SLUG}-referee.html) — games played against the rules",
         f"- [Revisions]({SLUG}-revisions.html) — what changed and what was refused",
         "", "## Locked mechanisms", "",
         "  \n".join(f"`{m}`" for m in mech.get("chosen", [])), "",
         f"> {mech.get('interaction', '')}", ""]

hi = sev(critic)
lines += ["## Blocking issues", ""]
if hi:
    for i in hi:
        lines += [f"**{i.get('where', '?')}** — {i.get('issue', '')}", "",
                  f"> fix: {i.get('fix', '')}", ""]
else:
    lines += ["None from the critic.", ""]
ch_cons = sev(cons)
lines += [f"Machine checks: **{len(ch_cons)} high**, {len(cons) - len(ch_cons)} warn.", ""]
med = [i for i in critic if i.get("severity") in ("medium", "low")]
if med:
    lines += ["## Waived — watch for these at the table", ""]
    lines += [f"- **{i['severity']}** {i.get('issue', '')}" for i in med]

img = []
if (SHARE / "keep-the-light-concept-v1.png").exists():
    img = [("keep-the-light-concept-v1.png", "Concept image the panel produced "
            "when it picked this game — a note, not the spec")]
render("\n".join(lines), f"{SLUG}-phase1", f"{SLUG} — phase 1", img)
print(f"\nhttp://178.128.89.39/{SLUG}-phase1.html")
