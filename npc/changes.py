"""Changes are usually documented with directives in the source code. These are
picked up by the changelog generator to create the changelog file.

Example:
    .. code-block:: python

        def my_function():
            '''
            ​.. versionadded:: 0.1.0 Added my_function
            ​.. versionchanged:: 0.2.0 Changed parameter order
            ​.. versionremoved:: 0.3.0 Removed unused parameter X
            '''
            pass

However, sometimes changes are not documented in the source code, but are still important
enough to be included in the changelog. For example, changes to the build system, or
changes to the documentation build process. These changes are documented in this file.

.. versionadded:: 0.3.2
    Export * from ``npc`` module in root ``__init__.py``, in order
    to make imports easier when this package is used in another party plugin.

.. versionchanged:: 0.3.2
    Updated ``scripts.py`` and ``generate_changelog.py`` to be
    usable in plugins using this package. Just copy them over and use them as is.

.. versionchanged:: 0.3.2
    Document the use of all the :doc:`scripts <scripts>` in this
    package.

.. versionadded:: 0.4.0 [:data:`npc.IS_DEV`] Explicit flag for development versions
"""
