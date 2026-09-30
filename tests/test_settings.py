
import typing

import pytest
import pydantic

from citadel.config import config
from citadel.watcher import base_watcher, swarm_watcher, container_watcher
from citadel.trigger import base_trigger, swarm_service_update, container_update, discord


def _settings(cls: typing.Type[config.BaseCitadelSettings], name: str, type_name: str) -> typing.Any:
    return cls(
        _env_prefix=f"{config.ENV_PREFIX}{type_name}{config.ENV_NESTED_DELIMITER}{name}{config.ENV_NESTED_DELIMITER}",
        _env_file=None,
    )


def test_global_settings_defaults() -> None:
    settings = config.GlobalSettings(_env_file=None)

    assert settings.log_level == "info"
    assert settings.tz == "UTC"


def test_global_settings_tz_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TZ", "America/Montreal")

    assert config.GlobalSettings(_env_file=None).tz == "America/Montreal"


def test_global_settings_invalid_tz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TZ", "Not/AZone")

    with pytest.raises(pydantic.ValidationError):
        config.GlobalSettings(_env_file=None)


def test_global_settings_invalid_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("citadel_log_level", "verbose")

    with pytest.raises(pydantic.ValidationError):
        config.GlobalSettings(_env_file=None)


def test_watcher_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("citadel_container-watcher__node1__url", "tcp://10.0.0.1:2375")

    settings = _settings(container_watcher.ContainerWatcherSettings, "node1", "container-watcher")

    assert settings.url == "tcp://10.0.0.1:2375"
    assert settings.enable is True
    assert settings.include_by_default is False
    assert settings.tz is None
    assert settings.cron == "*/15 * * * *"


