"""Module for defining commands

This module provides a decorator to define commands in a plugin. It also
provides fully documented available options unlike Nicotine+'s non existing
documentation.

Example:

    .. code-block:: python

        from npc import command, BasePlugin

        class Plugin(BasePlugin):

            @command
            def hello(self) -> None:
                \"""Say hello to the world\"""
                self.log("Hello World!")

            @command(parameters=["<name>", "<age>"])
            def greet(self, name: str, age: int) -> None:
                \"""Greet a person by name and age\"""
                self.window_log(f"Hello {name}, you are {age} years old")

            @command("custom-name", description="Via decorator instead of docstring")
            def other_name(self) -> None:
                ...

            # Shows up under "Users" in the command help window instead of the plugin
            @command(group=CommandGroup.USERS)
            def user_command(self) -> None:
                ...

Note:
    * The command name is extracted from the function name by default
    * The command description is extracted from the function's docstring by default
    * The command will be available in all interfaces by default
    * The command will not be daemonized by default (blocking the main thread)
    * The command will parse arguments according to the function's annotations by default

    .. seealso:: :func:`npc.command` for more information on the parameters
"""

import inspect
import re
import shlex
from functools import wraps
from threading import Thread
from typing import TYPE_CHECKING, Any, Callable, List, Literal, Optional, TypeVar, Union, get_args, get_origin, overload

try:
    from types import NoneType  # type: ignore[attr-defined]  # Added in Python 3.10
except ImportError:
    NoneType = type(None)


from .logging import log
from .types import AnyInputCallback, Callback, Command, CommandGroup, CommandInterface, DefaultCallback, ReturnCode

if TYPE_CHECKING:
    from .base import BasePlugin


__all__ = ["command"]


def _parse_according_to_annotation(annotation: Any, value: Any) -> Any:
    """Parse a value according to the given annotation (basic data types)

    Supported annotations:
        * str
        * int
        * float
        * bool
        * list
        * set
        * tuple
        * Union
        * NoneType

    Args:
        annotation (:obj:`typing.Any`): Annotation to be used for parsing (type hint)
        value (:obj:`typing.Any`): Value to be parsed

    Returns:
        :obj:`typing.Any: Parsed value
    """
    origin = get_origin(annotation) or annotation
    args = get_args(annotation)

    if annotation is inspect.Parameter.empty:
        return value
    elif origin in [str, int, float]:
        return origin(value)
    elif annotation is bool:
        if value.lower() in {"true", "t", "yes", "y", "1"}:
            return True
        elif value.lower() in {"false", "f", "no", "n", "0"}:
            return False
        raise ValueError(f"Invalid boolean value: {value}")
    elif origin in [list, set, tuple]:
        items = value.split(",")
        parsed_items = []
        for item in items:
            for arg in args:
                try:
                    parsed_items.append(_parse_according_to_annotation(arg, item))
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Invalid value: {value}, could not parse item: {item}")
        return origin(parsed_items)
    elif origin is Union:
        for arg in args:
            try:
                return _parse_according_to_annotation(arg, value)
            except ValueError:
                continue
        raise ValueError(f"Invalid value: {value}")
    elif origin is NoneType:
        if value.lower() in {"none", "null", "nil", ""}:
            return None
        raise ValueError(f"Invalid None value: {value}")


F = TypeVar("F", bound=Callback)
"""Type variable for function"""

AF = TypeVar("AF", bound=AnyInputCallback)
"""Type for function taking parsed input arguments"""

DF = TypeVar("DF", bound=DefaultCallback)
"""Type function taking default n+ command arguments"""


@overload
def command(
    *,
    description: Optional[str] = None,
    aliases: List[str] = [],
    disabled_interfaces: List[CommandInterface] = [],
    group: Optional[Union[str, CommandGroup]] = None,
    parameters: List[str] = [],
    parameters_chatroom: List[str] = [],
    parameters_private_chat: List[str] = [],
    parameters_cli: List[str] = [],
    daemonize: bool = False,
    daemonize_return: ReturnCode = ReturnCode.PASS,
    parse_args: Literal[True] = True,
) -> Callable[[AnyInputCallback], DefaultCallback]: ...


