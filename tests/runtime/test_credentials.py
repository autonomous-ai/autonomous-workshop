import os
import stat
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.runtime.credentials import (
    factory_credential_environment,
    factory_credential_file,
    factory_service_credential_environment,
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
            overridden = factory_credential_environment(
                {
                    "WORKSHOP_HOME": str(home),
                    "FACTORY_USERNAME": "workshop.publisher",
                    "FACTORY_PASSWORD": "environment-secret",
                }
            )
            self.assertEqual(
                overridden,
                {
                    "FACTORY_USERNAME": "workshop.publisher",
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

    def test_normalizes_one_service_account_and_rejects_identity_ambiguity(self):
        valid = (
            {
                "FACTORY_USERNAME": "workshop.publisher",
                "FACTORY_PASSWORD": "secret",
            },
            {"FACTORY_ALICE_USERNAME": "Alice", "FACTORY_PASSWORD": "secret"},
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
                {
                    "FACTORY_USERNAME": "workshop.publisher",
                    "FACTORY_ALICE_USERNAME": "alice",
                    "FACTORY_PASSWORD": "secret",
                },
                "only one Workshop service account",
            ),
            (
                {"FACTORY_ALICE__BOB_USERNAME": "alice--bob", "FACTORY_PASSWORD": "secret"},
                "canonical inventor_id",
            ),
            (
                {
                    "FACTORY_ALICE_USERNAME": "alice",
                    "FACTORY_LEO_SMITH_USERNAME": "LEO-SMITH",
                    "FACTORY_PASSWORD": "secret",
                },
                "only one Workshop service account",
            ),
            ({"FACTORY_USERNAME": "alice"}, "configured together"),
            ({"FACTORY_PASSWORD": "secret"}, "configured together"),
            ({"FACTORY_ALICE_USERNAME": "alice"}, "configured together"),
            ({"FACTORY_INVENTOR_ID": "Pico Press"}, "inventor id is malformed"),
            ({"FACTORY_INVENTOR_ID": "pico-press"}, "requires FACTORY_USERNAME"),
        )
        for values, message in invalid:
            with self.subTest(message=message), self.assertRaisesRegex(
                ContractError, message
            ):
                validate_factory_credential_configuration(values)

        self.assertEqual(
            factory_service_credential_environment(
                {
                    "FACTORY_USERNAME": "workshop.publisher",
                    "FACTORY_PASSWORD": "secret",
                }
            ),
            {
                "FACTORY_USERNAME": "workshop.publisher",
                "FACTORY_PASSWORD": "secret",
            },
        )
        self.assertEqual(
            factory_service_credential_environment(
                {
                    "FACTORY_ALICE_USERNAME": "Alice",
                    "FACTORY_PASSWORD": "secret",
                }
            ),
            {"FACTORY_USERNAME": "Alice", "FACTORY_PASSWORD": "secret"},
        )


if __name__ == "__main__":
    unittest.main()


class InventorAccountTest(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        self.home = Path(self._temporary.name).resolve() / "home"
        self.environment = {"WORKSHOP_HOME": str(self.home)}

    def test_each_inventor_publishes_as_its_own_stored_account(self):
        from workshop.runtime.credentials import (
            factory_credential_environment,
            inventor_credential_file,
            store_factory_credentials,
        )

        shared = store_factory_credentials("house", "p1", environment=self.environment)
        scoped = store_factory_credentials(
            "pico-press", "p2", inventor_id="pico-press", environment=self.environment
        )
        self.assertEqual(scoped, inventor_credential_file("pico-press", self.environment))
        self.assertEqual(stat.S_IMODE(scoped.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(scoped.parent.stat().st_mode), 0o700)
        self.assertEqual(
            dict(factory_credential_environment(self.environment, inventor_id="pico-press")),
            {
                "FACTORY_USERNAME": "pico-press",
                "FACTORY_PASSWORD": "p2",
                "FACTORY_INVENTOR_ID": "pico-press",
            },
        )
        self.assertEqual(
            factory_service_credential_environment(
                factory_credential_environment(
                    self.environment, inventor_id="pico-press"
                )
            ),
            {"FACTORY_USERNAME": "pico-press", "FACTORY_PASSWORD": "p2"},
        )
        self.assertIn(
            "FACTORY_INVENTOR_ID=pico-press\n",
            scoped.read_text(encoding="utf-8"),
        )
        # An Inventor without its own account still publishes through the host pair.
        self.assertEqual(
            dict(factory_credential_environment(self.environment, inventor_id="mira-fold")),
            {"FACTORY_USERNAME": "house", "FACTORY_PASSWORD": "p1"},
        )
        self.assertEqual(
            dict(factory_credential_environment(self.environment)),
            {"FACTORY_USERNAME": "house", "FACTORY_PASSWORD": "p1"},
        )
        self.assertTrue(shared.is_file())

    def test_scoped_file_rejects_a_missing_or_mismatched_inventor_binding(self):
        for binding in (None, "mira-fold"):
            with self.subTest(binding=binding):
                directory = self.home / "credentials" / "inventors"
                directory.mkdir(mode=0o700, parents=True, exist_ok=True)
                os.chmod(directory, 0o700)
                path = directory / "pico-press.env"
                source = "FACTORY_USERNAME=khoa\nFACTORY_PASSWORD=agent-secret\n"
                if binding is not None:
                    source += "FACTORY_INVENTOR_ID=%s\n" % binding
                path.write_text(source, encoding="utf-8")
                os.chmod(path, 0o600)

                with self.assertRaisesRegex(
                    ContractError, "not bound to Inventor pico-press"
                ):
                    factory_credential_environment(
                        self.environment, inventor_id="pico-press"
                    )

    def test_storing_replaces_atomically_and_rejects_bad_input(self):
        from workshop.errors import ContractError
        from workshop.runtime.credentials import (
            factory_credential_environment,
            store_factory_credentials,
        )

        path = store_factory_credentials(
            "pico-press", "first", inventor_id="pico-press", environment=self.environment
        )
        store_factory_credentials(
            "pico-press", "second", inventor_id="pico-press", environment=self.environment
        )
        self.assertEqual(
            factory_credential_environment(self.environment, inventor_id="pico-press")[
                "FACTORY_PASSWORD"
            ],
            "second",
        )
        self.assertFalse(path.with_name(path.name + ".tmp").exists())
        for username, password in ((" spaced ", "ok"), ("ok", ""), ("ok", "with space")):
            with self.subTest(username=username), self.assertRaises(ContractError):
                store_factory_credentials(
                    username, password, inventor_id="pico-press", environment=self.environment
                )
        for bad_id in ("Pico Press", "", "pico_press"):
            with self.subTest(bad_id=bad_id), self.assertRaises(ContractError):
                store_factory_credentials(
                    "a", "b", inventor_id=bad_id, environment=self.environment
                )
