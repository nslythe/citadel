
from ..config import config
from ..docker import registry
import pydantic

class RegistrySettings(config.BaseCitadelSettings):
    url: str = pydantic.Field()

class CustomRegistry:
    type_name = "custom-registry"
    settings_class = RegistrySettings

    def __init__(self, *, name: str, settings: RegistrySettings):
        self._name = name
        self._settings = settings
        self._registry = registry.BaseRegistry(self._settings.url)

    @property
    def docker_registry(self) -> registry.BaseRegistry:
        return self._registry

class ServerRegistry(CustomRegistry):
    def __init__(self, *, name: str, server: str):
        self._name = name
        self._registry = registry.BaseRegistry(server)
