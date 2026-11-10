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

``--update-listing SLUG --reason fix|reprice`` instead appends one version to
a design this Workshop already published (ADR 0097), keeping its listing,
slug and URL. Without ``--live`` it is a preview: authenticated reads only,
printing the current price, the predicted price and a confirmation code.
``--live --confirm CODE`` runs exactly that update. ``--reconcile-publish
PRODUCT_ID`` settles an ``unknown`` publish intent by readback alone.
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
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, TextIO

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
    _extra_materials,
    build_release_handoff,
    factory_credentials_from_environment,
    urllib_project_file_transport,
    urllib_transport,
)
from workshop.integrations.factory_listing import (
    FactoryListingUpdate,
    ListingUpdateBindings,
    ListingUpdatePlan,
    append_publication_version,
    listing_price_note,
    listing_update_version,
    read_only_transport,
)
from workshop.release.direct_publish import (
    EVIDENCE_PATH,
    PIPELINE_RECORD_PATH,
    VERIFY_ARGUMENTS,
    DirectSource,
    EvidenceStatus,
    KnownGateFailure,
    build_evidence,
    earlier_publications,
    evaluate_evidence,
    inventor_name,
    load_cad_project,
    load_public_toy_archive,
    load_published_record,
    published_design,
    SealedBought,
    sealed_bought,
    readme_summary,
    record_archive_publication,
    slugify,
    stage_direct_publication,
)
from workshop.release.local_paths import names_host_path
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
# Factory makes a design public at once but creates its shop listing a little
# later (20-90 s observed), and Workshop counts a listing as part of public
# readback. After an accepted (2xx) publish, FactoryPublicTransition itself
# re-reads for a bounded time. This wait covers the rest: a publish whose
# response was lost or ambiguous. The publish call is never repeated: each
# retry below only re-reads a publication whose ledger intent is "unknown".
LISTING_WAIT_SECONDS = 120
LISTING_POLL_SECONDS = 10
GATES_NOT_RUN = (
    "Wish and Inventor selection",
    "Make's own CAD gate, Component and signature reviews",
    "Playtest (recorded as not-run)",
)


