
import urllib.parse
from zoneinfo import ZoneInfo
import typing
import pydantic
import cron_converter

def validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (KeyError, ValueError) as e:
        raise ValueError(f"unknown timezone \"{value}\"") from e
    return value

def validate_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("must be an absolute http or https url")
    return value

def validate_docker_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if not parsed.scheme or not (parsed.netloc or parsed.path):
        raise ValueError("must be an absolute docker url, for example tcp://host:2375 or unix:///var/run/docker.sock")
    return value


def validate_cron(value: str) -> str:
    cron_converter.Cron().from_string(value)
    return value

Timezone = typing.Annotated[str, pydantic.AfterValidator(validate_timezone)]
HttpUrl = typing.Annotated[str, pydantic.AfterValidator(validate_url)]
DockerUrl = typing.Annotated[str, pydantic.AfterValidator(validate_docker_url)]
CronExpression = typing.Annotated[str, pydantic.AfterValidator(validate_cron)]
