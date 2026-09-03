import random
import re
import unittest

from workshop.make.step_canonical import (
    StepCanonicalError,
    canonical_step_digest,
    canonical_step_equal,
)


HEADER = (
    "ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('Open CASCADE Model'),'2;1');\n"
    "FILE_NAME('toy','1970-01-01T00:00:00',('Author'),('Open CASCADE'),"
    "'Open CASCADE STEP processor 7.9','cadgen','Unknown');\n"
    "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\nENDSEC;\n"
)
ENTITIES = (
    "#1 = CARTESIAN_POINT('',(0.,0.,0.));",
    "#2 = CARTESIAN_POINT('',(1.,0.,0.));",
    "#3 = VERTEX_POINT('',#1);",
    "#4 = VERTEX_POINT('',#2);",
    "#5 = COLOUR_RGB('',0.12,0.19,0.24);",
    "#6 = COLOUR_RGB('',0.45,0.55,0.60);",
    "#7 = STYLED_ITEM('color',(#5),#3);",
    "#8 = STYLED_ITEM('color',(#6),#4);",
    "#9 = MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',(\n"
    "    #7,#8),#1);",
    "#10 = PRODUCT('semi;colon #1 name','',' ',(#9));",
)


def _document(entities=ENTITIES):
    return (HEADER + "DATA;\n" + "\n".join(entities) + "\nENDSEC;\nEND-ISO-10303-21;\n").encode()


def _renumber(text: str, offset: int) -> str:
    out = []
    index = 0
    in_string = False
    while index < len(text):
        char = text[index]
        if in_string:
            out.append(char)
            in_string = char != "'"
        elif char == "'":
            in_string = True
            out.append(char)
        elif char == "#":
            match = re.match(r"#(\d+)", text[index:])
            out.append("#%d" % (int(match.group(1)) + offset))
            index += match.end()
            continue
        else:
            out.append(char)
        index += 1
    return "".join(out)


class CanonicalStepDigestTest(unittest.TestCase):
    def test_digest_ignores_numbering_order_and_wrapping(self):
        base = canonical_step_digest(_document())
        renumbered = _renumber(_document().decode(), 500).encode()
        self.assertEqual(canonical_step_digest(renumbered), base)
        shuffled = list(ENTITIES)
        random.Random(7).shuffle(shuffled)
        self.assertEqual(canonical_step_digest(_document(shuffled)), base)
        rewrapped = _document().decode().replace("(\n    #7,#8)", "(#7,\n  #8)").encode()
        self.assertEqual(canonical_step_digest(rewrapped), base)
        self.assertTrue(canonical_step_equal(_document(), renumbered))

    def test_digest_ignores_which_id_each_style_entity_carries(self):
        # Open CASCADE hands out STYLED_ITEM ids in pointer order: the same
        # model can carry #7 -> #3 / #8 -> #4 on one export and #8 -> #3 /
        # #7 -> #4 on the next, with the colours travelling along.
        swapped = list(ENTITIES)
        swapped[6] = "#7 = STYLED_ITEM('color',(#6),#4);"
        swapped[7] = "#8 = STYLED_ITEM('color',(#5),#3);"
        swapped[8] = ENTITIES[8].replace("#7,#8", "#8,#7")
        self.assertEqual(canonical_step_digest(_document(swapped)), canonical_step_digest(_document()))

    def test_digest_sees_every_literal_and_wiring_change(self):
        base = canonical_step_digest(_document())
        cases = {
            "coordinate": ("#2 = CARTESIAN_POINT('',(1.,0.,0.));", "#2 = CARTESIAN_POINT('',(1.001,0.,0.));"),
            "colour": ("#5 = COLOUR_RGB('',0.12,0.19,0.24);", "#5 = COLOUR_RGB('',0.5,0.19,0.24);"),
            "wiring": ("#7 = STYLED_ITEM('color',(#5),#3);", "#7 = STYLED_ITEM('color',(#5),#4);"),
            "string": ("'semi;colon #1 name'", "'semi;colon #2 name'"),
            "type": ("#3 = VERTEX_POINT('',#1);", "#3 = VERTEX_LOOP('',#1);"),
        }
        for label, (old, new) in cases.items():
            with self.subTest(label=label):
                text = _document().decode()
                self.assertIn(old, text)
                self.assertNotEqual(canonical_step_digest(text.replace(old, new, 1).encode()), base)
        header_changed = _document().decode().replace("FILE_NAME('toy'", "FILE_NAME('other'", 1).encode()
        self.assertNotEqual(canonical_step_digest(header_changed), base)

    def test_digest_counts_duplicate_subgraphs(self):
        doubled = list(ENTITIES) + ["#11 = CARTESIAN_POINT('',(0.,0.,0.));"]
        self.assertNotEqual(canonical_step_digest(_document(doubled)), canonical_step_digest(_document()))

    def test_malformed_inputs_are_refused(self):
        for label, content in {
            "not-step": b"hello",
            "no-data": HEADER.encode() + b"END-ISO-10303-21;\n",
            "unterminated-string": _document(("#1 = CARTESIAN_POINT('oops,(0.,0.,0.));",)),
            "duplicate-id": _document(("#1 = CARTESIAN_POINT('',(0.,0.,0.));", "#1 = CARTESIAN_POINT('',(1.,0.,0.));")),
            "dangling": _document(("#1 = VERTEX_POINT('',#9);",)),
            "bad-id": _document(("#x = VERTEX_POINT('',#1);",)),
            "no-entities": _document(()),
        }.items():
            with self.subTest(label=label), self.assertRaises(StepCanonicalError):
                canonical_step_digest(content)
        with self.assertRaises(StepCanonicalError):
            canonical_step_digest("text")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