@overload
def command(
    *,
    description: Optional[str] = None,
    aliases: List[str] = [],
    disabled_interfaces: List[CommandInterface] = [],
    group: Optional[Union[str, CommandGroup]] = None,
    parameters: List[str] = [],
    parameters_chatroom: List[str] = [],
    parameters_private_chat: List[str] = [],
    parameters_cli: List[str] = [],
    daemonize: bool = False,
    daemonize_return: ReturnCode = ReturnCode.PASS,
    parse_args: Literal[False] = False,
) -> Callable[[DefaultCallback], DefaultCallback]: ...


@overload
def command(
    func_or_name: AF,
    *,
    description: Optional[str] = None,
    aliases: List[str] = [],
    disabled_interfaces: List[CommandInterface] = [],
    group: Optional[Union[str, CommandGroup]] = None,
    parameters: List[str] = [],
    parameters_chatroom: List[str] = [],
    parameters_private_chat: List[str] = [],
    parameters_cli: List[str] = [],
    daemonize: bool = False,
    daemonize_return: ReturnCode = ReturnCode.PASS,
    parse_args: Literal[True] = True,
) -> DefaultCallback: ...


@overload
def command(
    func_or_name: DF,
    *,
    description: Optional[str] = None,
    aliases: List[str] = [],
    disabled_interfaces: List[CommandInterface] = [],
    group: Optional[Union[str, CommandGroup]] = None,
    parameters: List[str] = [],
    parameters_chatroom: List[str] = [],
    parameters_private_chat: List[str] = [],
    parameters_cli: List[str] = [],
    daemonize: bool = False,
    daemonize_return: ReturnCode = ReturnCode.PASS,
    parse_args: Literal[False] = False,
) -> DefaultCallback: ...


@overload
def command(
    func_or_name: str,
    *,
    description: Optional[str] = None,
    aliases: List[str] = [],
    disabled_interfaces: List[CommandInterface] = [],
    group: Optional[Union[str, CommandGroup]] = None,
    parameters: List[str] = [],
    parameters_chatroom: List[str] = [],
    parameters_private_chat: List[str] = [],
    parameters_cli: List[str] = [],
    daemonize: bool = False,
    daemonize_return: ReturnCode = ReturnCode.PASS,
    parse_args: Literal[True] = True,
) -> Callable[[AF], DefaultCallback]: ...


@overload
def command(
    func_or_name: str,
    *,
    description: Optional[str] = None,
    aliases: List[str] = [],
    disabled_interfaces: List[CommandInterface] = [],
    group: Optional[Union[str, CommandGroup]] = None,
    parameters: List[str] = [],
    parameters_chatroom: List[str] = [],
    parameters_private_chat: List[str] = [],
    parameters_cli: List[str] = [],
    daemonize: bool = False,
    daemonize_return: ReturnCode = ReturnCode.PASS,
    parse_args: Literal[False] = False,
) -> Callable[[DF], DefaultCallback]: ...


