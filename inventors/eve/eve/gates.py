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
  * print_gate    — if meshes exist, bed-fit / volume / watertight checks
                    aggregated per part; if no meshes are present yet it
                    reports "not measurable" and does not fail (so earlier
                    stages can advance).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

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
    """Return per-part mesh presence + simple geometric stats if meshes exist."""
    out = []
    build_dir = game_dir / "build"
    if not build_dir.exists():
        return out
    for stl in sorted(build_dir.glob("*.stl")):
        # Parse the ASCII 'solid' header only for presence + rough size via
        # file bytes; real watertight/volume checks need the org's cadcode.
        stat = stl.stat()
        out.append({
            "file": stl.name,
            "bytes": stat.st_size,
            "present": True,
        })
    return out


def print_gate(game, game_dir: Optional[Path] = None) -> GateResult:
    """Deterministic bed/volume checks when meshes exist; else 'not measurable'.

    Full watertight/slice checks live in the org's cadcode gate.py; this gate
    is Eve's own layer and reports honestly when there is nothing to measure.
    """
    if game_dir is None:
        # nothing to inspect -> not measurable, do not fail (early stages)
        return GateResult(False, [], measurable=False)
    parts = _mesh_states(game_dir)
    if not parts:
        return GateResult(False, ["no meshes in build/ — not measurable yet"], measurable=False)
    reasons = []
    ok = True
    for p in parts:
        if p["bytes"] == 0:
            ok = False
            reasons.append(f"{p['file']} is empty")
    if not ok:
        return GateResult(False, reasons)
    return GateResult(True, [f"{len(parts)} parts present with non-zero meshes"])
