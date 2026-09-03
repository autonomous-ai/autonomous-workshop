"""Lean user CLI for the native-agent Autonomous Workshop."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import threading
import time
import unicodedata
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, TextIO

from workshop.artifacts.core import MAX_PACK_BYTES
from workshop.artifacts.pack import bundle_artifact, plan_artifact, seal_artifact
from workshop.artifacts.schema_registry import discover_schemas, resolve_schemas_root
from workshop.contributors import (
    create_inventor,
    discover_inventors,
    inventor_collection,
    load_manifest,
    load_taste,
    load_taste_header,
    manifests_for_target,
    prepare_inventor_collection,
    validate_contribution,
    validate_inventor_collection,
)
from workshop.daydream import (
    DEFAULT_MAX_CONSECUTIVE_FAILURES,
    DaydreamError,
    acquire_loop,
    load_sealed_daydream,
    request_stop,
    run_daydream,
    wish_from_daydream,
)
from workshop.errors import WorkshopError
from workshop.invent.gamevault import default_client as default_gamevault_client
from workshop.invent.vault import Vault, VaultError
from workshop.make.skill_registry import (
    discover_skills,
    fingerprint_skill_tree,
    resolve_skills_root,
)
from workshop.runtime.agent_assets import product_run_agent_assets
from workshop.runtime.execution import codex_subprocess_environment
from workshop.runtime.credentials import (
    factory_credential_environment,
    factory_service_credential_environment,
)
from workshop.runtime.codex import (
    MINIMUM_CODEX_NATIVE_RUNTIME_VERSION,
    codex_supports_native_workshop,
)
from workshop.runtime.claude import claude_supports_native_workshop
from workshop.runtime.grok import grok_supports_native_workshop
from workshop.runtime.managers import (
    DEFAULT_MANAGER_ID,
    SUPPORTED_MANAGER_IDS,
    manager_spec,
)
from workshop.runtime.package_data import (
    default_workshop_home,
    packaged_inventors_root,
    product_run_domain_skill_roots,
)
from workshop.runtime.progress import WishRunTimingEvent
from workshop.wish import Wish, generate_wish_id
from workshop.workflow import native_run_status, resume_native_run, start_native_run
from workshop.workflow.effort import (
    DEFAULT_WORKSHOP_EFFORT,
    WORKSHOP_EFFORTS,
    workshop_effort,
)


_INVENTOR_ID_PART = re.compile(r"[^a-z0-9]+")
_LIVE_ACTIVE_INTERVAL_SECONDS = 2.0
_LIVE_RUNNING_INTERVAL_SECONDS = 30.0
_LIVE_CHURN_ACTIVITY = frozenset(("reasoning", "tool", "subagent"))
_LIVE_ACTIVITY_MESSAGES = {
    "starting": "Native Codex: starting the current stage.",
    "running": "Native Codex: process is still running.",
    "reasoning": "Native Codex: reasoning about the current stage.",
    "tool": "Native Codex: using a tool for the current stage.",
    "subagent": "Native Codex: coordinating a subagent.",
    "finalizing": "Native Codex: reported progress for the current stage.",
    "completed": "Native Codex: turn complete; Workshop is verifying it.",
    "failed": (
        "Native Codex: turn ended; Workshop is checking for a valid stage proposal."
    ),
}


class _LiveWishProgress:
    """Render bounded Wish timing and native activity without log churn."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._lock = threading.Lock()
        self._last_non_running: Optional[str] = None
        self._last_active_at: Optional[float] = None
        self._last_running_at: Optional[float] = None

    def activity(self, activity: str) -> None:
        message = _LIVE_ACTIVITY_MESSAGES.get(activity)
        if message is None:
            return
        now = time.monotonic()
        with self._lock:
            if activity == "running":
                if (
                    self._last_running_at is not None
                    and now - self._last_running_at
                    < _LIVE_RUNNING_INTERVAL_SECONDS
                ):
                    return
                self._last_running_at = now
            else:
                if activity == self._last_non_running:
                    return
                if activity in _LIVE_CHURN_ACTIVITY:
                    if (
                        self._last_active_at is not None
                        and now - self._last_active_at
                        < _LIVE_ACTIVE_INTERVAL_SECONDS
                    ):
                        return
                    self._last_active_at = now
                self._last_non_running = activity
            print(message, file=self._stream, flush=True)

    def timing(self, event: WishRunTimingEvent) -> None:
        fields = [
            "[%s]" % event.observed_at,
            "wish=%s" % event.product_id,
            "stage=%s" % event.stage,
            "operation=%s" % event.operation,
            "state=%s" % event.state,
        ]
        if event.elapsed_ms is not None:
            fields.append("elapsed_ms=%d" % event.elapsed_ms)
        with self._lock:
            print(" ".join(fields), file=self._stream, flush=True)


def _shell_command(*parts: Any) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _inventor_id_from_taste(path: Path) -> str:
    requested = Path(path)
    if requested.name != "TASTE.md":
        raise WorkshopError(
            "--taste must name a file called TASTE.md; rename it so its identity is explicit"
        )
    header = load_taste_header(requested.parent)
    ascii_name = unicodedata.normalize("NFKD", header.name).encode(
        "ascii", "ignore"
    ).decode("ascii")
    # ``create_inventor`` appends ``-inventor`` to form a bounded Codex skill.
    inventor_id = _INVENTOR_ID_PART.sub("-", ascii_name.lower()).strip("-")[:54]
    inventor_id = inventor_id.rstrip("-")
    if len(inventor_id) < 2 or not inventor_id[0].isalpha():
        raise WorkshopError(
            "the Taste name cannot produce a safe inventor id; provide one explicitly"
        )
    return inventor_id


