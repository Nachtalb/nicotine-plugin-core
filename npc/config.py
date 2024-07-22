"""Configuration module for Nicotine+ plugins

This module provides an advanced way to define the configuration of a plugin.
It allows for the definition of the settings once in a object oriented way and
automatically generates the settings and metasettings for the plugin.

Example:

    .. code-block:: python

        from npc import BasePlugin, String, Int, Float, Bool, ListString, Dropdown, Radio

        class Plugin(BasePlugin):

            class Config(BasePlugin.Config):
                 setting_1 = String("setting_1", "This is setting 1", "default")
                 setting_2 = Int("setting_2", "This is setting 2", 0)
                 setting_3 = Float("setting_3", "This is setting 3", 0.0, maximum=10.0, minimum=0.0, stepsize=0.1)
                 setting_4 = Bool("setting_4", "This is setting 4", False)
                 setting_5 = ListString("setting_5", "This is setting 5", ["item1", "item2", "item3"])
                 setting_6 = Dropdown("setting_6", "This is setting 6", ["option1", "option2", "option3"], "option1")
                 setting_7 = Radio("setting_7", "This is setting 7", ["option1", "option2", "option3"], "option1")

        ...

Note:
    It's recommended to inherit from :attr:`npc.base.BasePlugin.Config` to get
    the default config including the config for checking for updates.

In your plugins code it's recommended to use the :attr:`npc.base.BasePlugin.config`
attribute to access the configuration, instead of Nicotine+'s default
:attr:`npc.base.BasePlugin.settings`. This is because changes to
:attr:`npc.base.BasePlugin.settings` will not persist across sessions.
As well as the :attr:`npc.base.BasePlugin.config` attribute is type hinted,
thus providing better code completion and safety.

Note:
    When changing settings programmatically be e.g. ``plugin.config.setting_5.sort()``
    or ``plugin.config.setting_1 = "new value"`` the changes will not persist across sessions.
    You must call :meth:`BaseConfig.apply` to persist the changes.
    This is because Nicotine+ stores the settings during runtime in a all in
    one dict and persists this, without taking changes on the plugins instance
    into account. :meth:`BaseConfig.apply` will update the global configuration.
"""

from typing import TYPE_CHECKING, Any, Callable, List, Optional

from pynicotine.config import config as NConfig

from .types import MetaSetting, MetaSettings, Settings, SettingType

if TYPE_CHECKING:
    from .base import BasePlugin

__all__ = [
    "BaseConfig",
    "Field",
    "String",
    "TextView",
    "Text",
    "TextArea",
    "Int",
    "Float",
    "Number",
    "Bool",
    "Checkbox",
    "ListString",
    "Dropdown",
    "Radio",
]


