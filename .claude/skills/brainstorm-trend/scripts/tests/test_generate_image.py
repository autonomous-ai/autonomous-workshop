from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_image import (  # noqa: E402
    MAX_REFERENCE_IMAGES,
    GeneratedImage,
    HttpResponse,
    OPENROUTER_API_KEY_NAME,
    OPENROUTER_IMAGE_MODEL_NAME,
    OpenRouterConfig,
    OpenRouterError,
    generate_image,
    load_openrouter_config,
    main,
    parse_env_file,
)


def _png_bytes(width: int, height: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color=(200, 100, 50)).save(buffer, format="PNG")
    return buffer.getvalue()


def _data_url(image_bytes: bytes, media_type: str = "image/png") -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return "data:%s;base64,%s" % (media_type, encoded)


def _chat_completions_response(image_bytes: bytes, *, media_type: str = "image/png", status: int = 200) -> HttpResponse:
    payload = {
        "choices": [
            {
                "message": {
                    "images": [
                        {"type": "image_url", "image_url": {"url": _data_url(image_bytes, media_type)}}
                    ]
                }
            }
        ]
    }
    return HttpResponse(status, json.dumps(payload).encode("utf-8"))


def _fake_transport(response: HttpResponse):
    calls = []

    def transport(url, headers, body):
        calls.append((url, dict(headers), body))
        return response

    transport.calls = calls
    return transport


CONFIG = OpenRouterConfig(api_key="sk-or-secret-value", model="fake/image-model")


def test_generate_image_writes_bounded_png(tmp_path):
    image_bytes = _png_bytes(64, 32)
    transport = _fake_transport(_chat_completions_response(image_bytes))
    output_path = tmp_path / "concept.png"

    result = generate_image(
        "a lone wizard, fully inside the frame",
        output_path,
        config=CONFIG,
        transport=transport,
    )

    assert isinstance(result, GeneratedImage)
    assert result.path == output_path
    assert result.model == "fake/image-model"
    assert result.media_type == "image/png"
    assert result.width == 64
    assert result.height == 32
    assert output_path.read_bytes() == image_bytes

    # exactly one call; the key travels only in the Authorization header
    assert len(transport.calls) == 1
    url, headers, body = transport.calls[0]
    assert headers["Authorization"] == "Bearer sk-or-secret-value"
    sent = json.loads(body.decode("utf-8"))
    assert sent["model"] == "fake/image-model"
    assert sent["messages"][0]["content"] == "a lone wizard, fully inside the frame"


def test_generate_image_renames_output_to_match_media_type(tmp_path):
    image_bytes = _png_bytes(10, 10)
    transport = _fake_transport(_chat_completions_response(image_bytes))
    output_path = tmp_path / "concept.jpg"

    result = generate_image("subject", output_path, config=CONFIG, transport=transport)

    assert result.path == tmp_path / "concept.png"
    assert result.path.exists()
    assert not output_path.exists()


def test_generate_image_shrinks_an_oversized_image_to_the_limit(tmp_path):
    image_bytes = _png_bytes(1024, 512)
    transport = _fake_transport(_chat_completions_response(image_bytes))

    result = generate_image("subject", tmp_path / "out.png", config=CONFIG, transport=transport)

    assert (result.width, result.height) == (800, 400)
    with Image.open(result.path) as written:
        assert written.format == "PNG"
        assert written.size == (800, 400)
    assert result.size == result.path.stat().st_size


def test_generate_image_rejects_http_error_without_leaking_key(tmp_path):
    transport = _fake_transport(HttpResponse(401, b'{"error": "invalid key"}'))

    with pytest.raises(OpenRouterError) as excinfo:
        generate_image("subject", tmp_path / "out.png", config=CONFIG, transport=transport)

    assert "sk-or-secret-value" not in str(excinfo.value)
    assert "401" in str(excinfo.value)


def test_generate_image_rejects_response_without_image(tmp_path):
    transport = _fake_transport(HttpResponse(200, json.dumps({"choices": [{"message": {}}]}).encode("utf-8")))

    with pytest.raises(OpenRouterError, match="no image"):
        generate_image("subject", tmp_path / "out.png", config=CONFIG, transport=transport)


