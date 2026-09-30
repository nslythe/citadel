
import os
import typing

import pytest
import pydantic

from citadel.config import config, type_validator
from citadel.watcher import base_watcher
from citadel.trigger import base_trigger


@pytest.fixture(autouse=True)
def clean_config_env(monkeypatch: pytest.MonkeyPatch) -> typing.Iterator[None]:
    for key in list(os.environ.keys()):
        if key.lower().startswith(config.ENV_PREFIX) or key.lower() == "tz":
            monkeypatch.delenv(key, raising=False)
    config.reset_global_settings()
    yield
    config.reset_global_settings()


class DummyWatcherSettings(base_watcher.BaseWatcherSettings):
    url: type_validator.DockerUrl = pydantic.Field()


class DummyWatcher(base_watcher.BaseWatcher):
    type_name = "dummy-watcher"
    settings_class = DummyWatcherSettings

    def do_check(self) -> typing.List[base_watcher.BaseWatcherCheck]:
        return []


class DummyTriggerSettings(base_trigger.BaseTriggerSettings):
    token: str = pydantic.Field()


class DummyTrigger(base_trigger.BaseTriggerSingleMessage):
    type_name = "dummy-trigger"
    settings_class = DummyTriggerSettings

    def do_trigger(self, check: base_watcher.BaseWatcherCheck) -> None:
        pass


@pytest.fixture
def dummy_plugins() -> typing.List[typing.Any]:
    return [DummyWatcher, DummyTrigger]


@pytest.fixture
def dummy_watcher() -> typing.Type[DummyWatcher]:
    return DummyWatcher


@pytest.fixture
def dummy_trigger() -> typing.Type[DummyTrigger]:
    return DummyTrigger
