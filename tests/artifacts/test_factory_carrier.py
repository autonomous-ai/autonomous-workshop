"""Mixed compression retains canonical expanded identity without relaxing Packs."""

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

from workshop.artifacts import build_artifact_manifest, build_pack
from workshop.artifacts.core import _canonical
from workshop.artifacts.pack import validate_artifact_payload
from workshop.errors import ContractError
from workshop.artifacts import factory_carrier as codec


MANIFEST = "_inventor-artifact.json"


def inventory(members):
    entries = [{"path": name, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                "executable": False} for name, body in sorted(members.items())]
    return {"schema_version": 1, "created_at": "content-addressed", "entries": entries,
            "total_bytes": sum(row["bytes"] for row in entries),
            "artifact_sha256": hashlib.sha256(_canonical(entries)).hexdigest()}


def archive_bytes(members=None, *, manifest=None, order=None, metadata=None,
                  compression=zipfile.ZIP_DEFLATED, level=9, manifest_bytes=None):
    members = {"public/scene.step": b"STEP data\n" * 2000} if members is None else members
    manifest = inventory(members) if manifest is None else manifest
    all_members = dict(members)
    all_members[MANIFEST] = (_canonical(manifest) + b"\n" if manifest_bytes is None else manifest_bytes)
    order = [*sorted(members), MANIFEST] if order is None else order
    buffer = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(buffer, "w", compression=compression, compresslevel=level) as archive:
            for name in order:
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o644 << 16
                info.compress_type = compression
                if metadata:
                    metadata(info)
                archive.writestr(info, all_members[name], compresslevel=level)
    return buffer.getvalue()


def structure(content):
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        infos = archive.infolist()
    central = struct.unpack_from("<I", content, len(content) - 6)[0]
    positions = []
    cursor = central
    for info in infos:
        positions.append(cursor)
        cursor += 46 + len(info.filename.encode("utf-8")) + len(info.extra) + len(info.comment)
    return infos, central, positions


def change_declared_sizes(content, sizes):
    data = bytearray(content)
    infos, _, positions = structure(content)
    for index, size in sizes.items():
        struct.pack_into("<I", data, infos[index].header_offset + 22, size)
        struct.pack_into("<I", data, positions[index] + 24, size)
    return bytes(data)


def change_first_compressed_stream(content, change):
    """Keep all ZIP headers/offsets consistent while changing raw member framing."""
    infos, central, positions = structure(content)
    first = infos[0]
    start = first.header_offset + 30 + len(first.filename.encode("utf-8"))
    end = start + first.compress_size
    replacement = change(content[start:end])
    delta = len(replacement) - first.compress_size
    data = bytearray(content[:start] + replacement + content[end:])
    struct.pack_into("<I", data, first.header_offset + 18, len(replacement))
    struct.pack_into("<I", data, positions[0] + delta + 20, len(replacement))
    for info, position in zip(infos[1:], positions[1:]):
        struct.pack_into("<I", data, position + delta + 42, info.header_offset + delta)
    struct.pack_into("<I", data, len(data) - 6, central + delta)
    return bytes(data)


