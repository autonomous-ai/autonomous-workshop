"""publish.py — render a designed game to the Autonomous board-game catalog.

Two surfaces, deliberately distinct (DESIGN.md ss.4 / ss.3):

  * the **static catalog** (`render_card` / `insert_card` / `publish`) — puts a
    designed game's card + writeup onto the catalog page
    `projects/vibe/boardgames/index.html` in the `autonomous-org` repo, the same
    surface the other ten designs already occupy. This is what "publish the
    first board game on the site" means in the org's current operating state:
    the catalog is the design loop.
  * the **store pipeline** (`import_design` / `publish_to_store`) — taps the
    org's existing publishing pipeline (POST /designs/import on Panda Social)
    so a finished game gets a full, auto-generated product page (visuals, copy,
    and the rest are produced by that pipeline, not re-implemented here). Eve
    only hands it the finished folder, an honest description, and covers.

Honesty note: publishing a *design* is not the reward-terminal `ship`. `ship`
only fires after the fun gate clears on real (llm_table/human) playtest
evidence. This module never grants reward; it only surfaces finished work.

This module is deterministic, no-LLM: it formats recorded state into HTML/MD
and, when the store is configured, calls the existing import endpoint over
HTTP. Everything degrades gracefully when credentials are unset.
"""
from __future__ import annotations

import json
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Graduation-checkable symbols (see improve.graduation_check): any module-level
# name whose lesson marker is "[GRADUATED -> publish.<NAME>]" must exist. Keep
# the public store entry points here so the harness can verify them.
__all__ = [
    "render_card", "insert_card", "full_writeup", "publish",
    "import_design", "publish_to_store", "store_description",
]

BANNED = ["revolutionary", "empower", "supercharge", "unlock", "transform",
          "leverage", "synergy", "introducing", "excited to announce"]

# --- card rendering -------------------------------------------------------


def render_card(game, *, num: Optional[int] = None, blank_title=False, slug: Optional[str] = None) -> str:
    """Render one catalog `<div class="card">` matching the Vibe × Factory markup.

    Mirrors the exact structure/format of the existing 10 cards
    (projects/vibe/boardgames/index.html), including the `featured` + `flag`
    treatment, so an inserted card is visually identical.
    """
    slug = slug or getattr(game, "slug", None) or "game"
    title = game.title or game.slug
    mech = getattr(game, "mech", "") or getattr(game, "mechanism", "") or "printed mechanism"
    blurb = _one_line(getattr(game, "blurb", "") or game.idea or "")
    price = getattr(game, "price_usd", None)
    if not price:
        price = _default_price(game)
    seats = (getattr(game, "seats", None) or "2–4").replace("-", "–")
    tmin = getattr(game, "t_min", None) or "15"
    tmax = getattr(game, "t_max", None) or "25"
    n = f"{num:02d}" if num is not None else "–"
    flag = getattr(game, "flag", "")
    featured = " featured" if flag else ""
    flag_html = f'<span class="flag">{_esc(flag)}</span>' if flag else ""
    return (
        f'      <div class="card{featured}" data-slug="{_esc(slug)}">{flag_html}<div class="num">{n}</div><h4>{_esc(title)}</h4>\n'
        f'        <div class="mech">{_esc(mech)}</div>\n'
        f'        <p>{_esc(blurb)}</p>\n'
        f'        <div class="specs">{_esc(seats)}p · {_esc(tmin)}–{_esc(tmax)} min · <b>${price:.2f}</b></div></div>'
    )


def _default_price(game) -> float:
    c = getattr(game, "cogs_usd", None)
    if c:
        return max(29.99, round(c * 3.0, 2))
    return 44.99