@pytest.mark.parametrize("value", ["true", "True", "TRUE", "1", "on", "yes"])
def test_watcher_settings_bool_coercion(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("citadel_container-watcher__node1__url", "tcp://10.0.0.1:2375")
    monkeypatch.setenv("citadel_container-watcher__node1__enable", value)
    monkeypatch.setenv("citadel_container-watcher__node1__include_by_default", value)

    settings = _settings(container_watcher.ContainerWatcherSettings, "node1", "container-watcher")

    assert settings.enable is True
    assert settings.include_by_default is True


@pytest.mark.parametrize("value", ["false", "False", "0", "off", "no"])
def test_watcher_settings_bool_coercion_false(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("citadel_swarm-watcher__node1__url", "tcp://10.0.0.1:2375")
    monkeypatch.setenv("citadel_swarm-watcher__node1__enable", value)

    assert _settings(swarm_watcher.SwarmWatcherSettings, "node1", "swarm-watcher").enable is False


def test_watcher_settings_invalid_bool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("citadel_container-watcher__node1__url", "tcp://10.0.0.1:2375")
    monkeypatch.setenv("citadel_container-watcher__node1__enable", "maybe")

    with pytest.raises(pydantic.ValidationError):
        _settings(container_watcher.ContainerWatcherSettings, "node1", "container-watcher")


def test_watcher_settings_missing_url() -> None:
    with pytest.raises(pydantic.ValidationError, match="url"):
        _settings(swarm_watcher.SwarmWatcherSettings, "node1", "swarm-watcher")


def test_watcher_settings_invalid_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("citadel_swarm-watcher__node1__url", "10.0.0.1:2375")

    with pytest.raises(pydantic.ValidationError, match="url"):
        _settings(swarm_watcher.SwarmWatcherSettings, "node1", "swarm-watcher")


@pytest.mark.parametrize("url", ["unix:///var/run/docker.sock", "tcp://10.0.0.1:2375", "http://10.0.0.1:2375"])
def test_watcher_settings_valid_urls(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    monkeypatch.setenv("citadel_swarm-watcher__node1__url", url)

    assert _settings(swarm_watcher.SwarmWatcherSettings, "node1", "swarm-watcher").url == url


def test_watcher_settings_invalid_cron(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("citadel_swarm-watcher__node1__url", "tcp://10.0.0.1:2375")
    monkeypatch.setenv("citadel_swarm-watcher__node1__cron", "every minutes")

    with pytest.raises(pydantic.ValidationError, match="cron"):
        _settings(swarm_watcher.SwarmWatcherSettings, "node1", "swarm-watcher")


def test_watcher_settings_invalid_tz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("citadel_swarm-watcher__node1__url", "tcp://10.0.0.1:2375")
    monkeypatch.setenv("citadel_swarm-watcher__node1__tz", "Not/AZone")

    with pytest.raises(pydantic.ValidationError, match="tz"):
        _settings(swarm_watcher.SwarmWatcherSettings, "node1", "swarm-watcher")


def test_trigger_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("citadel_container-update__auto__enable", "true")

    settings = _settings(container_update.ContainerUpdateSettings, "auto", "container-update")

    assert settings.enable is True
    assert settings.dry_run is False
    assert settings.tz is None


def test_trigger_settings_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("citadel_container-update__auto__dry_run", "true")
    monkeypatch.setenv("citadel_swarm-service-update__updater__dry_run", "true")
    monkeypatch.setenv("citadel_swarm-service-update__updater__pull_on_all_node", "true")

    assert _settings(container_update.ContainerUpdateSettings, "auto", "container-update").dry_run is True

    settings = _settings(swarm_service_update.SwarmServiceUpdateSettings, "updater", "swarm-service-update")
    assert settings.dry_run is True
    assert settings.pull_on_all_node is True


def test_discord_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("citadel_discord__prod__webhook", "https://discord.com/api/webhooks/1/abc")

    settings = _settings(discord.DiscordSettings, "prod", "discord")

    assert settings.webhook == "https://discord.com/api/webhooks/1/abc"
    assert settings.dry_run is False


def test_discord_settings_missing_webhook() -> None:
    with pytest.raises(pydantic.ValidationError, match="webhook"):
        _settings(discord.DiscordSettings, "prod", "discord")


@pytest.mark.parametrize("webhook", ["discord.com/api/webhooks/1/abc", "ftp://discord.com/x", ""])
def test_discord_settings_invalid_webhook(monkeypatch: pytest.MonkeyPatch, webhook: str) -> None:
    monkeypatch.setenv("citadel_discord__prod__webhook", webhook)

    with pytest.raises(pydantic.ValidationError, match="webhook"):
        _settings(discord.DiscordSettings, "prod", "discord")


def test_settings_classes_inherit_common_options() -> None:
    watcher_options = set(base_watcher.BaseWatcherSettings.model_fields)
    trigger_options = set(base_trigger.BaseTriggerSettings.model_fields)

    assert watcher_options == {"enable", "include_by_default", "tz", "cron"}
    assert trigger_options == {"enable", "dry_run", "tz"}

    for cls in (swarm_watcher.SwarmWatcherSettings, container_watcher.ContainerWatcherSettings):
        assert set(cls.model_fields) == watcher_options | {"url"}
        assert issubclass(cls, config.BaseCitadelSettings)

    for cls in (
        swarm_service_update.SwarmServiceUpdateSettings,
        container_update.ContainerUpdateSettings,
        discord.DiscordSettings,
    ):
        assert watcher_options is not None
        assert set(cls.model_fields) >= trigger_options
        assert issubclass(cls, base_trigger.BaseTriggerSettings)
        assert issubclass(cls, config.BaseCitadelSettings)


def test_instances_are_independent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("citadel_container-watcher__node1__url", "tcp://10.0.0.1:2375")
    monkeypatch.setenv("citadel_container-watcher__node2__url", "tcp://10.0.0.2:2375")

    node1 = _settings(container_watcher.ContainerWatcherSettings, "node1", "container-watcher")
    node2 = _settings(container_watcher.ContainerWatcherSettings, "node2", "container-watcher")

    assert node1.url == "tcp://10.0.0.1:2375"
    assert node2.url == "tcp://10.0.0.2:2375"
