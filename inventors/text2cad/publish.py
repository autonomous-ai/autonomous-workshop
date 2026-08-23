#!/usr/bin/env python3
"""Publish a finished part to Panda Social as a DRAFT design.

    ./publish.py <slug>

Flow (all inside the VM): upload hero/parts renders via admindash /uploads
(CDN) -> bin/importdesign inserts the design with status=draft -> Telegram
tells Tam to review. The human confirmation IS the draft->public flip in
admindash — this script never publishes anything publicly.

Needs in .env: ADMIN_TOKEN (admindash bearer), PANDA_OWNER_ID (24-hex user id
that owns imported designs). Missing either -> graceful skip.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADMINDASH = os.environ.get("ADMINDASH_URL", "http://localhost:8090")


def load_env():
    for line in (HERE / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


def upload(path: Path, token: str) -> str:
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: Bearer {token}",
                        "-F", f"file=@{path}", f"{ADMINDASH}/api/uploads"],
                       capture_output=True, text=True, timeout=120)
    m = re.search(r"https?://[^\s\"']+", r.stdout)
    if not m:
        raise SystemExit(f"upload failed for {path.name}: {r.stdout[:200]}")
    return m.group(0)


def upload_project(out_dir: Path, slug: str, project_url: str) -> bool:
    """Push the FE project files (assembled STL + _tree.json) to the history's
    CDN prefix so the platform viewer isn't empty. Best-effort: a failure keeps
    the draft usable (thumbnails still show) and the bridge pattern
    (out/eclipse-v2/gcs_project.py) can repair later."""
    stl = out_dir / f"{slug}.stl"
    if not stl.is_file():
        stl = out_dir / "main.stl"
    if not stl.is_file():
        print("publish: no STL found — viewer stays empty until bridged")
        return False
    cmd = ["/root/gcsvenv/bin/python", str(HERE / "gcs_upload_project.py"),
           str(stl), project_url]
    fe_parts = out_dir / "fe_parts"
    if fe_parts.is_dir() and any(fe_parts.glob("*.stl")):
        cmd.append(str(fe_parts))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(f"publish: project upload FAILED (bridge later): {r.stderr[-300:]}")
        return False
    return True


def apply_part_colors(slug: str) -> str:
    """Key the design's part colors the way the FE resolves them (fe_colors.py:
    FE group dump -> owner map -> thumbnail_jobs upsert + strict verify).
    Best-effort; returns a Telegram warning line on failure, "" on success."""
    r = subprocess.run(["/root/.local/bin/uv", "run", "--with", "trimesh",
                        "--with", "numpy", "--with", "pymongo",
                        "python", str(HERE / "fe_colors.py"), slug],
                       capture_output=True, text=True, timeout=900, cwd=HERE)
    tail = (r.stdout + r.stderr).strip().splitlines()
    print("\n".join(tail[-4:]))
    if r.returncode != 0:
        return "\n\u26a0 part colors NOT keyed \u2014 ch\u1ea1y fe_colors.py tay."
    return ""


def telegram(text: str) -> None:
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_DM", "")
    if tok and chat:
        subprocess.run(["curl", "-s", f"https://api.telegram.org/bot{tok}/sendMessage",
                        "-d", f"chat_id={chat}", "--data-urlencode", f"text={text}"],
                       capture_output=True, timeout=30)


def main() -> int:
    load_env()
    slug = sys.argv[1]
    out_dir = HERE / "out" / slug
    token = os.environ.get("ADMIN_TOKEN", "").strip()
    owner = os.environ.get("PANDA_OWNER_ID", "").strip()
    if not token or not owner:
        print("publish: skipped — set ADMIN_TOKEN and PANDA_OWNER_ID in .env")
        return 0
    if (out_dir / "published.json").is_file():
        print("publish: already published — skip")
        return 0
    brief = (out_dir / "brief.md").read_text(encoding="utf-8")
    m = re.search(r"^#\s+(.+)$", brief, re.M)
    title = m.group(1).strip() if m else ""
    if m and title.lower() == "title":  # briefs often start with a literal "# Title" label
        rest = brief[m.end():].lstrip().splitlines()
        title = next((l.strip() for l in rest if l.strip() and not l.startswith("#")), "")
    title = (title or slug.replace("-", " ").title())[:120]
    run = json.loads((out_dir / "run.json").read_text(encoding="utf-8")) \
        if (out_dir / "run.json").is_file() else {}
    prompt = run.get("prompt", "")
    # Briefs may be a fenced ```design-brief JSON block with no prose at all —
    # drop fenced blocks first so raw JSON never becomes the description.
    prose = re.sub(r"```.*?```", "", brief, flags=re.S)
    # Prefer the brief's own Concept section; repair sessions prepend revision
    # blockquotes at the top, and those are build notes, not sales copy.
    concept = re.search(r"^##\s*Concept\s*$(.*?)^##", prose, re.S | re.M)
    body = concept.group(1) if concept else prose
    paras = [p.strip() for p in body.split("\n\n")
             if p.strip() and not p.startswith("#") and not p.lstrip().startswith(">")]
    desc = re.sub(r"[*_`]", "", paras[0])[:500] if paras else (prompt or title)[:500]

    thumbs = []
    for name, src in (("hero.png", "_assembled.png"), ("parts.png", "_qa.png")):
        p = out_dir / name
        # hero.png/parts.png are frozen at DRAFT time — they are the approved
        # visual contract, and BUILD spends hours refining the geometry after
        # that. The storefront has to show what actually shipped, so prefer the
        # newer render BUILD left in the review dir.
        alt = out_dir / f"{slug}_review" / src
        if alt.is_file() and (not p.is_file() or alt.stat().st_mtime > p.stat().st_mtime):
            p = alt
        if p.is_file():
            thumbs.append(upload(p, token))
    if not thumbs:
        raise SystemExit("publish: no renders found to upload")

    r = subprocess.run([str(HERE / "bin" / "importdesign"),
                        "-title", title, "-desc", desc, "-owner", owner,
                        "-thumbs", ",".join(thumbs), "-prompt", prompt,
                        "-tags", "text2cad,3d-print"],
                       capture_output=True, text=True, timeout=120,
                       cwd=os.environ.get("BACKEND_DIR", "/root/panda-social-backend"))
    if r.returncode != 0:
        raise SystemExit(f"importdesign failed: {r.stderr[-300:]}")
    info = json.loads(r.stdout.strip().splitlines()[-1])
    (out_dir / "published.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    viewer = ""
    if info.get("project_url"):
        if upload_project(out_dir, slug, info["project_url"]):
            viewer = apply_part_colors(slug)
        else:
            viewer = "\n⚠ project files NOT uploaded — viewer trống, cần chạy bridge."
    telegram(f"📦 text2cad DRAFT imported: {title}\nid={info['id']} status={info['status']}{viewer}\n"
             f"Duyệt trong admindash → đổi status sang public để lên feed.")
    print(f"published as draft: {info}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
