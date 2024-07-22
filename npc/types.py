"""This module contains all the types used by this plugin system. It also provides
some enums and typeddict that define undocumdent Nicotine+ features. As they are
undocumented in by Nicotine+ itself, they may be subject to change in the future.
"""

from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Protocol, Tuple, TypedDict, TypeVar, Union

__all__ = [
    "LogLevel",
    "PluginConfig",
    "Readable",
    "SettingsDiff",
    "SettingType",
    "SettingTypes",
    "Settings",
    "FileChooser",
    "RequiredMetaSetting",
    "MetaSetting",
    "MetaSettings",
    "AnyInputCallback",
    "DefaultCallback",
    "Callback",
    "ReturnCode",
    "CommandGroup",
    "CommandInterface",
    "CommandRequired",
    "Command",
    "Commands",
    "LegacyCommands",
]

# === Nicotine+ ===


class LogLevel(str, Enum):
    """ "Log Levels" for the logger. They just prefix the message with [LEVEL]

    Attributes:
        DEFAULT: Default log level
        DOWNLOAD: Log level for download messages
        UPLOAD: Log level for upload messages
        SEARCH: Log level for search messages
        CHAT: Log level for chat messages
        CONNECTION: Log level for connection messages
        MESSAGE: Log level for message messages
        TRANSFER: Log level for transfer messages
        MISCELLANEOUS: Log level for miscellaneous messages
    """

    DEFAULT = "default"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    SEARCH = "search"
    CHAT = "chat"
    CONNECTION = "connection"
    MESSAGE = "message"
    TRANSFER = "transfer"
    MISCELLANEOUS = "miscellaneous"


# === PLUGIN ===


class PluginConfig(TypedDict, total=False):
    """Plugin configuration via PLUGININFO file

    Attributes:
        name (:obj:`str`): Name of the plugin
        version (:obj:`str`): Version of the plugin
        author (:obj:`list` of :obj:`str`): List of authors of the plugin
        description (:obj:`str`): Description of the plugin
        prefix (:obj:`str`): Prefix for the plugin commands. Not required
        repository (:obj:`str`): GitHub repository of the plugin either as a URL or in the format "user/repo"
    """

    name: str
    description: str
    author: List[str]
    version: str
    prefix: str
    repository: str


# === PLUGIN API ===

T = TypeVar("T", covariant=True)
"""Type variable for the return type of the read method."""


class Readable(Protocol, Generic[T]):
    """Protocol for objects that can be read from."""

    def read(self, size: int = -1) -> T:
        """Read from the object

        Args:
            size (:obj:`int`): Number of bytes to read. If not provided, the whole object is read.

        Returns:
            :obj:`T`: Read data
        """
        ...


class SettingsDiff(TypedDict):
    """Difference between two settings

    Attributes:
        before (:obj:`Dict[str, Any]`): Old settings
        after (:obj:`Dict[str, Any]`): New settings
    """

    before: Dict[str, Any]
    after: Dict[str, Any]


# === SETTINGS ===


class SettingType(str, Enum):
    """Plugin settings types

    Attributes:
        INT: Text input that only accepts integers
            Accepts additional parameters: minimum, maximum, stepsize
        FLOAT: Text input that only accepts floats (2 decimal places)
            Accepts additional parameters: minimum, maximum, stepsize
        BOOL: Checkbox input
        RADIO: Radio button input
            Accepts additional parameters: options
        DROPDOWN: Dropdown menu input
            Accepts additional parameters: options
        STR: Text input that accepts any string
        TEXTVIEW: Text input for multiline text
        LIST_STRING: Extendable list of strings
        FILE: File input
            Accepts additional parameters: chooser
    """

    INT = "int"  # same as "integer" or "float"
    FLOAT = "float"  # same as "integer" or "int"
    BOOL = "bool"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    STR = "str"  # same as "string"
    TEXTVIEW = "textview"
    LIST_STRING = "list string"
    FILE = "file"


SettingTypes = Union[str, int, float, bool, List[str]]
"""Union of all setting types"""

Settings = Dict[str, SettingTypes]
"""Dictionary of settings with their names as keys and their values as values."""


class FileChooser(str, Enum):
    """File chooser types

    Attributes:
        FILE: File chooser for selecting a single file
        FOLDER: File chooser for selecting a folder
        IMAGE: File chooser for selecting an image
    """

    FILE = "file"
    FOLDER = "folder"
    IMAGE = "image"


class RequiredMetaSetting(TypedDict):
    """Required field definition for a setting

    Attributes:
        description (:obj:`str`): Description of the setting
        type (:obj:`SettingType`): Type of the setting
    """

    description: str
    type: SettingType


class MetaSetting(RequiredMetaSetting, total=False):
    """Field definition for a setting

    Attributes:
        description (:obj:`str`): Description of the setting
        type (:obj:`SettingType`): Type of the setting
        options (:obj:`list` of :obj:`str`): Options for :attr:`SettingType.RADIO` and :attr:`SettingType.DROPDOWN`
        minimum (:obj:`int` | :obj:`float`): Minimum value for :attr:`SettingType.INT` and :attr:`SettingType.FLOAT`
        maximum (:obj:`int` | :obj:`float`): Maximum value for :attr:`SettingType.INT` and :attr:`SettingType.FLOAT`
        stepsize (:obj:`int` | :obj:`float`): Step size for :attr:`SettingType.INT` and :attr:`SettingType.FLOAT`
        chooser (:obj:`FileChooser`): File chooser type for :attr:`SettingType.FILE`
    """

    options: List[str]
    minimum: Union[int, float]
    maximum: Union[int, float]
    stepsize: Union[int, float]
    chooser: FileChooser


