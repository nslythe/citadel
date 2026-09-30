
from citadel.docker import client, registry, service, container
from citadel import config

import logging
from . import base_watcher
import typing
import pydantic

class ContainerWatcherCheck(base_watcher.BaseWatcherCheck):
    def __init__(self, container: service.Service):
        self._container = container
    
    def __str__(self) -> str:
        return ""

class ContainerWatcher(base_watcher.BaseWatcher):
    type_name = "container-watcher"
    def __init__(self, conf: config.Config):
        super().__init__(conf)
        self._client = client.Client(url=self.conf.get("url"))

    def do_check(self) -> typing.List[ContainerWatcherCheck]:
        return_value = []

        for docker_container in self._client.containers:
            if not docker_container.in_swarm and docker_container.state == container.ContainerState.running:
                logging.debug("check container %s", docker_container.name)
                if not self.is_included(docker_container):
                    logging.debug("container %s skipped watch, not included", docker_container.name)
                    continue

                registry_image_digest = registry.get_image_digest(docker_container.image)
                if registry_image_digest != docker_container.image_digest:
                    return_value.append(ContainerWatcherCheck(docker_container))

        return return_value
