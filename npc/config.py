"""Configuration module for Nicotine+ plugins

This module provides an advanced way to define the configuration of a plugin.
It allows for the definition of the settings once in a object oriented way and
automatically generates the settings and metasettings for the plugin.

Example:

    .. code-block:: python

        from npc import BasePlugin, String, Int, Float, Bool, ListString, Dropdown, Radio

        class Plugin(BasePlugin):

            class Config(BasePlugin.Config):
                 setting_1 = String("This is setting 1", "default")
                 setting_2 = Int("This is setting 2", 0)
                 setting_3 = Float("This is setting 3", 0.0, maximum=10.0, minimum=0.0, stepsize=0.1)
                 setting_4 = Bool("This is setting 4", False)
                 setting_5 = ListString("This is setting 5", ["item1", "item2", "item3"])
                 setting_6 = Dropdown("This is setting 6", ["option1", "option2", "option3"], "option1")
                 setting_7 = Radio("This is setting 7", ["option1", "option2", "option3"], "option1")
                 setting_8 = File("This is setting 8", "", chooser=FileChooser.DIRECTORY)

        ...

Note:
    It's recommended to inherit from :attr:`npc.BasePlugin.Config` to get
    the default config including the config for checking for updates.

In your plugins code it's recommended to use the :attr:`npc.BasePlugin.config`
attribute to access the configuration, instead of Nicotine+'s default
:attr:`npc.BasePlugin.settings`. This is because changes to
:attr:`npc.BasePlugin.settings` will not persist across sessions.
As well as the :attr:`npc.BasePlugin.config` attribute is type hinted,
thus providing better code completion and safety.

Warning:
    When changing settings programmatically be e.g.:

    .. code-block:: python

        plugin.config.setting_5.sort()
        plugin.config.setting_1 = "new value"

    the changes will not persist across sessions.
    You must call :meth:`npc.BaseConfig.apply` to persist the changes.
    This is because Nicotine+ stores the settings during runtime in a all in
    one dict and persists this, without taking changes on the plugins instance
    into account. :meth:`npc.BaseConfig.apply` will update the global configuration.

    .. code-block:: python

        self.config.apply()
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Union

from pynicotine.config import config as NConfig

from .types import FileChooser, MetaSetting, MetaSettings, Settings, SettingType

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
        plugin (:obj:`npc.BasePlugin`): The plugin instance that the configuration is attached to.

    Attributes:
        model_plugin (:obj:`npc.BasePlugin`): The plugin instance that the configuration is attached to.
    """

    def __init__(self, plugin: "BasePlugin") -> None:
        self.model_plugin = plugin

        fields: dict[str, Field] = {}

        def get_fields(cls: Any) -> None:
            for name, field in cls.__dict__.items():
                if isinstance(field, Field):
                    if name in fields:
                        raise ValueError(f"Duplicate field name '{name}' in class '{cls.__name__}'")
                    if not field.name:
                        field.name = name
                    fields[name] = field
            for base in cls.__bases__:
                get_fields(base)

        get_fields(self.__class__)

        self.model_fields = fields

    def __getattribute__(self, name: str) -> Any:
        """Get the value of a setting or the attribute"""
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
        """Set the value of a setting or the attribute

        This will automatically persist the changes to the Nicotine+ global
        configuration.
        """
        try:
            fields = super().__getattribute__("model_fields")
        except AttributeError:
            fields = {}

        if name in fields:
            model_plugin = super().__getattribute__("model_plugin")
            value = fields[name].from_value(value)
            model_plugin.settings[name] = value
            return

        super().__setattr__(name, value)

    def model_settings(self) -> Settings:
        """Convert the model to settings

        Returns:
            :obj:`npc.types.Settings`: The settings dict generated from the model.
        """
        return {name: setting.from_value(setting.default) for name, setting in self.model_fields.items()}

    def model_metasettings(self) -> MetaSettings:
        """Convert the model to metasettings

        Returns:
            :obj:`npc.types.MetaSettings`: The metasettings dict generated from the model.
        """
        return {name: setting.metasetting() for name, setting in self.model_fields.items()}

    def apply(self) -> list[str]:
        """Persist the changes to the Nicotine+ global configuration

        Warning:
            You must call this method to persist the changes to the global
            configuration.

        Returns:
            :obj:`list` of :obj:`str`: The names of the settings that were changed.
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

    .. versionchanged:: 0.3.1 Removed `plugin` as a parameter for the
        :paramref:`from_value` function.

    .. versionchanged:: 0.4.0
        Added ``label`` parameter and made ``description`` optional.

    Args:
        label (:obj:`str`): The label of the setting.
        default (:obj:`typing.Any`): The default value of the setting.
        type (:obj:`npc.types.SettingType`): The type of the setting.
        description (:obj:`str`, optional): The description of the setting.
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.
            Does not need to be provided. By default it will use the variable name.
        to_value (:obj:`typing.Callable`, optional): A function to get the value of
            the setting.
        from_value (:obj:`typing.Callable`, optional): A function to set the value of
            the setting.
        **options (:obj:`typing.Any`): Additional options for the setting.

    Attributes:
        name (:obj:`str`): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.
        label (:obj:`str`): The label of the setting.
        description (:obj:`str`): The description of the setting.
        default (:obj:`typing.Any`): The default value of the setting.
        type (:obj:`npc.types.SettingType`): The type of the setting.
        options (:obj:`typing.Any`): Additional options for the setting.
        to_value_func (:obj:`typing.Callable`, optional): A function to get the
            value of the setting.
        from_value_func (:obj:`typing.Callable`, optional): A function to set the
            value of the setting.
    """

    def __init__(
        self,
        label: str,
        default: Any,
        type: SettingType,
        description: Optional[str] = "",
        name: Optional[str] = None,
        to_value: Optional[Callable[[Any, "Field", "BasePlugin"], Any]] = None,
        from_value: Optional[Callable[[Any, "Field"], Any]] = None,
        **options: Any,
    ) -> None:
        self.name = name or ""  # If not provided it will later be set by the BaseConfig
        self.label = label
        self.description = description
        self.default = default
        self.type = type
        self.options = options

        self.to_value_func = to_value
        self.from_value_func = from_value

    @property
    def metasettings_description(self) -> str:
        """Label for the settings dialog window

        The metasettings do not have separate labels and descriptions. Thus
        we just combine them with a newline.

        .. versionadded:: 0.4.0 Added property combining label and description

        Returns:
            :obj:`str`: The label of the setting.
        """
        if self.description:
            return f"{self.label}\n{self.description}"
        return self.label

    def metasetting(self) -> MetaSetting:
        """Convert the field to a metasetting

        Returns:
            :obj:`npc.types.MetaSetting`: The metasetting generated from the field.
        """
        setting = MetaSetting(
            {
                "description": self.metasettings_description,
                "type": self.type,
            }
        )
        if self.options:
            setting.update(self.options)  # type: ignore[typeddict-item]

        return setting

    def to_value(self, plugin: "BasePlugin") -> Any:
        """Get the value of the setting

        Args:
            plugin (:obj:`npc.BasePlugin`): The plugin instance that the setting is attached to.

        Returns:
            :obj:`typing.Any`: The value of the setting.
        """
        value = plugin.settings.get(self.name)
        if self.to_value_func:
            return self.to_value_func(value, self, plugin)
        return value

    def from_value(self, value: Any) -> Any:
        """Set the value of the setting

        .. versionchanged:: 0.3.1 Removed `plugin` as a parameter.

        Args:
            value (:obj:`typing.Any`): The value to set the setting to.

        Returns:
            :obj:`typing.Any`: The value of the setting.
        """
        if self.from_value_func:
            return self.from_value_func(value, self)
        return value


