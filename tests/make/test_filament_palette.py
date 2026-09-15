"""A printed colour names a spool, and the stock says which spool."""

from pathlib import Path
import subprocess
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
PALETTE = SCRIPTS / "cadfilament.py"

# Bambu Lab's published "Filament Hex Code Table - PETG Basic", read 2026-09-15,
# with the colour code the catalogue lists beside each name.
PETG_BASIC = {
    "black": ("#000000", "30105"),
    "white": ("#FFFFFF", "30106"),
    "gray": ("#7F7E83", "30107"),
    "misty blue": ("#688197", "30108"),
    "red": ("#D6001C", "30201"),
    "orange": ("#FF671F", "30302"),
    "yellow": ("#FCE300", "30402"),
    "dark beige": ("#DBC8B6", "30403"),
    "green": ("#009639", "30502"),
    "pine green": ("#034638", "30503"),
    "reflex blue": ("#001489", "30603"),
    "navy blue": ("#0086D6", "30604"),
    "dark brown": ("#4F2C1D", "30800"),
}


class FilamentPaletteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        import cadfilament

        cls.palette = cadfilament

    def test_both_stocks_round_trip_to_the_hex_their_catalogue_publishes(self):
        from cadgen.color import linear_to_srgb

        for stock, table in self.palette.MATERIALS.items():
            for name, published in table.items():
                with self.subTest(stock=stock, colour=name):
                    red, green, blue, alpha = tuple(
                        self.palette.filament(name, material=stock)
                    )
                    shown = "#%02X%02X%02X" % tuple(
                        round(linear_to_srgb(channel) * 255)
                        for channel in (red, green, blue)
                    )
                    self.assertEqual(shown, published)
                    self.assertEqual(alpha, 1.0)

    def test_petg_basic_holds_exactly_the_stocked_colours_and_their_codes(self):
        table = self.palette.MATERIALS["petg basic"]
        self.assertEqual(
            table, {name: hex_value for name, (hex_value, _) in PETG_BASIC.items()}
        )
        source = PALETTE.read_text(encoding="utf-8")
        petg = source.split('"petg basic": {', 1)[1].split("},", 1)[0]
        for name, (hex_value, code) in PETG_BASIC.items():
            with self.subTest(colour=name):
                self.assertIn(f'"{name}": "{hex_value}",', petg)
                self.assertIn(f"# {code}", petg)

    def test_a_shared_name_resolves_to_the_stock_that_was_asked_for(self):
        shared = set(self.palette.MATERIALS["pla lite"]) & set(
            self.palette.MATERIALS["petg basic"]
        )
        self.assertEqual(
            shared, {"black", "white", "gray", "red", "orange", "yellow", "green"}
        )
        self.assertEqual(self.palette.DEFAULT_MATERIAL, "pla lite")
        self.assertEqual(self.palette.filament_hex("red"), "#FF0000")
        self.assertEqual(
            self.palette.filament_hex("red", material="PETG Basic"), "#D6001C"
        )
        self.assertEqual(self.palette.FILAMENTS, self.palette.MATERIALS["pla lite"])

        lite, petg = (
            self.palette.MATERIALS["pla lite"],
            self.palette.MATERIALS["petg basic"],
        )
        self.assertEqual(
            sorted(name for name in shared if lite[name] != petg[name]),
            ["gray", "green", "red", "white", "yellow"],
        )
        # The other two are the same colour in both stocks, not a missing entry.
        self.assertEqual(lite["black"], petg["black"])
        self.assertEqual(lite["orange"], petg["orange"])

    def test_names_and_stocks_ignore_case_separators_and_family_shorthand(self):
        for spelling in ("PETG Basic", "petg_basic", "PETG-BASIC", "petg", "PETG"):
            with self.subTest(stock=spelling):
                self.assertEqual(
                    self.palette.filament_hex("Misty Blue", material=spelling),
                    self.palette.filament_hex("misty-blue", material="petg basic"),
                )
        self.assertEqual(
            self.palette.filament_hex("Dark Gray"),
            self.palette.filament_hex("dark_gray"),
        )

    def test_a_colour_the_other_stock_carries_names_that_stock(self):
        with self.assertRaises(ValueError) as raised:
            self.palette.filament("misty blue")
        message = str(raised.exception)
        self.assertIn("Bambu Lab PETG Basic", message)
        self.assertIn("material='petg basic'", message)

        with self.assertRaises(ValueError) as raised:
            self.palette.filament("cocoa brown", material="PETG")
        self.assertIn("Bambu Lab PLA Lite", str(raised.exception))

    def test_an_unknown_colour_or_unstocked_material_raises_with_the_list(self):
        with self.assertRaises(ValueError) as raised:
            self.palette.filament("hot pink")
        self.assertIn("sunflower yellow", str(raised.exception))

        with self.assertRaises(ValueError) as raised:
            self.palette.filament("black", material="nylon")
        message = str(raised.exception)
        self.assertIn("not a stock this repository prints", message)
        self.assertIn("Bambu Lab PETG Basic", message)

    def test_alpha_reaches_the_color_on_either_stock(self):
        self.assertEqual(
            tuple(self.palette.filament("navy blue", 0.42, material="PETG"))[3], 0.42
        )

    def test_palette_self_check_passes(self):
        result = subprocess.run(
            [sys.executable, str(PALETTE)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("all checks passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
