"""This module provides a easy to use and typed logging function for Nicotine+

Example:

    Using a python logging.Logger

    .. code-block:: python

        from npc.logging import LOGGER

        LOGGER.setLevel(logging.DEBUG)
        LOGGER.debug("Hello World!")

    Customizing the Logger

    .. code-block:: python

        import logging
        from npc.logging import NLogHandler

        handler = NLogHandler()
        format = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(format)
        own_logger = logging.Logger("MyPlugin")
        own_logger.addHandler(handler)

        own_logger.info("Hello World!")

    Using the log function

    .. code-block:: python

        from npc.logging import log

        log("Hello World!")
        # Hello World!

        log("Hello %s!", "World", prefix="MyPlugin")
        # MyPlugin: Hello World!

        log("Hello %s!", "World", title="MyPlugin")
        # Opens a window with the title "MyPlugin" and the message "Hello World!"
"""

import logging
from typing import Any, Optional

from pynicotine.logfacility import log as nlog

from .info import CONFIG
from .types import LogLevel

__all__ = ["log", "LOGGER", "NLogHandler"]


class NLogHandler(logging.Handler):
    """Custom logging handler for Nicotine+

    This handler will emit log records using Nicotine+'s log facility.

    Example:

        .. code-block:: python

            import logging
            from npc.logging import NLogHandler

            # Create a handler
            handler = NLogHandler()

            # Set the formatter
            format = logging.Formatter("%(levelname)s - %(message)s")
            handler.setFormatter(format)

            # Create a logger
            logger = logging.Logger("MyPlugin")
            logger.addHandler(handler)

            # Log a message
            logger.info("Hello World!")


    .. seealso:: :class:`logging.Handler` for more information on logging handlers
    """

    def __init__(self) -> None:
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record using Nicotine+'s log facility

        Args:
            record (:obj:`logging.LogRecord`): Log record to be emitted
        """
        # Convert the log record to a string
        message = self.format(record)

        # Call the nlog._add method
        nlog._add(msg=message, msg_args={})


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
        message_args (:obj:`typing.Any`) : Arguments to be formatted in the message.
            Common log python log arguments such as ``%s``, ``%d``, etc. can
            be used
        level (:obj:`npc.types.LogLevel`, optional): Log level, will be prefixed to the
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


handler = NLogHandler()
format = logging.Formatter(
    "%(name)s - %(levelname)s - %(message)s"
)  # %(asctime)s not needed as it's already added by n+
handler.setFormatter(format)

LOGGER = logging.Logger(CONFIG["name"])
LOGGER.addHandler(handler)
LOGGER.__doc__ = """
Your typical :class:`logging.Logger` logging to Nicotine+'s log facility

* It uses the :class:`npc.logging.NLogHandler` to emit log records
* It is already configured with the plugin's name
* It uses the format ``%(name)s - %(levelname)s - %(message)s``. Time is
  already added by Nicotine+


Example:

        .. code-block:: python

            from npc.logging import LOGGER

            LOGGER.setLevel(logging.DEBUG)
            LOGGER.debug("Hello World!")
"""
