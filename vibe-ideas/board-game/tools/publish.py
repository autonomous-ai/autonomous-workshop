#!/usr/bin/env python3
"""publish.py — put one SHIPPED board game on Panda Social as a DRAFT design.

    .venv/bin/python board-game/tools/publish.py <slug>
    .venv/bin/python board-game/tools/publish.py <slug> --dry-run
    .venv/bin/python board-game/tools/publish.py --all
    .venv/bin/python board-game/tools/publish.py <slug> --page         # rules/specs only
    .venv/bin/python board-game/tools/publish.py <slug> --new-version  # files again

`ship` is the owner saying the game is done; this is the only thing that
carries that decision out of the repo. It stops at DRAFT — private to its
owner — and the draft→public flip stays a human action in the app, exactly
like the text2cad pipeline this is ported from. Nothing here ever makes a
design public.

What it refuses to publish, and why:

  * a game whose queue state is not `shipped` — publishing is downstream of
    the owner's gate, never a substitute for it (`--force` overrides);
  * a game whose `gate.json` is missing or failed — the same invariant
    `audit.py` enforces on shipped ideas: nothing reaches the world unmeasured;
  * a game already in `published.json` — re-running is a no-op, so this is
    safe to call from a loop.

The rules go up in three places, because no single one of them holds a whole
rulebook: `RULES.md` is written into the published folder (complete, no
limit), the story blocks carry a walkthrough on the product page (10 sections
of at most 400 characters, and it says so when it had to stop early), and the
description carries the pitch. Editing the rules of a game that is already up
is `--page`; re-uploading its files is `--new-version`. Neither re-imports,
because a second import would fork the game into a second design.

The heavy half is `bin/publishdesign`, a small Go CLI compiled against the
panda-social-backend checkout (see publishdesign/build.sh). It calls
`services.ImportDesign` — the same function POST /designs/import runs — so the
CDN snapshot, the `_tree.json` the viewer reads, the GLB, the thumbnails, the
design_history row and the unique slug are all produced by the backend's own
code. This script's whole job is to decide WHETHER to publish and to hand that
call an honest zip.

Configuration lives in the repo's `.env`:

    PANDA_OWNER_ID    24-hex user id that will own the imported designs
    PANDA_BACKEND_DIR path to the panda-social-backend checkout
                      (default: ../panda-social-backend, sibling of this repo)
    GOOGLE_APPLICATION_CREDENTIALS  GCS service account json
                      (default: <backend>/secrets/gcs-sa.json)
    PANDA_APP_URL     optional; only used to print a clickable design link

Mongo/GCS coordinates are NOT duplicated here: the child process runs with the
backend checkout as its working directory and picks up that repo's own `.env`
through godotenv, so there is exactly one copy of those values.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import journal  # noqa: E402
import telegram  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
IDEAS = REPO_ROOT / "board-game" / "ideas"
QUEUE = REPO_ROOT / "board-game" / "QUEUE.json"
BIN = REPO_ROOT / "board-game" / "tools" / "bin" / "publishdesign"

# Junk that must never reach the CDN snapshot. The backend filters most of it
# again on its side (services.importIgnored); dropping it here too keeps the
# zip small and the entry count far under the importer's 4096 cap.
SKIP_DIRS = {"__pycache__", ".git", ".claude", ".idea", ".vscode"}
SKIP_SUFFIXES = (".pyc", ".pyo")
SKIP_NAMES = {".DS_Store"}

TAGS = "board-game,3d-print,cadquery"
# The two renders the review panel judges: the assembled hero, then the
# per-part QA sheet. Cover first — index 0 becomes the design's cover image.
COVER_ORDER = ("_assembled.png", "_qa.png")
MAX_THUMBS = 5  # services.importMaxThumbnails
MAX_DESC = 900  # the API allows 2000; a store blurb has no business being longer

# The FE's contract for a story block, mirrored from models/design_content.go
# (ContentBodyMinRunes / ContentBodyMaxRunes / ContentMaxStoryBlocks). A body
# outside the window does not render badly — the backend refuses to store it —
# so the packer below treats these as hard walls.
BLOCK_MIN, BLOCK_MAX, MAX_BLOCKS = 180, 400, 10
RULES_FILE = "RULES.md"
RULES_POINTER = f"The complete rules ship with the files as {RULES_FILE}."
# Spent on the page's last slot when the walkthrough had to stop early. A block
# body has a 180-rune floor, so this cannot be a one-line footnote.
RULES_CLOSING = (
    "The walkthrough above is the short version, and it stops before the last "
    "of the turn rules. The complete rules — every legality check, the full "
    f"component list, and how scoring resolves — ship with the files as "
    f"{RULES_FILE}, ready to read or print alongside the pieces.")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fail(msg: str) -> None:
    print(f"publish: {msg}", file=sys.stderr)
    raise SystemExit(1)


def backend_dir() -> Path:
    raw = os.environ.get("PANDA_BACKEND_DIR", "").strip()
    path = Path(raw).expanduser() if raw else REPO_ROOT.parent / "panda-social-backend"
    if not (path / "go.mod").is_file():
        fail(f"PANDA_BACKEND_DIR does not look like the backend checkout: {path}")
    return path.resolve()


def credentials(backend: Path) -> str:
    raw = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    path = Path(raw).expanduser() if raw else backend / "secrets" / "gcs-sa.json"
    if not path.is_file():
        fail(f"GCS credentials not found: {path}")
    return str(path.resolve())


def queue_state(slug: str) -> str:
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    item = data.get("ideas", {}).get(slug)
    if item is None:
        fail(f"{slug} is not in the queue")
    return item["state"]


def gate_passed(project: Path) -> tuple[bool, str]:
    gate = project / "gate.json"
    if not gate.is_file():
        return False, "no gate.json — the game was never measured"
    data = json.loads(gate.read_text(encoding="utf-8"))
    if not data.get("pass"):
        return False, f"gate.json says FAIL: {data.get('fails')}"
    return True, ""


def blurb(idea: dict) -> str:
    """A store description from the idea's own words: whole sentences off the
    concept, then the table facts a buyer scans for. Never a truncated
    mid-sentence stub — this is the text that sells the thing."""
    concept = " ".join((idea.get("concept") or "").split())
    out = ""
    for sentence in re.findall(r"[^.]+\.", concept) or [concept]:
        if len(out) + len(sentence) > MAX_DESC:
            break
        out += sentence
    out = (out or concept[:MAX_DESC]).strip()
    players = idea.get("players") or {}
    facts = []
    if players.get("min") and players.get("max"):
        facts.append(f"{players['min']}-{players['max']} players")
    if idea.get("playtime_min"):
        facts.append(f"{idea['playtime_min']} min")
    return f"{out}\n\n{' · '.join(facts)}" if facts else out


def rule_texts(idea: dict, key: str) -> list[str]:
    """The prose of one rules section. idea.json stores setup/turn/end as lists
    of {text, uses} and win as a single {text}, so both shapes end up here."""
    node = (idea.get("rules") or {}).get(key)
    if isinstance(node, dict):
        node = [node]
    return [" ".join(e["text"].split()) for e in (node or []) if e.get("text")]


def rules_markdown(idea: dict) -> str:
    """The rules sheet that ships INSIDE the design folder. This is the only
    surface with no length limit, so it is the one that carries the rules whole
    — the description and the story blocks are both windowed, and a game whose
    rules only half-arrived is not a game anyone can play."""
    players = idea.get("players") or {}
    facts = []
    if players.get("min") and players.get("max"):
        facts.append(f"{players['min']}-{players['max']} players")
    if idea.get("playtime_min"):
        facts.append(f"{idea['playtime_min']} minutes")
    out = [f"# {idea.get('title') or idea['slug']}", ""]
    if facts:
        out += [" · ".join(facts), ""]
    if idea.get("concept"):
        out += [" ".join(idea["concept"].split()), ""]

    components = idea.get("components") or []
    if components:
        out += ["## What is in the box", ""]
        for c in components:
            out.append(f"- **{c['name']}** ×{c.get('qty', 1)} — "
                       f"{' '.join((c.get('desc') or '').split())}")
        out.append("")
    for heading, key in (("Setup", "setup"), ("A turn", "turn"),
                         ("How the game ends", "end"), ("Winning", "win")):
        texts = rule_texts(idea, key)
        if not texts:
            continue
        out += [f"## {heading}", ""]
        out += [f"{i}. {t}" for i, t in enumerate(texts, 1)] if len(texts) > 1 else [texts[0]]
        out.append("")
    out += ["---", "",
            "Print the parts from the STL files in this folder (STEP included for "
            "editing). `bill.json` lists every part and quantity; `spec.md` carries "
            "the dimensions and the print notes."]
    return "\n".join(out) + "\n"


def split_prose(text: str, lo: int = BLOCK_MIN, hi: int = BLOCK_MAX) -> list[str]:
    """Cut prose into pieces that all land inside [lo, hi] runes, breaking on
    sentences. The piece count is chosen first and the target length derived
    from it, so the pieces come out even instead of leaving a runt at the end
    that the FE contract would reject."""
    sentences = [s.strip() for s in re.findall(r"[^.]+\.|[^.]+$", text) if s.strip()]
    pieces: list[str] = []
    for s in sentences:  # a single sentence longer than the window has to break
        while len(s) > hi:
            cut = s.rfind(" ", 0, hi)
            pieces.append(s[:cut].strip())
            s = s[cut:].strip()
        pieces.append(s)

    total = sum(len(p) + 1 for p in pieces)
    want = max(1, -(-total // hi))
    target = total / want
    chunks: list[str] = []
    cur = ""
    for p in pieces:
        if cur and (len(cur) + 1 + len(p) > hi or
                    (len(cur) >= target and len(chunks) < want - 1)):
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur} {p}".strip()
    if cur:
        chunks.append(cur)
    # Fold a tail that came out under the minimum back into its neighbour.
    while len(chunks) > 1 and len(chunks[-1]) < lo and \
            len(chunks[-2]) + 1 + len(chunks[-1]) <= hi:
        chunks[-2:] = [f"{chunks[-2]} {chunks[-1]}"]
    return [c for c in chunks if lo <= len(c) <= hi]


def story_blocks(idea: dict) -> tuple[list[dict], bool]:
    """The rules as the product page's story sections. Returns the blocks and
    whether anything had to be left out: 10 blocks × 400 runes cannot hold a
    full rulebook, so the walkthrough is deliberately partial — and when it is,
    the last slot is spent SAYING so rather than on one more paragraph that
    stops mid-game."""
    setup = split_prose(" ".join(rule_texts(idea, "setup")))
    turn = split_prose(" ".join(rule_texts(idea, "turn")))
    ending = split_prose(" ".join(rule_texts(idea, "end") + rule_texts(idea, "win")))

    # Setup and the ending are short and structural — losing the winning
    # condition would be the worst possible cut — so the long middle is what
    # gets squeezed, and the closing pointer takes a slot of its own.
    dropped = len(setup) + len(turn) + len(ending) > MAX_BLOCKS
    if dropped:
        setup = setup[:max(1, MAX_BLOCKS - 2 - len(ending))]
        turn = turn[:max(1, MAX_BLOCKS - 1 - len(setup) - len(ending))]

    blocks = []
    for lead, chunks in (("Setup", setup), ("A turn", turn), ("How it ends", ending)):
        for n, body in enumerate(chunks):
            blocks.append({"lead": lead if n == 0 else f"{lead} ({n + 1})",
                           "body": body})
    if dropped:
        blocks = blocks[:MAX_BLOCKS - 1] + [{"lead": "The full rules", "body": RULES_CLOSING}]
    return blocks[:MAX_BLOCKS], dropped


def print_specs(project: Path) -> dict:
    """The SPECS strip, from what the gate actually measured. Dimensions are the
    LARGEST single part's bounding box — for a 63-piece game that is the number
    a buyer needs (will it fit my bed), not the assembly's footprint. Weight and
    print time stay absent unless a slicer produced them; the FE hides the rows
    it has no value for, and a made-up figure is worse than a missing one."""
    gate = json.loads((project / "gate.json").read_text(encoding="utf-8"))
    specs: dict = {"materials": ["PLA"]}
    if gate.get("part_count"):
        specs["part_count"] = gate["part_count"]
    boxes = [p["bbox_mm"] for p in (gate.get("parts") or {}).values() if p.get("bbox_mm")]
    if boxes:
        x, y, z = max(boxes, key=lambda b: b[0] * b[1] * b[2])
        specs["dimensions_mm"] = {"x": x, "y": y, "z": z}
    # Deliberately no weight_g: the gate measures solid volume, which is the
    # mass at 100% infill and nothing anyone will actually print. A curated
    # spec row also OUTRANKS the slicer's measured one for good
    # (models.MergedPrintSpecs), so a guess here would permanently mask the
    # real number once a slice job produces it.
    return specs


def product_page(idea: dict, project: Path) -> tuple[dict, bool]:
    """use_case + story_blocks + print_specs, the shape publishdesign -content
    validates against the backend's own models.ValidateDesignContent."""
    blocks, dropped = story_blocks(idea)
    page: dict = {"print_specs": print_specs(project)}
    if blocks:
        page["story_blocks"] = blocks
    intro = split_prose(" ".join((idea.get("concept") or "").split()))
    if intro:
        # image is left empty on purpose: the CLI fills it with the design's own
        # cover, which does not exist until the import has uploaded it.
        page["use_case"] = {"label": "On the table", "body": intro[0], "image": ""}
    return page, dropped