def String(label: str, description: Optional[str] = "", default: str = "", name: Optional[str] = None) -> str:
    """A configuration field for one line string input

    .. versionchanged:: 0.4.0
       Added ``label`` parameter and made ``description`` optional.

    Args:
        label (str): The label of the setting.
        description (:obj:`str`, optional): The description of the setting. Defaults to "".
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.

    Returns:
        :obj:`str`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return Field(label=label, description=description, default=default, type=SettingType.STR, name=name)  # type: ignore[return-value]


def Int(
    label: str,
    description: Optional[str] = "",
    default: int = 0,
    name: Optional[str] = None,
    maximum: int = 9999999,
    minimum: int = 0,
    stepsize: int = 1,
) -> int:
    """A configuration field for a integer input

    .. versionchanged:: 0.4.0
       Added ``label`` parameter and made ``description`` optional.

    Note:
        Available aliases: ``Number``

    Args:
        label (str): The label of the setting.
        description (:obj:`str`, optional): The description of the setting. Defaults to "".
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.
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
    return Field(
        label=label,
        description=description,
        default=default,
        type=SettingType.INT,
        name=name,
        maximum=maximum,
        minimum=minimum,
        stepsize=stepsize,
    )  # type: ignore[return-value]


Number = Int


def Float(
    label: str,
    description: Optional[str] = "",
    default: float = 0.0,
    name: Optional[str] = None,
    maximum: float = 9999999.0,
    minimum: float = 0.0,
    stepsize: float = 0.1,
) -> float:
    """A configuration field for a float input

    .. versionchanged:: 0.4.0
       Added ``label`` parameter and made ``description`` optional.

    Args:
        label (str): The label of the setting.
        description (:obj:`str`, optional): The description of the setting. Defaults to "".
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.
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
    return Field(
        label=label,
        description=description,
        default=default,
        type=SettingType.FLOAT,
        name=name,
        maximum=maximum,
        minimum=minimum,
        stepsize=stepsize,
    )  # type: ignore[return-value]


def Bool(label: str, description: Optional[str] = "", default: bool = False, name: Optional[str] = None) -> bool:
    """A configuration field for a boolean checkbox

    .. versionchanged:: 0.4.0
       Added ``label`` parameter and made ``description`` optional.

    Note:
        Available aliases: ``Checkbox``

    Args:
        label (str): The label of the setting.
        description (:obj:`str`, optional): The description of the setting. Defaults to "".
        default (:obj:`str`, optional): The default value of the setting. Defaults to "".
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.

    Returns:
        :obj:`bool`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return Field(label=label, description=description, default=default, type=SettingType.BOOL, name=name)  # type: ignore[return-value]


