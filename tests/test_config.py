
import typing

import pytest

from citadel.config import config
from citadel.watcher import base_watcher
from citadel.trigger import base_trigger

from conftest import DummyWatcher, DummyTrigger


def test_discover_instances(
    monkeypatch: pytest.MonkeyPatch,
    dummy_plugins: typing.List[typing.Any],
) -> None:
    monkeypatch.setenv("citadel_dummy-watcher__node1__url", "tcp://10.0.0.1:2375")
    monkeypatch.setenv("citadel_dummy-watcher__node2__url", "tcp://10.0.0.2:2375")
    monkeypatch.setenv("citadel_dummy-watcher__node2__cron", "*/5 * * * *")
    monkeypatch.setenv("citadel_dummy-trigger__bot__token", "secret")

    assert config.discover(dummy_plugins, env_file=None) == {
        "dummy-watcher": {
            "node1": {"url"},
            "node2": {"url", "cron"},
        },
        "dummy-trigger": {
            "bot": {"token"},
        },
    }


def test_discover_is_case_insensitive(monkeypatch: pytest.MonkeyPatch, dummy_plugins: typing.List[typing.Any]) -> None:
    monkeypatch.setenv("CITADEL_DUMMY-WATCHER__Node1__URL", "tcp://10.0.0.1:2375")

    assert config.discover(dummy_plugins, env_file=None) == {"dummy-watcher": {"node1": {"url"}}}


def test_discover_supports_single_underscore_in_name(
    monkeypatch: pytest.MonkeyPatch,
    dummy_plugins: typing.List[typing.Any],
) -> None:
    monkeypatch.setenv("citadel_dummy-watcher__node_1__url", "tcp://10.0.0.1:2375")

    assert config.discover(dummy_plugins, env_file=None) == {"dummy-watcher": {"node_1": {"url"}}}


def test_discover_ignores_global_variables(
    monkeypatch: pytest.MonkeyPatch,
    dummy_plugins: typing.List[typing.Any],
) -> None:
    monkeypatch.setenv("citadel_log_level", "debug")
    monkeypatch.setenv("citadel_tz", "America/Montreal")

    assert config.discover(dummy_plugins, env_file=None) == {}


def test_discover_unknown_type_name(monkeypatch: pytest.MonkeyPatch, dummy_plugins: typing.List[typing.Any]) -> None:
    monkeypatch.setenv("citadel_dummy-service__node1__enable", "true")

    with pytest.raises(config.ConfigError, match="invalid type name \"dummy-service\""):
        config.discover(dummy_plugins, env_file=None)


def test_discover_unknown_option(monkeypatch: pytest.MonkeyPatch, dummy_plugins: typing.List[typing.Any]) -> None:
    monkeypatch.setenv("citadel_dummy-watcher__node1__url", "tcp://10.0.0.1:2375")
    monkeypatch.setenv("citadel_dummy-watcher__node1__unknown_option", "true")

    with pytest.raises(config.ConfigError, match="unknown option \"unknown_option\""):
        config.discover(dummy_plugins, env_file=None)


def test_discover_hyphenated_option(monkeypatch: pytest.MonkeyPatch, dummy_plugins: typing.List[typing.Any]) -> None:
    monkeypatch.setenv("citadel_dummy-watcher__node1__include-by-default", "true")

    with pytest.raises(config.ConfigError, match="did you mean \"include_by_default\""):
        config.discover(dummy_plugins, env_file=None)


def test_discover_unknown_option_suggestion(
    monkeypatch: pytest.MonkeyPatch,
    dummy_plugins: typing.List[typing.Any],
) -> None:
    monkeypatch.setenv("citadel_dummy-watcher__node1__cronn", "*/5 * * * *")

    with pytest.raises(config.ConfigError, match="did you mean \"cron\""):
        config.discover(dummy_plugins, env_file=None)


def test_discover_malformed_variable_name(monkeypatch: pytest.MonkeyPatch, dummy_plugins: typing.List[typing.Any]) -> None:
    monkeypatch.setenv("citadel_dummy-watcher__node1", "tcp://10.0.0.1:2375")

    with pytest.raises(config.ConfigError, match="expected citadel_<type_name>__<name>__<option>"):
        config.discover(dummy_plugins, env_file=None)


def test_discover_from_env_file(tmp_path: typing.Any, dummy_plugins: typing.List[typing.Any]) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("citadel_dummy-watcher__node1__url=tcp://10.0.0.1:2375\ncitadel_log_level=warning\n")

    assert config.discover(dummy_plugins, env_file=env_file) == {"dummy-watcher": {"node1": {"url"}}}


def test_config_instantiates_plugins(
    monkeypatch: pytest.MonkeyPatch,
    dummy_plugins: typing.List[typing.Any],
) -> None:
    monkeypatch.setenv("citadel_dummy-watcher__node1__url", "tcp://10.0.0.1:2375")
    monkeypatch.setenv("citadel_dummy-watcher__node2__url", "tcp://10.0.0.2:2375")
    monkeypatch.setenv("citadel_dummy-watcher__node2__enable", "false")
    monkeypatch.setenv("citadel_dummy-trigger__bot__token", "secret")

    conf = config.Config(plugins=dummy_plugins, env_file=None)

    watchers = [i for i in conf.instances if isinstance(i, DummyWatcher)]
    triggers = [i for i in conf.instances if isinstance(i, DummyTrigger)]
    assert [w.name for w in watchers] == ["node1", "node2"]
    assert [t.name for t in triggers] == ["bot"]

    assert watchers[0].settings.url == "tcp://10.0.0.1:2375"
    assert watchers[0].enable is True
    assert watchers[1].enable is False
    assert triggers[0].settings.token == "secret"
    assert triggers[0].dry_run is False


