
import abc
from . import base_trigger
from ..watcher import container_watcher
from citadel import config
import logging

class ContainerUpdate(base_trigger.BaseTriggerSingleMessage):
    type_name = "container-update"
    def __init__(self, conf: config.ConfigVariable):
        super().__init__(conf)

    def do_trigger(self, check: container_watcher.ContainerWatcherCheck):
        if isinstance(check, container_watcher.ContainerWatcherCheck):
            logging.info("updating %s %s", check, f"dry-run: {self.dry_run}")
            if not self.dry_run:
                check._container.update()
