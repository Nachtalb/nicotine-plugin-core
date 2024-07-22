"""This module provides a easy to use and typed logging function for Nicotine+

Todo:
    * Add support for logging to a file other than Nicotine+'s log file
    * Add support for a real :class:`logging.Handler` object wrapping Nicotine+'s log

Example:

    .. code-block:: python

        from npc.logging import log

        log("Hello World!")
        # Hello World!

        log("Hello %s!", "World", prefix="MyPlugin")
        # MyPlugin: Hello World!

        log("Hello %s!", "World", title="MyPlugin")
        # Opens a window with the title "MyPlugin" and the message "Hello World!"
"""

from typing import Any, Optional

from pynicotine.logfacility import log as nlog

from .types import LogLevel

__all__ = ["log", "LogLevel"]


def log(
    message: str,
    *message_args: Any,
    level: LogLevel = LogLevel.DEFAULT,
    prefix: Optional[str] = None,
    title: Optional[str] = None,
    windowed: bool = False,
    should_log_to_file: bool = True,
) -> None:
    """Log a message to Nicotine's log

    Note:
        The log level is just a prefix defined by Nicotine+. It prepends the
        message with [LEVEL]. The prefix argument of this function is a custom
        prefix that will be added like so "PREFIX: message". The reason as to
        why this prefix is provided instead of just using the level is because
        Nicotine+ filters out unknown log levels, thus no custom prefix would
        be shown.

    Args:
        message (:obj:`str`): Message to be logged
        message_args (:obj:`Any`) : Arguments to be formatted in the message.
            Common log python log arguments such as ``%s``, ``%d``, etc. can
            be used
        level (:obj:`LogLevel`, optional): Log level, will be prefixed to the
            message in the format ``[LEVEL]: message``
        prefix (:obj:`str`, optional): Prefix to be added to the message, will
            be prefixed to the message in the format "PREFIX: message"
        title (:obj:`str`, optional): Title of the message, will force windowed
            to True
        windowed (:obj:`bool`, optional): Whether the message should be shown
            in a window. If title is not provided, it will be set to the name
            of the plugin.
        should_log_to_file (:obj:`bool`, optional): Whether the message should
            be logged to the file
    """
    if windowed and not title:
        from . import CONFIG  # Import here to avoid circular import

        title = CONFIG["name"]
    if prefix:
        message = f"{prefix}: {message}"

    nlog._add(
        msg=message,
        msg_args=message_args,
        title=title,
        level=level,
        should_log_file=should_log_to_file,
    )
