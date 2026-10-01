
import typing
from . import config, type_validator
import pydantic

class AppSettings(config.BaseCitadelSettings):
    model_config = config.SettingsConfigDict(env_prefix=config.ENV_PREFIX)

    log_level: typing.Literal["debug", "info", "warning", "error", "critical"] = pydantic.Field(default="info")
    tz: type_validator.Timezone = pydantic.Field(default="UTC", validation_alias=pydantic.AliasChoices("TZ", "citadel_tz"))
    api_enabled: bool = pydantic.Field(default=True)
    api_bind_addr: str = pydantic.Field(default="0.0.0.0")
    api_port: int = pydantic.Field(default=8000)

    @pydantic.field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: typing.Any) -> typing.Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


_app_settings: typing.Optional[AppSettings] = None

def app_settings() -> AppSettings:
    global _app_settings
    if _app_settings is None:
        _app_settings = AppSettings(_env_file=config.ENV_FILE)
    return _app_settings
