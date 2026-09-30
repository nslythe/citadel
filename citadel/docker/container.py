

import citadel.docker.base_docker as base_docker
import typing
import enum
import datetime
import time
import uuid

class ContainerState(enum.StrEnum):
    created = enum.auto()
    running = enum.auto()
    rRestarting = enum.auto()
    exited = enum.auto()
    pPaused = enum.auto()
    dead = enum.auto()
    removing  = enum.auto()

class ContainerHealth(enum.StrEnum):
    starting  = enum.auto()
    healthy  = enum.auto()
    unhealthy  = enum.auto()
    unknown = enum.auto()

class UpdateException(Exception):
    def __init__(self, message):
        super().__init__(message)

class Container(base_docker.BaseDockerObject):
    def __init__(self, client, container):
        super().__init__(client)
        self._docker_container = container

    @property
    def labels(self) -> typing.Dict[str, str]:
        return self._docker_container.labels

    @property
    def image(self) -> str:
        return self._docker_container.attrs.get("Config").get("Image")
        # return self._docker_container.image.attrs.get("Identity").get("Pull")[0].get("Repository")

    @property
    def name(self) -> str:
        return self._docker_container.name

    @property
    def image_digest(self) -> str:
        return self._docker_container.image.id

    @property
    def in_swarm(self):
        for n in self.labels:
            if n.startswith("com.docker.swarm."):
                return True
        return False

    @property
    def id(self) -> str:
        return self._docker_container.id

    @property
    def state(self) -> ContainerState:
        return ContainerState[self._docker_container.status]

    @property
    def health(self) -> ContainerState:
        return ContainerHealth[self._docker_container.health]

    def get_config(self) -> dict[str, typing.Any]:
        networks = list(self._docker_container.attrs.get("NetworkSettings").get("Networks").keys())
        mounts = []
        for m in self._docker_container.attrs.get("Mounts"):
            mounts.append({
                "target" : m.get("Destination"),
                "type" : m.get("Type"),
                "source" : m.get("Source"),
                "read_only" : not m.get("RW"),
                "propagation" : m.get("Propagation"),
# consistency 
# no_copy 
# labels 
# driver_config 
# subpath 
# tmpfs_size 
# tmpfs_mode 
            })

        return {
            "image"         : self.image,
            "name"          : self.name,
            "command"       : self._docker_container.attrs.get("Config").get("Cmd"),
            "environment"   : self._docker_container.attrs.get("Config").get("Env"),
            "labels"        : self._docker_container.attrs.get("Config").get("Labels"),
            "entrypoint"    : self._docker_container.attrs.get("Config").get("Entrypoint"),
            "mounts"       : mounts,

            "devices"       : self._docker_container.attrs.get("HostConfig").get("Devices"),
            "runtime"       : self._docker_container.attrs.get("HostConfig").get("Runtime"),
            "restart_policy": self._docker_container.attrs.get("HostConfig").get("RestartPolicy"),

            "ports"         : self._docker_container.attrs.get("NetworkSettings").get("Ports"), 
            "network"       : networks[0], 
        }

    def stop(self, *,  timeout):
        self._docker_container.stop(timeout=timeout)

    def start(self, config, *, timeout = 30):
        config["detach"] = True
        new_container = self._docker_client._docker_client.containers.run(**config)
        time.sleep(10)
        start_time = datetime.datetime.now()
        while True:
            new_container.reload()
            new_container_satus = ContainerState[new_container.status]
            if new_container_satus == ContainerState.running:
                break
            if (datetime.datetime.now() - start_time).total_seconds() > timeout:
                raise UpdateException("Error restarting container")
            time.sleep(2)
        self._docker_container = new_container

    def update(self, *, stop_timeout = 10, start_timeout = 30):
        update_id = uuid.uuid4()

        old_container_id = self.id
        old_container_name = self.name
        new_container_name = "citadel_" + str(update_id)
        backup_container_name = "citadel_backup_" + str(update_id)

        self.docker_client._docker_client.images.pull(self.image)
        config = self.get_config()
        self.stop(timeout=stop_timeout)
        config["name"] = new_container_name
        try:
            self.start(config, timeout=start_timeout)
            self._docker_client._docker_client.containers.get(old_container_id).rename(backup_container_name)
            self._docker_client._docker_client.containers.get(self.id).rename(old_container_name)
        except UpdateException as e:
            self._docker_client.containers.start(old_container_id)