Checkbox = Bool


def TextView(label: str, description: Optional[str] = "", default: str = "", name: Optional[str] = None) -> str:
    """A configuration field for a multi-line text input

    .. versionchanged:: 0.4.0
       Added ``label`` parameter and made ``description`` optional.

    Note:
        Available aliases: :data:`Text`, :data:`TextArea`

    Args:
        label (str): The label of the setting.
        description (:obj:`str`, optional): The description of the setting. Defaults to "".
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.

    Returns:
        :obj:`str`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return Field(label=label, description=description, default=default, type=SettingType.TEXTVIEW, name=name)  # type: ignore[return-value]


Text = TextArea = TextView


def Dropdown(
    label: str, description: Optional[str] = "", options: List[str] = [], default: str = "", name: Optional[str] = None
) -> str:
    """A configuration field for a dropdown input

    .. versionchanged:: 0.4.0
       Added ``label`` parameter and made ``description`` optional.

    Args:
        label (str): The label of the setting.
        description (:obj:`str`, optional): The description of the setting. Defaults to "".
        options (:obj:`list` of :obj:`str`): The options for the dropdown.
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.

    Returns:
        :obj:`str`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return Field(
        label=label, description=description, default=default, type=SettingType.DROPDOWN, options=options, name=name
    )  # type: ignore[return-value]


def Radio(
    label: str, description: Optional[str] = "", options: List[str] = [], default: str = "", name: Optional[str] = None
) -> str:
    """A configuration field for a radio input

    .. versionchanged:: 0.4.0
       Added ``label`` parameter and made ``description`` optional.

    Args:
        label (str): The label of the setting.
        description (:obj:`str`, optional): The description of the setting. Defaults to "".
        options (:obj:`list` of :obj:`str`): The options for the radio.
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.

    Returns:
        :obj:`str`: A field object which will be replaced by the value of the
            setting on config initialization
    """

    def to_value(value: Any, field: Field, plugin: "BasePlugin") -> str:
        return field.options["options"][value]  # type: ignore[no-any-return]

    def from_value(value: Any, field: Field) -> int:
        options = field.options["options"]
        return options.index(value)  # type: ignore[no-any-return]

    index = options.index(default) if default in options else 0

    return Field(
        label=label,
        description=description,
        default=index,
        type=SettingType.RADIO,
        options=options,
        name=name,
        to_value=to_value,
        from_value=from_value,
    )  # type: ignore[return-value]


