#!/usr/bin/env python3
"""Publish a CAD project built outside Workshop to Factory, as Spark would.

Reads a CAD project directory (``--cad-dir``, what autonomous-product-to-cad's
``skills/toy-archive/scripts/publish`` stages) or a packed public toy archive
(``--archive``), stages the Made tree and schema-4 Release carrier Spark
publishes, and builds the exact Factory handoff ZIP. Without ``--live``
nothing is read from the credential store and nothing is sent: it prints what
would be uploaded.

``--live`` runs the host's existing Factory adapter unchanged: the Inventor's
stored credential, a durable effect ledger under
``$WORKSHOP_HOME/direct-publish/<product-id>/``, a private draft import with
authenticated readback, publication, and public readback of the exact
metadata anchor. It prints ``public: <url>`` on success. Re-running the same
bytes reconciles through the ledger instead of creating a second design.

No Workshop gate runs: no Wish, Make gate, print gate, review or Playtest.
See docs/PUBLISH_DIRECT.md.
"""

from __future__ import annotations

import argparse
import io
import sys
import tempfile
import zipfile
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
    DirectSource,
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
GATES_NOT_RUN = (
    "Wish and Inventor selection",
    "Make CAD gate and print gates (verify_project)",
    "Component and signature reviews",
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
    parser.add_argument("--reimport-slug", metavar="SLUG",
                        help="not supported: the host adapter never re-imports a public design")
    parser.add_argument("--inventors", type=Path, default=REPOSITORY / "inventors",
                        help=argparse.SUPPRESS)
    parser.add_argument("--live", action="store_true", help="publish; default is an offline dry run")
    return parser


def _source(args: argparse.Namespace) -> DirectSource:
    if args.archive is not None:
        return load_public_toy_archive(args.archive)
    return load_cad_project(args.cad_dir)


def _product_id(args: argparse.Namespace, source: DirectSource) -> str:
    if args.product_id:
        return args.product_id
    name = source.root.name
    if source.kind == "public-toy-archive" and name.startswith(args.inventor + "-"):
        name = name[len(args.inventor) + 1:]
    return slugify(name)


def _describe(
    out: TextIO,
    *,
    live: bool,
    source: DirectSource,
    product_id: str,
    inventor: str,
    display_name: str,
    staged: Any,
    handoff: Mapping[str, Any],
    environment: Optional[Mapping[str, str]],
) -> None:
    metadata = handoff["metadata"]
    content = handoff["content"]
    write = lambda line="": print(line, file=out)  # noqa: E731
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
    write("credential:    %s (%s)" % (
        credential, "present" if credential.exists() else
        "absent; --live refuses until `workshop login %s`" % inventor))
    write("ledger:        %s" % ledger_path(product_id, environment))
    write("gates not run by Workshop: %s" % "; ".join(GATES_NOT_RUN))


def _publish_live(
    staged: Any,
    *,
    product_id: str,
    inventor: str,
    environment: Optional[Mapping[str, str]],
    transports: Mapping[str, Any],
) -> Any:
    # Factory shows the authorizing account as the public author, so a
    # direct publication never falls back to a host-wide account.
    if not inventor_credential_file(inventor, environment).exists():
        raise ContractError(
            "no Factory credential for Inventor %s; run `workshop login %s`"
            % (inventor, inventor)
        )
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


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    environment: Optional[Mapping[str, str]] = None,
    transports: Optional[Mapping[str, Any]] = None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.reimport_slug:
            raise ContractError(
                "--reimport-slug is not supported: Workshop's Factory adapter never "
                "appends a version to a public design, and a direct tool will not add "
                "a second effect path"
            )
        source = _source(args)
        if args.live and source.publication is not None:
            page = (source.publication.get("publication") or {}).get("page_url")
            raise ContractError(
                "archive already records a publication (%s); publishing again would "
                "create a second design" % page
            )
        product_id = _product_id(args, source)
        readme_title, readme_paragraph = readme_summary(source.readme or b"")
        title = args.title or readme_title
        summary = args.summary or readme_paragraph
        if not title or not summary:
            raise ContractError("no --title/--summary and the project README does not supply one")
        display_name = inventor_name(args.inventors, args.inventor)
        primary_step = args.primary_step or source.entry_step()
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
            )
            handoff = build_release_handoff(
                staged.context, staged.release_root, staged.release_manifest
            )
            _describe(
                out, live=args.live, source=source, product_id=product_id,
                inventor=args.inventor, display_name=display_name,
                staged=staged, handoff=handoff, environment=environment,
            )
            if source.publication is not None:
                print("warning: archive already records a publication; --live is refused", file=out)
            if not args.live:
                print("dry run complete; re-run with --live to publish", file=out)
                return 0
            receipt = _publish_live(
                staged, product_id=product_id, inventor=args.inventor,
                environment=environment, transports=transports or {},
            )
        print("slug: %s" % receipt.slug, file=out)
        print("public: %s" % receipt.details["page_url"], file=out)
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
