from __future__ import annotations

import re
import unittest

from workshop.make.cad.step_color import (
    StepPartColor,
    linear_to_srgb_hex,
    read_step_part_colors,
)


from tests.make.step_documents import (
    linear_channels,
    srgb_to_linear,
    step_document,
)


class LinearToSrgbTest(unittest.TestCase):
    def test_channels_round_trip_the_hex_a_designer_picked(self):
        for value in ("#222a38", "#d8dee9", "#d89b3c", "#000000", "#ffffff"):
            self.assertEqual(linear_to_srgb_hex(linear_channels(value)), value)

    def test_channel_outside_the_unit_range_is_refused(self):
        for channels in ((0.0, 0.0, 1.5), (-0.1, 0.0, 0.0), (float("nan"), 0.0, 0.0)):
            with self.assertRaises(ValueError):
                linear_to_srgb_hex(channels)

    def test_a_colour_requires_exactly_three_channels(self):
        with self.assertRaises(ValueError):
            linear_to_srgb_hex((0.0, 0.0))


class ReadStepPartColorsTest(unittest.TestCase):
    def test_every_named_part_keeps_the_exact_colour_make_sealed(self):
        content = step_document(
            [("lunar_base", "#222a38"), ("moon_rocker", "#d8dee9")]
        )

        colours = read_step_part_colors(content)

        self.assertEqual(
            {name: value.hex for name, value in colours.items()},
            {"lunar_base": "#222a38", "moon_rocker": "#d8dee9"},
        )
        self.assertIsInstance(colours["lunar_base"], StepPartColor)
        self.assertEqual(colours["lunar_base"].name, "lunar_base")

    def test_an_unstyled_step_reports_no_colour(self):
        self.assertEqual(read_step_part_colors(step_document([("owl", None)])), {})
        self.assertEqual(
            read_step_part_colors(step_document([("owl", "#d8dee9")], colours=False)),
            {},
        )

    def test_a_part_with_two_different_colours_is_dropped(self):
        content = step_document([("owl", "#d8dee9"), ("owl", "#222a38")])

        self.assertEqual(read_step_part_colors(content), {})

    def test_a_part_repeating_one_colour_survives(self):
        content = step_document([("owl", "#d8dee9"), ("owl", "#d8dee9")])

        self.assertEqual(read_step_part_colors(content)["owl"].hex, "#d8dee9")

    def test_a_channel_outside_the_unit_range_is_dropped(self):
        content = step_document([("owl", "#d8dee9")])
        self.assertIn("owl", read_step_part_colors(content))

        broken = re.sub(rb"COLOUR_RGB\('',[^;]*\)", b"COLOUR_RGB('',1.5,0.5,0.5)", content)

        self.assertEqual(read_step_part_colors(broken), {})

    def test_a_duplicate_instance_id_makes_every_reference_ambiguous(self):
        content = step_document([("owl", "#d8dee9")]).replace(
            b"ENDSEC;\nEND-ISO", b"#10 = PRODUCT('other','other','',(#3));\nENDSEC;\nEND-ISO"
        )

        self.assertEqual(read_step_part_colors(content), {})

    def test_a_comment_and_a_quoted_semicolon_do_not_split_records(self):
        content = step_document([("owl", "#d8dee9")]).replace(
            b"PRODUCT('owl','owl','',(#3));",
            b"PRODUCT('owl;/*x*/','owl;/*x*/','',(#3)); /* trailing */",
        )

        self.assertEqual(
            {name: value.hex for name, value in read_step_part_colors(content).items()},
            {"owl;/*x*/": "#d8dee9"},
        )

    def test_bytes_are_required_and_empty_content_is_colourless(self):
        with self.assertRaises(TypeError):
            read_step_part_colors("not bytes")  # type: ignore[arg-type]
        self.assertEqual(read_step_part_colors(b""), {})
        self.assertEqual(read_step_part_colors(b"solid mesh\nendsolid mesh\n"), {})


if __name__ == "__main__":  # pragma: no cover - unittest entry point
    unittest.main()
