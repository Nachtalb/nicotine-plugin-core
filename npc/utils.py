"""Utility functions for Nicotine+ plugins

This module contains utility functions that can be used by Nicotine+ plugins.
These functions are not specific to any plugin and can be used by any plugin.

Example:

    .. code-block:: python

        from npc.utils import startfile, reload_plugin

        # Open a file
        startfile("path/to/music.mp3")

        # Reload a Plugin
        reload_plugin("MyPlugin", "AnotherPlugin", handler)
"""

import inspect
import os
import platform
import subprocess
from time import sleep

from pynicotine.pluginsystem import PluginHandler

from .logging import log

__all__ = ["startfile", "reload_plugin", "is_function_in_stacktrace"]


def startfile(file: str) -> None:
    """Open a file with the platform's default application

    Args:
        file (:obj:`str`): Path to the file to be opened
    """
    if platform.system() == "Darwin":  # macOS
        subprocess.call(("open", file))
    elif platform.system() == "Windows":  # Windows
        os.startfile(file)  # type: ignore[attr-defined]
    else:  # linux variants
        subprocess.call(("xdg-open", file))


def reload_plugin(name: str, plugin_id: str, handler: PluginHandler) -> bool:
    """Reload a plugin

    .. versionchanged:: 0.4.1 Changed :paramref:`plugin_name` to :paramref:`plugin_id` as it is more accurate

    Args:
        name (:obj:`str`): Name of the plugin reloading the plugin
        plugin_id (:obj:`str`): Identifier of the plugin in the plugin handler
        handler (:obj:`PluginHandler`): Plugin handler
            .. seealso:: `PluginHandler <https://github.com/nicotine-plus/nicotine-plus/blob/f9eb76a706a8def652d26173f1ce5df778259cfd/pynicotine/pluginsystem.py#L371>`_

    Returns:
        :obj:`bool`: Whether the plugin was successfully reloaded
    """
    log(f"# {name}: Disabling plugin {plugin_id}...")
    sleep(1)
    try:
        for plugin in handler.enabled_plugins:
            log(f"# {plugin}: {handler.enabled_plugins[plugin].path}")
        handler.disable_plugin(plugin_id)
    except Exception as e:
        log(f"# {name}: Failed to reload plugin {plugin_id}:\n{e}", title="Plugin Reload")
        return False
    log(f"# {name}: Enabling plugin {plugin_id}...")
    try:
        handler.enable_plugin(plugin_id)
    except Exception as e:
        log(f"# {name} Failed to reload plugin {plugin_id}:\n{e}", title="Plugin Reload")
        return False
    log(f"# {name}: Successfully reloaded plugin {plugin_id}", title="Plugin Reload")
    return True


def is_function_in_stacktrace(function_name: str) -> bool:
    """Check if a function is in the current stacktrace

    Args:
        function_name (:obj:`str`): Name of the function to be checked

    Returns:
        :obj:`bool`: Whether the function is in the current stacktrace
    """
    stack = inspect.stack()

    for frame_info in stack:
        if frame_info.function == function_name:
            return True

    return False
