Changelog
=========

0.3.5
-----

* Changed: [:meth:`npc.BasePlugin._setup_commands`] Add support for Nicotine+ < 3.3.0 legacy command system
* Changed: [:func:`npc.command`] Support legacy command system for Nicotine+ < 3.3.0
* Changed: [:class:`npc.logging.NLogHandler`] Fix logging on Nicotine+ < 3.3.3
* Changed: [:func:`npc.log`] Fix logging on Nicotine+ < 3.3.3
* Changed: [:meth:`npc.Version.parse`] Properly parse version strings with alpha, beta, and dev releases. Fixing recognition of dev version in config.

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

* Removed: [:class:`npc.BasePlugin`] Removed :meth:`npc.BasePlugin.vlog` in favour of the :attr:`npc.BasePlugin.log` logger instance. Use ``self.log.debug(...)`` instead.
* Changed: [:class:`npc.BasePlugin`] Replaced ``npc.BasePlugin.log()`` function with :attr:`npc.BasePlugin.log` logger instance. Use ``self.log.info(...)`` instead of ``self.log(...)``.
* Changed: [:meth:`npc.BasePlugin.window`] Renamed from :meth:`npc.BasePlugin.window_log` to :meth:`npc.BasePlugin.window`
* Added: [:class:`npc.logging.NLogHandler`] (no description provided)
