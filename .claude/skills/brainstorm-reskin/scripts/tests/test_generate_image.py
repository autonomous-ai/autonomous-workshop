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
    GeneratedImage,
    HttpResponse,
    OPENROUTER_API_KEY_NAME,
    OPENROUTER_IMAGE_MODEL_NAME,
    OpenRouterConfig,
    OpenRouterError,
    generate_image,
    load_openrouter_config,
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
    output_path = tmp_path / "ref-01-hero.png"

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
    output_path = tmp_path / "ref-01-hero.jpg"

    result = generate_image("subject", output_path, config=CONFIG, transport=transport)

    assert result.path == tmp_path / "ref-01-hero.png"
    assert result.path.exists()
    assert not output_path.exists()


def test_generate_image_rejects_oversized_image(tmp_path):
    image_bytes = _png_bytes(801, 800)
    transport = _fake_transport(_chat_completions_response(image_bytes))

    with pytest.raises(OpenRouterError, match="801x800"):
        generate_image("subject", tmp_path / "out.png", config=CONFIG, transport=transport)


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