def _default_inventor_name(inventor_id: str) -> str:
    return " ".join(part.capitalize() for part in inventor_id.split("-"))


def _looks_like_inventor_source(root: Path) -> bool:
    try:
        resolved = root.resolve(strict=True)
    except OSError:
        return False
    collection = resolved / "inventors" if (resolved / "inventors").is_dir() else resolved
    if collection.is_symlink() or not collection.is_dir():
        return False
    try:
        return any(
            child.is_dir()
            and not child.is_symlink()
            and (child / "inventor.json").is_file()
            and not (child / "inventor.json").is_symlink()
            and (child / "TASTE.md").is_file()
            and not (child / "TASTE.md").is_symlink()
            for child in collection.iterdir()
        )
    except OSError:
        return False


def _inventor_source_root(requested: Optional[Path]) -> Path:
    """Resolve read-only Inventor sources without creating installed state."""

    if requested is not None:
        candidate = Path(requested).resolve(strict=True)
        if not _looks_like_inventor_source(candidate):
            raise WorkshopError("source has no native Inventor bundles: %s" % candidate)
        return candidate

    source_root = Path(__file__).resolve().parents[2]
    if _looks_like_inventor_source(source_root):
        return source_root
    packaged = packaged_inventors_root()
    if packaged is not None and _looks_like_inventor_source(packaged):
        return packaged
    raise WorkshopError(
        "cannot find Inventor sources; provide --root with a Workshop checkout"
    )


def _validated_inventors(root: Path):
    collection = inventor_collection(root)
    validate_inventor_collection(collection)
    return tuple(discover_inventors(collection))


def _inventor_problems(manifests) -> list[str]:
    return [
        problem
        for manifest in manifests
        for problem in validate_contribution(manifest)
    ]


def _native_exit_code(receipt: Mapping[str, Any], *, strict: bool) -> int:
    status = receipt.get("status")
    if status == "failed":
        return 1
    if strict and status == "waiting":
        return 1
    return 0


def _print_native_receipt(receipt: Mapping[str, Any], *, verb: str) -> None:
    product_id = receipt.get("product_id", "unknown")
    status = receipt.get("status", "unknown")
    stage = str(receipt.get("stage", "unknown")).title()
    print("Wish: %s" % product_id)
    manager_id = receipt.get("manager")
    if isinstance(manager_id, str) and manager_id:
        print("Manager: %s" % manager_spec(manager_id).display_name)
    print("%s: %s at %s" % (verb, status, stage))
    progress = receipt.get("progress")
    if isinstance(progress, Mapping) and progress.get("status") == "available":
        stage_attempt = progress.get("stage_attempt")
        if isinstance(stage_attempt, Mapping):
            attempt_stage = str(stage_attempt.get("stage", "unknown")).title()
            attempt_number = stage_attempt.get("number", "?")
            activity = progress.get("activity", "unknown")
            elapsed = progress.get("elapsed_seconds", 0)
            last_activity = progress.get("last_activity_at", "unknown")
            print(
                "Progress: %s attempt %s — %s (%ss; last activity %s)"
                % (
                    attempt_stage,
                    attempt_number,
                    activity,
                    elapsed,
                    last_activity,
                )
            )
    rounds = receipt.get("rounds")
    if isinstance(rounds, (list, tuple)):
        for entry in rounds:
            if not isinstance(entry, Mapping):
                continue
            median = entry.get("score_median")
            if isinstance(median, Mapping):
                spread = entry.get("score_spread") or {}
                ambiguous = sorted(
                    dim
                    for dim, value in spread.items()
                    if isinstance(value, (int, float)) and value >= 3
                )
                scores = " ".join(
                    "%s %g" % (dim, value) for dim, value in sorted(median.items())
                )
                print(
                    "Round %s: %s — %s%s"
                    % (
                        entry.get("round", "?"),
                        entry.get("verdict", "?"),
                        scores,
                        " (readers disagree on %s)" % ", ".join(ambiguous) if ambiguous else "",
                    )
                )
            else:
                print("Round %s: %s — unscored" % (entry.get("round", "?"), entry.get("verdict", "?")))
    publication = receipt.get("publication")
    publication_reason = None
    if isinstance(publication, Mapping):
        page_url = publication.get("page_url")
        if isinstance(page_url, str) and page_url:
            print("Product page: %s (%s)" % (page_url, publication.get("status")))
        else:
            print("Product page: %s" % publication.get("status", "not-created"))
        manual_url = publication.get("manual_url")
        if isinstance(manual_url, str) and manual_url:
            print("Manual PDF: %s (hash-verified)" % manual_url)
        candidate_reason = publication.get("reason")
        if (
            isinstance(candidate_reason, str)
            and candidate_reason
            and (
                publication.get("requested") is True
                or publication.get("status") in ("unknown", "unavailable")
            )
        ):
            publication_reason = candidate_reason
            print("Publication note: %s" % candidate_reason)
    needs = receipt.get("needs")
    if isinstance(needs, (list, tuple)):
        for need in needs:
            if (
                isinstance(need, str)
                and need
                and need != publication_reason
            ):
                print("Need: %s" % need)
    print("Track: %s" % _shell_command("workshop", "status", product_id))
    if status == "waiting":
        print("Resume: %s" % _shell_command("workshop", "resume", product_id))


DEFAULT_MAX_ROUNDS = 4
MAX_ROUND_BUDGET = 100


