import hashlib
import json
import tempfile
import tomllib
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.runtime.agent_assets import (
    MAX_INVENTOR_AGENT_MANIFEST_BYTES,
    MAX_INVENTOR_AGENT_TASTE_BYTES,
    MAX_INVENTOR_CUSTOM_AGENT_BYTES,
    InventorCustomAgentBinding,
    InventorSkillBinding,
    inventor_custom_agent_bytes,
    parse_inventor_custom_agent_bytes,
    product_run_agent_assets,
)


REPOSITORY = Path(__file__).resolve().parents[2]
ALICE_SKILLS = (
    InventorSkillBinding(
        name="alice-inventor",
        path="skills/alice-inventor",
        artifact_sha256="a" * 64,
    ),
    InventorSkillBinding(
        name="alice-miniatures",
        path="skills/alice-miniatures",
        artifact_sha256="b" * 64,
    ),
)


def manifest_bytes(
    *,
    inventor_id="alice",
    skills=ALICE_SKILLS,
    schema_version=8,
    extra=None,
):
    value = {
        "schema_version": schema_version,
        "id": inventor_id,
        "status": "experimental",
        "source": {"kind": "local"},
        "extensions": [
            {"kind": "codex-skill", **skill.to_dict()} for skill in skills
        ],
    }
    if extra:
        value.update(extra)
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


ALICE_TASTE = (
    b"---\n"
    b"name: Alice\n"
    b"description: Makes exact personal classics.\n"
    b"---\n\n# Alice\n\nReject generic decoration.\n"
)