class BaseConfig:
    """Base class for plugin configuration

    This class is used to define the configuration of a plugin.
    It automatically generates the settings and metasettings for the plugin
    given the fields defined as class attributes.

    Args:
        plugin (:obj:`BasePlugin`): The plugin instance that the configuration is attached to.

    Attributes:
        model_plugin (:obj:`BasePlugin`): The plugin instance that the configuration is attached to.
    """

    def __init__(self, plugin: "BasePlugin") -> None:
        self.model_plugin = plugin

        fields: dict[str, Field] = {}

        def get_fields(cls: Any) -> None:
            for name, setting in cls.__dict__.items():
                if isinstance(setting, Field):
                    if name in fields:
                        raise ValueError(f"Duplicate field name '{name}' in class '{cls.__name__}'")
                    fields[name] = setting
            for base in cls.__bases__:
                get_fields(base)

        get_fields(self.__class__)

        self.model_fields = fields

    def __getattribute__(self, name: str) -> Any:
        """Get the value of a setting"""
        try:
            fields = super().__getattribute__("model_fields")
        except AttributeError:
            fields = {}

        if name in fields:
            model_plugin = super().__getattribute__("model_plugin")
            value = fields[name].to_value(model_plugin)
            return value

        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set the value of a setting

        This will automatically persist the changes to the Nicotine+ global
        configuration.
        """
        try:
            fields = super().__getattribute__("model_fields")
        except AttributeError:
            fields = {}

        if name in fields:
            model_plugin = super().__getattribute__("model_plugin")
            value = fields[name].from_value(value, model_plugin)
            model_plugin.settings[name] = value
            return

        super().__setattr__(name, value)

    def model_settings(self) -> Settings:
        """Convert the model to settings

        Returns:
            :obj:`Settings`: The settings dict generated from the model.
        """
        return {name: setting.default for name, setting in self.model_fields.items()}

    def model_metasettings(self) -> MetaSettings:
        """Convert the model to metasettings

        Returns:
            :obj:`MetaSettings`: The metasettings dict generated from the model.
        """
        return {name: setting.metasetting() for name, setting in self.model_fields.items()}

    def apply(self) -> list[str]:
        """Persist the changes to the Nicotine+ global configuration

        Warning:
            You must call this method to persist the changes to the global
            configuration.

        Returns:
            :obj`list` of :obj:`str`: The names of the settings that were changed.
        """
        marker = object()
        changed = []
        plugin_name = self.model_plugin.plugin_name.lower()
        for name, value in self.model_plugin.settings.items():
            if value != NConfig.sections["plugins"][plugin_name].get(name, marker):
                NConfig.sections["plugins"][plugin_name][name] = value
                changed.append(name)
        return changed


class Field:
    """Base class for a configuration field

    This class is used to define a configuration field for a plugin.

    Args:
        name (:obj:`str`): The name of the setting.
        description (:obj:`str`): The description of the setting.
        default (:obj:`Any`): The default value of the setting.
        type (:obj:`SettingType`): The type of the setting.
        to_value (:obj:`Callable`[[Any, Field, BasePlugin], Any], optional): A
            function to get the value of the setting.
        from_value (:obj:`Callable`[[Any, Field, BasePlugin], Any], optional): A
            function to set the value of the setting.
        **options (:obj:`Any`): Additional options for the setting.

    Attributes:
        name (:obj:`str`): The name of the setting.
        description (:obj:`str`): The description of the setting.
        default (:obj:`Any`): The default value of the setting.
        type (:obj:`SettingType`): The type of the setting.
        options (:obj:`Any`): Additional options for the setting.
        to_value (:obj:`Callable`[[Any, Field, BasePlugin], Any], optional): A
            function to get the value of the setting.
        from_value_func (:obj:`Callable`[[Any, Field, BasePlugin], Any]): A
            function to set the value of the setting.
    """

    def __init__(
        self,
        name: str,
        description: str,
        default: Any,
        type: SettingType,
        to_value: Optional[Callable[[Any, "Field", "BasePlugin"], Any]] = None,
        from_value: Optional[Callable[[Any, "Field", "BasePlugin"], Any]] = None,
        **options: Any,
    ) -> None:
        self.name = name
        self.description = description
        self.default = default
        self.type = type
        self.options = options

        self.to_value_func = to_value
        self.from_value_func = from_value

    def metasetting(self) -> MetaSetting:
        """Convert the field to a metasetting

        Returns:
            :obj:`MetaSetting`: The metasetting generated from the field.
        """
        setting = MetaSetting(
            {
                "description": self.description,
                "type": self.type,
            }
        )
        if self.options:
            setting.update(self.options)  # type: ignore[typeddict-item]

        return setting

    def to_value(self, plugin: "BasePlugin") -> Any:
        """Get the value of the setting

        Args:
            plugin (:obj:`BasePlugin`): The plugin instance that the setting is attached to.

        Returns:
            :obj:`Any`: The value of the setting.
        """
        value = plugin.settings.get(self.name)
        if self.to_value_func:
            return self.to_value_func(value, self, plugin)
        return value

    def from_value(self, value: Any, plugin: "BasePlugin") -> Any:
        """Set the value of the setting

        Args:
            value (:obj:`Any`): The value to set the setting to.
            plugin (:obj:`BasePlugin`): The plugin instance that the setting is attached to.

        Returns:
            :obj:`Any`: The value of the setting.
        """
        if self.from_value_func:
            return self.from_value_func(value, self, plugin)
        return value


def String(name: str, description: str, default: str = "") -> str:
    """A configuration field for one line string input

    Args:
        name (:obj:`str`): The name of the setting.
        description (:obj:`str`): The description of the setting.
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".

    Returns:
        :obj:`str`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return Field(name, description, default, SettingType.STR)  # type: ignore[return-value]


