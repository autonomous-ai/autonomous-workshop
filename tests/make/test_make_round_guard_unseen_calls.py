"""Issue #113: the guard fails closed on a make_round call it cannot see.

In Broken God attempt 18 five Component Worker commands each edited a part
source in a ``python3 - <<'EOF'`` heredoc, then called make_round on a later
line. A quote in the heredoc body hid the call from the guard's parser, so
the round ran with no worker nonce. The commands below have the same five
shapes; their bodies are synthetic.
"""

import unittest

from workshop.make.make_round_guard import decide, make_round_calls

SCRIPT = '"$WORKSHOP_PYTHON" /w/.agents/skills/make-round/scripts/make_round'


def _round(component):
    return SCRIPT + " . --component part_%s.step.py --nozzle 0.4" % component


ATTEMPT_18_SHAPES = (
    # wing r0002: cd, then a heredoc whose body holds triple-quoted strings.
    "cd /w/artifacts/make/r0001/product/cad && python3 - <<'EOF'\n"
    "p='part_wing.step.py'; s=open(p).read()\n"
    "i=s.index('    # the wing\\'s toothed boss')\n"
    "j=s.index('    # the wing\\'s plain boss')\n"
    "old='''def gen_step(instance: int = 1):\n"
    "    \"\"\"wing#`instance` in its print stance.\"\"\"\n"
    "'''\n"
    "new='''def _build(instance: int = 1):\n"
    "    \"\"\"wing#`instance`, the figure's left.\"\"\"\n"
    "'''\n"
    "assert old in s; s=s.replace(old,new)\n"
    "open(p,'w').write(s)\n"
    "EOF\n" + _round("wing"),
    # crest-helm r0006: an escaped quote inside the body.
    "python3 - <<'EOF'\n"
    "p='part_crest-helm.step.py'\n"
    "s=open(p).read()\n"
    "a=s.index('    # grille on the figure\\'s right')\n"
    "b=s.index('    # lancet relief on both cheek plates')\n"
    "new='''    # grille on the figure's right: four slits\n"
    "'''\n"
    "s=s[:a]+new+s[b:]\n"
    "open(p,'w').write(s)\n"
    "EOF\n" + _round("crest-helm"),
    # arm-right r0010: a grep between the heredoc and the call.
    "python3 - <<'EOF'\n"
    "p='part_arm-right.step.py'\n"
    "s=open(p).read()\n"
    "i=s.index('    # the fist\\'s roof land')\n"
    "j=s.index('    # the slot\\'s outer end')\n"
    "a=s[s.index(\"    # The slot's roof (its -Y side\"):s.index(\"    body = body\")]\n"
    "s=s.replace(a,'''    # the slot's roof rises outward\n'''); open(p,'w').write(s)\n"
    "EOF\n"
    "grep -n \"^FIST_SLOT_W = 3.8$\" part_arm-right.step.py; " + _round("arm-right"),
    # arm-right r0011: the body mentions the fist's corner in a comment.
    "python3 - <<'EOF'\n"
    "p='part_arm-right.step.py'\n"
    "s=open(p).read()\n"
    "i=s.index('    # the staff\\'s slot')\n"
    "s=s.replace(\"FIST_SLOT_W = 3.8\\n\",\"FIST_SLOT_W = 3.8\\nFIST_SLOT_DEG = 30.0\\n\")\n"
    "s+='''\n"
    "    # the staff slides in from the fist's front-outer corner\n"
    "'''\n"
    "open(p,'w').write(s)\n"
    "EOF\n"
    "grep -n \"^import math\\|FIST_SLOT\" part_arm-right.step.py; " + _round("arm-right"),
    # arm-right r0012: one assert line, then the call.
    "python3 - <<'EOF'\n"
    "p='part_arm-right.step.py'\n"
    "s=open(p).read()\n"
    "i=s.index('    # the fist\\'s outer wall')\n"
    "a=\"    # Fist-plate rivets left out.\\n\"\n"
    "b=a+'''    # end the fist's sliver in a land\n'''\n"
    "assert a in s; s=s.replace(a,b); open(p,'w').write(s)\n"
    "EOF\n" + _round("arm-right"),
)


def _event(command, agent_type="component-worker"):
    event = {
        "session_id": "s-1",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_use_id": "t-1",
    }
    if agent_type is not None:
        event["agent_type"] = agent_type
        event["agent_id"] = "a-1"
    return event


class _Issuer:
    def __init__(self):
        self.issued = []

    def __call__(self, event, component):
        nonce = "%032x" % (len(self.issued) + 1)
        self.issued.append(nonce)
        return nonce


def _decision(output):
    return None if output is None else output["hookSpecificOutput"]["permissionDecision"]


class UnseenCallTest(unittest.TestCase):
    def test_each_shape_hides_its_call_from_the_parser(self):
        # As in attempt 18: the call is swallowed into a quoted token.
        for command in ATTEMPT_18_SHAPES:
            with self.subTest(command=command[:60]):
                self.assertEqual(make_round_calls(command), [])

    def test_the_attempt_18_shapes_are_denied_for_every_caller(self):
        for agent_type in ("component-worker", None, "component-reviewer"):
            for command in ATTEMPT_18_SHAPES:
                with self.subTest(agent_type=agent_type, command=command[:60]):
                    issuer = _Issuer()
                    output = decide(_event(command, agent_type), issue=issuer)
                    self.assertEqual(_decision(output), "deny")
                    self.assertEqual(issuer.issued, [])
                    reason = output["hookSpecificOutput"]["permissionDecisionReason"]
                    self.assertIn("own", reason)

    def test_a_command_naming_make_round_that_parses_to_no_call_is_denied(self):
        # The parser sees no call: the name sits inside another program's text.
        for command in (
            "python3 -c 'import subprocess' ; echo make_round",
            "printf '%s\\n' make_round | bash",
            "xargs -a list make_round",
        ):
            with self.subTest(command=command):
                self.assertEqual(make_round_calls(command), [])
                self.assertEqual(_decision(decide(_event(command), issue=_Issuer())), "deny")

    def test_a_heredoc_beside_a_plain_call_is_denied(self):
        command = "cat > notes.txt <<'EOF'\nplain\nEOF\n" + _round("wing")
        self.assertEqual(_decision(decide(_event(command), issue=_Issuer())), "deny")

    def test_a_plain_call_is_admitted_with_a_nonce(self):
        issuer = _Issuer()
        output = decide(_event(_round("wing")), issue=issuer)
        self.assertEqual(_decision(output), "allow")
        self.assertIn("--worker-nonce %s" % issuer.issued[0],
                      output["hookSpecificOutput"]["updatedInput"]["command"])

    def test_reading_the_script_is_still_allowed(self):
        for command in (
            "sed -n 1,40p /w/.agents/skills/make-round/scripts/make_round",
            "grep -n SHAPE /w/.agents/skills/make-round/scripts/make_round",
            "cat /w/.agents/skills/make-round/scripts/make_round | head -20",
            "cd /w && grep -rn worker_nonce .agents/skills/make-round/scripts/make_round",
        ):
            for agent_type in ("component-worker", None):
                with self.subTest(command=command, agent_type=agent_type):
                    self.assertIsNone(decide(_event(command, agent_type), issue=_Issuer()))


if __name__ == "__main__":
    unittest.main()