def ledger_path(product_id: str, environment: Optional[Mapping[str, str]] = None) -> Path:
    return default_workshop_home(environment) / "direct-publish" / product_id / "factory-effects.sqlite3"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--cad-dir", type=Path, help="CAD project in its own layout")
    source.add_argument("--archive", type=Path, help="packed public toy archive (schema 4)")
    parser.add_argument("--inventor", required=True, help="roster Inventor whose Factory account publishes")
    parser.add_argument("--primary-step", help="top-level primary STEP (default: the one PRINTABLE entry)")
    parser.add_argument("--product-id", help="Workshop product id (default: from the directory name)")
    parser.add_argument("--title", help="listing title (default: README heading); follow docs/TOY_NAMING.md")
    parser.add_argument("--summary", help="listing description (default: README first paragraph)")
    parser.add_argument("--what-arrives", action="append", default=[], metavar="TEXT",
                        help="what the buyer receives; repeatable; read by Factory's copy auditor")
    parser.add_argument("--limitation", action="append", default=[], metavar="TEXT",
                        help="a known limitation; repeatable")
    parser.add_argument("--display-only", action="append", default=[], metavar="BODY",
                        help="a primary-STEP body the buyer does not get (a prop); removed from "
                             "what Factory weighs; repeatable")
    parser.add_argument("--bought", action="append", default=[], metavar="BODY=PART",
                        help="a primary-STEP body that is bought hardware the buyer gets; removed "
                             "from what Factory weighs and billed as an extra material; PART is a "
                             "catalogue id or a plain name; repeatable")
    parser.add_argument("--sealed-wish", type=Path,
                        help="a Workshop run's artifacts/wish/wish.json: bill the Bought Parts it "
                             "sealed, as its Release would, and leave its bought_ bodies out "
                             "of what Factory weighs")
    parser.add_argument("--part-price", action="append", default=[], metavar="PART=CENTS",
                        help="what one PART costs in US cents, for a part the catalogue does not "
                             "price; repeatable")
    parser.add_argument("--known-gate-failure", action="append", default=[], metavar="GATE:REASON",
                        help="a gate failure the owner accepts, recorded with the publication; repeatable")
    parser.add_argument("--verify", action="store_true",
                        help="--cad-dir only: run verify_project --fresh --print-gates in place first")
    parser.add_argument("--verifier-repo", type=Path,
                        help="autonomous-product-to-cad checkout (default: $PRODUCT_TO_CAD_REPO, then sibling)")
    parser.add_argument("--verifier-python", type=Path,
                        help="interpreter for the verifier (default: its .venv, then this one)")
    parser.add_argument("--reimport-slug", metavar="SLUG",
                        help="retired: use --update-listing SLUG --reason fix|reprice")
    parser.add_argument("--update-listing", metavar="SLUG",
                        help="append a version to this public design instead of creating one "
                             "(ADR 0097); without --live a preview with authenticated reads")
    parser.add_argument("--reason", choices=("fix", "reprice"),
                        help="--update-listing: fix (changed printed geometry or print settings, "
                             "needs gate evidence) or reprice (the live geometry, re-billed)")
    parser.add_argument("--published-archive", type=Path,
                        help="--update-listing with --cad-dir: the toy's packed archive, whose "
                             "PUBLICATION.json names the listing")
    parser.add_argument("--predicted-grams", type=float, metavar="G",
                        help="--update-listing: the printed-only primary's mass, measured with "
                             "Factory's own slice worker")
    parser.add_argument("--predicted-grams-source", metavar="TEXT",
                        help="--update-listing: how --predicted-grams was measured")
    parser.add_argument("--confirm", metavar="CODE",
                        help="--update-listing --live: the confirmation code the preview printed")
    parser.add_argument("--reconcile-publish", metavar="PRODUCT_ID",
                        help="settle this product's unknown publish intent by Factory readback "
                             "alone; never sends")
    parser.add_argument("--inventors", type=Path, default=REPOSITORY / "inventors",
                        help=argparse.SUPPRESS)
    parser.add_argument("--live", action="store_true", help="publish; default is an offline dry run")
    return parser


def _sealed_bought(args: argparse.Namespace, source: DirectSource) -> Optional[SealedBought]:
    if args.sealed_wish is None:
        return None
    if args.cad_dir is None:
        raise ContractError("--sealed-wish goes with --cad-dir, the run's own CAD project")
    try:
        wish = json.loads(Path(args.sealed_wish).read_bytes())
    except (OSError, ValueError) as exc:
        raise ContractError("--sealed-wish %s is unreadable: %s" % (args.sealed_wish, exc)) from exc
    return sealed_bought(wish, source.root)


