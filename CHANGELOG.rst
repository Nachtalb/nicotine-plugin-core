Changelog
=========

0.5.0
-----

* Removed: [:class:`npc.PeriodicJob`] :attr:`npc.PeriodicJob.min_delay` removed to make the waiting for next run non GIL blocking
* Added: [:class:`npc.PeriodicJob`] :attr:`npc.PeriodicJob.all_jobs` - list of all running jobs, :attr:`npc.PeriodicJob.log` - Logging for jobs, :attr:`npc.PeriodicJob.id` - Unique ID of the job, :meth:`npc.PeriodicJob.set_log_level` - To change the log level for a job
* Changed: [:class:`npc.PeriodicJob`] :attr:`_stopped` -> :attr:`_stop_event`, :attr:`_can_run` -> :attr:`_pause_event`, :attr:`npc.PeriodicJob.last_run` - Is now a instance variable rather than class variable which could have caused unexpected behaviour
* Changed: [:func:`npc.info.load_config`] Move to agnostic pyproject instead of poetry specific
* Changed: [:meth:`npc.BasePlugin.check_update`] Always show the update window not only on the first run
* Added: [:meth:`npc.BasePlugin.update_available`] Hook to handle available updates for plugins that need it
* Changed: [:meth:`npc.BasePlugin.stop`] Stop all running periodic jobs (incl. ones not created by the base plugin)
* Changed: [:meth:`npc.BasePlugin.settings_changed`] Also adjust logging for periodic jobs

0.4.2
-----

* Changed: [:meth:`npc.BasePlugin._automatic_update_check_delay`] Fix automatic update delay not reflected when changing the interval

0.4.1
-----

* Changed: [:func:`npc.reload_plugin`] Changed :paramref:`plugin_name` to :paramref:`plugin_id` as it is more accurate
* Removed: [:class:`npc.BasePlugin`] Removed :meth:`npc.BasePlugin.__name__` in favour of :attr:`npc.BasePlugin.plugin_name`.
* Added: [:meth:`npc.BasePlugin.plugin_identifier`] Added plugin identifier
* Changed: [:meth:`npc.BasePlugin.stop`] Fix unloading of modules

0.4.0
-----

* Changed: [:class:`npc.config.Field`] Added ``label`` parameter and made ``description`` optional.
* Added: [:meth:`npc.config.Field.metasettings_description`] Added property combining label and description
* Changed: [:func:`npc.String`] Added ``label`` parameter and made ``description`` optional.
* Changed: [:func:`npc.Int`] Added ``label`` parameter and made ``description`` optional.
* Changed: [:func:`npc.Float`] Added ``label`` parameter and made ``description`` optional.
* Changed: [:func:`npc.Bool`] Added ``label`` parameter and made ``description`` optional.
* Changed: [:func:`npc.TextView`] Added ``label`` parameter and made ``description`` optional.
* Changed: [:func:`npc.Dropdown`] Added ``label`` parameter and made ``description`` optional.
* Changed: [:func:`npc.Radio`] Added ``label`` parameter and made ``description`` optional.
* Changed: [:func:`npc.ListString`] Added ``label`` parameter and made ``description`` optional.
* Changed: [:func:`npc.File`] Added ``label`` parameter and made ``description`` optional.
* Changed: [:func:`npc.Folder`] Added ``label`` parameter and made ``description`` optional.
* Changed: [:func:`npc.Image`] Added ``label`` parameter and made ``description`` optional.
* Added: [:mod:`npc.changes`] [:data:`npc.IS_DEV`] Explicit flag for development versions
* Changed: [:func:`npc.info.load_config`] Return whether the plugin is a development version

0.3.6
-----

* Changed: [:func:`npc.log`] Fix windowed messages on Nicotine+ < 3.3.0
* Added: [:class:`npc.LegacyLogLevel`] Fix windowed messages on Nicotine+ < 3.3.0
* Changed: [:meth:`npc.BasePlugin.check_update`] Show window if no updates are available

0.3.5
-----

* Changed: [:func:`npc.command`] Support legacy command system for Nicotine+ < 3.3.0
* Changed: [:class:`npc.logging.NLogHandler`] Fix logging on Nicotine+ < 3.3.3
* Changed: [:func:`npc.log`] Fix logging on Nicotine+ < 3.3.3
* Changed: [:meth:`npc.Version.parse`] Properly parse version strings with alpha, beta, and dev releases. Fixing recognition of dev version in config.
* Changed: [:meth:`npc.BasePlugin._setup_commands`] Add support for Nicotine+ < 3.3.0 legacy command system

0.3.4
-----

* Changed: [:meth:`npc.BasePlugin.settings_changed`] Fixed still logging debug messages when verbose is disabled

0.3.2
-----

* Added: [:mod:`npc.changes`] Export * from ``npc`` module in root ``__init__.py``, in order to make imports easier when this package is used in another party plugin.
* Changed: [:mod:`npc.changes`] Updated ``scripts.py`` and ``generate_changelog.py`` to be usable in plugins using this package. Just copy them over and use them as is.
* Changed: [:mod:`npc.changes`] Document the use of all the :doc:`scripts <scripts>` in this package.

0.3.1
-----

* Changed: [:class:`npc.config.Field`] Removed `plugin` as a parameter for the :paramref:`from_value` function.
* Changed: [:meth:`npc.config.Field.from_value`] Removed `plugin` as a parameter.
* Added: [:func:`npc.Folder`] Quick alias for :func:`File` with :attr:`npc.types.FileChooser.FOLDER`
* Added: [:func:`npc.Image`] Quick alias for :func:`File` with :attr:`npc.types.FileChooser.IMAGE`

0.3.0
-----

* Added: [:func:`npc.File`] (no description provided)
* Changed: [:class:`npc.Version`] Add support for proper semantic versioning (alpha and beta releases)

0.2.0
-----

* Added: [:class:`npc.logging.NLogHandler`] (no description provided)
* Removed: [:class:`npc.BasePlugin`] Removed :meth:`npc.BasePlugin.vlog` in favour of the :attr:`npc.BasePlugin.log` logger instance. Use ``self.log.debug(...)`` instead.
* Changed: [:class:`npc.BasePlugin`] Replaced ``npc.BasePlugin.log()`` function with :attr:`npc.BasePlugin.log` logger instance. Use ``self.log.info(...)`` instead of ``self.log(...)``.
* Changed: [:meth:`npc.BasePlugin.window`] Renamed from :meth:`npc.BasePlugin.window_log` to :meth:`npc.BasePlugin.window`