def command(
    func_or_name: Union[str, F, None] = None,
    *,
    description: Optional[str] = None,
    aliases: List[str] = [],
    disabled_interfaces: List[CommandInterface] = [],
    group: Optional[Union[str, CommandGroup]] = None,
    parameters: List[str] = [],
    parameters_chatroom: List[str] = [],
    parameters_private_chat: List[str] = [],
    parameters_cli: List[str] = [],
    daemonize: bool = False,
    daemonize_return: ReturnCode = ReturnCode.PASS,
    parse_args: bool = True,
) -> Union[DefaultCallback, Callable[[F], DefaultCallback]]:
    """Decorator to define a command

    .. seealso:: :class:`npc.types.Command` for more information on the parameters

    Args:
        func_or_name (:obj:`str` | :obj:`npc.types.Callback`, optional): Name of the
            command or the function to be decorated
        description (:obj:`str`, optional): Description of the command, will be
            extracted from the function's docstring if not provided
        aliases (:obj:`list` of :obj:`str`, optional): List of aliases that can
            be used to call the command
        disabled_interfaces (:obj:`list` of :obj:`npc.types.CommandInterface`, optional):
            List of CommandInterfaces that the command should be disabled for
        group (:obj:`str` | :obj:`npc.types.CommandGroup`, optional): Group used to group
            the command in the command help window
        parameters (:obj:`list` of :obj:`str`, optional): List of parameters that
            are required to call the command everywhere unless overridden by
            any of the other parameters
        parameters_chatroom (:obj:`list` of :obj:`str`, optional): List of
            parameters that are required to call the command in a chatroom
        parameters_private_chat (:obj:`list` of :obj:`str`, optional): List of
            parameters that are required to call the command in a private chat
        parameters_cli (:obj:`list` of :obj:`str`, optional): List of parameters
            that are required to call the command in the command line interface
        daemonize (:obj:`bool`, optional): Whether the command should be run in
            a separate thread. These threads are daemons and will not block the
            main thread. This also means that the return value of the function
            is predefined as :attr:`npc.types.ReturnCode.PASS` or set via
            :paramref:`daemonize_return`
        daemonize_return (:obj:`npc.types.ReturnCode`, optional): Return code to be returned
            when the command is daemonized, default is :attr:`npc.types.ReturnCode.PASS`
        parse_args (:obj:`bool`, optional): Whether the arguments should be parsed
            according to the function's annotations

    Returns:
        :obj:`typing.Callable`: Decorator if only the options are provided, else the
            decorated function

    Raises:
        ValueError: If the command name is invalid
        ValueError: If the description is not provided
    """

    def outer_wrapper(func: F) -> DefaultCallback:
        if isinstance(func_or_name, str):
            name = func_or_name
        else:
            name = func.__name__

        name = name.replace("_", "-").lower()

        if not re.match(r"^[a-z0-9-]+$", name):
            raise ValueError(f'Invalid command name: "{name}", only alphanumeric characters and hyphens are allowed')

        desc = description or func.__doc__
        if not desc:
            raise ValueError(f"Description is required for command: {name}, either via the decorator or the docstring")

        command = Command(
            {
                "callback": func,
                "description": desc,
            }
        )

        if aliases:
            command["aliases"] = aliases
        if disabled_interfaces:
            command["disable"] = disabled_interfaces
        if group:
            command["group"] = group
        if parameters:
            command["parameters"] = parameters
        if parameters_chatroom:
            command["parameters_chatroom"] = parameters_chatroom
        if parameters_private_chat:
            command["parameters_private_chat"] = parameters_private_chat
        if parameters_cli:
            command["parameters_cli"] = parameters_cli

        @wraps(func)
        def wrapper(
            self: "BasePlugin", args: str, *, room: Optional[str] = None, user: Optional[str] = None
        ) -> Optional[ReturnCode]:
            if parse_args:
                user_args = shlex.split(args)
                parameters = inspect.signature(func).parameters.items()
                parameters = list(parameters)[1:]  # type: ignore[assignment]  # Skip self
                new_args: List[Any] = []
                for (arg_name, parameter), arg_value in zip(parameters, user_args):
                    if arg_name == "room":
                        new_args.append(room)
                    elif arg_name == "user":
                        new_args.append(user)
                    else:
                        try:
                            new_args.append(_parse_according_to_annotation(parameter.annotation, arg_value))
                        except ValueError as e:
                            from . import CONFIG  # Import here to avoid circular import

                            log(
                                f'Failed to parse argument: "{arg_name}" with value: "{arg_value}" - {e}',
                                title=f"[{CONFIG['name']}]: Failed to parse arguments in command \"{name}\"",
                            )
                            return ReturnCode.BREAK
                final_args = new_args
                log(f"Command: {name}, Args: {final_args}, Room: {room}, User: {user} - Parsed")
            else:
                final_args = [args, room, user]
                log(f"Command: {name}, Args: {final_args}, Room: {room}, User: {user} - Not Parsed")

            if daemonize:
                Thread(target=func, args=(self, final_args), daemon=True).start()
                return daemonize_return
            return func(self, *final_args)

        setattr(wrapper, "command", command)
        setattr(wrapper, "command_name", name)

        return wrapper  # type: ignore[return-value]

    if func_or_name is None or isinstance(func_or_name, str):
        return outer_wrapper
    return outer_wrapper(func_or_name)
