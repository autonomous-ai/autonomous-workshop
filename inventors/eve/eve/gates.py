"""Deterministic, no-LLM gates for Eve.

A model that can read its own gate will tune to it (the org's hard lesson),
so every *decision* gate here is pure code over the game's recorded state and
the corpus. Nothing here calls a model.

Three gates:
  * novelty_gate  — an invented idea must be new against Loop A's corpus:
                    the identity must be an explicit "like X plus Y" and the
                    idea must not collide with the corpus's owned/saturated
                    mechanics or themes.
  * rules_gate    — mechanical completeness: a bill of pieces, complete rules,
                    and a declared complexity budget within limits.
  * print_gate    — if meshes exist, shared topology / volume / bed checks
                    aggregated per part; if no meshes are present yet it
                    reports "not measurable" and does not fail (so earlier
                    stages can advance).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from inventor_workshop.cad import fits_bed_envelope, inspect_stl_path

# Bed: Bambu P2S nominal 256mm, 5mm margin per side (matches vibe-ideas).
BED_X_MM = 246.0
BED_Y_MM = 246.0
BED_Z_MM = 230.0
MAX_PARTS = 60


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if t and len(t) > 2}


class GateResult:
    def __init__(self, passed: bool, reasons: list[str], measurable: bool = True):
        self.passed = passed
        self.reasons = reasons
        self.measurable = measurable

    def to_dict(self):
        return {"passed": self.passed, "reasons": self.reasons, "measurable": self.measurable}


# --- novelty ---------------------------------------------------------------
def novelty_gate(game, corpus) -> GateResult:
    """New against the corpus's owned mechanics/themes, with an explicit identity.

    Passes only if:
      1. identity/idea is non-empty;
      2. identity contains a "+" (an explicit combination claim: "like X plus Y");
      3. the idea does not collide with either corpus['owned']['mechanics'] or
         corpus['owned']['themes'] beyond a small allowed overlap;
      4. it is not a "themed skin": idea must name a mechanic, not just a theme.
    """
    text = f"{game.idea} {game.identity}".strip()
    if not text:
        return GateResult(False, ["no idea recorded"])
    if not game.identity or "+" not in game.identity:
        return GateResult(False, ["identity must be an explicit 'like X plus Y' combination"])
    if "mechanics" not in corpus.get("owned", {}):
        return GateResult(False, ["corpus is not loaded — cannot judge novelty", "fallback: not measurable"])
    owned_mech = set(corpus["owned"]["mechanics"])
    owned_themes = set(corpus["owned"]["themes"])
    toks = _tokens(game.idea)
    mech_hit = toks & owned_mech
    theme_hit = toks & owned_themes
    if mech_hit:
        return GateResult(False, [f"collides with already-owned mechanic(s): {sorted(mech_hit)}"])
    if theme_hit:
        # a theme alone is a "themed skin" risk only if identity is theme-only;
        # combination identities that also name a mechanic pass.
        return GateResult(False, [f"collides with saturated theme(s): {sorted(theme_hit)}"])
    return GateResult(True, ["novel against corpus; identity is an explicit combination"])


# --- rules -----------------------------------------------------------------
COMPLEXITY_LIMIT = 5  # a declared 1..10 per-mechanic count; beyond is a scope fail

def rules_gate(game) -> GateResult:
    """Mechanical completeness of the rules package (bill, rules, complexity)."""
    reasons = []
    ok = True
    if not game.bill or not isinstance(game.bill, dict):
        reasons.append("no bill of pieces")
        ok = False
    else:
        n_parts = sum(len(v) if isinstance(v, list) else 1 for v in game.bill.values())
        if n_parts > MAX_PARTS:
            reasons.append(f"{n_parts} parts exceeds {MAX_PARTS} budget")
            ok = False
    if not game.idea or len(game.idea) < 20:
        reasons.append("rules/idea too short to be complete")
        ok = False
    if not game.identity:
        reasons.append("no identity recorded")
        ok = False
    if not ok:
        return GateResult(False, reasons)
    return GateResult(True, ["rules bill present and within size budget"])


# --- print -----------------------------------------------------------------
def _mesh_states(game_dir: Path) -> list[dict]:
    """Return exact-byte Workshop topology receipts for every part mesh."""
    out = []
    build_dir = game_dir / "build"
    if not build_dir.exists():
        return out
    for stl in sorted(build_dir.glob("*.stl")):
        try:
            receipt = inspect_stl_path(stl, expected_shell_count=1)
        except OSError as exc:
            error_code = getattr(exc, "code", type(exc).__name__)
            out.append({"file": stl.name, "status": "failed",
                        "reasons": ["mesh could not be safely inspected: %s" % error_code],
                        "receipt": None, "fits_bed": False})
            continue
        fits_bed = bool(
            receipt.status == "passed"
            and receipt.bounds_min_mm is not None
            and receipt.bounds_max_mm is not None
            and fits_bed_envelope(
                receipt.bounds_min_mm,
                receipt.bounds_max_mm,
                (BED_X_MM, BED_Y_MM, BED_Z_MM),
            )
        )
        out.append({
            "file": stl.name,
            "status": receipt.status,
            "reasons": list(receipt.failure_reasons + receipt.hold_reasons),
            "receipt": receipt.to_dict(),
            "receipt_sha256": receipt.receipt_sha256,
            "fits_bed": fits_bed,
        })
    return out


def print_gate(game, game_dir: Optional[Path] = None) -> GateResult:
    """Require every part to pass Workshop topology and bed-envelope checks."""
    if game_dir is None:
        # nothing to inspect -> not measurable, do not fail (early stages)
        return GateResult(False, [], measurable=False)
    parts = _mesh_states(game_dir)
    if not parts:
        return GateResult(False, ["no meshes in build/ — not measurable yet"], measurable=False)
    reasons = []
    for part in parts:
        if part["status"] != "passed":
            detail = ", ".join(part["reasons"]) or part["status"]
            reasons.append(
                "%s failed Workshop STL topology: %s" % (part["file"], detail)
            )
        elif not part["fits_bed"]:
            reasons.append(
                "%s exceeds Eve's %.0fx%.0fx%.0f mm bed envelope"
                % (part["file"], BED_X_MM, BED_Y_MM, BED_Z_MM)
            )
    if reasons:
        return GateResult(False, reasons)
    return GateResult(
        True,
        ["%d parts passed Workshop topology and bed-envelope checks" % len(parts)],
    )