def Int(
    name: str,
    description: str,
    default: int = 0,
    maximum: int = 9999999,
    minimum: int = 0,
    stepsize: int = 1,
) -> int:
    """A configuration field for a integer input

    Args:
        name (:obj:`str`): The name of the setting.
        description (:obj:`str`): The description of the setting.
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".
        maximum (:obj:`int`, optional): The maximum value of the setting.
            Defaults to 9999999.
        minimum (:obj:`int`, optional): The minimum value of the setting.
            Defaults to 0.
        stepsize (:obj:`int`, optional): The step size of the setting.
            Defaults to 1.

    Returns:
        :obj:`int`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return Field(name, description, default, SettingType.INT, maximum=maximum, minimum=minimum, stepsize=stepsize)  # type: ignore[return-value]


Number = Int


def Float(
    name: str,
    description: str,
    default: float = 0.0,
    maximum: float = 9999999.0,
    minimum: float = 0.0,
    stepsize: float = 0.1,
) -> float:
    """A configuration field for a float input

    Args:
        name (:obj:`str`): The name of the setting.
        description (:obj:`str`): The description of the setting.
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".
        maximum (:obj:`float`, optional): The maximum value of the setting.
            Defaults to 9999999.0.
        minimum (:obj:`float`, optional): The minimum value of the setting.
            Defaults to 0.0.
        stepsize (:obj:`float`, optional): The step size of the setting.
            Defaults to 0.1.

    Returns:
        :obj:`float`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return Field(name, description, default, SettingType.FLOAT, maximum=maximum, minimum=minimum, stepsize=stepsize)  # type: ignore[return-value]


def Bool(name: str, description: str, default: bool = False) -> bool:
    """A configuration field for a boolean checkbox

    Args:
        name (:obj:`str`): The name of the setting.
        description (:obj:`str`): The description of the setting.
        default (:obj:`str`, optional): The default value of the setting. Defaults to "".

    Returns:
        :obj:`bool`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return Field(name, description, default, SettingType.BOOL)  # type: ignore[return-value]


Checkbox = Bool


def TextView(name: str, description: str, default: str) -> str:
    """A configuration field for a multi-line text input

    Args:
        name (:obj:`str`): The name of the setting.
        description (:obj:`str`): The description of the setting.
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".

    Returns:
        :obj:`str`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return Field(name, description, default, SettingType.TEXTVIEW)  # type: ignore[return-value]


Text = TextArea = TextView


def Dropdown(name: str, description: str, options: List[str], default: str = "") -> str:
    """A configuration field for a dropdown input

    Args:
        name (:obj:`str`): The name of the setting.
        description (:obj:`str`): The description of the setting.
        options (:obj:`list` of :obj:`str`): The options for the dropdown.
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".

    Returns:
        :obj:`str`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return Field(name, description, default, SettingType.DROPDOWN, options=options)  # type: ignore[return-value]


def Radio(name: str, description: str, options: List[str], default: str = "") -> str:
    """A configuration field for a radio input

    Args:
        name (:obj:`str`): The name of the setting.
        description (:obj:`str`): The description of the setting.
        options (:obj:`list` of :obj:`str`): The options for the radio.
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".

    Returns:
        :obj:`str`: A field object which will be replaced by the value of the
            setting on config initialization
    """

    def to_value(value: Any, field: Field, plugin: "BasePlugin") -> str:
        return field.options["options"][value]  # type: ignore[no-any-return]

    def from_value(value: Any, field: Field, plugin: "BasePlugin") -> int:
        options = field.options["options"]
        return options.index(value)  # type: ignore[no-any-return]

    index = options.index(default) if default in options else 0

    return Field(
        name,
        description,
        index,
        SettingType.RADIO,
        options=options,
        to_value=to_value,
        from_value=from_value,
    )  # type: ignore[return-value]


def ListString(name: str, description: str, default: List[str] = []) -> List[str]:
    """A configuration field for managable list of strings input

    Args:
        name (:obj:`str`): The name of the setting.
        description (:obj:`str`): The description of the setting.
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".

    Returns:
        :obj:`list[str]`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return Field(name, description, default, SettingType.LIST_STRING)  # type: ignore[return-value]
