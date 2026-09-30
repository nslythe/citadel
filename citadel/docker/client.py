
import docker
from citadel.docker import service, node, container
import typing

class Client:
    def __init__(self, *, url: str):
        self._docker_client = docker.DockerClient(base_url=url)

    @property
    def services(self) -> typing.List[service.Service]:
        values = []
        for s in self._docker_client.services.list():
            values.append(service.Service(self, s))
        return values

    @property
    def nodes(self) -> typing.List[node.Node]:
        values = []
        for s in self._docker_client.nodes.list():
            values.append(node.Node(self, s))
        return values

    @property
    def containers(self) -> typing.List[container.Container]:
        values = []
        for c in self._docker_client.containers.list():
            values.append(container.Container(self, c))
        return values

    def get_node(self, id) -> node.Node:
        return node.Node(self, self._docker_client.nodes.get(id))

    @property
    def swarm_id(self) -> str:
        return self._docker_client.swarm.id