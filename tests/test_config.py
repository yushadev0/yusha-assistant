from __future__ import annotations

from pathlib import Path

import pytest

from yusha.config import AppConfig, Settings


def test_admin_ids_split_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("YUSHA_BOT_TOKEN", "x")
    monkeypatch.setenv("YUSHA_ADMIN_IDS", "111, 222 ,333")
    s = Settings()  # type: ignore[call-arg]
    assert s.admin_ids == [111, 222, 333]


def test_ssh_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("YUSHA_BOT_TOKEN", "x")
    monkeypatch.setenv("YUSHA_ADMIN_IDS", "1")
    assert Settings().ssh_enabled is False  # type: ignore[call-arg]


def test_load_app_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
services:
  - name: iposi
    container: iposi_prod
    actions: [logs, restart]
commands:
  - name: disk
    target: host
    argv: ["df", "-h"]
  - name: health
    target: "container:iposi_prod"
    argv: ["sh", "-c", "echo ok"]
    confirm: true
""",
        "utf-8",
    )
    monkeypatch.setenv("YUSHA_BOT_TOKEN", "x")
    monkeypatch.setenv("YUSHA_ADMIN_IDS", "1")
    monkeypatch.setenv("YUSHA_CONFIG_PATH", str(cfg))

    app = Settings().load_app_config()  # type: ignore[call-arg]

    assert app.service("iposi") is not None
    assert app.service("iposi").container == "iposi_prod"  # type: ignore[union-attr]
    assert app.service_by_container("iposi_prod").name == "iposi"  # type: ignore[union-attr]
    assert app.service("yok") is None
    assert app.command("disk").argv == ["df", "-h"]  # type: ignore[union-attr]
    assert app.command("health").confirm is True  # type: ignore[union-attr]


def test_missing_config_file_is_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("YUSHA_BOT_TOKEN", "x")
    monkeypatch.setenv("YUSHA_ADMIN_IDS", "1")
    monkeypatch.setenv("YUSHA_CONFIG_PATH", str(tmp_path / "nope.yaml"))
    app = Settings().load_app_config()  # type: ignore[call-arg]
    assert app == AppConfig()


def test_empty_argv_rejected() -> None:
    with pytest.raises(ValueError):
        AppConfig.model_validate({"commands": [{"name": "x", "argv": []}]})