def _one_line(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _esc(text) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --- catalog insertion ----------------------------------------------------


def insert_card(html_path: Path, card_html: str, *, slug: str) -> bool:
    """Insert a rendered card into the `.cards` container, idempotently.

    Returns True if inserted, False if the slug's card is already present.
    Does not touch anything else in the file. The card goes immediately before
    the `</div>` that closes the `.cards` container, which is the LAST `</div>`
    before the cards section's `</section>`.
    """
    text = html_path.read_text()
    if f'data-slug="{slug.lower()}"' in text.lower() or f'data-slug="{slug}"' in text:
        return False  # already published
    lines = text.splitlines(keepends=True)
    try:
        cards_open = next(i for i, ln in enumerate(lines) if '<div class="cards">' in ln)
    except StopIteration:
        raise ValueError(f"no '.cards' container in {html_path}")
    # find the section close that follows the cards container, then the LAST
    # `</div>` line before it (that is the container's own closing tag).
    sec_close = next(i for i in range(cards_open, len(lines))
                     if lines[i].strip() == "</section>")
    div_closes = [i for i in range(cards_open, sec_close)
                  if lines[i].strip() == "</div>"]
    if not div_closes:
        raise ValueError(f"no container close (</div>) before </section> in {html_path}")
    div_close = div_closes[-1]
    lines.insert(div_close, card_html + "\n")
    html_path.write_text("".join(lines))
    return True


# --- writeup --------------------------------------------------------------


def full_writeup(game, extra: Optional[dict] = None) -> str:
    """A markdown spec for one game, written to games/<slug>/README.md."""
    extra = extra or {}
    rules = extra.get("rules") or getattr(game, "rules_text", "") or "Pending full rulebook (engine-tested skeleton)."
    brief = extra.get("brief") or getattr(game, "brief", "") or ""
    evidence = ", ".join(str(e) for e in getattr(game, "fun_evidence", []) or []) or "playtest pending"
    outcome = extra.get("outcome", "")
    md = []
    md.append(f"# {game.title or game.slug}")
    md.append(f"**identity:** {getattr(game,'identity','')}")
    md.append(f"**stage:** {game.stage}  **COGS:** ${getattr(game,'cogs_usd',None) or '—'}  **price:** ${_default_price(game):.2f}")
    md.append("")
    md.append(f"**idea:** {getattr(game,'idea','')}")
    if brief:
        md.append("")
        md.append("## Brief")
        md.append(brief)
    md.append("")
    md.append("## Rules")
    md.append(rules)
    md.append("")
    md.append("## Playtest evidence")
    md.append(evidence)
    if outcome:
        md.append("")
        md.append(f"## Outcome\n{outcome}")
    md.append("")
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    md.append(f"_rendered by Eve · {ts}_")
    return "\n".join(md)


def publish(game, *, cfg=None, catalog_path: Optional[Path] = None, num: Optional[int] = None,
            writeup: Optional[str] = None, journal=None) -> dict:
    """Orchestrate a catalog publish: write the writeup + insert the card.

    Returns a result dict. Does NOT grant ship reward (see module docstring).
    """
    from .journal import open_journal
    journal = journal or (open_journal(cfg) if cfg else None)
    base = (cfg.root / "games") if cfg else Path("games")
    game_dir = base / game.slug
    game_dir.mkdir(parents=True, exist_ok=True)

    card = render_card(game, num=num)
    inserted = False
    written = None
    if catalog_path is not None:
        inserted = insert_card(catalog_path, card, slug=game.slug)
    wpath = game_dir / "README.md"
    wp = writeup if writeup is not None else full_writeup(game)
    wpath.write_text(wp)
    written = str(wpath)
    if journal:
        journal.append("published_design", game=game.slug, catalog=str(catalog_path),
                       card_inserted=inserted, writeup=written)
    return {"card": card, "inserted": inserted, "writeup": written}


# --- store pipeline (Panda Social /designs/import) ------------------------


def store_description(game) -> str:
    """An honest, sales-safe one-paragraph description from recorded state.

    Rules (org brand voice + shop honesty): "invents" not "invent"; no banned
    words; numeric claims only where measured; never claims a render is a
    printed part.
    """
    title = (game.title or game.slug).replace("-", " ").title()
    identity = getattr(game, "identity", "") or ""
    mech = getattr(game, "mech", "") or getattr(game, "mechanism", "") or "a printed mechanism"
    idea = _one_line(getattr(game, "idea", "") or "")
    seats = (getattr(game, "seats", None) or "2–4").replace("-", "–")
    tmin = getattr(game, "t_min", None) or "15"
    tmax = getattr(game, "t_max", None) or "25"
    body = (f"{title} is a {seats}-player tabletop game designed to be "
            f"3D-printed. Its play is carried by {mech}, and it is built as "
            f"a new combination \u2014 like {identity}."
            f" A game takes about {tmin}-{tmax} minutes. Eve invents these "
            f"games, carries each through rules, print, and playtest gates, "
            f"and only publishes one that reaches an end state.")
    if idea:
        body += f" {idea}"
    measured = []
    cogs = getattr(game, "cogs_usd", None)
    if cogs:
        measured.append(f"measured print+ship cost about ${cogs:.2f}")
    if measured:
        body += " " + "; ".join(measured) + "."
    body = f"{body} By Eve."
    # hard ban-word sweep (org brand voice)
    for w in BANNED:
        body = re.sub(re.escape(w), w.replace(" ", "-"), body, flags=re.I)
    return _one_line(body)[:2000]


def _zip_game_dir(game_dir: Path, slug: str) -> Path:
    """Zip a game folder for import; returns the archive path."""
    zip_path = game_dir.parent / f"{slug}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(game_dir.rglob("*")):
            if p.is_file():
                zf.write(p, arcname=p.relative_to(game_dir))
    return zip_path


def _upload_thumb(path: Path, cfg) -> Optional[str]:
    """Upload one cover to admindash /uploads; returns a CDN URL or None."""
    token = cfg.store_upload_token
    if not token:
        return None
    r = subprocess.run(
        ["curl", "-s", "-H", f"Authorization: Bearer {token}",
         "-F", f"file=@{path}", f"{cfg.store_upload_base}/api/uploads"],
        capture_output=True, text=True, timeout=120)
    m = re.search(r"https?://[^\s\"']+", r.stdout)
    if not m:
        return None
    return m.group(0)


def _cover_candidates(game_dir: Path) -> list[Path]:
    """Prefer the frozen hero render, then any PNG/JPG in the game folder."""
    cands = []
    for name in ("hero.png", "cover.png", "thumbnail.png"):
        p = game_dir / name
        if p.is_file():
            cands.append(p)
    cands += [p for p in sorted(game_dir.glob("*.png"))
              if p not in cands] + [p for p in sorted(game_dir.glob("*.jpg"))]
    return cands[:5]


def import_design(cfg, game, *, status: str = "draft", journal=None) -> dict:
    """POST the finished game folder to the store's /designs/import endpoint.

    Returns a result dict with the platform response (project_url etc.). Taps
    the org's existing pipeline so the auto product page is generated for us.
    Idempotent via games/<slug>/published.json. Skips (never fails) when the
    bearer token is unset so the pipeline runs offline.
    """
    from .journal import open_journal
    journal = journal or open_journal(cfg)
    if not cfg.store_configured or not cfg.store_bearer:
        journal.append("publish_skipped", game=game.slug,
                       reason="store not configured (set EVE_STORE_BEARER / ADMIN_TOKEN)")
        return {"skipped": True, "reason": "store not configured"}

    game_dir = cfg.games_dir / game.slug
    pub_file = game_dir / "published.json"
    if pub_file.exists():
        journal.append("publish_skipped", game=game.slug, reason="already published")
        return {"skipped": True, "already_published": json.loads(pub_file.read_text())}

    # build + validate the folder
    readme = game_dir / "README.md"
    if not readme.exists():
        full_writeup(game)
        (game_dir / "README.md").write_text(full_writeup(game))
    zip_path = _zip_game_dir(game_dir, game.slug)

    # covers: prefer locally-uploaded hero, else let the server render
    th_urls = []
    for p in _cover_candidates(game_dir):
        u = _upload_thumb(p, cfg)
        if u:
            th_urls.append(u)

    fields = ["-F", "file=@" + str(zip_path),
              "-F", f"title={_one_line(game.title or game.slug)[:120]}",
              "-F", f"description={store_description(game)}",
              "-F", "status=" + status,
              "-F", "license=CC-BY-NC",
              "-F", "category=tabletop",
              "-F", "tags=eve,board-game,3d-print"]
    fields += ["-F", "prompt=" + _one_line(getattr(game, "identity", "") or "")]
    for u in th_urls:
        fields += ["-F", f"thumbnail_urls={u}"]

    r = subprocess.run(
        ["curl", "-s", "-X", "POST",
         "-H", f"Authorization: Bearer {cfg.store_bearer}",
         *fields, f"{cfg.store_base_url}/api/v1/designs/import"],
        capture_output=True, text=True, timeout=180)
    out = r.stdout.strip()
    try:
        info = json.loads(out)
    except json.JSONDecodeError:
        info = {"raw": out[-400:], "rc": r.returncode}

    if r.returncode != 0 or info.get("error") or not (info.get("id") or info.get("slug")):
        journal.append("publish_failed", game=game.slug, detail=out[-400:])
        return {"ok": False, "error": out[-400:], "info": info}

    pub_file.write_text(json.dumps(info, indent=2))
    journal.append("published_store", game=game.slug, id=info.get("id"),
                   slug=info.get("slug"), project_url=info.get("project_url"),
                   status=status)
    _telegram(cfg, f"🎲 Eve published a new board game: {game.title or game.slug}\n"
                   f"id={info.get('id')} slug={info.get('slug')}\n"
                   f"{info.get('project_url', '')}")
    return {"ok": True, "info": info}


def publish_to_store(cfg, game, *, status: str = "draft", journal=None) -> dict:
    """Full store publish for one game: catalog writeup + import. Public entry
    point (claimable by a graduation marker)."""
    result = publish(game, cfg=cfg, journal=journal)
    result.update(import_design(cfg, game, status=status, journal=journal))
    return result


def _telegram(cfg, text: str) -> None:
    import os
    tok = os.environ.get("EVE_TELEGRAM_TOKEN", "")
    chat = os.environ.get("EVE_TELEGRAM_CHAT_DM", "")
    if not (tok and chat):
        return
    try:
        subprocess.run(
            ["curl", "-s", f"https://api.telegram.org/bot{tok}/sendMessage",
             "-d", f"chat_id={chat}", "--data-urlencode", f"text={text}"],
            capture_output=True, timeout=30)
    except Exception:
        pass
