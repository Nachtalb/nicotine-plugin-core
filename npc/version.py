"""This module provides a Version class for comparing versions

It is mainly used in :class:`npc.BasePlugin` to check if the plugin has a
newer version available. The version can be compared using the comparison
operators such as ``==``, ``!=``, ``<``, ``<=``, ``>``, and ``>=``.

Example:

    .. code-block:: python

        old = Version(1, 2, 3)
        new = Version.parse("1.2.4")

        new > old
        # True
"""

import re
from typing import Optional, Union

__all__ = ["Version"]


class Version:
    """Version class for comparing versions

    Example:

        .. code-block:: python

            Version(1, 2, 3, "dev")
            # Version(1.2.3dev)

            Version.parse("1.2.3dev")
            # Version(1.2.3dev)

            Version.parse("v1.2.3")
            # Version(1.2.3)

            Version.parse("1.2.3") == Version(1, 2, 3)
            # True

            Version.parse("1.2.3") < Version(1, 2, 4)
            # True

            Version.parse("1.2.3") > Version(1, 2, 4)
            # False

    Args:
        major (:obj:`int`): Major version
        minor (:obj:`int`): Minor version
        patch (:obj:`int`): Patch version
        dev (:obj:`str`, optional): Development version

    Attributes:
        major (:obj:`int`): Major version
        minor (:obj:`int`): Minor version
        patch (:obj:`int`): Patch version
        dev (:obj:`str`, optional): Development version

    Properties:
        astuple (:obj:`tuple`): Tuple representation of the version
    """

    def __init__(self, major: int, minor: int, patch: int, dev: Optional[str] = None) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch
        self.dev = dev

    @property
    def astuple(self) -> tuple[int, int, int, Optional[str]]:
        """Tuple representation of the version

        Returns:
            :obj:`tuple`: Tuple of version parts
        """
        return self.major, self.minor, self.patch, self.dev

    @staticmethod
    def parse(*version: Union[str, int, None]) -> "Version":
        """Parse version string to Version object

        .. seealso:: :class:`Version` on usage

        Note:
            Version such as ``1.2`` or simply ``1`` will be parsed as
            ``1.2.0`` and ``1.0.0`` respectively.

        Args:
            *version (:obj:`str`, :obj:`int`) : Version string or tuple of
                version parts. If length is 1, it will be split by "." and
                parsed as version parts

        Returns:
            :obj:`Version`: Version object

        Raises:
            :obj:`ValueError`: If version cannot be parsed
        """
        if len(version) == 1 and isinstance(version[0], str):
            match = re.match(r"v?(\d+)\.?(\d+)?\.?(\d+)?\.?(\w+)?", version[0])
            if not match:
                raise ValueError(f"Version {version} cannot be parsed")
            version = match.groups()
        else:
            version += (None,) * (4 - len(version))

        return Version(
            major=int(version[0]) if version[0] is not None else 0,
            minor=int(version[1]) if version[1] is not None else 0,
            patch=int(version[2]) if version[2] is not None else 0,
            dev=str(version[3]) if version[3] is not None else None,
        )

    def __str__(self) -> str:
        """String representation of the version

        .. seealso:: :meth:`Version.__repr__` for representation
        """
        return ".".join(map(str, self.astuple[:3])) + (self.dev if self.dev is not None else "")

    def __repr__(self) -> str:
        """Representation of the version

        .. seealso:: :meth:`Version.__str__` for string representation
        """
        return f"Version({self})"

    def __eq__(self, version: "Version") -> bool:  # type: ignore[override]
        """Check if versions are equal

        .. seealso:: :class:`Version` on usage

        Args:
            version (:obj:`Version`): Version object

        Returns:
            :obj:`bool`: True if versions are equal, False otherwise
        """
        return self.astuple == version.astuple

    def __lt__(self, version: "Version") -> bool:
        """Check if version is less than another version

        .. seealso:: :class:`Version` on usage

        Args:
            version (:obj:`Version`): Version object

        Returns:
            :obj:`bool`: True if version is less than the other version, False otherwise
        """
        return self.astuple[:3] < version.astuple[:3] or (
            self.astuple[:3] == version.astuple[:3]
            and (
                (self.dev is None and version.dev is not None)
                or (self.dev is not None and version.dev is not None and self.dev < version.dev)
            )
        )

    def __le__(self, version: "Version") -> bool:
        """Check if version is less than or equal to another version

        .. seealso:: :class:`Version` on usage

        Args:
            version (:obj:`Version`): Version object

        Returns:
            :obj:`bool`: True if version is less than or equal to the other version, False otherwise
        """
        return self < version or self == version

    def __gt__(self, version: "Version") -> bool:
        """Check if version is greater than another version

        .. seealso:: :class:`Version` on usage

        Args:
            version (:obj:`Version`): Version object

        Returns:
            :obj:`bool`: True if version is greater than the other version, False otherwise
        """
        return not self < version

    def __ge__(self, version: "Version") -> bool:
        """Check if version is greater than or equal to another version

        .. seealso:: :class:`Version` on usage

        Args:
            version (:obj:`Version`): Version object

        Returns:
            :obj:`bool`: True if version is greater than or equal to the other version, False otherwise
        """
        return not self < version or self == version

    def __ne__(self, version: "Version") -> bool:  # type: ignore[override]
        """Check if versions are not equal

        .. seealso:: :class:`Version` on usage

        Args:
            version (:obj:`Version`): Version object

        Returns:
            :obj:`bool`: True if versions are not equal, False otherwise
        """
        return not self == version