def ListString(
    label: str, description: Optional[str] = "", default: List[str] = [], name: Optional[str] = None
) -> List[str]:
    """A configuration field for managable list of strings input

    .. versionchanged:: 0.4.0
       Added ``label`` parameter and made ``description`` optional.

    Args:
        label (str): The label of the setting.
        description (:obj:`str`, optional): The description of the setting. Defaults to "".
        default (:obj:`str`, optional): The default value of the setting.
            Defaults to "".
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.

    Returns:
        :obj:`list` of :obj:`str`: A field object which will be replaced by
            the value of the setting on config initialization
    """
    return Field(label=label, description=description, default=default, type=SettingType.LIST_STRING, name=name)  # type: ignore[return-value]


def File(
    label: str,
    description: Optional[str] = "",
    default: Union[str, Path] = "",
    chooser: FileChooser = FileChooser.FILE,
    name: Optional[str] = None,
) -> Path:
    """A configuration field for a file input

    Will handle files as :obj:`pathlib.Path` objects instead of strings.

    .. versionadded:: 0.3.0

    .. versionchanged:: 0.4.0
       Added ``label`` parameter and made ``description`` optional.

    Args:
        label (str): The label of the setting.
        description (:obj:`str`, optional): The description of the setting. Defaults to "".
        default (:obj:`str` | :obj:`pathlib.Path`, optional): The default value of the setting.
            Defaults to "".
        file_chooser (:obj:`npc.types.FileChooser`, optional): The file chooser type.
            Defaults to :attr:`npc.types.FileChooser.FILE`.
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.

    Returns:
        :obj:`pathlib.Path`: A field object which will be replaced by the value of the
            setting on config initialization
    """

    def to_value(value: Any, field: Field, plugin: "BasePlugin") -> Path:
        return Path(value)

    def from_value(value: Any, field: Field) -> str:
        if isinstance(value, str):
            return value  # Prevents "" resolving to Path("") which is CWD
        return str(value)

    return Field(
        label=label,
        description=description,
        default=default,
        type=SettingType.FILE,
        name=name,
        chooser=chooser,
        to_value=to_value,
        from_value=from_value,
    )  # type: ignore[return-value]


def Folder(
    label: str, description: Optional[str] = "", default: Union[str, Path] = "", name: Optional[str] = None
) -> Path:
    """A configuration field for a folder input

    Will handle folders as :obj:`pathlib.Path` objects instead of strings.

    .. versionadded:: 0.3.1 Quick alias for :func:`File` with :attr:`npc.types.FileChooser.FOLDER`

    .. versionchanged:: 0.4.0
       Added ``label`` parameter and made ``description`` optional.

    Args:
        label (str): The label of the setting.
        description (:obj:`str`, optional): The description of the setting. Defaults to "".
        default (:obj:`str` | :obj:`pathlib.Path`, optional): The default value of the setting.
            Defaults to "".
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.

    Returns:
        :obj:`pathlib.Path`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return File(label=label, description=description, default=default, chooser=FileChooser.FOLDER, name=name)


Directory = Folder


def Image(
    label: str, description: Optional[str] = "", default: Union[str, Path] = "", name: Optional[str] = None
) -> Path:
    """A configuration field for an image input

    Will handle images as :obj:`pathlib.Path` objects instead of strings.

    .. versionadded:: 0.3.1 Quick alias for :func:`File` with :attr:`npc.types.FileChooser.IMAGE`

    .. versionchanged:: 0.4.0
       Added ``label`` parameter and made ``description`` optional.

    Args:
        label (str): The label of the setting.
        description (:obj:`str`, optional): The description of the setting. Defaults to "".
        default (:obj:`str` | :obj:`pathlib.Path`, optional): The default value of the setting.
            Defaults to "".
        name (:obj:`str`, optional): The name of the setting in the :attr:`npc.BasePlugin.settings` dict.

    Returns:
        :obj:`pathlib.Path`: A field object which will be replaced by the value of the
            setting on config initialization
    """
    return File(label=label, description=description, default=default, chooser=FileChooser.IMAGE, name=name)