def test_config_missing_required_option(monkeypatch: pytest.MonkeyPatch, dummy_plugins: typing.List[typing.Any]) -> None:
    monkeypatch.setenv("citadel_dummy-watcher__node1__cron", "*/5 * * * *")

    with pytest.raises(config.ConfigError, match="invalid configuration for \"citadel_dummy-watcher__node1__") as error:
        config.Config(plugins=dummy_plugins, env_file=None)
    assert "url" in str(error.value)


def test_config_invalid_global_setting(monkeypatch: pytest.MonkeyPatch, dummy_plugins: typing.List[typing.Any]) -> None:
    monkeypatch.setenv("citadel_log_level", "verbose")

    with pytest.raises(config.ConfigError, match="invalid global configuration"):
        config.Config(plugins=dummy_plugins, env_file=None)


def test_config_global_settings(monkeypatch: pytest.MonkeyPatch, dummy_plugins: typing.List[typing.Any]) -> None:
    monkeypatch.setenv("citadel_log_level", "DEBUG")
    monkeypatch.setenv("citadel_tz", "America/Montreal")

    conf = config.Config(plugins=dummy_plugins, env_file=None)

    assert conf.global_settings.log_level == "debug"
    assert conf.global_settings.tz == "America/Montreal"
    assert config.global_settings() is conf.global_settings


def test_config_global_settings_from_env_file(tmp_path: typing.Any, dummy_plugins: typing.List[typing.Any]) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("citadel_log_level=error\n")

    conf = config.Config(plugins=dummy_plugins, env_file=env_file)

    assert conf.global_settings.log_level == "error"


def test_watcher_timezone_fallback_on_global(
    monkeypatch: pytest.MonkeyPatch,
    dummy_plugins: typing.List[typing.Any],
) -> None:
    monkeypatch.setenv("TZ", "America/Montreal")
    monkeypatch.setenv("citadel_dummy-watcher__node1__url", "tcp://10.0.0.1:2375")

    conf = config.Config(plugins=dummy_plugins, env_file=None)

    watcher = conf.instances[0]
    assert watcher.settings.tz is None
    assert watcher._timezone_name == "America/Montreal"


def test_watcher_timezone_override(
    monkeypatch: pytest.MonkeyPatch,
    dummy_plugins: typing.List[typing.Any],
) -> None:
    monkeypatch.setenv("TZ", "America/Montreal")
    monkeypatch.setenv("citadel_dummy-watcher__node1__url", "tcp://10.0.0.1:2375")
    monkeypatch.setenv("citadel_dummy-watcher__node1__tz", "UTC")

    conf = config.Config(plugins=dummy_plugins, env_file=None)

    assert conf.instances[0]._timezone_name == "UTC"


def test_duplicate_type_name(dummy_watcher: typing.Type[DummyWatcher]) -> None:
    class Duplicated(dummy_watcher):  # type: ignore[misc, valid-type]
        pass

    with pytest.raises(config.ConfigError, match="is used by"):
        config.discover([dummy_watcher, Duplicated], env_file=None)


def test_plugin_without_settings_class() -> None:
    class WithoutSettings:
        type_name = "without-settings"

    with pytest.raises(config.ConfigError, match="does not define a settings_class"):
        config.discover([WithoutSettings], env_file=None)


def test_plugin_with_invalid_type_name(dummy_watcher: typing.Type[DummyWatcher]) -> None:
    class InvalidTypeName(dummy_watcher):  # type: ignore[misc, valid-type]
        type_name = "invalid__type-name"

    with pytest.raises(config.ConfigError, match="type_name \"invalid__type-name\" is invalid"):
        config.discover([InvalidTypeName], env_file=None)


def test_disabled_watcher_returns_no_check(monkeypatch: pytest.MonkeyPatch, dummy_plugins: typing.List[typing.Any]) -> None:
    monkeypatch.setenv("citadel_dummy-watcher__node1__url", "tcp://10.0.0.1:2375")
    monkeypatch.setenv("citadel_dummy-watcher__node1__enable", "off")

    conf = config.Config(plugins=dummy_plugins, env_file=None)

    watcher = conf.instances[0]
    assert watcher.enable is False
    assert watcher.check() == []


def test_plugin_protocol_is_satisfied(dummy_plugins: typing.List[typing.Any]) -> None:
    for plugin in dummy_plugins:
        assert issubclass(plugin.settings_class, config.BaseCitadelSettings)
        assert isinstance(plugin.type_name, str)


def test_set_logger(monkeypatch: pytest.MonkeyPatch, dummy_plugins: typing.List[typing.Any]) -> None:
    import logging

    import main

    previous_level = logging.root.level
    try:
        monkeypatch.setenv("citadel_log_level", "warning")
        main.set_logger(config.Config(plugins=dummy_plugins, env_file=None))
        assert logging.root.level == logging.WARNING

        monkeypatch.delenv("citadel_log_level")
        main.set_logger(config.Config(plugins=dummy_plugins, env_file=None))
        assert logging.root.level == logging.INFO
    finally:
        logging.root.setLevel(previous_level)


def test_base_settings_classes_are_shared() -> None:
    assert issubclass(DummyWatcher.settings_class, base_watcher.BaseWatcherSettings)
    assert issubclass(DummyTrigger.settings_class, base_trigger.BaseTriggerSettings)
