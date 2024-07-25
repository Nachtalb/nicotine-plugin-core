# Nicotine+ Plugin Core (NPC)

This is the core tp all my [Nicotine+][n+] plugins. It provides a more advanced
way to create plugins than the default n+ way. It is only a layer on top of the
default way, so you can still use the default way to create plugins.

Some features of this core are:

- Documentation
- Full type hints support
- Command decorator
- Non blocking commands
- Periodic tasks support
- Automatic update checking
- Detect changes in settings
- Plugin reload via a command
- And more...

```python
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
```

## Installation

You can find a full guide on how to install this core for your plugin in the
provided documentation. You can use the [online documentation][docs] or easily
build it yourself locally.

```sh

git clone https://github.com/Nachtalb/npc.git
cd npc
poetry install --with docs
poetry run build-docs
poetry run open-docs
```

Once you've built and opened the documentation you will find a guide on how to
use this core step by step under [Installation][installation-docs]. Enjoy!

## Credits and Thanks

This project is based on the work of the [Nicotine+][n+] team and the their
plugin system.

## License

This project is licensed under the LGPLv3 License - see the [LICENSE](LICENSE)
file for details.

[n+]: https://nicotine-plus.org/ "Nicotine+ Website"
[docs]:
  https://nicotine-plugin-core-npc.readthedocs.io/latest/
  "Nicotine+ Plugin Core Documentation"
[installation-docs]:
  https://nicotine-plugin-core-npc.readthedocs.io/latest/installation.html
  "Installation Guide"
