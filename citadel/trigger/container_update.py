
from . import base_trigger
from ..watcher import container_watcher
import logging

class ContainerUpdateSettings(base_trigger.BaseTriggerSettings):
    pass

class ContainerUpdate(base_trigger.BaseTriggerSingleMessage):
    type_name = "container-update"
    settings_class = ContainerUpdateSettings

    def __init__(self, *, name: str, settings: ContainerUpdateSettings):
        super().__init__(name=name, settings=settings)

    def do_trigger(self, check: container_watcher.ContainerWatcherCheck):
        if isinstance(check, container_watcher.ContainerWatcherCheck):
            logging.info("updating %s %s", check, f"dry-run: {self.dry_run}")
            if not self.dry_run:
                check._container.update()
