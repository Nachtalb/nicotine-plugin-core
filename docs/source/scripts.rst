Scripts
=======

This package provides custom scripts for a variety of tasks. The scripts are
defined mainly in ``scripts.py`` and are set up with poetry to be used as commands.

All of these scripts can be copied over to your own project, given you provide
them the proper structure. Each section has a note on how to do that.
Each section also has a file defined if applicable. This file is the actual script
the commands used to run the scripts in the examples, are the ones defined and
provided by poetry in the ``pyproject.toml`` file.

Generate Changelog
------------------

Changelogs are generally generated from the source code's docstrings. You can
use directives such as ``.. versionadded:: 0.1.0 ...`` to indicate when a feature
was added. More information on this can be found here :mod:`npc.changes` (which
tracks changes other than package API changes) and `Sphinx Tracking Changes <https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#describing-changes-between-versions>`_.

Instances when the changelog is automatically generated include:

- When a new release is made.

  .. seealso:: :ref:`release`

- When the ``build-docs`` command is run.

  .. seealso:: :ref:`Build Documentation`

You can also manually generate the changelog by running the following command:

.. code-block:: sh

    build-changelog CHANGELOG.rst

    build-changelog --help

When you look at the help message you'll see that you can provide two more
arguments other than the output file. Those are ``--directory`` and ``--exclude``.

- ``--directory`` is the directory where the source files are located. By default
  the script takes the first folder next to it that contains a ``__init__.py`` file.

- ``--exclude`` is a list of paths that should be excluded from the search. This
  makes this script usable in other plugins that use this package as a base.
  You can't install packages as described in :doc:`installation <installation>`
  but you can copy the package into your plugin's source. In that case you can
  exclude the npc package from the search (which is actually the default
  behavior).

.. note::

   File: ``generate_changelog.py``

   This script can be used in your own project without any setup. Just copy
   ``generate_changelog.py`` into your project and run it.

Build Documentation
-------------------

The documentation is built using Sphinx. The configuration is located in the
``docs`` folder. The main configuration file is ``source/conf.py``. Before
generating the docs, however, you need to install the dependencies. This can be
done by running the following command:

.. code-block:: sh

    poetry install --with docs

After the dependencies are installed you can generate the documentation by
running the following command:

.. code-block:: sh

    build-docs

This command also generates the changelog, as mentioned in the previous section.
The documentation is built simply by running Sphinx's ``make html`` command.
The output is located in the ``docs/build`` folder.

.. note::

    File: ``generate_changelog.py`` and Sphinx setup in ``docs`` folder.

    In order to use this command you need Sphinx and some sphinx extensions
    installed. Then you need a proper configuration in the ``docs`` folder.
    And finally you also need the ``generate_changelog.py`` script in your
    project.

    You can copy over the docs folder and delete all the ``.rst`` files in the
    ``source`` folder which you don't need. I'd at least keep the ``index.rst``,
    ``changes.rst`` and ``changelog.rst`` files. You can then adjust the
    ``index.rst`` and ``conf.py`` files to your liking. In the ``conf.py`` file
    you especially need to change the footer and project links, as they point
    to this project. Name, version, etc. is extracted from the ``pyproject.toml``
    via the ``docs/auxil/load_config.py`` file. Also adjust that one's fallback
    config.

Open Documentation
------------------

This script opens the documentation in your default browser. This is useful
when you want to quickly check the documentation after making changes. You can
run the following command to open the documentation:

.. code-block:: sh

    open-docs

This command opens the ``index.html`` file in the ``docs/build/html``
folder in your default browser.

.. note::

   While this script doesn't require a specific setup, you'll need to have
   built the documentation first. See the "Build Documentation" section for details.

Check
-----

This script runs a variety of checks via `pre-commit <https://pre-commit.com/>`_.
The checks are defined in the ``.pre-commit-config.yaml`` file. You can run the
checks by running the following command:

.. code-block:: sh

    check

This command is just an alias for ``pre-commit run --all-files``.

.. note::

    File: ``.pre-commit-config.yaml``

    You can copy over the ``.pre-commit-config.yaml`` file to your project and
    run the checks. You can also adjust the checks to your liking. The checks
    are defined in the ``.pre-commit-config.yaml`` file. You can also add more
    checks by adding more entries to the file.

    You also need the dev dependencies installed. You can copy them over from the
    ``pyproject.toml`` file.

Release
-------

This script is used to release a new version of the package. It does the following:

1. Bumps the version in the ``pyproject.toml`` file.
2. Generates the changelog.
3. Update ``PLUGININFO``.
4. Commits the changes.
6. Tags the commit.
7. Pushes the commit and tag.
8. Bumps the version in the ``pyproject.toml`` file again to the next development version.
9. Updates the ``PLUGININFO`` again.
10. Commits the changes.
11. Pushes the commit.

You get asked at every step if you want to continue. You can run the following
command to release a new version:

.. code-block:: sh

    release

.. note::

   Files: ``release.sh`` and optionally ``generate_changelog.py`` and ``PLUGININFO``.

   You can copy over the ``release.sh`` file to your project and run it.

   If you have the ``generate_changelog.py`` script in your project, the script
   will use it to update the changelog.

   If you have a ``PLUGININFO`` file in your project, the script will update it's version.
