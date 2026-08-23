"""Workshop naming, migration, and root-Taste invariants for Eve."""

from pathlib import Path

import pytest

from inventor_workshop import Taste, load_taste
from inventor_workshop.errors import ManifestError

from eve import config, driver, promptlib


SHOP_ENV = (
    "EVE_SHOP_API",
    "EVE_SHOP_TOKEN",
    "EVE_SHOP_OWNER_ID",
    "EVE_PORTAL_API",
    "EVE_PORTAL_TOKEN",
    "EVE_PORTAL_OWNER_ID",
    "EVE_STORE_BASE_URL",
    "EVE_STORE_BEARER",
    "EVE_STORE_OWNER_ID",
    "PANDA_OWNER_ID",
)


def _isolated_config(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    for name in SHOP_ENV:
        monkeypatch.delenv(name, raising=False)
    return config.Config.load


def test_new_shop_environment_is_canonical(monkeypatch, tmp_path):
    load = _isolated_config(monkeypatch, tmp_path)
    monkeypatch.setenv("EVE_SHOP_API", "https://shop.example")
    monkeypatch.setenv("EVE_SHOP_TOKEN", "new-token")
    monkeypatch.setenv("EVE_SHOP_OWNER_ID", "eve-owner")

    cfg = load()

    assert cfg.shop_api == "https://shop.example"
    assert cfg.shop_token == "new-token"
    assert cfg.shop_owner_id == "eve-owner"
    assert cfg.shop_configured is True


def test_legacy_environment_remains_a_guarded_fallback(monkeypatch, tmp_path):
    load = _isolated_config(monkeypatch, tmp_path)
    monkeypatch.setenv("EVE_STORE_BASE_URL", "https://legacy.example")
    monkeypatch.setenv("EVE_STORE_BEARER", "legacy-token")
    monkeypatch.setenv("PANDA_OWNER_ID", "legacy-owner")

    cfg = load()

    assert cfg.shop_api == "https://legacy.example"
    assert cfg.shop_token == "legacy-token"
    assert cfg.shop_owner_id == "legacy-owner"
    assert cfg.shop_configured is True


def test_conflicting_new_and_legacy_environment_fails_closed(monkeypatch, tmp_path):
    load = _isolated_config(monkeypatch, tmp_path)
    monkeypatch.setenv("EVE_SHOP_TOKEN", "current")
    monkeypatch.setenv("EVE_STORE_BEARER", "former")

    with pytest.raises(ValueError, match="EVE_SHOP_TOKEN conflicts"):
        load()


def test_portal_compatibility_properties_delegate_to_shop_fields(tmp_path):
    cfg = config.Config(root=tmp_path)
    cfg.portal_api = "https://old-name.example"
    cfg.portal_token = "old-token"
    cfg.portal_owner_id = "old-owner"
    cfg.portal_configured = True

    assert cfg.shop_api == "https://old-name.example"
    assert cfg.shop_token == "old-token"
    assert cfg.shop_owner_id == "old-owner"
    assert cfg.shop_configured is True


def test_prompt_taste_binding_is_exactly_the_root_taste(tmp_path):
    taste = tmp_path / "TASTE.md"
    taste.write_text("# Test Taste\n\nMake honest mechanisms.\n", encoding="utf-8")
    cfg = config.Config(root=tmp_path, taste_path=taste)
    taste_binding = load_taste(tmp_path)

    block = promptlib.taste_block(cfg)

    assert isinstance(taste_binding, Taste)
    assert "TASTE_SHA256=%s" % taste_binding.sha256 in block
    assert taste_binding.content in block


def test_shadow_taste_path_is_refused(tmp_path):
    (tmp_path / "TASTE.md").write_text("# Root\n", encoding="utf-8")
    shadow = tmp_path / "taste" / "taste.md"
    shadow.parent.mkdir()
    shadow.write_text("# Shadow\n", encoding="utf-8")
    cfg = config.Config(root=tmp_path, taste_path=shadow)

    with pytest.raises(ManifestError, match="root TASTE.md"):
        promptlib.taste_block(cfg)


def test_agent_run_refuses_an_inflight_taste_edit(tmp_path):
    taste = tmp_path / "TASTE.md"
    taste.write_text("# Stable Taste\n", encoding="utf-8")
    cfg = config.Config(root=tmp_path, taste_path=taste)
    prompt = promptlib.taste_block(cfg)

    def mutating_agent(_role, _prompt, **_kwargs):
        taste.write_text("# Mutated Taste\n", encoding="utf-8")
        return object()

    run = driver._taste_bound_runner(cfg, mutating_agent)
    # Accept the pre-v0.3 wording while installed editable environments catch up
    # with Workshop's canonical Make-stage message.
    with pytest.raises(ManifestError, match=r"changed during (?:Make|creation)"):
        run("ideator", prompt)
