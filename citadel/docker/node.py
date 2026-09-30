import citadel.docker.base_docker as base_docker
import docker
from . import platform

class Node(base_docker.BaseDockerObject):
    def __init__(self, client, node):
        super().__init__(client)
        self._docker_nodek = node

    @property
    def id(self) -> str:
        return self._docker_nodek.get("ID")

    @property
    def platform(self) -> platform.Platform:
        return platform.Platform(self._docker_nodek.attrs["Description"]["Platform"])

    @property
    def ip(self) -> str:
        return self._docker_nodek.attrs["Status"]["Addr"]

    @property
    def name(self) -> str:
        return self._docker_nodek.attrs["Description"]["Hostname"]


    def connect(self) -> docker.DockerClient:
        return docker.DockerClient(base_url=f'tcp://{self.ip}:2375')
