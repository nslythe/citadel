
import typing
from dataclasses import dataclass
import citadel.docker.task as task
import citadel.docker.base_docker as base_docker

# @dataclass
# class TaskImage:
#     image: str
#     digest: str
#     platform: typing.Dict[str, str]

class Service(base_docker.BaseDockerObject):
    def __init__(self, client, service):
        super().__init__(client)
        self._docker_service = service
        self._spec = self._docker_service.attrs.get("Spec")
        self._labels = self._spec.get("Labels")

    @property
    def labels(self) -> typing.Dict[str, str]:
        return self._labels

    @property
    def image(self) -> str:
        return self._labels.get("com.docker.stack.image")

    @property
    def name(self) -> str:
        return self._docker_service.name

    @property
    def stack_namespace(self) -> str:
        return self._labels.get("com.docker.stack.namespace")

    @property
    def tasks(self) -> typing.List[task.Task]:
        values = []
        for t in self._docker_service.tasks():
            values.append(task.Task(self.docker_client, t))
        return values

    @property
    def image_digest(self) -> str:
        for t in self.tasks:
            if t.state == "running":
                image_name = t.image
                digest = None
                try:
                    digest = image_name.split('@')[1]
                except:
                    pass

                if digest is None:
                    node_client = t.node.connect()
                    image = node_client.images.get(image_name)
                    digest = image.attrs['RepoDigests'][0].split('@')[1]

                if digest is not None:
                    return digest

        return None

    def update(self, *, pull_on_all_node: bool):
        if pull_on_all_node:
            for t in self.tasks:
                node_client = t.node.connect()
                node_client.images.pull(self.image)
        self._docker_service.update(image=self.image)
