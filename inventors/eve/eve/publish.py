"""publish.py — render a designed game to the Autonomous board-game catalog.

Two surfaces, deliberately distinct (DESIGN.md ss.4 / ss.3):

  * the **static catalog** (`render_card` / `insert_card` / `publish`) — puts a
    designed game's card + writeup onto the catalog page
    `projects/vibe/boardgames/index.html` in the `autonomous-org` repo, the same
    surface the other ten designs already occupy. This is what "publish the
    first board game on the site" means in the org's current operating state:
    the catalog is the design loop.
  * the **store pipeline** (`import_design` / `publish_to_store`) — hands the
    finished folder to Foundation for a canonical artifact packet and a
    durable Panda import intent. The remote effect is never retried after an
    ambiguous response; an operator must reconcile the persisted intent.

Honesty note: publishing a *design* is not the reward-terminal `ship`. `ship`
only fires after the fun gate clears on real (llm_table/human) playtest
evidence. This module never grants reward; it only surfaces finished work.

This module is deterministic, no-LLM: it formats recorded state into HTML/MD
and, when the store is configured, calls the existing import endpoint over
HTTP. Everything degrades gracefully when credentials are unset.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from inventor_core.errors import AmbiguousPublishError, ContractError, PublishError

from . import core_adapter

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



def _clip_bytes(text: str, n: int = 2000) -> str:
    """Clip a string to at most n UTF-8 BYTES (never splitting a code point).

    The store API measures the description length in bytes
    (len(strings.TrimSpace(desc)) > maxDescriptionLen), so a rune-based clip
    can still exceed the limit once em-dashes / middle dots are present.
    """
    raw = str(text)
    if len(raw.encode("utf-8")) <= n:
        return raw
    out = raw.encode("utf-8")[:n].decode("utf-8", errors="ignore")
    # re-trim to a clean code-point boundary and one line
    return re.sub(r"\s+", " ", out).strip()



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
    # Queue.Game.updated is durable, so rendering the same shipped game twice
    # does not silently change the artifact packet and defeat outbox replay.
    ts = getattr(game, "updated", None) or datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )
    md.append(f"_rendered by Eve · {ts}_")
    return "\n".join(md)


def publish(game, *, cfg=None, catalog_path: Optional[Path] = None, num: Optional[int] = None,
            writeup: Optional[str] = None, journal=None) -> dict:
    """Orchestrate a catalog publish: write the writeup + insert the card.

    Returns a result dict. Does NOT grant ship reward (see module docstring).
    """
    from .journal import open_journal
    slug = core_adapter.validate_slug(game.slug)
    journal = journal or (open_journal(cfg) if cfg else None)
    base = (cfg.root / "games") if cfg else Path("games")
    game_dir = base / slug
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
    identity = (getattr(game, "identity", "") or "").strip()
    # avoid "a new combination — like like Quoridor …": identity often already
    # carries a leading "like …" comp, so drop a redundant one before the join.
    if identity[:5].lower() == "like ":
        identity = identity[5:].lstrip()
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
    # hard ban-word sweep (org brand voice)
    for w in BANNED:
        body = re.sub(re.escape(w), w.replace(" ", "-"), body, flags=re.I)
    # reserve bytes for the required attribution so " By Eve." always survives
    suffix = " By Eve."
    body = _clip_bytes(_one_line(body), n=2000 - len(suffix.encode("utf-8")))
    return body + suffix


def _write_json_atomic(path: Path, document: Mapping[str, Any]) -> None:
    """Write an operator projection without making it publication authority."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % path.name, suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", closefd=True) as stream:
            descriptor = -1
            stream.write(json.dumps(dict(document), indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _record_core_projection(game_dir: Path, intent: Mapping[str, Any]) -> None:
    """Keep a readable non-authoritative copy beside the game.

    The authoritative state remains ``state/inventor-core.sqlite3``. This copy
    is deliberately excluded from artifact packets and helps an operator find
    the intent that must be reconciled.
    """
    projection = {
        "schema_version": 1,
        "authority": "state/inventor-core.sqlite3",
        "product_id": intent.get("product_id"),
        "intent_id": intent.get("id"),
        "state": intent.get("state"),
        "packet_sha256": intent.get("packet_sha256"),
        "receipt": intent.get("receipt"),
        "error": intent.get("error"),
    }
    _write_json_atomic(
        game_dir / core_adapter.CORE_PUBLICATION_PROJECTION, projection
    )


def import_design(
    cfg, game, *, status: str = "draft", journal=None, transport=None
) -> dict:
    """POST the finished game folder to the store's /designs/import endpoint.

    Returns a result dict with the platform response (project_url etc.). Taps
    the org's existing pipeline so the auto product page is generated for us.
    Successful historical imports still skip via ``published.json``. New
    imports are fenced by Foundation's durable intent database and bind the exact
    canonical packet, artifact tree, owner, and draft receipt. Skips (never
    fails) when credentials are unset so the creative pipeline runs offline.
    """
    from .journal import open_journal
    journal = journal or open_journal(cfg)
    if status != "draft":
        return {"ok": False, "error": "Eve publication is draft-only"}
    if (
        not cfg.store_configured
        or not cfg.store_bearer
        or not cfg.panda_owner_id
    ):
        journal.append("publish_skipped", game=game.slug,
                       reason="store not configured (set EVE_STORE_BEARER and PANDA_OWNER_ID)")
        return {
            "skipped": True,
            "reason": "store not configured (bearer and owner are required)",
        }

    try:
        slug = core_adapter.validate_slug(game.slug)
    except ContractError as exc:
        journal.append("publish_refused", game=str(game.slug), reason=str(exc))
        return {
            "ok": False,
            "blocked": False,
            "intent_id": None,
            "state": None,
            "error": str(exc),
        }

    game_dir = cfg.games_dir / slug
    pub_file = game_dir / "published.json"
    if pub_file.exists():
        journal.append("publish_skipped", game=game.slug, reason="already published")
        return {"skipped": True, "already_published": json.loads(pub_file.read_text())}

    # Render the source writeup before core freezes the artifact bytes.
    readme = game_dir / "README.md"
    if not readme.exists():
        (game_dir / "README.md").write_text(full_writeup(game))
    metadata = {
        "title": _one_line(game.title or game.slug)[:120],
        "description": store_description(game),
        "status": "draft",
        "license": "CC-BY-NC",
        "category": "toys",
        "tags": ["eve", "board-game", "3d-print"],
    }
    prompt = _one_line(getattr(game, "identity", "") or "")
    if prompt:
        metadata["prompt"] = prompt
    try:
        result = core_adapter.import_panda_draft(
            cfg, game, metadata, transport=transport
        )
    except AmbiguousPublishError as exc:
        intent = core_adapter.publication_state(cfg, game.slug) or {}
        if intent:
            _record_core_projection(game_dir, intent)
        journal.append(
            "publish_blocked",
            game=game.slug,
            intent_id=intent.get("id"),
            state=intent.get("state"),
            packet_sha256=intent.get("packet_sha256"),
            reason=str(exc),
        )
        return {
            "ok": False,
            "blocked": True,
            "intent_id": intent.get("id"),
            "state": intent.get("state"),
            "error": str(exc),
        }
    except PublishError as exc:
        intent = core_adapter.publication_state(cfg, game.slug) or {}
        if intent:
            _record_core_projection(game_dir, intent)
        journal.append(
            "publish_failed",
            game=game.slug,
            intent_id=intent.get("id"),
            state=intent.get("state"),
            reason=str(exc),
        )
        return {
            "ok": False,
            "blocked": False,
            "intent_id": intent.get("id"),
            "state": intent.get("state"),
            "error": str(exc),
        }
    except ContractError as exc:
        # Packet, metadata, owner, or selected-artifact contract failures are
        # proven local failures: no Panda effect was attempted. Report them as
        # a graceful refusal while keeping published.json absent.
        intent = core_adapter.publication_state(cfg, game.slug) or {}
        if intent:
            _record_core_projection(game_dir, intent)
        journal.append(
            "publish_refused",
            game=game.slug,
            intent_id=intent.get("id"),
            state=intent.get("state"),
            reason=str(exc),
        )
        return {
            "ok": False,
            "blocked": False,
            "intent_id": intent.get("id"),
            "state": intent.get("state"),
            "error": str(exc),
        }

    receipt = result["receipt"]
    persisted = {
        "schema_version": 1,
        "product_id": result["product_id"],
        "intent_id": result["intent_id"],
        "intent_state": result["intent_state"],
        "receipt": receipt,
        # Preserve the useful top-level shape of Eve's historical
        # published.json files for operator scripts while keeping the exact
        # typed core receipt intact above.
        "id": receipt["design_id"],
        "slug": receipt["slug"],
        "owner_id": receipt["owner_id"],
        "root_id": receipt["root_id"],
        "current_history_id": receipt["current_history_id"],
        "published_history_id": receipt["published_history_id"],
        "status": receipt["status"],
        "project_url": receipt["project_url"],
    }
    _write_json_atomic(pub_file, persisted)
    intent = core_adapter.publication_state(cfg, game.slug)
    if intent:
        _record_core_projection(game_dir, intent)
    # Eve's append-only journal retains the exact core receipt as well as the
    # per-game projection. It is an audit copy, not a second outbox authority.
    journal.append(
        "published_store",
        game=game.slug,
        intent_id=result["intent_id"],
        receipt=receipt,
        packet=result["packet"],
        status="draft",
        producer="inventor_core",
    )
    _telegram(cfg, f"🎲 Eve published a new board game: {game.title or game.slug}\n"
                   f"id={receipt.get('design_id')} slug={receipt.get('slug')}\n"
                   f"{receipt.get('project_url', '')}")
    compatibility_info = {
        "id": receipt["design_id"],
        "slug": receipt["slug"],
        "owner_id": receipt["owner_id"],
        "root_id": receipt["root_id"],
        "current_history_id": receipt["current_history_id"],
        "published_history_id": receipt["published_history_id"],
        "status": receipt["status"],
        "project_url": receipt["project_url"],
    }
    return {
        "ok": True,
        "product_id": result["product_id"],
        "intent_id": result["intent_id"],
        "receipt": receipt,
        # Compatibility for callers that previously inspected ``info``.
        "info": compatibility_info,
        "packet": result["packet"],
    }


def publish_to_store(cfg, game, *, status: str = "draft", journal=None) -> dict:
    """Full store publish for one game: catalog writeup + import. Public entry
    point (claimable by a graduation marker)."""
    try:
        core_adapter.validate_slug(game.slug)
    except ContractError as exc:
        from .journal import open_journal
        active_journal = journal or open_journal(cfg)
        active_journal.append("publish_refused", game=str(game.slug), reason=str(exc))
        return {"ok": False, "blocked": False, "error": str(exc)}
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
