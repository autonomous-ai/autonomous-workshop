"""The customer and operator CLI for Autonomous Workshop."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from .artifacts import MAX_PACK_BYTES
from .clockwork import Clockwork
from .contribution import check_target, manifests_for_target
from .errors import WorkshopError
from .factory_agent import (
    FactoryAgentInstructionsWriter,
    FactoryAgentSession,
    FactoryPublicTransition,
    factory_credentials_from_environment,
)
from .handoff import (
    ManagerAssignmentHandoff,
    validate_manager_assignment_result,
)
from .jobs import Delivered, Invented, Need, WaitingFor, WorkshopRun
from .execution_env import codex_subprocess_environment
from .agent_instructions import (
    DEFAULT_INSTRUCTIONS_CREATOR_MODEL,
    DEFAULT_INSTRUCTIONS_REWARD_MODEL,
    RewardedInstructions,
)
from .make import Wish, generate_wish_id
from .manifest import (
    discover_inventors,
    inventor_collection,
    load_manifest,
    validate_entrypoints,
)
from .models import Receipt
from .pack import pack_artifact, plan_pack, seal_artifact
from .manager import WorkshopManager, discover_inventor_catalog
from .semantic_manager import CodexSemanticManager
from .scaffold import (
    create_inventor,
    prepare_inventor_collection,
    scaffold_inventor,
)
from .schemas import discover_schemas, resolve_schemas_root
from .skills import discover_skills, resolve_skills_root
from .store import InventorStore
from .runtime import Runtime
from .taste import load_taste, load_taste_header
from .toys import PLAYTHING_LANES, ToyBlueprint
from .workshop import CUSTOMIZATION_LEVELS, Workshop, WorkshopTools


DEFAULT_WISH_PLAYTEST_ROUNDS = 4
_SHARED_ENGINE_ENVIRONMENT_NAMES = frozenset(
    (
        "WORKSHOP_CODEX_BIN",
        "WORKSHOP_INVENT_MODEL",
        "WORKSHOP_REWARD_MODEL",
        "WORKSHOP_MAKE_MODEL",
        "WORKSHOP_MAKE_REWARD_MODEL",
        "WORKSHOP_PLAYTEST_MODEL",
        "WORKSHOP_INSTRUCTIONS_MODEL",
        "WORKSHOP_INSTRUCTIONS_REWARD_MODEL",
        "WORKSHOP_CAD_PYTHON",
        "WORKSHOP_HANDLING_FORCE_N",
        "WORKSHOP_HANDLING_SAFETY_FACTOR",
        "WORKSHOP_HANDLING_TORQUE_N_MM",
        "WORKSHOP_PRUSASLICER_BIN",
        "WORKSHOP_PRUSASLICER_PRINTER_PROFILE",
        "WORKSHOP_PRUSASLICER_FILAMENT_PROFILE",
        "WORKSHOP_PRUSASLICER_PROCESS_PROFILE",
        "WORKSHOP_PRUSASLICER_VERSION",
        "WORKSHOP_PRUSA_PROFILES",
    )
)


def _inventor_process_environment(inventor_id: str) -> Mapping[str, str]:
    """Build a strict worker environment with no Factory or unrelated secrets.

    An inventor entrypoint is contribution code. It receives the Codex runtime
    inputs needed by shared Invent/Make/Playtest workers, but Factory authority
    stays in the Workshop Manager process for the later Instructions handoff.
    """

    if not isinstance(inventor_id, str) or not inventor_id:
        raise WorkshopError("selected Inventor identity is malformed")
    environment = dict(codex_subprocess_environment(os.environ))
    environment.update(
        {
            name: value
            for name in _SHARED_ENGINE_ENVIRONMENT_NAMES
            if isinstance((value := os.environ.get(name)), str) and value
        }
    )
    environment["WORKSHOP_AGENT_WORKERS"] = "codex"
    environment["WORKSHOP_INVENT_WORKER"] = "codex"
    return environment


def _factory_credential_environment(
    inventor_id: str, source: Optional[Mapping[str, str]] = None
) -> Optional[Mapping[str, str]]:
    """Select one Factory account inside the trusted Manager process only."""

    values = os.environ if source is None else source
    password = values.get("FACTORY_PASSWORD")
    if not isinstance(password, str) or not password:
        return None
    return {"FACTORY_USERNAME": inventor_id, "FACTORY_PASSWORD": password}


def _manifest_workshop_shape(card: Any) -> tuple[str, str]:
    """Read one exact lane/contribution pair from the selected manifest."""

    card_current = getattr(card, "assert_manifest_current", None)
    if callable(card_current):
        card_current()
    manifest = load_manifest(Path(card.root) / "inventor.json")
    lanes = tuple(item for item in manifest.capabilities if item in PLAYTHING_LANES)
    levels = tuple(
        item for item in manifest.capabilities if item in CUSTOMIZATION_LEVELS
    )
    if (
        len(lanes) != 1
        or len(levels) != 1
        or set(manifest.capabilities) != {lanes[0], levels[0]}
    ):
        raise WorkshopError(
            "selected Inventor manifest must declare exactly one lane and one known contribution level"
        )
    return lanes[0], levels[0]


def _invented_from_event(value: Any) -> Invented:
    if not isinstance(value, Mapping) or set(value) != {
        "wish_sha256",
        "taste_sha256",
        "lane",
        "concept",
        "concept_sha256",
        "score",
        "target_score",
        "passed",
    }:
        raise WorkshopError("persisted Invent result is malformed")
    invented = Invented(
        wish_sha256=value["wish_sha256"],
        taste_sha256=value["taste_sha256"],
        lane=value["lane"],
        concept=value["concept"],
        score=value["score"],
        target_score=value["target_score"],
    )
    if invented.to_dict() != dict(value):
        raise WorkshopError("persisted Invent result identity is inconsistent")
    return invented


def _delivered_from_event(value: Any) -> Delivered:
    if not isinstance(value, Mapping) or set(value) != {
        "schema_version",
        "product_artifact_sha256",
        "instructions_sha256",
        "carrier",
        "service",
        "tracking_id",
        "status",
        "observed_at",
        "evidence",
    } or value.get("schema_version") != 1:
        raise WorkshopError("persisted Deliver result is malformed")
    return Delivered(
        product_artifact_sha256=value["product_artifact_sha256"],
        instructions_sha256=value["instructions_sha256"],
        carrier=value["carrier"],
        service=value["service"],
        tracking_id=value["tracking_id"],
        status=value["status"],
        observed_at=value["observed_at"],
        evidence=value["evidence"],
    )


def _validate_child_workshop_state(
    assignment: Any,
    child_result: Mapping[str, Any],
    *,
    allow_durable_factory_page: bool = False,
) -> Mapping[str, Any]:
    """Derive the child result from the trusted event chain, never stdout claims."""

    card = assignment.decision.selected.card
    lane, level = _manifest_workshop_shape(card)
    database = Path(card.root) / ".workshop" / "workshop.sqlite3"
    if database.is_symlink() or not database.is_file():
        raise WorkshopError(
            "selected Inventor returned no durable Workshop event chain"
        )
    runtime = Runtime(database)
    product_id = assignment.wish.product_id
    if not runtime.verify_event_chain(product_id):
        raise WorkshopError("selected Inventor Workshop event chain is not trustworthy")
    product = runtime.get_product(product_id)
    events = runtime.events(product_id)
    if not events:
        raise WorkshopError("selected Inventor Workshop event chain is empty")
    latest = events[-1]
    payload = latest.get("payload")
    if not isinstance(payload, Mapping):
        raise WorkshopError("latest Workshop event payload is malformed")
    taste = assignment.decision.selected.taste
    expected_metadata = {
        "wish": assignment.wish.to_dict(),
        "inventor_id": card.inventor_id,
        "taste_sha256": taste.sha256,
        "blueprint_sha256": ToyBlueprint.for_lane(lane).sha256,
        "lane": lane,
        "customization_level": level,
        "playtest_rounds": assignment.playtest_rounds,
    }
    if product.get("metadata") != expected_metadata:
        raise WorkshopError(
            "durable Workshop state differs from the exact Manager assignment"
        )
    job = product.get("stage")
    if latest.get("to_stage") != job:
        raise WorkshopError("latest Workshop event differs from product state")
    status = payload.get("status")
    if status not in ("waiting", "stopped", "delivered"):
        raise WorkshopError(
            "selected Inventor stopped without a terminal Workshop event"
        )
    round_number = payload.get("round")
    if type(round_number) is not int:
        raise WorkshopError("terminal Workshop event has no valid round")
    artifact_sha256 = product.get("artifact_sha256")
    if latest.get("artifact_sha256") != artifact_sha256:
        raise WorkshopError("terminal Workshop artifact identity is inconsistent")
    needs = ()
    if status == "waiting":
        raw_needs = payload.get("needs")
        if not isinstance(raw_needs, list) or not raw_needs:
            raise WorkshopError("waiting Workshop event has no typed needs")
        try:
            needs = tuple(Need(**dict(item)) for item in raw_needs)
        except (TypeError, WorkshopError) as exc:
            raise WorkshopError("waiting Workshop needs are malformed") from exc
    instructions_sha256 = next(
        (
            event["payload"].get("instructions_sha256")
            for event in reversed(events)
            if isinstance(event.get("payload"), Mapping)
            and isinstance(event["payload"].get("instructions_sha256"), str)
        ),
        None,
    )
    invented_value = next(
        (
            event["payload"].get("invented")
            for event in events
            if isinstance(event.get("payload"), Mapping)
            and "invented" in event["payload"]
        ),
        None,
    )
    invented = (
        _invented_from_event(invented_value)
        if invented_value is not None
        else None
    )
    delivery = None
    if status == "delivered":
        delivery = _delivered_from_event(payload.get("delivery"))
        if (
            delivery.product_artifact_sha256 != artifact_sha256
            or delivery.instructions_sha256 != instructions_sha256
        ):
            raise WorkshopError("persisted Deliver result has different exact inputs")
    page_url = None
    if allow_durable_factory_page:
        intent = InventorStore(database).latest_publish_intent(product_id)
        receipt_value = intent.get("receipt") if isinstance(intent, Mapping) else None
        try:
            receipt = Receipt.from_dict(receipt_value)
            receipt.assert_artifact(artifact_sha256)
        except (TypeError, WorkshopError) as exc:
            raise WorkshopError(
                "Manager-resumed Instructions lacks an exact durable Factory receipt"
            ) from exc
        if not (receipt.is_verified_draft or receipt.is_verified_public):
            raise WorkshopError(
                "Manager-resumed Instructions Factory receipt is not verified"
            )
        if receipt.details.get("instructions_sha256") != instructions_sha256:
            raise WorkshopError(
                "Manager-resumed Factory receipt identifies different Instructions"
            )
        page_url = receipt.details.get("page_url")
        if not isinstance(page_url, str) or not page_url:
            raise WorkshopError("Manager-resumed Factory receipt has no product page")
    trusted = WorkshopRun(
        product_id=product_id,
        status=status,
        job=job,
        round=round_number,
        artifact_sha256=artifact_sha256,
        instructions_sha256=instructions_sha256,
        needs=needs,
        delivery=delivery,
        playtest_rounds=assignment.playtest_rounds,
        page_url=page_url,
        invented=invented,
    ).to_dict()
    supplied = {
        key: value
        for key, value in child_result.items()
        if key != "manager_assignment"
    }
    if supplied != trusted:
        raise WorkshopError(
            "selected Inventor stdout differs from its durable Workshop state"
        )
    return {**trusted, "manager_assignment": child_result["manager_assignment"]}


class _ResumeOnlyStructuredRunner:
    """Identity-only runner; sealed Instructions resume must never invoke AI."""

    def __init__(self, model: str, reasoning_effort: str) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.cli_version = "resume-only.1.0.0"

    def invoke(self, **kwargs):  # pragma: no cover - a resume invariant
        del kwargs
        raise WorkshopError("sealed Instructions resume attempted to rerun AI")


def _resume_factory_instructions(
    assignment: Any,
    result: Mapping[str, Any],
    *,
    environment: Optional[Mapping[str, str]] = None,
    store_factory: Any = InventorStore,
    writer_factory: Any = FactoryAgentInstructionsWriter,
    workshop_factory: Any = Workshop,
    state_validator: Any = _validate_child_workshop_state,
) -> Mapping[str, Any]:
    """Resume only a sealed Factory handoff outside inventor-owned code.

    The selected profile runs without Factory credentials and therefore stops
    truthfully after scoring and sealing its manual/page facts. If the Manager
    owns a credential, this function gives it only to the shared site adapter,
    reconstructs the exact checkpoint, and resumes Instructions without
    executing the profile or any custom Invent/Make/Playtest hook.
    """

    if not isinstance(result, Mapping):
        raise WorkshopError("Workshop child result must be an object")
    needs = result.get("needs")
    is_factory_wait = (
        result.get("status") == "waiting"
        and result.get("job") == "instructions"
        and isinstance(needs, list)
        and any(
            isinstance(need, Mapping)
            and need.get("job") == "instructions"
            and need.get("capability") in ("site-page", "site-reconciliation")
            for need in needs
        )
    )
    if not is_factory_wait:
        return dict(result)
    inventor_id = assignment.decision.selected.card.inventor_id
    selected_environment = _factory_credential_environment(
        inventor_id, os.environ if environment is None else environment
    )
    if selected_environment is None:
        return dict(result)
    assert_current = getattr(assignment, "assert_current", None)
    if callable(assert_current):
        assert_current()
    card = assignment.decision.selected.card
    lane, level = _manifest_workshop_shape(card)
    credentials = factory_credentials_from_environment(
        inventor_id, selected_environment
    )
    runtime_root = Path(card.root) / ".workshop"
    writer = writer_factory(
        store_factory(runtime_root / "workshop.sqlite3"),
        inventor_id,
        credentials,
    )
    instructions = RewardedInstructions(
        writer,
        creator=_ResumeOnlyStructuredRunner(
            DEFAULT_INSTRUCTIONS_CREATOR_MODEL, "medium"
        ),
        evaluator=_ResumeOnlyStructuredRunner(
            DEFAULT_INSTRUCTIONS_REWARD_MODEL, "low"
        ),
    )

    def unavailable(context):  # pragma: no cover - resume must not call these
        del context
        raise WorkshopError("Instructions resume attempted an earlier Workshop stage")

    workshop_kwargs = {
        "inventor_id": inventor_id,
        "tools": WorkshopTools(
            invent=unavailable,
            make=unavailable,
            playtest=unavailable,
            instructions=instructions,
        ),
        "runtime_root": runtime_root,
    }
    # These inert seams reconstruct only the checkpoint-bound contribution
    # level. They are never called by resume_instructions and never import or
    # execute the inventor's custom implementation.
    if level in ("custom-make", "custom-playtest"):
        workshop_kwargs["make"] = unavailable
    if level == "custom-playtest":
        workshop_kwargs["playtest"] = unavailable
    workshop = workshop_factory(card.root, lane, **workshop_kwargs)
    resumed = workshop.resume_instructions(assignment.wish).to_dict()
    handoff = ManagerAssignmentHandoff.from_assignment(assignment)
    if result.get("manager_assignment") != handoff.result_binding():
        raise WorkshopError(
            "Manager-resumed Instructions lost its exact assignment binding"
        )
    rebound = {**resumed, "manager_assignment": handoff.result_binding()}
    if not callable(state_validator):
        raise WorkshopError("Workshop resumed-state validator must be callable")
    return state_validator(
        assignment,
        rebound,
        allow_durable_factory_page=True,
    )


def _run_inventor(
    assignment,
    *,
    runner: Any = subprocess.run,
    state_validator: Any = _validate_child_workshop_state,
) -> Mapping[str, Any]:
    handoff = ManagerAssignmentHandoff.from_assignment(assignment)
    command = list(assignment.entrypoint)
    if command[0] in ("python", "python3"):
        command[0] = sys.executable
    command.extend(("run", "--assignment-stdin"))
    inventor_id = assignment.decision.selected.card.inventor_id
    completed = runner(
        command,
        cwd=str(assignment.decision.selected.card.root),
        env=_inventor_process_environment(inventor_id),
        input=json.dumps(
            handoff.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ),
        capture_output=True,
        text=True,
        timeout=3600,
        check=False,
    )
    if completed.returncode != 0:
        raise WorkshopError(
            "the selected Inventor stopped before returning a Workshop result"
        )
    try:
        payload = json.loads(completed.stdout)
    except (TypeError, ValueError) as exc:
        raise WorkshopError(
            "the selected Inventor returned an unreadable Workshop result"
        ) from exc
    if not isinstance(payload, dict):
        raise WorkshopError("the selected Inventor must return one Workshop result")
    try:
        bound = validate_manager_assignment_result(payload, handoff)
    except WorkshopError as exc:
        raise WorkshopError(
            "the selected Inventor returned a result for a different Manager assignment"
        ) from exc
    if not callable(state_validator):
        raise WorkshopError("Workshop child state validator must be callable")
    return state_validator(assignment, bound)


def _publish_inventor_draft(
    assignment,
    result: Mapping[str, Any],
    *,
    store_factory: Any = InventorStore,
    session_factory: Any = FactoryAgentSession,
    transition_factory: Any = FactoryPublicTransition,
) -> Mapping[str, Any]:
    """Make the exact authenticated Instructions draft public, then prove it."""

    product_id = assignment.wish.product_id
    inventor_id = assignment.decision.selected.card.inventor_id
    page_url = result.get("page_url")
    artifact_sha256 = result.get("artifact_sha256")
    if not isinstance(page_url, str) or not page_url:
        return {
            "status": "waiting",
            "reason": "Instructions has not produced an authenticated Factory draft yet.",
        }
    environment = _factory_credential_environment(inventor_id)
    try:
        if environment is None:
            raise WorkshopError("Factory credentials are not configured")
        credentials = factory_credentials_from_environment(inventor_id, environment)
        runtime_root = Path(assignment.decision.selected.card.root) / ".workshop"
        store = store_factory(runtime_root / "workshop.sqlite3")
        intent = store.latest_publish_intent(product_id)
        receipt_value = intent.get("receipt") if isinstance(intent, Mapping) else None
        draft = Receipt.from_dict(receipt_value)
        if draft.details.get("page_url") != page_url:
            raise WorkshopError(
                "the Factory draft URL differs from the Workshop Instructions receipt"
            )
        if isinstance(artifact_sha256, str):
            draft.assert_artifact(artifact_sha256)
        public = transition_factory(session_factory(credentials)).publish(draft)
    except WorkshopError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise WorkshopError(
            "the selected Inventor has no exact authenticated draft to publish"
        ) from exc
    return {
        "status": "public",
        "verified": True,
        "inventor_id": inventor_id,
        "design_id": public.design_id,
        "slug": public.slug,
        "current_history_id": public.current_history_id,
        "page_url": page_url,
    }


def _waiting_receipt(wish: Wish, waiting: WaitingFor) -> Mapping[str, Any]:
    return {
        "schema_version": 1,
        "status": "waiting",
        "wish": wish.to_dict(),
        "needs": [item.to_dict() for item in waiting.needs],
    }


def _print_wish_receipt(receipt: Mapping[str, Any]) -> None:
    wish = receipt["wish"]
    print("Wish: %s" % wish["product_id"])
    match = receipt.get("match")
    if isinstance(match, dict):
        print("Matched with %s." % match["name"])
        print("Why: %s" % match["explanation"])
    result = receipt.get("result", receipt)
    invented = result.get("invented")
    if isinstance(invented, dict):
        concept = invented.get("concept")
        title = concept.get("title") if isinstance(concept, dict) else None
        if isinstance(title, str) and title:
            print(
                "Invented: %s (%s/%s)."
                % (title, invented.get("score"), invented.get("target_score"))
            )
    if result.get("status") == "waiting":
        job = result.get("job")
        print("Waiting%s." % (" at %s" % str(job).title() if job else ""))
        for need in result.get("needs", ()):
            print("  %s — %s" % (need["capability"], need["reason"]))
    else:
        print("Status: %s" % result.get("status", "started"))
    publication = result.get("publication")
    if isinstance(publication, Mapping):
        if publication.get("status") == "public":
            print("Live: %s" % publication["page_url"])
        elif publication.get("reason"):
            print("Page: waiting — %s" % publication["reason"])


def _wish(args: argparse.Namespace) -> int:
    objective = " ".join(args.objective)
    wish = Wish.create(
        generate_wish_id(),
        objective,
        context={"source": "workshop-cli"},
    )
    semantic = CodexSemanticManager()
    manager = WorkshopManager(
        root=args.root,
        retriever=semantic.retrieve,
        judge=semantic.judge,
        judge_identity=semantic.judge_identity,
        judge_version=semantic.judge_version,
        judge_config_sha256=semantic.judge_config_sha256,
    )
    try:
        assignment = manager.assign(
            wish, playtest_rounds=DEFAULT_WISH_PLAYTEST_ROUNDS
        )
    except WaitingFor as waiting:
        receipt = _waiting_receipt(wish, waiting)
    else:
        result = _run_inventor(assignment)
        result = _resume_factory_instructions(assignment, result)
        if args.publish:
            result = {
                **result,
                "publication": _publish_inventor_draft(assignment, result),
            }
        decision = assignment.decision
        receipt = {
            "schema_version": 1,
            "status": result.get("status", "started"),
            "wish": wish.to_dict(),
            "match": {
                "inventor_id": assignment.inventor_id,
                "name": decision.selected.card.name,
                "score": decision.fit.score,
                "explanation": decision.fit.explanation,
                "decision_sha256": decision.decision_sha256,
            },
            "assignment_sha256": assignment.assignment_sha256,
            "result": result,
        }
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        _print_wish_receipt(receipt)
    return 0


def _registry(args: argparse.Namespace) -> int:
    manifests = discover_inventors(args.root)
    problems = validate_entrypoints(manifests) if args.check_entrypoints else []
    records = []
    for manifest in manifests:
        header = load_taste_header(manifest.path.parent)
        records.append(
            {
                "id": manifest.inventor_id,
                "status": manifest.status,
                "name": header.name,
                "description": header.description,
            }
        )
    if args.json:
        print(json.dumps(records, indent=2, sort_keys=True))
    else:
        for item in records:
            print(
                "%-12s %-18s %-20s %s"
                % (item["id"], item["status"], item["name"], item["description"])
            )
        print("%d inventor manifests valid" % len(manifests))
    for problem in problems:
        print("error: %s" % problem, file=sys.stderr)
    return 1 if problems else 0


def _manifest(args: argparse.Namespace) -> int:
    manifest = seal_artifact(args.source, extra_excludes=args.exclude)
    if args.output:
        manifest.write(args.output)
    print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
    return 0


def _pack(args: argparse.Namespace) -> int:
    packed = pack_artifact(
        args.source,
        args.output,
        extra_excludes=args.exclude,
        maximum_bytes=args.maximum_bytes,
    )
    print(
        json.dumps(
            {
                "artifact_sha256": packed.artifact_sha256,
                "bytes": packed.bytes,
                "entries": packed.entries,
                "pack_sha256": packed.pack_sha256,
                "path": str(packed.path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _plan_pack(args: argparse.Namespace) -> int:
    plan = plan_pack(
        args.source,
        extra_excludes=args.exclude,
        maximum_bytes=args.maximum_bytes,
        largest=args.largest,
    )
    print(json.dumps(plan.to_dict(), indent=2, sort_keys=True))
    return 0 if plan.fits else 1


def _init_state(args: argparse.Namespace) -> int:
    Clockwork(args.database)
    print(str(args.database))
    return 0


def _audit_state(args: argparse.Namespace) -> int:
    if not args.database.is_file():
        raise FileNotFoundError("state database does not exist: %s" % args.database)
    store = Clockwork(args.database)
    valid = store.verify_event_chain(args.product_id)
    print("valid" if valid else "INVALID")
    return 0 if valid else 1


def _new_inventor(args: argparse.Namespace) -> int:
    destination = scaffold_inventor(
        inventor_collection(args.root),
        args.inventor_id,
        args.name,
        args.niche,
        lane=args.lane,
        level=args.level,
        template=args.template,
    )
    print(str(destination))
    return 0


def _default_inventor_name(inventor_id: str) -> str:
    return " ".join(part.capitalize() for part in inventor_id.split("-"))


def _create_inventor(args: argparse.Namespace) -> int:
    collection = prepare_inventor_collection(args.root)
    name = args.name or _default_inventor_name(args.inventor_id)
    destination = create_inventor(
        collection,
        args.inventor_id,
        name,
        args.description,
        lane=args.lane,
        level=args.level,
        run_checks=True,
    )
    catalog = discover_inventor_catalog(collection)
    card = catalog.card(args.inventor_id)
    taste = load_taste(destination)
    receipt = {
        "schema_version": 1,
        "status": card.status,
        "id": args.inventor_id,
        "name": card.name,
        "description": card.description,
        "lane": args.lane,
        "level": args.level,
        "path": str(destination),
        "taste_sha256": taste.sha256,
        "manifest_sha256": card.manifest_sha256,
        "catalog_sha256": catalog.catalog_sha256,
        "catalog_size": len(catalog.cards),
        "validation": {"layout": "passed", "checks": "passed"},
    }
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        try:
            visible = destination.relative_to(Path.cwd())
        except ValueError:
            visible = destination
        print("%s joined the Workshop (experimental)." % card.name)
        print("Taste: %s" % (visible / "TASTE.md"))
        print("Checks: passed")
    return 0


def _check_inventor(args: argparse.Namespace) -> int:
    manifests = manifests_for_target(args.target)
    problems = check_target(args.target, run=args.run)
    for problem in problems:
        print("error: %s" % problem, file=sys.stderr)
    if not problems:
        action = "checks passed" if args.run else "layout valid"
        print("%d inventor(s): %s" % (len(manifests), action))
    return 1 if problems else 0


def _skills(args: argparse.Namespace) -> int:
    root = resolve_skills_root(args.root)
    if args.action == "path":
        print(str(root))
        return 0
    skills = discover_skills(root)
    if args.json:
        print(
            json.dumps(
                [skill.to_dict() for skill in skills],
                indent=2,
                sort_keys=True,
            )
        )
    else:
        for skill in skills:
            print("%-20s %s" % (skill.name, skill.sha256))
    return 0


def _schemas(args: argparse.Namespace) -> int:
    root = resolve_schemas_root(args.root)
    if args.action == "path":
        print(str(root))
        return 0
    for path in discover_schemas(root):
        print(path.name)
    return 0


def parser() -> argparse.ArgumentParser:
    root = Path.cwd()
    command = argparse.ArgumentParser(prog="workshop")
    subcommands = command.add_subparsers(
        dest="command", required=True, metavar="COMMAND"
    )

    wish = subcommands.add_parser(
        "wish", help="wish for a toy and let the Workshop choose its Inventor"
    )
    wish.add_argument(
        "objective",
        nargs="+",
        help="what you wish existed (quotes are optional)",
    )
    wish.add_argument(
        "--root",
        type=Path,
        default=root,
        help="Workshop checkout or inventor collection (default: current directory)",
    )
    wish.add_argument("--json", action="store_true")
    wish.add_argument(
        "--publish",
        action="store_true",
        help=(
            "make the exact authenticated Instructions draft public; this does "
            "not claim the toy was printed or delivered"
        ),
    )
    wish.set_defaults(handler=_wish)

    registry = subcommands.add_parser(
        "inventors", aliases=("registry",), help="list and validate inventors"
    )
    registry.add_argument("--root", type=Path, default=root)
    registry.add_argument("--json", action="store_true")
    registry.add_argument("--check-entrypoints", action="store_true")
    registry.set_defaults(handler=_registry)

    artifact = subcommands.add_parser(
        "seal", aliases=("artifact",), help="seal a product artifact tree"
    )
    artifact.add_argument("source", type=Path)
    artifact.add_argument("--output", type=Path)
    artifact.add_argument("--exclude", action="append", default=[])
    artifact.set_defaults(handler=_manifest)

    pack = subcommands.add_parser("pack", help="build a reproducible immutable Pack")
    pack.add_argument("source", type=Path)
    pack.add_argument("output", type=Path)
    pack.add_argument("--exclude", action="append", default=[])
    pack.add_argument("--maximum-bytes", type=int, default=MAX_PACK_BYTES)
    pack.set_defaults(handler=_pack)

    plan = subcommands.add_parser(
        "plan-pack", help="preview exact Pack size and largest eligible files"
    )
    plan.add_argument("source", type=Path)
    plan.add_argument("--exclude", action="append", default=[])
    plan.add_argument("--maximum-bytes", type=int, default=MAX_PACK_BYTES)
    plan.add_argument("--largest", type=int, default=5)
    plan.set_defaults(handler=_plan_pack)

    clockwork = subcommands.add_parser(
        "clockwork", help="initialize or audit durable Workshop state"
    )
    clockwork_commands = clockwork.add_subparsers(dest="clockwork_action", required=True)
    state = clockwork_commands.add_parser("init", help="initialize the durable database")
    state.add_argument("database", type=Path)
    state.set_defaults(handler=_init_state)
    audit = clockwork_commands.add_parser("audit", help="verify a product event hash chain")
    audit.add_argument("database", type=Path)
    audit.add_argument("product_id")
    audit.set_defaults(handler=_audit_state)

    # Compatibility commands for 0.2 automation.
    legacy_state = subcommands.add_parser("init-state")
    legacy_state.add_argument("database", type=Path)
    legacy_state.set_defaults(handler=_init_state)
    legacy_audit = subcommands.add_parser("audit-state")
    legacy_audit.add_argument("database", type=Path)
    legacy_audit.add_argument("product_id")
    legacy_audit.set_defaults(handler=_audit_state)

    create = subcommands.add_parser(
        "create", help="create a new inventor"
    )
    create_commands = create.add_subparsers(
        dest="create_kind", required=True, metavar="THING"
    )
    creator = create_commands.add_parser(
        "inventor",
        help="create a discoverable inventor powered by the Workshop",
    )
    creator.add_argument("inventor_id")
    creator.add_argument(
        "--name",
        help="display name (defaults to the inventor id in title case)",
    )
    creator.add_argument(
        "--description",
        required=True,
        help=(
            "Taste selection boundary: what should choose this inventor and "
            "the closest work that should not"
        ),
    )
    creator.add_argument(
        "--lane",
        choices=PLAYTHING_LANES,
        required=True,
        help="kind of plaything this inventor makes",
    )
    creator.add_argument(
        "--level",
        choices=CUSTOMIZATION_LEVELS,
        default="taste-only",
        help="creative code owned by the inventor (default: taste-only)",
    )
    creator.add_argument("--root", type=Path, default=root)
    creator.add_argument(
        "--json",
        action="store_true",
        help="emit a stable creation receipt for an agent",
    )
    creator.set_defaults(handler=_create_inventor)

    # Read-only command compatibility through 0.x. It is intentionally absent
    # from help; new humans and agents should learn only ``create inventor``.
    new = subcommands.add_parser("new")
    new.add_argument("inventor_id")
    new.add_argument("--name", required=True)
    new.add_argument("--niche", required=True)
    new.add_argument(
        "--lane",
        choices=PLAYTHING_LANES,
        help="kind of plaything this inventor makes",
    )
    new.add_argument(
        "--level",
        choices=CUSTOMIZATION_LEVELS,
        default="taste-only",
        help="how much Make and Playtest code this inventor owns (default: taste-only)",
    )
    new.add_argument(
        "--template",
        choices=("board-game", "physical-product", "custom"),
        help=argparse.SUPPRESS,
    )
    new.add_argument("--root", type=Path, default=root)
    new.set_defaults(handler=_new_inventor)

    check = subcommands.add_parser(
        "check", help="validate an inventor contribution"
    )
    check.add_argument(
        "target",
        type=Path,
        nargs="?",
        default=root,
        help="inventor folder, manifest, inventors/ collection, or repository",
    )
    check.add_argument(
        "--run",
        action="store_true",
        help="also execute the manifest's declared checks without a shell",
    )
    check.set_defaults(handler=_check_inventor)

    skills = subcommands.add_parser(
        "skills", help="discover the workshop's versioned agent skills"
    )
    skills.add_argument("action", choices=("list", "path"), nargs="?", default="list")
    skills.add_argument(
        "--root",
        type=Path,
        help="absolute skills root (auto-detected in a source checkout)",
    )
    skills.add_argument("--json", action="store_true")
    skills.set_defaults(handler=_skills)

    schemas = subcommands.add_parser(
        "schemas", help="discover the Workshop's installed JSON contracts"
    )
    schemas.add_argument("action", choices=("list", "path"), nargs="?", default="list")
    schemas.add_argument("--root", type=Path)
    schemas.set_defaults(handler=_schemas)
    return command


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parser().parse_args(argv)
        return int(args.handler(args))
    except (WorkshopError, OSError, ValueError, KeyError) as exc:
        print("workshop: %s" % exc, file=sys.stderr)
        return 2
