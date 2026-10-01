
import os
import re
import typing
import difflib
from pathlib import Path

import pydantic
from dotenv import dotenv_values
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "citadel_"
ENV_NESTED_DELIMITER = "__"
ENV_FILE: Path = Path(".env")
_NAME_REGEX = re.compile(r"[a-zA-Z0-9_-]+")

class ConfigError(Exception):
    pass

class BaseCitadelSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_nested_delimiter=ENV_NESTED_DELIMITER,
        extra="ignore",
    )

class Plugin(typing.Protocol):
    type_name: str
    settings_class: typing.Type[BaseCitadelSettings]

    def __init__(self, *, name: str, settings: typing.Any) -> None:
        pass

class Config:
    def __init__(self, *, plugins: typing.Iterable[typing.Any], env_file: typing.Optional[typing.Union[str, Path]] = ENV_FILE,):
        self._env_file = env_file
        self._plugins = list(plugins)
    
    def load(self):
        self._instances: typing.List[typing.Any] = []
        discovered = self.discover()
        for plugin in self._plugins:
            for name in sorted(discovered.get(plugin.type_name.lower(), {})):
                env_prefix = f"{ENV_PREFIX}{plugin.type_name}{ENV_NESTED_DELIMITER}{name}{ENV_NESTED_DELIMITER}"
                try:
                    settings = plugin.settings_class(_env_prefix=env_prefix, _env_file=self._env_file)
                except pydantic.ValidationError as e:
                    raise ConfigError(f"invalid configuration for \"{env_prefix}*\"\n{e}") from e
                self._instances.append(plugin(name=name, settings=settings))

    def _plugins_by_type_name(self) -> typing.Dict[str, typing.Any]:
        values: typing.Dict[str, typing.Any] = {}
        for p in self._plugins:
            type_name = getattr(p, "type_name", None)
            if type_name is None:
                raise ConfigError(f"{p.__name__} does not define type_name")
            settings_class = getattr(p, "settings_class", None)
            if not isinstance(settings_class, type) or not issubclass(settings_class, BaseCitadelSettings):
                raise ConfigError(f"{p.__name__} does not define a settings_class inheriting from BaseCitadelSettings")
            if _NAME_REGEX.fullmatch(type_name) is None or ENV_NESTED_DELIMITER in type_name:
                raise ConfigError(f"{p.__name__} type_name \"{type_name}\" is invalid")
            key = type_name.lower()
            if key in values:
                raise ConfigError(f"type_name \"{type_name}\" is used by {values[key].__name__} and {p.__name__}")
            values[key] = p
        return values

    def _env_keys(self) -> typing.Iterator[str]:
        yield from os.environ.keys()
        if self._env_file is not None:
            yield from dotenv_values(self._env_file).keys()

    def _valid_options(self, plugins) -> typing.Set[str]:
        return {name.lower() for name in plugins.settings_class.model_fields}

    def _split_env_name(self, key: str) -> typing.Tuple[str, str, str]:
        _, _, rest = key.lower().partition(ENV_PREFIX)
        type_name, delimiter, rest = rest.partition(ENV_NESTED_DELIMITER)
        if not delimiter:
            raise ConfigError(f"invalid environment variable \"{key}\", expected citadel_<type_name>__<name>__<option>")
        name, delimiter, option = rest.partition(ENV_NESTED_DELIMITER)
        if not delimiter or _NAME_REGEX.fullmatch(name) is None:
            raise ConfigError(f"invalid environment variable \"{key}\", expected citadel_<type_name>__<name>__<option>")
        return type_name, name, option

    def discover(self) -> typing.Dict[str, typing.Dict[str, typing.Set[str]]]:
        plugins_by_type_name = self._plugins_by_type_name()
        valid_type_names = ", ".join(sorted(plugins_by_type_name))

        values: typing.Dict[str, typing.Dict[str, typing.Set[str]]] = {}
        for key in self._env_keys():
            if not key.lower().startswith(ENV_PREFIX):
                continue

            rest = key[len(ENV_PREFIX):]
            if ENV_NESTED_DELIMITER not in rest:
                # not a plugin variable, global variables are handled by GlobalSettings
                continue

            type_name, name, option = self._split_env_name(key)
            if type_name not in plugins_by_type_name:
                raise ConfigError(f"invalid type name \"{type_name}\" in \"{key}\", choices are \"{valid_type_names}\"")

            values.setdefault(type_name, {}).setdefault(name, set()).add(option)

        for type_name, names in values.items():
            valid_options = self._valid_options(plugins_by_type_name[type_name])
            for name, options in names.items():
                for option in sorted(options - valid_options):
                    if option.replace("-", "_") in valid_options:
                        hint = f", option names cannot contain \"-\", did you mean \"{option.replace('-', '_')}\"?"
                    else:
                        suggestions = difflib.get_close_matches(option, sorted(valid_options), n=1)
                        hint = f", did you mean \"{suggestions[0]}\"?" if len(suggestions) > 0 else ""
                    raise ConfigError(
                        f"unknown option \"{option}\" in \"{ENV_PREFIX}{type_name}{ENV_NESTED_DELIMITER}"
                        f"{name}{ENV_NESTED_DELIMITER}{option}\", valid options are \"{', '.join(sorted(valid_options))}\"{hint}"
                    )

        return values


    @property
    def instances(self) -> typing.List[typing.Any]:
        return self._instances
