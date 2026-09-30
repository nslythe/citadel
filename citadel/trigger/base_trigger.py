
import abc
from ..watcher import base_watcher
from .. import config
import typing

class _BaseTrigger(metaclass=abc.ABCMeta):
    def __init__(self, conf: config.ConfigVariable):
        self.conf = conf
        self.enable = conf.get("enable", default=True)
        self.dry_run = conf.get("dry-run", default=False)

    @abc.abstractmethod
    def do_trigger(self, check: base_watcher.BaseWatcherCheck):
        pass

    def trigger(self, check: base_watcher.BaseWatcherCheck):
        if self.enable:
            self.do_trigger(check)

class BaseTriggerSingleMessage(_BaseTrigger):
    def __init__(self, conf: config.ConfigVariable):
        super().__init__(conf)

class BaseTriggerMultiMessage(_BaseTrigger):
    def __init__(self, conf: config.ConfigVariable):
        super().__init__(conf)