def _pairs(values: Sequence[str], flag: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        key, separator, item = value.partition("=")
        key, item = key.strip(), item.strip()
        if not separator or not key or not item:
            raise ContractError("%s takes KEY=VALUE, not %r" % (flag, value))
        if key in result:
            raise ContractError("%s names %s twice" % (flag, key))
        result[key] = item
    return result


def _part_prices(values: Sequence[str]) -> dict[str, int]:
    prices = {}
    for part, cents in _pairs(values, "--part-price").items():
        if not cents.isdigit():
            raise ContractError("--part-price %s must be whole US cents, not %r" % (part, cents))
        prices[part] = int(cents)
    return prices


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
    updating: bool = False,
    ledger_file: Optional[Path] = None,
) -> None:
    metadata = handoff["metadata"]
    content = handoff["content"]
    if updating:
        write("publish_direct: %s" % ("LIVE listing update" if live else
                                      "listing update preview: authenticated Factory reads only, "
                                      "nothing is sent"))
    else:
        write("publish_direct: %s" % ("LIVE" if live else "dry run, nothing is read from the credential store or sent"))
    write("source:        %s %s" % (source.kind, source.root))
    if updating and "measure/make-round-state.json" in source.files:
        write("note:          this CAD came from a Workshop run; `workshop publish <wish-id> "
              "--update-listing` ships that run's sealed bytes without a rebuild")
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
    if staged.stripped_bodies:
        write("primary model: %s <- printed bodies of %s  sha256 %s" % (
            primary["path"], staged.primary_source, primary["sha256"]))
        write("               removed, not weighed by Factory: %s" % ", ".join(staged.stripped_bodies))
    else:
        write("primary model: %s <- %s  sha256 %s" % (primary["path"], staged.primary_source, primary["sha256"]))
    hardware = staged.context.made.product.get("bought_hardware") or []
    if hardware:
        write("extra materials (billed on top of the print):")
        for item in hardware:
            write("  %s x%d at %d cents (%s price) = %d cents" % (
                item["name"], item["count"], item["unit_price_cents"], item["price_source"],
                item["count"] * item["unit_price_cents"]))
    else:
        write("extra materials: (none)")
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
    # Release's path hygiene has already redacted the handoff; anything left
    # here is a binary file that names a home directory.
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        unsanitized = sorted(
            name for name in archive.namelist() if names_host_path(archive.read(name))
        )
    if unsanitized:
        write("warning: these handoff files name a home directory and would publish it: %s"
              % ", ".join(unsanitized))
    credential = inventor_credential_file(inventor, environment)
    write("credential:    %s (%s)" % (credential, "present" if credential.exists() else "absent"))
    write("ledger:        %s" % (ledger_file or ledger_path(product_id, environment)))
    write("gates not run by Workshop: %s" % "; ".join(GATES_NOT_RUN))


def _blockers(
    args: argparse.Namespace,
    source: DirectSource,
    packed: Optional[str],
    evidence: EvidenceStatus,
    environment: Optional[Mapping[str, str]],
    *,
    product_id: str,
    title: str,
) -> list[str]:
    """Everything that stops ``--live`` before any credential is read."""

    blockers = []
    for earlier in earlier_publications(
        default_workshop_home(environment) / "direct-publish", product_id=product_id, title=title
    ):
        blockers.append(
            "product id %s already published this toy as %s (%s, import %s); publishing "
            "it under product id %s would create a second design. Update the listing in "
            "place with --update-listing %s --reason fix|reprice (docs/PUBLISH_DIRECT.md)"
            % (earlier.product_id, earlier.slug, earlier.page_url or "no page recorded",
               earlier.state, product_id, earlier.slug)
        )
    if source.publication is not None:
        page = (source.publication.get("publication") or {}).get("page_url")
        slug = (source.publication.get("publication") or {}).get("slug")
        blockers.append("archive already records a publication (%s); publishing again "
                        "would create a second design. Update it in place with "
                        "--update-listing %s --reason fix|reprice" % (page, slug))
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
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> Any:
    values = factory_credential_environment(environment, inventor_id=inventor)
    credentials = factory_credentials_from_environment(
        factory_service_credential_environment(values)
    )
    ledger = EffectLedger(ledger_path(product_id, environment))
    # Every wait goes through the injected sleeper: the writer's rate retries,
    # the transition's settle wait and the listing wait below. A sleeper the
    # caller placed in ``transports`` keeps precedence.
    session_options = {"sleeper": sleeper, **transports}
    receipt = FactoryReleaseWriter(ledger, inventor, credentials, **session_options)(
        staged.context, staged.release_root, staged.release_manifest
    )
    if receipt.is_verified_draft:
        transition = FactoryPublicTransition(
            ledger, FactoryAgentSession(credentials, **session_options)
        )
        receipt = _await_listing(
            transition, receipt, ledger, product_id, sleeper=sleeper, clock=clock
        )
    if not receipt.is_verified_public:
        raise ReceiptError("Factory publication lacks verified public readback")
    return receipt