class ProductRunAgentAssetsTest(unittest.TestCase):
    def test_source_checkout_uses_product_run_instructions_not_root_agents(self):
        assets = product_run_agent_assets(REPOSITORY)

        self.assertEqual(assets.source, "repository")
        self.assertEqual(
            assets.constitution,
            (REPOSITORY / ".agents" / "product-run" / "AGENTS.md").resolve(),
        )
        self.assertEqual(
            assets.skill_root,
            (
                REPOSITORY
                / ".agents"
                / "product-run"
                / ".agents"
                / "skills"
                / "autonomous-workshop"
            ).resolve(),
        )
        self.assertNotEqual(assets.constitution, (REPOSITORY / "AGENTS.md").resolve())
        self.assertRegex(assets.sha256, r"^[0-9a-f]{64}$")
        self.assertTrue(
            (
                assets.skill_root
                / "references"
                / "spark-economics-v1.md"
            ).is_file()
        )
        self.assertTrue(
            (
                assets.skill_root
                / "references"
                / "spark-economics-v3.md"
            ).is_file()
        )
        self.assertTrue(
            (
                assets.skill_root
                / "references"
                / "spark-economics-v2.md"
            ).is_file()
        )
        self.assertTrue(
            (
                assets.skill_root
                / "references"
                / "deep-economics-v1.md"
            ).is_file()
        )
        self.assertTrue(
            (
                assets.skill_root
                / "references"
                / "deep-economics-v2.md"
            ).is_file()
        )
        self.assertTrue(
            (
                assets.skill_root
                / "references"
                / "deep-economics-v3.md"
            ).is_file()
        )
        self.assertTrue(
            (
                assets.skill_root
                / "references"
                / "deep-economics-v4.md"
            ).is_file()
        )
        for reference in (
            "deep-economics-v5.md",
            "deep-economics-v6.md",
            "deep-economics-v7.md",
            "deep-economics-v8.md",
            "deep-economics-v9.md",
            "make.md",
            "spark-economics-v4.md",
            "visual-reference-inspection.md",
            "wish-expansion.md",
            "playtest.md",
        ):
            with self.subTest(reference=reference):
                self.assertTrue(
                    (assets.skill_root / "references" / reference).is_file()
                )

    def test_current_make_and_playtest_guidance_are_stage_scoped(self):
        reference_root = (
            REPOSITORY
            / ".agents"
            / "product-run"
            / ".agents"
            / "skills"
            / "autonomous-workshop"
            / "references"
        )
        make = " ".join(
            (reference_root / "make.md").read_text(encoding="utf-8").split()
        )
        playtest = " ".join(
            (reference_root / "playtest.md").read_text(encoding="utf-8").split()
        )

        for required in (
            "smallest viable parametric baseline",
            "every distinct physical component",
            "--component part_<role>.step.py",
            "--require-component-passes",
            "STEP is the only geometry format the toolchain writes",
            "Call a product print-ready only behind a passing `--print-gates` run",
            "one canonical final render family",
            "independent native critic",
            "blind held",
            ".make-proof-ready",
            "The trusted host owns the isolated fresh rebuild",
            "Spark and Forge truthfully record Playtest as not run",
        ):
            with self.subTest(reference="make", required=required):
                self.assertIn(required, make)
        for required in (
            "Quest Playtest",
            "exact sealed Made revision",
            "product_artifact_sha256",
            "returning to Make",
            "returning directly to Invent",
            "--run-root . playtest",
        ):
            with self.subTest(reference="playtest", required=required):
                self.assertIn(required, playtest)
        # ADR 0063 restores the gates but not the Workshop-local preflight mode.
        self.assertNotIn("--print-preflight", make)
        self.assertIn("check_thickness", make)
        self.assertNotIn("Make contract", playtest)

    def test_spark_make_expands_the_wish_without_replacing_it(self):
        product_run = REPOSITORY / ".agents" / "product-run"
        reference_root = (
            product_run / ".agents" / "skills" / "autonomous-workshop" / "references"
        )

        def text(path):
            return " ".join(path.read_text(encoding="utf-8").split())

        make = text(reference_root / "make.md")
        expansion = text(reference_root / "wish-expansion.md")
        constitution = text(product_run / "AGENTS.md")

        for required in (
            "[wish expansion](wish-expansion.md)",
            "`<cad-project>/WISH-EXPANSION.md`",
            "For Spark outside Contract Mode and outside an early-proof turn",
            "The Wish itself is unchanged and still decides",
            "When `WISH-EXPANSION.md` exists, also enumerate",
            "a choice the Wish does not require never fails a faithful build",
        ):
            with self.subTest(reference="make", required=required):
                self.assertIn(required, make)
        # The expansion is written before source, so the pointer precedes the
        # component funnel it feeds.
        self.assertLess(
            make.index("[wish expansion](wish-expansion.md)"),
            make.index("--component part_<role>.step.py"),
        )
        for required in (
            "new Spark Make only, outside Contract Mode and outside an early-proof turn",
            "The expansion exists to generate a 3D model",
            "before the first `part_<role>.step.py`",
            "What must be recognisable",
            "negative spaces that must stay open",
            "One overall size in mm",
            "generic shortcuts to avoid",
            "keyed locating joints",
            "record the tradeoff in `GEOMETRY-NOTES.md`",
            "The sealed Wish is unchanged and remains the objective",
            "Keep every explicit Wish requirement, value and prohibition exactly",
            "Do not add subjects, features, lights, electronics or mechanisms",
            "never a reason to fail a faithful build",
            "name its construction family",
            "## Reading the references first",
            "`measure_image.py`",
            "`## Reference reading`",
            "`[observed]`",
            "`[inferred]`",
            "One view fixes only two dimensions",
            "Take size from the Wish or a known object in frame, never from pixels",
            "name the conflict and follow the Wish",
            "say once that the expansion is text-derived",
            "at the natural seams the object already has",
            "translate every style word of the Wish",
            "Using the selected Inventor's Taste to decide the values",
            "**Section shape:**",
            "**Edges:**",
            "**Silhouette:**",
            "**Proportion:**",
            "Carry them into the blind review's `critical_form_requirements`",
            "First obtain references as",
            "its kind (sealed, found with its URL, or generated)",
            "Do not plan paired halves of one form",
        ):
            with self.subTest(reference="wish-expansion", required=required):
                self.assertIn(required, expansion)
        # A print half is not a component: halves double component rounds
        # and thicken detail, so a planar split comes last in the overhang
        # repair order, after reorienting and reshaping the piece.
        for required in (
            "It is not a print half",
            "before `check_overhang` has failed on that whole piece",
            "1. Reorient the piece's print pose.",
            "2. Reshape the unsupported underside",
            "3. Move or add a split at a natural seam",
            "4. Only then split the single form on a plane",
        ):
            with self.subTest(reference="make", required=required):
                self.assertIn(required, make)
        self.assertLess(
            make.index("1. Reorient the piece's print pose."),
            make.index("4. Only then split the single form on a plane"),
        )
        self.assertIn("never a pre-planned `_a`/`_b` print half", constitution)
        # The rough whole is previewed once, after every worker's first
        # passing round and before any Component Review, so placement between
        # parts is fixed before reviews lock them (ADR 0081, ADR 0087).
        for required in (
            "preview the whole object once",
            "before you ask any reviewer",
            "--preview-assembly",
            "Preview again only after a Component's size or placement changes",
            "A preview is evidence only: not a round, not a pass",
        ):
            with self.subTest(reference="make", required=required):
                self.assertIn(required, make)
        self.assertLess(
            make.index("preview the whole object once"),
            make.index("Read each round summary's `shape` and `lock` lines"),
        )
        self.assertIn("run one `make_round --preview-assembly` of the rough whole", constitution)
        # Style lives in shape, decided by the Inventor's Taste; the step and
        # the reference sourcing must survive compaction in the constitution.
        self.assertIn("proportion rules by the Inventor's Taste", constitution)
        self.assertIn("generated when the runtime has a built-in image tool", constitution)
        inspection = text(reference_root / "visual-reference-inspection.md")
        for required in (
            "every Spark Make outside Contract Mode obtains references",
            "For an original subject, search for the subject's real anatomy",
            "never a likeness target",
            "never copy one artist's design",
            "Codex's `image_gen`",
            "never call an image API with a key or script one",
            "it never outranks the Wish text or a sealed reference",
            "Do not pass them to `make_round --ref`",
        ):
            with self.subTest(reference="visual-reference-inspection", required=required):
                self.assertIn(required, inspection)
        # Compaction drops references but re-emits the constitution, so the
        # step itself must survive there.
        self.assertIn("`<cad-project>/WISH-EXPANSION.md`", constitution)
        self.assertIn("the sealed Wish stays unchanged and still decides", constitution)

    def test_make_session_guidance_saves_tokens_without_withholding_guidance(self):
        make = " ".join(
            (
                REPOSITORY
                / ".agents/product-run/.agents/skills/autonomous-workshop"
                / "references/make.md"
            ).read_text(encoding="utf-8").split()
        )
        make_round = " ".join(
            (
                REPOSITORY / "src/workshop/make/skills/make-round/SKILL.md"
            ).read_text(encoding="utf-8").split()
        )
        start = make.index("## Keep the session small")
        section = make[start : make.index("## Ownership and pipeline", start)]

        for required in (
            "`yield_time_ms: 300000`",
            "upper bound, not a",
            "continue that cell with `wait` at the same large yield",
            "`1000` is not a waiting value",
            "omit `yield_time_ms`",
            "Never put a `sleep` between polls",
            "one `wait_agent` at a long timeout",
            "takes precedence over them",
            "Always re-read what can change",
            "Seal each build group with `make-group`",
            "never on unchanged bytes",
        ):
            with self.subTest(required=required):
                self.assertIn(required, section)
        # Token rules may skip only later-stage contracts. make-playtest.md
        # carries the current build-group and vault-lead contract, and the
        # others hold CAD pitfalls and Spark concept guidance Make relies on.
        for withheld in ("make-playtest.md", "run-cost.md", "invent.md"):
            with self.subTest(withheld=withheld):
                self.assertNotIn(withheld, section)
        self.assertIn(
            "--cad-verification-path <cad-project>/measure/verification-pipeline.md",
            make,
        )
        # A compaction drops references/make.md from the session but keeps the
        # constitution, so the waiting rule has to exist in both.
        constitution = " ".join(
            (
                REPOSITORY / ".agents/product-run/AGENTS.md"
            ).read_text(encoding="utf-8").split()
        )
        for required in (
            "Wait for a long command in as few requests as possible",
            "`yield_time_ms: 300000`",
            "`1000` is not a waiting value",
            "Never sleep between polls",
            "one `wait_agent` at a long timeout",
        ):
            with self.subTest(constitution=required):
                self.assertIn(required, constitution)
        self.assertIn("`yield_time_ms: 300000`", make_round)
        # ADR 0077 raised every wait to 300000 ms; no 30000 ms wait survives.
        for text in (section, constitution, make_round):
            self.assertNotIn("`yield_time_ms: 30000`", text)
        self.assertIn("continue a yielded `exec` cell with", make_round)
        self.assertIn("Omit `yield_time_ms` before writing a small one", make_round)

    def test_make_hands_each_component_to_a_worker_and_a_root_owned_reviewer(self):
        make = " ".join(
            (
                REPOSITORY
                / ".agents/product-run/.agents/skills/autonomous-workshop"
                / "references/make.md"
            ).read_text(encoding="utf-8").split()
        )
        for required in (
            "`component-worker`",
            "`component-reviewer`",
            "one worker per Component",
            "only that Component's Design Contract rows",
            "10 lines or fewer",
            "Each Component has one reviewer",
            # Issue #77: one bound reviewer, a fixed request, an unedited answer.
            "Never spawn a second reviewer for a Component",
            "The review request has one fixed shape and nothing else",
            "never edit, filter or summarize the answer",
            "`reviewer` is the reviewer's native agent id",
            'tell the worker only "review recorded for round N"',
            "Neither you nor a worker views a Component's rendered rounds",
            "Workers never edit a shared file",
            "--record-review <review.json>",
            "ADR 0077",
            # ADR 0080: the worker authors, only it runs component rounds,
            # and a contract contradiction is a need.
            "In Spark you author no Component",
            "The worker writes the first draft",
            "may view its own sealed reference image once",
            "Only a `component-worker` runs a component round",
            "an Inventor never runs `make_round`",
            "return a `waiting` need that quotes both statements",
        ):
            with self.subTest(required=required):
                self.assertIn(required, make)
        constitution = " ".join(
            (REPOSITORY / ".agents/product-run/AGENTS.md").read_text(
                encoding="utf-8"
            ).split()
        )
        self.assertIn("`component-worker`", constitution)
        self.assertIn("`component-reviewer`", constitution)
        self.assertIn("only a Component Worker runs a Component's", constitution)
        skill = " ".join(
            (
                REPOSITORY
                / ".agents/product-run/.agents/skills/autonomous-workshop/SKILL.md"
            ).read_text(encoding="utf-8").split()
        )
        self.assertIn(
            "two statements of the sealed Design Contract cannot both hold", skill
        )

    def test_the_root_never_ends_its_turn_while_a_worker_or_reviewer_runs(self):
        # Issue #85: an ended turn is not a wait; the session can end before
        # a background worker reports, losing its round.
        make = " ".join(
            (
                REPOSITORY
                / ".agents/product-run/.agents/skills/autonomous-workshop"
                / "references/make.md"
            ).read_text(encoding="utf-8").split()
        )
        constitution = " ".join(
            (REPOSITORY / ".agents/product-run/AGENTS.md").read_text(
                encoding="utf-8"
            ).split()
        )
        for name, text in (("make", make), ("constitution", constitution)):
            for required in (
                "Never end your turn while a Component Worker or a Component "
                "Reviewer request is still running",
                "end your turn only on a stage proposal, a recorded need",
                "or a host stop",
                "An ended turn is not a wait",
                "On Claude Code",
                "`timeout: 600000`",
                "scripts/wait_for.py",
            ):
                with self.subTest(name=name, required=required):
                    self.assertIn(required, text)

    def test_claude_code_waits_end_when_the_awaited_job_ends(self):
        # Issue #112: a fixed sleep keeps waiting after the job has ended.
        def text(*parts):
            return " ".join(REPOSITORY.joinpath(*parts).read_text(encoding="utf-8").split())

        make = text(".agents/product-run/.agents/skills/autonomous-workshop/references/make.md")
        constitution = text(".agents/product-run/AGENTS.md")
        make_round = text("src/workshop/make/skills/make-round/SKILL.md")
        for name, body in (("make", make), ("constitution", constitution), ("make-round", make_round)):
            with self.subTest(name=name):
                self.assertNotIn("time.sleep(300)", body)
                self.assertIn("wait_for.py", body)
                self.assertIn("On Claude Code", body)
                self.assertIn("returns as soon as", body)
        for name, body in (("make", make), ("constitution", constitution)):
            for required in (
                "--exit-file",
                "--timeout 300",
                "Never queue several waits in one turn",
                "echo $? >",
            ):
                with self.subTest(name=name, required=required):
                    self.assertIn(required, body)
        self.assertTrue(
            (REPOSITORY / ".agents/product-run/.agents/skills/autonomous-workshop"
             / "scripts/wait_for.py").is_file()
        )

    def test_the_reviewer_reads_the_contract_from_its_packet_and_lists_reference_conflicts(self):
        # ADR 0084: the Design Contract wins over a reference image.
        def text(*parts):
            return " ".join(REPOSITORY.joinpath(*parts).read_text(encoding="utf-8").split())

        reviewer = text("src/workshop/make/agents/component-reviewer.toml")
        for required in (
            "the round's visual packet path and its packet sha256",
            "The packet's `contract` holds",
            "the text of every Interface that names it",
            "The Design Contract wins",
            "list it under `reference_conflicts`, never under `differences`",
            "A review whose only findings are Reference Conflicts agrees",
            '"reference_conflicts": [{"file": "...", "reference": "...", "contract": "..."}]',
            "A difference whose repair would go below them is not a difference",
            "If only such differences remain, the review agrees",
        ):
            with self.subTest(reviewer=required):
                self.assertIn(required, reviewer)
        # A difference below the print limits is never written down as "keep as is".
        self.assertNotIn('write a difference smaller than them as "keep as is"', reviewer)
        self.assertNotIn('than that land, write "keep as is"', reviewer)
        self.assertIn('never write "keep as is"', reviewer)
        worker = text("src/workshop/make/agents/component-worker.toml")
        self.assertIn("`summary.json` also holds them, copied from the sealed contract", worker)
        make = text(".agents/product-run/.agents/skills/autonomous-workshop/references/make.md")
        for required in (
            "`visual-packet.json` path and its packet sha256 from the worker's report",
            "writes the Component's contract into the packet itself",
            "a Reference Conflict is not a difference, costs no shape round",
            "never reaches the worker",
        ):
            with self.subTest(make=required):
                self.assertIn(required, make)
        skill = text("src/workshop/make/skills/make-round/SKILL.md")
        self.assertIn("`reference_conflicts` (at most 12)", skill)
        design = text(".claude/skills/design-a-toy/SKILL.md")
        self.assertIn('Write the block as `"schema_version": 4`', design)
        self.assertIn("**Joint features.**", design)
        contract_format = text(".claude/skills/build-a-toy/CONTRACT-FORMAT.md")
        self.assertIn('"schema_version": 4', contract_format)
        self.assertIn("`text` (schema 4, required and non-empty, no length limit)", contract_format)

    def test_design_a_toy_checks_shared_faces_and_assembly_row_scope(self):
        # Issues #116 and #117: a shared-face sentence agrees with every named
        # Component's extents and Interface ranges, and an assembly row states
        # only what the assembled renders show.
        def text(*parts):
            return " ".join(REPOSITORY.joinpath(*parts).read_text(encoding="utf-8").split())

        design = text(".claude/skills/design-a-toy/SKILL.md")
        stage2 = design[design.index("## Stage 2"):design.index("## Stage 3 ")]
        for required in (
            "Then check every **shared face**.",
            "check that each named Component's `extents_mm` and every Interface range that places it allow it",
            "A Component thinner or thicker than its neighbours states its thickness in its own row.",
            "Then check every **assembly row**.",
            "An assembly-scoped requirement states only what renders of the assembled toy in its Display Pose show",
            "Move materials, filament types, print order, pauses, inserted parts and physical behaviour to the prose",
        ):
            with self.subTest(design=required):
                self.assertIn(required, stage2)
        self.assertIn("Run Stage 2's shared-face check again", design)
        contract_format = text(".claude/skills/build-a-toy/CONTRACT-FORMAT.md")
        for required in (
            "An `assembly` row states only what renders of the assembled toy in its Display Pose show",
            "agrees with each one's `extents_mm` and every Interface range that places it",
            "Every assembly row states only what the assembled renders show",
        ):
            with self.subTest(contract_format=required):
                self.assertIn(required, contract_format)

    def test_workers_drop_a_twice_refused_detail_and_reviewers_ask_for_placeable_detail(self):
        # Issue #86: a Detail Refusal is repaired from the summary, a detail
        # refused twice at one spot is left out, and the reviewer's limits
        # cover placement as well as size.
        def text(*parts):
            return " ".join(REPOSITORY.joinpath(*parts).read_text(encoding="utf-8").split())

        worker = text("src/workshop/make/agents/component-worker.toml")
        for required in (
            "the build fails once with every refusal",
            "lists each on a `refuse` line",
            "what passes there",
            "Repair every one in the same edit",
            "Two refusals are the limit: when a detail at the same spot is refused in two rounds",
            "leave it out of your code and name it, with its passing value, in your report",
            "Never model it by hand instead",
            "each detail you left out after two refusals",
        ):
            with self.subTest(worker=required):
                self.assertIn(required, worker)
        reviewer = text("src/workshop/make/agents/component-reviewer.toml")
        for required in (
            "a detail on another detail (a rivet on a band or a rim) needs a host wider than the "
            "detail plus 0.5 mm on each side",
            "no raised detail on a concave surface deeper than the detail's height",
            "copies in a row keep a gap of at least 0.5 mm (the min cut width)",
            "A repair that breaks a placement rule is not a difference either",
        ):
            with self.subTest(reviewer=required):
                self.assertIn(required, reviewer)

    def test_a_blocked_worker_records_a_blocked_report_the_root_clears_with_the_tool(self):
        # Issue #88: reporting and clearing go through make_round on both
        # runtimes, and the root has a rule for every way to clear one.
        def text(*parts):
            return " ".join(REPOSITORY.joinpath(*parts).read_text(encoding="utf-8").split())

        worker = text("src/workshop/make/agents/component-worker.toml")
        for required in (
            "a Contract Contradiction",
            "A print rule your rows state (the stance, \"no part needs support\") is a row too",
            "Record a Blocked Report first, then report blocked to the Manager",
            "--report-blocked <blocked.json>",
            "each row copied verbatim from your contract rows",
            "Follow it with a new component round, or, if it still cannot hold, a new Blocked Report",
            "If the decision waits on another Component, wait until the Manager wakes you again",
        ):
            with self.subTest(worker=required):
                self.assertIn(required, worker)
        make = text(".agents/product-run/.agents/skills/autonomous-workshop/references/make.md")
        for required in (
            "The same tool works on Codex and on Claude Code",
            "--clear-blocked <answer.json>",
            '**Decision**, `{"report": N, "decision": "<ruling>"}`',
            '"waits_on": "part_<other>.step.py"}`',
            "until that Component's next passing round",
            "Never leave a woken worker idle",
            '**Contract Contradiction**, `{"report": N, "need":',
            "Do not answer a blocked worker in prose alone",
            "the finalizer refuses the Make proposal, and the host refuses Make acceptance",
            "On Claude Code the host also refuses your turn end unless it ends on a recorded need",
            "--blocked-reports",
            "or while a Blocked Report is open",
        ):
            with self.subTest(make=required):
                self.assertIn(required, make)
        constitution = text(".agents/product-run/AGENTS.md")
        for required in ("make_round --report-blocked", "--clear-blocked", "--blocked-reports",
                         "it survives compaction"):
            with self.subTest(constitution=required):
                self.assertIn(required, constitution)
        skill = text("src/workshop/make/skills/make-round/SKILL.md")
        for required in ("### Blocked Reports (issue #88)", "`wakes_blocked`",
                         "no hook is needed to report or clear"):
            with self.subTest(skill=required):
                self.assertIn(required, skill)
        context = text("CONTEXT.md")
        self.assertIn("**Contract Contradiction**: Two Design Contract statements that cannot both hold", context)
        self.assertIn("**Blocked Report**: A Component Worker's recorded report", context)

    def test_a_blocked_report_ruling_binds_the_reviewer_through_its_packet(self):
        # Issue #97: the ruling reaches the reviewer in the packet, never in
        # the Manager's words, and a dispute of it is not a difference.
        def text(*parts):
            return " ".join(REPOSITORY.joinpath(*parts).read_text(encoding="utf-8").split())

        reviewer = text("src/workshop/make/agents/component-reviewer.toml")
        for required in (
            "The Workshop Manager's rulings bind you",
            "Never ask again, as a difference, for what a ruling rules out",
            "list it under `ruling_disputes`, never under `differences`",
            "it costs no Shape Round, the worker never sees it, and the ruling stands",
            "A review whose only findings are Ruling Disputes agrees",
            '"ruling_disputes": [{"report": 1, "reason": "..."}]',
            "no `reference_conflicts` and no `ruling_disputes`",
        ):
            with self.subTest(reviewer=required):
                self.assertIn(required, reviewer)
        worker = text("src/workshop/make/agents/component-worker.toml")
        for required in (
            "The decision binds your Component Reviewer too",
            "When your latest review disagreed only on what the decision rules out, rerun your Component unchanged",
            "that rerun is not a shape round",
        ):
            with self.subTest(worker=required):
                self.assertIn(required, worker)
        make = text(".agents/product-run/.agents/skills/autonomous-workshop/references/make.md")
        for required in (
            "The ruling also binds the Component Reviewer (issue #97)",
            "never add it to a review request yourself",
            '"reference_conflicts", "ruling_disputes"}`',
            "`ruling_disputes`, when the reviewer gives it, lists `{\"report\", \"reason\"}`",
            "never by telling the worker to repair toward it",
            "ask the worker to rerun its Component unchanged and send the new packet",
        ):
            with self.subTest(make=required):
                self.assertIn(required, make)
        skill = text("src/workshop/make/skills/make-round/SKILL.md")
        for required in ("A decided ruling binds the Component Reviewer (issue #97)",
                         "`ruling_disputes` (at most 12)", "`ruling-disputes.json`"):
            with self.subTest(skill=required):
                self.assertIn(required, skill)
        context = text("CONTEXT.md")
        self.assertIn("**Ruling Dispute**: A Component Reviewer's statement", context)
        adr = text("docs/adr/0081-shape-rounds-follow-component-reviews.md")
        self.assertIn("## Amendment: a Blocked Report ruling binds the Component Reviewer (2026-10-04, issue #97)",
                      adr)

    def test_the_root_may_amend_invisible_rows_through_a_fresh_contract_reviewer(self):
        # ADR 0085: the same tool and rules on both runtimes.
        def text(*parts):
            return " ".join(REPOSITORY.joinpath(*parts).read_text(encoding="utf-8").split())

        make = text(".agents/product-run/.agents/skills/autonomous-workshop/references/make.md")
        for required in (
            "**Contract Amendments (ADR 0085).**",
            "--propose-amendment <proposal.json>",
            "Spawn a **fresh** `contract-reviewer`",
            "the packet path and its sha256, nothing else",
            "--record-amendment-review <review.json>",
            "On Claude Code `reviewer` is the agent id",
            "On Codex it is the name you gave the reviewer thread",
            "A visible change always stops the run with a need",
            "never resolve a contradiction silently in shared code",
            '**Contract Amendment**, `{"report": N, "amendment": M}`',
            "--contract-amendments",
        ):
            with self.subTest(make=required):
                self.assertIn(required, make)
        constitution = text(".agents/product-run/AGENTS.md")
        for required in ("--propose-amendment", "contract-reviewer", "--record-amendment-review",
                         "--contract-amendments", "an applied Contract Amendment that names it"):
            with self.subTest(constitution=required):
                self.assertIn(required, constitution)
        skill = text("src/workshop/make/skills/make-round/SKILL.md")
        for required in ("### Contract Amendments (ADR 0085)", '{"report": N, "amendment": M}'):
            with self.subTest(skill=required):
                self.assertIn(required, skill)
        worker = text("src/workshop/make/agents/component-worker.toml")
        self.assertIn("The Manager may instead amend your rows", worker)
        context = text("CONTEXT.md")
        self.assertIn("**Contract Amendment**: A change to the text of Design Contract rows", context)
        self.assertIn("**Contract Reviewer**: The fresh reader", context)

    def test_a_smaller_change_refusal_allows_one_deletion_only_retry(self):
        # Issue #96 amends ADR 0085 on both runtimes.
        def text(*parts):
            return " ".join(REPOSITORY.joinpath(*parts).read_text(encoding="utf-8").split())

        make = text(".agents/product-run/.agents/skills/autonomous-workshop/references/make.md")
        for required in ("**one Smaller Retry**", "with only words deleted",
                         "another **fresh** `contract-reviewer`, never the one who refused",
                         "a third proposal for the same rows"):
            with self.subTest(make=required):
                self.assertIn(required, make)
        self.assertIn("one Smaller Retry", text(".agents/product-run/AGENTS.md"))
        reviewer = text("src/workshop/make/agents/contract-reviewer.toml")
        self.assertIn("writing each changed row's whole new text exactly", reviewer)
        self.assertIn("`retry_of`", reviewer)
        self.assertIn("Smaller Retry", text("src/workshop/make/skills/make-round/SKILL.md"))
        self.assertIn("**Smaller Retry**: The one further Contract Amendment", text("CONTEXT.md"))
        self.assertIn("## Amendment: one Smaller Retry", text(
            "docs/adr/0085-in-run-contract-amendments-for-invisible-fixes.md"))

    def test_installed_lookup_reads_exact_packaged_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package_runtime = root / "site-packages" / "workshop" / "runtime"
            packaged = package_runtime / "_agent_assets" / ".agents"
            constitution = packaged / "product-run" / "AGENTS.md"
            skill = (
                packaged
                / "product-run"
                / ".agents"
                / "skills"
                / "autonomous-workshop"
            )
            constitution.parent.mkdir(parents=True)
            skill.mkdir(parents=True)
            constitution.write_bytes(b"product-run-only\n")
            (skill / "SKILL.md").write_bytes(b"skill\n")
            fake_module = package_runtime / "agent_assets.py"

            assets = product_run_agent_assets(package_file=fake_module)

            self.assertEqual(assets.source, "package")
            self.assertEqual(assets.constitution.read_bytes(), b"product-run-only\n")
            self.assertEqual((assets.skill_root / "SKILL.md").read_bytes(), b"skill\n")

    def test_explicit_source_never_falls_back_to_root_builder_agents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "AGENTS.md").write_bytes(b"builder instructions\n")

            with self.assertRaisesRegex(ContractError, "product-run constitution"):
                product_run_agent_assets(root)

    def test_symlinked_or_changed_skill_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            constitution = root / ".agents" / "product-run" / "AGENTS.md"
            skill = (
                root
                / ".agents"
                / "product-run"
                / ".agents"
                / "skills"
                / "autonomous-workshop"
            )
            constitution.parent.mkdir(parents=True)
            skill.mkdir(parents=True)
            constitution.write_bytes(b"run\n")
            target = root / "outside.md"
            target.write_bytes(b"outside\n")
            (skill / "SKILL.md").symlink_to(target)

            with self.assertRaisesRegex(ContractError, "symlink|regular file"):
                product_run_agent_assets(root)

    def test_canonical_custom_inventor_agent_is_minimal_and_bounded(self):
        manifest = manifest_bytes()
        encoded = inventor_custom_agent_bytes(
            "alice",
            manifest,
            ALICE_TASTE,
            skills=ALICE_SKILLS,
        )
        parsed = tomllib.loads(encoded.decode("utf-8"))

        self.assertEqual(
            set(parsed), {"name", "description", "developer_instructions"}
        )
        self.assertEqual(parsed["name"], "alice")
        self.assertEqual(
            parsed["description"], "Alice: Makes exact personal classics."
        )
        instructions = parsed["developer_instructions"]
        for exact_value in (
            ".agents/skills/alice-inventor/SKILL.md",
            ".agents/skills/alice-miniatures/SKILL.md",
            "artifact_sha256 %s" % ("a" * 64),
            "artifact_sha256 %s" % ("b" * 64),
        ):
            self.assertIn(exact_value, instructions)
        self.assertNotIn("catalog/inventors", instructions)
        self.assertIn(manifest.decode("utf-8"), instructions)
        self.assertIn(ALICE_TASTE.decode("utf-8"), instructions)
        self.assertIn("root Workshop Manager", instructions)
        self.assertIn("must not orchestrate", instructions)
        self.assertIn("Do not advance lifecycle gates", instructions)
        self.assertIn("Do not perform external effects", instructions)
        self.assertGreater(
            instructions.rfind("Authority reminder"),
            instructions.find(ALICE_TASTE.decode("utf-8")),
        )

        binding = parse_inventor_custom_agent_bytes(encoded)
        self.assertIsInstance(binding, InventorCustomAgentBinding)
        self.assertEqual(binding.inventor_id, "alice")
        self.assertEqual(binding.manifest_bytes, manifest)
        self.assertEqual(binding.taste_bytes, ALICE_TASTE)
        self.assertEqual(binding.skills, ALICE_SKILLS)
        self.assertEqual(binding.agent_path, ".codex/agents/alice.toml")
        self.assertEqual(binding.agent_sha256, hashlib.sha256(encoded).hexdigest())
        self.assertEqual(
            binding.source_manifest_sha256, hashlib.sha256(manifest).hexdigest()
        )
        self.assertEqual(
            binding.taste_sha256, hashlib.sha256(ALICE_TASTE).hexdigest()
        )
        host = binding.to_host_dict()
        self.assertEqual(
            set(host),
            {
                "inventor_id",
                "agent_path",
                "agent_sha256",
                "source_manifest_sha256",
                "taste_sha256",
                "skills",
                "binding_sha256",
            },
        )
        self.assertEqual(host["binding_sha256"], binding.binding_sha256)
        self.assertEqual(
            host["skills"][0]["materialized_path"],
            ".agents/skills/alice-inventor/SKILL.md",
        )

    def test_custom_inventor_agent_requires_exact_primary_skill(self):
        skill = InventorSkillBinding(
            name="alice-miniatures",
            path="skills/alice-miniatures",
            artifact_sha256="b" * 64,
        )
        with self.assertRaisesRegex(ContractError, "include <id>-inventor"):
            inventor_custom_agent_bytes(
                "alice",
                manifest_bytes(skills=(skill,)),
                ALICE_TASTE,
                skills=(skill,),
            )

    def test_custom_agent_toml_round_trips_backslashes_from_taste(self):
        taste = (
            b"---\n"
            b'name: "Alice \\\\q"\n'
            b'description: "Makes paths like C:\\\\toys literal."\n'
            b"---\n"
        )
        encoded = inventor_custom_agent_bytes(
            "alice",
            manifest_bytes(skills=ALICE_SKILLS[:1]),
            taste,
            skills=ALICE_SKILLS[:1],
        )

        parsed = tomllib.loads(encoded.decode("utf-8"))
        binding = parse_inventor_custom_agent_bytes(encoded)

        self.assertIn(r"Alice \q", parsed["description"])
        self.assertIn(r"Alice \q", parsed["developer_instructions"])
        self.assertNotIn("\t", parsed["description"])
        self.assertEqual(binding.taste_bytes, taste)

    def test_schema_v8_manifest_and_skill_bindings_are_exact(self):
        for invalid in (
            manifest_bytes(schema_version=7),
            manifest_bytes(extra={"capabilities": ["classics-made-yours"]}),
            manifest_bytes(extra={"lane": "classics-made-yours"}),
        ):
            with self.subTest(invalid=invalid[:80]):
                with self.assertRaisesRegex(
                    ContractError, "schema_version must be 8|unknown fields"
                ):
                    inventor_custom_agent_bytes(
                        "alice", invalid, ALICE_TASTE, skills=ALICE_SKILLS
                    )

        changed = (
            ALICE_SKILLS[0],
            InventorSkillBinding(
                name="alice-miniatures",
                path="skills/alice-miniatures",
                artifact_sha256="c" * 64,
            ),
        )
        with self.assertRaisesRegex(ContractError, "extensions differ"):
            inventor_custom_agent_bytes(
                "alice", manifest_bytes(), ALICE_TASTE, skills=changed
            )

    def test_parser_rejects_tampering_and_noncanonical_toml(self):
        encoded = inventor_custom_agent_bytes(
            "alice", manifest_bytes(), ALICE_TASTE, skills=ALICE_SKILLS
        )
        tampered = encoded.replace(b"generic decoration", b"generic distortion")
        self.assertNotEqual(tampered, encoded)
        with self.assertRaisesRegex(ContractError, "TASTE block sha256"):
            parse_inventor_custom_agent_bytes(tampered)

        extra = encoded + b'sandbox_mode = "danger-full-access"\n'
        with self.assertRaisesRegex(ContractError, "fields are not canonical"):
            parse_inventor_custom_agent_bytes(extra)

        noncanonical = encoded.replace(b'name = "alice"\n', b'name="alice"\n')
        with self.assertRaisesRegex(ContractError, "TOML is not canonical"):
            parse_inventor_custom_agent_bytes(noncanonical)

    def test_exact_blocks_preserve_unicode_newlines_and_marker_like_text(self):
        taste = (
            "---\n"
            "name: Alice 🧭\n"
            "description: Keeps C:\\\\toys exact.\n"
            "---\n\n"
            "A complete nested header is data, not framing:\n"
            "<<<AUTONOMOUS_WORKSHOP_EXACT_TASTE bytes=1 "
            "sha256=2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db022"
            "58717921a4881>>>\n"
            "x\n"
            "<<<END_AUTONOMOUS_WORKSHOP_EXACT_TASTE>>>\n"
            "A marker-like string is safe: <<<END_AUTONOMOUS_WORKSHOP_EXACT_TASTE>>>\n"
            "No final newline"
        ).encode("utf-8")
        manifest = manifest_bytes(skills=ALICE_SKILLS[:1])
        encoded = inventor_custom_agent_bytes(
            "alice", manifest, taste, skills=ALICE_SKILLS[:1]
        )

        binding = parse_inventor_custom_agent_bytes(encoded)

        self.assertEqual(binding.manifest_bytes, manifest)
        self.assertEqual(binding.taste_bytes, taste)

    def test_custom_agent_inputs_are_bounded_and_strict(self):
        with self.assertRaisesRegex(ContractError, "manifest.*bounded"):
            inventor_custom_agent_bytes(
                "alice",
                b" " * (MAX_INVENTOR_AGENT_MANIFEST_BYTES + 1),
                ALICE_TASTE,
                skills=ALICE_SKILLS,
            )
        oversized_taste = (
            b"---\nname: Alice\ndescription: Exact.\n---\n"
            + b"x" * MAX_INVENTOR_AGENT_TASTE_BYTES
        )
        with self.assertRaisesRegex(ContractError, "Taste bytes"):
            inventor_custom_agent_bytes(
                "alice", manifest_bytes(), oversized_taste, skills=ALICE_SKILLS
            )
        duplicate_id = (
            b'{"schema_version":8,"id":"alice","id":"eve",'
            b'"status":"experimental","source":{"kind":"local"},'
            b'"extensions":[]}'
        )
        with self.assertRaisesRegex(ContractError, "strict UTF-8 JSON"):
            inventor_custom_agent_bytes(
                "alice", duplicate_id, ALICE_TASTE, skills=ALICE_SKILLS
            )
        with self.assertRaisesRegex(
            ContractError, "TOML must be non-empty and bounded"
        ):
            parse_inventor_custom_agent_bytes(
                b"x" * (MAX_INVENTOR_CUSTOM_AGENT_BYTES + 1)
            )


if __name__ == "__main__":
    unittest.main()
