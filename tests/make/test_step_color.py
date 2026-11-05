from __future__ import annotations

import re
import unittest

from workshop.make.cad.step_color import (
    StepPartColor,
    displayed_hex,
    is_legacy_linear,
    linear_to_srgb_hex,
    read_step_part_colors,
)


from tests.make.step_documents import (
    linear_channels,
    srgb_channels,
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


class StepColourConventionTest(unittest.TestCase):
    """Sealed channels are sRGB; linear ones sealed before 2026-11-05 are
    recognised exactly and read as the hex they were authored from."""

    def test_no_srgb_byte_is_mistaken_for_a_linear_one(self):
        # Only 0 and 1, where the two conventions agree, are both.
        linear = [srgb_to_linear(k / 255.0) for k in range(256)]
        for k in range(1, 255):
            with self.subTest(byte=k):
                nearest = min(abs(k / 255.0 - value) for value in linear)
                self.assertGreater(nearest, 1e-6)

    def test_every_hex_reads_back_from_either_convention(self):
        for value in ("#5a3a22", "#1a1a1a", "#e9dcb8", "#c49a6c", "#010203"):
            with self.subTest(hex=value):
                self.assertFalse(is_legacy_linear(srgb_channels(value)))
                self.assertEqual(displayed_hex(srgb_channels(value)), value)
                self.assertTrue(is_legacy_linear(linear_channels(value)))
                self.assertEqual(displayed_hex(linear_channels(value)), value)

    def test_twelve_printed_digits_still_read_as_legacy(self):
        printed = tuple(float("%.12f" % value) for value in linear_channels("#5a3a22"))

        self.assertTrue(is_legacy_linear(printed))
        self.assertEqual(displayed_hex(printed), "#5a3a22")

    def test_float32_and_seven_digit_rounding_still_read_as_legacy(self):
        # OpenCascade holds colours in float32 and build123d rounds to 7
        # digits; a sealed v01 beaver STEP strays 1.3e-9 from the exact value.
        import struct

        for value in ("#5a3a22", "#1a1a1a", "#e9dcb8"):
            exact = linear_channels(value)
            for strayed in (
                tuple(struct.unpack("f", struct.pack("f", c))[0] for c in exact),
                tuple(round(c, 7) for c in exact),
            ):
                with self.subTest(hex=value, channels=strayed):
                    self.assertTrue(is_legacy_linear(strayed))
                    self.assertEqual(displayed_hex(strayed), value)

    def test_black_white_and_a_hand_typed_colour_are_srgb(self):
        for channels, shown in (
            ((0.0, 0.0, 0.0), "#000000"),
            ((1.0, 1.0, 1.0), "#ffffff"),
            ((1.0, 0.0, 1.0), "#ff00ff"),
            ((0.5, 0.25, 0.1), "#80401a"),
        ):
            with self.subTest(channels=channels):
                self.assertFalse(is_legacy_linear(channels))
                self.assertEqual(displayed_hex(channels), shown)

    def test_one_linear_channel_beside_srgb_ones_is_not_legacy(self):
        mixed = (srgb_to_linear(0x5A / 255.0), 0x3A / 255.0, 0x22 / 255.0)

        self.assertFalse(is_legacy_linear(mixed))


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

    def test_a_legacy_linear_step_reads_as_the_hex_it_was_authored_from(self):
        content = step_document(
            [("body", "#5a3a22"), ("nose", "#1a1a1a"), ("muzzle", "#e9dcb8")],
            legacy_linear=True,
        )

        colours = read_step_part_colors(content)

        self.assertEqual(
            {name: value.hex for name, value in colours.items()},
            {"body": "#5a3a22", "nose": "#1a1a1a", "muzzle": "#e9dcb8"},
        )
        self.assertAlmostEqual(colours["body"].channels[0], srgb_to_linear(0x5A / 255.0), places=9)

    def test_an_srgb_step_keeps_its_raw_channels(self):
        colours = read_step_part_colors(step_document([("body", "#5a3a22")]))

        self.assertEqual(colours["body"].hex, "#5a3a22")
        self.assertAlmostEqual(colours["body"].channels[0], 0x5A / 255.0, places=9)

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
