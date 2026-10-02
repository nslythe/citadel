

import requests
import dataclasses
import datetime
import logging
import email

@dataclasses.dataclass
class RegistryImage:
    registry:  str = None
    name: str = None
    tag: str = None
    digest: str | None = None

    def from_image(image: str, registry_name: str) -> RegistryImage:
        registry_image = RegistryImage()

        components = image.split(":")

        registry_image.name = image
        registry_image.tag = "latest"

        if len(components) > 1:
            registry_image.name = components[0]
            registry_image.tag = ":".join(components[1:])

        if registry_image.name.split("/")[0] == registry_name:
            registry_image.registry = registry_name
            registry_image.name = "/".join(registry_image.name.split("/")[1:])

        if "@" in registry_image.tag:
            registry_image.digest = registry_image.tag.split("@")[1]
        return registry_image

class WWWAuthenticate:
    def __init__(self, header_value, repository):
        self._header_value = header_value
        self._repository = repository
        self._scheme = self._header_value.split(" ")[0]
        www_authenticate_params_components = "".join(self._header_value.split(" ")[1:]).split(",")
        self._params = {}
        for wa in www_authenticate_params_components:
            wa_components = wa.split("=")
            self._params[wa_components[0]] = wa_components[1].replace("\"", "")

    def get_auth_token(self) -> str:
        realm = self._params["realm"]
        service = self._params["service"]
        url = f"{realm}?service={service}&scope=repository:{self._repository}:pull"
        response = requests.get(url)

        response.raise_for_status()

        return response.json().get('token')

@dataclasses.dataclass
class RegistryDigestResponse:
    digest: str = None
    expires: datetime.datetiem | None = None

class RateLimitedError(Exception):
    def __init__(self):
        super().__init__("Rate limited")

class BaseRegistry:
    def __init__(self, server):
        self._server = server
        self._base_url = f"https://{self._server}/v2"
        self.auth_token = None
        self._headers = {
                "Accept": "application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json"
        }
        self._not_before: datetime.datetime = None
        self._rate_limit_window_start: datetime.datetime = None
        self._rate_limit_window_length: int = None
        self._rate_limit_remaining: int = None
        self._rate_limit_limit: int = None

    def http_date_to_datetime(self, date_str: str):
        email.utils.parsedate_to_datetime(date_str)

    def include(self, image: str) -> bool:
        return image.split("/")[0] == self._server

    def www_authenticate(self, www_authenticate: WWWAuthenticate):
        self.auth_token = www_authenticate.get_auth_token()
        if self.auth_token is not None:
            self._headers["Authorization"] = f"Bearer {self.auth_token}"

    def get_image_digest(self, image: str) -> RegistryDigestResponse:
        if self._not_before is not None and datetime.datetime.now() < self._not_before:
            raise RateLimitedError()
        if self._rate_limit_remaining is not None and self._rate_limit_remaining == 0:
            if datetime.datetime.now() < (self._rate_limit_window_start + datetime.timedelta(seconds=self._rate_limit_window_length)):
                raise RateLimitedError()
        
        registry_image = RegistryImage.from_image(image, self._server)
        if registry_image.digest is not None:
            return RegistryDigestResponse(
                digest=registry_image.digest,
                expires=None)

        url = f"{self._base_url}/{registry_image.name}/manifests/{registry_image.tag}"
        
        response = requests.get(url, headers=self._headers)
        self.process_response_header(response)

        # need to authenticate
        if response.status_code == 401:
            if self.auth_token is not None:
                response.raise_for_status()
            www_authenticate_header_value = response.headers.get("www-authenticate")
            if www_authenticate_header_value is not None:
                self.www_authenticate(WWWAuthenticate(www_authenticate_header_value, registry_image.name))
                return_value = self.get_image_digest(image)
                del self._headers["Authorization"]
                self.auth_token = None
                return return_value

        response.raise_for_status()

        digest_response = RegistryDigestResponse()

        digest_response.digest = response.headers.get("Docker-Content-Digest")
        digest_response.expires = self.process_expires_header(response)

        return digest_response

    def process_expires_header(self, response) -> datetime.datetime | None:
        expires = response.headers.get("Expires")
        if expires is not None:
            return self.http_date_to_datetime(expires)
        return None

    def process_response_header(self, response):
        retry_after = response.headers.get("Retry-after")
        if retry_after is not None:
            try:
                retry_after_int = int(retry_after)
                self._not_before = datetime.datetime.now() + datetime.timedelta(seconds=retry_after_int)
            except:
                try:
                    self._not_before = self.http_date_to_datetime(retry_after)
                except:
                    logging.exception("Failed to get Retry-after when status code is 429 for url: %s", url)

        ratelimit_reset = response.headers.get("x-ratelimit-reset")                    
        if ratelimit_reset is None:
            ratelimit_reset = response.headers.get("x-ratelimit-reset")
        if ratelimit_reset is not None:
            self._rate_limit_window_start = datetime.datetime.now()
            try:
                self._rate_limit_window_length = int(ratelimit_reset)
            except:
                pass

        ratelimit_limit = response.headers.get("x-ratelimit-limit")
        if ratelimit_limit is None:
            ratelimit_limit = response.headers.get("x-ratelimit-limit")
        if ratelimit_limit is not None:
            if self._rate_limit_window_start is None:
                self._rate_limit_window_start = datetime.datetime.now()
            if self._rate_limit_window_length is None:
                length_str = ratelimit_limit.split(";")[1]
                self._rate_limit_window_length = int(length_str.split("=")[1])
            try:
                remaining = ratelimit_limit.split(";")[0]
                self._rate_limit_limit = int(remaining)
            except:
                pass

        ratelimit_remaining = response.headers.get("x-ratelimit-remaining")
        if ratelimit_remaining is None:
            ratelimit_remaining = response.headers.get("x-ratelimit-remaining")
        if ratelimit_remaining is not None:
            if self._rate_limit_window_start is None:
                self._rate_limit_window_start = datetime.datetime.now()
            if self._rate_limit_window_length is None:
                length_str = ratelimit_remaining.split(";")[1]
                self._rate_limit_window_length = int(length_str.split("=")[1])
            try:
                remaining = ratelimit_remaining.split(";")[0]
                self._rate_limit_remaining = int(remaining)
            except:
                pass



class DockerIO_Registry(BaseRegistry):
    def __init__(self):
        super().__init__("registry-1.docker.io")

    def include(self, repository: str) -> bool:
        return True

    def get_image_digest(self, image: str) -> str:
        if "/" not in image:
            image = f"library/{image}"

        return super().get_image_digest(image)

docker_io_registry = DockerIO_Registry()
