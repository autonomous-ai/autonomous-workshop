import io
import zipfile

import pytest

from workshop.artifacts.core import build_pack
from workshop.artifacts.pack import load_artifact_payload, validate_artifact_payload
from workshop.errors import ArtifactError, ContractError


def test_auto_preserves_small_stored_pack_bytes(tmp_path):
    root = tmp_path / "product"
    root.mkdir()
    (root / "part.step").write_text("STEP fixture\n")
    first, second = tmp_path / "stored.zip", tmp_path / "auto.zip"
    build_pack(root, first)
    build_pack(root, second, compression="auto")
    assert first.read_bytes() == second.read_bytes()


def test_large_compressible_pack_preserves_every_byte_and_logical_identity(tmp_path):
    root = tmp_path / "product"
    root.mkdir()
    content = b"STEP geometry fixture\n" * 100000
    (root / "part.step").write_bytes(content)
    stored, compressed, repeated = [tmp_path / name for name in ("stored.zip", "compressed.zip", "repeated.zip")]
    original = build_pack(root, stored)
    packed = build_pack(root, compressed, maximum_bytes=16384, compression="auto")
    build_pack(root, repeated, maximum_bytes=16384, compression="auto")
    assert packed["bytes"] < 16384 < original["bytes"]
    assert compressed.read_bytes() == repeated.read_bytes()
    assert load_artifact_payload(compressed)[2] == load_artifact_payload(stored)[2]
    with zipfile.ZipFile(compressed) as archive:
        assert archive.read("part.step") == content
        assert all(info.compress_type == zipfile.ZIP_DEFLATED for info in archive.infolist())


def test_compressed_pack_still_enforces_actual_upload_size_and_keeps_destination(tmp_path):
    root = tmp_path / "product"
    root.mkdir()
    (root / "part.step").write_bytes(b"geometry\n" * 1000)
    target = tmp_path / "existing.zip"
    target.write_bytes(b"preserved")
    with pytest.raises(ArtifactError, match="configured limit"):
        build_pack(root, target, maximum_bytes=100, compression="auto")
    assert target.read_bytes() == b"preserved"


@pytest.mark.parametrize("change", ["content", "mixed", "expanded-limit"])
def test_compression_does_not_relax_manifest_or_archive_guards(tmp_path, monkeypatch, change):
    root = tmp_path / "product"
    root.mkdir()
    (root / "part.step").write_bytes(b"geometry\n" * 10000)
    target = tmp_path / "compressed.zip"
    build_pack(root, target, maximum_bytes=4096, compression="auto")
    content = target.read_bytes()
    if change == "expanded-limit":
        monkeypatch.setattr("workshop.artifacts.pack.MAX_EXPANDED_BYTES", 1024)
        with pytest.raises(ContractError, match="expanded-size limit"):
            validate_artifact_payload(content)
        return
    buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(content)) as source, zipfile.ZipFile(buffer, "w") as archive:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename == "part.step":
                if change == "content":
                    data = data.replace(b"geometry", b"tampered", 1)
                else:
                    info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, data, compress_type=info.compress_type, compresslevel=9)
    with pytest.raises(ContractError, match="manifest|canonical form"):
        validate_artifact_payload(buffer.getvalue())
