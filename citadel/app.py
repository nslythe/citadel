

from citadel.watcher import base_watcher, swarm_watcher
from citadel.trigger import base_trigger
from citadel.config import config, app_config
from citadel.registry import registry, registry_manager
import logging
import time
import typing

class App:
    def __init__(self, supported_type):
        self._supported_type = supported_type
        self.set_logger()
        self._config = config.Config(plugins=self._supported_type)
        self._config.load()

        self._registry_manager = registry_manager.RegistryManager()
        self._watchers: typing.List[base_watcher.BaseWatcher] = []
        self._single_message_triggers: typing.List[base_trigger.BaseTriggerSingleMessage] = []
        self._multi_message_triggers: typing.List[base_trigger.BaseTriggerMultiMessage] = []

        for v in self._config.instances:
            if isinstance(v, registry.CustomRegistry):
                self._registry_manager.add(v)
            if isinstance(v, base_watcher.BaseWatcher):
                self._watchers.append(v)
            if isinstance(v, base_trigger.BaseTriggerSingleMessage):
                self._single_message_triggers.append(v)
            if isinstance(v, base_trigger.BaseTriggerMultiMessage):
                self._multi_message_triggers.append(v)

        self._registry_manager.add(registry.ServerRegistry(name="ghcr.io", server="ghcr.io"))
        self._registry_manager.add(registry.ServerRegistry(name="lscr.io", server="lscr.io"))
        self._registry_manager.add(registry.ServerRegistry(name="docker.gitea.com", server="docker.gitea.com"))

        # check swarm list
        known_swarm_id = {}
        for w in self._watchers:
            if isinstance(w, swarm_watcher.SwarmWatcher):
                if w.swarm_id in known_swarm_id:
                    logging.warning("watcher \"%s\" disable because swarm already known from \"%s\"", w.name, known_swarm_id[w.swarm_id].name)
                    w.enable = False
                    continue
                known_swarm_id[w.swarm_id] = w

    @property
    def watchers(self) -> typing.List[base_watcher.BaseWatcher]:
        return self._watchers

    @property
    def single_message_triggers(self) -> typing.List[base_trigger.BaseTriggerSingleMessage]:
        return self._single_message_triggers

    @property
    def multi_message_triggers(self) -> typing.List[base_trigger.BaseTriggerMultiMessage]:
        return self._multi_message_triggers

    def set_logger(self):
        logging.root.setLevel(level=app_config.app_settings().log_level.upper())
        logging.getLogger("docker").setLevel(level="ERROR")
        logging.getLogger("urllib3").setLevel(level="ERROR")

    def run(self):
        while True:
            for w in self._watchers:
                check_list = w.check(app = self)
                if len(check_list) > 0:
                    for t in self._multi_message_triggers:
                        t.trigger(check_list)
                    for c in check_list:
                        for t in self._single_message_triggers:
                            t.trigger(c)

            time.sleep(1)

    def get_watcher(self, name: str) -> base_watcher.BaseWatcher:
        for w in self._watchers:
            if w.name == name:
                return w
        return None

    def has_watcher(self, name: str) -> bool:
        return self.get_watcher(name) is not None

    def watch(self, name: str):
        w = self.get_watcher(name)
        if w is None:
            raise Exception(f"Watcher {name} does not exists")
        w.force_next_run()

    def watch_all(self):
        for w in self._watchers:
            w.force_next_run()

    @property
    def registry_manager(self) -> registry_manager.RegistryManager:
        return self._registry_manager