def covers(project: Path, slug: str) -> list[Path]:
    """The hero and the QA sheet, in that order. Everything else in the review
    folder is a single part on a turntable — useful to a reviewer, noise in a
    product gallery — so the rest is a fallback for when neither named render
    exists, not extra images to pad the listing with."""
    review = project / f"{slug}_review"
    if not review.is_dir():
        return []
    named = [review / name for name in COVER_ORDER if (review / name).is_file()]
    if named:
        return named
    return sorted(review.glob("*.png"))[:MAX_THUMBS]


def build_zip(project: Path, slug: str, dest: Path, rules: str = "") -> tuple[int, int]:
    """Zip the project folder wrapped in one directory named after the slug —
    the layout findDesignFolder expects, and the folder name detectPrimarySTL
    ranks the assembled STL against. `rules` is written in as RULES.md: the
    files someone downloads have to include how the game is played.

    `build/` is dropped when the root already carries the same assembled STL:
    the builder writes both, so shipping it doubles the snapshot AND leaves two
    identically-named STLs for the importer to choose between — the tie decided
    where the viewer GLB got written. A project whose ONLY exports live in
    build/ keeps them."""
    skip_dirs = set(SKIP_DIRS)
    if (project / f"{slug}.stl").is_file() and (project / "build" / f"{slug}.stl").is_file():
        skip_dirs.add("build")
    files = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(project.rglob("*")):
            if any(part in skip_dirs for part in path.relative_to(project).parts):
                continue
            if path.is_dir() or path.name in SKIP_NAMES or path.suffix in SKIP_SUFFIXES:
                continue
            zf.write(path, f"{slug}/{path.relative_to(project).as_posix()}")
            files += 1
        if rules:
            zf.writestr(f"{slug}/{RULES_FILE}", rules)
            files += 1
    return files, dest.stat().st_size


