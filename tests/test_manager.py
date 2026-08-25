import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.errors import ContractError, ManifestError
from inventor_workshop.make import Wish
import inventor_workshop.manager as manager_module
from inventor_workshop.manager import (
    InventorRetrieverRequired,
    NoInventorFit,
    Shortlist,
    TasteFit,
    TasteJudgeRequired,
    WorkshopManager,
    create_assignment,
    create_shortlist,
    discover_inventor_catalog,
    dispatch_assignment,
    load_finalists,
    retrieve_shortlist,
    select_inventor,
    shortlist_all,
)
from inventor_workshop.taste import load_taste, load_taste_header


JUDGE_PROVENANCE = {
    "judge_identity": "fixture-semantic-taste-judge",
    "judge_version": "model-and-policy-2026-08-23",
    "judge_config_sha256": "e" * 64,
}
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def taste_source(name, description, body):
    return "---\nname: %s\ndescription: %s\n---\n\n%s\n" % (
        name,
        description,
        body,
    )


def add_inventor(
    collection,
    inventor_id,
    name,
    description,
    body,
    *,
    status="experimental",
    source=None,
    capabilities=None,
):
    root = collection / inventor_id
    root.mkdir(parents=True)
    (root / "TASTE.md").write_text(
        taste_source(name, description, body), encoding="utf-8"
    )
    (root / "profile.py").write_text(
        "def run():\n    return 'one-shot fixture'\n", encoding="utf-8"
    )
    manifest = {
        "schema_version": 5,
        "id": inventor_id,
        "status": status,
        "entrypoint": ["python3", "profile.py"],
        "capabilities": capabilities or ["wish", "physical-product"],
        "checks": [],
        "source": source if source is not None else {"kind": "local"},
    }
    (root / "inventor.json").write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8"
    )
    return root


def make_shortlist(context, inventor_ids):
    return create_shortlist(
        context,
        inventor_ids,
        retriever="fixture-semantic-index",
        retriever_version="index-2026-08-23",
        rationale="External semantic retrieval compared the exact Wish with compact cards.",
    )


def fits_for(context, scores=None, rejected=()):
    scores = scores or {}
    rejected = set(rejected)
    return tuple(
        TasteFit(
            inventor_id=finalist.inventor_id,
            taste_sha256=finalist.taste.sha256,
            score=scores.get(finalist.inventor_id, 50),
            accepted=finalist.inventor_id not in rejected,
            explanation="Compared the exact Wish with %s's complete Taste."
            % finalist.card.name,
            tensions=("The Wish conflicts with a hard Taste rule.",)
            if finalist.inventor_id in rejected
            else (),
        )
        for finalist in reversed(context.finalists)
    )


def select_with_fixture_judge(context, judge, **provenance_overrides):
    provenance = dict(JUDGE_PROVENANCE)
    provenance.update(provenance_overrides)
    return select_inventor(context, judge, **provenance)


class WorkshopManagerTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        self.collection = self.repo / "inventors"
        self.collection.mkdir()
        add_inventor(
            self.collection,
            "classic-maker",
            "Classic Maker",
            "Makes known tabletop classics personal while preserving their rules.",
            "# Taste\n\nReject invented rules. Prefer heirloom table presence.",
        )
        add_inventor(
            self.collection,
            "game-maker",
            "Game Maker",
            "Invents original printable games for one particular group and table.",
            "# Taste\n\nReject cosmetic themes. Require replay demand from humans.",
        )
        self.wish = Wish.create(
            "wish-7",
            "Invent a tense deduction game for our research team's inside joke.",
            constraints={"printer": "FDM", "playtest_rounds": 99},
            context={"private_reference": "the blue notebook"},
        )

    def tearDown(self):
        self.temporary.cleanup()

    def context(self):
        return WorkshopManager(self.repo).prepare(self.wish)

    def finalists(self, inventor_ids=("classic-maker", "game-maker")):
        context = self.context()
        shortlist = make_shortlist(context, inventor_ids)
        return load_finalists(context, shortlist)

    def test_catalog_reads_headers_not_full_tastes_and_ignores_nested_manifests(self):
        nested = self.collection / "archive" / "old"
        nested.mkdir(parents=True)
        (nested / "inventor.json").write_text("{}", encoding="utf-8")
        (nested / "TASTE.md").write_text("not a routed file", encoding="utf-8")

        with mock.patch.object(
            manager_module, "load_taste", wraps=load_taste
        ) as full_loader, mock.patch.object(
            manager_module, "load_taste_header", wraps=load_taste_header
        ) as header_loader:
            catalog = discover_inventor_catalog(self.repo)

        self.assertEqual(
            [item.inventor_id for item in catalog.cards],
            ["classic-maker", "game-maker"],
        )
        self.assertEqual(full_loader.call_count, 0)
        self.assertEqual(header_loader.call_count, 2)
        self.assertNotIn("Reject invented rules", json.dumps(catalog.receipt()))
        page = catalog.page(limit=1).to_dict()
        self.assertNotIn("Reject invented rules", json.dumps(page))
        self.assertEqual(page["cards"][0]["description"], catalog.cards[0].description)

    def test_card_semantics_come_only_from_taste_header(self):
        card = self.context().catalog.card("game-maker")
        self.assertEqual(card.name, "Game Maker")
        self.assertIn("original printable games", card.description)
        self.assertFalse(hasattr(card, "niche"))
        self.assertNotIn("summary", card.to_routing_dict())
        self.assertEqual(len(card.card_sha256), 64)
        self.assertEqual(len(card.taste_header_sha256), 64)

    def test_operational_capabilities_never_reach_semantic_routing_cards(self):
        add_inventor(
            self.collection,
            "large-card",
            "Large Card",
            "Routes through Taste prose even when operational capability data is large.",
            "# Taste\n\nA complete creative constitution.",
            capabilities=["capability-%02d" % index for index in range(25)],
        )
        card = self.context().catalog.card("large-card")
        self.assertFalse(hasattr(card, "capabilities"))
        page = self.context().catalog.page(limit=3).to_dict()
        self.assertNotIn("capabilities", json.dumps(page))
        self.assertNotIn("capability-00", json.dumps(page))

    def test_catalog_is_paged_and_descriptions_can_be_omitted(self):
        catalog = self.context().catalog
        first = catalog.page(cursor=0, limit=1, include_descriptions=False)
        second = catalog.page(cursor=first.next_cursor, limit=1)
        self.assertEqual(first.total, 2)
        self.assertEqual(first.next_cursor, 1)
        self.assertIsNone(second.next_cursor)
        self.assertNotIn("description", first.to_dict()["cards"][0])
        self.assertTrue(first.to_dict()["cards"][0]["description_omitted"])
        with self.assertRaises(ContractError):
            catalog.page(limit=201)

    def test_orphan_files_symlinks_and_mismatched_operational_ids_fail_closed(self):
        orphan = self.collection / "orphan"
        orphan.mkdir()
        (orphan / "TASTE.md").write_text(
            taste_source("Orphan", "An orphan header.", "# Body"), encoding="utf-8"
        )
        with self.assertRaisesRegex(ManifestError, "missing"):
            discover_inventor_catalog(self.repo)

        (orphan / "inventor.json").symlink_to(
            self.collection / "classic-maker" / "inventor.json"
        )
        with self.assertRaises(ManifestError):
            discover_inventor_catalog(self.repo)

        (orphan / "inventor.json").unlink()
        add_document = json.loads(
            (self.collection / "classic-maker" / "inventor.json").read_text(
                encoding="utf-8"
            )
        )
        add_document["id"] = "different-id"
        (orphan / "inventor.json").write_text(json.dumps(add_document), encoding="utf-8")
        (orphan / "profile.py").write_text("pass\n", encoding="utf-8")
        with self.assertRaisesRegex(ManifestError, "must match"):
            discover_inventor_catalog(self.repo)

    def test_prepare_snapshots_wish_and_returns_only_catalog_receipt(self):
        context = self.context()
        expected = context.wish.to_dict()
        self.wish.constraints["printer"] = "mutated outside manager"
        receipt = context.audit_receipt()
        self.assertEqual(context.wish.to_dict(), expected)
        self.assertEqual(receipt["wish_sha256"], context.wish_sha256)
        self.assertEqual(receipt["catalog"]["total"], 2)
        self.assertNotIn("cards", receipt["catalog"])
        self.assertNotIn(self.wish.objective, json.dumps(receipt))
        self.assertNotIn("blue notebook", json.dumps(receipt))

    def test_versioned_catalog_provider_avoids_rebuilding_the_registry_per_wish(self):
        catalog = self.context().catalog
        provider = mock.Mock(return_value=catalog)
        manager = WorkshopManager(
            catalog_provider=provider,
            retriever=lambda context: make_shortlist(context, ("game-maker",)),
        )
        with mock.patch.object(
            manager_module,
            "discover_inventor_catalog",
            side_effect=AssertionError("provider-backed routing must not rebuild"),
        ), mock.patch.object(
            manager_module.InventorCatalog,
            "assert_current",
            side_effect=AssertionError("versioned provider must not rescan every card"),
        ):
            first = manager.prepare(self.wish)
            second = manager.prepare(
                Wish.create("another-wish", "A second request uses the same index revision.")
            )
            manager.shortlist(first)
        self.assertIs(first.catalog, catalog)
        self.assertIs(second.catalog, catalog)
        self.assertEqual(provider.call_count, 2)
        self.assertFalse(first.verify_live_catalog)

    def test_missing_retriever_and_judge_wait_truthfully(self):
        context = self.context()
        with self.assertRaises(InventorRetrieverRequired) as retrieval:
            retrieve_shortlist(context, None)
        self.assertEqual(
            retrieval.exception.needs[0].capability,
            "semantic-inventor-retriever",
        )
        shortlist = shortlist_all(
            context,
            retriever="explicit-small-catalog",
            retriever_version="1",
            rationale="The application explicitly chose every routable card in this small catalog.",
        )
        finalists = load_finalists(context, shortlist)
        with self.assertRaises(TasteJudgeRequired) as judgment:
            select_inventor(finalists, None)
        self.assertEqual(judgment.exception.needs[0].capability, "semantic-taste-judge")
        self.assertEqual(len(judgment.exception.context.finalists), 2)

    def test_shortlist_binds_ordered_card_hashes_and_retriever_provenance(self):
        context = self.context()
        shortlist = make_shortlist(context, ("game-maker", "classic-maker"))
        self.assertEqual(shortlist.inventor_ids, ("game-maker", "classic-maker"))
        self.assertEqual(
            shortlist.card_sha256s,
            tuple(context.catalog.card(item).card_sha256 for item in shortlist.inventor_ids),
        )
        receipt = shortlist.to_dict()
        self.assertEqual(receipt["retriever"], "fixture-semantic-index")
        self.assertIn("rationale", receipt)
        self.assertEqual(len(receipt["shortlist_sha256"]), 64)

        stale = Shortlist(
            wish_sha256=context.wish_sha256,
            catalog_sha256=context.catalog.catalog_sha256,
            inventor_ids=("game-maker",),
            card_sha256s=("0" * 64,),
            retriever="fixture",
            retriever_version="1",
            rationale="A deliberately stale card receipt for this test.",
        )
        with self.assertRaisesRegex(ContractError, "stale card"):
            retrieve_shortlist(context, lambda ignored: stale)

    def test_retriever_and_judge_must_return_complete_typed_results(self):
        context = self.context()
        with self.assertRaisesRegex(ContractError, "Shortlist"):
            retrieve_shortlist(context, lambda ignored: ["game-maker"])
        finalists = self.finalists()
        only_one = fits_for(finalists)[:1]
        with self.assertRaisesRegex(ContractError, "every finalist"):
            select_with_fixture_judge(finalists, lambda ignored: only_one)
        stale = list(fits_for(finalists))
        stale[0] = TasteFit(
            inventor_id=stale[0].inventor_id,
            taste_sha256="0" * 64,
            score=80,
            accepted=True,
            explanation="Deliberately stale full-Taste judgment.",
        )
        with self.assertRaisesRegex(ContractError, "stale Taste"):
            select_with_fixture_judge(finalists, lambda ignored: stale)

    def test_judge_provenance_is_required_public_and_hash_bound(self):
        finalists = self.finalists(("game-maker",))
        judge = lambda value: fits_for(value, scores={"game-maker": 91})

        with self.assertRaisesRegex(ContractError, "judge_identity"):
            select_inventor(finalists, judge)
        with self.assertRaisesRegex(ContractError, "judge_config_sha256"):
            select_with_fixture_judge(
                finalists,
                judge,
                judge_config_sha256="not-a-digest",
            )
        with self.assertRaisesRegex(ContractError, "judge_version"):
            select_with_fixture_judge(finalists, judge, judge_version="latest")
        with self.assertRaisesRegex(ContractError, "judge_identity"):
            WorkshopManager(self.repo, judge=judge)

        baseline = select_with_fixture_judge(finalists, judge)
        receipt = baseline.audit_receipt()
        self.assertEqual(receipt["judge"], {
            "identity": JUDGE_PROVENANCE["judge_identity"],
            "version": JUDGE_PROVENANCE["judge_version"],
            "config_sha256": JUDGE_PROVENANCE["judge_config_sha256"],
        })
        changes = (
            {"judge_identity": "another-semantic-judge"},
            {"judge_version": "model-and-policy-2026-08-24"},
            {"judge_config_sha256": "f" * 64},
        )
        for change in changes:
            with self.subTest(change=change):
                changed = select_with_fixture_judge(finalists, judge, **change)
                self.assertNotEqual(changed.decision_sha256, baseline.decision_sha256)

    def test_best_fit_selection_is_deterministic_and_all_rejections_wait(self):
        finalists = self.finalists()
        decision = select_with_fixture_judge(
            finalists,
            lambda value: fits_for(
                value, scores={"classic-maker": 82, "game-maker": 82}
            ),
        )
        self.assertEqual(decision.selected.inventor_id, "classic-maker")
        self.assertEqual(
            [item.inventor_id for item in decision.ranking],
            ["classic-maker", "game-maker"],
        )
        self.assertEqual(len(decision.decision_sha256), 64)

        with self.assertRaises(NoInventorFit) as rejected:
            select_with_fixture_judge(
                finalists,
                lambda value: fits_for(
                    value, rejected=("classic-maker", "game-maker")
                ),
            )
        self.assertEqual(rejected.exception.needs[0].capability, "inventor-fit")

    def test_blocked_and_reference_cards_are_visible_but_not_routable(self):
        add_inventor(
            self.collection,
            "blocked-maker",
            "Blocked Maker",
            "A visible but administratively blocked inventor.",
            "# Taste\n\nThis body must not be selected.",
            status="blocked",
        )
        context = self.context()
        self.assertFalse(context.catalog.card("blocked-maker").routable)
        with self.assertRaisesRegex(ContractError, "non-routable"):
            make_shortlist(context, ("blocked-maker",))

        add_inventor(
            self.collection,
            "pinned-maker",
            "Pinned Maker",
            "An enabled inventor whose implementation has pinned external provenance.",
            "# Taste\n\nA complete creative constitution.",
            status="experimental",
            source={
                "kind": "upstream-snapshot",
                "url": "https://example.test/team/pinned-maker",
                "commit": "a" * 40,
                "imported_at": "2026-08-23",
            },
        )
        context = self.context()
        self.assertTrue(context.catalog.card("pinned-maker").routable)

    def test_assignment_receipt_binds_every_routing_revision_and_trusted_rounds(self):
        manager = WorkshopManager(
            self.repo,
            retriever=lambda context: make_shortlist(context, ("game-maker",)),
            judge=lambda context: fits_for(context, scores={"game-maker": 95}),
            **JUDGE_PROVENANCE,
        )
        assignment = manager.assign(self.wish, playtest_rounds=3)
        receipt = assignment.to_dict()
        decision = receipt["decision"]
        self.assertEqual(assignment.inventor_id, "game-maker")
        self.assertEqual(assignment.playtest_rounds, 3)
        self.assertEqual(receipt["kind"], "one-shot")
        self.assertEqual(decision["wish"], assignment.wish.to_dict())
        self.assertEqual(len(decision["catalog_sha256"]), 64)
        self.assertIn("rationale", decision["shortlist"])
        self.assertEqual(len(decision["finalists_sha256"]), 64)
        self.assertEqual(len(decision["selected"]["taste_sha256"]), 64)
        self.assertEqual(len(decision["selected"]["implementation_sha256"]), 64)
        self.assertEqual(decision["selected"]["entrypoint"], ["python3", "profile.py"])
        self.assertEqual(decision["judge"]["config_sha256"], "e" * 64)
        self.assertEqual(len(decision["ranking"]), 1)
        self.assertEqual(len(receipt["assignment_sha256"]), 64)
        public = assignment.audit_receipt()
        self.assertNotIn(self.wish.objective, json.dumps(public))
        self.assertNotIn("blue notebook", json.dumps(public))
        self.assertEqual(public["decision"]["wish_sha256"], decision["wish_sha256"])
        self.assertEqual(public["decision"]["judge"], decision["judge"])
        for bad in (True, 0, 101, "3"):
            with self.subTest(playtest_rounds=bad), self.assertRaises(ContractError):
                create_assignment(assignment.decision, playtest_rounds=bad)

    def test_relevant_mutations_fail_but_unrelated_later_addition_does_not(self):
        finalists = self.finalists(("game-maker",))
        decision = select_with_fixture_judge(finalists, lambda value: fits_for(value))

        add_inventor(
            self.collection,
            "new-maker",
            "New Maker",
            "An inventor added after this immutable routing snapshot completed.",
            "# Taste\n\nThis later addition is unrelated to the completed decision.",
        )
        assignment = create_assignment(decision, playtest_rounds=2)
        self.assertEqual(assignment.inventor_id, "game-maker")

        (self.collection / "game-maker" / "profile.py").write_text(
            "def run():\n    return 'changed implementation'\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ManifestError, "implementation changed"):
            dispatch_assignment(assignment, mock.Mock())

    def test_runtime_and_toy_outputs_do_not_change_contribution_identity(self):
        root = self.collection / "game-maker"
        before = manager_module._implementation_sha256(root)
        generated = root / ".workshop" / "runs" / "wish-one" / "generated.py"
        generated.parent.mkdir(parents=True)
        generated.write_text("# generated CAD worker output\n", encoding="utf-8")
        self.assertEqual(manager_module._implementation_sha256(root), before)

        toy = root / "toys" / "wish-one" / "generated" / "product.json"
        toy.parent.mkdir(parents=True)
        toy.write_text('{"generated": true}\n', encoding="utf-8")
        self.assertEqual(manager_module._implementation_sha256(root), before)

        (root / "profile.py").write_text(
            "def run():\n    return 'changed source'\n", encoding="utf-8"
        )
        self.assertNotEqual(manager_module._implementation_sha256(root), before)

    def test_nested_config_and_prompt_bytes_change_contribution_identity(self):
        root = self.collection / "game-maker"
        config = root / "config" / "default.json"
        prompt = root / "prompts" / "reward.md"
        config.parent.mkdir()
        prompt.parent.mkdir()
        config.write_text('{"model":"luna"}\n', encoding="utf-8")
        prompt.write_text("Score the exact product.\n", encoding="utf-8")
        before = manager_module._implementation_sha256(root)

        config.write_text('{"model":"terra"}\n', encoding="utf-8")
        after_config = manager_module._implementation_sha256(root)
        self.assertNotEqual(after_config, before)

        prompt.write_text("Lower the reward threshold.\n", encoding="utf-8")
        self.assertNotEqual(
            manager_module._implementation_sha256(root), after_config
        )

    def test_symlink_in_inventor_owned_contribution_fails_closed(self):
        root = self.collection / "game-maker"
        (root / "linked-profile.py").symlink_to("profile.py")
        with self.assertRaisesRegex(ManifestError, "must not contain symlinks"):
            manager_module._implementation_sha256(root)

    def test_canonical_bob_shared_skill_links_remain_outside_his_contribution(self):
        wish = Wish.create(
            "canonical-bob-fingerprint",
            "A small moving machine that rewards curiosity.",
        )
        context = WorkshopManager(REPOSITORY_ROOT).prepare(wish)
        shortlist = make_shortlist(context, ("bob",))
        finalists = load_finalists(context, shortlist)

        self.assertEqual(tuple(item.inventor_id for item in finalists.finalists), ("bob",))
        self.assertEqual(len(finalists.finalists[0].implementation_sha256), 64)

    def test_catalog_or_finalist_staleness_is_detected_at_the_relevant_boundary(self):
        context = self.context()
        manifest_path = self.collection / "classic-maker" / "inventor.json"
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        document["capabilities"].append("changed-after-catalog")
        manifest_path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(ManifestError, "manifest changed"):
            retrieve_shortlist(
                context,
                lambda value: make_shortlist(value, ("game-maker",)),
            )

        context = self.context()
        finalists = load_finalists(context, make_shortlist(context, ("game-maker",)))
        taste_path = self.collection / "game-maker" / "TASTE.md"
        taste_path.write_text(
            taste_path.read_text(encoding="utf-8") + "\nA human changed the body.\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ManifestError, "Taste changed"):
            select_with_fixture_judge(finalists, lambda value: fits_for(value))

    def test_dispatch_calls_the_application_entrypoint_once(self):
        manager = WorkshopManager(
            self.repo,
            retriever=lambda context: make_shortlist(context, ("game-maker",)),
            judge=lambda context: fits_for(context),
            **JUDGE_PROVENANCE,
        )
        assignment = manager.assign(self.wish, playtest_rounds=7)
        entrypoint = mock.Mock(return_value="waiting-at-make")
        self.assertEqual(dispatch_assignment(assignment, entrypoint), "waiting-at-make")
        entrypoint.assert_called_once_with(assignment)

    def test_catalog_with_more_than_one_thousand_inventors_discloses_only_finalist_body(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            collection = repo / "inventors"
            collection.mkdir()
            for index in range(1001):
                inventor_id = "inventor-%04d" % index
                description = (
                    "Builds physically rigorous kinetic astronomy instruments for custom data."
                    if index == 1000
                    else "Explores a distinct physical plaything practice number %04d." % index
                )
                add_inventor(
                    collection,
                    inventor_id,
                    "Inventor %04d" % index,
                    description,
                    "# Private constitution %04d\n\nBODY-SENTINEL-%04d" % (index, index),
                )
            wish = Wish.create(
                "large-catalog",
                "Make an instrument that embodies my observatory's orbital data.",
            )

            observed_pages = []

            def indexed_retriever(context):
                request = context.audit_receipt()
                page = context.retrieval_page(
                    cursor=0, limit=25, include_descriptions=False
                )
                observed_pages.append(page)
                self.assertEqual(request["catalog"]["total"], 1001)
                self.assertEqual(len(page["page"]["cards"]), 25)
                # A real semantic index is keyed by catalog_sha256 and returns
                # this id without placing every card in one model context.
                return create_shortlist(
                    context,
                    ("inventor-1000",),
                    retriever="fixture-vector-index",
                    retriever_version="catalog-index-v17",
                    rationale=(
                        "Indexed semantic retrieval matched orbital data and physical "
                        "instrument practice; only the top candidate needs full Taste review."
                    ),
                )

            def judge(context):
                self.assertEqual(len(context.finalists), 1)
                self.assertIn("BODY-SENTINEL-1000", context.finalists[0].taste.content)
                return fits_for(context, scores={"inventor-1000": 96})

            with mock.patch.object(
                manager_module, "load_taste_header", wraps=load_taste_header
            ) as header_loader, mock.patch.object(
                manager_module, "load_taste", wraps=load_taste
            ) as full_loader:
                context = WorkshopManager(repo).prepare(wish)
                self.assertEqual(len(context.catalog.cards), 1001)
                self.assertEqual(header_loader.call_count, 1001)
                self.assertEqual(full_loader.call_count, 0)
                shortlist = retrieve_shortlist(context, indexed_retriever)
                finalists = load_finalists(context, shortlist)
                decision = select_with_fixture_judge(finalists, judge)
                assignment = create_assignment(decision, playtest_rounds=4)

            self.assertEqual(assignment.inventor_id, "inventor-1000")
            self.assertTrue(observed_pages)
            full_roots = {call.args[0].name for call in full_loader.call_args_list}
            self.assertEqual(full_roots, {"inventor-1000"})
            self.assertNotIn("BODY-SENTINEL", json.dumps(observed_pages))

    def test_taste_fit_rejects_unbounded_or_unexplained_scores(self):
        for score in (True, -1, 101, 1.5):
            with self.subTest(score=score), self.assertRaises(ContractError):
                TasteFit("inventor", "a" * 64, score, True, "Explanation")
        with self.assertRaisesRegex(ContractError, "tension"):
            TasteFit("inventor", "a" * 64, 0, False, "Rejected without a reason")


if __name__ == "__main__":
    unittest.main()
