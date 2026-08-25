"""The creative seams this inventor owns, bridged to the text2game pipeline.

Make adopts the operator-run text2game run whose slug equals the Wish
``product_id`` and imports its files as the exact product artifact. Playtest
binds that run's recorded verdicts — AI referee/critic rounds, CAD contract
gate + fit probes, slicer analysis — as artifact-bound evidence. Anything the
pipeline has not actually produced becomes a typed wait, never an invented
result; in particular, the lane's >=1,000 seeded-game simulation is reported
only when a real ``game_simulation.json`` exists.
"""

from inventor_workshop import (
    Feedback,
    Made,
    MakeContext,
    Need,
    Playtest,
    PlaytestContext,
    PlaytestResult,
    Playtested,
    WaitingFor,
    build_artifact_manifest,
)

from . import text2game_bridge as bridge


def make(context: MakeContext) -> Made:
    root = bridge.pipeline_root()
    slug = context.wish.product_id
    run = bridge.run_dir(root, slug)
    if context.feedback:
        codes = ", ".join(sorted({item.code for item in context.feedback})) or "playtest feedback"
        raise WaitingFor(
            Need(
                "make",
                "text2game-revision",
                "Playtest returned actionable feedback (%s); a revision is a paid, "
                "operator-run pipeline round, not something Make may improvise." % codes,
                "Revise the run: cd %s && ./text2game --slug %s --phase all --force, "
                "then run this Wish again to import the revised bytes." % (root, slug),
            )
        )
    if not bridge.pipeline_present(root):
        raise WaitingFor(
            Need(
                "make",
                "text2game-pipeline",
                "The text2game pipeline is not installed at %s." % root,
                "Install the pipeline there or point the %s environment variable "
                "at its checkout." % bridge.PIPELINE_ROOT_ENV,
            )
        )
    if run is None:
        raise WaitingFor(
            Need(
                "make",
                "text2game-run",
                "Wish product_id %r is not a text2game run slug." % slug,
                "Name the Wish product_id after the pipeline run slug "
                "(lowercase letters, digits, hyphens).",
            )
        )
    missing = bridge.missing_product_files(run)
    if missing:
        raise WaitingFor(
            Need(
                "make",
                "text2game-run",
                "Run %s has no complete product yet (missing: %s)." % (run, ", ".join(missing)),
                "Complete the run: cd %s && ./text2game --slug %s --phase all, "
                "then run this Wish again." % (root, slug),
            )
        )
    context.workspace.mkdir(parents=True, exist_ok=True)
    artifact_root = context.workspace / "artifact"
    stats = bridge.import_product(run, artifact_root)
    title, summary = bridge.title_and_summary(run, context.wish.objective)
    product = {
        "schema_version": 1,
        "title": title,
        "summary": summary,
        "lane": bridge.LANE,
        "source": {"pipeline": "text2game", "run": slug, "round": context.round},
        "part_designs": stats["part_sources"],
        "meshes": stats["meshes"],
    }
    return Made.from_root(artifact_root, product)


