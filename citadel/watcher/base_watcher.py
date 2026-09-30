
import abc
import typing
from .. import config
import cron_converter
import datetime
import logging
from zoneinfo import ZoneInfo

class BaseWatcherCheck(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __str__(self):
        pass


class BaseWatcher(metaclass=abc.ABCMeta):
    def __init__(self, conf: config.ConfigVariable):
        self.conf = conf
        self.enable = conf.get("enable", default=True)
        self.include_by_default = conf.get("include-by-default", default=False)
        self._timezone_name = conf.get("tz", default=self.conf.global_config.tz)
        self._cron_str = conf.get("cron", default="*/15 * * * *")

        self._timezone = ZoneInfo(self._timezone_name)
        self._cron = cron_converter.Cron()
        self._cron.from_string(self._cron_str)
        self._cron_reference = datetime.datetime.now(tz=self._timezone)
        self._cron_schedule = self._cron.schedule(self._cron_reference)
        self.update_schedule()

    def update_schedule(self):
        self._next_execution_date = self._cron_schedule.next()
        logging.info("Watcher %s next execution schedule for %s", self.conf.name, self._next_execution_date)

    def check(self) -> typing.List[BaseWatcherCheck]:
        if not self.enable:
            return []
        if self._next_execution_date > datetime.datetime.now(self._timezone):
            return []
        self.update_schedule()
        return self.do_check()

    @property
    def name(self) -> str:
        return self.conf.name

    @abc.abstractmethod
    def do_check(self) -> typing.List[BaseWatcherCheck]:
        pass
