import tempfile
import unittest
from pathlib import Path
from unittest import mock

import inventor_workshop.schemas as schemas_module
from inventor_workshop.schemas import SCHEMA_NAMES, resolve_schemas_root


class PackageDataTest(unittest.TestCase):
    def test_target_layout_prefers_package_owned_schemas(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            package = target / "inventor_workshop"
            schemas = package / "_data" / "schemas"
            schemas.mkdir(parents=True)
            for name in SCHEMA_NAMES:
                (schemas / name).write_text("{}\n", encoding="utf-8")
            legacy = target / "legacy-does-not-exist"
            with mock.patch.object(
                schemas_module,
                "__file__",
                str(package / "schemas.py"),
            ), mock.patch.object(
                schemas_module.sysconfig,
                "get_path",
                return_value=str(legacy),
            ):
                self.assertEqual(resolve_schemas_root(), schemas.resolve())


if __name__ == "__main__":
    unittest.main()
