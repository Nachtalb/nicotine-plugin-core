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

import os
import platform
import subprocess
from time import sleep

from pynicotine.pluginsystem import PluginHandler

from .logging import log

__all__ = ["startfile", "reload_plugin"]


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


def reload_plugin(name: str, plugin_name: str, handler: PluginHandler) -> bool:
    """Reload a plugin

    Args:
        name (:obj:`str`): Name of the plugin reloading the plugin
        plugin_name (:obj:`str`): Name of the plugin to be reloaded
        handler (:obj:`PluginHandler`): Plugin handler
            .. seealso:: `PluginHandler <https://github.com/nicotine-plus/nicotine-plus/blob/f9eb76a706a8def652d26173f1ce5df778259cfd/pynicotine/pluginsystem.py#L371>`_

    Returns:
        :obj:`bool`: Whether the plugin was successfully reloaded
    """
    log(f"# {name}: Disabling plugin {plugin_name}...")
    sleep(1)
    try:
        handler.disable_plugin(plugin_name)
    except Exception as e:
        log(f"# {name}: Failed to reload plugin {plugin_name}:\n{e}", title="Plugin Reload")
        return False
    log(f"# {name}: Enabling plugin {plugin_name}...")
    try:
        handler.enable_plugin(plugin_name)
    except Exception as e:
        log(f"# {name} Failed to reload plugin {plugin_name}:\n{e}", title="Plugin Reload")
        return False
    log(f"# {name}: Successfully reloaded plugin {plugin_name}", title="Plugin Reload")
    return True
