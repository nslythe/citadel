
import pydantic
import typing
import datetime
import requests
from zoneinfo import ZoneInfo

from . import base_trigger
from ..watcher import base_watcher, swarm_watcher
from citadel.config import config, type_validator
import logging

# doc for webhook
# https://birdie0.github.io/discord-webhooks-guide/structure/username.html

class DiscordWebhookFooter(pydantic.BaseModel):
    text: str
    icon_url: str | None = pydantic.Field(default=None)

class DiscordWebhookImage(pydantic.BaseModel):
    url: str

class DiscordWebhookField(pydantic.BaseModel):
    name: str
    value: str
    inline: bool | None = pydantic.Field(default=None)

class DiscordWebhookAuthor(pydantic.BaseModel):
    name: str
    url: str | None = pydantic.Field(default=None)
    icon_url: str | None = pydantic.Field(default=None)

class DiscordWebhookAllowMentions(pydantic.BaseModel):
    parse: typing.Literal["everyone", "users", "roles"]
    users: typing.List[str] = pydantic.Field(default_factory=list)
    roles: typing.List[str] = pydantic.Field(default_factory=list)

class DiscordWebhookEmbed(pydantic.BaseModel):
    title: str
    description: str | None = pydantic.Field(default=None)
    color: int | None = pydantic.Field(default=None)
    author: DiscordWebhookAuthor | None = pydantic.Field(default=None)
    url: str | None = pydantic.Field(default=None)
    fields: typing.List[DiscordWebhookField] = pydantic.Field(default_factory=list)
    image: DiscordWebhookImage | None = pydantic.Field(default=None)
    thumbnail: DiscordWebhookImage | None = pydantic.Field(default=None)
    footer: DiscordWebhookFooter | None = pydantic.Field(default=None)
    timestamp: datetime.datetime | None = pydantic.Field(default=None)
    # poll
    tts: bool = pydantic.Field(default=False)
    allowed_mentions: DiscordWebhookAllowMentions | None = pydantic.Field(default=None)

class DiscordWebhookMessage(pydantic.BaseModel):
    content: str
    username: str | None = pydantic.Field(default=None)
    avatar_url: str | None = pydantic.Field(default=None)
    embeds: typing.List[DiscordWebhookEmbed] = pydantic.Field(default_factory=list)

class DiscordSettings(base_trigger.BaseTriggerSettings):
    webhook: type_validator.HttpUrl = pydantic.Field()

class Discord(base_trigger.BaseTriggerMultiMessage):
    type_name = "discord"
    settings_class = DiscordSettings

    def __init__(self, *, name: str, settings: DiscordSettings):
        super().__init__(name=name, settings=settings)
        self._webhook = settings.webhook
        self._timezone_name = settings.tz if settings.tz is not None else config.global_settings().tz
        self._timezone = ZoneInfo(self._timezone_name)

    def do_trigger(self, checks: typing.List[base_watcher.BaseWatcherCheck]):
        logging.info("discord sending webhook")
        data = DiscordWebhookMessage(
            username="citadel",
            content="New docker image updated"
        )
        for c in checks:
            prefix = "Container"
            if isinstance(c, swarm_watcher.SwarmWatcherCheck):
                prefix = "Service"
            data.embeds.append(DiscordWebhookEmbed(
                color=12236346,
                title=f"{prefix} : {c} need update",
                timestamp=datetime.datetime.now(tz=self._timezone)
            ))

        response = requests.post(self._webhook, data=data.model_dump_json(), headers={
            "Content-Type": "application/json"
        })
        response.raise_for_status()
