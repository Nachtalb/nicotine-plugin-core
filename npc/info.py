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
import configparser
import sys
from pathlib import Path
from typing import Optional, Tuple

from pynicotine.logfacility import log as nlog

try:
    from pynicotine import __version__ as NICOTINE_VERSION

    if not isinstance(NICOTINE_VERSION, str):
        # This is a workaround for the building documentation
        NICOTINE_VERSION = "3.3.5"
except ImportError:
    from pynicotine.config import config as pynicotine_config

    NICOTINE_VERSION = pynicotine_config.version

from .types import PluginConfig
from .version import Version

__all__ = ["BASE_PATH", "CONFIG", "__version__", "IS_LEGACY", "NICOTINE_VERSION", "IS_DEV"]


def load_config(path: Path) -> Tuple[PluginConfig, bool]:
    """Load the plugin configuration from the given file

    .. versionchanged:: 0.4.0 Return whether the plugin is a development version

    Args:
        path (:obj:`pathlib.Path`): Path to the configuration file

    Returns:
        :obj:`tuple`: Plugin configuration and whether it is a development version
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

    version = Version.parse(config["version"])
    if version.is_prerelease:
        if config["prefix"]:
            nlog.add(
                f'{config["name"]} - WARNING - Attention: You are running this plugin in dev mode. '
                f'Prefix will be /d{config["prefix"]} instead of /{config["prefix"]} to prevent '
                'conflicts with the stable version.'
            )
            config["prefix"] = "d" + config["prefix"]
        config["name"] += " DEV"
        return config, True

    return config, False


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


def load_npc_package_config() -> PluginConfig:
    """Load the plugin configuration from the pyproject.toml file

    Returns:
        :obj:`npc.types.PluginConfig`: Plugin configuration
    """
    pyproject = find_file_in_parents("pyproject.toml", Path(__file__).parent)
    if pyproject:
        config = configparser.ConfigParser()
        config.read(str(pyproject))

        for option in ["name", "description", "author", "version"]:
            if config.has_option("tool.poetry", option):
                FALLBACK_CONFIG[option] = ast.literal_eval(config.get("tool.poetry", option))  # type: ignore[literal-required]
    return FALLBACK_CONFIG


FALLBACK_BASE_PATH = Path(__file__).parent
"""In case we are in a build environment like readthedocs.org"""

FALLBACK_CONFIG = PluginConfig(
    {
        "name": "Nicotine+ Plugin Core",
        "description": "A powerful core for building feature-rich Nicotine+ plugins with ease.",
        "author": ["Nachtalb"],
        "version": "0.2.0",
        "prefix": "",
        "repository": "Nachtalb/nicotine-plugin-core",
    }
)
"""Fallback configuration in case the plugin info file is not found"""

IS_DEV = False
"""Whether the plugin is a development version

.. versionadded:: 0.4.0 Explicit flag for development versions
"""

if path := find_file_in_parents("PLUGININFO", Path(__file__).parent):
    BASE_PATH = path.parent
    """Base path of the plugin directory"""

    config_file = BASE_PATH / "PLUGININFO"
    """Path to the plugin info file"""
    CONFIG, IS_DEV = load_config(config_file)
    """Plugin info"""
else:
    print("Could not find the base path of the plugin directory", file=sys.stderr)
    load_npc_package_config()
    BASE_PATH = FALLBACK_BASE_PATH
    """Base path of the plugin directory"""
    CONFIG = FALLBACK_CONFIG
    """Plugin info"""

__version__ = CONFIG["version"]
"""Plugin version"""


IS_LEGACY = Version.parse(NICOTINE_VERSION) < Version.parse("3.3.0")
