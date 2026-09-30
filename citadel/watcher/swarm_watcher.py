
from citadel.docker import client, registry, service
from citadel import config

import logging
from . import base_watcher
import typing

class SwarmWatcherCheck(base_watcher.BaseWatcherCheck):
    def __init__(self, service: service.Service):
        self._service = service
    
    def __str__(self) -> str:
        nodes = []
        for t in self._service.tasks:
            if t.is_running:
                nodes.append(t.node.name)
        nodes_str = ", ".join(nodes)
        return f"{self._service.stack_namespace}.{self._service.name} on node [{nodes_str}]"

class SwarmWatcher(base_watcher.BaseWatcher):
    type_name = "swarm-watcher"
    def __init__(self, conf: config.Config):
        super().__init__(conf)

        self._client = client.Client(url=self.conf.get("url"))

        if self._client.swarm_id is None:
            raise Exception(f"watcher is not a swarm manager {self.conf.name}")

    def do_check(self) -> typing.List[SwarmWatcherCheck]:
        return_value = []
        for docker_service in self._client.services:
            logging.debug("check service %s", docker_service.name)
            if not self.include_by_default and 'citadel.include.all_watcher' not in docker_service.labels:
                continue

            try:
                registry_image_digest = registry.get_image_digest(docker_service.image)
                if docker_service.image_digest != registry_image_digest:
                    return_value.append(SwarmWatcherCheck(docker_service))
                    break

            except Exception as e:
                logging.exception(f"{docker_service.image} not found")

        return return_value

    @property
    def swarm_id(self) -> str:
        return self._client.swarm_id