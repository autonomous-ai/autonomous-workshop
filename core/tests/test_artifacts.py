import json
import os
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from inventor_core.artifacts import (
    ArtifactManifest,
    build_artifact_manifest,
    build_publish_packet,
)
from inventor_core import artifacts as artifact_module
from inventor_core.errors import ArtifactError


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "product"
        self.root.mkdir()
        (self.root / "project.json").write_text('{"id":"p"}\n', encoding="utf-8")
        (self.root / "assembled.stl").write_bytes(b"solid x\nendsolid x\n")

    def test_manifest_is_content_addressed_and_excludes_secrets(self):
        first = build_artifact_manifest(
            self.root, created_at="2026-08-23T00:00:00+00:00"
        )
        (self.root / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
        (self.root / "credentials.json").write_text('{"token":"secret"}\n', encoding="utf-8")
        (self.root / "Credentials.JSON").write_text('{"token":"secret"}\n', encoding="utf-8")
        (self.root / "inventor-core.sqlite3").write_bytes(b"private state")
        (self.root / "inventor-core.sqlite3-wal").write_bytes(b"private state")
        second = build_artifact_manifest(
            self.root, created_at="2026-08-23T00:00:01+00:00"
        )
        self.assertEqual(first.artifact_sha256, second.artifact_sha256)
        self.assertNotIn(".env", [entry.path for entry in second.entries])
        self.assertNotIn("credentials.json", [entry.path for entry in second.entries])
        self.assertNotIn("Credentials.JSON", [entry.path for entry in second.entries])
        self.assertNotIn("inventor-core.sqlite3", [entry.path for entry in second.entries])
        self.assertNotIn("inventor-core.sqlite3-wal", [entry.path for entry in second.entries])

    def test_explicit_excludes_cover_directories_and_relative_files(self):
        generated = self.root / "generated"
        generated.mkdir()
        (generated / "cache.txt").write_text("cache\n", encoding="utf-8")
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "omit.txt").write_text("omit\n", encoding="utf-8")
        (nested / "keep.txt").write_text("keep\n", encoding="utf-8")
        manifest = build_artifact_manifest(
            self.root,
            extra_excludes=("generated", "nested/omit.txt"),
        )
        paths = [entry.path for entry in manifest.entries]
        self.assertNotIn("generated/cache.txt", paths)
        self.assertNotIn("nested/omit.txt", paths)
        self.assertIn("nested/keep.txt", paths)

    def test_explicit_excludes_reject_string_and_unsafe_paths(self):
        for excludes in ("generated", ("../outside",), ("unsafe\\path",)):
            with self.subTest(excludes=excludes), self.assertRaises(ArtifactError):
                build_artifact_manifest(self.root, extra_excludes=excludes)

    def test_artifact_manifest_schema_tracks_runtime_limits(self):
        schema_path = (
            Path(__file__).resolve().parents[1]
            / "schemas"
            / "artifact-manifest.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        entry = schema["properties"]["entries"]
        self.assertEqual(entry["maxItems"], 4096)
        self.assertEqual(
            entry["items"]["properties"]["bytes"]["maximum"],
            95 * 1024 * 1024,
        )
        self.assertEqual(
            schema["properties"]["total_bytes"]["maximum"],
            512 * 1024 * 1024,
        )

    def test_publish_packet_is_reproducible(self):
        one = Path(self.temp.name) / "one.zip"
        two = Path(self.temp.name) / "two.zip"
        result_one = build_publish_packet(self.root, one)
        os.utime(self.root / "project.json", None)
        result_two = build_publish_packet(self.root, two)
        self.assertEqual(result_one["packet_sha256"], result_two["packet_sha256"])
        self.assertEqual(stat.S_IMODE(one.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(two.stat().st_mode), 0o600)
        with zipfile.ZipFile(one) as archive:
            self.assertIn("_inventor-artifact.json", archive.namelist())
            self.assertTrue(
                all(item.compress_type == zipfile.ZIP_STORED for item in archive.infolist())
            )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_publish_packet_temp_path_replacement_cannot_clobber_target(self):
        destination = Path(self.temp.name) / "safe.zip"
        victim = Path(self.temp.name) / "victim.txt"
        victim.write_text("do not overwrite\n", encoding="utf-8")
        created = {}
        real_mkstemp = tempfile.mkstemp
        real_fdopen = os.fdopen

        def remember_mkstemp(*args, **kwargs):
            descriptor, path = real_mkstemp(*args, **kwargs)
            created["path"] = path
            return descriptor, path

        def replace_before_write(descriptor, *args, **kwargs):
            temporary = created["path"]
            os.unlink(temporary)
            os.symlink(victim, temporary)
            return real_fdopen(descriptor, *args, **kwargs)

        with mock.patch(
            "inventor_core.artifacts.tempfile.mkstemp",
            side_effect=remember_mkstemp,
        ), mock.patch(
            "inventor_core.artifacts.os.fdopen", side_effect=replace_before_write
        ), mock.patch(
            "inventor_core.artifacts._ANCHORED_STAGING", False
        ):
            with self.assertRaises(ArtifactError):
                build_publish_packet(self.root, destination)

        self.assertEqual(victim.read_text(encoding="utf-8"), "do not overwrite\n")
        self.assertFalse(destination.exists())

    @unittest.skipUnless(
        artifact_module._ANCHORED_STAGING,
        "descriptor-anchored staging unavailable",
    )
    def test_publish_packet_destination_parent_replacement_fails_closed(self):
        output = Path(self.temp.name) / "output"
        output.mkdir()
        replacement = Path(self.temp.name) / "replacement-output"
        replacement.mkdir()
        destination = output / "game.zip"
        resolved_output = output.resolve()
        real_open = os.open
        replaced = [False]

        def replace_parent(path, flags, *args, **kwargs):
            if path == str(resolved_output) and not replaced[0]:
                replaced[0] = True
                output.rename(Path(self.temp.name) / "output-original")
                replacement.rename(output)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch(
            "inventor_core.artifacts.os.open", side_effect=replace_parent
        ):
            with self.assertRaises(ArtifactError):
                build_publish_packet(self.root, destination)
        self.assertTrue(replaced[0])
        self.assertFalse(destination.exists())

    def test_reserved_manifest_name_cannot_create_duplicate_zip_member(self):
        (self.root / "_inventor-artifact.json").write_text("untrusted\n", encoding="utf-8")
        packet = Path(self.temp.name) / "reserved.zip"
        build_publish_packet(self.root, packet)
        with zipfile.ZipFile(packet) as archive:
            self.assertEqual(archive.namelist().count("_inventor-artifact.json"), 1)

    def test_packet_refuses_destination_inside_source(self):
        with self.assertRaises(ArtifactError):
            build_publish_packet(self.root, self.root / "recursive.zip")

    def test_packet_refuses_changed_bytes(self):
        destination = Path(self.temp.name) / "changed.zip"
        with mock.patch(
            "inventor_core.artifacts._read_open_file",
            side_effect=lambda root, relative: (
                b"changed",
                (root / relative).stat(),
            ),
        ):
            with self.assertRaises(ArtifactError):
                build_publish_packet(self.root, destination)

    def test_packet_refuses_changed_executable_mode(self):
        destination = Path(self.temp.name) / "changed-mode.zip"
        original_read = artifact_module._read_open_file
        changed = [False]

        def change_mode(root, relative):
            if not changed[0]:
                changed[0] = True
                os.chmod(root / relative, 0o755)
            return original_read(root, relative)

        with mock.patch(
            "inventor_core.artifacts._read_open_file", side_effect=change_mode
        ):
            with self.assertRaises(ArtifactError):
                build_publish_packet(self.root, destination)

    def test_manifest_enforces_expanded_size_limit(self):
        with self.assertRaises(ArtifactError):
            build_artifact_manifest(self.root, maximum_total_bytes=1)

    def test_manifest_revalidates_a_mutated_entry_sequence_before_serializing(self):
        original = build_artifact_manifest(self.root)
        entries = list(original.entries)
        mutable = ArtifactManifest(
            original.schema_version,
            original.artifact_sha256,
            entries,
            original.total_bytes,
            original.created_at,
        )
        entries.pop()
        with self.assertRaises(ArtifactError):
            mutable.to_dict()

    def test_packet_rejects_secret_content_under_an_innocent_name(self):
        (self.root / "notes.txt").write_text(
            "bot=" + "1234567:" + ("A" * 32), encoding="utf-8"
        )
        with self.assertRaises(ArtifactError):
            build_publish_packet(self.root, Path(self.temp.name) / "secret.zip")

    @unittest.skipIf(os.name == "nt", "backslash is a separator on Windows")
    def test_packet_rejects_backslash_member_names(self):
        (self.root / "..\\escape.txt").write_text("unsafe\n", encoding="utf-8")
        with self.assertRaises(ArtifactError):
                build_publish_packet(self.root, Path(self.temp.name) / "unsafe.zip")

    def test_packet_rejects_control_characters_in_member_names(self):
        (self.root / "unsafe\nname.txt").write_text("unsafe\n", encoding="utf-8")
        with self.assertRaises(ArtifactError):
            build_publish_packet(self.root, Path(self.temp.name) / "unsafe-control.zip")

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_symlink_fails_closed(self):
        os.symlink(self.root / "project.json", self.root / "alias.json")
        with self.assertRaises(ArtifactError):
            build_artifact_manifest(self.root)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs unavailable")
    def test_no_follow_open_rejects_fifo_without_blocking(self):
        fifo = self.root / "packet-fifo"
        os.mkfifo(fifo)
        with self.assertRaises(ArtifactError):
            artifact_module._open_regular_no_follow(
                self.root, Path("packet-fifo")
            )

    @unittest.skipUnless(
        hasattr(os, "O_DIRECTORY")
        and os.open in getattr(os, "supports_dir_fd", set()),
        "descriptor-relative opens unavailable",
    )
    def test_no_follow_open_rejects_regular_file_replacement(self):
        replacement = self.root / "replacement.json"
        replacement.write_text('{"id":"replacement"}\n', encoding="utf-8")
        target = self.root / "project.json"
        real_open = os.open
        replaced = [False]

        def replace_file(path, flags, *args, **kwargs):
            if (
                path == "project.json"
                and kwargs.get("dir_fd") is not None
                and not replaced[0]
            ):
                replaced[0] = True
                os.replace(replacement, target)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch(
            "inventor_core.artifacts.os.open", side_effect=replace_file
        ):
            with self.assertRaises(ArtifactError):
                artifact_module._open_regular_no_follow(
                    self.root, Path("project.json")
                )
        self.assertTrue(replaced[0])


if __name__ == "__main__":
    unittest.main()
