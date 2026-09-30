
from citadel.docker import client

class BaseDockerObject:
    def __init__(self, client: client.Client):
        self._docker_client = client

    @property
    def docker_client(self) -> client.Client:
        return self._docker_client
