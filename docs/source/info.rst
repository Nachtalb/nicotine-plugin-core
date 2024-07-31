Info
====

.. automodule:: npc.info

.. py:data:: npc.CONFIG
    :type: npc.types.PluginConfig

    Plugin information (not npc but the plugin using npc)

.. py:data:: npc.BASE_PATH
    :type: pathlib.Path

    Base path of the plugin (not npc but the plugin using npc)

.. py:data:: npc.__version__
    :type: str

    Version of the plugin (not npc but the plugin using npc)

.. py:data:: npc.IS_DEV
    :type: str

    Explicit flag to check if the plugin is in development mode (not npc but the plugin using npc)

.. autofunction:: npc.info.find_file_in_parents

.. autofunction:: npc.info.load_config
