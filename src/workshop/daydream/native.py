"""Run one Daydream: private workspace, one native Manager turn, lint, seal."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from workshop.contributors import (
    InventorManifest,
    Taste,
    discover_inventors,
    inventor_collection,
    load_taste,
    validate_inventor_collection,
)
from workshop.daydream._files import read_regular_bytes, write_private_bytes
from workshop.daydream.catalog import (
    PriorWork,
    lint_novelty,
    load_repository_prior_work,
    render_prior_work_markdown,
    source_checkout_root,
)
from workshop.daydream.contracts import (
    Verdict,
    CREATED_AT_FORMAT,
    DaydreamError,
    Idea,
    NoveltyReport,
    SealedDaydream,
    canonical_json,
    generate_daydream_id,
    render_brief,
    require_daydream_id,
    require_inventor_id,
)
from workshop.daydream.notebook import (
    NotebookEntry,
    append_notebook_entry,
    prior_work_from_notebook,
    read_notebook,
    render_notebook_markdown,
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
from workshop.daydream.seeds import DaydreamSeed, draw_seed
from workshop._validation import require_sha256
from workshop.errors import ContractError
from workshop.runtime.codex import CodexInvocationError, CodexRecoverableInvocationError
from workshop.runtime.managers import (
    NativeManagerRecoverableError,
    DEFAULT_MANAGER_ID,
    NativeManagerInvocationError,
    manager_launcher,
    manager_spec,
)
from workshop.runtime.package_data import default_workshop_home
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
MAX_IDEA_FILE_BYTES = 64 * 1024
MAX_SEALED_FILE_BYTES = 256 * 1024
MAX_ERROR_CHARS = 1_000
NOTEBOOK_LINT_LIMIT = 1_000_000
WISH_CONTEXT_SOURCE = "workshop-daydream"


@dataclass(frozen=True)
class DaydreamPaths:
    """One private daydream container and the Inventor's shared notebook."""

    container: Path
    workspace: Path
    work: Path
    host_state: Path
    notebook: Path


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


