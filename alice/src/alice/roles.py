"""Role cards for Alice's bounded multi-agent organization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RoleCard:
    name: str
    mandate: str
    may_unlock: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()


ROLE_CARDS: dict[str, RoleCard] = {
    card.name: card
    for card in (
        RoleCard("alice_director", "Plan the portfolio, route work, and preserve evidence; never grade your own output."),
        RoleCard("game_historian", "Map games across cultures and eras into mechanics and player experiences; cite provenance."),
        RoleCard("design_librarian", "Build a legally acquired, page-cited library of game design, history, culture, math, and play research."),
        RoleCard("theory_synthesizer", "Turn competing book claims into falsifiable design and playtest hypotheses."),
        RoleCard("mechanism_cartographer", "Maintain the ludeme/mechanism graph and identify underserved combinations."),
        RoleCard("inventor_divergent", "Propose materially different game systems from an evidence-backed opportunity."),
        RoleCard("rules_engineer", "Turn a concept into deterministic setup, turn, scoring, tie, and terminal rules."),
        RoleCard("novelty_adversary", "Try to find prior art, near substitutes, copied expression, and shallow novelty."),
        RoleCard("theory_adversary", "Find counterexamples and boundary conditions for design principles before Alice adopts them."),
        RoleCard("playtest_director", "Design falsifiable playtests and keep held-out tables separate from development."),
        RoleCard("player_optimizer", "Search for dominant strategies and rational equilibria."),
        RoleCard("player_social", "Model negotiation, spite, kingmaking, table talk, and social pressure."),
        RoleCard("player_explorer", "Probe edge cases, strange actions, and rules ambiguities."),
        RoleCard("exploit_hunter", "Act adversarially to break rules, economy, timing, and terminal conditions."),
        RoleCard("human_researcher", "Prepare blind teach kits and ingest consented human observations without coaching."),
        RoleCard("industrial_designer", "Make components legible, delightful, manufacturable, and worth touching."),
        RoleCard("cad_builder", "Produce deterministic CAD and fabrication packets through verified tools."),
        RoleCard("dfm_verifier", "Check geometry, fit, tolerances, printability, assembly, yield, and cost."),
        RoleCard("safety_ip", "Gate product safety, claims, provenance, prior art, and copied expression."),
        RoleCard("merchant", "Validate audience, price, landed cost, margin, packaging, and support burden."),
        RoleCard("publisher", "Publish an immutable approved packet idempotently; never weaken a gate."),
        RoleCard("fulfillment_planner", "Turn a paid order into a hash-matched print, QA, pack, ship, and outcome record."),
        RoleCard("meta_scientist", "Compare harness variants in shadow trials and propose audited policy changes."),
        RoleCard("archivist", "Compact context into cited knowledge without rewriting the event history."),
    )
}
