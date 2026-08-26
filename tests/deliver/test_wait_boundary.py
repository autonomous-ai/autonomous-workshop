import importlib.util
import unittest

import workshop.deliver as deliver


class DeliverWaitBoundaryTest(unittest.TestCase):
    def test_deliver_has_no_speculative_physical_effect_api(self):
        self.assertEqual(deliver.__all__, ())
        for name in (
            "DeliverContext",
            "Delivered",
            "DeliveryEvidenceReceipt",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(deliver, name))

    def test_removed_contract_modules_do_not_exist(self):
        self.assertIsNone(importlib.util.find_spec("workshop.deliver.contracts"))
        self.assertIsNone(importlib.util.find_spec("workshop.deliver.evidence"))


if __name__ == "__main__":
    unittest.main()
