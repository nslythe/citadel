

import requests
import citadel.docker.node as node

class WWWAuthenticate:
    def __init__(self, header_value):
        self._header_value = header_value
        self._scheme = self._header_value.split(" ")[0]
        www_authenticate_params_components = "".join(self._header_value.split(" ")[1:]).split(",")
        self._params = {}
        for wa in www_authenticate_params_components:
            wa_components = wa.split("=")
            self._params[wa_components[0]] = wa_components[1].replace("\"", "")

    def get_auth_token(self, repository: str) -> str:
        if "/" not in repository:
            repository = f"library/{repository}"

        realm = self._params["realm"]
        service = self._params["service"]
        url = f"{realm}?service={service}&scope=repository:{repository}:pull"
        response = requests.get(url)
        if not response.ok:
            raise Exception()
        return response.json().get('token')


class BaseRegistry:
    def __init__(self, url):
        self._base_url = f"https://{url}/v2"

    def get_image_digest(self, repository: str, tag: str) -> str:
        auth_token = None

        url = f"{self._base_url}/{repository}/manifests/{tag}"
        
        headers = {
                "Accept": "application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json"
        }

        response = requests.options(url)
        www_authenticate_header_value = response.headers.get("www-authenticate")
        if www_authenticate_header_value is not None:
            www_authenticate = WWWAuthenticate(www_authenticate_header_value)
            auth_token = www_authenticate.get_auth_token(repository)

        if auth_token is not None:
            headers["Authorization"] = f"Bearer {auth_token}"

        response = requests.get(url, headers=headers)
        if response.status_code == 401:
            www_authenticate_header_value = response.headers.get("www-authenticate")
            if www_authenticate_header_value is not None:
                www_authenticate = WWWAuthenticate(www_authenticate_header_value)
                auth_token = www_authenticate.get_auth_token(repository)
                if auth_token is not None:
                    headers["Authorization"] = f"Bearer {auth_token}"
                response = requests.get(url, headers=headers)

        response.raise_for_status()
        header_digest =  response.headers.get("Docker-Content-Digest")
        return header_digest

class DockerIO_Registry(BaseRegistry):
    def __init__(self):
        self._base_url = "https://registry-1.docker.io/v2"

    def get_image_digest(self, repository: str, tag: str) -> str:
        if "/" not in repository:
            repository = f"library/{repository}"

        return super().get_image_digest(repository, tag)

known_registries = {
    "registry.docker.io": DockerIO_Registry(),
    "docker.io": DockerIO_Registry(),
    "docker.slythe.net": BaseRegistry("docker.slythe.net"),
    "ghcr.io": BaseRegistry("ghcr.io"),
}

def get_image_digest(image_url: str) -> str:
        components = image_url.split(":")

        image = components[0]
        image_tag = "latest"
        if len(components) > 1:
            image_tag = image_url.split(":")[1]

        registry_name = image.split("/")[0]

        if registry_name not in known_registries.keys() and "." in registry_name:
            raise Exception(f"registry {registry_name} not configured")

        if registry_name not in known_registries.keys():
            registry_name = "registry.docker.io"
        else:
            image = "/".join(image.split("/")[1:])

        return known_registries[registry_name].get_image_digest(image, image_tag)
