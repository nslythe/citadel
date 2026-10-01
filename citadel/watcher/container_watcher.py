
from citadel.docker import client, registry, service, container

import logging
from . import base_watcher
from ..config import type_validator
from ..registry import registry as citadel_registry
import typing
import pydantic

class ContainerWatcherCheck(base_watcher.BaseWatcherCheck):
    def __init__(self, container: service.Service):
        self._container = container
    
    def __str__(self) -> str:
        return ""

class ContainerWatcherSettings(base_watcher.BaseWatcherSettings):
    url: type_validator.DockerUrl = pydantic.Field()

class ContainerWatcher(base_watcher.BaseWatcher):
    type_name = "container-watcher"
    settings_class = ContainerWatcherSettings

    def __init__(self, *, name: str, settings: ContainerWatcherSettings):
        super().__init__(name=name, settings=settings)

    def do_check(self, *, registries: typing.List[citadel_registry.CustomRegistry]) -> typing.List[ContainerWatcherCheck]:
        with client.open(url=self.settings.url) as docker_client:
            return_value = []

            for docker_container in docker_client.containers:
                if not docker_container.in_swarm and docker_container.state == container.ContainerState.running:
                    logging.debug("check container %s", docker_container.name)
                    if not self.is_included(docker_container):
                        logging.debug("container %s skipped watch, not included", docker_container.name)
                        continue

                    found_registry = None
                    for r in registries:
                        if r.docker_registry.include(docker_container.image):
                            found_registry = r.docker_registry
                            break
                    if found_registry is None:
                        found_registry = registry.DockerIO_Registry()

                    registry_image_digest = found_registry.get_image_digest(docker_container.image)
                    if registry_image_digest != docker_container.image_digest:
                        return_value.append(ContainerWatcherCheck(docker_container))

            return return_value
