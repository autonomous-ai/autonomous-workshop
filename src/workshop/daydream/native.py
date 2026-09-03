"""Run one Daydream: private workspace, one native Manager turn, lint, seal."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Optional, Sequence

from workshop.contributors import (
    InventorManifest,
    Taste,
    discover_inventors,
    inventor_collection,
    load_taste,
    validate_inventor_collection,
)
from workshop.contributors.extensions import load_inventor_extension_bundles
from workshop.daydream._files import read_regular_bytes, write_private_bytes
from workshop.daydream.catalog import (
    PriorWork,
    lint_novelty,
    load_prior_work,
    render_prior_work_markdown,
    source_checkout_root,
)
from workshop.daydream.contracts import (
    DaydreamProvenance,
    Verdict,
    CREATED_AT_FORMAT,
    DaydreamError,
    Idea,
    NoveltyReport,
    ROUTE_FLOORS,
    SealedDaydream,
    canonical_json,
    generate_daydream_id,
    render_brief,
    require_daydream_id,
    require_inventor_id,
)
from workshop.daydream.notebook import (
    JudgeMemory,
    NotebookEntry,
    StructuralTrace,
    append_notebook_entry,
    prior_work_from_notebook,
    read_notebook,
    render_notebook_markdown,
    unresolved_actionable_entries,
)
from workshop.daydream.outcomes import (
    RunOutcomeMemory,
    read_outcomes,
    render_outcomes_markdown,
)
from workshop.daydream.prompt import (
    DAYDREAM_CONSTITUTION,
    DAYDREAM_CONSTITUTION_SHA256,
    JUDGE_CONSTITUTION,
    JUDGE_CONSTITUTION_SHA256,
    ROUTE_BUDGETS,
    build_daydream_prompt,
    build_judge_prompt,
)
from workshop.daydream.portfolio import (
    PortfolioEntry,
    load_portfolio,
    prior_work_from_portfolio,
    render_portfolio_markdown,
)
from workshop.daydream.seeds import DaydreamSeed, draw_seed
from workshop._validation import require_sha256
from workshop.errors import ContractError, ManifestError
from workshop.invent.gamevault import (
    GameVaultError,
    GameVaultUnavailable,
    default_client as default_gamevault_client,
)
from workshop.invent.vault import MAX_PACKED_BYTES, Vault
from workshop.runtime.agent_assets import (
    InventorSkillBinding,
    inventor_custom_agent_bytes,
    parse_inventor_custom_agent_bytes,
)
from workshop.runtime.codex import CodexInvocationError, CodexRecoverableInvocationError
from workshop.runtime.managers import (
    NativeManagerRecoverableError,
    DEFAULT_MANAGER_ID,
    NativeManagerInvocationError,
    manager_launcher,
    manager_project_bytes,
    manager_spec,
)
from workshop.runtime.package_data import (
    PackageDataError,
    default_workshop_home,
    product_run_domain_skill_roots,
)
from workshop.runtime.project_boundary import (
    PRODUCT_RUN_ROOT_MARKER,
    PRODUCT_RUN_ROOT_MARKER_BYTES,
)
from workshop.wish import Wish, generate_wish_id


DAYDREAM_TURN_TIMEOUT_SECONDS = 900
DAYDREAM_REJECTION_KIND = "autonomous-workshop.daydream-rejection"
IDEA_FILE_NAME = "IDEA.json"
OUTCOME_FILE_NAME = "agent-outcome.json"
FINALIZER_FILE_NAME = "finalize_daydream.py"
SCHEMA_FILE_NAME = "daydream_schema.py"
DAYDREAM_OUTCOME_KIND = "autonomous-workshop.daydream-outcome"
MAX_OUTCOME_FILE_BYTES = 64 * 1024
JUDGE_WORKSPACE_NAME = "judge-workspace"
JUDGE_STATE_NAME = "judge-state"
VERDICT_FILE_NAME = "VERDICT.json"
JUDGE_TURN_TIMEOUT_SECONDS = 600
REJECTED_FILE_NAME = "REJECTED.json"
INVENTOR_BINDING_FILE_NAME = "INVENTOR.json"
VAULT_BINDING_FILE_NAME = "VAULT-BINDING.json"
PROVENANCE_FILE_NAME = "PROVENANCE.json"
MAX_IDEA_FILE_BYTES = 64 * 1024
MAX_SEALED_FILE_BYTES = 256 * 1024
MAX_ERROR_CHARS = 1_000
NOTEBOOK_LINT_LIMIT = 1_000_000
WISH_CONTEXT_SOURCE = "workshop-daydream"
MAX_INVENTOR_SOURCE_BYTES = 64 * 1024
MAX_DAYDREAM_SKILL_FILES = 128
MAX_DAYDREAM_SKILL_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class DaydreamPaths:
    """One private daydream container and the Inventor's shared notebook."""

    container: Path
    workspace: Path
    work: Path
    host_state: Path
    notebook: Path
    outcomes: Path


def _existing_real_directory(path: Path, *, label: str, private: bool = True) -> Path:
    try:
        identity = path.lstat()
    except OSError as exc:
        raise DaydreamError("%s is unavailable: %s" % (label, path)) from exc
    if path.is_symlink() or not stat.S_ISDIR(identity.st_mode):
        raise DaydreamError("%s must be a real directory: %s" % (label, path))
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise DaydreamError("%s is unavailable: %s" % (label, path)) from exc
    if resolved != path:
        raise DaydreamError("%s must not contain symlinks: %s" % (label, path))
    if private and stat.S_IMODE(identity.st_mode) != 0o700:
        raise DaydreamError("%s permissions must be 0700: %s" % (label, path))
    return resolved


def _ensure_private_directory(path: Path, *, label: str) -> Path:
    created = False
    try:
        path.mkdir(mode=0o700)
        created = True
    except FileExistsError:
        pass
    except OSError as exc:
        raise DaydreamError("%s could not be created: %s" % (label, path)) from exc
    if created:
        os.chmod(path, 0o700)
    return _existing_real_directory(path, label=label)


