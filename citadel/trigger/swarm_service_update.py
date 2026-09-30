
import pydantic
from . import base_trigger
from ..watcher import swarm_watcher
import logging

class SwarmServiceUpdateSettings(base_trigger.BaseTriggerSettings):
    pull_on_all_node: bool = pydantic.Field(default=False)

class SwarmServiceUpdate(base_trigger.BaseTriggerSingleMessage):
    type_name = "swarm-service-update"
    settings_class = SwarmServiceUpdateSettings

    def __init__(self, *, name: str, settings: SwarmServiceUpdateSettings):
        super().__init__(name=name, settings=settings)
        self.pull_on_all_node = settings.pull_on_all_node

    def do_trigger(self, check: swarm_watcher.SwarmWatcherCheck):
        if isinstance(check, swarm_watcher.SwarmWatcherCheck):
            logging.info("updating %s %s", check, f"dry-run: {self.dry_run}")
            if not self.dry_run:
                check._service.update(pull_on_all_node=self.pull_on_all_node)
