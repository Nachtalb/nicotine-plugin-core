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
from typing import Optional, Tuple, Union

__all__ = ["Version"]


class Version:
    """Version class for comparing versions with semantic versioning support

    Example:
        .. code-block:: python

            Version(1, 2, 3, "alpha", 1)
            # Version(1.2.3a1)

            Version.parse("1.2.3a1")
            # Version(1.2.3a1)

            Version.parse("v1.2.3")
            # Version(1.2.3)

            Version.parse("1.2.3") == Version(1, 2, 3)
            # True

            Version.parse("1.2.3") < Version(1, 2, 4)
            # True

            Version.parse("1.2.3") > Version(1, 2, 4)
            # False

    .. versionchanged:: 0.3.0 Add support for proper semantic versioning (alpha and beta releases)

    Args:
        major (:obj:`int`): Major version
        minor (:obj:`int`): Minor version
        patch (:obj:`int`): Patch version
        prerelease (:obj:`str`, optional): Prerelease identifier (e.g., "alpha", "beta")
        prerelease_num (:obj:`int`, optional): Prerelease number

    Attributes:
        major (:obj:`int`): Major version
        minor (:obj:`int`): Minor version
        patch (:obj:`int`): Patch version
        prerelease (:obj:`str`, optional): Prerelease identifier
        prerelease_num (:obj:`int`, optional): Prerelease number

    Properties:
        astuple (:obj:`tuple`): Tuple representation of the version
        is_prerelease (:obj:`bool`): True if the version is a prerelease
        is_alpha (:obj:`bool`): True if the version is an alpha release
        is_beta (:obj:`bool`): True if the version is a beta release
    """

    def __init__(
        self, major: int, minor: int, patch: int, prerelease: Optional[str] = None, prerelease_num: Optional[int] = None
    ) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease
        self.prerelease_num = prerelease_num

    @property
    def astuple(self) -> Tuple[int, int, int, Optional[str], Optional[int]]:
        """Tuple representation of the version

        Returns:
            :obj:`tuple`: Tuple of version parts
        """
        return self.major, self.minor, self.patch, self.prerelease, self.prerelease_num

    @property
    def is_prerelease(self) -> bool:
        """Check if the version is a prerelease

        Returns:
            bool: True if the version is a prerelease, False otherwise
        """
        return self.prerelease is not None

    @property
    def is_alpha(self) -> bool:
        """Check if the version is an alpha release

        Returns:
            bool: True if the version is an alpha release, False otherwise
        """
        return self.prerelease == "alpha"

    @property
    def is_beta(self) -> bool:
        """Check if the version is a beta release

        Returns:
            bool: True if the version is a beta release, False otherwise
        """
        return self.prerelease == "beta"

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
            match = re.match(r"v?(\d+)\.?(\d+)?\.?(\d+)?(?:[-.]?(?:a|alpha|b|beta|dev)\.?(\d+)?)?", version[0])
            if not match:
                raise ValueError(f"Version {version} cannot be parsed")
            version_parts = match.groups()
        else:
            version_parts = version + (None,) * (5 - len(version))

        major = int(version_parts[0]) if version_parts[0] is not None else 0
        minor = int(version_parts[1]) if version_parts[1] is not None else 0
        patch = int(version_parts[2]) if version_parts[2] is not None else 0

        prerelease = None
        prerelease_num = None
        if version_parts[3]:
            if version_parts[3].startswith(("a", "alpha")):
                prerelease = "alpha"
            elif version_parts[3].startswith(("b", "beta")):
                prerelease = "beta"
            elif version_parts[3].startswith("dev"):
                prerelease = "dev"

            prerelease_num = int(version_parts[3].split(".")[-1]) if version_parts[3].split(".")[-1].isdigit() else None

        return Version(major, minor, patch, prerelease, prerelease_num)

    def __str__(self) -> str:
        """String representation of the version

        .. seealso:: :meth:`Version.__repr__` for representation
        """
        version_str = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version_str += f"{self.prerelease[0]}"
            if self.prerelease_num is not None:
                version_str += f"{self.prerelease_num}"
        return version_str

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
        if self.major != version.major:
            return self.major < version.major
        if self.minor != version.minor:
            return self.minor < version.minor
        if self.patch != version.patch:
            return self.patch < version.patch

        if self.prerelease is None and version.prerelease is None:
            return False
        if self.prerelease is None:
            return False
        if version.prerelease is None:
            return True

        prerelease_order = {"dev": 0, "alpha": 1, "beta": 2}
        if self.prerelease != version.prerelease:
            return prerelease_order[self.prerelease] < prerelease_order[version.prerelease]

        if self.prerelease_num is None and version.prerelease_num is None:
            return False
        if self.prerelease_num is None:
            return True
        if version.prerelease_num is None:
            return False

        return self.prerelease_num < version.prerelease_num

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
        return not (self < version or self == version)

    def __ge__(self, version: "Version") -> bool:
        """Check if version is greater than or equal to another version

        .. seealso:: :class:`Version` on usage

        Args:
            version (:obj:`Version`): Version object

        Returns:
            :obj:`bool`: True if version is greater than or equal to the other version, False otherwise
        """
        return not self < version

    def __ne__(self, version: "Version") -> bool:  # type: ignore[override]
        """Check if versions are not equal

        .. seealso:: :class:`Version` on usage

        Args:
            version (:obj:`Version`): Version object

        Returns:
            :obj:`bool`: True if versions are not equal, False otherwise
        """
        return not self == version