def _round_budget(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("round budget must be an integer")
    if not 1 <= parsed <= MAX_ROUND_BUDGET:
        raise argparse.ArgumentTypeError(
            "round budget must be between 1 and %d" % MAX_ROUND_BUDGET
        )
    return parsed


def _start_run(
    wish: Wish,
    *,
    effort,
    manager,
    github: bool,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    progress: TextIO,
    live_progress: "_LiveWishProgress",
) -> Mapping[str, Any]:
    """Announce and start one native run; callers print the receipt."""

    print("Wish: %s" % wish.product_id, file=progress, flush=True)
    print(
        "Effort: %s — %s" % (effort.title, effort.description),
        file=progress,
        flush=True,
    )
    print(
        "Manager: %s%s"
        % (
            manager.display_name,
            " (experimental)" if manager.experimental else "",
        ),
        file=progress,
        flush=True,
    )
    print(
        "Starting one native %s session for %s..."
        % (manager.display_name, effort.enabled_stages[0].title()),
        file=progress,
        flush=True,
    )
    return start_native_run(
        wish,
        effort=effort.name,
        manager_id=manager.manager_id,
        max_rounds=max_rounds,
        github_publish_requested=github,
        activity_observer=live_progress.activity,
        timing_observer=live_progress.timing,
    )


def _wish(args: argparse.Namespace) -> int:
    effort = workshop_effort(args.effort)
    wish = Wish.create(
        generate_wish_id(),
        " ".join(args.objective),
        context={"source": "workshop-cli"},
    )
    progress = sys.stderr if args.json else sys.stdout
    live_progress = _LiveWishProgress(progress)
    manager = manager_spec(args.manager)
    receipt = _start_run(
        wish,
        effort=effort,
        manager=manager,
        github=args.github,
        max_rounds=args.max_rounds,
        progress=progress,
        live_progress=live_progress,
    )
    if args.json:
        _print_json(receipt)
    else:
        _print_native_receipt(receipt, verb="Run")
    return _native_exit_code(receipt, strict=args.strict)


def _print_daydream_card(sealed, *, stream: TextIO, offer_build: bool) -> None:
    idea = sealed.idea
    lines = [
        "Daydream: %s" % sealed.daydream_id,
        "Inventor: %s (%s)" % (sealed.inventor_name, sealed.inventor_id),
        "Title: %s" % idea.title,
        "In one line: %s" % idea.one_liner,
    ]
    if idea.held_form is not None:
        lines.append("What it looks like: %s" % idea.held_form)
    lines += [
        "What you do: %s" % idea.what_you_do,
        "What happens: %s" % idea.what_happens,
        "Why it is new: %s" % idea.why_it_is_new,
        "Closest existing things: %s"
        % "; ".join(
            "%s (%s)" % (entry.name, entry.how_this_differs)
            for entry in idea.prior_art
        ),
        "Taste fit: honors %s; steers clear of %s"
        % (
            "; ".join(idea.taste_fit.honors),
            "; ".join(idea.taste_fit.steers_clear_of),
        ),
        "Printed parts: %d" % idea.parts_estimate,
    ]
    nearest = ", ".join(
        "%s %.2f" % (neighbor.title, neighbor.similarity)
        for neighbor in sealed.novelty.nearest
    )
    lines.append(
        "Novelty lint: %s (%s)"
        % (
            sealed.novelty.status,
            "nearest: %s" % nearest if nearest else sealed.novelty.reason,
        )
    )
    if offer_build:
        lines.append(
            "Build it: %s"
            % _shell_command(
                "workshop",
                "start",
                sealed.inventor_id,
                "--idea",
                sealed.daydream_id,
            )
        )
    for line in lines:
        print(line, file=stream, flush=True)


def _dream_or_load(
    args: argparse.Namespace,
    *,
    root: Path,
    manager,
    progress: TextIO,
    live_progress: "_LiveWishProgress",
    effort: Optional[str],
):
    if args.idea is not None:
        sealed = load_sealed_daydream(args.inventor, args.idea)
        print("Daydream: %s (saved idea)" % sealed.daydream_id, file=progress, flush=True)
        return sealed
    print("Inventor: %s" % args.inventor, file=progress, flush=True)
    print(
        "Manager: %s%s"
        % (
            manager.display_name,
            " (experimental)" if manager.experimental else "",
        ),
        file=progress,
        flush=True,
    )
    print(
        "Daydreaming one brand-new idea that fits %s's Taste..." % args.inventor,
        file=progress,
        flush=True,
    )
    return run_daydream(
        args.inventor,
        source_root=root,
        manager_id=manager.manager_id,
        activity_observer=live_progress.activity,
        effort=effort,
    )


def _daydream(args: argparse.Namespace) -> int:
    root = _inventor_source_root(args.root)
    manager = manager_spec(args.manager)
    progress = sys.stderr if args.json else sys.stdout
    live_progress = _LiveWishProgress(progress)
    sealed = _dream_or_load(
        args,
        root=root,
        manager=manager,
        progress=progress,
        live_progress=live_progress,
        effort=None,
    )
    if args.json:
        _print_json({"daydream": sealed.to_dict()})
    else:
        _print_daydream_card(sealed, stream=progress, offer_build=True)
    return 0


def _start(args: argparse.Namespace) -> int:
    """Dream and build until stopped; ``--once`` or ``--idea`` does one idea."""

    root = _inventor_source_root(args.root)
    manager = manager_spec(args.manager)
    effort = workshop_effort(args.effort)
    progress = sys.stderr if args.json else sys.stdout
    live_progress = _LiveWishProgress(progress)
    once = args.once or args.idea is not None
    if args.max_ideas is not None and args.max_ideas < 1:
        raise WorkshopError("--max-ideas must be at least 1")
    if args.max_failures < 1:
        raise WorkshopError("--max-failures must be at least 1")
    lease = acquire_loop(args.inventor)
    if not once:
        print(
            "Loop: %s dreams and builds until you stop it (Ctrl-C, or "
            "%s from another terminal)."
            % (args.inventor, _shell_command("workshop", "stop", args.inventor)),
            file=progress,
            flush=True,
        )
    ideas = builds = published = 0
    failures = 0
    exit_code = 0
    reason = "finished"
    try:
        while True:
            if lease.stop_requested():
                reason = "stopped by workshop stop"
                break
            if not once and ideas:
                print("", file=progress, flush=True)
            try:
                sealed = _dream_or_load(
                    args,
                    root=root,
                    manager=manager,
                    progress=progress,
                    live_progress=live_progress,
                    effort=effort.name,
                )
            except DaydreamError as exc:
                if once:
                    raise
                failures += 1
                lease.update(consecutive_failures=failures)
                print("Daydream failed: %s" % exc, file=progress, flush=True)
                if failures >= args.max_failures:
                    reason = "%d consecutive failures" % failures
                    exit_code = 1
                    break
                continue
            ideas += 1
            lease.update(ideas=ideas, last_daydream_id=sealed.daydream_id)
            if not args.json:
                _print_daydream_card(sealed, stream=progress, offer_build=False)
            wish = wish_from_daydream(sealed)
            print("Sealing the idea as this run's brief.", file=progress, flush=True)
            receipt = _start_run(
                wish,
                effort=effort,
                manager=manager,
                github=args.github,
                progress=progress,
                live_progress=live_progress,
            )
            builds += 1
            publication = receipt.get("publication")
            if isinstance(publication, Mapping) and publication.get("status") == "public":
                published += 1
            if receipt.get("status") in ("failed", "waiting"):
                failures += 1
            else:
                failures = 0
            lease.update(
                builds=builds,
                published=published,
                consecutive_failures=failures,
                last_wish_id=wish.product_id,
            )
            if args.json:
                print(
                    json.dumps(
                        {"daydream": sealed.to_dict(), "run": receipt},
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
            else:
                _print_native_receipt(receipt, verb="Run")
            if once:
                exit_code = _native_exit_code(receipt, strict=args.strict)
                break
            if args.max_ideas is not None and ideas >= args.max_ideas:
                reason = "reached --max-ideas %d" % args.max_ideas
                break
            if failures >= args.max_failures:
                reason = "%d consecutive failures" % failures
                exit_code = 1
                break
            if lease.stop_requested():
                reason = "stopped by workshop stop"
                break
    except KeyboardInterrupt:
        reason = "stopped by Ctrl-C"
        exit_code = 130
    finally:
        state = lease.release(reason=reason)
    if not once or exit_code == 130:
        print(
            "Loop stopped (%s). Ideas: %d. Builds: %d. Published: %d."
            % (reason, state.ideas, state.builds, state.published),
            file=progress,
            flush=True,
        )
        if state.last_wish_id and exit_code == 130:
            print(
                "Last run: %s" % _shell_command("workshop", "status", state.last_wish_id),
                file=progress,
                flush=True,
            )
    return exit_code


def _stop(args: argparse.Namespace) -> int:
    state = request_stop(args.inventor, now=args.now)
    if args.now:
        print(
            "Interrupting the daydream loop for %s (pid %d) now; its current run "
            "stays resumable." % (args.inventor, state.pid)
        )
    else:
        print(
            "Stop requested for %s (pid %d): the loop ends after its current step. "
            "Use --now to interrupt it." % (args.inventor, state.pid)
        )
    print(
        "So far: %d idea(s), %d build(s), %d published."
        % (state.ideas, state.builds, state.published)
    )
    return 0


def _status(args: argparse.Namespace) -> int:
    receipt = native_run_status(args.product_id)
    if args.json:
        _print_json(receipt)
    else:
        _print_native_receipt(receipt, verb="Status")
    return 0


def _resume(args: argparse.Namespace) -> int:
    progress = sys.stderr if args.json else sys.stdout
    live_progress = _LiveWishProgress(progress)
    print(
        "Resuming the exact native Codex session for %s..." % args.product_id,
        file=progress,
        flush=True,
    )
    receipt = resume_native_run(
        args.product_id,
        activity_observer=live_progress.activity,
        timing_observer=live_progress.timing,
    )
    if args.json:
        _print_json(receipt)
    else:
        _print_native_receipt(receipt, verb="Resume")
    return _native_exit_code(receipt, strict=args.strict)


def _check_record(
    name: str,
    status: str,
    detail: str,
    *,
    next_step: Optional[str] = None,
) -> dict[str, str]:
    record = {"name": name, "status": status, "detail": detail}
    if next_step:
        record["next"] = next_step
    return record


def _doctor_catalog(root: Path) -> dict[str, str]:
    try:
        inventors = _validated_inventors(root)
    except (OSError, ValueError, WorkshopError) as exc:
        return _check_record(
            "inventor-catalog",
            "needs-attention",
            str(exc),
            next_step="Repair the schema-v8 Inventor bundles and their declared skill hashes.",
        )
    return _check_record(
        "inventor-catalog",
        "ready",
        "%d native Inventor bundle(s) validated statically" % len(inventors),
    )


def _doctor_codex() -> dict[str, str]:
    binary = os.environ.get("WORKSHOP_CODEX_BIN") or shutil.which("codex")
    if not binary:
        return _check_record(
            "codex",
            "needs-attention",
            "Codex CLI is not installed or on PATH.",
            next_step="Install Codex CLI, then run 'codex login'.",
        )
    environment = codex_subprocess_environment(os.environ)
    try:
        version = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError):
        version = None
    if version is None or version.returncode != 0:
        return _check_record(
            "codex",
            "needs-attention",
            "The configured Codex CLI command could not run.",
            next_step="Check WORKSHOP_CODEX_BIN and the Codex installation.",
        )
    output = version.stdout if isinstance(version.stdout, str) else ""
    version_match = re.search(
        r"\d+(?:\.\d+){2}(?:[-+][A-Za-z0-9.-]+)?", output
    )
    cli_version = version_match.group(0) if version_match else ""
    if not codex_supports_native_workshop(cli_version):
        minimum = ".".join(
            str(part) for part in MINIMUM_CODEX_NATIVE_RUNTIME_VERSION
        )
        return _check_record(
            "codex",
            "needs-attention",
            "The Codex CLI is too old for Workshop goals, subagents, and isolation.",
            next_step="Upgrade Codex CLI to %s or newer." % minimum,
        )
    try:
        login = subprocess.run(
            [binary, "login", "status"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError):
        login = None
    if login is None or login.returncode != 0:
        return _check_record(
            "codex",
            "needs-attention",
            "Codex CLI is installed but is not signed in.",
            next_step="Run 'codex login'; credentials remain owned by Codex.",
        )
    return _check_record("codex", "ready", "Codex CLI is installed and signed in.")


def _doctor_agent_assets() -> dict[str, str]:
    try:
        assets = product_run_agent_assets()
        roots = product_run_domain_skill_roots()
        fingerprints = {
            name: fingerprint_skill_tree(root) for name, root in roots.items()
        }
        verifier = roots["cad"] / "scripts" / "verify_project"
        identity = verifier.lstat()
        if (
            verifier.is_symlink()
            or not stat.S_ISREG(identity.st_mode)
            or not identity.st_mode & stat.S_IXUSR
        ):
            raise WorkshopError("materialized CAD verifier is not a regular executable")
        if not assets.constitution.is_file() or not assets.skill_root.is_dir():
            raise WorkshopError("product-run instructions are incomplete")
    except (KeyError, OSError, ValueError, WorkshopError) as exc:
        return _check_record(
            "agent-assets",
            "needs-attention",
            str(exc),
            next_step="Repair or reinstall the packaged product-run skills.",
        )
    return _check_record(
        "agent-assets",
        "ready",
        "Product-run constitution, workflow skill, CAD verifier, and %d domain skill(s) validated"
        % len(fingerprints),
    )


def _doctor_factory() -> dict[str, str]:
    try:
        credential_environment = factory_credential_environment()
        service_environment = factory_service_credential_environment(
            credential_environment
        )
    except WorkshopError as exc:
        return _check_record(
            "factory-credentials",
            "needs-attention",
            str(exc),
            next_step=(
                "Repair the private $WORKSHOP_HOME/credentials/factory.env "
                "file or configure a complete host environment pair."
            ),
        )
    password = bool(service_environment.get("FACTORY_PASSWORD"))
    username = bool(service_environment.get("FACTORY_USERNAME"))
    legacy_scoped_username = any(
        name
        for name, value in credential_environment.items()
        if name.startswith("FACTORY_")
        and name.endswith("_USERNAME")
        and name != "FACTORY_USERNAME"
        and bool(value)
    )
    if username and password:
        if legacy_scoped_username:
            return _check_record(
                "factory-credentials",
                "ready",
                (
                    "One legacy Factory username is available as Workshop's "
                    "host-only service account for every Inventor."
                ),
                next_step=(
                    "Rename the legacy scoped username variable to "
                    "FACTORY_USERNAME; its old scope no longer grants or limits "
                    "publication authority."
                ),
            )
        return _check_record(
            "factory-credentials",
            "ready",
            (
                "One complete host-only Workshop Factory service-account pair "
                "is available for every Inventor."
            ),
        )
    if not username and not password:
        return _check_record(
            "factory-credentials",
            "needs-attention",
            (
                "Factory credentials are not configured; Release requires public "
                "Factory publication."
            ),
            next_step=(
                "Configure the Workshop service account as FACTORY_USERNAME and "
                "FACTORY_PASSWORD in the private "
                "$WORKSHOP_HOME/credentials/factory.env file; Wish users do not "
                "supply Factory credentials."
            ),
        )
    return _check_record(
        "factory-credentials",
        "needs-attention",
        "Workshop's Factory service-account credentials are only partially configured.",
        next_step=(
            "Configure FACTORY_USERNAME and FACTORY_PASSWORD together in the "
            "host environment."
        ),
    )


def _doctor_optional_cli(
    name: str,
    *,
    binary_env: str,
    binary_name: str,
    supports,
    label: str,
) -> dict[str, str]:
    binary = os.environ.get(binary_env) or shutil.which(binary_name)
    if not binary:
        return _check_record(
            name,
            "skipped",
            "%s is not installed; Codex remains the default Manager." % label,
        )
    try:
        version = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=codex_subprocess_environment(os.environ),
        )
    except (OSError, subprocess.SubprocessError):
        return _check_record(
            name,
            "needs-attention",
            "The configured %s command could not run." % label,
            next_step="Check %s and the %s installation." % (binary_env, label),
        )
    output = version.stdout if isinstance(version.stdout, str) else ""
    if version.returncode != 0 or not supports(output):
        return _check_record(
            name,
            "needs-attention",
            "%s is installed but is not a Workshop-supported native Manager." % label,
            next_step="Upgrade %s, or keep using --manager codex." % label,
        )
    return _check_record(
        name,
        "ready",
        "%s is available as an experimental Manager via --manager %s."
        % (label, name),
    )


def _doctor(args: argparse.Namespace) -> int:
    root = _inventor_source_root(args.root)
    required = [
        _doctor_catalog(root),
        _doctor_codex(),
        _doctor_agent_assets(),
        _doctor_factory(),
    ]
    checks = [
        *required,
        _doctor_optional_cli(
            "claude",
            binary_env="WORKSHOP_CLAUDE_BIN",
            binary_name="claude",
            supports=claude_supports_native_workshop,
            label="Claude Code",
        ),
        _doctor_optional_cli(
            "grok",
            binary_env="WORKSHOP_GROK_BIN",
            binary_name="grok",
            supports=grok_supports_native_workshop,
            label="Grok Build",
        ),
    ]
    status = (
        "ready"
        if all(item["status"] == "ready" for item in required)
        else "needs-attention"
    )
    receipt = {
        "schema_version": 1,
        "kind": "workshop-doctor",
        "status": status,
        "root": str(root),
        "checks": checks,
    }
    if args.json:
        _print_json(receipt)
    else:
        for item in checks:
            print("%-21s %s — %s" % (item["name"], item["status"], item["detail"]))
            if item.get("next"):
                print("  Next: %s" % item["next"])
        print("Workshop: %s" % status)
    return 0 if status == "ready" else 1


def _inventors(args: argparse.Namespace) -> int:
    root = _inventor_source_root(args.root)
    manifests = _validated_inventors(root)
    records = []
    for manifest in manifests:
        header = load_taste_header(manifest.path.parent)
        taste = load_taste(manifest.path.parent)
        records.append(
            {
                "id": manifest.inventor_id,
                "status": manifest.status,
                "name": header.name,
                "description": header.description,
                "taste_sha256": taste.sha256,
                "skills": [extension.name for extension in manifest.extensions],
            }
        )
    if args.json:
        _print_json(records)
    else:
        for record in records:
            print(
                "%-12s %-13s %-20s %s"
                % (
                    record["id"],
                    record["status"],
                    record["name"],
                    record["description"],
                )
            )
        print("%d native Inventor bundle(s) valid" % len(records))
    return 0


def _create_inventor(args: argparse.Namespace) -> int:
    collection = prepare_inventor_collection(args.root)
    if args.taste is None and not args.inventor_id:
        raise WorkshopError(
            "inventor_id is required unless --taste supplies a TASTE.md name"
        )
    if args.taste is None and not args.description:
        raise WorkshopError("--description is required unless --taste is supplied")
    inventor_id = args.inventor_id or _inventor_id_from_taste(args.taste)
    name = args.name
    if args.taste is None and name is None:
        name = _default_inventor_name(inventor_id)
    destination = create_inventor(
        collection,
        inventor_id,
        name,
        args.description,
        taste_path=args.taste,
    )
    manifest = load_manifest(destination / "inventor.json")
    taste = load_taste(destination)
    problems = _inventor_problems((manifest,))
    if problems:
        raise WorkshopError("created inventor failed static validation: %s" % "; ".join(problems))
    manifest_sha256 = hashlib.sha256(
        (destination / "inventor.json").read_bytes()
    ).hexdigest()
    receipt = {
        "schema_version": 1,
        "kind": "native-inventor-bundle",
        "status": manifest.status,
        "id": manifest.inventor_id,
        "name": taste.name,
        "description": taste.description,
        "path": str(destination),
        "taste_sha256": taste.sha256,
        "manifest_sha256": manifest_sha256,
        "skills": [extension.to_dict() for extension in manifest.extensions],
        "validation": "static-passed",
    }
    if args.json:
        _print_json(receipt)
    else:
        print("%s joined the Workshop as a native Inventor bundle." % taste.name)
        print("Taste: %s" % (destination / "TASTE.md"))
        print("Skill: %s" % (destination / manifest.extensions[0].path / "SKILL.md"))
        print("Checks: static-passed")
    return 0


def _check_inventor(args: argparse.Namespace) -> int:
    manifests = manifests_for_target(args.target)
    problems = _inventor_problems(manifests)
    receipt = {
        "schema_version": 1,
        "kind": "inventor-static-check",
        "status": "passed" if not problems else "failed",
        "inventors": len(manifests),
        "problems": list(problems),
    }
    if args.json:
        _print_json(receipt)
    elif problems:
        for problem in problems:
            print("error: %s" % problem, file=sys.stderr)
    else:
        print("%d inventor(s): static layout valid" % len(manifests))
    return 1 if problems else 0


def _seal(args: argparse.Namespace) -> int:
    manifest = seal_artifact(args.source, extra_excludes=args.exclude)
    if args.output:
        manifest.write(args.output)
    _print_json(manifest.to_dict())
    return 0


def _pack(args: argparse.Namespace) -> int:
    packed = bundle_artifact(
        args.source,
        args.output,
        extra_excludes=args.exclude,
        maximum_bytes=args.maximum_bytes,
    )
    _print_json(
        {
            "artifact_sha256": packed.artifact_sha256,
            "bytes": packed.bytes,
            "entries": packed.entries,
            "pack_sha256": packed.pack_sha256,
            "path": str(packed.path),
        }
    )
    return 0


def _plan_pack(args: argparse.Namespace) -> int:
    planned = plan_artifact(
        args.source,
        extra_excludes=args.exclude,
        maximum_bytes=args.maximum_bytes,
        largest=args.largest,
    )
    _print_json(planned.to_dict())
    return 0 if planned.fits else 1


def _skills(args: argparse.Namespace) -> int:
    root = resolve_skills_root(args.root)
    if args.action == "path":
        print(str(root))
        return 0
    skills = discover_skills(root)
    if args.json:
        _print_json([skill.to_dict() for skill in skills])
    else:
        for skill in skills:
            print("%-20s %s" % (skill.name, skill.sha256))
    return 0


def _schemas(args: argparse.Namespace) -> int:
    root = resolve_schemas_root(args.root)
    if args.action == "path":
        print(str(root))
        return 0
    paths = discover_schemas(root)
    if args.json:
        _print_json([path.name for path in paths])
    else:
        for path in paths:
            print(path.name)
    return 0


def _vault(args: argparse.Namespace) -> int:
    if args.root is not None:
        root = Path(args.root).expanduser()
        if not root.is_dir():
            raise VaultError("no design vault directory at %s" % root)
        vault = Vault.from_directory(root)
    else:
        vault = default_gamevault_client().export()
    if args.action == "lint":
        errors, warnings = vault.lint()
        if args.json:
            _print_json(
                {"nodes": len(vault.nodes), "errors": errors, "warnings": warnings}
            )
        else:
            for line in errors:
                print("ERROR %s" % line)
            for line in warnings:
                print("WARN  %s" % line)
            print(
                "%d nodes, %d error(s), %d warning(s)"
                % (len(vault.nodes), len(errors), len(warnings))
            )
        return 2 if errors else 1 if warnings else 0
    findings = vault.check_compatibility(args.paths)
    if args.json:
        _print_json(findings)
    else:
        for finding in findings:
            print("%-17s %s" % (finding["kind"].upper(), " -> ".join(finding["nodes"])))
            for fix in finding["suggested_fixes"]:
                print("    fix: %s" % fix)
        print("%d finding(s) for %s" % (len(findings), ", ".join(args.paths)))
    return 0


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        prog="workshop",
        description=(
            "Let AI Inventors daydream new toys, then turn each liked idea into a "
            "product through one native Manager session and host-verified "
            "Workshop gates."
        ),
        epilog=(
            "Start here:\n"
            "  workshop doctor\n"
            "  workshop start pico-press\n"
            "  workshop start pico-press --effort forge"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subcommands = command.add_subparsers(
        dest="command", required=True, metavar="COMMAND"
    )

    start = subcommands.add_parser(
        "start",
        help="let one Inventor daydream and build brand-new toys until stopped",
    )
    start.add_argument(
        "inventor",
        metavar="INVENTOR",
        help="Inventor id such as pico-press (see `workshop inventors`)",
    )
    start.add_argument(
        "--idea",
        metavar="DAYDREAM_ID",
        help="build a saved idea instead of dreaming a new one",
    )
    start.add_argument(
        "--effort",
        choices=tuple(WORKSHOP_EFFORTS),
        default=DEFAULT_WORKSHOP_EFFORT,
        metavar="MODE",
        help=(
            "creative depth: spark (Make->Release; default), "
            "forge (Invent->Make->Release), or quest (Invent->Make->Playtest->Release)"
        ),
    )
    start.add_argument(
        "--manager",
        choices=tuple(SUPPORTED_MANAGER_IDS),
        default=DEFAULT_MANAGER_ID,
        metavar="RUNTIME",
        help=(
            "native Manager runtime for the daydream and the run: codex (default), "
            "claude, or grok"
        ),
    )
    start.add_argument(
        "--root", type=Path, help="Workshop checkout or inventor catalog"
    )
    start.add_argument(
        "--github",
        action="store_true",
        help=(
            "commit and push the generated toy folder after Release "
            "(default: disabled)"
        ),
    )
    start.add_argument(
        "--once",
        action="store_true",
        help="dream and build one idea, then stop (default: loop until stopped)",
    )
    start.add_argument(
        "--max-ideas",
        type=int,
        default=None,
        metavar="N",
        help="stop the loop after N ideas",
    )
    start.add_argument(
        "--max-failures",
        type=int,
        default=DEFAULT_MAX_CONSECUTIVE_FAILURES,
        metavar="N",
        help="stop the loop after N consecutive failed daydreams or builds (default: %d)"
        % DEFAULT_MAX_CONSECUTIVE_FAILURES,
    )
    start.add_argument(
        "--json",
        action="store_true",
        help="emit one JSON object per idea (one line each)",
    )
    start.add_argument(
        "--strict", action="store_true", help="with --once: exit 1 when the run waits"
    )
    start.set_defaults(handler=_start)

    stop = subcommands.add_parser(
        "stop", help="stop an Inventor's daydream loop after its current step"
    )
    stop.add_argument("inventor", metavar="INVENTOR")
    stop.add_argument(
        "--now",
        action="store_true",
        help="also interrupt the loop immediately; its current run stays resumable",
    )
    stop.set_defaults(handler=_stop)

    daydream = subcommands.add_parser(
        "daydream",
        help="let one Inventor dream one brand-new toy idea without building it",
    )
    daydream.add_argument(
        "inventor",
        metavar="INVENTOR",
        help="Inventor id such as pico-press (see `workshop inventors`)",
    )
    daydream.add_argument(
        "--idea",
        metavar="DAYDREAM_ID",
        help="print a saved idea instead of dreaming a new one",
    )
    daydream.add_argument(
        "--manager",
        choices=tuple(SUPPORTED_MANAGER_IDS),
        default=DEFAULT_MANAGER_ID,
        metavar="RUNTIME",
        help="native Manager runtime for the daydream: codex (default), claude, or grok",
    )
    daydream.add_argument(
        "--root", type=Path, help="Workshop checkout or inventor catalog"
    )
    daydream.add_argument("--json", action="store_true", help="emit one JSON receipt")
    daydream.set_defaults(handler=_daydream)

    wish = subcommands.add_parser(
        "wish", help="persist one Wish and start its native Manager session"
    )
    wish.add_argument("objective", nargs="+", metavar="WISH")
    wish.add_argument(
        "--effort",
        choices=tuple(WORKSHOP_EFFORTS),
        default=DEFAULT_WORKSHOP_EFFORT,
        metavar="MODE",
        help=(
            "creative depth: spark (Wish->Make->Release; default), "
            "forge (Wish->Invent->Make->Release), or "
            "quest (Wish->Invent->Make->Playtest->Release)"
        ),
    )
    wish.add_argument(
        "--manager",
        choices=tuple(SUPPORTED_MANAGER_IDS),
        default=DEFAULT_MANAGER_ID,
        metavar="RUNTIME",
        help=(
            "native Manager runtime: codex (default), claude, or grok; "
            "frozen for the run and cannot be changed on resume"
        ),
    )
    wish.add_argument(
        "--max-rounds",
        type=_round_budget,
        default=DEFAULT_MAX_ROUNDS,
        metavar="N",
        help=(
            "Invent-Make-Playtest round budget, 1-100 (default: %d); "
            "frozen for the run and cannot be changed on resume"
            % DEFAULT_MAX_ROUNDS
        ),
    )
    wish.add_argument(
        "--github",
        action="store_true",
        help=(
            "commit and push the generated toy folder after Release "
            "(default: disabled)"
        ),
    )
    wish.add_argument("--json", action="store_true", help="emit one JSON receipt")
    wish.add_argument("--strict", action="store_true", help="exit 1 when the run waits")
    wish.set_defaults(handler=_wish)

    status = subcommands.add_parser(
        "status", help="inspect one native Wish checkpoint without running a model"
    )
    status.add_argument("product_id", help="Wish id printed by 'workshop wish'")
    status.add_argument("--json", action="store_true", help="emit one JSON receipt")
    status.set_defaults(handler=_status)

    resume = subcommands.add_parser(
        "resume", help="resume the exact frozen native Manager session for one Wish"
    )
    resume.add_argument("product_id", help="saved Wish id")
    resume.add_argument("--json", action="store_true", help="emit one JSON receipt")
    resume.add_argument("--strict", action="store_true", help="exit 1 when the run waits")
    resume.set_defaults(handler=_resume)

    doctor = subcommands.add_parser(
        "doctor", help="check native runtime prerequisites without exposing credentials"
    )
    doctor.add_argument("--root", type=Path, help="Workshop checkout or inventor catalog")
    doctor.add_argument("--json", action="store_true", help="emit one JSON receipt")
    doctor.set_defaults(handler=_doctor)

    inventors = subcommands.add_parser(
        "inventors", help="list statically validated schema-v8 Inventor bundles"
    )
    inventors.add_argument("--root", type=Path, help="Workshop checkout or inventor catalog")
    inventors.add_argument("--json", action="store_true")
    inventors.set_defaults(handler=_inventors)

    create = subcommands.add_parser("create", help="create a native Inventor bundle")
    create_commands = create.add_subparsers(
        dest="create_kind", required=True, metavar="THING"
    )
    inventor = create_commands.add_parser(
        "inventor", help="create TASTE.md, a namespaced skill, and a v8 manifest"
    )
    inventor.add_argument("inventor_id", nargs="?")
    inventor.add_argument("--taste", type=Path, help="existing TASTE.md to preserve exactly")
    inventor.add_argument("--name", help="display name for a generated Taste")
    inventor.add_argument(
        "--description",
        help="routing boundary for a generated Taste (required without --taste)",
    )
    inventor.add_argument("--root", type=Path, default=Path.cwd())
    inventor.add_argument("--json", action="store_true")
    inventor.set_defaults(handler=_create_inventor)

    check = subcommands.add_parser(
        "check", help="statically validate native Inventor bundle data"
    )
    check.add_argument("target", type=Path, nargs="?", default=Path.cwd())
    check.add_argument("--json", action="store_true")
    check.set_defaults(handler=_check_inventor)

    seal = subcommands.add_parser("seal", help="seal an artifact tree")
    seal.add_argument("source", type=Path)
    seal.add_argument("--output", type=Path)
    seal.add_argument("--exclude", action="append", default=[])
    seal.set_defaults(handler=_seal)

    pack = subcommands.add_parser("pack", help="build a reproducible immutable Pack")
    pack.add_argument("source", type=Path)
    pack.add_argument("output", type=Path)
    pack.add_argument("--exclude", action="append", default=[])
    pack.add_argument("--maximum-bytes", type=int, default=MAX_PACK_BYTES)
    pack.set_defaults(handler=_pack)

    planned = subcommands.add_parser("plan-pack", help="preview exact Pack size")
    planned.add_argument("source", type=Path)
    planned.add_argument("--exclude", action="append", default=[])
    planned.add_argument("--maximum-bytes", type=int, default=MAX_PACK_BYTES)
    planned.add_argument("--largest", type=int, default=5)
    planned.set_defaults(handler=_plan_pack)

    skills = subcommands.add_parser("skills", help="discover Make-owned domain skills")
    skills.add_argument("action", choices=("list", "path"), nargs="?", default="list")
    skills.add_argument("--root", type=Path, help="absolute skills root")
    skills.add_argument("--json", action="store_true")
    skills.set_defaults(handler=_skills)

    schemas = subcommands.add_parser("schemas", help="discover installed JSON contracts")
    schemas.add_argument("action", choices=("list", "path"), nargs="?", default="list")
    schemas.add_argument("--root", type=Path)
    schemas.add_argument("--json", action="store_true")
    schemas.set_defaults(handler=_schemas)

    vault = subcommands.add_parser(
        "vault", help="lint or query the game design vault served by the vault API"
    )
    vault.add_argument("action", choices=("lint", "check"))
    vault.add_argument("paths", nargs="*", help="node paths for `check`")
    vault.add_argument(
        "--root",
        type=Path,
        help="a local vault checkout to read instead of the vault API",
    )
    vault.add_argument("--json", action="store_true")
    vault.set_defaults(handler=_vault)
    return command


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parser().parse_args(argv)
        return int(args.handler(args))
    except (WorkshopError, OSError, ValueError, KeyError) as exc:
        print("workshop: %s" % exc, file=sys.stderr)
        return 2


__all__ = ["main", "parser"]
