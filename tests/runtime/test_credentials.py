import os
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.runtime.credentials import (
    factory_credential_environment,
    factory_credential_file,
    validate_factory_credential_configuration,
)


class FactoryCredentialBoundaryTest(unittest.TestCase):
    @staticmethod
    def _private_file(root: Path, source: str) -> Path:
        directory = root / "credentials"
        directory.mkdir(mode=0o700)
        os.chmod(directory, 0o700)
        path = directory / "factory.env"
        path.write_text(source, encoding="utf-8")
        os.chmod(path, 0o600)
        return path

    def test_loads_private_file_and_environment_overrides_without_other_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            home.mkdir(mode=0o700)
            self._private_file(
                home,
                "FACTORY_ALICE_USERNAME=alice\nFACTORY_PASSWORD=file-secret\n",
            )
            values = factory_credential_environment(
                {
                    "WORKSHOP_HOME": str(home),
                    "FACTORY_PASSWORD": "environment-secret",
                    "AWS_SECRET_ACCESS_KEY": "not-factory-data",
                }
            )
            self.assertEqual(
                values,
                {
                    "FACTORY_ALICE_USERNAME": "alice",
                    "FACTORY_PASSWORD": "environment-secret",
                },
            )
            self.assertEqual(
                factory_credential_file({"WORKSHOP_HOME": str(home)}),
                home / "credentials" / "factory.env",
            )

    def test_missing_file_returns_only_supported_environment_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "unused"
            values = factory_credential_environment(
                {
                    "WORKSHOP_HOME": str(home),
                    "FACTORY_USERNAME": "alice",
                    "FACTORY_PASSWORD": "secret",
                    "FACTORY_TOKEN": "unsupported",
                }
            )
            self.assertEqual(
                values,
                {"FACTORY_USERNAME": "alice", "FACTORY_PASSWORD": "secret"},
            )
            self.assertFalse(home.exists())

    def test_rejects_unsafe_modes_symlinks_duplicates_and_unknown_names(self):
        cases = (
            ("FACTORY_PASSWORD=one\nFACTORY_PASSWORD=two\n", "duplicate"),
            ("FACTORY_TOKEN=secret\n", "unsupported name"),
            ("FACTORY_PASSWORD= secret\n", "invalid value"),
        )
        for source, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as temporary:
                home = Path(temporary).resolve() / "home"
                home.mkdir(mode=0o700)
                self._private_file(home, source)
                with self.assertRaisesRegex(ContractError, message):
                    factory_credential_environment({"WORKSHOP_HOME": str(home)})

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "home"
            home.mkdir(mode=0o700)
            path = self._private_file(home, "FACTORY_PASSWORD=secret\n")
            os.chmod(path, 0o644)
            with self.assertRaisesRegex(ContractError, "0600"):
                factory_credential_environment({"WORKSHOP_HOME": str(home)})

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "home"
            home.mkdir(mode=0o700)
            path = self._private_file(home, "FACTORY_PASSWORD=secret\n")
            target = path.with_name("actual.env")
            path.rename(target)
            path.symlink_to(target)
            with self.assertRaisesRegex(ContractError, "0600"):
                factory_credential_environment({"WORKSHOP_HOME": str(home)})

    def test_rejects_literal_shell_quotes_in_file_and_environment_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "home"
            home.mkdir(mode=0o700)
            self._private_file(
                home,
                'FACTORY_ALICE_USERNAME="alice"\nFACTORY_PASSWORD=secret\n',
            )
            with self.assertRaisesRegex(ContractError, "surrounding quotes") as raised:
                factory_credential_environment({"WORKSHOP_HOME": str(home)})
            self.assertNotIn('"alice"', str(raised.exception))

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "unused"
            with self.assertRaisesRegex(ContractError, "literal surrounding quotes") as raised:
                factory_credential_environment(
                    {
                        "WORKSHOP_HOME": str(home),
                        "FACTORY_USERNAME": "'alice'",
                        "FACTORY_PASSWORD": "secret",
                    }
                )
            self.assertNotIn("'alice'", str(raised.exception))

    def test_validates_scoped_identity_and_shared_password_pairing(self):
        valid = (
            {"FACTORY_USERNAME": "Alice", "FACTORY_PASSWORD": "secret"},
            {"FACTORY_ALICE_USERNAME": "Alice", "FACTORY_PASSWORD": "secret"},
            {
                "FACTORY_ALICE_USERNAME": "alice",
                "FACTORY_LEO_SMITH_USERNAME": "LEO-SMITH",
                "FACTORY_PASSWORD": "secret",
            },
            {},
        )
        for values in valid:
            with self.subTest(values=tuple(values)):
                validate_factory_credential_configuration(values)

        invalid = (
            (
                {"FACTORY_ALICE_USERNAME": "bob", "FACTORY_PASSWORD": "secret"},
                "exactly match",
            ),
            (
                {"FACTORY_USERNAME": "not an inventor", "FACTORY_PASSWORD": "secret"},
                "canonical inventor_id",
            ),
            (
                {"FACTORY_ALICE__BOB_USERNAME": "alice--bob", "FACTORY_PASSWORD": "secret"},
                "canonical inventor_id",
            ),
            ({"FACTORY_USERNAME": "alice"}, "configured together"),
            ({"FACTORY_PASSWORD": "secret"}, "configured together"),
            ({"FACTORY_ALICE_USERNAME": "alice"}, "configured together"),
        )
        for values, message in invalid:
            with self.subTest(message=message), self.assertRaisesRegex(
                ContractError, message
            ):
                validate_factory_credential_configuration(values)


if __name__ == "__main__":
    unittest.main()
