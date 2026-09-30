
import abc
import typing

import pydantic

from ..watcher import base_watcher
from ..config import config, type_validator


class BaseTriggerSettings(config.BaseCitadelSettings):
    enable: bool = pydantic.Field(default=True)
    dry_run: bool = pydantic.Field(default=False)
    tz: typing.Optional[type_validator.Timezone] = pydantic.Field(default=None)

class _BaseTrigger(metaclass=abc.ABCMeta):
    def __init__(self, *, name: str, settings: BaseTriggerSettings):
        self.name = name
        self.settings = settings
        self.enable = settings.enable
        self.dry_run = settings.dry_run

    @abc.abstractmethod
    def do_trigger(self, check: base_watcher.BaseWatcherCheck):
        pass

    def trigger(self, check: base_watcher.BaseWatcherCheck):
        if self.enable:
            self.do_trigger(check)

class BaseTriggerSingleMessage(_BaseTrigger):
    def __init__(self, *, name: str, settings: BaseTriggerSettings):
        super().__init__(name=name, settings=settings)

class BaseTriggerMultiMessage(_BaseTrigger):
    def __init__(self, *, name: str, settings: BaseTriggerSettings):
        super().__init__(name=name, settings=settings)
