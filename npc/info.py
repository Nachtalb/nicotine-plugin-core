"""Plugin information and configuration

This module provides information about the plugin and its configuration.
The plugin configuration is loaded from the ``PLUGININFO`` file in the plugin
directory. The configuration file should look like this:

.. code-block:: ini

    NAME="My Plugin"
    DESCRIPTION="This is a plugin"
    AUTHOR=["Author 1", "Author 2"]
    VERSION="1.0.0"
    PREFIX="m"
    REPOSITORY="User/MyPlugin"

Note:
    * The ``PREFIX`` is optional and will be used as the command prefix for the
      plugin. Additionally if version contains `dev` the prefix will be
      ``d{PREFIX}`` to indicate that it is a development version and prevent
      conflicts with the stable version.
    * The ``REPOSITORY`` is optional and should be in the format
      ``User/Repository`` or a URL to the GitHub repository. This enables
      automated checks for updates.
"""

import ast
from pathlib import Path
from typing import Optional

from .logging import log
from .types import PluginConfig

__all__ = ["BASE_PATH", "CONFIG", "__version__"]


def load_config(path: Path) -> PluginConfig:
    """Load the plugin configuration from the given file

    Args:
        path (:obj:`pathlib.Path`): Path to the configuration file

    Returns:
        :obj:`npc.types.PluginConfig`: Plugin configuration
    """
    content = path.read_text()
    config = PluginConfig(
        {
            "name": "",
            "description": "",
            "author": [],
            "version": "",
            "prefix": "",
            "repository": "",
        }
    )
    for line in content.split("\n"):
        if not line:
            continue
        key, _, value = line.partition("=")
        config[key.strip().lower()] = ast.literal_eval(value.strip())  # type: ignore[literal-required]

    if "dev" in config["version"]:
        if config["prefix"]:
            log("#" * 40 + f'\nAttention: You are running this in dev mode. Prefix will be /d{config["prefix"]}')
            config["prefix"] = "d" + config["prefix"]
        config["name"] += " DEV"

    return config


def find_file_in_parents(file: str, start: Path) -> Optional[Path]:
    """Find a file in the parent directories of the given path

    Args:
        file (:obj:`str`): File to search for
        start (:obj:`pathlib.Path`): Path to start the search from

    Returns:
        :obj:`pathlib.Path` | :obj:`None`: Path to the file or None if not found
    """
    path = start
    while path != path.parent:
        if (path / file).exists():
            return path / file
        path = path.parent
    return None


BASE_PATH = find_file_in_parents("PLUGININFO", Path(__file__).parent).parent  # type: ignore[union-attr]
"""Base path of the plugin directory"""

if not BASE_PATH:
    raise FileNotFoundError("Could not find the base path of the plugin directory")

config_file = BASE_PATH / "PLUGININFO"
"""Path to the plugin info file"""
CONFIG = load_config(config_file)
"""Plugin info"""

__version__ = CONFIG["version"]
"""Plugin version"""
