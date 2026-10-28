#!/usr/bin/env python3
"""Publish a CAD project built outside Workshop to Factory, as Spark would.

Reads a CAD project directory (``--cad-dir``, what autonomous-product-to-cad's
``skills/toy-archive/scripts/publish`` stages) or a packed public toy archive
(``--archive``), stages the Made tree and schema-4 Release carrier Spark
publishes, and builds the exact Factory handoff ZIP. Without ``--live``
nothing is read from the credential store and nothing is sent: it prints what
would be uploaded, the gate evidence, and whatever would stop ``--live``.

``--live`` needs fresh gate evidence: ``measure/direct-publish-evidence.json``
binding a ``verify_project --fresh --print-gates`` run to the exact source and
STEP bytes, with every failing gate declared by ``--known-gate-failure``.
``--verify`` (``--cad-dir`` only) runs autonomous-product-to-cad's verifier in
place and writes that file.

``--live`` then runs the host's existing Factory adapter unchanged: the
Inventor's own stored credential, a durable effect ledger under
``$WORKSHOP_HOME/direct-publish/<product-id>/``, a private draft import with
authenticated readback, publication, and public readback of the exact
metadata anchor. On success it prints ``slug:``, ``public: <url>`` and one
``publication-record: <json>`` line with the receipt's identity hashes.
Re-running the same bytes reconciles through the ledger instead of creating a
second design. See docs/PUBLISH_DIRECT.md.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, TextIO

from workshop.errors import (
    AmbiguousEffectError,
    ContractError,
    EffectError,
    ReceiptError,
    StateConflict,
)
from workshop.integrations.factory import (
    FACTORY_COVER_RENDER_PATH,
    FactoryAgentSession,
    FactoryCredentialRejected,
    FactoryPublicTransition,
    FactoryReleaseWriter,
    build_release_handoff,
    factory_credentials_from_environment,
)
from workshop.release.direct_publish import (
    EVIDENCE_PATH,
    PIPELINE_RECORD_PATH,
    VERIFY_ARGUMENTS,
    DirectSource,
    EvidenceStatus,
    KnownGateFailure,
    build_evidence,
    evaluate_evidence,
    inventor_name,
    load_cad_project,
    load_public_toy_archive,
    readme_summary,
    slugify,
    stage_direct_publication,
)
from workshop.runtime import EffectLedger
from workshop.runtime.credentials import (
    factory_credential_environment,
    factory_service_credential_environment,
    inventor_credential_file,
)
from workshop.runtime.package_data import default_workshop_home


REPOSITORY = Path(__file__).resolve().parents[1]
EXIT_INPUT = 2
EXIT_EFFECT = 3
VERIFIER = Path("skills") / "cad" / "scripts" / "verify_project"
GATES_NOT_RUN = (
    "Wish and Inventor selection",
    "Make's own CAD gate, Component and signature reviews",
    "Playtest (recorded as not-run)",
)


def ledger_path(product_id: str, environment: Optional[Mapping[str, str]] = None) -> Path:
    return default_workshop_home(environment) / "direct-publish" / product_id / "factory-effects.sqlite3"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--cad-dir", type=Path, help="CAD project in its own layout")
    source.add_argument("--archive", type=Path, help="packed public toy archive (schema 4)")
    parser.add_argument("--inventor", required=True, help="roster Inventor whose Factory account publishes")
    parser.add_argument("--primary-step", help="top-level primary STEP (default: the one PRINTABLE entry)")
    parser.add_argument("--product-id", help="Workshop product id (default: from the directory name)")
    parser.add_argument("--title", help="listing title (default: README heading)")
    parser.add_argument("--summary", help="listing description (default: README first paragraph)")
    parser.add_argument("--what-arrives", action="append", default=[], metavar="TEXT",
                        help="what the buyer receives; repeatable; read by Factory's copy auditor")
    parser.add_argument("--limitation", action="append", default=[], metavar="TEXT",
                        help="a known limitation; repeatable")
    parser.add_argument("--known-gate-failure", action="append", default=[], metavar="GATE:REASON",
                        help="a gate failure the owner accepts, recorded with the publication; repeatable")
    parser.add_argument("--verify", action="store_true",
                        help="--cad-dir only: run verify_project --fresh --print-gates in place first")
    parser.add_argument("--verifier-repo", type=Path,
                        help="autonomous-product-to-cad checkout (default: $PRODUCT_TO_CAD_REPO, then sibling)")
    parser.add_argument("--verifier-python", type=Path,
                        help="interpreter for the verifier (default: its .venv, then this one)")
    parser.add_argument("--reimport-slug", metavar="SLUG",
                        help="not supported yet: the host adapter never re-imports a public design")
    parser.add_argument("--inventors", type=Path, default=REPOSITORY / "inventors",
                        help=argparse.SUPPRESS)
    parser.add_argument("--live", action="store_true", help="publish; default is an offline dry run")
    return parser


def _source(args: argparse.Namespace) -> DirectSource:
    if args.archive is not None:
        return load_public_toy_archive(args.archive)
    return load_cad_project(args.cad_dir)


def _roster(inventors: Path) -> list[str]:
    return sorted(path.parent.name for path in Path(inventors).glob("*/inventor.json"))


def _packed_inventor(source: DirectSource, roster: Sequence[str]) -> Optional[str]:
    """The Inventor an archive was packed for: its ``<inventor>-`` name prefix."""

    if source.kind != "public-toy-archive":
        return None
    name = source.root.name
    matches = [inventor for inventor in roster if name.startswith(inventor + "-")]
    return max(matches, key=len) if matches else None


def _product_id(args: argparse.Namespace, source: DirectSource, packed: Optional[str]) -> str:
    if args.product_id:
        return args.product_id
    name = source.root.name
    if packed is not None:
        name = name[len(packed) + 1:]
    return slugify(name)


def _verifier(args: argparse.Namespace, environment: Mapping[str, str]) -> tuple[Path, Path]:
    candidates = [args.verifier_repo] if args.verifier_repo else [
        Path(environment["PRODUCT_TO_CAD_REPO"]) if environment.get("PRODUCT_TO_CAD_REPO") else None,
        REPOSITORY.parent / "autonomous-product-to-cad",
    ]
    for repository in candidates:
        if repository is not None and (repository / VERIFIER).is_file():
            script = (repository / VERIFIER).resolve()
            venv = repository / ".venv" / "bin" / "python"
            python = args.verifier_python or (venv if venv.is_file() else Path(sys.executable))
            return script, python
    raise ContractError(
        "--verify needs autonomous-product-to-cad's %s; pass --verifier-repo or set "
        "PRODUCT_TO_CAD_REPO" % VERIFIER.as_posix()
    )


def _run_verification(
    args: argparse.Namespace,
    primary_step: str,
    environment: Mapping[str, str],
    err: TextIO,
) -> None:
    """Run the verifier in place on ``--cad-dir`` and write the evidence file."""

    project = load_cad_project(args.cad_dir).root
    script, python = _verifier(args, environment)
    entry = primary_step[: -len(".step")] + ".step.py"
    if not (project / entry).is_file():
        raise ContractError("primary entry %s is not in the project" % entry)
    arguments = [*VERIFY_ARGUMENTS, "--assembly", "%s/%s" % (project.name, entry)]
    print("publish_direct: running %s on %s (rebuilds every STEP; this can take minutes)"
          % (VERIFIER.as_posix(), project.name), file=err)
    result = subprocess.run(
        [str(python), str(script), project.name, *arguments],
        cwd=project.parent, capture_output=True, text=True,
    )
    tail = (result.stdout + result.stderr).strip().splitlines()[-15:]
    for line in tail:
        print("  " + line, file=err)
    record = project / PIPELINE_RECORD_PATH
    if not record.is_file():
        raise ContractError("verify_project exited %d and wrote no %s"
                            % (result.returncode, PIPELINE_RECORD_PATH))
    evidence = build_evidence(
        load_cad_project(project),
        record=record.read_bytes(),
        exit_code=result.returncode,
        arguments=[*VERIFY_ARGUMENTS, "--assembly", entry],
        verifier_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
        recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    (project / EVIDENCE_PATH).write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _describe_evidence(write: Any, status: EvidenceStatus) -> None:
    document = status.document
    if document is not None:
        failing = [row for row in document["gates"] if row.get("result") == "fail"]
        write("evidence:      %s  (%s, recorded %s, verifier exit %s)" % (
            status.state, " ".join(document["arguments"]),
            document["recorded_at"], document["exit_code"]))
        write("               subject %s over %d source/STEP files" % (
            document["subject"]["sha256"], len(document["subject"]["files"])))
        for row in failing:
            write("               failed: %s%s (%s)" % (
                row["gate"], " on " + row["target"] if row.get("target") else "", row["status"]))
    else:
        write("evidence:      %s" % status.state)
    for failure in status.declared:
        write("known gate failure declared: %s: %s" % (failure.gate, failure.reason))
    for problem in status.problems:
        write("               %s" % problem)


def _describe(
    write: Any,
    *,
    live: bool,
    source: DirectSource,
    product_id: str,
    inventor: str,
    display_name: str,
    staged: Any,
    handoff: Mapping[str, Any],
    evidence: EvidenceStatus,
    environment: Optional[Mapping[str, str]],
) -> None:
    metadata = handoff["metadata"]
    content = handoff["content"]
    write("publish_direct: %s" % ("LIVE" if live else "dry run, nothing is read from the credential store or sent"))
    write("source:        %s %s" % (source.kind, source.root))
    if source.archive_sha256:
        write("               MANIFEST.json verified, artifact %s" % source.archive_sha256)
    write("product id:    %s" % product_id)
    write("inventor:      %s (%s)" % (inventor, display_name))
    write("title:         %s" % metadata["title"])
    write("summary:       %s" % metadata["description"])
    write("category/tags: %s / %s" % (metadata.get("category"), ", ".join(metadata["tags"])))
    page = handoff["page"]
    for name in ("what_arrives", "limitations"):
        write("%-14s %s" % (name + ":", "; ".join(page[name]) or "(none)"))
    write("playtest:      %s" % page["playtest_status"])
    _describe_evidence(write, evidence)
    primary = handoff["primary_model"]
    write("primary model: %s <- %s  sha256 %s" % (primary["path"], staged.primary_source, primary["sha256"]))
    write("cover:         %s <- %s  sha256 %s" % (
        FACTORY_COVER_RENDER_PATH, staged.cover_path, handoff["cover_render_sha256"]))
    write("anchor:        workshop-release-page.json sha256 %s" % handoff["product_page_sha256"])
    write("made artifact: %s" % staged.context.made.artifact_sha256)
    write("handoff zip:   %d bytes, pack sha256 %s" % (len(content), handoff["pack_sha256"]))
    write("files in the handoff:")
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            write("  %12d  %s" % (info.file_size, info.filename))
    made_steps = sorted(
        entry.path for entry in staged.context.made.artifact_manifest.entries
        if entry.path.casefold().endswith((".step", ".stp")) and entry.path != primary["path"]
    )
    if made_steps or source.dropped:
        write("not uploaded:")
        for path in made_steps:
            write("  %s (one STEP crosses: the primary)" % path)
        for path, reason in source.dropped:
            write("  %s (%s)" % (path, reason))
    unsanitized = source.host_path_files()
    if unsanitized:
        write("warning: these files name a home directory and would publish it: %s"
              % ", ".join(unsanitized))
    credential = inventor_credential_file(inventor, environment)
    write("credential:    %s (%s)" % (credential, "present" if credential.exists() else "absent"))
    write("ledger:        %s" % ledger_path(product_id, environment))
    write("gates not run by Workshop: %s" % "; ".join(GATES_NOT_RUN))


def _blockers(
    args: argparse.Namespace,
    source: DirectSource,
    packed: Optional[str],
    evidence: EvidenceStatus,
    environment: Optional[Mapping[str, str]],
) -> list[str]:
    """Everything that stops ``--live`` before any credential is read."""

    blockers = []
    if source.publication is not None:
        page = (source.publication.get("publication") or {}).get("page_url")
        blockers.append("archive already records a publication (%s); publishing again "
                        "would create a second design" % page)
    if packed is not None and packed != args.inventor:
        blockers.append(
            "archive was packed for Inventor %s; re-pack it with `toy_archive pack "
            "--inventor %s` so the archive and the listing name one Inventor"
            % (packed, args.inventor)
        )
    if not evidence.acceptable:
        blockers.append("gate evidence is %s: %s" % (evidence.state, "; ".join(evidence.problems)))
    # Factory shows the authorizing account as the public author, so a
    # direct publication never falls back to a host-wide account.
    if not inventor_credential_file(args.inventor, environment).exists():
        blockers.append("no Factory credential for Inventor %s; run `workshop login %s`"
                        % (args.inventor, args.inventor))
    return blockers


def _publish_live(
    staged: Any,
    *,
    product_id: str,
    inventor: str,
    environment: Optional[Mapping[str, str]],
    transports: Mapping[str, Any],
) -> Any:
    values = factory_credential_environment(environment, inventor_id=inventor)
    credentials = factory_credentials_from_environment(
        factory_service_credential_environment(values)
    )
    ledger = EffectLedger(ledger_path(product_id, environment))
    receipt = FactoryReleaseWriter(ledger, inventor, credentials, **transports)(
        staged.context, staged.release_root, staged.release_manifest
    )
    if receipt.is_verified_draft:
        receipt = FactoryPublicTransition(
            ledger, FactoryAgentSession(credentials, **transports)
        ).publish(receipt)
    if not receipt.is_verified_public:
        raise ReceiptError("Factory publication lacks verified public readback")
    return receipt


def publication_record(receipt: Any, staged: Any, evidence: EvidenceStatus) -> dict[str, Any]:
    """The receipt's identities, shaped like a Workshop archive's PUBLICATION.json."""

    details = receipt.details
    primary = staged.context.made.artifact_root / "assembled.step"
    identities = {
        "package_artifact_sha256": details["release_sha256"],
        "product_artifact_sha256": receipt.artifact_sha256,
        "playtest_evidence_sha256": details["playtest_evidence_sha256"],
        "product_page_sha256": details["product_page_sha256"],
        "primary_model_sha256": details["primary_model_sha256"],
        "product_facts_sha256": details["product_facts_sha256"],
        "handoff_artifact_sha256": details["handoff_artifact_sha256"],
        "pack_sha256": receipt.payload_sha256,
        "publication_anchor_path": details["publication_anchor_path"],
        "publication_anchor_sha256": details["publication_anchor_sha256"],
        "publication_anchor_readback_sha256": details["publication_anchor_readback_sha256"],
    }
    return {
        "identities": identities,
        "primary_model": {
            "path": "make/models/cad/" + staged.primary_source,
            "bytes": primary.stat().st_size,
            "sha256": details["primary_model_sha256"],
        },
        "publication": {
            "adapter": "factory",
            "status": "public",
            "slug": receipt.slug,
            "page_url": details["page_url"],
            "observed_at": receipt.observed_at,
            "listing": {
                "price_cents": receipt.listing_price_cents,
                "currency": receipt.listing_currency,
            },
            "publication_mode": details["publication_mode"],
            "publication_anchor_url": details["publication_anchor_url"],
        },
        "direct_publish": {
            "workshop_lifecycle": "not-run",
            "evidence": evidence.summary(),
        },
    }


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    environment: Optional[Mapping[str, str]] = None,
    transports: Optional[Mapping[str, Any]] = None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    args = _parser().parse_args(argv)
    write = lambda line="": print(line, file=out)  # noqa: E731
    try:
        if args.reimport_slug:
            raise ContractError(
                "--reimport-slug is not supported yet: Workshop's Factory adapter never "
                "appends a version to a public design (planned; see docs/PUBLISH_DIRECT.md)"
            )
        if args.verify and args.archive is not None:
            raise ContractError(
                "--verify runs on a --cad-dir; verify the project and re-pack the archive"
            )
        known = [KnownGateFailure.parse(value) for value in args.known_gate_failure]
        display_name = inventor_name(args.inventors, args.inventor)
        source = _source(args)
        primary_step = args.primary_step or source.entry_step()
        if args.verify:
            _run_verification(args, primary_step, environment or os.environ, err)
            source = _source(args)
        packed = _packed_inventor(source, _roster(args.inventors))
        product_id = _product_id(args, source, packed)
        readme_title, readme_paragraph = readme_summary(source.readme or b"")
        title = args.title or readme_title
        summary = args.summary or readme_paragraph
        if not title or not summary:
            raise ContractError("no --title/--summary and the project README does not supply one")
        evidence = evaluate_evidence(source, known)
        with tempfile.TemporaryDirectory(prefix="workshop-direct-publish-") as temporary:
            staged = stage_direct_publication(
                source,
                Path(temporary).resolve(),
                product_id=product_id,
                inventor_display_name=display_name,
                primary_step=primary_step,
                title=title,
                summary=summary,
                what_arrives=args.what_arrives,
                limitations=args.limitation,
                evidence=evidence.summary(),
            )
            handoff = build_release_handoff(
                staged.context, staged.release_root, staged.release_manifest
            )
            _describe(
                write, live=args.live, source=source, product_id=product_id,
                inventor=args.inventor, display_name=display_name, staged=staged,
                handoff=handoff, evidence=evidence, environment=environment,
            )
            blockers = _blockers(args, source, packed, evidence, environment)
            if blockers:
                write("live:          refused")
                for blocker in blockers:
                    write("  - %s" % blocker)
            else:
                write("live:          ready")
            if not args.live:
                write("dry run complete; nothing was sent")
                return 0
            if blockers:
                raise ContractError("--live refused: %s" % "; ".join(blockers))
            receipt = _publish_live(
                staged, product_id=product_id, inventor=args.inventor,
                environment=environment, transports=transports or {},
            )
            record = publication_record(receipt, staged, evidence)
        write("slug: %s" % receipt.slug)
        write("public: %s" % receipt.details["page_url"])
        write("publication-record: %s" % json.dumps(record, sort_keys=True, separators=(",", ":")))
        return 0
    except FactoryCredentialRejected:
        print("publish_direct: Factory rejected the credential for %s; run "
              "`workshop login %s`" % (args.inventor, args.inventor), file=err)
        return EXIT_EFFECT
    except (AmbiguousEffectError, EffectError, ReceiptError) as exc:
        print("publish_direct: %s: %s. Nothing is retried blindly; re-run the same "
              "command to reconcile through the ledger." % (type(exc).__name__, exc), file=err)
        return EXIT_EFFECT
    except (ContractError, StateConflict, OSError) as exc:
        print("publish_direct: %s" % exc, file=err)
        return EXIT_INPUT


if __name__ == "__main__":
    raise SystemExit(main())