def playtest(context: PlaytestContext) -> Playtested:
    root = bridge.pipeline_root()
    source = context.made.product.get("source") or {}
    slug = source.get("run") or context.wish.product_id
    run = bridge.run_dir(root, str(slug))
    missing = bridge.missing_evidence_files(run) if run is not None else list(bridge.EVIDENCE_FILES)
    records = {}
    if not missing:
        for name in ("phase1.json", "gate.json", "fit.json", "slice_report.json"):
            records[name] = bridge.load_json(run, name)
        missing = [name for name, value in records.items() if value is None]
    if missing:
        raise WaitingFor(
            Need(
                "playtest",
                "text2game-evidence",
                "The text2game run for %r has no readable recorded verdicts "
                "(missing or unparsable: %s)." % (slug, ", ".join(missing)),
                "Complete the pipeline run (phases 1-3) so phase1/gate/fit/slice "
                "verdicts exist, then run this Wish again.",
            )
        )
    context.workspace.mkdir(parents=True, exist_ok=True)
    bridge.copy_evidence(run, context.workspace)
    artifact_sha = context.made.artifact_sha256
    results = []
    feedback = []

    def bind(capability, passed, evidence, roles, evaluator, config, source_name):
        # The release policy verifies each result against its own sealed JSON
        # document: the evidence names the exact Make bytes, the AI roles that
        # produced it, and the recorded pipeline verdict it came from.
        evidence = dict(evidence)
        evidence["artifact_sha256"] = artifact_sha
        evidence["agent_roles"] = list(roles)
        evidence["source"] = source_name
        evidence_name = "%s.result.json" % capability
        bridge.write_result_document(context.workspace / evidence_name, evidence)
        results.append(
            PlaytestResult.create(
                capability,
                passed,
                artifact_sha,
                evidence,
                evaluator,
                bridge.BRIDGE_VERSION,
                bridge.config_sha256(config),
                evidence_name,
                bridge.sha256_file(context.workspace / evidence_name),
            )
        )

    referee_passed, referee_evidence = bridge.referee_verdict(records["phase1.json"])
    bind(
        "agent-playtest",
        referee_passed,
        referee_evidence,
        ("referee-player", "critic", "evaluator"),
        "text2game-referee",
        {"run": str(slug), "phase": 1},
        "phase1.json",
    )
    if not referee_passed:
        feedback.append(
            Feedback(
                "referee-not-accepted",
                "mechanics",
                "improve",
                "The pipeline's referee/critic loop kept no round of this design.",
                "Run another design round and keep a round before importing the product.",
                ("phase1.json", "referee.md"),
            )
        )
    elif referee_evidence["critic_high"] or not referee_evidence["referee_clean"]:
        feedback.append(
            Feedback(
                "referee-residue",
                "mechanics",
                "note",
                "The AI referee/critic left open findings after the allowed passes.",
                "Keep them on the print kit's watch-at-the-table list; revise only if "
                "customer Reviews confirm them.",
                ("referee.md",),
            )
        )

    gate_passed, gate_evidence, fit_high = bridge.gate_verdict(
        records["gate.json"], records["fit.json"]
    )
    bind(
        "mechanical-test",
        gate_passed,
        gate_evidence,
        ("cad-measure-agent", "fit-probe-agent"),
        "text2game-contract-gate",
        {"run": str(slug), "phase": 3, "checks": ["watertight", "bodies", "fit"]},
        "gate.json",
    )
    for item in fit_high[:5]:
        feedback.append(
            Feedback(
                "fit-%s" % item.get("code", "contract"),
                "geometry",
                "improve",
                item.get("message", "A part pair violates its fit contract."),
                "Reshape the mated parts until the measured gap meets the contract "
                "in parts_index.json.",
                ("fit.json",),
            )
        )

    slice_passed, slice_evidence = bridge.slice_verdict(records["slice_report.json"])
    bind(
        "print-test",
        slice_passed,
        slice_evidence,
        ("slicer-agent", "plate-packing-agent"),
        "text2game-slicer",
        {"run": str(slug), "profile": "petg"},
        "slice_report.json",
    )

    simulation = bridge.simulation_verdict(run)
    if simulation is not None:
        sim_passed, sim_evidence = simulation
        bind(
            "game-simulation",
            sim_passed,
            sim_evidence,
            sim_evidence.get("agent_roles")
            or ("optimizing-player", "adversarial-player"),
            "text2game-simulation",
            {"run": str(slug)},
            bridge.SIMULATION_FILE,
        )
    # With no mass simulation recorded, no game-simulation result is returned:
    # the shared invented-games policy then waits for that capability instead
    # of accepting a conveniently named pass.

    if not all(result.passed for result in results) and not any(
        item.severity in ("improve", "block") for item in feedback
    ):
        failed = ", ".join(result.playtest_id for result in results if not result.passed)
        feedback.append(
            Feedback(
                "recorded-verdict-failed",
                "mechanics",
                "improve",
                "Recorded pipeline verdicts failed for: %s." % failed,
                "Re-run the failing pipeline phase and import the revised run.",
                tuple(bridge.EVIDENCE_FILES),
            )
        )

    evidence_manifest = build_artifact_manifest(
        context.workspace, created_at="content-addressed"
    )
    return Playtested(
        Playtest(
            context.made.artifact_manifest,
            tuple(results),
            evidence_manifest=evidence_manifest,
        ),
        tuple(feedback),
    )
