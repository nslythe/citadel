
import typing
from ..docker import registry as docker_registry
from . import registry
import pydantic
import datetime
import requests
import logging

class RegistryManagerCacheItem(pydantic.BaseModel):
    digest: str
    date: datetime.datetime
    expires: datetime.datetime

class RegistryManagerCache(pydantic.BaseModel):
    cache: typing.Dict[str, RegistryManagerCacheItem] = pydantic.Field(default_factory=dict)

class RegistryManager:
    def __init__(self):
        self._registries: typing.List[registry.CustomRegistry] = []
        self._cache = RegistryManagerCache()

    def add(self, reg: registry.CustomRegistry):
        self._registries.append(reg)

    def get_image_digest(self, image: str) -> str | None:
        cached_image = self._cache.cache.get(image)
        if cached_image is not None:
            if datetime.datetime.now() < cached_image.expires:
                return cached_image.digest
            else:
                del self._cache.cache[image]

        found_registry = None
        for r in self._registries:
            if r.docker_registry.include(image):
                found_registry = r.docker_registry
                break
        if found_registry is None:
            found_registry = docker_registry.docker_io_registry

        digest_response = None
        try:
            digest_response = found_registry.get_image_digest(image)
        except requests.exceptions.HTTPError as e:
            logging.exception("Failed to get digest for image %s", image)
        except docker_registry.RateLimitedError as e:
            logging.error("Ration limit reached for iamge %s", image)
        except:
            logging.exception("Unknown error")

        if digest_response is not None:
            expires = digest_response.expires
            if expires is None:
                expires = datetime.datetime.now() + datetime.timedelta(minutes=5)
            self._cache.cache[image] = RegistryManagerCacheItem(
                digest=digest_response.digest,
                date=datetime.datetime.now(),
                expires=expires)

            return digest_response.digest
        return None
