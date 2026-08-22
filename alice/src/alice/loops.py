"""Alice's interacting loops and their bounded multi-agent work graphs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .domain import CandidateState, WorkItem


@dataclass(frozen=True, slots=True)
class LoopSpec:
    name: str
    purpose: str
    cadence_seconds: int
    budget_weight: int
    work: tuple[WorkItem, ...]


LOOPS: dict[str, LoopSpec] = {
    "library": LoopSpec(
        name="library",
        purpose="Study the best legally acquired game books and convert their claims into tested design knowledge.",
        cadence_seconds=86_400,
        budget_weight=1,
        work=(
            WorkItem("library", "library.discover", "design_librarian", "Maintain a provenance-rich reading queue across history, culture, mechanics, math, psychology, and design practice."),
            WorkItem("library", "library.read", "design_librarian", "Read the next legally available source and capture page-cited claims, examples, definitions, and open questions.", depends_on=("library.discover",)),
            WorkItem("library", "library.synthesize", "theory_synthesizer", "Compare the source with prior books; map agreements, contradictions, and scope conditions.", depends_on=("library.read",)),
            WorkItem("library", "library.adversary", "theory_adversary", "Find counterexamples and ways the new principle could mislead Alice.", depends_on=("library.synthesize",)),
            WorkItem("library", "library.experiment", "playtest_director", "Convert one surviving claim into a preregistered candidate or harness experiment.", depends_on=("library.adversary",)),
        ),
    ),
    "history": LoopSpec(
        name="history",
        purpose="Continuously expand the cited game/mechanism corpus across eras and cultures.",
        cadence_seconds=86_400,
        budget_weight=1,
        work=(
            WorkItem("history", "history.scan_traditional", "game_historian", "Find and cite traditional games or ludemes underrepresented in the corpus."),
            WorkItem("history", "history.scan_modern", "game_historian", "Map modern commercial games at metadata/mechanism level without copying protected expression."),
            WorkItem("history", "history.update_graph", "mechanism_cartographer", "Update the mechanism graph and identify evidence gaps.", depends_on=("history.scan_traditional", "history.scan_modern")),
            WorkItem("history", "history.compact", "archivist", "Compact only sourced durable facts; preserve provenance and disagreements.", depends_on=("history.update_graph",)),
        ),
    ),
    "invention": LoopSpec(
        name="invention",
        purpose="Generate a small, diverse portfolio of falsifiable original game systems.",
        cadence_seconds=86_400,
        budget_weight=3,
        work=(
            WorkItem("invention", "opportunity.frame", "alice_director", "Select one underserved player experience and explicit design constraints."),
            WorkItem("invention", "concept.propose_a", "inventor_divergent", "Propose a mechanism-first game for the opportunity; avoid theme-only novelty.", depends_on=("opportunity.frame",)),
            WorkItem("invention", "concept.propose_b", "inventor_divergent", "Independently propose a structurally different mechanism for the same opportunity.", depends_on=("opportunity.frame",)),
            WorkItem("invention", "concept.propose_c", "inventor_divergent", "Independently propose a third mechanism with a different interaction model.", depends_on=("opportunity.frame",)),
            WorkItem("invention", "concept.prior_art", "novelty_adversary", "Search for the closest substitutes and try to invalidate novelty.", depends_on=("concept.propose_a", "concept.propose_b", "concept.propose_c")),
            WorkItem("invention", "concept.select", "alice_director", "Select at most one proposal on evidence, structural novelty, falsifiability, and 3D-printable physical advantage; return a complete candidate object.", depends_on=("concept.propose_a", "concept.propose_b", "concept.propose_c", "concept.prior_art")),
        ),
    ),
    "meta": LoopSpec(
        name="meta",
        purpose="Improve Alice's harness without allowing Alice to move her own goalposts.",
        cadence_seconds=604_800,
        budget_weight=1,
        work=(
            WorkItem("meta", "harness.research", "meta_scientist", "Study new long-running-agent, multi-agent, evaluation, and game-design methods."),
            WorkItem("meta", "harness.propose", "meta_scientist", "Propose one measurable harness variant and a held-out shadow evaluation.", depends_on=("harness.research",)),
            WorkItem("meta", "harness.adversary", "novelty_adversary", "Try to show the proposed harness change rewards appearance rather than outcomes.", depends_on=("harness.propose",)),
        ),
    ),
    "learning": LoopSpec(
        name="learning",
        purpose="Calibrate surrogate graders and update improvement policies from held-out outcomes.",
        cadence_seconds=86_400,
        budget_weight=1,
        work=(
            WorkItem("learning", "outcomes.ingest", "archivist", "Reconcile immutable human, manufacturing, market, and support outcomes."),
            WorkItem("learning", "policy.shadow", "meta_scientist", "Update the learning policy in shadow mode and report calibration drift.", depends_on=("outcomes.ingest",)),
        ),
    ),
    "orders": LoopSpec(
        name="orders",
        purpose="Turn paid orders into verified print-on-demand shipments and learn from production outcomes.",
        cadence_seconds=300,
        budget_weight=2,
        work=(
            WorkItem("orders", "orders.poll_paid", "fulfillment_planner", "Fetch new paid orders and bind each SKU to its exact published packet hash."),
        ),
    ),
}


STATE_WORK: dict[str, tuple[WorkItem, ...]] = {
    CandidateState.PROPOSED: (
        WorkItem("candidate", "candidate.prior_art", "novelty_adversary", "Find the closest game, patent, product, and mechanic precedents."),
        WorkItem("candidate", "candidate.rules", "rules_engineer", "Formalize complete deterministic rules with setup, legal actions, end, scoring, and ties."),
        WorkItem("candidate", "candidate.safety_ip", "safety_ip", "Flag safety, copied expression, cultural provenance, claims, and IP risks."),
    ),
    CandidateState.RESEARCHED: (
        WorkItem("candidate", "rules.lint", "rules_engineer", "Resolve every ambiguity and prove the game reaches a terminal state."),
        WorkItem("candidate", "rules.adversary", "exploit_hunter", "Try illegal timing, resource, information, and terminal-state attacks."),
    ),
    CandidateState.RULES_VALID: (
        WorkItem("playtest", "simulation.optimizer", "player_optimizer", "Run seeded optimizing policies and find dominant strategies."),
        WorkItem("playtest", "simulation.social", "player_social", "Run social and negotiation personas; detect kingmaking and spite loops."),
        WorkItem("playtest", "simulation.explorer", "player_explorer", "Search edge cases and low-probability state transitions."),
        WorkItem("playtest", "simulation.exploit", "exploit_hunter", "Red-team the complete digital play trace and economy."),
    ),
    CandidateState.DIGITALLY_PLAYTESTED: (
        WorkItem("human", "human.prepare_blind_kit", "human_researcher", "Prepare a zero-coaching blind teach kit and preregister success/failure measures."),
    ),
    CandidateState.HUMAN_READY: (
        WorkItem("human", "human.collect_blind_results", "human_researcher", "Ingest independently run blind-table receipts with consent/provenance, unique trial ids, no designer coaching, and replay-choice outcomes."),
    ),
    CandidateState.HUMAN_VALIDATED: (
        WorkItem("physical", "physical.design", "industrial_designer", "Design the minimum physical form that makes the game clearer and more delightful."),
        WorkItem("physical", "physical.cad", "cad_builder", "Generate versioned CAD and fabrication files through the configured verified adapter.", depends_on=("physical.design",)),
        WorkItem("physical", "physical.dfm", "dfm_verifier", "Verify layout, fit, tolerances, mesh, assembly, cycle time, yield, and landed cost.", depends_on=("physical.cad",)),
        WorkItem(
            "physical",
            "physical.create_rich_draft",
            "publisher",
            "Invoke the existing Vibe Ideas publish.py operator for this exact production workspace and keep the result private; bind its rich page, design, history, project URL, and project hash for physical review.",
            depends_on=("physical.cad", "physical.dfm"),
        ),
    ),
    CandidateState.PHYSICAL_READY: (
        WorkItem("physical", "physical.prototype_print", "dfm_verifier", "Print the exact accepted artifacts, record machine/material/profile, and inspect every component."),
        WorkItem("physical", "physical.production_run", "fulfillment_planner", "Run a small hash-matched production sample and measure yield, time, material, packing, and defects.", depends_on=("physical.prototype_print",)),
    ),
    CandidateState.PRODUCTION_VALIDATED: (
        WorkItem("market", "market.offer", "merchant", "Validate the audience, honest promise, price, COGS, margin, packaging, and support load."),
        WorkItem("market", "market.validate_offer", "merchant", "Measure the exact offer, landed margin, and buyer evidence against the production packet.", depends_on=("market.offer",)),
        WorkItem("market", "market.final_safety_ip", "safety_ip", "Run final safety, provenance, IP, and claims gate on the exact production packet."),
        WorkItem("market", "release.evaluate", "alice_director", "Apply the pinned deterministic release policy to immutable human, manufacturing, market, and safety evidence.", depends_on=("market.validate_offer", "market.final_safety_ip")),
    ),
    CandidateState.PUBLISH_READY: (
        WorkItem("publish", "publish.packet", "publisher", "Assemble and hash the exact rules, assets, CAD, BOM, evidence, price, and disclosures."),
        WorkItem("publish", "publish.invoke_pipeline", "publisher", "Submit the verified product packet to the existing Vibe/Factory publishing pipeline and persist its durable run id.", depends_on=("publish.packet",)),
    ),
    CandidateState.PAGE_READY: (
        WorkItem("publish", "publish.verify_page", "publisher", "Verify the pipeline receipt, finished product URL, visuals, 3D viewer, copy, video where produced, specs, price, buy/remix actions, and packet identity."),
    ),
    CandidateState.REWORK: (
        WorkItem("learning", "candidate.choose_mutation", "alice_director", "Choose one auditable improvement action from the learning policy and state the falsifiable expectation."),
        WorkItem("learning", "candidate.apply_mutation", "rules_engineer", "Apply exactly the chosen mutation to the complete candidate, preserve physical manufacturability, and return the revised candidate plus its falsifiable expectation.", depends_on=("candidate.choose_mutation",)),
    ),
}


OUTPUT_CONTRACTS: dict[str, dict[str, Any]] = {
    "library.discover": {
        "required": ["queue", "acquisition_actions", "coverage_gaps"],
    },
    "library.read": {
        "required": [
            "source_id",
            "access_basis",
            "edition",
            "citations",
            "claims",
            "unavailable_reason",
        ],
        "properties": {
            "source_id": {"type": "string", "minLength": 1},
            "access_basis": {
                "type": "string",
                "enum": [
                    "licensed",
                    "owned_copy",
                    "library_loan",
                    "public_domain",
                    "open_access",
                    "author_permission",
                    "unavailable",
                ],
            },
            "edition": {"type": "string", "minLength": 1},
            "citations": {"type": "array"},
            "claims": {"type": "array"},
            "unavailable_reason": {"type": ["string", "null"]},
        },
    },
    "library.synthesize": {
        "required": ["agreements", "contradictions", "scope_conditions"],
    },
    "history.scan_traditional": {
        "required": ["sources", "citations", "games", "ludemes", "uncertainty"],
    },
    "history.scan_modern": {
        "required": ["sources", "citations", "games", "mechanics", "uncertainty"],
    },
    "concept.select": {
        "required": ["candidate"],
    },
    "candidate.rules": {
        "required": [
            "candidate_content_sha256",
            "rules_sha256",
            "setup",
            "turn",
            "legal_actions",
            "end",
            "scoring",
            "ties",
            "rules_markdown",
        ],
        "additionalProperties": True,
    },
    "candidate.prior_art": {
        "required": ["queries", "closest_precedents", "material_differences", "citations"],
    },
    "candidate.safety_ip": {
        "required": ["critical_safety_findings", "critical_ip_findings", "citations"],
    },
    "rules.lint": {
        "required": ["candidate_content_sha256", "rules_sha256", "rules_complete", "terminates", "ambiguities", "termination_proof"],
    },
    "rules.adversary": {
        "required": ["candidate_content_sha256", "rules_sha256", "critical_exploits", "attacks", "traces"],
    },
    "simulation.optimizer": {
        "required": ["candidate_content_sha256", "rules_sha256", "seed", "games", "policies", "win_rates", "dominant_strategy", "traces"],
        "properties": {
            "seed": {"type": "integer"},
            "games": {"type": "integer", "minimum": 1},
            "policies": {"type": "array", "minItems": 1},
            "win_rates": {"type": "object", "minProperties": 1},
            "traces": {"type": "array", "minItems": 1},
        },
    },
    "simulation.social": {
        "required": ["candidate_content_sha256", "rules_sha256", "seed", "games", "policies", "kingmaking", "spite_loops", "traces"],
        "properties": {
            "seed": {"type": "integer"},
            "games": {"type": "integer", "minimum": 1},
            "policies": {"type": "array", "minItems": 1},
            "traces": {"type": "array", "minItems": 1},
        },
    },
    "simulation.explorer": {
        "required": ["candidate_content_sha256", "rules_sha256", "seed", "games", "edge_cases", "state_coverage", "traces"],
        "properties": {
            "seed": {"type": "integer"},
            "games": {"type": "integer", "minimum": 1},
            "edge_cases": {"type": "array"},
            "traces": {"type": "array", "minItems": 1},
        },
    },
    "simulation.exploit": {
        "required": ["candidate_content_sha256", "rules_sha256", "seed", "games", "critical_exploits", "traces"],
        "properties": {
            "seed": {"type": "integer"},
            "games": {"type": "integer", "minimum": 1},
            "critical_exploits": {"type": "integer", "minimum": 0},
            "traces": {"type": "array", "minItems": 1},
        },
    },
    "human.prepare_blind_kit": {
        "required": ["candidate_content_sha256", "rules_sha256", "blind_kit_sha256", "rules_pdf_readback", "rules_pdf_sha256", "observation_sheet", "preregistered_measures"],
    },
    "human.collect_blind_results": {
        "required": [
            "trial_ids",
            "candidate_content_sha256",
            "rules_sha256",
            "blind_kit_sha256",
            "blind_groups",
            "group_ids",
            "minimum_games_per_group",
            "designer_hints_required",
            "independent_operator_id",
            "consent_provenance",
            "trial_provenance",
            "reward_evidence",
        ],
    },
    "physical.cad": {
        "required": ["candidate_content_sha256", "rules_sha256", "rules_file_sha256", "artifact_hashes", "slug", "project_sha256"],
    },
    "physical.dfm": {
        "required": [
            "artifact_hashes",
            "candidate_content_sha256",
            "rules_sha256",
            "rules_file_sha256",
            "project_sha256",
            "fit",
            "tolerances",
            "print_yield",
            "landed_cost",
            "receipt",
        ],
    },
    "physical.create_rich_draft": {
        "required": [
            "operation_key",
            "candidate_id",
            "candidate_version",
            "candidate_content_sha256",
            "rules_sha256",
            "rules_file_sha256",
            "design_id",
            "slug",
            "history_id",
            "project_url",
            "status",
            "project_sha256",
            "artifact_hashes",
            "rich_page",
        ],
    },
    "physical.prototype_print": {
        "required": ["candidate_content_sha256", "rules_sha256", "rules_file_sha256", "project_sha256", "artifact_hashes", "original_operation", "effect_operation_key", "task_input_sha256", "machine", "material", "profile", "inspection", "receipt"],
    },
    "physical.production_run": {
        "required": [
            "production_manifest",
            "candidate_content_sha256",
            "rules_sha256",
            "rules_file_sha256",
            "project_sha256",
            "artifact_hashes",
            "original_operation",
            "effect_operation_key",
            "task_input_sha256",
            "production_packet_hash",
            "reviewed_packet_hash",
            "print_yield",
            "landed_cost",
            "landed_cost_cents",
            "reward_evidence",
            "receipt",
        ],
    },
    "market.offer": {
        "required": ["audience", "promise", "price_cents", "currency", "disclosures"],
    },
    "market.validate_offer": {
        "required": [
            "price_cents",
            "currency",
            "candidate_content_sha256",
            "rules_sha256",
            "rules_file_sha256",
            "project_sha256",
            "artifact_hashes",
            "landed_cost_cents",
            "fees_cents",
            "shipping_subsidy_cents",
            "gross_margin",
            "reviewed_packet_hash",
            "factory_capabilities",
            "reward_evidence",
            "receipt",
        ],
    },
    "market.final_safety_ip": {
        "required": ["candidate_content_sha256", "rules_sha256", "critical_safety_findings", "critical_ip_findings", "reviewed_packet_hash", "citations"],
    },
    "release.evaluate": {
        "required": [
            "allowed",
            "policy_hash",
            "effect_mode",
            "failures",
            "production_packet_hash",
            "reviewed_packet_hash",
            "artifact_manifest_sha256",
        ],
    },
    "outcomes.ingest": {
        "required": ["outcomes"],
    },
    "orders.poll_paid": {
        "required": ["orders"],
    },
    "orders.create_print_job": {
        "required": ["print_jobs"],
    },
    "orders.qa_ship": {
        "required": ["shipments"],
    },
    "policy.shadow": {
        "required": ["accepted", "rejected", "state_version", "updates"],
    },
    "candidate.choose_mutation": {
        "required": ["action", "context", "selection"],
    },
    "candidate.apply_mutation": {
        "required": ["candidate", "action", "expectation"],
    },
    "publish.packet": {
        "required": [
            "publication_packet",
            "packet_hash",
            "policy_hash",
            "release_decision",
        ],
    },
}


LEGAL_BOOK_ACCESS_BASES = frozenset(
    {
        "owned_copy",
        "licensed_ebook",
        "publisher_or_author_copy",
        "library_loan",
        "public_domain",
        "legally_available_excerpt",
        "unavailable",
    }
)


def validate_output_semantics(action: str, content: Mapping[str, Any]) -> None:
    """Validate high-value semantics not expressible as top-level key presence.

    The model-facing contracts above steer structured generation.  This helper
    is deterministic and can also be called at persistence/release boundaries;
    release assembly already uses it for every simulation artifact.
    """

    if not isinstance(content, Mapping):
        raise ValueError(f"{action} output must be an object")
    if action == "library.read":
        for key in ("source_id", "access_basis", "edition"):
            _required_trimmed(content.get(key), f"library.read {key}")
        access_basis = str(content["access_basis"])
        if access_basis not in LEGAL_BOOK_ACCESS_BASES:
            raise ValueError("library.read access_basis is not a legal acquisition basis")
        citations = content.get("citations")
        claims = content.get("claims")
        if not isinstance(citations, list) or not isinstance(claims, list):
            raise ValueError("library.read citations and claims must be arrays")
        unavailable = content.get("unavailable_reason")
        if access_basis == "unavailable":
            _required_trimmed(unavailable, "library.read unavailable_reason")
            if citations or claims:
                raise ValueError(
                    "an unavailable library source cannot claim citations or reading notes"
                )
            return
        if unavailable not in (None, ""):
            raise ValueError(
                "an acquired library source cannot also have unavailable_reason"
            )
        if not citations or any(not _meaningful_entry(item) for item in citations):
            raise ValueError("an acquired library source needs non-empty citations")
        if not claims or any(not _meaningful_entry(item) for item in claims):
            raise ValueError("an acquired library source needs non-empty claims")
        return

    if not action.startswith("simulation."):
        return
    seed = content.get("seed")
    games = content.get("games")
    traces = content.get("traces")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError(f"{action} seed must be an integer")
    if isinstance(games, bool) or not isinstance(games, int) or games <= 0:
        raise ValueError(f"{action} games must be a positive integer")
    if not isinstance(traces, list) or not traces or any(
        not _meaningful_entry(item) for item in traces
    ):
        raise ValueError(f"{action} traces must contain a real play trace")
    if action in {"simulation.optimizer", "simulation.social"}:
        policies = content.get("policies")
        if not isinstance(policies, list) or not policies or any(
            not _meaningful_entry(item) for item in policies
        ):
            raise ValueError(f"{action} policies must be non-empty")
    if action == "simulation.optimizer":
        win_rates = content.get("win_rates")
        if not isinstance(win_rates, Mapping) or not win_rates:
            raise ValueError("simulation.optimizer win_rates must be non-empty")
    if action == "simulation.explorer":
        coverage = content.get("state_coverage")
        if isinstance(coverage, bool) or not isinstance(coverage, (int, float)):
            raise ValueError("simulation.explorer state_coverage must be numeric")
        if not 0.0 < float(coverage) <= 1.0:
            raise ValueError("simulation.explorer state_coverage must be in (0, 1]")


def _required_trimmed(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be a non-empty trimmed string")
    return value


def _meaningful_entry(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value) and all(
            isinstance(key, str) and bool(key.strip()) for key in value
        )
    return False


def work_for_state(state: str, candidate_id: str) -> tuple[WorkItem, ...]:
    """Bind a candidate id to the independent jobs required at its current state."""

    return tuple(
        WorkItem(
            loop=item.loop,
            action=item.action,
            role=item.role,
            objective=item.objective,
            candidate_id=candidate_id,
            payload=item.payload,
            depends_on=item.depends_on,
        )
        for item in STATE_WORK.get(state, ())
    )
