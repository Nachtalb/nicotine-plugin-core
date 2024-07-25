Installation
============

This package requires python 3.9 or higher.

To set the record straight, this package is not available on PyPI. Nor does it
make sense to publish it there. Plugin you install in Nicotine+ are cannot
use PyPI packages.

1. Get the code
---------------

1.1 Clone the Repository
^^^^^^^^^^^^^^^^^^^^^^^^
The easies way to install this package is to clone it as a submodule into your
project. This way you can easily update it.

.. code-block:: bash

    git submodule add https://github.com/Nachtalb/npc.git

The thing is though that the code resides in a subfolder. Technically this isn't
a problem, as I have already added a `__init__.py` file to the root of the repository.
But it just doesn't look as clean when importing the package.

1.2 Copy the Code
^^^^^^^^^^^^^^^^^

You can also just copy the code into your project. For that I recommend
downloading the latest release from the `Github Repository <https://github.com/Nachtalb/npc>`_
and copying the `npc` folder into your project.

2. Update your ``PLUGININFO`` file
----------------------------------

.. note::

   From here on out we'll continue on with the copied version as it looks cleaner
   and makes the documentation easier to understand.

You probaly already have a ``PLUGININFO`` file that looks somewhat like this:

.. code-block:: text

   NAME="My Plugin"
   AUTHOR="Your Name"
   DESCRIPTION="This is my plugin"

To get the best out of this package you should add the following lines to it:

.. code-block:: text

   VERSION="0.1.0"
   PREFIX="myplugin"
   REPOSITORY="GithubUser/Repository"  # Or the link to the repository

3. Use the package
------------------

Now you can use the package in your code.

.. code-block:: python

   from npc import BasePlugin

   class Plugin(BasePlugin):
       pass


That's it. You're ready to go. This is  the smallest possible plugin you can
create. And it already includes checking for updates, detecting settings changes,
and automaically adds a prefix if you work on a ``.dev`` version of your plugin.

I recommnd you to check out the `Reference <reference>`_ for more information
on how to use the package.

Here is a bit larger example for a plugin:


.. code-block:: python

  from .npc import BasePlugin, Checkbox, Dropdown, Float, Int, ListString, Radio, String, TextArea, command
  from .npc.types import CommandInterface, Settings, SettingsDiff


  class Plugin(BasePlugin):
      class Config(BasePlugin.Config):
          single_line = String("This is a single line string", "I am the default value")
          multi_line = TextArea("This is a multi line string", "I am the default value")
          number = Int("This is a number", 42)
          float = Float("This is a number with decimals", 3.14)
          check = Checkbox("This is a checkbox", True)
          dropdown = Dropdown("This is a dropdown", ["Option 1", "Option 2", "Option 3"], "Option 1")
          radio = Radio("This is a radio", ["Option 1", "Option 2", "Option 3"], "Option 1")
          list = ListString("This is a list", ["Value 1", "Value 2", "Value 3"])

          counter = Int("Counter", 0)

      def init(self) -> None:
          super().init()

          self.log.debug("Verbose logging")  # checks if self.config.verbose is True before logging

          # Do something once the plugin is loaded

      def stop(self) -> None:
          super().stop()

          # Plugin has been stopped, do some cleanup if needed

      def shutdown_notification(self) -> None:
          super().shutdown_notification()  # will run .stop()

          # Nicotine+ is shutting down

      def settings_changed(self, before: Settings, after: Settings, change: SettingsDiff) -> None:
          super().settings_changed(before, after, change)

          # Settings have been changed, do something with it

      @command(parameters=["<name>", "<age>"])  # Parameters with <> are required
      def hello(self, name: str, age: int) -> None:
          """Say hello to the world."""
          age += 1  # age: int - will automagically get parsed to an int

          self.window("Hello, %s! In a year you will be %d years old.", name, age)

      @command(parameters=["[n]"], aliases=["inc"])  # Parameters with [] are optional
      def increment(self, n: int = 1) -> None:
          """Increment the counter."""
          self.config.counter += n
          self.config.apply()  # Persist settings change across sessions
          self.log.info("Counter is now at %d", self.config.counter)  # normal logging to the console

      @command(parameters=["[n]"], aliases=["dec"])  # Aliases are additional names for the command
      def decrement(self, n: int = 1) -> None:
          """Decrement the counter."""
          self.config.counter -= n
          self.config.apply()  # Persist settings change across sessions
          self.log.info("Counter is now at %d", self.config.counter)

      @command(disabled_interfaces=[CommandInterface.CHATROOM])  # Disable the command in the chatroom
      def secret(self) -> None:
          """This command is a secret."""
          self.window("You can't run this command in the chatroom. It's a secret!")