MetaSettings = dict[str, MetaSetting]
"""Dictionary of settings with their names as keys and their definitions as values."""

# === COMMANDS ===


class ReturnCode(Enum):
    """Return codes for command callbacks.

    Attributes:
        BREAK: Don't give other plugins the event, do let Nicotine+ process it further
        ZAP: Don't give other plugins the event, don't let Nicotine+ process it further
        PASS: Do give other plugins the event, do let Nicotine+ process it further
    """

    BREAK = 0
    ZAP = 1
    PASS = 2


class CommandGroup(str, Enum):
    """Existing command groups.

    Command groups are used to group commands together in the command help window (via /help or the ? button).

    Attributes:
        CHAT: Chat commands (e.g. /away)
        CHAT_ROOMS: Chat room commands (e.g. /join <room>)
        PRIVATE_CHAT: Private chat commands (e.g. /pm <user>)
        USERS: User commands (e.g. /buddy <user>)
        NETWORK_FILTERS: Network filter commands (e.g. /ban <user or ip>)
        SHARES: Commands for managing shared files / folders (e.g. /rescan [force|rebuild])
        SEARCH_FILES: Search files commands (e.g. /search <query>)
    """

    CHAT = "CHAT"
    CHAT_ROOMS = "CHAT_ROOMS"
    PRIVATE_CHAT = "PRIVATE_CHAT"
    USERS = "USERS"
    NETWORK_FILTERS = "NETWORK_FILTERS"
    SHARES = "SHARES"
    SEARCH_FILES = "SEARCH_FILES"


class CommandInterface(str, Enum):
    """Command interfaces.

    Command interfaces are used to specify where a command can be used.

    Attributes:
        CHATROOM: Command can be used in a chatroom.
        PRIVATE_CHAT: Command can be used in a private chat.
        CLI: Command can be used in the command line interface.
    """

    CHATROOM = "chatroom"
    PRIVATE_CHAT = "private_chat"
    CLI = "cli"


AnyInputCallback = Callable[..., Optional[ReturnCode]]
"""Callback for commands where args get autoparsed"""

DefaultCallback = Callable[[str, Optional[str], Optional[str]], Optional[ReturnCode]]
"""Callback function for a command.

Arguments:
    args (:obj:`str`): List of arguments passed to the command as a single string
    room (:obj:`str`, optional): Room name where the command was called
    user (:obj:`str, optional): User name who called the command

Returns:
    ReturnCode or None which is equivalent to ReturnCode.PASS
"""

Callback = Union[AnyInputCallback, DefaultCallback]


class CommandRequired(TypedDict):
    """Required command fields.

    Attributes:
        callback (:obj:`Callback`): Callback function that is called when the command is executed.
        description (:obj:`str`): Description of the command. Shown in the command help window
    """

    callback: Callback
    description: str


class Command(CommandRequired, total=False):
    """Command fields.

    Note:
        Parameters are checked for if you use this syntax:

        .. code-block:: text

            /command <argument> <choice 1|choice 2>

        as in the following example:

        .. code-block:: python

            @command(parameters = ["<argument>", "<choice 1|choice 2>"])
            def do_something(self, argument: str, choice: str) -> None:
                ...

        Where ``<`` indicates that an argument is required and ``|`` indicate choices.
        If ``|`` is present and the user didn't enter one of the choices, he will
        receive and error message. The same goes for not providing the required
        amount of arguments (as counted by ``<``).


    Note:
        It's possible to define a callback for each interface separately. Same
        as it's possible to define parameters for each interface separately.

    Attributes:
        callback (:obj:`Callback`): Callback function that is called when the command
          is executed.
        description (:obj:`str`): Description of the command. Shown in the command
          help window
        aliases (:obj:`list` of :obj:`str`): List of aliases that can be used to call
          the command
        disable (:obj:`list` of :obj:`CommandInterface`): List of CommandInterfaces
          that the command should be disabled for
        group (:obj:`str` | :obj:`CommandGroup`): Group used to group the command in
          the command help window
        parameters (:obj:`list` of :obj:`str`): List of parameters that are required
          to call the command in a chatroom. Shown in the command help window
        parameters_chatroom (:obj:`list` of :obj:`str`): List of parameters that are
          required to call the command in a chatroom. Shown in the command help window
        parameters_private_chat (:obj:`list` of :obj:`str`): List of parameters that
          are required to call the command in a private chat. Shown in the command
          help window
        parameters_cli (:obj:`list` of :obj:`str`): List of parameters that are required
            to call the command in the command line interface. Shown in the command help
            window
        callback_chatroom (:obj:`Callback`): Callback function that is called when the
            command is executed in a chatroom
        callback_private_chat (:obj:`Callback`): Callback function that is called when
            the command is executed in a private chat
        callback_cli (:obj:`Callback`): Callback function that is called when the command
            is executed in the command line interface
    """

    aliases: List[str]
    disable: List[CommandInterface]
    group: Union[str, CommandGroup]

    parameters: List[str]
    parameters_chatroom: List[str]
    parameters_private_chat: List[str]
    parameters_cli: List[str]

    callback_chatroom: Callback
    callback_private_chat: Callback
    callback_cli: Callback


Commands = dict[str, Command]
"""Dictionary of commands with their names as keys and their definitions as values."""

LegacyCommands = List[Tuple[str, Callable[..., Any]]]
"""Deprecated: List of tuples with the command name and the callback function for commands."""
