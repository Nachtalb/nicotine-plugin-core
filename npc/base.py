"""This module provides the base class for plugins

This module provides a base class for plugins to inherit from. It provides a few
helper functions and properties to make plugin development easier. The plugin
class should inherit from this class.

Some default functionality that is provided by the BasePlugin class:
    * Check for updates
    * Logging with the plugin name
    * Settings change detection
    * Automatic command setup
    * Plugin reloading with `/reload`
"""

import inspect
import json
import re
import sys
from abc import ABC
from pathlib import Path
from textwrap import dedent
from threading import Thread
from typing import Any, Optional, Set, Tuple, Union

from pynicotine.pluginsystem import BasePlugin as NBasePlugin

from .command import command
from .config import BaseConfig, Bool, Int
from .info import BASE_PATH, CONFIG, __version__
from .logging import log
from .requests import get
from .threading import PeriodicJob
from .types import Commands, LegacyCommands, LogLevel, MetaSettings, PluginConfig, ReturnCode, Settings, SettingsDiff
from .utils import reload_plugin
from .version import Version

__all__ = ["BasePlugin"]


class BasePlugin(NBasePlugin, ABC):  # type: ignore[misc]
    """Base class for plugins

    To set the settings for the plugin, you can use the provided :class:`BaseConfig`
    class. It's best to inherit from the BasePlugins existing :attr:`BasePlugin.Config`,
    to ensure that default configuration, such as the update check and interval, is
    available. You can also add custom settings to the configuration class.

    Note:
        :attr:`BasePlugin.metasettings` and :attr:`BasePlugin.settings` are built
        automatically from the given :attr:`BasePlugin.Config`. They should not be
        overridden.

    Example:

        .. code-block:: python

            from npc import BasePlugin, Bool, Int, command

            class Plugin(BasePlugin):
                class Config(BasePlugin.Config):
                    setting1 = Bool("setting1", "Setting 1", True)
                    setting2 = Int("setting2", "Setting 2", 10)

                @command(parameters=["<name>", "<age>"])
                def hello(self, name: str, age: int) -> None:
                    \"\"\"Hello command\"\"\"
                    self.window_log(f"Hello {name}, you are {age} years old", title="Welcome")


    Attributes:
        settings (:obj:`Settings`): Plugin settings dictionary. Don't override
            this by yourself. It's automatically built from the settings in the
            :attr:`BasePlugin.Config`.
        metasettings (:obj:`MetaSettings`): Plugin meta settings dictionary. Don't
            override this by yourself. It's automatically built from the settings
            in the :attr:`BasePlugin.Config`.
        config (:obj:`BaseConfig`): Plugin configuration instance of the class
            :attr:`BasePlugin.Config`.
        plugin_config (:obj:`PluginConfig`): Information about the plugin itself,
            such as the name, version and authors.
        plugin_name (:obj:`str`): Name of the plugin
        auto_update (:obj:`PeriodicJob`): Periodic job for checking if the
            plugin is up to date. It runs the :meth:`BasePlugin._check_update`
            function every :attr:`BasePlugin.Config.check_update_interval` seconds.
        settings_watcher (:obj:`PeriodicJob`): Periodic job for watching changes
            in the settings. It runs the :meth:`BasePlugin.detect_settings_change`
            function every second.
        commands (:obj:`Commands`): Dictionary of commands. Don't override this
            it is built automatically. Use the :func:`npc.command` decorator to
            add commands to the plugin.
        __publiccommands__ (:obj:`LegacyCommands`): Deprecated: Legacy list of
            public commands. Use :attr:`BasePlugin.commands` instead.
        __privatecommands__ (:obj:`LegacyCommands`): Deprecated: Legacy list of
            private commands. Use :attr:`BasePlugin.commands` instead.
    """

    class Config(BaseConfig):
        check_update = Bool("check_update", "Check for updates", True)
        check_update_interval = Int("check_update_interval", "Update check interval (minutes)", 60 * 6)
        preview_versions = Bool("preview_versions", "Check for preview versions", "dev" in __version__)
        verbose = Bool("verbose", "Verbose logging", True)

    settings: Settings
    metasettings: MetaSettings

    plugin_config: PluginConfig = CONFIG

    __publiccommands__: LegacyCommands = []
    __privatecommands__: LegacyCommands = []
    commands: Commands = {}

    _informed_about_update: bool = False

    @property
    def __name__(self) -> str:
        return self.plugin_config.get("name", self.__class__.__name__)  # type: ignore[return-value]

    def __init__(self) -> None:
        # Settings changed by the user are not available yet!
        self.config = self.Config(self)
        self.settings = self.config.model_settings()
        self.metasettings = self.config.model_metasettings()

        self._setup_commands()

    def init(self) -> None:
        """Init after loading user settings

        This function is called after the user settings are loaded. It's a good
        place to do any setup that requires the user settings to be loaded.
        """
        self.vlog("Initializing plugin")
        self.auto_update = PeriodicJob(
            name="AutoUpdate",
            delay=self.config.check_update_interval * 60,
            update=self._check_update,
        )
        self.auto_update.start()

        self.settings_watcher = PeriodicJob(name="SettingsWatcher", update=self.detect_settings_change)
        self.settings_watcher.start()

        if self.plugin_config["version"]:
            self.log("Running version %s", self.plugin_config["version"])
        else:
            self.log("No version defined in plugin config")

    def _setup_commands(self) -> None:
        """Setup commands from methods decorated with @command"""
        self.vlog("Setting up commands")
        prefix = self.plugin_config.get("prefix")

        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for name, method in methods:
            if hasattr(method, "command"):
                command = method.command
                command_name = getattr(method, "command_name", name)
                command_name = f"{prefix}{command_name}" if prefix else command_name
                command["callback"] = method
                self.commands[command_name] = command
                self.vlog(f"Command {command_name} added {command['callback']}, {method}")

        self.vlog(f"Commands setup complete: {self.commands}")

    @property
    def plugin_name(self) -> str:
        """Return the plugin name"""
        return self.__name__

    @command(daemonize=False)
    def reload(self) -> None:
        """Reload the plugin"""
        Thread(target=reload_plugin, daemon=True, args=(self.__name__, self.plugin_name, self.parent)).start()

    @command(daemonize_return=ReturnCode.ZAP)
    def check_update(self) -> None:
        """Check for updates"""
        self._check_update(self.config.preview_versions)

    def _check_update(self, preview: bool = False) -> Union[None, Version]:
        """Actual update check implementation

        Args:
            preview (bool, optional): Whether to check for preview releases.
                Defaults to False.

        Returns:
            :obj:`npc.Version` | :obj:`None`: Latest version if not updated
        """
        repo_url = self.plugin_config.get("repository")
        if not repo_url:
            self.log("No repository defined for this plugin, disabling update check")
            self.config.check_update = False
            self.config.apply()
            return None

        if repo_url.startswith("http"):
            match = re.match(r"https?://github.com/([^/]+)/([^/]+)", repo_url)
            if match:
                user = match.group(1)
                repo = match.group(2)
            else:
                raise ValueError("Invalid repository URL")
        else:
            try:
                user, repo = repo_url.split("/")
            except ValueError as e:
                raise ValueError("Invalid repository configuration") from e

        releases_url = f"https://api.github.com/repos/{user}/{repo}/releases"
        try:
            current_version = Version.parse(__version__)
        except ValueError:
            self.log(f"Invalid version format: {__version__}")
            return None

        try:
            response = get(releases_url)
        except Exception as e:
            self.log(f"Error fetching releases: {e}")
            return None
        for release in response.json:
            if not preview and (release["draft"] or release["prerelease"]):
                continue

            try:
                version = Version.parse(release["tag_name"][1:])
            except ValueError:
                self.log(f"Invalid version format: {release['tag_name']}")
                continue

            if version > current_version:
                if not self._informed_about_update:
                    self.window_log(
                        dedent(
                            f"""
                        A new version of the plugin \"{self.__name__}\" is available:
                        - Current version: {current_version}
                        - New version: {version}
                        """
                        ),
                        title="Update available",
                    )
                else:
                    self.log(f"New version available: {current_version} -> {version}")
                self._informed_about_update = True
                return version
        return None

    def stop(self) -> None:
        """Stop the plugin and clean up"""
        if hasattr(self, "pre_stop"):
            self.pre_stop()
        self.auto_update.stop(wait=False)
        self.settings_watcher.stop(wait=False)

        # Module injection cleanup
        module_path = str(BASE_PATH.absolute())
        if module_path in sys.path:
            sys.path.remove(module_path)

        for name in list(sys.modules.keys())[:]:
            if name.startswith(Path(__file__).parent.name):
                sys.modules.pop(name)

    def shutdown_notification(self) -> None:
        """Notification that the plugin is being shutdown"""
        self.stop()

    def disable(self) -> None:
        """Disable the plugin"""
        self.stop()

    def _settings_to_set(self, settings: Settings) -> Set[Tuple[str, Any]]:
        """Convert settings to a set of tuples

        Note:
            List values are converted to tuples to be hashable and comparable

        Args:
            settings (:obj:`Settings`): Settings to convert (before or after)

        Returns:
            :obj:`set` of :obj:`tuple`: Set of tuples of settings key-value pairs
        """
        set_ = set()
        for k, v in settings.items():
            if k in self.settings:
                if isinstance(v, list):
                    v = tuple(v)  # type: ignore[assignment]
                set_.add((k, v))
        return set_

    def _set_to_settings(self, set_: Set[Tuple[str, Any]]) -> Settings:
        """Convert a set of tuples to settings

        Note:
            Tuples are converted to lists to match the settings format

        Args:
            set_ (:obj:`set` of :obj:`tuple`): Set of tuples of settings key-value pairs

        Returns:
            :obj:`Settings`: Settings dictionary
        """
        return {k: list(v) if isinstance(v, tuple) else v for k, v in set_}

    def detect_settings_change(self) -> None:
        """Detect changes in settings and call settings_changed if there are any

        Note:
            This function is called periodically to detect changes in settings. If
            there are any changes, the `settings_changed` function is called with
            the before and after settings and the changes.
        """
        if not hasattr(self, "_settings_before"):
            self._settings_before = self._settings_to_set(self.settings)
            return

        after = self._settings_to_set(self.settings)
        if changes := self._settings_before ^ after:
            change_dict = SettingsDiff(
                {
                    "before": dict(t for t in self._settings_before if t in changes),
                    "after": dict(t for t in after if t in changes),
                }
            )
            self.settings_changed(
                before=self._set_to_settings(self._settings_before), after=self.settings, change=change_dict
            )

            self._settings_before = after

    def settings_changed(self, before: Settings, after: Settings, change: SettingsDiff) -> None:
        """Called when settings are changed

        Note:
            By default, this function logs the changes in the settings. Override
            this function to handle the settings changes.

        Args:
            before (:obj:`Settings`): Complete settings before the change
            after (:obj:`Settings`): Complete settings after the change
            change (:obj:`SettingsDiff`): Dictionary of changes in the settings
        """
        self.log(f"Settings change: {json.dumps(change)}")

    def vlog(self, message: str, *message_args: Any) -> None:
        """Verbose log

        Log a message only if the verbose setting is enabled

        Args:
            message (:obj:`str`): Message to be logged
            message_args (:obj:`Any`): Arguments to be formatted in the message.
                Common log python log arguments such as %s, %d, etc. can be used
        """
        if self.settings.get("verbose", False):
            log(message, *message_args)

    def log(
        self,
        message: str,
        *message_args: Any,
        level: LogLevel = LogLevel.DEFAULT,
        prefix: Optional[str] = None,
        title: Optional[str] = None,
        windowed: bool = False,
        should_log_to_file: bool = True,
    ) -> None:
        """Log a message to the console and optionally to a window

        .. seealso:: Alias for :func:`npc.log` for arguments and usage.

        Adds the plugin name as a prefix to the message.
        """
        prefix = prefix if prefix is not None else self.__name__

        log(
            message,
            *message_args,
            level=level,
            prefix=prefix,
            title=title,
            windowed=windowed,
            should_log_to_file=should_log_to_file,
        )

    def window_log(
        self,
        message: str,
        *message_args: Any,
        title: Optional[str] = None,
        level: LogLevel = LogLevel.DEFAULT,
    ) -> None:
        """Log a message to a window

        .. seealso:: Alias for :func:`npc.log` for arguments and usage.

        The title will be prefixed with the plugin name or if not provided, the
        plugin name will be used as the title.
        """
        if not title:
            title = self.__name__
        else:
            title = f"{self.__name__}: {title}"
        self.log(message, *message_args, level=level, title=title, prefix="")