def test_generate_image_rejects_non_data_url(tmp_path):
    payload = {
        "choices": [{"message": {"images": [{"image_url": {"url": "https://example.com/x.png"}}]}}]
    }
    transport = _fake_transport(HttpResponse(200, json.dumps(payload).encode("utf-8")))

    with pytest.raises(OpenRouterError, match="data URL"):
        generate_image("subject", tmp_path / "out.png", config=CONFIG, transport=transport)


def test_generate_image_rejects_animated_image(tmp_path):
    buffer = io.BytesIO()
    frame_one = Image.new("RGB", (10, 10), color=(200, 100, 50))
    frame_two = Image.new("RGB", (10, 10), color=(50, 100, 200))
    frame_one.save(buffer, format="WEBP", save_all=True, append_images=[frame_two])
    transport = _fake_transport(_chat_completions_response(buffer.getvalue(), media_type="image/webp"))

    with pytest.raises(OpenRouterError, match="animated"):
        generate_image("subject", tmp_path / "out.webp", config=CONFIG, transport=transport)


def test_generate_image_rejects_blank_prompt(tmp_path):
    with pytest.raises(OpenRouterError, match="prompt"):
        generate_image("   ", tmp_path / "out.png", config=CONFIG, transport=_fake_transport(HttpResponse(200, b"{}")))


def test_parse_env_file_reads_name_value_lines(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "# comment",
                "",
                "OPENROUTER_API_KEY=sk-or-abc123",
                "OPENROUTER_IMAGE_MODEL=vendor/model-name",
            ]
        )
    )

    values = parse_env_file(env_path)

    assert values == {
        OPENROUTER_API_KEY_NAME: "sk-or-abc123",
        OPENROUTER_IMAGE_MODEL_NAME: "vendor/model-name",
    }


