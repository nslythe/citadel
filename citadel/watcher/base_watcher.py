
import abc
import typing
import datetime
import logging
from zoneinfo import ZoneInfo
from ..config import type_validator, app_config

import cron_converter
import pydantic

from ..config import config

if typing.TYPE_CHECKING:
    from ..docker import service, container

class BaseWatcherSettings(config.BaseCitadelSettings):
    enable: bool = pydantic.Field(default=True)
    include_by_default: bool = pydantic.Field(default=False)
    tz: typing.Optional[type_validator.Timezone] = pydantic.Field(default=None)
    cron: type_validator.CronExpression = pydantic.Field(default="*/15 * * * *")


class BaseWatcherCheck(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __str__(self):
        pass

class BaseWatcher(metaclass=abc.ABCMeta):
    def __init__(self, *, name: str, settings: BaseWatcherSettings):
        self.name = name
        self.settings = settings
        self.enable = settings.enable
        self.include_by_default = settings.include_by_default
        self._timezone_name = settings.tz if settings.tz is not None else app_config.app_settings().tz
        self._cron_str = settings.cron

        self._timezone = ZoneInfo(self._timezone_name)
        self._cron = cron_converter.Cron()
        self._cron.from_string(self._cron_str)
        self._cron_reference = datetime.datetime.now(tz=self._timezone)
        self._cron_schedule = self._cron.schedule(self._cron_reference)
        self.update_schedule()

    def update_schedule(self):
        self._next_execution_date = self._cron_schedule.next()
        logging.info("Watcher %s next execution schedule for %s", self.name, self._next_execution_date)

    def check(self) -> typing.List[BaseWatcherCheck]:
        if not self.enable:
            return []
        if self._next_execution_date > datetime.datetime.now(self._timezone):
            return []
        self.update_schedule()
        return self.do_check()

    @abc.abstractmethod
    def do_check(self) -> typing.List[BaseWatcherCheck]:
        pass

    def is_included(self, instance: 'service.Service' | 'container.Container') -> bool:
        include_all_watcher = pydantic.type_adapter.TypeAdapter(bool).validate_json(instance.labels.get('citadel.include.all_watcher', "false"))
        return self.include_by_default or include_all_watcher
