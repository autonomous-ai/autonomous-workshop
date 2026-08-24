"""Iteration budgets — in code, never in prompts.

The vibe-ideas rule this module exists to enforce: "An agent that can read
its own budget in its own prompt is an agent that will negotiate with it."
Generators receive lens reports; they never see these constants, and a round
is spent when THIS file says so, not when a model reports frugality.

Three budgets, three stated rationales (docs/research/vibe-ideas-lessons.md
§1.2, ported with the receipts):

- CLARIFY: ambiguity-only fixes, off the rework budget but bounded, "because
  an unbounded free lane is how a design flaw gets laundered."
- REWORK: mechanic defects. "An idea still failing after three balancing
  passes is a shape problem, not a tuning one." Exhaustion on the next
  failure kills (queue.park_or_kill enforces it).
- REPAIR: CAD repair rounds. "Past two rounds the problem is usually the
  spec rather than the code" (text2cad evidence — 6 Armillary repair rounds
  were spent on rules that later failed the playtest).

The anti-laundering pair freeze_surface()/settle_clarify() uses
queue.mech_surface(): a clarify round freezes the mechanic hash; the settle
recomputes it and, if it moved, converts the round after the fact — refund
clarify, charge rework, log it. The disposition is the queue's to enforce,
not the fixer's to claim.
"""

import json
import os

from harness import queue

# Exhaustion => parked, never silent (CONTRACTS §1). Values are contract-
# pinned; changing them is a PR against CONTRACTS.md, not an edit here.
CLARIFY_BUDGET = 3
REWORK_BUDGET = 3
REPAIR_BUDGET = 2

_BUDGETS = {
    "clarify": ("clarify_used", CLARIFY_BUDGET),
    "rework": ("rework_used", REWORK_BUDGET),
    "repair": ("repair_used", REPAIR_BUDGET),
}

# The mechanic-bearing doc for a game. One canonical name so the frozen hash
# and the settle always read the same file.
GAME_DOC = "game.json"


def spend(game, kind):
    """Charge one round of `kind` against a queue game dict.

    Returns True and increments the counter when budget remains; returns
    False WITHOUT incrementing when exhausted — the caller parks (or lets
    queue.park_or_kill decide park vs kill). Mutates the dict in place; the
    caller saves it inside the transaction it read it in.
    """
    if kind not in _BUDGETS:
        raise ValueError(
            "unknown budget kind '%s' — one of: %s" % (kind,
                                                       ", ".join(_BUDGETS))
        )
    field, cap = _BUDGETS[kind]
    budgets = game.setdefault(
        "budgets", {"clarify_used": 0, "rework_used": 0, "repair_used": 0}
    )
    if budgets.get(field, 0) >= cap:
        return False
    budgets[field] = budgets.get(field, 0) + 1
    return True


def _game_doc_path(slug):
    return os.path.join(queue.bob_home(), "toys", slug, GAME_DOC)


def _read_game_doc(slug):
    path = _game_doc_path(slug)
    if not os.path.exists(path):
        raise FileNotFoundError(
            "no %s for '%s' at %s — the rules step writes it before any "
            "clarify round can be frozen or settled" % (GAME_DOC, slug, path)
        )
    with open(path, "r") as fh:
        return json.load(fh)


def freeze_surface(slug):
    """Snapshot the mechanic hash at the start of a clarify round.

    Stored in the queue entry (mech_frozen), not next to the doc: the fixer
    edits the game dir, so the reference must live where the fixer cannot
    reach. Returns the hash.
    """
    surface = queue.mech_surface(_read_game_doc(slug))
    with queue.transaction() as q:
        game = q["games"].get(slug)
        if game is None:
            raise KeyError("no game '%s' in the queue to freeze" % slug)
        game["mech_frozen"] = {
            "hash": surface,
            "at": queue._iso(queue._now()),
        }
    return surface


def settle_clarify(slug):
    """Re-hash after a clarify round and convert it to a rework if it lied.

    Returns {"changed": bool, "converted": bool, "budget_ok": bool}:
    - changed False: wording-only fix, the clarify charge stands.
    - changed True: mechanics moved under a clarify label — refund the
      clarify, charge a rework (converted=True), and log the conversion so
      the ledger shows what actually happened.
    - budget_ok False: the conversion needed a rework round that no longer
      exists; the caller routes to queue.park_or_kill (which will kill,
      since rework is exhausted).

    No frozen hash on file is a no-op success — there was no clarify round
    in flight to settle.
    """
    current = queue.mech_surface(_read_game_doc(slug))
    with queue.transaction() as q:
        game = q["games"].get(slug)
        if game is None:
            raise KeyError("no game '%s' in the queue to settle" % slug)
        frozen = game.pop("mech_frozen", None)
        if frozen is None:
            return {"changed": False, "converted": False, "budget_ok": True}
        if current == frozen.get("hash"):
            return {"changed": False, "converted": False, "budget_ok": True}
        # Mechanics moved under a clarify label. Refund the clarify round
        # (it was mis-labelled, not free) and charge the rework it really was.
        budgets = game.setdefault(
            "budgets", {"clarify_used": 0, "rework_used": 0, "repair_used": 0}
        )
        budgets["clarify_used"] = max(0, budgets.get("clarify_used", 0) - 1)
        budget_ok = spend(game, "rework")
        game["log"].append({
            "at": queue._iso(queue._now()),
            "from": game["state"],
            "to": game["state"],
            "note": (
                "clarify converted to rework: mech_surface moved "
                "%s -> %s%s" % (
                    frozen.get("hash", "?")[:12], current[:12],
                    "" if budget_ok else " (rework budget exhausted)",
                )
            ),
        })
        return {"changed": True, "converted": True, "budget_ok": budget_ok}