def _exclusive_private_directory(path: Path, *, label: str) -> Path:
    if path.exists() or path.is_symlink():
        raise DaydreamError("%s already exists: %s" % (label, path))
    try:
        path.mkdir(mode=0o700)
    except OSError as exc:
        raise DaydreamError("%s could not be created exclusively: %s" % (label, path)) from exc
    os.chmod(path, 0o700)
    return _existing_real_directory(path, label=label)


def _workshop_home(home: Optional[Path]) -> Path:
    selected = Path(home) if home is not None else Path(default_workshop_home())
    selected = selected.expanduser()
    if not selected.is_absolute():
        raise ContractError("Workshop home must be absolute")
    try:
        selected.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as exc:
        raise DaydreamError("Workshop home could not be created: %s" % selected) from exc
    return _existing_real_directory(selected, label="Workshop home", private=False)


def _inventor_daydreams(inventor_id: str, *, home: Optional[Path], create: bool) -> Path:
    root = _workshop_home(home)
    daydreams = root / "daydreams"
    folder = daydreams / inventor_id
    if create:
        _ensure_private_directory(daydreams, label="private daydreams directory")
        return _ensure_private_directory(folder, label="Inventor daydreams directory")
    _existing_real_directory(daydreams, label="private daydreams directory")
    return _existing_real_directory(folder, label="Inventor daydreams directory")


def daydream_paths(
    inventor_id: str,
    daydream_id: str,
    *,
    home: Optional[Path] = None,
    create: bool = False,
) -> DaydreamPaths:
    """Resolve one private daydream workspace, its host state, and the notebook."""

    inventor_id = require_inventor_id(inventor_id)
    daydream_id = require_daydream_id(daydream_id)
    folder = _inventor_daydreams(inventor_id, home=home, create=create)
    container = folder / daydream_id
    if create:
        container = _exclusive_private_directory(container, label="daydream container")
        workspace = _exclusive_private_directory(
            container / "workspace", label="daydream workspace"
        )
        work = _exclusive_private_directory(workspace / "work", label="daydream work directory")
        host_state = _exclusive_private_directory(
            container / "host-state", label="daydream host state"
        )
    else:
        container = _existing_real_directory(container, label="daydream container")
        workspace = _existing_real_directory(
            container / "workspace", label="daydream workspace"
        )
        work = _existing_real_directory(workspace / "work", label="daydream work directory")
        host_state = _existing_real_directory(
            container / "host-state", label="daydream host state"
        )
    return DaydreamPaths(
        container=container,
        workspace=workspace,
        work=work,
        host_state=host_state,
        notebook=folder / "NOTEBOOK.jsonl",
        outcomes=folder / "OUTCOMES.jsonl",
    )


def resolve_inventor(
    inventor_id: str, *, source_root: Path
) -> tuple[InventorManifest, Taste]:
    """Find one validated Inventor bundle and load its exact Taste."""

    inventor_id = require_inventor_id(inventor_id)
    collection = inventor_collection(Path(source_root))
    validate_inventor_collection(collection)
    manifests = discover_inventors(collection)
    for manifest in manifests:
        if manifest.inventor_id == inventor_id:
            return manifest, load_taste(manifest.path.parent)
    raise DaydreamError(
        "unknown Inventor: %s (known: %s)"
        % (inventor_id, ", ".join(sorted(item.inventor_id for item in manifests)))
    )


def _utc_moment(moment: Optional[datetime]) -> datetime:
    observed = moment if moment is not None else datetime.now(timezone.utc)
    if not isinstance(observed, datetime):
        raise ContractError("daydream moment must be a datetime")
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    return observed.astimezone(timezone.utc)


def finalizer_bytes() -> bytes:
    """The exact run-local finalizer the host copies into every workspace."""

    return read_regular_bytes(
        Path(__file__).with_name(FINALIZER_FILE_NAME),
        maximum=MAX_OUTCOME_FILE_BYTES * 4,
        label="daydream finalizer source",
    )


def schema_bytes() -> bytes:
    """The exact shared schema copied beside the run-local finalizer."""

    return read_regular_bytes(
        Path(__file__).with_name("schema.py"),
        maximum=MAX_OUTCOME_FILE_BYTES * 8,
        label="daydream schema source",
    )


def _materialize_domain_skill(paths: DaydreamPaths, *, name: str, source_root: Path) -> None:
    """Copy one trusted package-owned skill without following linked content."""

    requested = Path(source_root)
    if requested.is_symlink():
        raise DaydreamError("Daydream domain skill %s must not be a symlink" % name)
    try:
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise DaydreamError("Daydream domain skill %s is unavailable" % name) from exc
    if root != requested or not root.is_dir():
        raise DaydreamError("Daydream domain skill %s must be a canonical directory" % name)
    entries: list[tuple[Path, Path, int]] = []
    total = 0
    for source in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = source.relative_to(root)
        if "__pycache__" in relative.parts or source.name == ".DS_Store":
            continue
        if source.is_symlink():
            raise DaydreamError("Daydream domain skill %s contains a symlink" % name)
        if source.is_dir():
            continue
        try:
            identity = source.lstat()
        except OSError as exc:
            raise DaydreamError("Daydream domain skill %s changed while reading" % name) from exc
        if not stat.S_ISREG(identity.st_mode):
            raise DaydreamError("Daydream domain skill %s contains a special file" % name)
        total += identity.st_size
        entries.append((source, relative, identity.st_mode))
    if (
        not entries
        or len(entries) > MAX_DAYDREAM_SKILL_FILES
        or total > MAX_DAYDREAM_SKILL_BYTES
    ):
        raise DaydreamError("Daydream domain skill %s exceeds its input bounds" % name)

    skills_root = paths.workspace / ".agents" / "skills"
    for directory, label in (
        (paths.workspace / ".agents", "Daydream agent inputs"),
        (skills_root, "Daydream skill inputs"),
        (skills_root / name, "Daydream %s skill" % name),
    ):
        _ensure_private_directory(directory, label=label)
    target_root = skills_root / name
    for source, relative, source_mode in entries:
        content = read_regular_bytes(
            source,
            maximum=MAX_DAYDREAM_SKILL_BYTES,
            label="Daydream %s skill file" % name,
        )
        destination = target_root / relative
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        write_private_bytes(
            destination,
            content,
            label="materialized Daydream %s skill" % name,
        )
        os.chmod(destination, 0o500 if source_mode & 0o111 else 0o400)


