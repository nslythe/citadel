
import os
from dotenv import load_dotenv
import re
from string import Template
from dataclasses import dataclass
import typing
from pydantic import TypeAdapter

@dataclass
class ConfigValue:
    name: str
    value: str

class ConfigNull:
    pass

def getenv(name: str, default = None):
    for e in os.environ:
        if e.lower() == name.lower():
            return os.getenv(e)
    return default

@dataclass
class ConfigVariable:
    def __init__(self, *, global_config: GlobalConfig, type_name: str, name: str):
        self._type_name = type_name
        self._name = name
        self._variables: typing.List[ConfigValue] = []
        self.global_config = global_config

    def add_variable(self, name: str, value: str):
        self._variables.append(ConfigValue(
            name=name,
            value=value
        ))

    @property
    def variables(self) -> typing.List[ConfigValue]:
        return self._variables

    def get(self, name: str, *, default = ConfigNull, value_type = None) -> typing.Any:
        for v in self._variables:
            if v.name == name:
                if value_type is None and default == ConfigNull:
                    return v.value
                _t = value_type
                if _t is None:
                    _t = type(default)
                return TypeAdapter(_t).validate_python(v.value)
        if default == ConfigNull:
            raise Exception("variable not set")
        return default

    @property
    def type_name(self) -> str:
        return self._type_name

    @property
    def name(self) -> str:
        return self._name

class GlobalConfig:
    def __init__(self):
        self.tz = getenv("TZ", "UTC")
        self.log_level = getenv("citadel_log_level", "info").upper()

class Config:
    def __init__(self, *, valid_types_name):
        self._variables: typing.List[ConfigVariable] = []
        self._variable_prefix = "citadel_"
        self._valid_type_names = valid_types_name
        self.global_config = GlobalConfig()
        
        for v in self._valid_type_names:
            if "_" in v:
                raise Exception(f"In config initialization valid_types_name list is invalid {v}")

        self._variable_regex_section_str = Template("(?P<$name>[a-zA-Z0-9-]+)")
        valid_types_name_regex_str = "|".join(self._valid_type_names)
        self._variable_regex_str = self._variable_prefix + \
            f"(?P<type_name>({valid_types_name_regex_str}))" + "_" +\
            self._variable_regex_section_str.safe_substitute(name="name") + "_" +\
            self._variable_regex_section_str.safe_substitute(name="config_name")
        self._variable_regex = re.compile(self._variable_regex_str)

        load_dotenv()

        for e in os.environ.keys():
            key_name = e.lower()
            if key_name.startswith(self._variable_prefix):
                match = self._variable_regex.match(key_name)
                if match is not None:
                    if match.group("type_name") not in self._valid_type_names:
                        _valid_type_names_list_str = ", ".join(self._valid_type_names)
                        raise Exception(f"Invalid type name in {key_name} choices are \"{_valid_type_names_list_str}\"")

                    value = os.getenv(e)              

                    confi_element = None
                    for v in self._variables:
                        if v.type_name == match.group("type_name") and v.name == match.group("name"):
                            confi_element = v

                    if confi_element is None:
                        confi_element = ConfigVariable(
                            global_config=self.global_config,
                            type_name=match.group("type_name"),
                            name=match.group("name")
                        )
                        self._variables.append(confi_element)
                
                    confi_element.add_variable(match.group("config_name"), value)

    @property
    def variables(self) -> typing.List[ConfigVariable]:
        return self._variables

    def get_variables(self, *, type_name: str = None) -> typing.List[ConfigVariable]:
        values = []
        for v in self._variables:
            add = True

            if type_name is not None:
                if v.type_name != type_name:
                    add = False

            if add:
                values.append(v)
        return values

