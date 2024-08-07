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
import logging
import re
import sys
from abc import ABC
from textwrap import dedent
from threading import Thread
from typing import Any, Dict, List, Optional, Set, Tuple

from pynicotine.pluginsystem import BasePlugin as NBasePlugin

from .command import command
from .config import BaseConfig, Bool, Int
from .info import BASE_PATH, CONFIG, IS_DEV, IS_LEGACY, NICOTINE_VERSION, __version__
from .logging import NLogHandler, log
from .requests import get
from .threading import PeriodicJob
from .types import (
    CommandInterface,
    Commands,
    LegacyCommands,
    MetaSettings,
    PluginConfig,
    ReturnCode,
    Settings,
    SettingsDiff,
)
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
                    setting1 = Bool("Setting 1", True)
                    setting2 = Int("Setting 2", 10)

                @command(parameters=["<name>", "<age>"])
                def hello(self, name: str, age: int) -> None:
                    \"\"\"Hello command\"\"\"
                    self.window(f"Hello {name}, you are {age} years old", title="Welcome")

    .. versionremoved:: 0.2.0 Removed :meth:`npc.BasePlugin.vlog` in favour of the
        :attr:`npc.BasePlugin.log` logger instance. Use ``self.log.debug(...)`` instead.

    .. versionremoved:: 0.4.1 Removed :meth:`npc.BasePlugin.__name__` in favour of
        :attr:`npc.BasePlugin.plugin_name`.

    Attributes:
        settings (:obj:`npc.types.Settings`): Plugin settings dictionary. Don't override
            this by yourself. It's automatically built from the settings in the
            :attr:`BasePlugin.Config`.
        metasettings (:obj:`npc.types.MetaSettings`): Plugin meta settings dictionary. Don't
            override this by yourself. It's automatically built from the settings
            in the :attr:`BasePlugin.Config`.
        config (:obj:`BaseConfig`): Plugin configuration instance of the class
            :attr:`BasePlugin.Config`.
        plugin_config (:obj:`npc.types.PluginConfig`): Information about the plugin itself,
            such as the name, version and authors.
        auto_update (:obj:`npc.PeriodicJob`): Periodic job for checking if the
            plugin is up to date. It runs the :meth:`BasePlugin._automatic_update_check`
            function every :attr:`BasePlugin.Config.check_update_interval` seconds.
        settings_watcher (:obj:`npc.PeriodicJob`): Periodic job for watching changes
            in the settings. It runs the :meth:`BasePlugin.detect_settings_change`
            function every second.
        commands (:obj:`npc.types.Commands`): Dictionary of commands. Don't override this
            it is built automatically. Use the :func:`npc.command` decorator to
            add commands to the plugin.
        __publiccommands__ (:obj:`npc.types.LegacyCommands`): Deprecated: Legacy list of
            public commands. Use :attr:`BasePlugin.commands` instead.
        __privatecommands__ (:obj:`npc.types.LegacyCommands`): Deprecated: Legacy list of
            private commands. Use :attr:`BasePlugin.commands` instead.
        log (:obj:`logging.Logger`): Logger instance for the plugin. It's named after
            the plugin name.

            .. versionchanged:: 0.2.0 Replaced ``npc.BasePlugin.log()`` function with
                :attr:`npc.BasePlugin.log` logger instance. Use ``self.log.info(...)`` instead
                of ``self.log(...)``.
    """

    class Config(BaseConfig):
        """Default configuration for plugins made with :class:`BasePlugin`

        The default configuration includes settings for checking for updates and
        the update check interval. You can add your own settings by inheriting
        from this class and adding your own settings.

        Attributes:
            check_update (:obj:`Bool`): Check for updates
            check_update_interval (:obj:`Int`): Update check interval in minutes
            preview_versions (:obj:`Bool`): Check for preview versions
            verbose (:obj:`Bool`): Verbose logging
        """

        check_update = Bool("Check for updates", default=True)
        check_update_interval = Int("Update check interval (minutes)", default=60 * 6, minimum=1)
        preview_versions = Bool("Check for preview versions", default=IS_DEV)
        verbose = Bool("Verbose logging", default=True)

    settings: Settings
    metasettings: MetaSettings

    plugin_config: PluginConfig = CONFIG

    __publiccommands__: LegacyCommands = []
    __privatecommands__: LegacyCommands = []
    commands: Commands = {}

    _informed_about_update: bool = False

    def __init__(self) -> None:
        # Settings changed by the user are not available yet!
        self.config = self.Config(self)
        self.settings = self.config.model_settings()
        self.metasettings = self.config.model_metasettings()

        handler = NLogHandler()
        format = logging.Formatter(
            "%(name)s - %(levelname)s - %(message)s"
        )  # %(asctime)s not needed as it's already added by n+
        handler.setFormatter(format)
        self.log = logging.Logger(self.plugin_name)
        self.log.addHandler(handler)

        self._setup_commands()

    def init(self) -> None:
        """Init after loading user settings

        This function is called after the user settings are loaded. It's a good
        place to do any setup that requires the user settings to be loaded.
        """
        self.log.debug("Initializing plugin")
        self.log.info(
            f"Running {self.plugin_name} plugin version {self.plugin_config['version']} on Nicotine+ {NICOTINE_VERSION}{' (legacy)' if IS_LEGACY else ''} with Python {sys.version}"
        )
        self.auto_update = PeriodicJob(
            name="AutoUpdate",
            delay=self._automatic_update_check_delay,
            update=self._automatic_update_check,
        )
        self.auto_update.start()

        self.settings_watcher = PeriodicJob(name="SettingsWatcher", update=self.detect_settings_change)
        self.settings_watcher.start()

        self.log.setLevel("DEBUG" if self.config.verbose else "INFO")
        # This should be done in the logging module, but for some reason it doesn't work
        # so we have to clear the cache manually
        self.log._cache.clear()  # type: ignore[attr-defined]

        if self.plugin_config["version"]:
            self.log.info("Running version %s", self.plugin_config["version"])
        else:
            self.log.info("No version defined in plugin config")

    @command
    def help(self) -> None:
        """Show help for the plugin commands"""
        if not IS_LEGACY:
            self.window(
                "This version of Nicotine+ has a builtin help command. Use /help to see the available commands."
            )
            return

        command_list: List[str] = []
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        prefix = self.plugin_config.get("prefix", "")
        for name, method in methods:
            if hasattr(method, "command"):
                command = method.command
                command_name = prefix + getattr(method, "command_name", name)
                command_args = " ".join(command.get("parameters", []))
                command_args = f" {command_args}" if command_args else ""
                command_list.append(f"/{command_name}{command_args}: {command.get('description', 'No description')}")

        commands = "- " + "\n- ".join(command_list)
        self.log.info(f"Commands for {self.plugin_name}:\n{commands}")

    def _setup_commands(self) -> None:
        """Setup commands from methods decorated with @command

        .. versionchanged:: 0.3.5 Add support for Nicotine+ < 3.3.0 legacy command system

        """
        self.log.debug("Setting up commands")
        prefix = self.plugin_config.get("prefix")

        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for name, method in methods:
            if hasattr(method, "command"):
                command = method.command
                command_name = getattr(method, "command_name", name)
                command_name = f"{prefix}{command_name}" if prefix else command_name
                command["callback"] = method

                if IS_LEGACY:
                    if CommandInterface.CHATROOM not in command.get("disable", []):
                        self.__publiccommands__.append((command_name, method))
                    if CommandInterface.PRIVATE_CHAT not in command.get("disable", []):
                        self.__privatecommands__.append((command_name, method))
                else:
                    self.commands[command_name] = command
                self.log.debug(f"Command {command_name} added {command['callback']}, {method}")

        self.log.debug(f"Commands setup complete: {self.commands}")

    @property
    def plugin_identifier(self) -> str:
        """Return the plugin path name which is the internal identifier

        .. versionadded:: 0.4.1 Added plugin identifier

        Returns:
            :obj:`str`: Plugin identifier
        """
        return BASE_PATH.name

    @property
    def plugin_name(self) -> str:
        """Return the plugin name"""
        return self.plugin_config.get("name", self.plugin_identifier)

    @command
    def verbose(self) -> None:
        """Toggle verbose logging"""
        self.config.verbose = not self.config.verbose
        self.config.apply()

    @command(daemonize=False)
    def reload(self) -> None:
        """Reload the plugin"""
        Thread(target=reload_plugin, daemon=True, args=(self.plugin_name, self.plugin_identifier, self.parent)).start()

    @command(daemonize_return=ReturnCode.ZAP)
    def check_update(self) -> None:
        """Check for updates

        .. versionchanged:: 0.3.6 Show window if no updates are available

        .. versionchanged:: 0.5.0 Always show the update window not only on the first run
        """
        current, new = self._check_update(self.config.preview_versions, {"type": "manual"})
        self._show_update_window(current, new)

    def update_available(self, old_version: Version, new_version: Version, context: Dict[str, Any] = {}) -> None:
        """Override this function to handle an available update

        Note:
            This is run before any window is shown to the user about the update.

        .. versionadded:: 0.5.0 Hook to handle available updates for plugins that need it

        Args:
            old_version (:obj:`Version`): Current version
            new_version (:obj:`Version`): New version
            context (:obj:`dict`, optional): Additional information about the update
        """

    def _gh_user_repo(self) -> Tuple[str, str]:
        """Return the GitHub user and repository

        Returns:
            :obj:`tuple` of :obj:`str`: GitHub user and repository

        Raises:
            :obj:`ValueError`: If the repository URL is invalid or not set
        """
        repo_url = self.plugin_config.get("repository")
        if not repo_url:
            raise ValueError("No repository defined for this plugin")
        if "github.com" in repo_url:
            if match := re.search(r"github.com(?::|/)([^/]+)/([^/]+)", repo_url):
                user, repo = match.groups()
            else:
                raise ValueError("Invalid repository URL")
        else:
            try:
                user, repo = repo_url.split("/")
            except ValueError as e:
                raise ValueError("Invalid repository configuration") from e
        return user, repo

    def _gh_api_releases_url(self) -> str:
        """Return the GitHub release URL for a version

        Returns:
            :obj:`str`: GitHub release URL

        Raises:
            :obj:`ValueError`: If the repository URL is invalid or not set
        """
        user, repo = self._gh_user_repo()
        return f"https://api.github.com/repos/{user}/{repo}/releases"

    def _automatic_update_check_delay(self) -> int:
        """Return the delay for the automatic update check

        .. versionchanged:: 0.4.2 Fix automatic update delay not reflected when
            changing the interval

        Returns:
            :obj:`int`: Delay in seconds
        """
        return self.config.check_update_interval * 60

    def _automatic_update_check(self) -> None:
        """Automatic update check function

        This function is called by the :attr:`BasePlugin.auto_update` job to
        check for updates. It calls the :meth:`BasePlugin._check_update` function
        and shows a window if an update is available.
        """
        if self.config.check_update:
            current, new = self._check_update(self.config.preview_versions, {"type": "auto"})

            if new:
                if not self._informed_about_update:
                    self._show_update_window(current, new)
                    self._informed_about_update = True
                self.log.info(f"New version available: {current} -> {new}")
            self.log.info(f"Using latest version: {current}")

    def _show_update_window(self, old_version: Version, new_version: Optional[Version]) -> None:
        """Show a window with the available update

        Args:
            old_version (:obj:`Version`): Current version
            new_version (:obj:`Version`, optional): New version or None if no update is available
        """
        if new_version:
            self.window(
                dedent(
                    f"""
                A new version of the plugin \"{self.plugin_name}\" is available:
                - Current version: {old_version}
                - New version: {new_version}
                """
                ),
                title="Update check",
            )
        else:
            self.window("No updates available", title="Update check")

    def _check_update(
        self, check_prerelease: bool = False, context: Dict[str, Any] = {}
    ) -> Tuple[Version, Optional[Version]]:
        """Actual update check implementation

        Args:
            check_prerelease (:obj:`bool`, optional): Check for pre releases versions. Defaults to False.
            context (:obj:`dict`, optional): Additional information to pass to the update hook

        Returns:
            :obj:`tuple` of :obj:`Version`, :obj:`Version`: Current version and new version if available
        """
        current_version = Version.parse(__version__)

        try:
            releases_url = self._gh_api_releases_url()
        except ValueError:
            self.log.info("No repository defined for this plugin, disabling update check")
            self.config.check_update = False
            self.config.apply()
            return current_version, None

        try:
            response = get(releases_url)
        except Exception as e:
            self.log.warning(f"Error fetching releases: {e}")
            return current_version, None

        for release in response.json:
            if release["draft"]:
                continue

            if not check_prerelease and release["prerelease"]:
                continue

            try:
                version = Version.parse(release["tag_name"][1:])
            except ValueError:
                self.log.warning(f"Invalid version format: {release['tag_name']}")
                continue

            if version > current_version:
                self.update_available(current_version, version, context=context)
                return current_version, version
        return current_version, None

    def stop(self) -> None:
        """Stop the plugin and clean up

        .. versionchanged:: 0.4.1 Fix unloading of modules
        """
        if hasattr(self, "pre_stop"):
            self.pre_stop()
        self.auto_update.stop(wait=False)
        self.settings_watcher.stop(wait=False)

        # Module injection cleanup
        module_path = str(BASE_PATH)
        self.log.debug(f"Module Path to remove: {module_path}")

        if module_path in sys.path:
            self.log.debug(f"Removing module path {module_path}")
            sys.path.remove(module_path)

        module_name = self.__class__.__module__.split(".")[0]
        self.log.debug(f"Module cleanup for {module_name}")

        for index, name in enumerate(list(sys.modules.keys())[:]):
            if name == module_name or name.startswith(f"{module_name}."):
                self.log.debug(f"Unloading module {name}")
                sys.modules.pop(name)

    def shutdown_notification(self) -> None:
        """Notification that the plugin is being shutdown"""
        self.log.info("Shutting down plugin")
        self.stop()

    def disable(self) -> None:
        """Disable the plugin"""
        self.log.info("Disabling plugin")
        self.stop()

    def _settings_to_set(self, settings: Settings) -> Set[Tuple[str, Any]]:
        """Convert settings to a set of tuples

        Note:
            List values are converted to tuples to be hashable and comparable

        Args:
            settings (:obj:`npc.types.Settings`): Settings to convert (before or after)

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
            :obj:`npc.types.Settings`: Settings dictionary
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

        This function is called when settings are changed. It's a good place to
        react to settings changes. The default implementation logs the changes
        and updates the log level if the verbose setting is changed.

        .. versionchanged:: 0.3.4 Fixed still logging debug messages when verbose is disabled

        Args:
            before (:obj:`npc.types.Settings`): Complete settings before the change
            after (:obj:`npc.types.Settings`): Complete settings after the change
            change (:obj:`npc.types.SettingsDiff`): Dictionary of changes in the settings
        """
        self.log.info(f"Settings change: {json.dumps(change)}")

        if "verbose" in change["after"]:
            new_level = logging.DEBUG if change["after"]["verbose"] else logging.INFO
            self.log.setLevel(new_level)
            # This should be done in the logging module, but for some reason it doesn't work
            # so we have to clear the cache manually
            self.log._cache.clear()  # type: ignore[attr-defined]

            self.log.info(f"Verbose logging {'enabled' if self.config.verbose else 'disabled'}")

    def window(self, message: str, title: Optional[str] = None) -> None:
        """Open a window with a message

        .. versionchanged:: 0.2.0 Renamed from :meth:`npc.BasePlugin.window_log` to
            :meth:`npc.BasePlugin.window`

        The title will be prefixed with the plugin name or if not provided, the
        plugin name will be used as the title.

        Args:
            message (:obj:`str`): Message to be shown in the window
            title (:obj:`str`, optional): Title of the window. Defaults to the plugin name.
        """
        if not title:
            title = self.plugin_name
        else:
            title = f"{self.plugin_name}: {title}"
        log(message, title=title)