class MixedFactoryCarrierTests(unittest.TestCase):
    def test_build_roundtrip_exact_members_inventory_permissions_and_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "public-projection"
            (root / "public").mkdir(parents=True)
            members = {"public/scene.step": b"ISO-10303-21;\n" * 2000,
                       "assembled.step": b"ISO-10303-21;\n" * 2000,
                       "public/hero.png": b"PNG placeholder", "public/caf\u00e9.txt": b"customer copy",
                       "public/empty.txt": b""}
            for name, body in members.items():
                (root / name).write_bytes(body)
            (root / "public/caf\u00e9.txt").chmod(0o755)
            before = build_artifact_manifest(root, created_at="content-addressed")
            path = Path(temporary) / "private" / "carrier.zip"
            result = codec.build_mixed_carrier(root, path)
            content, pack_sha, artifact_sha = codec.load_mixed_carrier(path)
            self.assertEqual(result["pack_sha256"], pack_sha)
            self.assertEqual(result["artifact_sha256"], artifact_sha)
            self.assertEqual(artifact_sha, before.artifact_sha256)
            self.assertEqual(result["bytes"], len(content))
            self.assertEqual(result["entries"], len(members) + 1)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                self.assertEqual(archive.namelist(), [*sorted(members), MANIFEST])
                for name, body in members.items():
                    self.assertEqual(archive.read(name), body)
                self.assertEqual(archive.read(MANIFEST), _canonical(before.to_dict()) + b"\n")
                self.assertTrue(all(i.compress_type == zipfile.ZIP_DEFLATED for i in archive.infolist()))
            other = Path(temporary) / "other.zip"
            codec.build_mixed_carrier(root, other)
            self.assertEqual(path.read_bytes(), other.read_bytes())  # Same runtime only.

    def test_expanded_content_over_pack_limit_compresses_without_relaxing_classic_pack(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "projection"
            (root / "public").mkdir(parents=True)
            block = b"complete scene data\n" * 65536
            for name in ("assembled.step", "public/scene.step"):
                with (root / name).open("wb") as stream:
                    for _ in range(23):
                        stream.write(block)
            self.assertGreater(sum(path.stat().st_size for path in root.rglob("*.step")), codec.MAX_PACK_BYTES)
            with self.assertRaises(ContractError):
                build_pack(root, Path(temporary) / "classic.zip")
            result = codec.build_mixed_carrier(root, Path(temporary) / "mixed.zip")
            self.assertLess(result["bytes"], codec.MAX_PACK_BYTES)
            content = (Path(temporary) / "mixed.zip").read_bytes()
            with self.assertRaises(ContractError):
                validate_artifact_payload(content)
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                for name in ("assembled.step", "public/scene.step"):
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(),
                                     hashlib.sha256((root / name).read_bytes()).hexdigest())

    def test_validation_accepts_exact_saved_deflate_stream_without_recompression(self):
        fast, dense = archive_bytes(level=1), archive_bytes(level=9)
        self.assertNotEqual(fast, dense)
        with mock.patch.object(codec.zlib, "compressobj", side_effect=AssertionError("recompressed")):
            first, second = codec.validate_mixed_carrier(fast), codec.validate_mixed_carrier(dense)
        self.assertEqual(first[2], second[2])
        self.assertNotEqual(first[1], second[1])
        self.assertIs(first[0], fast)

    def test_rejects_declared_bombs_and_all_existing_size_count_limits_before_inflate(self):
        content = archive_bytes({f"public/{index}.step": b"small" for index in range(6)})
        cases = [change_declared_sizes(content, {0: codec.MAX_FILE_BYTES + 1}),
                 change_declared_sizes(content, {index: codec.MAX_FILE_BYTES for index in range(6)})]
        for altered in cases:
            with self.subTest(case=len(altered)), mock.patch.object(codec, "_member_bytes") as inflate:
                with self.assertRaises(ContractError):
                    codec.validate_mixed_carrier(altered)
                inflate.assert_not_called()
        for limit, value in (("MAX_ENTRIES", 2), ("MAX_PACK_BYTES", len(content) - 1)):
            with self.subTest(limit=limit), mock.patch.object(codec, limit, value), \
                    mock.patch.object(codec, "_member_bytes") as inflate:
                with self.assertRaises(ContractError):
                    codec.validate_mixed_carrier(content)
                inflate.assert_not_called()
        # Do not allocate ZipFile's index for forged counts or hidden records.
        for declared in (2, codec.MAX_ENTRIES + 2):
            changed = bytearray(content)
            struct.pack_into("<HH", changed, len(changed) - 14, declared, declared)
            with mock.patch.object(codec.zipfile, "ZipFile", side_effect=AssertionError("indexed early")):
                with self.assertRaises(ContractError):
                    codec.validate_mixed_carrier(bytes(changed))
        # A dishonest small header cannot make decompression allocate the full bomb.
        members = {"public/scene.step": b"STEP data\n" * 2000}
        dishonest = inventory(members)
        dishonest["entries"][0]["bytes"] = 1
        dishonest["total_bytes"] = 1
        dishonest["artifact_sha256"] = hashlib.sha256(_canonical(dishonest["entries"])).hexdigest()
        with self.assertRaisesRegex(ContractError, "expands beyond"):
            codec.validate_mixed_carrier(change_declared_sizes(
                archive_bytes(members, manifest=dishonest), {0: 1}))

    def test_rejects_noncanonical_metadata_unsafe_paths_duplicates_and_conflicts(self):
        mutations = [lambda i: setattr(i, "date_time", (2026, 1, 1, 0, 0, 0)),
                     lambda i: setattr(i, "create_system", 0),
                     lambda i: setattr(i, "external_attr", 0o120777 << 16),
                     lambda i: setattr(i, "extra", b"\x01\x00\x00\x00"),
                     lambda i: setattr(i, "comment", b"comment"),
                     lambda i: setattr(i, "internal_attr", 1)]
        for mutate in mutations:
            with self.subTest(mutate=mutate), self.assertRaises(ContractError):
                codec.validate_mixed_carrier(archive_bytes(metadata=mutate))
        for name in ("../scene.step", "/scene.step", "a/../b", "a//b", "a\\b", "dir/"):
            with self.subTest(path=name), self.assertRaises(ContractError):
                codec.validate_mixed_carrier(archive_bytes({name: b"x"}))
        for members, order in (({"a": b"x"}, ["a", "a", MANIFEST]),
                               ({"a": b"x"}, ["a", MANIFEST, MANIFEST]),
                               ({"a": b"x", "a/b": b"y"}, None)):
            with self.subTest(order=order), self.assertRaises(ContractError):
                codec.validate_mixed_carrier(archive_bytes(members, order=order))
        with self.assertRaises(ContractError):
            codec.validate_mixed_carrier(archive_bytes(compression=zipfile.ZIP_STORED))

    def test_rejects_manifest_changes_unbound_bytes_and_permission_mismatches(self):
        members = {"a.txt": b"a", "b.txt": b"b"}
        good = inventory(members)
        altered = []
        for field, value in (("artifact_sha256", "0" * 64), ("total_bytes", 99),
                             ("created_at", "2026-09-11T00:00:00Z"), ("schema_version", True)):
            document = copy.deepcopy(good); document[field] = value; altered.append(document)
        document = copy.deepcopy(good); document["entries"][0]["sha256"] = "1" * 64; altered.append(document)
        document = copy.deepcopy(good); document["entries"].reverse(); altered.append(document)
        document = copy.deepcopy(good); document["extra"] = 1; altered.append(document)
        for document in altered:
            with self.subTest(document=document), self.assertRaises(ContractError):
                codec.validate_mixed_carrier(archive_bytes(members, manifest=document))
        for manifest_bytes in (json.dumps(good, indent=2).encode(),
                               (_canonical(good)[:-1] + b',"schema_version":1}\n')):
            with self.subTest(raw=manifest_bytes[:20]), self.assertRaises(ContractError):
                codec.validate_mixed_carrier(archive_bytes(members, manifest_bytes=manifest_bytes))
        for order in (["b.txt", "a.txt", MANIFEST], [MANIFEST, "a.txt", "b.txt"]):
            with self.subTest(order=order), self.assertRaises(ContractError):
                codec.validate_mixed_carrier(archive_bytes(members, order=order))
        with self.assertRaises(ContractError):
            codec.validate_mixed_carrier(archive_bytes({**members, "extra.txt": b"unbound"}, manifest=good))
        with self.assertRaises(ContractError):
            codec.validate_mixed_carrier(archive_bytes(members, metadata=lambda i: setattr(i, "external_attr", 0o755 << 16)))

    def test_rejects_prefix_trailing_gaps_headers_crc_and_hidden_deflate_bytes(self):
        content = archive_bytes()
        invalid = [b"prefix" + content, content + b"suffix", content + content,
                   change_first_compressed_stream(content, lambda body: body + b"hidden"),
                   change_first_compressed_stream(content, lambda body: body[:-1])]
        infos, central, positions = structure(content)
        gap = bytearray(content[:central] + b"X" + content[central:])
        struct.pack_into("<I", gap, len(gap) - 6, central + 1); invalid.append(bytes(gap))
        for offset in (14, 30, 6):  # Local CRC, name, encryption flag.
            changed = bytearray(content); changed[offset] ^= 1; invalid.append(bytes(changed))
        crc = bytearray(content)
        struct.pack_into("<I", crc, 14, infos[0].CRC ^ 1)
        struct.pack_into("<I", crc, positions[0] + 16, infos[0].CRC ^ 1)
        invalid.append(bytes(crc))
        for index, altered in enumerate(invalid):
            with self.subTest(index=index), self.assertRaises(ContractError):
                codec.validate_mixed_carrier(altered)

    def test_existing_secret_path_and_content_scanner_still_applies(self):
        for members in ({".env": b"private"}, {"public/key.txt": b"-----BEGIN PRIVATE KEY-----"},
                        {"public/a.txt": b"mongodb://user:password@example.invalid"}):
            with self.subTest(names=list(members)), self.assertRaises(ContractError):
                codec.validate_mixed_carrier(archive_bytes(members))

    def test_source_mutation_symlinks_and_failed_compression_do_not_install_carrier(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary); root = base / "source"; root.mkdir()
            source = root / "scene.step"; source.write_bytes(b"original")
            destination = base / "carrier.zip"
            original = codec.build_artifact_manifest
            def mutate(*args, **kwargs):
                result = original(*args, **kwargs)
                source.write_bytes(b"modified")
                return result
            with mock.patch.object(codec, "build_artifact_manifest", side_effect=mutate):
                with self.assertRaises(ContractError):
                    codec.build_mixed_carrier(root, destination)
            self.assertFalse(destination.exists())
            source.unlink(); source.symlink_to(base / "outside.step")
            (base / "outside.step").write_bytes(b"outside")
            with self.assertRaises(ContractError):
                codec.build_mixed_carrier(root, destination)
            source.unlink(); source.write_bytes(os.urandom(8192))
            destination.write_bytes(b"keep prior file")
            with mock.patch.object(codec, "MAX_PACK_BYTES", 512):
                with self.assertRaises(ContractError):
                    codec.build_mixed_carrier(root, destination)
            self.assertEqual(destination.read_bytes(), b"keep prior file")
            self.assertFalse(list(base.glob(".*.stage-*")))
            link = base / "link.zip"; link.symlink_to(destination)
            with self.assertRaises(ContractError):
                codec.load_mixed_carrier(link)
            with self.assertRaises(ContractError):
                codec.build_mixed_carrier(root, root / "inside.zip")


if __name__ == "__main__":
    unittest.main()