def _await_listing(
    transition: Any,
    draft: Any,
    ledger: EffectLedger,
    product_id: str,
    *,
    sleeper: Callable[[float], None],
    clock: Callable[[], float],
) -> Any:
    """Publish once, then re-read for up to LISTING_WAIT_SECONDS.

    A retry happens only while the ledger's publish intent is ``unknown``:
    ``FactoryPublicTransition`` then reconciles by readback alone and never
    sends the publish request again. Any other failure is raised at once.
    """

    deadline = clock() + LISTING_WAIT_SECONDS
    while True:
        try:
            return transition.publish(draft)
        except AmbiguousEffectError:
            intent = ledger.latest(product_id, "factory-publish")
            if intent is None or intent.state != "unknown" or clock() >= deadline:
                raise
        sleeper(LISTING_POLL_SECONDS)


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
            **({"printed_bodies_of": "make/models/cad/" + staged.primary_source,
                "removed_bodies": list(staged.stripped_bodies)}
               if staged.stripped_bodies else {}),
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


def _session(
    inventor: str,
    environment: Optional[Mapping[str, str]],
    transports: Mapping[str, Any],
    *,
    read_only: bool = False,
) -> FactoryAgentSession:
    """The Inventor's own authenticated session; ``read_only`` refuses any send."""

    values = factory_credential_environment(environment, inventor_id=inventor)
    credentials = factory_credentials_from_environment(
        factory_service_credential_environment(values)
    )
    options = dict(transports)
    if read_only:
        inner = options.get("transport", urllib_transport)
        options["transport"] = read_only_transport(inner)
        if "project_file_transport" not in options and inner is urllib_transport:
            options["project_file_transport"] = urllib_project_file_transport
    return FactoryAgentSession(credentials, **options)


