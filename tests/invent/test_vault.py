"""The design vault: parsing, links, resolution, compatibility, combos, lint, packing."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from workshop.invent.vault import (
    LEAD_ID_HEX,
    MAX_NODE_BYTES,
    MAX_PACKED_BYTES,
    MAX_VAULT_NODES,
    Vault,
    VaultError,
    VaultNodeNotFound,
    evidence_rows,
    normalize_path,
    parse_frontmatter,
    parse_node,
    slugify,
    assert_concept_compatible,
    lead_id,
)
from workshop.invent.vault import _read_node_file


def node(kind, name, *, relations=(), notes="", status="reviewed", extra=""):
    lines = ["---", "type: %s" % kind, 'name: "%s"' % name, "created: 2026-08-21",
             "source: agent", "status: %s" % status]
    if extra:
        lines.append(extra)
    lines += ["---", "", "# %s" % name, "", "## Definition", "%s does one thing." % name,
              "", "## Relations"]
    lines += ["- %s:: %s" % (kind_, ", ".join("[[%s]]" % t for t in targets))
              for kind_, targets in relations]
    lines += ["", "## Notes", notes]
    return "\n".join(lines) + "\n"


FIXTURE = {
    "mechanisms/hand-off": node(
        "mechanism", "Hand Off",
        relations=(("risks", ("anti-patterns/idle-player",)), ("requires", ("mechanisms/single-token",)),
                   ("component", ("components/token",))),
        extra="aliases: [pass the baton, baton-pass]",
    ),
    "mechanisms/single-token": node("mechanism", "Single Token"),
    "mechanisms/card-hand": node(
        "mechanism", "Card Hand",
        relations=(("conflicts-with", ("constraints/fdm-only",)),),
    ),
    "mechanisms/lonely": node("mechanism", "Lonely", status="seeded"),
    "anti-patterns/idle-player": node(
        "anti-pattern", "Idle Player",
        relations=(("mitigated-by", ("rule-patterns/simultaneous-reveal",)),),
        notes="- [yt:abc] first row\n- [run#ev-1] second row\nplain note",
    ),
    "rule-patterns/simultaneous-reveal": node("rule-pattern", "Simultaneous Reveal"),
    "constraints/fdm-only": node(
        "constraint", "FDM Only",
        relations=(("conflicts-with", ("mechanisms/card-hand",)),),
    ),
    "components/token": node("component", "Token", extra="stl_ref: null"),
    "games/relay": node(
        "game", "Relay",
        relations=(("uses", ("mechanisms/hand-off", "mechanisms/single-token")),),
        extra="player_counts: [2, 3, 4]",
    ),
}


def write_vault(root, nodes=FIXTURE):
    for path, text in nodes.items():
        target = Path(root) / (path + ".md")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    (Path(root) / "_templates").mkdir(exist_ok=True)
    (Path(root) / "_templates" / "mechanism.md").write_text("not a node", encoding="utf-8")
    (Path(root) / "README.md").write_text("top-level file, not a node", encoding="utf-8")
    return Path(root)


# A combo names a failure of a mechanism SET; a game records what a run exhibited.
COMBO_FIXTURE = {
    **FIXTURE,
    "combos/hand-off-with-single-token": node(
        "combo", "Hand Off With Single Token",
        relations=(("member", ("mechanisms/hand-off", "mechanisms/single-token")),
                   ("risks", ("anti-patterns/idle-player",)),
                   ("mitigated-by", ("rule-patterns/simultaneous-reveal",))),
        notes="- [relay#run] 2026-08-27: exit rounds-exhausted",
    ),
    "games/relay": node(
        "game", "Relay",
        relations=(("uses", ("mechanisms/hand-off", "mechanisms/single-token")),
                   ("exhibits", ("anti-patterns/idle-player",))),
        extra="player_counts: [2, 3, 4]",
    ),
}


class ParsingTest(unittest.TestCase):
    def test_frontmatter_subset_scalars_and_lists(self):
        parsed = parse_frontmatter(
            [
                "type: mechanism",
                'name: "Quoted"',
                "bgg_id: null",
                "count: 4",
                "ratio: 0.5",
                "flag: true",
                "other: false",
                "created: 2026-08-21",
                "aliases: [a-b, c d]",
                "empty: []",
                "sources:",
                "  - https://example.test/one",
                "  - https://example.test/two",
                "# a comment",
                "",
            ]
        )
        self.assertEqual(parsed["name"], "Quoted")
        self.assertIsNone(parsed["bgg_id"])
        self.assertEqual((parsed["count"], parsed["ratio"]), (4, 0.5))
        self.assertTrue(parsed["flag"])
        self.assertFalse(parsed["other"])
        self.assertEqual(parsed["created"], "2026-08-21")
        self.assertEqual(parsed["aliases"], ["a-b", "c d"])
        self.assertEqual(parsed["empty"], [])
        self.assertEqual(parsed["sources"], ["https://example.test/one", "https://example.test/two"])

    def test_frontmatter_rejects_malformed_and_repeated_keys(self):
        with self.assertRaisesRegex(VaultError, "malformed"):
            parse_frontmatter(["type mechanism"])
        with self.assertRaisesRegex(VaultError, "repeats"):
            parse_frontmatter(["type: a", "type: b"])

    def test_node_requires_terminated_frontmatter(self):
        with self.assertRaisesRegex(VaultError, "lacks frontmatter"):
            parse_node("# no frontmatter\n")
        with self.assertRaisesRegex(VaultError, "unterminated"):
            parse_node("---\ntype: mechanism\n# body\n")

    def test_node_sections_relations_and_evidence(self):
        parsed = parse_node(FIXTURE["anti-patterns/idle-player"])
        self.assertEqual(parsed["type"], "anti-pattern")
        self.assertEqual(parsed["name"], "Idle Player")
        self.assertEqual(parsed["definition"], "Idle Player does one thing.")
        self.assertEqual(parsed["relations"], {"mitigated-by": ["rule-patterns/simultaneous-reveal"]})
        self.assertEqual(
            evidence_rows(parsed["notes"]),
            [{"ref": "yt:abc", "text": "first row"}, {"ref": "run#ev-1", "text": "second row"}],
        )
        aliased = parse_node("---\ntype: game\nname: X\n---\n## Relations\n- uses:: [[mechanisms/a|A]], [[mechanisms/b.md]]\n")
        self.assertEqual(aliased["relations"], {"uses": ["mechanisms/a", "mechanisms/b"]})

    def test_helpers(self):
        self.assertEqual(normalize_path("./mechanisms/a.md"), "mechanisms/a")
        self.assertEqual(normalize_path("\\mechanisms\\a\\"), "mechanisms/a")
        self.assertEqual(slugify("Area Majority / Influence"), "area-majority-influence")


class VaultGraphTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = write_vault(self.temporary.name)
        self.vault = Vault.from_directory(self.root)

    def test_loads_only_folder_slug_nodes(self):
        self.assertEqual(self.vault.paths(), tuple(sorted(FIXTURE)))
        self.assertEqual(self.vault.paths("mechanisms"), tuple(sorted(p for p in FIXTURE if p.startswith("mechanisms/"))))
        self.assertEqual(len(self.vault.sha256), 64)
        node = self.vault.read_node("mechanisms/hand-off.md")
        self.assertEqual(node["frontmatter"]["aliases"], ["pass the baton", "baton-pass"])
        with self.assertRaises(TypeError):
            node["relations"]["risks"] = ()

    def test_missing_node_suggests_close_matches(self):
        with self.assertRaises(VaultNodeNotFound) as caught:
            self.vault.read_node("mechanisms/hand-of")
        self.assertIn("mechanisms/hand-off", caught.exception.suggestions)
        self.assertIn("Close matches", str(caught.exception))
        with self.assertRaises(VaultNodeNotFound) as caught:
            self.vault.read_node("zzz/qqq")
        self.assertEqual(caught.exception.suggestions, ())

    def test_follow_links_forward_reverse_depth_and_cycles(self):
        out = self.vault.follow_links("mechanisms/hand-off")
        self.assertEqual(
            {path: item["link_type"] for path, item in out.items()},
            {
                "anti-patterns/idle-player": "risks",
                "components/token": "component",
                "mechanisms/single-token": "requires",
            },
        )
        self.assertEqual(out["anti-patterns/idle-player"]["type"], "anti-pattern")
        self.assertEqual(out["anti-patterns/idle-player"]["children"], {})
        deep = self.vault.follow_links("mechanisms/hand-off", depth=9)
        self.assertEqual(
            list(deep["anti-patterns/idle-player"]["children"]),
            ["rule-patterns/simultaneous-reveal"],
        )
        only = self.vault.follow_links("mechanisms/hand-off", link_type="risks")
        self.assertEqual(list(only), ["anti-patterns/idle-player"])
        into = self.vault.follow_links("mechanisms/hand-off", reverse=True)
        self.assertEqual(list(into), ["games/relay"])
        self.assertEqual(self.vault.links_into("mechanisms/single-token"), (("games/relay", "uses"), ("mechanisms/hand-off", "requires")))
        # conflicts-with is a two-node cycle; each side is visited once
        cyc = self.vault.follow_links("mechanisms/card-hand", depth=3)
        self.assertEqual(list(cyc), ["constraints/fdm-only"])
        self.assertEqual(cyc["constraints/fdm-only"]["children"], {})
        with self.assertRaises(VaultNodeNotFound):
            self.vault.follow_links("mechanisms/none")

    def test_broken_target_appears_without_a_type(self):
        nodes = dict(FIXTURE)
        nodes["mechanisms/dangling"] = node("mechanism", "Dangling", relations=(("risks", ("anti-patterns/ghost",)),))
        vault = Vault.from_directory(write_vault(tempfile.mkdtemp(dir=self.temporary.name), nodes))
        out = vault.follow_links("mechanisms/dangling")
        self.assertIsNone(out["anti-patterns/ghost"]["type"])
        self.assertIn("mechanisms/dangling: broken link [[anti-patterns/ghost]]", vault.lint()[0])

    def test_resolve_exact_alias_fuzzy_none(self):
        self.assertEqual(self.vault.resolve("Hand Off"), "mechanisms/hand-off")
        self.assertEqual(self.vault.resolve("pass the baton"), "mechanisms/hand-off")
        self.assertEqual(self.vault.resolve("baton pass"), "mechanisms/hand-off")
        self.assertEqual(self.vault.resolve("single-tokens"), "mechanisms/single-token")
        self.assertIsNone(self.vault.resolve("rotating drum"))
        self.assertIsNone(self.vault.resolve("   "))
        self.assertEqual(self.vault.resolve("fdm only", folder="constraints"), "constraints/fdm-only")

    def test_resolve_refuses_a_close_string_with_a_different_meaning(self):
        nodes = {
            "mechanisms/role-playing": node("mechanism", "Role Playing"),
            "mechanisms/tile-placement": node("mechanism", "Tile Placement"),
            "mechanisms/deck-building": node("mechanism", "Deck Building"),
        }
        vault = Vault.from_directory(write_vault(tempfile.mkdtemp(dir=self.temporary.name), nodes))
        self.assertIsNone(vault.resolve("tile laying"))
        self.assertEqual(vault.resolve("deckbuilding"), "mechanisms/deck-building")
        self.assertEqual(vault.resolve("tile placements"), "mechanisms/tile-placement")
        nodes["mechanisms/tile-placement"] = node(
            "mechanism", "Tile Placement", extra="aliases: [tile-laying]"
        )
        vault = Vault.from_directory(write_vault(tempfile.mkdtemp(dir=self.temporary.name), nodes))
        self.assertEqual(vault.resolve("tile laying"), "mechanisms/tile-placement")

    def test_check_compatibility_reports_every_kind_sorted(self):
        findings = self.vault.check_compatibility(
            ["mechanisms/hand-off", "mechanisms/card-hand", "constraints/fdm-only"]
        )
        self.assertEqual(
            [(item["kind"], item["nodes"]) for item in findings],
            [
                ("conflict", ["mechanisms/card-hand", "constraints/fdm-only"]),
                ("risk", ["mechanisms/hand-off", "anti-patterns/idle-player"]),
                ("unmet-requirement", ["mechanisms/hand-off", "mechanisms/single-token"]),
            ],
        )
        risk = findings[1]
        self.assertEqual(risk["suggested_fixes"], ["apply rule-patterns/simultaneous-reveal"])
        self.assertEqual(risk["evidence"], ["[yt:abc] first row", "[run#ev-1] second row"])
        self.assertEqual(
            self.vault.check_compatibility(["mechanisms/hand-off", "mechanisms/single-token"])[0]["kind"],
            "risk",
        )
        self.assertEqual(self.vault.check_compatibility(["mechanisms/single-token"]), [])
        self.assertEqual(self.vault.check_compatibility([]), [])

    def test_risk_without_recorded_mitigation_or_target(self):
        nodes = dict(FIXTURE)
        nodes["anti-patterns/bare"] = node("anti-pattern", "Bare")
        nodes["mechanisms/risky"] = node(
            "mechanism", "Risky", relations=(("risks", ("anti-patterns/bare", "anti-patterns/ghost")),)
        )
        vault = Vault.from_directory(write_vault(tempfile.mkdtemp(dir=self.temporary.name), nodes))
        findings = vault.check_compatibility(["mechanisms/risky"])
        self.assertEqual(
            [item["suggested_fixes"] for item in findings],
            [["no recorded mitigation - add one to the vault"]] * 2,
        )

    def test_guidance_briefs_definition_risks_and_exemplars(self):
        briefing = self.vault.guidance(["mechanisms/hand-off", "mechanisms/lonely"])
        self.assertEqual(briefing[0]["node"], "mechanisms/hand-off")
        self.assertEqual(briefing[0]["definition"], "Hand Off does one thing.")
        self.assertEqual(
            briefing[0]["risks"],
            [
                {
                    "anti_pattern": "anti-patterns/idle-player",
                    "fixes": ["rule-patterns/simultaneous-reveal"],
                    "latest_evidence": "second row",
                }
            ],
        )
        self.assertEqual(briefing[0]["exemplars"], ["games/relay"])
        self.assertEqual(briefing[1]["risks"], [])
        self.assertEqual(briefing[1]["exemplars"], [])
        nodes = dict(FIXTURE)
        nodes["mechanisms/dangling"] = node("mechanism", "Dangling", relations=(("risks", ("anti-patterns/ghost",)),))
        nodes["anti-patterns/quiet"] = node("anti-pattern", "Quiet")
        nodes["mechanisms/quiet-risk"] = node("mechanism", "Quiet Risk", relations=(("risks", ("anti-patterns/quiet",)),))
        vault = Vault.from_directory(write_vault(tempfile.mkdtemp(dir=self.temporary.name), nodes))
        self.assertEqual(vault.guidance(["mechanisms/dangling"])[0]["risks"], [])
        self.assertIsNone(vault.guidance(["mechanisms/quiet-risk"])[0]["risks"][0]["latest_evidence"])

    def test_lint_fixture_is_clean_and_exempts_seeded_orphans(self):
        errors, warnings = self.vault.lint()
        self.assertEqual(errors, [])
        # mechanisms/lonely has no links but is still `status: seeded`
        self.assertEqual(warnings, [])

    def test_lint_finds_every_error_class(self):
        nodes = dict(FIXTURE)
        nodes["mechanisms/bad-type"] = node("widget", "Bad Type")
        nodes["mechanisms/bad-link"] = node("mechanism", "Bad Link", relations=(("loves", ("mechanisms/hand-off",)),))
        nodes["mechanisms/wrong-target"] = node("mechanism", "Wrong Target", relations=(("risks", ("mechanisms/hand-off",)),))
        nodes["mechanisms/shadow"] = node("mechanism", "Shadow", extra="aliases: [hand off]")
        nodes["mechanisms/twice"] = node("mechanism", "Twice", extra="aliases: [pass the baton]")
        nodes["mechanisms/not-list"] = node("mechanism", "Not List", extra="aliases: solo")
        nodes["mechanisms/one-sided"] = node("mechanism", "One Sided", relations=(("conflicts-with", ("mechanisms/single-token",)),))
        nodes["mechanisms/island"] = node("mechanism", "Island", status="reviewed")
        vault = Vault.from_directory(write_vault(tempfile.mkdtemp(dir=self.temporary.name), nodes))
        errors, warnings = vault.lint()
        joined = "\n".join(errors)
        self.assertIn("mechanisms/bad-type: type 'widget' not in", joined)
        self.assertIn("mechanisms/bad-link: unknown link type loves::", joined)
        self.assertIn("risks:: must point at a anti-pattern, [[mechanisms/hand-off]] is a mechanism", joined)
        self.assertIn("alias 'hand off' shadows the real node mechanisms/hand-off", joined)
        self.assertIn("alias 'pass the baton' already claimed by mechanisms/hand-off", joined)
        self.assertIn("mechanisms/not-list: aliases must be a list of strings", joined)
        self.assertIn("mechanisms/one-sided: conflicts-with [[mechanisms/single-token]] is one-sided", "\n".join(warnings))
        self.assertIn("mechanisms/island: orphan: no links in or out", warnings)

    def test_pack_round_trip_is_content_addressed(self):
        packed = self.vault.packed_bytes()
        again = Vault.from_packed_bytes(packed)
        self.assertEqual(again.sha256, self.vault.sha256)
        self.assertEqual(again.packed_bytes(), packed)
        self.assertEqual(again.check_compatibility(["mechanisms/card-hand", "constraints/fdm-only"])[0]["kind"], "conflict")
        document = json.loads(packed)
        self.assertEqual(document["kind"], "autonomous-workshop.design-vault")
        self.assertEqual(document["schema_version"], 1)
        with self.assertRaisesRegex(VaultError, "sha256"):
            Vault.from_packed({**document, "sha256": "0" * 64})
        with self.assertRaisesRegex(VaultError, "fields"):
            Vault.from_packed({**document, "extra": 1})
        with self.assertRaisesRegex(VaultError, "schema or kind"):
            Vault.from_packed({**document, "kind": "other"})
        with self.assertRaisesRegex(VaultError, "not JSON"):
            Vault.from_packed_bytes(b"\xff")

    def test_node_records_are_validated(self):
        with self.assertRaisesRegex(VaultError, "must be a mapping"):
            Vault(["not", "a", "mapping"])
        with self.assertRaisesRegex(VaultError, "path is invalid"):
            Vault({"Bad Path": {}})
        with self.assertRaisesRegex(VaultError, "record is malformed"):
            Vault({"mechanisms/a": {"type": "mechanism"}})
        record = dict(Vault.from_directory(self.root).packed()["nodes"]["mechanisms/hand-off"])
        with self.assertRaisesRegex(VaultError, "relations are malformed"):
            Vault({"mechanisms/a": {**record, "relations": {"risks": "not-a-list"}}})
        with self.assertRaisesRegex(VaultError, "exceeds %d nodes" % MAX_VAULT_NODES):
            Vault({"mechanisms/n%d" % i: record for i in range(MAX_VAULT_NODES + 1)})
        with self.assertRaisesRegex(VaultError, "finite JSON"):
            Vault({"mechanisms/a": {**record, "frontmatter": {"x": float("nan")}}})

    def test_directory_loading_fails_closed(self):
        with self.assertRaisesRegex(VaultError, "real directory"):
            Vault.from_directory(self.root / "missing")
        bad = write_vault(tempfile.mkdtemp(dir=self.temporary.name), dict(FIXTURE))
        (bad / "mechanisms" / "huge.md").write_text(FIXTURE["mechanisms/lonely"] + "x" * MAX_NODE_BYTES, encoding="utf-8")
        with self.assertRaisesRegex(VaultError, "exceeds"):
            Vault.from_directory(bad)
        (bad / "mechanisms" / "huge.md").unlink()
        (bad / "mechanisms" / "link.md").symlink_to(bad / "mechanisms" / "lonely.md")
        with self.assertRaisesRegex(VaultError, "regular file"):
            Vault.from_directory(bad)
        (bad / "mechanisms" / "link.md").unlink()
        (bad / "mechanisms" / "binary.md").write_bytes(b"---\ntype: mechanism\n---\n\xff")
        with self.assertRaisesRegex(VaultError, "UTF-8"):
            Vault.from_directory(bad)
        (bad / "mechanisms" / "binary.md").unlink()
        (bad / "mechanisms" / "Bad Name.md").write_text(FIXTURE["mechanisms/lonely"], encoding="utf-8")
        with self.assertRaisesRegex(VaultError, "path is invalid"):
            Vault.from_directory(bad)
        (bad / "mechanisms" / "Bad Name.md").unlink()
        (bad / "mechanisms" / "broken.md").write_text("no frontmatter\n", encoding="utf-8")
        with self.assertRaisesRegex(VaultError, "mechanisms/broken.md: node lacks frontmatter"):
            Vault.from_directory(bad)
        (bad / "mechanisms" / "broken.md").unlink()
        (bad / "mechanisms" / "gone.md").write_text("x", encoding="utf-8")
        os.chmod(bad / "mechanisms" / "gone.md", 0)
        try:
            with self.assertRaisesRegex(VaultError, "not UTF-8 text|unreadable"):
                Vault.from_directory(bad)
        finally:
            os.chmod(bad / "mechanisms" / "gone.md", 0o600)

    def test_node_that_vanishes_between_listing_and_reading_is_unreadable(self):
        with self.assertRaisesRegex(VaultError, "unreadable"):
            _read_node_file(self.root / "mechanisms" / "vanished.md")

    def test_packed_size_is_bounded(self):
        record = dict(self.vault.packed()["nodes"]["mechanisms/lonely"])
        record["notes"] = "x" * (MAX_NODE_BYTES - 1024)
        big = Vault({"mechanisms/n%03d" % i: dict(record) for i in range(140)})
        with self.assertRaisesRegex(VaultError, "packed vault exceeds %d bytes" % MAX_PACKED_BYTES):
            big.packed_bytes()


class ConceptBindingTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.vault = Vault.from_directory(write_vault(self.temporary.name))

    def test_leads_include_constraints_and_carry_stable_ids(self):
        leads = self.vault.leads_for_concept({"mechanisms": ["hand off", "single-token", "ghost-mechanism"]})
        self.assertEqual(
            [(item["kind"], item["nodes"]) for item in leads],
            [("risk", ["mechanisms/hand-off", "anti-patterns/idle-player"])],
        )
        self.assertEqual(len(leads[0]["id"]), LEAD_ID_HEX)
        self.assertEqual(leads[0]["id"], lead_id("risk", ["mechanisms/hand-off", "anti-patterns/idle-player"]))
        self.assertEqual(self.vault.leads_for_concept({"mechanisms": []}), [])
        with_conflict = self.vault.leads_for_concept({"mechanisms": ["card-hand"]})
        self.assertEqual(with_conflict[0]["kind"], "conflict")
        self.assertEqual(with_conflict[0]["nodes"], ["mechanisms/card-hand", "constraints/fdm-only"])
        with self.assertRaisesRegex(VaultError, "must be a list"):
            self.vault.resolve_concept_mechanisms({"mechanisms": "hand-off"})

    def test_compatible_concepts_are_accepted_with_resolution_and_leads(self):
        binding = assert_concept_compatible(
            self.vault, {"mechanisms": ["hand off", "single-token"]}
        )
        self.assertEqual(
            binding["mechanisms"],
            {"hand off": "mechanisms/hand-off", "single-token": "mechanisms/single-token"},
        )
        self.assertEqual(binding["novel"], {})
        self.assertEqual([item["kind"] for item in binding["leads"]], ["risk"])
        novel = assert_concept_compatible(
            self.vault,
            {
                "mechanisms": ["single-token", "rotating-drum"],
                "novel_mechanisms": [
                    {"id": "rotating-drum", "definition": "A barrel presents exactly one face at a time."}
                ],
            },
        )
        self.assertEqual(novel["novel"], {"rotating-drum": "A barrel presents exactly one face at a time."})
        self.assertIsNone(novel["mechanisms"]["rotating-drum"])

    def test_refusals_name_their_rule(self):
        cases = (
            ({"mechanisms": ["rotating-drum"]}, "mechanism-unknown"),
            ({"mechanisms": ["hand-off"], "novel_mechanisms": "no"}, "must be a list"),
            ({"mechanisms": ["hand-off"], "novel_mechanisms": [{"id": "x"}]}, "exactly id and definition"),
            ({"mechanisms": ["hand-off"], "novel_mechanisms": [{"id": "other", "definition": "x" * 30}]}, "one declared mechanism once"),
            (
                {"mechanisms": ["a", "single-token"], "novel_mechanisms": [{"id": "a", "definition": "x" * 30}, {"id": "a", "definition": "y" * 30}]},
                "one declared mechanism once",
            ),
            ({"mechanisms": ["a", "single-token"], "novel_mechanisms": [{"id": "a", "definition": "short"}]}, "20 to 2000 characters"),
            ({"mechanisms": ["hand-off"], "novel_mechanisms": [{"id": "hand-off", "definition": "x" * 30}]}, "mechanism-not-novel"),
            ({"mechanisms": ["card-hand"]}, "vault-conflict"),
            ({"mechanisms": ["hand-off"]}, "vault-requirement"),
            ({"mechanisms": ["hand-off"], "novel_mechanisms": [{"id": "n%d" % i, "definition": "x" * 30} for i in range(17)]}, "at most 16"),
        )
        for concept, pattern in cases:
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(VaultError, pattern):
                    assert_concept_compatible(self.vault, concept)

    def test_combos_fire_only_when_every_member_is_present(self):
        vault = Vault(
            {path: parse_node(text) for path, text in COMBO_FIXTURE.items()}
        )
        errors, warnings = vault.lint()
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        alone = vault.check_compatibility(["mechanisms/single-token"])
        self.assertEqual(alone, [])
        both = vault.check_compatibility(["mechanisms/hand-off", "mechanisms/single-token"])
        self.assertEqual(
            [(item["kind"], item["nodes"]) for item in both],
            [
                ("combo-risk", ["combos/hand-off-with-single-token", "anti-patterns/idle-player"]),
                ("risk", ["mechanisms/hand-off", "anti-patterns/idle-player"]),
            ],
        )
        self.assertEqual(both[0]["members"], ["mechanisms/hand-off", "mechanisms/single-token"])
        self.assertEqual(both[0]["suggested_fixes"], ["apply rule-patterns/simultaneous-reveal"])
        self.assertEqual(both[0]["evidence"], ["[relay#run] 2026-08-27: exit rounds-exhausted"])
        leads = vault.leads_for_concept({"mechanisms": ["hand-off", "single-token"]})
        self.assertEqual([item["kind"] for item in leads], ["combo-risk", "risk"])
        self.assertEqual(len(leads[0]["id"]), LEAD_ID_HEX)
        binding = assert_concept_compatible(vault, {"mechanisms": ["hand-off", "single-token"]})
        self.assertEqual([item["kind"] for item in binding["leads"]], ["combo-risk", "risk"])
        self.assertEqual(
            vault.follow_links("anti-patterns/idle-player", "exhibits", reverse=True),
            {"games/relay": {"type": "game", "link_type": "exhibits", "children": {}}},
        )


if __name__ == "__main__":
    unittest.main()
