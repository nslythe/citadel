
import abc
from . import base_trigger
from ..watcher import swarm_watcher
from citadel import config
import logging

class SwarmServiceUpdate(base_trigger.BaseTriggerSingleMessage):
    type_name = "swarm-service-update"
    def __init__(self, conf: config.ConfigVariable):
        super().__init__(conf)
        self.pull_on_all_node = self.conf.get("pull-on-all-node", default=False)

    def do_trigger(self, check: swarm_watcher.SwarmWatcherCheck):
        if isinstance(check, swarm_watcher.SwarmWatcherCheck):
            logging.info("updating %s %s", check, f"dry-run: {self.dry_run}")
            if not self.dry_run:
                check._service.update(pull_on_all_node=self.pull_on_all_node)