def _write_workspace(
    paths: DaydreamPaths,
    *,
    taste: Taste,
    repository_prior: Sequence[PriorWork],
    notebook_entries: Sequence[NotebookEntry],
) -> None:
    files = (
        ("TASTE.md", taste.content.encode("utf-8")),
        ("PRIOR-WORK.md", render_prior_work_markdown(repository_prior).encode("utf-8")),
        (
            "PORTFOLIO.md",
            render_prior_work_markdown(repository_prior)
            .replace("# Prior work", "# Workshop portfolio", 1)
            .encode("utf-8"),
        ),
        ("NOTEBOOK.md", render_notebook_markdown(notebook_entries).encode("utf-8")),
        (
            "VAULT.md",
            b"# Design Vault advisory context\n\n(no Vault snapshot available yet)\n",
        ),
        # The constitution doubles as AGENTS.md so the Manager runtime loads it
        # the same way it loads a product run's constitution.
        ("AGENTS.md", DAYDREAM_CONSTITUTION.encode("utf-8")),
        (FINALIZER_FILE_NAME, finalizer_bytes()),
        (SCHEMA_FILE_NAME, schema_bytes()),
        (PRODUCT_RUN_ROOT_MARKER, PRODUCT_RUN_ROOT_MARKER_BYTES),
    )
    for name, payload in files:
        write_private_bytes(paths.workspace / name, payload, label="daydream %s" % name)


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
    if verdict.schema_version == 2 and (
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
    paths: DaydreamPaths, *, daydream_id: str, created_at: str, idea: Idea, status: str
) -> None:
    append_notebook_entry(
        paths.notebook,
        NotebookEntry(
            daydream_id=daydream_id,
            created_at=created_at,
            title=idea.title,
            one_liner=idea.one_liner,
            idea_sha256=idea.sha256,
            status=status,
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
    _remember(paths, daydream_id=daydream_id, created_at=created_at, idea=idea, status="rejected")


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
    judge: bool = True,
) -> SealedDaydream:
    """Let one Inventor dream one new idea, judge it, and seal it, or explain why not.

    With ``judge`` the idea is handed to the independent Judge Goal before it
    is sealed; a ``dream-again`` verdict is sealed too, so it can be inspected
    or built on purpose, but it is remembered as ``judged`` and callers skip
    the build.  The judge assumes the Spark route unless ``effort`` names one.
    """

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
    repository_prior = load_repository_prior_work(catalog_root)
    notebook_entries = read_notebook(paths.notebook)
    _write_workspace(
        paths,
        taste=taste,
        repository_prior=repository_prior,
        notebook_entries=notebook_entries,
    )
    prompt = build_daydream_prompt(
        inventor_name=taste.name,
        inventor_id=manifest.inventor_id,
        seed=selected_seed,
        notebook_count=len(notebook_entries),
        prior_work_count=len(repository_prior),
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
    # The Inventor could write anything below the workspace; only a real,
    # unlinked work directory and a fresh notebook decide what gets sealed.
    _existing_real_directory(paths.workspace, label="daydream workspace")
    _existing_real_directory(paths.work, label="daydream work directory", private=False)
    _read_outcome(paths.workspace, file_name=IDEA_FILE_NAME, who="Inventor", goal="Daydream")
    idea = _read_idea(paths.work / IDEA_FILE_NAME)
    if idea.schema_version != 2:
        raise DaydreamError("new Daydream Goals must finalize an idea with schema_version 2")
    latest_entries = read_notebook(paths.notebook, limit=NOTEBOOK_LINT_LIMIT)
    novelty = lint_novelty(
        idea, (*repository_prior, *prior_work_from_notebook(latest_entries))
    )
    if novelty.status != "new":
        _reject(paths, daydream_id=selected_id, created_at=created_at, idea=idea, novelty=novelty)
        raise DaydreamError("Daydream %s rejected: %s" % (selected_id, novelty.reason))
    verdict: Optional[Verdict] = None
    if judge:
        verdict, _judge_session = judge_idea(
            paths,
            idea=idea,
            taste=taste,
            inventor_id=manifest.inventor_id,
            manager_id=spec.manager_id,
            effort=effort if effort is not None else "spark",
            daydream_id=selected_id,
            launcher_factory=launcher_factory,
            activity_observer=activity_observer,
        )
        if verdict.schema_version != 2:
            raise DaydreamError("new Judge Goals must finalize a verdict with schema_version 2")
    sealed = SealedDaydream(
        verdict=verdict,
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
        status="judged" if verdict is not None and verdict.decision != "build" else "dreamed",
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
    return Wish.create(
        wish_id if wish_id is not None else generate_wish_id(),
        sealed.brief,
        context={
            "source": WISH_CONTEXT_SOURCE,
            "inventor_id": sealed.inventor_id,
            "daydream_id": sealed.daydream_id,
            "idea_sha256": sealed.idea_sha256,
            "title": sealed.idea.title,
        },
    )


__all__ = [
    "DAYDREAM_REJECTION_KIND",
    "DAYDREAM_TURN_TIMEOUT_SECONDS",
    "DaydreamPaths",
    "DAYDREAM_OUTCOME_KIND",
    "FINALIZER_FILE_NAME",
    "SCHEMA_FILE_NAME",
    "IDEA_FILE_NAME",
    "JUDGE_TURN_TIMEOUT_SECONDS",
    "OUTCOME_FILE_NAME",
    "VERDICT_FILE_NAME",
    "judge_idea",
    "finalizer_bytes",
    "schema_bytes",
    "REJECTED_FILE_NAME",
    "WISH_CONTEXT_SOURCE",
    "daydream_paths",
    "list_daydreams",
    "load_sealed_daydream",
    "resolve_inventor",
    "run_daydream",
    "wish_from_daydream",
]
