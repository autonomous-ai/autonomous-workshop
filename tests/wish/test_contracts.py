import json
import unittest

from workshop.errors import ContractError
from workshop.wish import Wish, WishReference
from workshop.wish.contracts import (
    MAX_WISH_REFERENCE_BYTES,
    MAX_WISH_REFERENCE_TOTAL_BYTES,
    MAX_WISH_REFERENCES,
)


def _reference(index=1, slug="side", extension="png", media_type="image/png", **overrides):
    value = {
        "name": "ref-%02d-%s.%s" % (index, slug, extension),
        "sha256": ("%02x" % index) * 32,
        "media_type": media_type,
        "size": 1_024,
        "width": 640,
        "height": 480,
    }
    value.update(overrides)
    return value


class WishReferenceContractTest(unittest.TestCase):
    def test_plain_wish_bytes_are_unchanged_by_the_reference_field(self):
        wish = Wish.create("wish-plain", "a moon that waddles", context={"source": "t"})

        document = wish.to_dict()

        self.assertNotIn("references", document)
        self.assertEqual(
            list(json.dumps(document, sort_keys=True)),
            list(
                json.dumps(
                    {
                        "schema_version": 1,
                        "product_id": "wish-plain",
                        "objective": "a moon that waddles",
                        "constraints": {},
                        "context": {"source": "t"},
                    },
                    sort_keys=True,
                )
            ),
        )
        self.assertEqual(wish.references, ())

    def test_references_round_trip_in_order(self):
        first = _reference(1, "side", "jpg", "image/jpeg")
        second = _reference(2, "front")
        wish = Wish.create("wish-refs", "a locomotive", references=[first, second])

        document = wish.to_dict()

        self.assertEqual(document["references"], [first, second])
        self.assertEqual(Wish(**document), wish)
        self.assertEqual(wish.references[0].path, "wish-references/ref-01-side.jpg")
        self.assertEqual(wish.references[1].index, 2)
        self.assertIsInstance(wish.references[0], WishReference)

    def test_references_must_be_numbered_in_order_and_unique(self):
        with self.assertRaisesRegex(ContractError, "numbered ref-01"):
            Wish.create("wish-x", "toy", references=[_reference(2)])
        with self.assertRaisesRegex(ContractError, "numbered ref-01"):
            Wish.create("wish-x", "toy", references=[_reference(1), _reference(3)])
        with self.assertRaisesRegex(ContractError, "repeat the same bytes"):
            Wish.create(
                "wish-x",
                "toy",
                references=[_reference(1), _reference(2, sha256="01" * 32)],
            )
        with self.assertRaisesRegex(ContractError, "at most %d" % MAX_WISH_REFERENCES):
            Wish.create(
                "wish-x",
                "toy",
                references=[_reference(index) for index in range(1, MAX_WISH_REFERENCES + 2)],
            )
        with self.assertRaisesRegex(ContractError, "total at most"):
            Wish.create(
                "wish-x",
                "toy",
                references=[
                    _reference(index, size=MAX_WISH_REFERENCE_BYTES)
                    for index in range(1, MAX_WISH_REFERENCE_TOTAL_BYTES // MAX_WISH_REFERENCE_BYTES + 2)
                ],
            )
        with self.assertRaisesRegex(ContractError, "must be a list"):
            Wish.create("wish-x", "toy", references=_reference(1))

    def test_reference_fields_are_validated(self):
        cases = {
            "name": ("Ref-01-Side.png", "look like ref-NN"),
            "sha256": ("0" * 63, "64 lowercase hex"),
            "media_type": ("image/gif", "media_type must be one of"),
            "size": (0, "size must be an integer"),
            "width": (8, "width must be an integer"),
            "height": (20_000, "height must be an integer"),
        }
        for field_name, (value, message) in cases.items():
            with self.subTest(field=field_name), self.assertRaisesRegex(
                ContractError, message
            ):
                WishReference.from_value(_reference(**{field_name: value}), "wish reference")
        with self.assertRaisesRegex(ContractError, "extension must match"):
            WishReference.from_value(
                _reference(1, "side", "png", "image/jpeg"), "wish reference"
            )
        with self.assertRaisesRegex(ContractError, "at most 50000000 pixels"):
            WishReference.from_value(
                _reference(width=10_000, height=6_000), "wish reference"
            )
        with self.assertRaisesRegex(ContractError, "carry exactly"):
            WishReference.from_value(
                dict(_reference(), note="extra"), "wish reference"
            )


if __name__ == "__main__":
    unittest.main()
