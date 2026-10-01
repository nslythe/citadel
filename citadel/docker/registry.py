

import requests

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
        if "/" not in self._repository:
            self._repository = f"library/{self._repository}"

        realm = self._params["realm"]
        service = self._params["service"]
        url = f"{realm}?service={service}&scope=repository:{self._repository}:pull"
        response = requests.get(url)
        if not response.ok:
            raise Exception()
        return response.json().get('token')

class BaseRegistry:
    def __init__(self, server):
        self._server = server
        self._base_url = f"https://{self._server}/v2"
        self.auth_token = None
        self._headers = {
                "Accept": "application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json"
        }

    def include(self, image: str) -> bool:
        return image.split("/")[0] == self._server

    def www_authenticate(self, www_authenticate: WWWAuthenticate):
        self.auth_token = www_authenticate.get_auth_token()
        if self.auth_token is not None:
            self._headers["Authorization"] = f"Bearer {self.auth_token}"

    def get_image_digest(self, image: str) -> str:
        components = image.split(":")
        path_components = image.split("/")
        image_name = image
        registry_name = path_components[0]

        image_tag = "latest"
        if len(components) > 1:
            image_name = components[0]
            image_tag = components[1]

        image_name = "/".join(image_name.split("/")[1:])

        url = f"{self._base_url}/{image_name}/manifests/{image_tag}"
        
        response = requests.get(url, headers=self._headers)
        if response.status_code == 401:
            if self.auth_token is not None:
                response.raise_for_status()
            www_authenticate_header_value = response.headers.get("www-authenticate")
            if www_authenticate_header_value is not None:
                self.www_authenticate(WWWAuthenticate(www_authenticate_header_value, registry_name))
                self.get_image_digest()

        response.raise_for_status()
        header_digest =  response.headers.get("Docker-Content-Digest")
        return header_digest

class DockerIO_Registry(BaseRegistry):
    def __init__(self):
        self._base_url = "https://registry-1.docker.io/v2"

    def include(self, repository: str) -> bool:
        return True

    def get_image_digest(self, repository: str, tag: str) -> str:
        if "/" not in repository:
            repository = f"library/{repository}"

        return super().get_image_digest(repository, tag)

docker_hub_registries = {
    "registry.docker.io": DockerIO_Registry(),
    "docker.io": DockerIO_Registry()
}
