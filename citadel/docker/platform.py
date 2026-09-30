

class Platform:
    def __init__(self, p):
        self._docker_platform = p
        keys = list(self._docker_platform.keys())
        for k in keys:
            self._docker_platform[k.lower()] = self._docker_platform[k]

    @property
    def architecture(self) -> str:
        return self._docker_platform["architecture"].lower().replace("amd64", "x86_64")

    @property
    def os(self) -> str:
        return self._docker_platform["os"].lower()

    def compare(self, b: 'Platform') -> bool:
        return self.architecture == b.architecture and self.os == b.os
