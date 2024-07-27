.. npc documentation master file, created by
   sphinx-quickstart on Wed Jul 24 23:08:44 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Nicotine+ Plugin Core
=====================

The "Nicotine+ Plugin Core" is a library that provides a set of tools to help
you develop plugins for the `Nicotine+ <https://nicotine-plus.org/>`_ client.

Nicotine+ is written in Python and uses `GTK+ <https://www.gtk.org/>`_. It
has built-in plugin support, but it's not very well documented and not very
user-friendly. This library aims to make it easier to develop plugins for
Nicotine+.

.. note::

    It's noteworthy that this module will sit in your plugin code. It's not possible
    to install packages into Nicotine+ itself. This is a limitation of the client.
    Follow the :doc:`installation guide <installation>` to see how to install
    this package into your plugin.

Notable Features
----------------

- Easy to use
- Fully typed
- Configuration management
- Automatic update checks
- Reloadable
- Easy command system
- Fully documented

Example
-------

Here is a small example of how to use the library to create a plugin:

.. code-block:: python

   from npc import BasePlugin, TextArea, command

   class Plugin(BasePlugin):
      class Config(BasePlugin.Config):
         hello_text = TextArea("Hello World!")

      @command
      def hello(self) -> None:
         """Say hello to the world."""
         self.window_log(self.config.hello_text)

With this code, you already have a working plugin that will open a window and
print "Hello World!" in it when running /hello in the chat.

As you can also see, I added an ease-of-use class :class:`npc.BaseConfig` that will help you
to manage your configuration. This class will automatically create the
corresponding ``settings`` and ``metasettings`` configurations needed for
Nicotine+. It's also typed, so while you use :func:`npc.TextArea`, :func:`npc.Int`,
or any other field, you get the correct type such as ``str``, ``int`` in this
case.

.. warning::

   It's important to note that if you want to change the configuration
   programmatically, you must use :meth:`npc.BaseConfig.apply` to persist
   the changes. By default, Nicotine+ will ignore configuration changes made
   through code. :meth:`npc.BaseConfig.apply` will make sure that the changes are
   updated behind the scenes in Nicotine+.

I strongly recommend that you type your code using `mypy <https://mypy.readthedocs.io/en/stable/>`_.
This will help you avoid many errors and make your code more robust.
Of course, this package is fully typed.

Check out :class:`npc.BasePlugin` for more information on how to create a plugin and
:func:`npc.command` for more information on how to create commands.

Update Feature
--------------

In addition to the default `PLUGININFO` file information that Nicotine+ requires
from you (that would be the ``name``, ``version``, ``author``, ``description``),
you can also provide ``prefix`` and ``repository``. The ``prefix`` will be
added to all commands of the plugin to prevent conflicts with other plugins.

The ``repository`` is a link to the repository of the plugin. If this is given,
the plugin will automatically check and notify the user if there is a new
version available.

.. note::

    As of now, this library only supports GitHub repositories. It will not
    check other resources such as GitLab or Bitbucket for updates.


Requirements
------------

This package requires Python 3.9 or higher.

.. toctree::
    :hidden:
    :caption: Installation

    installation
    scripts

.. toctree::
    :hidden:
    :caption: Reference

    core-tree
    auxiliary-tree


.. toctree::
    :hidden:
    :caption: Project

    changelog
    GitHub Repository <https://github.com/Nachtalb/npc>
    Me on Telegram <https://t.me/Nachtalb>