def _default_vault_loader() -> Vault:
    return default_gamevault_client().export()


def _materialize_vault(
    paths: DaydreamPaths, *, vault_loader: Callable[[], Vault]
) -> tuple[bytes, Mapping[str, Any]]:
    """Fetch one host-owned advisory Vault snapshot and its offline query skill."""

    try:
        design_vault_skill = product_run_domain_skill_roots()["design-vault"]
    except (KeyError, PackageDataError) as exc:
        raise DaydreamError("the packaged design-vault skill is unavailable") from exc
    _materialize_domain_skill(paths, name="design-vault", source_root=design_vault_skill)
    try:
        vault = vault_loader()
    except GameVaultUnavailable:
        binding: Mapping[str, Any] = {"status": "unavailable"}
        summary = (
            "# Design Vault advisory context\n\n"
            "Status: unavailable for this Daydream. Do not claim Vault leads or "
            "invent missing knowledge. Continue from Taste, world sources, portfolio, "
            "and prior art.\n"
        ).encode("utf-8")
    except GameVaultError as exc:
        raise DaydreamError("Design Vault returned invalid evidence: %s" % exc) from exc
    else:
        if not isinstance(vault, Vault):
            raise DaydreamError("Design Vault loader returned no typed Vault")
        packed = vault.packed_bytes()
        if not 1 <= len(packed) <= MAX_PACKED_BYTES:
            raise DaydreamError("Design Vault snapshot exceeds its byte bound")
        digest = hashlib.sha256(packed).hexdigest()
        binding = {
            "status": "available",
            "path": "VAULT.json",
            "skill": ".agents/skills/design-vault/SKILL.md",
            "sha256": digest,
            "nodes": len(vault.nodes),
        }
        write_private_bytes(
            paths.workspace / "VAULT.json", packed, label="Daydream Vault snapshot"
        )
        os.chmod(paths.workspace / "VAULT.json", 0o400)
        write_private_bytes(
            paths.host_state / "VAULT.json", packed, label="host Daydream Vault snapshot"
        )
        summary = (
            "# Design Vault advisory context\n\n"
            "Status: available\n"
            "Snapshot: `VAULT.json`\n"
            "SHA-256: `%s`\n"
            "Nodes: %d\n\n"
            "Query it only through `.agents/skills/design-vault/vault_tools.py`. "
            "This pre-Wish workspace has no `STAGE.json`; use only the skill's "
            "offline resolve, node, and guidance queries. "
            "Treat every result as an advisory mechanism lead or risk, never an "
            "engineering fact and never Taste authority.\n"
            % (digest, len(vault.nodes))
        ).encode("utf-8")
    write_private_bytes(
        paths.host_state / VAULT_BINDING_FILE_NAME,
        (canonical_json(binding) + "\n").encode("utf-8"),
        label="Daydream Vault binding",
    )
    return summary, binding