def _money(cents: Optional[int]) -> str:
    return "unknown" if cents is None else "$%d.%02d" % (cents // 100, cents % 100)


def _extras_text(items: Sequence[Mapping[str, Any]]) -> str:
    if not items:
        return "(none)"
    return "; ".join("%s %s" % (item["name"], _money(item["price_cents"])) for item in items)


def _update_record(
    args: argparse.Namespace, source: DirectSource
) -> Mapping[str, Any]:
    """The PUBLICATION.json that names the listing this update targets."""

    if args.archive is not None:
        record = source.publication
    elif args.published_archive is not None:
        record = load_published_record(args.published_archive)
    else:
        raise ContractError("--update-listing with --cad-dir needs --published-archive")
    if record is None:
        raise ContractError("the archive records no publication; there is no listing to update")
    slug = (record.get("publication") or {}).get("slug")
    if slug != args.update_listing:
        raise ContractError(
            "--update-listing %s does not match the archive's listing %s"
            % (args.update_listing, slug)
        )
    return record


def _update_plan(
    args: argparse.Namespace,
    source: DirectSource,
    record: Mapping[str, Any],
    primary_step: str,
    staged: Any,
) -> ListingUpdatePlan:
    versions = record.get("versions") or []
    latest = versions[-1] if versions and isinstance(versions[-1], Mapping) else {}
    return ListingUpdatePlan(
        reason=args.reason,
        slug=args.update_listing,
        source_primary_path=primary_step,
        source_primary_sha256=hashlib.sha256(source.files[primary_step].read_bytes()).hexdigest(),
        kept_bodies=(),
        stripped_bodies=tuple(staged.stripped_bodies),
        extra_materials=tuple(_extra_materials(staged.context.made.product)),
        predicted_weight_g=args.predicted_grams,
        predicted_weight_source=args.predicted_grams_source,
        recorded_source_primary_sha256=latest.get("source_primary_sha256"),
        recorded_history_id=latest.get("history_id"),
    )


def _update_bindings(staged: Any, handoff: Mapping[str, Any]) -> ListingUpdateBindings:
    return ListingUpdateBindings(
        content=handoff["content"],
        pack_sha256=handoff["pack_sha256"],
        handoff_artifact_sha256=handoff["artifact_sha256"],
        product_artifact_sha256=staged.context.made.artifact_sha256,
        release_sha256=staged.release_manifest.artifact_sha256,
        playtest_evidence_sha256=handoff["page"]["playtest_evidence_artifact_sha256"],
        product_page_sha256=handoff["product_page_sha256"],
        primary_model_sha256=handoff["primary_model"]["sha256"],
        product_facts_sha256=handoff["product_facts_sha256"],
    )


def _describe_preview(write: Any, plan: ListingUpdatePlan, state: Any, problems: Sequence[str],
                      code: Optional[str]) -> None:
    write("listing update: %s (design %s), reason %s" % (plan.slug, state.design_id, plan.reason))
    write("  current:     %s, listing %s, version %s" % (
        _money(state.price_cents),
        {True: "active", False: "paused", None: "absent"}[state.listing_active],
        state.current_history_id))
    write("               measured %s, extras %s" % (
        "%.2f g" % state.weight_g if state.weight_g is not None else
        "not yet (%s)" % (state.slice.status or "no slice"),
        _extras_text(state.extra_materials)))
    follows = state.price_follows_formula
    write("               Factory's formula for that gives %s: %s" % (
        _money(state.formula_price_cents),
        "the price follows the formula" if follows else
        "unknown" if follows is None else
        "the price does NOT follow it; it may have been set by hand, in which case the "
        "update will not move it and new extras may pause it"))
    write("  infill:      %s" % ("%d%%" % state.infill_percent if state.infill_percent else
                                   "not in Factory's readback (no print_settings); the new version "
                                   "carries no override, so it prints at the shop's 15%"))
    write("  geometry:    source %s sha256 %s" % (plan.source_primary_path, plan.source_primary_sha256))
    write("               live version made from %s (%s)" % (
        state.live_primary_sha256 or "an unrecorded primary",
        "same" if state.live_primary_sha256 == plan.source_primary_sha256 else "different"))
    write("  new extras:  %s = %s" % (_extras_text(plan.extra_materials), _money(plan.extras_cents)))
    if plan.predicted_weight_g is not None:
        write("  predicted:   %.2f g (%s) -> %s" % (
            plan.predicted_weight_g, plan.predicted_weight_source, _money(plan.predicted_price_cents)))
    else:
        write("  predicted:   unknown (no --predicted-grams)")
    write("  sends:       POST /designs/%s/import (no extras), waits for its slice, then "
          "PUT /designs/%s/extra-materials" % (plan.slug, plan.slug))
    if problems:
        write("  refused:")
        for problem in problems:
            write("    - %s" % problem)
    write("  confirmation: %s" % (code or "none (the update cannot run)"))


def _reconcile_publish(
    args: argparse.Namespace,
    environment: Optional[Mapping[str, str]],
    transports: Mapping[str, Any],
    write: Any,
) -> int:
    """Settle an unknown publish intent by readback alone (ADR 0097, decision 7)."""

    path = ledger_path(args.reconcile_publish, environment)
    if not path.is_file():
        raise ContractError("no direct-publish ledger for %s at %s" % (args.reconcile_publish, path))
    ledger = EffectLedger(path)
    publish = ledger.latest(args.reconcile_publish, "factory-publish")
    draft_intent = ledger.latest(args.reconcile_publish, "factory-import")
    if publish is None or draft_intent is None or draft_intent.receipt is None:
        raise ContractError("%s has no import receipt and publish intent to reconcile"
                            % args.reconcile_publish)
    write("reconcile:     %s publish intent is %s (%s)" % (
        args.reconcile_publish, publish.state, publish.error or "no error recorded"))
    if publish.state not in ("sending", "unknown"):
        write("nothing to reconcile")
        return 0
    session = _session(args.inventor, environment, transports, read_only=True)
    transition = FactoryPublicTransition(ledger, session)
    receipt = transition.publish(draft_intent.receipt)
    settled = ledger.latest(args.reconcile_publish, "factory-publish")
    write("reconciled:    publish intent is now %s" % settled.state)
    write("slug: %s" % receipt.slug)
    write("public: %s" % receipt.details.get("page_url", "https://www.autonomous.ai/toys/product/" + receipt.slug))
    write("listing: %s %s, version %s" % (
        _money(receipt.listing_price_cents),
        "active" if receipt.listing_active else "not active", receipt.published_history_id))
    return 0


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    environment: Optional[Mapping[str, str]] = None,
    transports: Optional[Mapping[str, Any]] = None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    args = _parser().parse_args(argv)
    write = lambda line="": print(line, file=out)  # noqa: E731
    try:
        if args.reconcile_publish:
            if args.cad_dir or args.archive or args.update_listing or args.live:
                raise ContractError("--reconcile-publish takes only --inventor")
            return _reconcile_publish(args, environment, transports or {}, write)
        if args.cad_dir is None and args.archive is None:
            raise ContractError("pass --cad-dir or --archive")
        if args.reimport_slug:
            raise ContractError(
                "--reimport-slug is retired: append a version to the public design with "
                "--update-listing %s --reason fix|reprice (ADR 0097)" % args.reimport_slug
            )
        updating = args.update_listing is not None
        if updating and args.reason is None:
            raise ContractError("--update-listing needs --reason fix or --reason reprice")
        if not updating and (args.reason or args.confirm or args.predicted_grams is not None
                             or args.published_archive):
            raise ContractError("--reason, --confirm, --predicted-grams and --published-archive "
                                "go with --update-listing")
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
        record = None
        published = None
        if updating:
            record = _update_record(args, source)
            home = default_workshop_home(environment)
            # A Workshop run's Release keeps its receipt in state/<wish-id>/.
            published = published_design(
                (home / "direct-publish", home / "state"), args.update_listing
            )
            if args.product_id and args.product_id != published.product_id:
                raise ContractError(
                    "%s was published as product id %s; an update keeps that id, not %s"
                    % (args.update_listing, published.product_id, args.product_id)
                )
            product_id = published.product_id
        else:
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
                display_only=args.display_only,
                bought=_pairs(args.bought, "--bought"),
                part_prices=_part_prices(args.part_price),
                sealed_bought=_sealed_bought(args, source),
            )
            handoff = build_release_handoff(
                staged.context, staged.release_root, staged.release_manifest
            )
            _describe(
                write, live=args.live, source=source, product_id=product_id,
                inventor=args.inventor, display_name=display_name, staged=staged,
                handoff=handoff, evidence=evidence, environment=environment,
                updating=updating, ledger_file=published.ledger if published is not None else None,
            )
            if updating:
                assert record is not None and published is not None
                return _run_update(
                    args, write, source=source, packed=packed, evidence=evidence,
                    environment=environment, transports=transports or {},
                    product_id=product_id, record=record, primary_step=primary_step,
                    staged=staged, handoff=handoff, sleeper=sleeper, clock=clock,
                    ledger_file=published.ledger or ledger_path(product_id, environment),
                )
            blockers = _blockers(args, source, packed, evidence, environment,
                                 product_id=product_id, title=title)
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
                sleeper=sleeper, clock=clock,
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


