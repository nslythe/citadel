
import citadel.docker.base_docker as base_docker
import citadel.docker.node as node
import typing

class Task(base_docker.BaseDockerObject):
    def __init__(self, client, task):
        super().__init__(client)
        self._docker_task = task

    @property
    def node_id(self) -> str:
        return self._docker_task.get("NodeID")

    @property
    def node(self) -> node.Node:
        docker_node = self._docker_client.get_node(self.node_id)
        if docker_node is None:
            return None
        return docker_node

    @property
    def state(self) -> str:
        return self._docker_task["Status"]["State"]

    @property
    def is_running(self) -> bool:
        return self.state == "running"

    @property
    def image(self) -> str:
        return self._docker_task["Spec"]["ContainerSpec"]["Image"]
