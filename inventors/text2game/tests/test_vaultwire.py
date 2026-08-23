#!/usr/bin/env python3
"""The design-vault leads block the critic prompt carries.

    python3 tests/test_vaultwire.py

_vault() computes check_compatibility() over the draft's mechanisms and hands
the critic leads with node paths. The tests care about three things: a real
match produces the declared conflict and the recorded fix; a miss - invented
vocabulary, missing vault, kill switch - degrades to an EMPTY block and a
LOUD warning, never a crash (a broken vault must not cost a run); and the
FDM production constraint rides along so card mechanisms collide with it.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import prompts  # noqa: E402

PASS = FAIL = 0


def ok(name, got, want=True):
    global PASS, FAIL
    good = got == want
    PASS += good
    FAIL += not good
    print(f"  {'ok' if good else 'FAIL'}  {name}"
          + ("" if good else f"  got={got!r} want={want!r}"))


def draft(tmp, chosen):
    d = Path(tmp) / "game"
    d.mkdir(exist_ok=True)
    (d / "mechanisms.json").write_text(json.dumps({"chosen": chosen}),
                                       encoding="utf-8")
    return d


def vault_block(chosen, tmp, env=None):
    old = {k: os.environ.get(k) for k in ("CRITIC_VAULT", "GAMEVAULT")}
    os.environ.pop("CRITIC_VAULT", None)
    os.environ.pop("GAMEVAULT", None)
    os.environ.update(env or {})
    err = io.StringIO()
    try:
        with contextlib.redirect_stdout(err):
            return prompts._vault(draft(tmp, chosen)), err.getvalue()
    finally:
        for k, v in old.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


def main():
    print("vault leads in the critic prompt")
    have_vault = (Path(os.environ.get("GAMEVAULT", "/root/gamevault"))
                  / "vault_tools.py").is_file()
    with tempfile.TemporaryDirectory() as tmp:
        if have_vault:
            b, w = vault_block(["worker_placement",
                                "simultaneous_action_selection"], tmp)
            ok("declared conflict surfaces", "CONFLICT:" in b
               and "simultaneous-action-selection" in b)
            ok("risk carries the recorded fix",
               "RISK:" in b and "variable-turn-order" in b)
            ok("leads framed as leads, not verdicts", "not a verdict" in b)

            b, w = vault_block(["hand_management"], tmp)
            ok("card mechanism collides with the FDM constraint",
               "CONFLICT:" in b and "fdm-printed-components-only" in b)

            b, w = vault_block(["ratchet_dial", "peephole_screen"], tmp)
            ok("invented vocabulary -> empty block", b, "")
            ok("...and a loud warning", "WARNING" in w and "ratchet_dial" in w)

            b, w = vault_block(["worker_placement", "ratchet_dial"], tmp)
            ok("partial map still produces leads", "CONFLICT:" in b
               or "RISK:" in b or "no declared" in b)
            ok("...and warns about the unmapped id", "ratchet_dial" in w)

            b, w = vault_block(["worker_placement"], tmp,
                               {"CRITIC_VAULT": "off"})
            ok("kill switch", b, "")

        b, w = vault_block(["worker_placement"], tmp,
                           {"GAMEVAULT": "/nonexistent-vault"})
        ok("missing vault -> empty block, not a crash", b, "")
        ok("...and says so", "WARNING" in w and "no design vault" in w)

        d = Path(tmp) / "bare"
        d.mkdir()
        err = io.StringIO()
        with contextlib.redirect_stdout(err):
            b = prompts._vault(d)
        ok("no mechanisms.json -> empty block", b, "")

        if have_vault:
            text = prompts.critic(draft(tmp, ["worker_placement",
                                              "simultaneous_action_selection"]))
            ok("critic() prompt carries the vault block",
               "the design vault says" in text)

            # the two bridges added 2026-08-21: aliases in the vault, and the
            # taxonomy MECHANISM LOCK declares at the source
            b, w = vault_block(["area_control", "co-op"], tmp)
            ok("alias catches what fuzzy would miss",
               "area-majority-influence" in b and "cooperative-game" in b)

            d = draft(tmp, [])
            (d / "mechanisms.json").write_text(json.dumps({
                "chosen": ["ratchet_dial"],
                "bgg_taxonomy": {"ratchet_dial": ["Events"]}}),
                encoding="utf-8")
            err = io.StringIO()
            with contextlib.redirect_stdout(err):
                b = prompts._vault(d)
            ok("declared taxonomy maps invented vocabulary",
               "mechanisms/events" in b)

            (d / "mechanisms.json").write_text(json.dumps({
                "chosen": ["worker_placement"],
                "bgg_taxonomy": {"worker_placement": ["No Such Mechanism"]}}),
                encoding="utf-8")
            err = io.StringIO()
            with contextlib.redirect_stdout(err):
                b = prompts._vault(d)
            ok("bad declared name warns and falls back",
               "worker-placement" in b and "no such node" in err.getvalue())

            p = prompts.mechanism(d)
            ok("mechanism() prompt carries the taxonomy bridge",
               "taxonomy bridge" in p and "bgg_taxonomy" in p
               and "do NOT force a match" in p)
        else:
            print("  (no vault at $GAMEVAULT - live-vault cases skipped)")

        # lane B: the market briefing rides into DISCOVER's trend files
        import trends
        old = os.environ.get("GAMEVAULT")
        try:
            os.environ["GAMEVAULT"] = tmp
            ok("no briefing -> no phantom trend file",
               trends.gamevault_briefing(), [])
            bdir = Path(tmp) / "briefings"
            bdir.mkdir()
            (bdir / "trends-2026-07.md").write_text("old", encoding="utf-8")
            (bdir / "trends-2026-08.md").write_text("new", encoding="utf-8")
            got = trends.gamevault_briefing()
            ok("newest briefing only",
               [Path(p).name for p in got], ["trends-2026-08.md"])
        finally:
            os.environ.pop("GAMEVAULT", None)
            if old is not None:
                os.environ["GAMEVAULT"] = old

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
