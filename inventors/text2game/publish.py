#!/usr/bin/env python3
"""Publish a finished game to Panda Social as a DRAFT design.

    ./publish.py <slug>

Ported from text2cad's publish.py. Same discipline, and the important half of
it is what this script does NOT do: it imports with status=draft and telegrams
a human. The draft->public flip is a person's decision in admindash, always.

What a game changes versus a single printed part:

- the description comes from discover.md's PITCH, because that is the sentence
  the panel actually picked the game on. text2cad reads brief.md, which this
  pipeline does not produce.
- print_specs numbers come from slice_report.json - measured by the slicer over
  the real mesh. Never let a model produce them.
- the RULEBOOK is deliberately left out. The product-page content contract is
  ~1,600 characters in total (use_case 400 + at most three 400-character story
  blocks, checked by models.ValidateDesignContent); rulebook.md for overcommit
  is 11,999 characters, 7.5x over, and story_blocks is a sales narrative rather
  than a manual. It belongs in the downloadable print bundle instead - not
  wired yet, deliberately skipped on Tam's call 2026-08-20.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ADMINDASH = os.environ.get("ADMINDASH_URL", "http://localhost:8090")
BACKEND = os.environ.get("BACKEND_DIR", "/root/panda-social-backend")
TEXT2CAD = Path(os.environ.get("TEXT2CAD_DIR", "/root/text2cad"))


# importdesign talks to Mongo directly and defaults to localhost:27017, which
# nothing listens on here - the real URI lives in the shared secrets file. Read
# it LINE BY LINE: MONGODB_URI's value breaks shell parsing, so `set -a; . .env`
# takes the whole file's exports down with it.
SECRETS = Path(os.environ.get("PANDA_SECRETS_ENV", "/root/panda-secrets/.env"))
# The GCS uploader runs in its own venv (google-cloud-storage); GCS_PY names
# its interpreter. uv is looked up on PATH unless UV_BIN says otherwise.
GCS_PY = os.environ.get("GCS_PY", "/root/gcsvenv/bin/python")
UV_BIN = os.environ.get("UV_BIN") or shutil.which("uv") or "/root/.local/bin/uv"


def _read_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            v = re.split(r"\s#", v, 1)[0]
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_env() -> None:
    _read_env_file(HERE / ".env")
    _read_env_file(SECRETS)
    if not os.environ.get("MONGODB_URI"):
        raise SystemExit(f"publish: no MONGODB_URI in {HERE}/.env or {SECRETS}")


def telegram(text: str) -> None:
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_DM", "")
    if tok and chat:
        subprocess.run(["curl", "-s", f"https://api.telegram.org/bot{tok}/sendMessage",
                        "-d", f"chat_id={chat}", "--data-urlencode", f"text={text}"],
                       capture_output=True, timeout=30)


def upload(path: Path, token: str) -> str:
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: Bearer {token}",
                        "-F", f"file=@{path}", f"{ADMINDASH}/api/uploads"],
                       capture_output=True, text=True, timeout=120)
    m = re.search(r"https?://[^\s\"']+", r.stdout)
    if not m:
        raise SystemExit(f"upload failed for {path.name}: {r.stdout[:200]}")
    return m.group(0)


def title_and_desc(out_dir: Path, slug: str) -> tuple:
    """Title from the slug, description from the panel's own PITCH line.

    discover.md is the record of what was picked and why; its pitch is one
    sentence written to sell the idea to a judge, which is the closest thing
    this pipeline has to storefront copy.
    """
    title = slug.replace("-", " ").title()[:120]
    dm = out_dir / "discover.md"
    desc = ""
    if dm.is_file():
        text = dm.read_text(encoding="utf-8")
        m = re.search(r"^WINNER:\s*\S+\s*\n+(.+?)\n", text, re.M)
        if m:
            desc = m.group(1).strip()
        mech = re.search(r"^Mechanism:\s*(.+)$", text, re.M)
        if mech and len(desc) < 380:
            desc = f"{desc} {mech.group(1).strip()}".strip()
    if not desc:
        seed = out_dir / "seed.md"
        desc = seed.read_text(encoding="utf-8").strip() if seed.is_file() else title
    return title, re.sub(r"[*_`]", "", desc)[:500]


def fe_key_colours(out_dir: Path) -> None:
    """Re-key part_colors.json to the uploaded sibling names.

    fe_colors prefixes `assembled_` but keeps whatever suffix it finds, and the
    CDN siblings are assembled_<id>.stl - so a bare `capacity_tray` key becomes
    `assembled_capacity_tray` and matches nothing. Phase 2 writes bare ids.
    """
    f = out_dir / "part_colors.json"
    if not f.is_file():
        return
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    keyed = {(k if k.endswith(".stl") else k + ".stl"): v for k, v in d.items()}
    if keyed != d:
        f.write_text(json.dumps(keyed, indent=2), encoding="utf-8")


def print_facts(out_dir: Path) -> str:
    """One line of MEASURED print numbers, or empty if nothing was sliced."""
    f = out_dir / "slice_report.json"
    if not f.is_file():
        return ""
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    comps = d.get("parts") or []
    pieces = sum(p.get("qty", 0) for p in comps)
    return (f"{len(comps)} printed designs, {pieces} pieces, "
            f"{d.get('total_grams')}g PETG, {d.get('total_print_time')} of printing")


def fit_desc(desc: str, facts: str, cap: int = 500) -> str:
    """Description + measured print facts inside `cap`, facts kept.

    This was `f"{desc} ({facts})"[:500]`, which appends the facts and then
    truncates the concatenation - so when the description is already at the cap,
    and it always is, the facts are added and immediately sliced back off.
    coach-party 2026-08-20 published with "scatters each round's a" as its last
    words and no print numbers at all.

    The facts are the only sentence here nobody can reconstruct: they are what
    the slicer measured over the real meshes. The pitch is in discover.md,
    gdd.md and the panel table. So the facts get their budget first and the
    prose is trimmed to what is left, on a word boundary.
    """
    facts = (facts or "").strip()
    desc = " ".join((desc or "").split())
    if not facts:
        return desc if len(desc) <= cap else desc[:cap - 1].rsplit(" ", 1)[0] + "\u2026"
    tail = f" ({facts})"
    room = cap - len(tail)
    if room < 40:                       # facts alone would eat the whole field
        return facts[:cap]
    if len(desc) > room:
        desc = desc[:room - 1].rsplit(" ", 1)[0] + "\u2026"
    return desc + tail


def upload_project(out_dir: Path, project_url: str) -> bool:
    """Push the assembled STL + every part to the viewer's CDN prefix.

    Best-effort by design: a failure leaves a usable draft with thumbnails, and
    the bridge pattern can repair the viewer later. A dead viewer is worse than
    no viewer only if it stops the import, so it does not.
    """
    stl = out_dir / "assembled.stl"
    if not stl.is_file():
        print("publish: no assembled.stl - viewer stays empty until bridged")
        return False
    up = TEXT2CAD / "gcs_upload_project.py"
    if not up.is_file():
        print(f"publish: {up} not found - viewer stays empty")
        return False
    cmd = [GCS_PY, str(up), str(stl), project_url]
    parts = out_dir / "fe_parts"
    if parts.is_dir() and any(parts.glob("*.stl")):
        cmd.append(str(parts))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    print(r.stdout.strip()[-400:])
    if r.returncode != 0:
        print(f"publish: project upload FAILED (bridge later): {r.stderr[-300:]}")
        return False
    return True


def apply_part_colors(slug: str, out_dir: Path) -> str:
    """Key the design's part colours the way the FE actually resolves them.

    Left out of the first version of this script and caught immediately: without
    it gcs_upload_project writes assembly_parts with every part #ffffff, so a
    locked palette that art_direction reasoned about - fluorescent chartreuse on
    the one piece a player must find in a hurry - never reaches the viewer.

    Not a filename->colour loop, which is why text2cad's tool is reused rather
    than reimplemented: on overcommit the FE dump produced 44 groups for 10
    parts, because slivers shed at contact faces take part numbers too. The
    extra 34 have to be owned geometrically or they render white beside the
    part they broke off.
    """
    fe = TEXT2CAD / "fe_colors.py"
    if not fe.is_file():
        return "\npart colours NOT keyed - fe_colors.py not found"
    r = subprocess.run([UV_BIN, "run", "--with", "trimesh",
                        "--with", "numpy", "--with", "pymongo", "python",
                        str(fe), slug, "--dir", str(out_dir)],
                       capture_output=True, text=True, timeout=1800, cwd=TEXT2CAD)
    print("\n".join((r.stdout + r.stderr).strip().splitlines()[-3:]))
    if r.returncode != 0:
        return f"\npart colours NOT keyed (rc={r.returncode}) - run fe_colors.py by hand"
    return ""


def main() -> int:
    load_env()
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    slug = sys.argv[1]
    out_dir = HERE / "out" / slug
    if not out_dir.is_dir():
        raise SystemExit(f"publish: {out_dir} not found")
    token = os.environ.get("ADMIN_TOKEN", "").strip()
    owner = os.environ.get("PANDA_OWNER_ID", "").strip()
    if not token or not owner:
        print("publish: skipped - set ADMIN_TOKEN and PANDA_OWNER_ID in .env")
        return 0
    if (out_dir / "published.json").is_file():
        print("publish: already published - skip")
        return 0

    fe_key_colours(out_dir)
    title, desc = title_and_desc(out_dir, slug)
    facts = print_facts(out_dir)
    desc = fit_desc(desc, facts)

    # renders/assembled.png is the coloured, correctly-positioned assembly.
    # The older *_review.png files are the print-orientation contact sheets and
    # must never reach a storefront: every part sits at the origin in them.
    thumbs = []
    for p in (out_dir / "renders" / "assembled.png", out_dir / "concept.png"):
        if p.is_file():
            thumbs.append(upload(p, token))
    if not thumbs:
        raise SystemExit("publish: no renders found to upload")

    r = subprocess.run([str(TEXT2CAD / "bin" / "importdesign"),
                        "-title", title, "-desc", desc, "-owner", owner,
                        "-thumbs", ",".join(thumbs), "-prompt", desc,
                        "-tags", "text2game,board-game,3d-print"],
                       capture_output=True, text=True, timeout=120, cwd=BACKEND)
    if r.returncode != 0:
        raise SystemExit(f"importdesign failed: {r.stderr[-300:] or r.stdout[-300:]}")
    info = json.loads(r.stdout.strip().splitlines()[-1])
    (out_dir / "published.json").write_text(json.dumps(info, indent=2), encoding="utf-8")

    viewer = ""
    if info.get("project_url"):
        if upload_project(out_dir, info["project_url"]):
            viewer = apply_part_colors(slug, out_dir)
        else:
            viewer = "\nproject files NOT uploaded - viewer empty, needs the bridge."
    telegram(f"text2game DRAFT imported: {title}\n"
             f"id={info.get('id')} status={info.get('status')}\n"
             f"{facts}{viewer}\n\n"
             f"Rulebook KHONG di kem (content toi da ~1600 ky tu, rulebook 12k).\n"
             f"Duyet trong admindash -> doi status sang public de len feed.")
    print(f"published as draft: {info}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