def test_parse_env_file_rejects_malformed_line(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("not-a-valid-line")

    with pytest.raises(OpenRouterError, match="malformed"):
        parse_env_file(env_path)


def test_load_openrouter_config_reads_env_file(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "OPENROUTER_API_KEY=sk-or-abc123\nOPENROUTER_IMAGE_MODEL=vendor/model-name\n"
    )

    config = load_openrouter_config(env_path, environment={})

    assert config.api_key == "sk-or-abc123"
    assert config.model == "vendor/model-name"


def test_load_openrouter_config_prefers_process_environment(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "OPENROUTER_API_KEY=file-key\nOPENROUTER_IMAGE_MODEL=file-model\n"
    )

    config = load_openrouter_config(
        env_path,
        environment={
            OPENROUTER_API_KEY_NAME: "process-key",
            OPENROUTER_IMAGE_MODEL_NAME: "process-model",
        },
    )

    assert config.api_key == "process-key"
    assert config.model == "process-model"


def test_load_openrouter_config_requires_api_key(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("OPENROUTER_IMAGE_MODEL=vendor/model-name\n")

    with pytest.raises(OpenRouterError, match=OPENROUTER_API_KEY_NAME):
        load_openrouter_config(env_path, environment={})


def test_load_openrouter_config_requires_model(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("OPENROUTER_API_KEY=sk-or-abc123\n")

    with pytest.raises(OpenRouterError, match=OPENROUTER_IMAGE_MODEL_NAME):
        load_openrouter_config(env_path, environment={})


def test_load_openrouter_config_missing_file_falls_back_to_environment(tmp_path):
    config = load_openrouter_config(
        tmp_path / "does-not-exist.env",
        environment={
            OPENROUTER_API_KEY_NAME: "process-key",
            OPENROUTER_IMAGE_MODEL_NAME: "process-model",
        },
    )

    assert config.api_key == "process-key"
    assert config.model == "process-model"


def test_config_repr_never_reveals_the_key():
    config = OpenRouterConfig(api_key="super-secret-value", model="vendor/model")

    assert "super-secret-value" not in repr(config)
    assert "super-secret-value" not in str(config)
    assert "vendor/model" in repr(config)


def test_main_writes_the_image_and_prints_its_facts_without_the_key(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv(OPENROUTER_API_KEY_NAME, raising=False)
    monkeypatch.delenv(OPENROUTER_IMAGE_MODEL_NAME, raising=False)
    env = tmp_path / ".env"
    env.write_text("%s=sk-or-secret-value\n%s=fake/image-model\n" % (OPENROUTER_API_KEY_NAME, OPENROUTER_IMAGE_MODEL_NAME))
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("one toy whale, fully inside the frame")
    transport = _fake_transport(_chat_completions_response(_png_bytes(40, 40)))

    code = main(["--prompt-file", str(prompt), "--out", str(tmp_path / "concept.jpg"), "--env", str(env)], transport=transport)

    captured = capsys.readouterr()
    assert code == 0
    facts = json.loads(captured.out)
    assert facts["path"] == str(tmp_path / "concept.png")
    assert facts["model"] == "fake/image-model"
    assert (tmp_path / "concept.png").is_file()
    assert "sk-or-secret-value" not in captured.out + captured.err


def test_main_exits_2_when_the_key_is_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv(OPENROUTER_API_KEY_NAME, raising=False)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("one toy")

    code = main(["--prompt-file", str(prompt), "--out", str(tmp_path / "concept.png"), "--env", str(tmp_path / "none")])

    assert code == 2
    assert OPENROUTER_API_KEY_NAME in capsys.readouterr().err


def test_generate_image_sends_reference_images_after_the_prompt(tmp_path):
    concept = tmp_path / "concept.png"
    concept.write_bytes(_png_bytes(12, 12))
    style = tmp_path / "style.jpg"
    Image.new("RGB", (8, 8)).save(style, format="JPEG")
    transport = _fake_transport(_chat_completions_response(_png_bytes(20, 20)))

    generate_image("redraw the first in the style of the second", tmp_path / "out.png",
                   config=CONFIG, transport=transport, references=[concept, style])

    content = json.loads(transport.calls[0][2].decode("utf-8"))["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "redraw the first in the style of the second"}
    assert [part["type"] for part in content[1:]] == ["image_url", "image_url"]
    assert content[1]["image_url"]["url"] == _data_url(concept.read_bytes(), "image/png")
    assert content[2]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_generate_image_rejects_an_unreadable_reference(tmp_path):
    bad = tmp_path / "notes.png"
    bad.write_text("not an image")
    transport = _fake_transport(_chat_completions_response(_png_bytes(10, 10)))

    with pytest.raises(OpenRouterError, match="reference"):
        generate_image("x", tmp_path / "out.png", config=CONFIG, transport=transport, references=[bad])
    assert transport.calls == []


def test_generate_image_rejects_too_many_references(tmp_path):
    refs = []
    for index in range(MAX_REFERENCE_IMAGES + 1):
        path = tmp_path / ("r%d.png" % index)
        path.write_bytes(_png_bytes(4, 4))
        refs.append(path)
    transport = _fake_transport(_chat_completions_response(_png_bytes(10, 10)))

    with pytest.raises(OpenRouterError, match="at most"):
        generate_image("x", tmp_path / "out.png", config=CONFIG, transport=transport, references=refs)
    assert transport.calls == []


def test_main_passes_each_ref_flag_as_a_reference(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv(OPENROUTER_API_KEY_NAME, "sk-or-secret-value")
    monkeypatch.setenv(OPENROUTER_IMAGE_MODEL_NAME, "fake/image-model")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("restyle the concept")
    first, second = tmp_path / "a.png", tmp_path / "b.png"
    first.write_bytes(_png_bytes(6, 6))
    second.write_bytes(_png_bytes(7, 7))
    transport = _fake_transport(_chat_completions_response(_png_bytes(30, 30)))

    code = main(["--prompt-file", str(prompt), "--out", str(tmp_path / "concept.png"),
                 "--env", str(tmp_path / "none"), "--ref", str(first), "--ref", str(second)], transport=transport)

    assert code == 0
    content = json.loads(transport.calls[0][2].decode("utf-8"))["messages"][0]["content"]
    assert len(content) == 3
    assert "sk-or-secret-value" not in capsys.readouterr().out