def _materialize_selected_inventor(
    paths: DaydreamPaths, *, manifest: InventorManifest, taste: Taste
) -> Mapping[str, Any]:
    """Project the selected Inventor's exact agent and skill trees read-only."""

    try:
        bundles = load_inventor_extension_bundles(manifest)
    except ManifestError as exc:
        raise DaydreamError("selected Inventor skills are invalid: %s" % exc) from exc
    if not bundles:
        raise DaydreamError("selected Inventor declares no specialist skill")
    manifest_bytes = read_regular_bytes(
        manifest.path,
        maximum=MAX_INVENTOR_SOURCE_BYTES,
        label="selected Inventor manifest",
    )
    taste_path = manifest.path.parent / "TASTE.md"
    taste_bytes = read_regular_bytes(
        taste_path,
        maximum=MAX_INVENTOR_SOURCE_BYTES,
        label="selected Inventor Taste",
    )
    if hashlib.sha256(taste_bytes).hexdigest() != taste.sha256:
        raise DaydreamError("selected Inventor Taste changed after validation")
    skills = tuple(
        InventorSkillBinding(
            name=bundle.extension.name,
            path=bundle.extension.path,
            artifact_sha256=bundle.extension.artifact_sha256,
        )
        for bundle in bundles
    )
    try:
        agent_bytes = inventor_custom_agent_bytes(
            manifest.inventor_id,
            manifest_bytes,
            taste_bytes,
            skills=skills,
        )
    except ContractError as exc:
        raise DaydreamError("selected Inventor custom agent is invalid: %s" % exc) from exc

    agents_root = paths.workspace / ".agents"
    skills_root = agents_root / "skills"
    codex_root = paths.workspace / ".codex"
    codex_agents = codex_root / "agents"
    for directory, label in (
        (agents_root, "Daydream agent inputs"),
        (skills_root, "Daydream skill inputs"),
        (codex_root, "Daydream Codex inputs"),
        (codex_agents, "Daydream custom agents"),
    ):
        _ensure_private_directory(directory, label=label)

    for bundle in bundles:
        target_root = skills_root / bundle.extension.name
        _ensure_private_directory(target_root, label="Inventor skill %s" % bundle.extension.name)
        for entry in bundle.manifest.entries:
            relative = PurePosixPath(entry.path)
            source = bundle.root.joinpath(*relative.parts)
            content = read_regular_bytes(
                source,
                maximum=entry.bytes,
                label="Inventor skill %s" % relative.as_posix(),
            )
            if len(content) != entry.bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
                raise DaydreamError(
                    "Inventor skill %s changed after validation" % relative.as_posix()
                )
            destination = target_root.joinpath(*relative.parts)
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            write_private_bytes(
                destination,
                content,
                label="materialized Inventor skill %s" % relative.as_posix(),
            )
            os.chmod(destination, 0o500 if entry.executable else 0o400)

    agent_path = codex_agents / (manifest.inventor_id + ".toml")
    write_private_bytes(agent_path, agent_bytes, label="materialized Inventor custom agent")
    os.chmod(agent_path, 0o400)
    try:
        binding = parse_inventor_custom_agent_bytes(agent_bytes)
    except ContractError as exc:  # pragma: no cover - compiler and parser share a contract
        raise DaydreamError("materialized Inventor custom agent is invalid") from exc
    for root in (agents_root, codex_root):
        for directory in sorted(
            (path for path in root.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            os.chmod(directory, 0o500)
        os.chmod(root, 0o500)
    return binding.to_host_dict()


def _write_workspace(
    paths: DaydreamPaths,
    *,
    taste: Taste,
    repository_prior: Sequence[PriorWork],
    notebook_entries: Sequence[NotebookEntry],
    portfolio_entries: Sequence[PortfolioEntry],
    outcome_entries: Sequence[RunOutcomeMemory],
    vault_summary: bytes,
) -> Mapping[str, str]:
    files = (
        ("TASTE.md", taste.content.encode("utf-8")),
        ("PRIOR-WORK.md", render_prior_work_markdown(repository_prior).encode("utf-8")),
        (
            "PORTFOLIO.md",
            render_portfolio_markdown(portfolio_entries).encode("utf-8"),
        ),
        (
            "NOTEBOOK.md",
            (
                render_notebook_markdown(notebook_entries)
                + "\n"
                + render_outcomes_markdown(outcome_entries)
            ).encode("utf-8"),
        ),
        ("VAULT.md", vault_summary),
        # The constitution doubles as AGENTS.md so the Manager runtime loads it
        # the same way it loads a product run's constitution.
        ("AGENTS.md", DAYDREAM_CONSTITUTION.encode("utf-8")),
        (FINALIZER_FILE_NAME, finalizer_bytes()),
        (SCHEMA_FILE_NAME, schema_bytes()),
        (PRODUCT_RUN_ROOT_MARKER, PRODUCT_RUN_ROOT_MARKER_BYTES),
    )
    identities: dict[str, str] = {}
    for name, payload in files:
        write_private_bytes(paths.workspace / name, payload, label="daydream %s" % name)
        identities[name] = hashlib.sha256(payload).hexdigest()
    return identities


def _normalized_excerpt(value: str) -> str:
    return " ".join(value.casefold().split())


def _validate_thesis_evidence(
    idea: Idea, *, taste: Taste, observed_at: str, route: str
) -> None:
    """Bind temporal claims and Taste citations to the exact turn inputs."""

    if idea.schema_version != 3:
        raise DaydreamError("new Daydream Goals must finalize an idea with schema_version 3")
    assert idea.opportunity is not None
    if idea.opportunity.world_scan.observed_at != observed_at or any(
        entry.observed_at != observed_at for entry in idea.prior_art
    ):
        raise DaydreamError(
            "Daydream world-scan and prior-art observed_at must match the exact turn time"
        )
    assert idea.route_floor is not None
    if ROUTE_FLOORS.index(route) < ROUTE_FLOORS.index(idea.route_floor):
        raise DaydreamError(
            "Daydream thesis requires at least the %s route; target route is %s"
            % (idea.route_floor, route)
        )
    taste_text = _normalized_excerpt(taste.content)
    citations = (*idea.taste_fit.honors, *idea.taste_fit.steers_clear_of)
    missing = [
        citation
        for citation in citations
        if _normalized_excerpt(citation) not in taste_text
    ]
    if missing:
        raise DaydreamError(
            "Daydream Taste citations are not exact excerpts of TASTE.md: %s"
            % "; ".join(missing)
        )


def _validate_learning(
    idea: Idea, entries: Sequence[NotebookEntry]
) -> None:
    """Require exact closure of the newest unresolved rejected thesis.

    This is a lineage gate only.  Whether the prior creative direction should
    be repaired or abandoned, and whether the response is good, remain native
    Inventor and independent-Judge judgments.
    """

    if idea.schema_version != 3:
        raise DaydreamError("new Daydream learning requires an idea with schema_version 3")
    unresolved = unresolved_actionable_entries(entries)
    unresolved_by_id = {entry.daydream_id: entry for entry in unresolved}
    traces_by_id = {trace.daydream_id: trace for trace in idea.learning}
    stale = sorted(set(traces_by_id) - set(unresolved_by_id))
    if stale:
        raise DaydreamError(
            "Daydream learning references resolved or non-actionable memories: %s"
            % ", ".join(stale)
        )
    for daydream_id, trace in traces_by_id.items():
        if trace.memory_sha256 != unresolved_by_id[daydream_id].sha256:
            raise DaydreamError(
                "Daydream learning memory_sha256 does not match %s" % daydream_id
            )
    if unresolved and unresolved[-1].daydream_id not in traces_by_id:
        raise DaydreamError(
            "Daydream learning must disposition newest unresolved memory %s"
            % unresolved[-1].daydream_id
        )


def _json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _json_line_sha256(value: Any) -> str:
    return hashlib.sha256((canonical_json(value) + "\n").encode("utf-8")).hexdigest()


def _build_provenance(
    *,
    route: str,
    manager: Any,
    prompt: str,
    idea: Idea,
    workspace_sha256s: Mapping[str, str],
    inventor_binding: Mapping[str, Any],
    vault_binding: Mapping[str, Any],
) -> DaydreamProvenance:
    assert idea.opportunity is not None
    vault_snapshot = vault_binding.get("sha256")
    if vault_snapshot is not None:
        require_sha256(vault_snapshot, "Daydream Vault snapshot sha256")
    return DaydreamProvenance(
        route=route,
        input_sha256s={
            "daydream_prompt": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "daydream_constitution": workspace_sha256s["AGENTS.md"],
            "judge_constitution": JUDGE_CONSTITUTION_SHA256,
            "taste": workspace_sha256s["TASTE.md"],
            "inventor_binding": _json_line_sha256(inventor_binding),
            "vault_binding": _json_line_sha256(vault_binding),
            "vault_snapshot": vault_snapshot,
            "prior_work": workspace_sha256s["PRIOR-WORK.md"],
            "portfolio": workspace_sha256s["PORTFOLIO.md"],
            "notebook": workspace_sha256s["NOTEBOOK.md"],
            "finalizer": workspace_sha256s[FINALIZER_FILE_NAME],
            "schema": workspace_sha256s[SCHEMA_FILE_NAME],
            "world_scan": _json_sha256(idea.opportunity.world_scan.to_dict()),
            "prior_art": _json_sha256([entry.to_dict() for entry in idea.prior_art]),
            "manager_spec": hashlib.sha256(manager_project_bytes(manager)).hexdigest(),
        },
    )


def _daydream_wish_sha256(
    daydream_id: str, inventor_id: str, taste_sha256: str, seed: DaydreamSeed
) -> str:
    identity = {
        "daydream_id": daydream_id,
        "inventor_id": inventor_id,
        "taste_sha256": taste_sha256,
        "seed": seed.to_dict(),
    }
    return hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest()


def _native_turn(
    launcher_factory: Callable[..., Any],
    manager_id: str,
    *,
    run_root: Path,
    host_state_root: Path,
    product_id: str,
    wish_sha256: str,
    constitution_sha256: str,
    prompt: str,
    activity_observer: Optional[Callable[[str], None]],
    finalized_files: Sequence[Path],
    label: str,
    launcher_kwargs: Mapping[str, Any],
) -> Mapping[str, Any]:
    try:
        launcher = launcher_factory(manager_id, **launcher_kwargs)
        outcome = launcher.start(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
            prompt=prompt,
            activity_observer=activity_observer,
            finalization_marker=run_root / OUTCOME_FILE_NAME,
        )
    except (NativeManagerRecoverableError, CodexRecoverableInvocationError) as exc:
        # The runtime lost its terminal event or timed out after the Goal was
        # finalized.  The finalized file is still the agent's work; keep it
        # and record the truth.
        if all(path.is_file() for path in finalized_files) and (
            run_root / OUTCOME_FILE_NAME
        ).is_file():
            return {"status": "incomplete", "error": _bounded_error(exc)}
        raise DaydreamError("%s session failed: %s" % (label, exc)) from exc
    except (CodexInvocationError, NativeManagerInvocationError, ContractError) as exc:
        raise DaydreamError("%s session failed: %s" % (label, exc)) from exc
    to_dict = getattr(outcome, "to_dict", None)
    if not callable(to_dict):
        raise DaydreamError("%s session returned no redacted outcome" % label)
    try:
        return json.loads(canonical_json(dict(to_dict())))
    except (TypeError, ValueError) as exc:
        raise DaydreamError("%s session outcome is not a JSON object" % label) from exc


def _bounded_error(exc: BaseException) -> str:
    text = " ".join(str(exc).split())
    return text[:MAX_ERROR_CHARS] if text else exc.__class__.__name__


def _read_outcome(
    workspace: Path, *, file_name: str, who: str, goal: str
) -> Mapping[str, Any]:
    """Require the finalizer's Goal marker and bind it to the exact finalized bytes."""

    relative = "work/%s" % file_name
    try:
        payload = read_regular_bytes(
            workspace / OUTCOME_FILE_NAME,
            maximum=MAX_OUTCOME_FILE_BYTES,
            label="agent-outcome.json",
        )
    except FileNotFoundError as exc:
        raise DaydreamError(
            "the %s did not finalize its %s Goal: agent-outcome.json is missing" % (who, goal)
        ) from exc
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise DaydreamError("agent-outcome.json is not valid UTF-8 JSON: %s" % exc) from exc
    if (
        not isinstance(raw, dict)
        or raw.get("schema_version") != 1
        or raw.get("kind") != DAYDREAM_OUTCOME_KIND
        or raw.get("status") != "ready"
        or raw.get("idea_path") != relative
    ):
        raise DaydreamError("agent-outcome.json is not a ready %s outcome" % goal)
    try:
        require_sha256(raw.get("idea_sha256"), "%s outcome sha256" % goal)
    except ContractError as exc:
        raise DaydreamError("agent-outcome.json carries no sha256") from exc
    try:
        finalized = read_regular_bytes(
            workspace / "work" / file_name, maximum=MAX_IDEA_FILE_BYTES, label=relative
        )
    except FileNotFoundError as exc:
        raise DaydreamError("the %s wrote no %s" % (who, relative)) from exc
    if hashlib.sha256(finalized).hexdigest() != raw["idea_sha256"]:
        raise DaydreamError(
            "%s changed after the finalizer ran; its bytes do not match agent-outcome.json"
            % relative
        )
    return raw


def _read_idea(path: Path) -> Idea:
    try:
        payload = read_regular_bytes(path, maximum=MAX_IDEA_FILE_BYTES, label="work/IDEA.json")
    except FileNotFoundError as exc:
        raise DaydreamError("the Inventor wrote no work/IDEA.json") from exc
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise DaydreamError("work/IDEA.json is not valid UTF-8 JSON: %s" % exc) from exc
    if not isinstance(raw, dict):
        raise DaydreamError("work/IDEA.json must be a JSON object")
    try:
        return Idea.parse(raw)
    except ContractError as exc:
        raise DaydreamError("work/IDEA.json is invalid: %s" % exc) from exc


def _read_verdict(path: Path) -> Verdict:
    try:
        payload = read_regular_bytes(path, maximum=MAX_IDEA_FILE_BYTES, label="work/VERDICT.json")
    except FileNotFoundError as exc:
        raise DaydreamError("the judge wrote no work/VERDICT.json") from exc
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise DaydreamError("work/VERDICT.json is not valid UTF-8 JSON: %s" % exc) from exc
    if not isinstance(raw, dict):
        raise DaydreamError("work/VERDICT.json must be a JSON object")
    try:
        return Verdict.parse(raw)
    except ContractError as exc:
        raise DaydreamError("work/VERDICT.json is invalid: %s" % exc) from exc


def judge_idea(
    paths: DaydreamPaths,
    *,
    idea: Idea,
    taste: Taste,
    inventor_id: str,
    manager_id: str,
    effort: str,
    daydream_id: str,
    notebook_entries: Sequence[NotebookEntry],
    launcher_factory: Callable[..., Any] = manager_launcher,
    activity_observer: Optional[Callable[[str], None]] = None,
) -> tuple[Verdict, Mapping[str, Any]]:
    """Run the independent Judge Goal on a sealed idea and return its verdict."""

    if effort not in ROUTE_BUDGETS:
        raise ContractError("judge route is unknown: %r" % (effort,))
    workspace = _exclusive_private_directory(
        paths.container / JUDGE_WORKSPACE_NAME, label="judge workspace"
    )
    _ensure_private_directory(workspace / "work", label="judge work directory")
    state = _exclusive_private_directory(paths.container / JUDGE_STATE_NAME, label="judge host state")
    files = (
        ("IDEA.json", (canonical_json(idea.to_dict()) + "\n").encode("utf-8")),
        ("TASTE.md", taste.content.encode("utf-8")),
        (
            "NOTEBOOK.md",
            render_notebook_markdown(notebook_entries).encode("utf-8"),
        ),
        ("ROUTE.md", ("# Route\n\n%s\n" % ROUTE_BUDGETS[effort]).encode("utf-8")),
        ("AGENTS.md", JUDGE_CONSTITUTION.encode("utf-8")),
        (FINALIZER_FILE_NAME, finalizer_bytes()),
        (SCHEMA_FILE_NAME, schema_bytes()),
        (PRODUCT_RUN_ROOT_MARKER, PRODUCT_RUN_ROOT_MARKER_BYTES),
    )
    for name, payload in files:
        write_private_bytes(workspace / name, payload, label="judge %s" % name)
    launcher_kwargs: dict[str, Any] = {"timeout_seconds": JUDGE_TURN_TIMEOUT_SECONDS}
    if manager_id == "codex":
        # The judge reads one small file; medium reasoning is enough and fast.
        launcher_kwargs["reasoning_effort"] = "medium"
    session = _native_turn(
        launcher_factory,
        manager_id,
        run_root=workspace,
        host_state_root=state,
        product_id="%s-judge" % daydream_id,
        wish_sha256=hashlib.sha256(
            canonical_json(
                {"daydream_id": daydream_id, "idea_sha256": idea.sha256, "effort": effort}
            ).encode("utf-8")
        ).hexdigest(),
        constitution_sha256=JUDGE_CONSTITUTION_SHA256,
        prompt=build_judge_prompt(
            inventor_name=taste.name,
            inventor_id=inventor_id,
            title=idea.title,
            effort=effort,
            daydream_id=daydream_id,
            idea_sha256=idea.sha256,
            taste_sha256=taste.sha256,
        ),
        activity_observer=activity_observer,
        finalized_files=(workspace / "work" / VERDICT_FILE_NAME,),
        label="Judge",
        launcher_kwargs=launcher_kwargs,
    )
    _existing_real_directory(workspace, label="judge workspace")
    _existing_real_directory(workspace / "work", label="judge work directory", private=False)
    _read_outcome(workspace, file_name=VERDICT_FILE_NAME, who="judge", goal="Judge")
    verdict = _read_verdict(workspace / "work" / VERDICT_FILE_NAME)
    if verdict.schema_version >= 2 and (
        verdict.daydream_id != daydream_id
        or verdict.idea_sha256 != idea.sha256
        or verdict.taste_sha256 != taste.sha256
        or verdict.route != effort
    ):
        raise DaydreamError("Judge verdict identity does not match the exact Daydream inputs")
    write_private_bytes(
        paths.host_state / VERDICT_FILE_NAME,
        (
            canonical_json({"verdict": verdict.to_dict(), "session": dict(session)}) + "\n"
        ).encode("utf-8"),
        label="judge verdict",
    )
    return verdict, session


def _remember(
    paths: DaydreamPaths,
    *,
    daydream_id: str,
    created_at: str,
    idea: Idea,
    status: str,
    verdict: Optional[Verdict] = None,
    rejection_reason: Optional[str] = None,
) -> None:
    thesis_memory = idea.schema_version in (2, 3)
    append_notebook_entry(
        paths.notebook,
        NotebookEntry(
            daydream_id=daydream_id,
            created_at=created_at,
            title=idea.title,
            one_liner=idea.one_liner,
            idea_sha256=idea.sha256,
            status=status,
            schema_version=idea.schema_version if thesis_memory else 1,
            structure=StructuralTrace.from_idea(idea) if thesis_memory else None,
            judge=JudgeMemory.from_verdict(verdict) if verdict is not None else None,
            rejection_reason=rejection_reason,
            learning=idea.learning,
        ),
    )


def _reject(
    paths: DaydreamPaths,
    *,
    daydream_id: str,
    created_at: str,
    idea: Idea,
    novelty: NoveltyReport,
) -> None:
    rejection = {
        "schema_version": 1,
        "kind": DAYDREAM_REJECTION_KIND,
        "daydream_id": daydream_id,
        "created_at": created_at,
        "idea": idea.to_dict(),
        "novelty": novelty.to_dict(),
    }
    write_private_bytes(
        paths.host_state / REJECTED_FILE_NAME,
        (canonical_json(rejection) + "\n").encode("utf-8"),
        label="daydream rejection",
    )
    _remember(
        paths,
        daydream_id=daydream_id,
        created_at=created_at,
        idea=idea,
        status="rejected",
        rejection_reason=novelty.reason,
    )


def run_daydream(
    inventor_id: str,
    *,
    source_root: Path,
    manager_id: str = DEFAULT_MANAGER_ID,
    repository_root: Optional[Path] = None,
    home: Optional[Path] = None,
    launcher_factory: Callable[..., Any] = manager_launcher,
    activity_observer: Optional[Callable[[str], None]] = None,
    seed: Optional[DaydreamSeed] = None,
    moment: Optional[datetime] = None,
    daydream_id: Optional[str] = None,
    effort: Optional[str] = None,
    vault_loader: Callable[[], Vault] = _default_vault_loader,
) -> SealedDaydream:
    """Dream, independently judge, and seal one thesis, or explain why not.

    A ``dream-again`` verdict remains inspectable and informs the next Dream,
    but only a ``build`` verdict can become Wish intent.  The Judge assumes the
    Spark route unless ``effort`` names one.
    """

    route = effort if effort is not None else "spark"
    if route not in ROUTE_BUDGETS:
        raise ContractError("daydream route budget is unknown: %r" % (route,))
    spec = manager_spec(manager_id)
    manifest, taste = resolve_inventor(inventor_id, source_root=source_root)
    selected_seed = seed if seed is not None else draw_seed()
    if not isinstance(selected_seed, DaydreamSeed):
        raise ContractError("daydream seed must be a DaydreamSeed")
    observed = _utc_moment(moment)
    created_at = observed.strftime(CREATED_AT_FORMAT)
    selected_id = (
        daydream_id if daydream_id is not None else generate_daydream_id(moment=observed)
    )
    paths = daydream_paths(manifest.inventor_id, selected_id, home=home, create=True)
    catalog_root = repository_root if repository_root is not None else source_checkout_root()
    repository_prior = load_prior_work(catalog_root)
    notebook_entries = read_notebook(paths.notebook)
    outcome_entries = read_outcomes(paths.outcomes)
    portfolio_entries = load_portfolio(
        paths.notebook.parent.parent, exclude_inventor=manifest.inventor_id
    )
    vault_summary, vault_binding = _materialize_vault(
        paths, vault_loader=vault_loader
    )
    inventor_binding = _materialize_selected_inventor(
        paths, manifest=manifest, taste=taste
    )
    write_private_bytes(
        paths.host_state / INVENTOR_BINDING_FILE_NAME,
        (canonical_json(inventor_binding) + "\n").encode("utf-8"),
        label="Daydream Inventor binding",
    )
    workspace_sha256s = _write_workspace(
        paths,
        taste=taste,
        repository_prior=repository_prior,
        notebook_entries=notebook_entries,
        portfolio_entries=portfolio_entries,
        outcome_entries=outcome_entries,
        vault_summary=vault_summary,
    )
    prompt = build_daydream_prompt(
        inventor_name=taste.name,
        inventor_id=manifest.inventor_id,
        seed=selected_seed,
        notebook_count=len(notebook_entries),
        prior_work_count=len(repository_prior),
        portfolio_count=len(portfolio_entries),
        outcome_count=len(outcome_entries),
        effort=effort,
        observed_at=created_at,
    )
    session = _native_turn(
        launcher_factory,
        spec.manager_id,
        run_root=paths.workspace,
        host_state_root=paths.host_state,
        product_id=selected_id,
        wish_sha256=_daydream_wish_sha256(
            selected_id, manifest.inventor_id, taste.sha256, selected_seed
        ),
        constitution_sha256=DAYDREAM_CONSTITUTION_SHA256,
        prompt=prompt,
        activity_observer=activity_observer,
        finalized_files=(paths.work / IDEA_FILE_NAME,),
        label="Daydream",
        launcher_kwargs={"timeout_seconds": DAYDREAM_TURN_TIMEOUT_SECONDS},
    )
    if session.get("used_web_search") is not True:
        raise DaydreamError(
            "Daydream session produced no verified live web-search event"
        )
    # The Inventor could write anything below the workspace; only a real,
    # unlinked work directory and a fresh notebook decide what gets sealed.
    _existing_real_directory(paths.workspace, label="daydream workspace")
    _existing_real_directory(paths.work, label="daydream work directory", private=False)
    _read_outcome(paths.workspace, file_name=IDEA_FILE_NAME, who="Inventor", goal="Daydream")
    idea = _read_idea(paths.work / IDEA_FILE_NAME)
    _validate_thesis_evidence(
        idea, taste=taste, observed_at=created_at, route=route
    )
    latest_entries = read_notebook(paths.notebook, limit=NOTEBOOK_LINT_LIMIT)
    _validate_learning(idea, latest_entries)
    latest_portfolio = load_portfolio(
        paths.notebook.parent.parent, exclude_inventor=manifest.inventor_id
    )
    novelty = lint_novelty(
        idea,
        (
            *repository_prior,
            *prior_work_from_notebook(latest_entries),
            *prior_work_from_portfolio(latest_portfolio),
        ),
    )
    if novelty.status != "new":
        _reject(paths, daydream_id=selected_id, created_at=created_at, idea=idea, novelty=novelty)
        raise DaydreamError("Daydream %s rejected: %s" % (selected_id, novelty.reason))
    verdict, _judge_session = judge_idea(
        paths,
        idea=idea,
        taste=taste,
        inventor_id=manifest.inventor_id,
        manager_id=spec.manager_id,
            effort=route,
        daydream_id=selected_id,
        notebook_entries=latest_entries,
        launcher_factory=launcher_factory,
        activity_observer=activity_observer,
    )
    if verdict.schema_version != 3:
        raise DaydreamError("new Judge Goals must finalize a verdict with schema_version 3")
    provenance = _build_provenance(
        route=route,
        manager=spec,
        prompt=prompt,
        idea=idea,
        workspace_sha256s=workspace_sha256s,
        inventor_binding=inventor_binding,
        vault_binding=vault_binding,
    )
    write_private_bytes(
        paths.host_state / PROVENANCE_FILE_NAME,
        (canonical_json(provenance.to_dict()) + "\n").encode("utf-8"),
        label="Daydream provenance",
    )
    sealed = SealedDaydream(
        schema_version=3,
        verdict=verdict,
        provenance=provenance,
        daydream_id=selected_id,
        inventor_id=manifest.inventor_id,
        inventor_name=taste.name,
        taste_sha256=taste.sha256,
        manager_id=spec.manager_id,
        seed=selected_seed.to_dict(),
        created_at=created_at,
        idea=idea,
        idea_sha256=idea.sha256,
        novelty=novelty,
        session=session,
        brief=render_brief(idea, inventor_name=taste.name, inventor_id=manifest.inventor_id),
    )
    write_private_bytes(
        paths.host_state / IDEA_FILE_NAME,
        (canonical_json(sealed.to_dict()) + "\n").encode("utf-8"),
        label="sealed daydream",
    )
    _remember(
        paths,
        daydream_id=selected_id,
        created_at=created_at,
        idea=idea,
        status="judged" if verdict.decision != "build" else "dreamed",
        verdict=verdict,
    )
    return sealed


def load_sealed_daydream(
    inventor_id: str, daydream_id: str, *, home: Optional[Path] = None
) -> SealedDaydream:
    """Reload one sealed idea and re-verify its identity and brief."""

    paths = daydream_paths(inventor_id, daydream_id, home=home, create=False)
    path = paths.host_state / IDEA_FILE_NAME
    try:
        payload = read_regular_bytes(
            path, maximum=MAX_SEALED_FILE_BYTES, label="sealed daydream"
        )
    except FileNotFoundError as exc:
        if (paths.host_state / REJECTED_FILE_NAME).is_file():
            raise DaydreamError(
                "daydream %s was rejected by the novelty lint and has no sealed idea"
                % daydream_id
            ) from exc
        raise DaydreamError("daydream %s has no sealed idea: %s" % (daydream_id, path)) from exc
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise DaydreamError("sealed daydream %s is not valid JSON" % daydream_id) from exc
    if not isinstance(raw, dict):
        raise DaydreamError("sealed daydream %s must be a JSON object" % daydream_id)
    try:
        sealed = SealedDaydream.parse(raw)
    except ContractError as exc:
        raise DaydreamError("sealed daydream %s is invalid: %s" % (daydream_id, exc)) from exc
    if sealed.daydream_id != daydream_id or sealed.inventor_id != inventor_id:
        raise DaydreamError("sealed daydream %s does not match its path" % daydream_id)
    return sealed


def list_daydreams(
    inventor_id: str, *, home: Optional[Path] = None
) -> tuple[NotebookEntry, ...]:
    """Return the Inventor's remembered daydreams, oldest first."""

    inventor_id = require_inventor_id(inventor_id)
    folder = _workshop_home(home) / "daydreams" / inventor_id
    if not folder.exists() and not folder.is_symlink():
        return ()
    folder = _inventor_daydreams(inventor_id, home=home, create=False)
    return read_notebook(folder / "NOTEBOOK.jsonl")


def wish_from_daydream(sealed: SealedDaydream, *, wish_id: Optional[str] = None) -> Wish:
    """Seal a liked idea as the Wish that keys one product run."""

    if not isinstance(sealed, SealedDaydream):
        raise ContractError("wish_from_daydream requires a SealedDaydream")
    if sealed.schema_version >= 2 and (
        sealed.verdict is None or sealed.verdict.decision != "build"
    ):
        raise ContractError(
            "only a Judge-accepted Daydream can become Wish intent"
        )
    context = {
        "source": WISH_CONTEXT_SOURCE,
        "inventor_id": sealed.inventor_id,
        "daydream_id": sealed.daydream_id,
        "daydream_sha256": sealed.sha256,
        "idea_sha256": sealed.idea_sha256,
        "title": sealed.idea.title,
    }
    if sealed.provenance is not None:
        context.update(
            {
                "provenance_sha256": sealed.provenance.sha256,
                "route": sealed.provenance.route,
            }
        )
    return Wish.create(
        wish_id if wish_id is not None else generate_wish_id(),
        sealed.brief,
        context=context,
    )


__all__ = [
    "DAYDREAM_REJECTION_KIND",
    "DAYDREAM_TURN_TIMEOUT_SECONDS",
    "DaydreamPaths",
    "DAYDREAM_OUTCOME_KIND",
    "FINALIZER_FILE_NAME",
    "SCHEMA_FILE_NAME",
    "IDEA_FILE_NAME",
    "INVENTOR_BINDING_FILE_NAME",
    "JUDGE_TURN_TIMEOUT_SECONDS",
    "OUTCOME_FILE_NAME",
    "PROVENANCE_FILE_NAME",
    "VERDICT_FILE_NAME",
    "judge_idea",
    "finalizer_bytes",
    "schema_bytes",
    "REJECTED_FILE_NAME",
    "WISH_CONTEXT_SOURCE",
    "VAULT_BINDING_FILE_NAME",
    "daydream_paths",
    "list_daydreams",
    "load_sealed_daydream",
    "resolve_inventor",
    "run_daydream",
    "wish_from_daydream",
]