def publish(slug: str, dry_run: bool, force: bool, mode: str = "import") -> int:
    """mode: `import` creates the design, `version` uploads the files again as
    a new version of it, `page` rewrites only the curated product page. The
    last two exist because the rules are content: they get edited after a game
    is already up, and re-importing would fork it into a second design."""
    idea_dir = IDEAS / slug
    project = idea_dir / "project"
    if not project.is_dir():
        fail(f"{slug} has no built project at {project}")
    published = idea_dir / "published.json"
    prior = json.loads(published.read_text(encoding="utf-8")) if published.is_file() else None
    if mode == "import" and prior and not dry_run:
        print(f"publish: {slug} already published — skip "
              f"(--page rewrites the rules, --new-version re-uploads the files)")
        return 0
    if mode != "import" and not prior:
        fail(f"{slug} has no published.json — publish it first")

    state = queue_state(slug)
    if state != "shipped" and not force:
        fail(f"{slug} is {state}, not shipped — the owner's gate 2 comes first "
             f"(--force to override)")
    ok, why = gate_passed(project)
    if not ok and not force:
        fail(f"{slug}: {why} (--force to override)")

    idea = json.loads((idea_dir / "idea.json").read_text(encoding="utf-8"))
    title = idea.get("title") or slug.replace("-", " ").title()
    description = f"{blurb(idea)}\n\n{RULES_POINTER}"
    prompt = " ".join((idea.get("concept") or description).split())
    thumbs = covers(project, slug)
    if not thumbs and mode == "import":
        fail(f"{slug} has no renders in {project.name}/{slug}_review — "
             f"a design with no cover cannot be imported")
    page, dropped = product_page(idea, project)

    backend = backend_dir()
    creds = credentials(backend)
    if not BIN.is_file():
        fail(f"{BIN} not built — run board-game/tools/publishdesign/build.sh")

    page_file = REPO_ROOT / "board-game" / f".publish-{slug}.content.json"
    page_file.write_text(json.dumps(page, indent=2), encoding="utf-8")
    cmd = [str(BIN), "-owner", os.environ["PANDA_OWNER_ID"], "-content", str(page_file)]
    archive = REPO_ROOT / "board-game" / f".publish-{slug}.zip"
    if mode != "page":
        count, size = build_zip(project, slug, archive, rules=rules_markdown(idea))
        cmd += ["-zip", str(archive), "-thumbs", ",".join(str(p) for p in thumbs)]
        print(f"publish: {slug} — {count} files, {size >> 20}MB zipped, "
              f"{len(thumbs)} covers")
    if mode == "import":
        cmd += ["-title", title, "-desc", description, "-prompt", prompt,
                "-tags", TAGS, "-status", "draft"]
    else:
        cmd += ["-design", prior["id"]]
    print(f"publish: {slug} — {len(page.get('story_blocks', []))} rules blocks"
          f"{', tail left to RULES.md' if dropped else ''}")
    if dry_run:
        cmd.append("-dry-run")
    # A deliberately minimal environment: the child reads Mongo/GCS/CDN
    # settings from the backend checkout's own .env (godotenv, cwd-relative),
    # so this repo's tokens have no business being in there.
    env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""),
           "GOOGLE_APPLICATION_CREDENTIALS": creds}
    try:
        run = subprocess.run(cmd, cwd=backend, env=env, capture_output=True,
                             text=True, timeout=3600)
    finally:
        archive.unlink(missing_ok=True)
        page_file.unlink(missing_ok=True)
    if run.returncode != 0:
        fail(f"{slug}: publishdesign failed\n{(run.stderr or run.stdout).strip()[-800:]}")
    tail = run.stdout.strip().splitlines()[-1] if run.stdout.strip() else "{}"

    if dry_run:
        print(run.stdout.strip())
        return 0

    info = json.loads(tail)
    info["published_at"] = now()
    info["owner_id"] = os.environ["PANDA_OWNER_ID"]
    if mode == "page":  # no new snapshot: keep the one the files are actually at
        info = {**prior, **info}
    published.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")

    link = ""
    app = os.environ.get("PANDA_APP_URL", "").strip().rstrip("/")
    if app:
        link = f"\n{app}/design/{info['slug']}"
    what = {"import": "imported to Panda Social as a draft",
            "version": "re-uploaded its files as a new version",
            "page": "rewrote its product page"}[mode]
    journal.append(slug, kind="publish", by="publish.py", title=title,
                   summary=f"{what} ({info['slug']}, "
                           f"{len(page.get('story_blocks', []))} rules blocks)",
                   body=json.dumps(info, indent=2))
    telegram.send(
        f"📦 {title} — {what}\n"
        f"id={info['id']}  slug={info['slug']}{link}\n"
        f"page: {', '.join(info.get('applied') or ['nothing'])}\n\n"
        f"It is private until you flip it to public in the app. "
        f"Check the viewer loads the model first — the snapshot is at\n{info['project_url']}")
    print(f"publish: {slug} → {mode} ok ({info['slug']}, {info['id']})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", nargs="?", help="idea slug; omit with --all")
    ap.add_argument("--all", action="store_true",
                    help="publish every shipped game that is not published yet")
    ap.add_argument("--dry-run", action="store_true",
                    help="check everything and print what would be imported")
    ap.add_argument("--force", action="store_true",
                    help="publish even if the queue state or gate says otherwise")
    ap.add_argument("--page", action="store_true",
                    help="already-published game: rewrite the rules/specs page only")
    ap.add_argument("--new-version", action="store_true",
                    help="already-published game: upload the files again as a new version")
    args = ap.parse_args()
    if args.page and args.new_version:
        ap.error("--page and --new-version are different jobs; run one, then the other")
    mode = "page" if args.page else "version" if args.new_version else "import"

    telegram.load_env()
    if not os.environ.get("PANDA_OWNER_ID", "").strip():
        fail("PANDA_OWNER_ID is not set in .env — nothing to own the design")

    if args.all:
        if mode != "import":
            ap.error("--all only does first publishes; name the slug to update one")
        data = json.loads(QUEUE.read_text(encoding="utf-8"))
        slugs = [s for s, i in data.get("ideas", {}).items()
                 if i["state"] == "shipped" and not (IDEAS / s / "published.json").is_file()]
        if not slugs:
            print("publish: nothing shipped and unpublished")
            return 0
        for slug in slugs:
            publish(slug, args.dry_run, args.force)
        return 0
    if not args.slug:
        ap.error("give a slug or --all")
    return publish(args.slug, args.dry_run, args.force, mode)


if __name__ == "__main__":
    sys.exit(main())