def _update_blockers(
    args: argparse.Namespace,
    packed: Optional[str],
    evidence: EvidenceStatus,
    environment: Optional[Mapping[str, str]],
) -> list[str]:
    """What stops a Listing Update before any credential is read."""

    blockers = []
    if packed is not None and packed != args.inventor:
        blockers.append(
            "archive was packed for Inventor %s; re-pack it with `toy_archive pack "
            "--inventor %s`" % (packed, args.inventor)
        )
    # A reprice republishes the live printed geometry, which the preview
    # proves by hash, so it needs no new gate run. A fix changes it.
    if args.reason == "fix" and not evidence.acceptable:
        blockers.append("a fix needs gate evidence, and it is %s: %s"
                        % (evidence.state, "; ".join(evidence.problems)))
    if not inventor_credential_file(args.inventor, environment).exists():
        blockers.append("no Factory credential for Inventor %s; run `workshop login %s`"
                        % (args.inventor, args.inventor))
    return blockers


def _run_update(
    args: argparse.Namespace,
    write: Any,
    *,
    source: DirectSource,
    packed: Optional[str],
    evidence: EvidenceStatus,
    environment: Optional[Mapping[str, str]],
    transports: Mapping[str, Any],
    product_id: str,
    record: Mapping[str, Any],
    primary_step: str,
    staged: Any,
    handoff: Mapping[str, Any],
    sleeper: Callable[[float], None],
    clock: Callable[[], float],
    ledger_file: Path,
) -> int:
    blockers = _update_blockers(args, packed, evidence, environment)
    if blockers:
        write("listing update: refused")
        for blocker in blockers:
            write("  - %s" % blocker)
        if args.live:
            raise ContractError("--live refused: %s" % "; ".join(blockers))
        write("preview stopped before any Factory read")
        return 0
    plan = _update_plan(args, source, record, primary_step, staged)
    ledger = EffectLedger(ledger_file)
    updater = FactoryListingUpdate(
        ledger,
        _session(args.inventor, environment, transports, read_only=not args.live),
        sleeper=sleeper, clock=clock,
    )
    if not args.live:
        state, problems, code = updater.preview(plan)
        _describe_preview(write, plan, state, problems, code)
        pending = updater.pending(product_id)
        if pending is not None and pending.state in ("sending", "unknown"):
            write("  pending:     an earlier update (code %s) is %s: %s" % (
                pending.request["listing_update"].get("confirmation_code"),
                pending.state, pending.error))
        write("preview complete; nothing was sent")
        if code and not problems:
            write("to run it: the same command with --live --confirm %s" % code)
        return 0
    if not args.confirm:
        raise ContractError("--update-listing --live needs --confirm CODE from this update's preview")
    receipt = updater.run(
        product_id=product_id, plan=plan,
        bindings=_update_bindings(staged, handoff), confirm=args.confirm,
    )
    version = listing_update_version(receipt)
    write("slug: %s" % receipt.slug)
    write("public: %s" % receipt.details["page_url"])
    write("version: %s (was %s)" % (version["history_id"], version["base_history_id"]))
    write("price: %s -> %s (predicted %s)%s" % (
        _money(version["price_before_cents"]), _money(version["price_after_cents"]),
        _money(version["predicted_price_cents"]),
        listing_price_note(version)))
    write("measured: %s g -> %s g (predicted %s g)" % (
        version["weight_before_g"], version["weight_after_g"], version["predicted_weight_g"]))
    write("listing-update-record: %s" % json.dumps(version, sort_keys=True, separators=(",", ":")))
    updated = append_publication_version(record, version)
    write("publication-record: %s" % json.dumps(updated, sort_keys=True, separators=(",", ":")))
    if args.archive is not None:
        # The listing changed; the archive records it so the next update
        # starts from this version. A --cad-dir update's archive is repacked
        # by its packer from the printed record.
        try:
            changed = record_archive_publication(args.archive, updated)
        except (ContractError, OSError) as exc:
            write("archive: not updated (%s); write the publication-record above into "
                  "publication/PUBLICATION.json and reseal it" % exc)
        else:
            write("archive: %s publication/PUBLICATION.json" % ("updated" if changed else "already records"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
