
from citadel.docker import client, registry, service

import logging
import pydantic
from . import base_watcher
from ..config import type_validator
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

class SwarmWatcherSettings(base_watcher.BaseWatcherSettings):
    url: type_validator.DockerUrl = pydantic.Field()

class SwarmWatcher(base_watcher.BaseWatcher):
    type_name = "swarm-watcher"
    settings_class = SwarmWatcherSettings

    def __init__(self, *, name: str, settings: SwarmWatcherSettings):
        super().__init__(name=name, settings=settings)

    def do_check(self) -> typing.List[SwarmWatcherCheck]:
        with client.open(url=self.settings.url) as docker_client:
            if docker_client.swarm_id is None:
                raise Exception(f"watcher is not a swarm manager {self.name}")

            return_value = []
            for docker_service in docker_client.services:
                logging.debug("check service %s", docker_service.name)
                if not self.is_included(docker_service):
                    logging.debug("service %s skipped watch, not included", docker_service.name)
                    continue

                registry_image_digest = registry.get_image_digest(docker_service.image)
                if docker_service.image_digest != registry_image_digest:
                    return_value.append(SwarmWatcherCheck(docker_service))

            return return_value


    @property
    def swarm_id(self) -> str:
        with client.open(url=self.settings.url) as docker_client:
            return docker_client.swarm_id
